# Pattern Detection Module

Automated data collection and analysis tools for identifying anti-patterns and improvement opportunities in your codebase.

## Overview

The pattern detection module collects signals from three sources:

1. **Git History** - Fix commits and repeated modifications
2. **Agent Memory** - Repeated learnings and patterns
3. **Code Churn** - Hot files with frequent changes

## Quick Start (CLI)

The easiest way to use the pattern detector is via the interactive CLI:

```bash
# Run full interactive workflow
./hunt-patterns hunt

# Non-interactive (auto-approve all)
./hunt-patterns hunt --auto

# Preview without changes
./hunt-patterns hunt --dry-run
```

See [CLI-USAGE.md](CLI-USAGE.md) for complete CLI documentation.

## Installation

No installation required. The module uses only Python standard library.

Requirements:
- Python 3.11+
- Git repository
- Anthropic API key (for AI-powered analysis)

Optional:
- `pyyaml` - For pre-commit hook updates
- `pytest` - For running defeat tests

## Module Architecture

The pattern detector consists of several modules that can be used independently or orchestrated via the CLI:

1. **collect.py** - Data collection from git, memory, churn
2. **analyze.py** - AI-powered pattern identification
3. **generate_tests.py** - Defeat test generation
4. **propose_updates.py** - Agent prompt proposals
5. **update_precommit.py** - Pre-commit hook updates
6. **update_memory.py** - Agent memory updates
7. **cli.py** - Interactive CLI orchestrator

## Usage

### Using the CLI (Recommended)

```bash
# Full interactive workflow
./hunt-patterns hunt

# Individual commands
./hunt-patterns collect --days 30
./hunt-patterns analyze --input signals.json
./hunt-patterns generate --input patterns.json
./hunt-patterns apply --input proposals.json
```

### Using Individual Modules

```bash
# Collect signals from current directory
python3 collect.py

# Collect from specific repository
python3 collect.py --repo-path /path/to/repo

# Look back 60 days instead of default 30
python3 collect.py --days 60

# Save to file with pretty formatting
python3 collect.py --output signals.json --pretty
```

### Advanced Options

```bash
# Use custom agent memory location
python3 collect.py --memory-path /custom/path/memories.json

# Get top 20 hot files instead of default 10
python3 collect.py --top-n 20

# Combine options
python3 collect.py \
  --repo-path ~/projects/myapp \
  --days 90 \
  --top-n 15 \
  --output analysis.json \
  --pretty
```

### Help

```bash
python3 collect.py --help
```

## Output Format

The script outputs JSON with the following structure:

```json
{
  "timestamp": "2025-12-10T13:22:00.926220",
  "repo_path": "/path/to/repo",
  "collection_period_days": 30,
  "git_signals": [
    {
      "type": "fix_commit",
      "hash": "abc123",
      "date": "2025-12-10T12:00:00",
      "author": "Developer Name",
      "message": "Fix authentication bug",
      "files_changed": ["auth.py"],
      "stats": {"insertions": 10, "deletions": 5}
    },
    {
      "type": "repeated_modification",
      "file": "auth.py",
      "modification_count": 5,
      "modifications": [...],
      "signal_strength": "high"
    }
  ],
  "memory_signals": [
    {
      "type": "repeated_learning",
      "pattern": "Multiple learnings in category: authentication",
      "occurrences": 4,
      "memories": [...],
      "signal_strength": "medium"
    }
  ],
  "churn_signals": [
    {
      "type": "hot_file",
      "file": "auth.py",
      "churn_score": 1250,
      "commit_count": 5,
      "total_changes": 250,
      "signal_strength": "high"
    }
  ],
  "summary": {
    "total_signals": 12,
    "fix_commits": 5,
    "repeated_modifications": 3,
    "repeated_learnings": 2,
    "hot_files": 2
  }
}
```

## Signal Types

### Git Signals

- **fix_commit** - Commits with keywords like "fix", "bug", "repair", "hotfix"
- **repeated_modification** - Files modified 3+ times in the time period

### Memory Signals

- **repeated_learning** - Categories or tags with 3+ agent memories

### Churn Signals

- **hot_file** - Files with highest churn scores (commits × changes)

## Signal Strength

Each signal includes a strength indicator:

