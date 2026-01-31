---
phase: quick
plan: 014
type: execute
wave: 1
depends_on: []
files_modified:
  - filematcher/formatters.py
autonomous: true

must_haves:
  truths:
    - "Multiple duplicate groups display sequentially (one under another) in TTY mode"
    - "Hash is still displayed in verbose mode"
    - "Interactive confirmation prompts can still use inline status symbols"
  artifacts:
    - path: "filematcher/formatters.py"
      provides: "TextActionFormatter with simplified group display"
      contains: "format_duplicate_group"
  key_links:
    - from: "filematcher/formatters.py"
      to: "cli.py interactive_execute"
      via: "format_duplicate_group call"
      pattern: "format_duplicate_group"
---

<objective>
Remove TTY carriage return/overwrite behavior in duplicate group display so groups display sequentially (one under another) instead of overwriting each other.

Purpose: Improve readability by showing all groups in sequence rather than having later groups overwrite earlier ones.

Output: Modified TextActionFormatter.format_duplicate_group() with simplified output logic.
</objective>

<execution_context>
@/Users/patrick/.claude/get-shit-done/workflows/execute-plan.md
@/Users/patrick/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@filematcher/formatters.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Remove ANSI escape overwrite behavior in TextActionFormatter</name>
  <files>filematcher/formatters.py</files>
  <action>
In TextActionFormatter.format_duplicate_group() (around lines 681-728), remove the TTY-specific ANSI escape code logic that causes groups to overwrite each other:

1. Remove the `_prev_group_row_count` instance variable initialization in __init__ (line 636)

2. In format_duplicate_group(), simplify the method by removing the "inline_progress" conditional logic:
   - Remove the `inline_progress` variable (line 694)
   - Remove the block that checks `if self._prev_group_row_count > 0` and uses `\033[A\033[K` escape codes (lines 714-717)
   - Remove the `if lines:` block that sets prefix (lines 718-719)
   - Remove the `row_count` tracking logic (lines 721, 725, 727-728)
   - Remove the `terminal_rows_for_line` calculation complexity (line 725)

3. Keep the group index prefix display - when group_index and total_groups are provided, prepend `[{group_index}/{total_groups}] ` to the first line. This should happen ALWAYS, not just for TTY.

4. Keep the hash display in verbose mode (lines 709-710) - no changes needed there.

5. The resulting method should simply:
   - Build the GroupLine list via format_duplicate_group()
   - Add hash line if verbose
   - Add group index prefix to first line if group_index/total_groups provided
   - Print each line normally with render_group_line()

The format_confirmation_status() and format_group_prompt() methods should NOT be changed - they can continue to use their existing inline behavior.
  </action>
  <verify>
Run: `python3 -m filematcher test_dir1 test_dir2 --action delete` and confirm multiple groups display sequentially in terminal.
Run: `python3 -m filematcher test_dir1 test_dir2 --action delete -v` and confirm hash is displayed.
Run: `python3 run_tests.py` and confirm all tests pass.
  </verify>
  <done>
Groups display under one another without overwriting. Hash still visible in verbose mode. All tests pass.
  </done>
</task>

<task type="auto">
  <name>Task 2: Clean up unused imports</name>
  <files>filematcher/formatters.py</files>
  <action>
After Task 1, check if the following are still needed:
- `shutil` import - only used for `get_terminal_size()` which may no longer be needed in formatters.py
- `terminal_rows_for_line` import from colors module - was used for row counting

If these are no longer used in formatters.py, remove the unused imports.

Note: Do NOT remove `shutil` if it's used elsewhere in the file. Check all usages first.
  </action>
  <verify>
Run: `python3 -c "import filematcher.formatters"` - no import errors.
Run: `python3 run_tests.py` - all tests pass.
  </verify>
  <done>
No unused imports remain. Module imports cleanly. All tests pass.
  </done>
</task>

</tasks>

<verification>
1. `python3 -m filematcher test_dir1 test_dir2 --action delete` shows groups stacked vertically
2. `python3 -m filematcher test_dir1 test_dir2 --action delete -v` shows hash for each group
3. `python3 -m filematcher test_dir1 test_dir2 --action delete --execute` in interactive mode still shows checkmark/X after confirmation
4. `python3 run_tests.py` passes all 305 tests
</verification>

<success_criteria>
- Duplicate groups display sequentially in TTY mode (not overwriting)
- Hash is displayed when --verbose flag is used
- Interactive confirmation still shows inline status symbols
- All existing tests pass
- No unused imports
</success_criteria>

<output>
After completion, create `.planning/quick/014-remove-tty-carriage-return-from-group-di/014-SUMMARY.md`
</output>
