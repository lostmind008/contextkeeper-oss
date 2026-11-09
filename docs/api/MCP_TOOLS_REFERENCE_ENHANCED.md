# ContextKeeper Enhanced MCP Tools - Complete Reference Guide

**Version**: 2.0.0 Enhanced  
**Date**: 2025-07-29  
**MCP Server**: `/mcp-server/enhanced_mcp_server.js`

This document provides comprehensive documentation for all 9 MCP tools available in the ContextKeeper Enhanced integration, including their capabilities, usage examples, internal component connections, and practical applications.

---

## 🎯 Overview

The ContextKeeper Enhanced MCP server provides 9 powerful tools that integrate directly with Claude Code and other AI assistants. These tools bridge the gap between AI agents and your development context, providing rich contextual information, development insights, and intelligent assistance.

### Tool Categories

1. **Context & Analysis Tools**
   - `get_development_context` - Comprehensive project status
   - `intelligent_search` - Semantic search across all content
   - `analyze_git_activity` - Git activity analysis
   - `check_development_drift` - Alignment monitoring

2. **Project Management Tools**
   - `manage_objectives` - Add, update, complete project goals
   - `track_decision` - Record architectural decisions
   - `suggest_next_action` - AI-powered task suggestions

3. **Development Support Tools**
   - `get_code_context` - Feature implementation guidance
   - `daily_briefing` - Comprehensive project overview

---

## 🔧 Tool Detailed Documentation

## 1. get_development_context

### Purpose
Provides comprehensive development context including project status, git activity, objectives, decisions, and drift analysis for AI-assisted development.

### Internal Components
- **Primary**: RAG Agent endpoint `/context/export`
- **Git Integration**: Git activity analysis
- **Drift Analysis**: Development alignment checking

### Parameters
```json
{
  "project_id": "string (optional)",
  "include_git": "boolean (default: true)",
  "include_drift": "boolean (default: true)",
  "hours": "number (default: 24)"
}
```

### Usage Examples

#### Full Development Context
```json
{
  "tool": "get_development_context",
  "arguments": {
    "project_id": "myproject_123",
    "include_git": true,
    "include_drift": true,
    "hours": 48
  }
}
```

#### Context Without Git Activity
```json
{
  "tool": "get_development_context",
  "arguments": {
    "project_id": "myproject_123",
    "include_git": false,
    "hours": 24
  }
}
```

### Response Format
```markdown
# Comprehensive Development Context

## Project: My Project
**Status**: active
**Path**: /Users/username/myproject

## Recent Decisions
- Use JWT for authentication (2 days ago)
  - Reasoning: Better security and stateless design

## Active Objectives
1. **Implement user management** (high priority)
   - Status: in_progress
   - Created: 3 days ago

## Git Activity (Last 24 hours)
- 5 commits on main branch
- Files modified: auth/jwt_manager.py, models/user.py
- Latest: "Add JWT token validation"

## Development Drift Analysis
**Status**: ALIGNED
**Score**: 92%
- Development following planned objectives
- Minor suggestions for improvement
```

### When to Use
- **Start of development sessions** - Understand current project state
- **Code review preparation** - Get complete context
- **AI pair programming** - Provide AI assistant with full project understanding
- **Status reporting** - Generate comprehensive project summaries

### Caching
- **Cached**: Yes (5 minutes)
- **Cache Key**: `get_development_context-{project_id}-{include_git}-{include_drift}-{hours}`

---

## 2. intelligent_search

### Purpose
Performs semantic search across code, decisions, objectives, and git history using natural language queries, powered by AI enhancement for contextual understanding.

### Internal Components
- **Primary**: RAG Agent search endpoints
- **Search Engine**: Vector database with semantic embeddings
- **Content Types**: Code files, decisions, objectives, git activity

### Parameters
```json
{
  "query": "string (required)",
  "search_types": "array (default: ['all'])",
  "project_id": "string (optional)",
  "max_results": "number (default: 5)"
}
```

#### Search Types
- **`code`**: Source code files, comments, documentation
- **`decisions`**: Architectural decisions and reasoning
- **`objectives`**: Development goals and milestones
- **`git_activity`**: Git commits and changes
- **`all`**: Search across all content types

### Usage Examples

#### Cross-Content Search
```json
{
  "tool": "intelligent_search",
  "arguments": {
    "query": "authentication implementation approach",
    "search_types": ["all"],
    "max_results": 5
  }
}
```

