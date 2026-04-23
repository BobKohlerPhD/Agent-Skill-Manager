# Agent Skill Manager

Making sure skills were linked between my two workstations and accessible by both a CLI and google's Antigravity was getting very tiring so I made an attempt at cleaning up the process a bit. As far as I am aware, the gemini-cli has a skill builder but does not have robust linking and management capabilities.

**My plan is to integrate this with the IMDA project (see repo) in some way but I have not thought of how yet..**

There are some automated checks to ensure the files are formatted correctly and a config file makes the path crap more intuitive. 

## Using Config File (`asm-config.json`)

Instead of hardcoding the paths for the CLI and AG, you can now just change them in `asm-config.json` instead of editing things manually. 

**Things you can change in the .json:**
*   `cli_ext_dir`: Where you want the CLI skills (or extensions in AG)  to be.
*   `gui_skills_dir`: Where Antigravity will look for skills.
*   `required_md_headers`: The headers that *must* be in your `SKILL.md` or the script will not work properly.

## Skill Checks (Validation)

To keep things from breaking, the script now checks your work when you try to link or check status.

*   **JSON Check**: Makes sure your `gemini-extension.json` is actually a valid JSON file
*   **Header Check**: Looks at `SKILL.md` for sections like "Instructions" or "Examples" to make sure they are "complete".
*   **Broken Skills**: The script will skip skills that are 'broken'.

## Quick skill generation (skills should be well-thought out and robust though)

If you just run the `create` command with no arguments, then it will  ask you for the Name and Description. It's a lot faster than trying to remember the syntax every time.

```bash
./generate-skill.sh create
```

Or you can just have at the whole dang thing:
```bash
./generate-skill.sh create "My Skill" "A quick description"
```

## Is your skill getting sick on you?

Use `status` command for checks to make sure the links are actually working.

```bash
./generate-skill.sh status
```

**Status icons:**
*   **[OK]**: Everything is fine.
*   **[!!]**: Something is wrong with the skill files (check the JSON or headers).
*   **[SKILL-GONE]**: You have a link in your system folder but the actual skill folder in the repo is gone.
*   **[GHOST-BLOCKING]**: There's a real folder in your system extension directory that is blocking the link. You should probably delete it and link again.

## Syncing skills
```bash
./generate-skill.sh link
```

It'll only link the skills that pass the checks.

## How everything is organized

Fairly simply organization structure:
*   **`generate-skill.sh`**: The script that does all the heavy lifting.
*   **`asm-config.json`**: Where you store your paths and settings.
*   **`skills/`**: This is where all your skill folders live. Each one has:
    *   `gemini-extension.json`: The technical info the CLI needs.
    *   `SKILL.md`: The actual instructions and examples for the agent.
