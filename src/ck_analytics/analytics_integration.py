#!/usr/bin/env python3
"""
# GOVERNANCE HEADER - SKELETON FIRST DEVELOPMENT
# File: /path/to/contextkeeper/src/ck_analytics/analytics_integration.py
# Project: ContextKeeper v3.0
# Purpose: Analytics endpoints and metrics calculation for dashboard
# Dependencies: flask, analytics module, enhanced_drift_sacred
# Dependents: rag_agent.py API endpoints, analytics_dashboard_live.html
# Created: 2025-08-04
# Modified: 2025-08-05

## PLANNING CONTEXT EMBEDDED
This module provides analytics integration for the dashboard:
- Sacred plan metrics and adherence scores
- Drift analysis visualization data
- Project activity aggregation
- Time-series metrics for charts
- Performance and health indicators

## ARCHITECTURAL DECISIONS
1. RESTful endpoints for dashboard consumption
2. Real-time metric calculation (no caching yet)
3. Time-based filtering with flexible windows
4. Project-specific and cross-project analytics
5. Integration with sacred drift detection

## TODO FROM PLANNING
- [ ] Add caching layer for expensive calculations
- [ ] Implement metric export functionality
- [ ] Add custom metric definitions
- [ ] Create alerting thresholds

Analytics Integration for ContextKeeper RAG Agent
Adds sacred metrics endpoints to the Flask application
"""

import logging
import asyncio
from flask import request, jsonify

from src.ck_analytics.sacred_metrics import SacredMetricsCalculator
from src.ck_analytics.analytics_service import AnalyticsService
from src.sacred.enhanced_drift_sacred import SacredDriftDetector

logger = logging.getLogger(__name__)


def add_analytics_endpoints(app, agent):
    """
    Add analytics endpoints to the Flask application

    Args:
        app: Flask application instance
        agent: RAG agent instance with sacred integration
    """

    @app.route("/analytics/sacred", methods=["GET"])
    def sacred_analytics():
        """Get comprehensive sacred plan analytics"""
        try:
            timeframe = request.args.get("timeframe", "7d")
            project_filter = request.args.get("project_filter")
            include_history = (
                request.args.get("include_history", "false").lower() == "true"
            )

            # Initialize analytics service
            drift_detector = SacredDriftDetector(
                agent, agent.sacred_integration.sacred_manager
            )

            metrics_calculator = SacredMetricsCalculator(
                agent.sacred_integration.sacred_manager,
                drift_detector,
                agent.project_manager,
            )

            analytics_service = AnalyticsService(metrics_calculator)

            # Run async analytics calculation
            result = asyncio.run(
                analytics_service.get_sacred_analytics(
                    timeframe=timeframe,
                    project_filter=project_filter,
                    include_history=include_history,
                )
            )

            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in sacred analytics endpoint: {str(e)}", exc_info=True)
            return (
                jsonify({"error": f"Failed to calculate sacred analytics: {str(e)}"}),
                500,
            )

    @app.route("/analytics/sacred/health", methods=["GET"])
    def sacred_analytics_health():
        """Health check for sacred analytics system"""
        try:
            drift_detector = SacredDriftDetector(
                agent, agent.sacred_integration.sacred_manager
            )

            metrics_calculator = SacredMetricsCalculator(
                agent.sacred_integration.sacred_manager,
                drift_detector,
                agent.project_manager,
            )

            analytics_service = AnalyticsService(metrics_calculator)

            # Run async health check
            result = asyncio.run(analytics_service.get_sacred_health_check())

            return jsonify(result)
        except Exception as e:
            logger.error(
                f"Error in sacred analytics health check: {str(e)}", exc_info=True
            )
            return (
                jsonify({"error": f"Failed to check analytics health: {str(e)}"}),
                500,
            )

    @app.route("/analytics/sacred/project/<project_id>", methods=["GET"])
    def project_sacred_analytics(project_id):
        """Get detailed sacred analytics for a specific project"""
        try:
            timeframe = request.args.get("timeframe", "7d")

            drift_detector = SacredDriftDetector(
                agent, agent.sacred_integration.sacred_manager
            )

            metrics_calculator = SacredMetricsCalculator(
                agent.sacred_integration.sacred_manager,
                drift_detector,
                agent.project_manager,
            )

            analytics_service = AnalyticsService(metrics_calculator)

            # Run async project analytics
            result = asyncio.run(
                analytics_service.get_project_detailed_analytics(
                    project_id=project_id,
                    timeframe=timeframe,
                )
            )

            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in project sacred analytics: {str(e)}", exc_info=True)
            return jsonify({"error": f"Failed to get project analytics: {str(e)}"}), 500

    @app.route("/analytics/sacred/clear-cache", methods=["POST"])
    def clear_analytics_cache():
        """Clear analytics cache - useful for development and testing"""
        try:
            drift_detector = SacredDriftDetector(
                agent, agent.sacred_integration.sacred_manager
            )

            metrics_calculator = SacredMetricsCalculator(
                agent.sacred_integration.sacred_manager,
                drift_detector,
                agent.project_manager,
            )

            analytics_service = AnalyticsService(metrics_calculator)
            analytics_service.clear_cache()

            return jsonify(
                {"status": "success", "message": "Analytics cache cleared successfully"}
            )
        except Exception as e:
            logger.error(f"Error clearing analytics cache: {str(e)}", exc_info=True)
            return jsonify({"error": f"Failed to clear cache: {str(e)}"}), 500

    logger.info("Sacred analytics endpoints added successfully")


def integrate_analytics_with_rag_agent():
    """Helper to attach analytics endpoints to rag_agent.py"""

    def decorator(rag_agent_class):
        original_setup_routes = rag_agent_class._setup_routes

        def enhanced_setup_routes(self):
            # Call original setup_routes
            original_setup_routes(self)

            # Add analytics endpoints
            add_analytics_endpoints(self.app, self.agent)

            logger.info("Analytics endpoints integrated with RAG agent")

        rag_agent_class._setup_routes = enhanced_setup_routes
        return rag_agent_class

    return decorator
