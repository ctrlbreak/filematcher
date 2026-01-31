---
phase: 015
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - filematcher/formatters.py
  - filematcher/cli.py
  - tests/test_formatters.py
autonomous: true

must_haves:
  truths:
    - "Confirmation status appears at start of action line"
    - "Content does not shift right after confirmation"
    - "Status symbol replaces leading spaces"
  artifacts:
    - path: "filematcher/formatters.py"
      provides: "format_confirmation_status with ANSI cursor movement"
    - path: "filematcher/cli.py"
      provides: "Track duplicate line count for cursor movement"
    - path: "tests/test_formatters.py"
      provides: "Updated tests for new status placement"
  key_links:
    - from: "filematcher/cli.py"
      to: "formatter.format_confirmation_status()"
      via: "Passes line count to move cursor back"
---

<objective>
Move confirmation checkmark/cross to appear at the start of the action line (WILL DELETE, etc.) instead of on its own line after the group.

Current behavior:
```
[1/2] MASTER: /path/master/a.txt
    WILL DELETE: /path/dup/a.txt
[1/2] Delete duplicate? [y/n/a/q] n
X
```

Desired behavior:
```
[1/2] MASTER: /path/master/a.txt
X   WILL DELETE: /path/dup/a.txt
[1/2] Delete duplicate? [y/n/a/q] n
```

Purpose: Cleaner visual feedback - status appears inline with the action being confirmed/skipped.
Output: Modified formatters.py and cli.py with ANSI cursor movement to place status on action line.
</objective>

<context>
@filematcher/formatters.py (TextActionFormatter.format_confirmation_status, format_duplicate_group)
@filematcher/cli.py (interactive_execute - calls format_confirmation_status)
@filematcher/colors.py (GroupLine, render_group_line)
@tests/test_formatters.py (test_format_confirmation_status_*)
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add ANSI cursor movement to format_confirmation_status</name>
  <files>filematcher/formatters.py, filematcher/colors.py</files>
  <action>
Modify TextActionFormatter.format_confirmation_status() to:
1. Accept a `lines_back` parameter (int) indicating how many lines to move cursor up
2. Use ANSI escape codes:
   - Move cursor up N lines: `\033[{N}A`
   - Print status symbol (checkmark or X) at current position (replaces first 4 chars of indent)
   - Move cursor down N lines: `\033[{N}B` to return to original position
   - No newline needed since we're not on our own line anymore

The action lines currently have "    " (4-space indent). The status symbol + 3 spaces should replace this:
- Confirmed: checkmark + 3 spaces = "V   " (but V is the checkmark)
- Skipped: X + 3 spaces = "X   "

In colors.py, add ANSI constants for cursor movement if not present:
- CURSOR_UP = "\033[{n}A" (template, use f-string with n)
- CURSOR_DOWN = "\033[{n}B"

Update method signature:
```python
def format_confirmation_status(self, confirmed: bool, lines_back: int = 1) -> None:
```

When lines_back > 0:
- Move cursor up lines_back lines
- Print status + spaces (no newline, use end="")
- Move cursor down lines_back lines
- Print newline to restore position

When lines_back == 0 (fallback for non-TTY or testing):
- Keep original behavior: print status on new line
  </action>
  <verify>Run `python3 -c "from filematcher.formatters import TextActionFormatter; from filematcher.colors import ColorConfig, ColorMode; f = TextActionFormatter('delete', ColorConfig(ColorMode.NEVER)); print('Line 1'); print('    Line 2'); f.format_confirmation_status(True, 1); print('Done')"` - checkmark should appear on Line 2</verify>
  <done>format_confirmation_status accepts lines_back parameter and uses ANSI cursor movement</done>
</task>

<task type="auto">
  <name>Task 2: Pass duplicate count to format_confirmation_status in interactive_execute</name>
  <files>filematcher/cli.py</files>
  <action>
