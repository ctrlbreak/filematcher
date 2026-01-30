"""Tests for interactive confirmation loop functions."""

from __future__ import annotations

import unittest
from unittest.mock import patch, MagicMock
import io
import sys
import os
import tempfile

from filematcher.cli import (
    _normalize_response,
    prompt_for_group,
    interactive_execute,
)
from filematcher.types import Action, DuplicateGroup
from filematcher.formatters import TextActionFormatter
from filematcher.colors import ColorConfig, ColorMode


class TestNormalizeResponse(unittest.TestCase):
    """Tests for _normalize_response() helper."""

    def test_yes_responses(self):
        """Test all 'yes' variants normalize to 'y'."""
        for response in ['y', 'Y', 'yes', 'YES', 'Yes', 'yEs']:
            with self.subTest(response=response):
                self.assertEqual(_normalize_response(response), 'y')

    def test_no_responses(self):
        """Test all 'no' variants normalize to 'n'."""
        for response in ['n', 'N', 'no', 'NO', 'No', 'nO']:
            with self.subTest(response=response):
                self.assertEqual(_normalize_response(response), 'n')

    def test_all_responses(self):
        """Test all 'all' variants normalize to 'a'."""
        for response in ['a', 'A', 'all', 'ALL', 'All', 'aLl']:
            with self.subTest(response=response):
                self.assertEqual(_normalize_response(response), 'a')

    def test_quit_responses(self):
        """Test all 'quit' variants normalize to 'q'."""
        for response in ['q', 'Q', 'quit', 'QUIT', 'Quit', 'qUiT']:
            with self.subTest(response=response):
                self.assertEqual(_normalize_response(response), 'q')

    def test_invalid_responses(self):
        """Test invalid responses return None."""
        for response in ['', ' ', 'x', 'maybe', 'yy', 'nn', 'help', '1', 'true']:
            with self.subTest(response=response):
                self.assertIsNone(_normalize_response(response))

    def test_whitespace_handling(self):
        """Test that casefold handles input correctly."""
        # Note: prompt_for_group strips whitespace, but _normalize_response doesn't
        # So 'y ' with trailing space would fail
        self.assertIsNone(_normalize_response('y '))
        self.assertIsNone(_normalize_response(' y'))


