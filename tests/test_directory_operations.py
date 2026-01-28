#!/usr/bin/env python3

import io
import os
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from filematcher import (
    index_directory, find_matching_files, get_file_hash,
    is_symlink_to, execute_action, is_hardlink_to,
    filter_hardlinked_duplicates, main
)
from tests.test_base import BaseFileMatcherTest


class TestDirectoryOperations(BaseFileMatcherTest):
    """Tests for directory indexing and file matching operations."""
    
    def test_index_directory(self):
        """Test directory indexing functionality."""
        index1 = index_directory(self.test_dir1)
        
        # Should have the right number of files
        file_count = sum(len(files) for files in index1.values())
        self.assertEqual(file_count, 5)  # 4 files in main dir + 1 in subdir
        
        # Check that files with same content have the same hash key
        # First, find the hash for file1.txt
        file1_path = os.path.join(self.test_dir1, "file1.txt")
        file1_hash = get_file_hash(file1_path)
        
        # There should be two files with this hash (file1.txt and file3.txt)
        files_with_hash = index1[file1_hash]
        self.assertEqual(len(files_with_hash), 2)

    def test_find_matching_files(self):
        """Test the main matching functionality."""
        matches, unmatched1, unmatched2 = find_matching_files(self.test_dir1, self.test_dir2)
        
        # Should find one hash with matches (the "This is file content A" files)
        self.assertEqual(len(matches), 1)
        
        # Extract the hash key
        file_hash = list(matches.keys())[0]
        
        # There should be 2 files in dir1 with this hash
        self.assertEqual(len(matches[file_hash][0]), 2)
        
        # There should be 2 files in dir2 with this hash
        self.assertEqual(len(matches[file_hash][1]), 2)
        
        # Check unmatched files
        # In dir1: file2.txt, common_name.txt, subdir/nested1.txt
        self.assertEqual(len(unmatched1), 3)
        
        # In dir2: file4.txt, common_name.txt, subdir/different_nested.txt
        self.assertEqual(len(unmatched2), 3)
    
    def test_with_real_directories(self):
        """Test with the actual test directories in the project."""
        # Get the absolute path of the current script's directory
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Construct paths to the test directories relative to the script
        test_dir1 = os.path.join(current_dir, "test_dir1")
        test_dir2 = os.path.join(current_dir, "test_dir2")

        # Only run this test if the directories exist
        if os.path.isdir(test_dir1) and os.path.isdir(test_dir2):
            matches, unmatched1, unmatched2 = find_matching_files(test_dir1, test_dir2)

            # We expect at least one match based on our exploration
            self.assertGreater(len(matches), 0)

            # Log details about matches for debugging
            for file_hash, (files1, files2) in matches.items():
                print(f"\nHash match: {file_hash}")
                print(f"Files in test_dir1: {files1}")
                print(f"Files in test_dir2: {files2}")
        else:
            self.skipTest("Test directories not found")

    def test_no_circular_imports(self):
        """Verify filematcher package imports cleanly in fresh subprocess (PKG-04)."""
        # Test importing all major exports in fresh Python process
        result = subprocess.run(
            [sys.executable, '-c', '''
from filematcher import (
    main,
    find_matching_files,
    index_directory,
    get_file_hash,
    get_sparse_hash,
    execute_action,
    execute_all_actions,
    safe_replace_with_link,
    ColorConfig,
    ColorMode,
    ActionFormatter,
    TextActionFormatter,
    JsonActionFormatter,
    is_hardlink_to,
    is_symlink_to,
    check_cross_filesystem,
    create_audit_logger,
)
print("All imports successful")
'''],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent)
        )
        self.assertEqual(result.returncode, 0, f"Import failed: {result.stderr}")
        self.assertIn("All imports successful", result.stdout)
        self.assertNotIn("ImportError", result.stderr)
        self.assertNotIn("circular", result.stderr.lower())


