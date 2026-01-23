#!/usr/bin/env python3

from __future__ import annotations

import io
import os
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch

from file_matcher import main, execute_action, already_hardlinked
from tests.test_base import BaseFileMatcherTest


class TestCLI(BaseFileMatcherTest):
    """Tests for command-line interface and output formatting."""

    def run_main_with_args(self, args: list[str]) -> str:
        """Helper to run main() with given args and capture stdout."""
        f = io.StringIO()
        with redirect_stdout(f):
            main()
        return f.getvalue()

    def run_main_capture_all(self, args: list[str]) -> tuple[str, str]:
        """Helper to run main() and capture both stdout and stderr separately.

        Returns:
            Tuple of (stdout_output, stderr_output)
        """
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            main()
        return stdout_capture.getvalue(), stderr_capture.getvalue()

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
        # Logger messages go to stderr (Unix convention: status to stderr, data to stdout)
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2]):
            stdout, stderr = self.run_main_capture_all([])
            self.assertIn("Using MD5 hashing algorithm", stderr)

        # Test with SHA256
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--hash', 'sha256']):
            stdout, stderr = self.run_main_capture_all([])
            self.assertIn("Using SHA256 hashing algorithm", stderr)

    def test_fast_mode_option(self):
        """Test the fast mode command-line option."""
        # Logger messages go to stderr (Unix convention: status to stderr, data to stdout)
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--fast']):
            stdout, stderr = self.run_main_capture_all([])
            self.assertIn("Fast mode enabled", stderr)

    def test_verbose_mode_option(self):
        """Test the verbose mode command-line option."""
        # Logger messages go to stderr (Unix convention: status to stderr, data to stdout)
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--verbose']):
            stdout, stderr = self.run_main_capture_all([])

            # Check for verbose mode indicators (on stderr)
            self.assertIn("Verbose mode enabled", stderr)
            self.assertIn("Found", stderr)
            self.assertIn("files to process", stderr)
            self.assertIn("Processing", stderr)
            self.assertIn("Completed indexing", stderr)

            # Should show progress for each file (on stderr)
            self.assertIn("[1/", stderr)  # Progress counter
            self.assertIn("B)", stderr)   # File size

        # Test verbose mode with summary
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--verbose', '--summary']):
            stdout, stderr = self.run_main_capture_all([])

            # Should still show verbose progress on stderr with summary on stdout
            self.assertIn("Verbose mode enabled", stderr)
            self.assertIn("Processing", stderr)
            self.assertIn("Matched files summary:", stdout)


