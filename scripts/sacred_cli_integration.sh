#!/bin/bash
# sacred_cli_extension.sh - Sacred layer commands for ContextKeeper
# Add to rag_cli_v2.sh or create as separate script

# Sacred plan management commands
handle_sacred() {
    check_agent
    case "$1" in
        create)
            shift
            PROJECT_ID="$1"
            TITLE="$2"
            PLAN_FILE="$3"

            if [ $# -lt 3 ]; then
                echo "Usage: rag sacred create <project_id> \"<title>\" <plan_file>"
                exit 1
            fi

            if [ ! -f "$PLAN_FILE" ]; then
                echo -e "${RED}Error: Plan file not found: $PLAN_FILE${NC}"
                exit 1
            fi

            echo -e "${BLUE}Creating sacred plan...${NC}"

            RESPONSE=$(curl -s -X POST "http://localhost:5556/sacred/plans" \
                -H "Content-Type: application/json" \
                -d "{
                    \"project_id\": \"$PROJECT_ID\",
                    \"title\": \"$TITLE\",
                    \"file_path\": \"$PLAN_FILE\"
                }")

            PLAN_ID=$(echo "$RESPONSE" | jq -r '.plan_id')
            VERIFICATION_CODE=$(echo "$RESPONSE" | jq -r '.verification_code')

            echo -e "${GREEN}✅ Sacred plan created${NC}"
            echo -e "Plan ID: ${CYAN}$PLAN_ID${NC}"
            echo -e "Verification Code: ${YELLOW}$VERIFICATION_CODE${NC}"
            echo -e "${YELLOW}⚠️  Save this verification code - you'll need it for approval${NC}"
            ;;

        approve)
            shift
            PLAN_ID="$1"

            if [ -z "$PLAN_ID" ]; then
                echo "Usage: rag sacred approve <plan_id>"
                exit 1
            fi

            # Interactive approval process
            echo -e "${YELLOW}🔐 Sacred Plan Approval Process${NC}"
            echo -e "${YELLOW}This requires 2-layer verification${NC}"
            echo ""

            # Show plan details
            PLAN_STATUS=$(curl -s "http://localhost:5556/sacred/plans/$PLAN_ID/status")
            echo -e "Plan Title: $(echo "$PLAN_STATUS" | jq -r '.title')"
            echo -e "Created: $(echo "$PLAN_STATUS" | jq -r '.created_at')"
            echo ""

            # Layer 1: Verification code
            read -p "Enter verification code: " VERIFICATION_CODE

            # Layer 2: Secondary verification
            echo -e "\n${YELLOW}Secondary Verification Required${NC}"
            read -s -p "Enter approval key: " APPROVAL_KEY
            echo ""

            # Get approver name
            read -p "Your name (for audit): " APPROVER

            # Confirm
            echo -e "\n${YELLOW}⚠️  This action will lock the plan permanently.${NC}"
            read -p "Are you sure you want to approve? (yes/NO): " CONFIRM

            if [ "$CONFIRM" != "yes" ]; then
                echo -e "${BLUE}Approval cancelled${NC}"
                exit 0
            fi

            # Submit approval
            RESPONSE=$(curl -s -X POST "http://localhost:5556/sacred/plans/$PLAN_ID/approve" \
                -H "Content-Type: application/json" \
                -d "{
                    \"approver\": \"$APPROVER\",
                    \"verification_code\": \"$VERIFICATION_CODE\",
                    \"secondary_verification\": \"$APPROVAL_KEY\"
                }")

            SUCCESS=$(echo "$RESPONSE" | jq -r '.success')
            MESSAGE=$(echo "$RESPONSE" | jq -r '.message')

            if [ "$SUCCESS" = "true" ]; then
                echo -e "${GREEN}✅ $MESSAGE${NC}"
                echo -e "${GREEN}Plan is now locked and immutable${NC}"
            else
                echo -e "${RED}❌ Approval failed: $MESSAGE${NC}"
                exit 1
            fi
            ;;

        list)
            shift
            PROJECT_ID="$1"
            STATUS_FILTER="${2:-all}"

            echo -e "${BLUE}📜 Sacred Plans${NC}"

            URL="http://localhost:5556/sacred/plans"
            if [ -n "$PROJECT_ID" ]; then
                URL="$URL?project_id=$PROJECT_ID"
            fi
            if [ "$STATUS_FILTER" != "all" ]; then
                URL="$URL&status=$STATUS_FILTER"
            fi

            PLANS=$(curl -s "$URL")

            echo "$PLANS" | jq -r '.[] |
                "\(.status) | \(.plan_id) | \(.title) | \(.created_at) | \(.approved_at // "N/A")"' |
            while IFS='|' read -r status plan_id title created approved; do
                # Status icons
                case "$(echo "$status" | xargs)" in
                    "draft") STATUS_ICON="📝" ;;
                    "approved") STATUS_ICON="✅" ;;
                    "locked") STATUS_ICON="🔒" ;;
                    "superseded") STATUS_ICON="🔄" ;;
                    *) STATUS_ICON="❓" ;;
                esac

                echo -e "${STATUS_ICON} $(echo "$plan_id" | xargs)"
                echo -e "   Title: $(echo "$title" | xargs)"
                echo -e "   Created: $(echo "$created" | xargs)"
                if [ "$(echo "$approved" | xargs)" != "N/A" ]; then
                    echo -e "   Approved: $(echo "$approved" | xargs)"
                fi
                echo ""
            done
            ;;

        query)
            shift
            PROJECT_ID="$1"
            shift
            QUERY="$*"

            if [ -z "$PROJECT_ID" ] || [ -z "$QUERY" ]; then
                echo "Usage: rag sacred query <project_id> <query>"
                exit 1
            fi

            echo -e "${BLUE}🔍 Searching sacred plans...${NC}"

            RESPONSE=$(curl -s -X POST "http://localhost:5556/sacred/query" \
                -H "Content-Type: application/json" \
                -d "{
                    \"project_id\": \"$PROJECT_ID\",
                    \"query\": \"$QUERY\"
                }")

            CONTEXT=$(echo "$RESPONSE" | jq -r '.context')
            PLAN_COUNT=$(echo "$RESPONSE" | jq -r '.plan_count')

            echo -e "${GREEN}Found $PLAN_COUNT relevant plan(s)${NC}\n"
            echo "$CONTEXT"
            ;;

        drift)
            shift
            PROJECT_ID="$1"
            HOURS="${2:-24}"

            if [ -z "$PROJECT_ID" ]; then
                echo "Usage: rag sacred drift <project_id> [hours]"
                exit 1
            fi

            echo -e "${BLUE}🎯 Analyzing drift from sacred plans...${NC}"

            RESPONSE=$(curl -s "http://localhost:5556/projects/$PROJECT_ID/sacred-drift?hours=$HOURS")

            ALIGNMENT=$(echo "$RESPONSE" | jq -r '.analysis.alignment_score')
            STATUS=$(echo "$RESPONSE" | jq -r '.analysis.status')
            VIOLATIONS=$(echo "$RESPONSE" | jq -r '.analysis.violation_count')

            # Status icon
            case "$STATUS" in
                "aligned") STATUS_ICON="✅" ;;
                "minor_drift") STATUS_ICON="⚠️" ;;
                "major_drift") STATUS_ICON="🟠" ;;
                "critical_violation") STATUS_ICON="🔴" ;;
                *) STATUS_ICON="❓" ;;
            esac

            echo -e "\n${STATUS_ICON} Status: $STATUS"
            echo -e "Alignment Score: $(printf "%.1f%%" $(echo "$ALIGNMENT * 100" | bc))"
            echo -e "Violations: $VIOLATIONS"

            # Show plan adherence
            echo -e "\nPlan Adherence:"
            echo "$RESPONSE" | jq -r '.analysis.plan_adherence | to_entries | .[] |
                "\(.key): \(.value)"' | while read line; do
                PLAN_ID=$(echo "$line" | cut -d: -f1)
                SCORE=$(echo "$line" | cut -d: -f2 | xargs)
                PERCENTAGE=$(printf "%.1f%%" $(echo "$SCORE * 100" | bc))

                if (( $(echo "$SCORE >= 0.8" | bc -l) )); then
                    ICON="✅"
                elif (( $(echo "$SCORE >= 0.5" | bc -l) )); then
                    ICON="⚠️"
                else
                    ICON="🔴"
                fi

                echo -e "  $ICON $PLAN_ID: $PERCENTAGE"
            done

            # Show recommendations
            echo -e "\nRecommendations:"
            echo "$RESPONSE" | jq -r '.analysis.recommendations[]' | while read rec; do
                echo -e "  • $rec"
            done

            # Option to see full report
            echo ""
            read -p "View full report? (y/N): " VIEW_REPORT
            if [ "$VIEW_REPORT" = "y" ]; then
                echo "$RESPONSE" | jq -r '.report'
            fi
            ;;

        lock)
            shift
            PLAN_ID="$1"

            if [ -z "$PLAN_ID" ]; then
                echo "Usage: rag sacred lock <plan_id>"
                exit 1
            fi

            echo -e "${YELLOW}⚠️  This will permanently lock the plan${NC}"
            read -p "Are you sure? (yes/NO): " CONFIRM

            if [ "$CONFIRM" != "yes" ]; then
                echo -e "${BLUE}Lock cancelled${NC}"
                exit 0
            fi

            RESPONSE=$(curl -s -X POST "http://localhost:5556/sacred/plans/$PLAN_ID/lock")
            SUCCESS=$(echo "$RESPONSE" | jq -r '.success')

            if [ "$SUCCESS" = "true" ]; then
                echo -e "${GREEN}✅ Plan locked successfully${NC}"
            else
                echo -e "${RED}❌ Failed to lock plan${NC}"
            fi
            ;;

        supersede)
            shift
            OLD_PLAN="$1"
            NEW_PLAN="$2"

            if [ -z "$OLD_PLAN" ] || [ -z "$NEW_PLAN" ]; then
                echo "Usage: rag sacred supersede <old_plan_id> <new_plan_id>"
                exit 1
            fi

            echo -e "${BLUE}Superseding plan $OLD_PLAN with $NEW_PLAN${NC}"

            RESPONSE=$(curl -s -X POST "http://localhost:5556/sacred/plans/supersede" \
                -H "Content-Type: application/json" \
                -d "{
                    \"old_plan_id\": \"$OLD_PLAN\",
                    \"new_plan_id\": \"$NEW_PLAN\"
                }")

            SUCCESS=$(echo "$RESPONSE" | jq -r '.success')

            if [ "$SUCCESS" = "true" ]; then
                echo -e "${GREEN}✅ Plan superseded successfully${NC}"
            else
                echo -e "${RED}❌ Failed to supersede plan${NC}"
            fi
            ;;

        *)
            echo "Sacred Plan Commands:"
            echo "  rag sacred create <project_id> \"<title>\" <file>  Create new plan"
            echo "  rag sacred approve <plan_id>                       Approve with 2FA"
            echo "  rag sacred list [project_id] [status]              List plans"
            echo "  rag sacred query <project_id> <query>              Search plans"
            echo "  rag sacred drift <project_id> [hours]              Check drift"
            echo "  rag sacred lock <plan_id>                          Lock approved plan"
            echo "  rag sacred supersede <old_id> <new_id>             Replace plan"
            echo ""
            echo "Status values: draft, approved, locked, superseded"
            ;;
    esac
}

