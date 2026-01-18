#!/usr/bin/env python3

import os
import random
import unittest

import file_matcher
from file_matcher import get_file_hash, get_sparse_hash, find_matching_files
from tests.test_base import BaseFileMatcherTest


class TestFastMode(BaseFileMatcherTest):
    """Tests for fast mode and sparse hashing functionality."""
    
    def test_sparse_hash_fast_mode(self):
        """Test the fast mode sparse sampling functionality."""
        # Create a larger file (12MB to trigger fast mode with lower threshold for testing)
        large_file_path = os.path.join(self.temp_dir, "large_file_for_sparse.bin")
        duplicate_file_path = os.path.join(self.temp_dir, "duplicate_for_sparse.bin")
        modified_file_path = os.path.join(self.temp_dir, "modified_for_sparse.bin")
        
        # Use a smaller size threshold for testing
        size_threshold = 10 * 1024 * 1024  # 10MB
        file_size = 12 * 1024 * 1024  # 12MB
        
        # Create a large file with pseudo-random content
        random.seed(42)  # For reproducibility
        with open(large_file_path, 'wb') as f:
            # Write in chunks to avoid memory issues
            chunk_size = 65536  # 64KB chunks
            remaining = file_size
            while remaining > 0:
                size = min(chunk_size, remaining)
                data = bytes(random.getrandbits(8) for _ in range(size))
                f.write(data)
                remaining -= size
        
        # Create exact duplicates
        with open(large_file_path, 'rb') as src, open(duplicate_file_path, 'wb') as dst:
            dst.write(src.read())
        with open(large_file_path, 'rb') as src, open(modified_file_path, 'wb') as dst:
            dst.write(src.read())
        
        # Test normal vs fast mode on identical files
        normal_hash1 = get_file_hash(large_file_path, 'md5', fast_mode=False)
        normal_hash2 = get_file_hash(duplicate_file_path, 'md5', fast_mode=False)
        
        # These should be identical since the files are identical
        self.assertEqual(normal_hash1, normal_hash2)
        
        # Now test with fast mode
        fast_hash1 = get_file_hash(large_file_path, 'md5', fast_mode=True, size_threshold=size_threshold)
        fast_hash2 = get_file_hash(duplicate_file_path, 'md5', fast_mode=True, size_threshold=size_threshold)
        
        # Fast mode should also find them identical
        self.assertEqual(fast_hash1, fast_hash2)
        
        # But the fast hash and normal hash will be different due to different algorithms
        self.assertNotEqual(normal_hash1, fast_hash1)
        
        # Now modify the file in the middle
        with open(modified_file_path, 'r+b') as f:
            # Seek to the middle of the file
            f.seek(file_size // 2)
            f.write(b'MODIFIED_MIDDLE')
        
        # Fast mode should detect the difference
        modified_fast_hash = get_file_hash(modified_file_path, 'md5', fast_mode=True, size_threshold=size_threshold)
        self.assertNotEqual(fast_hash1, modified_fast_hash)
        
        # Test direct comparison of files with different sizes
        different_size_path = os.path.join(self.temp_dir, "different_size.bin")
        with open(different_size_path, 'wb') as f:
            f.write(b'Small file with different size')
        
        # Files with different sizes should have different sparse hashes
        small_file_hash = get_file_hash(different_size_path, 'md5', fast_mode=True)
        self.assertNotEqual(fast_hash1, small_file_hash)
        
    def test_fast_mode_in_directory_comparison(self):
        """Test that fast mode works correctly when comparing directories."""
        # Create test files in temporary subdirectories
        temp_dir1 = os.path.join(self.temp_dir, "fast_test_dir1")
        temp_dir2 = os.path.join(self.temp_dir, "fast_test_dir2")
        os.makedirs(temp_dir1)
        os.makedirs(temp_dir2)
        
        # Set size threshold lower for testing
        size_threshold = 1024  # 1KB threshold for testing
        
        # Create matching files (small files, should not use fast mode)
        with open(os.path.join(temp_dir1, "small_a.txt"), "w") as f:
            f.write("small file content A")
        with open(os.path.join(temp_dir2, "small_b.txt"), "w") as f:
            f.write("small file content A")  # Same content, different name
            
        # Create "large" files that will trigger fast mode with our lower threshold
        large_content = "X" * 2048  # 2KB content
        with open(os.path.join(temp_dir1, "large_a.bin"), "w") as f:
            f.write(large_content)
        with open(os.path.join(temp_dir2, "large_b.bin"), "w") as f:
            f.write(large_content)  # Same content, different name
            
        # Create unmatched files
        with open(os.path.join(temp_dir1, "unique_a.txt"), "w") as f:
            f.write("unique content A")
        with open(os.path.join(temp_dir2, "unique_b.txt"), "w") as f:
            f.write("unique content B")
            
        # Find matches using normal mode
        matches_normal, unmatched1_normal, unmatched2_normal = find_matching_files(
            temp_dir1, temp_dir2, fast_mode=False)
            
        # Find matches using fast mode
        # Monkeypatch the size threshold temporarily
        original_threshold = 100*1024*1024  # Save original
        file_matcher.get_file_hash.__defaults__ = (file_matcher.get_file_hash.__defaults__[0], 
                                                 False, size_threshold)
        
        try:
            matches_fast, unmatched1_fast, unmatched2_fast = find_matching_files(
                temp_dir1, temp_dir2, fast_mode=True)
                
            # Results should be the same regardless of mode
            self.assertEqual(len(matches_normal), len(matches_fast))
            self.assertEqual(len(unmatched1_normal), len(unmatched1_fast))
            self.assertEqual(len(unmatched2_normal), len(unmatched2_fast))
            
            # Check that we have 2 matches (one for small files, one for large files)
            self.assertEqual(len(matches_fast), 2)
            
        finally:
            # Restore original threshold
            file_matcher.get_file_hash.__defaults__ = (file_matcher.get_file_hash.__defaults__[0], 
                                                    False, original_threshold)


if __name__ == "__main__":
    unittest.main() 