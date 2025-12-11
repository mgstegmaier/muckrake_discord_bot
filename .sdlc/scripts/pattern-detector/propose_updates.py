#!/usr/bin/env python3
"""
Agent Prompt Update Proposal Generator

Generates proposed updates to agent character sheets based on identified patterns.
Creates reviewable markdown with:
- Non-Negotiable entries
- Discipline checklist items
- Memory entries
- Defeat test references

Usage:
    python propose_updates.py [--input FILE] [--output FILE] [--mock]

Input:
    JSON file from analyze.py with structure:
    {
        "timestamp": "ISO-8601 datetime",
        "patterns": [
            {
                "name": "Pattern name",
                "description": "Detailed description",
                "evidence": ["specific files/commits"],
                "frequency": "daily" | "weekly" | "per-feature" | "monthly",
                "impact": "high" | "medium" | "low",
                "root_cause": "Hypothesis about why",
                "score": float
            }
        ]
    }

Output:
    Markdown file in progress/pattern-proposals-{date}.md with reviewable format
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# Template for generating proposals using Claude
PROPOSAL_GENERATION_PROMPT = """You are an expert in software development best practices and agent prompt engineering. You are helping improve AI agent character sheets based on identified anti-patterns.

**Pattern Detected:**
{pattern_json}

**Agent Type:** {agent_type}

**Your Task:**
Generate three specific, actionable updates to the {agent_type} agent's character sheet to prevent this pattern from recurring:

1. **Non-Negotiable Test Entry**: A checklist item for what to ALWAYS verify/check (1 line, starts with "NEVER" or "ALWAYS")
2. **Discipline Item**: A procedural step for what to do before/during coding (1-2 lines, actionable)
3. **Memory Entry**: A concise learning statement (1 sentence, starts with "Learned:")

**Output Format** (return ONLY valid JSON, no markdown):
{{
  "non_negotiable": "- [ ] NEVER use .get(key, default) without explicit validation",
  "discipline": "Before using dictionary access, verify the key exists or handle missing explicitly",
  "memory": "Learned: Silent fallbacks hide bugs. Always validate explicitly.",
  "memory_tags": ["anti-patterns", "defeat-test", "pattern-name"]
}}

