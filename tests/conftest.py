#!/usr/bin/env python3
"""
conftest.py - Shared test configuration and fixtures for ContextKeeper v3

This file provides reusable test fixtures and configuration for all test modules.
Ensures consistent test environment setup across the entire test suite.

Created: 2025-07-29 04:17:00 (Australia/Sydney)
"""

import pytest
import tempfile
import shutil
import os
import json
from pathlib import Path
from unittest.mock import Mock, patch
import asyncio
from typing import Dict, Any

# Add parent directory to path for imports
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.sacred.sacred_layer_implementation import (
    SacredLayerManager,
    SacredIntegratedRAGAgent,
    PlanStatus,
)
from src.core.project_manager import ProjectManager
from rag_agent import ProjectKnowledgeAgent

# Test configuration constants
TEST_PROJECT_ID = "test_project_12345"
TEST_API_KEY = "test_api_key_12345"
TEST_PORT = 5557  # Use different port to avoid conflicts


class MockEmbedder:
    """Mock embedder for testing without API calls"""
    
    def embed_documents(self, texts):
        # Return consistent mock embeddings (384 dimensions for testing)
        return [[0.1] * 384 for _ in texts]
    
    def embed_query(self, text):
        return [0.1] * 384


class MockGenAIClient:
    """Mock Google GenAI client for testing"""
    
    def generate_content(self, prompt, **kwargs):
        mock_response = Mock()
        mock_response.text = f"Mock response for: {prompt[:50]}..."
        return mock_response


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    temp_path = tempfile.mkdtemp(prefix="contextkeeper_test_")
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_embedder():
    """Provide a mock embedder for testing"""
    return MockEmbedder()


@pytest.fixture
def mock_genai_client():
    """Provide a mock GenAI client for testing"""
    return MockGenAIClient()


@pytest.fixture
def sacred_manager(temp_dir, mock_embedder):
    """Create a SacredLayerManager instance for testing"""
    return SacredLayerManager(temp_dir, mock_embedder)


@pytest.fixture
def test_project_config():
    """Standard test project configuration"""
    return {
        "project_id": TEST_PROJECT_ID,
        "name": "Test Project",
        "path": "/tmp/test_project",
        "description": "A test project for ContextKeeper testing",
        "status": "active"
    }


@pytest.fixture
def project_manager(temp_dir):
    """Create a ProjectManager instance for testing"""
    return ProjectManager(storage_path=temp_dir)


@pytest.fixture
def mock_rag_agent(temp_dir, mock_embedder):
    """Create a mock RAG agent for testing"""
    with patch('rag_agent.genai') as mock_genai:
        mock_genai.Client.return_value = MockGenAIClient()
        
        # Create minimal RAG agent setup
        agent = Mock()
        agent.project_manager = ProjectManager(storage_path=temp_dir)
        agent.embedder = mock_embedder
        agent.storage_path = temp_dir
        
        return agent


@pytest.fixture
def sacred_integrated_agent(mock_rag_agent):
    """Create SacredIntegratedRAGAgent for testing"""
    return SacredIntegratedRAGAgent(mock_rag_agent)


@pytest.fixture
def sample_plan_content():
    """Sample plan content for testing"""
    return """
# Authentication Architecture Plan

## Overview
This plan outlines the authentication system for the application.

## Components
1. User authentication service
2. Token management
3. Session handling
4. Security protocols

## Implementation Steps
1. Set up authentication middleware
2. Implement JWT token system
3. Create user validation endpoints
4. Add security headers and CORS
5. Test authentication flows

## Security Considerations
- Use HTTPS for all authentication endpoints
- Implement rate limiting
- Add proper input validation
- Store credentials securely
"""


