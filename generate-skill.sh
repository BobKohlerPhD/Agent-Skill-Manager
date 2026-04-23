#!/bin/bash

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$REPO_ROOT/asm-config.json"
REPO_SKILLS_DIR="$REPO_ROOT/skills"

# Default Paths (will be overridden by config if present)
CLI_EXT_DIR="$HOME/.gemini/extensions"
GUI_SKILLS_DIR="$HOME/.gemini/antigravity/skills"

# Load Configuration
load_config() {
    if [ -f "$CONFIG_FILE" ]; then
        # /usr/bin/python3
        CLI_EXT_DIR_CONFIG=$(/usr/bin/python3 -c "import json, sys; print(json.load(open('$CONFIG_FILE')).get('cli_ext_dir', '$CLI_EXT_DIR'))" 2>/dev/null)
        GUI_SKILLS_DIR_CONFIG=$(/usr/bin/python3 -c "import json, sys; print(json.load(open('$CONFIG_FILE')).get('gui_skills_dir', '$GUI_SKILLS_DIR'))" 2>/dev/null)
        
    
        CLI_EXT_DIR="${CLI_EXT_DIR_CONFIG/#\~/$HOME}"
        GUI_SKILLS_DIR="${GUI_SKILLS_DIR_CONFIG/#\~/$HOME}"
    fi

    # Ensure paths are not empty or root
    if [[ -z "$CLI_EXT_DIR" || "$CLI_EXT_DIR" == "/" ]]; then
        CLI_EXT_DIR="$HOME/.gemini/extensions"
    fi
    if [[ -z "$GUI_SKILLS_DIR" || "$GUI_SKILLS_DIR" == "/" ]]; then
        GUI_SKILLS_DIR="$HOME/.gemini/antigravity/skills"
    fi
}

usage() {
    echo "Usage: $(basename "$0") {create|link|status} [args]"
    echo ""
    echo "Commands:"
    echo "  create [name] [desc]  Initialize a new skill (interactive if args missing)."
    echo "  link                  Synchronize repository skills with system directories."
    echo "  status                Perform health diagnostics on the current environment."
    exit 1
}

# Validation Module
validate_skill() {
    local target_dir=$1
    local skill_id=$(basename "$target_dir")
    local success=true

    # Make sure the json is actually a json 
    if [ -f "$target_dir/gemini-extension.json" ]; then
        /usr/bin/python3 -m json.tool "$target_dir/gemini-extension.json" > /dev/null 2>&1
        if [ $? -ne 0 ]; then
            echo "[ERROR] Invalid JSON syntax in $skill_id/gemini-extension.json"
            success=false
        fi
    else
        echo "[ERROR] Missing gemini-extension.json in $skill_id"
        success=false
    fi

    # Check for skill headers 
    if [ -f "$target_dir/SKILL.md" ]; then
        if [ -f "$CONFIG_FILE" ]; then
            local headers=$(/usr/bin/python3 -c "import json; print(' '.join(json.load(open('$CONFIG_FILE')).get('required_md_headers', [])))")
            for header in $headers; do
                grep -q "## $header" "$target_dir/SKILL.md"
                if [ $? -ne 0 ]; then
                    echo "[WARNING] Missing header '## $header' in $skill_id/SKILL.md"
                fi
            done
        fi
    else
        echo "[ERROR (sorry)] THERE IS NO SKILL.md in $skill_id"
        success=false
    fi

    [[ "$success" == "true" ]] && return 0 || return 1
}

# Create new skill 
create_skill() {
    local NAME=$1
    local DESC=$2

    if [ -z "$NAME" ]; then
        echo -n "Enter Skill Name: "
        read NAME
    fi
    if [ -z "$DESC" ]; then
        echo -n "Enter Skill Description: "
        read DESC
    fi

    local ID=$(echo "$NAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
    local TARGET="$REPO_SKILLS_DIR/$ID"

    if [ -d "$TARGET" ]; then
        echo "[OOPS] Skill '$ID' already exists."
        exit 1
    fi

    mkdir -p "$TARGET"

    # EOF editing , i hate nano so much 
    cat <<EOF > "$TARGET/gemini-extension.json"
{
  "name": "$ID",
  "version": "1.0.0",
  "description": "$DESC",
  "main": "SKILL.md"
}
EOF

    cat <<EOF > "$TARGET/SKILL.md"
---
name: $ID
description: $DESC
---
# Skill: $NAME

## Context / scope of the new skill
[Describe the domain of application]

## Instructions
1. [Operational step 1]
2. [Operational step 2]

## Technical Crap 
[Documentation of dependencies and system requirements]

## Examples
[Provide input/output pairs for validation]
EOF

    echo "[SUCCESS] Template for '$ID' created in $TARGET"
}

# Environment Synchronization
link_skills() {
    echo "Starting synchronization..."
    mkdir -p "$CLI_EXT_DIR"
    mkdir -p "$GUI_SKILLS_DIR"

    for skill_path in "$REPO_SKILLS_DIR"/*; do
        if [ -d "$skill_path" ]; then
            local skill_id=$(basename "$skill_path")
            
            if validate_skill "$skill_path"; then
                ln -sf "$skill_path" "$CLI_EXT_DIR/$skill_id"
                ln -sf "$skill_path" "$GUI_SKILLS_DIR/$skill_id"
                echo "[LINKED] $skill_id"
            else
                echo "[SKIPPED] $skill_id due to validation errors."
            fi
        fi
    done
    echo "Synchronization complete."
}

# Check 'health' of skill [could be dying a slow death :(]
check_status() {
    echo "--- System Health Report ---"
    echo "CLI Directory: $CLI_EXT_DIR"
    echo "GUI Directory: $GUI_SKILLS_DIR"
    echo ""

    echo "Repository Status:"
    local skill_count=0
    for skill in "$REPO_SKILLS_DIR"/*; do
        if [ -d "$skill" ]; then
            ((skill_count++))
            local sid=$(basename "$skill")
            if validate_skill "$skill" > /dev/null; then
                echo "  [OK] $sid"
            else
                echo "  [!!] $sid (Validation Failed)"
            fi
        fi
    done
    echo "Total Skills in Repo: $skill_count"
    echo ""

    echo "Environment Status (CLI):"
    for link in "$CLI_EXT_DIR"/*; do
        if [ -L "$link" ]; then
            if [ ! -e "$link" ]; then
                echo "  [SKILL-GONE] $(basename "$link") (Target missing)"
            fi
        elif [ -e "$link" ]; then
            echo "  [GHOST-BLOCKING] $(basename "$link") (Real directory exists, blocking link)"
        fi
    done
}

# Main
load_config

case "$1" in
    create)
        create_skill "$2" "$3"
        ;;
    link)
        link_skills
        ;;
    status)
        check_status
        ;;
    *)
        usage
        ;;
esac