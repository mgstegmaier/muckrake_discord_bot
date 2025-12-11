# Pattern Hunter CLI - Usage Guide

An interactive command-line tool for the complete pattern detection and defeat workflow.

## Quick Start

```bash
# Run full interactive workflow
./hunt-patterns hunt

# Non-interactive (auto-approve all)
./hunt-patterns hunt --auto

# Preview without making changes
./hunt-patterns hunt --dry-run
```

## Overview

The Pattern Hunter CLI orchestrates six key steps:

1. **Collect** - Gather signals from git history, agent memory, and code churn
2. **Analyze** - Use AI to identify concrete patterns from signals
3. **Review** - Interactively review and approve patterns
4. **Generate** - Create defeat tests for approved patterns
5. **Propose** - Generate agent prompt and memory updates
6. **Apply** - Update pre-commit hooks and agent memory

## Commands

### `hunt` - Full Workflow

Run the complete pattern detection and defeat workflow with interactive review points.

```bash
# Interactive mode (default)
./hunt-patterns hunt

# Auto-approve all prompts
./hunt-patterns hunt --auto

# Preview without changes
./hunt-patterns hunt --dry-run

# Custom analysis period
./hunt-patterns hunt --days 60 --top-n 15
```

**Options:**
- `--days N` - Days of git history to analyze (default: 30)
- `--top-n N` - Maximum patterns to identify (default: 10)

**Interactive Prompts:**
- For each pattern: "Process this pattern? [Y/n]"
- "Update pre-commit hooks with defeat tests? [Y/n]"
- "Update agent memory with learnings? [Y/n]"

**Example Output:**
```
============================================================
🎯 PATTERN HUNT - Full Workflow
============================================================

Step 1: Collecting Signals
✓ Collected 47 git signals, 12 memory signals, 8 churn signals

Step 2: Analyzing Patterns
✓ Identified 5 patterns

Step 3: Pattern Review
Pattern 1/5: Silent Fallback Anti-Pattern
Description: Using .get(key, default) without validation hides bugs
Frequency: weekly
Impact: high
Evidence:
  • src/api/routes.py: modified 7 times
  • src/utils/config.py: fixed error handling
  ... and 4 more
Process this pattern? [Y/n]: y
✓ Pattern added to queue

[... review remaining patterns ...]

Step 4: Generating Defeat Tests
✓ Generated test_silent_fallback.py
✓ Generated test_bare_except.py

Step 5: Generating Agent Updates
✓ Generated 3 proposals

Step 6: Review & Apply Updates
Proposed Updates Summary:
  • Dev-Backend: Silent Fallback Anti-Pattern
  • Dev-Backend: Bare Except Blocks
  • Dev-Frontend: Missing Null Checks

Update pre-commit hooks with defeat tests? [Y/n]: y
✓ Pre-commit hooks updated

Update agent memory with learnings? [Y/n]: y
✓ Agent memory updated

============================================================
🎉 Pattern Hunt Complete!
============================================================

✓ Processed 3 patterns
→ Results saved in: .sdlc/pattern-hunter
```

### `collect` - Collect Signals

Gather pattern signals from git history, agent memory, and code churn.

```bash
# Collect signals from last 30 days
./hunt-patterns collect

# Custom time period and output
./hunt-patterns collect --days 60 --output signals.json
```

**Options:**
- `--days N` - Days of history to analyze (default: 30)
- `--output FILE` - Output file path (default: auto-generated timestamp)

**Output:** JSON file with structure:
```json
{
  "timestamp": "2025-12-10T13:45:00",
  "repo_path": "/path/to/repo",
  "collection_period_days": 30,
  "git_signals": [...],
  "memory_signals": [...],
  "churn_signals": [...]
}
```

### `analyze` - Analyze Patterns

Use AI to identify concrete patterns from collected signals.

```bash
# Analyze most recent collection
./hunt-patterns analyze

# Analyze specific signals file
./hunt-patterns analyze --input signals.json --output patterns.json

# Limit to top 5 patterns
./hunt-patterns analyze --top-n 5
```

**Options:**
- `--input FILE` - Input signals file (default: use last collection)
- `--output FILE` - Output patterns file (default: auto-generated timestamp)
- `--top-n N` - Maximum patterns to identify (default: 10)

**Output:** JSON file with structure:
```json
{
  "timestamp": "2025-12-10T13:45:00",
  "patterns": [
    {
      "name": "Silent Fallback Anti-Pattern",
      "description": "Using .get(key, default) without validation",
      "evidence": ["file.py: modified 7 times", "..."],
      "frequency": "weekly",
      "impact": "high",
      "root_cause": "Developers prefer concise code over explicit validation",
      "score": 8.5
    }
  ]
}
```

### `generate` - Generate Defeat Tests

Create pytest defeat tests for identified patterns.

```bash
# Generate tests for all patterns in last analysis
./hunt-patterns generate

# Generate test for specific pattern
./hunt-patterns generate --pattern "silent_fallback"

# Use specific patterns file
./hunt-patterns generate --input patterns.json
```

**Options:**
- `--input FILE` - Input patterns file (default: use last analysis)
- `--pattern NAME` - Filter by pattern name (substring match)

**Output:** Python test files in `.sdlc/tests/patterns/`:
```
.sdlc/tests/patterns/
├── test_silent_fallback.py
├── test_bare_except.py
└── test_missing_null_checks.py
```

### `apply` - Apply Updates

Apply agent prompt updates and memory entries.

```bash
# Apply proposals (requires proposals file)
./hunt-patterns apply --input proposals.json
```

**Options:**
- `--input FILE` - Input proposals file (required)

**Interactive Prompts:**
- "Update pre-commit hooks with defeat tests? [Y/n]"
- "Update agent memory with learnings? [Y/n]"

