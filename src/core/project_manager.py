#!/usr/bin/env python3
"""
# GOVERNANCE HEADER - SKELETON FIRST DEVELOPMENT
# File: /path/to/contextkeeper/src/core/project_manager.py
# Project: ContextKeeper v3.0
# Purpose: Multi-project state management and lifecycle control
# Dependencies: dataclasses, enum, pathlib, json, logging
# Dependents: rag_agent.py, mcp-server/enhanced_mcp_server.js, all CLI scripts
# Created: 2025-08-03
# Modified: 2025-08-05

## PLANNING CONTEXT EMBEDDED
This module manages the complete lifecycle of projects in ContextKeeper:
- Project creation with unique IDs and isolated ChromaDB collections
- State persistence to filesystem (projects/ directory)
- Decision and objective tracking with timestamps
- Real-time event tracking for development activities
- Git integration for repository awareness

## ARCHITECTURAL DECISIONS
1. Projects stored as JSON files for simplicity and debugging
2. Each project gets a UUID-based identifier
3. Decisions/objectives stored within project state
4. Events tracked separately for performance
5. Focus state managed centrally

## TODO FROM PLANNING
- [ ] Add project archival functionality
- [ ] Implement project export/import
- [ ] Add project health metrics
- [ ] Enhance git integration for branch tracking

Project Manager for Multi-Project RAG Agent
Handles project lifecycle, configuration, and metadata management
"""

import os
import json
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from enum import Enum

logger = logging.getLogger(__name__)

class EventType(Enum):
    """Types of development events"""
    CODE_CHANGE = "code_change"
    ERROR = "error"
    DEPLOYMENT = "deployment"
    DECISION = "decision"
    OBJECTIVE = "objective"
    BUILD = "build"
    TEST = "test"
    PERFORMANCE = "performance"
    SECURITY = "security"
    API_CALL = "api_call"
    USER_ACTION = "user_action"
    

