#!/usr/bin/env python3
"""
# GOVERNANCE HEADER - SKELETON FIRST DEVELOPMENT
# File: /path/to/contextkeeper/src/sacred/enhanced_drift_sacred.py
# Project: ContextKeeper v3.0
# Purpose: Detect drift between implementation and sacred architectural plans
# Dependencies: numpy, sklearn, dataclasses, logging
# Dependents: rag_agent.py drift detection endpoints, sacred CLI commands
# Created: 2025-08-04
# Modified: 2025-08-05

## PLANNING CONTEXT EMBEDDED
This module provides advanced drift detection capabilities:
- Compares current implementation against approved sacred plans
- Uses semantic similarity to detect architectural violations
- Provides actionable recommendations for alignment
- Tracks adherence scores for each sacred plan
- Generates warnings for critical violations

## ARCHITECTURAL DECISIONS
1. TF-IDF vectorization for text similarity
2. Cosine similarity for semantic comparison
3. Multi-level severity (aligned → critical_violation)
4. Time-based analysis for recent changes
5. Integration with sacred layer for plan retrieval

## TODO FROM PLANNING
- [ ] Add visual drift reports
- [ ] Implement real-time drift notifications
- [ ] Create drift history tracking
- [ ] Add plan-specific thresholds

Enhanced Drift Detection with Sacred Layer Integration
Compares development activity against approved sacred plans
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class SacredDriftAnalysis:
    """Results of drift analysis against sacred plans"""
    alignment_score: float  # 0-1 overall alignment
    sacred_violations: List[Dict[str, Any]]  # Specific violations
    warnings: List[str]  # Warning messages
    recommendations: List[str]  # Action recommendations
    plan_adherence: Dict[str, float]  # plan_id -> adherence score
    status: str  # aligned, minor_drift, major_drift, critical_violation

class SacredDriftDetector:
    """Detects drift from sacred approved plans"""
    
    def __init__(self, rag_agent, sacred_manager):
        self.rag_agent = rag_agent
        self.sacred_manager = sacred_manager
        self.vectorizer = TfidfVectorizer(
            max_features=200,
            stop_words='english',
            ngram_range=(1, 3),  # Capture more context
            min_df=1
        )
    
    async def analyze_sacred_drift(self, project_id: str,
                                  hours: int = 24) -> SacredDriftAnalysis:
        """Analyze drift from sacred plans"""
        
        # Get approved sacred plans
        sacred_plans = self.sacred_manager.list_plans(
            project_id=project_id,
            status=PlanStatus.APPROVED
        )
        
        if not sacred_plans:
            return SacredDriftAnalysis(
                alignment_score=1.0,  # No plans = no violations
                sacred_violations=[],
                warnings=["No sacred plans found for comparison"],
                recommendations=["Consider creating and approving development plans"],
                plan_adherence={},
                status="no_plans"
            )
        
        # Get recent development activity
        activities = await self._get_recent_activities(project_id, hours)
        
        if not activities:
            return SacredDriftAnalysis(
                alignment_score=0.5,
                sacred_violations=[],
                warnings=["No recent activity to analyze"],
                recommendations=["Resume development according to sacred plans"],
                plan_adherence={},
                status="no_activity"
            )

        # Analyze each sacred plan
        violations = []
        plan_scores = {}
        all_warnings = []

        for plan_info in sacred_plans:
            plan_id = plan_info['plan_id']
            
            # Get full plan content
            plan_results = await self.sacred_manager.query_sacred_plans(
                project_id, f"plan_id:{plan_id}", reconstruct=True
            )
            
            if not plan_results['plans']:
                continue
            
            plan_content = plan_results['plans'][0]['content']
            
            # Compare with activities
            adherence_score, plan_violations = await self._compare_with_plan(
                plan_content, activities
            )
            
            plan_scores[plan_id] = adherence_score
            
            if plan_violations:
                violations.extend(plan_violations)
                all_warnings.append(
                    f"Violations detected against plan: {plan_info['title']}"
                )

        # Calculate overall alignment
        if plan_scores:
            overall_alignment = sum(plan_scores.values()) / len(plan_scores)
        else:
            overall_alignment = 0.5

        # Determine status
        if overall_alignment >= 0.8:
            status = "aligned"
        elif overall_alignment >= 0.6:
            status = "minor_drift"
        elif overall_alignment >= 0.4:
            status = "major_drift"
        else:
            status = "critical_violation"

        # Generate recommendations
        recommendations = self._generate_sacred_recommendations(
            overall_alignment, violations, plan_scores
        )

        return SacredDriftAnalysis(
            alignment_score=overall_alignment,
            sacred_violations=violations,
            warnings=all_warnings,
            recommendations=recommendations,
            plan_adherence=plan_scores,
            status=status
        )

    async def _get_recent_activities(self, project_id: str,
                                   hours: int) -> List[Dict[str, Any]]:
        """Get recent development activities"""
        activities = []

        # Get from git if available
        if hasattr(self.rag_agent, 'git_integration'):
            git_activity = self.rag_agent.git_integration.git_trackers.get(project_id)
            if git_activity:
                commits = git_activity.get_recent_commits(hours)
                for commit in commits:
                    activities.append({
                        'type': 'commit',
                        'content': f"{commit.message}\n{' '.join(commit.files_changed)}",
                        'timestamp': commit.date,
                        'metadata': {
                            'files': commit.files_changed,
                            'additions': commit.additions,
                            'deletions': commit.deletions
                        }
                    })

        # Get recent code queries/changes from knowledge base
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        kb_results = await self.rag_agent.query(
            f"changes OR modifications OR updates since:{since}",
            k=50,
            project_id=project_id
        )

        for result in kb_results.get('results', []):
            if result['metadata'].get('ingested_at', '') > since:
                activities.append({
                    'type': 'code_change',
                    'content': result['content'],
                    'timestamp': result['metadata'].get('ingested_at'),
                    'metadata': result['metadata']
                })

        # Get recent decisions
        project = self.rag_agent.project_manager.get_project(project_id)
        if project:
            for decision in project.decisions:
                if decision.timestamp > since:
                    activities.append({
                        'type': 'decision',
                        'content': f"{decision.decision} - {decision.reasoning}",
                        'timestamp': decision.timestamp,
                        'metadata': {'tags': decision.tags}
                    })

        return sorted(activities, key=lambda x: x['timestamp'], reverse=True)

    async def _compare_with_plan(self, plan_content: str,
                               activities: List[Dict[str, Any]]) -> tuple[float, List[Dict]]:
        """Compare activities with a sacred plan"""

        # Extract key requirements from plan
        plan_requirements = self._extract_requirements(plan_content)

        # Prepare texts for comparison
        activity_texts = [a['content'] for a in activities]

        if not activity_texts or not plan_requirements:
            return 0.5, []  # No data to compare

        # Vectorize and compare
        all_texts = plan_requirements + activity_texts
        try:
            tfidf_matrix = self.vectorizer.fit_transform(all_texts)
            
            # Split matrices
            plan_vectors = tfidf_matrix[:len(plan_requirements)]
            activity_vectors = tfidf_matrix[len(plan_requirements):]
            
            # Calculate similarities
            similarities = cosine_similarity(activity_vectors, plan_vectors)

            # Analyze violations
            violations = []
            adherence_scores = []

            for i, activity in enumerate(activities):
                max_similarity = np.max(similarities[i])
                best_requirement_idx = np.argmax(similarities[i])
                
                if max_similarity < 0.3:  # Low similarity = potential violation
                    violations.append({
                        'activity': activity,
                        'similarity': float(max_similarity),
                        'expected': plan_requirements[best_requirement_idx],
                        'severity': 'high' if max_similarity < 0.1 else 'medium'
                    })
                
                adherence_scores.append(max_similarity)
            
            # Calculate overall adherence
            overall_adherence = np.mean(adherence_scores) if adherence_scores else 0.5
            
            return float(overall_adherence), violations
            
        except Exception as e:
            logger.error(f"Error in plan comparison: {e}")
            return 0.5, []
    
    def _extract_requirements(self, plan_content: str) -> List[str]:
        """Extract key requirements from plan text"""
        requirements = []
        
        # Look for common requirement patterns
        lines = plan_content.split('\n')

        for line in lines:
            line = line.strip()

            # Common patterns for requirements
            if any(pattern in line.lower() for pattern in [
                'must', 'shall', 'should', 'will', 'requirement:',
                'objective:', 'goal:', 'deliverable:', 'implement',
                'create', 'develop', 'ensure', 'verify'
            ]):
                requirements.append(line)
            
            # Bullet points often indicate requirements
            elif line.startswith(('- ', '* ', '• ', '□ ', '☐ ')):
                requirements.append(line[2:])

            # Numbered items
            elif any(line.startswith(f"{i}.") for i in range(1, 10)):
                requirements.append(line.split('.', 1)[1].strip())

        # If no explicit requirements found, use paragraphs
        if not requirements:
            paragraphs = [p.strip() for p in plan_content.split('\n\n') if p.strip()]
            requirements = paragraphs[:10]  # Top 10 paragraphs
        
        return requirements
    
    def _generate_sacred_recommendations(self, alignment_score: float,
                                       violations: List[Dict],
                                       plan_scores: Dict[str, float]) -> List[str]:
        """Generate recommendations based on sacred drift analysis"""
        recommendations = []
        
        # Critical violations
        if alignment_score < 0.4:
            recommendations.append(
                "🚨 CRITICAL: Development significantly deviates from sacred plans. "
                "Immediate review and realignment required."
            )
            recommendations.append(
                "Consider pausing current work and reviewing sacred plans with team."
            )
        
        # Specific plan violations
        low_adherence_plans = [
            plan_id for plan_id, score in plan_scores.items()
            if score < 0.5
        ]
        
        if low_adherence_plans:
            recommendations.append(
                f"⚠️ Low adherence to {len(low_adherence_plans)} sacred plan(s). "
                "Review these plans and adjust development approach."
            )
        
        # Activity-specific recommendations
        if violations:
            high_severity = [v for v in violations if v['severity'] == 'high']
            if high_severity:
                recommendations.append(
                    f"🔴 {len(high_severity)} high-severity violations detected. "
                    "These activities directly contradict sacred plans."
                )
            
            # Most common violation type
            violation_types = {}
            for v in violations:
                activity_type = v['activity']['type']
                violation_types[activity_type] = violation_types.get(activity_type, 0) + 1

            if violation_types:
                most_common = max(violation_types.items(), key=lambda x: x[1])
                recommendations.append(
                    f"Most violations are from {most_common[0]} activities. "
                    f"Review your {most_common[0]} process against sacred plans."
                )
        
        # Positive reinforcement
        if alignment_score >= 0.8:
            recommendations.append(
                "✅ Excellent adherence to sacred plans! Continue current approach."
            )
        elif alignment_score >= 0.6:
            recommendations.append(
                "👍 Good alignment with sacred plans. Minor adjustments may improve adherence."
            )

        # Action items
        if violations:
            recommendations.append(
                "Action items:\n"
                "1. Review violation details below\n"
                "2. Adjust current work to align with plans\n"
                "3. If plans need updating, follow sacred plan revision process"
            )
        
        return recommendations
    
    def generate_sacred_drift_report(self, project_name: str,
                                   analysis: SacredDriftAnalysis) -> str:
        """Generate detailed drift report"""
        report = f"""
