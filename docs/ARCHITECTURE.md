# ContextKeeper Architecture

## System Overview

ContextKeeper is a multi-project RAG system with sacred plan protection for AI collaboration.

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Git Activity   │  │  Multi-Project  │  │  Sacred Layer   │
│  Tracker        │  │  RAG Agent      │  │  Manager        │
│  (v3.0)         │  │  (v2.0+)        │  │  (v3.0)         │
└─────────┬───────┘  └─────────┬───────┘  └─────────┬───────┘
          │                    │                    │
          ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────┐
│               ChromaDB Vector Storage                   │
│  • Project Collections (isolated)                      │
│  • Sacred Collections (immutable)                      │
│  • Decision & Objective Tracking                       │
└─────────────────────────────────────────────────────────┘
```

## Core Components

### 1. ProjectKnowledgeAgent (`rag_agent.py`)
**Role**: Central orchestrator
- Manages multiple projects with isolated ChromaDB collections
- Coordinates file indexing, querying, and context export
- Integrates with Google GenAI for embeddings
- Provides Flask API for external access

### 2. ProjectManager (`project_manager.py`)
**Role**: Project lifecycle management
- Create, pause, resume, archive projects
- Track decisions and objectives per project
- Store configurations in `~/.rag_projects/`
- Maintain project focus and context switching

### 3. Sacred Layer (`sacred_layer_implementation.py`) - v3.0
**Role**: Immutable plan protection
- 2-layer verification for plan approval
- Isolated ChromaDB collections for sacred content
- Semantic chunking for large plan documents
- Drift detection against approved plans

### 4. Git Activity Tracker (`git_activity_tracker.py`) - v3.0
**Role**: Development activity tracking
- Monitor git commits and changes
- Correlate activity with projects
- Replace file-watching with reliable git-based tracking
- Feed activity data to drift detection

## Data Flow

### v2.0 Flow (Current)
```
Code Files → File Watcher → RAG Agent → ChromaDB Collections
                                ↓
User Queries → Vector Search → Contextual Responses
```

### v3.0 Flow (Target)
```
Git Commits → Activity Tracker → RAG Agent → Project Collections
                                      ↓
Sacred Plans → Sacred Layer → Sacred Collections (isolated)
                                      ↓
Development Activity + Sacred Plans → Drift Detection → Alerts
```

## Key Design Principles

### 1. Project Isolation
Each project maintains:
- Separate ChromaDB collection
- Independent configuration
- Isolated decision/objective tracking
- Individual sacred plan storage

### 2. Sacred Plan Security
- **Immutable Storage**: Once approved, plans cannot be modified
- **2-Layer Verification**: Code + environment key required
- **Isolation**: Sacred plans in separate ChromaDB collections
- **Audit Trail**: Full history of approvals and changes

### 3. Fail-Safe AI Collaboration
- Sacred plans act as guardrails for AI agents
- Real-time drift detection prevents derailment
- Context export includes sacred plan boundaries
- Violation alerts for plan deviations

## Database Schema

### ChromaDB Collections
- `project_<id>`: Main project knowledge
- `sacred_<id>`: Sacred plans for project
- Metadata includes type, project_id, timestamps

### File Storage
- `~/.rag_projects/`: Project configurations
- `rag_knowledge_db/`: ChromaDB persistence
- `rag_knowledge_db/sacred_plans/`: Plan files
- `rag_knowledge_db/sacred_chromadb/`: Sacred embeddings

## API Architecture

### v2.0 Endpoints
- Project CRUD operations
- Knowledge querying and context export
- Decision and objective tracking

### v3.0 Additions
- Sacred plan management
- 2-layer verification workflow
- Drift detection and alerts
- Git activity integration

## Security Model

### Authentication
- Google Cloud service account for AI APIs
- Environment variable for sacred approval key
- No external authentication (local tool)

### Data Protection
- Local-only storage (no cloud data)
- Immutable sacred plan storage
- Audit trail for all sacred operations
- Isolated collections prevent data mixing

## Performance Considerations

### Scalability
- Per-project ChromaDB collections scale independently
- Sacred collections optimised for verification queries
- Git activity processed incrementally
- Caching for frequent context exports

### Resource Management
- Memory-efficient vector operations
- Disk space monitoring for embeddings
- Background processes for continuous monitoring
- Graceful degradation when components unavailable