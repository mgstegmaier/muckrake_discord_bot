#!/usr/bin/env python3
"""
Pattern Detection AI Analysis Module

Uses Claude to analyze collected signals and identify concrete patterns with supporting evidence.

Usage:
    python analyze.py [--input FILE] [--output FILE] [--mock] [--top-n N]

Input:
    JSON file from collect.py with structure:
    {
        "git_signals": [...],
        "memory_signals": [...],
        "churn_signals": [...]
    }

Output:
    JSON file with structure:
    {
        "timestamp": "ISO-8601 datetime",
        "patterns": [
            {
                "name": "Pattern name",
                "description": "Detailed description",
                "evidence": ["specific files/commits"],
                "frequency": "daily" | "weekly" | "per-feature",
                "impact": "high" | "medium" | "low",
                "root_cause": "Hypothesis about why this happens",
                "score": float (impact × frequency numeric score)
            }
        ]
    }
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# Analysis prompt template
ANALYSIS_PROMPT = """You are a software engineering expert analyzing code development patterns. You have been given signals from:

1. **Git history** - commits that fix bugs, repeated modifications to the same files
2. **Agent memory** - recurring learnings and patterns agents have encountered
3. **Code churn** - files with high modification frequency

Your task is to identify concrete anti-patterns and development issues that are happening repeatedly. For each pattern you identify, provide:

1. **Name**: Short, descriptive name for the pattern
2. **Description**: What is happening (be specific, not vague)
3. **Evidence**: Specific files, commits, or memory entries that show this pattern
4. **Frequency**: How often this occurs (daily, weekly, per-feature, monthly)
5. **Impact**: High (blocks work/causes bugs), Medium (slows development), Low (minor annoyance)
6. **Root Cause**: Your hypothesis about WHY this pattern keeps happening

**IMPORTANT**:
- Only identify patterns with strong evidence (3+ occurrences)
- Be specific - reference actual files and commits
- Focus on actionable patterns that can be prevented
- Patterns should be about developer behavior or code structure, not business logic

**INPUT SIGNALS**:

{signals}

**OUTPUT FORMAT**:
Return ONLY valid JSON with this structure (no markdown, no commentary):
{{
  "patterns": [
    {{
      "name": "Pattern Name",
      "description": "Detailed description of what's happening",
      "evidence": ["file.py: modified 7 times", "commit abc123: fixed error handling"],
      "frequency": "weekly",
      "impact": "high",
      "root_cause": "Why this keeps happening"
    }}
  ]
}}

