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
# Install via pip (recommended)
pip install .
filematcher <master_dir> <duplicate_dir>

# Or run directly without installing
python file_matcher.py <master_dir> <duplicate_dir>

# For development (editable install)
pip install -e .
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
# Basic comparison (finds all files with identical content)
filematcher dir1 dir2

# Equivalent to above (compare is the default action)
filematcher dir1 dir2 --action compare

# Only show files with identical content but different names
filematcher dir1 dir2 --different-names-only

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

### Target Directory Mode

Use `--target-dir` to create links in a different location instead of replacing files in dir2. This is useful for creating a deduplicated copy while preserving the original dir2:

```bash
# Create hardlinks in /backup instead of modifying dir2
filematcher dir1 dir2 --action hardlink --target-dir /backup --execute

# Create symlinks in a new location
filematcher dir1 dir2 --action symlink --target-dir /links --execute
```

**How it works:**
1. For each duplicate in dir2, computes the relative path from dir2
2. Creates the link at the same relative path under target-dir (creating subdirectories as needed)
3. Deletes the original file in dir2

**Example:**
```
Before:
  dir1/file.txt (master)
  dir2/subdir/dup.txt (duplicate)

After --target-dir /backup:
  dir1/file.txt (master, unchanged)
  dir2/subdir/dup.txt (deleted)
  /backup/subdir/dup.txt (hardlink to master)
```

**Notes:**
- Only works with `--action hardlink` or `--action symlink`
- Target directory must exist
- Nested directory structure from dir2 is preserved in target

## Command-Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--show-unmatched` | `-u` | Display files with no content match |
| `--hash` | `-H` | Hash algorithm: `md5` (default) or `sha256` |
| `--summary` | `-s` | Show counts instead of file lists |
| `--fast` | `-f` | Fast mode for large files (>100MB) |
| `--verbose` | `-v` | Show per-file progress |
| `--different-names-only` | `-d` | Only report files with identical content but different names |
| `--action` | `-a` | Action: `compare` (default), `hardlink`, `symlink`, or `delete` |
| `--execute` | | Execute changes (default: preview only) |
| `--yes` | `-y` | Skip confirmation prompt |
| `--log` | `-l` | Custom audit log path |
| `--fallback-symlink` | | Use symlink if hardlink fails |
| `--target-dir` | `-t` | Create links in this directory instead of dir2 (hardlink/symlink only) |
| `--json` | `-j` | Output results in JSON format for scripting |
| `--quiet` | `-q` | Suppress progress messages and headers (data and errors still shown) |

## JSON Output

Use `--json` or `-j` to get machine-readable JSON output for scripting and automation.

### Basic Usage

```bash
# Compare mode with JSON output
filematcher dir1 dir2 --json

# Action mode preview with JSON
filematcher dir1 dir2 --action hardlink --json

# Execute with JSON output (requires --yes for non-interactive mode)
filematcher dir1 dir2 --action hardlink --execute --yes --json
```

### Schema (Compare Mode)

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string | Execution time (RFC 3339 format) |
| `directories.dir1` | string | First directory path (absolute) |
| `directories.dir2` | string | Second directory path (absolute) |
| `hashAlgorithm` | string | Hash algorithm used ("md5" or "sha256") |
| `matches` | array | Groups of files with matching content |
| `matches[].hash` | string | Content hash for the group |
| `matches[].filesDir1` | array | File paths from dir1 (sorted) |
| `matches[].filesDir2` | array | File paths from dir2 (sorted) |
| `unmatchedDir1` | array | Unmatched files in dir1 (with --show-unmatched) |
| `unmatchedDir2` | array | Unmatched files in dir2 (with --show-unmatched) |
| `summary.matchCount` | number | Number of unique content hashes with matches |
| `summary.matchedFilesDir1` | number | Files with matches in dir1 |
| `summary.matchedFilesDir2` | number | Files with matches in dir2 |
| `metadata` | object | Per-file metadata (with --verbose) |
| `metadata[path].sizeBytes` | number | File size in bytes |
| `metadata[path].modified` | string | Last modified time (RFC 3339) |

### Schema (Action Mode)

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string | Execution time (RFC 3339) |
| `mode` | string | "preview" or "execute" |
| `action` | string | "hardlink", "symlink", or "delete" |
| `directories.master` | string | Master directory path (absolute) |
| `directories.duplicate` | string | Duplicate directory path (absolute) |
| `warnings` | array | Warning messages (e.g., multiple files in master with same content) |
| `duplicateGroups` | array | Groups of duplicates |
| `duplicateGroups[].masterFile` | string | Master file path (preserved) |
| `duplicateGroups[].duplicates` | array | Duplicate file objects |
| `duplicateGroups[].duplicates[].path` | string | Duplicate file path |
| `duplicateGroups[].duplicates[].sizeBytes` | number | File size in bytes |
| `duplicateGroups[].duplicates[].action` | string | Action to apply |
| `duplicateGroups[].duplicates[].crossFilesystem` | boolean | True if on different filesystem than master |
| `duplicateGroups[].duplicates[].targetPath` | string | Target path when using --target-dir (optional) |
| `statistics.groupCount` | number | Number of duplicate groups |
| `statistics.duplicateCount` | number | Total duplicate files |
| `statistics.masterCount` | number | Number of master files |
| `statistics.spaceSavingsBytes` | number | Bytes that would be/were saved |
| `statistics.crossFilesystemCount` | number | Files that cannot be hardlinked (cross-fs) |

**Additional fields when `--execute` is used:**

