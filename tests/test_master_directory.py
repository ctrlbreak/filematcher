#!/usr/bin/env python3
"""Tests for master directory validation and output formatting."""

from __future__ import annotations

import io
import os
import time
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch

from file_matcher import main, validate_master_directory
from tests.test_base import BaseFileMatcherTest


class TestMasterDirectoryValidation(BaseFileMatcherTest):
    """Tests for --master flag validation."""

    def run_main_with_args(self, args: list[str]) -> str:
        """Helper to run main() with given args and capture stdout."""
        f = io.StringIO()
        with redirect_stdout(f):
            main()
        return f.getvalue()

    def test_valid_master_dir1(self):
        """Test that --master with first directory passes validation."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1]):
            # Should not raise SystemExit
            output = self.run_main_with_args([])
            # Tool should run successfully (no error exit)
            self.assertNotIn("Error", output)

    def test_valid_master_dir2(self):
        """Test that --master with second directory passes validation."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir2]):
            # Should not raise SystemExit
            output = self.run_main_with_args([])
            # Tool should run successfully (no error exit)
            self.assertNotIn("Error", output)

    def test_valid_master_relative_path(self):
        """Test that --master with ./dir resolves correctly."""
        # Create a relative path to test_dir1 from temp_dir
        original_cwd = os.getcwd()
        try:
            os.chdir(self.temp_dir)
            relative_path = "./test_dir1"
            with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', relative_path]):
                output = self.run_main_with_args([])
                self.assertNotIn("Error", output)
        finally:
            os.chdir(original_cwd)

    def test_valid_master_parent_path(self):
        """Test that --master with ../parent/dir resolves correctly."""
        original_cwd = os.getcwd()
        try:
            # Change to test_dir1, then use ../test_dir2 as master
            os.chdir(self.test_dir1)
            relative_path = "../test_dir2"
            with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', relative_path]):
                output = self.run_main_with_args([])
                self.assertNotIn("Error", output)
        finally:
            os.chdir(original_cwd)

    def test_invalid_master_nonexistent(self):
        """Test that --master with non-existent path exits code 2."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', '/nonexistent/path']):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 2)

    def test_invalid_master_wrong_directory(self):
        """Test that --master with unrelated directory exits code 2."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', '/tmp']):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 2)

    def test_invalid_master_error_message(self):
        """Test that error message contains expected text."""
        stderr_capture = io.StringIO()
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', '/tmp']):
            with redirect_stderr(stderr_capture):
                with self.assertRaises(SystemExit):
                    main()
        error_output = stderr_capture.getvalue()
        self.assertIn("Master must be one of the compared directories", error_output)

    def test_no_master_flag(self):
        """Test that tool works without --master (backward compatibility)."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2]):
            output = self.run_main_with_args([])
            # Original output format should have "Hash:" prefix
            self.assertIn("Hash:", output)


class TestMasterDirectoryOutput(BaseFileMatcherTest):
    """Tests for master-aware output formatting."""

    def run_main_with_args(self, args: list[str]) -> str:
        """Helper to run main() with given args and capture stdout."""
        f = io.StringIO()
        with redirect_stdout(f):
            main()
        return f.getvalue()

    def test_master_output_arrow_notation(self):
        """Test that output contains -> when --master set."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1]):
            output = self.run_main_with_args([])
            # Arrow notation should appear in output when there are duplicates
            self.assertIn("->", output)

    def test_master_output_master_first(self):
        """Test that master file appears before arrow."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1]):
            output = self.run_main_with_args([])
            # Find lines with arrows - master should be in test_dir1
            lines_with_arrow = [line for line in output.split('\n') if '->' in line]
            for line in lines_with_arrow:
                # Master file (before ->) should be from test_dir1
                master_part = line.split('->')[0].strip()
                self.assertIn('test_dir1', master_part)

    def test_no_master_preserves_old_format(self):
        """Test that without --master, output has Hash: format."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2]):
            output = self.run_main_with_args([])
            self.assertIn("Hash:", output)

    def test_master_summary_shows_counts(self):
        """Test that --summary shows master files and duplicates counts."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1, '--summary']):
            output = self.run_main_with_args([])
            self.assertIn("Master files:", output)
            self.assertIn("Duplicates:", output)

    def test_master_verbose_shows_reasoning(self):
        """Test that --verbose shows Selected master: text."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1, '--verbose']):
            output = self.run_main_with_args([])
            self.assertIn("Selected master:", output)


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
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1, '--verbose']):
            output = self.run_main_with_args([])
            # The older file (dup_a.txt) should be selected as master
            # Look for the line that shows master selection for our duplicate content
            lines = output.split('\n')
            for line in lines:
                if 'dup_a.txt' in line and 'Selected master:' in line:
                    self.assertIn('oldest', line.lower())
                    break

    def test_timestamp_selection_in_verbose(self):
        """Verify verbose output explains timestamp selection."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1, '--verbose']):
            output = self.run_main_with_args([])
            # Should mention "oldest" in the selection reasoning
            self.assertIn("oldest", output.lower())

    def test_warning_multiple_masters(self):
        """Verify warning printed when multiple files in master have same content."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1]):
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

        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--master', self.test_dir1]):
            output = self.run_main_with_args([])
            # Find the line with the newer_master.txt or very_old.txt duplicate pair
            lines_with_arrow = [line for line in output.split('\n') if '->' in line and ('newer_master.txt' in line or 'very_old.txt' in line)]
            # The file from master dir (test_dir1) should be the master, appearing before ->
            for line in lines_with_arrow:
                if 'newer_master.txt' in line or 'very_old.txt' in line:
                    master_part = line.split('->')[0]
                    # Master should be from test_dir1
                    self.assertIn('test_dir1', master_part)


if __name__ == "__main__":
    unittest.main()