- **high** - 5+ occurrences/commits
- **medium** - 3-4 occurrences/commits
- **low** - 1-2 occurrences/commits

## Error Handling

The script handles errors gracefully:

- Missing agent memory file: Continues with warning
- Invalid git repository: Exits with error
- Parse errors: Reports warning and continues

## Integration

This module is designed to be used standalone or as part of the pattern detection pipeline:

```
collect.py → analyze.py → generate.py → apply.py
   ↓            ↓            ↓            ↓
 Signals    Patterns      Tests       Pre-commit
```

## Examples

### Find Frequently Fixed Files

```bash
python3 collect.py --pretty | jq '.git_signals[] | select(.type == "fix_commit")'
```

### Top 5 Hot Files

```bash
python3 collect.py --pretty | jq '.churn_signals[:5]'
```

### Agent Learning Categories

```bash
python3 collect.py --pretty | jq '.memory_signals[].category' | sort | uniq -c
```

## Troubleshooting

**No git signals found**
- Verify you're in a git repository
- Check date range with `--days` parameter
- Ensure commits exist in the time period

**Agent memory not found**
- Default location: `~/.agent-memory/memories.json`
- Specify custom path with `--memory-path`
- This is optional - script continues without it

**Empty churn signals**
- No commits in time period
- Try increasing `--days` parameter

## Development

The module is organized into three analyzer classes:

- `GitHistoryAnalyzer` - Processes git log output
- `AgentMemoryAnalyzer` - Parses agent memory JSON
- `CodeChurnAnalyzer` - Calculates file churn scores

Each analyzer can be used independently or via the `collect_all_signals()` function.

## AI Analysis (analyze.py)

### Overview

Uses Claude AI to analyze collected signals and identify concrete anti-patterns with supporting evidence.

### Usage

```bash
# Analyze signals from file (mock mode - no API calls)
python3 analyze.py --input signals.json --mock

# Analyze with real Claude API (via CLI)
python3 analyze.py --input signals.json

# Pipeline from collect.py
python3 collect.py | python3 analyze.py --mock --top-n 5

# Save to file
python3 analyze.py --input signals.json --output patterns.json --pretty

# Use Python SDK instead of CLI
python3 analyze.py --input signals.json --use-sdk --api-key YOUR_KEY
```

### Output Format

```json
{
  "timestamp": "2025-12-10T10:05:00",
  "patterns": [
    {
      "name": "Silent Fallback Pattern",
      "description": "Using .get() with defaults instead of validation",
      "evidence": [
        "file.py: modified 5 times with validation fixes",
        "Agent memory: 'learned to validate' appears 4 times"
      ],
      "frequency": "weekly",
      "impact": "high",
      "root_cause": "Developers default to .get() for convenience...",
      "score": 9.0
    }
  ],
  "metadata": {
    "total_patterns_found": 3,
    "patterns_returned": 3,
    "api_method": "cli"
  }
}
```

### Pattern Scoring

Patterns are ranked by: **score = impact × frequency**

**Impact Scores:**
- High: 3.0 (blocks work, causes bugs)
- Medium: 2.0 (slows development)
- Low: 1.0 (minor annoyance)

**Frequency Scores:**
- Daily: 4.0
- Weekly: 3.0
- Per-feature: 2.0
- Monthly: 1.0

### API Configuration

**Claude CLI (Default):**
```bash
# Requires claude CLI to be installed and configured
python3 analyze.py --input signals.json
```

**Python SDK:**
```bash
# Install SDK: pip install anthropic
export ANTHROPIC_API_KEY=your_key_here
python3 analyze.py --input signals.json --use-sdk
```

**Mock Mode (Testing):**
```bash
# Use predefined patterns (no API calls)
python3 analyze.py --input signals.json --mock
```

### Command-Line Options

| Flag | Description | Default |
|------|-------------|---------|
| `--input` | Input signals file | stdin |
| `--output` | Output file | stdout |
| `--mock` | Use mock data | False |
| `--use-sdk` | Use Python SDK | False (uses CLI) |
| `--api-key` | Anthropic API key | `ANTHROPIC_API_KEY` env var |
| `--top-n` | Return top N patterns | 5 |
| `--pretty` | Pretty-print JSON | False |

### Error Handling

