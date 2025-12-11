#!/bin/bash
# scripts/morning-review.sh
# Enhanced daily morning review script for Agentic SDLC
# Features: Color output, project health score, agent memory recall, comprehensive checks

set -o pipefail

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Help flag
if [[ "$1" == "--help" || "$1" == "-h" ]]; then
    echo "Usage: ./morning-review.sh [OPTIONS]"
    echo ""
    echo "Enhanced morning review script with comprehensive status checks."
    echo ""
    echo "OPTIONS:"
    echo "  --help, -h     Show this help message"
    echo "  --no-color     Disable colored output"
    echo ""
    echo "FEATURES:"
    echo "  - Git activity summary (last 24h)"
    echo "  - Roadmap status with progress tracking"
    echo "  - Project health score calculation"
    echo "  - Agent memory recall (recent learnings)"
    echo "  - Test suite status"
    echo "  - Infrastructure health checks"
    echo "  - Color-coded output for quick scanning"
    echo ""
    exit 0
fi

# No color flag
if [[ "$1" == "--no-color" ]]; then
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    CYAN=''
    BOLD=''
    NC=''
fi

# Section header function
print_section() {
    echo ""
    echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}${BOLD}  $1${NC}"
    echo -e "${CYAN}${BOLD}═══════════════════════════════════════════════════════════${NC}"
}

# Success message
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Warning message
print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Error message
print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Info message
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Banner
echo ""
echo -e "${BOLD}${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${BLUE}║                   MORNING REVIEW                          ║${NC}"
echo -e "${BOLD}${BLUE}║            Agentic SDLC - $(date +"%Y-%m-%d %H:%M")             ║${NC}"
echo -e "${BOLD}${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Initialize health score components
health_score=0
health_max=0

# ============================================
# SECTION 1: Git Activity (last 24h)
# ============================================
print_section "Git Activity (Last 24 Hours)"

commit_count=$(git log --since="24 hours ago" --oneline 2>/dev/null | wc -l | tr -d ' ')
if [[ "$commit_count" -gt 0 ]]; then
    print_success "$commit_count commits in the last 24 hours"
    git log --since="24 hours ago" --oneline --color=always 2>/dev/null | head -5
    if [[ "$commit_count" -gt 5 ]]; then
        echo -e "${BLUE}... and $((commit_count - 5)) more${NC}"
    fi
    health_score=$((health_score + 10))
else
    print_warning "No commits in the last 24 hours"
fi
health_max=$((health_max + 10))

# ============================================
# SECTION 2: Roadmap Status
# ============================================
print_section "Roadmap Status"

if [[ -f ".sdlc/plans/roadmap.md" ]]; then
    print_success "Roadmap file found"

    # Count requirements by status
    not_started=$(grep -c "⚪" .sdlc/plans/roadmap.md 2>/dev/null || echo "0")
    in_progress=$(grep -c "🟡" .sdlc/plans/roadmap.md 2>/dev/null || echo "0")
    completed=$(grep -c "🟢" .sdlc/plans/roadmap.md 2>/dev/null || echo "0")
    blocked=$(grep -c "🔴" .sdlc/plans/roadmap.md 2>/dev/null || echo "0")

    total=$((not_started + in_progress + completed + blocked))

    if [[ "$total" -gt 0 ]]; then
        completion_rate=$(awk "BEGIN {printf \"%.1f\", ($completed / $total) * 100}")
        echo ""
        echo -e "${BOLD}Progress Summary:${NC}"
        echo -e "  🟢 Completed:    ${GREEN}$completed${NC} ($completion_rate%)"
        echo -e "  🟡 In Progress:  ${YELLOW}$in_progress${NC}"
        echo -e "  ⚪ Not Started:  $not_started"
        echo -e "  🔴 Blocked:      ${RED}$blocked${NC}"
        echo -e "  ${BOLD}Total:${NC}          $total requirements"

        # Add to health score based on completion and no blockers
        if [[ "$blocked" -eq 0 ]]; then
            health_score=$((health_score + 15))
        elif [[ "$blocked" -le 2 ]]; then
            health_score=$((health_score + 10))
        else
            health_score=$((health_score + 5))
        fi
    else
        print_warning "No requirements found in roadmap"
    fi
    health_max=$((health_max + 15))
