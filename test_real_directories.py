#!/usr/bin/env python3

import unittest
import os
from file_matcher import index_directory, find_matching_files, get_file_hash

class TestRealDirectories(unittest.TestCase):
    """Tests that validate file matching using the actual test directories."""
    
    def setUp(self):
        """Set up paths to test directories."""
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.test_dir1 = os.path.join(self.current_dir, "test_dir1")
        self.test_dir2 = os.path.join(self.current_dir, "test_dir2")
        
        # Skip tests if test directories don't exist
        if not (os.path.isdir(self.test_dir1) and os.path.isdir(self.test_dir2)):
            self.skipTest("Test directories not found")

    def test_file_hashing(self):
        """Test that identical content files have the same hash."""
        file1 = os.path.join(self.test_dir1, "file1.txt")
        file_different_name = os.path.join(self.test_dir2, "different_name.txt")
        
        # These files should have identical content based on our exploration
        self.assertEqual(get_file_hash(file1), get_file_hash(file_different_name))
        
        # Different files should have different hashes
        file2 = os.path.join(self.test_dir1, "file2.txt")
        self.assertNotEqual(get_file_hash(file1), get_file_hash(file2))
        
        # Files with same name but different content should have different hashes
        common_name1 = os.path.join(self.test_dir1, "common_name.txt")
        common_name2 = os.path.join(self.test_dir2, "common_name.txt")
        self.assertNotEqual(get_file_hash(common_name1), get_file_hash(common_name2))

    def test_directory_indexing(self):
        """Test indexing of the real test directories."""
        index1 = index_directory(self.test_dir1)
        index2 = index_directory(self.test_dir2)
        
        # Test directory 1 should have 5 files (4 in main dir + 1 in subdir)
        file_count1 = sum(len(files) for files in index1.values())
        self.assertEqual(file_count1, 5)
        
        # Test directory 2 should have 5 files (4 in main dir + 1 in subdir)
        file_count2 = sum(len(files) for files in index2.values())
        self.assertEqual(file_count2, 5)
        
        # Check that we have the right structure of hashes to files
        # There should be multiple unique hashes in each index
        self.assertGreater(len(index1), 1)
        self.assertGreater(len(index2), 1)

    def test_matching_files(self):
        """Test that file matching correctly identifies matches between test directories."""
        matches, unmatched1, unmatched2 = find_matching_files(self.test_dir1, self.test_dir2)
        
        # We expect at least one match from files with same content but different names
        self.assertGreater(len(matches), 0)
        
        # Check that we found the match between file1.txt/file3.txt and different_name.txt/also_different_name.txt
        found_content_a_match = False
        for file_hash, (files1, files2) in matches.items():
            file1_basenames = [os.path.basename(f) for f in files1]
            file2_basenames = [os.path.basename(f) for f in files2]
            
            if "file1.txt" in file1_basenames and "different_name.txt" in file2_basenames:
                found_content_a_match = True
                break
                
        self.assertTrue(found_content_a_match, "Failed to find expected match between file1.txt and different_name.txt")
        
        # Verify that unmatched files include common_name.txt (which has different content in both dirs)
        unmatched1_basenames = [os.path.basename(f) for f in unmatched1]
        unmatched2_basenames = [os.path.basename(f) for f in unmatched2]
        
        self.assertIn("common_name.txt", unmatched1_basenames, 
                     "common_name.txt should be in unmatched files for test_dir1")
        self.assertIn("common_name.txt", unmatched2_basenames, 
                     "common_name.txt should be in unmatched files for test_dir2")

    def test_nested_files(self):
        """Test that nested files are correctly processed."""
        matches, unmatched1, unmatched2 = find_matching_files(self.test_dir1, self.test_dir2)
        
        # Check if the nested files are being matched rather than considered unmatched
        found_nested_match = False
        for file_hash, (files1, files2) in matches.items():
            for file1 in files1:
                if "nested1.txt" in file1:
                    found_nested_match = True
                    break
            
            if found_nested_match:
                break
                
        # Either the nested file should be in matches or unmatched1
        nested1_full_path = os.path.join(self.test_dir1, "subdir", "nested1.txt")
        nested2_full_path = os.path.join(self.test_dir2, "subdir", "different_nested.txt")
        
        nested_in_matches = found_nested_match
        nested_in_unmatched = nested1_full_path in unmatched1
        
        # The nested files must be either matched or unmatched
        self.assertTrue(nested_in_matches or nested_in_unmatched, 
                      f"Nested file {nested1_full_path} not found in either matches or unmatched lists")


if __name__ == "__main__":
    unittest.main() 