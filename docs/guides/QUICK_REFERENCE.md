# RAG Agent Quick Reference

## 🚀 Getting Started

1. **First Time Setup**:
   ```bash
   cd contextkeeper
   ./setup.sh
   ```

2. **Edit Configuration**:
   - Edit `.env` with your Google Cloud credentials
   - Update `rag_agent.py` CONFIG section with your project paths

3. **Start the Agent**:
   ```bash
   python rag_agent.py start
   ```

## 📝 Common Commands

### Project Management (Essential Workflow)
```bash
# List all projects
./scripts/rag_cli_v2.sh projects list

# Create a new project with path
./scripts/rag_cli_v2.sh projects create <project_name> <project_path>
# Example: ./scripts/rag_cli_v2.sh projects create veo3app /path/to/projects/veo3-video-application

# Focus on a project (makes it active)
./scripts/rag_cli_v2.sh projects focus <project_id>

# Index project files (after creating/focusing)
python rag_agent.py ingest --path <project_path>
# Example: python rag_agent.py ingest --path /path/to/projects/veo3-video-application

# Pause/resume project tracking
./scripts/rag_cli_v2.sh projects pause <project_id>
./scripts/rag_cli_v2.sh projects resume <project_id>

# Archive completed project
./scripts/rag_cli_v2.sh projects archive <project_id>
```

### Knowledge Base Queries
```bash
# Query knowledge base (v2 CLI)
./scripts/rag_cli_v2.sh ask "What payment system are we using?"

# Query with specific project context
curl -X POST http://localhost:5556/query_llm \
  -H "Content-Type: application/json" \
  -d '{"question": "Your question here", "k": 5, "project_id": "<project_id>"}'

# Add a decision
./scripts/rag_cli_v2.sh decisions add "Using Stripe for payments" "Better API support"

# Morning briefing
./scripts/rag_cli_v2.sh briefing

# Check agent status
./scripts/rag_cli_v2.sh status

# View logs
./scripts/rag_cli_v2.sh logs
```

## 🎯 Sacred Layer Commands (v3.0)

```bash
# Create sacred plan
./scripts/rag_cli.sh sacred create <project_id> "Plan Title" plan.md

# Approve sacred plan (requires 2-layer verification)
./scripts/rag_cli.sh sacred approve <plan_id>

# Check drift from sacred plans
./scripts/rag_cli.sh sacred drift <project_id>

# Query sacred plans
./scripts/rag_cli.sh sacred query <project_id> "search query"
```

## 🔧 API Access

```bash
# Query via API
curl -X POST http://localhost:5556/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Show Gemini integration code"}'

# Add decision via API
curl -X POST http://localhost:5556/decision \
  -H "Content-Type: application/json" \
  -d '{"decision": "Using Gemini 2.5", "context": "Better multimodal support"}'
```

## 🐛 Troubleshooting

### Common Issues & Solutions

1. **Agent not starting**: 
   - Check `.env` file and Google Cloud credentials
   - Ensure virtual environment is activated: `source venv/bin/activate`
   - Verify port 5556 is not in use: `lsof -i :5556`

2. **"No project context specified" error**:
   - Create a project first: `./scripts/rag_cli_v2.sh projects create <name> <path>`
   - Focus on the project: `./scripts/rag_cli_v2.sh projects focus <project_id>`
   - Index the files: `python rag_agent.py ingest --path <project_path>`

3. **No results from queries**:
   - Ensure files are indexed after project creation
   - Check if project is focused/active
   - Verify project path exists and contains files

4. **Permission errors**: 
   - Run `chmod +x scripts/*.sh`
   - Check file permissions in project directory

5. **Import errors**: 
   - Activate virtual environment: `source venv/bin/activate`
   - Run `pip install -r requirements.txt`

6. **Indexing timeout**:
   - Normal for large projects (can take 2-3 minutes)
   - Check logs for progress: `tail -f rag_agent.log`

## 💡 Tips

1. The agent watches your files automatically - just save and it updates
2. All API keys and passwords are automatically redacted
3. Use the morning briefing to quickly get context when starting work
4. Add decisions as you make them - they'll help Claude stay consistent

## 📚 Files in this directory

- `rag_agent.py` - Main agent code
- `rag_cli.sh` - Command line wrapper
- `sacred_layer_implementation.py` - Sacred Layer core functionality
- `git_activity_tracker.py` - Git integration for activity tracking
- `enhanced_drift_sacred.py` - Drift detection system
- `requirements.txt` - Python dependencies
- `setup.sh` - Quick setup script
- `.env.template` - Environment variable template
- `README.md` - Detailed documentation

Happy coding! 🚀
