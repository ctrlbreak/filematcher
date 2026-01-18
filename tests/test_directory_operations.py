#!/usr/bin/env python3

import os
import unittest

from file_matcher import index_directory, find_matching_files, get_file_hash
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


if __name__ == "__main__":
    unittest.main() 