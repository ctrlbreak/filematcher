#!/usr/bin/env python3

import unittest
import sys

if __name__ == "__main__":
    # Discover and run all tests in the current directory
    test_suite = unittest.defaultTestLoader.discover('.', pattern='test_*.py')
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Return non-zero exit code if tests failed
    sys.exit(not result.wasSuccessful()) 