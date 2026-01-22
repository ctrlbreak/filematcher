# File Matcher

A Python CLI utility that finds files with identical content across two directory hierarchies and optionally deduplicates them using hard links, symbolic links, or deletion.

## Features

- Find files with identical content across two directories
- Compare using MD5 or SHA-256 content hashing
- Fast mode with sparse sampling for large files (>100MB)
- **Deduplicate** by replacing duplicates with hard links, symbolic links, or deleting them
- Safe by default: preview changes before executing
- Audit logging of all modifications
- Pure Python standard library (no external dependencies)

## Installation

```bash
pip install -e .
# Or just run directly:
python file_matcher.py <dir1> <dir2>
```

## Quick Start

```bash
# Find matching files
filematcher dir1 dir2

# Preview deduplication (safe - no changes made)
filematcher dir1 dir2 --action hardlink

# Execute deduplication
filematcher dir1 dir2 --action hardlink --execute
```

## Usage

### Finding Duplicate Files

```bash
# Basic comparison
filematcher dir1 dir2

# Show files with no matches
filematcher dir1 dir2 --show-unmatched

# Summary counts only
filematcher dir1 dir2 --summary

# Use SHA-256 instead of MD5
filematcher dir1 dir2 --hash sha256

# Fast mode for large files
filematcher dir1 dir2 --fast

# Verbose progress output
filematcher dir1 dir2 --verbose
```

### Deduplicating Files

To deduplicate, specify an action. The first directory is the master (files here are preserved):

```bash
# Preview hard link deduplication (default: preview only)
filematcher dir1 dir2 --action hardlink

# Preview symbolic link deduplication
filematcher dir1 dir2 --action symlink

# Preview deletion of duplicates
filematcher dir1 dir2 --action delete
```

To actually execute the changes, add `--execute`:

```bash
# Execute with confirmation prompt
filematcher dir1 dir2 --action hardlink --execute

# Execute without prompt (for scripts)
filematcher dir1 dir2 --action hardlink --execute --yes

# Execute with custom log file
filematcher dir1 dir2 --action hardlink --execute --log changes.log
```

### Cross-Filesystem Support

Hard links cannot span filesystems. Use `--fallback-symlink` to automatically use symbolic links when hard links fail:

```bash
filematcher dir1 dir2 --action hardlink --fallback-symlink --execute
```

## Command-Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--show-unmatched` | `-u` | Display files with no content match |
| `--hash` | `-H` | Hash algorithm: `md5` (default) or `sha256` |
| `--summary` | `-s` | Show counts instead of file lists |
| `--fast` | `-f` | Fast mode for large files (>100MB) |
| `--verbose` | `-v` | Show per-file progress |
| `--action` | `-a` | Action: `hardlink`, `symlink`, or `delete` (first directory is master) |
| `--execute` | | Execute changes (default: preview only) |
| `--yes` | `-y` | Skip confirmation prompt |
| `--log` | `-l` | Custom audit log path |
| `--fallback-symlink` | | Use symlink if hardlink fails |

## Output Formats

### Default Output

```
Found 2 hashes with matching files:

Hash: e853edac47...
  Files in dir1:
    /path/dir1/file1.txt
  Files in dir2:
    /path/dir2/different_name.txt
```

### Action Mode Output

When `--action` is specified, output shows which files are masters vs duplicates (first directory is master):

```
[MASTER] /path/dir1/file1.txt (23 B)
    [WOULD HARDLINK] /path/dir2/different_name.txt
```

### Preview Statistics

```
=== PREVIEW MODE - Use --execute to apply changes ===

...file listings...

Duplicate groups: 3
Duplicate files: 5
Space to be reclaimed: 1.2 MB

Use --execute to apply changes
```

## Actions

| Action | Description |
|--------|-------------|
| `hardlink` | Replace duplicate with hard link to master (same inode, saves space) |
| `symlink` | Replace duplicate with symbolic link to master (points to master path) |
| `delete` | Delete duplicate file (irreversible) |

**Safety features:**
- Preview by default (must add `--execute` to modify files)
- Confirmation prompt before execution
- Audit log records all changes with timestamps
- Atomic operations using temp files prevent corruption

## Audit Logging

All modifications are logged with timestamps:

```
=== File Matcher Audit Log ===
Timestamp: 2026-01-20T10:30:00
Directories: /path/dir1, /path/dir2
Master: /path/dir1
Action: hardlink
Flags: --execute --yes
==============================

[2026-01-20T10:30:01] HARDLINK /path/dir2/dup.txt -> /path/dir1/master.txt (1.2 KB) [e853ed...] OK
[2026-01-20T10:30:01] HARDLINK /path/dir2/dup2.txt -> /path/dir1/master.txt (1.2 KB) [e853ed...] OK

==============================
Completed: 2 successful, 0 failed, 0 skipped
Space reclaimed: 2.4 KB
==============================
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (or user aborted) |
| 1 | All operations failed |
| 2 | Invalid arguments |
| 3 | Partial success (some operations failed) |

## Testing

```bash
# Run all tests
python3 run_tests.py

# Run specific test module
python3 -m tests.test_actions
python3 -m tests.test_safe_defaults
python3 -m tests.test_master_directory
```

## Requirements

- Python 3.9+
- No external dependencies

## License

MIT