else
    print_error "No roadmap found at .sdlc/plans/roadmap.md"
    health_max=$((health_max + 15))
fi

# ============================================
# SECTION 3: Current Work Focus
# ============================================
print_section "Current Work Focus"

if [[ -f ".sdlc/plans/roadmap.md" ]]; then
    in_progress_items=$(grep -E "🟡.*REQ-[0-9]+" .sdlc/plans/roadmap.md 2>/dev/null)

    if [[ -n "$in_progress_items" ]]; then
        echo ""
        echo -e "${YELLOW}${BOLD}In Progress:${NC}"
        echo "$in_progress_items" | head -5
    else
        print_info "No items currently in progress"
    fi

    blocked_items=$(grep -E "🔴.*REQ-[0-9]+" .sdlc/plans/roadmap.md 2>/dev/null)
    if [[ -n "$blocked_items" ]]; then
        echo ""
        echo -e "${RED}${BOLD}Blocked Items (Needs Attention):${NC}"
        echo "$blocked_items" | head -3
    fi
fi

# ============================================
# SECTION 4: Test Suite Status
# ============================================
print_section "Test Suite Status"

if command -v pytest &> /dev/null; then
    if [[ -d "tests" || -d ".sdlc/tests" ]]; then
        test_output=$(pytest tests/ .sdlc/tests/ -q --tb=no 2>&1 || true)
        test_exit=$?

        if [[ $test_exit -eq 0 ]]; then
            print_success "All tests passing"
            health_score=$((health_score + 20))
        elif [[ $test_exit -eq 5 ]]; then
            print_warning "No tests found"
            health_score=$((health_score + 10))
        else
            print_error "Some tests failing"
            echo "$test_output" | tail -5
            health_score=$((health_score + 5))
        fi
    else
        print_warning "No test directories found"
        health_score=$((health_score + 10))
    fi
else
    print_info "pytest not installed (tests skipped)"
    health_score=$((health_score + 10))
fi
health_max=$((health_max + 20))

# ============================================
# SECTION 5: Agent Memory Recall
# ============================================
print_section "Agent Memory (Recent Learnings)"

