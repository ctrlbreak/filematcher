# File Matcher v1.1.0 Release Notes

**Release Date:** 2026-01-20

## Overview

File Matcher v1.1.0 adds full file deduplication capability. You can now replace duplicate files with hard links, symbolic links, or delete them entirely—all with preview-by-default safety and comprehensive audit logging.

## New Features

### Master Directory Protection
Designate one directory as "master" using `--master`. Files in the master directory are never modified or deleted.

```bash
filematcher dir1 dir2 --master dir1 --action hardlink
```

### Deduplication Actions
Three ways to handle duplicates:
- **hardlink** — Replace duplicate with hard link to master (same inode, saves space)
- **symlink** — Replace duplicate with symbolic link to master
- **delete** — Remove duplicate file entirely (irreversible)

### Preview-by-Default Safety
Running with `--action` shows a preview of what would happen. No files are modified until you add `--execute`.

```bash
# Preview only (safe)
filematcher dir1 dir2 --master dir1 --action hardlink

# Actually execute
filematcher dir1 dir2 --master dir1 --action hardlink --execute
```

### Confirmation Prompt
Before execution, you'll see a confirmation prompt. Use `--yes` to skip for scripted use.

### Audit Logging
Every modification is logged with timestamps. Use `--log` for a custom log path.

```bash
filematcher dir1 dir2 --master dir1 --action hardlink --execute --log changes.log
```

### Cross-Filesystem Support
Hard links can't span filesystems. Use `--fallback-symlink` to automatically use symbolic links when hard links fail.

## New Command-Line Options

| Option | Description |
|--------|-------------|
| `--master`, `-m` | Master directory (files never modified) |
| `--action`, `-a` | Action: `hardlink`, `symlink`, or `delete` |
| `--execute` | Execute changes (default: preview only) |
| `--yes`, `-y` | Skip confirmation prompt |
| `--log`, `-l` | Custom audit log path |
| `--fallback-symlink` | Use symlink if hardlink fails |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (or user aborted) |
| 1 | All operations failed |
| 2 | Invalid arguments |
| 3 | Partial success (some failed) |

## Example Workflow

```bash
# 1. Find duplicates
filematcher photos_backup photos_main

# 2. Preview deduplication
filematcher photos_backup photos_main --master photos_main --action hardlink

# 3. Execute with logging
filematcher photos_backup photos_main --master photos_main --action hardlink --execute --log dedup.log
```

## Technical Details

- Atomic operations using temp-rename pattern (no data loss on failure)
- 1,374 lines of Python
- 114 unit tests, all passing
- Pure Python standard library (no external dependencies)
- Python 3.9+ required

## Upgrading from v1.0.0

v1.1.0 is fully backward compatible. All v1.0.0 commands work unchanged. The new deduplication features are opt-in via `--master` and `--action` flags.

## Links

- [Full Documentation](README.md)
- [Changelog](CHANGELOG.md)
- [License](LICENSE)
