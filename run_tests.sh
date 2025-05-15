#!/bin/bash

# Script to test file_matcher.py with test directories
# Usage: ./run_tests.sh

# Set script directory as working directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Running file matcher tests..."
echo "=============================="
echo ""

# Test 1: Default output with MD5 (matched files only)
echo "TEST 1: Default output with MD5 (matched files only)"
echo "---------------------------------------------------"
python3 file_matcher.py test_dir1 test_dir2

echo ""
echo "=============================="
echo ""

# Test 2: Including unmatched files with MD5
echo "TEST 2: Including unmatched files with MD5"
echo "----------------------------------------"
python3 file_matcher.py test_dir1 test_dir2 --show-unmatched

echo ""
echo "=============================="
echo ""

# Test 3: Using SHA-256 algorithm
echo "TEST 3: Using SHA-256 algorithm"
echo "------------------------------"
python3 file_matcher.py test_dir1 test_dir2 --hash sha256

echo ""
echo "=============================="
echo "All tests completed!" 