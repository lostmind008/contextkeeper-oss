#!/bin/bash
# fix_cli_ports.sh - Fix port mismatch in CLI files from 5555 to 5556

echo "🔧 Fixing CLI port mismatch: 5555 → 5556"
echo ""

# List of files that need port fixes
FILES=(
    "sacred_cli_integration.sh"
    "v3 Approved Plan for AI Agent/sacred_cli_integration.sh"
    "analytics_dashboard.html"
    "v3 Approved Plan for AI Agent/analytics_dashboard.html"
    "Proposed_enhancments/enhanced_rag_cli.sh"
    "Proposed_enhancments/rag_mcp_server.js"
    "v3 Approved Plan for AI Agent/enhanced_mcp_server.js"
    "rag_agent.py"
    "rag_agent_v1_backup.py"
)

FIXED_COUNT=0
TOTAL_REPLACEMENTS=0

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        # Count how many 5555 references exist
        COUNT=$(grep -c "5555" "$file" 2>/dev/null || echo "0")
        
        if [ "$COUNT" -gt 0 ]; then
            echo "📁 $file: Found $COUNT references to fix"
            
            # Create backup
            cp "$file" "${file}.backup"
            
            # Replace all instances of 5555 with 5556
            sed -i '' 's/5555/5556/g' "$file"
            
            # Verify the changes
            NEW_COUNT=$(grep -c "5556" "$file" 2>/dev/null || echo "0")
            echo "   ✅ Replaced $COUNT instances, now has $NEW_COUNT references to 5556"
            
            FIXED_COUNT=$((FIXED_COUNT + 1))
            TOTAL_REPLACEMENTS=$((TOTAL_REPLACEMENTS + COUNT))
        else
            echo "📁 $file: No port 5555 references found ✅"
        fi
    else
        echo "📁 $file: File not found ⚠️"
    fi
    echo ""
done

echo "🎉 Port fix completed!"
echo "Files modified: $FIXED_COUNT"
echo "Total replacements: $TOTAL_REPLACEMENTS"
echo ""
echo "Backup files created with .backup extension"
echo "You can remove backups later with: rm *.backup */**.backup"