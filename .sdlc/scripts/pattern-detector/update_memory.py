#!/usr/bin/env python3
"""
Agent Memory Auto-Update Module

Automatically adds pattern learnings to agent memory. Supports both direct file
modification and MCP server integration.

Usage:
    # From file (proposals from propose_updates.py)
    python update_memory.py --input proposals.json

    # From stdin (pipeline)
    python propose_updates.py --json | python update_memory.py

    # Dry run (show what would be added)
    python update_memory.py --input proposals.json --dry-run

    # Custom memory location
    python update_memory.py --input proposals.json --memory-path /custom/path

    # Force MCP mode even if server isn't running
    python update_memory.py --input proposals.json --use-mcp

Input Format:
    JSON from propose_updates.py with structure:
    {
        "proposals": [
            {
                "agent": "Dev",
                "pattern_name": "Silent Fallback",
                "memory": "Learned: Silent fallbacks hide bugs...",
                "memory_tags": ["anti-patterns", "defeat-test", "silent-fallback"]
            }
        ]
    }

Output:
    Updates ~/.agent-memory/memories.json with new entries
    Avoids duplicates by checking pattern_id in metadata
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class MemoryUpdater:
    """Updates agent memory with pattern learnings."""

    def __init__(
        self,
        memory_path: Optional[str] = None,
        use_mcp: bool = False,
        dry_run: bool = False
    ):
        """
        Initialize memory updater.

        Args:
            memory_path: Path to memories.json (default: ~/.agent-memory/memories.json)
            use_mcp: Force MCP server usage (default: auto-detect)
            dry_run: Show changes without applying them (default: False)
        """
        self.memory_path = Path(memory_path) if memory_path else Path.home() / '.agent-memory' / 'memories.json'
        self.use_mcp = use_mcp
        self.dry_run = dry_run
        self.mcp_available = self._check_mcp_available()

    def _check_mcp_available(self) -> bool:
        """
        Check if MCP agent-memory server is available.

        Returns:
            True if MCP server is running and accessible
        """
        if self.use_mcp:
            # User forced MCP mode, assume it's available
            return True

        # Try to detect MCP server
        # For now, we'll just check if the server script exists
        # In practice, we'd need to check if the server is actually running
        # This is a simplified check
        try:
            # Check if we can import the MCP client (placeholder)
            # In real implementation, would check server connection
            return False  # Default to direct file mode for now
        except Exception:
            return False

    def _generate_pattern_slug(self, pattern_name: str) -> str:
        """
        Generate a valid slug from pattern name.

        Args:
            pattern_name: Human-readable pattern name

        Returns:
            snake_case slug
        """
        slug = pattern_name.lower()
        slug = re.sub(r'[^a-z0-9]+', '_', slug)
        slug = slug.strip('_')
        slug = re.sub(r'_+', '_', slug)
        return slug

    def _load_existing_memories(self) -> List[Dict[str, Any]]:
        """
        Load existing memories from file.

        Returns:
            List of memory entries

        Raises:
            FileNotFoundError: If memory file doesn't exist
            json.JSONDecodeError: If memory file is invalid JSON
        """
        if not self.memory_path.exists():
            # In dry-run mode, don't create the file
            if self.dry_run:
                return []
            # Create empty memory file
            self.memory_path.parent.mkdir(parents=True, exist_ok=True)
            self.memory_path.write_text('[]')
            return []

        try:
            content = self.memory_path.read_text()
            memories = json.loads(content)
            return memories if isinstance(memories, list) else []
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in memory file {self.memory_path}: {e.msg}",
                e.doc,
                e.pos
            )

    def _check_duplicate(
        self,
        memories: List[Dict[str, Any]],
        pattern_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Check if a learning with this pattern_id already exists.

        Args:
            memories: Existing memory entries
            pattern_id: Pattern identifier to check

        Returns:
            Existing memory entry if found, None otherwise
        """
        for memory in memories:
            metadata = memory.get('metadata', {})
            if metadata.get('pattern_id') == pattern_id:
                return memory
        return None

    def _create_memory_entry(
        self,
        proposal: Dict[str, Any],
        next_id: int
    ) -> Dict[str, Any]:
        """
        Create a memory entry from a proposal.

        Args:
            proposal: Proposal dictionary from propose_updates.py
            next_id: Next available memory ID

        Returns:
            Memory entry dictionary
        """
        pattern_name = proposal.get('pattern_name', 'Unknown Pattern')
        pattern_slug = self._generate_pattern_slug(pattern_name)

        # Generate defeat test filename
        defeat_test = f"test_{pattern_slug}.py"

        # Create memory entry
        entry = {
            'id': next_id,
            'content': proposal.get('memory', f"Learned: {pattern_name}"),
            'category': 'anti-patterns',
            'tags': proposal.get('memory_tags', ['anti-patterns', 'defeat-test']),
            'metadata': {
                'pattern_id': pattern_slug,
                'defeat_test': defeat_test,
                'added_by': 'pattern-detector',
                'agent': proposal.get('agent', 'Dev')
            },
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        return entry

    def _save_memories_direct(self, memories: List[Dict[str, Any]]) -> None:
        """
        Save memories directly to file.

        Args:
            memories: Updated list of memory entries
        """
        if self.dry_run:
            print(f"[DRY RUN] Would write {len(memories)} memories to {self.memory_path}", file=sys.stderr)
            return

        # Ensure directory exists
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)

        # Write with pretty formatting
        content = json.dumps(memories, indent=2, ensure_ascii=False)
        self.memory_path.write_text(content)

        print(f"Updated {self.memory_path}", file=sys.stderr)

    def _save_memory_mcp(self, entry: Dict[str, Any]) -> bool:
        """
        Save a single memory entry using MCP server.

        Args:
            entry: Memory entry to save

        Returns:
            True if successful, False otherwise
        """
        if self.dry_run:
            print(f"[DRY RUN] Would send to MCP server: {entry['content'][:60]}...", file=sys.stderr)
            return True

        # In a real implementation, this would call the MCP server
        # For now, this is a placeholder
        # Example: call MCP server via subprocess or API
        try:
            # Placeholder for MCP server call
            # In practice, would use MCP SDK or subprocess to call server tools
            print(f"WARNING: MCP integration not yet implemented, falling back to direct file mode", file=sys.stderr)
            return False
        except Exception as e:
            print(f"Error calling MCP server: {e}", file=sys.stderr)
            return False

    def add_learnings(
        self,
        proposals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Add learnings from proposals to agent memory.

        Args:
            proposals: List of proposal dictionaries

        Returns:
            Summary dictionary with added, skipped, and error counts
        """
        result = {
            'added': [],
            'skipped': [],
            'errors': [],
            'total_proposals': len(proposals)
        }

        # Load existing memories
        try:
            memories = self._load_existing_memories()
        except Exception as e:
            result['errors'].append(f"Failed to load memories: {e}")
            return result

        # Determine next ID
        if memories:
            next_id = max(m.get('id', 0) for m in memories) + 1
        else:
            next_id = 1

        # Process each proposal
        for proposal in proposals:
            pattern_name = proposal.get('pattern_name', 'Unknown')
            pattern_slug = self._generate_pattern_slug(pattern_name)

            # Check for duplicates
            existing = self._check_duplicate(memories, pattern_slug)
            if existing:
                result['skipped'].append({
                    'pattern_name': pattern_name,
                    'pattern_id': pattern_slug,
                    'reason': 'Already exists in memory',
                    'existing_id': existing.get('id')
                })
                print(f"  Skipped: {pattern_name} (already exists as memory #{existing.get('id')})", file=sys.stderr)
                continue

            # Create new memory entry
            try:
                entry = self._create_memory_entry(proposal, next_id)

                # Add to memories list
                memories.append(entry)
                next_id += 1

                result['added'].append({
                    'pattern_name': pattern_name,
                    'pattern_id': pattern_slug,
                    'memory_id': entry['id'],
                    'agent': proposal.get('agent', 'Dev')
                })

                dry_run_prefix = "[DRY RUN] " if self.dry_run else ""
                print(f"  {dry_run_prefix}Added: {pattern_name} (memory #{entry['id']})", file=sys.stderr)

            except Exception as e:
                result['errors'].append({
                    'pattern_name': pattern_name,
                    'error': str(e)
                })
                print(f"  Error: {pattern_name} - {e}", file=sys.stderr)

        # Save updated memories
        if result['added'] and not self.dry_run:
            try:
                if self.use_mcp and self.mcp_available:
                    # MCP mode - save individual entries
                    print("Using MCP server mode...", file=sys.stderr)
                    for entry_info in result['added']:
                        # Find the entry in memories
                        entry = next(m for m in memories if m['id'] == entry_info['memory_id'])
                        if not self._save_memory_mcp(entry):
                            # Fall back to direct mode
                            self._save_memories_direct(memories)
                            break
                else:
                    # Direct file mode
                    self._save_memories_direct(memories)

            except Exception as e:
                result['errors'].append(f"Failed to save memories: {e}")
                print(f"Error saving memories: {e}", file=sys.stderr)

        return result

    def print_summary(self, result: Dict[str, Any]) -> None:
        """
        Print summary of memory update operation.

        Args:
            result: Result dictionary from add_learnings()
        """
        print("\n=== Memory Update Summary ===", file=sys.stderr)
        print(f"Total proposals: {result['total_proposals']}", file=sys.stderr)
        print(f"Added: {len(result['added'])}", file=sys.stderr)
        print(f"Skipped: {len(result['skipped'])}", file=sys.stderr)
        print(f"Errors: {len(result['errors'])}", file=sys.stderr)

        if result['added']:
            print("\nAdded learnings:", file=sys.stderr)
            for item in result['added']:
                print(f"  - {item['pattern_name']} (ID: {item['memory_id']}, Agent: {item['agent']})", file=sys.stderr)

        if result['skipped']:
            print("\nSkipped (duplicates):", file=sys.stderr)
            for item in result['skipped']:
                print(f"  - {item['pattern_name']} (exists as #{item['existing_id']})", file=sys.stderr)

        if result['errors']:
            print("\nErrors:", file=sys.stderr)
            for error in result['errors']:
                if isinstance(error, dict):
                    print(f"  - {error.get('pattern_name', 'Unknown')}: {error.get('error', error)}", file=sys.stderr)
                else:
                    print(f"  - {error}", file=sys.stderr)


def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description='Add pattern learnings to agent memory.'
    )
    parser.add_argument(
        '--input',
        help='Input JSON file from propose_updates.py (default: read from stdin)'
    )
    parser.add_argument(
        '--memory-path',
        help='Path to memories.json (default: ~/.agent-memory/memories.json)'
    )
    parser.add_argument(
        '--use-mcp',
        action='store_true',
        help='Use MCP server instead of direct file modification'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be added without making changes'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output result as JSON instead of summary'
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
                data = json.load(f)
        else:
            data = json.load(sys.stdin)

        # Extract proposals
        proposals = data.get('proposals', [])

        if not proposals:
            print("No proposals found in input", file=sys.stderr)
            return 1

        print(f"Processing {len(proposals)} proposals...", file=sys.stderr)

        # Initialize updater
        updater = MemoryUpdater(
            memory_path=args.memory_path,
            use_mcp=args.use_mcp,
            dry_run=args.dry_run
        )

        # Add learnings
        result = updater.add_learnings(proposals)

        # Output results
        if args.json:
            output = json.dumps(result, indent=2 if args.pretty else None)
            print(output)
        else:
            updater.print_summary(result)

        # Exit code based on results
        if result['errors']:
            return 1
        return 0

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        return 1
    except FileNotFoundError as e:
        print(f"Error: File not found: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
