#!/usr/bin/env python3
"""Tests for master directory validation and output formatting."""

from __future__ import annotations

import io
import os
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


if __name__ == "__main__":
    unittest.main()
