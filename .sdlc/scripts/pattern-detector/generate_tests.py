#!/usr/bin/env python3
"""
Defeat Test Generation Module

Automatically generates Python defeat test code for identified patterns.

Usage:
    python generate_tests.py [--input FILE] [--output-dir DIR] [--mock] [--validate-only]

Input:
    JSON file from analyze.py with structure:
    {
        "patterns": [
            {
                "name": "Pattern Name",
                "description": "...",
                "evidence": [...],
                "frequency": "weekly",
                "impact": "high",
                "root_cause": "..."
            }
        ]
    }

Output:
    Python test files in .sdlc/tests/patterns/:
    - test_{pattern_name}.py (defeat test code)
    - Each test is syntactically validated
    - Tests follow defeat test format with metadata docstring
"""

import argparse
import ast
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# Test generation prompt template
TEST_GENERATION_PROMPT = """You are a Python testing expert specializing in static code analysis and anti-pattern detection.

Generate a pytest defeat test for the following anti-pattern:

**Pattern Name:** {pattern_name}
**Description:** {description}
**Evidence:** {evidence}
**Frequency:** {frequency}
**Impact:** {impact}
**Root Cause:** {root_cause}

**REQUIREMENTS:**

1. **File Structure:**
   - Module docstring with metadata (pattern name, severity, generated date)
   - Import statements (pytest, re, ast, pathlib as needed)
   - One or more test functions

2. **Test Function:**
   - Name: test_no_{pattern_slug} or similar descriptive name
   - Docstring explaining what the test prevents
   - Implementation that FAILS when pattern is detected
   - Clear assertion messages with file/line information

3. **Detection Methods (choose appropriate):**
   - **Regex scanning** - for simple text patterns (e.g., `.get(key, default)`)
   - **AST parsing** - for structural code patterns (e.g., function length, bare except)
   - **File content analysis** - for documentation/format issues
   - **Import checking** - for forbidden dependencies

4. **Best Practices:**
   - Scan relevant file types only (*.py for Python patterns)
   - Skip test files, examples, scripts unless pattern applies there too
   - Use relative paths from project root
   - Provide helpful error messages with locations
   - Handle file read errors gracefully

**TEMPLATE EXAMPLES:**

**Regex Pattern Example:**
```python
import re
from pathlib import Path

def test_no_silent_fallbacks():
    \"\"\"Detect .get(key, default) patterns that hide missing data.\"\"\"
    project_root = Path(__file__).parent.parent.parent
    violations = []

    for py_file in project_root.rglob("*.py"):
        if 'test_' in py_file.name:
            continue
        try:
            content = py_file.read_text()
            for i, line in enumerate(content.split('\\n'), 1):
                if re.search(r'\\.get\\([^,]+,\\s*(0|None|\'\'|""|\\[\\]|\\{{\\}})\\)', line):
                    violations.append(f"{{py_file.relative_to(project_root)}}:{{i}}: {{line.strip()}}")
        except Exception:
            continue

    assert not violations, f"Silent fallbacks found:\\n" + "\\n".join(violations[:10])
```

**AST Pattern Example:**
```python
import ast
from pathlib import Path

def test_no_god_functions():
    \"\"\"Functions should be under 50 lines for maintainability.\"\"\"
    project_root = Path(__file__).parent.parent.parent
    violations = []

    for py_file in project_root.rglob("*.py"):
        try:
            tree = ast.parse(py_file.read_text())
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    length = node.end_lineno - node.lineno + 1
                    if length > 50:
                        violations.append(
                            f"{{py_file.relative_to(project_root)}}:{{node.name}} = {{length}} lines"
                        )
        except SyntaxError:
            continue

    assert not violations, f"God functions found:\\n" + "\\n".join(violations[:10])
```

**OUTPUT FORMAT:**

Return ONLY valid Python code (no markdown, no commentary, no code fences).
Start with the module docstring, then imports, then test functions.

Generate the complete defeat test now:
"""

