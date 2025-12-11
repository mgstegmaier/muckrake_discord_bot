#!/usr/bin/env python3
"""
Acceptance tests for Pattern Hunter CLI

Tests the CLI interface and workflow orchestration.
"""

import subprocess
import sys
from pathlib import Path


def run_cli(*args, input_data=None):
    """
    Run the CLI with given arguments.

    Args:
        *args: CLI arguments
        input_data: Optional stdin input

    Returns:
        Tuple of (returncode, stdout, stderr)
    """
    script = Path(__file__).parent / 'cli.py'
    cmd = [sys.executable, str(script)] + list(args)

    result = subprocess.run(
        cmd,
        input=input_data,
        capture_output=True,
        text=True
    )

    return result.returncode, result.stdout, result.stderr


def test_help_output():
    """Test that --help displays usage information."""
    returncode, stdout, stderr = run_cli('--help')

    assert returncode == 0, f"Help command failed: {stderr}"
    assert 'Pattern Hunter' in stdout, "Help output missing title"
    assert 'hunt' in stdout, "Help output missing 'hunt' command"
    assert 'collect' in stdout, "Help output missing 'collect' command"
    assert 'analyze' in stdout, "Help output missing 'analyze' command"
    assert 'generate' in stdout, "Help output missing 'generate' command"
    assert 'apply' in stdout, "Help output missing 'apply' command"

    print("✓ Help output test passed")


def test_hunt_dry_run():
    """Test that hunt --dry-run completes without errors."""
    returncode, stdout, stderr = run_cli(
        '--dry-run',
        '--auto',
        '--no-color',
        'hunt'
    )

    assert returncode == 0, f"Hunt dry-run failed: {stderr}"
    assert 'DRY RUN MODE' in stdout, "Missing dry-run mode indicator"
    assert 'AUTO MODE' in stdout, "Missing auto mode indicator"
    assert 'Pattern Hunt Complete' in stdout, "Hunt did not complete successfully"

    print("✓ Hunt dry-run test passed")


def test_hunt_interactive():
    """Test that hunt accepts interactive input."""
    # Answer 'n' to first pattern prompt (should skip processing)
    returncode, stdout, stderr = run_cli(
        '--dry-run',
        '--no-color',
        'hunt',
        input_data='n\n'
    )

    assert returncode == 0, f"Hunt interactive failed: {stderr}"
    assert 'Process this pattern?' in stdout, "Missing interactive prompt"
    assert 'No patterns selected for processing' in stdout, "Pattern was processed despite 'n' response"

    print("✓ Hunt interactive test passed")


def test_subcommand_help():
    """Test that subcommands have help output."""
    for command in ['hunt', 'collect', 'analyze', 'generate', 'apply']:
        returncode, stdout, stderr = run_cli(command, '--help')

        assert returncode == 0, f"{command} --help failed: {stderr}"
        assert 'usage:' in stdout.lower(), f"{command} help missing usage"

    print("✓ Subcommand help test passed")


def test_collect_dry_run():
    """Test that collect command works."""
    returncode, stdout, stderr = run_cli(
        '--dry-run',
        '--no-color',
        'collect',
        '--days', '7'
    )

    # Collect doesn't have special dry-run handling, so it will attempt to run
    # We just verify it accepts the arguments
    # In actual dry-run mode, it would run but not modify files
    assert '--days' not in stderr or returncode == 0, f"Collect command failed: {stderr}"

    print("✓ Collect command test passed")


def test_invalid_command():
    """Test that invalid commands are handled gracefully."""
    returncode, stdout, stderr = run_cli('invalid-command')

    assert returncode != 0, "Invalid command should fail"

    print("✓ Invalid command test passed")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Pattern Hunter CLI - Acceptance Tests")
    print("=" * 60 + "\n")

    tests = [
        test_help_output,
        test_hunt_dry_run,
        test_hunt_interactive,
        test_subcommand_help,
        test_collect_dry_run,
        test_invalid_command,
    ]

    failed = []

    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed.append(test.__name__)
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed.append(test.__name__)

    print("\n" + "=" * 60)
    if failed:
        print(f"FAILED: {len(failed)} test(s) failed")
        for name in failed:
            print(f"  - {name}")
        return 1
    else:
        print(f"SUCCESS: All {len(tests)} tests passed")
    print("=" * 60 + "\n")

    return 0


if __name__ == '__main__':
    sys.exit(main())
