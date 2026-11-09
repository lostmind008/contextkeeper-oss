"""
Sacred Metrics Calculator
Calculates comprehensive metrics for sacred plan analytics dashboard
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from src.sacred.sacred_layer_implementation import SacredLayerManager
from src.sacred.enhanced_drift_sacred import SacredDriftDetector

logger = logging.getLogger(__name__)


class SacredMetricsCalculator:
    """Calculates metrics for sacred plan analytics"""

    def __init__(
        self,
        sacred_manager: SacredLayerManager,
        drift_detector: SacredDriftDetector,
        project_manager,
    ):
        self.sacred_manager = sacred_manager
        self.drift_detector = drift_detector
        self.project_manager = project_manager

    async def calculate_overall_metrics(self) -> Dict[str, Any]:
        """Calculate system-wide sacred plan metrics"""
        try:
            # Get all projects
            projects = await self._get_all_projects()
            total_projects = len(projects)

            # Get plan statistics
            plan_stats = self.sacred_manager.get_plans_statistics()
            total_plans = plan_stats["total_plans"]
            approved_plans = plan_stats["by_status"].get("APPROVED", 0)

            # Calculate projects with plans
            projects_with_plans = len(plan_stats["by_project"])

            # Calculate coverage and compliance
            sacred_coverage_percentage = (
                (projects_with_plans / total_projects * 100)
                if total_projects > 0
                else 0
            )
            compliance_rate = (
                (approved_plans / total_plans * 100) if total_plans > 0 else 0
            )

            # Calculate average adherence score
            avg_adherence_score = await self._calculate_average_adherence_score(
                list(plan_stats["by_project"].keys())
            )

            return {
                "total_projects": total_projects,
                "projects_with_plans": projects_with_plans,
                "sacred_coverage_percentage": round(sacred_coverage_percentage, 1),
                "total_plans": total_plans,
                "approved_plans": approved_plans,
                "compliance_rate": round(compliance_rate, 1),
                "avg_adherence_score": round(avg_adherence_score, 1),
            }

        except Exception as e:
            logger.error(f"Error calculating overall metrics: {str(e)}", exc_info=True)
            # Return default metrics on error
            return {
                "total_projects": 0,
                "projects_with_plans": 0,
                "sacred_coverage_percentage": 0,
                "total_plans": 0,
                "approved_plans": 0,
                "compliance_rate": 0,
                "avg_adherence_score": 0,
            }

    async def calculate_project_metrics(
        self, project_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Calculate per-project sacred plan metrics"""
        try:
            projects = await self._get_all_projects()
            if project_filter:
                projects = [p for p in projects if p["id"] == project_filter]

            project_metrics = []

            for project in projects:
                project_id = project["id"]
                project_name = project.get("name", project_id)

                # Get project plan summary
                plan_summary = self.sacred_manager.get_project_plan_summary(project_id)

                # Calculate adherence score
                adherence_score = await self.calculate_adherence_score(project_id)

                # Get drift warnings count
                drift_warnings = await self._get_drift_warnings_count(project_id)

                # Get last drift check time
                last_drift_check = await self._get_last_drift_check(project_id)

                project_metrics.append(
                    {
                        "project_id": project_id,
                        "project_name": project_name,
                        "plan_count": plan_summary["total_plans"],
                        "approved_plans": plan_summary["approved_plans"],
                        "adherence_score": round(adherence_score, 1),
                        "drift_warnings": drift_warnings,
                        "last_drift_check": (
                            last_drift_check.isoformat() if last_drift_check else None
                        ),
                        "status_breakdown": {
                            "DRAFT": plan_summary["draft_plans"],
                            "APPROVED": plan_summary["approved_plans"],
                            "LOCKED": plan_summary["locked_plans"],
                            "SUPERSEDED": plan_summary["superseded_plans"],
                        },
                    }
                )

            return project_metrics

        except Exception as e:
            logger.error(f"Error calculating project metrics: {str(e)}", exc_info=True)
            return []

    async def calculate_adherence_score(self, project_id: str) -> float:
        """Calculate adherence score (0-100) based on drift analysis and plan compliance"""
        try:
            # Start with base score of 100
            base_score = 100.0

            # Check if project has any approved plans
            plan_summary = self.sacred_manager.get_project_plan_summary(project_id)
            if plan_summary["approved_plans"] == 0:
                return 0.0  # No approved plans = 0 adherence

            # Analyze recent drift (last 7 days)
            try:
                drift_analysis = await self.drift_detector.analyze_sacred_drift(
                    project_id, hours=168
                )  # 7 days

                # Deduct points based on drift severity
                if hasattr(drift_analysis, "violations") and drift_analysis.violations:
                    violation_penalty = min(
                        len(drift_analysis.violations) * 10, 50
                    )  # Max 50 points for violations
                    base_score -= violation_penalty

                if hasattr(drift_analysis, "concerns") and drift_analysis.concerns:
                    concern_penalty = min(
                        len(drift_analysis.concerns) * 5, 25
                    )  # Max 25 points for concerns
                    base_score -= concern_penalty

                # Consider drift frequency
                if hasattr(drift_analysis, "severity_score"):
                    severity_penalty = min(
                        drift_analysis.severity_score * 5, 25
                    )  # Max 25 points for severity
                    base_score -= severity_penalty

            except Exception as drift_error:
                logger.warning(
                    f"Could not analyze drift for adherence score calculation: {str(drift_error)}"
                )
                # Slight penalty for inability to check drift
                base_score -= 5

            # Ensure score is between 0 and 100
            final_score = max(0.0, min(100.0, base_score))

            return final_score

        except Exception as e:
            logger.error(
                f"Error calculating adherence score for {project_id}: {str(e)}",
                exc_info=True,
            )
            return 0.0

    async def get_recent_activity(self, timeframe: str = "7d") -> List[Dict[str, Any]]:
        """Get recent sacred plan activity"""
        try:
            # Parse timeframe
            hours = self._parse_timeframe(timeframe)
            cutoff_time = datetime.now() - timedelta(hours=hours)

            activities = []

            # Check for recent plan creations and approvals
            for plan_id, plan_data in self.sacred_manager.plans_registry.items():
                plan = plan_data["plan"]
                created_at = plan_data.get("created_at")
                approved_at = plan_data.get("approved_at")

                # Plan creation activity
                if created_at and created_at >= cutoff_time:
                    activities.append(
                        {
                            "type": "plan_created",
                            "project_id": plan.project_id,
                            "plan_id": plan_id,
                            "timestamp": created_at.isoformat(),
                            "details": f"Sacred plan '{plan.title}' created",
                        }
                    )

                # Plan approval activity
                if approved_at and approved_at >= cutoff_time:
                    activities.append(
                        {
                            "type": "plan_approved",
                            "project_id": plan.project_id,
                            "plan_id": plan_id,
                            "timestamp": approved_at.isoformat(),
                            "details": f"Sacred plan '{plan.title}' approved",
                        }
                    )

            # Sort by timestamp (most recent first)
            activities.sort(key=lambda x: x["timestamp"], reverse=True)

            # Limit to 20 most recent activities
            return activities[:20]

        except Exception as e:
            logger.error(f"Error getting recent activity: {str(e)}", exc_info=True)
            return []

    async def calculate_drift_analysis(self, timeframe: str = "7d") -> Dict[str, Any]:
        """Calculate drift analysis summary"""
        try:
            hours = self._parse_timeframe(timeframe)

            # Get all projects with plans
            plan_stats = self.sacred_manager.get_plans_statistics()
            projects_with_plans = list(plan_stats["by_project"].keys())

            total_drift_events = 0
            projects_with_drift = 0
            total_severity = 0.0
            drift_count = 0
            recent_drift_events = []

            for project_id in projects_with_plans:
                try:
                    drift_analysis = await self.drift_detector.analyze_sacred_drift(
                        project_id, hours=hours
                    )

                    # Count violations and concerns as drift events
                    project_drift_events = 0
                    if hasattr(drift_analysis, "violations"):
                        project_drift_events += len(drift_analysis.violations)
                    if hasattr(drift_analysis, "concerns"):
                        project_drift_events += len(drift_analysis.concerns)

                    if project_drift_events > 0:
                        projects_with_drift += 1
                        total_drift_events += project_drift_events

                        recent_drift_events.append(
                            {
                                "project_id": project_id,
                                "drift_events": project_drift_events,
                                "timestamp": datetime.now().isoformat(),
                                "details": f"{project_drift_events} drift events detected",
                            }
                        )

                    # Add to severity calculation
                    if hasattr(drift_analysis, "severity_score"):
                        total_severity += drift_analysis.severity_score
                        drift_count += 1

                except Exception as project_drift_error:
                    logger.warning(
                        f"Could not analyze drift for project {project_id}: {str(project_drift_error)}"
                    )
                    continue

            avg_drift_severity = (
                (total_severity / drift_count) if drift_count > 0 else 0.0
            )

            return {
                "total_drift_events": total_drift_events,
                "projects_with_drift": projects_with_drift,
                "avg_drift_severity": round(avg_drift_severity, 1),
                "recent_drift_events": recent_drift_events[
                    :10
                ],  # Limit to 10 most recent
            }

        except Exception as e:
            logger.error(f"Error calculating drift analysis: {str(e)}", exc_info=True)
            return {
                "total_drift_events": 0,
                "projects_with_drift": 0,
                "avg_drift_severity": 0.0,
                "recent_drift_events": [],
            }

    # Helper methods

    async def _get_all_projects(self) -> List[Dict[str, Any]]:
        """Get all projects from project manager"""
        try:
            if hasattr(self.project_manager, "list_projects"):
                return await self.project_manager.list_projects()
            elif hasattr(self.project_manager, "get_all_projects"):
                return await self.project_manager.get_all_projects()
            else:
                # Fallback: extract projects from sacred plans
                plan_stats = self.sacred_manager.get_plans_statistics()
                projects = []
                for project_id in plan_stats["by_project"].keys():
                    projects.append(
                        {
                            "id": project_id,
                            "name": project_id,  # Use ID as name if no project manager
                        }
                    )
                return projects
        except Exception as e:
            logger.warning(f"Could not get projects from manager: {str(e)}")
            # Fallback: extract from sacred plans
            plan_stats = self.sacred_manager.get_plans_statistics()
            projects = []
            for project_id in plan_stats["by_project"].keys():
                projects.append({"id": project_id, "name": project_id})
            return projects

    async def _calculate_average_adherence_score(self, project_ids: List[str]) -> float:
        """Calculate average adherence score across projects"""
        if not project_ids:
            return 0.0

        total_score = 0.0
        valid_scores = 0

        for project_id in project_ids:
            try:
                score = await self.calculate_adherence_score(project_id)
                total_score += score
                valid_scores += 1
            except Exception as e:
                logger.warning(
                    f"Could not calculate adherence for {project_id}: {str(e)}"
                )
                continue

        return (total_score / valid_scores) if valid_scores > 0 else 0.0

    async def _get_drift_warnings_count(self, project_id: str) -> int:
        """Get count of drift warnings for a project"""
        try:
            drift_analysis = await self.drift_detector.analyze_sacred_drift(
                project_id, hours=168
            )  # 7 days
            warnings = 0
            if hasattr(drift_analysis, "violations"):
                warnings += len(drift_analysis.violations)
            if hasattr(drift_analysis, "concerns"):
                warnings += len(drift_analysis.concerns)
            return warnings
        except Exception as e:
            logger.warning(f"Could not get drift warnings for {project_id}: {str(e)}")
            return 0

    async def _get_last_drift_check(self, project_id: str) -> Optional[datetime]:
        """Get timestamp of last drift check for a project"""
        try:
            # For now, return current time as we don't store drift check history
            # In future, this could be enhanced to track actual drift check timestamps
            return datetime.now()
        except Exception as e:
            logger.warning(f"Could not get last drift check for {project_id}: {str(e)}")
            return None

    def _parse_timeframe(self, timeframe: str) -> int:
        """Parse timeframe string to hours"""
        timeframe_map = {"1d": 24, "7d": 168, "30d": 720, "90d": 2160}
        return timeframe_map.get(timeframe, 168)  # Default to 7 days
