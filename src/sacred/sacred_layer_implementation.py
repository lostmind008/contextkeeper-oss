#!/usr/bin/env python3
# flake8: noqa
# fmt: off
"""
# GOVERNANCE HEADER - SKELETON FIRST DEVELOPMENT
# File: /path/to/contextkeeper/src/sacred/sacred_layer_implementation.py
# Project: ContextKeeper v3.0
# Purpose: Immutable architectural decisions with 2-layer verification
# Dependencies: chromadb, langchain_text_splitters, hashlib, json
# Dependents: rag_agent.py, sacred CLI commands, drift detection systems
# Created: 2025-08-03
# Modified: 2025-08-05

## PLANNING CONTEXT EMBEDDED
The Sacred Layer provides architectural governance for ContextKeeper:
- Immutable storage of approved architectural plans
- 2-layer verification system (draft → pending → approved)
- Isolated ChromaDB collection for sacred documents
- Drift detection between plans and implementation
- Plan superseding with full audit trail

## ARCHITECTURAL DECISIONS
1. Sacred plans are write-once, read-many (WORM)
2. Approval requires SACRED_APPROVAL_KEY environment variable
3. Each plan gets unique hash-based identifier
4. Plans stored both in ChromaDB and filesystem
5. Drift detection uses semantic similarity

## TODO FROM PLANNING
- [ ] Add plan visualization capabilities
- [ ] Implement plan diffing for superseded versions
- [ ] Add automated drift notifications
- [ ] Create plan templates for common architectures

Sacred Layer Implementation for ContextKeeper
Provides immutable plan storage with 2-layer verification and isolated embeddings
"""
import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path
import asyncio
# For chunking large plans
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb
from chromadb.config import Settings
logger = logging.getLogger(__name__)
class PlanStatus(Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    LOCKED = "locked"
    SUPERSEDED = "superseded"
@dataclass
class SacredPlan:
    """Represents an approved, immutable plan"""
    plan_id: str
    project_id: str
    title: str
    content: str  # Full content or reference to chunks
    status: PlanStatus
    created_at: str
    approved_at: Optional[str]
    approved_by: Optional[str]
    verification_code: Optional[str]
    chunk_count: int = 1
    metadata: Dict[str, Any] = None
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
class SacredLayerManager:
    """Manages sacred plans with verification and isolation"""

    def __init__(self, db_path: str, embedder):
        self.db_path = Path(db_path)
        self.embedder = embedder
        self.plans_dir = self.db_path / "sacred_plans"
        self.plans_dir.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client for sacred collections
        self.client = chromadb.PersistentClient(
            path=str(self.db_path / "sacred_chromadb"),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=False  # Prevent accidental resets
            )
        )

        # Text splitter for large plans
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ".", " ", ""],
            length_function=len
        )

        # Load plan registry
        self.plans_registry = self._load_registry()
    def _load_registry(self) -> Dict[str, SacredPlan]:
        """Load registry of all sacred plans"""
        registry_file = self.plans_dir / "registry.json"
        if registry_file.exists():
            with open(registry_file, 'r') as f:
                data = json.load(f)
                registry = {}
                for plan_id, plan_data in data.items():
                    # Convert string status back to enum
                    if 'status' in plan_data and isinstance(plan_data['status'], str):
                        plan_data['status'] = PlanStatus(plan_data['status'])
                    registry[plan_id] = SacredPlan(**plan_data)
                return registry
        return {}
    def _save_registry(self):
        """Persist registry to disk"""
        registry_file = self.plans_dir / "registry.json"
        with open(registry_file, 'w') as f:
            # Convert enum to string for JSON serialization
            serializable_data = {}
            for plan_id, plan in self.plans_registry.items():
                plan_dict = plan.__dict__.copy()
                plan_dict['status'] = plan.status.value  # Convert enum to string
                serializable_data[plan_id] = plan_dict
            json.dump(serializable_data, f, indent=2)
    def _get_sacred_collection(self, project_id: str):
        """Get or create sacred collection for a project"""
        collection_name = f"sacred_{project_id}"
        try:
            return self.client.get_collection(collection_name)
        except:
            return self.client.create_collection(
                name=collection_name,
                metadata={
                    "type": "sacred",
                    "project_id": project_id,
                    "created_at": datetime.now().isoformat()
                }
            )
    async def async_create_plan(self, project_id: str, title: str,
                                content: str, file_path: Optional[str] = None) -> SacredPlan:
        """Create a new plan in draft status"""
        if file_path and os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

        plan_id = hashlib.sha256(content.encode()).hexdigest()[:12]

        plan = SacredPlan(
            plan_id=plan_id,
            project_id=project_id,
            title=title,
            content=content,
            status=PlanStatus.DRAFT,
            created_at=datetime.now().isoformat(),
            approved_at=None,
            approved_by=None,
            verification_code=None
        )

        self.plans_registry[plan_id] = plan
        self._save_registry()
        plan_file = self.plans_dir / f"{plan_id}.txt"
        with open(plan_file, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Created draft plan: {plan_id} for project {project_id}")
        return plan

    def create_plan(self, project_id: str, title: str,
                    content: str, file_path: Optional[str] = None) -> SacredPlan:
        """Synchronous wrapper around async_create_plan"""
        return asyncio.run(self.async_create_plan(project_id, title, content, file_path))
    async def async_approve_plan(self, plan_id: str, approver: str,
                                 verification_code: str, secondary_verification: str) -> Tuple[bool, str]:
        """Approve a plan with 2-layer verification"""
        if plan_id not in self.plans_registry:
            return False, "Plan not found"

        plan = self.plans_registry[plan_id]
        if plan.status != PlanStatus.DRAFT:
            return False, f"Plan is not in draft status (current: {plan.status.value})"

        expected_code = self._generate_verification_code(plan)
        if verification_code != expected_code:
            logger.warning(f"Failed verification for plan {plan_id}: invalid code")
            return False, "Invalid verification code"

        if not self._verify_secondary(approver, secondary_verification):
            logger.warning(f"Failed secondary verification for plan {plan_id}")
            return False, "Secondary verification failed"

        plan.status = PlanStatus.APPROVED
        plan.approved_at = datetime.now().isoformat()
        plan.approved_by = approver
        plan.verification_code = verification_code

        await self._embed_and_store_plan_async(plan)

        self._save_registry()
        logger.info(f"Plan {plan_id} approved by {approver}")
        return True, "Plan approved and locked"

    def approve_plan(self, plan_id: str, approver: str,
                     verification_code: str, secondary_verification: str) -> Tuple[bool, str]:
        """Synchronous wrapper around async_approve_plan"""
        return asyncio.run(self.async_approve_plan(plan_id, approver, verification_code, secondary_verification))
    async def _embed_and_store_plan_async(self, plan: SacredPlan):
        """Embed and store plan in isolated sacred collection"""
        collection = self._get_sacred_collection(plan.project_id)
        # Load full content
        plan_file = self.plans_dir / f"{plan.plan_id}.txt"
        with open(plan_file, 'r', encoding='utf-8') as f:
            content = f.read()
        # Check if chunking is needed
        if len(content) > 2000:  # Threshold for chunking
            chunks = self.text_splitter.split_text(content)
            plan.chunk_count = len(chunks)

            # Embed and store each chunk
            for i, chunk in enumerate(chunks):
                chunk_id = f"{plan.plan_id}_chunk_{i}"
                embedding = await self.embedder.embed_text(chunk)
                collection.upsert(
                    ids=[chunk_id],
                    embeddings=[embedding],
                    documents=[chunk],
                    metadatas=[{
                        'plan_id': plan.plan_id,
                        'type': 'sacred_plan',
                        'status': plan.status.value,
                        'locked': True,
                        'chunk_index': i,
                        'total_chunks': len(chunks),
                        'title': plan.title,
                        'approved_at': plan.approved_at,
                        'approved_by': plan.approved_by
                    }]
                )
                logger.debug(f"Stored chunk {i+1}/{len(chunks)} for plan {plan.plan_id}")
        else:
            # Store as single document
            embedding = await self.embedder.embed_text(content)
            collection.upsert(
                ids=[plan.plan_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[{
                    'plan_id': plan.plan_id,
                    'type': 'sacred_plan',
                    'status': plan.status.value,
                    'locked': True,
                    'chunk_index': 0,
                    'total_chunks': 1,
                    'title': plan.title,
                    'approved_at': plan.approved_at,
                    'approved_by': plan.approved_by
                }]
            )

    async def async_query_sacred_plans(self, project_id: str, query: str,
                                       reconstruct: bool = True) -> Dict[str, Any]:
        """Query sacred plans with optional reconstruction"""
        collection = self._get_sacred_collection(project_id)

        query_embedding = await self.embedder.embed_text(query)

        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=10,
                where={
                    "type": {"$eq": "sacred_plan"},
                    "status": {"$eq": "approved"}
                }
            )
        except Exception as e:
            logger.warning(f"ChromaDB filter error with new syntax: {e}, trying older syntax")
            try:
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=10,
                    where={"$and": [{"type": "sacred_plan"}, {"status": "approved"}]}
                )
            except Exception as e2:
                logger.error(f"ChromaDB filter error with both syntaxes: {e2}")
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=10
                )

        if not results['ids'][0]:
            return {"plans": [], "query": query}

        if reconstruct:
            reconstructed_plans = {}

            for i, metadata in enumerate(results['metadatas'][0]):
                plan_id = metadata['plan_id']

                if plan_id not in reconstructed_plans:
                    reconstructed_plans[plan_id] = {
                        'plan_id': plan_id,
                        'title': metadata['title'],
                        'chunks': {},
                        'total_chunks': metadata['total_chunks'],
                        'relevance_score': results['distances'][0][i] if 'distances' in results else None
                    }
                chunk_index = metadata['chunk_index']
                reconstructed_plans[plan_id]['chunks'][chunk_index] = results['documents'][0][i]

            for plan_id, plan_data in reconstructed_plans.items():
                if len(plan_data['chunks']) == plan_data['total_chunks']:
                    sorted_chunks = [
                        plan_data['chunks'][i]
                        for i in sorted(plan_data['chunks'].keys())
                    ]
                    plan_data['content'] = '\n'.join(sorted_chunks)
                    plan_data['reconstruction_complete'] = True
                else:
                    plan_data['content'] = '\n'.join([
                        plan_data['chunks'][i]
                        for i in sorted(plan_data['chunks'].keys())
                    ])
                    plan_data['reconstruction_complete'] = False
                    plan_data['missing_chunks'] = [
                        i for i in range(plan_data['total_chunks'])
                        if i not in plan_data['chunks']
                    ]
                del plan_data['chunks']

            return {
                "plans": list(reconstructed_plans.values()),
                "query": query,
                "reconstructed": True
            }

        return {
            "results": results,
            "query": query,
            "reconstructed": False
        }

    def query_sacred_plans(self, project_id: str, query: str,
                           reconstruct: bool = True) -> Dict[str, Any]:
        """Synchronous wrapper around async_query_sacred_plans"""
        return asyncio.run(self.async_query_sacred_plans(project_id, query, reconstruct))

    def lock_plan(self, plan_id: str) -> Tuple[bool, str]:
        """Lock an approved plan to prevent modifications"""
        if plan_id not in self.plans_registry:
            return False, "Plan not found"

        plan = self.plans_registry[plan_id]

        if plan.status != PlanStatus.APPROVED:
            return False, "Only approved plans can be locked"

        plan.status = PlanStatus.LOCKED
        self._save_registry()
        logger.info(f"Plan {plan_id} locked")
        return True, "Plan locked successfully"
    def supersede_plan(self, old_plan_id: str, new_plan_id: str) -> Tuple[bool, str]:
        """Mark a plan as superseded by a new plan"""
        if old_plan_id not in self.plans_registry:
            return False, "Old plan not found"

        if new_plan_id not in self.plans_registry:
            return False, "New plan not found"

        old_plan = self.plans_registry[old_plan_id]
        new_plan = self.plans_registry[new_plan_id]

        if new_plan.status not in [PlanStatus.APPROVED, PlanStatus.LOCKED]:
            return False, "New plan must be approved or locked"

        old_plan.status = PlanStatus.SUPERSEDED
        old_plan.metadata['superseded_by'] = new_plan_id
        old_plan.metadata['superseded_at'] = datetime.now().isoformat()

        new_plan.metadata['supersedes'] = old_plan_id
        self._save_registry()
        logger.info(f"Plan {old_plan_id} superseded by {new_plan_id}")
        return True, "Plan superseded successfully"
    def _generate_verification_code(self, plan: SacredPlan) -> str:
        """Generate verification code for a plan"""
        # Combine plan content hash with timestamp for unique code
        content_hash = hashlib.sha256(plan.content.encode()).hexdigest()
        time_component = plan.created_at[:10].replace('-', '')
        return f"{content_hash[:8]}-{time_component}"

    def _verify_secondary(self, approver: str, verification: str) -> bool:
        """Perform secondary verification"""
        # This could be:
        # - Password check
        # - 2FA code validation
        # - Biometric verification
        # - Custom business logic

        # For demo, check against environment variable
        expected = os.environ.get("SACRED_APPROVAL_KEY")
        if not expected:
            logger.error("SACRED_APPROVAL_KEY environment variable is not set")
            raise RuntimeError(
                "SACRED_APPROVAL_KEY must be configured; approval cannot proceed"
            )
        return verification == expected
    def get_plan_status(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get status and metadata for a plan"""
        if plan_id not in self.plans_registry:
            return None

        plan = self.plans_registry[plan_id]
        return {
            'plan_id': plan.plan_id,
            'title': plan.title,
            'status': plan.status.value,
            'created_at': plan.created_at,
            'approved_at': plan.approved_at,
            'approved_by': plan.approved_by,
            'chunk_count': plan.chunk_count,
            'metadata': plan.metadata
        }


    def list_plans(self, project_id: Optional[str] = None,
                  status: Optional[PlanStatus] = None) -> List[Dict[str, Any]]:
        """List all plans with optional filtering"""
        plans = []

        for plan in self.plans_registry.values():
            # Apply filters
            if project_id and plan.project_id != project_id:
                continue
            if status and plan.status != status:
                continue

            plans.append({
                'plan_id': plan.plan_id,
                'project_id': plan.project_id,
                'title': plan.title,
                'status': plan.status.value,
                'created_at': plan.created_at,
                'approved_at': plan.approved_at,
                'chunk_count': plan.chunk_count
            })

        return sorted(plans, key=lambda x: x['created_at'], reverse=True)

    def get_plans_statistics(self) -> Dict[str, Any]:
        """Get comprehensive plan statistics for analytics"""
        stats = {
            'total_plans': len(self.plans_registry),
            'by_status': {},
            'by_project': {}
        }

        for plan in self.plans_registry.values():
            status = plan.status.value
            project_id = plan.project_id

            # Count by status
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1

            # Count by project
            stats['by_project'][project_id] = stats['by_project'].get(project_id, 0) + 1

        return stats

    def get_project_plan_summary(self, project_id: str) -> Dict[str, Any]:
        """Get plan summary for specific project"""
        project_plans = [
            plan for plan in self.plans_registry.values()
            if plan.project_id == project_id
        ]

        return {
            'total_plans': len(project_plans),
            'approved_plans': len([p for p in project_plans if p.status == PlanStatus.APPROVED]),
            'draft_plans': len([p for p in project_plans if p.status == PlanStatus.DRAFT]),
            'locked_plans': len([p for p in project_plans if p.status == PlanStatus.LOCKED]),
            'superseded_plans': len([p for p in project_plans if p.status == PlanStatus.SUPERSEDED])
        }

# Integration with main RAG agent
class SacredIntegratedRAGAgent:
    """Extension to integrate sacred layer with RAG agent"""

    def __init__(self, rag_agent):
        self.rag_agent = rag_agent
        self.sacred_manager = SacredLayerManager(
            db_path=rag_agent.config['db_path'],
            embedder=rag_agent
        )
    async def create_sacred_plan(self, project_id: str, title: str,
                               content_or_file: str) -> Dict[str, Any]:
        """Create a new sacred plan"""
        if os.path.isfile(content_or_file):
            plan = await self.sacred_manager.async_create_plan(
                project_id, title, "", file_path=content_or_file
            )
        else:
            plan = await self.sacred_manager.async_create_plan(
                project_id, title, content_or_file
            )

        return {
            'plan_id': plan.plan_id,
            'status': 'created',
            'verification_code': self.sacred_manager._generate_verification_code(plan)
        }

    async def approve_sacred_plan(self, plan_id: str, approver: str,
                                verification_code: str, secondary: str) -> Dict[str, Any]:
        """Approve a sacred plan with verification"""
        success, message = await self.sacred_manager.async_approve_plan(
            plan_id, approver, verification_code, secondary
        )

        return {
            'success': success,
            'message': message,
            'plan_id': plan_id if success else None
        }

    async def query_sacred_context(self, project_id: str, query: str) -> Dict[str, Any]:
        """Query sacred plans for context"""
        results = await self.sacred_manager.async_query_sacred_plans(
            project_id, query, reconstruct=True
        )

        # Format for AI consumption
        if results['plans']:
            context = "# Sacred Plans Context\n\n"
            for plan in results['plans']:
                context += f"## {plan['title']}\n"
                context += f"Status: Approved and Locked\n"
                context += f"Relevance: {plan.get('relevance_score', 'N/A')}\n\n"
                if plan.get('reconstruction_complete', True):
                    context += plan['content'][:1000]  # First 1000 chars
                    if len(plan['content']) > 1000:
                        context += "\n... (truncated)"
                else:
                    context += f"Warning: Partial reconstruction ({len(plan.get('missing_chunks', []))} chunks missing)\n"
                    context += plan['content'][:500]
                context += "\n\n---\n\n"

            return {
                'context': context,
                'plan_count': len(results['plans']),
                'query': query
            }

        return {
            'context': "No sacred plans found for this query.",
            'plan_count': 0,
            'query': query
        }
    def check_against_sacred_plans(self, project_id: str,
                                 proposed_action: str) -> Dict[str, Any]:
        """Check if a proposed action violates sacred plans"""
        # This would use drift detection logic
        # For now, return a simple check
        return {
            'allowed': True,
            'warnings': [],
            'relevant_plans': []
        }
