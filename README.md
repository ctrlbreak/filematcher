# File Matcher

Deduplicate files by content, not name. Reclaim space with hardlinks/symlinks while preserving alternate filenames. Preview-first safety, audit logging. Built for media libraries.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

## Use Cases

- **Media Libraries** — Deduplicate movies/TV shows across Plex, Sonarr, Radarr directories
- **Backups** — Find and link identical files across backup drives to save space
- **Downloads** — Clean up duplicate downloads while keeping organized copies

## Features

- **Content-based matching** — Find duplicates by hash, not filename
- **Preserve filenames** — Duplicates become links but keep their original names and paths
- **Preview-first safety** — See changes before executing (requires `--execute` flag)
- **Interactive mode** — Confirm each action with y/n/a/q prompts
- **Audit logging** — Full trail of all modifications
- **Fast mode** — Sparse sampling for large files (>100MB)
- **No dependencies** — Pure Python standard library

## Installation

```bash
pip install .                # Install
filematcher dir1 dir2        # Run

# Or run directly
python file_matcher.py dir1 dir2

# Development
pip install -e .
```

## Quick Start

```bash
# Find matching files
filematcher dir1 dir2

# Preview deduplication (safe - no changes made)
filematcher dir1 dir2 --action hardlink

# Execute deduplication (interactive confirmation)
filematcher dir1 dir2 --action hardlink --execute

# Execute without prompts (for scripts)
filematcher dir1 dir2 --action hardlink --execute --yes
```

## Usage

### Finding Duplicates

```bash
filematcher dir1 dir2                    # Basic comparison
filematcher dir1 dir2 --different-names-only  # Only different filenames
filematcher dir1 dir2 --show-unmatched   # Include unmatched files
filematcher dir1 dir2 --summary          # Counts only
filematcher dir1 dir2 --fast             # Fast mode for large files
filematcher dir1 dir2 --hash sha256      # Use SHA-256 instead of MD5
```

### Deduplicating

The first directory is the **master** (files preserved). Duplicates in dir2 are replaced/deleted.

```bash
# Preview (default - no changes)
filematcher dir1 dir2 --action hardlink
filematcher dir1 dir2 --action symlink
filematcher dir1 dir2 --action delete

# Execute
filematcher dir1 dir2 --action hardlink --execute
filematcher dir1 dir2 --action hardlink --execute --yes    # Skip prompts
filematcher dir1 dir2 --action hardlink --execute --log changes.log
```

### Interactive Mode

When running `--execute` without `--yes`, you're prompted for each group:

```
[1/5] Hardlink this group? [y/n/a/q]:
```

- `y` — Execute on this group
- `n` — Skip this group
- `a` — Execute all remaining without prompting
- `q` — Quit immediately

### Advanced Options

```bash
# Cross-filesystem: fall back to symlink when hardlink fails
filematcher dir1 dir2 --action hardlink --fallback-symlink --execute

# Target directory: create links in a new location, preserving duplicate filenames
# e.g., dir2/movies/film.mkv → /backup/movies/film.mkv (linked to master)
filematcher dir1 dir2 --action hardlink --target-dir /backup --execute
```

## Command-Line Reference

| Option | Short | Description |
|--------|-------|-------------|
| `--action` | `-a` | Action: `compare` (default), `hardlink`, `symlink`, `delete` |
| `--execute` | | Execute changes (default: preview only) |
| `--yes` | `-y` | Skip confirmation prompts |
| `--show-unmatched` | `-u` | Show files with no matches |
| `--different-names-only` | `-d` | Only show matches with different filenames |
| `--summary` | `-s` | Show counts only |
| `--fast` | `-f` | Fast mode for large files (>100MB) |
| `--hash` | `-H` | Hash algorithm: `md5` (default), `sha256` |
| `--verbose` | `-v` | Show detailed progress |
| `--log` | `-l` | Custom audit log path |
| `--fallback-symlink` | | Use symlink if hardlink fails (cross-filesystem) |
| `--target-dir` | `-t` | Create links in new location (preserves dir2 structure/names) |
| `--json` | `-j` | JSON output (see [JSON_SCHEMA.md](JSON_SCHEMA.md)) |
| `--quiet` | `-q` | Suppress progress messages |
| `--color` | | Force color output |
| `--no-color` | | Disable color output |

## JSON Output

Use `--json` for machine-readable output. See [JSON_SCHEMA.md](JSON_SCHEMA.md) for full schema.

```bash
# Get space savings
filematcher dir1 dir2 --action hardlink --json | jq '.statistics.spaceSavingsBytes'

# List duplicate paths
filematcher dir1 dir2 --action hardlink --json | jq -r '.duplicateGroups[].duplicates[].path'

# Execution summary
filematcher dir1 dir2 --action hardlink --execute --yes --json | \
  jq '{success: .execution.successCount, failed: .execution.failureCount}'
```

Note: `--json --execute` requires `--yes` (no interactive prompts in JSON mode).

## Actions

| Action | Description |
|--------|-------------|
| `compare` | Find matches only, no modifications (default) |
| `hardlink` | Replace duplicate with hard link to master (saves space) |
| `symlink` | Replace duplicate with symbolic link to master |
| `delete` | Delete duplicate file (irreversible) |

## Audit Logging

All modifications are logged:

```
=== File Matcher Audit Log ===
Timestamp: 2026-01-20T10:30:00
Action: hardlink
==============================
[2026-01-20T10:30:01] HARDLINK /dir2/dup.txt -> /dir1/master.txt (1.2 KB) OK
==============================
Completed: 2 successful, 0 failed
Space reclaimed: 2.4 KB
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | All operations failed |
| 2 | Invalid arguments or partial failure |
| 130 | User quit (q or Ctrl+C) |

## Output Options

**Streams:** Data goes to stdout, progress/errors to stderr. Use `--quiet` to suppress progress.

**Colors:** Auto-enabled for TTY, disabled when piped. Override with `--color` or `--no-color`. Respects `NO_COLOR` and `FORCE_COLOR` environment variables.

## Testing

```bash
python3 run_tests.py              # Run all 308 tests
python3 -m tests.test_actions     # Run specific module
```

## Package Structure

```
filematcher/
├── cli.py           # Command-line interface
├── colors.py        # TTY-aware color output
├── hashing.py       # MD5/SHA-256 hashing
├── filesystem.py    # Filesystem helpers
├── actions.py       # Action execution, audit logging
├── formatters.py    # Text and JSON formatters
└── directory.py     # Directory indexing
```

## Requirements

- Python 3.9+
- No external dependencies

## License

MIT

---

See [CHANGELOG.md](CHANGELOG.md) for version history and breaking changes.
