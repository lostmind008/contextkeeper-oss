#!/usr/bin/env python3
"""
File: /path/to/contextkeeper/rag_agent.py
Project: ContextKeeper v3.0
Purpose: Main orchestrator - Flask API server, ChromaDB management, multi-project RAG system
Dependencies: ChromaDB, Flask, Sacred Layer, Project Manager, Analytics
Dependents: MCP Server, CLI scripts, Dashboard, All system components
Created: 2025-07-XX
Modified: 2025-08-05

PLANNING CONTEXT:
Core RAG agent implementing multi-project context management with sacred architectural
principles. Serves as the central orchestrator for all ContextKeeper operations including:
- Multi-project isolation with ChromaDB collections
- Sacred layer architectural decision management
- Real-time analytics and event tracking
- Flask API endpoints for all system interactions
- Git integration and development activity monitoring

ARCHITECTURAL DECISIONS:
- Each project gets isolated ChromaDB collection for content separation
- Sacred layer provides immutable architectural decision storage
- Event-driven architecture for real-time development tracking
- Australian English spelling throughout (colour, behaviour, realise)
- Conversational comment style for maintainability

TODO FROM PLANNING:
- [ ] Implement automatic project indexing after creation
- [ ] Add visual indicators for indexed vs non-indexed projects
- [ ] Enhance file browser integration for project paths
- [ ] Optimise ChromaDB query performance for large codebases
- [ ] Add project archival and cleanup mechanisms
"""

# === NAVIGATION ===
# Previous: N/A - This is the main orchestrator
# Next: mcp-server/enhanced_mcp_server.js - Exposes tools to Claude Code
# Children: project_manager.py, sacred_layer_implementation.py, analytics components
# Dashboard: analytics_dashboard_live.html - Consumes this API
"""
ContextKeeper - Multi-Project RAG Knowledge Agent v2.0

Copyright 2025 LostMindAI

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

ContextKeeper maintains persistent knowledge across multiple projects
and coding sessions using vector search, intelligent code indexing,
and comprehensive project management.
"""

import os
import re
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
import hashlib
import argparse
import uuid
import concurrent.futures

# Core dependencies
import chromadb
from chromadb.config import Settings
from google import genai
from google.genai.types import HttpOptions
import tiktoken
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman

# Import security modules
from src.security.security_config import SecurityConfig
from src.security.security_validator import SecurityValidator, security_logger

# Import ProjectManager for multi-project support
from src.core.project_manager import ProjectManager, ProjectStatus

# Import v3.0 Sacred Layer components
from src.sacred.sacred_layer_implementation import SacredLayerManager, SacredIntegratedRAGAgent
from src.tracking.git_activity_tracker import GitActivityTracker, GitIntegratedRAGAgent
from src.sacred.enhanced_drift_sacred import SacredDriftDetector, add_sacred_drift_endpoint

# ChromaDB embedding function for Google GenAI
class GoogleGenAIEmbeddingFunction:
    """Custom embedding function for ChromaDB using Google's text-embedding-004"""
    
    def __init__(self, api_key: str, model: str = "text-embedding-004"):
        self.client = genai.Client(api_key=api_key)
        self.model = model
    
    def __call__(self, input: List[str]) -> List[List[float]]:
        """Embed a list of texts and return embeddings"""
        embeddings = []
        for text in input:
            try:
                response = self.client.models.embed_content(
                    model=self.model,
                    contents=text,
                    task_type="RETRIEVAL_DOCUMENT" # This is the key addition
                )
                embeddings.append(response.embeddings[0].values)
            except Exception as e:
                logger.error(f"Embedding error for text: {e}")
                # Return zero vector of correct dimension on error
                embeddings.append([0.0] * 768)
        return embeddings
    
    def name(self) -> str:
        """Return the name of the embedding function"""
        return f"google_genai_{self.model}"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rag_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
CONFIG = {
    "db_path": "./rag_knowledge_db",
    "projects_config_dir": os.path.expanduser("~/.rag_projects"),
    "default_file_extensions": [".py", ".js", ".jsx", ".ts", ".tsx", ".md", ".json", ".yaml"],
    # Legacy support - these dirs will be imported as a project on first run
    "legacy_watch_dirs": [
        # Removed hardcoded legacy directories - create projects manually instead
    ],
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "max_results": 10,
    "embedding_model": "gemini-embedding-001",
    "api_port": 5556,
    # Directory patterns to ignore during ingestion
    "ignore_directories": [
        "node_modules",
        ".git", 
        "__pycache__",
        ".pytest_cache",
        "venv",
        ".venv",
        "env",
        ".env",
        "build",
        "dist",
        ".next",
        ".nuxt",
        "coverage",
        ".coverage",
        ".nyc_output",
        "logs",
        "tmp",
        "temp",
        ".cache",
        ".tox",
        ".mypy_cache",
        ".sass-cache",
        "bower_components",
        "jspm_packages",
        # IDE and editor directories
        ".vscode",
        ".idea",
        ".vs",
        ".atom",
        ".sublime-text",
        # Additional build/cache directories
        "target",
        "bin",
        "obj",
        ".gradle",
        ".mvn",
        # OS and system directories
        ".Trash",
        "System Volume Information",
        "$RECYCLE.BIN"
    ],
    # File patterns to ignore during ingestion
    "ignore_files": [
        "*.log",
        "*.tmp",
        "*.temp",
        "*.pyc",
        "*.pyo",
        "*.pyd",
        "*.so",
        "*.egg",
        "*.egg-info",
        ".DS_Store",
        "Thumbs.db",
        "*.min.js",
        "*.min.css",
        "package-lock.json",
        "yarn.lock",
        "*.bundle.js",
        "*.chunk.js",
        # Binary and media files
        "*.exe", "*.dll", "*.bin", "*.dat",
        "*.jpg", "*.jpeg", "*.png", "*.gif", "*.bmp", "*.svg", "*.ico",
        "*.mp3", "*.mp4", "*.avi", "*.mov", "*.wav", "*.pdf",
        # Archive files
        "*.zip", "*.tar", "*.gz", "*.rar", "*.7z",
        # Non-relevant programming languages for this project
        "*.java", "*.class", "*.jar",
        "*.c", "*.cpp", "*.h", "*.hpp", "*.o",
        "*.cs", "*.vb", "*.fs",
        "*.php", "*.rb", "*.go", "*.rs", "*.kt", "*.swift",
        "*.scala", "*.clj", "*.r", "*.m", "*.pl", "*.lua",
        # Database and other binary formats
        "*.db", "*.sqlite", "*.mdb",
        "*.lock", "*.pid",
        # IDE and editor files
        "*.swp", "*.swo", "*~", "*.bak", "*.orig",
        ".gitignore", ".gitattributes", ".gitmodules",
        "*.iml", "*.sln", "*.vcxproj", "*.csproj",
        # Configuration files that might contain sensitive data
        "*.env", "*.env.*", ".env.*",
        # Test and coverage files
        "*.coverage", ".coverage.*", "coverage.xml",
        # Package manager files
        "composer.lock", "Pipfile.lock", "poetry.lock",
        # Documentation builds
        "*.pdf", "*.docx", "*.xlsx", "*.pptx"
    ],
    "sensitive_patterns": [
        r'api[_-]?key\s*[:=]\s*["\']([^"\']+)["\']',
        r'password\s*[:=]\s*["\']([^"\']+)["\']',
        r'secret\s*[:=]\s*["\']([^"\']+)["\']',
        r'token\s*[:=]\s*["\']([^"\']+)["\']',
        r'stripe[_-]?key\s*[:=]\s*["\']([^"\']+)["\']'
    ]
}

class SecurityFilter:
    """Filters sensitive information before embedding"""
    
    def __init__(self, patterns: List[str]):
        self.patterns = [re.compile(p, re.IGNORECASE) for p in patterns]
    
    def clean(self, content: str) -> str:
        """Remove sensitive data from content"""
        cleaned = content
        for pattern in self.patterns:
            cleaned = pattern.sub('[REDACTED]', cleaned)
        return cleaned

