# Changelog

All notable changes to the File Matcher project will be documented in this file.

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
