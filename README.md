# File Matcher

A Python utility script that finds files with identical content but different names across two directory hierarchies.

## Features

- Recursively scans directories and subdirectories
- Compares file content using selectable hashing algorithms (MD5 or SHA-256)
- Identifies files with identical content but different names
- Can detect and report files with no content matches in either directory
- Efficiently handles large files by reading in chunks
- Provides both detailed listing and summary count modes
- Offers a fast mode for processing very large files quickly
- Verbose mode shows processing progress for each file

## Usage

```bash
# Basic usage (uses MD5 by default)
python file_matcher.py <directory1> <directory2>

# Show unmatched files as well
python file_matcher.py <directory1> <directory2> --show-unmatched

# Use SHA-256 for more robust hashing (slower)
python file_matcher.py <directory1> <directory2> --hash sha256

# Use fast mode for large files
python file_matcher.py <directory1> <directory2> --fast

# Show verbose progress output
python file_matcher.py <directory1> <directory2> --verbose

# Combined options
python file_matcher.py <directory1> <directory2> --show-unmatched --hash sha256 --summary --fast --verbose
```

## Command-line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--show-unmatched` | `-u` | Display files with no content match |
| `--hash` | `-H` | Select hash algorithm: `md5` (default, faster) or `sha256` (more secure) |
| `--summary` | `-s` | Show only counts instead of listing all files |
| `--fast` | `-f` | Enable fast mode for large files (>100MB) |
| `--verbose` | `-v` | Show detailed progress for each file being processed |

## Fast Mode

The fast mode provides significant performance improvements when comparing large files (like videos, images, or datasets) by using smart sampling techniques:

1. **File Size Comparison**: Files with different sizes can never be identical, so they are quickly rejected
2. **Sparse Block Sampling**: Instead of hashing the entire file, samples are taken from:
   - The beginning of the file
   - The end of the file
   - The middle of the file
   - The 1/4 and 3/4 positions
3. **Size-Aware Hashing**: File size is incorporated into the hash to further improve accuracy

For files smaller than 100MB, the normal full-content hashing is used. This provides a good balance between speed and accuracy, making it particularly useful for comparing large media libraries.

## Example Output

### Detailed Mode (Default)

When run with the `--show-unmatched` flag in detailed mode, the script provides comprehensive output:

```
Found 3 hashes with matching files:

Hash: e853edac47...
  Files in dir1:
    /path/to/dir1/file1.txt
  Files in dir2:
    /path/to/dir2/different_name.txt

Hash: 42848197f3...
  Files in dir1:
    /path/to/dir1/file2.txt
  Files in dir2:
    /path/to/dir2/also_different_name.txt

Files with no content matches:
==============================

Unique files in dir1 (1):
  /path/to/dir1/unique_file.txt

Unique files in dir2 (1):
  /path/to/dir2/another_unique.txt
```

## Verbose Mode

The verbose mode (`--verbose` or `-v`) provides detailed progress information during file processing, which is especially useful when working with large directory trees or many files:

```bash
python file_matcher.py test_dir1 test_dir2 --verbose
```

**Verbose mode output includes:**
- Total number of files found in each directory
- Progress counter showing current file being processed
- Individual file names and their sizes in human-readable format
- Summary of unique content hashes found after processing each directory

**Example verbose output:**
```
Using MD5 hashing algorithm
Verbose mode enabled: Showing progress for each file
Found 5 files to process in test_dir1
[1/5] Processing file1.txt (23 B)
[2/5] Processing file2.txt (23 B)
[3/5] Processing large_file.mkv (2.3 GB)
[4/5] Processing document.pdf (456.2 KB)
[5/5] Processing image.jpg (1.2 MB)
Completed indexing test_dir1: 5 unique file contents found
```

This mode is particularly helpful for:
- Monitoring progress when processing large directory trees
- Identifying which files are taking longer to process
- Debugging issues with specific files
- Understanding the distribution of file sizes in your directories

### Summary Mode

When run with the `--summary` flag, the script produces a compact count-based output:

```
Matched files summary:
  Unique content hashes with matches: 3
  Files in dir1 with matches in dir2: 4
  Files in dir2 with matches in dir1: 3

Unmatched files summary:
  Files in dir1 with no match: 2
  Files in dir2 with no match: 1
```

## Examples

The repository includes test directories that you can use to try out the script:

### Simple Test Directories (test_dir1, test_dir2)
```bash
# Basic usage with test directories
python file_matcher.py test_dir1 test_dir2

# With unmatched files
python file_matcher.py test_dir1 test_dir2 --show-unmatched

# Summary mode
python file_matcher.py test_dir1 test_dir2 --summary
```

### Complex Test Directories (complex_test/dir1, complex_test/dir2)
These directories contain various matching patterns including multiple matches, asymmetric matches, and nested directories:

```bash
# Detailed view of complex matching patterns
python file_matcher.py complex_test/dir1 complex_test/dir2

# Summary of complex matching patterns
python file_matcher.py complex_test/dir1 complex_test/dir2 --summary --show-unmatched

# Using fast mode with complex directories
python file_matcher.py complex_test/dir1 complex_test/dir2 --fast
```

## Testing

The project includes comprehensive unit tests to validate all functionality, organized into specific test areas:

```bash
# Run all unit tests
python3 run_tests.py

# Run tests from a specific category
python3 -m tests.test_file_hashing
python3 -m tests.test_fast_mode
python3 -m tests.test_directory_operations
python3 -m tests.test_cli

# Run a specific test
python3 -m unittest tests.test_fast_mode.TestFastMode.test_sparse_hash_fast_mode
```

### Test Coverage

The unit tests are organized into logical modules by functionality:

#### Test Organization
- **`tests/test_file_hashing.py`**: Basic file hash calculations and large file handling
- **`tests/test_fast_mode.py`**: Fast mode and sparse block sampling for large files
- **`tests/test_directory_operations.py`**: Directory scanning and file matching functionality 
- **`tests/test_real_directories.py`**: Comprehensive tests using real test directories with complex matching patterns
- **`tests/test_cli.py`**: Command-line interface and output formatting (including verbose mode)
- **`tests/test_base.py`**: Common base test class with shared setup/teardown functionality

#### Core Functionality Tests
- **File Hashing**: Verifies that identical content produces identical hashes and different content produces different hashes
- **Directory Indexing**: Tests the creation and structure of file indexes for directories
- **Match Finding**: Validates that files with identical content but different names are correctly identified
- **File Processing**: Confirms that nested directories and subfolders are properly processed

#### Advanced Feature Tests
- **Large File Handling**: Tests that large files (8MB+) are correctly hashed when processed in chunks
- **Fast Mode**: Validates the sparse sampling approach used for large files in fast mode
- **Summary Mode**: Ensures the correct counts are displayed in summary output
- **Hash Algorithms**: Tests both MD5 and SHA-256 hash algorithms

#### Environment Tests
- **Temporary Test Environment**: Creates controlled test directories to validate functionality
- **Actual Test Directories**: Uses the real test directories included in the repository
- **Complex Matching Patterns**: Tests multiple file matches, asymmetric matches, and nested directories

The test suite is designed to catch regressions and ensure reliability across different operating environments and file patterns.

## How it Works

1. The script indexes each directory, computing hashes for all files
2. Files are matched based on identical content hashes
3. Files with matching content but different names are identified
4. Optionally, files with no content matches can be identified
5. In fast mode, large files are compared using intelligent sampling instead of full content hashing 