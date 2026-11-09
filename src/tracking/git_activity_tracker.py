#!/usr/bin/env python3
"""
# GOVERNANCE HEADER - SKELETON FIRST DEVELOPMENT
# File: /path/to/contextkeeper/src/tracking/git_activity_tracker.py
# Project: ContextKeeper v3.0
# Purpose: Track git activity for temporal context in RAG queries
# Dependencies: subprocess, dataclasses, pathlib
# Dependents: rag_agent.py GitIntegratedRAGAgent, project context queries
# Created: 2025-08-03
# Modified: 2025-08-05

## PLANNING CONTEXT EMBEDDED
This module provides git repository awareness to ContextKeeper:
- Tracks commit history with file changes
- Monitors uncommitted modifications
- Analyzes branch activity and merges
- Provides temporal context for queries
- Integrates with RAG for "recent changes" queries

## ARCHITECTURAL DECISIONS
1. Uses subprocess for git commands (portable)
2. Caches commit data for performance
3. Integrates at RAG query level
4. Tracks both commits and working directory
5. Time-based filtering for relevance

## TODO FROM PLANNING
- [ ] Add git blame integration
- [ ] Track pull request associations
- [ ] Monitor remote repository changes
- [ ] Add commit message sentiment analysis

Git Activity Tracker for ContextKeeper
Tracks development activity through git commits and changes
"""

import os
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
import logging
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class GitCommit:
    """Represents a git commit"""
    hash: str
    author: str
    date: datetime
    message: str
    files_changed: List[str]
    additions: int
    deletions: int

@dataclass
class GitActivity:
    """Aggregated git activity for a time period"""
    commits: List[GitCommit]
    total_commits: int
    files_modified: Dict[str, int]  # file -> change count
    lines_added: int
    lines_deleted: int
    active_branches: List[str]
    current_branch: str