class TestPromptForGroup(unittest.TestCase):
    """Tests for prompt_for_group() function."""

    def setUp(self):
        """Create formatter for tests."""
        self.formatter = TextActionFormatter(
            verbose=False,
            preview_mode=False,
            action='hardlink',
            color_config=ColorConfig(mode=ColorMode.NEVER)
        )

    def test_valid_response_returns_immediately(self):
        """Valid first response returns without re-prompting."""
        with patch('builtins.input', return_value='y'):
            result = prompt_for_group(self.formatter, 1, 5, 'hardlink')
            self.assertEqual(result, 'y')

    def test_invalid_then_valid_reprompts(self):
        """Invalid input shows error and re-prompts."""
        responses = iter(['invalid', 'y'])
        captured_output = io.StringIO()

        with patch('builtins.input', side_effect=lambda _: next(responses)):
            with patch('sys.stdout', captured_output):
                result = prompt_for_group(self.formatter, 1, 5, 'hardlink')

        self.assertEqual(result, 'y')
        self.assertIn('Invalid response', captured_output.getvalue())

    def test_multiple_invalid_then_valid(self):
        """Multiple invalid inputs re-prompt until valid."""
        responses = iter(['', 'maybe', 'help', 'n'])
        captured_output = io.StringIO()

        with patch('builtins.input', side_effect=lambda _: next(responses)):
            with patch('sys.stdout', captured_output):
                result = prompt_for_group(self.formatter, 2, 10, 'delete')

        self.assertEqual(result, 'n')
        # Should have printed error 3 times
        self.assertEqual(captured_output.getvalue().count('Invalid response'), 3)

    def test_keyboard_interrupt_propagates(self):
        """KeyboardInterrupt propagates to caller."""
        with patch('builtins.input', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                prompt_for_group(self.formatter, 1, 5, 'hardlink')

    def test_eof_error_propagates(self):
        """EOFError propagates to caller."""
        with patch('builtins.input', side_effect=EOFError):
            with self.assertRaises(EOFError):
                prompt_for_group(self.formatter, 1, 5, 'hardlink')

    def test_whitespace_stripped(self):
        """Leading/trailing whitespace is stripped before validation."""
        with patch('builtins.input', return_value='  yes  '):
            result = prompt_for_group(self.formatter, 1, 5, 'symlink')
            self.assertEqual(result, 'y')


class TestInteractiveExecute(unittest.TestCase):
    """Tests for interactive_execute() main loop."""

    def setUp(self):
        """Create test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.formatter = TextActionFormatter(
            verbose=False,
            preview_mode=False,
            action='delete',
            color_config=ColorConfig(mode=ColorMode.NEVER)
        )

        # Create test files with known content/size
        self.master1 = os.path.join(self.test_dir, 'master1.txt')
        self.dup1 = os.path.join(self.test_dir, 'dup1.txt')
        self.master2 = os.path.join(self.test_dir, 'master2.txt')
        self.dup2 = os.path.join(self.test_dir, 'dup2.txt')

        for f in [self.master1, self.dup1, self.master2, self.dup2]:
            with open(f, 'w') as fp:
                fp.write('test content')  # 12 bytes each

        # Create DuplicateGroup tuples
        self.groups = [
            DuplicateGroup(self.master1, [self.dup1], 'test', 'hash1'),
            DuplicateGroup(self.master2, [self.dup2], 'test', 'hash2'),
        ]

    def tearDown(self):
        """Clean up test directory."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_yes_executes_group(self):
        """'y' response executes the action on that group."""
        responses = iter(['y', 'n'])  # Confirm first, skip second

        with patch('builtins.input', side_effect=lambda _: next(responses)):
            result = interactive_execute(
                groups=self.groups,
                action=Action.DELETE,
                formatter=self.formatter
            )

        success, failure, skipped, space, failed, confirmed, user_skipped, remaining, user_quit = result
        self.assertEqual(confirmed, 1)
        self.assertEqual(user_skipped, 1)
        self.assertEqual(success, 1)  # One file successfully deleted
        self.assertGreater(space, 0)  # space_saved should be > 0
        self.assertFalse(user_quit)
        # First duplicate should be deleted
        self.assertFalse(os.path.exists(self.dup1))
        # Second duplicate should still exist
        self.assertTrue(os.path.exists(self.dup2))

    def test_no_skips_group(self):
        """'n' response skips the group without execution."""
        responses = iter(['n', 'n'])

        with patch('builtins.input', side_effect=lambda _: next(responses)):
            result = interactive_execute(
                groups=self.groups,
                action=Action.DELETE,
                formatter=self.formatter
            )

        success, failure, skipped, space, failed, confirmed, user_skipped, remaining, user_quit = result
        self.assertEqual(confirmed, 0)
        self.assertEqual(user_skipped, 2)
        self.assertEqual(success, 0)
        self.assertEqual(space, 0)  # No space saved
        self.assertFalse(user_quit)
        # Both duplicates should still exist
        self.assertTrue(os.path.exists(self.dup1))
        self.assertTrue(os.path.exists(self.dup2))

    def test_all_confirms_remaining(self):
        """'a' response confirms current and all remaining groups."""
        with patch('builtins.input', return_value='a'):
            result = interactive_execute(
                groups=self.groups,
                action=Action.DELETE,
                formatter=self.formatter
            )

        success, failure, skipped, space, failed, confirmed, user_skipped, remaining, user_quit = result
        self.assertEqual(confirmed, 2)
        self.assertEqual(user_skipped, 0)
        self.assertEqual(success, 2)  # Both files deleted
        self.assertGreater(space, 0)  # space_saved should be > 0
        self.assertFalse(user_quit)
        # Both duplicates should be deleted
        self.assertFalse(os.path.exists(self.dup1))
        self.assertFalse(os.path.exists(self.dup2))

    def test_quit_stops_immediately(self):
        """'q' response stops processing without executing remaining."""
        with patch('builtins.input', return_value='q'):
            result = interactive_execute(
                groups=self.groups,
                action=Action.DELETE,
                formatter=self.formatter
            )

        success, failure, skipped, space, failed, confirmed, user_skipped, remaining, user_quit = result
        self.assertEqual(confirmed, 0)
        self.assertEqual(user_skipped, 0)  # Quit is not "skipped"
        self.assertEqual(success, 0)
        self.assertTrue(user_quit)  # User quit via 'q'
        self.assertEqual(remaining, 1)  # 1 remaining group (quit on first)
        # Both duplicates should still exist
        self.assertTrue(os.path.exists(self.dup1))
        self.assertTrue(os.path.exists(self.dup2))

    def test_keyboard_interrupt_handled(self):
        """Ctrl+C stops loop gracefully."""
        with patch('builtins.input', side_effect=KeyboardInterrupt):
            # Should not raise, should return partial results
            result = interactive_execute(
                groups=self.groups,
                action=Action.DELETE,
                formatter=self.formatter
            )

        success, failure, skipped, space, failed, confirmed, user_skipped, remaining, user_quit = result
        # Should return zeros (no groups processed)
        self.assertEqual(confirmed, 0)
        self.assertTrue(user_quit)  # User quit via Ctrl+C

    def test_mixed_responses(self):
        """Test y, n, y sequence."""
        # Create 3 groups
        master3 = os.path.join(self.test_dir, 'master3.txt')
        dup3 = os.path.join(self.test_dir, 'dup3.txt')
        with open(master3, 'w') as f:
            f.write('content')
        with open(dup3, 'w') as f:
            f.write('content')

        groups = self.groups + [DuplicateGroup(master3, [dup3], 'test', 'hash3')]
        responses = iter(['y', 'n', 'y'])

        with patch('builtins.input', side_effect=lambda _: next(responses)):
            result = interactive_execute(
                groups=groups,
                action=Action.DELETE,
                formatter=self.formatter
            )

        success, failure, skipped, space, failed, confirmed, user_skipped, remaining, user_quit = result
        self.assertEqual(confirmed, 2)
        self.assertEqual(user_skipped, 1)
        self.assertEqual(success, 2)  # Two files deleted
        self.assertFalse(user_quit)
        self.assertFalse(os.path.exists(self.dup1))  # y - deleted
        self.assertTrue(os.path.exists(self.dup2))   # n - kept
        self.assertFalse(os.path.exists(dup3))       # y - deleted

    def test_empty_groups_returns_zeros(self):
        """Empty groups list returns all zeros."""
        result = interactive_execute(
            groups=[],
            action=Action.DELETE,
            formatter=self.formatter
        )

        success, failure, skipped, space, failed, confirmed, user_skipped, remaining, user_quit = result
        self.assertEqual(confirmed, 0)
        self.assertEqual(user_skipped, 0)
        self.assertEqual(success, 0)
        self.assertEqual(space, 0)
        self.assertFalse(user_quit)

    def test_space_saved_tracked_correctly(self):
        """Verify space_saved tracks file sizes for successful operations."""
        # Create files with known sizes
        large_dup = os.path.join(self.test_dir, 'large_dup.txt')
        with open(large_dup, 'w') as f:
            f.write('x' * 1000)  # 1000 bytes

        groups = [DuplicateGroup(self.master1, [large_dup], 'test', 'hash_large')]

        with patch('builtins.input', return_value='y'):
            result = interactive_execute(
                groups=groups,
                action=Action.DELETE,
                formatter=self.formatter
            )

        success, failure, skipped, space, failed, confirmed, user_skipped, remaining, user_quit = result
        self.assertEqual(success, 1)
        self.assertEqual(space, 1000)  # Exactly 1000 bytes saved
        self.assertFalse(user_quit)


if __name__ == '__main__':
    unittest.main()