Sacred Plan Drift Analysis - {project_name}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
{'=' * 60}

Overall Sacred Plan Alignment: {analysis.alignment_score:.1%}
Status: {analysis.status.upper()}

Plan Adherence Scores:
"""
        
        for plan_id, score in analysis.plan_adherence.items():
            status_icon = "✅" if score >= 0.8 else "⚠️" if score >= 0.5 else "🔴"
            report += f"  {status_icon} Plan {plan_id}: {score:.1%}\n"
        
        if analysis.warnings:
            report += "\nWarnings:\n"
            for warning in analysis.warnings:
                report += f"  ⚠️ {warning}\n"
        
        if analysis.sacred_violations:
            report += f"\nViolations Detected ({len(analysis.sacred_violations)}):\n"
            for i, violation in enumerate(analysis.sacred_violations[:10]):
                report += f"\n{i+1}. {violation['activity']['type'].upper()} "
                report += f"(Similarity: {violation['similarity']:.1%})\n"
                report += f"   Activity: {violation['activity']['content'][:100]}...\n"
                report += f"   Expected: {violation['expected'][:100]}...\n"
                report += f"   Severity: {violation['severity']}\n"
        
        report += "\nRecommendations:\n"
        for rec in analysis.recommendations:
            report += f"  {rec}\n"

        return report

# Integration endpoint
def add_sacred_drift_endpoint(app, agent, project_manager, sacred_manager):
    """Add sacred drift detection endpoint"""
    detector = SacredDriftDetector(agent, sacred_manager)
    
    @app.route('/projects/<project_id>/sacred-drift', methods=['GET'])
    async def analyze_sacred_drift(project_id):
        hours = int(request.args.get('hours', 24))
        
        project = project_manager.get_project(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404

        # Analyze drift
        analysis = await detector.analyze_sacred_drift(project_id, hours)

        # Generate report
        report = detector.generate_sacred_drift_report(project.name, analysis)

        return jsonify({
            'project_id': project_id,
            'project_name': project.name,
            'analysis': {
                'alignment_score': analysis.alignment_score,
                'status': analysis.status,
                'plan_adherence': analysis.plan_adherence,
                'violation_count': len(analysis.sacred_violations),
                'warnings': analysis.warnings,
                'recommendations': analysis.recommendations
            },
            'report': report,
            'violations': [
                {
                    'type': v['activity']['type'],
                    'timestamp': v['activity']['timestamp'],
                    'severity': v['severity'],
                    'similarity': v['similarity']
                }
                for v in analysis.sacred_violations[:10]  # First 10
            ]
        })