class GitActivityTracker:
    """Tracks development activity through git"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.git_dir = self.project_root / ".git"

        if not self.git_dir.exists():
            raise ValueError(f"No git repository found at {project_root}")
    
    def _run_git_command(self, args: List[str]) -> str:
        """Execute a git command and return output"""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {e.stderr}")
            return ""
    
    def get_recent_commits(self, hours: int = 24, branch: Optional[str] = None) -> List[GitCommit]:
        """Get commits from the last N hours"""
        since = datetime.now() - timedelta(hours=hours)
        since_str = since.strftime("%Y-%m-%d %H:%M:%S")
        
        # Build git log command
        cmd = [
            "log",
            f"--since=\"{since_str}\"",
            "--pretty=format:%H|%an|%ad|%s",
            "--date=iso",
            "--numstat"
        ]
        
        if branch:
            cmd.append(branch)
        
        output = self._run_git_command(cmd)
        if not output:
            return []
        
        commits = []
        current_commit = None
        files_changed = []
        additions = 0
        deletions = 0

        for line in output.split('\n'):
            if '|' in line and not '\t' in line:
                # Save previous commit if exists
                if current_commit:
                    current_commit.files_changed = files_changed
                    current_commit.additions = additions
                    current_commit.deletions = deletions
                    commits.append(current_commit)

                # Parse new commit
                parts = line.split('|')
                if len(parts) >= 4:
                    current_commit = GitCommit(
                        hash=parts[0],
                        author=parts[1],
                        date=datetime.fromisoformat(parts[2].strip()),
                        message=parts[3],
                        files_changed=[],
                        additions=0,
                        deletions=0
                    )
                    files_changed = []
                    additions = 0
                    deletions = 0
            
            elif '\t' in line and current_commit:
                # Parse file stats
                parts = line.split('\t')
                if len(parts) >= 3:
                    try:
                        add = int(parts[0]) if parts[0] != '-' else 0
                        delete = int(parts[1]) if parts[1] != '-' else 0
                        additions += add
                        deletions += delete
                        files_changed.append(parts[2])
                    except ValueError:
                        pass

        # Don't forget the last commit
        if current_commit:
            current_commit.files_changed = files_changed
            current_commit.additions = additions
            current_commit.deletions = deletions
            commits.append(current_commit)

        return commits
    
    def get_file_changes(self, file_path: str, hours: int = 168) -> List[Tuple[datetime, str]]:
        """Get change history for a specific file"""
        cmd = [
            "log",
            f"--since=\"{hours} hours ago\"",
            "--pretty=format:%ad|%s",
            "--date=iso",
            "--",
            file_path
        ]
        
        output = self._run_git_command(cmd)
        if not output:
            return []
        
        changes = []
        for line in output.split('\n'):
            if '|' in line:
                parts = line.split('|', 1)
                if len(parts) == 2:
                    date = datetime.fromisoformat(parts[0].strip())
                    message = parts[1].strip()
                    changes.append((date, message))

        return changes

    def get_current_branch(self) -> str:
        """Get the current branch name"""
        return self._run_git_command(["branch", "--show-current"])

    def get_active_branches(self, days: int = 7) -> List[str]:
        """Get branches with recent activity"""
        cmd = [
            "for-each-ref",
            "--sort=-committerdate",
            "refs/heads/",
            f"--format=%(refname:short)|%(committerdate:iso)"
        ]

        output = self._run_git_command(cmd)
        if not output:
            return []

        cutoff = datetime.now() - timedelta(days=days)
        active_branches = []

        for line in output.split('\n'):
            if '|' in line:
                parts = line.split('|')
                if len(parts) == 2:
                    branch = parts[0]
                    date = datetime.fromisoformat(parts[1].strip())
                    if date > cutoff:
                        active_branches.append(branch)

        return active_branches

    def get_uncommitted_changes(self) -> Dict[str, Any]:
        """Get current uncommitted changes"""
        # Get status
        status_output = self._run_git_command(["status", "--porcelain"])

        modified_files = []
        untracked_files = []
        staged_files = []

        for line in status_output.split('\n'):
            if line:
                status = line[:2]
                file_path = line[3:]
                
                if status[0] in ['M', 'A', 'D', 'R']:
                    staged_files.append(file_path)
                if status[1] == 'M':
                    modified_files.append(file_path)
                elif status == '??':
                    untracked_files.append(file_path)

        # Get diff stats
        diff_output = self._run_git_command(["diff", "--stat"])

        return {
            "modified": modified_files,
            "untracked": untracked_files,
            "staged": staged_files,
            "has_changes": bool(modified_files or untracked_files or staged_files),
            "diff_summary": diff_output
        }
    
    def analyze_activity(self, hours: int = 24) -> GitActivity:
        """Analyze git activity for a time period"""
        commits = self.get_recent_commits(hours)
        
        # Aggregate statistics
        files_modified = defaultdict(int)
        total_additions = 0
        total_deletions = 0
        
        for commit in commits:
            total_additions += commit.additions
            total_deletions += commit.deletions
            for file in commit.files_changed:
                files_modified[file] += 1

        return GitActivity(
            commits=commits,
            total_commits=len(commits),
            files_modified=dict(files_modified),
            lines_added=total_additions,
            lines_deleted=total_deletions,
            active_branches=self.get_active_branches(),
            current_branch=self.get_current_branch()
        )

    def correlate_with_objectives(self, commits: List[GitCommit],
                                 objectives: List[str]) -> Dict[str, Any]:
        """Correlate commit messages with project objectives"""
        # Simple keyword matching - can be enhanced with NLP
        objective_keywords = {}
        for obj in objectives:
            # Extract keywords from objectives
            keywords = [w.lower() for w in obj.split()
                       if len(w) > 3 and w.lower() not in
                       ['the', 'and', 'for', 'with', 'from']]
            objective_keywords[obj] = keywords

        objective_commits = defaultdict(list)
        unaligned_commits = []

        for commit in commits:
            commit_words = commit.message.lower().split()
            aligned = False
            
            for obj, keywords in objective_keywords.items():
                if any(keyword in commit_words for keyword in keywords):
                    objective_commits[obj].append(commit)
                    aligned = True
                    break
            
            if not aligned:
                unaligned_commits.append(commit)

        # Calculate alignment score
        total_commits = len(commits)
        aligned_commits = total_commits - len(unaligned_commits)
        alignment_score = aligned_commits / total_commits if total_commits > 0 else 0

        return {
            "alignment_score": alignment_score,
            "objective_commits": dict(objective_commits),
            "unaligned_commits": unaligned_commits,
            "status": "aligned" if alignment_score > 0.6 else "potential_drift"
        }

    def generate_activity_summary(self, hours: int = 24) -> str:
        """Generate a human-readable activity summary"""
        activity = self.analyze_activity(hours)
        uncommitted = self.get_uncommitted_changes()

        summary = f"""
