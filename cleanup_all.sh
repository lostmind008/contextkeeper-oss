#!/bin/bash

# ContextKeeper Complete Cleanup Script
# This script removes all databases, logs, and indexes

echo "🧹 ContextKeeper Complete Cleanup"
echo "================================="
echo "This will delete:"
echo "  - ChromaDB database (rag_knowledge_db/)"
echo "  - All log files (*.log)"
echo "  - Project configurations (projects/)"
echo "  - Any SQLite databases"
echo "  - Test databases"
echo ""
read -p "Are you sure you want to delete everything? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "Starting cleanup..."
    
    # Delete ChromaDB database
    if [ -d "rag_knowledge_db" ]; then
        echo "✓ Removing ChromaDB database..."
        rm -rf rag_knowledge_db/
    fi
    
    # Delete all log files
    echo "✓ Removing log files..."
    rm -f *.log
    
    # Delete project configurations
    if [ -d "projects" ]; then
        echo "✓ Removing project configurations..."
        rm -rf projects/
    fi
    
    # Delete SQLite databases
    echo "✓ Removing SQLite databases..."
    rm -f *.db *.sqlite *.sqlite3
    
    # Delete test databases
    if [ -d "test_db" ]; then
        echo "✓ Removing test database..."
        rm -rf test_db/
    fi
    
    if [ -d ".chromadb" ]; then
        echo "✓ Removing .chromadb directory..."
        rm -rf .chromadb/
    fi
    
    # Optional: Remove cache directories
    echo "✓ Removing cache directories..."
    rm -rf __pycache__/
    rm -rf .pytest_cache/
    
    echo ""
    echo "✅ Cleanup complete!"
    echo ""
    echo "To start fresh:"
    echo "  1. source venv/bin/activate"
    echo "  2. python rag_agent.py server"
    echo "  3. Create new projects as needed"
else
    echo "❌ Cleanup cancelled"
fi