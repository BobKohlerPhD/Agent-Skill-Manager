# Agent Skill Manager

Making sure skills were linked between my two workstations and accessible by both a CLI and google's Antigravity was getting very tiring when I started amounting too many custom skills. This is an attempt at cleaning up the process a bit. As far as I am aware, the gemini-cli has a skill builder but does not have robust linking and management capabilities. However, depending on how you initially setup different tools, you may already have a nice linked structure making this not very necessary. 

There are some automated checks to ensure the files are formatted correctly and a config file makes the path crap more intuitive.

## Using Config File (`asm-config.json`)

Instead of hardcoding the paths for the CLI and AG, you can now just change them in `asm-config.json` instead of editing things manually. It supports `~` expansion now too, so it should work on whatever machine you're currently using without complaining.

**Things you can change in the .json:**
*   `cli_ext_dir`: Where you want the CLI skills (or extensions in AG)  to be.
*   `gui_skills_dir`: Where Antigravity will look for skills.
*   `required_md_headers`: The headers that *must* be in your `SKILL.md` or the script will not work properly.

## Skill Checks

To keep things from breaking, the script checks your skills when you try to link or check the status.

*   **JSON Check**: Makes sure your `gemini-extension.json` is actually a valid JSON file.
*   **Header Check**: Looks at `SKILL.md` for the headers you defined in the config to make sure they are "complete".
*   **Broken Skills**: The script will skip skills that are 'broken' during a sync.

## Quick skill generation (skills should be well-thought out and robust though)

If you just run the `create` command with no arguments, then it will ask you for the Name and Description. It's a lot faster than trying to remember the syntax every time.

```bash
./generate-skill.sh create
```

Or you can just have at the whole dang thing:
```bash
./generate-skill.sh create "My Skill" "A quick description"
```

## Is your skill getting sick on you?

The `status` command gives a full report on all skills in the repo and if it's working in both the CLI and AG. This should also track **external** skills / extensions that are 'installed' or implemented, so you can see exactly whats loaded and working in your current environment. 

```bash
./generate-skill.sh status
```

**What the status labels mean:**
*   **[OK]**: Validation passed.
*   **[INVALID]**: Something is wrong with the skill files (check the JSON or headers).
*   **[LINKED]**: The symlink is alive and pointing exactly where it should.
*   **[MISSING]**: The skill exists here but isn't linked in that environment yet.
*   **[MISMATCH]**: A link exists but it's pointing to some other folder.
*   **[BLOCKING]**: There's a real folder in your system extension directory that is blocking the link. You should probably delete it and link again.
*   **[DIR] / [LINK]**: Found in the "External" section—these are skills/extensions managed outside of this script.

## Syncing skills
```bash
./generate-skill.sh link
```

It'll only link the skills that pass the checks. It's smart enough to not overwrite real directories or mess up existing valid links.

## How everything is organized

Fairly simply organization structure:
*   **`generate-skill.sh`**: The script that does all the heavy lifting.
*   **`asm-config.json`**: Where you store your paths and settings.
*   **`skills/`**: This is where all your skill folders live. Each one has:
    *   `gemini-extension.json`: The technical info the CLI needs.
    *   `SKILL.md`: The actual instructions and examples for the agent.
