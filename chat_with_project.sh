#!/bin/bash

# ContextKeeper Chat Interface
# For chatting with already indexed projects

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PORT=5556

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if server is running
check_server() {
    if curl -s http://localhost:$PORT/health > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# List projects and let user select
select_project() {
    print_status "Fetching available projects..."
    
    # Get projects list
    projects_json=$(curl -s http://localhost:$PORT/projects)
    
    # Parse and display projects
    echo
    echo "Available Projects:"
    echo "==================="
    
    # Parse projects for macOS compatibility
    local i=1
    echo "$projects_json" | jq -r '.projects[] | "\(.id)|\(.name)"' | while IFS='|' read -r id name; do
        echo "$i. $name ($id)"
        i=$((i + 1))
    done
    
    # Store project count for validation
    local total_projects=$(echo "$projects_json" | jq -r '.projects | length')
    
    echo
    read -p "Select project number (or press Enter to use focused project): " selection
    
    if [ -z "$selection" ]; then
        # Use focused project
        PROJECT_ID=$(echo "$projects_json" | jq -r '.focused_project // empty')
        if [ -z "$PROJECT_ID" ]; then
            print_error "No focused project found. Please select a project."
            return 1
        fi
        PROJECT_NAME=$(echo "$projects_json" | jq -r ".projects[] | select(.id == \"$PROJECT_ID\") | .name")
        print_success "Using focused project: $PROJECT_NAME"
    else
        # Validate selection
        if [[ "$selection" =~ ^[0-9]+$ ]] && [ "$selection" -ge 1 ] && [ "$selection" -le "$total_projects" ]; then
            # Get project by index
            local idx=$((selection - 1))
            PROJECT_ID=$(echo "$projects_json" | jq -r ".projects[$idx].id")
            PROJECT_NAME=$(echo "$projects_json" | jq -r ".projects[$idx].name")
            print_success "Selected: $PROJECT_NAME"
        else
            print_error "Invalid selection"
            return 1
        fi
    fi
    
    echo "$PROJECT_ID"
}

# Interactive chat function
interactive_chat() {
    local project_id="$1"
    local project_name="$2"
    
    echo
    echo "═══════════════════════════════════════════════════════════════════"
    echo "  ContextKeeper Chat - Project: $project_name"
    echo "═══════════════════════════════════════════════════════════════════"
    echo "  Commands:"
    echo "    /projects  - List all projects"
    echo "    /switch    - Switch to different project"
    echo "    /info      - Show project info"
    echo "    /help      - Show this help"
    echo "    /quit      - Exit chat"
    echo "═══════════════════════════════════════════════════════════════════"
    echo
    
    while true; do
        echo -ne "${BLUE}You:${NC} "
        read -r question
        
        case "$question" in
            /quit|/exit)
                print_status "Exiting chat..."
                break
                ;;
            /projects)
                curl -s http://localhost:$PORT/projects | jq -r '.projects[] | "\(.name) (\(.id)) - \(.status)"'
                continue
                ;;
            /switch)
                new_project_id=$(select_project)
                if [ $? -eq 0 ] && [ -n "$new_project_id" ]; then
                    project_id="$new_project_id"
                    # Get new project name
                    project_name=$(curl -s http://localhost:$PORT/projects | jq -r ".projects[] | select(.id == \"$project_id\") | .name")
                    echo "Switched to: $project_name"
                fi
                continue
                ;;
            /info)
                curl -s http://localhost:$PORT/projects | jq ".projects[] | select(.id == \"$project_id\")"
                continue
                ;;
            /help)
                echo "  Commands:"
                echo "    /projects  - List all projects"
                echo "    /switch    - Switch to different project"
                echo "    /info      - Show project info"
                echo "    /help      - Show this help"
                echo "    /quit      - Exit chat"
                continue
                ;;
            "")
                continue
                ;;
            *)
                # Query the knowledge base
                echo -ne "${GREEN}AI:${NC} "
                response=$(curl -s -X POST http://localhost:$PORT/query_llm \
                    -H "Content-Type: application/json" \
                    -d "{\"question\": \"$question\", \"k\": 5, \"project_id\": \"$project_id\"}")
                
                # Parse response safely
                if echo "$response" | jq -e . >/dev/null 2>&1; then
                    answer=$(echo "$response" | jq -r '.answer // .error // "No response"')
                    echo -e "$answer\n"
                else
                    echo -e "Error: Invalid response from server\n"
                fi
                ;;
        esac
    done
}

# Main script
main() {
    clear
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║               ContextKeeper Chat Interface                         ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    echo
    
    # Check if server is running
    if ! check_server; then
        print_error "ContextKeeper server is not running!"
        echo "Please start it with: python rag_agent.py server"
        exit 1
    fi
    
    print_success "Server is running"
    
    # Select project
    PROJECT_ID=$(select_project)
    if [ $? -ne 0 ] || [ -z "$PROJECT_ID" ]; then
        exit 1
    fi
    
    # Get project name
    PROJECT_NAME=$(curl -s http://localhost:$PORT/projects | jq -r ".projects[] | select(.id == \"$PROJECT_ID\") | .name")
    
    # Start chat
    interactive_chat "$PROJECT_ID" "$PROJECT_NAME"
    
    echo
    print_success "Thank you for using ContextKeeper!"
}

# Run main function
main "$@"