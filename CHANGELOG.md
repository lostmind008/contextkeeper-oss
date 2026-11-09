# Changelog

All notable changes to ContextKeeper will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] - 2025-08-01

### Added
- **Sacred Layer Implementation** - Revolutionary immutable architectural plan system with 2-layer verification
  - Create sacred plans that cannot be modified once approved
  - Hash-based verification codes + environment key protection
  - Automatic drift detection when development deviates from plans
  - Sacred plan supersession for controlled evolution
  - Lock functionality to prevent any modifications
- **Analytics Dashboard** - Professional real-time monitoring interface
  - Live metrics display with auto-refresh
  - Dark mode support with persistent preferences
  - Mobile-responsive design
  - Export functionality (PDF, PNG, JSON)
  - Interactive charts with drill-down capabilities
  - Search and filter functionality
  - Sacred plan timeline visualization
- **LLM-Enhanced Queries** - Natural language responses powered by Google Gemini
  - `/query_llm` endpoint for AI-powered answers
  - Context-aware responses based on project knowledge
  - Automatic summarization of search results
- **Sacred Metrics API** - Comprehensive analytics endpoints
  - `/analytics/sacred` for governance metrics
  - Project adherence scoring (0-100)
  - Drift analysis and compliance monitoring
  - Recent activity tracking
  - 5-minute intelligent caching
- **Git Integration** - Development activity tracking
  - Automatic commit tracking
  - Branch analysis
  - Uncommitted changes detection
  - Activity correlation with sacred plans
- **Enhanced MCP Tools** - 8 powerful tools for Claude Code
  - `get_development_context` - Comprehensive project state
  - `intelligent_search` - Semantic code search
  - `analyze_git_activity` - Git analysis
  - `check_development_drift` - Sacred plan alignment
  - `manage_objectives` - Objective tracking
  - `track_decision` - Decision recording
  - `suggest_next_action` - AI suggestions
  - `get_code_context` - Relevant examples

### Changed
- **Port Configuration** - Server now runs on port 5556 (was 5555)
- **API Updates** - Migrated to Google GenAI latest models
  - Embedding model: `gemini-embedding-001`
  - LLM model: `gemini-2.0-flash`
- **Flask Endpoints** - All endpoints now use async for better performance
- **ChromaDB Integration** - Enhanced with proper filter fallback strategies
- **CLI Scripts** - Updated to use clean integration without merge conflicts
- **Test Suite** - Sacred layer tests updated to match implementation

### Fixed
- **Sacred Query Endpoint** - Resolved 500 errors with proper error handling
- **CLI JSON Parsing** - Fixed merge conflicts in sacred CLI integration
- **LLM Integration** - Added missing client attribute to ProjectKnowledgeAgent
- **Project Isolation** - Verified complete isolation (false positive resolved)
- **Path Filtering** - Enhanced to prevent venv/node_modules pollution
- **Test Coverage** - All 14 failing sacred tests now passing

### Security
- **2-Layer Verification** - Sacred plans protected by dual verification
- **Project Isolation** - Zero cross-contamination between projects
- **API Key Redaction** - Automatic detection and removal of sensitive data
- **Path Security** - Smart filtering prevents access to system directories

### Performance
- **Async Endpoints** - All Flask routes now use async/await
- **Smart Caching** - 5-minute cache for analytics endpoints
- **Optimized Embeddings** - Better performance with new Google models
- **Error Recovery** - Exponential backoff and automatic retries

## [2.0.0] - 2025-07-15

### Added
- Multi-project management system
- Project-specific ChromaDB collections
- Enhanced path filtering
- Basic drift detection
- Decision tracking functionality

### Changed
- Migrated from single to multi-project architecture
- Updated ChromaDB to latest version
- Improved error handling throughout

### Fixed
- Memory leaks in long-running sessions
- File watcher performance issues
- Database corruption on improper shutdown

## [1.0.0] - 2025-06-01

### Added
- Initial RAG implementation
- Basic file ingestion
- ChromaDB vector storage
- Simple CLI interface
- Google GenAI embeddings

---

For upgrade instructions, see [MIGRATION_GUIDE.md](docs/guides/MIGRATION_GUIDE.md)