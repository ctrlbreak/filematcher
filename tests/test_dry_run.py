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


class TestDryRunStatistics(BaseFileMatcherTest):
    """Tests for dry-run statistics footer."""

    def run_main_with_args(self, args: list[str]) -> str:
        """Helper to run main() with given args and capture stdout."""
        f = io.StringIO()
        with redirect_stdout(f):
            main()
        return f.getvalue()

    def test_statistics_footer_displayed(self):
        """Statistics section should appear at end of output."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1, '--dry-run']):
            output = self.run_main_with_args([])
            # Verify "Statistics" header
            self.assertIn("Statistics", output)
            # Verify "Duplicate groups:" line
            self.assertIn("Duplicate groups:", output)
            # Verify "Duplicate files:" line
            self.assertIn("Duplicate files:", output)
            # Verify "Space to be reclaimed:" line
            self.assertIn("Space to be reclaimed:", output)

    def test_statistics_counts_correct(self):
        """Statistics should show correct counts."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1, '--dry-run']):
            output = self.run_main_with_args([])
            # The base test setup creates 1 duplicate group with 3 files having same content
            # (file1.txt, different_name.txt, file3.txt, also_different_name.txt all have "This is file content A\n")
            # So we should have at least 1 duplicate group
            self.assertIn("Duplicate groups: 1", output)
            # Should show master files preserved
            self.assertIn("Master files preserved:", output)

    def test_verbose_shows_exact_bytes(self):
        """Verbose mode should show exact byte count."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1, '--dry-run', '--verbose']):
            output = self.run_main_with_args([])
            # Verify "(X bytes)" format in verbose output
            self.assertIn("bytes)", output)

    def test_summary_shows_only_statistics(self):
        """--dry-run --summary should show only stats, no file list."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1, '--dry-run', '--summary']):
            output = self.run_main_with_args([])
            # Verify stats present
            self.assertIn("Statistics", output)
            self.assertIn("Duplicate groups:", output)
            # Verify no [MASTER]/[DUP] lines
            self.assertNotIn("[MASTER]", output)
            self.assertNotIn("[DUP:", output)


class TestDryRunActionLabels(BaseFileMatcherTest):
    """Tests for action labels in dry-run output."""

    def run_main_with_args(self, args: list[str]) -> str:
        """Helper to run main() with given args and capture stdout."""
        f = io.StringIO()
        with redirect_stdout(f):
            main()
        return f.getvalue()

    def test_no_action_shows_question_mark(self):
        """Without --action, duplicates show [DUP:?]."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1, '--dry-run']):
            output = self.run_main_with_args([])
            # Verify "[DUP:?]" in output
            self.assertIn("[DUP:?]", output)

    def test_hardlink_action_label(self):
        """With --action hardlink, duplicates show [DUP:hardlink]."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1, '--dry-run', '--action', 'hardlink']):
            output = self.run_main_with_args([])
            self.assertIn("[DUP:hardlink]", output)

    def test_symlink_action_label(self):
        """With --action symlink, duplicates show [DUP:symlink]."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1, '--dry-run', '--action', 'symlink']):
            output = self.run_main_with_args([])
            self.assertIn("[DUP:symlink]", output)

    def test_delete_action_label(self):
        """With --action delete, duplicates show [DUP:delete]."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1, '--dry-run', '--action', 'delete']):
            output = self.run_main_with_args([])
            self.assertIn("[DUP:delete]", output)


class TestDryRunCrossFilesystem(BaseFileMatcherTest):
    """Tests for cross-filesystem warnings."""

    def run_main_with_args(self, args: list[str]) -> str:
        """Helper to run main() with given args and capture stdout."""
        f = io.StringIO()
        with redirect_stdout(f):
            main()
        return f.getvalue()

    def test_cross_fs_warning_in_output(self):
        """Cross-filesystem files should show [!cross-fs] warning."""
        # Mock check_cross_filesystem to return a known set of "cross-filesystem" files
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1, '--dry-run', '--action', 'hardlink']):
            # Get the duplicate file paths that would normally be checked
            # We'll mock check_cross_filesystem to return all duplicates as cross-fs
            with patch('file_matcher.check_cross_filesystem') as mock_check:
                # Return all duplicates as cross-filesystem
                def mock_cross_fs(master_file, duplicates):
                    return set(duplicates)
                mock_check.side_effect = mock_cross_fs
                output = self.run_main_with_args([])
                # Should show [!cross-fs] marker
                self.assertIn("[!cross-fs]", output)

    def test_cross_fs_count_in_statistics(self):
        """Statistics should show count of cross-fs files when present."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1, '--dry-run', '--action', 'hardlink']):
            with patch('file_matcher.check_cross_filesystem') as mock_check:
                # Return all duplicates as cross-filesystem
                def mock_cross_fs(master_file, duplicates):
                    return set(duplicates)
                mock_check.side_effect = mock_cross_fs
                output = self.run_main_with_args([])
                # Should show warning in statistics
                self.assertIn("Warning:", output)
                self.assertIn("cannot hardlink", output)

    def test_no_cross_fs_warning_without_hardlink(self):
        """Cross-filesystem warning should not appear for symlink/delete actions."""
        for action in ['symlink', 'delete']:
            with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1, '--dry-run', '--action', action]):
                output = self.run_main_with_args([])
                # Should NOT show [!cross-fs] marker for non-hardlink actions
                self.assertNotIn("[!cross-fs]", output)


if __name__ == "__main__":
    unittest.main()
