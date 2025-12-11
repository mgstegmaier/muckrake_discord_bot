#!/bin/bash
# scripts/weekly-refactor.sh
# Weekly refactor ritual script for Agentic SDLC
# Orchestrates pattern detection, metrics reporting, and archiving

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Default flags
DRY_RUN=false
ARCHIVE_ONLY=false
SKIP_PATTERNS=false
SKIP_METRICS=false
SKIP_ARCHIVE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            echo "Weekly Refactor Ritual Script"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --help, -h           Show this help message"
            echo "  --dry-run            Preview actions without executing"
            echo "  --archive-only       Only archive completed work (skip patterns and metrics)"
            echo "  --skip-patterns      Skip pattern detection checks"
            echo "  --skip-metrics       Skip metrics report generation"
            echo "  --skip-archive       Skip archiving completed work"
            echo ""
            echo "This script orchestrates the weekly refactor workflow:"
            echo "  1. Check for pattern detection tests"
            echo "  2. Generate weekly metrics report"
            echo "  3. Archive completed work from the week"
            echo "  4. Update agent memory (placeholder)"
            echo ""
            echo "Examples:"
            echo "  $0                      # Run full weekly refactor"
            echo "  $0 --dry-run            # Preview what would happen"
            echo "  $0 --archive-only       # Only archive completed work"
            echo "  $0 --skip-patterns      # Skip pattern detection"
            exit 0
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --archive-only)
            ARCHIVE_ONLY=true
            SKIP_PATTERNS=true
            SKIP_METRICS=true
            shift
            ;;
        --skip-patterns)
            SKIP_PATTERNS=true
            shift
            ;;
        --skip-metrics)
            SKIP_METRICS=true
            shift
            ;;
        --skip-archive)
            SKIP_ARCHIVE=true
            shift
            ;;
        *)
            echo -e "${RED}Error: Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Helper functions
print_header() {
    echo ""
    echo -e "${BOLD}${CYAN}========================================${NC}"
    echo -e "${BOLD}${CYAN}$1${NC}"
    echo -e "${BOLD}${CYAN}========================================${NC}"
    echo ""
}

print_section() {
    echo ""
    echo -e "${BOLD}${BLUE}## $1${NC}"
    echo ""
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

execute() {
    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY RUN]${NC} Would execute: $1"
    else
        eval "$1"
    fi
}

# Define common variables
WEEK_DATE=$(date +%Y-%m-%d)
WEEK_NUM=$(date +%U)
REPORT_FILE=".sdlc/progress/weekly-refactor-week-${WEEK_NUM}-${WEEK_DATE}.md"

# Start
print_header "Weekly Refactor Ritual"

if [ "$DRY_RUN" = true ]; then
    print_warning "Running in DRY RUN mode - no changes will be made"
fi

# Phase 1: Pattern Detection Check
if [ "$SKIP_PATTERNS" = false ]; then
    print_section "Phase 1: Pattern Detection"

    if [ -d ".sdlc/tests/patterns" ]; then
        PATTERN_COUNT=$(find .sdlc/tests/patterns -name "test_*.py" 2>/dev/null | wc -l | tr -d ' ')

        if [ "$PATTERN_COUNT" -gt 0 ]; then
            print_success "Found $PATTERN_COUNT pattern test files"
            echo ""
            echo "Pattern test files:"
            find .sdlc/tests/patterns -name "test_*.py" 2>/dev/null | while read -r file; do
                echo "  - $(basename "$file")"
            done

            # Run pattern tests if pytest is available
            if command -v pytest &> /dev/null; then
                echo ""
                print_info "Running pattern detection tests..."
                if [ "$DRY_RUN" = false ]; then
                    if pytest .sdlc/tests/patterns/ -v --tb=short 2>/dev/null; then
                        print_success "All pattern tests passed"
                    else
                        print_warning "Some pattern tests failed (new patterns detected?)"
                    fi
                else
                    echo -e "${YELLOW}[DRY RUN]${NC} Would run: pytest .sdlc/tests/patterns/ -v --tb=short"
                fi
            else
                print_info "pytest not found - skipping pattern test execution"
            fi
        else
            print_warning "No pattern tests found in .sdlc/tests/patterns/"
            print_info "Create pattern tests with: Skills/SDLC/pattern-defeat/SKILL.md"
        fi
    else
        print_warning "Directory .sdlc/tests/patterns/ does not exist"
        print_info "Run setup script to create directory structure"
    fi
fi

# Phase 2: Weekly Metrics Report
if [ "$SKIP_METRICS" = false ]; then
    print_section "Phase 2: Weekly Metrics Report"

    print_info "Generating report: $REPORT_FILE"

    if [ "$DRY_RUN" = false ]; then
        mkdir -p .sdlc/progress

        cat > "$REPORT_FILE" <<EOF
