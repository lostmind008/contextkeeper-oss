# ContextKeeper v3.0: System Architecture

This document provides a technical overview of the ContextKeeper v3.0 system architecture, reflecting its state as of August 2025.

## 1. Core Philosophy

The architecture is designed around a central, stateful **RAG (Retrieval-Augmented Generation) Agent** that serves as the single source of truth for all development context. All interactions, whether from the CLI, the dashboard, or other AI tools, are mediated through this agent. This ensures consistency and prevents state fragmentation.

## 2. High-Level Diagram

```
                               +-------------------------+
                               |   End Users & Tools     |
                               +-----------+-------------+
                                           |
                  +------------------------+------------------------+
                  |                        |                        |
         +--------v--------+      +--------v--------+      +--------v--------+
         |   Interactive   |      |  CLI Scripts    |      |  External AI    |
         |    Dashboard    |      | (contextkeeper) |      |   (Claude)      |
         +--------+--------+      +--------+--------+      +--------+--------+
                  |                        |                        |
+-----------------|------------------------+------------------------|-----------------+
| Real-Time Layer |                        |                        |                 |
| (WebSockets)    |                        |                        |                 |
+-----------------|------------------------+------------------------|-----------------+
                  |                        |                        |
                  |       +----------------+----------------+       |
                  |       |      HTTP RESTful API           |       |
                  |       +----------------+----------------+       |
                  |                        |                        |
         +--------v--------+      +--------v--------+      +--------v--------+
         | Real-Time Comms |      | RAG Agent (Flask)       |      | MCP Server      |
         |  (Socket.IO)    |      | (rag_agent.py)          |      | (Node.js)       |
         +-----------------+      +--------+--------+      +-----------------+
                                           |
                 +-------------------------+-------------------------+
                 |                         |                         |
        +--------v--------+       +--------v--------+       +--------v--------+
        |  `src/core`     |       |  `src/sacred`   |       |  `src/ck_analytics`|
        | Project Mgmt    |       | Governance      |       | Metrics Service |
        +--------+--------+       +--------+--------+       +--------+--------+
                 |                         |                         |
                 |                         |                         |
                 +-------------------------+-------------------------+
                                           |
                                  +--------v--------+
                                  |  ChromaDB       |
                                  |  Vector Store   |
                                  +-----------------+

```

## 3. Key Components

### Frontend / User-Facing
*   **Interactive Dashboard (`analytics_dashboard_live.html`)**: A single-page application providing a real-time, interactive view of the system. It communicates with the backend primarily via WebSockets for live updates and uses the REST API for initial data loading and actions.
*   **CLI (`scripts/contextkeeper.sh`)**: A powerful bash script for terminal-based interaction. It communicates directly with the RAG Agent's REST API.

### Backend / Service Layer
*   **RAG Agent (`rag_agent.py`)**: The core of the system. This is a Flask application that serves both a REST API and a WebSocket server. It orchestrates all business logic, from project management to RAG queries.
*   **Real-Time Layer (`Flask-SocketIO`)**: Integrated into the RAG Agent, this layer pushes real-time updates to connected clients (like the dashboard) for events such as indexing progress or focus changes.
*   **MCP Server (`mcp-server/enhanced_mcp_server.js`)**: A Node.js server that acts as a bridge for external AI tools like Claude, exposing ContextKeeper's functionality via the Model-Context-Protocol (MCP).

### Core Logic (`src/` directory)
The Python codebase is organized into a modular `src/` directory:
*   **`src/core`**: Manages fundamental entities like projects and decisions.
*   **`src/sacred`**: Implements the architectural governance features (Sacred Plans, drift detection).
*   **`src/ck_analytics`**: Contains the new analytics service for calculating governance and project metrics.
*   **`src/tracking`**: Handles Git activity tracking and other event monitoring.

### Data Storage
*   **ChromaDB**: The vector database used for all semantic search capabilities. Each project has its own isolated collection to prevent data leakage.
*   **File System**: Project configurations and Sacred Plans are stored as JSON and Markdown files on the local file system, making them version-controllable.

## 4. Data Flows

### Project Onboarding (Async Task System)
1.  **Initiation**: A user runs `./scripts/contextkeeper.sh project add ...` or uses the dashboard modal.
2.  **Immediate Response**: A `POST` request is sent to the `/projects/create-and-index` endpoint on the RAG Agent.
3.  **Task Creation**: The agent immediately creates the project configuration and returns a `202 Accepted` response with:
    - `task_id`: Unique identifier for tracking async operation
    - `project_id`: Unique project identifier (e.g., `proj_abc123`)
4.  **Project Metadata**: The project JSON file is created in the `projects/` directory with initial state.
5.  **Background Processing**: A background task is spawned using Python threading to handle indexing asynchronously.
6.  **Indexing Pipeline**:
    - **Security Filtering**: Files are scanned with PathFilter to exclude sensitive directories (.git, node_modules)
    - **Content Processing**: SecurityFilter redacts API keys and sensitive patterns
    - **Chunking**: Content is split into semantic chunks for embedding
    - **Embedding Generation**: Chunks are embedded using the Gemini API
    - **Storage**: A new ChromaDB collection is created specifically for this project (e.g., `proj_abc123`)
    - **Isolation**: Embeddings are stored in the isolated collection to prevent cross-contamination
7.  **Real-Time Progress**: Throughout the process, `indexing_progress` events are emitted via WebSocket with:
    - `project_id`: The project being indexed
    - `progress`: Percentage completion (0-100)
    - `current_file`: Currently processing file (optional)
