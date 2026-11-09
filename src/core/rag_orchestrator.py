#!/usr/bin/env python3
"""
File: /path/to/contextkeeper/src/core/rag_orchestrator.py
Project: ContextKeeper v3.0
Purpose: Main RAG orchestration - coordinates all system components
Dependencies: ChromaDB, Google GenAI, Sacred Layer, Analytics
Dependents: Flask API, MCP Server, CLI scripts
Created: 2025-08-05 (RESTRUCTURE)
Modified: 2025-08-05

PLANNING CONTEXT:
- Restructure Session [2025-08-05]: Split monolithic rag_agent.py into focused modules
- Decision: Orchestrator pattern to coordinate between core components
- Reason: 2000+ line files violate governance protocol

TODO FROM PLANNING:
- [ ] Extract vector store operations to vector_store.py
- [ ] Move Flask routes to api/flask_app.py  
- [ ] Move query processing to query_processor.py
- [ ] Add proper error handling with circuit breaker
"""

# === NAVIGATION ===
# Previous: ../rag_agent.py (LEGACY - to be deprecated)
# Next: vector_store.py - handles ChromaDB operations
# Child: ../api/flask_app.py - exposes HTTP endpoints
# Child: ../sacred/sacred_manager.py - manages architectural decisions

import os
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import logging

import chromadb
from chromadb.config import Settings
from flask import Flask, request, jsonify
from flask_cors import CORS

from .project_manager import ProjectManager

logger = logging.getLogger(__name__)


class GoogleGenAIEmbeddingFunction:
    """Lightweight wrapper around Google GenAI embeddings for ChromaDB"""

    def __init__(self, api_key: str, model: str = "text-embedding-004"):
        from google import genai

        self.client = genai.Client(api_key=api_key)
        self.model = model

    def __call__(self, input: List[str]) -> List[List[float]]:  # pragma: no cover - thin wrapper
        embeddings = []
        for text in input:
            try:
                response = self.client.models.embed_content(
                    model=self.model,
                    contents=text,
                    task_type="RETRIEVAL_DOCUMENT",
                )
                embeddings.append(response.embeddings[0].values)
            except Exception as exc:  # pragma: no cover - network failure is non-critical in tests
                logger.error("Embedding error: %s", exc)
                embeddings.append([0.0] * 768)
        return embeddings

    def name(self) -> str:
        return f"google_genai_{self.model}"

@dataclass
class RAGOrchestrator:
    """Central coordinator for ContextKeeper components"""

    config: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        """Initialise core subsystems and register API routes"""
        self.config = self.config or {
            "db_path": "./rag_knowledge_db",
            "projects_config_dir": os.path.expanduser("~/.rag_projects"),
            "max_results": 10,
            "embedding_model": "text-embedding-004",
            "api_port": 5556,
        }

        # Project management
        self.project_manager = ProjectManager(self.config.get("projects_config_dir"))

        # Vector store and embedding setup
        api_key = os.getenv("GEMINI_API_KEY", "")
        self.embedding_function = GoogleGenAIEmbeddingFunction(api_key, self.config["embedding_model"])
        self.db = chromadb.HttpClient(host="localhost", port=8000, settings=Settings(anonymized_telemetry=False))

        self.collections: Dict[str, Any] = {}
        self._init_project_collections()

        # Flask application
        self.app = Flask(__name__)
        self.app.config.update(TESTING=False)
        CORS(self.app)
        self._register_routes()

    # ------------------------------------------------------------------
    # Internal helpers
    def _init_project_collections(self) -> None:
        """Ensure a Chroma collection exists for each active project"""
        for project in self.project_manager.get_active_projects():
            name = f"project_{project.project_id}"
            try:
                self.collections[project.project_id] = self.db.get_collection(
                    name=name, embedding_function=self.embedding_function
                )
            except Exception:
                self.collections[project.project_id] = self.db.create_collection(
                    name=name,
                    embedding_function=self.embedding_function,
                    metadata={"hnsw:space": "cosine", "project_name": project.name},
                )

    def _register_routes(self) -> None:
        """Attach core HTTP routes to the Flask application"""

        @self.app.route("/query", methods=["POST"])
        def query_route() -> Any:
            data = request.get_json(force=True)
            question = data.get("query", "")
            project_id = data.get("project_id")
            return jsonify(self.coordinate_query(question, project_id))

        @self.app.route("/health", methods=["GET"])
        def health_route() -> Any:
            return jsonify(self.health_check())

    # ------------------------------------------------------------------
    # Public API
    def coordinate_query(self, query: str, project_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute a vector search scoped to a specific project"""

        if project_id is None:
            return {
                "query": query,
                "error": "No project context specified",
                "results": [],
            }

        if project_id not in self.collections:
            return {
                "query": query,
                "error": f"Project {project_id} not found",
                "results": [],
            }

        try:
            res = self.collections[project_id].query(
                query_texts=[query],
                n_results=self.config.get("max_results", 10),
            )
        except Exception as exc:
            logger.error("Vector store query failed: %s", exc)
            return {"query": query, "error": str(exc), "results": []}

        formatted: List[Dict[str, Any]] = []
        if res and res.get("ids") and res["ids"][0]:
            for idx in range(len(res["ids"][0])):
                formatted.append(
                    {
                        "content": res["documents"][0][idx],
                        "metadata": res["metadatas"][0][idx],
                        "distance": res.get("distances", [[None]])[0][idx],
                        "project_id": project_id,
                    }
                )

        return {"query": query, "project_id": project_id, "results": formatted}

    def health_check(self) -> Dict[str, str]:
        """Aggregate basic health information for system components"""

        status = {"projects": str(len(self.project_manager.projects))}
        try:
            self.db.heartbeat()
            status["vector_store"] = "ok"
        except Exception as exc:  # pragma: no cover - network failure in tests
            status["vector_store"] = f"error: {exc}"

        return status
