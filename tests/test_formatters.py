#!/usr/bin/env python3
"""Tests for formatters module interactive prompt methods.

Tests cover:
- TextActionFormatter.format_group_prompt() - prompt string generation
- TextActionFormatter.format_confirmation_status() - checkmark/X output
- TextActionFormatter.format_remaining_count() - remaining groups message
- JsonActionFormatter no-op implementations of the above
"""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout

from filematcher.formatters import TextActionFormatter, JsonActionFormatter
from filematcher.colors import ColorConfig, ColorMode


class TestTextActionFormatterPrompts(unittest.TestCase):
    """Tests for TextActionFormatter interactive prompt methods."""

    def setUp(self):
        """Set up formatter with colors disabled for predictable output."""
        self.cc = ColorConfig(mode=ColorMode.NEVER)
        self.formatter = TextActionFormatter(
            verbose=False,
            preview_mode=False,
            action="delete",
            color_config=self.cc
        )

    def test_format_group_prompt_includes_progress(self):
        """Prompt contains [index/total] format."""
        prompt = self.formatter.format_group_prompt(3, 10, "delete")
        self.assertIn("[3/10]", prompt)

    def test_format_group_prompt_includes_verb_delete(self):
        """Prompt shows 'Delete duplicate?' for delete action."""
        prompt = self.formatter.format_group_prompt(1, 5, "delete")
        self.assertIn("Delete duplicate?", prompt)

    def test_format_group_prompt_includes_verb_hardlink(self):
        """Prompt shows 'Create hardlink?' for hardlink action."""
        prompt = self.formatter.format_group_prompt(1, 5, "hardlink")
        self.assertIn("Create hardlink?", prompt)

    def test_format_group_prompt_includes_verb_symlink(self):
        """Prompt shows 'Create symlink?' for symlink action."""
        prompt = self.formatter.format_group_prompt(1, 5, "symlink")
        self.assertIn("Create symlink?", prompt)

    def test_format_group_prompt_includes_options(self):
        """Prompt contains [y/n/a/q] options."""
        prompt = self.formatter.format_group_prompt(1, 5, "delete")
        self.assertIn("[y/n/a/q]", prompt)

    def test_format_group_prompt_returns_string(self):
        """format_group_prompt returns a string (for use with input())."""
        prompt = self.formatter.format_group_prompt(2, 8, "hardlink")
        self.assertIsInstance(prompt, str)
        # Should end with space for user input
        self.assertTrue(prompt.endswith(" "))

    def test_format_confirmation_status_confirmed(self):
        """Confirmed status outputs checkmark symbol (U+2713) with lines_back=0."""
        stdout_capture = io.StringIO()
        with redirect_stdout(stdout_capture):
            self.formatter.format_confirmation_status(confirmed=True, lines_back=0)
        output = stdout_capture.getvalue()
        # Should contain checkmark U+2713
        self.assertIn("\u2713", output)
        # Fallback mode: no ANSI cursor movement
        self.assertNotIn("\033[", output)

    def test_format_confirmation_status_skipped(self):
        """Skipped status outputs X symbol (U+2717) with lines_back=0."""
        stdout_capture = io.StringIO()
        with redirect_stdout(stdout_capture):
            self.formatter.format_confirmation_status(confirmed=False, lines_back=0)
        output = stdout_capture.getvalue()
        # Should contain X mark U+2717
        self.assertIn("\u2717", output)
        # Fallback mode: no ANSI cursor movement
        self.assertNotIn("\033[", output)

    def test_format_confirmation_status_moves_cursor_up(self):
        """With _last_duplicate_rows set, uses ANSI cursor movement."""
        # Set up formatter state (simulates calling format_duplicate_group first)
        self.formatter._last_duplicate_rows = 1  # 1 duplicate row + 1 prompt = 2 total
        stdout_capture = io.StringIO()
        with redirect_stdout(stdout_capture):
            self.formatter.format_confirmation_status(confirmed=True)
        output = stdout_capture.getvalue()
        # Should contain checkmark
        self.assertIn("\u2713", output)
        # Should contain ANSI cursor up sequence for 2 rows (1 dup + 1 prompt)
        self.assertIn("\033[2A", output)
        # Should contain ANSI cursor down sequence for 2 rows
        self.assertIn("\033[2B", output)

    def test_format_confirmation_status_cursor_movement_for_skipped(self):
        """Cursor movement works for skipped (X) status too."""
        # Set up formatter state (simulates calling format_duplicate_group first)
        self.formatter._last_duplicate_rows = 2  # 2 duplicate rows + 1 prompt = 3 total
        stdout_capture = io.StringIO()
        with redirect_stdout(stdout_capture):
            self.formatter.format_confirmation_status(confirmed=False)
        output = stdout_capture.getvalue()
        # Should contain X mark
        self.assertIn("\u2717", output)
        # Should contain ANSI cursor up sequence for 3 rows (2 dup + 1 prompt)
        self.assertIn("\033[3A", output)
        # Should contain ANSI cursor down sequence for 3 rows
        self.assertIn("\033[3B", output)

    def test_format_remaining_count_output(self):
        """Remaining count outputs 'Processing N remaining groups...' message."""
        stdout_capture = io.StringIO()
        with redirect_stdout(stdout_capture):
            self.formatter.format_remaining_count(7)
        output = stdout_capture.getvalue()
        self.assertIn("Processing 7 remaining groups...", output)


class TestJsonActionFormatterPrompts(unittest.TestCase):
    """Tests for JsonActionFormatter interactive prompt methods (no-ops)."""

    def setUp(self):
        """Set up JSON formatter."""
        self.formatter = JsonActionFormatter(
            verbose=False,
            preview_mode=False,
            action="delete"
        )

    def test_json_format_group_prompt_returns_empty(self):
        """JSON formatter returns empty string for group prompt."""
        prompt = self.formatter.format_group_prompt(1, 5, "delete")
        self.assertEqual(prompt, "")

    def test_json_format_confirmation_status_noop(self):
        """JSON formatter does nothing for confirmation status."""
        stdout_capture = io.StringIO()
        with redirect_stdout(stdout_capture):
            self.formatter.format_confirmation_status(confirmed=True, lines_back=0)
        output = stdout_capture.getvalue()
        # Should produce no output
        self.assertEqual(output, "")

    def test_json_format_confirmation_status_ignores_lines_back(self):
        """JSON formatter ignores lines_back parameter."""
        stdout_capture = io.StringIO()
        with redirect_stdout(stdout_capture):
            self.formatter.format_confirmation_status(confirmed=True, lines_back=5)
        output = stdout_capture.getvalue()
        # Should produce no output regardless of lines_back
        self.assertEqual(output, "")

    def test_json_format_remaining_count_noop(self):
        """JSON formatter does nothing for remaining count."""
        stdout_capture = io.StringIO()
        with redirect_stdout(stdout_capture):
            self.formatter.format_remaining_count(5)
        output = stdout_capture.getvalue()
        # Should produce no output
        self.assertEqual(output, "")


if __name__ == "__main__":
    unittest.main()
