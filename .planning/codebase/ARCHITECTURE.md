# Architecture

**Analysis Date:** 2026-01-19

## Pattern Overview

**Overall:** Single-module CLI tool with functional design

**Key Characteristics:**
- Single-file implementation (`file_matcher.py`) containing all core logic
- Pure functions with explicit parameters (no hidden state)
- Hash-based file comparison using content addressing
- Recursive directory traversal with error resilience

## Layers

**CLI Layer:**
- Purpose: Parse arguments, configure logging, invoke core logic, format output
- Location: `file_matcher.py` (lines 248-342, `main()` function)
- Contains: Argument parsing, logging setup, output formatting
- Depends on: Core Layer
- Used by: Entry point (`__main__` block)

**Core Layer:**
- Purpose: File hashing and directory comparison logic
- Location: `file_matcher.py` (lines 24-245)
- Contains: Hash computation, directory indexing, match detection
- Depends on: Standard library (hashlib, pathlib, os)
- Used by: CLI Layer, Tests

## Data Flow

**Directory Comparison Flow:**

1. `main()` parses CLI arguments and validates directories
2. `find_matching_files()` orchestrates the comparison
3. `index_directory()` recursively scans each directory
4. `get_file_hash()` computes content hash for each file
5. For large files in fast mode, `get_sparse_hash()` samples file positions
6. `find_matching_files()` computes set intersection of hashes
7. Results returned as `(matches, unmatched1, unmatched2)` tuple
8. `main()` formats and prints results

**State Management:**
- No persistent state; each run is independent
- Directory indices are in-memory `defaultdict(list)` structures
- Hash maps: `{content_hash: [file_paths]}`

## Key Abstractions

**File Hash:**
- Purpose: Content-addressable identifier for file comparison
- Examples: MD5 or SHA-256 hex digest strings
- Pattern: Computed on-demand, not cached

**Directory Index:**
- Purpose: Map content hashes to file paths within a directory
- Examples: `{"abc123...": ["/path/to/file1.txt", "/path/to/file2.txt"]}`
- Pattern: `defaultdict(list)` populated via recursive traversal

**Match Result:**
- Purpose: Files with identical content across two directories
- Examples: `{hash: ([files_from_dir1], [files_from_dir2])}`
- Pattern: Dictionary with hash keys and file list tuples

## Entry Points

**CLI Entry Point:**
- Location: `file_matcher.py` line 341-342 (`if __name__ == "__main__"`)
- Triggers: Direct execution (`python file_matcher.py`) or installed command (`filematcher`)
- Responsibilities: Call `main()` and return exit code

**Package Entry Point:**
- Location: `pyproject.toml` line 30 (`filematcher = "file_matcher:main"`)
- Triggers: Running `filematcher` command after `pip install`
- Responsibilities: Invoke `main()` function

**Test Entry Point:**
- Location: `run_tests.py`
- Triggers: Running `python3 run_tests.py`
- Responsibilities: Discover and execute all tests in `tests/`

## Error Handling

**Strategy:** Catch and log errors, continue processing remaining files

**Patterns:**
- File access errors (`PermissionError`, `OSError`) are caught in `index_directory()`, logged via `logger.error()`, and skipped
- Invalid arguments (non-directory paths) cause early exit with return code 1
- Invalid hash algorithm raises `ValueError` (programming error, not user input)

## Cross-Cutting Concerns

**Logging:** Module-level `logger = logging.getLogger(__name__)` with configurable level (INFO default, DEBUG in verbose mode). Status messages use `logger.info()`/`logger.debug()`. Program results use `print()`.

**Validation:** Directory existence checked in `main()` before processing. File readability checked implicitly during hash computation.

**Authentication:** Not applicable (local filesystem tool)

---

*Architecture analysis: 2026-01-19*