8.  **Client Handling**:
    - **Dashboard**: Listens for WebSocket events and updates UI in real-time with progress bars
    - **CLI**: Polls the `/tasks/{task_id}` endpoint to display progress bar in terminal
9.  **Completion**: Upon successful indexing, an `indexing_complete` event is emitted with the final project state.
10. **Error Handling**: If indexing fails, an `indexing_error` event is emitted with error details.

### Real-Time Dashboard Updates
1.  The dashboard opens a persistent WebSocket connection to the RAG Agent.
2.  When an action occurs (e.g., a project is focused via the CLI), the corresponding API endpoint (`/projects/{id}/focus`) emits a `focus_changed` event.
3.  All connected dashboard clients receive this event and update their UI accordingly (e.g., by highlighting the focused project card).

### Analytics Calculation
1.  A request is made to the `GET /analytics/sacred` endpoint.
2.  The RAG Agent routes this to the `AnalyticsService` in `src/ck_analytics/analytics_service.py`.
3.  The `AnalyticsService` uses the `SacredMetricsCalculator` to gather data from the `SacredLayerManager` and `ProjectManager`.
4.  It calculates metrics like plan counts, approval rates, and adherence scores.
5.  The results are cached for 5 minutes to ensure subsequent requests are fast.
6.  The calculated metrics are returned as a JSON response.

### Query Processing (RAG Workflow)
1.  User submits a query through CLI (`./scripts/contextkeeper.sh query`) or dashboard.
2.  The query is sent to `/projects/{id}/query` endpoint.
3.  The system verifies a project is focused, otherwise returns an error.
4.  The query is embedded using the Gemini API.
5.  ChromaDB performs semantic search in the project's isolated collection.
6.  Top-k relevant code chunks are retrieved based on cosine similarity.
7.  Retrieved context is combined with the query and sent to Gemini LLM.
8.  The LLM generates a response grounded in the codebase context.
9.  The response is returned to the user and logged as an event.

### Sacred Layer Governance
1.  A Sacred Plan is proposed through the dashboard or API.
2.  The plan requires approval with the `SACRED_APPROVAL_KEY` environment variable.
3.  Once approved, the plan becomes immutable and stored in the project's sacred directory.
4.  The drift detection engine (`enhanced_drift_sacred.py`) monitors development activity.
5.  If code changes deviate from approved architectural patterns, drift alerts are generated.
6.  Drift metrics are calculated and exposed through the analytics endpoint.

## 5. WebSocket Events

The system emits comprehensive real-time events via Socket.IO to keep all clients synchronised:

### Project Management Events
- **`indexing_progress`**: 
  - **Payload**: `{ "project_id": string, "progress": int, "current_file": string? }`
  - **Purpose**: Real-time progress updates during async project indexing
  - **Frequency**: Emitted periodically during file processing

- **`indexing_complete`**: 
  - **Payload**: `{ "project_id": string, "total_files": int, "total_chunks": int }`
  - **Purpose**: Notification when project indexing finishes successfully
  - **Trigger**: After all files are processed and embeddings stored

- **`indexing_error`**: 
  - **Payload**: `{ "project_id": string, "error": string, "failed_file": string? }`
  - **Purpose**: Error notification during indexing process
  - **Trigger**: When file processing or embedding generation fails

- **`focus_changed`**: 
  - **Payload**: `{ "project_id": string, "project_name": string }`
  - **Purpose**: Notification when active project changes
  - **Trigger**: CLI focus command or dashboard project selection

- **`project_updated`**: 
  - **Payload**: `{ "project_id": string, "changes": object }`
  - **Purpose**: Notification when project metadata changes
  - **Trigger**: Project configuration updates

### Governance Events
- **`decision_added`**: 
  - **Payload**: `{ "project_id": string, "decision": object, "timestamp": string }`
  - **Purpose**: Notification when architectural decisions are tracked
  - **Trigger**: New decision added via API or dashboard

- **`objective_updated`**: 
  - **Payload**: `{ "project_id": string, "objective": object, "action": string }`
  - **Purpose**: Notification when project objectives change
  - **Trigger**: Objective creation, completion, or modification

- **`sacred_plan_created`**: 
  - **Payload**: `{ "project_id": string, "plan_id": string, "title": string }`
  - **Purpose**: Notification when new Sacred Plans are proposed
  - **Trigger**: Sacred plan creation via CLI or dashboard

- **`sacred_plan_approved`**: 
  - **Payload**: `{ "project_id": string, "plan_id": string, "approver": string, "timestamp": string }`
  - **Purpose**: Notification when plans receive governance approval
  - **Trigger**: Successful 2-layer plan approval process

## 6. Security Considerations
*   **Authentication & Authorization**: Currently, the system relies on the security of the local machine it runs on. There is no user-based authentication layer.
*   **Secret Management**: API keys and the `SACRED_APPROVAL_KEY` are managed via an `.env` file. The SACRED_APPROVAL_KEY has no default and must be explicitly set.
*   **Data Redaction**: The `SecurityFilter` class automatically redacts sensitive patterns (like API keys) from file content before it is indexed.
*   **Path Filtering**: A robust `PathFilter` prevents the ingestion of sensitive directories (`.git`, `node_modules`) and files.
*   **Project Isolation**: Each project has its own ChromaDB collection, preventing cross-contamination of embeddings.
