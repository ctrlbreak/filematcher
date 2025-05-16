# File Matcher

A Python utility script that finds files with identical content but different names across two directory hierarchies.

## Features

- Recursively scans directories and subdirectories
- Compares file content using selectable hashing algorithms (MD5 or SHA-256)
- Identifies files with identical content but different names
- Can detect and report files with no content matches in either directory
- Efficiently handles large files by reading in chunks

## Usage

```bash
# Basic usage (uses MD5 by default)
python file_matcher.py <directory1> <directory2>

# Show unmatched files as well
python file_matcher.py <directory1> <directory2> --show-unmatched

# Use SHA-256 for more robust hashing (slower)
python file_matcher.py <directory1> <directory2> --hash sha256

# Combined options
python file_matcher.py <directory1> <directory2> --show-unmatched --hash sha256
```

## Command-line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--show-unmatched` | `-u` | Display files with no content match |
| `--hash` | `-H` | Select hash algorithm: `md5` (default, faster) or `sha256` (more secure) |

## Example Output

When run with the `--show-unmatched` flag, the script provides comprehensive output:

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

## Examples

The repository includes an example script (`example.sh`) and test directories with sample files to demonstrate the functionality:

```bash
./example.sh
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