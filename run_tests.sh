#!/bin/bash

# Script to test file_matcher.py with test directories
# Usage: ./run_tests.sh

# Set script directory as working directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Running file matcher tests..."
echo "=============================="
echo ""

# Run the file matcher script with test directories (matched files only)
echo "TEST 1: Default output (matched files only)"
echo "-------------------------------------------"
python3 file_matcher.py test_dir1 test_dir2

echo ""
echo "=============================="
echo ""

# Run the file matcher script including unmatched files
echo "TEST 2: Including unmatched files"
echo "--------------------------------"
python3 file_matcher.py test_dir1 test_dir2 --show-unmatched

echo ""
echo "=============================="
echo "All tests completed!" 