**Actions:**
- Updates `.pre-commit-config.yaml` with pattern defeat test hook
- Adds memory entries to `~/.agent-memory/memories.json`
- Creates reviewable proposals in `progress/pattern-proposals-{date}.md`

## Global Options

These options can be specified before the command:

```bash
./hunt-patterns [OPTIONS] COMMAND [COMMAND_OPTIONS]
```

**Global Options:**
- `--repo-path PATH` - Path to repository (default: current directory)
- `--dry-run` - Preview actions without making changes
- `--auto` - Auto-approve all interactive prompts
- `--no-color` - Disable colored output (for piping/logging)

**Examples:**
```bash
# Dry-run for different repo
./hunt-patterns --repo-path ~/other-project --dry-run hunt

# Auto-approve without colors (for CI/automation)
./hunt-patterns --auto --no-color hunt

# Combine multiple flags
./hunt-patterns --dry-run --auto --no-color hunt
```

## State Management

The CLI maintains state between runs in `.sdlc/pattern-hunter/state.json`:

```json
{
  "last_run": "2025-12-10T13:45:00",
  "last_collection": "/path/to/signals-20251210-134500.json",
  "last_analysis": "/path/to/patterns-20251210-134530.json",
  "patterns_pending_review": [],
  "patterns_approved": []
}
```

This allows commands like `analyze` and `generate` to automatically use the most recent outputs without specifying `--input`.

## Output Files

All intermediate and final outputs are saved in `.sdlc/pattern-hunter/`:

```
.sdlc/pattern-hunter/
├── state.json                          # State tracking
├── signals-20251210-134500.json        # Collected signals
├── patterns-20251210-134530.json       # Identified patterns
└── proposals-20251210-134600.json      # Agent update proposals
```

Generated tests are saved in `.sdlc/tests/patterns/`:

```
.sdlc/tests/patterns/
├── test_silent_fallback.py
├── test_bare_except.py
└── test_missing_null_checks.py
```

## Dry-Run Mode

Use `--dry-run` to preview what would happen without making any changes:

```bash
./hunt-patterns --dry-run hunt
```

**What it does:**
- Shows commands that would be executed
- Uses mock data for testing workflow
- Skips file writes and git operations
- Still shows interactive prompts (unless `--auto` is used)

**Use cases:**
- Testing the workflow before running for real
- Verifying configuration is correct
- Demonstrating the tool to others
- CI/CD pipeline validation

## Auto Mode

Use `--auto` to skip all interactive prompts (always answer "yes"):

```bash
./hunt-patterns --auto hunt
```

**Use cases:**
- Automated CI/CD pipelines
- Scheduled cron jobs
- Batch processing multiple repositories
- When you trust the AI analysis completely

**Caution:** Auto mode will:
- Process ALL identified patterns
- Update pre-commit hooks automatically
- Add ALL memory entries automatically
- Should be used with `--dry-run` first to preview

## Integration with Pre-existing Workflow

The Pattern Hunter CLI integrates with existing tools:

1. **Git History** - Analyzes commit messages and file changes
2. **Agent Memory** - Reads from `~/.agent-memory/memories.json`
3. **Pre-commit Hooks** - Updates `.pre-commit-config.yaml`
4. **Pytest** - Generates standard pytest test files
5. **Claude AI** - Uses Claude for pattern analysis and proposal generation

## Troubleshooting

### "No input file specified and no previous collection found"

Run `collect` first:
```bash
./hunt-patterns collect
```

### "Pattern analysis failed: API key not found"

Set your Anthropic API key:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### "Pre-commit update failed: File not found"

Initialize pre-commit configuration:
```bash
touch .pre-commit-config.yaml
```

### "Memory update failed: Directory not found"

Create agent memory directory:
```bash
mkdir -p ~/.agent-memory
echo '{"memories": []}' > ~/.agent-memory/memories.json
```

## Advanced Usage

### Pipeline Individual Commands

You can run commands individually and chain them:

```bash
# Step 1: Collect
./hunt-patterns collect --days 30 --output signals.json

# Step 2: Analyze
./hunt-patterns analyze --input signals.json --output patterns.json

# Step 3: Generate tests for specific pattern
./hunt-patterns generate --input patterns.json --pattern "silent_fallback"

# Step 4: Generate proposals
python3 pattern-detector/propose_updates.py --input patterns.json --output proposals.json

# Step 5: Apply
./hunt-patterns apply --input proposals.json
```

### Using with Multiple Repositories

```bash
# Create a script to process multiple repos
for repo in ~/projects/*; do
    echo "Processing $repo"
    ./hunt-patterns --repo-path "$repo" --auto hunt
done
```

### Scheduled Pattern Hunting

Add to crontab for weekly pattern detection:

```cron
# Run pattern hunt every Monday at 9 AM
0 9 * * 1 cd /path/to/repo && ./hunt-patterns --auto hunt > pattern-hunt.log 2>&1
```

## Best Practices

1. **Start with dry-run** - Always test with `--dry-run` first
2. **Review interactively** - Don't use `--auto` until you trust the patterns
3. **Run regularly** - Weekly or bi-weekly pattern detection catches issues early
4. **Review proposals** - Always review generated proposals before applying
5. **Test defeat tests** - Run `pytest .sdlc/tests/patterns/` after generation
6. **Commit incrementally** - Commit each pattern's defeat test separately

## Exit Codes

- `0` - Success
- `1` - General error (see error message)
- `130` - Interrupted by user (Ctrl+C)

## See Also

- [Pattern Detector README](README.md) - Module documentation
- [REQ-064 Implementation](../../plans/roadmap.md) - Requirements
- [Agentic SDLC Framework](../../README.md) - Overall framework