| Field | Type | Description |
|-------|------|-------------|
| `execution.successCount` | number | Number of successful operations |
| `execution.failureCount` | number | Number of failed operations |
| `execution.skippedCount` | number | Number of skipped operations |
| `execution.spaceSavedBytes` | number | Actual bytes saved |
| `execution.logPath` | string | Path to the audit log file |
| `execution.failures` | array | Failed operation details |
| `execution.failures[].path` | string | File that failed |
| `execution.failures[].error` | string | Error message |

### jq Examples

```bash
# List all matching file pairs (first file from each directory)
filematcher dir1 dir2 --json | jq -r '.matches[] | "\(.filesDir1[0]) <-> \(.filesDir2[0])"'

# Get count of matching groups
filematcher dir1 dir2 --json | jq '.summary.matchCount'

# List all matched files from dir1
filematcher dir1 dir2 --json | jq -r '.matches[].filesDir1[]'

# Get total space that would be saved by hardlinking
filematcher dir1 dir2 --action hardlink --json | jq '.statistics.spaceSavingsBytes'

# List only duplicate file paths (files to be replaced/deleted)
filematcher dir1 dir2 --action hardlink --json | jq -r '.duplicateGroups[].duplicates[].path'

# Get human-readable space savings (bytes to MB)
filematcher dir1 dir2 --action hardlink --json | jq '.statistics.spaceSavingsBytes / 1048576 | "\(.) MB"'

# Filter duplicates larger than 1MB
filematcher dir1 dir2 --action hardlink --json | \
  jq '[.duplicateGroups[].duplicates[] | select(.sizeBytes > 1048576)]'

# List master files and their duplicate counts
filematcher dir1 dir2 --action hardlink --json | \
  jq -r '.duplicateGroups[] | "\(.masterFile): \(.duplicates | length) duplicates"'

# Get execution results summary
filematcher dir1 dir2 --action hardlink --execute --yes --json | \
  jq '{success: .execution.successCount, failed: .execution.failureCount, saved: .execution.spaceSavedBytes}'
```

### Flag Interactions

| Flags | Behavior |
|-------|----------|
| `--json --summary` | Summary statistics only, matches array still populated but no verbose metadata |
| `--json --verbose` | Includes per-file metadata (size, modified time) in `metadata` object |
| `--json --show-unmatched` | Includes `unmatchedDir1` and `unmatchedDir2` arrays with file paths |
| `--json --execute` | Requires `--yes` flag (no interactive prompts in JSON mode) |
| `--json --action` | Outputs action mode schema instead of compare mode schema |

**Notes:**
- All file paths in JSON output are absolute paths
- All lists (matches, files, duplicates) are sorted for deterministic output
- Logger/progress messages go to stderr, JSON goes to stdout
- Timestamps use RFC 3339 format with timezone (e.g., `2026-01-23T10:30:00+00:00`)

## Output Formats

### Default Output

```
Compare mode: dir1 vs dir2
Found 2 duplicate groups (3 files, 0 B reclaimable)

[MASTER] /path/dir1/file1.txt
    [DUPLICATE] /path/dir2/different_name.txt

--- Statistics ---
Duplicate groups: 2
Total files with matches: 3
```

Use `--verbose` to see hash details:

```
[MASTER] /path/dir1/file1.txt
    [DUPLICATE] /path/dir2/different_name.txt
  Hash: e853edac47...
```

### Action Mode Output

When `--action` is specified, output shows the action that would be taken:

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
| `compare` | Compare only, no modifications (default when `--action` is not specified) |
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

## Output Streams

File Matcher follows Unix conventions for output streams:

- **stdout**: Data output (match groups, statistics, JSON)
- **stderr**: Progress messages, status updates, errors

This enables clean piping:

```bash
# Pipe only data to grep
filematcher dir1 dir2 | grep "pattern"

# Redirect data to file, see progress on terminal
filematcher dir1 dir2 > matches.txt

# Suppress all progress with --quiet
filematcher dir1 dir2 --quiet | wc -l
```

Use `--quiet` to suppress progress messages entirely while still outputting data and errors:

```bash
# Quiet mode for scripting - only data output, no progress
filematcher dir1 dir2 --quiet

# Combine with --json for clean machine-readable output
filematcher dir1 dir2 --json --quiet
```

### Color Output

File Matcher supports colored output to highlight key information:
- **Green**: Master files (protected, preserved)
- **Yellow**: Duplicate files (candidates for action)
- **Cyan**: Headers and statistics
- **Bold Yellow**: PREVIEW MODE banner

Color behavior:
- **Automatic**: Color enabled when output is a terminal (TTY), disabled when piped
- `--color` - Force color output (useful for `less -R` or colored logs)
- `--no-color` - Disable color output

Environment variables:
- `NO_COLOR` - Set to any value to disable color (standard: https://no-color.org/)
- `FORCE_COLOR` - Set to any value to enable color in non-TTY contexts (CI systems)

Flag precedence (last wins):
```bash
# --no-color wins (specified last)
filematcher dir1 dir2 --color --no-color

# --color wins (specified last)
filematcher dir1 dir2 --no-color --color
```

Note: JSON output (`--json`) never includes color codes regardless of flags.

## Testing

```bash
# Run all tests (228 tests)
python3 run_tests.py

# Run specific test module
python3 -m tests.test_actions
python3 -m tests.test_safe_defaults
python3 -m tests.test_master_directory
```

## Package Structure

File Matcher is organized as a Python package:

```
filematcher/
├── cli.py           # Command-line interface and main()
├── colors.py        # TTY-aware color output
├── hashing.py       # MD5/SHA-256 content hashing
├── filesystem.py    # Filesystem helpers
├── actions.py       # Action execution and audit logging
├── formatters.py    # Text and JSON output formatters
└── directory.py     # Directory indexing and matching
```

The `file_matcher.py` script remains for backward compatibility and re-exports all public symbols from the package.

## Requirements

- Python 3.9+
- No external dependencies

## License

MIT