#### Code-Specific Search
```json
{
  "tool": "intelligent_search",
  "arguments": {
    "query": "JWT token validation logic",
    "search_types": ["code"],
    "max_results": 10
  }
}
```

### Response Format
```markdown
# Search Results for: authentication implementation approach

## Code Results (3 found)
1. **auth/jwt_manager.py** (95% match)
   - JWT token generation and validation
   - Contains `generate_token()` and `validate_token()` methods

2. **middleware/auth_middleware.py** (87% match)
   - Authentication middleware for API routes
   - Implements token verification

## Decision Results (1 found)
1. **Use JWT for authentication** (2 days ago)
   - Reasoning: Stateless, secure, industry standard
   - Alternatives considered: Sessions, OAuth2

## Objective Results (1 found)
1. **Implement secure authentication** (high priority)
   - Status: in_progress
   - Related to user management system
```

### When to Use
- **Research existing implementations** - Find related code across project
- **Understand design decisions** - Search decisions and code together
- **Explore feature relationships** - See how components connect
- **Find examples** - Locate similar implementations

### Caching
- **Cached**: No (search results need real-time accuracy)

---

## 3. analyze_git_activity

### Purpose
Analyzes git activity, uncommitted changes, and branch status to provide insights into recent development work.

### Internal Components
- **Primary**: Git command execution
- **Analysis**: Commit parsing, file change tracking
- **Branch Status**: Current branch and divergence info

### Parameters
```json
{
  "project_id": "string (optional)",
  "include_branches": "boolean (default: true)",
  "include_uncommitted": "boolean (default: true)"
}
```

### Usage Examples

#### Full Git Analysis
```json
{
  "tool": "analyze_git_activity",
  "arguments": {
    "project_id": "myproject_123",
    "include_branches": true,
    "include_uncommitted": true
  }
}
```

### Response Format
```markdown
# Git Activity Analysis

## Current Branch: feature/user-auth
- 3 commits ahead of main
- 0 commits behind main

## Recent Commits (Last 7 days)
1. **Add JWT token validation** (2 hours ago)
   - Files: auth/jwt_manager.py
   - +45 lines, -12 lines

2. **Create user model** (1 day ago)
   - Files: models/user.py, models/__init__.py
   - +120 lines, -0 lines

## Uncommitted Changes
### Modified Files (2)
- auth/jwt_manager.py (+5, -2)
- tests/test_auth.py (+30, -0)

### Untracked Files (1)
- docs/auth-design.md

## Branch Status
- **main**: stable, last updated 3 days ago
- **feature/user-auth**: active development
- **hotfix/login-bug**: merged yesterday
```

### When to Use
- **Development status checks** - See what's been worked on
- **Pre-commit reviews** - Check uncommitted changes
- **Branch management** - Understand branch relationships
- **Team coordination** - Track who's working on what

### Caching
- **Cached**: Yes (5 minutes)

---

## 4. check_development_drift

### Purpose
Analyzes recent development activity against project objectives to detect alignment or drift from planned goals.

### Internal Components
- **Primary**: Drift detection algorithm
- **Objectives**: Compare against active objectives
- **Recommendations**: AI-generated suggestions

### Parameters
```json
{
  "project_id": "string (optional)",
  "hours": "number (default: 24)",
  "include_recommendations": "boolean (default: true)"
}
```

### Usage Examples

#### Daily Drift Check
```json
{
  "tool": "check_development_drift",
  "arguments": {
    "project_id": "myproject_123",
    "hours": 24,
    "include_recommendations": true
  }
}
```

### Response Format
```markdown
# Development Drift Analysis

## Alignment Status: ✅ ALIGNED
## Alignment Score: 88%

## Analysis Period: Last 24 hours

### Active Objectives vs Recent Work
1. **Implement user management** ✅
   - Recent commits directly related
   - Progress: JWT auth implementation

2. **Add testing coverage** ⚠️
   - Limited test commits detected
   - Only 1 test file modified

## Recommendations
1. **Increase test coverage** for authentication module
   - Current coverage appears low
   - Consider TDD for remaining features

2. **Document authentication design**
   - Noticed uncommitted design doc
   - Consider committing to share with team

3. **Continue current approach**
   - JWT implementation aligns with objectives
   - Good progress on user management
```

