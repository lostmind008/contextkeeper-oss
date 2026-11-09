# API Reference

**Base URL**: `http://localhost:5556`  
**Status**: ✅ All endpoints operational (August 2025)
**Version**: 3.0.0

## 1. Core Endpoints

### Project Management
```http
# Unified project creation and indexing (asynchronous)
POST   /projects/create-and-index
# Body: { "name": "...", "root_path": "..." }
# Returns 202 Accepted: { "task_id": "task_abc123", "project_id": "proj_xyz789" }
# Note: Indexing runs in background, use task_id to track progress

# Check status of a background task (like indexing)
GET    /tasks/<task_id>
# Returns: 
#   In Progress: { "status": "indexing", "progress": 45 }
#   Completed: { "status": "completed", "result": {...} }
#   Failed: { "status": "failed", "error": "..." }

# List all projects with status
GET    /projects
# Returns: [{ "id": "proj_123", "name": "...", "status": "active", "indexed": true }]

# Set active project (emits 'focus_changed' WebSocket event)
POST   /projects/<project_id>/focus
# Body: {} (empty)
# Returns: { "focused_project": { "id": "...", "name": "..." } }

# Get project details
GET    /projects/<project_id>
# Returns: { "id": "...", "name": "...", "root_path": "...", "indexed": true }
```

### Knowledge & Context
```http
# Global search across projects, plans, and decisions
GET    /search?q=<query>

# Query knowledge base with LLM enhancement
POST   /query_llm
# Body: { "question": "...", "project_id": "..." }

# Add an architectural decision
POST   /decision
# Body: { "decision": "...", "reasoning": "...", "project_id": "..." }
```

## 2. Sacred Layer & Governance

### Sacred Plan Management
```http
# Create a new sacred plan
POST   /sacred/plans
# Body: { "project_id": "...", "title": "...", "file_path": "..." }

# Approve a sacred plan (2-layer verification)
POST   /sacred/plans/<plan_id>/approve
# Body: { "approver": "...", "verification_code": "...", "secondary_verification": "..." }

# List sacred plans for a project
GET    /sacred/plans?project_id=<project_id>

# Query sacred plans
POST   /sacred/query
# Body: { "query": "...", "project_id": "..." }

# Check for architectural drift
GET    /sacred/drift/<project_id>
```

### Analytics
```http
# Get detailed governance and sacred metrics
GET    /analytics/sacred
```

## 3. Real-Time Events (WebSockets)

Connect to the Socket.IO server at the base URL (`http://localhost:5556`). The server emits comprehensive real-time events:

### Project Management Events

#### `indexing_progress`
Fired periodically during project indexing to show real-time progress.
- **Payload**: `{ "project_id": string, "progress": int, "current_file": string? }`
- **Example**: `{ "project_id": "proj_123", "progress": 45, "current_file": "src/main.py" }`
- **Usage**: Update progress bars in UI

#### `indexing_complete`
Fired when a project has been successfully indexed and is ready for queries.
- **Payload**: `{ "project_id": string, "total_files": int, "total_chunks": int }`
- **Example**: `{ "project_id": "proj_123", "total_files": 247, "total_chunks": 1583 }`
- **Usage**: Enable project interaction, update status to "Active"

#### `indexing_error`
Fired if an error occurs during the indexing process.
- **Payload**: `{ "project_id": string, "error": string, "failed_file": string? }`
- **Example**: `{ "project_id": "proj_123", "error": "Permission denied", "failed_file": "/restricted/file.py" }`
- **Usage**: Show error messages, allow retry

#### `focus_changed`
Fired when a project's focus is changed via CLI or dashboard.
- **Payload**: `{ "project_id": string, "project_name": string }`
- **Example**: `{ "project_id": "proj_456", "project_name": "WebApp Backend" }`
- **Usage**: Update UI to highlight focused project

#### `project_updated`
Fired when project metadata or configuration changes.
- **Payload**: `{ "project_id": string, "changes": object }`
- **Example**: `{ "project_id": "proj_123", "changes": { "name": "Updated Name" } }`
- **Usage**: Refresh project display information

### Governance Events

#### `decision_added`
Fired when architectural decisions are tracked for a project.
- **Payload**: `{ "project_id": string, "decision": object, "timestamp": string }`
- **Example**: `{ "project_id": "proj_123", "decision": { "title": "Use GraphQL", "reasoning": "..." }, "timestamp": "2025-08-08T12:00:00Z" }`
- **Usage**: Update decision logs in dashboard

#### `objective_updated`
Fired when project objectives are created, completed, or modified.
- **Payload**: `{ "project_id": string, "objective": object, "action": string }`
- **Example**: `{ "project_id": "proj_123", "objective": { "title": "Implement Auth" }, "action": "completed" }`
- **Usage**: Update objective lists and progress tracking

#### `sacred_plan_created`
Fired when new Sacred Plans are proposed for architectural governance.
- **Payload**: `{ "project_id": string, "plan_id": string, "title": string }`
- **Example**: `{ "project_id": "proj_123", "plan_id": "plan_456", "title": "API Design Guidelines" }`
- **Usage**: Show new plans requiring approval

#### `sacred_plan_approved`
Fired when plans receive governance approval through the 2-layer system.
- **Payload**: `{ "project_id": string, "plan_id": string, "approver": string, "timestamp": string }`
- **Example**: `{ "project_id": "proj_123", "plan_id": "plan_456", "approver": "John Doe", "timestamp": "2025-08-08T12:00:00Z" }`
- **Usage**: Update plan status to "Approved", enable enforcement


## 4. Health & Status
```http
# System health check
GET    /health
```

## 5. Request/Response Examples

### Create & Index a Project
```bash
curl -X POST http://localhost:5556/projects/create-and-index \
  -H "Content-Type: application/json" \
  -d '{"name": "WebApp", "root_path": "/path/to/webapp"}'
```
**Response (202 Accepted)**:
```json
{
  "task_id": "task_abc123",
  "project_id": "proj_xyz789"
}
```

### Check Task Status
```bash
curl http://localhost:5556/tasks/task_abc123
```
**Response**:
```json
{
  "status": "indexing",
  "progress": 75
}
```

### Global Search
```bash
curl "http://localhost:5556/search?q=auth"
```
**Response**:
```json
{
  "projects": [{ "id": "proj_1", "name": "Authentication Service" }],
  "plans": [{ "plan_id": "plan_2", "title": "OAuth2 Authentication Plan" }],
  "decisions": []
}
```

### Get Sacred Analytics
```bash
curl http://localhost:5556/analytics/sacred
```
**Response**:
```json
{
  "overall_metrics": {
    "total_plans": 10,
    "compliance_rate": 80.0
  },
  "project_metrics": [
    {
      "project_name": "WebApp",
      "adherence_score": 95.5
    }
  ]
}
```
