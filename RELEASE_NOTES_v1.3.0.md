# File Matcher v1.3.0 Release Notes

**Release Date:** 2026-01-23

## Overview

File Matcher v1.3.0 completes the output rationalisation work started in v1.2.0 and unifies the codebase. This release adds JSON output for scripting, colored terminal output, quiet mode, and simplifies the internal architecture by unifying all modes under a single code path.

## New Features

### JSON Output (v1.2.0)

Machine-readable JSON output for scripting and automation:

```bash
# Compare mode with JSON
filematcher dir1 dir2 --json

# Action mode with JSON
filematcher dir1 dir2 --action hardlink --json

# Execute with JSON (requires --yes)
filematcher dir1 dir2 --action hardlink --execute --yes --json
```

Use with jq for powerful filtering:

```bash
# Get space savings
filematcher dir1 dir2 --action hardlink --json | jq '.statistics.spaceSavingsBytes'

# List all duplicate paths
filematcher dir1 dir2 --action hardlink --json | jq -r '.duplicateGroups[].duplicates[].path'
```

### Color Output (v1.2.0)

TTY-aware colored output highlights key information:
- **Green**: Master files (protected)
- **Yellow**: Duplicate files (action candidates)
- **Cyan**: Headers and statistics
- **Bold Yellow**: PREVIEW MODE banner

Color is automatic (enabled in terminals, disabled in pipes). Control with:

```bash
# Force color (useful for less -R)
filematcher dir1 dir2 --color

# Disable color
filematcher dir1 dir2 --no-color
```

Environment variables supported:
- `NO_COLOR` — Disable color (https://no-color.org/)
- `FORCE_COLOR` — Enable color in CI systems

### Quiet Mode (v1.2.0)

Suppress progress messages while preserving data output:

```bash
# Quiet mode for scripting
filematcher dir1 dir2 --quiet

# Combine with JSON for clean output
filematcher dir1 dir2 --json --quiet
```

### Stream Separation (v1.2.0)

Following Unix conventions:
- **stdout**: Data output (match groups, statistics, JSON)
- **stderr**: Progress messages, status updates, errors

```bash
# Pipe only data
filematcher dir1 dir2 | grep "pattern"

# Redirect data, see progress on terminal
filematcher dir1 dir2 > matches.txt
```

### Unified Action Model (v1.3.0)

Compare mode is now `--action compare`, unifying all modes:

```bash
# These are equivalent (compare is the default)
filematcher dir1 dir2
filematcher dir1 dir2 --action compare
```

All actions: `compare`, `hardlink`, `symlink`, `delete`

## New Command-Line Options

| Option | Description |
|--------|-------------|
| `--json`, `-j` | Output results in JSON format |
| `--quiet`, `-q` | Suppress progress messages |
| `--color` | Force colored output |
| `--no-color` | Disable colored output |
| `--action compare` | Explicit compare mode (default) |

## Changed Behavior

### Unified Output Structure
Compare mode and action mode now use identical output structure:
- Unified header format
- Summary line with group/file counts
- Hierarchical file display (master unindented, duplicates indented)
- Statistics footer in all modes

### Deterministic Output
All file lists are sorted for reproducible results across runs.

## Technical Details

- 2,438 lines of Python (reduced from 2,951 — 513 lines removed)
- 198 unit tests, all passing
- Single ActionFormatter hierarchy handles all modes
- Pure Python standard library (no external dependencies)
- Python 3.9+ required

## Upgrading from v1.1.0

v1.3.0 is fully backward compatible. All v1.1.0 commands work unchanged:
- Default behavior (no flags) produces same results
- All existing flags work as before
- `--master` flag still works but is optional (first directory is master by default)

New features are opt-in via `--json`, `--quiet`, `--color`, `--no-color` flags.

## Example Workflows

### Scripted Deduplication with JSON

```bash
#!/bin/bash
# Get space that would be saved
SAVINGS=$(filematcher backup main --action hardlink --json | jq '.statistics.spaceSavingsBytes')
echo "Would save $SAVINGS bytes"

# Execute if savings > 1MB
if [ "$SAVINGS" -gt 1048576 ]; then
  filematcher backup main --action hardlink --execute --yes --json > result.json
fi
```

### Quiet Pipeline

```bash
# Count duplicate groups silently
filematcher dir1 dir2 --quiet | grep -c "MASTER"

# Export to file with progress visible
filematcher dir1 dir2 --json > duplicates.json
```

### Colored Output in Pager

```bash
# View with color in less
filematcher dir1 dir2 --color | less -R
```

## Links

- [Full Documentation](README.md)
- [Changelog](CHANGELOG.md)
- [JSON Schema Documentation](README.md#json-output)
- [License](LICENSE)
