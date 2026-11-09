#!/bin/bash
set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <project_id>"
  echo "Lists available projects if no ID is provided."
  curl -s http://localhost:5556/projects | jq '.projects[] | .id + "  |  " + .name'
  exit 1
fi

PROJECT_ID=$1

# Get project path from the API
PROJECT_PATH=$(curl -s http://localhost:5556/projects | jq -r --arg pid "$PROJECT_ID" '.projects[] | select(.id==$pid) | .root_path')

if [ -z "$PROJECT_PATH" ] || [ "$PROJECT_PATH" == "null" ]; then
  echo "Error: Project with ID '$PROJECT_ID' not found or has no root path."
  exit 1
fi

echo "Re-indexing project '$PROJECT_ID' at path '$PROJECT_PATH'..."
python rag_agent.py ingest --path "$PROJECT_PATH"

echo "✅ Re-indexing complete."
