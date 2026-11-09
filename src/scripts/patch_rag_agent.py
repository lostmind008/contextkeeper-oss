#!/usr/bin/env python3
"""
Patch script to add analytics integration to rag_agent.py
"""


def patch_rag_agent():
    """Add analytics integration to rag_agent.py"""

    # Read the current rag_agent.py
    with open("rag_agent.py", "r") as f:
        content = f.read()

    # Check if already patched
    if (
        "from ck_analytics.analytics_integration import add_analytics_endpoints"
        in content
    ):
        print("rag_agent.py already patched with analytics integration!")
        return

    # Add the import after the enhanced_drift_sacred import
    import_marker = "from enhanced_drift_sacred import SacredDriftDetector, add_sacred_drift_endpoint"

    if import_marker in content:
        analytics_import = (
            "\nfrom ck_analytics.analytics_integration import add_analytics_endpoints"
        )
        content = content.replace(import_marker, import_marker + analytics_import)
        print("✓ Added analytics import")
    else:
        print("✗ Could not find enhanced_drift_sacred import marker")
        return

    # Add the analytics endpoint call in _setup_routes method
    # Find the line right before the final route (usually right before the run method)
    marker = "            return jsonify(briefing)"

    if marker in content:
        analytics_call = """

        # Add Sacred Analytics endpoints
        add_analytics_endpoints(self.app, self.agent)"""

        content = content.replace(marker, marker + analytics_call)
        print("✓ Added analytics endpoint integration")
    else:
        print("✗ Could not find briefing return marker")
        return

    # Write the patched content back
    with open("rag_agent.py", "w") as f:
        f.write(content)

    print("✓ rag_agent.py successfully patched with analytics integration!")
    print("\nNew endpoints available:")
    print("  GET  /analytics/sacred")
    print("  GET  /analytics/sacred/health")
    print("  GET  /analytics/sacred/project/<project_id>")
    print("  POST /analytics/sacred/clear-cache")


if __name__ == "__main__":
    patch_rag_agent()
