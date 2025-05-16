#!/usr/bin/env python3

import unittest
import sys
import os

if __name__ == "__main__":
    print("==================================================")
    print("Running tests from tests directory")
    print("==================================================")
    
    # Discover and run all tests in the tests directory
    test_suite = unittest.defaultTestLoader.discover('.', pattern='test_*.py')
    
    # Run tests with verbose output
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    print("\n==================================================")
    print(f"Tests complete: {result.testsRun} tests run")
    print(f"Failures: {len(result.failures)}, Errors: {len(result.errors)}, Skipped: {len(result.skipped)}")
    print("==================================================")
    
    # Return non-zero exit code if tests failed
    sys.exit(not result.wasSuccessful()) 