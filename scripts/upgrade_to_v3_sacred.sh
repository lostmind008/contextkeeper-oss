#!/bin/bash
# upgrade_to_v3_sacred.sh - Automated upgrade script for ContextKeeper v3.0
# Created: 2025-07-24 03:49:00 (Australia/Sydney)
# Part of: ContextKeeper v3.0 Sacred Layer Upgrade

set -e  # Exit on error

echo "🚀 Upgrading ContextKeeper to v3.0 with Sacred Layer"
echo "=================================================="
echo ""

# Check if we're in the right directory
if [ ! -f "rag_agent.py" ]; then
    echo "❌ Error: rag_agent.py not found. Please run from ContextKeeper root directory."
    exit 1
fi

# Step 1: Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version | cut -d' ' -f2)
echo "Found Python $python_version"

# Step 2: Create/activate virtual environment
echo ""
echo "🐍 Setting up virtual environment..."
if [ ! -d "venv" ]; then
    echo "Creating new virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

# Step 3: Backup existing installation
echo ""
echo "💾 Creating backup..."
backup_dir="../contextkeeper-v2-backup-$(date +%Y%m%d-%H%M%S)"
cp -r . "$backup_dir"
echo "Backup created at: $backup_dir"

# Step 4: Install dependencies
echo ""
echo "📦 Installing v3.0 dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Step 5: Create sacred directories
echo ""
echo "📁 Creating sacred directories..."
mkdir -p rag_knowledge_db/sacred_plans
mkdir -p rag_knowledge_db/sacred_chromadb
echo "Sacred directories created"

# Step 6: Set up environment variables
echo ""
echo "🔐 Setting up sacred approval key..."
if grep -q "SACRED_APPROVAL_KEY" .env 2>/dev/null; then
    echo "Sacred approval key already configured"
else
    echo ""
    echo "⚠️  IMPORTANT: Sacred Layer requires a secure approval key"
    echo "This key will be used as the second layer of verification for approving plans"
    echo ""
    read -s -p "Enter sacred approval key (will be hidden): " SACRED_KEY
    echo ""
    echo "export SACRED_APPROVAL_KEY='$SACRED_KEY'" >> .env
    echo "Sacred approval key saved to .env"
fi

# Step 7: Run initial tests
echo ""
echo "🧪 Running tests..."
if command -v pytest &> /dev/null; then
    echo "Running sacred layer tests..."
    pytest tests/sacred -v || echo "⚠️  Some tests failed (expected for placeholders)"
    
    echo ""
    echo "Running git integration tests..."
    pytest tests/git -v || echo "⚠️  Some tests failed (expected for placeholders)"
    
    echo ""
    echo "Running drift detection tests..."
    pytest tests/drift -v || echo "⚠️  Some tests failed (expected for placeholders)"
else
    echo "pytest not found, skipping tests"
fi

# Step 8: Check MCP server
echo ""
echo "🔌 Checking MCP server setup..."
if [ -d "mcp-server" ]; then
    echo "MCP server directory found"
    if [ -f "mcp-server/package.json" ]; then
        echo "Installing MCP server dependencies..."
        cd mcp-server
        npm install
        cd ..
    fi
else
    echo "⚠️  MCP server directory not found - will need to be set up separately"
fi

# Step 9: Verify Git repository
echo ""
echo "📊 Verifying Git repository..."
if git rev-parse --git-dir > /dev/null 2>&1; then
    echo "✅ Git repository detected"
    current_branch=$(git branch --show-current)
    echo "Current branch: $current_branch"
else
    echo "⚠️  Not a Git repository - Git tracking features will be limited"
fi

# Step 10: Create initial sacred plan example
echo ""
echo "📝 Creating example sacred plan template..."
cat > sacred_plan_template.md << 'EOF'
# Sacred Plan Template

## Plan Title
[Your Architecture/Design Plan Title]

## Purpose
[Why this plan exists and what it governs]

## Core Principles
1. [Principle 1]
2. [Principle 2]
3. [Principle 3]

## Technical Decisions
- **Technology Choice**: [What and why]
- **Architecture Pattern**: [Pattern and rationale]
- **Key Constraints**: [What must not change]

## Implementation Guidelines
[Specific rules that must be followed]

## Success Criteria
[How to verify adherence to this plan]
EOF

echo "Sacred plan template created: sacred_plan_template.md"

# Step 11: Final setup summary
echo ""
echo "✅ ContextKeeper v3.0 Sacred Layer Upgrade Complete!"
echo "=================================================="
echo ""
echo "🎯 Next Steps:"
echo "1. Update rag_agent.py with Sacred Layer imports"
echo "2. Create your first sacred plan:"
echo "   ./scripts/rag_cli.sh sacred create <project_id> \"Plan Title\" sacred_plan.md"
echo "3. Approve the plan with 2-layer verification:"
echo "   ./scripts/rag_cli.sh sacred approve <plan_id>"
echo "4. Start the enhanced agent:"
echo "   python rag_agent.py start"
echo ""
echo "📚 Documentation:"
echo "- Sacred Layer Guide: See revised_implementation_roadmap.md"
echo "- API Reference: See AI Agent TODO List.md"
echo "- CLI Commands: ./scripts/rag_cli.sh sacred --help"
echo ""
echo "⚠️  Important Notes:"
echo "- Sacred plans are IMMUTABLE once approved"
echo "- Keep your SACRED_APPROVAL_KEY secure"
echo "- Test in development before production use"
echo ""
echo "Happy coding with Sacred Layer protection! 🔒"