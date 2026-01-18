#!/usr/bin/env python3

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from file_matcher import main
from tests.test_base import BaseFileMatcherTest


class TestCLI(BaseFileMatcherTest):
    """Tests for command-line interface and output formatting."""

    def run_main_with_args(self, args: list[str]) -> str:
        """Helper to run main() with given args and capture stdout."""
        f = io.StringIO()
        with redirect_stdout(f):
            main()
        return f.getvalue()

    def test_summary_mode(self):
        """Test summary mode output with matched and unmatched files."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--summary', '--show-unmatched']):
            output = self.run_main_with_args([])

            # Check summary output format
            self.assertIn("Matched files summary:", output)
            self.assertIn("Unique content hashes with matches:", output)
            self.assertIn("Files in", output)

            # Check that it includes unmatched summary
            self.assertIn("Unmatched files summary:", output)

            # Actual numbers should be in the output
            self.assertIn("with matches in", output)
            self.assertIn("with no match:", output)

            # The output should not contain detailed file listings
            self.assertNotIn("Hash:", output)
            self.assertNotIn("file1.txt", output)
            self.assertNotIn("file2.txt", output)

        # Test summary mode without unmatched files
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--summary']):
            output = self.run_main_with_args([])

            # Should have matched summary but not unmatched summary
            self.assertIn("Matched files summary:", output)
            self.assertNotIn("Unmatched files summary:", output)

    def test_detailed_output_mode(self):
        """Test detailed output format (default mode)."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2]):
            output = self.run_main_with_args([])

            # Check that the output includes hash details and file listings
            self.assertIn("Hash:", output)
            self.assertIn("Files in", output)

        # Test with unmatched files option
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--show-unmatched']):
            output = self.run_main_with_args([])

            # Check for unmatched files section
            self.assertIn("Files with no content matches", output)
            self.assertIn("Unique files in", output)

    def test_hash_algorithm_option(self):
        """Test the hash algorithm command-line option."""
        # Test with MD5 (default)
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2]):
            output = self.run_main_with_args([])
            self.assertIn("Using MD5 hashing algorithm", output)

        # Test with SHA256
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--hash', 'sha256']):
            output = self.run_main_with_args([])
            self.assertIn("Using SHA256 hashing algorithm", output)

    def test_fast_mode_option(self):
        """Test the fast mode command-line option."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--fast']):
            output = self.run_main_with_args([])
            self.assertIn("Fast mode enabled", output)

    def test_verbose_mode_option(self):
        """Test the verbose mode command-line option."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--verbose']):
            output = self.run_main_with_args([])

            # Check for verbose mode indicators
            self.assertIn("Verbose mode enabled", output)
            self.assertIn("Found", output)
            self.assertIn("files to process", output)
            self.assertIn("Processing", output)
            self.assertIn("Completed indexing", output)

            # Should show progress for each file
            self.assertIn("[1/", output)  # Progress counter
            self.assertIn("B)", output)   # File size

        # Test verbose mode with summary
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--verbose', '--summary']):
            output = self.run_main_with_args([])

            # Should still show verbose progress with summary output
            self.assertIn("Verbose mode enabled", output)
            self.assertIn("Processing", output)
            self.assertIn("Matched files summary:", output)


if __name__ == "__main__":
    unittest.main()
