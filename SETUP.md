# Development setup

Agent Skill Manager performs read-only repository checks. It does not require or modify any agent runtime installation directory.

## Local environment

Use Python 3.11 or newer:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --editable .
```

Run the manager tests:

```bash
python3 -m unittest discover -s tests -v
```

Audit the separate skills repository:

```bash
asm --root ../Agent-Skills audit
```

Without installing the console entry point, run:

```bash
./asm --root ../Agent-Skills audit
```

## Repository separation

Do not add real skills to this repository. The root `skills/` directory is ignored so local copies cannot accidentally be committed here.

Place `asm-config.json` in the skills repository when its layout or policy differs from the defaults. Copy `asm-config.example.json` from this repository as a starting point.

The manager will not create missing manifests or rewrite a skill during validation. Diagnostics identify the exact package, path, and rule so repairs remain intentional and reviewable.
