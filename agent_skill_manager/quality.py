from __future__ import annotations

import json
import math
import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

import yaml


NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
TOKEN_RE = re.compile(r"[a-z0-9]+")
FRONTMATTER_RE = re.compile(
    r"\A---[ \t]*\r?\n(?P<yaml>.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL
)

PLACEHOLDER_PATTERNS = {
    "unfinished-placeholder": re.compile(
        r"\[(?:todo|tbd|describe|mock|operational step|expected output)|"
        r"\b(?:TODO|TBD)\b|A brief description of what this skill does|"
        r"Instructions for the agent to follow",
        re.IGNORECASE,
    ),
    "reasoning-trace": re.compile(
        r"agent thought|chain[- ]of[- ]thought|\bCoT\b", re.IGNORECASE
    ),
}

OVERCLAIM_RE = re.compile(
    r"\b(?:perfectly|bit-perfect|guaranteed|always-alive|master protocol|"
    r"under all circumstances)\b",
    re.IGNORECASE,
)
HOST_TOOL_RE = re.compile(
    r"\b(?:view_file|write_to_file|str_replace_editor|computer\.use)\b"
)

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "build",
    "create",
    "design",
    "for",
    "from",
    "help",
    "in",
    "into",
    "implement",
    "is",
    "it",
    "of",
    "on",
    "or",
    "run",
    "that",
    "the",
    "this",
    "to",
    "update",
    "use",
    "when",
    "with",
}


@dataclass(frozen=True)
class Diagnostic:
    severity: str
    code: str
    message: str
    path: str
    skill: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SkillPackage:
    path: Path
    name: str | None = None
    description: str | None = None
    body: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    routing: dict[str, Any] | None = None

    @property
    def label(self) -> str:
        return self.name or self.path.name

    def to_inventory(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "path": str(self.path),
            "description": self.description,
            "has_openai_metadata": (self.path / "agents" / "openai.yaml").is_file(),
            "has_legacy_gemini_metadata": (
                self.path / "gemini-extension.json"
            ).is_file(),
            "routing_positive": len((self.routing or {}).get("positive", [])),
            "routing_negative": len((self.routing or {}).get("negative", [])),
            "scripts": _count_files(self.path / "scripts"),
            "references": _count_files(self.path / "references"),
            "assets": _count_files(self.path / "assets"),
        }


@dataclass
class RoutingCase:
    skill: str
    kind: str
    prompt: str
    predicted: str | None
    expected: str | None
    margin: float
    passed: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AuditResult:
    root: Path
    skills: list[SkillPackage]
    diagnostics: list[Diagnostic]
    routing_cases: list[RoutingCase]

    @property
    def errors(self) -> int:
        return sum(item.severity == "error" for item in self.diagnostics)

    @property
    def warnings(self) -> int:
        return sum(item.severity == "warning" for item in self.diagnostics)

    def exit_code(self, strict: bool = False) -> int:
        return int(self.errors > 0 or (strict and self.warnings > 0))

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": str(self.root),
            "summary": {
                "skills": len(self.skills),
                "errors": self.errors,
                "warnings": self.warnings,
                "routing_cases": len(self.routing_cases),
                "routing_failures": sum(not case.passed for case in self.routing_cases),
            },
            "skills": [skill.to_inventory() for skill in self.skills],
            "diagnostics": [item.to_dict() for item in self.diagnostics],
            "routing_cases": [case.to_dict() for case in self.routing_cases],
        }


def load_config(root: Path) -> dict[str, Any]:
    config_path = root / "asm-config.json"
    if not config_path.is_file():
        return {}
    with config_path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("asm-config.json must contain a JSON object")
    return data


def discover_skills(skills_dir: Path) -> tuple[list[SkillPackage], list[Diagnostic]]:
    diagnostics: list[Diagnostic] = []
    packages: list[SkillPackage] = []
    if not skills_dir.is_dir():
        diagnostics.append(
            Diagnostic(
                "error",
                "skills-dir-missing",
                "Configured skills directory does not exist.",
                str(skills_dir),
            )
        )
        return packages, diagnostics

    for child in sorted(skills_dir.iterdir()):
        if not child.is_dir() or child.name.startswith("."):
            continue
        skill_md = child / "SKILL.md"
        if not skill_md.is_file():
            diagnostics.append(
                Diagnostic(
                    "warning",
                    "orphan-skill-directory",
                    "Directory under skills/ has no SKILL.md.",
                    str(child),
                    child.name,
                )
            )
            continue
        package, parse_diagnostics = _load_skill(child)
        packages.append(package)
        diagnostics.extend(parse_diagnostics)
    return packages, diagnostics


