# Testing Patterns

**Analysis Date:** 2025-01-19

## Test Framework

**Runner:**
- `unittest` (Python standard library)
- Config: `pyproject.toml` specifies `testpaths = ["tests"]` for pytest compatibility

**Assertion Library:**
- `unittest` built-in assertions (`assertEqual`, `assertNotEqual`, `assertTrue`, `assertIn`, etc.)

**Run Commands:**
```bash
python3 run_tests.py              # Run all tests with verbose output
python3 -m tests.test_file_hashing  # Run specific test module
python3 -m unittest tests.test_fast_mode.TestFastMode.test_sparse_hash_fast_mode  # Run single test
```

## Test File Organization

**Location:**
- Separate `tests/` directory at project root
- Not co-located with source code

**Naming:**
- Files: `test_*.py` prefix (e.g., `test_cli.py`, `test_fast_mode.py`)
- Classes: `Test*` prefix with PascalCase (e.g., `TestCLI`, `TestFastMode`)
- Methods: `test_*` prefix with snake_case (e.g., `test_get_file_hash`, `test_summary_mode`)

**Structure:**
```
tests/
├── __init__.py           # sys.path setup for imports
├── test_base.py          # Base test class with fixtures
├── test_file_hashing.py  # Hash computation tests
├── test_fast_mode.py     # Sparse sampling tests
├── test_directory_operations.py  # Directory scanning tests
├── test_cli.py           # CLI argument and output tests
└── test_real_directories.py      # Integration tests
```

## Test Structure

**Suite Organization:**
```python
#!/usr/bin/env python3

import os
import unittest

from file_matcher import get_file_hash, format_file_size
from tests.test_base import BaseFileMatcherTest


class TestFileHashing(BaseFileMatcherTest):
    """Tests for basic file hashing functionality."""

    def test_get_file_hash(self):
        """Test file hashing function."""
        # Arrange: use self.test_dir1, self.test_dir2 from base class
        file1 = os.path.join(self.test_dir1, "file1.txt")
        file2 = os.path.join(self.test_dir2, "different_name.txt")

        # Act & Assert
        self.assertEqual(get_file_hash(file1), get_file_hash(file2))


if __name__ == "__main__":
    unittest.main()
```

**Patterns:**
- One test class per functional area
- Tests inherit from `BaseFileMatcherTest` for fixture access
- Each test method has a docstring describing what it tests
- `if __name__ == "__main__": unittest.main()` at end of each file

## Base Test Class

**Location:** `tests/test_base.py`

**Provides:**
```python
class BaseFileMatcherTest(unittest.TestCase):
    """Base test class with common setup/teardown methods."""

    def setUp(self):
        """Set up test environment with temporary directories."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_dir1 = os.path.join(self.temp_dir, "test_dir1")
        self.test_dir2 = os.path.join(self.temp_dir, "test_dir2")
        # Creates directories and sample files...

    def tearDown(self):
        """Clean up temporary directories after tests."""
        shutil.rmtree(self.temp_dir)
```

**Available Fixtures:**
- `self.temp_dir` - Root temporary directory
- `self.test_dir1` - First test directory with files
- `self.test_dir2` - Second test directory with files
- Pre-created files with various matching patterns:
  - Same content, different names
  - Different content, different names
  - Same name, different content
  - Nested files in subdirectories

## Mocking

**Framework:** `unittest.mock`

**Patterns:**
```python
from unittest.mock import patch

class TestCLI(BaseFileMatcherTest):
    def test_hash_algorithm_option(self):
        """Test the hash algorithm command-line option."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1, self.test_dir2]):
            output = self.run_main_with_args([])
            self.assertIn("Using MD5 hashing algorithm", output)
```

**What to Mock:**
- `sys.argv` for CLI argument testing
- Function defaults when testing threshold behavior

**What NOT to Mock:**
- Actual file operations (use real temp files)
- Hash functions (test actual behavior)
- Directory traversal (test with real directories)

## Fixtures and Factories

**Test Data:**
```python
# In setUp():
# Files with identical content but different names
with open(os.path.join(self.test_dir1, "file1.txt"), "w") as f:
    f.write("This is file content A\n")
with open(os.path.join(self.test_dir2, "different_name.txt"), "w") as f:
    f.write("This is file content A\n")

# Large files for fast mode testing
random.seed(42)  # For reproducibility
with open(large_file_path, 'wb') as f:
    for _ in range(chunks):
        data = bytes(random.getrandbits(8) for _ in range(chunk_size))
        f.write(data)
```

