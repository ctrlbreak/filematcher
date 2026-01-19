#!/usr/bin/env python3
"""Unit tests for safe defaults (preview-by-default) behavior."""

from __future__ import annotations

import io
import os
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch

from file_matcher import main, PREVIEW_BANNER, EXECUTE_BANNER, confirm_execution
from tests.test_base import BaseFileMatcherTest


class TestFlagValidation(BaseFileMatcherTest):
    """Tests for flag validation."""

    def run_main_with_args(self, args: list[str]) -> str:
        """Helper to run main() with given args and capture stdout."""
        f = io.StringIO()
        with redirect_stdout(f):
            main()
        return f.getvalue()

    def test_dry_run_flag_removed(self):
        """--dry-run flag should produce unrecognized arguments error."""
        stderr_capture = io.StringIO()
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--dry-run']):
            with redirect_stderr(stderr_capture):
                with self.assertRaises(SystemExit) as cm:
                    main()
            self.assertEqual(cm.exception.code, 2)
        error_output = stderr_capture.getvalue()
        self.assertIn("unrecognized arguments", error_output)

    def test_action_with_master_shows_preview(self):
        """--action with --master (no --execute) should show PREVIEW MODE."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1, '--action', 'hardlink']):
            output = self.run_main_with_args([])
            self.assertIn("PREVIEW MODE", output)

    def test_action_choices_valid(self):
        """--action accepts hardlink, symlink, delete (shows preview)."""
        for action in ['hardlink', 'symlink', 'delete']:
            with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1, '--action', action]):
                output = self.run_main_with_args([])
                # Should show preview mode
                self.assertIn("PREVIEW MODE", output)

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

    def test_execute_requires_master_and_action(self):
        """--execute without --master and --action should fail."""
        # Test --execute without --master
        stderr_capture = io.StringIO()
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--execute']):
            with redirect_stderr(stderr_capture):
                with self.assertRaises(SystemExit) as cm:
                    main()
            self.assertEqual(cm.exception.code, 2)
        error_output = stderr_capture.getvalue()
        self.assertIn("--execute requires --master and --action", error_output)

        # Test --execute with --master but no --action
        stderr_capture = io.StringIO()
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1, '--execute']):
            with redirect_stderr(stderr_capture):
                with self.assertRaises(SystemExit) as cm:
                    main()
            self.assertEqual(cm.exception.code, 2)
        error_output = stderr_capture.getvalue()
        self.assertIn("--execute requires --master and --action", error_output)


class TestPreviewBanner(BaseFileMatcherTest):
    """Tests for preview mode banner output."""

    def run_main_with_args(self, args: list[str]) -> str:
        """Helper to run main() with given args and capture stdout."""
        f = io.StringIO()
        with redirect_stdout(f):
            main()
        return f.getvalue()

    def test_banner_displayed_at_top(self):
        """Preview banner should appear at start of output."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1, '--action', 'hardlink']):
            output = self.run_main_with_args([])
            # Verify "PREVIEW MODE" in output
            self.assertIn("PREVIEW MODE", output)
            self.assertIn("Use --execute to apply changes", output)
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

    def test_banner_not_shown_without_action(self):
        """Banner should not appear when --action not specified."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1]):
            output = self.run_main_with_args([])
            self.assertNotIn(PREVIEW_BANNER, output)
            self.assertNotIn("PREVIEW MODE", output)

    def test_banner_shown_with_summary(self):
        """Preview banner should appear even with --summary flag."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1, '--action', 'hardlink', '--summary']):
            output = self.run_main_with_args([])
            self.assertIn("PREVIEW MODE", output)
            self.assertIn("Use --execute to apply changes", output)


class TestPreviewStatistics(BaseFileMatcherTest):
    """Tests for preview mode statistics footer."""

    def run_main_with_args(self, args: list[str]) -> str:
        """Helper to run main() with given args and capture stdout."""
        f = io.StringIO()
        with redirect_stdout(f):
            main()
        return f.getvalue()

    def test_statistics_footer_displayed(self):
        """Statistics section should appear at end of output."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1, '--action', 'hardlink']):
            output = self.run_main_with_args([])
            # Verify "Statistics" header
            self.assertIn("Statistics", output)
            # Verify "Duplicate groups:" line
            self.assertIn("Duplicate groups:", output)
            # Verify "Duplicate files:" line
            self.assertIn("Duplicate files:", output)
            # Verify "Space to be reclaimed:" line
            self.assertIn("Space to be reclaimed:", output)
            # Verify hint about --execute
            self.assertIn("Use --execute to apply changes", output)

    def test_statistics_counts_correct(self):
        """Statistics should show correct counts."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1, '--action', 'hardlink']):
            output = self.run_main_with_args([])
            # The base test setup creates 1 duplicate group with 3 files having same content
            # (file1.txt, different_name.txt, file3.txt, also_different_name.txt all have "This is file content A\n")
            # So we should have at least 1 duplicate group
            self.assertIn("Duplicate groups: 1", output)
            # Should show master files preserved
            self.assertIn("Master files preserved:", output)

    def test_verbose_shows_exact_bytes(self):
        """Verbose mode should show exact byte count."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1, '--action', 'hardlink', '--verbose']):
            output = self.run_main_with_args([])
            # Verify "(X bytes)" format in verbose output
            self.assertIn("bytes)", output)

    def test_summary_shows_only_statistics(self):
        """--action --summary should show only stats, no file list."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1, '--action', 'hardlink', '--summary']):
            output = self.run_main_with_args([])
            # Verify stats present
            self.assertIn("Statistics", output)
            self.assertIn("Duplicate groups:", output)
            # Verify no [MASTER] lines (summary mode hides file listing)
            self.assertNotIn("[MASTER]", output)
            # Verify no WOULD labels (summary mode hides file listing)
            self.assertNotIn("[WOULD", output)


class TestPreviewActionLabels(BaseFileMatcherTest):
    """Tests for action labels in preview output."""

    def run_main_with_args(self, args: list[str]) -> str:
        """Helper to run main() with given args and capture stdout."""
        f = io.StringIO()
        with redirect_stdout(f):
            main()
        return f.getvalue()

    def test_hardlink_action_label(self):
        """With --action hardlink, duplicates show [WOULD HARDLINK]."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1, '--action', 'hardlink']):
            output = self.run_main_with_args([])
            self.assertIn("[WOULD HARDLINK]", output)

    def test_symlink_action_label(self):
        """With --action symlink, duplicates show [WOULD SYMLINK]."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1, '--action', 'symlink']):
            output = self.run_main_with_args([])
            self.assertIn("[WOULD SYMLINK]", output)

    def test_delete_action_label(self):
        """With --action delete, duplicates show [WOULD DELETE]."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1, '--action', 'delete']):
            output = self.run_main_with_args([])
            self.assertIn("[WOULD DELETE]", output)

    def test_no_action_shows_question_mark(self):
        """Without --action, duplicates show [DUP:?] in master mode."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1]):
            output = self.run_main_with_args([])
            # In master mode without action, should show [DUP:?]
            self.assertIn("[DUP:?]", output)


class TestCrossFilesystemWarnings(BaseFileMatcherTest):
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
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1, '--action', 'hardlink']):
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
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1, '--action', 'hardlink']):
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
            with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1, '--action', action]):
                output = self.run_main_with_args([])
                # Should NOT show [!cross-fs] marker for non-hardlink actions
                self.assertNotIn("[!cross-fs]", output)


if __name__ == "__main__":
    unittest.main()
