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


if __name__ == '__main__':
    unittest.main()
