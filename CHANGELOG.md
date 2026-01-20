# Changelog

All notable changes to the File Matcher project will be documented in this file.

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
