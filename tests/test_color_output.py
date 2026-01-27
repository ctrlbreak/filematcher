#!/usr/bin/env python3
"""Tests for Phase 8: Color Enhancement features.

Tests cover:
- --color flag (force color on)
- --no-color flag (force color off)
- NO_COLOR environment variable
- FORCE_COLOR environment variable
- JSON output never colored
- Text content identical with/without color
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

# Regex to match ANSI escape codes
ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*m')


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    return ANSI_ESCAPE.sub('', text)


class TestColorFlag(unittest.TestCase):
    """Tests for --color flag."""

    def setUp(self):
        """Set up test directories."""
        self.test_dir1 = str(Path(__file__).parent.parent / "test_dir1")
        self.test_dir2 = str(Path(__file__).parent.parent / "test_dir2")

    def test_color_flag_forces_color(self):
        """--color flag should force color output even when piped."""
        result = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2, "--color"],
            capture_output=True,
            text=True
        )
        # Should have ANSI codes in output
        self.assertIn('\033[', result.stdout)


class TestNoColorFlag(unittest.TestCase):
    """Tests for --no-color flag."""

    def setUp(self):
        """Set up test directories."""
        self.test_dir1 = str(Path(__file__).parent.parent / "test_dir1")
        self.test_dir2 = str(Path(__file__).parent.parent / "test_dir2")

    def test_no_color_flag_disables_color(self):
        """--no-color flag should disable color output."""
        result = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2, "--no-color"],
            capture_output=True,
            text=True
        )
        # Should NOT have ANSI codes in output
        self.assertNotIn('\033[', result.stdout)
        self.assertNotIn('\033[', result.stderr)

    def test_no_color_overrides_color_when_last(self):
        """--no-color should win when specified after --color (last wins)."""
        result = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2,
             "--color", "--no-color"],
            capture_output=True,
            text=True
        )
        self.assertNotIn('\033[', result.stdout)

    def test_color_overrides_no_color_when_last(self):
        """--color should win when specified after --no-color (last wins)."""
        result = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2,
             "--no-color", "--color"],
            capture_output=True,
            text=True
        )
        self.assertIn('\033[', result.stdout)


class TestNoColorEnvironment(unittest.TestCase):
    """Tests for NO_COLOR environment variable."""

    def setUp(self):
        """Set up test directories."""
        self.test_dir1 = str(Path(__file__).parent.parent / "test_dir1")
        self.test_dir2 = str(Path(__file__).parent.parent / "test_dir2")

    def test_no_color_env_disables_color(self):
        """NO_COLOR environment variable should disable color."""
        env = os.environ.copy()
        env['NO_COLOR'] = '1'
        result = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2],
            capture_output=True,
            text=True,
            env=env
        )
        self.assertNotIn('\033[', result.stdout)

    def test_color_flag_overrides_no_color_env(self):
        """--color flag should override NO_COLOR environment variable."""
        env = os.environ.copy()
        env['NO_COLOR'] = '1'
        result = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2, "--color"],
            capture_output=True,
            text=True,
            env=env
        )
        # --color should win over NO_COLOR env
        self.assertIn('\033[', result.stdout)


class TestForceColorEnvironment(unittest.TestCase):
    """Tests for FORCE_COLOR environment variable."""

    def setUp(self):
        """Set up test directories."""
        self.test_dir1 = str(Path(__file__).parent.parent / "test_dir1")
        self.test_dir2 = str(Path(__file__).parent.parent / "test_dir2")

    def test_force_color_env_enables_color(self):
        """FORCE_COLOR environment variable should enable color in pipes."""
        env = os.environ.copy()
        env['FORCE_COLOR'] = '1'
        # Remove NO_COLOR if present
        env.pop('NO_COLOR', None)
        result = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2],
            capture_output=True,
            text=True,
            env=env
        )
        self.assertIn('\033[', result.stdout)

    def test_no_color_env_takes_precedence_over_force_color(self):
        """NO_COLOR should take precedence over FORCE_COLOR."""
        env = os.environ.copy()
        env['NO_COLOR'] = '1'
        env['FORCE_COLOR'] = '1'
        result = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2],
            capture_output=True,
            text=True,
            env=env
        )
        self.assertNotIn('\033[', result.stdout)


class TestJsonNeverColored(unittest.TestCase):
    """Tests that JSON output is never colored."""

    def setUp(self):
        """Set up test directories."""
        self.test_dir1 = str(Path(__file__).parent.parent / "test_dir1")
        self.test_dir2 = str(Path(__file__).parent.parent / "test_dir2")

    def test_json_no_color(self):
        """JSON output should never have ANSI codes."""
        result = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2, "--json"],
            capture_output=True,
            text=True
        )
        self.assertNotIn('\033[', result.stdout)

    def test_json_with_color_flag_still_no_color(self):
        """--json --color should still produce JSON without ANSI codes."""
        result = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2,
             "--json", "--color"],
            capture_output=True,
            text=True
        )
        self.assertNotIn('\033[', result.stdout)

    def test_json_with_force_color_env_still_no_color(self):
        """--json with FORCE_COLOR should still produce JSON without ANSI codes."""
        env = os.environ.copy()
        env['FORCE_COLOR'] = '1'
        result = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2, "--json"],
            capture_output=True,
            text=True,
            env=env
        )
        self.assertNotIn('\033[', result.stdout)


class TestContentIdentical(unittest.TestCase):
    """Tests that text content is identical with and without color."""

    def setUp(self):
        """Set up test directories."""
        self.test_dir1 = str(Path(__file__).parent.parent / "test_dir1")
        self.test_dir2 = str(Path(__file__).parent.parent / "test_dir2")

    def test_compare_mode_content_identical(self):
        """Compare mode: content should be identical with/without color."""
        # Get colored output
        colored = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2, "--color"],
            capture_output=True,
            text=True
        )
        # Get plain output
        plain = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2, "--no-color"],
            capture_output=True,
            text=True
        )
        # Strip ANSI and compare
        self.assertEqual(strip_ansi(colored.stdout), plain.stdout)

    def test_action_mode_content_identical(self):
        """Action mode: content should be identical with/without color."""
        # Get colored output
        colored = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2,
             "--action", "hardlink", "--color"],
            capture_output=True,
            text=True
        )
        # Get plain output
        plain = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2,
             "--action", "hardlink", "--no-color"],
            capture_output=True,
            text=True
        )
        # Strip ANSI and compare
        self.assertEqual(strip_ansi(colored.stdout), plain.stdout)


class TestAutoModeNoColorInPipes(unittest.TestCase):
    """Tests that auto mode disables color when piped (no TTY)."""

    def setUp(self):
        """Set up test directories."""
        self.test_dir1 = str(Path(__file__).parent.parent / "test_dir1")
        self.test_dir2 = str(Path(__file__).parent.parent / "test_dir2")

    def test_auto_mode_no_color_when_piped(self):
        """Auto mode (default) should not use color when stdout is piped."""
        # subprocess.run with capture_output=True means stdout is not a TTY
        # So auto mode should disable color
        env = os.environ.copy()
        # Remove any color-forcing env vars
        env.pop('NO_COLOR', None)
        env.pop('FORCE_COLOR', None)
        result = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2],
            capture_output=True,
            text=True,
            env=env
        )
        # Should NOT have color (piped, not TTY)
        self.assertNotIn('\033[', result.stdout)


class TestTerminalRowCalculation(unittest.TestCase):
    """Tests for terminal row calculation helpers.

    These functions are used by inline TTY progress to correctly calculate
    how many terminal rows to clear when updating output in place.
    """

    def test_strip_ansi_plain_text(self):
        """strip_ansi returns plain text unchanged."""
        from file_matcher import strip_ansi
        self.assertEqual(strip_ansi('hello world'), 'hello world')

    def test_strip_ansi_removes_color_codes(self):
        """strip_ansi removes ANSI color escape sequences."""
        from file_matcher import strip_ansi, GREEN, RESET, BOLD_GREEN
        self.assertEqual(strip_ansi(f'{GREEN}hello{RESET}'), 'hello')
        self.assertEqual(strip_ansi(f'{BOLD_GREEN}label:{RESET}path'), 'label:path')

    def test_visible_len_plain_text(self):
        """visible_len returns correct length for plain text."""
        from file_matcher import visible_len
        self.assertEqual(visible_len('hello'), 5)
        self.assertEqual(visible_len('hello world'), 11)

    def test_visible_len_with_ansi(self):
        """visible_len excludes ANSI codes from length."""
        from file_matcher import visible_len, GREEN, RESET, BOLD_GREEN, YELLOW
        # 5 visible chars, ANSI codes add length but not visibility
        colored = f'{GREEN}hello{RESET}'
        self.assertEqual(visible_len(colored), 5)
        # Multiple color codes
        multi = f'{BOLD_GREEN}label:{RESET}{YELLOW}path{RESET}'
        self.assertEqual(visible_len(multi), len('label:path'))

    def test_terminal_rows_short_line(self):
        """Short lines take 1 row."""
        from file_matcher import terminal_rows_for_line
        self.assertEqual(terminal_rows_for_line('hello', 80), 1)
        self.assertEqual(terminal_rows_for_line('x' * 40, 80), 1)

    def test_terminal_rows_exact_width(self):
        """Line exactly terminal width takes 1 row."""
        from file_matcher import terminal_rows_for_line
        self.assertEqual(terminal_rows_for_line('x' * 80, 80), 1)

    def test_terminal_rows_wrapping(self):
        """Lines longer than terminal width wrap to multiple rows."""
        from file_matcher import terminal_rows_for_line
        # 81 chars on 80-col terminal = 2 rows
        self.assertEqual(terminal_rows_for_line('x' * 81, 80), 2)
        # 160 chars = exactly 2 rows
        self.assertEqual(terminal_rows_for_line('x' * 160, 80), 2)
        # 161 chars = 3 rows
        self.assertEqual(terminal_rows_for_line('x' * 161, 80), 3)

    def test_terminal_rows_excludes_ansi_codes(self):
        """ANSI codes should not affect row calculation."""
        from file_matcher import terminal_rows_for_line, GREEN, RESET
        # 100 visible chars = 2 rows on 80-col terminal
        plain_path = 'x' * 100
        colored_path = f'{GREEN}{plain_path}{RESET}'

        # Both should calculate to 2 rows
        self.assertEqual(terminal_rows_for_line(plain_path, 80), 2)
        self.assertEqual(terminal_rows_for_line(colored_path, 80), 2)

    def test_terminal_rows_edge_cases(self):
        """Edge cases: empty string, zero/negative width."""
        from file_matcher import terminal_rows_for_line
        # Empty string still takes 1 row (newline)
        self.assertEqual(terminal_rows_for_line('', 80), 1)
        # Zero or negative width defaults to 1 row
        self.assertEqual(terminal_rows_for_line('hello', 0), 1)
        self.assertEqual(terminal_rows_for_line('hello', -1), 1)


if __name__ == "__main__":
    unittest.main()
