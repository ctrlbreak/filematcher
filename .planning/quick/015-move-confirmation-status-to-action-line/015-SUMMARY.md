---
phase: 015
plan: 01
subsystem: interactive-ui
tags: [ansi, cursor-movement, tty, confirmation-status]
completed: 2026-01-31
duration: ~10min
---

# Quick Task 015: Move Confirmation Status to Action Line - Summary

**One-liner:** ANSI cursor movement places checkmark/X at start of action line instead of separate line after prompt.

## What Was Done

### Task 1: Add ANSI cursor movement to format_confirmation_status
- Added `lines_back` parameter to `format_confirmation_status()` method signature
- When `lines_back > 0`: Uses ANSI escape codes (`\033[nA` up, `\033[nB` down) to move cursor
- When `lines_back == 0`: Fallback mode prints status on current line (for testing/non-TTY)
- Updated ABC `ActionFormatter` and `JsonActionFormatter` signatures

**Commit:** `7c83965` feat(015): add ANSI cursor movement to format_confirmation_status

### Task 2: Pass duplicate count to format_confirmation_status
- Calculated `lines_back = len(duplicates)` for cursor positioning
- Added `+1` when verbose mode with file_hash (hash line shown after duplicates)
- Updated all 4 calls in `interactive_execute()`: confirm_all, 'y', 'n', 'a' branches

**Commit:** `8908c4c` feat(015): pass lines_back to format_confirmation_status in interactive_execute

### Task 3: Update tests for new behavior
- Updated existing tests to verify no ANSI codes with `lines_back=0`
- Added `test_format_confirmation_status_moves_cursor_up` - verifies ANSI sequences present
- Added `test_format_confirmation_status_cursor_movement_for_skipped` - X symbol with cursor
- Added `test_json_format_confirmation_status_ignores_lines_back` - JSON no-op preserved

**Commit:** `f434ab9` test(015): add tests for cursor movement in format_confirmation_status

## Files Modified

| File | Changes |
|------|---------|
| `filematcher/formatters.py` | Added `lines_back` param, ANSI cursor movement logic |
| `filematcher/cli.py` | Calculate and pass `lines_back` to format_confirmation_status |
| `tests/test_formatters.py` | Added 3 new tests for cursor movement |

## Verification

- All 308 tests pass (305 original + 3 new)
- Manual verification in TTY shows status on action line

## Output Change

**Before:**
```
[1/2] MASTER: /path/master/a.txt
    WILL DELETE: /path/dup/a.txt
[1/2] Delete duplicate? [y/n/a/q] n
X
```

**After:**
```
[1/2] MASTER: /path/master/a.txt
X   WILL DELETE: /path/dup/a.txt
[1/2] Delete duplicate? [y/n/a/q] n
```

## Deviations from Plan

None - plan executed exactly as written.
