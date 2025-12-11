#!/bin/bash
# scripts/evening-handoff.sh
# Enhanced evening handoff script for Agentic SDLC

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
RESET='\033[0m'
BOLD='\033[1m'

# Parse command line flags
SAVE_REPORT=false
SHOW_HELP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --save)
            SAVE_REPORT=true
            shift
            ;;
        --help)
            SHOW_HELP=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${RESET}"
            SHOW_HELP=true
            shift
            ;;
    esac
done

# Show help if requested
if [ "$SHOW_HELP" = true ]; then
    cat << 'EOF'
Evening Handoff Script - Agentic SDLC

Usage: ./evening-handoff.sh [OPTIONS]

Options:
  --save    Save handoff report to .sdlc/progress/handoff-{date}.md
  --help    Show this help message

Description:
  Generates an evening handoff report showing:
  - Session summary (commits, files changed, completed work)
  - Infrastructure status
  - Tomorrow's priorities from roadmap
  - Agent memory save placeholder

Examples:
  ./evening-handoff.sh           # Display report only
  ./evening-handoff.sh --save    # Display and save to file

EOF
    exit 0
fi

# Initialize report content
REPORT=""

# Helper function to add to report
add_to_report() {
    echo -e "$1"
    REPORT+="$1\n"
}

# Header
add_to_report "${BOLD}${CYAN}╔═══════════════════════════════════════════════════════════════╗${RESET}"
add_to_report "${BOLD}${CYAN}║              Evening Handoff - $(date +%Y-%m-%d)                    ║${RESET}"
add_to_report "${BOLD}${CYAN}╚═══════════════════════════════════════════════════════════════╝${RESET}"
add_to_report ""

# Session Summary Section
add_to_report "${BOLD}${BLUE}═══ Session Summary ═══${RESET}"
add_to_report ""

# Today's commits
COMMIT_COUNT=$(git log --since="8 hours ago" --oneline 2>/dev/null | wc -l | tr -d ' ')
if [ "$COMMIT_COUNT" -gt 0 ]; then
    add_to_report "${GREEN}✓ Commits today: ${COMMIT_COUNT}${RESET}"
    add_to_report ""
    git log --since="8 hours ago" --pretty=format:"  %h - %s (%an, %ar)" 2>/dev/null | while read line; do
        add_to_report "  ${line}"
    done
    add_to_report ""
else
    add_to_report "${YELLOW}○ No commits today${RESET}"
fi
add_to_report ""

# Files changed today
FILES_CHANGED=$(git diff --name-only HEAD@{8.hours.ago} 2>/dev/null | wc -l | tr -d ' ')
if [ "$FILES_CHANGED" -gt 0 ]; then
    add_to_report "${GREEN}✓ Files changed: ${FILES_CHANGED}${RESET}"
    git diff --name-only HEAD@{8.hours.ago} 2>/dev/null | head -10 | while read file; do
        add_to_report "  • ${file}"
    done
    if [ "$FILES_CHANGED" -gt 10 ]; then
        add_to_report "  ... and $((FILES_CHANGED - 10)) more"
    fi
else
    add_to_report "${YELLOW}○ No files changed${RESET}"
fi
add_to_report ""

# Completed work today
add_to_report "${BOLD}${BLUE}═══ Completed Today ═══${RESET}"
TODAY_DATE=$(date +%Y-%m-%d)
COMPLETED=$(grep -E "🟢.*${TODAY_DATE}" .sdlc/plans/roadmap.md 2>/dev/null)
if [ -n "$COMPLETED" ]; then
    add_to_report "${GREEN}✓ Work completed:${RESET}"
    echo "$COMPLETED" | while read line; do
        add_to_report "  ${line}"
    done
else
    add_to_report "${YELLOW}○ No work items completed today${RESET}"
fi
add_to_report ""

# Current work in progress
add_to_report "${BOLD}${BLUE}═══ Current Work (In Progress) ═══${RESET}"
IN_PROGRESS=$(grep -A3 "🟡" .sdlc/plans/roadmap.md 2>/dev/null)
if [ -n "$IN_PROGRESS" ]; then
    add_to_report "${YELLOW}⚠ In progress:${RESET}"
    echo "$IN_PROGRESS" | while read line; do
        add_to_report "  ${line}"
    done
else
    add_to_report "${GREEN}✓ Nothing in progress${RESET}"
fi
add_to_report ""