**Location:**
- Fixtures created in `setUp()` methods
- Real test directories at project root: `test_dir1/`, `test_dir2/`, `complex_test/`

## Coverage

**Requirements:** None enforced

**View Coverage:**
```bash
# No coverage tool configured; can use:
python3 -m coverage run run_tests.py
python3 -m coverage report
```

## Test Types

**Unit Tests:**
- `test_file_hashing.py` - Tests individual functions (`get_file_hash`, `format_file_size`)
- `test_fast_mode.py` - Tests sparse hashing algorithm
- Scope: Single function behavior with controlled inputs

**Integration Tests:**
- `test_directory_operations.py` - Tests `index_directory` and `find_matching_files` together
- `test_real_directories.py` - Tests against real project test directories
- Scope: Multiple functions working together

**CLI Tests:**
- `test_cli.py` - Tests command-line interface and output formatting
- Uses `redirect_stdout` to capture output
- Scope: End-to-end from argument parsing to output

**E2E Tests:**
- `test_real_directories.py` with real `test_dir1/`, `test_dir2/`, `complex_test/` directories
- Tests skip gracefully if directories don't exist

## Common Patterns

**Capturing stdout:**
```python
import io
from contextlib import redirect_stdout

def run_main_with_args(self, args: list[str]) -> str:
    """Helper to run main() with given args and capture stdout."""
    f = io.StringIO()
    with redirect_stdout(f):
        main()
    return f.getvalue()
```

**Async Testing:**
- Not applicable (synchronous codebase)

**Error Testing:**
```python
def test_invalid_hash_algorithm(self):
    with self.assertRaises(ValueError):
        get_file_hash(filepath, "invalid_algo")
```

**Skip Conditions:**
```python
def test_with_real_directories(self):
    if not os.path.isdir(self.test_dir1):
        self.skipTest("Test directories not found")
```

**Testing Modified Files:**
```python
# Create identical files
shutil.copy(large_file_path, duplicate_file_path)

# Verify identical hashes
hash1 = get_file_hash(large_file_path)
hash2 = get_file_hash(duplicate_file_path)
self.assertEqual(hash1, hash2)

# Modify one file
with open(duplicate_file_path, 'r+b') as f:
    f.seek(file_size - 100)
    f.write(b'MODIFIED_END')

# Verify different hashes
modified_hash = get_file_hash(duplicate_file_path)
self.assertNotEqual(hash1, modified_hash)
```

## Test Runner

**Location:** `run_tests.py`

**Pattern:**
```python
#!/usr/bin/env python3
import unittest
import sys

if __name__ == "__main__":
    test_suite = unittest.defaultTestLoader.discover('./tests', pattern='test_*.py')
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    sys.exit(not result.wasSuccessful())
```

**Output:**
- Runs with verbosity=2 (shows each test name and result)
- Prints summary at end (tests run, failures, errors, skipped)
- Returns non-zero exit code on failure

## Test Categories by Module

**`test_file_hashing.py`:**
- `test_get_file_hash` - Basic hash computation
- `test_large_file_chunking` - 8MB file handling
- `test_format_file_size` - Size formatting (B, KB, MB, GB, TB)

**`test_fast_mode.py`:**
- `test_sparse_hash_fast_mode` - 12MB file sparse sampling
- `test_fast_mode_in_directory_comparison` - Fast mode in full workflow

**`test_directory_operations.py`:**
- `test_index_directory` - Directory indexing
- `test_find_matching_files` - Match detection
- `test_with_real_directories` - Real directory test

**`test_cli.py`:**
- `test_summary_mode` - `--summary` flag output
- `test_detailed_output_mode` - Default output format
- `test_hash_algorithm_option` - `--hash` flag
- `test_fast_mode_option` - `--fast` flag
- `test_verbose_mode_option` - `--verbose` flag

**`test_real_directories.py`:**
- `test_file_hashing` - Real files hashing
- `test_directory_indexing` - Real directory indexing
- `test_matching_files` - Real match detection
- `test_nested_files` - Subdirectory handling
- `test_complex_matching_patterns` - Asymmetric matches

---

*Testing analysis: 2025-01-19*