- **API failures**: Retries 3 times with exponential backoff
- **Invalid JSON**: Clear error messages
- **Empty signals**: Gracefully handles and continues
- **Timeout**: 2-minute timeout per API call

### Programmatic Usage

```python
from analyze import PatternAnalyzer

# Initialize analyzer
analyzer = PatternAnalyzer(mock=False)

# Analyze signals
results = analyzer.analyze(signals_data)

# Access patterns
for pattern in results['patterns']:
    print(f"{pattern['name']}: {pattern['score']:.1f}")
```

See `example_usage.py` for complete workflow example.

## Complete Pipeline

```bash
# Full workflow: collect → analyze → save
python3 collect.py --days 30 | \
  python3 analyze.py --mock --top-n 5 --pretty > patterns.json
```

## Test Generation (generate_tests.py)

### Overview

Automatically generates Python defeat tests from identified patterns. Uses Claude AI to generate test code with proper structure, detection logic, and validation.

### Usage

```bash
# Generate tests from analyzed patterns (mock mode - no API calls)
python3 generate_tests.py --input patterns.json --mock

# Generate with real Claude API (via CLI)
python3 generate_tests.py --input patterns.json

# Generate from pipeline
python3 analyze.py --input signals.json --mock | \
  python3 generate_tests.py --mock

# Specify output directory
python3 generate_tests.py --input patterns.json --output-dir .sdlc/tests/patterns --mock

# Dry run (generate but don't write files)
python3 generate_tests.py --input patterns.json --mock --dry-run

# Validate existing tests
python3 generate_tests.py --output-dir .sdlc/tests/patterns --validate-only
```

### Output Format

Generated test files follow the defeat test format:

```python
#!/usr/bin/env python3
"""
Defeat Test: Pattern Name
Pattern: pattern_slug
Severity: HIGH
Generated: 2025-12-10
Description: What the pattern is
"""
import re
from pathlib import Path


def test_no_pattern_name():
    """Prevent pattern from occurring."""
    project_root = Path(__file__).parent.parent.parent
    violations = []

    # Detection logic (regex, AST, file scanning, etc.)
    for py_file in project_root.rglob("*.py"):
        if 'test_' in py_file.name:
            continue
        # Pattern detection here
        pass

    assert not violations, f"Pattern found:\n" + "\n".join(violations[:10])
```

### Detection Methods

The generator uses templates for common detection patterns:

| Method | Use Case | Example |
|--------|----------|---------|
| **Regex** | Simple text patterns | `.get(key, default)` |
| **AST** | Structural code patterns | Function length, bare except |
| **File content** | Documentation issues | Missing docstrings |
| **Import checking** | Forbidden dependencies | Deprecated libraries |

### Command-Line Options

| Flag | Description | Default |
|------|-------------|---------|
| `--input` | Input patterns file | stdin |
| `--output-dir` | Output directory | `.sdlc/tests/patterns` |
| `--mock` | Use mock templates | False (uses Claude API) |
| `--use-sdk` | Use Python SDK | False (uses CLI) |
| `--api-key` | Anthropic API key | `ANTHROPIC_API_KEY` env var |
| `--validate-only` | Only validate existing tests | False |
| `--dry-run` | Generate but don't write | False |

### Validation

All generated tests are validated for:

- **Syntax correctness** - Uses `ast.parse()` to validate Python syntax
- **Required structure** - Module docstring with metadata, imports, test functions
- **Executable** - Can be run with pytest

Invalid tests are reported but not written to files.

### Programmatic Usage

```python
from generate_tests import TestGenerator

# Initialize generator
generator = TestGenerator(mock=False)

# Generate test for a pattern
pattern = {
    'name': 'Silent Fallback',
    'description': 'Using .get() with defaults',
    'evidence': ['file.py: modified 5 times'],
    'frequency': 'weekly',
    'impact': 'high',
    'root_cause': 'Convenience over safety'
}

result = generator.generate_test(pattern)

# Check if valid
if result['validation']['is_valid']:
    print(f"Generated {result['filename']}")
else:
    print(f"Validation failed: {result['validation']['error']}")

# Write to file
generator.write_test_files([result], '.sdlc/tests/patterns')
```

## Agent Prompt Update Proposals (propose_updates.py)

### Overview

Generates proposed updates to agent character sheets based on identified patterns. For each pattern, creates:
- Non-Negotiable test entries
- Discipline checklist items
- Memory entries
- Defeat test references

