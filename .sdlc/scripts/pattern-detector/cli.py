#!/usr/bin/env python3
"""
Pattern Hunter CLI - Interactive Pattern Detection Workflow

Orchestrates the complete pattern detection and defeat workflow:
1. collect - Gather signals from git, memory, code churn
2. analyze - AI-powered pattern identification
3. generate - Create defeat tests
4. apply - Update pre-commit hooks and agent memory

Usage:
    # Full interactive workflow
    ./hunt-patterns hunt

    # Non-interactive (auto-approve all)
    ./hunt-patterns hunt --auto

    # Preview without changes
    ./hunt-patterns hunt --dry-run

    # Individual steps
    ./hunt-patterns collect --days 30
    ./hunt-patterns analyze --input signals.json
    ./hunt-patterns generate --input patterns.json
    ./hunt-patterns apply --input proposals.json

Features:
    - Interactive review with y/n prompts
    - Progress indicators
    - Color-coded output
    - State preservation between runs
    - Dry-run mode for safe previewing
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ANSI color codes for better UX
class Colors:
    """ANSI color codes for terminal output."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    # Foreground colors
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # Background colors
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'

    @classmethod
    def disable(cls):
        """Disable colors (for non-TTY output)."""
        cls.RESET = ''
        cls.BOLD = ''
        cls.DIM = ''
        cls.RED = ''
        cls.GREEN = ''
        cls.YELLOW = ''
        cls.BLUE = ''
        cls.MAGENTA = ''
        cls.CYAN = ''
        cls.WHITE = ''
        cls.BG_RED = ''
        cls.BG_GREEN = ''
        cls.BG_YELLOW = ''


# Disable colors if not a TTY
if not sys.stdout.isatty():
    Colors.disable()


