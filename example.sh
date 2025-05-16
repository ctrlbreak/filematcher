#!/bin/bash

# Example script to demonstrate file_matcher.py usage with test directories
# This is NOT the unit test runner - for unit tests, use run_tests.py instead
#
# Usage: ./example.sh

# Set script directory as working directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Running file matcher examples..."
echo "================================"
echo ""

# Example 1: Default output with MD5 (matched files only)
echo "EXAMPLE 1: Default output with MD5 (matched files only)"
echo "------------------------------------------------------"
python3 file_matcher.py test_dir1 test_dir2

echo ""
echo "=============================="
echo ""

# Example 2: Including unmatched files with MD5
echo "EXAMPLE 2: Including unmatched files with MD5"
echo "------------------------------------------"
python3 file_matcher.py test_dir1 test_dir2 --show-unmatched

echo ""
echo "=============================="
echo ""

# Example 3: Using SHA-256 algorithm
echo "EXAMPLE 3: Using SHA-256 algorithm"
echo "--------------------------------"
python3 file_matcher.py test_dir1 test_dir2 --hash sha256

echo ""
echo "=============================="
echo "All examples completed!" 