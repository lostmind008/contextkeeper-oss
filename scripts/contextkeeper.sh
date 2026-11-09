#!/bin/bash
#
# File: /path/to/contextkeeper/scripts/contextkeeper.sh
# Project: ContextKeeper v3
# Purpose: Main contextkeeper CLI script
# Dependencies: rag_agent.py
# Dependents: CLI workflow, automation
# Created: 2025-08-05 (moved from root)
# Modified: 2025-08-05
#
# PLANNING CONTEXT:
# Moved from root directory to scripts/ as part of governance cleanup.
# This appears to be the main contextkeeper CLI interface.
#
# TODO FROM PLANNING:
# - [ ] Verify script functionality after move
# - [ ] Update any hardcoded paths if necessary
# - [ ] Ensure this is the current version (vs contextkeeper_simple.sh)

# === NAVIGATION ===
# Previous: [../contextkeeper_manager.sh] - manager script
# Next: [./contextkeeper_simple.sh] - simplified version
# Parent: [../] - root contextkeeper directory

set -e

if [ -z "$SACRED_APPROVAL_KEY" ]; then
    echo "Error: SACRED_APPROVAL_KEY environment variable is required"
    exit 1
fi

RAG_AGENT_URL="http://localhost:5556"

function usage() {
    echo "Usage: $0 <command> [options]"
    echo
    echo "Commands:"
    echo "  project add <path> <name>    Create and index a new project."
    echo "  project list                 List all projects."
    echo "  project focus <id>           Focus on a project."
    echo "  query <question> [project_id]  Query the knowledge base."
    echo
}

function project_add() {
    local path="$1"
    local name="$2"

    if [ -z "$path" ] || [ -z "$name" ]; then
        echo "Error: Path and name are required for 'project add'."
        exit 1
    fi

    echo "Creating and indexing project '$name'..."
    response=$(curl -s -X POST "$RAG_AGENT_URL/projects/create-and-index" \
        -H "Content-Type: application/json" \
        -d "{\"name\": \"$name\", \"root_path\": \"$path\"}")

    task_id=$(echo "$response" | jq -r .task_id)
    project_id=$(echo "$response" | jq -r .project_id)

    if [ -z "$task_id" ] || [ "$task_id" == "null" ]; then
        echo "Error: Failed to create project. Response:"
        echo "$response"
        exit 1
    fi

    echo "Project created with ID: $project_id"
    echo "Indexing started with Task ID: $task_id"

    # Poll for completion
    while true; do
        status_response=$(curl -s "$RAG_AGENT_URL/tasks/$task_id")
        status=$(echo "$status_response" | jq -r .status)
        progress=$(echo "$status_response" | jq -r .progress)

        printf "\rIndexing progress: [%-50s] %d%%" $(printf '#%.0s' $(seq 1 $(($progress / 2)))) "$progress"

        if [ "$status" == "complete" ]; then
            echo -e "\n\n✅ Indexing complete."
            break
        elif [ "$status" == "failed" ]; then
            error=$(echo "$status_response" | jq -r .error)
            echo -e "\n\n❌ Indexing failed: $error"
            exit 1
        fi
        sleep 2
    done
}

function select_project() {
    curl -s "$RAG_AGENT_URL/projects" | \
    jq -r '.projects[] | .name + " (" + .id + ")"' | \
    fzf --prompt="Select a Project > " | \
    sed -n 's/.*(\(.*\)).*/\1/p'
}

function project_focus() {
    local project_id="$1"
    if [ -z "$project_id" ]; then
        project_id=$(select_project)
    fi

    if [ -z "$project_id" ]; then
        echo "No project selected."
        exit 1
    fi

    curl -s -X POST "$RAG_AGENT_URL/projects/$project_id/focus"
    echo "Focused on project $project_id"
}

function main() {
    local command="$1"
    shift

    case "$command" in
        project)
            local sub_command="$1"
            shift
            case "$sub_command" in
                add)
                    project_add "$@"
                    ;;
                focus)
                    project_focus "$@"
                    ;;
                *)
                    echo "Unknown project command: $sub_command"
                    usage
                    exit 1
                    ;;
            esac
            ;;
        *)
            echo "Unknown command: $command"
            usage
            exit 1
            ;;
    esac
}

if [ "$#" -eq 0 ]; then
    usage
    exit 1
fi

main "$@"
