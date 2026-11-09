#!/bin/bash

# ContextKeeper Simple Management Script
# A cleaner, simpler version that works correctly

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Config
PORT=5556
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Helper functions
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Show projects and return selection
select_project() {
    # Get projects
    local json=$(curl -s http://localhost:$PORT/projects 2>/dev/null)
    
    # Check if valid JSON
    if ! echo "$json" | jq -e . >/dev/null 2>&1; then
        print_error "Failed to get projects from server"
        return 1
    fi
    
    # Get project count
    local count=$(echo "$json" | jq -r '.projects | length')
    if [ "$count" -eq "0" ]; then
        print_error "No projects found"
        return 1
    fi
    
    # Display projects
    echo
    echo "Available Projects:"
    echo "==================="
    
    local i=1
    local focused=$(echo "$json" | jq -r '.focused_project // ""')
    
    # Store projects in array for selection
    local project_ids=()
    local project_names=()
    
    while IFS='|' read -r id name status; do
        project_ids+=("$id")
        project_names+=("$name")
        
        if [ "$id" = "$focused" ]; then
            echo -e "$i) ${GREEN}$name${NC} ${CYAN}[FOCUSED]${NC}"
        else
            echo "$i) $name"
        fi
        ((i++))
    done < <(echo "$json" | jq -r '.projects[] | "\(.id)|\(.name)|\(.status)"')
    
    echo
    read -p "Select project number (or press Enter for focused): " selection
    
    # Handle selection
    if [ -z "$selection" ]; then
        # Use focused project
        if [ -n "$focused" ] && [ "$focused" != "null" ]; then
            echo "$focused"
            return 0
        else
            print_error "No focused project set"
            return 1
        fi
    elif [[ "$selection" =~ ^[0-9]+$ ]] && [ "$selection" -ge 1 ] && [ "$selection" -le "${#project_ids[@]}" ]; then
        # Return selected project ID
        local idx=$((selection - 1))
        echo "${project_ids[$idx]}"
        return 0
    else
        print_error "Invalid selection"
        return 1
    fi
}

# Chat with project
chat_project() {
    local project_id="$1"
    
    # Get project name
    local json=$(curl -s http://localhost:$PORT/projects 2>/dev/null)
    local project_name=$(echo "$json" | jq -r ".projects[] | select(.id == \"$project_id\") | .name")
    
    echo
    echo "═══════════════════════════════════════════════════════════════════"
    echo "  Chat with: $project_name"
    echo "═══════════════════════════════════════════════════════════════════"
    echo "  Type your questions below. Commands:"
    echo "    /quit - Exit chat"
    echo "    /help - Show commands"
    echo "═══════════════════════════════════════════════════════════════════"
    echo
    
    while true; do
        echo -ne "${BLUE}You:${NC} "
        read -r question
        
        case "$question" in
            /quit|/exit)
                break
                ;;
            /help)
                echo "Commands: /quit, /help"
                ;;
            "")
                continue
                ;;
            *)
                # Query the API
                echo -ne "${GREEN}AI:${NC} "
                local response=$(curl -s -X POST http://localhost:$PORT/query_llm \
                    -H "Content-Type: application/json" \
                    -d "{\"question\": \"$question\", \"k\": 5, \"project_id\": \"$project_id\"}" 2>/dev/null)
                
                if echo "$response" | jq -e . >/dev/null 2>&1; then
                    echo "$response" | jq -r '.answer // .error // "No response"'
                else
                    print_error "Failed to get response"
                fi
                echo
                ;;
        esac
    done
}

# Create project
create_project() {
    echo
    read -p "Project name: " name
    read -p "Project path: " path
    
    if [ -z "$name" ] || [ -z "$path" ]; then
        print_error "Name and path are required"
        return 1
    fi
    
    if [ ! -d "$path" ]; then
        print_error "Path does not exist: $path"
        return 1
    fi
    
    # Create project
    print_status "Creating project..."
    local result=$(./scripts/rag_cli_v2.sh projects create "$name" "$path" 2>&1)
    local project_id=$(echo "$result" | grep -o 'proj_[a-f0-9]\{12\}' | head -1)
    
    if [ -n "$project_id" ]; then
        print_success "Created project: $name ($project_id)"
        
        read -p "Index now? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_status "Indexing..."
            ./scripts/rag_cli_v2.sh projects focus "$project_id" >/dev/null 2>&1
            python rag_agent.py ingest --path "$path"
        fi
    else
        print_error "Failed to create project"
        echo "$result"
    fi
}

# Main menu
main_menu() {
    while true; do
        echo
        echo "ContextKeeper Menu"
        echo "=================="
        echo "1) Chat with project"
        echo "2) Create new project"
        echo "3) List all projects"
        echo "4) Exit"
        echo
        read -p "Select option: " choice
        
        case $choice in
            1)
                project_id=$(select_project)
                if [ $? -eq 0 ] && [ -n "$project_id" ]; then
                    chat_project "$project_id"
                fi
                ;;
            2)
                create_project
                ;;
            3)
                echo
                curl -s http://localhost:$PORT/projects | jq -r '
                    .projects[] | 
                    "• \(.name) (\(.id)) - \(.status)"
                '
                ;;
            4|q|quit|exit)
                echo "Goodbye!"
                exit 0
                ;;
            *)
                print_error "Invalid option"
                ;;
        esac
    done
}

# Check dependencies
if ! command -v jq >/dev/null 2>&1; then
    print_error "jq is required. Install with: brew install jq"
    exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
    print_error "curl is required"
    exit 1
fi

# Check server
if ! curl -s http://localhost:$PORT/health >/dev/null 2>&1; then
    print_error "ContextKeeper server is not running on port $PORT"
    print_status "Start it with: python rag_agent.py server"
    exit 1
fi

print_success "Connected to ContextKeeper server"

# Run menu
main_menu