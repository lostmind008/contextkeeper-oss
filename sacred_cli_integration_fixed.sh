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
    fi
}

# Sacred-aware morning briefing
sacred_briefing() {
    echo -e "${PURPLE}📜 Sacred Plans Status${NC}"
    
    # Get all projects with sacred plans
    PROJECTS=$(curl -s "http://localhost:5556/projects")
    
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