### Status Levels
- **✅ aligned** (80-100%): Good alignment with objectives
- **⚠️ minor_drift** (60-79%): Some deviation from plans
- **🔶 moderate_drift** (40-59%): Significant deviation
- **🚨 major_drift** (0-39%): Completely off track

### When to Use
- **Daily standups** - Report on alignment
- **Sprint planning** - Assess current trajectory
- **Course correction** - Identify when to refocus

### Caching
- **Cached**: Yes (5 minutes)

---

## 5. manage_objectives

### Purpose
Add, update, complete, or list project objectives to maintain clear development goals and track progress.

### Internal Components
- **Primary**: Objectives management system
- **Storage**: Project configuration files
- **Actions**: add, complete, update, list

### Parameters
```json
{
  "action": "add|complete|update|list",
  "project_id": "string (optional)",
  "title": "string (for add/update)",
  "description": "string (for add/update)",
  "objective_id": "string (for complete/update)",
  "priority": "low|medium|high (default: medium)"
}
```

### Usage Examples

#### Add New Objective
```json
{
  "tool": "manage_objectives",
  "arguments": {
    "action": "add",
    "title": "Implement user authentication",
    "description": "Add JWT-based authentication system with role support",
    "priority": "high",
    "project_id": "myproject_123"
  }
}
```

#### Complete Objective
```json
{
  "tool": "manage_objectives",
  "arguments": {
    "action": "complete",
    "objective_id": "obj_auth_123",
    "project_id": "myproject_123"
  }
}
```

#### List All Objectives
```json
{
  "tool": "manage_objectives",
  "arguments": {
    "action": "list",
    "project_id": "myproject_123"
  }
}
```

### Response Format

#### Add Response
```markdown
# Objective Added Successfully

**ID**: obj_auth_456
**Title**: Implement user authentication
**Priority**: high
**Status**: pending
**Created**: 2025-07-29 10:30:00
```

#### List Response
```markdown
# Project Objectives

## High Priority (2)
1. **Implement user authentication** (obj_auth_123)
   - Status: in_progress
   - Created: 3 days ago
   - Description: JWT-based auth with roles

2. **Add API rate limiting** (obj_rate_124)
   - Status: pending
   - Created: 1 day ago

## Medium Priority (1)
1. **Improve test coverage** (obj_test_125)
   - Status: pending
   - Created: 5 days ago

## Completed (3)
- ✅ Set up project structure
- ✅ Configure development environment
- ✅ Create database schema
```

### When to Use
- **Sprint planning** - Define clear objectives
- **Progress tracking** - Mark objectives complete
- **Priority management** - Update objective priorities
- **Status reporting** - List all objectives

### Caching
- **Cached**: No (write operation)

---

## 6. track_decision

### Purpose
Record architectural or implementation decisions with context to maintain a clear decision log for the project.

### Internal Components
- **Primary**: Decision tracking system
- **Storage**: Decision logs in project configuration
- **Context**: Reasoning and alternatives

### Parameters
```json
{
  "decision": "string (required)",
  "reasoning": "string (required)",
  "alternatives_considered": "array of strings (optional)",
  "project_id": "string (optional)",
  "tags": "array of strings (optional)"
}
```

### Usage Examples

#### Track Architecture Decision
```json
{
  "tool": "track_decision",
  "arguments": {
    "decision": "Use PostgreSQL for main database",
    "reasoning": "Need ACID compliance, complex queries, and proven reliability for financial data",
    "alternatives_considered": [
      "MongoDB - rejected due to eventual consistency",
      "MySQL - less feature-rich than PostgreSQL"
    ],
    "tags": ["architecture", "database"],
    "project_id": "myproject_123"
  }
}
```

### Response Format
```markdown
# Decision Recorded

**ID**: dec_db_789
**Decision**: Use PostgreSQL for main database
**Date**: 2025-07-29
**Tags**: architecture, database

## Reasoning
Need ACID compliance, complex queries, and proven reliability for financial data

## Alternatives Considered
1. MongoDB - rejected due to eventual consistency
2. MySQL - less feature-rich than PostgreSQL

Decision has been logged and will be included in future context retrievals.
```

### When to Use
- **Architecture decisions** - Document technology choices
- **Design patterns** - Record pattern selections
- **Trade-off decisions** - Capture reasoning for compromises
- **Team alignment** - Share decision rationale

