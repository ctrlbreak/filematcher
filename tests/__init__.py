"""
Tests for file_matcher.py functionality.
"""

import os
import sys

# Add parent directory to path so test modules can import file_matcher
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) 