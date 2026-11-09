"""Simple CLI for interacting with RAGOrchestrator"""

import argparse
from src.core.rag_orchestrator import RAGOrchestrator


def main() -> None:
    parser = argparse.ArgumentParser(description="Query ContextKeeper")
    parser.add_argument("query", help="Question to ask")
    parser.add_argument("--project", dest="project", required=True, help="Project ID")
    args = parser.parse_args()

    orchestrator = RAGOrchestrator()
    result = orchestrator.coordinate_query(args.query, args.project)
    for item in result.get("results", []):
        print(f"- {item.get('content')}")


if __name__ == "__main__":
    main()