# Weekly Refactor Report - Week ${WEEK_NUM}

**Date:** ${WEEK_DATE}

## Summary

This report was generated by the weekly refactor ritual script.

---

## Git Activity (Last 7 Days)

### Commits
EOF

        git log --since="7 days ago" --oneline >> "$REPORT_FILE" 2>/dev/null || echo "No commits in last 7 days" >> "$REPORT_FILE"

        cat >> "$REPORT_FILE" <<EOF

### Most Changed Files
EOF

        echo "" >> "$REPORT_FILE"
        git log --since="7 days ago" --name-only --pretty=format: 2>/dev/null | sort | uniq -c | sort -rn | head -10 >> "$REPORT_FILE" || echo "No file changes" >> "$REPORT_FILE"

        cat >> "$REPORT_FILE" <<EOF

### Fix/Bug Commits
EOF

        echo "" >> "$REPORT_FILE"
        git log --oneline --since="7 days ago" 2>/dev/null | grep -iE "fix|bug|oops" >> "$REPORT_FILE" || echo "No fix/bug commits" >> "$REPORT_FILE"

        cat >> "$REPORT_FILE" <<EOF

---

## Pattern Detection

EOF

        if [ -d ".sdlc/tests/patterns" ]; then
            PATTERN_COUNT=$(find .sdlc/tests/patterns -name "test_*.py" 2>/dev/null | wc -l | tr -d ' ')
            echo "**Pattern Tests:** ${PATTERN_COUNT} test files" >> "$REPORT_FILE"
            echo "" >> "$REPORT_FILE"

            if [ "$PATTERN_COUNT" -gt 0 ]; then
                echo "### Pattern Test Files" >> "$REPORT_FILE"
                echo "" >> "$REPORT_FILE"
                find .sdlc/tests/patterns -name "test_*.py" 2>/dev/null | while read -r file; do
                    echo "- \`$(basename "$file")\`" >> "$REPORT_FILE"
                done
            fi
        else
            echo "No pattern tests directory found." >> "$REPORT_FILE"
        fi

        cat >> "$REPORT_FILE" <<EOF

---

## Roadmap Status

EOF

        if [ -f ".sdlc/plans/roadmap.md" ]; then
            COMPLETED_COUNT=$(grep -c "🟢" .sdlc/plans/roadmap.md 2>/dev/null || echo "0")
            IN_PROGRESS_COUNT=$(grep -c "🟡" .sdlc/plans/roadmap.md 2>/dev/null || echo "0")
            BLOCKED_COUNT=$(grep -c "🔴" .sdlc/plans/roadmap.md 2>/dev/null || echo "0")
            NOT_STARTED_COUNT=$(grep -c "⚪" .sdlc/plans/roadmap.md 2>/dev/null || echo "0")

            echo "- ✓ Completed: ${COMPLETED_COUNT}" >> "$REPORT_FILE"
            echo "- ⟳ In Progress: ${IN_PROGRESS_COUNT}" >> "$REPORT_FILE"
            echo "- ⊗ Blocked: ${BLOCKED_COUNT}" >> "$REPORT_FILE"
            echo "- ○ Not Started: ${NOT_STARTED_COUNT}" >> "$REPORT_FILE"
        else
            echo "No roadmap found." >> "$REPORT_FILE"
        fi

        cat >> "$REPORT_FILE" <<EOF

---

## Agent Memory Status (Placeholder)

This section will be populated when agent memory integration is complete.

**Agents:**
- dev-backend: [memory status]
- dev-frontend: [memory status]
- dev-infrastructure: [memory status]
- project-manager: [memory status]
- code-reviewer: [memory status]

**Actions Needed:**
- [ ] Review memory consolidation
- [ ] Archive stale memories
- [ ] Update agent character sheets based on learnings

---

## Next Week Focus

Based on this week's activity, consider:

1. **Patterns to Address:** Review most-changed files and fix commits
2. **Tests to Add:** Create pattern tests for recurring issues
3. **Agent Updates:** Update character sheets with new learnings
4. **Architecture:** Review team structure and responsibilities

---

## Action Items

- [ ] Review this report with team
- [ ] Create pattern tests for identified issues
- [ ] Update agent character sheets
- [ ] Archive completed work
- [ ] Update roadmap priorities

