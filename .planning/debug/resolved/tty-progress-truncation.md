---
status: resolved
trigger: "TTY inline progress mode truncates/overwrites output incorrectly with long file paths"
created: 2026-01-24T00:04:00Z
updated: 2026-01-24T00:20:00Z
---

## Current Focus

hypothesis: CONFIRMED - Root cause identified, fix implemented and verified
test: Full test suite (216 tests) + manual verification with long paths
expecting: All tests pass
next_action: Archive session and commit fix

## Symptoms

expected: Each duplicate group should show [n/m] MASTER line, then DUPLICATE lines, then Hash - with inline progress updating in place until the final group which stays visible
actual:
- Group numbers skip (336->337->340, etc)
- Lines truncated mid-output (path ends with partial text then next [n/m] starts on same line)
- Only the last group (366/366) shows DUPLICATE and Hash lines
- Earlier groups show only summarized MASTER line "(1 duplicates, X GB)"
errors: No error messages - visual corruption only
reproduction: Run filematcher on large directories (366 groups) with long file paths in TTY mode
started: Introduced in Quick 006 (inline progress feature)

## Eliminated

## Evidence

- timestamp: 2026-01-24T00:06:00Z
  checked: Lines 957-979 in file_matcher.py - inline progress cursor movement logic
  found: |
    Code uses simple loop: `for _ in range(self._prev_group_line_count): sys.stdout.write('\033[A')`
    The _prev_group_line_count is set to the number of logical lines printed (line_count += 1 per GroupLine)
    This does NOT account for terminal line wrapping - when a path exceeds terminal width, it wraps to multiple rows
    But cursor-up only moves up one terminal row, not one logical line
  implication: With long paths, fewer rows are cleared than were written, leaving residual text

- timestamp: 2026-01-24T00:07:00Z
  checked: Terminal width handling elsewhere in codebase
  found: |
    Lines 2194-2198 use shutil.get_terminal_size().columns for stderr progress
    The inline progress mode does NOT use terminal width - it assumes 1 line = 1 terminal row
  implication: The fix needs to calculate terminal rows per line using terminal width

- timestamp: 2026-01-24T00:08:00Z
  checked: render_group_line function (lines 234-266)
  found: |
    Returns fully formatted string with ANSI color codes embedded
    Need to calculate visible width (excluding ANSI codes) to determine wrapping
  implication: Must strip ANSI codes before measuring line length for wrap calculation

## Resolution

root_cause: |
  In TextActionFormatter.format_duplicate_group() lines 957-979, the inline TTY progress uses
  cursor-up escape sequences (\033[A) to clear previous output. The code tracks the number of
  logical lines printed (_prev_group_line_count) but cursor-up moves by terminal ROWS, not
  logical lines. When a line (typically file paths) exceeds terminal width, it wraps to
  multiple terminal rows. The cursor only moves up by the logical line count, leaving
  residual text from wrapped lines visible, causing the truncation/corruption observed.

  Example: A 200-char line on an 80-col terminal takes 3 rows. But code only moves up 1 row.

fix: |
  1. Added import re for ANSI stripping
  2. Added strip_ansi() function to remove ANSI escape sequences
  3. Added visible_len() function to get visible character count
  4. Added terminal_rows_for_line() function to calculate how many terminal rows a line occupies
  5. Modified TextActionFormatter.format_duplicate_group() to:
     - Get terminal width with shutil.get_terminal_size().columns
     - Track row_count instead of line_count
     - Use terminal_rows_for_line() to calculate actual terminal rows for each rendered line
  6. Renamed _prev_group_line_count to _prev_group_row_count for clarity
verification: |
  - Full test suite passes (216 tests, including 9 new regression tests)
  - Manual verification: terminal_rows_for_line correctly calculates rows for:
    - Short lines (1 row)
    - Lines exactly terminal width (1 row)
    - Wrapped lines (multiple rows based on ceiling division)
    - Lines with ANSI codes (codes excluded from width calculation)
files_changed:
  - file_matcher.py
  - tests/test_color_output.py