def audit_repository(
    root: Path,
    *,
    include_routing: bool = True,
) -> AuditResult:
    root = root.resolve()
    try:
        config = load_config(root)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return AuditResult(
            root,
            [],
            [
                Diagnostic(
                    "error",
                    "config-invalid",
                    str(exc),
                    str(root / "asm-config.json"),
                )
            ],
            [],
        )

    skills_dir, quality, diagnostics = _validate_config(root, config)
    if skills_dir is None:
        return AuditResult(root, [], diagnostics, [])

    packages, discovery_diagnostics = discover_skills(skills_dir)
    diagnostics.extend(discovery_diagnostics)

    for package in packages:
        diagnostics.extend(_check_skill(package, quality))
    diagnostics.extend(_check_portfolio(packages))

    routing_cases: list[RoutingCase] = []
    if include_routing:
        route_diagnostics, routing_cases = _check_routing(packages, quality)
        diagnostics.extend(route_diagnostics)

    diagnostics.sort(key=lambda item: (item.path, item.severity != "error", item.code))
    return AuditResult(root, packages, diagnostics, routing_cases)


def _validate_config(
    root: Path, config: dict[str, Any]
) -> tuple[Path | None, dict[str, Any], list[Diagnostic]]:
    config_path = root / "asm-config.json"
    diagnostics: list[Diagnostic] = []

    schema_version = config.get("schema_version", 2)
    if schema_version != 2:
        diagnostics.append(
            Diagnostic(
                "error",
                "config-schema-unsupported",
                "schema_version must be 2.",
                str(config_path),
            )
        )

    raw_skills_dir = config.get("skills_dir", "skills")
    skills_dir: Path | None = None
    if not isinstance(raw_skills_dir, str) or not raw_skills_dir.strip():
        diagnostics.append(
            Diagnostic(
                "error",
                "config-skills-dir-invalid",
                "skills_dir must be a non-empty relative path.",
                str(config_path),
            )
        )
    else:
        candidate = (root / raw_skills_dir).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "config-skills-dir-outside-root",
                    "skills_dir must stay inside the audited repository.",
                    str(config_path),
                )
            )
        else:
            skills_dir = candidate

    raw_quality = config.get("quality", {})
    if not isinstance(raw_quality, dict):
        diagnostics.append(
            Diagnostic(
                "error",
                "config-quality-invalid",
                "quality must be a JSON object.",
                str(config_path),
            )
        )
        raw_quality = {}

    quality = dict(raw_quality)
    _validate_boolean_setting(
        quality, "require_routing_tests", False, config_path, diagnostics
    )
    _validate_boolean_setting(
        quality, "require_folder_name_match", False, config_path, diagnostics
    )
    _validate_boolean_setting(
        quality, "check_legacy_metadata", False, config_path, diagnostics
    )
    description_max = quality.get("description_max_chars", 600)
    if (
        not isinstance(description_max, int)
        or isinstance(description_max, bool)
        or description_max < 30
    ):
        diagnostics.append(
            Diagnostic(
                "error",
                "config-description-max-invalid",
                "description_max_chars must be an integer of at least 30.",
                str(config_path),
            )
        )
        quality["description_max_chars"] = 600

    routing_margin = quality.get("routing_min_margin", 0.02)
    if (
        not isinstance(routing_margin, (int, float))
        or isinstance(routing_margin, bool)
        or not math.isfinite(routing_margin)
        or routing_margin < 0
    ):
        diagnostics.append(
            Diagnostic(
                "error",
                "config-routing-margin-invalid",
                "routing_min_margin must be a finite, non-negative number.",
                str(config_path),
            )
        )
        quality["routing_min_margin"] = 0.02

    return skills_dir, quality, diagnostics


def _validate_boolean_setting(
    quality: dict[str, Any],
    key: str,
    default: bool,
    config_path: Path,
    diagnostics: list[Diagnostic],
) -> None:
    value = quality.get(key, default)
    if not isinstance(value, bool):
        diagnostics.append(
            Diagnostic(
                "error",
                f"config-{key.replace('_', '-')}-invalid",
                f"{key} must be true or false.",
                str(config_path),
            )
        )
        quality[key] = default