Identify up to 10 patterns, ranked by (impact × frequency).
"""

# Mock patterns for testing without API calls
MOCK_PATTERNS = {
    "patterns": [
        {
            "name": "Silent Fallback Pattern",
            "description": "Using .get() with default values instead of explicit validation, leading to silent failures and hard-to-debug issues",
            "evidence": [
                "Skills/ai-vendor-evaluation/SKILL.md: modified 5 times with validation fixes",
                "Skills/complex-excel-builder/SKILL.md: 3 commits adding error handling",
                "Agent memory: 'learned to validate explicitly' appears 4 times"
            ],
            "frequency": "weekly",
            "impact": "high",
            "root_cause": "Developers default to using .get() for convenience without considering edge cases. Pattern persists because linters don't catch it and it only fails in production."
        },
        {
            "name": "Missing Error Context",
            "description": "Raising exceptions without providing context about what operation failed or what data was involved",
            "evidence": [
                "Skills/xlsx-editor/SKILL.md: 3 commits adding context to exceptions",
                "Skills/SDLC/roadmap-workflow/SKILL.md: modified 4 times",
                "Git: 'fix error message' appears in 6 commits"
            ],
            "frequency": "per-feature",
            "impact": "medium",
            "root_cause": "Developers focus on happy path first and add minimal error handling. When bugs occur in production, lack of context makes debugging difficult."
        },
        {
            "name": "Inconsistent File Path Handling",
            "description": "Mixing relative and absolute paths, causing failures in different execution contexts",
            "evidence": [
                "Agentic_SDLC/scripts/: multiple scripts modified for path handling",
                "Git: 'fix path' in 4 commits over 2 weeks"
            ],
            "frequency": "monthly",
            "impact": "medium",
            "root_cause": "No standard established for path handling. Each developer makes different assumptions about working directory."
        }
    ]
}


class PatternAnalyzer:
    """Analyzes collected signals using Claude API or CLI to identify patterns."""

    def __init__(self, api_key: Optional[str] = None, use_cli: bool = True, mock: bool = False):
        """
        Initialize pattern analyzer.

        Args:
            api_key: Anthropic API key (optional if using CLI or environment variable)
            use_cli: Use Claude CLI instead of Python SDK (default: True)
            mock: Use mock data instead of real API calls (default: False)
        """
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        self.use_cli = use_cli
        self.mock = mock
        self.max_retries = 3
        self.retry_delay = 2  # seconds

    def _call_claude_cli(self, prompt: str) -> str:
        """
        Call Claude using the CLI.

        Args:
            prompt: Analysis prompt

        Returns:
            Claude's response

        Raises:
            subprocess.CalledProcessError: If CLI call fails
        """
        try:
            result = subprocess.run(
                ['claude', '-p', prompt],
                capture_output=True,
                text=True,
                check=True,
                timeout=120  # 2 minute timeout
            )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            raise Exception("Claude CLI call timed out after 120 seconds")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Claude CLI call failed: {e.stderr}")

    def _call_claude_sdk(self, prompt: str) -> str:
        """
        Call Claude using the Python SDK.

        Args:
            prompt: Analysis prompt

        Returns:
            Claude's response

        Raises:
            ImportError: If anthropic SDK is not installed
            Exception: If API call fails
        """
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "anthropic SDK not installed. Install with: pip install anthropic\n"
                "Or use --use-cli flag to use the Claude CLI instead."
            )

        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable not set and no API key provided"
            )

        client = anthropic.Anthropic(api_key=self.api_key)

        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4000,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.content[0].text

    def _call_claude_with_retry(self, prompt: str) -> str:
        """
        Call Claude with retry logic for transient failures.

        Args:
            prompt: Analysis prompt

        Returns:
            Claude's response

        Raises:
            Exception: If all retry attempts fail
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                if self.use_cli:
                    return self._call_claude_cli(prompt)
                else:
                    return self._call_claude_sdk(prompt)
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (attempt + 1)
                    print(
                        f"Warning: API call failed (attempt {attempt + 1}/{self.max_retries}): {e}",
                        file=sys.stderr
                    )
                    print(f"Retrying in {wait_time} seconds...", file=sys.stderr)
                    time.sleep(wait_time)

        raise Exception(f"All {self.max_retries} retry attempts failed. Last error: {last_error}")

    def _parse_claude_response(self, response: str) -> Dict[str, Any]:
        """
        Parse Claude's JSON response.

        Args:
            response: Raw response from Claude

        Returns:
            Parsed JSON data

        Raises:
            json.JSONDecodeError: If response is not valid JSON
        """
        # Claude sometimes wraps JSON in markdown code blocks
        response = response.strip()
        if response.startswith('```'):
            # Remove markdown code block markers
            lines = response.split('\n')
            # Remove first line (```json or ```)
            lines = lines[1:]
            # Remove last line (```)
            if lines[-1].strip() == '```':
                lines = lines[:-1]
            response = '\n'.join(lines)

        return json.loads(response)

    def _calculate_pattern_score(self, pattern: Dict[str, Any]) -> float:
        """
        Calculate numeric score for pattern ranking.

        Score = impact_value × frequency_value

        Args:
            pattern: Pattern dictionary

        Returns:
            Numeric score (higher is more important)
        """
        # Impact scoring
        impact_scores = {
            'high': 3.0,
            'medium': 2.0,
            'low': 1.0
        }
        impact = pattern.get('impact', 'low').lower()
        impact_value = impact_scores.get(impact, 1.0)

        # Frequency scoring
        frequency_scores = {
            'daily': 4.0,
            'weekly': 3.0,
            'per-feature': 2.0,
            'monthly': 1.0
        }
        frequency = pattern.get('frequency', 'monthly').lower()
        frequency_value = frequency_scores.get(frequency, 1.0)

        return impact_value * frequency_value

    def analyze(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze collected signals to identify patterns.

        Args:
            signals: Dictionary from collect.py with git_signals, memory_signals, churn_signals

        Returns:
            Dictionary with ranked patterns:
            {
                "timestamp": "ISO-8601 datetime",
                "patterns": [pattern_objects],
                "metadata": {
                    "total_patterns_found": N,
                    "api_method": "cli" | "sdk" | "mock",
                    "signals_analyzed": {
                        "git_signals": N,
                        "memory_signals": N,
                        "churn_signals": N
                    }
                }
            }
        """
        print("Analyzing patterns with Claude...", file=sys.stderr)

        # Handle mock mode
        if self.mock:
            print("Using mock patterns (--mock flag enabled)", file=sys.stderr)
            patterns = MOCK_PATTERNS['patterns']
        else:
            # Prepare signals summary for prompt
            signals_summary = json.dumps({
                'git_signals': signals.get('git_signals', [])[:20],  # Limit to avoid token limits
                'memory_signals': signals.get('memory_signals', [])[:10],
                'churn_signals': signals.get('churn_signals', [])[:10],
                'summary': signals.get('summary', {})
            }, indent=2)

            # Create analysis prompt
            prompt = ANALYSIS_PROMPT.format(signals=signals_summary)

            # Call Claude with retry logic
            try:
                response = self._call_claude_with_retry(prompt)
                parsed = self._parse_claude_response(response)
                patterns = parsed.get('patterns', [])
                print(f"Claude identified {len(patterns)} patterns", file=sys.stderr)
            except Exception as e:
                print(f"Error calling Claude API: {e}", file=sys.stderr)
                print("Falling back to empty pattern list", file=sys.stderr)
                patterns = []

        # Calculate scores and rank patterns
        for pattern in patterns:
            pattern['score'] = self._calculate_pattern_score(pattern)

        # Sort by score (descending)
        patterns.sort(key=lambda p: p['score'], reverse=True)

        # Prepare results
        result = {
            'timestamp': datetime.now().isoformat(),
            'patterns': patterns,
            'metadata': {
                'total_patterns_found': len(patterns),
                'api_method': 'mock' if self.mock else ('cli' if self.use_cli else 'sdk'),
                'signals_analyzed': {
                    'git_signals': len(signals.get('git_signals', [])),
                    'memory_signals': len(signals.get('memory_signals', [])),
                    'churn_signals': len(signals.get('churn_signals', []))
                }
            }
        }

        return result


def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description='Analyze pattern detection signals using Claude AI.'
    )
    parser.add_argument(
        '--input',
        help='Input JSON file from collect.py (default: read from stdin)'
    )
    parser.add_argument(
        '--output',
        help='Output file path (default: print to stdout)'
    )
    parser.add_argument(
        '--mock',
        action='store_true',
        help='Use mock data instead of calling Claude API'
    )
    parser.add_argument(
        '--use-sdk',
        action='store_true',
        help='Use Anthropic Python SDK instead of Claude CLI'
    )
    parser.add_argument(
        '--api-key',
        help='Anthropic API key (default: use ANTHROPIC_API_KEY env var)'
    )
    parser.add_argument(
        '--top-n',
        type=int,
        default=5,
        help='Return top N patterns (default: 5)'
    )
    parser.add_argument(
        '--pretty',
        action='store_true',
        help='Pretty-print JSON output'
    )

    args = parser.parse_args()

    try:
        # Read input
        if args.input:
            with open(args.input, 'r') as f:
                signals = json.load(f)
        else:
            signals = json.load(sys.stdin)

        # Initialize analyzer
        analyzer = PatternAnalyzer(
            api_key=args.api_key,
            use_cli=not args.use_sdk,
            mock=args.mock
        )

        # Analyze patterns
        results = analyzer.analyze(signals)

        # Limit to top N
        results['patterns'] = results['patterns'][:args.top_n]
        results['metadata']['patterns_returned'] = len(results['patterns'])

        # Format output
        if args.pretty:
            output = json.dumps(results, indent=2)
        else:
            output = json.dumps(results)

        # Write output
        if args.output:
            with open(args.output, 'w') as f:
                f.write(output)
            print(f"\nResults written to {args.output}", file=sys.stderr)
        else:
            print(output)

        # Print summary
        print("\n=== Analysis Summary ===", file=sys.stderr)
        print(f"Patterns identified: {results['metadata']['total_patterns_found']}", file=sys.stderr)
        print(f"Patterns returned: {results['metadata']['patterns_returned']}", file=sys.stderr)
        print(f"API method: {results['metadata']['api_method']}", file=sys.stderr)

        if results['patterns']:
            print("\nTop patterns:", file=sys.stderr)
            for i, pattern in enumerate(results['patterns'][:5], 1):
                print(
                    f"  {i}. [{pattern['impact'].upper()}] {pattern['name']} "
                    f"(score: {pattern['score']:.1f})",
                    file=sys.stderr
                )

        return 0

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
