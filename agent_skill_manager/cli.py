from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from . import __version__
from .quality import AuditResult, audit_repository


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="asm",
        description=(
            "Audit an Agent Skills repository for structural quality, metadata drift, "
            "portfolio collisions, and routing-fixture regressions."
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository root (default: current directory).",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("check", "Run all structural, semantic, portfolio, and routing checks."),
        ("audit", "Alias for check; intended for CI and review workflows."),
        ("status", "Print a compact repository quality summary."),
        ("inventory", "List skill packages and optional resources."),
        ("routing", "Run offline description-routing smoke tests."),
    ):
        command = subparsers.add_parser(name, help=help_text)
        command.add_argument(
            "--format",
            choices=("text", "json"),
            default="text",
            help="Output format.",
        )
        command.add_argument(
            "--strict",
            action="store_true",
            help="Treat warnings as a failing exit status.",
        )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = audit_repository(args.root, include_routing=True)

    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    elif args.command == "inventory":
        _print_inventory(result)
    elif args.command == "routing":
        _print_routing(result)
    elif args.command == "status":
        _print_status(result)
    else:
        _print_check(result)
    return result.exit_code(strict=args.strict)


def _print_check(result: AuditResult) -> None:
    for item in result.diagnostics:
        label = item.skill or "repository"
        print(f"{item.severity.upper():7} {item.code:32} {label}: {item.message}")
        print(f"        {item.path}")
    _print_status(result)


def _print_status(result: AuditResult) -> None:
    routing_failures = sum(not case.passed for case in result.routing_cases)
    print(
        f"Skills: {len(result.skills)} | Errors: {result.errors} | "
        f"Warnings: {result.warnings} | Routing failures: {routing_failures}"
    )


def _print_inventory(result: AuditResult) -> None:
    print(
        f"{'SKILL':32} {'ROUTING':>9} {'SCRIPTS':>8} {'REFS':>5} "
        f"{'ASSETS':>7} {'OPENAI':>7} {'LEGACY':>7}"
    )
    for skill in result.skills:
        item = skill.to_inventory()
        routing = f"{item['routing_positive']}/{item['routing_negative']}"
        print(
            f"{skill.label:32} {routing:>9} {item['scripts']:>8} "
            f"{item['references']:>5} {item['assets']:>7} "
            f"{_yes_no(item['has_openai_metadata']):>7} "
            f"{_yes_no(item['has_legacy_gemini_metadata']):>7}"
        )
    _print_status(result)


def _print_routing(result: AuditResult) -> None:
    for case in result.routing_cases:
        outcome = "PASS" if case.passed else "WARN"
        print(
            f"{outcome:4} {case.skill:32} {case.kind:8} "
            f"predicted={case.predicted or 'none'} margin={case.margin:.3f}"
        )
        print(f"     {case.prompt}")
    _print_status(result)


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


if __name__ == "__main__":
    sys.exit(main())
