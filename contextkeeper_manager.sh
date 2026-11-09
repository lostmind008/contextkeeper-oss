#!/bin/bash

# ContextKeeper Manager Script
# Created: 2025-08-05 17:49 AEST
# Author: LostMind AI
# 
# Story: After spending hours manually creating projects, focusing, indexing, and
# testing queries, a single script was needed that would automate everything.
# He was frustrated with having to remember the exact sequence of commands and
# wanted to just provide a project path and start chatting immediately.
#
# This script was born from the need to:
# 1. Check if the RAG agent server is running (and start it if not)
# 2. Automatically create a project with a generated ID
# 3. Focus on the project and start indexing in the background
# 4. Provide an interactive chat interface while indexing continues
# 5. Handle all error cases gracefully
#
# Location: /path/to/contextkeeper/contextkeeper_manager.sh
# Purpose: One-command solution to track any project and start querying it
#
# Usage: ./contextkeeper_manager.sh /path/to/project
# Or just: ./contextkeeper_manager.sh (will prompt for path)

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"
PORT=5556
SERVER_LOG="server.log"

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
    lsof -ti :$PORT | xargs kill -9 2>/dev/null
    sleep 1
    
    # Start server in background
    source venv/bin/activate
    python rag_agent.py server > $SERVER_LOG 2>&1 &
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

# Function to create and index project
create_and_index_project() {
    local project_path="$1"
    local project_name=$(basename "$project_path")
    
    print_status "Creating project: $project_name"
    
    # Create project and capture output
    local create_output=$(./scripts/rag_cli_v2.sh projects create "$project_name" "$project_path" 2>&1)
    local project_id=$(echo "$create_output" | grep -o 'proj_[a-f0-9]\{12\}' | head -1)
    
    if [ -z "$project_id" ]; then
        print_error "Failed to create project"
        echo "$create_output"
        return 1
    fi
    
    print_success "Created project with ID: $project_id"
    
    # Focus on the project
    print_status "Focusing on project..."
    ./scripts/rag_cli_v2.sh projects focus "$project_id" > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        print_success "Project focused"
    else
        print_error "Failed to focus on project"
        return 1
    fi
    
    # Start indexing in background
    print_status "Starting indexing process..."
    (
        python rag_agent.py ingest --path "$project_path" > indexing_${project_id}.log 2>&1
        if [ $? -eq 0 ]; then
            echo -e "\n${GREEN}✓ Indexing completed for project $project_id${NC}"
        else
            echo -e "\n${RED}✗ Indexing failed for project $project_id${NC}"
        fi
    ) &
    INDEXING_PID=$!
    
    print_success "Indexing started in background (PID: $INDEXING_PID)"
    print_warning "You can start asking questions while indexing continues..."
    
    echo "$project_id"
}

# Function for interactive chat
interactive_chat() {
    local project_id="$1"
    
    echo
    echo "═══════════════════════════════════════════════════════════════════"
    echo "  ContextKeeper Interactive Chat (Project: $project_id)"
    echo "═══════════════════════════════════════════════════════════════════"
    echo "  Commands:"
    echo "    /status    - Check indexing status"
    echo "    /projects  - List all projects"
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
            /status)
                if ps -p $INDEXING_PID > /dev/null 2>&1; then
                    print_warning "Indexing still in progress..."
                else
                    print_success "Indexing completed"
                fi
                continue
                ;;
            /projects)
                ./scripts/rag_cli_v2.sh projects list
                continue
                ;;
            /help)
                echo "  Commands:"
                echo "    /status    - Check indexing status"
                echo "    /projects  - List all projects"
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
                    echo -e "Raw response: $response\n"
                fi
                ;;
        esac
    done
}

# Main script
main() {
    clear
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║               ContextKeeper Manager v1.0                           ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    echo
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        print_error "Virtual environment not found. Please run: python3 -m venv venv"
        exit 1
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Check dependencies
    print_status "Checking dependencies..."
    python -c "import flask, chromadb, google.genai" 2>/dev/null
    if [ $? -ne 0 ]; then
        print_error "Missing dependencies. Please run: pip install -r requirements.txt"
        exit 1
    fi
    print_success "Dependencies OK"

    # Ensure sacred approval key is set
    if [ -z "$SACRED_APPROVAL_KEY" ]; then
        print_error "SACRED_APPROVAL_KEY environment variable is required"
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
    
    # Get project path
    if [ -n "$1" ]; then
        PROJECT_PATH="$1"
    else
        echo
        read -p "Enter the absolute path to the project you want to track: " PROJECT_PATH
    fi
    
    # Validate path
    if [ ! -d "$PROJECT_PATH" ]; then
        print_error "Directory does not exist: $PROJECT_PATH"
        exit 1
    fi
    
    # Make path absolute
    PROJECT_PATH=$(cd "$PROJECT_PATH" && pwd)
    print_status "Project path: $PROJECT_PATH"
    
    # Create and index project
    PROJECT_ID=$(create_and_index_project "$PROJECT_PATH")
    
    if [ -z "$PROJECT_ID" ]; then
        print_error "Failed to create project"
        exit 1
    fi
    
    # Start interactive chat
    sleep 2
    interactive_chat "$PROJECT_ID"
    
    # Cleanup
    print_status "Cleaning up..."
    if [ -n "$INDEXING_PID" ] && ps -p $INDEXING_PID > /dev/null 2>&1; then
        print_warning "Indexing still running in background (PID: $INDEXING_PID)"
    fi
    
    echo
    print_success "Thank you for using ContextKeeper!"
}

# Run main function with all arguments
main "$@"