EOF

        print_success "Report generated: $REPORT_FILE"

        # Display report summary
        echo ""
        print_info "Report Summary:"
        echo ""
        if [ -f ".sdlc/plans/roadmap.md" ]; then
            echo "  Completed: $(grep -c "🟢" .sdlc/plans/roadmap.md 2>/dev/null || echo "0")"
            echo "  In Progress: $(grep -c "🟡" .sdlc/plans/roadmap.md 2>/dev/null || echo "0")"
            echo "  Blocked: $(grep -c "🔴" .sdlc/plans/roadmap.md 2>/dev/null || echo "0")"
        fi
        echo "  Commits (7 days): $(git log --since="7 days ago" --oneline 2>/dev/null | wc -l | tr -d ' ')"
        echo "  Pattern tests: $(find .sdlc/tests/patterns -name "test_*.py" 2>/dev/null | wc -l | tr -d ' ')"

    else
        echo -e "${YELLOW}[DRY RUN]${NC} Would generate report: $REPORT_FILE"
        echo -e "${YELLOW}[DRY RUN]${NC} Would include:"
        echo "  - Git activity (last 7 days)"
        echo "  - Most changed files"
        echo "  - Fix/bug commits"
        echo "  - Pattern detection status"
        echo "  - Roadmap status summary"
        echo "  - Agent memory status (placeholder)"
    fi
fi

# Phase 3: Archive Completed Work
if [ "$SKIP_ARCHIVE" = false ]; then
    print_section "Phase 3: Archive Completed Work"

    if [ -f ".sdlc/plans/roadmap.md" ]; then
        COMPLETED_COUNT=$(grep -c "🟢" .sdlc/plans/roadmap.md 2>/dev/null || echo "0")

        if [ "$COMPLETED_COUNT" -gt 0 ]; then
            print_info "Found $COMPLETED_COUNT completed items"

            ARCHIVE_DATE=$(date +%Y-%m-%d)
            ARCHIVE_FILE=".sdlc/completed/week-${WEEK_NUM}-${ARCHIVE_DATE}.md"

            print_info "Archive target: $ARCHIVE_FILE"

            if [ "$DRY_RUN" = false ]; then
                mkdir -p .sdlc/completed

                # Create archive header
                cat > "$ARCHIVE_FILE" <<EOF
# Completed Work - Week ${WEEK_NUM}

**Archived:** ${ARCHIVE_DATE}

---

EOF

                # Extract completed items (this is a simplified version)
                # In production, you'd want more sophisticated parsing
                grep -B 5 "🟢" .sdlc/plans/roadmap.md 2>/dev/null | head -50 >> "$ARCHIVE_FILE" || true

                print_success "Created archive: $ARCHIVE_FILE"
                print_warning "Note: Review archive and manually clean roadmap.md"
                print_info "Remove completed items from .sdlc/plans/roadmap.md after verification"
            else
                echo -e "${YELLOW}[DRY RUN]${NC} Would create archive: $ARCHIVE_FILE"
                echo -e "${YELLOW}[DRY RUN]${NC} Would archive $COMPLETED_COUNT completed items"
            fi
        else
            print_info "No completed items to archive this week"
        fi
    else
        print_warning "Roadmap file not found: .sdlc/plans/roadmap.md"
        print_info "Cannot archive without roadmap"
    fi
fi

# Phase 4: Agent Memory Summary (Placeholder)
print_section "Phase 4: Agent Memory Update"
print_info "Agent memory integration is not yet implemented"
print_info "This phase will:"
echo "  - Consolidate weekly learnings"
echo "  - Archive stale memories"
echo "  - Update agent character sheets"
echo "  - Run REM sleep process"
echo ""
print_info "See: Skills/SDLC/weekly-refactor/SKILL.md Phase 4 for details"

# Summary
print_header "Weekly Refactor Complete"

echo "Summary of actions:"
echo ""

if [ "$SKIP_PATTERNS" = false ]; then
    if [ -d ".sdlc/tests/patterns" ]; then
        PATTERN_COUNT=$(find .sdlc/tests/patterns -name "test_*.py" 2>/dev/null | wc -l | tr -d ' ')
        echo "  Pattern Tests: $PATTERN_COUNT files checked"
    else
        echo "  Pattern Tests: Directory not found"
    fi
fi

if [ "$SKIP_METRICS" = false ]; then
    if [ "$DRY_RUN" = false ]; then
        echo "  Metrics Report: Generated at $REPORT_FILE"
    else
        echo "  Metrics Report: Would be generated (dry run)"
    fi
fi

if [ "$SKIP_ARCHIVE" = false ]; then
    if [ -f ".sdlc/plans/roadmap.md" ]; then
        COMPLETED_COUNT=$(grep -c "🟢" .sdlc/plans/roadmap.md 2>/dev/null || echo "0")
        echo "  Archive: $COMPLETED_COUNT completed items identified"
    else
        echo "  Archive: Roadmap not found"
    fi
fi

echo ""
print_info "Next steps:"
echo "  1. Review weekly report: $REPORT_FILE"
echo "  2. Create pattern tests for recurring issues"
echo "  3. Update agent character sheets with learnings"
echo "  4. Clean up roadmap by removing archived items"
echo "  5. Plan next week's priorities"
echo ""

if [ "$DRY_RUN" = false ]; then
    print_success "Weekly refactor ritual complete!"
else
    print_info "Dry run complete - no changes were made"
fi

echo ""