### Caching
- **Cached**: No (write operation)

---

## 7. suggest_next_action

### Purpose
Get AI-powered suggestions for what to work on next based on objectives, current state, and development patterns.

### Internal Components
- **Primary**: AI suggestion engine
- **Analysis**: Current state, objectives, blockers
- **Prioritization**: Importance and dependency ordering

### Parameters
```json
{
  "project_id": "string (optional)",
  "consider_blockers": "boolean (default: true)"
}
```

### Usage Examples

#### Get Next Action Suggestions
```json
{
  "tool": "suggest_next_action",
  "arguments": {
    "project_id": "myproject_123",
    "consider_blockers": true
  }
}
```

### Response Format
```markdown
# Suggested Next Actions

Based on your current objectives and recent activity, here are prioritized suggestions:

## 1. 🔴 Complete JWT Token Refresh Logic (High Priority)
**Why**: You've implemented token generation but not refresh
**Objective**: Implement user authentication
**Estimated Time**: 2-3 hours
**Files to modify**: auth/jwt_manager.py, middleware/auth_middleware.py

## 2. 🟡 Write Tests for Authentication (Medium Priority)
**Why**: No tests for recently added auth code
**Objective**: Improve test coverage
**Blocker**: Need to set up test database first
**Estimated Time**: 3-4 hours

## 3. 🟢 Document Authentication Flow (Low Priority)
**Why**: Uncommitted design doc detected
**Benefit**: Team alignment and onboarding
**Estimated Time**: 1 hour

## Potential Blockers Detected
- Test database not configured (blocking auth tests)
- Missing environment variables for JWT secret

## Quick Wins Available
- Commit the auth design doc (5 minutes)
- Add .env.example file (10 minutes)
```

### When to Use
- **Daily planning** - Decide what to work on
- **When stuck** - Get unstuck with suggestions
- **Priority decisions** - Understand most important tasks
- **Blocker identification** - Find what's preventing progress

### Caching
- **Cached**: No (needs current state)

---

## 8. get_code_context

### Purpose
Get relevant code examples and patterns for implementing a specific feature based on existing codebase.

### Internal Components
- **Primary**: Code analysis and pattern matching
- **Search**: Find similar implementations
- **Context**: Related files and patterns

### Parameters
```json
{
  "feature_description": "string (required)",
  "project_id": "string (optional)",
  "include_similar": "boolean (default: true)"
}
```

### Usage Examples

#### Get Implementation Guidance
```json
{
  "tool": "get_code_context",
  "arguments": {
    "feature_description": "Add password reset functionality",
    "include_similar": true,
    "project_id": "myproject_123"
  }
}
```