class PathFilter:
    """Filters files and directories that should be ignored during ingestion"""
    
    def __init__(self, ignore_directories: List[str], ignore_files: List[str]):
        self.ignore_directories = set(ignore_directories)
        self.ignore_file_patterns = ignore_files
        # Compile file patterns for glob-style matching
        self.compiled_file_patterns = []
        for pattern in ignore_files:
            # Convert glob pattern to regex
            regex_pattern = pattern.replace('*', '.*').replace('?', '.')
            self.compiled_file_patterns.append(re.compile(f'^{regex_pattern}$', re.IGNORECASE))
    
    def should_ignore_directory(self, dir_name: str) -> bool:
        """Check if a directory should be ignored"""
        # Always ignore hidden directories (starting with .)
        if dir_name.startswith('.'):
            return True
        
        # Check against ignore list
        return dir_name in self.ignore_directories
    
    def should_ignore_file(self, file_name: str) -> bool:
        """Check if a file should be ignored"""
        # Check against file patterns
        for pattern in self.compiled_file_patterns:
            if pattern.match(file_name):
                return True
        return False
    
    def _should_ignore_enhanced_patterns(self, file_path: str) -> bool:
        """
        Enhanced pattern matching for problematic directory structures.
        Catches nested patterns that basic directory name matching misses.
        """
        # Convert to lowercase for case-insensitive matching
        path_lower = file_path.lower()
        
        # Split path using both Unix and Windows separators for cross-platform compatibility
        # Replace backslashes with forward slashes first, then split
        normalised_path = file_path.replace('\\', '/')
        path_parts = [part for part in normalised_path.split('/') if part]  # Remove empty parts
        
        # Check for venv-like directories using endswith logic
        for part in path_parts:
            part_lower = part.lower()
            # Catch any directory name ending with 'venv' (handles .venv, demo_venv, test_venv, etc.)
            if part_lower.endswith('venv'):
                return True
            # Also catch standalone '.venv' directory names
            if part_lower == '.venv':
                return True
        
        # Check for nested problematic directories anywhere in the path
        # Use both Unix and Windows path separators for cross-platform compatibility
        nested_patterns = [
            # Python package installations
            '/site-packages/',
            '\\site-packages\\',
            'site-packages/',      # Also catch without leading separator
            'site-packages\\',
            
            # Python cache directories
            '/__pycache__/',
            '\\__pycache__\\',
            '__pycache__/',        # Also catch without leading separator
            '__pycache__\\',
            
            # Node.js dependencies
            '/node_modules/',
            '\\node_modules\\',
            'node_modules/',       # Also catch without leading separator
            'node_modules\\',
            
            # Git repository data
            '/.git/',
            '\\.git\\',
            '.git/',               # Also catch without leading separator
            '.git\\',
            
            # Distribution/build directories
            '/dist/',
            '\\dist\\',
            '/build/',
            '\\build\\',
        ]
        
        # Check if any nested pattern exists in the path
        # This approach catches patterns anywhere in the path structure
        for pattern in nested_patterns:
            if pattern in path_lower:
                return True
                
        return False
    
    def should_ignore_path(self, file_path: str) -> bool:
        """
        Check if any part of the path should be ignored.
        Uses both original logic (backwards compatibility) and enhanced pattern matching.
        """
        # First, use enhanced pattern matching to catch problematic nested structures
        if self._should_ignore_enhanced_patterns(file_path):
            return True
        
        # Then, apply original logic for backwards compatibility
        path_parts = Path(file_path).parts
        
        # Check if any directory in the path should be ignored (original logic)
        for part in path_parts[:-1]:  # Exclude the filename
            if self.should_ignore_directory(part):
                return True
        
        # Check if the filename should be ignored (original logic)
        if len(path_parts) > 0:
            return self.should_ignore_file(path_parts[-1])
        
        return False