def _load_skill(path: Path) -> tuple[SkillPackage, list[Diagnostic]]:
    skill_md = path / "SKILL.md"
    diagnostics: list[Diagnostic] = []
    package = SkillPackage(path=path)
    try:
        text = skill_md.read_text(encoding="utf-8")
    except OSError as exc:
        diagnostics.append(
            Diagnostic("error", "skill-unreadable", str(exc), str(skill_md), path.name)
        )
        return package, diagnostics

    frontmatter_match = FRONTMATTER_RE.match(text)
    if frontmatter_match is None:
        if not re.match(r"\A---[ \t]*(?:\r?\n)", text):
            code = "frontmatter-missing"
            message = "SKILL.md must start with YAML frontmatter."
        else:
            code = "frontmatter-unclosed"
            message = "SKILL.md YAML frontmatter is not closed on its own line."
        diagnostics.append(
            Diagnostic(
                "error",
                code,
                message,
                str(skill_md),
                path.name,
            )
        )
        package.body = text
        return package, diagnostics

    raw_frontmatter = frontmatter_match.group("yaml")
    package.body = text[frontmatter_match.end() :].lstrip("\r\n")
    try:
        metadata = yaml.safe_load(raw_frontmatter)
    except yaml.YAMLError as exc:
        diagnostics.append(
            Diagnostic(
                "error",
                "frontmatter-invalid",
                f"Invalid YAML frontmatter: {exc}",
                str(skill_md),
                path.name,
            )
        )
        return package, diagnostics

    if not isinstance(metadata, dict):
        diagnostics.append(
            Diagnostic(
                "error",
                "frontmatter-not-object",
                "YAML frontmatter must be a mapping.",
                str(skill_md),
                path.name,
            )
        )
        return package, diagnostics

    package.metadata = metadata
    package.name = metadata.get("name") if isinstance(metadata.get("name"), str) else None
    package.description = (
        metadata.get("description")
        if isinstance(metadata.get("description"), str)
        else None
    )

    routing_path = path / "tests" / "routing.yaml"
    if routing_path.is_file():
        try:
            routing = yaml.safe_load(routing_path.read_text(encoding="utf-8"))
            if isinstance(routing, dict):
                package.routing = routing
            else:
                raise ValueError("routing fixture must be a mapping")
        except (OSError, ValueError, yaml.YAMLError) as exc:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "routing-fixture-invalid",
                    str(exc),
                    str(routing_path),
                    package.label,
                )
            )
    return package, diagnostics


def _check_skill(package: SkillPackage, quality: dict[str, Any]) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    skill_md = package.path / "SKILL.md"
    name = package.name
    description = package.description

    if not name:
        diagnostics.append(
            Diagnostic(
                "error", "name-missing", "Frontmatter name is required.", str(skill_md), package.label
            )
        )
    else:
        if len(name) > 64 or not NAME_RE.fullmatch(name):
            diagnostics.append(
                Diagnostic(
                    "error",
                    "name-invalid",
                    "Name must be 1-64 lowercase letters, digits, and single hyphens.",
                    str(skill_md),
                    package.label,
                )
            )
        if bool(quality.get("require_folder_name_match", False)) and package.path.name != name:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "folder-name-mismatch",
                    f"Folder '{package.path.name}' must match skill name '{name}'.",
                    str(package.path),
                    package.label,
                )
            )

    if not description or not description.strip():
        diagnostics.append(
            Diagnostic(
                "error",
                "description-missing",
                "Frontmatter description is required.",
                str(skill_md),
                package.label,
            )
        )
    else:
        max_description = int(quality.get("description_max_chars", 600))
        if len(description) < 30:
            diagnostics.append(
                Diagnostic(
                    "warning",
                    "description-too-short",
                    "Description is unlikely to provide a discriminating routing contract.",
                    str(skill_md),
                    package.label,
                )
            )
        if len(description) > max_description:
            diagnostics.append(
                Diagnostic(
                    "warning",
                    "description-too-long",
                    f"Description exceeds configured {max_description}-character budget.",
                    str(skill_md),
                    package.label,
                )
            )
        lowered = description.lower()
        if not any(term in lowered for term in ("when ", "use for", "use when", "trigger")):
            diagnostics.append(
                Diagnostic(
                    "warning",
                    "description-trigger-unclear",
                    "Description should state when the skill applies.",
                    str(skill_md),
                    package.label,
                )
            )
        if not any(term in lowered for term in ("do not", "not for", "avoid")):
            diagnostics.append(
                Diagnostic(
                    "warning",
                    "description-boundary-unclear",
                    "Description should include a meaningful boundary when adjacent requests may misroute.",
                    str(skill_md),
                    package.label,
                )
            )

    text = package.body
    for code, pattern in PLACEHOLDER_PATTERNS.items():
        if pattern.search(text):
            severity = "error" if code == "unfinished-placeholder" else "warning"
            diagnostics.append(
                Diagnostic(
                    severity,
                    code,
                    "Remove unfinished scaffold text."
                    if code == "unfinished-placeholder"
                    else "Do not request or expose private reasoning traces; specify observable actions and outputs.",
                    str(skill_md),
                    package.label,
                )
            )
    if OVERCLAIM_RE.search((description or "") + "\n" + text):
        diagnostics.append(
            Diagnostic(
                "warning",
                "overclaim-language",
                "Replace universal or guaranteed language with scoped outcomes and verification criteria.",
                str(skill_md),
                package.label,
            )
        )
    if HOST_TOOL_RE.search(text):
        diagnostics.append(
            Diagnostic(
                "warning",
                "host-specific-tool",
                "Host-specific tool name appears without portable dependency metadata.",
                str(skill_md),
                package.label,
            )
        )

    diagnostics.extend(_check_links(package))
    diagnostics.extend(_check_scripts(package))
    diagnostics.extend(_check_openai_metadata(package))
    diagnostics.extend(_check_legacy_metadata(package, quality))

    require_routing = bool(quality.get("require_routing_tests", False))
    if require_routing and package.routing is None:
        diagnostics.append(
            Diagnostic(
                "error",
                "routing-fixture-missing",
                "Add tests/routing.yaml with positive and negative prompts.",
                str(package.path / "tests" / "routing.yaml"),
                package.label,
            )
        )
    return diagnostics


