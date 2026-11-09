#!/usr/bin/env python3
"""
ContextKeeper v3.0 Sacred Layer - Basic Usage Example

This example demonstrates how to use ContextKeeper programmatically
for project management and sacred plan creation.
"""

import requests
import json
import os
from pathlib import Path

# Configuration
RAG_AGENT_URL = "http://localhost:5556"
SACRED_APPROVAL_KEY = os.getenv("SACRED_APPROVAL_KEY", "your-secret-key")

class ContextKeeperClient:
    """Simple client for ContextKeeper Sacred Layer API"""
    
    def __init__(self, base_url=RAG_AGENT_URL):
        self.base_url = base_url
        self.session = requests.Session()
    
    def create_project(self, name: str, path: str) -> dict:
        """Create a new project"""
        response = self.session.post(f"{self.base_url}/projects", json={
            "name": name,
            "path": path,
            "description": f"Project created from API: {name}"
        })
        return response.json()
    
    def create_sacred_plan(self, project_id: str, title: str, content: str) -> dict:
        """Create a new sacred plan"""
        response = self.session.post(f"{self.base_url}/sacred/plans", json={
            "project_id": project_id,
            "title": title,
            "content": content
        })
        return response.json()
    
    def approve_plan(self, plan_id: str) -> dict:
        """Approve a sacred plan with 2-layer verification"""
        response = self.session.post(f"{self.base_url}/sacred/plans/{plan_id}/approve", json={
            "approval_key": SACRED_APPROVAL_KEY
        })
        return response.json()
    
    def check_drift(self, project_id: str) -> dict:
        """Check drift for a project"""
        response = self.session.get(f"{self.base_url}/sacred/drift/{project_id}")
        return response.json()

def main():
    """Example usage of ContextKeeper Sacred Layer"""
    
    print("🚀 ContextKeeper v3.0 Sacred Layer - Basic Usage Example")
    print("=" * 60)
    
    # Initialize client
    client = ContextKeeperClient()
    
    try:
        # 1. Create a project
        print("\n1. Creating project...")
        project = client.create_project(
            name="E-commerce Platform",
            path="/path/to/ecommerce-project"
        )
        project_id = project.get("project_id")
        print(f"✅ Created project: {project_id}")
        
        # 2. Create sacred plan
        print("\n2. Creating sacred plan...")
        plan_content = """
# Database Architecture - Sacred Plan

## Core Principles
- Use PostgreSQL as primary database
- Implement read replicas for scaling
- All migrations must be backward compatible

## Schema Design
- Use UUID primary keys for all entities
- Implement soft deletes with deleted_at timestamp
- All tables must have created_at and updated_at

## Security Requirements
- All sensitive data encrypted at rest
- Database connections must use TLS
- Implement row-level security where applicable
        """.strip()
        
        plan = client.create_sacred_plan(
            project_id=project_id,
            title="Database Architecture",
            content=plan_content
        )
        plan_id = plan.get("plan_id")
        print(f"✅ Created sacred plan: {plan_id}")
        
        # 3. Approve the plan
        print("\n3. Approving sacred plan...")
        approval = client.approve_plan(plan_id)
        print(f"✅ Plan approved: {approval.get('status')}")
        
        # 4. Check drift
        print("\n4. Checking drift detection...")
        drift = client.check_drift(project_id)
        print(f"✅ Drift status: {drift.get('alignment_status')}")
        print(f"   Alignment score: {drift.get('alignment_score', 'N/A')}")
        
        print("\n🎉 Example completed successfully!")
        print("\nNext steps:")
        print("- Use Claude Code with MCP integration")
        print("- Create more sacred plans for your architecture")
        print("- Monitor drift detection during development")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to ContextKeeper")
        print("   Make sure the Sacred Layer is running: python rag_agent.py start")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()