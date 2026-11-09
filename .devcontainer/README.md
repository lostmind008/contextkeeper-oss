# ContextKeeper v3 - GitHub Codespaces & Dev Container Guide

Welcome to ContextKeeper v3! This guide will help you get started quickly with GitHub Codespaces or VS Code Dev Containers.

## 🚀 Quick Start (GitHub Codespaces)

### 1. Open in Codespaces
- Click the green "Code" button on the repository
- Select "Codespaces" tab
- Click "Create codespace on main"
- Wait for the container to build (first time takes ~3-5 minutes)

### 2. Configure API Keys
Once the Codespace is ready, you'll need to add your API keys:

```bash
# The setup script has already created a .env file
# Edit it to add your keys:
nano .env

# Or use VS Code's editor:
code .env
```

Add these required keys:
```env
GOOGLE_API_KEY=your-google-ai-api-key-here
GEMINI_API_KEY=your-gemini-api-key-here  # Can be same as GOOGLE_API_KEY
SACRED_APPROVAL_KEY=your-secret-approval-key-minimum-32-characters
```

### 3. Start ContextKeeper
```bash
# The virtual environment is already activated
# Start the service:
python rag_agent.py start

# Or use the CLI:
./scripts/rag_cli_v2.sh server
```

### 4. Test the Installation
Open a new terminal (Terminal → New Terminal) and run:
```bash
# List projects
./scripts/rag_cli_v2.sh projects list

# Search for information
./scripts/rag_cli_v2.sh search "your search query"

# Get development context
./scripts/rag_cli_v2.sh context
```

## 🛠️ VS Code Dev Containers (Local Development)

### Prerequisites
- Docker Desktop installed and running
- VS Code with Remote-Containers extension
- Git

### Setup Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/lostmind008/contextkeeper-v3.git
   cd contextkeeper-v3
   ```

2. Open in VS Code:
   ```bash
   code .
   ```

3. When prompted, click "Reopen in Container" or:
   - Press `F1` or `Cmd/Ctrl+Shift+P`
   - Type "Remote-Containers: Reopen in Container"
   - Press Enter

4. Wait for container build (first time takes ~5-10 minutes)

5. Follow steps 2-4 from the Codespaces section above

## 🔑 API Key Configuration

### Getting API Keys

1. **Google AI API Key**:
   - Visit https://aistudio.google.com/app/apikey
   - Click "Create API Key"
   - Copy the key to your .env file

2. **Sacred Approval Key**:
   - Generate a secure random string (32+ characters)
   - Example: `openssl rand -hex 32`
   - This is used for v3's Sacred Layer security features

### Using GitHub Codespaces Secrets (Recommended)

Instead of editing .env directly, you can use Codespaces secrets:

1. Go to GitHub Settings → Codespaces → Secrets
2. Add these repository secrets:
   - `GOOGLE_API_KEY`
   - `GEMINI_API_KEY`
   - `SACRED_APPROVAL_KEY`

3. In your Codespace, access them:
   ```bash
   # They're automatically available as environment variables
   echo $GOOGLE_API_KEY  # Should show your key
   ```

## 📁 Project Structure

```
contextkeeper-v3/
├── .devcontainer/          # Dev container configuration
│   ├── devcontainer.json   # Container settings
│   ├── setup.sh           # Setup script (runs automatically)
│   └── README.md          # This file
├── rag_agent.py           # Main ContextKeeper service
├── scripts/               # CLI scripts
│   ├── rag_cli_v2.sh     # Primary CLI interface
│   └── sacred_cli_integration.sh  # Sacred layer CLI
├── rag_knowledge_db/      # ChromaDB storage
├── logs/                  # Application logs
├── tests/                 # Test suite
└── docs/                  # Documentation
```

## 🧪 Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html

# Run specific test category
python -m pytest tests/unit/
python -m pytest tests/integration/
python -m pytest tests/sacred/

# Run in watch mode (auto-rerun on changes)
python -m pytest tests/ --watch
```

## 🔧 Common Commands

### ContextKeeper CLI
```bash
# Project management
./scripts/rag_cli_v2.sh projects list
./scripts/rag_cli_v2.sh projects add /path/to/project
./scripts/rag_cli_v2.sh projects remove project-name

# Search and context
./scripts/rag_cli_v2.sh search "search query"
./scripts/rag_cli_v2.sh context
./scripts/rag_cli_v2.sh drift check

# Sacred layer (v3 features)
./scripts/sacred_cli_integration.sh plan "Create new API endpoint"
./scripts/sacred_cli_integration.sh approve <plan-id>
```

### Development Tools
```bash
# Code formatting
black .

# Linting
flake8 .

# Type checking (if mypy installed)
mypy .

# Interactive Python with project context
ipython
```

## 🐛 Troubleshooting

### Port Already in Use
If you see "Address already in use" errors:
```bash
# Find process using port 5556
lsof -i :5556

# Kill the process
kill -9 <PID>

# Or use a different port
CONTEXTKEEPER_PORT=5557 python rag_agent.py start
```

### API Key Issues
```bash
# Verify your keys are loaded
python -c "import os; print('API Key set:', bool(os.getenv('GOOGLE_API_KEY')))"

# Test API connection
python -c "from google import genai; genai.configure(api_key=os.getenv('GOOGLE_API_KEY')); print('API connected!')"
```

### ChromaDB Issues
```bash
# Reset the database
rm -rf rag_knowledge_db/
mkdir -p rag_knowledge_db
python rag_agent.py start  # Will recreate DB
```

### Virtual Environment Issues
```bash
# Reactivate virtual environment
source venv/bin/activate

# Verify it's active
which python  # Should show venv/bin/python
```

## 🌐 Accessing Services

In GitHub Codespaces, all ports are automatically forwarded:

- **ContextKeeper API**: Click on "Ports" tab → Port 5556 → Open in Browser
- **Direct URL**: `https://<codespace-name>-5556.app.github.dev`

For local Dev Containers:
- **ContextKeeper API**: http://localhost:5556
- **Swagger UI**: http://localhost:5556/api/docs (if enabled)

## 📚 Additional Resources

- **Main Documentation**: [docs/](../docs/)
- **Installation Guide**: [docs/INSTALLATION.md](../docs/INSTALLATION.md)
- **Usage Guide**: [docs/USAGE.md](../docs/USAGE.md)
- **API Reference**: [docs/api/API_REFERENCE.md](../docs/api/API_REFERENCE.md)
- **Troubleshooting**: [docs/TROUBLESHOOTING.md](../docs/TROUBLESHOOTING.md)

## 💡 Tips for Codespaces

1. **Preserve Work**: Codespaces auto-suspend after 30 minutes of inactivity. Your work is preserved, but services stop.

2. **Restart Services**: After resuming a Codespace:
   ```bash
   source venv/bin/activate
   python rag_agent.py start
   ```

3. **Share Your Codespace**: You can make ports public to share with teammates:
   - Ports tab → Right-click port 5556 → Port Visibility → Public

4. **Use Prebuild**: For faster startup, enable Codespaces prebuilds in repository settings.

5. **VS Code Settings Sync**: Your VS Code settings sync to Codespaces automatically.

## 🤝 Getting Help

- **GitHub Issues**: Report bugs or request features
- **Documentation**: Check docs/ directory for detailed guides
- **Logs**: Check `rag_agent.log` for service logs
- **Debug Mode**: Set `FLASK_DEBUG=1` in .env for detailed errors

---

Happy coding with ContextKeeper v3! 🚀

*Note: This guide is optimised for GitHub Codespaces but works equally well with local VS Code Dev Containers.*