### Response Format
```markdown
# Code Context for: Add password reset functionality

## Relevant Existing Patterns

### Authentication Flow (auth/jwt_manager.py)
```python
def generate_token(user_id, expires_in=3600):
    """Current token generation pattern you can adapt"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(seconds=expires_in)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')
```

### Email Service Pattern (services/email_service.py)
```python
def send_email(to_email, subject, body):
    """Existing email service to use for reset emails"""
    # Implementation here
```

## Suggested Implementation Approach

1. **Create Password Reset Token Model**
   - Store token, user_id, expiry
   - Similar to how JWT tokens are handled

2. **Add Reset Endpoints**
   ```python
   @app.route('/auth/forgot-password', methods=['POST'])
   @app.route('/auth/reset-password', methods=['POST'])
   ```

3. **Reuse Existing Patterns**
   - Token generation from jwt_manager.py
   - Email sending from email_service.py
   - User lookup from models/user.py

## Files to Create/Modify
- `auth/password_reset.py` (new)
- `models/password_reset_token.py` (new)
- `auth/routes.py` (modify)
- `templates/reset_email.html` (new)
```

### When to Use
- **Feature implementation** - Get relevant patterns
- **Code reuse** - Find existing similar code
- **Architecture guidance** - Understand conventions
- **Learning codebase** - See how things are done

### Caching
- **Cached**: No (needs current code state)

---

## 9. daily_briefing

### Purpose
Get a comprehensive daily briefing with all projects, objectives, recent activity, and recommendations.

### Internal Components
- **Primary**: Aggregates multiple tool outputs
- **Components**: Context, objectives, git activity, suggestions
- **Format**: Comprehensive daily overview

### Parameters
```json
{
  "include_all_projects": "boolean (default: false)"
}
```

### Usage Examples

#### Get Daily Briefing
```json
{
  "tool": "daily_briefing",
  "arguments": {
    "include_all_projects": false
  }
}
```

### Response Format
```markdown
# Daily Development Briefing
**Date**: 2025-07-29
**Time**: 09:30 AM

## 📊 Active Projects (1)

### MyProject (Active)
**Path**: /Users/username/myproject
**Last Activity**: 2 hours ago

#### 🎯 Current Objectives (3 active)
1. **Implement user authentication** (high) - 60% complete
2. **Add API rate limiting** (high) - not started
3. **Improve test coverage** (medium) - 25% complete

#### 💡 Recent Decisions
- Use PostgreSQL for main database (yesterday)
- JWT for authentication (3 days ago)

#### 🔄 Git Activity (Last 24h)
- 5 commits on feature/user-auth
- 2 files modified, 1 untracked
- Ready to merge: No (tests needed)

#### 📈 Development Alignment
**Status**: ✅ ALIGNED (88%)
- Good progress on authentication
- Consider adding tests soon

#### 🚀 Suggested Next Actions
1. Complete JWT refresh logic (2-3 hours)
2. Write authentication tests (3-4 hours)
3. Document auth flow (1 hour)

## 📝 Summary
You're making good progress on user authentication. Focus on completing the JWT refresh mechanism and adding tests before moving to the next objective. Consider committing the design doc you've started.

**Have a productive day! 🎯**
```

### When to Use
- **Morning routine** - Start day with full context
- **Project switching** - Get oriented quickly
- **Team standups** - Share comprehensive status
- **Weekly planning** - Review overall progress

### Caching
- **Cached**: Yes (5 minutes)

---

## 🔗 Tool Interactions and Workflows

### Morning Development Flow
```javascript
// 1. Get daily briefing
const briefing = await daily_briefing();

// 2. Check specific project context if needed
const context = await get_development_context({ 
  hours: 48 
});

// 3. Get suggestions for the day
const suggestions = await suggest_next_action();
```

### Feature Implementation Flow
```javascript
// 1. Search for similar code
const search = await intelligent_search({
  query: "user permissions implementation"
});

// 2. Get code context
const patterns = await get_code_context({
  feature_description: "role-based permissions"
});

// 3. Track decision
await track_decision({
  decision: "Use decorator pattern for permissions",
  reasoning: "Clean, reusable, follows existing patterns"
});
```

### Progress Tracking Flow
```javascript
// 1. Check alignment
const drift = await check_development_drift();

// 2. Update objectives based on progress
await manage_objectives({
  action: "complete",
  objective_id: "obj_auth_123"
});

// 3. Add new objective
await manage_objectives({
  action: "add",
  title: "Add permission system",
  priority: "high"
});
```

---

## 🚀 Best Practices

### 1. Start Sessions with Context
Always begin with `daily_briefing` or `get_development_context` to understand current state.

### 2. Track Decisions Immediately
Use `track_decision` as soon as you make architectural choices.

### 3. Regular Alignment Checks
Run `check_development_drift` daily to ensure you're on track.

### 4. Leverage Code Context
Use `get_code_context` before implementing new features to maintain consistency.

### 5. Manage Objectives Actively
Keep objectives updated with `manage_objectives` to maintain accurate project state.

---

## 🔧 Troubleshooting

### Connection Issues
If tools fail to connect:
1. Ensure RAG agent is running on port 5556
2. Check environment variables in MCP config
3. Verify project is properly initialized

### Empty Results
If searches return no results:
1. Ensure project has been ingested
2. Check if project_id is correct
3. Verify search terms are relevant

### Cache Issues
If getting stale data:
1. Cache duration is 5 minutes for most tools
2. Wait for cache to expire or restart MCP server
3. Non-cached tools always return fresh data

---

## 📊 Performance Expectations

- **Context tools**: 1-2 seconds (cached: <200ms)
- **Search tools**: 2-3 seconds
- **Management tools**: <1 second
- **Analysis tools**: 2-4 seconds
- **Daily briefing**: 3-5 seconds (aggregates multiple tools)

---

This documentation reflects the actual implementation of the enhanced_mcp_server.js with all 9 tools properly documented and ready for use with Claude Code and other AI assistants.