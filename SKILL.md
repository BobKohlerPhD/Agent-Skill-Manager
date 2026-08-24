---
name: agent-skill-manager
description: Audit an Agent Skills repository when structural quality, metadata drift, portfolio collisions, resource integrity, or routing fixtures need deterministic verification. Do not use to create, install, link, enable, or package skills.
---

# Agent Skill Manager

Use this repository's read-only CLI as a quality gate for a collection of Agent Skills.

## Workflow

1. Locate the separate skills repository root containing `asm-config.json` and `skills/`.
2. Run `asm --root /path/to/skills-repository audit`. Add `--strict` when repository policy treats warnings as failures.
3. Read diagnostics by severity, code, skill, and path.
4. Inspect `asm --root /path/to/skills-repository routing` when a description or routing fixture changes.
5. Make only user-requested repairs, then rerun the strict audit and relevant tests.

Do not use this manager for operations already owned by the host runtime, including skill creation, installation, local discovery, invocation, or plugin packaging. Its purpose is deterministic repository-wide verification.
