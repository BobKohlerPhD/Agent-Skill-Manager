from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent_skill_manager.quality import audit_repository


class QualityAuditTests(unittest.TestCase):
    def make_repo(
        self,
        *,
        folder: str = "sample-skill",
        name: str = "sample-skill",
        description: str | None = None,
        body: str = "# Sample\n\nFollow the requested sample workflow.\n",
    ) -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        (root / "asm-config.json").write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "skills_dir": "skills",
                    "quality": {
                        "require_folder_name_match": True,
                        "require_routing_tests": False,
                        "check_legacy_metadata": True,
                    },
                }
            ),
            encoding="utf-8",
        )
        skill_dir = root / "skills" / folder
        skill_dir.mkdir(parents=True)
        description = description or (
            "Run a sample repository workflow when its deterministic check is requested. "
            "Do not use for unrelated work."
        )
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: {description}\n---\n\n{body}",
            encoding="utf-8",
        )
        return root

    def codes(self, root: Path) -> set[str]:
        return {item.code for item in audit_repository(root).diagnostics}

    def test_valid_minimal_skill_passes(self) -> None:
        root = self.make_repo()
        result = audit_repository(root)
        self.assertEqual(result.errors, 0)
        self.assertEqual(result.warnings, 0)

    def test_folder_must_match_name(self) -> None:
        root = self.make_repo(folder="wrong-folder")
        self.assertIn("folder-name-mismatch", self.codes(root))

    def test_folder_name_check_can_be_disabled_for_legacy_repositories(self) -> None:
        root = self.make_repo(folder="wrong-folder")
        (root / "asm-config.json").write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "skills_dir": "skills",
                    "quality": {
                        "require_folder_name_match": False,
                        "require_routing_tests": False,
                    },
                }
            ),
            encoding="utf-8",
        )
        self.assertNotIn("folder-name-mismatch", self.codes(root))

    def test_missing_relative_reference_is_an_error(self) -> None:
        root = self.make_repo(
            body="# Sample\n\nRead [the policy](references/policy.md).\n"
        )
        self.assertIn("reference-missing", self.codes(root))

    def test_reasoning_trace_is_reported(self) -> None:
        root = self.make_repo(body="# Sample\n\nAgent Thought (CoT): hidden reasoning\n")
        self.assertIn("reasoning-trace", self.codes(root))

    def test_legacy_metadata_drift_is_an_error(self) -> None:
        root = self.make_repo()
        manifest = root / "skills" / "sample-skill" / "gemini-extension.json"
        manifest.write_text(
            json.dumps(
                {
                    "name": "different-name",
                    "description": "different description",
                    "main": "SKILL.md",
                }
            ),
            encoding="utf-8",
        )
        codes = self.codes(root)
        self.assertIn("legacy-name-drift", codes)
        self.assertIn("legacy-description-drift", codes)

    def test_invocation_policy_must_match_routing_fixture(self) -> None:
        root = self.make_repo()
        skill = root / "skills" / "sample-skill"
        (skill / "agents").mkdir()
        (skill / "tests").mkdir()
        (skill / "agents" / "openai.yaml").write_text(
            "policy:\n  allow_implicit_invocation: true\n", encoding="utf-8"
        )
        (skill / "tests" / "routing.yaml").write_text(
            "explicit_only: true\npositive: []\nnegative: []\n", encoding="utf-8"
        )
        self.assertIn("invocation-policy-drift", self.codes(root))

    def test_skills_directory_cannot_escape_repository(self) -> None:
        root = self.make_repo()
        (root / "asm-config.json").write_text(
            json.dumps({"schema_version": 2, "skills_dir": "../skills"}),
            encoding="utf-8",
        )
        self.assertIn("config-skills-dir-outside-root", self.codes(root))

    def test_invalid_quality_value_is_a_diagnostic_not_a_traceback(self) -> None:
        root = self.make_repo()
        (root / "asm-config.json").write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "skills_dir": "skills",
                    "quality": {"routing_min_margin": "high"},
                }
            ),
            encoding="utf-8",
        )
        self.assertIn("config-routing-margin-invalid", self.codes(root))

if __name__ == "__main__":
    unittest.main()