def _check_links(package: SkillPackage) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for match in MARKDOWN_LINK_RE.finditer(package.body):
        raw_target = match.group(1).strip()
        target = raw_target.split(maxsplit=1)[0].strip("<>")
        if not target or target.startswith(("#", "http://", "https://", "mailto:")):
            continue
        clean = target.split("#", 1)[0]
        resolved = (package.path / clean).resolve()
        try:
            resolved.relative_to(package.path.resolve())
        except ValueError:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "reference-outside-package",
                    f"Relative link escapes the skill package: {raw_target}",
                    str(package.path / "SKILL.md"),
                    package.label,
                )
            )
            continue
        if not resolved.exists():
            diagnostics.append(
                Diagnostic(
                    "error",
                    "reference-missing",
                    f"Referenced resource does not exist: {raw_target}",
                    str(package.path / "SKILL.md"),
                    package.label,
                )
            )
    return diagnostics


def _check_scripts(package: SkillPackage) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    scripts_dir = package.path / "scripts"
    if not scripts_dir.is_dir():
        return diagnostics
    for script in sorted(path for path in scripts_dir.rglob("*") if path.is_file()):
        if not os.access(script, os.X_OK):
            diagnostics.append(
                Diagnostic(
                    "warning",
                    "script-not-executable",
                    "Script resource is not executable.",
                    str(script),
                    package.label,
                )
            )
    return diagnostics


