# Agent Skill Manager

This repo used to be a symlink manager. Keeping skills linked between different agents and workstations was getting annoying, so the original shell script tried to make the path crap less painful.

That is not really the problem anymore. Current agent runtimes already do a decent job of finding, installing, and invoking skills. Codex has a built-in skill creator and installer, supports repository and user skill locations, and uses plugins for distribution. The [official OpenAI skill documentation](https://learn.chatgpt.com/docs/build-skills) covers that side of things.

The problem I still have is figuring out whether a growing folder of skills is actually in good shape before I commit or publish it.

So Agent Skill Manager is now a read-only audit tool. It looks through the whole skill repository, points out suspicious or broken bits, and leaves the actual files alone.

The skills themselves do not live in this repository anymore. I keep them in a separate skills repo so there is only one version of each skill to maintain. The root `skills/` directory is ignored here on purpose.

## What it is useful for

LLMs are already quite capable of drafting or revising one skill. I do not need another wrapper pretending to do that better.

What is still useful is a boring, repeatable check that does not depend on which model happens to review the repo that day. The manager currently checks for things like:

- Invalid or incomplete `SKILL.md` frontmatter
- Duplicate skill names
- Folder and skill-name mismatches, when I choose to enforce them
- Vague descriptions that may trigger at the wrong time
- Overlapping skill descriptions
- Old scaffold text, private-reasoning examples, and unsupported guarantees
- Host-specific tool names that make a skill less portable
- Broken or package-escaping resource links
- Scripts that are present but not executable
- Drift between `SKILL.md` and older manifests, when that check is enabled
- Problems in optional `agents/openai.yaml` metadata
- Obvious routing regressions using optional positive and negative prompts

This is not a model evaluator, and the routing check does not reproduce an LLM's semantic router. It is just a cheap offline smoke test that can catch obvious description drift.

## What it deliberately does not do

The manager does not:

- Create skills
- Install skills
- Link skills into agent directories
- Enable or disable skills
- Rewrite an existing skill to make a warning go away
- Package skills as plugins

Those jobs either belong to the agent runtime or should remain an intentional editing decision.

## Quick start

Python 3.11 or newer is required.

Point the installed command at the separate skills repository:

```bash
asm --root ../Agent-Skills audit
```

To install the `asm` command from this repository:

```bash
python3 -m pip install --editable .
asm --root ../Agent-Skills audit
```

Without installing it:

```bash
./asm --root ../Agent-Skills audit
```

The audit is read-only. Errors return a failing exit code. Warnings are reported without failing unless `--strict` is used.

## Commands

### Check everything

```bash
asm --root ../Agent-Skills check
asm --root ../Agent-Skills audit
asm --root ../Agent-Skills audit --strict
```

`check` and `audit` currently run the same checks. I kept `audit` because it reads more naturally in CI.

### Get the short version

```bash
asm --root ../Agent-Skills status
```

### See what is in the repo

```bash
asm --root ../Agent-Skills inventory
```

This lists each skill and whether it has scripts, references, assets, routing fixtures, OpenAI metadata, or an older manifest.

### Run routing smoke tests

```bash
asm --root ../Agent-Skills routing
```

Routing tests are optional. If a skill has `tests/routing.yaml`, the manager checks its positive and negative examples against the rest of the repository.

### Get JSON for another tool

```bash
asm --root ../Agent-Skills audit --format json
```

## Configuration

Repository settings live in `asm-config.json` inside the skills repository being audited. If that file is missing, the manager looks for a `skills/` directory and uses its default checks.

This manager repo includes [`asm-config.example.json`](asm-config.example.json) as a starting point:

```json
{
  "schema_version": 2,
  "skills_dir": "skills",
  "quality": {
    "require_folder_name_match": false,
    "require_routing_tests": false,
    "description_max_chars": 600,
    "routing_min_margin": 0.02,
    "check_legacy_metadata": false
  }
}
```

The stricter checks are optional on purpose. I do not want the manager silently changing older skills or making the tool unusable until I review those skills against their actual source projects.

When the repository is ready, I can turn on folder-name enforcement, require routing fixtures, check legacy manifests for drift, or run the whole audit with `--strict`.

## Optional routing fixtures

A routing fixture looks like this:

```yaml
explicit_only: false
positive:
  - "Tailor my resume to this job description without inventing qualifications."
  - "Create an ATS-readable revision of my existing resume for this target role."
negative:
  - "Help me prepare for a behavioral interview."
  - "Give me salary negotiation advice."
```

Positive prompts should sound like realistic requests for that skill. Negative prompts should be close enough to be informative instead of random unrelated text.

## Expected layout in the separate skills repo

```text
skills/example-skill/
├── SKILL.md
├── agents/
│   └── openai.yaml       optional
├── references/           optional
├── scripts/              optional
├── assets/               optional
└── tests/
    └── routing.yaml      optional manager fixture
```

`SKILL.md` stays the canonical skill definition. The manager does not add another required manifest.

## CI

The included GitHub Actions workflow installs the manager, runs its unit tests, and verifies the installed command. It does not audit private or separately maintained skills.

The skills repository can run its own `asm --root . audit` or `asm --root . audit --strict` workflow when I want repository-specific quality checks there.
