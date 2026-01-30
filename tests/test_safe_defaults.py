#!/usr/bin/env python3
"""Unit tests for safe defaults (preview-by-default) behavior."""

from __future__ import annotations

import io
import os
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch

from filematcher import main, PREVIEW_BANNER, EXECUTE_BANNER, confirm_execution
from tests.test_base import BaseFileMatcherTest
import json


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

    def test_action_shows_preview(self):
        """--action (no --execute) should show PREVIEW MODE."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--action', 'hardlink']):
            output = self.run_main_with_args([])
            self.assertIn("PREVIEW MODE", output)

    def test_action_choices_valid(self):
        """--action accepts hardlink, symlink, delete (shows preview)."""
        for action in ['hardlink', 'symlink', 'delete']:
            with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--action', action]):
                output = self.run_main_with_args([])
                # Should show preview mode
                self.assertIn("PREVIEW MODE", output)

    def test_action_invalid_choice(self):
        """--action with invalid choice should fail."""
        stderr_capture = io.StringIO()
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--action', 'invalid']):
            with redirect_stderr(stderr_capture):
                with self.assertRaises(SystemExit) as cm:
                    main()
            self.assertEqual(cm.exception.code, 2)
        error_output = stderr_capture.getvalue()
        self.assertIn("invalid choice", error_output)

    def test_execute_with_compare_action_fails(self):
        """--execute with compare action (default) should fail."""
        stderr_capture = io.StringIO()
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--execute']):
            with redirect_stderr(stderr_capture):
                with self.assertRaises(SystemExit) as cm:
                    main()
            self.assertEqual(cm.exception.code, 2)
        error_output = stderr_capture.getvalue()
        self.assertIn("compare action doesn't modify files", error_output)


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
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--action', 'hardlink']):
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
            # Banner should appear before any MASTER: or DUP: lines
            first_master_index = None
            for i, line in enumerate(lines):
                if 'MASTER:' in line:
                    first_master_index = i
                    break
            if first_master_index is not None:
                self.assertLess(banner_index, first_master_index, "Banner should appear before file listings")

    def test_banner_not_shown_without_action(self):
        """Banner should not appear when --action not specified."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2]):
            output = self.run_main_with_args([])
            self.assertNotIn(PREVIEW_BANNER, output)
            self.assertNotIn("PREVIEW MODE", output)

    def test_banner_shown_with_summary(self):
        """Preview banner should appear even with --summary flag."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--action', 'hardlink', '--summary']):
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
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--action', 'hardlink']):
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
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--action', 'hardlink']):
            output = self.run_main_with_args([])
            # The base test setup creates 1 duplicate group with 3 files having same content
            # (file1.txt, different_name.txt, file3.txt, also_different_name.txt all have "This is file content A\n")
            # So we should have at least 1 duplicate group
            self.assertIn("Duplicate groups: 1", output)
            # Should show master files preserved
            self.assertIn("Master files preserved:", output)

    def test_verbose_shows_exact_bytes(self):
        """Verbose mode should show exact byte count."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--action', 'hardlink', '--verbose']):
            output = self.run_main_with_args([])
            # Verify "(X bytes)" format in verbose output
            self.assertIn("bytes)", output)

    def test_summary_shows_only_statistics(self):
        """--action --summary should show only stats, no file list."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--action', 'hardlink', '--summary']):
            output = self.run_main_with_args([])
            # Verify stats present
            self.assertIn("Statistics", output)
            self.assertIn("Duplicate groups:", output)
            # Verify no MASTER: lines (summary mode hides file listing)
            self.assertNotIn("MASTER:", output)
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
        """With --action hardlink, duplicates show WOULD HARDLINK:."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--action', 'hardlink']):
            output = self.run_main_with_args([])
            self.assertIn("WOULD HARDLINK:", output)

    def test_symlink_action_label(self):
        """With --action symlink, duplicates show WOULD SYMLINK:."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--action', 'symlink']):
            output = self.run_main_with_args([])
            self.assertIn("WOULD SYMLINK:", output)

    def test_delete_action_label(self):
        """With --action delete, duplicates show WOULD DELETE:."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--action', 'delete']):
            output = self.run_main_with_args([])
            self.assertIn("WOULD DELETE:", output)

