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


if __name__ == '__main__':
    unittest.main()
