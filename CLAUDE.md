# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

File Matcher is a Python CLI utility that finds files with identical content but different names across two directory hierarchies. It uses content hashing (MD5 or SHA-256) to identify matches and supports a "fast mode" for large files using sparse sampling.

## Development Setup

```bash
pip install -e .  # Install in editable mode
```

## Commands

### Running the tool
```bash
python file_matcher.py <directory1> <directory2> [options]
# Or after pip install:
filematcher <directory1> <directory2> [options]
```

Options: `--show-unmatched/-u`, `--hash/-H md5|sha256`, `--summary/-s`, `--fast/-f`, `--verbose/-v`

### Running tests
```bash
# Run all tests
python3 run_tests.py

# Run a specific test module
python3 -m tests.test_file_hashing
python3 -m tests.test_fast_mode
python3 -m tests.test_directory_operations
python3 -m tests.test_cli
python3 -m tests.test_real_directories

# Run a single test
python3 -m unittest tests.test_fast_mode.TestFastMode.test_sparse_hash_fast_mode
```

## Architecture

### Core Module: `file_matcher.py`

Single-file implementation with type hints (requires Python 3.9+, uses `from __future__ import annotations`). Uses module-level `logger` for status/debug output; program results use `print()`.

Key functions:

- `get_file_hash()` - Computes file hash, delegates to `get_sparse_hash()` for large files in fast mode
- `get_sparse_hash()` - Samples file at 5 positions (start, 1/4, middle, 3/4, end) plus file size for fast hashing of large files (>100MB threshold)
- `index_directory()` - Recursively indexes all files, returns dict mapping hash → list of file paths
- `find_matching_files()` - Main comparison logic: indexes both directories, finds common hashes, identifies unmatched files
- `format_file_size()` - Human-readable size formatting for verbose mode
- `main()` - CLI entry point, returns 0 on success, 1 on error

### Test Structure: `tests/`

`tests/__init__.py` handles `sys.path` setup for imports. Tests inherit from `BaseFileMatcherTest` (`test_base.py`) which provides:
- Temporary directory setup/teardown
- Pre-created test file structure with various matching patterns

Test modules are organized by functionality:
- `test_file_hashing.py` - Hash computation
- `test_fast_mode.py` - Sparse sampling for large files
- `test_directory_operations.py` - Directory scanning and matching
- `test_cli.py` - CLI argument parsing and output formatting (uses `unittest.mock.patch` for `sys.argv`)
- `test_real_directories.py` - Integration tests using `test_dir1/`, `test_dir2/`, `complex_test/`

### Test Directories

The repo includes test fixtures:
- `test_dir1/`, `test_dir2/` - Simple test cases
- `complex_test/dir1/`, `complex_test/dir2/` - Complex matching patterns (multiple matches, nested dirs)
