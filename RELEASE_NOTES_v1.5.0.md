# File Matcher v1.5.0 Release Notes

**Release Date:** 2026-01-31

## Overview

File Matcher v1.5.0 introduces interactive execute mode with per-file confirmation prompts. This makes deduplication safer by letting you review each action before it happens. The release also includes a restructured JSON schema (v2.0) for better machine parsing.

## What's New

### Interactive Execute Mode

Running `--execute` now prompts for each duplicate group by default:

```bash
filematcher dir1 dir2 --action hardlink --execute
```

```
=== EXECUTE MODE ===
Action: hardlink | Groups: 5 | Files: 8 | Space: 1.2 MB

[MASTER] /path/dir1/file1.txt (1.2 KB)
    [WILL HARDLINK] /path/dir2/copy.txt

[1/5] Hardlink this group? [y/n/a/q]: y
✓ Confirmed - hardlinked 1 file

[MASTER] /path/dir1/file2.txt (2.3 KB)
    [WILL HARDLINK] /path/dir2/another.txt

[2/5] Hardlink this group? [y/n/a/q]:
```

**Response options:**
| Key | Action |
|-----|--------|
| `y` | Execute action on this group, continue to next |
| `n` | Skip this group, continue to next |
| `a` | Execute on all remaining groups without prompting |
| `q` | Stop immediately, show summary |

### Batch Mode (Scripts)

For non-interactive use, add `--yes` to skip all prompts:

```bash
filematcher dir1 dir2 --action hardlink --execute --yes
```

### Enhanced Execution Summary

The final summary now distinguishes user decisions from execution results:

```
=== Execution Complete ===
User confirmed: 3 groups
User skipped: 1 group
Succeeded: 3
Failed: 0
Space freed: 3.6 KB (3,686 bytes)
Audit log: filematcher_20260131_120000.log
```

### Exit Code 130

User quit (`q` response or Ctrl+C) now returns exit code 130, following Unix convention (128 + SIGINT).

## Breaking Changes

### JSON Schema v2.0

JSON output has been restructured with a unified header object. This is a **breaking change** for scripts parsing JSON output.

**Metadata moved to header:**
```json
// OLD (v1.x)
{"timestamp": "2026-01-31T12:00:00Z", "mode": "preview", ...}

// NEW (v2.0)
{
  "header": {
    "name": "filematcher",
    "version": "2.0",
    "timestamp": "2026-01-31T12:00:00Z",
    "mode": "preview",
    "hashAlgorithm": "md5",
    "directories": {
      "master": "/path/dir1",
      "duplicate": "/path/dir2"
    }
  },
  ...
}
```

**Directory keys renamed:**
- OLD: `directories.dir1`, `directories.dir2`
- NEW: `header.directories.master`, `header.directories.duplicate`

**Unmatched field names:**
- OLD: `unmatchedDir1`, `unmatchedDir2`
- NEW: `unmatchedMaster`, `unmatchedDuplicate`

### Flag Validation

These flag combinations now require `--yes`:
- `--json --execute` (JSON output incompatible with prompts)
- `--quiet --execute` (can't suppress output and prompt)
- Non-TTY stdin with `--execute` (piped input can't provide responses)

## Technical Details

- 308 unit tests, all passing
- 5 phases, 10 plans implemented
- ActionFormatter ABC extended with interactive prompt methods
- New test files: test_formatters.py, test_interactive.py, test_error_handling.py
- Python 3.9+ required
- No external dependencies

## Upgrading from v1.4.0

**Interactive mode:** If you have scripts using `--execute`, they will now prompt for input. Add `--yes` to restore batch behavior:

```bash
# OLD (worked silently after Y/N prompt)
filematcher dir1 dir2 --action hardlink --execute

# NEW (for scripts - skip all prompts)
filematcher dir1 dir2 --action hardlink --execute --yes
```

**JSON consumers:** Update parsing to use the new header structure:

```bash
# OLD
jq '.timestamp' output.json

# NEW
jq '.header.timestamp' output.json
```

## Links

- [Full Documentation](README.md)
- [Changelog](CHANGELOG.md)
- [License](LICENSE)
