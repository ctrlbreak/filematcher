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

    def test_color_flag_long_form(self):
        """--color flag should work."""
        result = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2, "--color"],
            capture_output=True,
            text=True
        )
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


if __name__ == "__main__":
    unittest.main()
