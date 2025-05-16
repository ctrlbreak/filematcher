#!/usr/bin/env python3

import unittest
import os
import tempfile
import shutil
import random
from pathlib import Path

class BaseFileMatcherTest(unittest.TestCase):
    """Base test class with common setup/teardown methods for file matcher tests."""
    
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