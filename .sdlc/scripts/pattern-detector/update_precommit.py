#!/usr/bin/env python3
"""
Pre-commit Hook Auto-Update Module

Automatically updates .pre-commit-config.yaml to include new defeat tests.

Usage:
    python update_precommit.py [--config FILE] [--test-dir DIR] [--dry-run] [--install]

Features:
    - Creates .pre-commit-config.yaml if missing
    - Adds pattern defeat tests to existing config
    - Idempotent: running twice produces same result
    - Preserves existing hooks
    - Validates YAML syntax
    - Optionally installs pre-commit hooks

Example:
    # Basic usage (updates .pre-commit-config.yaml in current directory)
    python update_precommit.py

    # Dry run to see changes without applying
    python update_precommit.py --dry-run

    # Specify custom locations
    python update_precommit.py --config /path/to/.pre-commit-config.yaml --test-dir .sdlc/tests/patterns

    # Update and install hooks
    python update_precommit.py --install
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Try to import PyYAML, provide helpful error if missing
try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required but not installed.", file=sys.stderr)
    print("Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


# Default pre-commit configuration template
DEFAULT_CONFIG = {
    'repos': []
}

# Pattern defeat tests hook configuration
PATTERN_HOOK_CONFIG = {
    'repo': 'local',
    'hooks': [
        {
            'id': 'pattern-defeat-tests',
            'name': 'Pattern Defeat Tests',
            'entry': 'pytest .sdlc/tests/patterns/ -v',
            'language': 'system',
            'types': ['python'],
            'pass_filenames': False
        }
    ]
}


class PreCommitUpdater:
    """Updates .pre-commit-config.yaml with pattern defeat tests."""

    def __init__(
        self,
        config_path: Optional[Path] = None,
        test_dir: Optional[Path] = None
    ):
        """
        Initialize pre-commit updater.

        Args:
            config_path: Path to .pre-commit-config.yaml (default: .pre-commit-config.yaml in cwd)
            test_dir: Path to test directory (default: .sdlc/tests/patterns)
        """
        self.config_path = config_path or Path('.pre-commit-config.yaml')
        self.test_dir = test_dir or Path('.sdlc/tests/patterns')

    def check_precommit_installed(self) -> bool:
        """
        Check if pre-commit is installed.

        Returns:
            True if pre-commit is installed, False otherwise
        """
        try:
            result = subprocess.run(
                ['pre-commit', '--version'],
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def load_config(self) -> Dict[str, Any]:
        """
        Load existing pre-commit config or return default.

        Returns:
            Configuration dictionary
        """
        if not self.config_path.exists():
            print(f"No config found at {self.config_path}, will create new config", file=sys.stderr)
            return DEFAULT_CONFIG.copy()

        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)

            if not config:
                print(f"Empty config file, using default", file=sys.stderr)
                return DEFAULT_CONFIG.copy()

            if not isinstance(config, dict):
                print(f"Invalid config format, using default", file=sys.stderr)
                return DEFAULT_CONFIG.copy()

            # Ensure repos key exists
            if 'repos' not in config:
                config['repos'] = []

            return config

        except yaml.YAMLError as e:
            print(f"Error parsing {self.config_path}: {e}", file=sys.stderr)
            print("Using default config", file=sys.stderr)
            return DEFAULT_CONFIG.copy()
        except Exception as e:
            print(f"Error reading {self.config_path}: {e}", file=sys.stderr)
            print("Using default config", file=sys.stderr)
            return DEFAULT_CONFIG.copy()

    def find_local_repo(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find the local repo entry in config.

        Args:
            config: Pre-commit configuration

        Returns:
            Local repo dict if found, None otherwise
        """
        repos = config.get('repos', [])
        for repo in repos:
            if repo.get('repo') == 'local':
                return repo
        return None

    def find_pattern_hook(self, local_repo: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find the pattern defeat tests hook in local repo.

        Args:
            local_repo: Local repo configuration

        Returns:
            Pattern hook dict if found, None otherwise
        """
        hooks = local_repo.get('hooks', [])
        for hook in hooks:
            if hook.get('id') == 'pattern-defeat-tests':
                return hook
        return None

    def get_test_command(self) -> str:
        """
        Get the pytest command for pattern defeat tests.

        Returns:
            Pytest command string
        """
        # Normalize path for consistency
        test_path = str(self.test_dir).replace('\\', '/')

        # Check if test directory exists
        if not self.test_dir.exists():
            print(f"Warning: Test directory {self.test_dir} does not exist", file=sys.stderr)

        return f"pytest {test_path} -v"

    def update_config(self, config: Dict[str, Any]) -> tuple[Dict[str, Any], bool]:
        """
        Update config to include pattern defeat tests.

        Args:
            config: Existing configuration

        Returns:
            Tuple of (updated_config, changed)
        """
        changed = False

        # Ensure repos list exists
        if 'repos' not in config:
            config['repos'] = []
            changed = True

        # Find or create local repo
        local_repo = self.find_local_repo(config)

        if local_repo is None:
            # Create new local repo entry
            print("Creating new 'local' repo entry", file=sys.stderr)
            local_repo = {
                'repo': 'local',
                'hooks': []
            }
            config['repos'].append(local_repo)
            changed = True

        # Ensure hooks list exists
        if 'hooks' not in local_repo:
            local_repo['hooks'] = []
            changed = True

        # Find or create pattern hook
        pattern_hook = self.find_pattern_hook(local_repo)

        test_command = self.get_test_command()

        if pattern_hook is None:
            # Create new pattern hook
            print("Adding pattern-defeat-tests hook", file=sys.stderr)
            new_hook = {
                'id': 'pattern-defeat-tests',
                'name': 'Pattern Defeat Tests',
                'entry': test_command,
                'language': 'system',
                'types': ['python'],
                'pass_filenames': False
            }
            local_repo['hooks'].append(new_hook)
            changed = True
        else:
            # Update existing hook if command changed
            if pattern_hook.get('entry') != test_command:
                print(f"Updating pattern-defeat-tests command", file=sys.stderr)
                print(f"  Old: {pattern_hook.get('entry')}", file=sys.stderr)
                print(f"  New: {test_command}", file=sys.stderr)
                pattern_hook['entry'] = test_command
                changed = True
            else:
                print("Pattern-defeat-tests hook already up to date", file=sys.stderr)

        return config, changed

    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate configuration structure.

        Args:
            config: Configuration to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check basic structure
            if not isinstance(config, dict):
                return False, "Config must be a dictionary"

            if 'repos' not in config:
                return False, "Config must have 'repos' key"

            if not isinstance(config['repos'], list):
                return False, "'repos' must be a list"

            # Validate each repo
            for i, repo in enumerate(config['repos']):
                if not isinstance(repo, dict):
                    return False, f"Repo {i} must be a dictionary"

                if 'repo' not in repo:
                    return False, f"Repo {i} missing 'repo' key"

                if 'hooks' not in repo:
                    return False, f"Repo {i} missing 'hooks' key"

                if not isinstance(repo['hooks'], list):
                    return False, f"Repo {i} 'hooks' must be a list"

                # Validate each hook
                for j, hook in enumerate(repo['hooks']):
                    if not isinstance(hook, dict):
                        return False, f"Repo {i} hook {j} must be a dictionary"

                    required_keys = ['id', 'name', 'entry', 'language']
                    for key in required_keys:
                        if key not in hook:
                            return False, f"Repo {i} hook {j} missing '{key}' key"

            # Try to serialize to YAML
            try:
                yaml.safe_dump(config)
            except Exception as e:
                return False, f"Config cannot be serialized to YAML: {e}"

            return True, None

        except Exception as e:
            return False, f"Validation error: {e}"

    def write_config(self, config: Dict[str, Any]) -> None:
        """
        Write configuration to file.

        Args:
            config: Configuration to write

        Raises:
            Exception: If write fails
        """
        # Ensure parent directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Write with proper YAML formatting
        with open(self.config_path, 'w') as f:
            yaml.safe_dump(
                config,
                f,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )

        print(f"Wrote configuration to {self.config_path}", file=sys.stderr)

    def install_hooks(self) -> bool:
        """
        Install pre-commit hooks.

        Returns:
            True if successful, False otherwise
        """
        if not self.check_precommit_installed():
            print("ERROR: pre-commit is not installed", file=sys.stderr)
            print("Install with: pip install pre-commit", file=sys.stderr)
            return False

        try:
            print("Installing pre-commit hooks...", file=sys.stderr)
            result = subprocess.run(
                ['pre-commit', 'install'],
                capture_output=True,
                text=True,
                check=True
            )
            print(result.stdout, file=sys.stderr)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to install hooks: {e.stderr}", file=sys.stderr)
            return False

    def update(self, dry_run: bool = False, install: bool = False) -> tuple[bool, bool]:
        """
        Update pre-commit configuration.

        Args:
            dry_run: If True, show changes without applying
            install: If True, install pre-commit hooks after update

        Returns:
            Tuple of (success, changed)
        """
        try:
            # Load existing config
            print(f"Loading config from {self.config_path}...", file=sys.stderr)
            config = self.load_config()

            # Update config
            updated_config, changed = self.update_config(config)

            if not changed:
                print("\nNo changes needed", file=sys.stderr)
                return True, False

            # Validate updated config
            is_valid, error = self.validate_config(updated_config)
            if not is_valid:
                print(f"ERROR: Invalid configuration: {error}", file=sys.stderr)
                return False, False

            print("\n✓ Configuration validated successfully", file=sys.stderr)

            if dry_run:
                print("\n=== Dry Run: Changes Preview ===", file=sys.stderr)
                print(yaml.safe_dump(updated_config, default_flow_style=False, sort_keys=False), file=sys.stderr)
                print("\nDry run complete - no files modified", file=sys.stderr)
                return True, True

            # Write updated config
            self.write_config(updated_config)
            print(f"✓ Updated {self.config_path}", file=sys.stderr)

            # Optionally install hooks
            if install:
                if self.install_hooks():
                    print("✓ Pre-commit hooks installed", file=sys.stderr)
                else:
                    print("✗ Failed to install pre-commit hooks", file=sys.stderr)
                    return False, True

            return True, True

        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return False, False


def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description='Update .pre-commit-config.yaml with pattern defeat tests.'
    )
    parser.add_argument(
        '--config',
        type=Path,
        help='Path to .pre-commit-config.yaml (default: .pre-commit-config.yaml in cwd)'
    )
    parser.add_argument(
        '--test-dir',
        type=Path,
        help='Path to test directory (default: .sdlc/tests/patterns)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show changes without applying them'
    )
    parser.add_argument(
        '--install',
        action='store_true',
        help='Install pre-commit hooks after updating config'
    )
    parser.add_argument(
        '--check-only',
        action='store_true',
        help='Only check if update is needed, do not modify anything'
    )

    args = parser.parse_args()

    # Initialize updater
    updater = PreCommitUpdater(
        config_path=args.config,
        test_dir=args.test_dir
    )

    # Check if pre-commit is installed
    if args.install and not updater.check_precommit_installed():
        print("=" * 60, file=sys.stderr)
        print("ERROR: pre-commit is not installed", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print("\nPre-commit is required to use --install flag.", file=sys.stderr)
        print("\nInstall with:", file=sys.stderr)
        print("  pip install pre-commit", file=sys.stderr)
        print("\nOr update config without installing:", file=sys.stderr)
        print(f"  python {sys.argv[0]} --config {updater.config_path}", file=sys.stderr)
        return 1

    # Check-only mode
    if args.check_only:
        print("Checking if update is needed...", file=sys.stderr)
        config = updater.load_config()
        _, changed = updater.update_config(config)

        if changed:
            print("\n✗ Update needed", file=sys.stderr)
            return 1
        else:
            print("\n✓ No update needed", file=sys.stderr)
            return 0

    # Perform update
    print("=" * 60, file=sys.stderr)
    print("Pre-commit Config Update", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    success, changed = updater.update(dry_run=args.dry_run, install=args.install)

    if success:
        if changed:
            print("\n✓ Update complete", file=sys.stderr)
        return 0
    else:
        print("\n✗ Update failed", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