# Add to main command handling in rag_cli_v2.sh:
# sacred|s)
#     shift
#     handle_sacred "$@"
#     ;;

# Also add these helper functions
check_sacred_before_action() {
    # Function to check sacred plans before major actions
    PROJECT_ID="$1"
    ACTION="$2"
    
    # Quick drift check
    DRIFT_CHECK=$(curl -s "http://localhost:5556/projects/$PROJECT_ID/sacred-drift?hours=1")
    STATUS=$(echo "$DRIFT_CHECK" | jq -r '.analysis.status')
    
<<<<<<< HEAD:scripts/sacred_cli_integration.sh
    if [ ! -f "$file_path" ]; then
        echo "Error: File not found: $file_path"
        return 1
    fi
    
    echo "Creating sacred plan..."
    echo "Project: $project_id"
    echo "Title: $title"
    echo "File: $file_path"
    
    # Make API call to create sacred plan
    response=$(curl -s -X POST http://localhost:5556/sacred/plans \
        -H "Content-Type: application/json" \
        -d "{
            \"project_id\": \"$project_id\",
            \"title\": \"$title\",
            \"file_path\": \"$file_path\"
        }")
    
    # Parse response
    plan_id=$(echo "$response" | jq -r '.plan_id')
    verification_code=$(echo "$response" | jq -r '.verification_code')
    
    if [ "$plan_id" != "null" ]; then
        echo ""
        echo "✅ Sacred plan created"
        echo "Plan ID: $plan_id"
        echo "Verification Code: $verification_code"
        echo ""
        echo "⚠️  Save this verification code - you'll need it for approval"
    else
        echo "❌ Failed to create sacred plan"
        echo "$response" | jq '.'
=======
    if [ "$STATUS" = "critical_violation" ]; then
        echo -e "${RED}⚠️  WARNING: Critical sacred plan violations detected!${NC}"
        echo -e "${RED}Action '$ACTION' may violate approved plans.${NC}"
        read -p "Continue anyway? (yes/NO): " CONTINUE
        if [ "$CONTINUE" != "yes" ]; then
            echo -e "${BLUE}Action cancelled to preserve sacred plan integrity${NC}"
            exit 1
        fi
    elif [ "$STATUS" = "major_drift" ]; then
        echo -e "${YELLOW}⚠️  Caution: Significant drift from sacred plans detected${NC}"
>>>>>>> v3-upgrade:sacred_cli_integration.sh
    fi
}

