#!/usr/bin/env python3

import unittest
import sys
import os
import shutil
from pathlib import Path

if __name__ == "__main__":
    print("==================================================")
    print("Starting File Matcher tests")
    print("==================================================")

    # Set up test log directory - clear at START so logs are inspectable after
    logs_dir = Path(__file__).parent / '.logs_test'
    if logs_dir.exists():
        shutil.rmtree(logs_dir)
    logs_dir.mkdir(exist_ok=True)
    os.environ['FILEMATCHER_LOG_DIR'] = str(logs_dir.resolve())
    print(f"Test logs will be written to: {logs_dir}")

    # Discover and run all tests in the tests directory
    test_suite = unittest.defaultTestLoader.discover('./tests', pattern='test_*.py')
    
    # Run tests with verbose output
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    print("\n==================================================")
    print(f"Tests complete: {result.testsRun} tests run")
    print(f"Failures: {len(result.failures)}, Errors: {len(result.errors)}, Skipped: {len(result.skipped)}")
    print("==================================================")
    
    # Return non-zero exit code if tests failed
    sys.exit(not result.wasSuccessful()) 