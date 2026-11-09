"""
Analytics Service Layer
Provides high-level analytics services for the sacred metrics dashboard
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from .sacred_metrics import SacredMetricsCalculator

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service layer for sacred plan analytics"""

    def __init__(self, metrics_calculator: SacredMetricsCalculator):
        self.calculator = metrics_calculator
        self._cache = {}
        self._cache_timestamps = {}
        self.cache_duration_minutes = 5  # Cache for 5 minutes

    async def get_sacred_analytics(
        self,
        timeframe: str = "7d",
        project_filter: Optional[str] = None,
        include_history: bool = False,
    ) -> Dict[str, Any]:
        """
        Main method for /analytics/sacred endpoint
        Returns comprehensive sacred plan analytics
        """
        try:
            # Generate cache key
            cache_key = (
                f"sacred_analytics_{timeframe}_{project_filter}_{include_history}"
            )

            # Check cache first
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                logger.debug(f"Returning cached analytics for key: {cache_key}")
                return cached_result

            logger.info(
                f"Calculating sacred analytics - timeframe: {timeframe}, project_filter: {project_filter}"
            )

            # Calculate all metrics concurrently for better performance
            overall_metrics = await self.calculator.calculate_overall_metrics()
            project_metrics = await self.calculator.calculate_project_metrics(
                project_filter
            )
            recent_activity = await self.calculator.get_recent_activity(timeframe)
            drift_analysis = await self.calculator.calculate_drift_analysis(timeframe)

            # Build response
            result = {
                "timestamp": datetime.now().isoformat(),
                "timeframe": timeframe,
                "overall_metrics": overall_metrics,
                "project_metrics": project_metrics,
                "recent_activity": recent_activity,
                "drift_analysis": drift_analysis,
            }

            # Add historical trends if requested
            if include_history:
                result["historical_trends"] = await self._get_historical_trends(
                    timeframe
                )

            # Cache the result
            self._cache_result(cache_key, result)

            logger.info(
                f"Sacred analytics calculated successfully - {len(project_metrics)} projects, {len(recent_activity)} activities"
            )
            return result

        except Exception as e:
            logger.error(f"Error in get_sacred_analytics: {str(e)}", exc_info=True)
            # Return minimal error response
            return {
                "timestamp": datetime.now().isoformat(),
                "timeframe": timeframe,
                "error": f"Failed to calculate analytics: {str(e)}",
                "overall_metrics": {
                    "total_projects": 0,
                    "projects_with_plans": 0,
                    "sacred_coverage_percentage": 0,
                    "total_plans": 0,
                    "approved_plans": 0,
                    "compliance_rate": 0,
                    "avg_adherence_score": 0,
                },
                "project_metrics": [],
                "recent_activity": [],
                "drift_analysis": {
                    "total_drift_events": 0,
                    "projects_with_drift": 0,
                    "avg_drift_severity": 0,
                    "recent_drift_events": [],
                },
            }

    async def get_project_detailed_analytics(
        self, project_id: str, timeframe: str = "7d"
    ) -> Dict[str, Any]:
        """
        Get detailed analytics for a specific project
        Useful for project-specific dashboard views
        """
        try:
            cache_key = f"project_analytics_{project_id}_{timeframe}"
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                return cached_result

            logger.info(f"Calculating detailed analytics for project: {project_id}")

            # Get project-specific metrics
            project_metrics = await self.calculator.calculate_project_metrics(
                project_id
            )
            project_data = project_metrics[0] if project_metrics else None

            if not project_data:
                return {
                    "error": f"Project {project_id} not found or has no sacred plans"
                }

            # Calculate adherence score with details
            adherence_score = await self.calculator.calculate_adherence_score(
                project_id
            )

            # Get recent activity for this project
            all_activity = await self.calculator.get_recent_activity(timeframe)
            project_activity = [
                activity
                for activity in all_activity
                if activity.get("project_id") == project_id
            ]

            # Get drift analysis for this project
            try:
                drift_analysis = (
                    await self.calculator.drift_detector.analyze_sacred_drift(
                        project_id
                    )
                )
                drift_details = {
                    "has_drift": bool(
                        getattr(drift_analysis, "violations", [])
                        or getattr(drift_analysis, "concerns", [])
                    ),
                    "violations": getattr(drift_analysis, "violations", []),
                    "concerns": getattr(drift_analysis, "concerns", []),
                    "severity_score": getattr(drift_analysis, "severity_score", 0),
                }
            except Exception as drift_error:
                logger.warning(
                    f"Could not get drift details for {project_id}: {str(drift_error)}"
                )
                drift_details = {
                    "has_drift": False,
                    "violations": [],
                    "concerns": [],
                    "severity_score": 0,
                }

            result = {
                "timestamp": datetime.now().isoformat(),
                "project_id": project_id,
                "timeframe": timeframe,
                "project_metrics": project_data,
                "adherence_details": {
                    "score": adherence_score,
                    "drift_analysis": drift_details,
                },
                "recent_activity": project_activity,
                "plan_breakdown": project_data["status_breakdown"],
            }

            self._cache_result(cache_key, result)
            return result

        except Exception as e:
            logger.error(
                f"Error in get_project_detailed_analytics: {str(e)}", exc_info=True
            )
            return {"error": f"Failed to calculate project analytics: {str(e)}"}

    async def get_sacred_health_check(self) -> Dict[str, Any]:
        """
        Health check for sacred analytics system
        Returns system status and basic connectivity info
        """
        try:
            health_status = {
                "timestamp": datetime.now().isoformat(),
                "status": "healthy",
                "components": {},
            }

            # Check sacred manager
            try:
                plan_stats = self.calculator.sacred_manager.get_plans_statistics()
                health_status["components"]["sacred_manager"] = {
                    "status": "healthy",
                    "total_plans": plan_stats["total_plans"],
                }
            except Exception as e:
                health_status["components"]["sacred_manager"] = {
                    "status": "error",
                    "error": str(e),
                }
                health_status["status"] = "degraded"

            # Check drift detector
            try:
                # Simple test - try to access drift detector methods
                if hasattr(self.calculator.drift_detector, "analyze_sacred_drift"):
                    health_status["components"]["drift_detector"] = {
                        "status": "healthy"
                    }
                else:
                    health_status["components"]["drift_detector"] = {
                        "status": "error",
                        "error": "Missing required methods",
                    }
                    health_status["status"] = "degraded"
            except Exception as e:
                health_status["components"]["drift_detector"] = {
                    "status": "error",
                    "error": str(e),
                }
                health_status["status"] = "degraded"

            # Check project manager
            try:
                projects = await self.calculator._get_all_projects()
                health_status["components"]["project_manager"] = {
                    "status": "healthy",
                    "total_projects": len(projects),
                }
            except Exception as e:
                health_status["components"]["project_manager"] = {
                    "status": "warning",
                    "error": str(e),
                    "note": "Using fallback project detection",
                }
                if health_status["status"] == "healthy":
                    health_status["status"] = "degraded"

            return health_status

        except Exception as e:
            logger.error(f"Error in sacred health check: {str(e)}", exc_info=True)
            return {
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "error": str(e),
            }

    # Cache management methods

    def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached result if still valid"""
        try:
            if cache_key in self._cache and cache_key in self._cache_timestamps:
                cache_time = self._cache_timestamps[cache_key]
                age_minutes = (datetime.now() - cache_time).total_seconds() / 60

                if age_minutes < self.cache_duration_minutes:
                    return self._cache[cache_key]
                else:
                    # Remove expired cache entry
                    del self._cache[cache_key]
                    del self._cache_timestamps[cache_key]

            return None
        except Exception as e:
            logger.warning(f"Error accessing cache: {str(e)}")
            return None

    def _cache_result(self, cache_key: str, result: Dict[str, Any]):
        """Cache result with timestamp"""
        try:
            self._cache[cache_key] = result
            self._cache_timestamps[cache_key] = datetime.now()

            # Simple cache cleanup - remove old entries if cache gets too large
            if len(self._cache) > 100:
                self._cleanup_cache()

        except Exception as e:
            logger.warning(f"Error caching result: {str(e)}")

    def _cleanup_cache(self):
        """Remove expired cache entries"""
        try:
            current_time = datetime.now()
            expired_keys = []

            for cache_key, cache_time in self._cache_timestamps.items():
                age_minutes = (current_time - cache_time).total_seconds() / 60
                if age_minutes >= self.cache_duration_minutes:
                    expired_keys.append(cache_key)

            for key in expired_keys:
                if key in self._cache:
                    del self._cache[key]
                if key in self._cache_timestamps:
                    del self._cache_timestamps[key]

            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

        except Exception as e:
            logger.warning(f"Error during cache cleanup: {str(e)}")

    async def _get_historical_trends(self, timeframe: str) -> Dict[str, Any]:
        """
        Get historical trends data
        This is a placeholder for future enhancement - could track metrics over time
        """
        # For now, return placeholder data
        # Future enhancement: implement time-series data storage and retrieval
        return {
            "note": "Historical trends not yet implemented",
            "compliance_trend": [],
            "drift_trend": [],
            "plan_creation_trend": [],
        }

    def clear_cache(self):
        """Clear all cached results - useful for testing or manual cache invalidation"""
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.info("Analytics cache cleared")