# Sacred-aware morning briefing
sacred_briefing() {
    echo -e "${PURPLE}📜 Sacred Plans Status${NC}"
    
    # Get all projects with sacred plans
    PROJECTS=$(curl -s "http://localhost:5556/projects")
    
<<<<<<< HEAD:scripts/sacred_cli_integration.sh
    # Prompt for verification code
    echo -n "Enter verification code: "
    read -r verification_code
    
    # Prompt for secondary verification (environment key)
    echo -n "Enter approval key: "
    read -rs approval_key
    echo ""
    
    # Get approver name
    approver=$(whoami)
    
    echo "Approving sacred plan..."
    
    # Make API call to approve
    response=$(curl -s -X POST "http://localhost:5556/sacred/plans/$plan_id/approve" \
        -H "Content-Type: application/json" \
        -d "{
            \"approver\": \"$approver\",
            \"verification_code\": \"$verification_code\",
            \"secondary_verification\": \"$approval_key\"
        }")
    
    # Check response
    status=$(echo "$response" | jq -r '.status')
    
    if [ "$status" = "approved" ]; then
        echo "✅ Sacred plan approved and locked"
        echo "This plan is now immutable and will guide development"
    else
        echo "❌ Failed to approve sacred plan"
        echo "$response" | jq '.'
    fi
}

