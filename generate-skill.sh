#!/bin/bash
shopt -s nullglob

resolve_path() {
    python3 -c "import os, sys; print(os.path.realpath(sys.argv[1]))" "$1"
}

expand_tilde() {
    case "$1" in
        "~/"*) echo "${1/#\~/$HOME}" ;;
        "~") echo "$HOME" ;;
        *) echo "$1" ;;
    esac
}

REPO_ROOT=$(resolve_path "$(dirname "${BASH_SOURCE[0]}")")
CONFIG_FILE="$REPO_ROOT/asm-config.json"
REPO_SKILLS_DIR="$REPO_ROOT/skills"

# Default Paths (will be overridden by config if present)
CLI_EXT_DIR="$HOME/.gemini/extensions"
GUI_SKILLS_DIR="$HOME/.gemini/antigravity/skills"

# Load Configuration
load_config() {
    if [ -f "$CONFIG_FILE" ]; then
        # /usr/bin/python3
        CLI_EXT_DIR_CONFIG=$(python3 -c "import json, sys; print(json.load(open(sys.argv[1])).get('cli_ext_dir', sys.argv[2]))" "$CONFIG_FILE" "$CLI_EXT_DIR" 2>/dev/null)
        GUI_SKILLS_DIR_CONFIG=$(python3 -c "import json, sys; print(json.load(open(sys.argv[1])).get('gui_skills_dir', sys.argv[2]))" "$CONFIG_FILE" "$GUI_SKILLS_DIR" 2>/dev/null)
        
        CLI_EXT_DIR=$(expand_tilde "$CLI_EXT_DIR_CONFIG")
        GUI_SKILLS_DIR=$(expand_tilde "$GUI_SKILLS_DIR_CONFIG")
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
        python3 -m json.tool "$target_dir/gemini-extension.json" > /dev/null 2>&1
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
            local headers=$(python3 -c "import json, sys; print('|'.join(json.load(open(sys.argv[1])).get('required_md_headers', [])))" "$CONFIG_FILE")
            if [ -n "$headers" ]; then
                IFS='|' read -ra ADDR <<< "$headers"
                for header in "${ADDR[@]}"; do
                    grep -q "## $header" "$target_dir/SKILL.md"
                    if [ $? -ne 0 ]; then
                        echo "[WARNING] Missing header '## $header' in $skill_id/SKILL.md"
                    fi
                done
            fi
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
    python3 -c '
import json, sys
data = {"name": sys.argv[1], "version": "1.0.0", "description": sys.argv[2], "main": "SKILL.md"}
with open(sys.argv[3], "w") as f:
    json.dump(data, f, indent=2)
' "$ID" "$DESC" "$TARGET/gemini-extension.json"

    cat <<EOF2 > "$TARGET/SKILL.md"
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
EOF2

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
                local real_skill_path=$(resolve_path "$skill_path")
                
                # Link CLI
                local cli_target="$CLI_EXT_DIR/$skill_id"
                if [ -L "$cli_target" ]; then
                    if [ "$(resolve_path "$cli_target")" == "$real_skill_path" ]; then
                        echo "[SKIPPED] $skill_id is already linked in CLI."
                    else
                        echo "[WARNING] $skill_id CLI link points elsewhere. Skipping."
                    fi
                elif [ -e "$cli_target" ]; then
                    echo "[ERROR] $skill_id in CLI is a real directory, blocking link."
                else
                    ln -sf "$real_skill_path" "$cli_target"
                    echo "[LINKED] $skill_id in CLI."
                fi

                # Link GUI
                local gui_target="$GUI_SKILLS_DIR/$skill_id"
                if [ -L "$gui_target" ]; then
                    if [ "$(resolve_path "$gui_target")" == "$real_skill_path" ]; then
                        echo "[SKIPPED] $skill_id is already linked in GUI."
                    else
                        echo "[WARNING] $skill_id GUI link points elsewhere. Skipping."
                    fi
                elif [ -e "$gui_target" ]; then
                    echo "[ERROR] $skill_id in GUI is a real directory, blocking link."
                else
                    ln -sf "$real_skill_path" "$gui_target"
                    echo "[LINKED] $skill_id in GUI."
                fi
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

    echo "Repository Skills Tracking:"
    printf "%-20s | %-15s | %-10s | %-10s\n" "SKILL ID" "VALIDATION" "CLI LINK" "GUI LINK"
    echo "---------------------|-----------------|------------|------------"

    for skill_path in "$REPO_SKILLS_DIR"/*; do
        if [ -d "$skill_path" ]; then
            local skill_id=$(basename "$skill_path")
            local v_status="[OK]"
            validate_skill "$skill_path" > /dev/null 2>&1 || v_status="[INVALID]"

            local real_skill_path=$(resolve_path "$skill_path")

            local cli_link_status="[MISSING]"
            local cli_target="$CLI_EXT_DIR/$skill_id"
            if [ -L "$cli_target" ]; then
                if [ "$(resolve_path "$cli_target")" == "$real_skill_path" ]; then
                    cli_link_status="[LINKED]"
                else
                    cli_link_status="[MISMATCH]"
                fi
            elif [ -e "$cli_target" ]; then
                cli_link_status="[BLOCKING]"
            fi

            local gui_link_status="[MISSING]"
            local gui_target="$GUI_SKILLS_DIR/$skill_id"
            if [ -L "$gui_target" ]; then
                if [ "$(resolve_path "$gui_target")" == "$real_skill_path" ]; then
                    gui_link_status="[LINKED]"
                else
                    gui_link_status="[MISMATCH]"
                fi
            elif [ -e "$gui_target" ]; then
                gui_link_status="[BLOCKING]"
            fi

            printf "%-20s | %-15s | %-10s | %-10s\n" "$skill_id" "$v_status" "$cli_link_status" "$gui_link_status"
        fi
    done

    echo ""
    echo "External / System Skills (Not in this repo):"
    
    echo "  CLI Extensions:"
    local found_cli=false
    for item in "$CLI_EXT_DIR"/*; do
        local sid=$(basename "$item")
        if [ ! -d "$REPO_SKILLS_DIR/$sid" ]; then
            found_cli=true
            if [ -L "$item" ]; then
                echo "    [LINK] $sid -> $(python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$item")"
            else
                echo "    [DIR]  $sid"
            fi
        fi
    done
    [[ "$found_cli" == "false" ]] && echo "    (none)"

    echo "  GUI/Antigravity Skills:"
    local found_gui=false
    for item in "$GUI_SKILLS_DIR"/*; do
        local sid=$(basename "$item")
        if [ ! -d "$REPO_SKILLS_DIR/$sid" ]; then
            found_gui=true
            if [ -L "$item" ]; then
                echo "    [LINK] $sid -> $(python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$item")"
            else
                echo "    [DIR]  $sid"
            fi
        fi
    done
    [[ "$found_gui" == "false" ]] && echo "    (none)"
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