memory_file="$HOME/.agent-memory/memories.json"
if [[ -f "$memory_file" ]]; then
    print_success "Agent memory available"

    # Try to extract recent memories (last 3 days)
    recent_count=$(python3 -c "
import json, sys
from datetime import datetime, timedelta
try:
    with open('$memory_file') as f:
        data = json.load(f)
    memories = data.get('memories', [])
    recent = [m for m in memories if 'timestamp' in m]
    print(len(recent))
except:
    print(0)
" 2>/dev/null)

    if [[ "$recent_count" -gt 0 ]]; then
        print_info "Found $recent_count stored memories"
        echo ""
        echo -e "${BOLD}Recent learnings (sample):${NC}"
        python3 -c "
import json
try:
    with open('$memory_file') as f:
        data = json.load(f)
    memories = data.get('memories', [])
    for m in memories[-3:]:
        category = m.get('category', 'general')
        content = m.get('content', '')[:80]
        print(f'  • [{category}] {content}...')
except:
    pass
" 2>/dev/null
        health_score=$((health_score + 10))
    else
        print_info "No recent memories found"
        health_score=$((health_score + 5))
    fi
else
    print_info "Agent memory not initialized (MCP server starts on demand)"
    health_score=$((health_score + 5))
fi
health_max=$((health_max + 10))

# ============================================
# SECTION 6: Infrastructure Health
# ============================================
print_section "Infrastructure Health"

echo ""
echo -e "${BOLD}Services:${NC}"

# NATS Server
if nats stream ls > /dev/null 2>&1; then
    print_success "NATS Server: Running"
    work_messages=$(nats stream info WORK --json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['state']['messages'])" 2>/dev/null || echo "0")
    echo "    └─ WORK queue: $work_messages messages"
    health_score=$((health_score + 5))
else
    print_warning "NATS Server: Not running (optional)"
fi
health_max=$((health_max + 5))

# Agent Memory Server
if pgrep -f agent-memory > /dev/null; then
    print_success "Agent Memory Server: Running"
    health_score=$((health_score + 5))
else
    print_info "Agent Memory Server: Not running (starts on demand)"
    health_score=$((health_score + 5))
fi
health_max=$((health_max + 5))

# Git Status
if git diff --quiet && git diff --cached --quiet; then
    print_success "Working directory: Clean"
    health_score=$((health_score + 5))
else
    print_warning "Working directory: Uncommitted changes"
    uncommitted=$(git status --short | wc -l | tr -d ' ')
    echo "    └─ $uncommitted file(s) modified"
    health_score=$((health_score + 2))
fi
health_max=$((health_max + 5))

# ============================================
# SECTION 7: Skill Usage Statistics
# ============================================
print_section "Skill Usage Statistics"

skill_count=$(find Skills -name "SKILL.md" 2>/dev/null | wc -l | tr -d ' ')
if [[ "$skill_count" -gt 0 ]]; then
    print_success "$skill_count skills available"
    echo ""
    echo -e "${BOLD}Recently modified skills:${NC}"
    find Skills -name "SKILL.md" -mtime -7 2>/dev/null | head -5 | while read skill; do
        skill_name=$(basename $(dirname "$skill"))
        mod_date=$(stat -f "%Sm" -t "%Y-%m-%d" "$skill" 2>/dev/null || stat -c "%y" "$skill" 2>/dev/null | cut -d' ' -f1)
        echo "  • $skill_name (modified: $mod_date)"
    done
    health_score=$((health_score + 5))
else
    print_warning "No skills found"
fi
health_max=$((health_max + 5))

# ============================================
# SECTION 8: Project Health Score
# ============================================
print_section "Project Health Score"

echo ""
if [[ "$health_max" -gt 0 ]]; then
    health_percent=$(awk "BEGIN {printf \"%.0f\", ($health_score / $health_max) * 100}")

    # Color-code based on health
    if [[ "$health_percent" -ge 80 ]]; then
        health_color=$GREEN
        health_status="Excellent"
    elif [[ "$health_percent" -ge 60 ]]; then
        health_color=$YELLOW
        health_status="Good"
    elif [[ "$health_percent" -ge 40 ]]; then
        health_color=$YELLOW
        health_status="Fair"
    else
        health_color=$RED
        health_status="Needs Attention"
    fi

    echo -e "${BOLD}Overall Project Health:${NC} ${health_color}${health_percent}%${NC} - ${health_status}"
    echo -e "  Score: $health_score / $health_max"
    echo ""

    # Health bar visualization
    bar_length=50
    filled=$(awk "BEGIN {printf \"%.0f\", ($health_percent / 100) * $bar_length}")
    empty=$((bar_length - filled))

    printf "  ["
    printf "${health_color}"
    printf "%${filled}s" | tr ' ' '█'
    printf "${NC}"
    printf "%${empty}s" | tr ' ' '░'
    printf "]\n"
else
    print_warning "Unable to calculate health score"
fi

# ============================================
# SECTION 9: Recommendations
# ============================================
print_section "Recommendations"

echo ""
if [[ "$blocked" -gt 0 ]]; then
    echo -e "${YELLOW}►${NC} Address ${RED}$blocked blocked item(s)${NC} to unblock progress"
fi

if [[ "$in_progress" -eq 0 ]] && [[ "$not_started" -gt 0 ]]; then
    echo -e "${YELLOW}►${NC} Start a new requirement (${not_started} available)"
fi

if [[ $test_exit -ne 0 ]] && [[ $test_exit -ne 5 ]]; then
    echo -e "${YELLOW}►${NC} Fix failing tests before starting new work"
fi

if [[ "$commit_count" -eq 0 ]]; then
    echo -e "${YELLOW}►${NC} Consider committing any completed work"
fi

if [[ -z "$in_progress_items" ]] && [[ "$not_started" -gt 0 ]]; then
    echo -e "${BLUE}►${NC} Review roadmap and select next priority"
fi

# ============================================
# Footer
# ============================================
echo ""
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}Morning review complete!${NC} Have a productive day! 🚀"
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
