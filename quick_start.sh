#!/bin/bash

# Quick Start Script for ContextKeeper
# Usage: ./quick_start.sh [project_path]

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# If no path provided, ask for it
if [ -z "$1" ]; then
    echo "ContextKeeper Quick Start"
    echo "========================"
    echo
    echo "Examples:"
    echo "  ./quick_start.sh /path/to/my/project"
    echo "  ./quick_start.sh ."
    echo "  ./quick_start.sh ~/Documents/myproject"
    echo
    read -p "Enter project path (or press Enter to use current directory): " PROJECT_PATH
    
    if [ -z "$PROJECT_PATH" ]; then
        PROJECT_PATH="$PWD"
    fi
else
    PROJECT_PATH="$1"
fi

# Run the main manager script
exec "$SCRIPT_DIR/contextkeeper_manager.sh" "$PROJECT_PATH"