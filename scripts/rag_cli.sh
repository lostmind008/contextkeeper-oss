#!/bin/bash
# rag_cli.sh - Wrapper for ContextKeeper v3.0 Sacred Layer
# This script now delegates to the enhanced v2 CLI
# Make executable: chmod +x rag_cli.sh

# Delegate to v2 CLI
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
exec "$DIR/rag_cli_v2.sh" "$@"