### Usage

```bash
# Basic usage - outputs to progress/pattern-proposals-{date}.md
python3 propose_updates.py --input patterns.json

# Specify output file
python3 propose_updates.py --input patterns.json --output proposals.md

# Use mock data (no API calls)
python3 propose_updates.py --input patterns.json --mock

# Output JSON instead of markdown
python3 propose_updates.py --input patterns.json --json --pretty

# Pipeline from analyze.py
python3 collect.py | python3 analyze.py --mock | \
  python3 propose_updates.py --mock
```

### Output Format

```markdown
# Pattern Proposals - 2025-12-10

## Pattern: Silent Fallback Pattern (Score: 9.0, HIGH impact)

**Description:** Using .get() with default values...
**Frequency:** weekly
**Root Cause:** Convenience over correctness...

**Evidence:**
- file.py: modified 5 times
- commit abc123: added validation

### Proposed Update for Agent: Dev

#### Non-Negotiable Addition
```
- [ ] NEVER use .get(key, default) without explicit validation
```

#### Discipline Item
```
Before using dictionary access, verify the key exists...
```

#### Memory Entry
```json
{
  "content": "Learned: Silent fallbacks hide bugs...",
  "category": "anti-patterns",
  "tags": ["anti-patterns", "defeat-test", "silent-fallback"]
}
```

#### Related Defeat Test
`test_no_silent_fallback_pattern.py`
```

### Agent Classification

Patterns are automatically routed to the appropriate agent:

| Pattern Type | Agent | Keywords |
|--------------|-------|----------|
| Code patterns | Dev | error, validation, api, database, testing |
| Documentation | Research | documentation, readme, spec, analysis |
| Process | Project-Manager | workflow, planning, roadmap, coordination |
| Quality | Code-Reviewer | review, quality, merge, standards |
| Release | Release-Manager | release, deploy, version, production |

### Command-Line Options

| Flag | Description | Default |
|------|-------------|---------|
| `--input` | Input patterns file | stdin |
| `--output` | Output file | `progress/pattern-proposals-{date}.md` |
| `--mock` | Use mock data | False |
| `--use-sdk` | Use Python SDK | False (uses CLI) |
| `--api-key` | Anthropic API key | `ANTHROPIC_API_KEY` env var |
| `--json` | Output JSON | False (outputs markdown) |
| `--pretty` | Pretty-print JSON | False |

### Programmatic Usage

```python
from propose_updates import ProposalGenerator

# Initialize generator
generator = ProposalGenerator(mock=False)

# Generate proposals from analysis results
results = generator.generate_proposals(analysis_data)

# Access proposals
for proposal in results['proposals']:
    print(f"Agent: {proposal['agent']}")
    print(f"Pattern: {proposal['pattern_name']}")
    print(f"Non-negotiable: {proposal['non_negotiable']}")
```

## Complete Pipeline

### Full Workflow

```bash
# 1. Collect signals from repository
python3 collect.py --days 30 --output signals.json

# 2. Analyze patterns using Claude
python3 analyze.py --input signals.json --output patterns.json

# 3. Generate agent prompt proposals
python3 propose_updates.py --input patterns.json --output proposals.md

# 4. Review proposals and apply to agent character sheets
# (Manual step - review progress/pattern-proposals-{date}.md)
```

### Testing Workflow (No API Calls)

```bash
# Complete pipeline with mock data
echo '{}' | \
  python3 collect.py | \
  python3 analyze.py --mock | \
  python3 propose_updates.py --mock --output test-proposals.md
```

## Agent Memory Auto-Update (update_memory.py)

### Overview

Automatically adds pattern learnings to agent memory. Supports both direct file modification and MCP server integration. Prevents duplicates by checking pattern_id in metadata.

### Usage

```bash
# Basic usage - from file
python3 update_memory.py --input proposals.json

# From pipeline
python3 propose_updates.py --json | python3 update_memory.py

# Dry run (show what would be added)
python3 update_memory.py --input proposals.json --dry-run

# Custom memory location
python3 update_memory.py --input proposals.json --memory-path /custom/path/memories.json

# Force MCP mode
python3 update_memory.py --input proposals.json --use-mcp
```

### Input Format

Expects JSON from `propose_updates.py`:

```json
{
  "proposals": [
    {
      "agent": "Dev",
      "pattern_name": "Silent Fallback Pattern",
      "memory": "Learned: Silent fallbacks hide bugs...",
      "memory_tags": ["anti-patterns", "defeat-test", "silent-fallback"]
    }
  ]
}
```

### Memory Entry Format

Created entries follow this structure:

```json
{
  "id": 42,
  "content": "Learned: Silent fallbacks hide bugs...",
  "category": "anti-patterns",
  "tags": ["anti-patterns", "defeat-test", "silent-fallback"],
  "metadata": {
    "pattern_id": "silent_fallback_pattern",
    "defeat_test": "test_silent_fallback_pattern.py",
    "added_by": "pattern-detector",
    "agent": "Dev"
  },
  "created_at": "2025-12-10T14:00:00",
  "updated_at": "2025-12-10T14:00:00"
}
```

### Duplicate Prevention

The module checks for existing learnings by `pattern_id` in metadata:

- **First addition**: Creates new memory entry
- **Subsequent additions**: Skips with message "Already exists in memory"
- **Pattern ID**: Generated from pattern name (e.g., "Silent Fallback" → "silent_fallback")

### Command-Line Options

| Flag | Description | Default |
|------|-------------|---------|
| `--input` | Input JSON file | stdin |
| `--memory-path` | Path to memories.json | `~/.agent-memory/memories.json` |
| `--use-mcp` | Use MCP server | False (uses direct file) |
| `--dry-run` | Show changes without applying | False |
| `--json` | Output JSON instead of summary | False |
| `--pretty` | Pretty-print JSON output | False |

### Output Summary

```
Processing 2 proposals...
  Added: Silent Fallback Pattern (memory #1)
  Skipped: Missing Error Context (already exists as memory #2)

=== Memory Update Summary ===
Total proposals: 2
Added: 1
Skipped: 1
Errors: 0

Added learnings:
  - Silent Fallback Pattern (ID: 1, Agent: Dev)

Skipped (duplicates):
  - Missing Error Context (exists as #2)
```

### Programmatic Usage

```python
from update_memory import MemoryUpdater

# Initialize
updater = MemoryUpdater(
    memory_path='~/.agent-memory/memories.json',
    dry_run=False
)

# Add learnings
proposals = [
    {
        'agent': 'Dev',
        'pattern_name': 'New Pattern',
        'memory': 'Learned: Something important',
        'memory_tags': ['anti-patterns', 'defeat-test']
    }
]

result = updater.add_learnings(proposals)

# Check results
print(f"Added: {len(result['added'])}")
print(f"Skipped: {len(result['skipped'])}")
print(f"Errors: {len(result['errors'])}")
```

### Error Handling

- **Missing memory file**: Creates new file with empty array
- **Invalid JSON**: Reports error and exits
- **Duplicate patterns**: Skips and reports in summary
- **MCP unavailable**: Falls back to direct file mode

## Complete Pipeline

### Full Workflow

```bash
# 1. Collect signals from repository
python3 collect.py --days 30 --output signals.json

# 2. Analyze patterns using Claude
python3 analyze.py --input signals.json --output patterns.json

# 3. Generate defeat tests
python3 generate_tests.py --input patterns.json --output-dir .sdlc/tests/patterns

# 4. Generate agent prompt proposals
python3 propose_updates.py --input patterns.json --json --output proposals.json

# 5. Auto-update agent memory
python3 update_memory.py --input proposals.json

# 6. Review proposals and apply to agent character sheets
# (Manual step - review progress/pattern-proposals-{date}.md)
```

### One-Liner Pipeline

```bash
# Complete automation (with mock data for testing)
python3 collect.py --days 30 | \
  python3 analyze.py --mock | \
  tee patterns.json | \
  python3 generate_tests.py --mock && \
  python3 propose_updates.py --input patterns.json --json | \
  python3 update_memory.py --dry-run
```

## Pre-commit Hook Auto-Update (update_precommit.py)

### Overview

Automatically updates `.pre-commit-config.yaml` to include pattern defeat tests. Creates config if missing, adds tests without breaking existing hooks, and is fully idempotent.

### Usage