In interactive_execute(), after each call to format_confirmation_status(), pass the number of lines to move back:
- Count = 1 + len(duplicates) for a group (1 for prompt line we're on, but actually we need to go back to the first duplicate line)

Actually, reconsider: The cursor is at the end of the prompt line after user input. We need to go back:
- To the FIRST duplicate line (the WILL DELETE line)
- Not past the MASTER line

For a group with 1 duplicate:
```
[1/2] MASTER: ...          <- line -2
    WILL DELETE: ...       <- line -1 (target)
[1/2] prompt? n            <- current line (cursor here after input)
```

So lines_back = 1 for single duplicate.

For multiple duplicates (e.g., 2):
```
[1/2] MASTER: ...          <- line -3
    WILL DELETE: ...       <- line -2 (first duplicate, target)
    WILL DELETE: ...       <- line -1
[1/2] prompt? n            <- current line
```

So lines_back = len(duplicates) to reach first duplicate line.

Wait, re-read the request: "at the start of the action line" - singular. The status shows once, on the first duplicate line. So lines_back = len(duplicates) to go back to first duplicate.

Update all calls to format_confirmation_status in interactive_execute:
```python
formatter.format_confirmation_status(confirmed=True, lines_back=len(duplicates))
formatter.format_confirmation_status(confirmed=False, lines_back=len(duplicates))
```

There are 4 places where format_confirmation_status is called:
1. Line ~145: confirm_all branch (confirmed=True)
2. Line ~192: response == 'y' (confirmed=True)
3. Line ~235: response == 'n' (confirmed=False)
4. Line ~239: response == 'a' (confirmed=True)

For verbose mode with hash line, add 1 more line. Check if verbose flag is set and file_hash is provided in the group.

Actually simpler: compute duplicate_line_count based on:
- len(duplicates) for the action lines
- +1 if verbose and file_hash (hash line is after duplicates but before prompt)

Pass this count to format_confirmation_status.
  </action>
  <verify>Run interactive execute with test directories and verify status appears on action line: `echo "n" | python3 -m filematcher /private/tmp/fm_test_master /private/tmp/fm_test_dup -a delete --execute 2>/dev/null`</verify>
  <done>interactive_execute passes correct lines_back to format_confirmation_status</done>
</task>

<task type="auto">
  <name>Task 3: Update tests for new behavior</name>
  <files>tests/test_formatters.py</files>
  <action>
Update test_format_confirmation_status_confirmed and test_format_confirmation_status_skipped:

1. Test with lines_back=0 (original behavior for compatibility):
   - Should output checkmark/X followed by newline
   - Existing assertions should still pass

2. Add new tests for lines_back > 0:
   - test_format_confirmation_status_moves_cursor_up
   - Capture stdout, call with lines_back=2
   - Assert output contains ANSI cursor up sequence (can check for escape codes)
   - Assert output contains checkmark/X
   - Assert output contains ANSI cursor down sequence

3. Test that JsonActionFormatter.format_confirmation_status ignores lines_back:
   - Already a no-op, but update signature to accept optional parameter

Update JsonActionFormatter.format_confirmation_status signature:
```python
def format_confirmation_status(self, confirmed: bool, lines_back: int = 0) -> None:
```
Still does nothing (JSON mode doesn't show interactive status).

Update ABC ActionFormatter.format_confirmation_status signature if it exists.
  </action>
  <verify>Run `python3 -m tests.test_formatters` - all tests pass</verify>
  <done>Tests updated to cover new cursor movement behavior</done>
</task>

</tasks>

<verification>
1. `python3 run_tests.py` - all 305+ tests pass
2. Manual test with real directories:
   ```
   echo "n" | python3 -m filematcher /private/tmp/fm_test_master /private/tmp/fm_test_dup -a delete --execute
   ```
   Verify X appears at start of WILL DELETE line, not on separate line
3. Test confirm path:
   ```
   echo "y" | python3 -m filematcher /private/tmp/fm_test_master /private/tmp/fm_test_dup -a delete --execute
   ```
   Verify checkmark appears at start of WILL DELETE line
</verification>

<success_criteria>
- Confirmation status (checkmark/X) appears at the start of the action line
- Content on action line does not shift (status replaces leading indent spaces)
- All existing tests pass
- Interactive execute shows cleaner output format
</success_criteria>

<output>
After completion, update `.planning/STATE.md` quick tasks table with this task.
</output>
