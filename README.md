# ContextKeeper v3.0
**AI-Powered Development Context Management for Software Engineering Teams**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![Node.js](https://img.shields.io/badge/Node.js-16%2B-green.svg)](https://nodejs.org)
[![Tests](https://img.shields.io/badge/Tests-72%25%20Passing-yellow.svg)](#testing-status)

ContextKeeper transforms how software engineering teams navigate complex, multi-repository codebases. Using RAG (Retrieval-Augmented Generation) with ChromaDB vector search and Google Gemini, it maintains intelligent context across your projects, tracks architectural decisions, and provides real-time development insights.

> **🚧 CURRENT STATUS (August 2025)**: v3.0 - **Local Development Ready**  
> ✅ Core RAG functionality working • ✅ Real-time dashboard • ⚠️ No authentication (local use only) • ⚠️ Some async issues in Sacred Layer

## 🎯 When to Use ContextKeeper

**Perfect for:**
- **Microservices teams** managing 5+ related repositories
- **Legacy codebase exploration** where documentation is scattered or outdated
- **Team onboarding** to complex systems with multiple interconnected components
- **Architectural decision tracking** across long-term projects
- **Context preservation** during developer handoffs or team transitions

**Not suitable for:**
- Single, well-documented repositories under 10,000 lines
- Real-time pair programming or live collaboration
- Production environments requiring authentication
- Highly sensitive codebases (no access control implemented)

## 💪 Current Capabilities

### ✅ **Proven Working Features**
- **📚 Multi-Project RAG**: Query multiple codebases with intelligent context isolation
- **🎨 Real-Time Dashboard**: WebSocket-powered UI showing live project status at `localhost:5556`
- **🤖 Natural Language Queries**: "How does authentication work in the payment service?"
- **⚡ Vector Search**: ChromaDB-powered semantic code search across your entire codebase
- **🏗️ Project Isolation**: Zero cross-contamination between different codebases
- **📊 Development Analytics**: Track coding patterns, file changes, and project health
- **🔒 Data Security**: Automatic API key redaction and secure local storage

### ⚠️ **Limitations & Known Issues** 
- **No Authentication**: Local use only - anyone with network access can query your code
- **Scale Unknown**: Not performance-tested beyond small-to-medium projects (< 100MB)
- **Sacred Layer Bugs**: Some async issues in architectural decision management (72% test pass rate)
- **API Costs**: Large codebases may incur significant Google Gemini API charges
- **Manual Project Setup**: Each codebase requires explicit indexing before use

## 🚀 Real-World SWE Scenario

**The Problem**: Your team inherited a microservices architecture with 8 repositories, inconsistent documentation, and no one remembers why certain design decisions were made.

**The Solution**: ContextKeeper indexes all repos and maintains queryable context:

```bash
# Setup (5 minutes)
git clone https://github.com/lostmind008/contextkeeper-oss.git
cd contextkeeper-oss/contextkeeper
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.template .env
# Edit .env: Add GEMINI_API_KEY and create SACRED_APPROVAL_KEY

# Start the system
python rag_agent.py server
# Dashboard now running at http://localhost:5556/analytics_dashboard_live.html

# Index your services (30 seconds each)
./scripts/contextkeeper.sh project add "/path/to/user-service" "User Service"
./scripts/contextkeeper.sh project add "/path/to/payment-service" "Payment Service" 
./scripts/contextkeeper.sh project add "/path/to/order-service" "Order Service"
# Watch real-time indexing progress in dashboard

# Start querying across all codebases
./scripts/contextkeeper.sh query "How do microservices communicate with each other?"
./scripts/contextkeeper.sh query "Where is user authentication implemented?"
./scripts/contextkeeper.sh query "What database schema changes happened in the last month?"
```

**Expected Results**:
- Semantic search finds relevant code across all 8 repositories
- Natural language answers with file references and code snippets
- Real-time dashboard shows project health and development activity
- Architectural decisions preserved in Sacred Layer (when working properly)

## ⚡ Installation & Setup

### Prerequisites
- Python 3.8+ and Node.js 16+ (for MCP server)
- Google Gemini API key (get from [AI Studio](https://aistudio.google.com/app/apikey))
- 2GB+ RAM for ChromaDB vector operations
- Local network access (no authentication implemented)

### 1. Core Installation
```bash
git clone https://github.com/lostmind008/contextkeeper-oss.git
cd contextkeeper-oss/contextkeeper

# Python environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Environment configuration
cp .env.template .env
```

### 2. Environment Variables (.env file)
```bash
# Required - Get from https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your-google-ai-api-key-here

# Required - Generate with: openssl rand -hex 32
SACRED_APPROVAL_KEY=your-secret-approval-key-minimum-32-characters

# Optional - defaults are fine for local use
# RAG_AGENT_URL=http://localhost:5556
# CHROMADB_PERSIST_DIR=./rag_knowledge_db
```

### 3. Start the System
```bash
# Terminal 1: Start backend server (required)
python rag_agent.py server
# Server starts on http://localhost:5556

# Terminal 2: Add your first project
./scripts/contextkeeper.sh project add "/path/to/your/code" "Project Name"
# Watch progress: open http://localhost:5556/analytics_dashboard_live.html
```

### 4. Verify Installation
```bash
# Test query functionality
./scripts/contextkeeper.sh query "What files contain main functions?"

# Check dashboard
curl http://localhost:5556/health
# Should return: {"status": "healthy", "projects": N}
```

## 💼 More SWE User Stories

### Story 1: Legacy System Detective
**Scenario**: New team member needs to understand a 50k-line legacy payment system with minimal documentation.

```bash
# Index the legacy system
./scripts/contextkeeper.sh project add "/path/to/payment-legacy" "Legacy Payment System"

# Natural exploration queries
./scripts/contextkeeper.sh query "What are the main payment processing flows?"
./scripts/contextkeeper.sh query "How are database transactions handled?"
./scripts/contextkeeper.sh query "Where are the security validations implemented?"
./scripts/contextkeeper.sh query "What external services does this system integrate with?"
```

**Result**: Developer gains system understanding in hours instead of weeks.

### Story 2: Multi-Team Architecture Alignment  
**Scenario**: Platform team managing shared libraries across 12 microservices needs to understand usage patterns.

```bash
# Index all services that use the shared library
for service in user-service order-service payment-service notification-service; do
  ./scripts/contextkeeper.sh project add "/path/to/$service" "$service"
done

# Cross-service analysis
./scripts/contextkeeper.sh query "How is the shared authentication library used across services?"
./scripts/contextkeeper.sh query "Which services have custom implementations of rate limiting?"
./scripts/contextkeeper.sh query "What database migration patterns are used?"
```

**Result**: Platform team identifies inconsistencies and creates unified standards.

### Story 3: Incident Response Context
**Scenario**: Production incident - need to quickly understand how error handling works across the distributed system.

```bash
# During incident - quick context gathering
./scripts/contextkeeper.sh query "How are HTTP 500 errors handled in the user service?"
./scripts/contextkeeper.sh query "What monitoring and alerting is configured for payment failures?"
./scripts/contextkeeper.sh query "Where are circuit breakers implemented?"
```

**Result**: Faster incident diagnosis with comprehensive context.

## 🏗️ Architecture & Technical Details

### System Flow
```
User Request → CLI/Dashboard → RAG Agent (Flask) → ChromaDB → Google Gemini
                    ↓              ↓               ↓
                Projects/      WebSocket      Vector Search
                JSON Files     Real-time      Embeddings
                    ↓              ↓               ↓
                Sacred Layer   Analytics     Code Context
                Decisions      Dashboard     Responses
```

### Core Components
1. **RAG Agent** (`rag_agent.py`): Flask API server on port 5556, handles all operations
2. **Project Manager** (`src/core/project_manager.py`): Multi-project state management
3. **Sacred Layer** (`src/sacred/sacred_layer_implementation.py`): Architectural governance (buggy)
4. **Analytics Service** (`src/ck_analytics/analytics_service.py`): Governance metrics
5. **MCP Integration** (`mcp-server/enhanced_mcp_server.js`): Bridge for Claude Code
6. **Dashboard** (`analytics_dashboard_live.html`): Real-time UI with WebSocket updates

### Data Storage
- **ChromaDB**: Vector embeddings stored in `./rag_knowledge_db/`
- **Project Metadata**: JSON files in `./projects/` directory
- **Sacred Layer**: Architectural decisions (when working)
- **Git Integration**: Tracks development activity and changes

## 🔧 Usage Examples

### Basic Project Management
```bash
# List all projects
./scripts/contextkeeper.sh project list

# Focus on specific project for queries
./scripts/contextkeeper.sh project focus
# Interactive selection menu

# Query focused project
./scripts/contextkeeper.sh query "Explain the database schema"

# Query specific project by name
./scripts/contextkeeper.sh query "How does caching work?" --project "E-commerce API"
```

### Advanced Queries
```bash
# Cross-file analysis
./scripts/contextkeeper.sh query "What files import the User model and how do they use it?"

# Security analysis
./scripts/contextkeeper.sh query "Show me all SQL queries and check for injection risks"

# Architecture analysis
./scripts/contextkeeper.sh query "Map the data flow from API endpoint to database"

# Performance analysis  
./scripts/contextkeeper.sh query "What are the most expensive database operations?"
```

### Dashboard Features
Access the dashboard at `http://localhost:5556/analytics_dashboard_live.html`:

- **Real-time Project Status**: See indexing progress, query activity
- **Development Analytics**: Code change patterns, file modification heat maps
- **Sacred Layer Management**: Create and approve architectural decisions (when working)
- **Multi-Project Overview**: Switch between projects, compare metrics

## 📊 Performance & Scale Characteristics

### What We Know Works
- **Small Projects**: < 5MB, < 1000 files - excellent performance
- **Medium Projects**: 5-50MB, 1000-10000 files - good performance
- **Query Response**: Typically 2-8 seconds for complex queries
- **Concurrent Users**: 1-3 users tested, WebSocket stability good

### Scale Unknowns (Use with Caution)
- **Large Codebases**: > 50MB, > 10000 files - not tested
- **Memory Usage**: ChromaDB memory requirements at scale unknown
- **API Costs**: Google Gemini costs can escalate with large embedding sets
- **Network Latency**: WebSocket performance under load not tested

### Cost Estimates (Google Gemini API)
- **Small Project** (< 1000 files): ~$1-5 for initial indexing
- **Medium Project** (< 10000 files): ~$10-50 for initial indexing  
- **Ongoing Queries**: ~$0.01-0.10 per complex query

## 🧪 Testing Status

Current test results from `pytest tests/ -v`:
```
===== 115 passed, 25 failed, 1 skipped, 53 warnings, 19 errors =====
```

### ✅ **Working Test Categories** (115 passing)
- CLI integration and command validation
- Multi-project isolation workflows
- Git activity tracking
- Sacred drift detection and monitoring
- Path filtering and security validation
- Basic RAG query functionality

### ❌ **Known Test Failures** (25 failed, 19 errors)
- Sacred Layer async operations (create_plan, approval workflow)
- End-to-end Sacred integration tests
- Some analytics endpoint tests
- Frontend modal integration tests
- Performance integration tests

### ⚠️ **Implications for Users**
- **Core RAG functionality is reliable** - use with confidence
- **Sacred Layer features are experimental** - expect issues
- **Multi-project isolation works well** - safe for production use
- **CLI and dashboard are stable** - good user experience

## 🔒 Security Considerations

### Current Security Status
✅ **Security vulnerabilities patched** (OWASP Top 10 fixes applied)  
✅ **Input validation implemented** for all user inputs  
✅ **API key redaction working** - secrets automatically cleaned from logs  
✅ **Path traversal protection** - file access properly sandboxed  
❌ **No authentication system** - anyone with network access can query  
❌ **No authorisation controls** - all users have full access  
❌ **No audit logging** - user actions not tracked  

### Recommended Usage Patterns
- **Local development only** - do not expose to public networks
- **Trusted team members** - assume anyone on network has full access
- **Non-sensitive codebases** - avoid using with proprietary or secret code
- **Regular API key rotation** - monitor Gemini API usage and costs

### Network Security
```bash
# Bind to localhost only (default)
CONTEXTKEEPER_HOST=127.0.0.1  # Never use 0.0.0.0 in production

# Use firewall to restrict access if needed
# Only allow specific IPs to connect to port 5556
```

## 🛠️ Troubleshooting

### Common Issues

**Server won't start**
```bash
# Check if port 5556 is in use
lsof -i :5556

# Kill existing process
kill -9 <PID>

# Start with different port
CONTEXTKEEPER_PORT=5557 python rag_agent.py server
```

**Project indexing fails**
```bash
# Check disk space (ChromaDB needs storage)
df -h

# Check API key is valid
curl -H "Authorization: Bearer $GEMINI_API_KEY" \
     https://generativelanguage.googleapis.com/v1beta/models

# Clear ChromaDB and retry
rm -rf ./rag_knowledge_db/
./scripts/contextkeeper.sh project add "/path/to/code" "Project Name"
```

**Dashboard not loading**
```bash
# Verify server is running
curl http://localhost:5556/health

# Check browser console for WebSocket errors
# Open developer tools → Console

# Try different browser (WebSocket compatibility)
```

**High API costs**
```bash
# Monitor usage in Google Cloud Console
# Set billing alerts to avoid surprises

# Reduce embedding frequency for large projects
# Focus on specific directories instead of entire codebase
```

**Sacred Layer errors**
```bash
# Sacred Layer has known async issues - expected behavior
# Core RAG functionality still works fine

# Check test results for current status
pytest tests/sacred/ -v
```

### Getting Help

1. **Check test results**: `pytest tests/ -v` shows current functionality status
2. **Review logs**: Server logs show detailed error information  
3. **Dashboard health check**: `curl http://localhost:5556/health`
4. **API key validation**: Ensure Gemini API key has proper permissions
5. **File an issue**: Include test results and error logs

## 📖 Documentation

For more detailed information:
- **[USER_GUIDE.md](docs/USER_GUIDE.md)**: Comprehensive feature walkthrough
- **[ARCHITECTURE.md](ARCHITECTURE.md)**: Technical deep-dive and design decisions
- **[API_REFERENCE.md](docs/api/API_REFERENCE.md)**: Complete API documentation
- **[SECURITY_IMPLEMENTATION.md](SECURITY_IMPLEMENTATION.md)**: Security fixes and hardening

## 🤝 Contributing

ContextKeeper is under active development. Key areas needing improvement:
1. **Authentication system** - implement user management and access control
2. **Sacred Layer stability** - fix async issues in architectural decision management
3. **Performance testing** - validate behaviour with large codebases
4. **Scale optimization** - improve ChromaDB performance and memory usage
5. **Test coverage** - increase test pass rate from current 72%

## 📜 License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.

---

**Status**: Local development ready • **Next milestone**: Authentication system • **Test coverage**: 72% • **Production readiness**: Not recommended

---

Built by [LostMind AI](https://www.lostmindai.com). ContextKeeper v3, published as a clean snapshot.
