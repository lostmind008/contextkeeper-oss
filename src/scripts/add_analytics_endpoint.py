#!/usr/bin/env python3
"""
Script to add analytics endpoint to rag_agent.py
"""


def add_analytics_to_rag_agent():
    """Add analytics import and endpoint to rag_agent.py"""

    # Read the original file
    with open("rag_agent.py", "r") as f:
        lines = f.readlines()

    # Add import after the enhanced_drift_sacred import (line 52)
    analytics_import = (
        "from ck_analytics import SacredMetricsCalculator, AnalyticsService\n"
    )

    # Find the line with enhanced_drift_sacred import
    for i, line in enumerate(lines):
        if "from enhanced_drift_sacred import" in line:
            lines.insert(i + 1, analytics_import)
            break

    # Add analytics endpoint before the final return jsonify(briefing) (around line 1607)
    analytics_endpoint = '''
        @self.app.route('/analytics/sacred', methods=['GET'])
        def sacred_analytics():
            """Get comprehensive sacred plan analytics"""
            try:
                timeframe = request.args.get('timeframe', '7d')
                project_filter = request.args.get('project_filter')
                include_history = request.args.get('include_history', 'false').lower() == 'true'

                # Initialize analytics service
                from enhanced_drift_sacred import SacredDriftDetector
                drift_detector = SacredDriftDetector(
                    self.agent,
                    self.agent.sacred_integration.sacred_manager
                )

                metrics_calculator = SacredMetricsCalculator(
                    self.agent.sacred_integration.sacred_manager,
                    drift_detector,
                    self.agent.project_manager
                )

                analytics_service = AnalyticsService(metrics_calculator)

                result = self._run_async(analytics_service.get_sacred_analytics(
                    timeframe=timeframe,
                    project_filter=project_filter,
                    include_history=include_history
                ))

                return jsonify(result)
            except Exception as e:
                logger.error(f"Error in sacred analytics endpoint: {str(e)}", exc_info=True)
                return jsonify({'error': f'Failed to calculate sacred analytics: {str(e)}'}), 500

        @self.app.route('/analytics/sacred/health', methods=['GET'])
        def sacred_analytics_health():
            """Health check for sacred analytics system"""
            try:
                from enhanced_drift_sacred import SacredDriftDetector
                drift_detector = SacredDriftDetector(
                    self.agent,
                    self.agent.sacred_integration.sacred_manager
                )

                metrics_calculator = SacredMetricsCalculator(
                    self.agent.sacred_integration.sacred_manager,
                    drift_detector,
                    self.agent.project_manager
                )

                analytics_service = AnalyticsService(metrics_calculator)

                result = self._run_async(analytics_service.get_sacred_health_check())
                return jsonify(result)
            except Exception as e:
                logger.error(f"Error in sacred analytics health check: {str(e)}", exc_info=True)
                return jsonify({'error': f'Failed to check analytics health: {str(e)}'}), 500

        @self.app.route('/analytics/sacred/project/<project_id>', methods=['GET'])
        def project_sacred_analytics(project_id):
            """Get detailed sacred analytics for a specific project"""
            try:
                timeframe = request.args.get('timeframe', '7d')

                from enhanced_drift_sacred import SacredDriftDetector
                drift_detector = SacredDriftDetector(
                    self.agent,
                    self.agent.sacred_integration.sacred_manager
                )

                metrics_calculator = SacredMetricsCalculator(
                    self.agent.sacred_integration.sacred_manager,
                    drift_detector,
                    self.agent.project_manager
                )

                analytics_service = AnalyticsService(metrics_calculator)

                result = self._run_async(analytics_service.get_project_detailed_analytics(
                    project_id=project_id,
                    timeframe=timeframe
                ))

                return jsonify(result)
            except Exception as e:
                logger.error(f"Error in project sacred analytics: {str(e)}", exc_info=True)
                return jsonify({'error': f'Failed to get project analytics: {str(e)}'}), 500

'''

    # Find the line with "return jsonify(briefing)" and insert before it
    for i, line in enumerate(lines):
        if "return jsonify(briefing)" in line:
            # Insert the analytics endpoint before this line
            lines.insert(i, analytics_endpoint)
            break

    # Write the modified content back to the file
    with open("rag_agent.py", "w") as f:
        f.writelines(lines)

    print("Analytics endpoint added to rag_agent.py successfully!")


if __name__ == "__main__":
    add_analytics_to_rag_agent()
