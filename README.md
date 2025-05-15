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

## Testing

The repository includes a test script (`run_tests.sh`) and test directories with sample files to demonstrate the functionality:

```bash
./run_tests.sh
```

## How it Works

1. The script indexes each directory, computing MD5 hashes for all files
2. Files are matched based on identical content hashes
3. Files with matching content but different names are identified
4. Optionally, files with no content matches can be identified 