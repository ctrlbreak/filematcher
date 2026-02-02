#!/usr/bin/env python3
"""
File Matcher - Find files with identical content across two directory trees.

This script is preserved for backward compatibility.
The implementation has moved to the filematcher package.

Usage (all equivalent):
    python file_matcher.py <args>
    python -m filematcher <args>
    filematcher <args>  # after pip install

Version: 1.5.1
"""

from __future__ import annotations

# Re-export everything from the filematcher package for backward compatibility
# This allows `from file_matcher import get_file_hash, find_matching_files` to work
from filematcher import *  # noqa: F401, F403

# Import main explicitly for the entry point
from filematcher.cli import main

if __name__ == "__main__":
    import sys
    sys.exit(main())