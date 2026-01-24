#!/usr/bin/env python3
"""Tests for Phase 7: Output Unification features.

Tests cover:
- Stream separation (logger to stderr, data to stdout)
- --quiet flag behavior
- Unified header format
- Statistics footer in compare mode
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


class TestStreamSeparation(unittest.TestCase):
    """Tests for stdout/stderr stream separation."""

    def setUp(self):
        """Set up test directories."""
        self.test_dir1 = str(Path(__file__).parent.parent / "test_dir1")
        self.test_dir2 = str(Path(__file__).parent.parent / "test_dir2")

    def test_logger_messages_go_to_stderr(self):
        """Verify logger messages (Using MD5...) go to stderr, not stdout."""
        result = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2],
            capture_output=True,
            text=True
        )
        # Logger messages should be on stderr
        self.assertIn("Using MD5", result.stderr)
        # Data should be on stdout (MASTER/DUPLICATE labels, Hash only in verbose)
        self.assertIn("MASTER:", result.stdout)
        self.assertIn("DUPLICATE:", result.stdout)
        # Logger messages should NOT be on stdout
        self.assertNotIn("Using MD5", result.stdout)

    def test_indexing_messages_go_to_stderr(self):
        """Verify Indexing directory messages go to stderr."""
        result = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2],
            capture_output=True,
            text=True
        )
        # Indexing messages should be on stderr
        self.assertIn("Indexing directory:", result.stderr)
        # Should NOT be on stdout
        self.assertNotIn("Indexing directory:", result.stdout)

    def test_stderr_with_verbose_mode(self):
        """Verify verbose progress goes to stderr."""
        result = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2, "--verbose"],
            capture_output=True,
            text=True
        )
        # Verbose progress should be on stderr (file processing messages)
        # In verbose mode, shows "[N/M] Processing file..." messages
        self.assertIn("Processing", result.stderr)
        self.assertIn("Verbose mode enabled", result.stderr)

    def test_errors_go_to_stderr(self):
        """Verify error messages go to stderr."""
        result = subprocess.run(
            [sys.executable, "file_matcher.py", "nonexistent", "alsonothere"],
            capture_output=True,
            text=True
        )
        self.assertIn("Error", result.stderr)
        self.assertEqual(result.returncode, 1)

    def test_data_output_on_stdout(self):
        """Verify data (file groups, statistics) go to stdout."""
        result = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2],
            capture_output=True,
            text=True
        )
        # Data should be on stdout (MASTER/DUPLICATE labels)
        self.assertIn("MASTER:", result.stdout)
        self.assertIn("DUPLICATE:", result.stdout)
        self.assertIn("--- Statistics ---", result.stdout)
        self.assertIn("Duplicate groups:", result.stdout)


class TestQuietFlag(unittest.TestCase):
    """Tests for --quiet/-q flag."""

    def setUp(self):
        """Set up test directories."""
        self.test_dir1 = str(Path(__file__).parent.parent / "test_dir1")
        self.test_dir2 = str(Path(__file__).parent.parent / "test_dir2")

    def test_quiet_suppresses_progress(self):
        """--quiet should suppress progress messages."""
        result = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2, "--quiet"],
            capture_output=True,
            text=True
        )
        # Should not have logger messages
        self.assertNotIn("Using MD5", result.stderr)
        self.assertNotIn("Indexing", result.stderr)
        # Should still have data (MASTER/DUPLICATE labels)
        self.assertIn("MASTER:", result.stdout)

    def test_quiet_short_flag(self):
        """-q should work same as --quiet."""
        result = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2, "-q"],
            capture_output=True,
            text=True
        )
        self.assertNotIn("Using MD5", result.stderr)

    def test_quiet_still_shows_data(self):
        """--quiet should not suppress data output."""
        result = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2, "--quiet"],
            capture_output=True,
            text=True
        )
        # Data output should still appear (MASTER/DUPLICATE labels)
        self.assertIn("MASTER:", result.stdout)
        self.assertIn("--- Statistics ---", result.stdout)

    def test_quiet_still_shows_errors(self):
        """--quiet should not suppress error messages."""
        result = subprocess.run(
            [sys.executable, "file_matcher.py", "nonexistent", "alsonothere", "--quiet"],
            capture_output=True,
            text=True
        )
        # Errors should still appear
        self.assertIn("Error", result.stderr)

    def test_quiet_with_action_mode(self):
        """--quiet should work in action mode."""
        result = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2,
             "--action", "hardlink", "--quiet"],
            capture_output=True,
            text=True
        )
        self.assertNotIn("Using MD5", result.stderr)
        # Should still show action preview data
        self.assertIn("MASTER", result.stdout)

    def test_quiet_suppresses_header(self):
        """--quiet should suppress unified header."""
        result = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2, "--quiet"],
            capture_output=True,
            text=True
        )
        # Header should not appear
        self.assertNotIn("Compare mode:", result.stdout)

    def test_quiet_with_verbose_quiet_wins(self):
        """When both --quiet and --verbose are specified, --quiet takes precedence."""
        result = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2,
             "--quiet", "--verbose"],
            capture_output=True,
            text=True
        )
        # Quiet should suppress verbose messages
        self.assertNotIn("Using MD5", result.stderr)


class TestUnifiedHeaders(unittest.TestCase):
    """Tests for unified header format."""

    def setUp(self):
        """Set up test directories."""
        self.test_dir1 = str(Path(__file__).parent.parent / "test_dir1")
        self.test_dir2 = str(Path(__file__).parent.parent / "test_dir2")

    def test_compare_mode_header(self):
        """Compare mode should show 'Compare mode: dir1 vs dir2'."""
        result = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2],
            capture_output=True,
            text=True
        )
        self.assertIn("Compare mode:", result.stdout)
        self.assertIn("vs", result.stdout)

    def test_compare_mode_header_contains_directories(self):
        """Compare mode header should reference directory names."""
        result = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2],
            capture_output=True,
            text=True
        )
        # Should contain test_dir1 and test_dir2 references
        self.assertIn("test_dir1", result.stdout)
        self.assertIn("test_dir2", result.stdout)

    def test_action_mode_preview_header(self):
        """Action mode preview should show 'Action mode (PREVIEW): action'."""
        result = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2,
             "--action", "hardlink"],
            capture_output=True,
            text=True
        )
        self.assertIn("Action mode (PREVIEW)", result.stdout)
        self.assertIn("hardlink", result.stdout)

    def test_action_mode_symlink_header(self):
        """Action mode with symlink should show symlink in header."""
        result = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2,
             "--action", "symlink"],
            capture_output=True,
            text=True
        )
        self.assertIn("Action mode (PREVIEW)", result.stdout)
        self.assertIn("symlink", result.stdout)

    def test_action_mode_delete_header(self):
        """Action mode with delete should show delete in header."""
        result = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2,
             "--action", "delete"],
            capture_output=True,
            text=True
        )
        self.assertIn("Action mode (PREVIEW)", result.stdout)
        self.assertIn("delete", result.stdout)


class TestCompareStatisticsFooter(unittest.TestCase):
    """Tests for statistics footer in compare mode."""

    def setUp(self):
        """Set up test directories."""
        self.test_dir1 = str(Path(__file__).parent.parent / "test_dir1")
        self.test_dir2 = str(Path(__file__).parent.parent / "test_dir2")

    def test_compare_mode_shows_statistics(self):
        """Compare mode should show statistics footer."""
        result = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2],
            capture_output=True,
            text=True
        )
        self.assertIn("--- Statistics ---", result.stdout)
        self.assertIn("Duplicate groups:", result.stdout)

    def test_statistics_shows_total_files(self):
        """Statistics should show total files with matches."""
        result = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2],
            capture_output=True,
            text=True
        )
        self.assertIn("Total files with matches:", result.stdout)

    def test_statistics_after_match_groups(self):
        """Statistics should appear after match groups."""
        result = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2],
            capture_output=True,
            text=True
        )
        # Find positions
        hash_pos = result.stdout.find("Hash:")
        stats_pos = result.stdout.find("--- Statistics ---")
        # Statistics should be after hash output
        self.assertGreater(stats_pos, hash_pos)

    def test_action_mode_shows_statistics(self):
        """Action mode should also show statistics footer."""
        result = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2,
             "--action", "hardlink"],
            capture_output=True,
            text=True
        )
        self.assertIn("--- Statistics ---", result.stdout)
        self.assertIn("Duplicate groups:", result.stdout)

    def test_json_compare_includes_statistics(self):
        """JSON compare mode should include statistics object."""
        result = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2, "--json"],
            capture_output=True,
            text=True
        )
        data = json.loads(result.stdout)
        self.assertIn("statistics", data)
        self.assertIn("duplicateGroups", data["statistics"])

    def test_statistics_shows_reclaimable_message(self):
        """Compare mode statistics should mention --action for space calculations."""
        result = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2],
            capture_output=True,
            text=True
        )
        # Should indicate that --action is needed for space calculations
        self.assertIn("--action", result.stdout)


class TestStreamSeparationWithJson(unittest.TestCase):
    """Tests for stream separation when using --json flag."""

    def setUp(self):
        """Set up test directories."""
        self.test_dir1 = str(Path(__file__).parent.parent / "test_dir1")
        self.test_dir2 = str(Path(__file__).parent.parent / "test_dir2")

    def test_json_output_on_stdout_only(self):
        """JSON should be on stdout, progress on stderr."""
        result = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2, "--json"],
            capture_output=True,
            text=True
        )
        # stdout should be valid JSON
        data = json.loads(result.stdout)
        self.assertIsInstance(data, dict)

        # stderr should have progress messages
        self.assertIn("Using MD5", result.stderr)

    def test_json_with_quiet_clean_stdout(self):
        """--json --quiet should have clean stdout and no stderr."""
        result = subprocess.run(
            [sys.executable, "file_matcher.py", self.test_dir1, self.test_dir2,
             "--json", "--quiet"],
            capture_output=True,
            text=True
        )
        # stdout should be valid JSON
        data = json.loads(result.stdout)
        self.assertIsInstance(data, dict)

        # stderr should be empty or minimal
        self.assertNotIn("Using MD5", result.stderr)


if __name__ == "__main__":
    unittest.main()