# Mock test templates for testing without API calls
MOCK_TESTS = {
    "silent_fallback": r'''#!/usr/bin/env python3
"""
Defeat Test: No Silent Fallbacks
Pattern: silent_fallback
Severity: HIGH
Generated: {generated_date}
Description: Using .get() with default values instead of explicit validation
"""
import re
from pathlib import Path


def test_no_silent_fallbacks():
    """Detect .get(key, default) patterns that silently hide missing data."""
    project_root = Path(__file__).parent.parent.parent
    violations = []

    # Pattern to detect .get() with default values
    pattern = r'\.get\([^,]+,\s*(0|None|\'\'|""|\\[\\]|\\{{\\}})\)'

    for py_file in project_root.rglob("*.py"):
        # Skip test files and examples
        if 'test_' in py_file.name or 'example' in str(py_file).lower():
            continue

        try:
            content = py_file.read_text()
            for i, line in enumerate(content.split('\n'), 1):
                if re.search(pattern, line):
                    relative_path = py_file.relative_to(project_root)
                    violations.append(f"{{relative_path}}:{{i}}: {{line.strip()}}")
        except Exception:
            continue

    assert not violations, (
        f"Silent fallbacks found (use explicit validation instead):\n" +
        "\n".join(violations[:10])
    )
''',
    "missing_error_context": '''#!/usr/bin/env python3
"""
Defeat Test: No Missing Error Context
Pattern: missing_error_context
Severity: MEDIUM
Generated: {generated_date}
Description: Raising exceptions without context about what failed
"""
import ast
from pathlib import Path


def test_no_missing_error_context():
    """Detect raise statements without contextual information."""
    project_root = Path(__file__).parent.parent.parent
    violations = []

    for py_file in project_root.rglob("*.py"):
        if 'test_' in py_file.name:
            continue

        try:
            tree = ast.parse(py_file.read_text())

            for node in ast.walk(tree):
                if isinstance(node, ast.Raise):
                    # Check if exception has no message or very short message
                    if node.exc and isinstance(node.exc, ast.Call):
                        if not node.exc.args or (
                            len(node.exc.args) == 1 and
                            isinstance(node.exc.args[0], ast.Constant) and
                            len(str(node.exc.args[0].value)) < 10
                        ):
                            relative_path = py_file.relative_to(project_root)
                            violations.append(
                                f"{{relative_path}}:{{node.lineno}}: "
                                f"Exception lacks context"
                            )
        except SyntaxError:
            continue

    assert not violations, (
        f"Exceptions without context found:\\n" +
        "\\n".join(violations[:10]) +
        "\\n\\nAdd context: what failed, what data, what was expected"
    )
''',
    "default": '''#!/usr/bin/env python3
"""
Defeat Test: {pattern_title}
Pattern: {pattern_slug}
Severity: {severity}
Generated: {generated_date}
Description: {description}
"""
import re
from pathlib import Path


def test_no_{pattern_slug}():
    """Detect and prevent {pattern_title} pattern."""
    project_root = Path(__file__).parent.parent.parent
    violations = []

    # TODO: Implement pattern detection logic
    # This is a placeholder test - customize based on pattern

    for py_file in project_root.rglob("*.py"):
        if 'test_' in py_file.name:
            continue

        try:
            content = py_file.read_text()
            # Add pattern detection here
            # Example: if pattern in content:
            #     violations.append(f"{{py_file}}:{{line_num}}")
        except Exception:
            continue

    assert not violations, (
        f"{pattern_title} pattern found:\\n" +
        "\\n".join(violations[:10])
    )
'''
}