class EventSeverity(Enum):
    """Severity levels for events"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class DevelopmentEvent:
    """Real-time development event"""
    id: str = field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    type: EventType = EventType.CODE_CHANGE
    severity: EventSeverity = EventSeverity.INFO
    title: str = ""
    description: str = ""
    project_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'type': self.type.value,
            'severity': self.severity.value,
            'title': self.title,
            'description': self.description,
            'project_id': self.project_id,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat(),
            'tags': self.tags
        }


class ProjectStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"
    
@dataclass
class Decision:
    """Represents an architectural decision"""
    id: str
    decision: str
    reasoning: str
    timestamp: str
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

@dataclass 
class Objective:
    """Represents a project objective/goal"""
    id: str
    title: str
    description: str
    created_at: str
    completed_at: Optional[str] = None
    status: str = "pending"  # pending, in_progress, completed
    priority: str = "medium"  # low, medium, high

@dataclass
class ProjectConfig:
    """Configuration for a single project"""
    project_id: str
    name: str
    root_path: str
    watch_dirs: List[str]
    status: ProjectStatus
    created_at: str
    last_active: str
    description: str = ""
    file_extensions: List[str] = None
    decisions: List[Decision] = None
    objectives: List[Objective] = None
    events: List[DevelopmentEvent] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.file_extensions is None:
            self.file_extensions = [".py", ".js", ".jsx", ".ts", ".tsx", ".md", ".json", ".yaml"]
        if self.decisions is None:
            self.decisions = []
        if self.objectives is None:
            self.objectives = []
        if self.events is None:
            self.events = []
        if self.metadata is None:
            self.metadata = {}
            
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['status'] = self.status.value
        data['decisions'] = [asdict(d) for d in self.decisions]
        data['objectives'] = [asdict(o) for o in self.objectives]
        data['events'] = [e.to_dict() for e in self.events]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ProjectConfig':
        """Create from dictionary"""
        data = data.copy()
        data['status'] = ProjectStatus(data['status'])
        data['decisions'] = [Decision(**d) for d in data.get('decisions', [])]
        data['objectives'] = [Objective(**o) for o in data.get('objectives', [])]
        # Handle events deserialization
        events_data = data.get('events', [])
        events = []
        for e in events_data:
            e_copy = e.copy()
            e_copy['type'] = EventType(e_copy['type'])
            e_copy['severity'] = EventSeverity(e_copy['severity'])
            e_copy['timestamp'] = datetime.fromisoformat(e_copy['timestamp'])
            events.append(DevelopmentEvent(**e_copy))
        data['events'] = events
        return cls(**data)

class ProjectManager:
    """Manages multiple project configurations and lifecycles"""
    
    def __init__(self, config_dir: str = None):
        """Initialize project manager
        
        Args:
            config_dir: Directory to store project configurations
        """
        self.config_dir = Path(config_dir or os.path.expanduser("~/.rag_projects"))
        self.config_dir.mkdir(exist_ok=True)
        self.projects: Dict[str, ProjectConfig] = {}
        self.focused_project_id: Optional[str] = None
        self.load_all_projects()
        
    def load_all_projects(self):
        """Load all project configurations from disk"""
        for config_file in self.config_dir.glob("*.json"):
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    project = ProjectConfig.from_dict(data)
                    self.projects[project.project_id] = project
                    logger.info(f"Loaded project: {project.name} ({project.project_id})")
            except Exception as e:
                logger.error(f"Error loading project config {config_file}: {e}")
                
        # Set focused project if none set
        if not self.focused_project_id and self.projects:
            active_projects = [p for p in self.projects.values() if p.status == ProjectStatus.ACTIVE]
            if active_projects:
                self.focused_project_id = active_projects[0].project_id
                
    def save_project(self, project: ProjectConfig):
        """Save project configuration to disk"""
        config_file = self.config_dir / f"{project.project_id}.json"
        with open(config_file, 'w') as f:
            json.dump(project.to_dict(), f, indent=2)
        logger.info(f"Saved project config: {project.name}")
        
    def create_project(self, name: str, root_path: str, watch_dirs: List[str] = None,
                      description: str = "") -> ProjectConfig:
        """Create a new project
        
        Args:
            name: Project name
            root_path: Root directory of the project
            watch_dirs: Directories to watch (defaults to root_path)
            description: Project description
            
        Returns:
            Created project configuration
        """
        project_id = f"proj_{uuid.uuid4().hex[:12]}"
        
        # Default watch dirs to root path if not specified
        if watch_dirs is None:
            watch_dirs = [root_path]
            
        # Ensure absolute paths
        root_path = os.path.abspath(root_path)
        watch_dirs = [os.path.abspath(d) for d in watch_dirs]
        
        project = ProjectConfig(
            project_id=project_id,
            name=name,
            root_path=root_path,
            watch_dirs=watch_dirs,
            status=ProjectStatus.ACTIVE,
            created_at=datetime.now().isoformat(),
            last_active=datetime.now().isoformat(),
            description=description
        )
        
        self.projects[project_id] = project
        self.save_project(project)
        
        # Set as focused if it's the first project
        if len(self.projects) == 1:
            self.focused_project_id = project_id
            
        logger.info(f"Created project: {name} ({project_id})")
        return project
        
    def get_project(self, project_id: str) -> Optional[ProjectConfig]:
        """Get project by ID"""
        return self.projects.get(project_id)
        
    def get_focused_project(self) -> Optional[ProjectConfig]:
        """Get the currently focused project"""
        if self.focused_project_id:
            return self.projects.get(self.focused_project_id)
        return None
        
    def set_focus(self, project_id: str) -> bool:
        """Set the focused project"""
        if project_id in self.projects:
            self.focused_project_id = project_id
            project = self.projects[project_id]
            project.last_active = datetime.now().isoformat()
            self.save_project(project)
            logger.info(f"Focused on project: {project.name}")
            return True
        return False
        
    def update_status(self, project_id: str, status: ProjectStatus) -> bool:
        """Update project status"""
        if project_id in self.projects:
            project = self.projects[project_id]
            project.status = status
            project.last_active = datetime.now().isoformat()
            self.save_project(project)
            logger.info(f"Updated project {project.name} status to: {status.value}")
            return True
        return False
        
    def pause_project(self, project_id: str) -> bool:
        """Pause a project"""
        return self.update_status(project_id, ProjectStatus.PAUSED)
        
    def resume_project(self, project_id: str) -> bool:
        """Resume a paused project"""
        return self.update_status(project_id, ProjectStatus.ACTIVE)
        
    def archive_project(self, project_id: str) -> bool:
        """Archive a project"""
        return self.update_status(project_id, ProjectStatus.ARCHIVED)
        
    def add_decision(self, project_id: str, decision: str, reasoning: str, 
                    tags: List[str] = None) -> Optional[Decision]:
        """Add a decision to a project"""
        if project_id not in self.projects:
            return None
            
        project = self.projects[project_id]
        decision_obj = Decision(
            id=f"dec_{uuid.uuid4().hex[:8]}",
            decision=decision,
            reasoning=reasoning,
            timestamp=datetime.now().isoformat(),
            tags=tags or []
        )
        
        project.decisions.append(decision_obj)
        project.last_active = datetime.now().isoformat()
        self.save_project(project)
        
        logger.info(f"Added decision to project {project.name}: {decision}")
        return decision_obj
        
    def add_objective(self, project_id: str, title: str, description: str = "",
                     priority: str = "medium") -> Optional[Objective]:
        """Add an objective to a project"""
        if project_id not in self.projects:
            return None
            
        project = self.projects[project_id]
        objective = Objective(
            id=f"obj_{uuid.uuid4().hex[:8]}",
            title=title,
            description=description,
            created_at=datetime.now().isoformat(),
            priority=priority
        )
        
        project.objectives.append(objective)
        project.last_active = datetime.now().isoformat()
        self.save_project(project)
        
        logger.info(f"Added objective to project {project.name}: {title}")
        return objective
        
    def complete_objective(self, project_id: str, objective_id: str) -> bool:
        """Mark an objective as completed"""
        if project_id not in self.projects:
            return False
            
        project = self.projects[project_id]
        for obj in project.objectives:
            if obj.id == objective_id:
                obj.status = "completed"
                obj.completed_at = datetime.now().isoformat()
                project.last_active = datetime.now().isoformat()
                self.save_project(project)
                logger.info(f"Completed objective in project {project.name}: {obj.title}")
                return True
        return False
        
    def get_active_projects(self) -> List[ProjectConfig]:
        """Get all active projects"""
        return [p for p in self.projects.values() if p.status == ProjectStatus.ACTIVE]
        
    def get_all_watch_dirs(self) -> List[str]:
        """Get all watch directories from active projects"""
        watch_dirs = []
        for project in self.get_active_projects():
            watch_dirs.extend(project.watch_dirs)
        return list(set(watch_dirs))  # Remove duplicates
        
    def export_context(self, project_id: str) -> Dict[str, Any]:
        """Export project context for AI agents"""
        if project_id not in self.projects:
            return {}
            
        project = self.projects[project_id]
        
        # Get recent decisions and pending objectives
        recent_decisions = sorted(project.decisions, 
                                key=lambda d: d.timestamp, 
                                reverse=True)[:10]
        pending_objectives = [o for o in project.objectives if o.status != "completed"]
        
        context = {
            "project": {
                "id": project.project_id,
                "name": project.name,
                "description": project.description,
                "root_path": project.root_path,
                "status": project.status.value,
                "last_active": project.last_active
            },
            "recent_decisions": [
                {
                    "decision": d.decision,
                    "reasoning": d.reasoning,
                    "timestamp": d.timestamp,
                    "tags": d.tags
                } for d in recent_decisions
            ],
            "pending_objectives": [
                {
                    "title": o.title,
                    "description": o.description,
                    "priority": o.priority,
                    "created_at": o.created_at
                } for o in pending_objectives
            ],
            "statistics": {
                "total_decisions": len(project.decisions),
                "total_objectives": len(project.objectives),
                "completed_objectives": len([o for o in project.objectives if o.status == "completed"]),
                "watch_directories": len(project.watch_dirs)
            }
        }
        
        return context
        
    def get_project_summary(self) -> Dict[str, Any]:
        """Get summary of all projects"""
        summary = {
            "total_projects": len(self.projects),
            "active_projects": len([p for p in self.projects.values() if p.status == ProjectStatus.ACTIVE]),
            "paused_projects": len([p for p in self.projects.values() if p.status == ProjectStatus.PAUSED]),
            "archived_projects": len([p for p in self.projects.values() if p.status == ProjectStatus.ARCHIVED]),
            "focused_project": self.focused_project_id,
            "projects": []
        }
        
        for project in self.projects.values():
            summary["projects"].append({
                "id": project.project_id,
                "name": project.name,
                "status": project.status.value,
                "last_active": project.last_active,
                "objectives_pending": len([o for o in project.objectives if o.status != "completed"]),
                "total_decisions": len(project.decisions)
            })
            
        return summary
    
    def add_event(self, event: DevelopmentEvent) -> Optional[DevelopmentEvent]:
        """Add a development event to a project
        
        Args:
            event: DevelopmentEvent instance with project_id set
            
        Returns:
            The event if successful, None otherwise
        """
        try:
            # Use focused project if no project_id
            if not event.project_id:
                event.project_id = self.focused_project_id
                
            if not event.project_id:
                logger.error("No project specified for event")
                return None
                
            project = self.get_project(event.project_id)
            if not project:
                logger.error(f"Project {event.project_id} not found")
                return None
                
            # Add event to project
            project.events.append(event)
            
            # Keep only last 1000 events per project
            if len(project.events) > 1000:
                project.events = project.events[-1000:]
            
            # Update last active
            project.last_active = datetime.now().isoformat()
            
            # Save configuration
            self.save_project(project)
            
            logger.info(f"Added event {event.type.value} to project {project.name}")
            return event
            
        except Exception as e:
            logger.error(f"Failed to add event: {e}")
            return None
    
    def get_recent_events(self, project_id: str = None, limit: int = 100, 
                         event_types: List[EventType] = None,
                         severity: EventSeverity = None) -> List[DevelopmentEvent]:
        """Get recent events for a project with optional filtering
        
        Args:
            project_id: Project ID (uses focused project if None)
            limit: Maximum number of events to return
            event_types: Filter by event types
            severity: Minimum severity level
            
        Returns:
            List of recent events
        """
        project_id = project_id or self.focused_project_id
        if not project_id:
            return []
            
        project = self.get_project(project_id)
        if not project:
            return []
            
        events = project.events[-limit:]  # Get most recent
        
        # Apply filters
        if event_types:
            events = [e for e in events if e.type in event_types]
            
        if severity:
            severity_order = [EventSeverity.INFO, EventSeverity.WARNING, 
                            EventSeverity.ERROR, EventSeverity.CRITICAL]
            min_severity_index = severity_order.index(severity)
            events = [e for e in events 
                     if severity_order.index(e.severity) >= min_severity_index]
        
        return events