class PatternHunterCLI:
    """Main CLI orchestrator for pattern detection workflow."""

    def __init__(self, repo_path: Optional[Path] = None, dry_run: bool = False, auto: bool = False):
        """
        Initialize Pattern Hunter CLI.

        Args:
            repo_path: Path to repository (default: current directory)
            dry_run: If True, show plans without executing
            auto: If True, auto-approve all prompts
        """
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self.dry_run = dry_run
        self.auto = auto
        self.state_dir = self.repo_path / '.sdlc' / 'pattern-hunter'
        self.state_file = self.state_dir / 'state.json'

        # Ensure state directory exists
        self.state_dir.mkdir(parents=True, exist_ok=True)

        # Load or initialize state
        self.state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        """Load state from previous runs."""
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    return json.load(f)
            except Exception as e:
                self._print_warning(f"Failed to load state: {e}")

        return {
            'last_run': None,
            'last_collection': None,
            'last_analysis': None,
            'patterns_pending_review': [],
            'patterns_approved': []
        }

    def _save_state(self):
        """Save state for future runs."""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            self._print_warning(f"Failed to save state: {e}")

    # Output formatting helpers

    def _print_header(self, message: str):
        """Print section header."""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{message}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.RESET}\n")

    def _print_subheader(self, message: str):
        """Print subsection header."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{message}{Colors.RESET}")
        print(f"{Colors.BLUE}{'-' * 40}{Colors.RESET}")

    def _print_success(self, message: str):
        """Print success message."""
        print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")

    def _print_error(self, message: str):
        """Print error message."""
        print(f"{Colors.RED}✗ {message}{Colors.RESET}", file=sys.stderr)

    def _print_warning(self, message: str):
        """Print warning message."""
        print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")

    def _print_info(self, message: str):
        """Print info message."""
        print(f"{Colors.CYAN}→ {message}{Colors.RESET}")

    def _print_dim(self, message: str):
        """Print dimmed message."""
        print(f"{Colors.DIM}{message}{Colors.RESET}")

    def _progress(self, message: str, delay: float = 0.5):
        """Show progress indicator."""
        print(f"{Colors.YELLOW}⏳ {message}...{Colors.RESET}", end='', flush=True)
        time.sleep(delay)
        print(f" {Colors.GREEN}Done{Colors.RESET}")

    def _ask_yes_no(self, question: str, default: bool = True) -> bool:
        """
        Ask user a yes/no question.

        Args:
            question: Question to ask
            default: Default answer if user presses Enter

        Returns:
            True if yes, False if no
        """
        if self.auto:
            answer = "yes" if default else "no"
            print(f"{Colors.CYAN}{question} [auto: {answer}]{Colors.RESET}")
            return default

        suffix = " [Y/n]" if default else " [y/N]"
        while True:
            response = input(f"{Colors.YELLOW}{question}{suffix}: {Colors.RESET}").strip().lower()

            if not response:
                return default

            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print(f"{Colors.RED}Please answer 'y' or 'n'{Colors.RESET}")

    def _ask_choice(self, question: str, choices: List[str]) -> Optional[str]:
        """
        Ask user to choose from a list.

        Args:
            question: Question to ask
            choices: List of valid choices

        Returns:
            Selected choice or None if skipped
        """
        if self.auto:
            choice = choices[0] if choices else None
            print(f"{Colors.CYAN}{question} [auto: {choice}]{Colors.RESET}")
            return choice

        print(f"{Colors.YELLOW}{question}{Colors.RESET}")
        for i, choice in enumerate(choices, 1):
            print(f"  {i}. {choice}")
        print(f"  0. Skip")

        while True:
            response = input(f"{Colors.YELLOW}Choice [1-{len(choices)}, 0 to skip]: {Colors.RESET}").strip()

            if response == '0':
                return None

            try:
                idx = int(response) - 1
                if 0 <= idx < len(choices):
                    return choices[idx]
            except ValueError:
                pass

            print(f"{Colors.RED}Invalid choice. Please enter a number 0-{len(choices)}{Colors.RESET}")

    # Workflow orchestration

    def cmd_hunt(self, args: argparse.Namespace) -> int:
        """
        Run full pattern hunting workflow.

        Steps:
        1. Collect signals
        2. Analyze patterns
        3. Review patterns (interactive)
        4. Generate defeat tests
        5. Review proposals (interactive)
        6. Apply updates

        Returns:
            0 on success, non-zero on error
        """
        self._print_header("🎯 PATTERN HUNT - Full Workflow")

        if self.dry_run:
            self._print_warning("DRY RUN MODE - No files will be modified")

        if self.auto:
            self._print_warning("AUTO MODE - All prompts will be auto-approved")

        # Step 1: Collect signals
        self._print_subheader("Step 1: Collecting Signals")
        signals_file = self.state_dir / f'signals-{datetime.now().strftime("%Y%m%d-%H%M%S")}.json'

        result = self._run_collect(signals_file, args.days)
        if result != 0:
            self._print_error("Signal collection failed")
            return result

        self.state['last_collection'] = str(signals_file)
        self._save_state()

        # Step 2: Analyze patterns
        self._print_subheader("Step 2: Analyzing Patterns")
        patterns_file = self.state_dir / f'patterns-{datetime.now().strftime("%Y%m%d-%H%M%S")}.json'

        result = self._run_analyze(signals_file, patterns_file, args.top_n)
        if result != 0:
            self._print_error("Pattern analysis failed")
            return result

        self.state['last_analysis'] = str(patterns_file)
        self._save_state()

        # In dry-run mode, create mock patterns for testing
        if self.dry_run:
            self._print_info("Dry-run mode: Using mock patterns")
            patterns = [
                {
                    'name': 'Mock Pattern 1',
                    'description': 'This is a mock pattern for dry-run testing',
                    'evidence': ['file1.py', 'file2.py'],
                    'frequency': 'weekly',
                    'impact': 'high',
                    'root_cause': 'Mock root cause'
                }
            ]
        else:
            # Load patterns for review
            with open(patterns_file) as f:
                patterns_data = json.load(f)

            patterns = patterns_data.get('patterns', [])

        if not patterns:
            self._print_warning("No patterns identified. Hunt complete.")
            return 0

        # Step 3: Review patterns interactively
        self._print_subheader("Step 3: Pattern Review")
        self._print_info(f"Found {len(patterns)} patterns")

        patterns_to_process = self._review_patterns(patterns)

        if not patterns_to_process:
            self._print_warning("No patterns selected for processing")
            return 0

        # Step 4: Generate defeat tests
        self._print_subheader("Step 4: Generating Defeat Tests")

        result = self._run_generate_tests(patterns_to_process)
        if result != 0:
            self._print_error("Test generation failed")
            return result

        # Step 5: Generate proposals
        self._print_subheader("Step 5: Generating Agent Updates")
        proposals_file = self.state_dir / f'proposals-{datetime.now().strftime("%Y%m%d-%H%M%S")}.json'

        result = self._run_propose_updates(patterns_to_process, proposals_file)
        if result != 0:
            self._print_error("Proposal generation failed")
            return result

        # Step 6: Review and apply
        self._print_subheader("Step 6: Review & Apply Updates")

        result = self._review_and_apply(proposals_file)
        if result != 0:
            self._print_error("Application failed")
            return result

        # Success!
        self._print_header("🎉 Pattern Hunt Complete!")
        self._print_success(f"Processed {len(patterns_to_process)} patterns")
        self._print_info(f"Results saved in: {self.state_dir}")

        self.state['last_run'] = datetime.now().isoformat()
        self._save_state()

        return 0

    def _review_patterns(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Review patterns interactively and select which to process.

        Args:
            patterns: List of identified patterns

        Returns:
            List of patterns selected for processing
        """
        selected = []

        for i, pattern in enumerate(patterns, 1):
            print(f"\n{Colors.BOLD}Pattern {i}/{len(patterns)}: {pattern['name']}{Colors.RESET}")
            print(f"{Colors.DIM}Description:{Colors.RESET} {pattern['description']}")
            print(f"{Colors.DIM}Frequency:{Colors.RESET} {pattern['frequency']}")
            print(f"{Colors.DIM}Impact:{Colors.RESET} {pattern['impact']}")
            print(f"{Colors.DIM}Evidence:{Colors.RESET}")
            for evidence in pattern.get('evidence', [])[:3]:  # Show first 3
                print(f"  • {evidence}")
            if len(pattern.get('evidence', [])) > 3:
                print(f"  {Colors.DIM}... and {len(pattern['evidence']) - 3} more{Colors.RESET}")

            if self._ask_yes_no("Process this pattern?", default=True):
                selected.append(pattern)
                self._print_success("Pattern added to queue")
            else:
                self._print_dim("Pattern skipped")

        return selected

    def _review_and_apply(self, proposals_file: Path) -> int:
        """
        Review proposals and apply selected updates.

        Args:
            proposals_file: Path to proposals JSON file

        Returns:
            0 on success, non-zero on error
        """
        # In dry-run mode, create mock proposals
        if self.dry_run:
            proposals = [
                {
                    'agent': 'Dev-Backend',
                    'pattern_name': 'Mock Pattern 1',
                    'non_negotiable': '- [ ] NEVER use mock patterns',
                    'discipline': 'Always validate before using',
                    'memory': 'Learned: Mock patterns are for testing',
                    'memory_tags': ['anti-patterns', 'mock']
                }
            ]
        else:
            with open(proposals_file) as f:
                proposals_data = json.load(f)
            proposals = proposals_data.get('proposals', [])

        if not proposals:
            self._print_warning("No proposals generated")
            return 0

        # Show summary
        print(f"\n{Colors.BOLD}Proposed Updates Summary:{Colors.RESET}")
        for proposal in proposals:
            print(f"  • {proposal['agent']}: {proposal['pattern_name']}")

        # Ask about pre-commit hooks
        if self._ask_yes_no("\nUpdate pre-commit hooks with defeat tests?", default=True):
            result = self._run_update_precommit()
            if result != 0:
                self._print_error("Pre-commit update failed")
                return result

        # Ask about agent memory
        if self._ask_yes_no("Update agent memory with learnings?", default=True):
            # In dry-run mode, pass mock data instead of file
            if self.dry_run:
                result = self._run_update_memory_mock(proposals)
            else:
                result = self._run_update_memory(proposals_file)

            if result != 0:
                self._print_error("Memory update failed")
                return result

        # Show proposal file location (if not dry-run)
        if not self.dry_run:
            self._print_info(f"Review full proposals at: {proposals_file}")

        return 0

    # Individual command implementations

    def cmd_collect(self, args: argparse.Namespace) -> int:
        """Collect signals from git, memory, and code churn."""
        self._print_header("📊 Collecting Pattern Signals")

        output_file = Path(args.output) if args.output else self.state_dir / f'signals-{datetime.now().strftime("%Y%m%d-%H%M%S")}.json'

        result = self._run_collect(output_file, args.days)

        if result == 0:
            self._print_success(f"Signals saved to: {output_file}")
            self.state['last_collection'] = str(output_file)
            self._save_state()

        return result

    def cmd_analyze(self, args: argparse.Namespace) -> int:
        """Analyze collected signals to identify patterns."""
        self._print_header("🔍 Analyzing Patterns")

        input_file = Path(args.input) if args.input else self.state.get('last_collection')
        if not input_file:
            self._print_error("No input file specified and no previous collection found")
            return 1

        input_file = Path(input_file)
        if not input_file.exists():
            self._print_error(f"Input file not found: {input_file}")
            return 1

        output_file = Path(args.output) if args.output else self.state_dir / f'patterns-{datetime.now().strftime("%Y%m%d-%H%M%S")}.json'

        result = self._run_analyze(input_file, output_file, args.top_n)

        if result == 0:
            self._print_success(f"Patterns saved to: {output_file}")
            self.state['last_analysis'] = str(output_file)
            self._save_state()

        return result

    def cmd_generate(self, args: argparse.Namespace) -> int:
        """Generate defeat tests for patterns."""
        self._print_header("🧪 Generating Defeat Tests")

        input_file = Path(args.input) if args.input else self.state.get('last_analysis')
        if not input_file:
            self._print_error("No input file specified and no previous analysis found")
            return 1

        input_file = Path(input_file)
        if not input_file.exists():
            self._print_error(f"Input file not found: {input_file}")
            return 1

        # Load patterns
        with open(input_file) as f:
            patterns_data = json.load(f)

        patterns = patterns_data.get('patterns', [])

        # Filter by pattern name if specified
        if args.pattern:
            patterns = [p for p in patterns if args.pattern.lower() in p['name'].lower()]
            if not patterns:
                self._print_error(f"No patterns matching '{args.pattern}' found")
                return 1

        result = self._run_generate_tests(patterns)

        if result == 0:
            self._print_success(f"Tests generated in: {self.repo_path / '.sdlc' / 'tests' / 'patterns'}")

        return result

    def cmd_apply(self, args: argparse.Namespace) -> int:
        """Apply agent prompt updates and memory entries."""
        self._print_header("📝 Applying Updates")

        input_file = Path(args.input) if args.input else None
        if not input_file:
            self._print_error("No input file specified. Generate proposals first with 'propose' command")
            return 1

        if not input_file.exists():
            self._print_error(f"Input file not found: {input_file}")
            return 1

        return self._review_and_apply(input_file)

    # Helper methods that call actual implementation modules

    def _run_collect(self, output_file: Path, days: int) -> int:
        """Run collect.py module."""
        script = Path(__file__).parent / 'collect.py'
        cmd = [
            sys.executable,
            str(script),
            '--repo-path', str(self.repo_path),
            '--days', str(days),
            '--output', str(output_file)
        ]

        if self.dry_run:
            self._print_dim(f"Would run: {' '.join(cmd)}")
            return 0

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            self._print_dim(result.stdout)
            return 0
        except subprocess.CalledProcessError as e:
            self._print_error(f"Collection failed: {e.stderr}")
            return e.returncode

    def _run_analyze(self, input_file: Path, output_file: Path, top_n: int) -> int:
        """Run analyze.py module."""
        script = Path(__file__).parent / 'analyze.py'
        cmd = [
            sys.executable,
            str(script),
            '--input', str(input_file),
            '--output', str(output_file),
            '--top-n', str(top_n)
        ]

        if self.dry_run:
            self._print_dim(f"Would run: {' '.join(cmd)}")
            return 0

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            self._print_dim(result.stdout)
            return 0
        except subprocess.CalledProcessError as e:
            self._print_error(f"Analysis failed: {e.stderr}")
            return e.returncode

    def _run_generate_tests(self, patterns: List[Dict[str, Any]]) -> int:
        """Run generate_tests.py module."""
        script = Path(__file__).parent / 'generate_tests.py'

        # In dry-run mode, just show what would be done
        if self.dry_run:
            self._print_dim(f"Would generate {len(patterns)} defeat tests in .sdlc/tests/patterns/")
            for pattern in patterns:
                pattern_slug = pattern['name'].lower().replace(' ', '_')
                self._print_dim(f"  - test_{pattern_slug}.py")
            return 0

        # Write patterns to temp file
        temp_file = self.state_dir / 'temp_patterns.json'
        with open(temp_file, 'w') as f:
            json.dump({'patterns': patterns}, f, indent=2)

        cmd = [
            sys.executable,
            str(script),
            '--input', str(temp_file),
            '--output-dir', str(self.repo_path / '.sdlc' / 'tests' / 'patterns')
        ]

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            self._print_dim(result.stdout)
            return 0
        except subprocess.CalledProcessError as e:
            self._print_error(f"Test generation failed: {e.stderr}")
            return e.returncode
        finally:
            # Clean up temp file
            if temp_file.exists():
                temp_file.unlink()

    def _run_propose_updates(self, patterns: List[Dict[str, Any]], output_file: Path) -> int:
        """Run propose_updates.py module."""
        script = Path(__file__).parent / 'propose_updates.py'

        # In dry-run mode, just show what would be done
        if self.dry_run:
            self._print_dim(f"Would generate proposals for {len(patterns)} patterns")
            for pattern in patterns:
                self._print_dim(f"  - {pattern['name']}: Agent prompt + memory update")
            return 0

        # Write patterns to temp file
        temp_file = self.state_dir / 'temp_patterns.json'
        with open(temp_file, 'w') as f:
            json.dump({'patterns': patterns}, f, indent=2)

        cmd = [
            sys.executable,
            str(script),
            '--input', str(temp_file),
            '--output', str(output_file)
        ]

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            self._print_dim(result.stdout)
            return 0
        except subprocess.CalledProcessError as e:
            self._print_error(f"Proposal generation failed: {e.stderr}")
            return e.returncode
        finally:
            # Clean up temp file
            if temp_file.exists():
                temp_file.unlink()

    def _run_update_precommit(self) -> int:
        """Run update_precommit.py module."""
        script = Path(__file__).parent / 'update_precommit.py'
        cmd = [
            sys.executable,
            str(script),
            '--config', str(self.repo_path / '.pre-commit-config.yaml'),
            '--test-dir', str(self.repo_path / '.sdlc' / 'tests' / 'patterns')
        ]

        if self.dry_run:
            cmd.append('--dry-run')

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            self._print_dim(result.stdout)
            self._print_success("Pre-commit hooks updated")
            return 0
        except subprocess.CalledProcessError as e:
            self._print_error(f"Pre-commit update failed: {e.stderr}")
            return e.returncode

    def _run_update_memory(self, proposals_file: Path) -> int:
        """Run update_memory.py module."""
        script = Path(__file__).parent / 'update_memory.py'
        cmd = [
            sys.executable,
            str(script),
            '--input', str(proposals_file)
        ]

        if self.dry_run:
            cmd.append('--dry-run')

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            self._print_dim(result.stdout)
            self._print_success("Agent memory updated")
            return 0
        except subprocess.CalledProcessError as e:
            self._print_error(f"Memory update failed: {e.stderr}")
            return e.returncode

    def _run_update_memory_mock(self, proposals: List[Dict[str, Any]]) -> int:
        """Mock memory update for dry-run mode."""
        self._print_dim(f"Would add {len(proposals)} memory entries to agent memory")
        for proposal in proposals:
            self._print_dim(f"  - {proposal['agent']}: {proposal['memory']}")
        self._print_success("Agent memory updated (dry-run)")
        return 0


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description='Pattern Hunter - Interactive pattern detection workflow',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full interactive workflow
  hunt-patterns hunt

  # Non-interactive (auto-approve)
  hunt-patterns hunt --auto

  # Preview without changes
  hunt-patterns hunt --dry-run

  # Individual steps
  hunt-patterns collect --days 30
  hunt-patterns analyze --input signals.json
  hunt-patterns generate --input patterns.json
  hunt-patterns apply --input proposals.json
        """
    )

    parser.add_argument('--repo-path', type=str, help='Path to repository (default: current directory)')
    parser.add_argument('--dry-run', action='store_true', help='Show plans without executing')
    parser.add_argument('--auto', action='store_true', help='Auto-approve all prompts')
    parser.add_argument('--no-color', action='store_true', help='Disable colored output')

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # hunt command
    hunt_parser = subparsers.add_parser('hunt', help='Run full pattern hunting workflow')
    hunt_parser.add_argument('--days', type=int, default=30, help='Days of history to analyze (default: 30)')
    hunt_parser.add_argument('--top-n', type=int, default=10, help='Max patterns to identify (default: 10)')
    hunt_parser.set_defaults(days=30, top_n=10)

    # collect command
    collect_parser = subparsers.add_parser('collect', help='Collect pattern signals')
    collect_parser.add_argument('--days', type=int, default=30, help='Days of history to analyze (default: 30)')
    collect_parser.add_argument('--output', type=str, help='Output file (default: auto-generated)')
    collect_parser.set_defaults(days=30)

    # analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze collected signals')
    analyze_parser.add_argument('--input', type=str, help='Input signals file (default: use last collection)')
    analyze_parser.add_argument('--output', type=str, help='Output file (default: auto-generated)')
    analyze_parser.add_argument('--top-n', type=int, default=10, help='Max patterns to identify (default: 10)')
    analyze_parser.set_defaults(top_n=10)

    # generate command
    generate_parser = subparsers.add_parser('generate', help='Generate defeat tests')
    generate_parser.add_argument('--input', type=str, help='Input patterns file (default: use last analysis)')
    generate_parser.add_argument('--pattern', type=str, help='Filter by pattern name')

    # apply command
    apply_parser = subparsers.add_parser('apply', help='Apply agent updates')
    apply_parser.add_argument('--input', type=str, required=True, help='Input proposals file')

    args = parser.parse_args()

    # Disable colors if requested
    if args.no_color:
        Colors.disable()

    # Default to hunt if no command specified
    if not args.command:
        args.command = 'hunt'
        args.days = 30
        args.top_n = 10

    # Create CLI instance
    cli = PatternHunterCLI(
        repo_path=args.repo_path,
        dry_run=args.dry_run,
        auto=args.auto
    )

    # Route to appropriate command
    command_map = {
        'hunt': cli.cmd_hunt,
        'collect': cli.cmd_collect,
        'analyze': cli.cmd_analyze,
        'generate': cli.cmd_generate,
        'apply': cli.cmd_apply
    }

    handler = command_map.get(args.command)
    if not handler:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1

    try:
        return handler(args)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupted by user{Colors.RESET}")
        return 130
    except Exception as e:
        print(f"{Colors.RED}Fatal error: {e}{Colors.RESET}", file=sys.stderr)
        if '--debug' in sys.argv:
            raise
        return 1


if __name__ == '__main__':
    sys.exit(main())