```bash
# Basic usage (updates .pre-commit-config.yaml in current directory)
python3 update_precommit.py

# Dry run to preview changes
python3 update_precommit.py --dry-run

# Custom paths
python3 update_precommit.py --config /path/to/.pre-commit-config.yaml --test-dir .sdlc/tests/patterns

# Update and install hooks
python3 update_precommit.py --install

# Check if update is needed
python3 update_precommit.py --check-only
```

### Features

- **Creates config if missing**: New repositories get a valid `.pre-commit-config.yaml`
- **Preserves existing hooks**: Adds pattern tests without removing other hooks
- **Idempotent**: Running twice produces same result, no unnecessary changes
- **Validates YAML**: Ensures config is syntactically correct before writing
- **Dry run support**: Preview changes without modifying files
- **Pre-commit integration**: Optionally installs hooks with `--install`

### Hook Structure

Generated hook configuration:

```yaml
repos:
  - repo: local
    hooks:
      - id: pattern-defeat-tests
        name: Pattern Defeat Tests
        entry: pytest .sdlc/tests/patterns/ -v
        language: system
        types: [python]
        pass_filenames: false
```

### Command-Line Options

| Flag | Description | Default |
|------|-------------|---------|
| `--config` | Path to .pre-commit-config.yaml | `.pre-commit-config.yaml` in cwd |
| `--test-dir` | Path to test directory | `.sdlc/tests/patterns` |
| `--dry-run` | Show changes without applying | False |
| `--install` | Install pre-commit hooks after update | False |
| `--check-only` | Check if update needed, don't modify | False |

### Programmatic Usage

```python
from update_precommit import PreCommitUpdater

# Initialize
updater = PreCommitUpdater(
    config_path='.pre-commit-config.yaml',
    test_dir='.sdlc/tests/patterns'
)

# Check if pre-commit is installed
if updater.check_precommit_installed():
    print("pre-commit is installed")

# Load existing config
config = updater.load_config()

# Update config (idempotent)
updated_config, changed = updater.update_config(config)

# Validate
is_valid, error = updater.validate_config(updated_config)

# Write if valid
if is_valid:
    updater.write_config(updated_config)

# Or use the high-level method
success, changed = updater.update(dry_run=False, install=False)
```

### Acceptance Tests

**Test 1: New repository without pre-commit config**
```bash
# Create empty repo
mkdir new-repo && cd new-repo

# Run updater
python3 update_precommit.py --test-dir .sdlc/tests/patterns

# Result: Creates valid .pre-commit-config.yaml with pattern tests
```

**Test 2: Existing repository with other hooks**
```bash
# Existing .pre-commit-config.yaml with black formatter
repos:
  - repo: https://github.com/psf/black
    hooks:
      - id: black

# Run updater
python3 update_precommit.py

# Result: Adds pattern tests, preserves black hook
repos:
  - repo: https://github.com/psf/black
    hooks:
      - id: black
  - repo: local
    hooks:
      - id: pattern-defeat-tests
        # ... pattern test config
```

### Error Handling

- **Missing pre-commit**: Warns if `--install` flag used without pre-commit installed
- **Invalid YAML**: Validates before writing, reports errors clearly
- **Missing test directory**: Warns but creates config (tests can be added later)
- **Parse errors**: Falls back to default config with warning

### Integration with Pattern Detector

```bash
# Complete workflow with pre-commit integration
python3 collect.py --days 30 | \
  python3 analyze.py --mock | \
  python3 generate_tests.py --mock && \
  python3 update_precommit.py --install

# Now git commits will run pattern defeat tests automatically
git add .
git commit -m "Add feature"
# → pre-commit runs pytest .sdlc/tests/patterns/ -v
```

## Next Steps

After collecting, analyzing, and generating proposals:

1. Review the proposals in `progress/pattern-proposals-{date}.md`
2. Apply approved updates to agent character sheets in `Agentic_SDLC/agents/`
3. Generate defeat tests with `generate_tests.py` (REQ-062) ✅
4. Update pre-commit hooks with `update_precommit.py` (REQ-065) ✅
5. Add memory entries with `update_memory.py` (REQ-066) ✅
6. Run defeat tests to verify patterns are caught

Future automation:
- `cli.py` - Interactive CLI tool (REQ-064)
- `weekly-refactor.sh` - Automated weekly workflow (REQ-067)

See the Pattern Detection documentation for the complete workflow.