class TextChunker:
    """Intelligent text chunking for code and documentation"""
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.encoding = tiktoken.encoding_for_model("gpt-4")
    
    def chunk_code(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Create semantic chunks from code files"""
        chunks = []
        lines = content.split('\n')
        
        # Try to chunk by functions/classes for code files
        if file_path.endswith(('.py', '.js', '.ts')):
            chunks = self._chunk_by_structure(lines, file_path)
        else:
            chunks = self._chunk_by_size(content, file_path)
        
        return chunks
    
    def _chunk_by_structure(self, lines: List[str], file_path: str) -> List[Dict[str, Any]]:
        """Chunk code by structural boundaries"""
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for i, line in enumerate(lines):
            tokens = len(self.encoding.encode(line))
            
            # Detect structural boundaries
            is_boundary = (
                line.strip().startswith(('def ', 'class ', 'function ', 'const ', 'export ')) or
                (current_tokens + tokens > self.chunk_size and len(current_chunk) > 10)
            )
            
            if is_boundary and current_chunk:
                # Save current chunk
                chunk_text = '\n'.join(current_chunk)
                chunks.append({
                    'content': chunk_text,
                    'metadata': {
                        'file': file_path,
                        'start_line': i - len(current_chunk),
                        'end_line': i - 1,
                        'type': 'code',
                        'tokens': current_tokens
                    }
                })
                
                # Start new chunk with overlap
                overlap_lines = max(0, len(current_chunk) - 5)
                current_chunk = current_chunk[-5:] if overlap_lines > 0 else []
                current_tokens = sum(len(self.encoding.encode(l)) for l in current_chunk)
            
            current_chunk.append(line)
            current_tokens += tokens
        
        # Don't forget the last chunk
        if current_chunk:
            chunk_text = '\n'.join(current_chunk)
            chunks.append({
                'content': chunk_text,
                'metadata': {
                    'file': file_path,
                    'start_line': len(lines) - len(current_chunk),
                    'end_line': len(lines) - 1,
                    'type': 'code',
                    'tokens': current_tokens
                }
            })
        
        return chunks
    
    def _chunk_by_size(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Simple size-based chunking for non-code files"""
        chunks = []
        tokens = self.encoding.encode(content)
        
        for i in range(0, len(tokens), self.chunk_size - self.overlap):
            chunk_tokens = tokens[i:i + self.chunk_size]
            chunk_text = self.encoding.decode(chunk_tokens)
            
            chunks.append({
                'content': chunk_text,
                'metadata': {
                    'file': file_path,
                    'chunk_index': i // (self.chunk_size - self.overlap),
                    'type': 'document',
                    'tokens': len(chunk_tokens)
                }
            })
        
        return chunks

class ProjectKnowledgeAgent:
    """Enhanced RAG agent with multi-project support"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.security_filter = SecurityFilter(config['sensitive_patterns'])
        self.path_filter = PathFilter(config['ignore_directories'], config['ignore_files'])
        self.chunker = TextChunker(config['chunk_size'], config['chunk_overlap'])
        
        # Initialize ProjectManager
        self.project_manager = ProjectManager(config.get('projects_config_dir'))
        self._setup_legacy_project()
        
        # Initialize Google GenAI
        try:
            self.embedder = genai.Client(
                http_options=HttpOptions(api_version="v1beta"),
                api_key=os.environ.get("GEMINI_API_KEY")
            )
            # Initialize content generation client for LLM responses
            self.client = genai.Client(
                api_key=os.environ.get("GEMINI_API_KEY")
            )
            # Create embedding function for ChromaDB
            self.embedding_function = GoogleGenAIEmbeddingFunction(
                api_key=os.getenv('GEMINI_API_KEY'),
                model=config['embedding_model']
            )
            logger.info("Google GenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize GenAI client: {e}")
            raise
        
        # Initialize ChromaDB
        self.db = chromadb.PersistentClient(
            path=config['db_path'],
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        # self.db = chromadb.HttpClient(host='localhost', port=8000)
        
        # Collections will be created per project
        self.collections = {}
        self._init_project_collections()
        
        # Track processed files per project
        self.processed_files = {}
        self._load_all_processed_files()
        
        # Initialize v3.0 Sacred Layer components
        self.git_integration = GitIntegratedRAGAgent(self, self.project_manager)
        for project in self.project_manager.get_active_projects():
            try:
                self.git_integration.init_git_tracking(project.project_id)
                logger.info(f"Git tracking initialized for {project.name}")
            except Exception as e:
                logger.warning(f"Could not initialize git tracking for {project.name}: {e}")
        self.sacred_integration = SacredIntegratedRAGAgent(self)
        
        # Verify critical methods are accessible (debugging aid)
        logger.info(f"ProjectKnowledgeAgent initialization complete. Methods: {[m for m in dir(self) if not m.startswith('_')]}")
        if hasattr(self, 'add_decision'):
            logger.info("✅ add_decision method is accessible")
        else:
            logger.error("❌ add_decision method NOT found after initialization!")
    
    def _setup_legacy_project(self):
        """Import legacy watch directories as a project if no projects exist"""
        if not self.project_manager.projects and self.config.get('legacy_watch_dirs'):
            # Check if legacy dirs exist
            legacy_dirs = [d for d in self.config['legacy_watch_dirs'] if os.path.exists(d)]
            if legacy_dirs:
                logger.info("Importing legacy YouTube Analyzer project...")
                project = self.project_manager.create_project(
                    name="YouTube Analyzer (Legacy Import)",
                    root_path=os.path.dirname(legacy_dirs[0]),
                    watch_dirs=legacy_dirs,
                    description="Automatically imported from v1.0 configuration"
                )
                logger.info(f"Created legacy project: {project.name}")
    
    def _init_project_collections(self):
        """Initialize ChromaDB collections for all active projects"""
        for project in self.project_manager.get_active_projects():
            collection_name = f"project_{project.project_id}"
            try:
                self.collections[project.project_id] = self.db.get_collection(
                    name=collection_name,
                    embedding_function=self.embedding_function
                )
                logger.info(f"Using existing collection for project: {project.name}")
            except:
                self.collections[project.project_id] = self.db.create_collection(
                    name=collection_name,
                    embedding_function=self.embedding_function,
                    metadata={"hnsw:space": "cosine", "project_name": project.name}
                )
                logger.info(f"Created new collection for project: {project.name}")
    
    def _load_all_processed_files(self):
        """Load processed files for all projects"""
        for project in self.project_manager.projects.values():
            hash_file = Path(self.config['db_path']) / f"processed_files_{project.project_id}.json"
            if hash_file.exists():
                with open(hash_file, 'r') as f:
                    self.processed_files[project.project_id] = json.load(f)
    
    
    def _save_processed_files(self, project_id: str):
        """Save hash of processed files for a project"""
        if project_id in self.processed_files:
            hash_file = Path(self.config['db_path']) / f"processed_files_{project_id}.json"
            with open(hash_file, 'w') as f:
                json.dump(self.processed_files[project_id], f, indent=2)
    
    def _get_file_hash(self, file_path: str) -> str:
        """Calculate file hash for change detection"""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def _find_project_for_file(self, file_path: str) -> Optional[str]:
        """Find which project a file belongs to based on watch directories"""
        abs_path = os.path.abspath(file_path)
        for project in self.project_manager.get_active_projects():
            for watch_dir in project.watch_dirs:
                if abs_path.startswith(os.path.abspath(watch_dir)):
                    return project.project_id
        return None
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embeddings using Google's gemini-embedding-001"""
        try:
            response = await asyncio.to_thread(
                self.embedder.models.embed_content,
                model=self.config['embedding_model'],
                contents=text
            )
            return response.embeddings[0].values
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            raise
    
    async def ingest_file(self, file_path: str, project_id: str = None) -> int:
        """Process and embed a single file for a specific project"""
        try:
            # Determine which project this file belongs to
            if project_id is None:
                project_id = self._find_project_for_file(file_path)
                if not project_id:
                    logger.warning(f"No project found for file: {file_path}")
                    return 0
            
            # Initialize project structures if needed
            if project_id not in self.processed_files:
                self.processed_files[project_id] = {}
            if project_id not in self.collections:
                self._init_project_collections()
            
            # Check if file needs processing
            current_hash = self._get_file_hash(file_path)
            if (file_path in self.processed_files[project_id] and 
                self.processed_files[project_id][file_path] == current_hash):
                logger.debug(f"Skipping unchanged file: {file_path}")
                return 0
            
            # Read and clean content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            cleaned_content = self.security_filter.clean(content)
            
            # Chunk the content
            chunks = self.chunker.chunk_code(cleaned_content, file_path)
            
            # Store each chunk (ChromaDB will handle embeddings via embedding_function)
            chunk_count = 0
            for chunk in chunks:
                # Generate unique ID
                chunk_id = f"{file_path}_{chunk['metadata'].get('chunk_index', chunk['metadata'].get('start_line', 0))}"
                
                # Store in project-specific collection
                self.collections[project_id].upsert(
                    ids=[chunk_id],
                    documents=[chunk['content']],
                    metadatas=[{
                        **chunk['metadata'],
                        'project_id': project_id,
                        'ingested_at': datetime.now().isoformat()
                    }]
                )
                chunk_count += 1
            
            # Update processed files
            self.processed_files[project_id][file_path] = current_hash
            self._save_processed_files(project_id)
            
            logger.info(f"Ingested {chunk_count} chunks from {file_path} into project {project_id}")
            return chunk_count
            
        except Exception as e:
            logger.error(f"Error ingesting {file_path}: {e}")
            return 0
    
    async def ingest_directory(self, directory: str, project_id: str = None, progress_callback: callable = None) -> int:
        """Recursively ingest all files in a directory"""
        total_chunks = 0
        
        # First, count the total number of files to process for progress tracking
        total_files = 0
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if not self.path_filter.should_ignore_directory(d)]
            for file in files:
                if any(file.endswith(ext) for ext in self.config['default_file_extensions']):
                    file_path = os.path.join(root, file)
                    if not self.path_filter.should_ignore_path(file_path):
                        total_files += 1

        processed_files = 0
        for root, dirs, files in os.walk(directory):
            # Filter out directories that should be ignored
            dirs[:] = [d for d in dirs if not self.path_filter.should_ignore_directory(d)]
            
            for file in files:
                if any(file.endswith(ext) for ext in self.config['default_file_extensions']):
                    file_path = os.path.join(root, file)
                    
                    # Check if the full path should be ignored (comprehensive check)
                    if self.path_filter.should_ignore_path(file_path):
                        continue
                    
                    chunks = await self.ingest_file(file_path, project_id)
                    total_chunks += chunks
                    processed_files += 1

                    if progress_callback and total_files > 0:
                        progress = int((processed_files / total_files) * 100)
                        await progress_callback(progress)

        return total_chunks
    
    async def query(self, question: str, k: int = None, project_id: str = None) -> Dict[str, Any]:
        """Query the knowledge base with STRICT project filtering"""
        if k is None:
            k = self.config['max_results']
        
        # CRITICAL: Require project_id - fail closed, not open
        if project_id is None:
            # FAIL CLOSED: No project = no results
            logger.warning(f"Query attempted without project_id: {question[:50]}...")
            return {
                'query': question,
                'error': 'No project context specified',
                'results': [],
                'timestamp': datetime.now().isoformat()
            }
        
        # Validate project exists and is accessible
        if project_id not in self.collections:
            logger.error(f"Query attempted for non-existent project: {project_id}")
            return {
                'query': question,
                'error': f'Project {project_id} not found',
                'results': [],
                'timestamp': datetime.now().isoformat()
            }
        
        try:
            # Search ONLY the specified project - no cross-project contamination
            results = self.collections[project_id].query(
                query_texts=[question],
                n_results=k
            )
            
            # Format results with project context
            formatted_results = []
            if results and 'ids' in results and results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    formatted_results.append({
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i] if 'distances' in results else None,
                        'project_id': project_id  # Always include source project
                    })
            
            return {
                'query': question,
                'results': formatted_results,
                'project_id': project_id,  # Always include project context
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Query error in project {project_id}: {e}")
            return {
                'query': question,
                'error': str(e),
                'results': [],
                'project_id': project_id
            }
    async def query_with_llm(self, question: str, k: int = None, project_id: str = None) -> Dict[str, Any]:
        """Enhanced query with natural language response generation"""
        # CRITICAL: Enforce project_id requirement
        if project_id is None:
            return {
                'question': question,
                'answer': "No project context specified. Please select a project first.",
                'sources': [],
                'error': 'No project context'
            }
        
        # Get raw RAG results using the fixed query method
        raw_results = await self.query(question, k, project_id)

        if raw_results.get('error'):
            return {
                'question': question,
                'answer': f"Error: {raw_results['error']}",
                'sources': [],
                'project_id': project_id
            }

        if not raw_results['results']:
            return {
                'question': question,
                'answer': f"""I couldn't find any indexed content for project {project_id}.

This usually means:
• The project hasn't been indexed yet, or
• The project has no compatible files, or  
• The indexing process failed

To fix this, please index your project with content:
./scripts/rag_cli_v2.sh projects ingest {project_id} /path/to/your/project

After indexing, try your question again.""",
                'sources': [],
                'project_id': project_id,
                'suggestion': 'index_project'
            }

        # Prepare context for LLM
        context_chunks = []
        sources = []

        for result in raw_results['results'][:5]:  # Use top 5 results
            context_chunks.append(result['content'])
            sources.append(result['metadata'].get('file', 'Unknown'))

        context = "\n\n---\n\n".join(context_chunks)

        # Generate response using LLM
        try:
            prompt = f"""You are an expert software architect AI, an assistant for the 'ContextKeeper v3' project. Your task is to answer questions based *exclusively* on the provided context from the project's codebase and documentation. Do not use any external knowledge.

    **Context from Project '{project_id}':**
    ---
    {context}
    ---

    **User's Question:** "{question}"

    **Instructions:**
    1.  **Synthesize a Clear Answer:** Provide a direct, conversational, and well-structured response based *only* on the context above.
    2.  **Ground Your Answer:** If you provide a code snippet, explain what it does in plain English. Every statement must be directly supported by the provided text.
    3.  **Acknowledge Limits:** If the context does not contain the answer, you MUST state: "The provided context does not contain enough information to answer this question." Do not attempt to guess.
    4.  **Format Your Output:** Structure your response in Markdown for clarity. Use bullet points and bold text to highlight key information.

    **Expert Answer:**
    """
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            return {
                'question': question,
                'answer': response.text,
                'sources': list(set(sources)),  # Unique sources
                'project_id': project_id,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            return {
                'question': question,
                'answer': f"Error generating response: {str(e)}",
                'sources': sources,
                'project_id': project_id,
                'error': str(e)
            }
    
    def add_decision(self, decision: str, reasoning: str = "", project_id: str = None, tags: List[str] = None) -> Optional[Any]:
        """Add a decision to a project with embedding/search functionality"""
        try:
            logger.info(f"add_decision called with: decision='{decision[:50]}...', project_id={project_id}")
            
            # Use focused project if no project_id provided
            if project_id is None:
                project_id = self.project_manager.focused_project_id
                if not project_id:
                    logger.error("No project specified and no focused project available")
                    return None
                logger.info(f"Using focused project: {project_id}")
            
            # Validate project exists
            if project_id not in self.project_manager.projects:
                logger.error(f"Project {project_id} not found. Available projects: {list(self.project_manager.projects.keys())}")
                return None
            
            # Use project manager to create and persist the decision
            logger.info(f"Creating decision via project manager for project {project_id}")
            decision_obj = self.project_manager.add_decision(
                project_id=project_id,
                decision=decision,
                reasoning=reasoning,
                tags=tags or []
            )
            
            if decision_obj and project_id in self.collections:
                # Create content for embedding
                content = f"PROJECT DECISION: {decision}"
                if reasoning:
                    content += f"\nREASONING: {reasoning}"
                if tags:
                    content += f"\nTAGS: {', '.join(tags)}"
                content += f"\nDATE: {decision_obj.timestamp}"
                
                # Store decision in ChromaDB for embedding/search functionality
                logger.info(f"Adding decision to ChromaDB collection for project {project_id}")
                self.collections[project_id].add(
                    ids=[decision_obj.id],
                    documents=[content],
                    metadatas=[{
                        'type': 'decision',
                        'project_id': project_id,
                        'tags': ', '.join(tags) if tags else '',
                        'date': decision_obj.timestamp
                    }]
                )
                
                logger.info(f"Successfully added decision to project {project_id}: {decision[:50]}...")
            elif not decision_obj:
                logger.error("Project manager failed to create decision object")
                return None
            elif project_id not in self.collections:
                logger.warning(f"ChromaDB collection not found for project {project_id}. Decision saved to project manager only.")
            
            return decision_obj
            
        except Exception as e:
            logger.error(f"Error adding decision: {e}", exc_info=True)
            return None
    
    def add_objective(self, title: str, description: str = "", priority: str = "medium", project_id: str = None) -> Optional[Any]:
        """Add an objective to a project with embedding/search functionality"""
        try:
            # Use focused project if no project_id provided
            if project_id is None:
                project_id = self.project_manager.focused_project_id
                if not project_id:
                    logger.error("No project specified and no focused project available")
                    return None
            
            # Validate project exists
            if project_id not in self.project_manager.projects:
                logger.error(f"Project {project_id} not found")
                return None
            
            # Use project manager to create and persist the objective
            objective_obj = self.project_manager.add_objective(
                project_id=project_id,
                title=title,
                description=description,
                priority=priority
            )
            
            if objective_obj and project_id in self.collections:
                # Create content for embedding
                content = f"PROJECT OBJECTIVE: {title}"
                if description:
                    content += f"\nDESCRIPTION: {description}"
                content += f"\nPRIORITY: {priority}"
                content += f"\nDATE: {objective_obj.created_at}"
                
                # Store objective in ChromaDB for embedding/search functionality
                self.collections[project_id].add(
                    ids=[objective_obj.id],
                    documents=[content],
                    metadatas=[{
                        'type': 'objective',
                        'project_id': project_id,
                        'priority': priority,
                        'date': objective_obj.created_at
                    }]
                )
                
                logger.info(f"Added objective to project {project_id}: {title}")
            
            return objective_obj
            
        except Exception as e:
            logger.error(f"Error adding objective: {e}")
            return None

class CodebaseWatcher(FileSystemEventHandler):
    """Watches for file changes and updates knowledge base"""
    
    def __init__(self, agent: ProjectKnowledgeAgent):
        self.agent = agent
        self.update_queue = asyncio.Queue()
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        # Check if the file should be ignored
        if self.agent.path_filter.should_ignore_path(event.src_path):
            return
        
        if any(event.src_path.endswith(ext) for ext in self.agent.config['default_file_extensions']):
            logger.info(f"File modified: {event.src_path}")
            asyncio.run(self.agent.ingest_file(event.src_path))
    
    def on_created(self, event):
        self.on_modified(event)

class RAGServer:
    """Flask API server for RAG agent"""
    
    def __init__(self, agent: ProjectKnowledgeAgent, port: int = 5556):
        self.agent = agent
        self.app = Flask(__name__)
        
        # Apply Flask security configuration
        self.app.config.update(SecurityConfig.get_flask_config())
        
        # Configure CORS with proper origins - Reference: https://owasp.org/www-community/attacks/CORS_OriginHeaderScrutiny
        CORS(self.app, origins=SecurityConfig.CORS_ORIGINS, supports_credentials=True)
        
        # Initialise rate limiter - Reference: https://owasp.org/www-community/controls/Rate_Limiting
        self.limiter = Limiter(
            app=self.app,
            key_func=get_remote_address,
            default_limits=["200 per day", "50 per hour"],
            storage_uri=os.environ.get('REDIS_URL', 'memory://')
        )
        
        # Apply security headers - Reference: https://owasp.org/www-project-secure-headers/
        if SecurityConfig.ENVIRONMENT == 'production':
            Talisman(
                self.app,
                force_https=True,
                strict_transport_security=True,
                content_security_policy={
                    'default-src': "'self'",
                    'script-src': "'self' 'unsafe-inline' cdnjs.cloudflare.com cdn.socket.io",
                    'style-src': "'self' 'unsafe-inline'",
                    'img-src': "'self' data:",
                    'connect-src': "'self' ws: wss:"
                }
            )
        else:
            # Development mode - less strict
            @self.app.after_request
            def set_security_headers(response):
                for header, value in SecurityConfig.SECURITY_HEADERS.items():
                    response.headers[header] = value
                return response
        
        self.port = port
        self.tasks = {}
        # Fix CORS for Socket.IO - no wildcard origins
        self.socketio = SocketIO(
            self.app, 
            cors_allowed_origins=SecurityConfig.CORS_ORIGINS
        )
        self.executor = concurrent.futures.ThreadPoolExecutor()
        self._setup_routes()
        add_sacred_drift_endpoint(
            self.app,
            self.agent,
            self.agent.project_manager,
            self.agent.sacred_integration.sacred_manager
        )

    def _run_async(self, coro):
        """Execute coroutine using shared thread executor"""
        return self.executor.submit(asyncio.run, coro).result()
    
    def _setup_routes(self):
        @self.app.route('/health', methods=['GET'])
        def health():
            return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})
        
        @self.app.route('/query', methods=['POST'])
        @self.limiter.limit("10 per minute")  # Rate limiting - OWASP A04:2021
        def query():
            try:
                # Get client IP for logging
                client_ip = request.remote_addr
                
                # Validate and sanitise input - OWASP A03:2021 - Injection prevention
                data = SecurityValidator.validate_json_input(
                    request.json,
                    required_fields=['question']
                )
                
                question = SecurityValidator.sanitise_html_input(data.get('question', ''))
                k = min(int(data.get('k', 5)), 20)  # Limit max results
                
                # Validate project_id if provided
                project_id = data.get('project_id')
                if project_id:
                    project_id = SecurityValidator.validate_project_id(project_id)
                
                # Log the query
                security_logger.log_access(
                    user='anonymous',  # Add user when auth implemented
                    resource='query',
                    action='search',
                    ip_address=client_ip
                )
                
                # Execute query
                results = self._run_async(self.agent.query(question, k, project_id))
                
                return jsonify(results)
                
            except ValueError as e:
                security_logger.log_validation_failure('query', str(e), request.remote_addr)
                return jsonify({'error': 'Invalid input'}), 400
            except Exception as e:
                logger.error(f"Query error: {e}", exc_info=True)
                return jsonify({'error': 'Internal server error'}), 500
        
        @self.app.route('/ingest', methods=['POST'])
        @self.limiter.limit("5 per minute")  # Rate limiting for resource-intensive operation
        def ingest():
            try:
                # Validate and sanitise input - OWASP A03:2021
                data = SecurityValidator.validate_json_input(
                    request.json,
                    required_fields=['path', 'project_id']
                )
                
                # Validate file path to prevent path traversal
                path = SecurityValidator.validate_file_path(data.get('path', ''))
                
                if not os.path.exists(path):
                    return jsonify({'error': 'Path does not exist'}), 404
                
                # Validate project_id
                project_id = SecurityValidator.validate_project_id(data.get('project_id'))
                
                # Log the ingestion attempt
                security_logger.log_access(
                    user='anonymous',
                    resource='ingest',
                    action='add_documents',
                    ip_address=request.remote_addr
                )
                
                # Validate project exists
                if project_id not in self.agent.collections:
                    # Try to initialize collections in case project was just created
                    self.agent._init_project_collections()
                    if project_id not in self.agent.collections:
                        return jsonify({'error': f'Project {project_id} not found or not accessible'}), 404
                
                if os.path.isfile(path):
                    # Check if single file should be ignored
                    if self.agent.path_filter.should_ignore_path(path):
                        return jsonify({'error': 'File path is ignored by configuration', 'chunks_ingested': 0})
                    chunks = self._run_async(self.agent.ingest_file(path, project_id))
                else:
                    chunks = self._run_async(self.agent.ingest_directory(path, project_id))
                
                return jsonify({'chunks_ingested': chunks})
                
            except ValueError as e:
                security_logger.log_validation_failure('ingest', str(e), request.remote_addr)
                return jsonify({'error': 'Invalid input'}), 400
            except Exception as e:
                logger.error(f"Ingest error: {e}", exc_info=True)
                return jsonify({'error': 'Internal server error'}), 500
        
        @self.app.route('/decision', methods=['POST'])
        def add_decision():
            try:
                logger.info("Flask /decision endpoint called")
                
                # Verify agent has add_decision method
                if not hasattr(self.agent, 'add_decision'):
                    logger.error("Agent does not have add_decision method!")
                    logger.error(f"Agent type: {type(self.agent)}")
                    logger.error(f"Agent attributes: {dir(self.agent)}")
                    return jsonify({'error': 'Internal server error: add_decision method not found'}), 500
                
                data = request.json
                if not data:
                    return jsonify({'error': 'No JSON data provided'}), 400
                
                decision = data.get('decision', '')
                reasoning = data.get('reasoning', data.get('context', ''))  # Support old 'context' param
                project_id = data.get('project_id')
                tags = data.get('tags', [])
                
                logger.info(f"Request data: decision='{decision[:50]}...', project_id={project_id}")
                
                if not decision:
                    return jsonify({'error': 'Decision required'}), 400
                
                # Call the method with proper error handling  
                decision_obj = self.agent.add_decision(decision, reasoning, project_id, tags)
                
                if decision_obj:
                    logger.info(f"Successfully created decision: {decision_obj.id}")
                    return jsonify({
                        'status': 'Decision added',
                        'decision_id': decision_obj.id,
                        'project_id': project_id or self.agent.project_manager.focused_project_id
                    })
                else:
                    logger.error("add_decision returned None - check method implementation")
                    return jsonify({'error': 'Failed to add decision - method returned None'}), 400
                    
            except AttributeError as e:
                logger.error(f"AttributeError in /decision endpoint: {e}", exc_info=True)
                return jsonify({'error': f'Method access error: {str(e)}'}), 500
            except Exception as e:
                logger.error(f"Unexpected error in /decision endpoint: {e}", exc_info=True)
                return jsonify({'error': f'Internal server error: {str(e)}'}), 500
        
        # Event tracking endpoints
        @self.app.route('/events', methods=['POST'])
        def track_event():
            """Track a development event"""
            try:
                data = request.json
                
                # Import event models
                from project_manager import DevelopmentEvent, EventType, EventSeverity
                
                # Create event from request data
                event = DevelopmentEvent(
                    type=EventType(data.get('type', 'code_change')),
                    severity=EventSeverity(data.get('severity', 'info')),
                    title=data.get('title', ''),
                    description=data.get('description', ''),
                    project_id=data.get('project_id', ''),
                    metadata=data.get('metadata', {}),
                    tags=data.get('tags', [])
                )
                
                # Add event to project manager
                saved_event = self.agent.project_manager.add_event(event)
                
                if saved_event:
                    # Also add to ChromaDB for searchability
                    project_id = saved_event.project_id
                    if project_id in self.agent.collections:
                        content = f"EVENT: {saved_event.title}\n"
                        content += f"TYPE: {saved_event.type.value}\n"
                        content += f"SEVERITY: {saved_event.severity.value}\n"
                        content += f"DESCRIPTION: {saved_event.description}\n"
                        content += f"TIMESTAMP: {saved_event.timestamp.isoformat()}\n"
                        
                        # Handle metadata safely
                        tags_str = ', '.join(saved_event.tags) if saved_event.tags else ''
                        
                        self.agent.collections[project_id].add(
                            ids=[saved_event.id],
                            documents=[content],
                            metadatas=[{
                                'type': 'event',
                                'event_type': saved_event.type.value,
                                'severity': saved_event.severity.value,
                                'project_id': project_id,
                                'tags': tags_str,
                                'date': saved_event.timestamp.isoformat()
                            }]
                        )
                    
                    return jsonify({
                        'event_id': saved_event.id,
                        'project_id': saved_event.project_id,
                        'status': 'Event tracked'
                    }), 200
                else:
                    return jsonify({'error': 'Failed to track event'}), 400
                    
            except Exception as e:
                logger.error(f"Error tracking event: {e}", exc_info=True)
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/events', methods=['GET'])
        def get_events():
            """Get recent events with optional filtering"""
            try:
                project_id = request.args.get('project_id')
                limit = int(request.args.get('limit', 100))
                event_type = request.args.get('type')
                severity = request.args.get('severity')
                
                # Import event models
                from project_manager import EventType, EventSeverity
                
                # Parse filters
                event_types = [EventType(event_type)] if event_type else None
                min_severity = EventSeverity(severity) if severity else None
                
                # Get events from project manager
                events = self.agent.project_manager.get_recent_events(
                    project_id=project_id,
                    limit=limit,
                    event_types=event_types,
                    severity=min_severity
                )
                
                return jsonify({
                    'events': [e.to_dict() for e in events],
                    'count': len(events)
                }), 200
                
            except Exception as e:
                logger.error(f"Error getting events: {e}", exc_info=True)
                return jsonify({'error': str(e)}), 500
        
        # Project management endpoints
        @self.app.route('/projects', methods=['GET'])
        def list_projects():
            return jsonify(self.agent.project_manager.get_project_summary())
        
        @self.app.route('/projects', methods=['POST'])
        def create_project():
            data = request.json
            name = data.get('name', '')
            root_path = data.get('root_path', '')
            watch_dirs = data.get('watch_dirs')
            description = data.get('description', '')
            
            if not name or not root_path:
                return jsonify({'error': 'Name and root_path required'}), 400
            
            project = self.agent.project_manager.create_project(
                name, root_path, watch_dirs, description
            )
            return jsonify({
                'status': 'Project created',
                'project_id': project.project_id,
                'name': project.name
            })

        @self.app.route('/projects/create-and-index', methods=['POST'])
        def create_and_index():
            data = request.json
            name = data.get('name')
            root_path = data.get('root_path')

            if not name or not root_path:
                return jsonify({'error': 'name and root_path are required'}), 400

            project = self.agent.project_manager.create_project(name, root_path)
            task_id = f"task_{uuid.uuid4().hex[:8]}"

            async def background_ingest():
                self.tasks[task_id] = {'status': 'indexing', 'progress': 0, 'project_id': project.project_id}

                async def progress_callback(progress):
                    self.tasks[task_id]['progress'] = progress
                    self.socketio.emit('indexing_progress', {'project_id': project.project_id, 'progress': progress})

                try:
                    await self.agent.ingest_directory(project.root_path, project.project_id, progress_callback)
                    self.tasks[task_id]['status'] = 'complete'
                    self.tasks[task_id]['progress'] = 100
                    self.socketio.emit('indexing_complete', {'project_id': project.project_id})
                except Exception as e:
                    logger.error(f"Background ingestion failed for task {task_id}: {e}")
                    self.tasks[task_id]['status'] = 'failed'
                    self.tasks[task_id]['error'] = str(e)
                    self.socketio.emit('indexing_failed', {'project_id': project.project_id, 'error': str(e)})


            # Run the async background task in the event loop of the RAGServer
            self._run_async(background_ingest())

            return jsonify({'task_id': task_id, 'project_id': project.project_id}), 202

        @self.app.route('/tasks/<task_id>', methods=['GET'])
        def get_task_status(task_id):
            task = self.tasks.get(task_id)
            if not task:
                return jsonify({'error': 'Task not found'}), 404
            return jsonify(task)
        
        @self.app.route('/projects/<project_id>/focus', methods=['POST'])
        def focus_project(project_id):
            if self.agent.project_manager.set_focus(project_id):
                self.socketio.emit('focus_changed', {'project_id': project_id})
                return jsonify({'status': 'Project focused', 'project_id': project_id})
            return jsonify({'error': 'Project not found'}), 404
        
        @self.app.route('/projects/validate/<project_id>', methods=['GET'])
        def validate_project_access(project_id):
            """Validate if a project exists and is accessible"""
            if project_id not in self.agent.collections:
                return jsonify({
                    'valid': False,
                    'error': f'Project {project_id} not found'
                }), 404
            
            project = self.agent.project_manager.projects.get(project_id)
            if not project:
                return jsonify({
                    'valid': False,
                    'error': f'Project {project_id} not in project manager'
                }), 404
            
            return jsonify({
                'valid': True,
                'project_id': project_id,
                'name': project.name,
                'status': project.status.value,
                'is_focused': project_id == self.agent.project_manager.focused_project_id
            })
        
        @self.app.route('/projects/<project_id>/status', methods=['PUT'])
        def update_project_status(project_id):
            data = request.json
            status = data.get('status', '')
            
            if status not in ['active', 'paused', 'archived']:
                return jsonify({'error': 'Invalid status'}), 400
            
            if self.agent.project_manager.update_status(project_id, ProjectStatus(status)):
                return jsonify({'status': 'Project status updated', 'new_status': status})
            return jsonify({'error': 'Project not found'}), 404
        
        @self.app.route('/projects/<project_id>/objectives', methods=['POST'])
        def add_objective(project_id):
            data = request.json
            title = data.get('title', '')
            description = data.get('description', '')
            priority = data.get('priority', 'medium')
            
            if not title:
                return jsonify({'error': 'Title required'}), 400
            
            objective = self.agent.project_manager.add_objective(
                project_id, title, description, priority
            )
            if objective:
                return jsonify({
                    'status': 'Objective added',
                    'objective_id': objective.id,
                    'title': objective.title
                })
            return jsonify({'error': 'Project not found'}), 404
        
        @self.app.route('/projects/<project_id>/objectives/<objective_id>/complete', 
                       methods=['POST'])
        def complete_objective(project_id, objective_id):
            if self.agent.project_manager.complete_objective(project_id, objective_id):
                return jsonify({'status': 'Objective completed'})
            return jsonify({'error': 'Project or objective not found'}), 404
        
        @self.app.route('/projects/<project_id>/context', methods=['GET'])
        def export_context(project_id):
            context = self.agent.project_manager.export_context(project_id)
            if context:
                return jsonify(context)
            return jsonify({'error': 'Project not found'}), 404

        @self.app.route('/search', methods=['GET'])
        def search():
            query = request.args.get('q', '').lower()
            if not query:
                return jsonify({'projects': [], 'plans': [], 'decisions': []})

            # Search projects
            projects = [
                p.to_dict() for p in self.agent.project_manager.projects.values()
                if query in p.name.lower()
            ]

            # Search plans (this is a simplified search)
            plans = [
                plan for plan in self.agent.sacred_integration.sacred_manager.plans_registry.values()
                if query in plan['title'].lower()
            ]

            # Search decisions (this is a simplified search)
            decisions = []
            for project in self.agent.project_manager.projects.values():
                for decision in project.decisions:
                    if query in decision.decision.lower():
                        decisions.append(decision.to_dict())

            return jsonify({
                'projects': projects[:5],
                'plans': plans[:5],
                'decisions': decisions[:5]
            })
        
        # Sacred Layer v3.0 endpoints
        @self.app.route('/sacred/plans', methods=['POST'])
        def create_sacred_plan():
            data = request.json
            result = self._run_async(self.agent.sacred_integration.create_sacred_plan(
                data['project_id'],
                data['title'],
                data.get('file_path') or data.get('content')
            ))
            return jsonify(result)

        @self.app.route('/sacred/plans', methods=['GET'])
        def list_sacred_plans():
            """List sacred plans with optional filtering"""
            try:
                # Get query parameters
                project_id = request.args.get('project_id')
                status = request.args.get('status')
                
                # Get the sacred manager
                sacred_manager = self.agent.sacred_integration.sacred_manager
                
                # List plans with optional filters
                plans = sacred_manager.list_plans(
                    project_id=project_id,
                    status=status
                )
                
                return jsonify(plans)
            except Exception as e:
                logger.error(f"Error listing sacred plans: {str(e)}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/sacred/plans/<plan_id>', methods=['GET'])
        def get_sacred_plan(plan_id):
            """Retrieve full sacred plan content"""
            try:
                sacred_manager = self.agent.sacred_integration.sacred_manager

                if plan_id not in sacred_manager.plans_registry:
                    return jsonify({'error': 'Plan not found'}), 404

                plan = sacred_manager.plans_registry[plan_id]
                return jsonify({
                    'plan_id': plan.plan_id,
                    'project_id': plan.project_id,
                    'title': plan.title,
                    'content': plan.content,
                    'status': plan.status.value,
                    'created_at': plan.created_at,
                    'approved_at': plan.approved_at,
                    'approved_by': plan.approved_by
                })
            except Exception as e:
                logger.error(f"Error getting sacred plan: {str(e)}")
                return jsonify({'error': str(e)}), 500

        @self.app.route('/sacred/plans/<plan_id>/approve', methods=['POST'])
        def approve_sacred_plan(plan_id):
            data = request.json
            result = self._run_async(self.agent.sacred_integration.approve_sacred_plan(
                plan_id,
                data['approver'],
                data['verification_code'],
                data['secondary_verification']
            ))
            return jsonify(result)

        @self.app.route('/sacred/query', methods=['POST'])
        def query_sacred_plans():
            try:
                data = request.json
                
                # Validate required fields
                if not data or 'query' not in data:
                    return jsonify({'error': 'Query is required'}), 400
                
                # Project ID is optional - will use focused project if not provided
                project_id = data.get('project_id')
                query = data['query']
                
                # If no project_id provided, use the focused project
                if not project_id:
                    if hasattr(self.agent, 'project_manager') and hasattr(self.agent.project_manager, 'focused_project_id') and self.agent.project_manager.focused_project_id:
                        project_id = self.agent.project_manager.focused_project_id
                    else:
                        return jsonify({'error': 'No project_id provided and no focused project set'}), 400
                
                # Execute the query
                result = self._run_async(self.agent.sacred_integration.query_sacred_context(
                    project_id,
                    query
                ))
                return jsonify(result)
            except Exception as e:
                logger.error(f"Error in sacred query endpoint: {str(e)}", exc_info=True)
                return jsonify({'error': f'Failed to query sacred plans: {str(e)}'}), 500
        
        @self.app.route('/sacred/plans/<plan_id>/status', methods=['GET'])
        def get_sacred_plan_status(plan_id):
            """Get status of a specific sacred plan"""
            try:
                sacred_manager = self.agent.sacred_integration.sacred_manager
                
                # Find the plan
                if plan_id not in sacred_manager.plans_registry:
                    return jsonify({'error': 'Plan not found'}), 404
                
                plan = sacred_manager.plans_registry[plan_id]
                return jsonify({
                    'plan_id': plan['plan_id'],
                    'title': plan['title'],
                    'status': plan['status'],
                    'created_at': plan['created_at'],
                    'approved_at': plan.get('approved_at'),
                    'project_id': plan['project_id']
                })
            except Exception as e:
                logger.error(f"Error getting plan status: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/sacred/plans/<plan_id>/lock', methods=['POST'])
        def lock_sacred_plan(plan_id):
            """Lock a sacred plan"""
            try:
                sacred_manager = self.agent.sacred_integration.sacred_manager
                
                # Check if plan exists and is approved
                if plan_id not in sacred_manager.plans_registry:
                    return jsonify({'error': 'Plan not found'}), 404
                
                plan = sacred_manager.plans_registry[plan_id]
                if plan['status'] != 'approved':
                    return jsonify({'error': 'Only approved plans can be locked'}), 400
                
                # Lock the plan
                plan['status'] = 'locked'
                sacred_manager._save_registry()
                
                return jsonify({
                    'success': True,
                    'message': 'Plan locked successfully',
                    'plan_id': plan_id
                })
            except Exception as e:
                logger.error(f"Error locking plan: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/sacred/plans/supersede', methods=['POST'])
        def supersede_sacred_plan():
            """Supersede an old plan with a new one"""
            try:
                data = request.json
                old_plan_id = data.get('old_plan_id')
                new_plan_id = data.get('new_plan_id')
                
                if not old_plan_id or not new_plan_id:
                    return jsonify({'error': 'Both old_plan_id and new_plan_id are required'}), 400
                
                sacred_manager = self.agent.sacred_integration.sacred_manager
                
                # Check both plans exist
                if old_plan_id not in sacred_manager.plans_registry:
                    return jsonify({'error': 'Old plan not found'}), 404
                if new_plan_id not in sacred_manager.plans_registry:
                    return jsonify({'error': 'New plan not found'}), 404
                
                # Update old plan status
                sacred_manager.plans_registry[old_plan_id]['status'] = 'superseded'
                sacred_manager.plans_registry[old_plan_id]['superseded_by'] = new_plan_id
                sacred_manager.plans_registry[old_plan_id]['superseded_at'] = datetime.now().isoformat()
                
                # Save changes
                sacred_manager._save_registry()
                
                return jsonify({
                    'success': True,
                    'message': f'Plan {old_plan_id} superseded by {new_plan_id}',
                    'old_plan_id': old_plan_id,
                    'new_plan_id': new_plan_id
                })
            except Exception as e:
                logger.error(f"Error superseding plan: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/projects/<project_id>/git/activity', methods=['GET'])
        def get_git_activity(project_id):
            hours = int(request.args.get('hours', 24))
            if project_id not in self.agent.git_integration.git_trackers:
                return jsonify({'error': 'Git not initialized for project'}), 404
            
            activity = self.agent.git_integration.git_trackers[project_id].analyze_activity(hours)
            # Note: The dataclasses from git_activity_tracker need to be JSON serializable.
            # A helper function might be needed here if they are not.
            return jsonify(activity.__dict__)

        @self.app.route('/projects/<project_id>/git/sync', methods=['POST'])
        def sync_from_git(project_id):
            try:
                self._run_async(self.agent.git_integration.update_project_from_git(project_id))
                return jsonify({'status': 'synced', 'timestamp': datetime.now().isoformat()})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/query_llm', methods=['POST'])
        def query_with_llm_endpoint():
            """Enhanced query endpoint with natural language responses"""
            data = request.json
            question = data.get('question', '')
            k = data.get('k', 5)
            project_id = data.get('project_id')
            
            if not question:
                return jsonify({'error': 'Question required'}), 400
            
            # Pass project_id to query_with_llm (will handle validation internally)
            result = self._run_async(self.agent.query_with_llm(question, k, project_id))
            
            # Security audit logging
            logger.info(f"LLM Query executed - Project: {project_id or 'FOCUSED'}, Question: {question[:50]}...")
            
            return jsonify(result)

        @self.app.route('/analytics/summary', methods=['GET'])
        def get_analytics_summary():
            # This should be expanded with real data from git/drift analysis
            summary = self.agent.project_manager.get_project_summary()
            # Add more analytics data here in the future
            return jsonify(summary)
        
        @self.app.route('/analytics_dashboard_live.html', methods=['GET'])
        def get_analytics_dashboard():
            """Serve the analytics dashboard HTML file with path traversal protection"""
            try:
                # Validate file path to prevent path traversal - OWASP A01:2021
                # Reference: https://owasp.org/www-community/attacks/Path_Traversal
                dashboard_path = SecurityValidator.validate_file_path(
                    'analytics_dashboard_live.html',
                    base_dir=os.getcwd()
                )
                return send_from_directory(
                    os.path.dirname(dashboard_path),
                    os.path.basename(dashboard_path)
                )
            except ValueError as e:
                logger.error(f"Path validation failed: {e}")
                return jsonify({'error': 'Dashboard not accessible'}), 403
            except FileNotFoundError:
                return jsonify({'error': 'Analytics dashboard not found'}), 404
        
        # Additional endpoints to match MCP server expectations
        
        @self.app.route('/context', methods=['GET'])
        def get_global_context():
            """Get context for the focused project (no project_id required)"""
            focused_project = self.agent.project_manager.get_focused_project()
            if not focused_project:
                return jsonify({'error': 'No focused project. Use /projects/<id>/focus first'}), 400
            
            # Use the existing export_context functionality
            context = self.agent.project_manager.export_context(focused_project.project_id)
            if context:
                return jsonify(context)
            return jsonify({'error': 'Failed to get context'}), 500
        
        @self.app.route('/projects/<project_id>/drift', methods=['GET'])
        def get_drift_analysis(project_id):
            """Get drift analysis for a project"""
            hours = int(request.args.get('hours', 24))
            
            project = self.agent.project_manager.get_project(project_id)
            if not project:
                return jsonify({'error': 'Project not found'}), 404
            
            # Use the SacredDriftDetector to get analysis
            from enhanced_drift_sacred import SacredDriftDetector
            detector = SacredDriftDetector(self.agent, self.agent.sacred_integration.sacred_manager)
            
            try:
                analysis = self._run_async(detector.analyze_project_drift(project, hours))
                
                # Format the response to match MCP expectations
                formatted_analysis = {
                    'analysis': {
                        'alignment_score': analysis.sacred_alignment_score,
                        'status': 'aligned' if analysis.sacred_alignment_score > 0.7 else 'drifting',
                        'objective_progress': {},  # Would need to calculate this
                        'aligned_count': len([a for a in analysis.objective_alignment if a.is_aligned]),
                        'recommendations': analysis.recommendations
                    },
                    'report': analysis.generate_report()
                }
                
                return jsonify(formatted_analysis)
            except Exception as e:
                logger.error(f"Drift analysis error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/objectives', methods=['GET'])
        def list_all_objectives():
            """List objectives across all projects or filtered by project_id"""
            project_id = request.args.get('project_id')
            
            if project_id:
                # Get objectives for specific project
                project = self.agent.project_manager.get_project(project_id)
                if not project:
                    return jsonify({'error': 'Project not found'}), 404
                
                objectives = [{
                    'id': obj.id,
                    'title': obj.title,
                    'description': obj.description,
                    'priority': obj.priority,
                    'status': obj.status,
                    'created_at': obj.created_at,
                    'completed_at': obj.completed_at,
                    'project_id': project_id,
                    'project_name': project.name
                } for obj in project.objectives]
            else:
                # Get objectives for all projects
                objectives = []
                for proj_id, project in self.agent.project_manager.projects.items():
                    for obj in project.objectives:
                        objectives.append({
                            'id': obj.id,
                            'title': obj.title,
                            'description': obj.description,
                            'priority': obj.priority,
                            'status': obj.status,
                            'created_at': obj.created_at,
                            'completed_at': obj.completed_at,
                            'project_id': proj_id,
                            'project_name': project.name
                        })
            
            return jsonify({'objectives': objectives})
        
        @self.app.route('/objectives', methods=['POST'])
        def add_objective_global():
            """Add objective to focused project or specified project"""
            data = request.json
            title = data.get('title', '')
            description = data.get('description', '')
            priority = data.get('priority', 'medium')
            project_id = data.get('project_id')
            
            if not title:
                return jsonify({'error': 'Title required'}), 400
            
            # FAIL CLOSED: Require explicit project_id
            if not project_id:
                return jsonify({'error': 'No project specified. Please provide project_id.'}), 400
            
            objective = self.agent.project_manager.add_objective(
                project_id, title, description, priority
            )
            if objective:
                return jsonify({
                    'status': 'Objective added',
                    'objective_id': objective.id,
                    'project_id': project_id,
                    'title': objective.title
                })
            return jsonify({'error': 'Failed to add objective'}), 400
        
        @self.app.route('/objectives/<objective_id>', methods=['PUT'])
        def update_objective(objective_id):
            """Update an objective"""
            data = request.json
            project_id = data.get('project_id')
            
            # Find which project contains this objective
            target_project_id = None
            target_objective = None
            
            if project_id:
                # Check specific project
                project = self.agent.project_manager.get_project(project_id)
                if project:
                    for obj in project.objectives:
                        if obj.id == objective_id:
                            target_project_id = project_id
                            target_objective = obj
                            break
            else:
                # Search all projects
                for proj_id, project in self.agent.project_manager.projects.items():
                    for obj in project.objectives:
                        if obj.id == objective_id:
                            target_project_id = proj_id
                            target_objective = obj
                            break
                    if target_objective:
                        break
            
            if not target_objective:
                return jsonify({'error': 'Objective not found'}), 404
            
            # Update fields
            if 'title' in data:
                target_objective.title = data['title']
            if 'description' in data:
                target_objective.description = data['description']
            if 'priority' in data:
                target_objective.priority = data['priority']
            
            # Save changes
            self.agent.project_manager._save_projects()
            
            return jsonify({
                'status': 'Objective updated',
                'objective_id': objective_id,
                'project_id': target_project_id
            })
        
        @self.app.route('/objectives/<objective_id>/complete', methods=['POST'])
        def complete_objective_global(objective_id):
            """Complete an objective"""
            data = request.json
            project_id = data.get('project_id')
            
            # Find and complete the objective
            if project_id:
                success = self.agent.project_manager.complete_objective(project_id, objective_id)
                if success:
                    return jsonify({'status': 'Objective completed'})
            else:
                # Search all projects
                for proj_id in self.agent.project_manager.projects:
                    if self.agent.project_manager.complete_objective(proj_id, objective_id):
                        return jsonify({'status': 'Objective completed', 'project_id': proj_id})
            
            return jsonify({'error': 'Objective not found'}), 404
        
        @self.app.route('/code-context', methods=['POST'])
        def get_code_context():
            """Get relevant code examples and patterns for implementing a feature"""
            data = request.json
            feature_description = data.get('feature_description', '')
            project_id = data.get('project_id')
            include_similar = data.get('include_similar', True)
            k = data.get('k', 10 if include_similar else 5)
            
            if not feature_description:
                return jsonify({'error': 'feature_description required'}), 400
            
            # FAIL CLOSED: Require explicit project_id
            if not project_id:
                return jsonify({'error': 'No project specified. Please provide project_id.'}), 400
            
            # Query for relevant code
            query_results = self._run_async(self.agent.query(
                f"code implementation example pattern {feature_description}",
                k=k,
                project_id=project_id
            ))
            
            # Format results as code context
            similar_implementations = []
            patterns = []
            dependencies = []
            
            for result in query_results.get('results', []):
                metadata = result.get('metadata', {})
                if metadata.get('type') == 'code':
                    impl = {
                        'file': metadata.get('file', ''),
                        'code': result.get('content', ''),
                        'similarity': 1.0 - (result.get('distance', 0) if result.get('distance') else 0),
                        'language': metadata.get('file', '').split('.')[-1] if '.' in metadata.get('file', '') else ''
                    }
                    
                    # Try to extract function name from code
                    code_lines = impl['code'].split('\n')
                    for line in code_lines[:10]:  # Check first 10 lines
                        if 'def ' in line or 'function ' in line or 'class ' in line:
                            impl['function_name'] = line.strip()
                            break
                    
                    similar_implementations.append(impl)
            
            # Generate recommendations based on findings
            recommendations = []
            if similar_implementations:
                recommendations.append(f"Found {len(similar_implementations)} similar implementations in the codebase")
                recommendations.append("Consider following the existing patterns for consistency")
                recommendations.append("Review the similar implementations for best practices")
            else:
                recommendations.append("No similar implementations found - this appears to be a new pattern")
                recommendations.append("Consider establishing a new pattern that others can follow")
                recommendations.append("Document your implementation thoroughly for future reference")
            
            response = {
                'similar_implementations': similar_implementations[:5],  # Top 5
                'patterns': patterns,
                'dependencies': dependencies,
                'recommendations': recommendations,
                'architectural_notes': f"When implementing {feature_description}, ensure it aligns with the project's existing architecture and coding standards."
            }
            
            return jsonify(response)
        
        @self.app.route('/daily-briefing', methods=['GET'])
        def get_daily_briefing():
            """Get comprehensive daily briefing across all projects"""
            include_all = request.args.get('include_all', 'false').lower() == 'true'
            
            briefing = {
                'projects': [],
                'priority_objectives': [],
                'recent_decisions': [],
                'recommendations': [],
                'drift_alerts': [],
                'statistics': {
                    'active_projects': 0,
                    'total_objectives': 0,
                    'completed_this_week': 0,
                    'total_decisions': 0,
                    'average_alignment': 0
                }
            }
            
            # Gather project summaries
            alignment_scores = []
            for project_id, project in self.agent.project_manager.projects.items():
                if not include_all and project.status != ProjectStatus.ACTIVE:
                    continue
                
                if project.status == ProjectStatus.ACTIVE:
                    briefing['statistics']['active_projects'] += 1
                
                # Count objectives
                pending_objectives = [obj for obj in project.objectives if obj.status == 'pending']
                briefing['statistics']['total_objectives'] += len(project.objectives)
                
                # Check recent completions (would need to track completion time)
                week_ago = datetime.now().timestamp() - (7 * 24 * 60 * 60)
                completed_this_week = [obj for obj in project.objectives 
                                     if obj.status == 'completed' and obj.completed_at and 
                                     datetime.fromisoformat(obj.completed_at).timestamp() > week_ago]
                briefing['statistics']['completed_this_week'] += len(completed_this_week)
                
                # Get recent decisions
                recent_decisions = project.decisions[-5:] if hasattr(project, 'decisions') else []
                briefing['statistics']['total_decisions'] += len(getattr(project, 'decisions', []))
                
                project_summary = {
                    'name': project.name,
                    'status': project.status,
                    'last_active': project.last_updated,
                    'pending_objectives': len(pending_objectives),
                    'recent_decisions': len(recent_decisions)
                }
                
                # Try to get git status if available
                try:
                    git_tracker = self.agent.git_integration.git_trackers.get(project_id)
                    if git_tracker:
                        # Would need to add a method to get status
                        project_summary['git_status'] = 'Active'
                except:
                    pass
                
                briefing['projects'].append(project_summary)
                
                # Add high priority objectives
                for obj in pending_objectives:
                    if obj.priority == 'high':
                        briefing['priority_objectives'].append({
                            'title': obj.title,
                            'description': obj.description,
                            'priority': obj.priority,
                            'created_at': obj.created_at,
                            'project_name': project.name,
                            'project_id': project_id
                        })
                
                # Add recent decisions
                for decision in recent_decisions:
                    briefing['recent_decisions'].append({
                        'decision': decision.decision,
                        'reasoning': decision.reasoning,
                        'tags': decision.tags,
                        'timestamp': decision.timestamp,
                        'project_name': project.name
                    })
            
            # Sort priority objectives by age
            briefing['priority_objectives'].sort(key=lambda x: x['created_at'])
            
            # Sort recent decisions by timestamp
            briefing['recent_decisions'].sort(key=lambda x: x['timestamp'], reverse=True)
            briefing['recent_decisions'] = briefing['recent_decisions'][:10]  # Top 10
            
            # Generate recommendations
            if len(briefing['priority_objectives']) > 3:
                briefing['recommendations'].append({
                    'priority': 'high',
                    'message': f"You have {len(briefing['priority_objectives'])} high-priority objectives pending"
                })
            
            if briefing['statistics']['active_projects'] > 5:
                briefing['recommendations'].append({
                    'priority': 'medium',
                    'message': "Consider archiving completed projects to maintain focus"
                })
            
            # Calculate average alignment (would need actual drift scores)
            if alignment_scores:
                briefing['statistics']['average_alignment'] = sum(alignment_scores) / len(alignment_scores)
            
            return jsonify(briefing)
    
    def run(self):
        logger.info(f"Starting RAG server on port {self.port}")
        self.socketio.run(self.app, host='0.0.0.0', port=self.port, debug=False, allow_unsafe_werkzeug=True)

class RAGCLI:
    """Command-line interface for RAG agent"""
    
    def __init__(self, agent: ProjectKnowledgeAgent):
        self.agent = agent
    
    async def interactive_mode(self):
        """Interactive query mode"""
        print("\n🧠 RAG Knowledge Agent - Interactive Mode")
        print("Type 'exit' to quit, 'help' for commands\n")
        
        while True:
            try:
                query = input("Ask > ").strip()
                
                if query.lower() == 'exit':
                    break
                elif query.lower() == 'help':
                    self._print_help()
                elif query.lower().startswith('add decision:'):
                    decision = query[13:].strip()
                    context = input("Context > ").strip()
                    self.agent.add_decision(decision, context)
                    print("✅ Decision added to knowledge base")
                else:
                    results = await self.agent.query(query)
                    self._print_results(results)
                    
            except KeyboardInterrupt:
                print("\n\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def _print_help(self):
        print("""
Commands:
  exit                     - Exit the program
  help                     - Show this help
  add decision: <text>     - Add a project decision
  <any other text>         - Query the knowledge base
        """)
    
    def _print_results(self, results: Dict[str, Any]):
        if 'error' in results:
            print(f"\n❌ Error: {results['error']}")
            return
        
        print(f"\n📊 Found {len(results['results'])} relevant results:\n")
        
        for i, result in enumerate(results['results'], 1):
            print(f"--- Result {i} ---")
            print(f"File: {result['metadata'].get('file', 'Unknown')}")
            print(f"Type: {result['metadata'].get('type', 'Unknown')}")
            
            # Truncate content for display
            content = result['content']
            if len(content) > 200:
                content = content[:200] + "..."
            print(f"Content: {content}")
            print()

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='RAG Knowledge Agent')
    parser.add_argument('command', choices=['start', 'query', 'ingest', 'watch', 'server'],
                       help='Command to run')
    parser.add_argument('--path', help='Path to ingest (for ingest command)')
    parser.add_argument('--question', help='Question to ask (for query command)')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    
    args = parser.parse_args()
    
    # Initialize agent
    agent = ProjectKnowledgeAgent(CONFIG)
    
    if args.command == 'start':
        # Start everything: watcher + server
        print("🚀 Starting RAG Knowledge Agent...")
        
        # Initial ingestion for all active projects
        print("📁 Performing initial knowledge ingestion...")
        for project in agent.project_manager.get_active_projects():
            for directory in project.watch_dirs:
                if os.path.exists(directory):
                    chunks = await agent.ingest_directory(directory)
                    print(f"✅ Ingested {chunks} chunks from {directory} (Project: {project.name})")
        
        # Start file watcher
        observer = Observer()
        event_handler = CodebaseWatcher(agent)
        
        for project in agent.project_manager.get_active_projects():
            for directory in project.watch_dirs:
                if os.path.exists(directory):
                    observer.schedule(event_handler, directory, recursive=True)
                    print(f"👁️  Watching {directory} (Project: {project.name})")
        
        observer.start()
        
        # Start API server in background
        server = RAGServer(agent, CONFIG['api_port'])
        import threading
        server_thread = threading.Thread(target=server.run, daemon=True)
        server_thread.start()
        
        print(f"\n✅ RAG Agent running!")
        print(f"📡 API Server: http://localhost:{CONFIG['api_port']}")
        print(f"💡 Use 'rag_cli.py query' for CLI access\n")
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            print("\n👋 Shutting down...")
        
        observer.join()
    
    elif args.command == 'query':
        if args.question:
            results = await agent.query(args.question)
            cli = RAGCLI(agent)
            cli._print_results(results)
        else:
            # Interactive mode
            cli = RAGCLI(agent)
            await cli.interactive_mode()
    
    elif args.command == 'ingest':
        if not args.path:
            print("Error: --path required for ingest command")
            return
        
        if os.path.isfile(args.path):
            # Check if single file should be ignored
            if agent.path_filter.should_ignore_path(args.path):
                print(f"⚠️  File path is ignored by configuration: {args.path}")
                chunks = 0
            else:
                chunks = await agent.ingest_file(args.path)
        else:
            chunks = await agent.ingest_directory(args.path)
        
        print(f"✅ Ingested {chunks} chunks")
    
    elif args.command == 'watch':
        # Just run the watcher
        observer = Observer()
        event_handler = CodebaseWatcher(agent)
        
        for project in agent.project_manager.get_active_projects():
            for directory in project.watch_dirs:
                if os.path.exists(directory):
                    observer.schedule(event_handler, directory, recursive=True)
                    print(f"Watching {directory} (Project: {project.name})")
        
        observer.start()
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        
        observer.join()
    
    elif args.command == 'server':
        # Just run the API server
        server = RAGServer(agent, CONFIG['api_port'])
        server.run()

if __name__ == "__main__":
    asyncio.run(main())