# Check drift against sacred plans
check_sacred_drift() {
    local project_id=$1
    local detailed=${2:-""}
    
    if [ -z "$project_id" ]; then
        echo "Usage: sacred drift <project_id> [--detailed]"
        return 1
    fi
    
    echo "Analyzing sacred drift for project: $project_id"
    
    # Make API call
    response=$(curl -s "http://localhost:5556/sacred/drift/$project_id")
    
    # Parse response
    status=$(echo "$response" | jq -r '.status')
    alignment=$(echo "$response" | jq -r '.alignment_score')
    violations=$(echo "$response" | jq -r '.violations | length')
    
    # Display results with color coding
    case "$status" in
        "aligned")
            echo "✅ Status: aligned"
            ;;
        "minor_drift")
            echo "⚠️  Status: minor_drift"
            ;;
        "moderate_drift")
            echo "🟠 Status: moderate_drift"
            ;;
        "critical_violation")
            echo "🔴 Status: critical_violation"
            ;;
    esac
    
    echo "Alignment Score: ${alignment}%"
    echo "Violations: $violations"
    
    if [ "$violations" -gt 0 ]; then
        echo ""
        echo "Plan Adherence:"
        echo "$response" | jq -r '.sacred_plans_checked[] | "  \(.status_icon) \(.plan_id): \(.alignment)%"'
    fi
    
    # Show recommendations
    echo ""
    echo "Recommendations:"
    echo "$response" | jq -r '.recommendations[] | "  • \(.)"'
    
    # Detailed view if requested
    if [ "$detailed" = "--detailed" ]; then
        echo ""
        echo "Detailed Violations:"
        echo "$response" | jq '.violations'
    fi
}