# Infrastructure Status Section
add_to_report "${BOLD}${BLUE}═══ Infrastructure Status ═══${RESET}"
add_to_report ""

# NATS status
if pgrep -f nats-server > /dev/null; then
    add_to_report "${GREEN}✓ NATS server running${RESET}"

    # Check pending work queue
    if nats stream ls > /dev/null 2>&1; then
        PENDING=$(nats stream info WORK --json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['state']['messages'])" 2>/dev/null)
        if [ -n "$PENDING" ]; then
            add_to_report "${CYAN}  └─ Work queue: ${PENDING} messages pending${RESET}"
        fi
    fi
else
    add_to_report "${RED}✗ NATS server stopped${RESET}"
fi

# Memory server status
if pgrep -f agent-memory > /dev/null; then
    add_to_report "${GREEN}✓ Agent memory server running${RESET}"
else
    add_to_report "${YELLOW}○ Agent memory server stopped${RESET}"
fi
add_to_report ""

# Tests Status
add_to_report "${BOLD}${BLUE}═══ Tests Status ═══${RESET}"
if [ -d "tests" ]; then
    if pytest tests/ -q --tb=no 2>/dev/null; then
        add_to_report "${GREEN}✓ All tests passing${RESET}"
    else
        add_to_report "${RED}✗ Some tests failing - review before tomorrow${RESET}"
    fi
else
    add_to_report "${YELLOW}○ No tests directory found${RESET}"
fi
add_to_report ""

# Tomorrow's Priorities Section
add_to_report "${BOLD}${BLUE}═══ Tomorrow's Priorities ═══${RESET}"
add_to_report ""

# Extract not-started items from roadmap
NOT_STARTED=$(grep -A3 "⚪" .sdlc/plans/roadmap.md 2>/dev/null | head -15)
if [ -n "$NOT_STARTED" ]; then
    add_to_report "${CYAN}Top priorities to start:${RESET}"
    echo "$NOT_STARTED" | while read line; do
        add_to_report "  ${line}"
    done
else
    add_to_report "${GREEN}✓ No pending work items${RESET}"
fi
add_to_report ""

# Extract blocked items
BLOCKED=$(grep -A3 "🔴" .sdlc/plans/roadmap.md 2>/dev/null)
if [ -n "$BLOCKED" ]; then
    add_to_report "${RED}⚠ Blocked items requiring attention:${RESET}"
    echo "$BLOCKED" | while read line; do
        add_to_report "  ${line}"
    done
    add_to_report ""
fi

# Agent Memory Save Placeholder
add_to_report "${BOLD}${BLUE}═══ Agent Memory Save ═══${RESET}"
add_to_report "${YELLOW}📝 Placeholder: Agent memory save functionality${RESET}"
add_to_report "   To save session learnings, use:"
add_to_report "   ${CYAN}store_memory(content=\"[summary]\", category=\"dev-infrastructure\", tags=[\"session\"])${RESET}"
add_to_report ""

# Footer
add_to_report "${BOLD}${CYAN}╔═══════════════════════════════════════════════════════════════╗${RESET}"
add_to_report "${BOLD}${CYAN}║              Handoff Complete - Rest Well! 🌙                 ║${RESET}"
add_to_report "${BOLD}${CYAN}╚═══════════════════════════════════════════════════════════════╝${RESET}"
add_to_report ""
add_to_report "${BOLD}Action items for tomorrow:${RESET}"
add_to_report "  ${GREEN}•${RESET} Run morning-review.sh to resume work"
add_to_report "  ${GREEN}•${RESET} Review any overnight agent activity"
add_to_report "  ${GREEN}•${RESET} Address blocked items if any"
add_to_report "  ${GREEN}•${RESET} Start next priority from roadmap"
add_to_report ""

# Save report if requested
if [ "$SAVE_REPORT" = true ]; then
    PROGRESS_DIR=".sdlc/progress"
    mkdir -p "$PROGRESS_DIR"

    REPORT_FILE="${PROGRESS_DIR}/handoff-$(date +%Y-%m-%d).md"

    # Strip color codes for markdown file
    echo -e "$REPORT" | sed -r "s/\x1B\[([0-9]{1,3}(;[0-9]{1,2})?)?[mGK]//g" > "$REPORT_FILE"

    echo -e "${GREEN}✓ Report saved to: ${REPORT_FILE}${RESET}"
    echo ""
fi