class TestDifferentNamesOnly(unittest.TestCase):
    """Tests for the --different-names-only flag."""

    def setUp(self):
        """Set up test directories with same-name and different-name duplicates."""
        import tempfile
        import shutil
        self.temp_dir = tempfile.mkdtemp()

        self.dir1 = os.path.join(self.temp_dir, "dir1")
        self.dir2 = os.path.join(self.temp_dir, "dir2")
        os.makedirs(self.dir1)
        os.makedirs(self.dir2)

        # Same content, SAME name in both dirs
        with open(os.path.join(self.dir1, "same_name.txt"), "w") as f:
            f.write("identical content A\n")
        with open(os.path.join(self.dir2, "same_name.txt"), "w") as f:
            f.write("identical content A\n")

        # Same content, DIFFERENT names
        with open(os.path.join(self.dir1, "original.txt"), "w") as f:
            f.write("identical content B\n")
        with open(os.path.join(self.dir2, "renamed.txt"), "w") as f:
            f.write("identical content B\n")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_default_includes_same_name_matches(self):
        """By default, find_matching_files includes same-name content matches."""
        matches, _, _ = find_matching_files(self.dir1, self.dir2)
        # Should find 2 groups: same_name.txt match AND original.txt/renamed.txt match
        self.assertEqual(len(matches), 2)

    def test_different_names_only_excludes_same_name_matches(self):
        """With different_names_only=True, same-name matches are excluded."""
        matches, _, _ = find_matching_files(self.dir1, self.dir2, different_names_only=True)
        # Should only find 1 group: original.txt/renamed.txt
        self.assertEqual(len(matches), 1)
        # Verify the remaining match is the different-named pair
        file_hash = list(matches.keys())[0]
        files1, files2 = matches[file_hash]
        self.assertTrue(any("original.txt" in f for f in files1))
        self.assertTrue(any("renamed.txt" in f for f in files2))

    def test_different_names_only_with_mixed_group(self):
        """Test a group with both same-name and different-name files."""
        # Add another file with the same content as same_name.txt but different name
        with open(os.path.join(self.dir2, "also_same_content.txt"), "w") as f:
            f.write("identical content A\n")

        matches, _, _ = find_matching_files(self.dir1, self.dir2, different_names_only=True)
        # Now the "identical content A" group has different names, so it should be included
        self.assertEqual(len(matches), 2)


class TestIsHardlinkTo(unittest.TestCase):
    """Tests for is_hardlink_to() function."""

    def setUp(self):
        import tempfile
        import shutil
        self.temp_dir = tempfile.mkdtemp()
        self.master_file = os.path.join(self.temp_dir, "master.txt")
        self.duplicate_file = os.path.join(self.temp_dir, "duplicate.txt")
        self._shutil = shutil

    def tearDown(self):
        self._shutil.rmtree(self.temp_dir)

    def test_is_hardlink_to_false_different_files(self):
        """Two separate files are not hardlinked."""
        with open(self.master_file, "w") as f:
            f.write("content")
        with open(self.duplicate_file, "w") as f:
            f.write("content")
        self.assertFalse(is_hardlink_to(self.master_file, self.duplicate_file))

    def test_is_hardlink_to_true(self):
        """Files that share an inode are detected as hardlinked."""
        with open(self.master_file, "w") as f:
            f.write("content")
        os.link(self.master_file, self.duplicate_file)
        self.assertTrue(is_hardlink_to(self.master_file, self.duplicate_file))

    def test_is_hardlink_to_missing_file_returns_false(self):
        """Missing file returns False, not error."""
        with open(self.master_file, "w") as f:
            f.write("content")
        self.assertFalse(is_hardlink_to(self.master_file, "/nonexistent/path"))

    def test_is_hardlink_to_both_files_missing_returns_false(self):
        """Both files missing returns False, not error."""
        self.assertFalse(is_hardlink_to("/nonexistent/path1", "/nonexistent/path2"))