Git Activity Summary (Last {hours} hours)
=====================================
Current Branch: {activity.current_branch}
Total Commits: {activity.total_commits}
Lines Added: +{activity.lines_added}
Lines Deleted: -{activity.lines_deleted}

Most Modified Files:
"""

        # Sort files by modification count
        sorted_files = sorted(activity.files_modified.items(),
                            key=lambda x: x[1], reverse=True)[:5]

        for file, count in sorted_files:
            summary += f"  - {file}: {count} changes\n"

        if uncommitted['has_changes']:
            summary += f"\nUncommitted Changes:\n"
            summary += f"  - Modified: {len(uncommitted['modified'])} files\n"
            summary += f"  - Staged: {len(uncommitted['staged'])} files\n"
            summary += f"  - Untracked: {len(uncommitted['untracked'])} files\n"

        if activity.commits:
            summary += f"\nRecent Commits:\n"
            for commit in activity.commits[:5]:
                summary += f"  - {commit.date.strftime('%Y-%m-%d %H:%M')}: {commit.message[:60]}...\n"

        return summary

# Integration with RAG Agent
class GitIntegratedRAGAgent:
    """Extension to integrate git tracking with RAG agent"""
    
    def __init__(self, rag_agent, project_manager):
        self.rag_agent = rag_agent
        self.project_manager = project_manager
        self.git_trackers = {}

    def init_git_tracking(self, project_id: str):
        """Initialize git tracking for a project"""
        project = self.project_manager.get_project(project_id)
        if not project:
            return False
        
        try:
            tracker = GitActivityTracker(project.root_path)
            self.git_trackers[project_id] = tracker
            return True
        except ValueError as e:
            logger.warning(f"Could not init git tracking for {project.name}: {e}")
            return False

    async def update_project_from_git(self, project_id: str):
        """Update project knowledge base from recent git activity"""
        if project_id not in self.git_trackers:
            if not self.init_git_tracking(project_id):
                return
        
        tracker = self.git_trackers[project_id]
        activity = tracker.analyze_activity(hours=24)

        # Ingest recently modified files
        for file_path, _ in activity.files_modified.items():
            full_path = Path(tracker.project_root) / file_path
            if full_path.exists() and full_path.is_file():
                # Check if it's a supported file type
                if any(str(full_path).endswith(ext) for ext in
                      self.rag_agent.config['default_file_extensions']):
                    await self.rag_agent.ingest_file(str(full_path), project_id)
        
        # Add git activity summary to knowledge base
        summary = tracker.generate_activity_summary()
        await self._add_activity_to_knowledge(project_id, summary)
    
    async def _add_activity_to_knowledge(self, project_id: str, summary: str):
        """Add git activity summary to the knowledge base"""
        content = f"GIT ACTIVITY SUMMARY\n{summary}\nDATE: {datetime.now().isoformat()}"
        
        # Embed and store
        embedding = await self.rag_agent.embed_text(content)
        
        if project_id in self.rag_agent.collections:
            self.rag_agent.collections[project_id].add(
                ids=[f"git_activity_{datetime.now().timestamp()}"],
                embeddings=[embedding],
                documents=[content],
                metadatas=[{
                    'type': 'git_activity',
                    'project_id': project_id,
                    'timestamp': datetime.now().isoformat()
                }]
            )

    def check_objective_alignment(self, project_id: str) -> Dict[str, Any]:
        """Check if recent commits align with project objectives"""
        project = self.project_manager.get_project(project_id)
        if not project or project_id not in self.git_trackers:
            return {"error": "Project not found or git not initialized"}

        tracker = self.git_trackers[project_id]
        commits = tracker.get_recent_commits(hours=24)

        # Get active objectives
        active_objectives = [
            obj.title for obj in project.objectives
            if obj.status != "completed"
        ]

        if not active_objectives:
            return {"status": "no_objectives"}

        return tracker.correlate_with_objectives(commits, active_objectives)
