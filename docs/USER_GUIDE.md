# ContextKeeper v3.0: The Ultimate User Guide

Welcome to ContextKeeper! This guide provides everything you need to know to harness the full power of the system, from initial setup to advanced workflows.

**Last Updated**: August 8, 2025  
**System Status**: Production Ready with Real-Time Features

## 1. 🚀 Getting Started: Your First 5 Minutes

This section will get you up and running with a fully indexed project.

### Step 1: Installation
```bash
# 1. Clone the repository
git clone https://github.com/lostmind008/contextkeeper-oss.git
cd contextkeeper-oss

# 2. Set up Python environment
python3 -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.template .env
# Edit .env and add your keys:
# GEMINI_API_KEY=your-gemini-api-key
# SACRED_APPROVAL_KEY=a-long-secret-key-you-create
```

### Step 2: Start the ContextKeeper Service
```bash
# Start the main application (RAG Agent with WebSocket support)
python src/rag_agent.py server
```
This command starts the backend server on `http://localhost:5556`. Keep this terminal window running.

### Step 3: Create and Index Your First Project (Async Onboarding)
The streamlined workflow uses async processing with real-time progress updates.

```bash
# Open a NEW terminal window and run:
./scripts/contextkeeper.sh project add "/path/to/your/code" "My Awesome Project"
```
This single command will:
1.  **Immediately** create the project in ContextKeeper (returns task_id)
2.  **Asynchronously** start indexing all relevant files in the background
3.  **Show real-time progress** via terminal progress bar
4.  **Emit WebSocket events** to update any connected dashboard clients
5.  **Notify upon completion** when project is fully indexed and ready

### Step 4: Explore the Real-Time Dashboard
Open your browser and navigate to:
`http://localhost:5556/analytics_dashboard_live.html`

You will see your new project card, now "Active" and ready for interaction. The dashboard features:
- **Live Project Status**: Real-time updates as projects are created and indexed
- **Instant Progress Tracking**: Watch indexing progress bars without refreshing
- **Immediate Focus Changes**: See when colleagues focus on projects
- **Live Governance Updates**: Sacred Plan approvals appear instantly
- **WebSocket Connection**: Persistent connection for zero-latency updates

## 2. Core Workflows: Day-to-Day Usage

### Interacting with Your Project
Once your project is indexed, you can interact with it via the CLI or the real-time dashboard.

#### Using the Interactive Dashboard
The dashboard is the central hub for managing your projects.

*   **Global Search:** Use the search bar at the top to instantly find projects, Sacred Plans, or decisions.
*   **Focusing a Project:** Simply click on a project card. This will highlight it and load its specific governance data in the "Sacred Plans" section.
*   **Real-Time Feedback:** The dashboard uses WebSockets for instant updates. When you add a new project or a colleague focuses on one, the UI updates automatically without needing a refresh. Indexing progress is also shown in real-time.

#### Using the Command-Line Interface (CLI)
The CLI is powerful for scripting and quick actions.

*   **Focus on a Project:**
    ```bash
    # If you know the ID
    ./scripts/contextkeeper.sh project focus <project_id>

    # If you don't, a fuzzy finder will appear!
    ./scripts/contextkeeper.sh project focus
    ```
*   **Ask a Question:**
    ```bash
    # Get a quick answer from the knowledge base
    ./scripts/contextkeeper.sh query "How does the caching layer work?"

    # Get a detailed explanation from the LLM
    ./scripts/contextkeeper.sh query --llm "Explain our authentication strategy"
    ```

## 3. 🏛️ Governance with Sacred Plans

Sacred Plans are the heart of ContextKeeper's governance features, allowing you to define and enforce architectural rules.

### Managing Plans from the Dashboard
This is the recommended and most intuitive way to manage Sacred Plans.

1.  **Focus a Project:** Click on a project card in the dashboard.
2.  **View Plans:** The "Sacred Plans Governance" section will appear, listing all plans for that project.
3.  **Approve a Plan:**
    *   Click the "Approve" button next to a "draft" plan.
    *   A secure modal will appear.
    *   Enter your name, the verification code from the plan file, and your `SACRED_APPROVAL_KEY`.
    *   Acknowledge the security warning and confirm.
    *   The plan's status will update to "Approved" in real-time.

### Managing Plans from the CLI
For scripting or terminal-native users.

*   **Create a Plan:**
    1.  Write your architectural rules in a Markdown file (e.g., `api_design.md`).
    2.  Submit it to ContextKeeper:
        ```bash
        ./scripts/contextkeeper.sh sacred create <project_id> "API Design Guidelines" api_design.md
        ```
