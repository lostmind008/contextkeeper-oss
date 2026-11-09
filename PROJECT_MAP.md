# Project: ContextKeeper v3.0
Generated: 2025-08-06
Last Updated: 2025-08-08

## 🎯 Project Overview
ContextKeeper v3.0 is an AI-powered development context management system with multi-project support, sacred architectural principles, and real-time analytics. Built as a hybrid Python/Node.js system with a Flask backend and MCP integration.

## ✅ Governance Compliance Status
- ✅ PROJECT_MAP.md present and updated (August 2025)
- ✅ Directory-level CLAUDE.md files created and updated
- ✅ Documentation consolidated and updated
- ✅ Untracked files cleaned up: removed duplicate src/core/rag_agent.py, moved test_sample_project/ to .gitignore, removed empty src/utils/ directory

## Directory Structure
```
contextkeeper/
├── src/
│   ├── ck_analytics/            # Analytics and metrics service
│   ├── core/                    # Core system components
│   ├── sacred/                  # Sacred layer governance implementation
│   ├── tracking/                # Event and git activity tracking
│   └── scripts/                 # Utility scripts and fixes
├── scripts/
│   └── contextkeeper.sh         # Main CLI script
├── tests/                       # Comprehensive test suite
├── docs/
│   ├── USER_GUIDE.md
│   ├── ARCHITECTURE.md
│   └── api/
│       └── API_REFERENCE.md
├── mcp-server/                  # MCP integration for Claude Code
│   └── enhanced_mcp_server.js
├── projects/                    # Project state storage (4 test projects)
├── test_sample_project/         # Test fixture for development
├── analytics_dashboard_live.html # Main dashboard with WebSocket integration
├── rag_agent.py                 # Main RAG orchestrator (Flask API server)
└── README.md
```

## Key Files with Governance Context

### Core System Files
- **`rag_agent.py`**
  - Main orchestrator with Flask API server and Socket.IO for real-time updates.
  - Handles all RAG operations, project management, and serves the dashboard.
  - Dependencies: flask, chromadb, google.genai, flask-socketio.

- **`src/core/project_manager.py`**
  - Multi-project state management.
  - Tracks decisions, objectives, events.

### Sacred Layer
- **`src/sacred/sacred_layer_implementation.py`**
  - Implements immutable architectural decisions and the 2-layer approval system.

- **`src/sacred/enhanced_drift_sacred.py`**
  - Advanced drift detection engine.

### Analytics
- **`src/ck_analytics/analytics_service.py`**
  - Service layer for the `/analytics/sacred` endpoint.
- **`src/ck_analytics/sacred_metrics.py`**
  - Core logic for calculating governance metrics.

### Frontend
- **`analytics_dashboard_live.html`**
  - Real-time dashboard with WebSocket integration.
  - UI for project management, Sacred Plan approval, and global search.

### MCP Integration
- **`mcp-server/enhanced_mcp_server.js`**
  - Bridge for Claude Code integration.

## Development Workflow

1. **Start System**
   ```bash
   source venv/bin/activate
   python src/rag_agent.py server
   ```

2. **Create & Index Project (Async with Real-Time Updates)**
   ```bash
   ./scripts/contextkeeper.sh project add "/path/to/your/code" "My Project"
   ```
   - Project creation returns task_id immediately
   - Background indexing with progress events via WebSocket
   - Real-time UI updates in dashboard

3. **Interactive Usage**
   - **Dashboard**: Open `http://localhost:5556/analytics_dashboard_live.html`
   - **CLI**: Use `./scripts/contextkeeper.sh` for commands like `focus` and `query`
   - **WebSocket Events**: indexing_progress, indexing_complete, focus_changed, project_updated

4. **Key WebSocket Events**
   - `indexing_progress`: Real-time progress updates during project creation
   - `indexing_complete`: Notification when project is ready
   - `focus_changed`: When project focus changes via CLI or dashboard
   - `project_updated`: When project metadata changes
   - `decision_added`: When architectural decisions are tracked
   - `sacred_plan_created`: When new Sacred Plans are proposed
   - `sacred_plan_approved`: When plans receive governance approval

## Current System State (August 2025)

### Active Features ✅
- Async project creation with task_id tracking
- Real-time WebSocket events for UI updates
- Sacred Layer governance with 2-layer approval system
- ChromaDB isolation per project (no cross-contamination)
- MCP server integration for Claude Code
- Analytics service with governance metrics
- Interactive dashboard with live updates

### File Management Completed ✅
- `src/core/rag_agent.py` - Duplicate removed (main file remains in root)
- `test_sample_project/` - Added to .gitignore as test fixture
- `src/utils/` - Empty directory removed
- `src/scripts/__init__.py` - Unnecessary empty file removed

### Git Status
- Repository cleaned up: no untracked files requiring attention
- Main rag_agent.py remains in project root (functional)
- All core functionality operational and repository structure clean

## Next Governance Steps

1. **Enforcement Scripts** ✅ COMPLETED
   - Pre-commit hooks for governance are in place (`.pre-commit-config.yaml`).

2. **Documentation Lifecycle** ✅ COMPLETED (August 2025)
   - All documentation updated to reflect current system state
   - WebSocket events fully documented
   - Async workflows clearly explained

3. **File Management** ✅ COMPLETED (August 2025)
   - Cleaned up duplicate src/core/rag_agent.py
   - Added test_sample_project/ to .gitignore as test fixture
   - Removed empty src/utils/ directory and unnecessary __init__.py files

4. **Continuous Verification** (Ongoing)
   - Ensure documentation is kept in sync with new features
   - Monitor untracked files and maintain clean repository state
