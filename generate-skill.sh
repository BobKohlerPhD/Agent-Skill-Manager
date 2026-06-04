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

# Default Paths
SYSTEM_SKILL_DIRS=()

# Load Configuration
load_config() {
    if [ -f "$CONFIG_FILE" ]; then
        local json_dirs=$(python3 -c "import json, sys; print('|'.join(json.load(open(sys.argv[1])).get('system_skill_dirs', [])))" "$CONFIG_FILE" 2>/dev/null)
        if [ -n "$json_dirs" ]; then
            IFS='|' read -ra ADDR <<< "$json_dirs"
            for dir in "${ADDR[@]}"; do
                SYSTEM_SKILL_DIRS+=("$(expand_tilde "$dir")")
            done
        fi
    fi

    # Fallback to defaults if empty
    if [ ${#SYSTEM_SKILL_DIRS[@]} -eq 0 ]; then
        SYSTEM_SKILL_DIRS+=("$HOME/.gemini/extensions")
        SYSTEM_SKILL_DIRS+=("$HOME/.gemini/antigravity/skills")
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

    # Try to auto-recover gemini-extension.json if missing but SKILL.md is present
    if [ ! -f "$target_dir/gemini-extension.json" ] && [ -f "$target_dir/SKILL.md" ]; then
        python3 -c '
import sys, os, json, re
target_dir = sys.argv[1]
skill_md = os.path.join(target_dir, "SKILL.md")
ext_json = os.path.join(target_dir, "gemini-extension.json")
try:
    with open(skill_md, "r") as f:
        content = f.read()
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if match:
        fm_text = match.group(1)
        name, desc = None, None
        for line in fm_text.splitlines():
            if line.startswith("name:"):
                name = line.split(":", 1)[1].strip().strip("\"\x27").strip()
            elif line.startswith("description:"):
                desc = line.split(":", 1)[1].strip().strip("\"\x27").strip()
        if name and desc:
            with open(ext_json, "w") as f:
                json.dump({"name": name, "version": "1.0.0", "description": desc, "main": "SKILL.md"}, f, indent=2)
            print(f"[RECOVERED] Generated missing gemini-extension.json for {os.path.basename(target_dir)}")
except Exception as e:
    pass
' "$target_dir"
    fi

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
                    # Match header robustly allowing leading/trailing spaces
                    grep -qE "^##[[:space:]]+${header}[[:space:]]*$" "$target_dir/SKILL.md"
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

## Trigger Criteria & Bounds
*   **Use Cases**: [Describe when the agent should trigger this skill]
*   **Anti-Patterns (Do NOT Use)**: [Describe when this skill should NOT be triggered]

## Execution Protocol
*   **Pre-conditions**: [Requirements before running, e.g., working directory state]
*   **Step-by-Step Instructions**:
    1. [Operational step 1]
    2. [Operational step 2]
*   **Error Handling**: [Steps for the agent to take if execution fails or inputs are malformed]

## Requirements & Environment
*   **System Dependencies**: [e.g., CLI tools, OS packages]
*   **Runtime Packages**: [e.g., pip/uv packages, npm packages]
*   **API Keys / Environment Variables**: [List required keys]

## Few-Shot Cognitive Examples
### Example 1: Standard Success Path
*   **Input**:
    ```json
    [Mock input data or request]
    ```
*   **Agent Thought (CoT)**: [Model's step-by-step internal reasoning]
*   **Action**: [Tools invoked]
*   **Output / Result**:
    ```json
    [Resulting state or content]
    ```
EOF2

    echo "[SUCCESS] Template for '$ID' created in $TARGET"
}

# Environment Synchronization
link_skills() {
    echo "Starting synchronization..."
    for dir in "${SYSTEM_SKILL_DIRS[@]}"; do
        mkdir -p "$dir"
    done

    for skill_path in "$REPO_SKILLS_DIR"/*; do
        if [ -d "$skill_path" ]; then
            local skill_id=$(basename "$skill_path")
            
            if validate_skill "$skill_path"; then
                local real_skill_path=$(resolve_path "$skill_path")
                
                for target_base in "${SYSTEM_SKILL_DIRS[@]}"; do
                    local target="$target_base/$skill_id"
                    if [ -L "$target" ]; then
                        if [ "$(resolve_path "$target")" == "$real_skill_path" ]; then
                            echo "[SKIPPED] $skill_id is already linked in $target_base"
                        else
                            echo "[WARNING] $skill_id link in $target_base points elsewhere. Skipping."
                        fi
                    elif [ -e "$target" ]; then
                        echo "[ERROR] $skill_id in $target_base is a real directory, blocking link."
                    else
                        ln -sf "$real_skill_path" "$target"
                        echo "[LINKED] $skill_id in $target_base"
                    fi
                done
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
    echo "Tracking Directories:"
    for dir in "${SYSTEM_SKILL_DIRS[@]}"; do
        echo "  - $dir"
    done
    echo ""

    echo "Repository Skills Tracking:"
    printf "%-20s | %-12s | %-s\n" "SKILL ID" "VALIDATION" "LOCATION STATUS"
    echo "---------------------|--------------|-----------------------------------"

    for skill_path in "$REPO_SKILLS_DIR"/*; do
        if [ -d "$skill_path" ]; then
            local skill_id=$(basename "$skill_path")
            local v_status="[OK]"
            validate_skill "$skill_path" > /dev/null 2>&1 || v_status="[INVALID]"

            local real_skill_path=$(resolve_path "$skill_path")
            local status_summary=""

            for target_base in "${SYSTEM_SKILL_DIRS[@]}"; do
                local target="$target_base/$skill_id"
                local label=$(basename "$target_base")
                # Handle special case for .gemini/extensions vs .gemini/skills
                if [[ "$target_base" == *".gemini/extensions"* ]]; then label="CLI"; fi
                if [[ "$target_base" == *".gemini/antigravity/skills"* ]]; then label="GUI"; fi
                if [[ "$target_base" == *".agents/skills"* ]]; then label="AGTS"; fi
                if [[ "$target_base" == *".gemini/skills"* ]]; then label="SKLS"; fi

                if [ -L "$target" ]; then
                    if [ "$(resolve_path "$target")" == "$real_skill_path" ]; then
                        status_summary+="$label:[LINKED] "
                    else
                        status_summary+="$label:[MISMATCH] "
                    fi
                elif [ -e "$target" ]; then
                    status_summary+="$label:[BLOCKING] "
                else
                    status_summary+="$label:[MISSING] "
                fi
            done

            printf "%-20s | %-12s | %-s\n" "$skill_id" "$v_status" "$status_summary"
        fi
    done

    echo ""
    echo "External / System Skills (Not in this repo):"
    
    for target_base in "${SYSTEM_SKILL_DIRS[@]}"; do
        echo "  In $target_base:"
        local found=false
        # Use a subshell to avoid expansion errors if dir is empty
        for item in "$target_base"/*; do
            if [ -e "$item" ]; then
                local sid=$(basename "$item")
                if [ ! -d "$REPO_SKILLS_DIR/$sid" ]; then
                    found=true
                    if [ -L "$item" ]; then
                        echo "    [LINK] $sid -> $(resolve_path "$item")"
                    else
                        echo "    [DIR]  $sid"
                    fi
                fi
            fi
        done
        [[ "$found" == "false" ]] && echo "    (none)"
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
