# ContextKeeper v3.0 Troubleshooting Guide

This guide covers common issues and their solutions based on fixes applied in July 2025. All issues listed here have been resolved in the current version.

## 🩺 Quick Health Check

Before troubleshooting, verify the system status:

```bash
# 1. Check server health
curl http://localhost:5556/health
# Expected: {"status":"healthy"}

# 2. Check if ContextKeeper is running
ps aux | grep "rag_agent.py"

# 3. Check Sacred Layer specifically
curl -X POST http://localhost:5556/sacred/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'

# 4. Test CLI functionality
./scripts/rag_cli_v2.sh projects list
```

## ✅ Resolved Issues (July 2025)

### CLI Merge Conflicts Fixed

**Issue**: CLI commands failing with git merge conflict errors
```bash
# Error message seen:
# <<<<<<< HEAD
# conflicting content
# >>>>>>> branch-name
```

**Root Cause**: Unresolved merge conflicts in rag_cli_v2.sh script

**Solution Applied**: ✅ FIXED
- All merge conflicts in `scripts/rag_cli_v2.sh` resolved
- Script now executes cleanly without conflict markers
- Port configuration standardised to 5556

**How to Use**:
```bash
# Always use the v2 script (not the old rag_cli.sh)
./scripts/rag_cli_v2.sh projects list
./scripts/rag_cli_v2.sh projects create "My Project" /path/to/project
./scripts/rag_cli_v2.sh ask "What is this project about?"
```

### Sacred Layer 500 Internal Server Errors Fixed

**Issue**: Sacred Layer endpoints returning 500 Internal Server Error
```bash
# Error when calling:
curl -X POST http://localhost:5556/sacred/query
# Response: 500 Internal Server Error
```

**Root Cause**: Incorrect ChromaDB filter syntax causing query failures

**Solution Applied**: ✅ FIXED
- Fixed ChromaDB filter formatting from:
  ```python
  # Before (broken):
  {"type": "sacred_plan", "status": "approved"}
  
  # After (working):
  {"$and": [{"type": "sacred_plan"}, {"status": "approved"}]}
  ```

**Verification**:
```bash
# This now works correctly:
curl -X POST http://localhost:5556/sacred/query \
  -H "Content-Type: application/json" \
  -d '{"query": "database architecture"}'
# Expected: JSON response with results
```

### Google GenAI API Version Compatibility Fixed

**Issue**: API calls failing with version compatibility errors
```bash
# Error messages:
# API version not supported
# Model not found: gemini-embedding-001
```

**Root Cause**: Using outdated API version (v1) instead of required v1beta

**Solution Applied**: ✅ FIXED
- Updated API configuration:
  ```python
  # Before (broken):
  HttpOptions(api_version="v1")
  
  # After (working):
  HttpOptions(api_version="v1beta")
  ```
- Model updated to `gemini-embedding-001` with proper v1beta compatibility

**Verification**:
```bash
# Check that embeddings are working:
./scripts/rag_cli_v2.sh projects create "test" /tmp
# Should complete without API errors
```

### ChromaDB Embedding Function Conflicts Fixed

**Issue**: Database initialization failing with embedding function errors
```bash
# Error messages:
# Embedding function conflict
# Cannot initialize ChromaDB
# Collection creation failed
```

**Root Cause**: Conflicting embedding function definitions in ChromaDB

**Solution Applied**: ✅ FIXED
- Complete ChromaDB reset performed
- Database recreated with compatible embedding functions
- Embedding model standardised to gemini-embedding-001

**Recovery Steps** (if you encounter similar issues):
```bash
# 1. Remove corrupted database
rm -rf rag_knowledge_db/chroma.sqlite3
rm -rf rag_knowledge_db/sacred_chromadb/

# 2. Restart ContextKeeper (will recreate database)
python rag_agent.py start

# 3. Verify database recreation
curl http://localhost:5556/health
```

### Path Filtering Not Working Fixed

**Issue**: System indexing unwanted files (venv, node_modules, etc.)
```bash
# Problem: Database polluted with:
# - Python virtual environment files
# - Node.js dependencies
# - Build artifacts
# - Binary files
```

**Root Cause**: Path filtering logic not properly excluding system directories

**Solution Applied**: ✅ FIXED
- Path filtering confirmed working correctly
- Comprehensive exclusion patterns active:
  ```python
  EXCLUDED_PATTERNS = [
      'venv/', 'node_modules/', '.git/', '__pycache__/',
      'build/', 'dist/', '.pytest_cache/', 'coverage/',
      '*.pyc', '*.pyo', '*.so', '*.exe', '*.dll'
  ]
  ```

**Verification**:
```bash
# Create a test project and verify filtering
./scripts/rag_cli_v2.sh projects create "filter_test" /path/with/venv
# Check logs show excluded paths being filtered out
```

## 🔧 Current Issue Resolution

### Server Won't Start

