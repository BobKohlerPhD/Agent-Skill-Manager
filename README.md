# Agent Skill Manager

This repo used to be a symlink manager. Keeping skills linked between different agents and workstations was getting annoying, so the original shell script tried to make the path crap less painful.  That isn't really a problem anymore as agents already do a decent job of finding, installing, and invoking skills. Codex has a built-in skill creator and installer, supports repository and user skill locations, and uses plugins for distribution. The problem I still had/have is figuring out whether a growing folder of skills is actually in good shape before I commit or publish it so now this is a read-only audit tool. It looks through the whole skill repository, but leaves the actual files alone.

## What it is useful for


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


## To use


```bash
asm --root ../Agent-Skills audit
```

```bash
python3 -m pip install --editable .
asm --root ../Agent-Skills audit
```

Without installing:

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

### short version

```bash
asm --root ../Agent-Skills status
```

### See what there is

```bash
asm --root ../Agent-Skills inventory
```

This lists each skill and whether it has scripts, references, assets, routing fixtures, OpenAI metadata, or an older manifest.

### routing
```bash
asm --root ../Agent-Skills routing
```

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

Positive prompts should sound like realistic requests for a skill while Negative prompts should be close enough to provide addtional info. 

## Expected layout

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
