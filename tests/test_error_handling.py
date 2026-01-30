"""Tests for error handling and execution summaries (Phase 21)."""

from __future__ import annotations

import unittest
import json
from io import StringIO
from unittest.mock import patch

from filematcher.formatters import TextActionFormatter, JsonActionFormatter
from filematcher.colors import ColorConfig, ColorMode
from filematcher.types import FailedOperation
from filematcher.cli import EXIT_SUCCESS, EXIT_PARTIAL, EXIT_USER_QUIT


class TestFormatFileError(unittest.TestCase):
    """Tests for format_file_error() method."""

    def test_text_format_file_error_output(self):
        """Verify text output includes path and error message."""
        formatter = TextActionFormatter(
            verbose=False,
            preview_mode=False,
            action='delete',
            color_config=ColorConfig(mode=ColorMode.NEVER)
        )

        captured = StringIO()
        with patch('sys.stdout', captured):
            formatter.format_file_error('/path/to/file.txt', 'Permission denied')

        output = captured.getvalue()
        self.assertIn('/path/to/file.txt', output)
        self.assertIn('Permission denied', output)
        self.assertIn('\u2717', output)  # X mark

    def test_json_format_file_error_accumulates(self):
        """Verify JSON accumulates errors in errors array."""
        formatter = JsonActionFormatter(
            verbose=False,
            preview_mode=False,
            action='delete'
        )

        formatter.format_file_error('/path/one.txt', 'Error 1')
        formatter.format_file_error('/path/two.txt', 'Error 2')

        self.assertIn('errors', formatter._data)
        self.assertEqual(len(formatter._data['errors']), 2)
        self.assertEqual(formatter._data['errors'][0]['path'], '/path/one.txt')
        self.assertEqual(formatter._data['errors'][0]['error'], 'Error 1')
        self.assertEqual(formatter._data['errors'][1]['path'], '/path/two.txt')
        self.assertEqual(formatter._data['errors'][1]['error'], 'Error 2')


class TestFormatQuitSummary(unittest.TestCase):
    """Tests for format_quit_summary() method."""

    def test_text_format_quit_summary_all_fields(self):
        """Verify all fields present in text quit summary."""
        formatter = TextActionFormatter(
            verbose=False,
            preview_mode=False,
            action='hardlink',
            color_config=ColorConfig(mode=ColorMode.NEVER)
        )

        captured = StringIO()
        with patch('sys.stdout', captured):
            formatter.format_quit_summary(
                confirmed_count=5,
                skipped_count=2,
                remaining_count=3,
                space_saved=1000000,
                log_path='/logs/audit.log'
            )

        output = captured.getvalue()
        self.assertIn('5 processed', output)
        self.assertIn('2 skipped', output)
        self.assertIn('3 remaining', output)
        self.assertIn('Freed', output)
        self.assertIn('976.6 KB', output)  # format_file_size result
        self.assertIn('/logs/audit.log', output)
        self.assertIn('Re-run command', output)

    def test_text_format_quit_summary_zero_space(self):
        """Verify no 'Freed' line when space_saved=0."""
        formatter = TextActionFormatter(
            verbose=False,
            preview_mode=False,
            action='delete',
            color_config=ColorConfig(mode=ColorMode.NEVER)
        )

        captured = StringIO()
        with patch('sys.stdout', captured):
            formatter.format_quit_summary(
                confirmed_count=0,
                skipped_count=0,
                remaining_count=10,
                space_saved=0,
                log_path='/logs/audit.log'
            )

        output = captured.getvalue()
        self.assertNotIn('Freed', output)
        self.assertIn('10 remaining', output)

    def test_json_format_quit_summary_structure(self):
        """Verify JSON quit status structure."""
        formatter = JsonActionFormatter(
            verbose=False,
            preview_mode=False,
            action='symlink'
        )

        formatter.format_quit_summary(
            confirmed_count=3,
            skipped_count=1,
            remaining_count=6,
            space_saved=5000,
            log_path='/logs/audit.log'
        )

        self.assertIn('quit', formatter._data)
        quit_data = formatter._data['quit']
        self.assertEqual(quit_data['processedCount'], 3)
        self.assertEqual(quit_data['skippedCount'], 1)
        self.assertEqual(quit_data['remainingCount'], 6)
        self.assertEqual(quit_data['spaceSavedBytes'], 5000)
        self.assertEqual(quit_data['logPath'], '/logs/audit.log')


