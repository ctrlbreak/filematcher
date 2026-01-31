# Quick Task 014 Summary: Remove TTY Carriage Return from Group Display

**One-liner:** Removed TTY overwrite behavior so duplicate groups display sequentially instead of overwriting each other.

## What Was Done

### Task 1: Remove ANSI escape overwrite behavior
- Removed `_prev_group_row_count` instance variable from `TextActionFormatter.__init__`
- Simplified `format_duplicate_group()` method by removing:
  - `inline_progress` TTY detection logic
  - ANSI escape codes (`\033[A\033[K`) that cleared previous lines
  - `term_width` calculation using `shutil.get_terminal_size()`
  - `terminal_rows_for_line()` row counting
- Preserved group index prefix `[n/m]` display for all output (not just TTY)
- Hash display in verbose mode unchanged

### Task 2: Clean up unused imports
- Removed `import shutil` (was only used for `get_terminal_size()`)
- Removed `import sys` (was only used for `stdout.write/flush`)
- Removed `terminal_rows_for_line` from colors module import

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 | e8d4f8e | fix(quick-014): remove TTY carriage return overwrite behavior in group display |
| 2 | 9a9391b | chore(quick-014): remove unused imports from formatters.py |

## Files Modified

- `filematcher/formatters.py` - Simplified TextActionFormatter.format_duplicate_group()

## Verification

All success criteria verified:
- [x] Groups display sequentially in TTY mode (not overwriting)
- [x] Hash is displayed when --verbose flag is used
- [x] Interactive confirmation still shows inline status symbols (unchanged)
- [x] All 305 existing tests pass
- [x] No unused imports

## Deviations from Plan

None - plan executed exactly as written.

## Notes

- The `terminal_rows_for_line` function remains in `filematcher/colors.py` and is still exported via `filematcher/__init__.py` as part of the public API
- Tests for `terminal_rows_for_line` in `tests/test_color_output.py` still pass (function not removed from codebase)
- The group index prefix `[n/m]` is now always displayed (regardless of TTY status) which improves consistency

---
*Completed: 2026-01-31*