class TestActionExecution(BaseFileMatcherTest):
    """Integration tests for action execution CLI (TEST-05)."""

    def run_main_capture_output(self) -> tuple[str, int]:
        """Helper to run main() and capture stdout, return (output, exit_code)."""
        f = io.StringIO()
        with redirect_stdout(f):
            exit_code = main()
        return f.getvalue(), exit_code

    def test_execute_hardlink_modifies_files(self):
        """--execute with hardlink actually creates hard links."""
        # Get the paths to files with matching content
        master_file = os.path.join(self.test_dir1, "file1.txt")
        dup_file = os.path.join(self.test_dir2, "different_name.txt")

        # Verify they're not already hardlinked
        self.assertFalse(already_hardlinked(master_file, dup_file))

        with patch('sys.argv', ['filematcher', self.test_dir1, self.test_dir2,
                                '--action', 'hardlink',
                                '--execute', '--yes']):
            with patch('sys.stdin.isatty', return_value=False):
                output, exit_code = self.run_main_capture_output()

        self.assertEqual(exit_code, 0)
        # Verify files are now hardlinked (check inode numbers match)
        self.assertTrue(already_hardlinked(master_file, dup_file))

    def test_execute_symlink_creates_links(self):
        """--execute with symlink creates symbolic links."""
        # Get the paths to files with matching content
        dup_file = Path(self.test_dir2) / "different_name.txt"

        with patch('sys.argv', ['filematcher', self.test_dir1, self.test_dir2,
                                '--action', 'symlink',
                                '--execute', '--yes']):
            with patch('sys.stdin.isatty', return_value=False):
                output, exit_code = self.run_main_capture_output()

        self.assertEqual(exit_code, 0)
        # Verify symlinks created
        self.assertTrue(dup_file.is_symlink())

    def test_execute_delete_removes_duplicates(self):
        """--execute with delete removes duplicate files."""
        # Get the path to a duplicate file
        dup_file = Path(self.test_dir2) / "different_name.txt"

        # Verify file exists before deletion
        self.assertTrue(dup_file.exists())

        with patch('sys.argv', ['filematcher', self.test_dir1, self.test_dir2,
                                '--action', 'delete',
                                '--execute', '--yes']):
            with patch('sys.stdin.isatty', return_value=False):
                output, exit_code = self.run_main_capture_output()

        self.assertEqual(exit_code, 0)
        # Verify duplicates no longer exist
        self.assertFalse(dup_file.exists())

    def test_log_flag_creates_file(self):
        """--log flag creates log file at specified path."""
        log_path = Path(self.test_dir1) / "test_execution.log"
        with patch('sys.argv', ['filematcher', self.test_dir1, self.test_dir2,
                                '--action', 'hardlink',
                                '--execute', '--yes',
                                '--log', str(log_path)]):
            with patch('sys.stdin.isatty', return_value=False):
                output, exit_code = self.run_main_capture_output()

        self.assertTrue(log_path.exists())
        # Check log has expected content
        log_content = log_path.read_text()
        self.assertIn("File Matcher Execution Log", log_content)

    def test_fallback_symlink_flag_accepted(self):
        """--fallback-symlink flag is accepted with hardlink action."""
        with patch('sys.argv', ['filematcher', self.test_dir1, self.test_dir2,
                                '--action', 'hardlink',
                                '--fallback-symlink']):
            with patch('sys.stdin.isatty', return_value=False):
                output, exit_code = self.run_main_capture_output()

        # Preview mode - should succeed
        self.assertEqual(exit_code, 0)

    def test_fallback_symlink_requires_hardlink_action(self):
        """--fallback-symlink should only work with --action hardlink."""
        stderr_capture = io.StringIO()
        with patch('sys.argv', ['filematcher', self.test_dir1, self.test_dir2,
                                '--action', 'symlink',
                                '--fallback-symlink']):
            with redirect_stderr(stderr_capture):
                with self.assertRaises(SystemExit) as cm:
                    main()
            self.assertEqual(cm.exception.code, 2)
        error_output = stderr_capture.getvalue()
        self.assertIn("--fallback-symlink only applies to --action hardlink", error_output)

    def test_partial_failure_returns_exit_code_3(self):
        """Partial failures return exit code 3."""
        # Create test files where some will succeed and some will fail
        # Mock execute_action to fail for specific files
        call_count = [0]

        def mock_execute_action(duplicate, master, action, fallback_symlink=False):
            call_count[0] += 1
            # Fail every other file
            if call_count[0] % 2 == 0:
                return (False, "Mocked permission denied", action)
            return (True, "", action)

        with patch('sys.argv', ['filematcher', self.test_dir1, self.test_dir2,
                                '--action', 'hardlink',
                                '--execute', '--yes']):
            with patch('sys.stdin.isatty', return_value=False):
                with patch('file_matcher.execute_action', side_effect=mock_execute_action):
                    output, exit_code = self.run_main_capture_output()

        # Should return 3 for partial failure (some succeeded, some failed)
        # Note: If no duplicates exist, this may return 0. With our test setup:
        # - file1.txt, file3.txt match different_name.txt, also_different_name.txt
        # So we should have duplicates to process
        self.assertEqual(exit_code, 3)  # Partial failure

    def test_all_flags_together(self):
        """All flags can be combined correctly."""
        log_path = Path(self.test_dir1) / "combined.log"
        with patch('sys.argv', ['filematcher', self.test_dir1, self.test_dir2,
                                '--action', 'hardlink',
                                '--execute', '--yes',
                                '--log', str(log_path),
                                '--fallback-symlink',
                                '--verbose']):
            with patch('sys.stdin.isatty', return_value=False):
                output, exit_code = self.run_main_capture_output()

        self.assertEqual(exit_code, 0)
        self.assertTrue(log_path.exists())

    def test_execute_shows_summary(self):
        """--execute shows execution summary with counts."""
        with patch('sys.argv', ['filematcher', self.test_dir1, self.test_dir2,
                                '--action', 'hardlink',
                                '--execute', '--yes']):
            with patch('sys.stdin.isatty', return_value=False):
                output, exit_code = self.run_main_capture_output()

        # Should show execution summary
        self.assertIn("Execution complete:", output)
        self.assertIn("Successful:", output)
        self.assertIn("Failed:", output)
        self.assertIn("Skipped:", output)
        self.assertIn("Space saved:", output)
        self.assertIn("Log file:", output)

    def test_log_requires_execute(self):
        """--log requires --execute flag."""
        log_path = Path(self.test_dir1) / "test.log"
        stderr_capture = io.StringIO()
        with patch('sys.argv', ['filematcher', self.test_dir1, self.test_dir2,
                                '--action', 'hardlink',
                                '--log', str(log_path)]):
            with redirect_stderr(stderr_capture):
                with self.assertRaises(SystemExit) as cm:
                    main()
            self.assertEqual(cm.exception.code, 2)
        error_output = stderr_capture.getvalue()
        self.assertIn("--log requires --execute", error_output)