def _check_openai_metadata(package: SkillPackage) -> list[Diagnostic]:
    metadata_path = package.path / "agents" / "openai.yaml"
    if not metadata_path.is_file():
        return []
    diagnostics: list[Diagnostic] = []
    try:
        data = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return [
            Diagnostic(
                "error",
                "openai-metadata-invalid",
                str(exc),
                str(metadata_path),
                package.label,
            )
        ]
    if not isinstance(data, dict):
        return [
            Diagnostic(
                "error",
                "openai-metadata-not-object",
                "agents/openai.yaml must contain a mapping.",
                str(metadata_path),
                package.label,
            )
        ]
    interface = data.get("interface", {})
    if interface and not isinstance(interface, dict):
        diagnostics.append(
            Diagnostic(
                "error",
                "openai-interface-invalid",
                "interface must be a mapping.",
                str(metadata_path),
                package.label,
            )
        )
        return diagnostics
    if isinstance(interface, dict):
        short = interface.get("short_description")
        if short is not None and (not isinstance(short, str) or not 25 <= len(short) <= 64):
            diagnostics.append(
                Diagnostic(
                    "error",
                    "openai-short-description-invalid",
                    "short_description must contain 25-64 characters.",
                    str(metadata_path),
                    package.label,
                )
            )
        prompt = interface.get("default_prompt")
        if prompt is not None and (
            not isinstance(prompt, str) or f"${package.label}" not in prompt
        ):
            diagnostics.append(
                Diagnostic(
                    "error",
                    "openai-default-prompt-invalid",
                    f"default_prompt must mention ${package.label}.",
                    str(metadata_path),
                    package.label,
                )
            )
    policy = data.get("policy", {})
    if policy and not isinstance(policy, dict):
        diagnostics.append(
            Diagnostic(
                "error",
                "openai-policy-invalid",
                "policy must be a mapping.",
                str(metadata_path),
                package.label,
            )
        )
    elif isinstance(policy, dict) and "allow_implicit_invocation" in policy:
        if not isinstance(policy["allow_implicit_invocation"], bool):
            diagnostics.append(
                Diagnostic(
                    "error",
                    "openai-policy-implicit-invalid",
                    "allow_implicit_invocation must be true or false.",
                    str(metadata_path),
                    package.label,
                )
            )
    if package.routing is not None and isinstance(policy, dict):
        fixture_explicit = package.routing.get("explicit_only", False)
        declared_implicit = policy.get("allow_implicit_invocation", True)
        if isinstance(fixture_explicit, bool) and isinstance(declared_implicit, bool):
            if fixture_explicit == declared_implicit:
                diagnostics.append(
                    Diagnostic(
                        "error",
                        "invocation-policy-drift",
                        "routing explicit_only disagrees with agents/openai.yaml invocation policy.",
                        str(metadata_path),
                        package.label,
                    )
                )
    return diagnostics


