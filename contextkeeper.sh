#!/bin/bash

# ContextKeeper Ultimate Management Script
# Compatible with macOS (bash 3.2+) and Linux
# Created: 2025-08-05
# Purpose: Complete ContextKeeper management - create projects, index, chat, manage

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"
PORT=5556
SERVER_LOG="server.log"
VENV_PATH="venv"

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

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${CYAN}ℹ${NC} $1"
}

# Function to check if server is running
check_server() {
    if curl -s http://localhost:$PORT/health > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to start the server
start_server() {
    print_status "Starting ContextKeeper server..."
    
    # Kill any existing process on the port
    if command -v lsof >/dev/null 2>&1; then
        lsof -ti :$PORT | xargs kill -9 2>/dev/null
    fi
    sleep 1
    
    # Start server in background
    source "$VENV_PATH/bin/activate"
    python rag_agent.py server > "$SERVER_LOG" 2>&1 &
    SERVER_PID=$!
    
    # Wait for server to start
    local count=0
    while ! check_server && [ $count -lt 30 ]; do
        sleep 1
        count=$((count + 1))
        echo -n "."
    done
    echo
    
    if check_server; then
        print_success "Server started successfully (PID: $SERVER_PID)"
        return 0
    else
        print_error "Failed to start server. Check $SERVER_LOG for errors."
        return 1
    fi
}

# Function to list projects (full display)
list_projects() {
    local json=$(curl -s http://localhost:$PORT/projects)
    if [ $? -ne 0 ]; then
        print_error "Failed to fetch projects"
        return 1
    fi
    
    # Validate JSON response
    if ! echo "$json" | jq -e . >/dev/null 2>&1; then
        print_error "Invalid JSON response from server"
        print_info "Raw response: $json"
        return 1
    fi
    
    echo
    echo "═══════════════════════════════════════════════════════════════════"
    echo "                        Available Projects                          "
    echo "═══════════════════════════════════════════════════════════════════"
    
    # Parse JSON manually for macOS compatibility using process substitution
    local i=1
    local focused_project=$(echo "$json" | jq -r '.focused_project // ""')
    
    while IFS='|' read -r id name status _; do
        if [ "$id" = "$focused_project" ]; then
            echo -e "$i. ${GREEN}$name${NC} ($id) - $status ${CYAN}[FOCUSED]${NC}"
        else
            echo "$i. $name ($id) - $status"
        fi
        i=$((i + 1))
    done < <(echo "$json" | jq -r '.projects[] | "\(.id)|\(.name)|\(.status)|"')
    
    # Show summary
    local total=$(echo "$json" | jq -r '.total_projects // 0')
    local active=$(echo "$json" | jq -r '.active_projects // 0')
    echo "───────────────────────────────────────────────────────────────────"
    echo "Total: $total | Active: $active"
    echo
}

# Function to list projects (compact for selection)
list_projects_compact() {
    local json=$(curl -s http://localhost:$PORT/projects)
    if [ $? -ne 0 ]; then
        return 1
    fi
    
    # Validate JSON response
    if ! echo "$json" | jq -e . >/dev/null 2>&1; then
        print_error "Invalid JSON response from server"
        return 1
    fi
    
    echo
    # Parse JSON manually for macOS compatibility using process substitution
    local i=1
    local focused=$(echo "$json" | jq -r '.focused_project // ""')
    
    while IFS='|' read -r id name status _; do
        if [ "$id" = "$focused" ]; then
            echo -e "  $i. ${GREEN}$name${NC} ${CYAN}[FOCUSED]${NC}"
        else
            echo "  $i. $name"
        fi
        i=$((i + 1))
    done < <(echo "$json" | jq -r '.projects[] | "\(.id)|\(.name)|\(.status)|"')
    echo
}

# Function to select a project
select_project() {
    local prompt="${1:-Select project number: }"
    
    # Get projects
    local json=$(curl -s http://localhost:$PORT/projects)
    
    # Validate JSON response
    if ! echo "$json" | jq -e . >/dev/null 2>&1; then
        print_error "Invalid JSON response from server"
        return 1
    fi
    
    local total=$(echo "$json" | jq -r '.projects | length')
    
    if [ "$total" -eq 0 ]; then
        print_warning "No projects found"
        return 1
    fi
    
    # Don't show projects again if already shown
    if [ "$2" != "no_list" ]; then
        list_projects
    fi
    
    # Get selection
    read -p "$prompt" selection
    
    if [ -z "$selection" ]; then
        # Use focused project
        local focused=$(echo "$json" | jq -r '.focused_project // ""')
        if [ -n "$focused" ] && [ "$focused" != "null" ]; then
            echo "$focused"
            return 0
        else
            print_error "No focused project found"
            return 1
        fi
    elif [[ "$selection" =~ ^[0-9]+$ ]] && [ "$selection" -ge 1 ] && [ "$selection" -le "$total" ]; then
        # Get project by index
        local idx=$((selection - 1))
        local project_id=$(echo "$json" | jq -r ".projects[$idx].id")
        echo "$project_id"
        return 0
    else
        print_error "Invalid selection"
        return 1
    fi
}

# Function to create a new project
create_project() {
    echo
    echo "═══════════════════════════════════════════════════════════════════"
    echo "                      Create New Project                            "
    echo "═══════════════════════════════════════════════════════════════════"
    
    # Get project name
    read -p "Project name: " project_name
    if [ -z "$project_name" ]; then
        print_error "Project name cannot be empty"
        return 1
    fi
    
    # Get project path
    read -p "Project path (absolute): " project_path
    if [ -z "$project_path" ]; then
        project_path="$PWD"
        print_info "Using current directory: $project_path"
    fi
    
    # Validate path
    if [ ! -d "$project_path" ]; then
        print_error "Directory does not exist: $project_path"
        return 1
    fi
    
    # Make path absolute
    project_path=$(cd "$project_path" && pwd)
    
    print_status "Creating project..."
    
    # Create project
    local result=$(./scripts/rag_cli_v2.sh projects create "$project_name" "$project_path" 2>&1)
    local project_id=$(echo "$result" | grep -o 'proj_[a-f0-9]\{12\}' | head -1)
    
    if [ -z "$project_id" ]; then
        print_error "Failed to create project"
        echo "$result"
        return 1
    fi
    
    print_success "Created project: $project_name ($project_id)"
    
    # Ask if user wants to index
    read -p "Index project now? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        index_project "$project_id" "$project_path"
    fi
    
    echo "$project_id"
}

# Function to index a project
index_project() {
    local project_id="$1"
    local project_path="$2"
    
    if [ -z "$project_path" ]; then
        # Get path from project info
        read -p "Enter project path to index: " project_path
        if [ ! -d "$project_path" ]; then
            print_error "Invalid path: $project_path"
            return 1
        fi
    fi
    
    print_status "Focusing on project $project_id..."
    ./scripts/rag_cli_v2.sh projects focus "$project_id" > /dev/null 2>&1
    
    print_status "Starting indexing process..."
    print_info "This may take a few minutes depending on project size..."
    
    # Run indexing
    local start_time=$(date +%s)
    python rag_agent.py ingest --path "$project_path" 2>&1 | while read line; do
        if [[ "$line" =~ "Ingested" ]]; then
            echo -ne "\r${GREEN}Progress:${NC} $line"
        fi
    done
    echo
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    print_success "Indexing completed in ${duration}s"
}

# Function for interactive chat
chat_with_project() {
    local project_id="$1"
    
    # Get project info
    local json=$(curl -s http://localhost:$PORT/projects)
    
    # Validate JSON response
    if ! echo "$json" | jq -e . >/dev/null 2>&1; then
        print_error "Invalid JSON response from server"
        return 1
    fi
    
    local project_name=$(echo "$json" | jq -r ".projects[] | select(.id == \"$project_id\") | .name")
    
    echo
    echo "═══════════════════════════════════════════════════════════════════"
    echo "  Chat Interface - $project_name"
    echo "═══════════════════════════════════════════════════════════════════"
    echo "  Commands:"
    echo "    /help      - Show available commands"
    echo "    /clear     - Clear screen"
    echo "    /project   - Show current project info"
    echo "    /switch    - Switch to another project"
    echo "    /quit      - Exit chat"
    echo "═══════════════════════════════════════════════════════════════════"
    echo
    
    while true; do
        echo -ne "${BLUE}You:${NC} "
        read -r question
        
        case "$question" in
            /quit|/exit|/q)
                print_status "Exiting chat..."
                break
                ;;
            /clear)
                clear
                echo "Chat with $project_name"
                echo "═══════════════════════════════════════════════════════════════════"
                continue
                ;;
            /help|/h)
                echo "Available commands:"
                echo "  /help, /h     - Show this help"
                echo "  /clear        - Clear screen"
                echo "  /project, /p  - Show current project info"
                echo "  /switch, /s   - Switch to another project"
                echo "  /quit, /q     - Exit chat"
                continue
                ;;
            /project|/p)
                echo "$json" | jq ".projects[] | select(.id == \"$project_id\")"
                continue
                ;;
            /switch|/s)
                local new_id=$(select_project "Switch to project: ")
                if [ $? -eq 0 ] && [ -n "$new_id" ]; then
                    project_id="$new_id"
                    json=$(curl -s http://localhost:$PORT/projects)
                    
                    # Validate JSON response
                    if echo "$json" | jq -e . >/dev/null 2>&1; then
                        project_name=$(echo "$json" | jq -r ".projects[] | select(.id == \"$project_id\") | .name")
                        echo "Switched to: $project_name"
                    else
                        print_error "Failed to fetch updated project info"
                    fi
                fi
                continue
                ;;
            "")
                continue
                ;;
            *)
                # Query the knowledge base
                echo -ne "${GREEN}AI:${NC} "
                local response=$(curl -s -X POST http://localhost:$PORT/query_llm \
                    -H "Content-Type: application/json" \
                    -d "{\"question\": \"$question\", \"k\": 5, \"project_id\": \"$project_id\"}")
                
                # Check if response is valid JSON
                if echo "$response" | jq -e . >/dev/null 2>&1; then
                    local answer=$(echo "$response" | jq -r '.answer // .error // "No response"')
                    echo -e "$answer\n"
                else
                    print_error "Invalid response from server"
                    echo "Raw: $response"
                fi
                ;;
        esac
    done
}