# List sacred plans for a project
list_sacred_plans() {
    local project_id=$1
    
    if [ -z "$project_id" ]; then
        echo "Usage: sacred list <project_id>"
        return 1
    fi
    
    echo "Sacred Plans for project: $project_id"
    echo ""
    
    # Make API call
    response=$(curl -s "http://localhost:5556/sacred/plans?project_id=$project_id")
    
    # Display plans
    echo "$response" | jq -r '.plans[] | "\(.status_icon) [\(.plan_id)] \(.title) - \(.status) (created: \(.created_at))"'
}

# Query sacred plans
query_sacred_plans() {
    local project_id=$1
    local query=$2
    
    if [ -z "$project_id" ] || [ -z "$query" ]; then
        echo "Usage: sacred query <project_id> <query>"
        return 1
    fi
    
    echo "Querying sacred plans..."
    
    # Make API call
    response=$(curl -s -X POST http://localhost:5556/sacred/query \
        -H "Content-Type: application/json" \
        -d "{
            \"project_id\": \"$project_id\",
            \"query\": \"$query\"
        }")
    
    # Display results
    echo "$response" | jq '.'
}

# Verify sacred database integrity
verify_sacred_integrity() {
    echo "Verifying sacred database integrity..."
    
    # Make API call
    response=$(curl -s http://localhost:5556/sacred/verify)
    
    # Display results
    status=$(echo "$response" | jq -r '.status')
    
    if [ "$status" = "healthy" ]; then
        echo "✅ Sacred database integrity verified"
        echo "$response" | jq '.'
    else
        echo "❌ Sacred database integrity check failed"
        echo "$response" | jq '.'
    fi
}

# Export sacred plans
export_sacred_plans() {
    local project_id=$1
    local format=${2:-"json"}
    
    if [ -z "$project_id" ]; then
        echo "Usage: sacred export <project_id> [--format markdown|json]"
        return 1
    fi
    
    echo "Exporting sacred plans for project: $project_id"
    
    # Make API call
    curl -s "http://localhost:5556/sacred/export?project_id=$project_id&format=$format"
}

# Helper function to display sacred status icons
get_sacred_status_icon() {
    local status=$1
    
    case "$status" in
        "draft")
            echo "📝"
            ;;
        "pending_approval")
            echo "⏳"
            ;;
        "approved")
            echo "🔒"
            ;;
        "superseded")
            echo "🔄"
            ;;
        "archived")
            echo "📦"
            ;;
        *)
            echo "❓"
            ;;
    esac
}
=======
    echo "$PROJECTS" | jq -r '.projects[]' | while read -r project; do
        PROJECT_ID=$(echo "$project" | jq -r '.id')
        PROJECT_NAME=$(echo "$project" | jq -r '.name')

        # Check for sacred plans
        SACRED_COUNT=$(curl -s "http://localhost:5556/sacred/plans?project_id=$PROJECT_ID" | jq '. | length')

        if [ "$SACRED_COUNT" -gt 0 ]; then
            echo -e "\n${CYAN}$PROJECT_NAME${NC}"

            # Get drift status
            DRIFT=$(curl -s "http://localhost:5556/projects/$PROJECT_ID/sacred-drift?hours=24")
            ALIGNMENT=$(echo "$DRIFT" | jq -r '.analysis.alignment_score')
            STATUS=$(echo "$DRIFT" | jq -r '.analysis.status')

            # Format alignment
            ALIGNMENT_PCT=$(printf "%.0f%%" $(echo "$ALIGNMENT * 100" | bc))

            case "$STATUS" in
                "aligned") STATUS_COLOR="${GREEN}" ;;
                "minor_drift") STATUS_COLOR="${YELLOW}" ;;
                *) STATUS_COLOR="${RED}" ;;
            esac

            echo -e "  Sacred Plans: $SACRED_COUNT"
            echo -e "  Alignment: ${STATUS_COLOR}$ALIGNMENT_PCT${NC} ($STATUS)"

            # Show top recommendation
            TOP_REC=$(echo "$DRIFT" | jq -r '.analysis.recommendations[0] // "Stay on track!"')
            echo -e "  💡 $TOP_REC"
        fi
    done
}

# Export functions for use in main script
export -f handle_sacred
export -f check_sacred_before_action
export -f sacred_briefing
>>>>>>> v3-upgrade:sacred_cli_integration.sh
