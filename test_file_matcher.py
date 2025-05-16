#!/usr/bin/env python3

import unittest
import os
import tempfile
import shutil
import random
import string
from pathlib import Path
from file_matcher import get_file_hash, index_directory, find_matching_files

class TestFileMatcher(unittest.TestCase):
    def setUp(self):
        """Set up test environment with temporary directories."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test_dir1 structure inside temp dir
        self.test_dir1 = os.path.join(self.temp_dir, "test_dir1")
        os.makedirs(self.test_dir1)
        os.makedirs(os.path.join(self.test_dir1, "subdir"))
        
        # Create test_dir2 structure inside temp dir
        self.test_dir2 = os.path.join(self.temp_dir, "test_dir2")
        os.makedirs(self.test_dir2)
        os.makedirs(os.path.join(self.test_dir2, "subdir"))
        
        # Create files with identical content but different names
        with open(os.path.join(self.test_dir1, "file1.txt"), "w") as f:
            f.write("This is file content A\n")
        
        with open(os.path.join(self.test_dir2, "different_name.txt"), "w") as f:
            f.write("This is file content A\n")
            
        # Create files with different content and different names
        with open(os.path.join(self.test_dir1, "file2.txt"), "w") as f:
            f.write("This is file content B\n")
            
        with open(os.path.join(self.test_dir2, "file4.txt"), "w") as f:
            f.write("This is file content C\n")
            
        # Create files with same name but different content
        with open(os.path.join(self.test_dir1, "common_name.txt"), "w") as f:
            f.write("This is common name file with content X\n")
            
        with open(os.path.join(self.test_dir2, "common_name.txt"), "w") as f:
            f.write("This is common name file with content Y\n")
            
        # Create identical files with same content in subdir
        with open(os.path.join(self.test_dir1, "file3.txt"), "w") as f:
            f.write("This is file content A\n")
            
        with open(os.path.join(self.test_dir2, "also_different_name.txt"), "w") as f:
            f.write("This is file content A\n")
            
        # Create nested files
        with open(os.path.join(self.test_dir1, "subdir", "nested1.txt"), "w") as f:
            f.write("This is nested content\n")
            
        with open(os.path.join(self.test_dir2, "subdir", "different_nested.txt"), "w") as f:
            f.write("This is different nested content\n")

    def tearDown(self):
        """Clean up temporary directories after tests."""
        shutil.rmtree(self.temp_dir)

    def test_get_file_hash(self):
        """Test file hashing function."""
        file1 = os.path.join(self.test_dir1, "file1.txt")
        file2 = os.path.join(self.test_dir2, "different_name.txt")
        
        # Same content files should have same hash
        self.assertEqual(get_file_hash(file1), get_file_hash(file2))
        
        file3 = os.path.join(self.test_dir1, "file2.txt")
        # Different content files should have different hash
        self.assertNotEqual(get_file_hash(file1), get_file_hash(file3))
        
        # Test with different hash algorithm
        self.assertEqual(get_file_hash(file1, "sha256"), get_file_hash(file2, "sha256"))

    def test_large_file_chunking(self):
        """Test that file hashing works correctly with large files that require chunking."""
        # Create a large file (8MB - larger than the 4KB chunk size)
        large_file_path = os.path.join(self.temp_dir, "large_file.bin")
        duplicate_file_path = os.path.join(self.temp_dir, "large_file_duplicate.bin")
        
        # Size of 8MB (2^23 = 8,388,608 bytes)
        file_size = 2**23
        
        # Create a large file with pseudo-random content
        random.seed(42)  # For reproducibility
        with open(large_file_path, 'wb') as f:
            # Write in chunks to avoid memory issues
            chunk_size = 65536  # 64KB chunks for file generation
            remaining = file_size
            while remaining > 0:
                # Generate random bytes
                size = min(chunk_size, remaining)
                data = bytes(random.getrandbits(8) for _ in range(size))
                f.write(data)
                remaining -= size
        
        # Create an exact duplicate of the large file
        shutil.copy(large_file_path, duplicate_file_path)
        
        # Verify file sizes
        self.assertEqual(os.path.getsize(large_file_path), file_size)
        self.assertEqual(os.path.getsize(duplicate_file_path), file_size)
        
        # Get file hashes
        hash1 = get_file_hash(large_file_path)
        hash2 = get_file_hash(duplicate_file_path)
        
        # Identical files should have identical hashes
        self.assertEqual(hash1, hash2)
        
        # Now modify the beginning of the duplicate file slightly
        with open(duplicate_file_path, 'r+b') as f:
            f.write(b'MODIFIED')  # Overwrite first 8 bytes
        
        # Get hash of modified file
        modified_hash = get_file_hash(duplicate_file_path)
        
        # Modified file should have different hash
        self.assertNotEqual(hash1, modified_hash)
        
        # Test with different hash algorithm
        hash1_sha256 = get_file_hash(large_file_path, 'sha256')
        modified_hash_sha256 = get_file_hash(duplicate_file_path, 'sha256')
        self.assertNotEqual(hash1_sha256, modified_hash_sha256)
        
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
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
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


if __name__ == "__main__":
    unittest.main() 