# Main menu
show_menu() {
    echo
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║              ContextKeeper Management System v2.0                 ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    echo
    echo "1. Chat with existing project"
    echo "2. Create new project"
    echo "3. Index/Re-index project"
    echo "4. List all projects"
    echo "5. Focus on project"
    echo "6. View project details"
    echo "7. Server status"
    echo "8. View dashboard (browser)"
    echo "9. Clean database (start fresh)"
    echo "0. Exit"
    echo
    read -p "Select option: " choice
    
    case $choice in
        1)
            # Chat with project
            echo
            print_info "Select a project to chat with:"
            local project_id=$(select_project "Enter project number (or press Enter for focused): ")
            if [ $? -eq 0 ] && [ -n "$project_id" ]; then
                chat_with_project "$project_id"
            fi
            ;;
        2)
            # Create new project
            create_project
            ;;
        3)
            # Index project
            echo
            print_info "Select a project to index:"
            local project_id=$(select_project "Enter project number: ")
            if [ $? -eq 0 ] && [ -n "$project_id" ]; then
                index_project "$project_id"
            fi
            ;;
        4)
            # List projects
            list_projects
            read -p "Press Enter to continue..."
            ;;
        5)
            # Focus project
            echo
            print_info "Select a project to focus on:"
            local project_id=$(select_project "Enter project number: ")
            if [ $? -eq 0 ] && [ -n "$project_id" ]; then
                ./scripts/rag_cli_v2.sh projects focus "$project_id"
                print_success "Project focused"
            fi
            ;;
        6)
            # View project details
            echo
            print_info "Select a project to view details:"
            local project_id=$(select_project "Enter project number: ")
            if [ $? -eq 0 ] && [ -n "$project_id" ]; then
                echo
                local project_json=$(curl -s http://localhost:$PORT/projects)
                if echo "$project_json" | jq -e . >/dev/null 2>&1; then
                    echo "$project_json" | jq ".projects[] | select(.id == \"$project_id\")"
                else
                    print_error "Invalid JSON response from server"
                fi
                echo
                read -p "Press Enter to continue..."
            fi
            ;;
        7)
            # Server status
            if check_server; then
                print_success "Server is running on port $PORT"
                local health_json=$(curl -s http://localhost:$PORT/health)
                if echo "$health_json" | jq -e . >/dev/null 2>&1; then
                    echo "$health_json" | jq '.'
                else
                    print_error "Invalid JSON response from health endpoint"
                    print_info "Raw response: $health_json"
                fi
            else
                print_error "Server is not running"
            fi
            read -p "Press Enter to continue..."
            ;;
        8)
            # Open dashboard
            print_status "Opening dashboard in browser..."
            open "http://localhost:$PORT/analytics_dashboard_live.html" 2>/dev/null || \
            xdg-open "http://localhost:$PORT/analytics_dashboard_live.html" 2>/dev/null || \
            print_error "Please open http://localhost:$PORT/analytics_dashboard_live.html manually"
            ;;
        9)
            # Clean database
            print_warning "This will delete all projects and data!"
            read -p "Are you sure? (yes/no): " confirm
            if [ "$confirm" = "yes" ]; then
                ./cleanup_all.sh
            fi
            ;;
        0|q|quit|exit)
            print_status "Exiting..."
            exit 0
            ;;
        *)
            print_error "Invalid option"
            ;;
    esac
}

