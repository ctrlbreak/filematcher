# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

File Matcher (v1.5.1) is a Python CLI utility that finds files with identical content across two directory hierarchies and can deduplicate them using hardlinks, symlinks, or deletion. It uses content hashing (MD5 or SHA-256) to identify matches and supports a "fast mode" for large files using sparse sampling. The first directory (`dir1`) is the implicit **master directory** - files there are preserved while duplicates in `dir2` are candidates for action.

## Development Setup

```bash
pip install -e .  # Install in editable mode
```

## Commands

### Running the tool
```bash
python file_matcher.py <master_dir> <duplicate_dir> [options]
# Or after pip install:
filematcher <master_dir> <duplicate_dir> [options]
```

**Comparison options:**
- `--show-unmatched/-u` - Display files with no content match
- `--hash/-H md5|sha256` - Hash algorithm (default: md5)
- `--summary/-s` - Show summary statistics only
- `--fast/-f` - Fast mode using sparse sampling for large files
- `--verbose/-v` - Show additional details (file sizes, hashes)
- `--different-names-only/-d` - Only show matches with different filenames

**Action options:**
- `--action/-a compare|hardlink|symlink|delete` - Action to perform (default: compare)
- `--execute` - Execute actions (default is preview/dry-run)
- `--yes/-y` - Skip confirmation prompt
- `--log/-l PATH` - Custom audit log path
- `--fallback-symlink` - Fall back to symlink for cross-filesystem hardlinks
- `--target-dir/-t PATH` - Create links in this directory instead of dir2 (hardlink/symlink only)

**Output options:**
- `--json/-j` - JSON output format
- `--quiet/-q` - Suppress non-essential output
- `--color` - Force color output
- `--no-color` - Disable color output

### Running tests
```bash
# Run all tests (308 tests)
python3 run_tests.py

# Run a specific test module
python3 -m tests.test_file_hashing
python3 -m tests.test_fast_mode
python3 -m tests.test_directory_operations
python3 -m tests.test_cli
python3 -m tests.test_real_directories
python3 -m tests.test_actions
python3 -m tests.test_json_output
python3 -m tests.test_color_output
python3 -m tests.test_master_directory
python3 -m tests.test_safe_defaults
python3 -m tests.test_output_unification
python3 -m tests.test_determinism
python3 -m tests.test_formatters
python3 -m tests.test_interactive
python3 -m tests.test_error_handling

# Run a single test
python3 -m unittest tests.test_fast_mode.TestFastMode.test_sparse_hash_fast_mode
```

Test logs are written to `.logs_test/` (controlled by `FILEMATCHER_LOG_DIR` env var).

## Architecture

### Core Module: `file_matcher.py`

Single-file implementation with type hints (requires Python 3.9+, uses `from __future__ import annotations`). Uses module-level `logger` for status/debug output; program results use `print()`.

**Key sections:**

#### Color System
- `ColorMode` enum - AUTO, NEVER, ALWAYS modes
- `ColorConfig` class - Determines color output based on mode, environment (NO_COLOR, FORCE_COLOR), and TTY detection
- Helper functions: `green()`, `yellow()`, `red()`, `cyan()`, `dim()`, `bold()`

#### Output Formatters (Strategy Pattern)
- `ActionFormatter` ABC - Abstract base class for output formatting
- `TextActionFormatter` - Human-readable colored text output
- `JsonActionFormatter` - Machine-readable JSON output (accumulator pattern)

#### Hashing Functions
- `get_file_hash()` - Computes file hash, delegates to `get_sparse_hash()` for large files in fast mode
- `get_sparse_hash()` - Samples file at 5 positions (start, 1/4, middle, 3/4, end) plus file size for fast hashing (>100MB threshold)

#### Directory Operations
- `index_directory()` - Recursively indexes all files, returns dict mapping hash → list of file paths
- `find_matching_files()` - Main comparison logic: indexes both directories, finds common hashes, identifies unmatched files
- `select_master_file()` - Selects master file from candidates (prefers master directory)

#### Action Execution
- `safe_replace_with_link()` - Atomic replace with rollback on failure
- `execute_action()` - Execute single action (hardlink/symlink/delete) with logging
- `execute_all_actions()` - Process all duplicate groups with progress tracking
- `determine_exit_code()` - Returns appropriate exit code based on success/failure counts

#### Filesystem Helpers
- `is_hardlink_to()` - Check if two paths are hardlinks (same inode)
- `is_symlink_to()` - Check if path is symlink pointing to target
- `check_cross_filesystem()` - Detect files on different filesystems
- `get_device_id()` - Get device ID for cross-filesystem detection

#### Audit Logging
- `create_audit_logger()` - Creates timestamped audit log file
- `write_log_header()` / `write_log_footer()` - Log session boundaries
- `log_operation()` - Log individual file operations

#### CLI
- `main()` - Entry point, returns 0 on success, 1 on error, 2 on partial failure

### Test Structure: `tests/`

`tests/__init__.py` handles `sys.path` setup. Tests inherit from `BaseFileMatcherTest` (`test_base.py`) which provides:
- Temporary directory setup/teardown
- Pre-created test file structure with various matching patterns

Test modules organized by functionality:
- `test_file_hashing.py` - Hash computation
- `test_fast_mode.py` - Sparse sampling for large files
- `test_directory_operations.py` - Directory scanning, matching, hardlink detection
- `test_cli.py` - CLI argument parsing and output formatting
- `test_real_directories.py` - Integration tests using fixture directories
- `test_actions.py` - Action execution (hardlink/symlink/delete), rollback, audit logging
- `test_json_output.py` - JSON output format validation
- `test_color_output.py` - Color output and NO_COLOR/FORCE_COLOR handling
- `test_master_directory.py` - Master directory selection and output formatting
- `test_safe_defaults.py` - Preview mode (dry-run) behavior
- `test_output_unification.py` - Consistent output across modes
- `test_determinism.py` - Deterministic output ordering

### Test Directories

The repo includes test fixtures:
- `test_dir1/`, `test_dir2/` - Simple test cases
- `complex_test/dir1/`, `complex_test/dir2/` - Complex matching patterns (multiple matches, nested dirs)

### Planning Documentation

Development planning docs in `.planning/`:
- `codebase/` - Architecture, conventions, testing documentation
- `phases/` - Feature development phases (01-09+)
- `milestones/` - Version roadmaps and requirements
- `research/` - Technical research notes

## Git Conventions

- Do not add Claude attribution (e.g., `Co-Authored-By: Claude`) to commit messages

## Release Workflow

When completing a milestone and releasing a new version:

1. **Update version numbers** in all 3 files:
   - `pyproject.toml` (`version = "X.Y.Z"`)
   - `filematcher/__init__.py` (`__version__ = "X.Y.Z"`)
   - `file_matcher.py` (`Version: X.Y.Z`)

2. **Add changelog entry** to `CHANGELOG.md` with the new version section

3. **Commit** the version bump and changelog

4. **Run release script**:
   ```bash
   python3 create_release.py X.Y.Z --dry-run  # Preview first
   python3 create_release.py X.Y.Z            # Create release
   ```

The script will:
- Verify version consistency across files
- Extract release notes from CHANGELOG.md
- Create and push git tag
- Create GitHub release with extracted notes

GitHub automatically generates source archives (zip/tar.gz) from the tag.