def _check_legacy_metadata(
    package: SkillPackage, quality: dict[str, Any]
) -> list[Diagnostic]:
    if not bool(quality.get("check_legacy_metadata", False)):
        return []
    legacy_path = package.path / "gemini-extension.json"
    if not legacy_path.is_file():
        return []
    try:
        data = json.loads(legacy_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [
            Diagnostic(
                "error",
                "legacy-metadata-invalid",
                str(exc),
                str(legacy_path),
                package.label,
            )
        ]
    diagnostics: list[Diagnostic] = []
    if data.get("name") != package.name:
        diagnostics.append(
            Diagnostic(
                "error",
                "legacy-name-drift",
                "Legacy manifest name differs from SKILL.md.",
                str(legacy_path),
                package.label,
            )
        )
    if data.get("description") != package.description:
        diagnostics.append(
            Diagnostic(
                "error",
                "legacy-description-drift",
                "Legacy manifest description differs from SKILL.md.",
                str(legacy_path),
                package.label,
            )
        )
    return diagnostics


def _check_portfolio(packages: list[SkillPackage]) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    names: dict[str, list[SkillPackage]] = {}
    for package in packages:
        if package.name:
            names.setdefault(package.name, []).append(package)
    for name, matches in names.items():
        if len(matches) > 1:
            for package in matches:
                diagnostics.append(
                    Diagnostic(
                        "error",
                        "duplicate-skill-name",
                        f"Skill name '{name}' occurs {len(matches)} times.",
                        str(package.path),
                        package.label,
                    )
                )

    threshold = 0.72
    for index, left in enumerate(packages):
        for right in packages[index + 1 :]:
            left_tokens = _tokens(left.description or "")
            right_tokens = _tokens(right.description or "")
            if not left_tokens or not right_tokens:
                continue
            similarity = len(left_tokens & right_tokens) / len(left_tokens | right_tokens)
            if similarity >= threshold:
                diagnostics.append(
                    Diagnostic(
                        "warning",
                        "description-overlap",
                        f"Description overlaps {right.label} ({similarity:.0%} token similarity).",
                        str(left.path / "SKILL.md"),
                        left.label,
                    )
                )
    return diagnostics


def _check_routing(
    packages: list[SkillPackage], quality: dict[str, Any]
) -> tuple[list[Diagnostic], list[RoutingCase]]:
    diagnostics: list[Diagnostic] = []
    cases: list[RoutingCase] = []
    min_margin = float(quality.get("routing_min_margin", 0.02))

    profiles = {
        package.label: _routing_profile(package)
        for package in packages
        if package.description
        and not bool((package.routing or {}).get("explicit_only", False))
    }
    prompts_seen: dict[str, str] = {}

    for package in packages:
        if package.routing is None:
            continue
        routing_path = package.path / "tests" / "routing.yaml"
        positive = package.routing.get("positive", [])
        negative = package.routing.get("negative", [])
        explicit_only = package.routing.get("explicit_only", False)
        if not isinstance(explicit_only, bool):
            diagnostics.append(
                Diagnostic(
                    "error",
                    "routing-explicit-only-invalid",
                    "explicit_only must be true or false.",
                    str(routing_path),
                    package.label,
                )
            )
            explicit_only = False
        for kind, prompts in (("positive", positive), ("negative", negative)):
            if not isinstance(prompts, list) or not all(isinstance(item, str) for item in prompts):
                diagnostics.append(
                    Diagnostic(
                        "error",
                        f"routing-{kind}-invalid",
                        f"{kind} must be a list of prompt strings.",
                        str(routing_path),
                        package.label,
                    )
                )
                continue
            if len(prompts) < 2:
                diagnostics.append(
                    Diagnostic(
                        "warning",
                        f"routing-{kind}-sparse",
                        f"Provide at least two {kind} routing prompts.",
                        str(routing_path),
                        package.label,
                    )
                )
            for prompt in prompts:
                normalized = " ".join(prompt.lower().split())
                if normalized in prompts_seen:
                    diagnostics.append(
                        Diagnostic(
                            "error",
                            "routing-prompt-duplicate",
                            f"Prompt duplicates a fixture in {prompts_seen[normalized]}.",
                            str(routing_path),
                            package.label,
                        )
                    )
                else:
                    prompts_seen[normalized] = package.label

                ranked = sorted(
                    (
                        (_routing_score(prompt, profile), label)
                        for label, profile in profiles.items()
                    ),
                    reverse=True,
                )
                predicted = ranked[0][1] if ranked and ranked[0][0] > 0 else None
                top_score = ranked[0][0] if ranked else 0.0
                second_score = ranked[1][0] if len(ranked) > 1 else 0.0
                margin = top_score - second_score
                if kind == "positive":
                    passed = bool(explicit_only or (predicted == package.label and margin >= min_margin))
                    expected = package.label if not explicit_only else None
                else:
                    own_score = next(
                        (score for score, label in ranked if label == package.label), 0.0
                    )
                    passed = bool(explicit_only or predicted != package.label or own_score <= 0)
                    expected = None
                case = RoutingCase(
                    package.label,
                    kind,
                    prompt,
                    predicted,
                    expected,
                    round(margin, 4),
                    passed,
                )
                cases.append(case)
                if not passed:
                    diagnostics.append(
                        Diagnostic(
                            "warning",
                            "routing-smoke-failed",
                            f"Offline {kind} prompt routed to {predicted or 'none'}; review description boundaries. This heuristic is not a model eval.",
                            str(routing_path),
                            package.label,
                        )
                    )
    return diagnostics, cases


def _routing_profile(package: SkillPackage) -> tuple[set[str], set[str], set[str]]:
    description = package.description or ""
    sentences = re.split(r"(?<=[.!?])\s+", description)
    positive_parts: list[str] = []
    negative_parts: list[str] = []
    for sentence in sentences:
        lowered = sentence.lower()
        if any(marker in lowered for marker in ("do not", "not for", "avoid")):
            negative_parts.append(sentence)
        else:
            positive_parts.append(sentence)
    return (
        _tokens(" ".join(positive_parts)),
        _tokens(" ".join(negative_parts)),
        _tokens(package.name or ""),
    )


def _routing_score(prompt: str, profile: tuple[set[str], set[str], set[str]]) -> float:
    positive, negative, name_tokens = profile
    prompt_tokens = _tokens(prompt)
    if not prompt_tokens or not positive:
        return 0.0
    positive_overlap = prompt_tokens & positive
    negative_overlap = prompt_tokens & negative
    weighted = len(positive_overlap) + 2 * len(prompt_tokens & name_tokens)
    penalty = 1.25 * len(negative_overlap)
    return (weighted - penalty) / math.sqrt(len(prompt_tokens) * len(positive))


def _tokens(text: str) -> set[str]:
    return {
        _normalize_token(token)
        for token in TOKEN_RE.findall(text.lower())
        if token not in STOPWORDS
    }


def _normalize_token(token: str) -> str:
    # Small, deterministic normalization for routing smoke tests. This is
    # intentionally not presented as semantic or model-equivalent routing.
    if len(token) > 5 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 4 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def _count_files(path: Path) -> int:
    if not path.is_dir():
        return 0
    return sum(item.is_file() for item in path.rglob("*"))


def diagnostics_by_severity(
    diagnostics: Iterable[Diagnostic], severity: str
) -> list[Diagnostic]:
    return [item for item in diagnostics if item.severity == severity]
