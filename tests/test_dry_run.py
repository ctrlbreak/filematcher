#!/usr/bin/env python3
"""Unit tests for dry-run output formatting."""

from __future__ import annotations

import io
import os
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch

from file_matcher import main, DRY_RUN_BANNER
from tests.test_base import BaseFileMatcherTest


class TestDryRunValidation(BaseFileMatcherTest):
    """Tests for --dry-run flag validation."""

    def run_main_with_args(self, args: list[str]) -> str:
        """Helper to run main() with given args and capture stdout."""
        f = io.StringIO()
        with redirect_stdout(f):
            main()
        return f.getvalue()

    def test_dry_run_requires_master(self):
        """--dry-run without --master should fail with error."""
        stderr_capture = io.StringIO()
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--dry-run']):
            with redirect_stderr(stderr_capture):
                with self.assertRaises(SystemExit) as cm:
                    main()
            self.assertEqual(cm.exception.code, 2)
        error_output = stderr_capture.getvalue()
        self.assertIn("--dry-run requires --master", error_output)

    def test_dry_run_with_master_succeeds(self):
        """--dry-run with --master should not produce validation error."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1, '--dry-run']):
            # Should not raise SystemExit
            output = self.run_main_with_args([])
            # Dry run mode should show banner
            self.assertIn("DRY RUN", output)

    def test_action_choices_valid(self):
        """--action accepts hardlink, symlink, delete."""
        for action in ['hardlink', 'symlink', 'delete']:
            with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1, '--dry-run', '--action', action]):
                output = self.run_main_with_args([])
                # Should not raise error
                self.assertIn("DRY RUN", output)

    def test_action_invalid_choice(self):
        """--action with invalid choice should fail."""
        stderr_capture = io.StringIO()
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1, '--action', 'invalid']):
            with redirect_stderr(stderr_capture):
                with self.assertRaises(SystemExit) as cm:
                    main()
            self.assertEqual(cm.exception.code, 2)
        error_output = stderr_capture.getvalue()
        self.assertIn("invalid choice", error_output)


class TestDryRunBanner(BaseFileMatcherTest):
    """Tests for dry-run banner output."""

    def run_main_with_args(self, args: list[str]) -> str:
        """Helper to run main() with given args and capture stdout."""
        f = io.StringIO()
        with redirect_stdout(f):
            main()
        return f.getvalue()

    def test_banner_displayed_at_top(self):
        """Dry-run banner should appear at start of output."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1, '--dry-run']):
            output = self.run_main_with_args([])
            # Verify "DRY RUN" and "No changes will be made" in output
            self.assertIn("DRY RUN", output)
            self.assertIn("No changes will be made", output)
            # Verify it's at the top (first non-empty line after logging output)
            lines = output.split('\n')
            # Find first line that starts with '=' (the banner)
            banner_index = None
            for i, line in enumerate(lines):
                if line.startswith('==='):
                    banner_index = i
                    break
            self.assertIsNotNone(banner_index, "Banner should appear in output")
            # Banner should appear before any [MASTER] or [DUP] lines
            first_master_index = None
            for i, line in enumerate(lines):
                if '[MASTER]' in line:
                    first_master_index = i
                    break
            if first_master_index is not None:
                self.assertLess(banner_index, first_master_index, "Banner should appear before file listings")

    def test_banner_not_shown_without_dry_run(self):
        """Banner should not appear when --dry-run not specified."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1]):
            output = self.run_main_with_args([])
            self.assertNotIn(DRY_RUN_BANNER, output)
            self.assertNotIn("DRY RUN", output)

    def test_banner_shown_with_summary(self):
        """Banner should appear even with --summary flag."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1, '--dry-run', '--summary']):
            output = self.run_main_with_args([])
            self.assertIn("DRY RUN", output)
            self.assertIn("No changes will be made", output)


if __name__ == "__main__":
    unittest.main()
