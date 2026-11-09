#!/bin/bash

echo "🔧 Applying CLI Port Fixes: 5555 → 5556"
echo "================================================"

# List of files to fix
declare -a FILES=(
    "sacred_cli_integration.sh"
    "v3 Approved Plan for AI Agent/sacred_cli_integration.sh"
    "analytics_dashboard.html"
    "v3 Approved Plan for AI Agent/analytics_dashboard.html"
    "Proposed_enhancments/enhanced_rag_cli.sh"
    "Proposed_enhancments/rag_mcp_server.js"
    "v3 Approved Plan for AI Agent/enhanced_mcp_server.js"
)

TOTAL_FIXED=0
TOTAL_REPLACEMENTS=0

# Function to fix a single file
fix_file() {
    local file="$1"
    
    if [ -f "$file" ]; then
        # Count existing references
        local count_5555=$(grep -c "5555" "$file" 2>/dev/null || echo "0")
        
        if [ "$count_5555" -gt 0 ]; then
            echo "📁 $file"
            echo "   Found $count_5555 references to port 5555"
            
            # Create backup
            cp "$file" "${file}.backup_$(date +%Y%m%d_%H%M%S)"
            
            # Apply fix using sed
            sed -i.tmp 's/5555/5556/g' "$file"
            rm "${file}.tmp" 2>/dev/null || true
            
            # Verify the fix
            local count_5556=$(grep -c "5556" "$file" 2>/dev/null || echo "0")
            echo "   ✅ Applied $count_5555 replacements, now has $count_5556 references to 5556"
            
            TOTAL_FIXED=$((TOTAL_FIXED + 1))
            TOTAL_REPLACEMENTS=$((TOTAL_REPLACEMENTS + count_5555))
        else
            echo "📁 $file - No port 5555 references found ✅"
        fi
    else
        echo "📁 $file - File not found ⚠️"
    fi
    echo ""
}

# Fix each file
for file in "${FILES[@]}"; do
    fix_file "$file"
done

# Also check Python files for default port parameters
echo "🐍 Checking Python files for default port parameters..."
for py_file in rag_agent.py rag_agent_v1_backup.py; do
    if [ -f "$py_file" ]; then
        # Look for port parameter defaults
        local py_5555_count=$(grep -c "port.*=.*5555" "$py_file" 2>/dev/null || echo "0")
        if [ "$py_5555_count" -gt 0 ]; then
            echo "📁 $py_file"
            echo "   Found $py_5555_count default port parameters set to 5555"
            cp "$py_file" "${py_file}.backup_$(date +%Y%m%d_%H%M%S)"
            sed -i.tmp 's/port.*=.*5555/port = 5556/g' "$py_file"
            rm "${py_file}.tmp" 2>/dev/null || true
            echo "   ✅ Updated default port parameters to 5556"
            TOTAL_FIXED=$((TOTAL_FIXED + 1))
            TOTAL_REPLACEMENTS=$((TOTAL_REPLACEMENTS + py_5555_count))
        else
            echo "📁 $py_file - No default port 5555 found ✅"
        fi
    fi
done

echo ""
echo "🎉 Port Fix Summary"
echo "==================="
echo "Files modified: $TOTAL_FIXED"
echo "Total port references updated: $TOTAL_REPLACEMENTS"
echo ""
echo "💾 Backup files created with timestamp suffixes"
echo "🧪 Ready for testing with port 5556"
echo ""

# Verify no 5555 references remain in critical files
echo "🔍 Final Verification - Checking for any remaining 5555 references..."
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        local remaining=$(grep -c "5555" "$file" 2>/dev/null || echo "0")
        if [ "$remaining" -gt 0 ]; then
            echo "⚠️  WARNING: $file still has $remaining references to port 5555"
        fi
    fi
done

echo ""
echo "✅ CLI Port Fix Complete - All files should now use port 5556"