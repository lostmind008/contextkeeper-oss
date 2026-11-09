# LostMind AI - ContextKeeper v3.0 Installation Guide

## Prerequisites

- **Python 3.8+** with pip
- **Node.js 16+** with npm (for MCP server)
- **Git** (for activity tracking)
- **Google Cloud account** (for GenAI API)

## Quick Installation

### 1. Clone and Setup
```bash
# Clone repository
git clone https://github.com/lostmind008/contextkeeper-v3.git
cd contextkeeper

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Create .env file
touch .env

# Edit with your values
nano .env
```

Required environment variables:
```bash
# Google Cloud (for embeddings and LLM)
GEMINI_API_KEY=your-gemini-api-key

# Sacred Layer (v3.0) - required, no default
SACRED_APPROVAL_KEY=your-secret-approval-key

# Optional: Analytics and Performance
ANALYTICS_CACHE_DURATION=300  # Cache duration in seconds (default: 300)
FLASK_ASYNC_MODE=True         # Enable async endpoints (default: True)
DEBUG=0                       # Set to 1 for debug logging
```

ContextKeeper will raise an error during plan approval if `SACRED_APPROVAL_KEY` is not set.

### 3. Verify Installation
```bash
# Start ContextKeeper (server-only mode recommended)
python rag_agent.py server

# Test basic functionality
./scripts/rag_cli_v2.sh projects list

# Test sacred layer
curl http://localhost:5556/sacred/plans

# Access the beautiful dashboard
open http://localhost:5556/analytics_dashboard_live.html
```

## Google Cloud Setup

### 1. Create Project and Enable APIs
```bash
# Install Google Cloud CLI
# Follow: https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login
gcloud auth application-default login

# Enable required APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable generativelanguage.googleapis.com
```

### 2. Get API Key
```bash
# Go to Google AI Studio: https://makersuite.google.com/app/apikey
# Create a new API key
# Copy the key to your .env file
```

### 3. Test API Access
```bash
# Test with curl
curl -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent \
  -d '{"contents":[{"parts":[{"text":"Hello, world!"}]}]}'
```

## Claude Code Integration

### 1. Configure MCP Server
Add to Claude Code MCP configuration:
```json
{
  "contextkeeper-sacred": {
    "type": "stdio",
    "command": "node",
    "args": ["/absolute/path/to/contextkeeper/mcp-server/enhanced_mcp_server.js"],
    "env": {
      "RAG_AGENT_URL": "http://localhost:5556"
    }
  }
}
```

### 2. Verify Integration
```bash
# Start ContextKeeper
python rag_agent.py server

# Test MCP tools in Claude Code
# Use: /mcp list_tools contextkeeper-sacred
```

## Beautiful Dashboard Setup

### 1. Access the Dashboard
Once ContextKeeper is running, open your browser to:
```
http://localhost:5556/analytics_dashboard_live.html
```

### 2. Dashboard Features
- **Interactive Three.js Background**: 4000 animated particles
- **Real-time Statistics**: Live project metrics and system health
- **Project Management**: Create, view, and focus projects
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Modern Dark Theme**: Glass morphism effects with color-coded indicators

### 3. Dashboard Requirements
- **Modern Browser**: Chrome, Firefox, Safari, or Edge
- **JavaScript Enabled**: Required for Three.js animations
- **WebGL Support**: For particle rendering (most modern browsers support this)

## Troubleshooting

### Common Issues

**Google Cloud Authentication:**
```bash
# Check API key is set
echo $GEMINI_API_KEY

# Test API access
curl -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GEMINI_API_KEY" \
  https://generativelanguage.googleapis.com/v1beta/models
```

**Server Not Starting:**
```bash
# Use server-only mode (recommended)
python rag_agent.py server

# Check for port conflicts
netstat -an | grep 5556

# Check logs
tail -f rag_agent.out
```

**Dashboard Not Loading:**
```bash
# Verify server is running
curl http://localhost:5556/health

# Check dashboard route
curl -I http://localhost:5556/analytics_dashboard_live.html

# Check browser console for JavaScript errors
```

**Sacred Layer Issues:**
```bash
# Check sacred key is set
echo $SACRED_APPROVAL_KEY

# Test sacred endpoints
curl http://localhost:5556/sacred/plans
```

**MCP Integration Issues:**
```bash
# Check MCP server
node mcp-server/enhanced_mcp_server.js --help

# Verify RAG agent connectivity
curl http://localhost:5556/health

# Check MCP server logs
tail -f mcp-server/mcp-server.log
```

### Directory Structure Issues
```bash
# Create required directories
mkdir -p ~/.rag_projects
mkdir -p rag_knowledge_db/sacred_plans
mkdir -p rag_knowledge_db/sacred_chromadb

# Fix permissions
chmod +x scripts/rag_cli_v2.sh
chmod +x scripts/sacred_cli_integration.sh
```

### Performance Issues
```bash
# Clear database if corrupted
rm -rf rag_knowledge_db
mkdir rag_knowledge_db

# Check disk space
df -h

# Monitor memory usage
ps aux | grep python

# Check ChromaDB status
ls -la rag_knowledge_db/
```

### Browser Compatibility
```bash
# Test WebGL support
# Visit: https://get.webgl.org/

# Test Three.js compatibility
# Visit: https://threejs.org/examples/

# Check browser console for errors
# Press F12 and check Console tab
```

## Development Setup

### 1. Development Environment
```bash
# Clone with development tools
git clone https://github.com/lostmind008/contextkeeper-v3.git
cd contextkeeper

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -r requirements.txt
pip install pytest pytest-cov black flake8

# Install Node.js dependencies for MCP server
cd mcp-server
npm install
cd ..
```

### 2. Development Mode
```bash
# Start with debug logging
DEBUG=1 python rag_agent.py server

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Format code
black rag_agent.py project_manager.py

# Lint code
flake8 rag_agent.py project_manager.py
```

### 3. Testing Dashboard
```bash
# Start server
python rag_agent.py server

# Test dashboard in different browsers
# Chrome, Firefox, Safari, Edge

# Test responsive design
# Resize browser window to test mobile/tablet views

# Test Three.js performance
# Monitor FPS in browser dev tools
```

## Production Deployment

### 1. Environment Setup
```bash
# Set production environment variables
export FLASK_ENV=production
export DEBUG=0
export ANALYTICS_CACHE_DURATION=300

# Use production WSGI server
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5556 rag_agent:app
```

### 2. Security Considerations
```bash
# Use strong sacred approval key
export SACRED_APPROVAL_KEY="your-very-secure-approval-key"

# Restrict file permissions
chmod 600 .env
chmod 700 rag_knowledge_db/

# Use HTTPS in production
# Configure reverse proxy with SSL termination
```

### 3. Monitoring
```bash
# Monitor server health
curl http://localhost:5556/health

# Check dashboard accessibility
curl -I http://localhost:5556/analytics_dashboard_live.html

# Monitor logs
tail -f rag_agent.out

# Check system resources
htop
df -h
```

## Next Steps

1. **Create Your First Project**: `./scripts/rag_cli_v2.sh projects create "My Project" /path/to/project`
2. **Access the Dashboard**: Open `http://localhost:5556/analytics_dashboard_live.html`
3. **Create Sacred Plan**: `./scripts/rag_cli_v2.sh sacred create proj_123 "Architecture" plan.md`
4. **Start Development**: Use Claude Code with MCP integration for AI-aware development

For usage examples, see [USAGE.md](USAGE.md).
For API documentation, see [docs/api/API_REFERENCE.md](api/API_REFERENCE.md).
