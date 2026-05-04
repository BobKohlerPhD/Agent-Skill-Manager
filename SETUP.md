# Setup

Getting started with the Agent Skill Manager.

## Initial Configuration

The tool uses `asm-config.json` to manage storage paths. You can generate a default configuration file with the following command:

```bash
cat <<EOF > asm-config.json
{
  "system_skill_dirs": [
    "~/.gemini/extensions",
    "~/.agents/skills"
  ],
  "required_md_headers": [
    "Context / scope of the new skill",
    "Instructions",
    "Technical Crap",
    "Examples"
  ]
}
EOF
```

*Note: Update the paths in the `"system_skill_dirs"` array to match your local Gemini CLI or Antigravity skill directories.*

## Verifying the environment

Run the status check to verify the environment and identified paths:

```bash
./generate-skill.sh status
```

This will report the status of all current skills and indicate if any are `[MISSING]` or `[BLOCKING]` in your environment.

## Syncing skills

To link the repository skills to your system directories, run:

```bash
./generate-skill.sh link
```

The script will validate each skill and create the necessary symlinks.

## Troubleshooting

- **Conflict Errors**: Ensure you do not have overlapping directories in your `system_skill_dirs`. Redundant paths may cause Gemini CLI to report duplicate skill conflicts.
- **Permission Denied**: Ensure the user running the script has read and write access to the directories defined in `asm-config.json`.
- **Validation Errors**: If a skill is listed as `[INVALID]`, check that your `SKILL.md` contains the headers defined in `asm-config.json` and that your `gemini-extension.json` is valid.