class TestExecuteMode(BaseFileMatcherTest):
    """Tests for --execute flag behavior."""

    def run_main_with_args(self, args: list[str]) -> str:
        """Helper to run main() with given args and capture stdout."""
        f = io.StringIO()
        with redirect_stdout(f):
            main()
        return f.getvalue()

    def test_execute_shows_will_labels_then_banner(self):
        """--execute should show 'WILL' labels (not WOULD/PREVIEW) then EXECUTE MODE banner."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2,
                   '--action', 'hardlink', '--execute']):
            with patch('sys.stdin.isatty', return_value=True):
                with patch('builtins.input', return_value='n'):
                    output = self.run_main_with_args([])
                    # With --execute, pre-execution display uses "WILL" not "WOULD"
                    self.assertIn("WILL HARDLINK", output)
                    self.assertNotIn("WOULD HARDLINK", output)
                    # No PREVIEW banner when --execute is set
                    self.assertNotIn("PREVIEW MODE", output)
                    # EXECUTE MODE banner shown before groups
                    self.assertIn("EXECUTE MODE!", output)

    def test_execute_prompts_for_confirmation(self):
        """--execute should prompt user before proceeding."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2,
                   '--action', 'hardlink', '--execute']):
            with patch('sys.stdin.isatty', return_value=True):
                with patch('builtins.input', return_value='n') as mock_input:
                    self.run_main_with_args([])
                    mock_input.assert_called_once()
                    # Verify prompt text
                    call_args = mock_input.call_args[0][0] if mock_input.call_args[0] else ""
                    self.assertIn("[y/N]", call_args)

    def test_execute_abort_shows_message(self):
        """Declining confirmation should show abort message."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2,
                   '--action', 'hardlink', '--execute']):
            with patch('sys.stdin.isatty', return_value=True):
                with patch('builtins.input', return_value='n'):
                    output = self.run_main_with_args([])
                    self.assertIn("Aborted", output)
                    self.assertIn("No changes made", output)

    def test_execute_abort_exit_code_zero(self):
        """Aborting should exit with code 0 (not an error)."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2,
                   '--action', 'hardlink', '--execute']):
            with patch('sys.stdin.isatty', return_value=True):
                with patch('builtins.input', return_value='n'):
                    f = io.StringIO()
                    with redirect_stdout(f):
                        result = main()
                    self.assertEqual(result, 0)

    def test_yes_flag_skips_confirmation(self):
        """--yes should skip the confirmation prompt entirely."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2,
                   '--action', 'hardlink', '--execute', '--yes']):
            with patch('builtins.input') as mock_input:
                self.run_main_with_args([])
                mock_input.assert_not_called()

    def test_confirmation_accepts_affirmative_responses(self):
        """Confirmation accepts 'y', 'yes', 'Y', 'YES', 'Yes' (case insensitive)."""
        affirmative_responses = ['y', 'yes', 'Y', 'YES', 'Yes']
        for response in affirmative_responses:
            with self.subTest(response=response):
                with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2,
                           '--action', 'hardlink', '--execute']):
                    with patch('sys.stdin.isatty', return_value=True):
                        with patch('builtins.input', return_value=response):
                            output = self.run_main_with_args([])
                            self.assertNotIn("Aborted", output, f"Response '{response}' should proceed")


class TestNonInteractiveMode(BaseFileMatcherTest):
    """Tests for non-interactive (piped/scripted) mode."""

    def test_non_tty_defaults_to_abort(self):
        """Non-interactive mode should fail-fast with parser.error without --yes.

        This is fail-fast validation - fails BEFORE file scanning begins.
        Exit code 2 is the argparse standard for argument errors.
        """
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2,
                   '--action', 'hardlink', '--execute']):
            with patch('sys.stdin.isatty', return_value=False):
                stderr_capture = io.StringIO()
                with redirect_stderr(stderr_capture):
                    with self.assertRaises(SystemExit) as cm:
                        main()
                self.assertEqual(cm.exception.code, 2)
                # Should show error about stdin not being a terminal
                error_output = stderr_capture.getvalue()
                self.assertIn("stdin", error_output.lower())
                self.assertIn("terminal", error_output.lower())

    def test_non_tty_with_yes_proceeds(self):
        """Non-interactive mode with --yes should proceed without prompt."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2,
                   '--action', 'hardlink', '--execute', '--yes']):
            with patch('sys.stdin.isatty', return_value=False):
                f = io.StringIO()
                with redirect_stdout(f):
                    main()
                output = f.getvalue()
                # Should NOT show abort message
                self.assertNotIn("Aborted", output)


class TestInteractiveFlagValidation(BaseFileMatcherTest):
    """Tests for interactive mode flag validation."""

    def test_quiet_execute_without_yes_fails(self):
        """--quiet --execute without --yes should fail."""
        stderr_capture = io.StringIO()
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2,
                   '--action', 'delete', '--execute', '--quiet']):
            with redirect_stderr(stderr_capture):
                with self.assertRaises(SystemExit) as cm:
                    main()
            self.assertEqual(cm.exception.code, 2)
        error_output = stderr_capture.getvalue()
        self.assertIn("--quiet", error_output)
        self.assertIn("interactive", error_output.lower())

    def test_quiet_execute_with_yes_succeeds(self):
        """--quiet --execute --yes should work (batch mode)."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2,
                   '--action', 'hardlink', '--execute', '--quiet', '--yes']):
            f = io.StringIO()
            with redirect_stdout(f):
                result = main()
            # Should succeed (may have 0 or partial success depending on test files)
            self.assertIn(result, [0, 2])  # 0 success, 2 partial

    def test_non_tty_execute_without_yes_fails(self):
        """Non-TTY stdin with --execute (no --yes) should fail early."""
        stderr_capture = io.StringIO()
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2,
                   '--action', 'delete', '--execute']):
            with patch('sys.stdin.isatty', return_value=False):
                with redirect_stderr(stderr_capture):
                    with self.assertRaises(SystemExit) as cm:
                        main()
                self.assertEqual(cm.exception.code, 2)
        error_output = stderr_capture.getvalue()
        self.assertIn("stdin", error_output.lower())
        self.assertIn("terminal", error_output.lower())

    def test_json_execute_without_yes_fails(self):
        """--json --execute without --yes should fail (existing behavior)."""
        stderr_capture = io.StringIO()
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2,
                   '--action', 'delete', '--execute', '--json']):
            with redirect_stderr(stderr_capture):
                with self.assertRaises(SystemExit) as cm:
                    main()
            self.assertEqual(cm.exception.code, 2)
        error_output = stderr_capture.getvalue()
        self.assertIn("--json", error_output)

    def test_json_execute_with_yes_succeeds(self):
        """--json --execute --yes should work."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2,
                   '--action', 'hardlink', '--execute', '--json', '--yes']):
            f = io.StringIO()
            with redirect_stdout(f):
                result = main()
            output = f.getvalue()
            # Should produce valid JSON
            data = json.loads(output)
            self.assertIn("execution", data)


if __name__ == "__main__":
    unittest.main()