*   **Approve a Plan:**
    ```bash
    ./scripts/contextkeeper.sh sacred approve <plan_id>
    # You will be prompted for your name, verification code, and approval key.
    ```

## 4. 📊 Analytics and Real-Time Insights

ContextKeeper includes a powerful analytics service providing real-time insights into your project's governance health.

### Accessing Analytics
*   **API Endpoint:** Use the `/analytics/sacred` endpoint to get detailed metrics.
    ```bash
    curl http://localhost:5556/analytics/sacred
    ```
*   **Dashboard Integration:** Analytics are automatically loaded in the dashboard and update based on WebSocket events.
*   **Real-Time Updates:** Metrics refresh when governance events occur (plan approvals, decision additions).

### What it Tracks
*   **Sacred Plans:** Total count, approval rates, compliance metrics
*   **Project Health:** Alignment scores, governance adherence
*   **Decision Tracking:** Architectural decision logs and impact analysis
*   **Drift Detection:** Monitoring of code changes against approved plans

### Technical Implementation
*   **Service Layer:** The `AnalyticsService` (`src/ck_analytics/`) calculates metrics on-demand
*   **Metrics Calculator:** `SacredMetricsCalculator` computes governance health scores
*   **Caching:** Results cached for 5 minutes to ensure high performance
*   **Event-Driven Updates:** WebSocket events trigger metric recalculation when needed

## 5. 🔌 API and Integration

### Key API Endpoints
*   `POST /projects/create-and-index`: Creates and indexes a project asynchronously.
*   `GET /tasks/{task_id}`: Checks the status of a background task (like indexing).
*   `GET /search?q=...`: Powers the global search on the dashboard.
*   `GET /analytics/sacred`: Provides governance metrics.
*   `POST /sacred/plans/{id}/approve`: Approves a Sacred Plan.

### Real-Time Events (WebSockets)
Your client can listen for comprehensive real-time events from the Socket.IO server at `http://localhost:5556`:

#### Project Management Events
*   `indexing_progress`: `{ "project_id": "...", "progress": 25, "current_file": "src/main.py" }`
*   `indexing_complete`: `{ "project_id": "...", "total_files": 247, "total_chunks": 1583 }`
*   `indexing_error`: `{ "project_id": "...", "error": "Permission denied", "failed_file": "..." }`
*   `focus_changed`: `{ "project_id": "...", "project_name": "WebApp Backend" }`
*   `project_updated`: `{ "project_id": "...", "changes": {...} }`

#### Governance Events
*   `decision_added`: `{ "project_id": "...", "decision": {...}, "timestamp": "..." }`
*   `objective_updated`: `{ "project_id": "...", "objective": {...}, "action": "completed" }`
*   `sacred_plan_created`: `{ "project_id": "...", "plan_id": "...", "title": "..." }`
*   `sacred_plan_approved`: `{ "project_id": "...", "plan_id": "...", "approver": "..." }`

#### Integration Example (JavaScript)
```javascript
const socket = io('http://localhost:5556');
socket.on('indexing_progress', (data) => {
    console.log(`Project ${data.project_id}: ${data.progress}% complete`);
    updateProgressBar(data.progress);
});
```

## 6. 🔧 Troubleshooting

### Common Issues
*   **Server won't start:** Check if port 5556 is already in use (`lsof -i :5556`).
*   **No results from queries:** Ensure project indexing is complete. Check the project card on the dashboard for "Active" status.
*   **Plan approval fails:** Double-check your `SACRED_APPROVAL_KEY` in the `.env` file and ensure you are entering the correct verification code.

### Real-Time & Async Issues
*   **Dashboard not updating:** Check browser console for WebSocket connection errors. Ensure server is running.
*   **Indexing stuck:** Check the task status with `curl http://localhost:5556/tasks/<task_id>`. Look for permission or API key issues.
*   **Progress not showing:** Verify WebSocket connection in browser dev tools. Network tab should show Socket.IO connections.
*   **Events not firing:** Check server logs for error messages. Ensure all required environment variables are set.

### System Status Checks
```bash
# Check if server is running
curl http://localhost:5556/health

# Check WebSocket connectivity
curl -I http://localhost:5556/socket.io/

# View recent logs
tail -f contextkeeper.log  # if logging is enabled
```

---

**Happy coding with ContextKeeper! 🚀**
