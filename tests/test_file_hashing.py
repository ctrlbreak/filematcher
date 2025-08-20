#!/usr/bin/env python3

import os
import sys
import random
import shutil
import unittest

# Add parent directory to path so we can import the file_matcher module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from file_matcher import get_file_hash, format_file_size
from tests.test_base import BaseFileMatcherTest


class TestFileHashing(BaseFileMatcherTest):
    """Tests for basic file hashing functionality."""
    
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
        
        # Now modify the end of the duplicate file
        # This ensures we're testing a modification in a later chunk
        with open(duplicate_file_path, 'r+b') as f:
            # Seek to near the end of the file - specifically to the last chunk
            # The chunk size in get_file_hash is 4KB (4096 bytes)
            f.seek(file_size - 100)  # 100 bytes from the end
            f.write(b'MODIFIED_END')  # Modify the last chunk
        
        # Get hash of modified file
        modified_hash = get_file_hash(duplicate_file_path)
        
        # Modified file should have different hash
        self.assertNotEqual(hash1, modified_hash)
        
        # Test with different hash algorithm
        hash1_sha256 = get_file_hash(large_file_path, 'sha256')
        modified_hash_sha256 = get_file_hash(duplicate_file_path, 'sha256')
        self.assertNotEqual(hash1_sha256, modified_hash_sha256)
    
    def test_format_file_size(self):
        """Test the file size formatting function."""
        # Test bytes
        self.assertEqual(format_file_size(0), "0 B")
        self.assertEqual(format_file_size(512), "512 B")
        self.assertEqual(format_file_size(1023), "1023 B")
        
        # Test kilobytes
        self.assertEqual(format_file_size(1024), "1.0 KB")
        self.assertEqual(format_file_size(1536), "1.5 KB")
        self.assertEqual(format_file_size(2048), "2.0 KB")
        
        # Test megabytes
        self.assertEqual(format_file_size(1024*1024), "1.0 MB")
        self.assertEqual(format_file_size(1024*1024*1.5), "1.5 MB")
        
        # Test gigabytes
        self.assertEqual(format_file_size(1024*1024*1024), "1.0 GB")
        self.assertEqual(format_file_size(int(1024*1024*1024*2.5)), "2.5 GB")
        
        # Test terabytes
        self.assertEqual(format_file_size(1024*1024*1024*1024), "1.0 TB")


if __name__ == "__main__":
    unittest.main() 