class TestSkipAlreadyLinked(unittest.TestCase):
    """Tests for symlink and hardlink detection and skipping."""

    def setUp(self):
        """Set up test directories with master and duplicate files."""
        import tempfile
        self.temp_dir = tempfile.mkdtemp()
        self.master_dir = os.path.join(self.temp_dir, "master")
        self.dup_dir = os.path.join(self.temp_dir, "dup")
        os.makedirs(self.master_dir)
        os.makedirs(self.dup_dir)

        # Create master file
        self.master_file = os.path.join(self.master_dir, "master.txt")
        with open(self.master_file, "w") as f:
            f.write("master content\n")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_is_symlink_to_true(self):
        """Symlink pointing to master file is detected."""
        symlink_path = os.path.join(self.dup_dir, "link.txt")
        os.symlink(self.master_file, symlink_path)

        self.assertTrue(is_symlink_to(symlink_path, self.master_file))

    def test_is_symlink_to_false_different_target(self):
        """Symlink pointing to different file is not detected as symlink to master."""
        # Create another file
        other_file = os.path.join(self.master_dir, "other.txt")
        with open(other_file, "w") as f:
            f.write("other content\n")

        # Create symlink pointing to other file
        symlink_path = os.path.join(self.dup_dir, "link.txt")
        os.symlink(other_file, symlink_path)

        self.assertFalse(is_symlink_to(symlink_path, self.master_file))

    def test_is_symlink_to_false_regular_file(self):
        """Regular file is not detected as symlink to master."""
        duplicate_path = os.path.join(self.dup_dir, "dup.txt")
        with open(duplicate_path, "w") as f:
            f.write("master content\n")

        self.assertFalse(is_symlink_to(duplicate_path, self.master_file))

    def test_is_symlink_to_missing_file_returns_false(self):
        """Missing file returns False, not error."""
        self.assertFalse(is_symlink_to("/nonexistent/path", self.master_file))

    def test_is_symlink_to_both_files_missing_returns_false(self):
        """Both files missing returns False, not error."""
        self.assertFalse(is_symlink_to("/nonexistent/path1", "/nonexistent/path2"))

    def test_execute_action_skips_symlink_to_master(self):
        """execute_action skips symlinks pointing to master with correct reason."""
        symlink_path = os.path.join(self.dup_dir, "link.txt")
        os.symlink(self.master_file, symlink_path)

        success, error, actual_action = execute_action(
            symlink_path, self.master_file, 'hardlink'
        )

        self.assertTrue(success)
        self.assertEqual(error, "symlink to master")
        self.assertEqual(actual_action, "skipped")
        # Symlink should still exist
        self.assertTrue(os.path.islink(symlink_path))

    def test_execute_action_skips_hardlink_to_master_all_actions(self):
        """execute_action skips hardlinks to master for all action types."""
        hardlink_path = os.path.join(self.dup_dir, "linked.txt")
        os.link(self.master_file, hardlink_path)

        # Test with action='symlink'
        success, error, actual_action = execute_action(
            hardlink_path, self.master_file, 'symlink'
        )
        self.assertTrue(success)
        self.assertEqual(error, "hardlink to master")
        self.assertEqual(actual_action, "skipped")

        # Test with action='delete'
        success, error, actual_action = execute_action(
            hardlink_path, self.master_file, 'delete'
        )
        self.assertTrue(success)
        self.assertEqual(error, "hardlink to master")
        self.assertEqual(actual_action, "skipped")

        # Test with action='hardlink' (original behavior)
        success, error, actual_action = execute_action(
            hardlink_path, self.master_file, 'hardlink'
        )
        self.assertTrue(success)
        self.assertEqual(error, "hardlink to master")
        self.assertEqual(actual_action, "skipped")

        # Hardlink should still exist (not modified)
        self.assertTrue(os.path.exists(hardlink_path))
        self.assertTrue(is_hardlink_to(hardlink_path, self.master_file))


