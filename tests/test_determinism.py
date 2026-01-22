"""Tests for output determinism (OUT-04).

Verifies that running the same command multiple times produces
identical output, regardless of hash iteration order or filesystem
ordering.
"""

import unittest
import subprocess
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDeterminism(unittest.TestCase):
    """Test that output is deterministic across multiple runs."""

    def test_compare_mode_determinism(self):
        """Compare mode produces identical output on repeated runs."""
        cmd = [sys.executable, 'file_matcher.py', 'test_dir1', 'test_dir2']

        # Run 5 times and compare
        outputs = []
        for _ in range(5):
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            outputs.append(result.stdout)

        # All outputs should be identical
        for i, output in enumerate(outputs[1:], start=2):
            self.assertEqual(
                outputs[0], output,
                f"Run 1 and run {i} produced different output"
            )

    def test_action_mode_determinism(self):
        """Action mode produces identical output on repeated runs."""
        cmd = [
            sys.executable, 'file_matcher.py',
            'test_dir1', 'test_dir2',
            '--action', 'hardlink'
        ]

        outputs = []
        for _ in range(5):
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            outputs.append(result.stdout)

        for i, output in enumerate(outputs[1:], start=2):
            self.assertEqual(
                outputs[0], output,
                f"Run 1 and run {i} produced different output"
            )

    def test_unmatched_mode_determinism(self):
        """Unmatched files output is deterministic."""
        cmd = [
            sys.executable, 'file_matcher.py',
            'test_dir1', 'test_dir2',
            '--show-unmatched'
        ]

        outputs = []
        for _ in range(5):
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            outputs.append(result.stdout)

        for i, output in enumerate(outputs[1:], start=2):
            self.assertEqual(
                outputs[0], output,
                f"Run 1 and run {i} produced different output"
            )

    def test_verbose_mode_determinism(self):
        """Verbose mode produces identical output on repeated runs."""
        cmd = [
            sys.executable, 'file_matcher.py',
            'test_dir1', 'test_dir2',
            '--action', 'hardlink',
            '--verbose'
        ]

        outputs = []
        for _ in range(5):
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            outputs.append(result.stdout)

        for i, output in enumerate(outputs[1:], start=2):
            self.assertEqual(
                outputs[0], output,
                f"Run 1 and run {i} produced different output"
            )


if __name__ == '__main__':
    unittest.main()
