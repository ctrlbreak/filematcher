---
phase: 015
plan: 01
subsystem: interactive-ui
tags: [ansi, cursor-movement, tty, confirmation-status, line-wrapping]
completed: 2026-01-31
duration: ~30min
---

# Quick Task 015: Move Confirmation Status to Action Line - Summary

**One-liner:** ANSI cursor movement places checkmark/X at start of action line, handles line wrapping, clears prompt line.

## What Was Done

### Initial Implementation
- Added `lines_back` parameter to `format_confirmation_status()` for cursor movement
- ANSI escape codes (`\033[nA` up, `\033[nB` down) position status on action line

**Commits:** `7c83965`, `8908c4c`, `f434ab9`

### Fix: Cursor Offset for Prompt Line
- Changed calculation from `len(duplicates)` to `len(duplicates) + 1` to account for prompt line

**Commit:** `0f6e6f9`

### Fix: Handle Line Wrapping
- Added `_last_duplicate_rows` tracking to TextActionFormatter
- Uses `terminal_rows_for_line()` to calculate actual terminal rows for wrapped lines
- Formatter now internally tracks rows instead of receiving `lines_back` parameter
- Removed unused `lines_back` calculation from cli.py

**Commits:** `75493e7`, `acaf73e`

### Style: Cross Color
- Changed skip cross from yellow to red (checkmark stays green)

**Commit:** `61d5b03`

### Fix: Clear Prompt Line
- After showing status, cursor moves to prompt line and clears it
- Next group overwrites the prompt line instead of appearing below
- Removes extra blank line between groups

**Commit:** `324247d`

## Files Modified

| File | Changes |
|------|---------|
| `filematcher/formatters.py` | `_last_duplicate_rows` tracking, `terminal_rows_for_line()` usage, prompt line clearing |
| `filematcher/cli.py` | Removed unused `lines_back` calculation |
| `tests/test_formatters.py` | Updated tests for new cursor movement behavior |

## Verification

- All 308 tests pass
- Manual verification with short and long (wrapping) paths
- Prompt line properly cleared between groups

## Output Change

**Before:**
```
[1/2] MASTER: /path/master/a.txt
    WILL DELETE: /path/dup/a.txt
[1/2] Delete duplicate? [y/n/a/q] n
X

[2/2] MASTER: ...
```

**After:**
```
[1/2] MASTER: /path/master/a.txt
X   WILL DELETE: /path/dup/a.txt
[2/2] MASTER: ...
```

- Status symbol appears on action line (green checkmark / red cross)
- Prompt line cleared and overwritten by next group
- Works correctly with long paths that wrap in terminal