**Symptoms**:
- `python rag_agent.py start` fails
- Port 5556 unavailable
- Import errors

**Troubleshooting Steps**:
```bash
# 1. Check if port is already in use
lsof -i :5556
# If occupied, kill the process or use different port

# 2. Verify Python environment
source venv/bin/activate
python --version  # Should be 3.8+

# 3. Check dependencies
pip list | grep -E "(chromadb|google|flask)"

# 4. Test minimal startup
DEBUG=1 python rag_agent.py start
```

### API Calls Timing Out

**Symptoms**:
- Health check returns 200 but other endpoints timeout
- Long response times (>30 seconds)

**Troubleshooting Steps**:
```bash
# 1. Check server logs for errors
tail -f rag_agent.log

# 2. Test with minimal query
curl -X POST http://localhost:5556/query \
  -H "Content-Type: application/json" \
  -d '{"question": "test", "k": 1}' \
  --max-time 10

# 3. Check ChromaDB status
ls -la rag_knowledge_db/
# Should show chroma.sqlite3 and other files

# 4. Monitor resource usage
top -p $(pgrep -f rag_agent.py)
```

### Environment Configuration Issues

**Symptoms**:
- Google Cloud authentication failing
- Missing environment variables
- Permission errors

**Troubleshooting Steps**:
```bash
# 1. Verify .env file exists and is sourced
cat .env | grep -E "(GOOGLE|SACRED)"

# 2. Test Google Cloud credentials
gcloud auth application-default login
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# 3. Verify required environment variables
echo $GOOGLE_CLOUD_PROJECT
echo $GOOGLE_GENAI_USE_VERTEXAI

# 4. Check service account permissions
gcloud projects get-iam-policy $GOOGLE_CLOUD_PROJECT
```

### MCP Integration Not Working

**Symptoms**:
- Claude Code can't connect to MCP server
- Tools not available in Claude
- STDIO communication errors

**Troubleshooting Steps**:
```bash
# 1. Test MCP server directly
node mcp-server/enhanced_mcp_server.js

# 2. Check Claude Code MCP configuration
cat ~/.config/claude-code/mcp.json

# 3. Verify ContextKeeper is accessible
curl http://localhost:5556/health

# 4. Test MCP tools manually
echo '{"method": "tools/list"}' | node mcp-server/enhanced_mcp_server.js
```

## 🚨 Emergency Recovery Procedures

### Complete System Reset

If all else fails, perform a complete reset:

```bash
# 1. Stop all ContextKeeper processes
pkill -f rag_agent.py
pkill -f enhanced_mcp_server.js

# 2. Backup existing data (optional)
cp -r rag_knowledge_db/ backup_$(date +%Y%m%d)/

# 3. Clean installation
rm -rf venv/
rm -rf rag_knowledge_db/
rm -rf __pycache__/

# 4. Fresh setup
./setup.sh

# 5. Reconfigure environment
cp .env.backup .env  # If you have a backup
# Edit .env with correct credentials

# 6. Start fresh
source venv/bin/activate
python rag_agent.py start
```

### Data Recovery

If you need to recover from a backup:

```bash
# 1. Stop ContextKeeper
pkill -f rag_agent.py

# 2. Restore database
rm -rf rag_knowledge_db/
cp -r backup_20250729/rag_knowledge_db/ ./

# 3. Restart with recovered data
python rag_agent.py start

# 4. Verify data integrity
./scripts/rag_cli_v2.sh projects list
```

## 🆔 Getting Support

If you encounter issues not covered here:

### Information to Collect

Before seeking help, gather this information:

```bash
# 1. System information
python --version
node --version
uname -a

# 2. ContextKeeper status
curl http://localhost:5556/health

# 3. Error logs (last 50 lines)
tail -50 rag_agent.log

# 4. Process status
ps aux | grep -E "(rag_agent|enhanced_mcp)"

# 5. Environment check
env | grep -E "(GOOGLE|SACRED)" | sed 's/=.*/=***/'  # Hides secrets
```

### Support Channels

1. **GitHub Issues**: [https://github.com/lostmind008/contextkeeper/issues](https://github.com/lostmind008/contextkeeper/issues)
2. **Documentation**: [docs/](../docs/) - Check other guides first
3. **Community**: [GitHub Discussions](https://github.com/lostmind008/contextkeeper/discussions)

### Issue Template

When reporting issues, use this template:

```markdown
## Issue Description
Brief description of the problem

## Environment
- OS: [e.g., macOS 14.5]
- Python Version: [e.g., 3.11.5]
- ContextKeeper Version: [e.g., v3.0]

## Steps to Reproduce
1. Step one
2. Step two
3. Error occurs

## Expected Behavior
What should have happened

## Actual Behavior
What actually happened

## Error Messages
```
Paste any error messages here
```

## Additional Context
Any other relevant information
```

---

**Last Updated**: July 2025  
**Status**: All major issues resolved, system operational  
**Next Review**: February 2025 or when new issues are discovered