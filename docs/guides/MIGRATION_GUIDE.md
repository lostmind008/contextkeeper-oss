# Migration Guide: ContextKeeper v2.0 to v3.0 Sacred Layer

## Overview

ContextKeeper v3.0 introduces the Sacred Layer - immutable architectural plan storage with 2-layer verification. This upgrade maintains full backward compatibility with v2.0 multi-project functionality while adding sacred plan protection for AI collaboration.

## What's New in v3.0

### Major Features
- **Sacred Layer**: Immutable architectural plan storage with 2-layer verification
- **Drift Detection**: Real-time monitoring of development alignment with sacred plans
- **MCP Integration**: 8 sacred-aware tools for Claude Code integration
- **Git Activity Tracking**: Replace file watching with reliable git-based monitoring
- **LLM Enhancement**: Natural language responses for technical queries
- **Enhanced Security**: Environment key verification for plan approval

### Backward Compatibility
- All v2.0 multi-project functionality preserved
- Existing project configurations continue to work
- The API maintains compatibility with existing integrations
- Legacy CLI commands remain functional

## Quick Start

### 1. Environment Setup
Set up the Sacred Layer environment key:
```bash
# Set the sacred approval key
export SACRED_APPROVAL_KEY="your-secret-key"

# Start the Sacred Layer (port 5556)
python rag_agent.py start
```

### 2. Create Sacred Plans
```bash
# Create a sacred plan
./scripts/rag_cli.sh sacred create proj_123 "Database Architecture" db_plan.md

# Approve with 2-layer verification
./scripts/rag_cli.sh sacred approve plan_abc123
```

### 3. Monitor Drift Detection
```bash
# Check alignment with sacred plans
./scripts/rag_cli.sh sacred drift proj_123

# Query sacred context
./scripts/rag_cli.sh sacred query proj_123 "authentication approach"
```

### 4. Claude Code Integration
Configure MCP server in Claude Code settings:
```json
{
  "contextkeeper-sacred": {
    "type": "stdio",
    "command": "node",
    "args": ["[path]/mcp-server/enhanced_mcp_server.js"],
    "env": {"RAG_AGENT_URL": "http://localhost:5556"}
  }
}
```

## Command Changes

### Legacy Commands (Still Work)
```bash
./scripts/rag_cli.sh ask "What authentication system did I use?"
./scripts/rag_cli.sh add "Using CrewAI for multi-agent system"
./scripts/rag_cli.sh morning
```

### New v2.0 Commands
```bash
# Project management
./scripts/rag_cli.sh projects create|list|focus|pause|resume|archive

# Decision tracking
./scripts/rag_cli.sh decisions add "decision" "reasoning" "tags"

# Objective tracking
./scripts/rag_cli.sh objectives add|complete|list

# Context export
./scripts/rag_cli.sh context export
./scripts/rag_cli.sh briefing
```

## API Changes

### Query Endpoint
Now supports optional project filtering:
```bash
# Query specific project
curl -X POST http://localhost:5556/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Show auth code", "project_id": "proj_abc123"}'
```

### New Endpoints
```bash
# Project management
GET  /projects                    # List all projects
POST /projects                    # Create project
POST /projects/<id>/focus         # Focus project
PUT  /projects/<id>/status        # Update status
GET  /projects/<id>/context       # Export context

# Objectives
POST /projects/<id>/objectives    # Add objective
POST /projects/<id>/objectives/<oid>/complete
```

## Data Migration

### Automatic Migration
- Your existing ChromaDB collection is preserved
- A new project-specific collection is created for the imported YouTube Analyzer project
- Future ingestions will use the project-specific collection

### Manual Migration (Optional)
If you want to fully migrate old data to the new structure:
```bash
# Re-ingest your project files
./scripts/rag_cli.sh projects focus proj_<youtube_id>
python rag_agent.py ingest --path "/path/to/youtube-analyzer"
```

## Configuration Files

### New Configuration Location
Project configurations are now stored in:
```
~/.rag_projects/
├── proj_<id1>.json
├── proj_<id2>.json
└── ...
```

### Legacy Configuration
The old configuration in `rag_agent.py` is used only for initial import.

## Breaking Changes

None! v2.0 is fully backward compatible.

## Troubleshooting

### Agent Won't Start
```bash
# Check logs
tail -f ~/rag-agent/rag_agent.log

# Ensure virtual environment is activated
source ~/rag-agent/venv/bin/activate
```

### Projects Not Showing
```bash
# Check project directory
ls ~/.rag_projects/

# Restart agent
./scripts/rag_cli.sh restart
```

### Import Issues
If your YouTube Analyzer project wasn't imported:
1. Check that the directories exist
2. Manually create the project:
```bash
./scripts/rag_cli.sh projects create "YouTube Analyzer" "/path/to/project"
```

## Best Practices

1. **One Project Per Repository**: Create a project for each git repository
2. **Use Descriptive Names**: "YouTube Analyzer" instead of "project1"
3. **Set Objectives**: Track what you're working on
4. **Record Decisions**: Document architectural choices with reasoning
5. **Regular Context Export**: Use for AI pair programming

## Need Help?

- Check the updated [README.md](README.md)
- Review the [CHANGELOG.md](CHANGELOG.md)
- Examine the API documentation in the code

Welcome to RAG Agent v2.0! 🎉