# Quick mode for command line usage
quick_mode() {
    case "$1" in
        chat)
            shift
            if [ -n "$1" ]; then
                # Project ID provided
                chat_with_project "$1"
            else
                # Select project
                local project_id=$(select_project)
                if [ $? -eq 0 ] && [ -n "$project_id" ]; then
                    chat_with_project "$project_id"
                fi
            fi
            ;;
        create)
            create_project
            ;;
        index)
            shift
            if [ -n "$1" ]; then
                index_project "$1" "$2"
            else
                local project_id=$(select_project "Select project to index: ")
                if [ $? -eq 0 ] && [ -n "$project_id" ]; then
                    index_project "$project_id"
                fi
            fi
            ;;
        list)
            list_projects
            ;;
        *)
            echo "Usage: $0 [command]"
            echo "Commands:"
            echo "  chat [project_id]  - Start chat with project"
            echo "  create             - Create new project"
            echo "  index [project_id] - Index a project"
            echo "  list               - List all projects"
            echo
            echo "Or run without arguments for interactive menu"
            ;;
    esac
}

# Main script
main() {
    # Check system dependencies first
    print_status "Checking system dependencies..."
    
    # Check for jq
    if ! command -v jq >/dev/null 2>&1; then
        print_error "jq is required but not installed"
        print_info "Install with: brew install jq (macOS) or apt-get install jq (Linux)"
        exit 1
    fi
    
    # Check for curl
    if ! command -v curl >/dev/null 2>&1; then
        print_error "curl is required but not installed"
        print_info "Install with: brew install curl (macOS) or apt-get install curl (Linux)"
        exit 1
    fi
    
    # Check if virtual environment exists
    if [ ! -d "$VENV_PATH" ]; then
        print_error "Virtual environment not found at $VENV_PATH"
        print_info "Run: python3 -m venv $VENV_PATH"
        exit 1
    fi
    
    # Activate virtual environment
    source "$VENV_PATH/bin/activate"
    
    # Check Python dependencies
    print_status "Checking Python dependencies..."
    if ! python -c "import flask, chromadb, google.genai" 2>/dev/null; then
        print_error "Missing Python dependencies"
        print_info "Run: pip install -r requirements.txt"
        exit 1
    fi
    
    # Check/start server
    if check_server; then
        print_success "Server is already running"
    else
        if ! start_server; then
            exit 1
        fi
    fi
    
    # Check if quick mode or interactive
    if [ $# -gt 0 ]; then
        quick_mode "$@"
    else
        # Interactive mode
        while true; do
            show_menu
        done
    fi
}

# Handle script arguments
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "ContextKeeper Management System"
    echo
    echo "Usage: $0 [command] [options]"
    echo
    echo "Commands:"
    echo "  chat [project_id]     Start chat with a project"
    echo "  create                Create a new project"
    echo "  index [project_id]    Index or re-index a project"
    echo "  list                  List all projects"
    echo
    echo "Run without arguments for interactive menu"
    exit 0
fi

# Run main function
main "$@"