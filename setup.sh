#!/bin/bash
# Quick setup script for RAG Knowledge Agent

echo "🚀 RAG Knowledge Agent - Quick Setup"
echo "===================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  No .env file found!"
    echo "Creating .env from template..."
    cp .env.template .env
    echo ""
    echo "Please edit .env with your Google Cloud credentials:"
    echo "  1. Set GOOGLE_CLOUD_PROJECT to your project ID"
    echo "  2. Set GOOGLE_APPLICATION_CREDENTIALS to your service account JSON path"
    echo "  3. Set SACRED_APPROVAL_KEY to your secret approval key (required)"
    echo ""
    read -p "Press Enter to continue after editing .env..."
fi

# Warn if SACRED_APPROVAL_KEY is missing
if [ -z "$SACRED_APPROVAL_KEY" ] && ! grep -q "SACRED_APPROVAL_KEY" .env 2>/dev/null; then
    echo "⚠️  SACRED_APPROVAL_KEY is not set. Define it in your environment or .env before approving plans."
fi

# Make CLI executable
chmod +x rag_cli.sh

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the RAG agent:"
echo "  python rag_agent.py start"
echo ""
echo "Or use the CLI wrapper:"
echo "  ./scripts/rag_cli.sh start"
echo ""
echo "For help:"
echo "  ./scripts/rag_cli.sh help"