class TestFormatterEdgeCases(BaseFileMatcherTest):
    """Tests for edge case formatter methods added for output unification."""

    def setUp(self):
        """Set up empty test directories for edge case testing."""
        super().setUp()
        # Create additional empty directories for no-match testing
        self.empty_dir1 = os.path.join(self.temp_dir, "empty1")
        self.empty_dir2 = os.path.join(self.temp_dir, "empty2")
        os.makedirs(self.empty_dir1)
        os.makedirs(self.empty_dir2)

    def run_main_with_args(self, args: list[str]) -> str:
        """Helper to run main() with given args and capture stdout."""
        f = io.StringIO()
        with redirect_stdout(f):
            main()
        return f.getvalue()

    def test_empty_result_compare_mode(self):
        """Test format_empty_result in compare mode."""
        # Create dirs with no matching files (different content)
        with open(os.path.join(self.empty_dir1, "unique1.txt"), "w") as f:
            f.write("content1")
        with open(os.path.join(self.empty_dir2, "unique2.txt"), "w") as f:
            f.write("content2")

        with patch('sys.argv', ['file_matcher.py', self.empty_dir1, self.empty_dir2]):
            output = self.run_main_with_args([])
            self.assertIn("No matching files found", output)

    def test_empty_result_dedup_mode(self):
        """Test format_empty_result in dedup mode."""
        # Create two dirs with unique content (no matches between them)
        with open(os.path.join(self.empty_dir1, "file1.txt"), "w") as f:
            f.write("unique1_master")
        with open(os.path.join(self.empty_dir2, "file2.txt"), "w") as f:
            f.write("unique2_dup")

        with patch('sys.argv', ['file_matcher.py', self.empty_dir1, self.empty_dir2,
                                '--action', 'hardlink']):
            with patch('sys.stdin.isatty', return_value=False):
                output = self.run_main_with_args([])
                self.assertIn("No duplicates found", output)

    def test_unmatched_header_text_mode(self):
        """Test format_unmatched_header routes through formatter."""
        # Create dirs with no matching files
        with open(os.path.join(self.empty_dir1, "unique.txt"), "w") as f:
            f.write("unique")
        with open(os.path.join(self.empty_dir2, "other.txt"), "w") as f:
            f.write("other")

        with patch('sys.argv', ['file_matcher.py', self.empty_dir1, self.empty_dir2, '-u']):
            output = self.run_main_with_args([])
            self.assertIn("Files with no content matches", output)

    def test_unmatched_header_json_mode(self):
        """Test JSON mode doesn't output unmatched header text."""
        import json as json_module
        # Create dirs with no matching files
        with open(os.path.join(self.empty_dir1, "unique.txt"), "w") as f:
            f.write("unique")
        with open(os.path.join(self.empty_dir2, "other.txt"), "w") as f:
            f.write("other")

        with patch('sys.argv', ['file_matcher.py', self.empty_dir1, self.empty_dir2,
                                '-u', '--json']):
            output = self.run_main_with_args([])
            # JSON mode should NOT have the text header
            self.assertNotIn("Files with no content matches", output)
            # But should have valid JSON
            parsed = json_module.loads(output)
            self.assertIn('unmatchedDir1', parsed)


if __name__ == "__main__":
    unittest.main()