**Guidelines:**
- Be specific and actionable
- Reference the pattern by name in memory tags
- Use imperative language for discipline items
- Non-negotiables should be testable
- Memory should capture the core lesson learned
"""

# Agent type mapping based on pattern characteristics
AGENT_TYPE_RULES = [
    # Code patterns -> Dev agent
    {
        'keywords': ['code', 'function', 'variable', 'error handling', 'exception',
                     'validation', 'fallback', 'api', 'database', 'testing'],
        'agent': 'Dev',
        'priority': 1
    },
    # Documentation patterns -> Research agent
    {
        'keywords': ['documentation', 'comment', 'readme', 'docstring', 'markdown',
                     'spec', 'requirements', 'analysis'],
        'agent': 'Research',
        'priority': 2
    },
    # Process patterns -> Project-Manager agent
    {
        'keywords': ['workflow', 'process', 'coordination', 'planning', 'roadmap',
                     'prioritization', 'scheduling', 'handoff'],
        'agent': 'Project-Manager',
        'priority': 2
    },
    # Code review patterns -> Code-Reviewer agent
    {
        'keywords': ['review', 'quality', 'merge', 'pr', 'pull request', 'approval',
                     'standards'],
        'agent': 'Code-Reviewer',
        'priority': 3
    },
    # Release patterns -> Release-Manager agent
    {
        'keywords': ['release', 'deploy', 'version', 'changelog', 'rollback',
                     'production'],
        'agent': 'Release-Manager',
        'priority': 3
    }
]

# Mock proposals for testing without API calls
MOCK_PROPOSALS = {
    "Silent Fallback Pattern": {
        "agent": "Dev",
        "non_negotiable": "- [ ] NEVER use .get(key, default) without explicit validation",
        "discipline": "Before using dictionary access, verify the key exists or handle missing keys explicitly with proper error messages",
        "memory": "Learned: Silent fallbacks hide bugs by masking missing data. Always validate required fields explicitly before use.",
        "memory_tags": ["anti-patterns", "defeat-test", "silent-fallback"]
    },
    "Missing Error Context": {
        "agent": "Dev",
        "non_negotiable": "- [ ] ALWAYS include relevant context in error messages (what failed, what data was involved)",
        "discipline": "When raising exceptions, include the operation name and relevant identifiers (IDs, names) in the error message",
        "memory": "Learned: Generic error messages make debugging difficult. Include specific context about what failed and why.",
        "memory_tags": ["anti-patterns", "defeat-test", "error-context"]
    },
    "Inconsistent File Path Handling": {
        "agent": "Dev",
        "non_negotiable": "- [ ] ALWAYS use absolute paths in scripts, never rely on working directory assumptions",
        "discipline": "Convert relative paths to absolute at entry point using Path(__file__).parent or similar",
        "memory": "Learned: Mixed path handling causes failures in different execution contexts. Standardize on absolute paths.",
        "memory_tags": ["anti-patterns", "defeat-test", "path-handling"]
    }
}


class ProposalGenerator:
    """Generates agent prompt update proposals from identified patterns."""

    def __init__(self, api_key: Optional[str] = None, use_cli: bool = True, mock: bool = False):
        """
        Initialize proposal generator.

        Args:
            api_key: Anthropic API key (optional if using CLI or environment variable)
            use_cli: Use Claude CLI instead of Python SDK (default: True)
            mock: Use mock data instead of real API calls (default: False)
        """
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        self.use_cli = use_cli
        self.mock = mock

    def classify_pattern_agent(self, pattern: Dict[str, Any]) -> str:
        """
        Determine which agent(s) should receive this pattern update.

        Args:
            pattern: Pattern dictionary with name, description, etc.

        Returns:
            Agent name (Dev, Research, Project-Manager, etc.)
        """
        pattern_text = f"{pattern.get('name', '')} {pattern.get('description', '')} {pattern.get('root_cause', '')}".lower()

        # Score each agent type
        scores = []
        for rule in AGENT_TYPE_RULES:
            keyword_matches = sum(1 for kw in rule['keywords'] if kw in pattern_text)
            if keyword_matches > 0:
                # Higher priority (lower number) gets bonus
                score = keyword_matches * (4 - rule['priority'])
                scores.append((score, rule['agent']))

        # Return agent with highest score, default to Dev if no matches
        if scores:
            scores.sort(reverse=True)
            return scores[0][1]
        return 'Dev'

    def _call_claude_cli(self, prompt: str) -> str:
        """Call Claude using the CLI."""
        try:
            result = subprocess.run(
                ['claude', '-p', prompt],
                capture_output=True,
                text=True,
                check=True,
                timeout=60
            )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            raise Exception("Claude CLI call timed out after 60 seconds")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Claude CLI call failed: {e.stderr}")

    def _call_claude_sdk(self, prompt: str) -> str:
        """Call Claude using the Python SDK."""
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
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.content[0].text

    def _parse_claude_response(self, response: str) -> Dict[str, Any]:
        """Parse Claude's JSON response."""
        response = response.strip()
        if response.startswith('```'):
            lines = response.split('\n')
            lines = lines[1:]
            if lines[-1].strip() == '```':
                lines = lines[:-1]
            response = '\n'.join(lines)

        return json.loads(response)

    def generate_proposal(self, pattern: Dict[str, Any], agent: str) -> Dict[str, Any]:
        """
        Generate update proposal for a specific pattern and agent.

        Args:
            pattern: Pattern dictionary from analyze.py
            agent: Target agent name (Dev, Research, etc.)

        Returns:
            Proposal dictionary with non_negotiable, discipline, memory, memory_tags
        """
        if self.mock:
            # Use mock proposals
            pattern_name = pattern.get('name', '')
            if pattern_name in MOCK_PROPOSALS:
                return MOCK_PROPOSALS[pattern_name]
            # Generic fallback for mock mode
            return {
                "non_negotiable": f"- [ ] ALWAYS check for {pattern_name} pattern",
                "discipline": f"Before implementing, verify this doesn't introduce {pattern_name}",
                "memory": f"Learned: {pattern.get('description', 'Pattern detected')}",
                "memory_tags": ["anti-patterns", "defeat-test", "generic"]
            }

        # Generate proposal using Claude
        pattern_json = json.dumps({
            'name': pattern.get('name'),
            'description': pattern.get('description'),
            'impact': pattern.get('impact'),
            'frequency': pattern.get('frequency'),
            'root_cause': pattern.get('root_cause')
        }, indent=2)

        prompt = PROPOSAL_GENERATION_PROMPT.format(
            pattern_json=pattern_json,
            agent_type=agent
        )

        try:
            if self.use_cli:
                response = self._call_claude_cli(prompt)
            else:
                response = self._call_claude_sdk(prompt)

            proposal = self._parse_claude_response(response)
            return proposal

        except Exception as e:
            print(f"Warning: Failed to generate proposal for {pattern.get('name')}: {e}", file=sys.stderr)
            # Fallback proposal
            return {
                "non_negotiable": f"- [ ] Check for pattern: {pattern.get('name')}",
                "discipline": f"Verify this pattern doesn't occur: {pattern.get('description')}",
                "memory": f"Learned: {pattern.get('description', 'Pattern detected')}",
                "memory_tags": ["anti-patterns", "defeat-test", "auto-generated"]
            }

    def generate_defeat_test_name(self, pattern: Dict[str, Any]) -> str:
        """
        Generate standardized defeat test filename from pattern name.

        Args:
            pattern: Pattern dictionary

        Returns:
            Test filename (e.g., "test_no_silent_fallbacks.py")
        """
        name = pattern.get('name', 'unknown_pattern')
        # Convert to snake_case
        name = name.lower()
        name = name.replace(' ', '_')
        # Remove special characters
        name = ''.join(c if c.isalnum() or c == '_' else '' for c in name)
        return f"test_no_{name}.py"

    def format_proposal_markdown(self, patterns: List[Dict[str, Any]], proposals: List[Dict[str, Any]]) -> str:
        """
        Format proposals as reviewable markdown.

        Args:
            patterns: List of pattern dictionaries from analyze.py
            proposals: List of generated proposal dictionaries

        Returns:
            Formatted markdown string
        """
        date = datetime.now().strftime('%Y-%m-%d')
        lines = [
            f"# Pattern Proposals - {date}",
            "",
            "This document contains proposed updates to agent character sheets based on detected patterns.",
            "Review each proposal and decide whether to apply it to the corresponding agent.",
            "",
            "---",
            ""
        ]

        for pattern, proposal in zip(patterns, proposals):
            impact = pattern.get('impact', 'unknown').upper()
            score = pattern.get('score', 0.0)
            agent = proposal.get('agent', 'Unknown')

            lines.extend([
                f"## Pattern: {pattern.get('name')} (Score: {score:.1f}, {impact} impact)",
                "",
                f"**Description:** {pattern.get('description')}",
                "",
                f"**Frequency:** {pattern.get('frequency')}",
                "",
                f"**Root Cause:** {pattern.get('root_cause')}",
                "",
                "**Evidence:**",
            ])

            for evidence in pattern.get('evidence', []):
                lines.append(f"- {evidence}")

            lines.extend([
                "",
                f"### Proposed Update for Agent: {agent}",
                "",
                "#### Non-Negotiable Addition",
                "```",
                proposal.get('non_negotiable', ''),
                "```",
                "",
                "#### Discipline Item",
                "```",
                proposal.get('discipline', ''),
                "```",
                "",
                "#### Memory Entry",
                "```json",
                json.dumps({
                    "content": proposal.get('memory', ''),
                    "category": "anti-patterns",
                    "tags": proposal.get('memory_tags', [])
                }, indent=2),
                "```",
                "",
                "#### Related Defeat Test",
                f"`{self.generate_defeat_test_name(pattern)}`",
                "",
                "---",
                ""
            ])

        return '\n'.join(lines)

    def generate_proposals(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate all proposals from analysis results.

        Args:
            analysis: Analysis results from analyze.py

        Returns:
            Dictionary with proposals and metadata
        """
        patterns = analysis.get('patterns', [])
        print(f"Generating proposals for {len(patterns)} patterns...", file=sys.stderr)

        proposals = []
        for i, pattern in enumerate(patterns, 1):
            print(f"  [{i}/{len(patterns)}] Processing: {pattern.get('name')}", file=sys.stderr)

            # Classify which agent should receive this update
            agent = self.classify_pattern_agent(pattern)
            print(f"    -> Agent: {agent}", file=sys.stderr)

            # Generate proposal
            proposal = self.generate_proposal(pattern, agent)
            proposal['agent'] = agent
            proposal['pattern_name'] = pattern.get('name')
            proposal['pattern_score'] = pattern.get('score')

            proposals.append(proposal)

        # Generate markdown output
        markdown = self.format_proposal_markdown(patterns, proposals)

        result = {
            'timestamp': datetime.now().isoformat(),
            'total_proposals': len(proposals),
            'proposals': proposals,
            'markdown': markdown,
            'metadata': {
                'api_method': 'mock' if self.mock else ('cli' if self.use_cli else 'sdk'),
                'patterns_processed': len(patterns)
            }
        }

        return result


def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description='Generate agent prompt update proposals from pattern analysis.'
    )
    parser.add_argument(
        '--input',
        help='Input JSON file from analyze.py (default: read from stdin)'
    )
    parser.add_argument(
        '--output',
        help='Output markdown file path (default: progress/pattern-proposals-{date}.md)'
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
        '--pretty',
        action='store_true',
        help='Pretty-print JSON output (if outputting JSON)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output JSON instead of markdown'
    )

    args = parser.parse_args()

    try:
        # Read input
        if args.input:
            with open(args.input, 'r') as f:
                analysis = json.load(f)
        else:
            analysis = json.load(sys.stdin)

        # Initialize generator
        generator = ProposalGenerator(
            api_key=args.api_key,
            use_cli=not args.use_sdk,
            mock=args.mock
        )

        # Generate proposals
        results = generator.generate_proposals(analysis)

        # Determine output format and path
        if args.json:
            # Output JSON
            if args.pretty:
                output = json.dumps(results, indent=2)
            else:
                output = json.dumps(results)

            if args.output:
                with open(args.output, 'w') as f:
                    f.write(output)
                print(f"\nJSON results written to {args.output}", file=sys.stderr)
            else:
                print(output)
        else:
            # Output markdown (default)
            output = results['markdown']

            if args.output:
                output_path = args.output
            else:
                # Default to progress directory
                project_root = Path(__file__).parent.parent.parent.parent
                progress_dir = project_root / 'progress'
                progress_dir.mkdir(exist_ok=True)

                date_str = datetime.now().strftime('%Y-%m-%d')
                output_path = progress_dir / f'pattern-proposals-{date_str}.md'

            with open(output_path, 'w') as f:
                f.write(output)

            print(f"\nProposals written to {output_path}", file=sys.stderr)

        # Print summary
        print("\n=== Proposal Generation Summary ===", file=sys.stderr)
        print(f"Patterns processed: {results['metadata']['patterns_processed']}", file=sys.stderr)
        print(f"Proposals generated: {results['total_proposals']}", file=sys.stderr)
        print(f"API method: {results['metadata']['api_method']}", file=sys.stderr)

        if results['proposals']:
            print("\nProposals by agent:", file=sys.stderr)
            agent_counts = {}
            for proposal in results['proposals']:
                agent = proposal.get('agent', 'Unknown')
                agent_counts[agent] = agent_counts.get(agent, 0) + 1

            for agent, count in sorted(agent_counts.items()):
                print(f"  {agent}: {count} proposals", file=sys.stderr)

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