class TestFilterHardlinkedDuplicates(unittest.TestCase):
    """Tests for filter_hardlinked_duplicates() function."""

    def setUp(self):
        import tempfile
        import shutil
        self._shutil = shutil
        self.temp_dir = tempfile.mkdtemp()
        self.master_file = os.path.join(self.temp_dir, "master.txt")
        self.dup1 = os.path.join(self.temp_dir, "dup1.txt")
        self.dup2 = os.path.join(self.temp_dir, "dup2.txt")
        self.hardlink_dup = os.path.join(self.temp_dir, "hardlink_dup.txt")

    def tearDown(self):
        self._shutil.rmtree(self.temp_dir)

    def test_filter_separates_hardlinked_from_regular(self):
        """Hardlinked duplicates should be separated from regular duplicates."""
        # Create master and two regular duplicates
        with open(self.master_file, "w") as f:
            f.write("content")
        with open(self.dup1, "w") as f:
            f.write("content")
        with open(self.dup2, "w") as f:
            f.write("content")
        # Create hardlink to master
        os.link(self.master_file, self.hardlink_dup)

        duplicates = [self.dup1, self.dup2, self.hardlink_dup]
        actionable, hardlinked = filter_hardlinked_duplicates(self.master_file, duplicates)

        self.assertEqual(len(actionable), 2)
        self.assertIn(self.dup1, actionable)
        self.assertIn(self.dup2, actionable)
        self.assertEqual(len(hardlinked), 1)
        self.assertIn(self.hardlink_dup, hardlinked)

    def test_filter_all_hardlinked(self):
        """When all duplicates are hardlinked, actionable list is empty."""
        with open(self.master_file, "w") as f:
            f.write("content")
        os.link(self.master_file, self.dup1)
        os.link(self.master_file, self.dup2)

        duplicates = [self.dup1, self.dup2]
        actionable, hardlinked = filter_hardlinked_duplicates(self.master_file, duplicates)

        self.assertEqual(len(actionable), 0)
        self.assertEqual(len(hardlinked), 2)

    def test_filter_no_hardlinked(self):
        """When no duplicates are hardlinked, hardlinked list is empty."""
        with open(self.master_file, "w") as f:
            f.write("content")
        with open(self.dup1, "w") as f:
            f.write("content")
        with open(self.dup2, "w") as f:
            f.write("content")

        duplicates = [self.dup1, self.dup2]
        actionable, hardlinked = filter_hardlinked_duplicates(self.master_file, duplicates)

        self.assertEqual(len(actionable), 2)
        self.assertEqual(len(hardlinked), 0)

    def test_filter_empty_duplicates(self):
        """Empty duplicates list returns two empty lists."""
        with open(self.master_file, "w") as f:
            f.write("content")

        actionable, hardlinked = filter_hardlinked_duplicates(self.master_file, [])

        self.assertEqual(actionable, [])
        self.assertEqual(hardlinked, [])


class TestCrossFilesystemWarnings(BaseFileMatcherTest):
    """Tests for cross-filesystem detection and warnings in output."""

    def run_main_with_args(self, args: list[str]) -> str:
        """Helper to run main() with given args and capture stdout."""
        f = io.StringIO()
        with redirect_stdout(f):
            main()
        return f.getvalue()

    def test_cross_fs_marker_shown_for_hardlink(self):
        """Cross-filesystem files show [!cross-fs] marker in hardlink mode."""
        # Mock check_cross_filesystem to simulate cross-filesystem files
        # Patch where the function is used (filematcher.cli), not where it's defined
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--action', 'hardlink']):
            with patch('filematcher.cli.check_cross_filesystem') as mock_check:
                # Return all duplicates as cross-filesystem
                def mock_cross_fs(master_file, duplicates):
                    return set(duplicates)
                mock_check.side_effect = mock_cross_fs
                output = self.run_main_with_args([])
                self.assertIn("[!cross-fs]", output)

    def test_no_cross_fs_marker_for_symlink_or_delete(self):
        """Cross-filesystem marker should not appear for symlink/delete actions."""
        for action in ['symlink', 'delete']:
            with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2, '--action', action]):
                output = self.run_main_with_args([])
                # Symlink and delete work across filesystems, so no warning needed
                self.assertNotIn("[!cross-fs]", output)


if __name__ == "__main__":
    unittest.main() 