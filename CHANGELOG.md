# Changelog

All notable changes to the File Matcher project will be documented in this file.

## [1.4.0] - 2026-01-28

### Changed
- **Package Structure**: Refactored from single-file `file_matcher.py` to `filematcher/` package
- **Module Organization**: Code split into focused modules (cli, colors, hashing, filesystem, actions, formatters, directory)
- **Entry Point**: `filematcher` command now uses `filematcher.cli:main` via pyproject.toml

### Added
- **Circular Import Test**: Automated test verifies no circular imports in package structure

### Technical Details
- 7 modules in filematcher/ package: cli.py, colors.py, hashing.py, filesystem.py, actions.py, formatters.py, directory.py
- Full backward compatibility: `python file_matcher.py` and `from file_matcher import` still work
- file_matcher.py is now a thin wrapper that re-exports from filematcher package
- 218 unit tests (217 original + 1 circular import test), all passing
- Python 3.9+ required

## [1.3.0] - 2026-01-23

### Changed
- **Unified Action Model**: Compare mode is now `--action compare` (the default), unifying all modes under a single code path
- **Simplified Codebase**: Removed 513 lines of duplicate code by eliminating separate CompareFormatter hierarchy

### Technical Details
- All modes (compare, hardlink, symlink, delete) now use the same ActionFormatter code path
- `--action compare` is equivalent to not specifying `--action` (backward compatible)
- file_matcher.py reduced from 2,951 to 2,438 lines
- 198 unit tests, all passing

## [1.2.0] - 2026-01-23

### Added
- **JSON Output**: Machine-readable output with `--json` flag for scripting and automation
- **Color Output**: TTY-aware colored output highlighting masters (green), duplicates (yellow), and statistics (cyan)
- **Quiet Mode**: `--quiet` flag suppresses progress messages while preserving data output
- **Output Streams**: Progress to stderr, data to stdout (Unix convention)

### Features
- **`--json`**: Output results in JSON format with stable schema
- **`--quiet`**: Suppress progress and status messages
- **`--color`**: Force colored output (useful for `less -R`)
- **`--no-color`**: Disable colored output
- **`NO_COLOR`** environment variable: Standard way to disable color (https://no-color.org/)
- **`FORCE_COLOR`** environment variable: Enable color in CI systems

### Changed
- Unified output structure between compare mode and action mode
- Statistics footer now appears in all modes
- Hierarchical output format: master file unindented, duplicates indented
- Deterministic output ordering for reproducible results

### Technical Details
- Formatter abstraction layer (ActionFormatter ABC hierarchy)
- JSON schema documented in README with jq examples
- 16-color ANSI codes for maximum terminal compatibility
- 198 unit tests covering all functionality

## [1.1.0] - 2026-01-20

### Added
- **Master Directory Support**: Designate one directory as master with `--master` flag
- **Deduplication Actions**: Replace duplicates with hard links, symbolic links, or delete them
- **Preview-by-Default**: Safe execution model requires `--execute` flag to modify files
- **Confirmation Prompt**: Interactive Y/N confirmation before execution
- **Audit Logging**: Comprehensive logging with timestamps via `--log` flag
- **Cross-Filesystem Detection**: Automatic detection with `--fallback-symlink` option
- **Non-Interactive Mode**: `--yes` flag for scripted execution

### Features
- **`--master`**: Protect files in master directory from modification
- **`--action`**: Choose deduplication method (hardlink, symlink, delete)
- **`--execute`**: Enable actual file modifications (preview-only by default)
- **`--yes`**: Skip confirmation prompt for automation
- **`--log`**: Custom audit log path with ISO 8601 timestamps
- **`--fallback-symlink`**: Use symlinks when hardlinks fail (cross-filesystem)

### Technical Details
- Atomic file operations using temp-rename pattern for safety
- Rollback on failure prevents data loss
- Exit codes: 0 (success), 1 (all failed), 2 (validation error), 3 (partial success)
- 114 unit tests covering all functionality
- 1,374 lines of Python with comprehensive error handling

## [1.0.0] - 2025-08-20

### Added
- Core file matching functionality using content hashing
- Support for MD5 and SHA-256 hash algorithms
- Directory indexing and recursive file scanning
- Fast mode for large files (>100MB) using sparse sampling
- Summary mode for quick overview of matches
- Detailed output mode showing all file paths
- Comprehensive unit test suite with modular organization
- Support for nested directory structures
- Large file handling with chunked reading (4KB chunks)

### Features
- **File Hashing**: MD5 and SHA-256 algorithms with configurable selection
- **Fast Mode**: Efficient comparison of large files using sparse block sampling
- **Summary Mode**: Quick count of matches and unmatched files
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **No Dependencies**: Uses only Python standard library

### Technical Details
- Sparse sampling samples from beginning, middle, 1/4, 3/4, and end of large files
- Incorporates file size into hash for additional confidence
- Efficient memory usage with chunked file reading
- Comprehensive error handling and user feedback

## [0.1.0] - Initial Development

### Added
- Basic file matching functionality
- Directory traversal and indexing
- Simple hash-based comparison
