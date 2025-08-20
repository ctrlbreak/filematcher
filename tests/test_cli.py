#!/usr/bin/env python3

import os
import sys
import io
import unittest
from contextlib import redirect_stdout

# Add parent directory to path so we can import the file_matcher module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from file_matcher import main
from tests.test_base import BaseFileMatcherTest


class TestCLI(BaseFileMatcherTest):
    """Tests for command-line interface and output formatting."""
    
    def test_summary_mode(self):
        """Test summary mode output with matched and unmatched files."""
        # Save original sys.argv
        original_argv = sys.argv.copy()
        
        try:
            # Set up arguments for summary mode with unmatched files
            sys.argv = ['file_matcher.py', self.test_dir1, self.test_dir2, '--summary', '--show-unmatched']
            
            # Capture stdout
            f = io.StringIO()
            with redirect_stdout(f):
                main()
                
            output = f.getvalue()
            
            # Check summary output format
            self.assertIn("Matched files summary:", output)
            self.assertIn("Unique content hashes with matches:", output)
            self.assertIn("Files in", output)
            
            # Check that it includes unmatched summary
            self.assertIn("Unmatched files summary:", output)
            
            # Actual numbers should be in the output
            self.assertIn("with matches in", output)  # Check for this specific text
            self.assertIn("with no match:", output)
            
            # The output should not contain detailed file listings
            self.assertNotIn("Hash:", output)
            # Directory paths will be in the summary, but there shouldn't be individual file listings
            self.assertNotIn("file1.txt", output)
            self.assertNotIn("file2.txt", output)
            
            # Now test summary mode without unmatched files
            sys.argv = ['file_matcher.py', self.test_dir1, self.test_dir2, '--summary']
            
            f = io.StringIO()
            with redirect_stdout(f):
                main()
                
            output = f.getvalue()
            
            # Should have matched summary but not unmatched summary
            self.assertIn("Matched files summary:", output)
            self.assertNotIn("Unmatched files summary:", output)
            
        finally:
            # Restore original sys.argv
            sys.argv = original_argv
    
    def test_detailed_output_mode(self):
        """Test detailed output format (default mode)."""
        # Save original sys.argv
        original_argv = sys.argv.copy()
        
        try:
            # Set up arguments for default detailed output mode 
            sys.argv = ['file_matcher.py', self.test_dir1, self.test_dir2]
            
            # Capture stdout
            f = io.StringIO()
            with redirect_stdout(f):
                main()
                
            output = f.getvalue()
            
            # Check that the output includes hash details and file listings
            self.assertIn("Hash:", output)
            self.assertIn("Files in", output)
            
            # Test with unmatched files option
            sys.argv = ['file_matcher.py', self.test_dir1, self.test_dir2, '--show-unmatched']
            
            f = io.StringIO()
            with redirect_stdout(f):
                main()
                
            output = f.getvalue()
            
            # Check for unmatched files section
            self.assertIn("Files with no content matches", output)
            self.assertIn("Unique files in", output)
            
        finally:
            # Restore original sys.argv
            sys.argv = original_argv
    
    def test_hash_algorithm_option(self):
        """Test the hash algorithm command-line option."""
        # Save original sys.argv
        original_argv = sys.argv.copy()
        
        try:
            # Test with MD5 (default)
            sys.argv = ['file_matcher.py', self.test_dir1, self.test_dir2]
            
            f = io.StringIO()
            with redirect_stdout(f):
                main()
                
            output_md5 = f.getvalue()
            self.assertIn("Using MD5 hashing algorithm", output_md5)
            
            # Test with SHA256
            sys.argv = ['file_matcher.py', self.test_dir1, self.test_dir2, '--hash', 'sha256']
            
            f = io.StringIO()
            with redirect_stdout(f):
                main()
                
            output_sha256 = f.getvalue()
            self.assertIn("Using SHA256 hashing algorithm", output_sha256)
            
        finally:
            # Restore original sys.argv
            sys.argv = original_argv
    
    def test_fast_mode_option(self):
        """Test the fast mode command-line option."""
        # Save original sys.argv
        original_argv = sys.argv.copy()
        
        try:
            # Test with fast mode enabled
            sys.argv = ['file_matcher.py', self.test_dir1, self.test_dir2, '--fast']
            
            f = io.StringIO()
            with redirect_stdout(f):
                main()
                
            output = f.getvalue()
            self.assertIn("Fast mode enabled", output)
            
        finally:
            # Restore original sys.argv
            sys.argv = original_argv
    
    def test_verbose_mode_option(self):
        """Test the verbose mode command-line option."""
        # Save original sys.argv
        original_argv = sys.argv.copy()
        
        try:
            # Test with verbose mode enabled
            sys.argv = ['file_matcher.py', self.test_dir1, self.test_dir2, '--verbose']
            
            f = io.StringIO()
            with redirect_stdout(f):
                main()
                
            output = f.getvalue()
            
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
            sys.argv = ['file_matcher.py', self.test_dir1, self.test_dir2, '--verbose', '--summary']
            
            f = io.StringIO()
            with redirect_stdout(f):
                main()
                
            output = f.getvalue()
            
            # Should still show verbose progress with summary output
            self.assertIn("Verbose mode enabled", output)
            self.assertIn("Processing", output)
            self.assertIn("Matched files summary:", output)
            
        finally:
            # Restore original sys.argv
            sys.argv = original_argv


if __name__ == "__main__":
    unittest.main() 