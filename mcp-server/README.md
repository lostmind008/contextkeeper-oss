# ContextKeeper Sacred Layer MCP Server v3.0

## Overview

This MCP server provides Claude Code and other AI assistants with sacred-aware development context from ContextKeeper v3.0. It enables AI agents to understand and respect architectural constraints defined in sacred plans.

## Features

### Sacred Layer Tools (Phase 3)
- **`get_sacred_context`** - Access sacred architectural plans for AI-aware development  
- **`check_sacred_drift`** - Real-time violation detection against sacred plans
- **`query_with_llm`** - Natural language responses using Phase 2.5 LLM enhancement
- **`export_development_context`** - Complete project context with sacred awareness
- **`create_sacred_plan`** - Create new architectural plans (requires approval)

### Enhanced Development Tools
- **`get_development_context`** - Comprehensive project status with sacred layer integration
- **`intelligent_search`** - Semantic search across code, decisions, and sacred plans
- **`health_check`** - Monitor sacred layer and RAG agent status

## Requirements

- **Node.js**: >=18.0.0
- **ContextKeeper RAG Agent**: Running on port 5556 (or set RAG_AGENT_URL)
- **Sacred Layer**: Phase 2 implementation active
- **LLM Enhancement**: Phase 2.5 implementation active

## Installation

```bash
# Navigate to MCP server directory
cd mcp-server

# Install dependencies
npm install

# Test server functionality
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}' | node enhanced_mcp_server.js
```

## Claude Code Integration

### Add to Claude Code Configuration

```bash
# Method 1: Using Claude Code CLI
claude mcp add contextkeeper-sacred "node /full/path/to/contextkeeper/mcp-server/enhanced_mcp_server.js"

# Method 2: Manual configuration in ~/.config/claude-code/config.json
{
  "mcpServers": {
    "contextkeeper-sacred": {
      "command": "node",
      "args": ["/full/path/to/contextkeeper/mcp-server/enhanced_mcp_server.js"],
      "env": {
        "RAG_AGENT_URL": "http://localhost:5556"
      }
    }
  }
}
```

### Environment Variables

```bash
# Set RAG agent URL (default: http://localhost:5556)
export RAG_AGENT_URL="http://localhost:5556"

# Ensure sacred approval key is set (for creating plans)
export SACRED_APPROVAL_KEY="your-sacred-key"
```

## Usage Examples

### Get Sacred Context
Query architectural constraints for AI-aware development:

```json
{
  "tool": "get_sacred_context",
  "arguments": {
    "project_id": "proj_6cafffed59ba",
    "plan_status": "approved"
  }
}
```

### Check Sacred Drift
Verify development aligns with sacred plans:

```json
{
  "tool": "check_sacred_drift", 
  "arguments": {
    "project_id": "proj_6cafffed59ba",
    "hours": 24
  }
}
```

### Natural Language Query
Use Phase 2.5 LLM enhancement for conversational responses:

```json
{
  "tool": "query_with_llm",
  "arguments": {
    "question": "How does the 2-layer verification system work?",
    "k": 5
  }
}
```

### Export Development Context
Get complete context for AI agents:

```json
{
  "tool": "export_development_context",
  "arguments": {
    "project_id": "proj_6cafffed59ba",
    "include_sacred": true,
    "include_drift": true
  }
}
```

## Health Monitoring

Check system status:

```bash
# Test MCP server health
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "health_check", "arguments": {}}}' | node enhanced_mcp_server.js
```

Expected response shows:
- ✅ RAG Agent: healthy
- ✅ Sacred Layer: Active  
- ✅ LLM Enhancement: Active
- ✅ MCP Server: 8 tools available

## Architecture

### Data Flow
```
Claude Code → MCP Server → RAG Agent (port 5556) → Sacred Layer
                ↓                    ↓                    ↓
        AI-aware context    Natural language    Sacred plans
                                responses       & drift analysis
```

### Sacred Layer Integration
- **Immutable Plans**: Approved sacred plans cannot be modified
- **2-Layer Verification**: Plans require verification code + approval key
- **Real-time Drift**: Continuous monitoring against sacred constraints
- **AI Compliance**: Prevents AI agents from violating architectural decisions

### Caching Strategy
- **5-minute cache** for expensive operations
- **Context export** cached for performance
- **Sacred drift analysis** cached to reduce load
- **Health checks** not cached for real-time status

## Troubleshooting

### Common Issues

**MCP Server Won't Start**
```bash
# Check Node.js version
node --version  # Should be >=18.0.0

# Check dependencies
npm install

# Check RAG agent connectivity  
curl http://localhost:5556/health
```

**Sacred Layer Tools Failing**
```bash
# Verify sacred layer is active
curl http://localhost:5556/sacred/health

# Test sacred endpoints directly
curl http://localhost:5556/sacred/drift/proj_6cafffed59ba
```

**LLM Enhancement Not Working**
```bash
# Test LLM endpoint directly
curl -X POST http://localhost:5556/query_llm \
  -H "Content-Type: application/json" \
  -d '{"question": "test", "k": 1}'
```

### Debug Mode

Run with additional logging:
```bash
# Enable debug output
DEBUG=* node enhanced_mcp_server.js

# Or check stderr for status messages
node enhanced_mcp_server.js 2>&1 | grep "Sacred Layer"
```

## Development

### Adding New Tools

1. Add tool definition to `setupToolHandlers()` tools array
2. Add case to tool call handler switch statement  
3. Implement tool method following naming convention
4. Update README with tool documentation
5. Test with MCP protocol messages

### Testing Tools

```bash
# Test tool listing
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}' | node enhanced_mcp_server.js

# Test specific tool
echo '{"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "tool_name", "arguments": {}}}' | node enhanced_mcp_server.js
```

## Success Criteria (Phase 3)

- [x] MCP server running and responding to tool calls
- [x] Claude Code can query sacred plans through MCP  
- [x] Sacred drift detection accessible via MCP tools
- [x] Real-time development context export working
- [x] AI agent compliance with sacred constraints verified
- [x] Natural language responses via LLM enhancement
- [x] Health monitoring for all components
- [x] Comprehensive documentation and examples

## Support

For issues with the MCP server:
1. Check health status with `health_check` tool
2. Verify RAG agent is running on port 5556
3. Ensure sacred layer implementation is active
4. Review error messages in stderr output

## Version History

- **v3.0.0** - Sacred Layer integration with 8 tools
- **v2.5.0** - LLM enhancement integration  
- **v2.0.0** - Enhanced development context
- **v1.0.0** - Basic MCP server functionality