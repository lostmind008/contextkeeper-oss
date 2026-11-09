"""Flask application wiring for ContextKeeper"""

from src.core.rag_orchestrator import RAGOrchestrator

orchestrator = RAGOrchestrator()
app = orchestrator.app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=orchestrator.config.get("api_port", 5556))
