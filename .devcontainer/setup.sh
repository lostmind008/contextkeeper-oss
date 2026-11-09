#!/bin/bash
# ============================================================================
# ContextKeeper v3 - DevContainer Setup Script
# ============================================================================
# This script sets up the development environment for GitHub Codespaces
# and VS Code Dev Containers. It handles dependency installation,
# directory creation, and initial configuration.
# ============================================================================

set -e  # Exit on error

# Colours for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Colour

# Function to print coloured messages
print_message() {
    local colour=$1
    local message=$2
    echo -e "${colour}${message}${NC}"
}

print_message $GREEN "🚀 Starting ContextKeeper v3 DevContainer Setup..."

# Navigate to workspace - handle different container environments
cd /workspaces/contextkeeper || cd /workspaces/contextkeeper-v3 || cd /workspace || cd $(pwd)
print_message $YELLOW "📁 Working directory: $(pwd)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_message $YELLOW "🐍 Creating Python virtual environment..."
    python3 -m venv venv
else
    print_message $GREEN "✅ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
print_message $YELLOW "📦 Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install Python dependencies
print_message $YELLOW "📦 Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    print_message $RED "❌ requirements.txt not found!"
    exit 1
fi

# Install additional development tools
print_message $YELLOW "🛠️  Installing additional development tools..."
pip install flake8 black pytest-cov ipython

# Create necessary directories
print_message $YELLOW "📁 Creating required directories..."
mkdir -p rag_knowledge_db
mkdir -p rag_knowledge_db/sacred_chromadb
mkdir -p rag_knowledge_db/sacred_plans
mkdir -p logs
mkdir -p tests/temp
mkdir -p .vscode

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    print_message $YELLOW "🔧 Creating .env file from template..."
    if [ -f ".env.template" ]; then
        # Copy template and remove 'export' statements
        sed 's/^export //' .env.template > .env
        print_message $GREEN "✅ .env file created from template"
        print_message $YELLOW "⚠️  IMPORTANT: Please configure your API keys in .env file"
    else
        print_message $RED "❌ .env.template not found!"
    fi
else
    print_message $GREEN "✅ .env file already exists"
fi

# Set proper permissions
print_message $YELLOW "🔒 Setting permissions..."
chmod +x scripts/*.sh 2>/dev/null || true
chmod +x .devcontainer/setup.sh 2>/dev/null || true
chmod +x *.sh 2>/dev/null || true

# Install MCP server dependencies if directory exists
if [ -d "mcp-server" ]; then
    print_message $YELLOW "🔌 Installing MCP server dependencies..."
    cd mcp-server
    npm install
    cd ..
else
    print_message $YELLOW "ℹ️  MCP server directory not found, skipping Node.js setup"
fi

# Create VS Code settings if not exists
if [ ! -f ".vscode/settings.json" ]; then
    print_message $YELLOW "⚙️  Creating VS Code settings..."
    cat > .vscode/settings.json << 'EOF'
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "python.terminal.activateEnvironment": true,
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.pytestArgs": [
        "tests"
    ],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        "**/.pytest_cache": true
    },
    "editor.formatOnSave": true,
    "[python]": {
        "editor.codeActionsOnSave": {
            "source.organizeImports": true
        }
    }
}
EOF
fi

# Initialize ChromaDB if Python is available
print_message $YELLOW "🗄️  Initialising ChromaDB..."
python3 << 'EOF' 2>/dev/null || echo "ChromaDB initialisation skipped"
try:
    import chromadb
    import os
    db_path = "./rag_knowledge_db"
    client = chromadb.PersistentClient(path=db_path)
    print(f"ChromaDB initialised at {db_path}")
except Exception as e:
    print(f"ChromaDB initialisation skipped: {e}")
EOF

# Create sacred plans registry if needed
if [ ! -f "rag_knowledge_db/sacred_plans/registry.json" ]; then
    print_message $YELLOW "📝 Creating sacred plans registry..."
    mkdir -p rag_knowledge_db/sacred_plans
    echo '{"plans": {}}' > rag_knowledge_db/sacred_plans/registry.json
fi

# Create a sample test to verify installation
print_message $YELLOW "🧪 Running environment verification..."
python3 << 'EOF'
import sys
print(f"Python version: {sys.version}")

# Check required packages
packages = {
    "google-genai": "Google AI SDK",
    "chromadb": "ChromaDB",
    "flask": "Flask",
    "watchdog": "File watcher",
    "tiktoken": "Token counter"
}

missing = []
for package, name in packages.items():
    try:
        __import__(package.replace("-", "_"))
        print(f"✅ {name} installed")
    except ImportError:
        print(f"❌ {name} not found")
        missing.append(name)

if missing:
    print(f"\n⚠️  Missing packages: {', '.join(missing)}")
else:
    print("\n✅ All required packages installed!")
EOF

# Show welcome message
print_message $GREEN "
============================================================================
🎉 ContextKeeper v3 DevContainer Setup Complete!
============================================================================

📍 Next Steps:
1. Configure your API keys in the .env file:
   - GOOGLE_API_KEY / GEMINI_API_KEY (required)
   - SACRED_APPROVAL_KEY (required for v3 features)
   
2. Start the ContextKeeper service:
   source venv/bin/activate
   python rag_agent.py start
   
   Or use the CLI:
   ./scripts/rag_cli_v2.sh server

3. Test the installation:
   python -m pytest tests/

4. Access the services:
   - http://localhost:5556 (ContextKeeper API)
   - The ports are automatically forwarded in Codespaces

📚 Documentation:
   - README.md - Project overview
   - docs/INSTALLATION.md - Detailed setup guide
   - docs/USAGE.md - How to use ContextKeeper
   - docs/TROUBLESHOOTING.md - Common issues
   - .devcontainer/README.md - Codespaces guide

🔧 Quick Commands:
   ./scripts/rag_cli_v2.sh projects list    # List projects
   ./scripts/rag_cli_v2.sh search \"query\"   # Search knowledge
   ./scripts/rag_cli_v2.sh context          # Get development context
   
💡 Development Tools:
   flake8 .                # Check code style
   black .                 # Format code
   pytest tests/ -v        # Run tests
   ipython                 # Interactive Python

============================================================================
"

# Check if .env has been configured
if [ -f ".env" ] && grep -q "your-google-ai-api-key-here" .env 2>/dev/null; then
    print_message $RED "
⚠️  WARNING: API keys are not configured!
Please edit the .env file and add your actual API keys:
   1. GOOGLE_API_KEY or GEMINI_API_KEY
   2. SACRED_APPROVAL_KEY

Without these keys, ContextKeeper will not function properly.
"
fi

# Show environment info
print_message $YELLOW "
🔍 Environment Information:
- Python: $(python --version 2>&1)
- Pip: $(pip --version)
- Virtual env: ${VIRTUAL_ENV:-Not activated}
- Working dir: $(pwd)
- Codespace: ${CODESPACES:-false}
"

# Run verification test if available
if [ -f ".devcontainer/test-setup.py" ]; then
    print_message $YELLOW "🧪 Running setup verification..."
    python .devcontainer/test-setup.py
fi

print_message $GREEN "✅ Setup complete! Happy coding! 🚀"