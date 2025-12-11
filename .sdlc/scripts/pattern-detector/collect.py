#!/usr/bin/env python3
"""
Pattern Detection Data Collection Module

Collects pattern signals from three sources:
1. Git history (fix commits, repeated modifications)
2. Agent memories (repeated learnings)
3. Code churn (hot files with frequent changes)

Usage:
    python collect.py [--repo-path PATH] [--days N] [--output FILE]

Output:
    JSON file with structure:
    {
        "timestamp": "ISO-8601 datetime",
        "repo_path": "/path/to/repo",
        "collection_period_days": 30,
        "git_signals": [...],
        "memory_signals": [...],
        "churn_signals": [...]
    }
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


class GitHistoryAnalyzer:
    """Analyzes git history for fix-related commits and repeated modifications."""

    # Patterns that indicate fix commits
    FIX_PATTERNS = [
        r'\bfix(ed|es|ing)?\b',
        r'\bbug\b',
        r'\brepair\b',
        r'\bcorrect\b',
        r'\bresolve(d|s)?\b',
        r'\bhotfix\b',
        r'\bpatch\b',
        r'\brevert\b',
        r'\boops\b',
        r'\btypo\b',
        r'\bwhoops\b',
    ]

    def __init__(self, repo_path: str, days: int = 30):
        """
        Initialize git history analyzer.

        Args:
            repo_path: Path to git repository
            days: Number of days to look back in history
        """
        self.repo_path = Path(repo_path).resolve()
        self.days = days
        self.since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    def _run_git_command(self, args: List[str]) -> str:
        """
        Run a git command and return output.

        Args:
            args: Git command arguments

        Returns:
            Command output as string

        Raises:
            subprocess.CalledProcessError: If git command fails
        """
        cmd = ['git', '-C', str(self.repo_path)] + args
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()

    def _is_fix_commit(self, message: str) -> bool:
        """
        Check if commit message indicates a fix.

        Args:
            message: Commit message

        Returns:
            True if message contains fix-related keywords
        """
        message_lower = message.lower()
        return any(
            re.search(pattern, message_lower, re.IGNORECASE)
            for pattern in self.FIX_PATTERNS
        )

    def analyze(self) -> List[Dict[str, Any]]:
        """
        Analyze git history for fix commits and patterns.

        Returns:
            List of signal dictionaries with structure:
            {
                "type": "fix_commit" | "repeated_modification",
                "hash": "commit_hash",
                "date": "ISO-8601 datetime",
                "author": "author_name",
                "message": "commit message",
                "files_changed": ["file1.py", "file2.py"],
                "stats": {"insertions": N, "deletions": M}
            }
        """
        signals = []

        try:
            # Get all commits in the time period with stats
            log_format = '%H%x00%aI%x00%an%x00%s'  # hash, ISO date, author, subject
            log_output = self._run_git_command([
                'log',
                f'--since={self.since_date}',
                f'--format={log_format}',
                '--numstat'
            ])

            if not log_output:
                return signals

            # Parse commits
            current_commit = None
            for line in log_output.split('\n'):
                if '\x00' in line:  # Commit header line
                    if current_commit:
                        signals.append(current_commit)

                    parts = line.split('\x00')
                    if len(parts) >= 4:
                        commit_hash, date, author, message = parts[0], parts[1], parts[2], parts[3]

                        current_commit = {
                            'type': 'fix_commit' if self._is_fix_commit(message) else 'commit',
                            'hash': commit_hash,
                            'date': date,
                            'author': author,
                            'message': message,
                            'files_changed': [],
                            'stats': {'insertions': 0, 'deletions': 0}
                        }
                elif line and current_commit:  # Stats line
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        insertions, deletions, filename = parts[0], parts[1], parts[2]

                        # Skip binary files
                        if insertions != '-' and deletions != '-':
                            current_commit['files_changed'].append(filename)
                            current_commit['stats']['insertions'] += int(insertions)
                            current_commit['stats']['deletions'] += int(deletions)

            # Add last commit
            if current_commit:
                signals.append(current_commit)

            # Filter to only fix commits
            fix_signals = [s for s in signals if s['type'] == 'fix_commit']

            # Analyze file modification frequency
            file_modification_count: Dict[str, List[Dict]] = {}
            for signal in signals:
                for filepath in signal['files_changed']:
                    if filepath not in file_modification_count:
                        file_modification_count[filepath] = []
                    file_modification_count[filepath].append({
                        'hash': signal['hash'],
                        'date': signal['date'],
                        'message': signal['message']
                    })

            # Add repeated modification signals for files changed 3+ times
            repeated_signals = []
            for filepath, modifications in file_modification_count.items():
                if len(modifications) >= 3:
                    repeated_signals.append({
                        'type': 'repeated_modification',
                        'file': filepath,
                        'modification_count': len(modifications),
                        'modifications': modifications[:5],  # Keep first 5
                        'signal_strength': 'high' if len(modifications) >= 5 else 'medium'
                    })

            # Sort by modification count (descending)
            repeated_signals.sort(key=lambda x: x['modification_count'], reverse=True)

            return fix_signals + repeated_signals

        except subprocess.CalledProcessError as e:
            print(f"Warning: Git command failed: {e}", file=sys.stderr)
            return []
        except Exception as e:
            print(f"Warning: Error analyzing git history: {e}", file=sys.stderr)
            return []


class AgentMemoryAnalyzer:
    """Analyzes agent memory for repeated learnings and patterns."""

    def __init__(self, memory_path: Optional[str] = None):
        """
        Initialize agent memory analyzer.

        Args:
            memory_path: Path to agent memory file (defaults to ~/.agent-memory/memories.json)
        """
        if memory_path:
            self.memory_path = Path(memory_path)
        else:
            self.memory_path = Path.home() / '.agent-memory' / 'memories.json'

    def analyze(self) -> List[Dict[str, Any]]:
        """
        Analyze agent memory for repeated learnings.

        Returns:
            List of signal dictionaries with structure:
            {
                "type": "repeated_learning",
                "pattern": "description of pattern",
                "occurrences": N,
                "memories": [memory_objects],
                "signal_strength": "high" | "medium" | "low"
            }
        """
        signals = []

        try:
            if not self.memory_path.exists():
                print(f"Info: Agent memory file not found at {self.memory_path}", file=sys.stderr)
                return signals

            with open(self.memory_path, 'r') as f:
                memories = json.load(f)

            if not isinstance(memories, list):
                print("Warning: Agent memory file has unexpected format", file=sys.stderr)
                return signals

            # Group memories by category and tags
            category_groups: Dict[str, List[Dict]] = {}
            tag_groups: Dict[str, List[Dict]] = {}

            for memory in memories:
                if not isinstance(memory, dict):
                    continue

                # Group by category
                category = memory.get('category', 'unknown')
                if category not in category_groups:
                    category_groups[category] = []
                category_groups[category].append(memory)

                # Group by tags
                tags = memory.get('tags', [])
                if isinstance(tags, list):
                    for tag in tags:
                        if tag not in tag_groups:
                            tag_groups[tag] = []
                        tag_groups[tag].append(memory)

            # Identify repeated patterns (categories with 3+ memories)
            for category, mems in category_groups.items():
                if len(mems) >= 3:
                    signals.append({
                        'type': 'repeated_learning',
                        'pattern': f'Multiple learnings in category: {category}',
                        'category': category,
                        'occurrences': len(mems),
                        'memories': [
                            {
                                'timestamp': m.get('timestamp'),
                                'content': m.get('content', '')[:200],  # Truncate
                                'tags': m.get('tags', [])
                            }
                            for m in mems[:5]  # Keep first 5
                        ],
                        'signal_strength': 'high' if len(mems) >= 5 else 'medium'
                    })

            # Identify repeated patterns (tags with 3+ memories)
            for tag, mems in tag_groups.items():
                if len(mems) >= 3:
                    signals.append({
                        'type': 'repeated_learning',
                        'pattern': f'Multiple learnings with tag: {tag}',
                        'tag': tag,
                        'occurrences': len(mems),
                        'memories': [
                            {
                                'timestamp': m.get('timestamp'),
                                'content': m.get('content', '')[:200],  # Truncate
                                'category': m.get('category')
                            }
                            for m in mems[:5]  # Keep first 5
                        ],
                        'signal_strength': 'high' if len(mems) >= 5 else 'medium'
                    })

            # Sort by occurrences (descending)
            signals.sort(key=lambda x: x['occurrences'], reverse=True)

            return signals

        except json.JSONDecodeError as e:
            print(f"Warning: Failed to parse agent memory JSON: {e}", file=sys.stderr)
            return []
        except Exception as e:
            print(f"Warning: Error analyzing agent memory: {e}", file=sys.stderr)
            return []


class CodeChurnAnalyzer:
    """Analyzes code churn to identify hot files."""

    def __init__(self, repo_path: str, days: int = 30, top_n: int = 10):
        """
        Initialize code churn analyzer.

        Args:
            repo_path: Path to git repository
            days: Number of days to look back
            top_n: Number of top hot files to return
        """
        self.repo_path = Path(repo_path).resolve()
        self.days = days
        self.top_n = top_n
        self.since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    def _run_git_command(self, args: List[str]) -> str:
        """Run a git command and return output."""
        cmd = ['git', '-C', str(self.repo_path)] + args
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()

    def analyze(self) -> List[Dict[str, Any]]:
        """
        Analyze code churn to find hot files.

        Returns:
            List of signal dictionaries with structure:
            {
                "type": "hot_file",
                "file": "path/to/file.py",
                "churn_score": N,
                "commit_count": N,
                "total_changes": N,
                "recent_commits": [commit_objects],
                "signal_strength": "high" | "medium" | "low"
            }
        """
        signals = []

        try:
            # Get file change statistics
            log_output = self._run_git_command([
                'log',
                f'--since={self.since_date}',
                '--format=%H%x00%aI%x00%s',
                '--numstat'
            ])

            if not log_output:
                return signals

            # Parse file statistics
            file_stats: Dict[str, Dict[str, Any]] = {}
            current_commit = None

            for line in log_output.split('\n'):
                if '\x00' in line:  # Commit header
                    parts = line.split('\x00')
                    if len(parts) >= 3:
                        current_commit = {
                            'hash': parts[0],
                            'date': parts[1],
                            'message': parts[2]
                        }
                elif line and current_commit:  # Stats line
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        insertions, deletions, filename = parts[0], parts[1], parts[2]

                        # Skip binary files
                        if insertions != '-' and deletions != '-':
                            if filename not in file_stats:
                                file_stats[filename] = {
                                    'commit_count': 0,
                                    'total_insertions': 0,
                                    'total_deletions': 0,
                                    'commits': []
                                }

                            file_stats[filename]['commit_count'] += 1
                            file_stats[filename]['total_insertions'] += int(insertions)
                            file_stats[filename]['total_deletions'] += int(deletions)
                            file_stats[filename]['commits'].append(current_commit)

            # Calculate churn scores and create signals
            for filename, stats in file_stats.items():
                total_changes = stats['total_insertions'] + stats['total_deletions']
                churn_score = stats['commit_count'] * total_changes

                # Determine signal strength
                if stats['commit_count'] >= 5:
                    strength = 'high'
                elif stats['commit_count'] >= 3:
                    strength = 'medium'
                else:
                    strength = 'low'

                signals.append({
                    'type': 'hot_file',
                    'file': filename,
                    'churn_score': churn_score,
                    'commit_count': stats['commit_count'],
                    'total_changes': total_changes,
                    'insertions': stats['total_insertions'],
                    'deletions': stats['total_deletions'],
                    'recent_commits': stats['commits'][:5],  # Keep first 5
                    'signal_strength': strength
                })

            # Sort by churn score and return top N
            signals.sort(key=lambda x: x['churn_score'], reverse=True)
            return signals[:self.top_n]

        except subprocess.CalledProcessError as e:
            print(f"Warning: Git command failed: {e}", file=sys.stderr)
            return []
        except Exception as e:
            print(f"Warning: Error analyzing code churn: {e}", file=sys.stderr)
            return []


def collect_all_signals(
    repo_path: str,
    days: int = 30,
    memory_path: Optional[str] = None,
    top_n_hot_files: int = 10
) -> Dict[str, Any]:
    """
    Collect all pattern signals from git history, agent memory, and code churn.

    Args:
        repo_path: Path to git repository
        days: Number of days to look back in history
        memory_path: Path to agent memory file (optional)
        top_n_hot_files: Number of hot files to include

    Returns:
        Dictionary with structure:
        {
            "timestamp": "ISO-8601 datetime",
            "repo_path": "/path/to/repo",
            "collection_period_days": 30,
            "git_signals": [...],
            "memory_signals": [...],
            "churn_signals": [...]
        }
    """
    print(f"Collecting pattern signals from {repo_path}...", file=sys.stderr)
    print(f"Looking back {days} days", file=sys.stderr)

    # Initialize analyzers
    git_analyzer = GitHistoryAnalyzer(repo_path, days)
    memory_analyzer = AgentMemoryAnalyzer(memory_path)
    churn_analyzer = CodeChurnAnalyzer(repo_path, days, top_n_hot_files)

    # Collect signals
    print("Analyzing git history...", file=sys.stderr)
    git_signals = git_analyzer.analyze()
    print(f"  Found {len(git_signals)} git signals", file=sys.stderr)

    print("Analyzing agent memory...", file=sys.stderr)
    memory_signals = memory_analyzer.analyze()
    print(f"  Found {len(memory_signals)} memory signals", file=sys.stderr)

    print("Analyzing code churn...", file=sys.stderr)
    churn_signals = churn_analyzer.analyze()
    print(f"  Found {len(churn_signals)} hot files", file=sys.stderr)

    # Compile results
    return {
        'timestamp': datetime.now().isoformat(),
        'repo_path': str(Path(repo_path).resolve()),
        'collection_period_days': days,
        'git_signals': git_signals,
        'memory_signals': memory_signals,
        'churn_signals': churn_signals,
        'summary': {
            'total_signals': len(git_signals) + len(memory_signals) + len(churn_signals),
            'fix_commits': len([s for s in git_signals if s['type'] == 'fix_commit']),
            'repeated_modifications': len([s for s in git_signals if s['type'] == 'repeated_modification']),
            'repeated_learnings': len(memory_signals),
            'hot_files': len(churn_signals)
        }
    }


def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description='Collect pattern detection signals from git history, agent memory, and code churn.'
    )
    parser.add_argument(
        '--repo-path',
        default='.',
        help='Path to git repository (default: current directory)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Number of days to look back in history (default: 30)'
    )
    parser.add_argument(
        '--memory-path',
        help='Path to agent memory file (default: ~/.agent-memory/memories.json)'
    )
    parser.add_argument(
        '--top-n',
        type=int,
        default=10,
        help='Number of hot files to include (default: 10)'
    )
    parser.add_argument(
        '--output',
        help='Output file path (default: print to stdout)'
    )
    parser.add_argument(
        '--pretty',
        action='store_true',
        help='Pretty-print JSON output'
    )

    args = parser.parse_args()

    try:
        # Collect signals
        results = collect_all_signals(
            repo_path=args.repo_path,
            days=args.days,
            memory_path=args.memory_path,
            top_n_hot_files=args.top_n
        )

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
        summary = results['summary']
        print("\n=== Collection Summary ===", file=sys.stderr)
        print(f"Total signals: {summary['total_signals']}", file=sys.stderr)
        print(f"  Fix commits: {summary['fix_commits']}", file=sys.stderr)
        print(f"  Repeated modifications: {summary['repeated_modifications']}", file=sys.stderr)
        print(f"  Repeated learnings: {summary['repeated_learnings']}", file=sys.stderr)
        print(f"  Hot files: {summary['hot_files']}", file=sys.stderr)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