class TestExecutionSummaryEnhanced(unittest.TestCase):
    """Tests for enhanced format_execution_summary() with user decision counts."""

    def test_text_summary_shows_user_decisions(self):
        """Verify confirmed/skipped counts in output."""
        formatter = TextActionFormatter(
            verbose=False,
            preview_mode=False,
            action='delete',
            color_config=ColorConfig(mode=ColorMode.NEVER)
        )

        captured = StringIO()
        with patch('sys.stdout', captured):
            formatter.format_execution_summary(
                success_count=10,
                failure_count=1,
                skipped_count=0,
                space_saved=1000000,
                log_path='/logs/audit.log',
                failed_list=[FailedOperation('/fail.txt', 'Error')],
                confirmed_count=8,
                user_skipped_count=3
            )

        output = captured.getvalue()
        self.assertIn('User confirmed: 8', output)
        self.assertIn('User skipped: 3', output)
        self.assertIn('Succeeded: 10', output)
        self.assertIn('Failed: 1', output)
        self.assertNotIn('Already linked', output)  # skipped_count=0

    def test_text_summary_shows_dual_space_format(self):
        """Verify both human-readable and bytes format for space."""
        formatter = TextActionFormatter(
            verbose=False,
            preview_mode=False,
            action='hardlink',
            color_config=ColorConfig(mode=ColorMode.NEVER)
        )

        captured = StringIO()
        with patch('sys.stdout', captured):
            formatter.format_execution_summary(
                success_count=5,
                failure_count=0,
                skipped_count=2,
                space_saved=1288490188,  # ~1.2 GB
                log_path='/logs/audit.log',
                failed_list=[],
                confirmed_count=5,
                user_skipped_count=0
            )

        output = captured.getvalue()
        # Check for both human-readable and bytes format
        self.assertIn('1.2 GB', output)
        self.assertIn('1,288,490,188 bytes', output)
        self.assertIn('Already linked: 2', output)  # skipped_count > 0

    def test_json_summary_includes_user_counts(self):
        """Verify JSON has userConfirmedCount and userSkippedCount."""
        formatter = JsonActionFormatter(
            verbose=False,
            preview_mode=False,
            action='delete'
        )

        formatter.format_execution_summary(
            success_count=7,
            failure_count=2,
            skipped_count=1,
            space_saved=50000,
            log_path='/logs/audit.log',
            failed_list=[
                FailedOperation('/a.txt', 'Error A'),
                FailedOperation('/b.txt', 'Error B')
            ],
            confirmed_count=6,
            user_skipped_count=4
        )

        self.assertIn('execution', formatter._data)
        exec_data = formatter._data['execution']
        self.assertEqual(exec_data['userConfirmedCount'], 6)
        self.assertEqual(exec_data['userSkippedCount'], 4)
        self.assertEqual(exec_data['successCount'], 7)
        self.assertEqual(exec_data['failureCount'], 2)
        self.assertEqual(exec_data['skippedCount'], 1)
        self.assertEqual(exec_data['spaceSavedBytes'], 50000)
        self.assertEqual(len(exec_data['failures']), 2)


class TestExitCodeConstants(unittest.TestCase):
    """Tests for exit code constant values."""

    def test_exit_code_values(self):
        """Verify EXIT_SUCCESS=0, EXIT_PARTIAL=2, EXIT_USER_QUIT=130."""
        self.assertEqual(EXIT_SUCCESS, 0)
        self.assertEqual(EXIT_PARTIAL, 2)
        self.assertEqual(EXIT_USER_QUIT, 130)  # 128 + SIGINT


if __name__ == '__main__':
    unittest.main()