@pytest.fixture
def sample_large_plan_content():
    """Large plan content for testing chunking"""
    base_content = """
# Large Architecture Plan

## Section 1: Overview
This is a comprehensive architecture plan that will be used to test
the chunking functionality of the Sacred Layer system.

## Section 2: Detailed Requirements
"""
    
    # Generate large content by repeating sections
    large_content = base_content
    for i in range(10):
        large_content += f"""
### Subsection 2.{i+1}
This is subsection {i+1} with detailed requirements and specifications.
It contains multiple paragraphs of content to simulate a real-world
architecture document that would need to be chunked for processing.

The content includes technical details, implementation notes, and
various other information that would be found in a comprehensive
architecture plan document.
"""
    
    return large_content


@pytest.fixture
def test_flask_app():
    """Create a test Flask app configuration"""
    return {
        "host": "127.0.0.1",
        "port": TEST_PORT,
        "debug": True,
        "testing": True
    }


@pytest.fixture
def api_base_url():
    """Base URL for API testing"""
    return f"http://127.0.0.1:{TEST_PORT}"


@pytest.fixture
def sample_files_for_ingestion(temp_dir):
    """Create sample files for testing ingestion"""
    files_dir = Path(temp_dir) / "sample_files"
    files_dir.mkdir(exist_ok=True)
    
    # Create sample Python file
    python_file = files_dir / "sample.py"
    python_file.write_text("""
def calculate_fibonacci(n):
    \"\"\"Calculate Fibonacci number using dynamic programming\"\"\"
    if n <= 1:
        return n
    
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    
    return b

if __name__ == "__main__":
    print(calculate_fibonacci(10))
""")
    
    # Create sample markdown file
    md_file = files_dir / "README.md"
    md_file.write_text("""
# Test Project

This is a sample README file for testing the ContextKeeper ingestion system.

## Features
- File processing
- Content extraction  
- Vector embedding
- Intelligent querying

## Usage
Run the application and ingest files for knowledge base creation.
""")
    
    # Create sample configuration file
    config_file = files_dir / "config.json"
    config_file.write_text(json.dumps({
        "database": {
            "host": "localhost",
            "port": 5432,
            "name": "test_db"
        },
        "features": {
            "enable_caching": True,
            "max_connections": 100
        }
    }, indent=2))
    
    return files_dir


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Set up test environment variables"""
    monkeypatch.setenv("GEMINI_API_KEY", TEST_API_KEY)
    monkeypatch.setenv("CONTEXTKEEPER_TEST_MODE", "true")
    monkeypatch.setenv("CONTEXTKEEPER_LOG_LEVEL", "DEBUG")


@pytest.fixture
def mock_file_watcher():
    """Mock file system watcher for testing"""
    watcher = Mock()
    watcher.start = Mock()
    watcher.stop = Mock()
    watcher.is_alive = Mock(return_value=True)
    return watcher


# Test data generators
def generate_test_embeddings(count: int = 5):
    """Generate test embeddings for vector testing"""
    return [[0.1 + i * 0.01] * 384 for i in range(count)]


def generate_test_documents(count: int = 5):
    """Generate test documents for ingestion testing"""
    documents = []
    for i in range(count):
        documents.append({
            "content": f"This is test document {i+1} with sample content for testing.",
            "metadata": {
                "file_path": f"/test/file_{i+1}.txt",
                "file_type": "text",
                "created_at": "2025-07-29T04:17:00Z"
            }
        })
    return documents


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Clean up any test files created during testing"""
    yield
    # Cleanup code runs after each test
    # Remove any temporary files that weren't cleaned up
    temp_patterns = [
        "/tmp/contextkeeper_test*",
        "/tmp/test_project*",
        "test_*.db",
        "*.test.log"
    ]
    
    import glob
    for pattern in temp_patterns:
        for file_path in glob.glob(pattern):
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path, ignore_errors=True)
            except OSError:
                pass  # Ignore cleanup errors


# Performance testing fixtures
@pytest.fixture
def performance_test_data():
    """Generate data for performance testing"""
    return {
        "small_dataset": generate_test_documents(10),
        "medium_dataset": generate_test_documents(100),
        "large_dataset": generate_test_documents(1000),
        "embeddings_small": generate_test_embeddings(10),
        "embeddings_medium": generate_test_embeddings(100),
        "embeddings_large": generate_test_embeddings(1000)
    }