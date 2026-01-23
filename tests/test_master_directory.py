#!/usr/bin/env python3
"""Tests for master directory output formatting (first directory is implicit master)."""

from __future__ import annotations

import io
import os
import time
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch

from file_matcher import main
from tests.test_base import BaseFileMatcherTest


class TestCompareMode(BaseFileMatcherTest):
    """Tests for compare mode (no --action flag)."""

    def run_main_with_args(self, args: list[str]) -> str:
        """Helper to run main() with given args and capture stdout."""
        f = io.StringIO()
        with redirect_stdout(f):
            main()
        return f.getvalue()

    def test_compare_mode_works(self):
        """Test that tool works without --action (compare mode)."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2]):
            output = self.run_main_with_args([])
            # Output uses [MASTER]/[DUPLICATE] labels
            self.assertIn("[MASTER]", output)
            self.assertIn("[DUPLICATE]", output)


class TestMasterDirectoryOutput(BaseFileMatcherTest):
    """Tests for master-aware output formatting when --action is used."""

    def run_main_with_args(self, args: list[str]) -> str:
        """Helper to run main() with given args and capture stdout."""
        f = io.StringIO()
        with redirect_stdout(f):
            main()
        return f.getvalue()

    def test_action_output_format(self):
        """Test that output uses [MASTER]/[WOULD ...] format when --action set."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--action', 'hardlink']):
            output = self.run_main_with_args([])
            # New format should have [MASTER] and [WOULD HARDLINK] prefixes
            self.assertIn("[MASTER]", output)
            self.assertIn("[WOULD HARDLINK]", output)

    def test_master_output_master_first(self):
        """Test that [MASTER] lines contain files from first directory."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--action', 'hardlink']):
            output = self.run_main_with_args([])
            # Find lines with [MASTER] - should be from test_dir1
            master_lines = [line for line in output.split('\n') if '[MASTER]' in line]
            for line in master_lines:
                # Master file should be from test_dir1
                self.assertIn('test_dir1', line)

    def test_no_action_preserves_compare_format(self):
        """Test that without --action, output uses hierarchical format."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2]):
            output = self.run_main_with_args([])
            # Compare mode uses [MASTER]/[DUPLICATE] labels like action mode
            self.assertIn("[MASTER]", output)
            self.assertIn("[DUPLICATE]", output)

    def test_action_summary_shows_counts(self):
        """Test that --summary shows master files and duplicates counts."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--action', 'hardlink', '--summary']):
            output = self.run_main_with_args([])
            self.assertIn("Master files preserved:", output)
            self.assertIn("Duplicate", output)

    def test_action_verbose_shows_details(self):
        """Test that --verbose shows duplicate count and file size."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--action', 'hardlink', '--verbose']):
            output = self.run_main_with_args([])
            # Verbose mode should show duplicate count and size in [MASTER] line
            self.assertIn("duplicates", output.lower())
            # Should still have the [MASTER] format
            self.assertIn("[MASTER]", output)


class TestMasterDirectoryTimestamp(BaseFileMatcherTest):
    """Tests for timestamp-based master selection within master directory."""

    def setUp(self):
        """Set up test environment with duplicate files having different timestamps."""
        super().setUp()
        # Create duplicate files within master directory with different timestamps
        self.dup_in_master1 = os.path.join(self.test_dir1, "dup_a.txt")
        self.dup_in_master2 = os.path.join(self.test_dir1, "dup_b.txt")

        # Write same content to both files in master directory
        content = "Duplicate content in master\n"
        with open(self.dup_in_master1, "w") as f:
            f.write(content)
        with open(self.dup_in_master2, "w") as f:
            f.write(content)

        # Set timestamps: dup_a is older, should be master
        old_time = time.time() - 3600  # 1 hour ago
        os.utime(self.dup_in_master1, (old_time, old_time))

        # Create matching file in second directory
        self.dup_in_dir2 = os.path.join(self.test_dir2, "dup_c.txt")
        with open(self.dup_in_dir2, "w") as f:
            f.write(content)

    def run_main_with_args(self, args: list[str]) -> str:
        """Helper to run main() with given args and capture stdout."""
        f = io.StringIO()
        with redirect_stdout(f):
            main()
        return f.getvalue()

    def test_oldest_file_becomes_master(self):
        """Verify oldest file in master dir is selected as master."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--action', 'hardlink']):
            output = self.run_main_with_args([])
            # The older file (dup_a.txt) should be selected as master
            # It should appear in a [MASTER] line, with dup_b.txt as [WOULD HARDLINK]
            master_lines = [line for line in output.split('\n') if '[MASTER]' in line and 'dup_' in line]
            self.assertTrue(any('dup_a.txt' in line for line in master_lines),
                            "dup_a.txt (oldest) should be selected as master")
            # dup_b.txt should be a duplicate
            dup_lines = [line for line in output.split('\n') if '[WOULD HARDLINK]' in line and 'dup_b.txt' in line]
            self.assertTrue(len(dup_lines) > 0, "dup_b.txt should appear as a duplicate")

    def test_duplicate_group_has_correct_structure(self):
        """Verify duplicate groups have [MASTER] followed by indented lines."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--action', 'hardlink']):
            output = self.run_main_with_args([])
            lines = output.split('\n')
            # Find groups - [MASTER] should be followed by indented lines
            for i, line in enumerate(lines):
                if '[MASTER]' in line:
                    # Check that next non-empty lines are indented
                    j = i + 1
                    while j < len(lines) and lines[j].strip() and '[MASTER]' not in lines[j]:
                        if lines[j].strip():
                            self.assertTrue(lines[j].startswith('    '),
                                            f"DUP lines should be indented: {lines[j]}")
                        j += 1

    def test_warning_multiple_masters(self):
        """Verify warning printed when multiple files in master have same content."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--action', 'hardlink']):
            output = self.run_main_with_args([])
            # Should have a warning about multiple files in master directory
            self.assertIn("Warning:", output)
            self.assertIn("Multiple files in master directory", output)

    def test_master_dir_file_preferred(self):
        """Verify file in master dir chosen over older file in non-master dir."""
        # Create an even older file in dir2 (non-master)
        older_file_dir2 = os.path.join(self.test_dir2, "very_old.txt")
        with open(older_file_dir2, "w") as f:
            f.write("Unique old content\n")
        # Also create matching file in dir1 (master)
        matching_file_dir1 = os.path.join(self.test_dir1, "newer_master.txt")
        with open(matching_file_dir1, "w") as f:
            f.write("Unique old content\n")

        # Make dir2 file much older
        very_old_time = time.time() - 7200  # 2 hours ago
        os.utime(older_file_dir2, (very_old_time, very_old_time))

        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--action', 'hardlink']):
            output = self.run_main_with_args([])
            # Find the [MASTER] line with newer_master.txt - it should be from test_dir1
            master_lines = [line for line in output.split('\n') if '[MASTER]' in line and 'newer_master.txt' in line]
            self.assertTrue(len(master_lines) > 0, "newer_master.txt should be a [MASTER]")
            for line in master_lines:
                # Master should be from test_dir1
                self.assertIn('test_dir1', line)
            # very_old.txt should be a [WOULD HARDLINK]
            dup_lines = [line for line in output.split('\n') if '[WOULD HARDLINK]' in line and 'very_old.txt' in line]
            self.assertTrue(len(dup_lines) > 0, "very_old.txt should appear as duplicate")


if __name__ == "__main__":
    unittest.main()
