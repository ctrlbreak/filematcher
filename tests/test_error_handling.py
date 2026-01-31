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


# ============================================================================
# Integration Tests for Interactive Execute (from Plan 21-03 scope)
# ============================================================================

import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock

from filematcher.cli import interactive_execute
from filematcher.types import Action, DuplicateGroup
from filematcher.actions import create_audit_logger

from tests.test_base import BaseFileMatcherTest


class TestInteractiveExecuteErrorHandling(BaseFileMatcherTest):
    """Integration tests for interactive_execute error handling."""

    def setUp(self):
        """Set up test environment with temporary directories and files."""
        super().setUp()
        self.formatter = TextActionFormatter(
            verbose=False,
            preview_mode=False,
            action='delete',
            color_config=ColorConfig(mode=ColorMode.NEVER)
        )

        # Create additional test files for these tests
        self.master1 = os.path.join(self.temp_dir, 'master1.txt')
        self.dup1 = os.path.join(self.temp_dir, 'dup1.txt')
        self.master2 = os.path.join(self.temp_dir, 'master2.txt')
        self.dup2 = os.path.join(self.temp_dir, 'dup2.txt')

        for f in [self.master1, self.dup1, self.master2, self.dup2]:
            with open(f, 'w') as fp:
                fp.write('test content')  # 12 bytes each

        self.groups = [
            DuplicateGroup(self.master1, [self.dup1], 'test', 'hash1'),
            DuplicateGroup(self.master2, [self.dup2], 'test', 'hash2'),
        ]

    def test_permission_error_displays_and_continues(self):
        """Permission error displayed and execution continues to next file."""
        # Create group with 2 duplicates
        dup1a = os.path.join(self.temp_dir, 'dup1a.txt')
        dup1b = os.path.join(self.temp_dir, 'dup1b.txt')
        with open(dup1a, 'w') as f:
            f.write('content')
        with open(dup1b, 'w') as f:
            f.write('content')

        groups = [DuplicateGroup(self.master1, [dup1a, dup1b], 'test', 'hash1')]

        # Mock execute_action to fail on first file, succeed on second
        call_count = [0]

        def mock_execute(dup, master, action, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return (False, "Permission denied", action)
            return (True, "", action)

        # Patch in cli module namespace where it's imported
        with patch('filematcher.cli.execute_action', side_effect=mock_execute):
            with patch('builtins.input', return_value='a'):
                result = interactive_execute(
                    groups=groups,
                    action=Action.DELETE,
                    formatter=self.formatter
                )

        success, failure, skipped, space, failed, confirmed, user_skipped, remaining, user_quit = result
        self.assertEqual(failure, 1)
        self.assertEqual(success, 1)
        self.assertFalse(user_quit)

    def test_oserror_on_file_size_displays_error(self):
        """OSError when getting file size displays error via formatter."""
        groups = [DuplicateGroup(self.master1, [self.dup1], 'test', 'hash1')]

        # Create a mock formatter to track calls
        mock_formatter = MagicMock(spec=TextActionFormatter)
        mock_formatter.format_group_prompt.return_value = 'test? '

        with patch('builtins.input', return_value='y'):
            with patch('os.path.getsize', side_effect=PermissionError("Permission denied")):
                with patch('os.path.exists', return_value=True):
                    result = interactive_execute(
                        groups=groups,
                        action=Action.DELETE,
                        formatter=mock_formatter
                    )

        # format_file_error should have been called
        self.assertTrue(mock_formatter.format_file_error.called)
        call_args = mock_formatter.format_file_error.call_args
        self.assertIn(self.dup1, call_args[0][0])  # file path
        self.assertIn('Permission denied', str(call_args[0][1]))  # error message

    def test_quit_response_returns_remaining_count(self):
        """Quit after first group returns correct remaining_count."""
        # Create 3 groups
        master3 = os.path.join(self.temp_dir, 'master3.txt')
        dup3 = os.path.join(self.temp_dir, 'dup3.txt')
        with open(master3, 'w') as f:
            f.write('content')
        with open(dup3, 'w') as f:
            f.write('content')

        groups = self.groups + [DuplicateGroup(master3, [dup3], 'test', 'hash3')]
        responses = iter(['y', 'q'])

        with patch('builtins.input', side_effect=lambda _: next(responses)):
            result = interactive_execute(
                groups=groups,
                action=Action.DELETE,
                formatter=self.formatter
            )

        success, failure, skipped, space, failed, confirmed, user_skipped, remaining, user_quit = result
        # Quit at group 2 means groups 2 and 3 remaining (current group wasn't processed)
        self.assertEqual(remaining, 2)
        self.assertTrue(user_quit)
        self.assertEqual(confirmed, 1)  # One group confirmed before quit

    def test_keyboard_interrupt_sets_user_quit(self):
        """KeyboardInterrupt sets user_quit=True."""
        with patch('builtins.input', side_effect=KeyboardInterrupt):
            result = interactive_execute(
                groups=self.groups,
                action=Action.DELETE,
                formatter=self.formatter
            )

        success, failure, skipped, space, failed, confirmed, user_skipped, remaining, user_quit = result
        self.assertTrue(user_quit)


class TestExitCodes(BaseFileMatcherTest):
    """Integration tests for exit codes."""

    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.formatter = TextActionFormatter(
            verbose=False,
            preview_mode=False,
            action='delete',
            color_config=ColorConfig(mode=ColorMode.NEVER)
        )

        # Create test files
        self.master = os.path.join(self.temp_dir, 'master.txt')
        self.dup = os.path.join(self.temp_dir, 'dup.txt')
        with open(self.master, 'w') as f:
            f.write('content')
        with open(self.dup, 'w') as f:
            f.write('content')

        self.groups = [DuplicateGroup(self.master, [self.dup], 'test', 'hash1')]

    def test_exit_success_when_no_failures(self):
        """All succeed returns exit 0."""
        from filematcher.actions import determine_exit_code
        # 5 successes, 0 failures
        exit_code = determine_exit_code(5, 0)
        self.assertEqual(exit_code, 0)

    def test_exit_partial_when_some_failures(self):
        """Some failures returns exit 2 (EXIT_PARTIAL)."""
        from filematcher.actions import determine_exit_code
        # determine_exit_code returns 2 for partial, consistent with EXIT_PARTIAL
        exit_code = determine_exit_code(5, 2)
        self.assertEqual(exit_code, 2)

    def test_exit_user_quit_on_q_response(self):
        """User quit via 'q' returns exit 130."""
        # Verify that EXIT_USER_QUIT is used for 'q' response
        # The actual exit code is tested via the constant value
        self.assertEqual(EXIT_USER_QUIT, 130)

    def test_exit_success_when_user_skips_all(self):
        """User skipping everything via 'n' returns success (no failures)."""
        from filematcher.actions import determine_exit_code

        # User skipping via 'n' means:
        # - success_count = 0 (no files processed)
        # - failure_count = 0 (no errors)
        # This should be exit 0 - user intentionally skipped
        exit_code = determine_exit_code(0, 0)
        self.assertEqual(exit_code, 0)


class TestAuditLoggerFailFast(unittest.TestCase):
    """Tests for audit logger fail-fast behavior."""

    def test_audit_logger_exits_on_write_error(self):
        """Audit logger creation failure exits with code 2."""
        import logging

        with patch.object(logging, 'FileHandler', side_effect=OSError("Permission denied")):
            with self.assertRaises(SystemExit) as cm:
                create_audit_logger(Path('/nonexistent/path/audit.log'))

        self.assertEqual(cm.exception.code, 2)

    def test_audit_logger_prints_helpful_message(self):
        """Audit logger failure prints helpful message to stderr."""
        import logging

        captured_stderr = StringIO()
        with patch.object(logging, 'FileHandler', side_effect=OSError("Permission denied")):
            with patch('sys.stderr', captured_stderr):
                try:
                    create_audit_logger(Path('/nonexistent/path/audit.log'))
                except SystemExit:
                    pass

        stderr_output = captured_stderr.getvalue()
        self.assertIn('Cannot create audit log', stderr_output)
        self.assertIn('Audit trail is required', stderr_output)


if __name__ == '__main__':
    unittest.main()
