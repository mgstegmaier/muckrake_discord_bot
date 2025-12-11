# Pattern Hunter - Quick Start Guide

Get started with pattern detection in 2 minutes.

## Installation

No installation needed! Just make sure you have:
- Python 3.11+
- A git repository
- Anthropic API key (set as `ANTHROPIC_API_KEY` environment variable)

## Basic Usage

### 1. First Time - Preview Mode

Start with a dry-run to see what would happen:

```bash
cd /path/to/your/repo
./hunt-patterns --dry-run --auto hunt
```

This shows you the full workflow without making any changes.

### 2. Interactive Mode

Run the full workflow with human review:

```bash
./hunt-patterns hunt
```

You'll be asked to review each pattern:
```
Pattern 1/3: Silent Fallback Anti-Pattern
Description: Using .get(key, default) without validation
Process this pattern? [Y/n]: y
```

And approve updates:
```
Update pre-commit hooks with defeat tests? [Y/n]: y
Update agent memory with learnings? [Y/n]: y
```

### 3. Automated Mode

Skip all prompts and process everything:

```bash
./hunt-patterns --auto hunt
```

Perfect for CI/CD pipelines and scheduled jobs.

## What Happens?

The tool:

1. **Collects Signals** - Analyzes git commits, agent memory, code churn
2. **Identifies Patterns** - Uses Claude AI to find recurring issues
3. **Generates Tests** - Creates pytest defeat tests for each pattern
4. **Updates Config** - Adds tests to `.pre-commit-config.yaml`
5. **Trains Agents** - Adds learnings to agent memory

## Example Output

```
============================================================
🎯 PATTERN HUNT - Full Workflow
============================================================

Step 1: Collecting Signals
✓ Collected 47 git signals, 12 memory signals, 8 churn signals

Step 2: Analyzing Patterns
✓ Identified 3 patterns

Step 3: Pattern Review
Pattern 1/3: Silent Fallback Anti-Pattern
Process this pattern? [Y/n]: y
✓ Pattern added to queue

Step 4: Generating Defeat Tests
✓ Generated test_silent_fallback.py

Step 5: Generating Agent Updates
✓ Generated 1 proposals

Step 6: Review & Apply Updates
✓ Pre-commit hooks updated
✓ Agent memory updated

============================================================
🎉 Pattern Hunt Complete!
============================================================
```

## Output Files

After running, you'll find:

```
.sdlc/
├── pattern-hunter/
│   ├── signals-*.json          # Raw data collected
│   ├── patterns-*.json         # Identified patterns
│   └── proposals-*.json        # Agent update proposals
└── tests/patterns/
    ├── test_silent_fallback.py
    └── test_bare_except.py
```

Plus updated:
- `.pre-commit-config.yaml` - With new defeat tests
- `~/.agent-memory/memories.json` - With pattern learnings

## Next Steps

1. **Review Tests** - Check generated tests in `.sdlc/tests/patterns/`
2. **Run Tests** - `pytest .sdlc/tests/patterns/`
3. **Install Hooks** - `pre-commit install` (if not already installed)
4. **Commit Changes** - Commit the new tests and config

## Common Options

```bash
# Process specific time period
./hunt-patterns hunt --days 60

# Limit number of patterns
./hunt-patterns hunt --top-n 5

# Different repository
./hunt-patterns --repo-path ~/other-project hunt

# Disable colors (for logs)
./hunt-patterns --no-color hunt
```

## Troubleshooting

### "API key not found"
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### "Pre-commit update failed"
```bash
# Initialize pre-commit config
touch .pre-commit-config.yaml
```

### "Memory directory not found"
```bash
# Create agent memory
mkdir -p ~/.agent-memory
echo '{"memories": []}' > ~/.agent-memory/memories.json
```

## Documentation

- [CLI-USAGE.md](CLI-USAGE.md) - Complete command reference
- [README.md](README.md) - Module documentation
- [REQ-064-IMPLEMENTATION.md](REQ-064-IMPLEMENTATION.md) - Implementation details

## Get Help

```bash
# General help
./hunt-patterns --help

# Command-specific help
./hunt-patterns hunt --help
./hunt-patterns collect --help
./hunt-patterns analyze --help
```

## Examples

### Weekly Pattern Detection (Cron)

Add to crontab:
```cron
0 9 * * 1 cd /path/to/repo && ./hunt-patterns --auto hunt
```

### CI/CD Integration

```yaml
# .github/workflows/pattern-detection.yml
name: Pattern Detection
on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9 AM

jobs:
  detect:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Pattern Hunter
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: ./hunt-patterns --auto --no-color hunt
```

### Multiple Repositories

```bash
#!/bin/bash
for repo in ~/projects/*; do
    echo "Processing $repo"
    ./hunt-patterns --repo-path "$repo" --auto hunt
done
```

## Best Practices

1. **Start with --dry-run** - Always preview first
2. **Run weekly** - Catch patterns early
3. **Review interactively** - Don't blindly trust --auto mode
4. **Commit separately** - One pattern per commit
5. **Test defeat tests** - Run pytest after generation

## That's It!

You're ready to hunt patterns. Start with:

```bash
./hunt-patterns --dry-run hunt
```

Then remove `--dry-run` when you're ready to apply changes.
