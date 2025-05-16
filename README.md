# File Matcher

A Python utility script that finds files with identical content but different names across two directory hierarchies.

## Features

- Recursively scans directories and subdirectories
- Compares file content using selectable hashing algorithms (MD5 or SHA-256)
- Identifies files with identical content but different names
- Can detect and report files with no content matches in either directory
- Efficiently handles large files by reading in chunks
- Provides both detailed listing and summary count modes

## Usage

```bash
# Basic usage (uses MD5 by default)
python file_matcher.py <directory1> <directory2>

# Show unmatched files as well
python file_matcher.py <directory1> <directory2> --show-unmatched

# Use SHA-256 for more robust hashing (slower)
python file_matcher.py <directory1> <directory2> --hash sha256

# Use summary mode to show counts only
python file_matcher.py <directory1> <directory2> --summary

# Combined options
python file_matcher.py <directory1> <directory2> --show-unmatched --hash sha256 --summary
```

## Command-line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--show-unmatched` | `-u` | Display files with no content match |
| `--hash` | `-H` | Select hash algorithm: `md5` (default, faster) or `sha256` (more secure) |
| `--summary` | `-s` | Show only counts instead of listing all files |

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
```

## Testing

The project includes comprehensive unit tests to validate all functionality:

```bash
# Run all unit tests
python run_tests.py

# Run specific test files
python test_file_matcher.py
python test_real_directories.py

# Run a specific test
python -m unittest test_file_matcher.TestFileMatcher.test_large_file_chunking
```

The unit tests cover:

- File hashing with various algorithms
- Directory indexing
- Finding matching files across directories
- Handling large files with chunking
- Nested directory processing

## How it Works

1. The script indexes each directory, computing hashes for all files
2. Files are matched based on identical content hashes
3. Files with matching content but different names are identified
4. Optionally, files with no content matches can be identified 