class TestGenerator:
    """Generates defeat tests from pattern analysis."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        use_cli: bool = True,
        mock: bool = False
    ):
        """
        Initialize test generator.

        Args:
            api_key: Anthropic API key (optional if using CLI or environment variable)
            use_cli: Use Claude CLI instead of Python SDK (default: True)
            mock: Use mock templates instead of real API calls (default: False)
        """
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        self.use_cli = use_cli
        self.mock = mock
        self.max_retries = 3
        self.retry_delay = 2

    def _call_claude_cli(self, prompt: str) -> str:
        """
        Call Claude using the CLI.

        Args:
            prompt: Test generation prompt

        Returns:
            Claude's response

        Raises:
            Exception: If CLI call fails
        """
        try:
            result = subprocess.run(
                ['claude', '-p', prompt],
                capture_output=True,
                text=True,
                check=True,
                timeout=120
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
            prompt: Test generation prompt

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

    def _generate_pattern_slug(self, pattern_name: str) -> str:
        """
        Generate a valid Python identifier from pattern name.

        Args:
            pattern_name: Human-readable pattern name

        Returns:
            snake_case slug suitable for function/file names
        """
        # Convert to lowercase
        slug = pattern_name.lower()
        # Replace spaces and special chars with underscores
        slug = re.sub(r'[^a-z0-9]+', '_', slug)
        # Remove leading/trailing underscores
        slug = slug.strip('_')
        # Collapse multiple underscores
        slug = re.sub(r'_+', '_', slug)
        return slug

    def _validate_python_syntax(self, code: str) -> tuple[bool, Optional[str]]:
        """
        Validate that generated code is syntactically correct Python.

        Args:
            code: Python code to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            ast.parse(code)
            return True, None
        except SyntaxError as e:
            return False, f"Syntax error at line {e.lineno}: {e.msg}"
        except Exception as e:
            return False, f"Parse error: {str(e)}"

    def _clean_claude_response(self, response: str) -> str:
        """
        Clean Claude's response to extract just the Python code.

        Args:
            response: Raw response from Claude

        Returns:
            Clean Python code
        """
        # Remove markdown code blocks if present
        response = response.strip()
        if response.startswith('```'):
            lines = response.split('\n')
            # Remove first line (```python or ```)
            lines = lines[1:]
            # Remove last line (```)
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            response = '\n'.join(lines)

        return response.strip()

    def _get_mock_template(self, pattern_slug: str, pattern: Dict[str, Any]) -> str:
        """
        Get mock test template for testing without API calls.

        Args:
            pattern_slug: Pattern slug identifier
            pattern: Pattern dictionary

        Returns:
            Mock test code
        """
        # Check for exact match first
        if pattern_slug in MOCK_TESTS:
            template = MOCK_TESTS[pattern_slug]
        # Check for partial matches (e.g., "silent_fallback_pattern" matches "silent_fallback")
        else:
            matched = False
            for key in MOCK_TESTS:
                if key != 'default' and (key in pattern_slug or pattern_slug.startswith(key)):
                    template = MOCK_TESTS[key]
                    matched = True
                    break
            if not matched:
                template = MOCK_TESTS['default']

        # Format template
        return template.format(
            pattern_title=pattern['name'],
            pattern_slug=pattern_slug,
            severity=pattern.get('impact', 'MEDIUM').upper(),
            generated_date=datetime.now().strftime('%Y-%m-%d'),
            description=pattern['description']
        )

    def generate_test(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a defeat test for a single pattern.

        Args:
            pattern: Pattern dictionary with keys:
                - name: Pattern name
                - description: What the pattern is
                - evidence: List of evidence
                - frequency: How often it occurs
                - impact: Severity (high/medium/low)
                - root_cause: Why it happens

        Returns:
            Dictionary with:
                - pattern_name: Original pattern name
                - pattern_slug: Slug for filename
                - test_code: Generated Python code
                - validation: Syntax validation result
                - filename: Suggested filename
        """
        pattern_name = pattern['name']
        pattern_slug = self._generate_pattern_slug(pattern_name)

        print(f"Generating test for: {pattern_name}...", file=sys.stderr)

        # Generate test code
        if self.mock:
            print(f"  Using mock template", file=sys.stderr)
            test_code = self._get_mock_template(pattern_slug, pattern)
        else:
            # Create prompt
            prompt = TEST_GENERATION_PROMPT.format(
                pattern_name=pattern_name,
                pattern_slug=pattern_slug,
                description=pattern['description'],
                evidence='\n'.join(f"  - {e}" for e in pattern.get('evidence', [])),
                frequency=pattern.get('frequency', 'unknown'),
                impact=pattern.get('impact', 'medium'),
                root_cause=pattern.get('root_cause', 'Unknown')
            )

            # Call Claude
            try:
                if self.use_cli:
                    response = self._call_claude_cli(prompt)
                else:
                    response = self._call_claude_sdk(prompt)

                test_code = self._clean_claude_response(response)
                print(f"  Generated {len(test_code)} characters", file=sys.stderr)
            except Exception as e:
                print(f"  Error generating test: {e}", file=sys.stderr)
                print(f"  Falling back to mock template", file=sys.stderr)
                test_code = self._get_mock_template(pattern_slug, pattern)

        # Validate syntax
        is_valid, error = self._validate_python_syntax(test_code)

        if is_valid:
            print(f"  ✓ Syntax validation passed", file=sys.stderr)
        else:
            print(f"  ✗ Syntax validation failed: {error}", file=sys.stderr)

        return {
            'pattern_name': pattern_name,
            'pattern_slug': pattern_slug,
            'test_code': test_code,
            'validation': {
                'is_valid': is_valid,
                'error': error
            },
            'filename': f"test_{pattern_slug}.py"
        }

    def generate_all_tests(
        self,
        patterns: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate defeat tests for all patterns.

        Args:
            patterns: List of pattern dictionaries

        Returns:
            List of test generation results
        """
        results = []

        for i, pattern in enumerate(patterns, 1):
            print(f"\n[{i}/{len(patterns)}] ", file=sys.stderr, end='')
            result = self.generate_test(pattern)
            results.append(result)

        return results

    def write_test_files(
        self,
        results: List[Dict[str, Any]],
        output_dir: Path
    ) -> List[Path]:
        """
        Write generated tests to files.

        Args:
            results: Test generation results
            output_dir: Directory to write test files

        Returns:
            List of written file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        written_files = []

        for result in results:
            if not result['validation']['is_valid']:
                print(
                    f"Skipping {result['filename']}: syntax validation failed",
                    file=sys.stderr
                )
                continue

            filepath = output_dir / result['filename']
            filepath.write_text(result['test_code'])
            filepath.chmod(0o755)  # Make executable

            written_files.append(filepath)
            print(f"Wrote: {filepath}", file=sys.stderr)

        return written_files


def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description='Generate defeat tests from pattern analysis.'
    )
    parser.add_argument(
        '--input',
        help='Input JSON file from analyze.py (default: read from stdin)'
    )
    parser.add_argument(
        '--output-dir',
        default='.sdlc/tests/patterns',
        help='Output directory for test files (default: .sdlc/tests/patterns)'
    )
    parser.add_argument(
        '--mock',
        action='store_true',
        help='Use mock templates instead of calling Claude API'
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
        '--validate-only',
        action='store_true',
        help='Only validate existing tests, do not generate new ones'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Generate tests but do not write files'
    )

    args = parser.parse_args()

    try:
        # Validate-only mode
        if args.validate_only:
            print("Validating existing tests...", file=sys.stderr)
            test_dir = Path(args.output_dir)
            if not test_dir.exists():
                print(f"Test directory does not exist: {test_dir}", file=sys.stderr)
                return 1

            test_files = list(test_dir.glob("test_*.py"))
            print(f"Found {len(test_files)} test files", file=sys.stderr)

            generator = TestGenerator()
            invalid_count = 0

            for test_file in test_files:
                code = test_file.read_text()
                is_valid, error = generator._validate_python_syntax(code)

                if is_valid:
                    print(f"✓ {test_file.name}", file=sys.stderr)
                else:
                    print(f"✗ {test_file.name}: {error}", file=sys.stderr)
                    invalid_count += 1

            if invalid_count > 0:
                print(f"\n{invalid_count} test(s) failed validation", file=sys.stderr)
                return 1
            else:
                print(f"\nAll tests validated successfully", file=sys.stderr)
                return 0

        # Read input patterns
        if args.input:
            with open(args.input, 'r') as f:
                data = json.load(f)
        else:
            data = json.load(sys.stdin)

        patterns = data.get('patterns', [])

        if not patterns:
            print("No patterns found in input", file=sys.stderr)
            return 1

        print(f"Generating tests for {len(patterns)} patterns...", file=sys.stderr)

        # Initialize generator
        generator = TestGenerator(
            api_key=args.api_key,
            use_cli=not args.use_sdk,
            mock=args.mock
        )

        # Generate tests
        results = generator.generate_all_tests(patterns)

        # Summary
        valid_count = sum(1 for r in results if r['validation']['is_valid'])
        invalid_count = len(results) - valid_count

        print(f"\n=== Generation Summary ===", file=sys.stderr)
        print(f"Total patterns: {len(patterns)}", file=sys.stderr)
        print(f"Valid tests: {valid_count}", file=sys.stderr)
        print(f"Invalid tests: {invalid_count}", file=sys.stderr)

        # Write files (unless dry-run)
        if not args.dry_run:
            written_files = generator.write_test_files(results, args.output_dir)
            print(f"\nWrote {len(written_files)} test files to {args.output_dir}", file=sys.stderr)

            # Output file list to stdout (for scripting)
            for filepath in written_files:
                print(str(filepath))
        else:
            print("\nDry-run mode: no files written", file=sys.stderr)

        return 0 if invalid_count == 0 else 1

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
