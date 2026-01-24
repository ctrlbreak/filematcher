---
phase: quick
plan: 006
type: execute
wave: 1
depends_on: []
files_modified:
  - file_matcher.py
  - tests/test_cli.py
autonomous: true

must_haves:
  truths:
    - "In TTY mode, user sees inline progress like [1/100] while groups output"
    - "In non-TTY mode (pipes/logs), groups output normally without progress"
    - "All existing coloring still works"
    - "Verbose mode still shows hash at end of group"
  artifacts:
    - path: "file_matcher.py"
      provides: "TTY-aware inline progress for group output"
      contains: "group_index"
  key_links:
    - from: "TextActionFormatter.format_duplicate_group"
      to: "sys.stderr"
      via: "TTY progress write"
      pattern: "sys\\.stderr\\.write.*group"
---

<objective>
Add inline progress indicator [1/100] style to group detail output in TTY mode.

Purpose: Improve user experience by showing progress during group output, especially for large result sets.
Output: TTY-aware progress indicator that updates in place, with clean final output.
</objective>

<execution_context>
@/Users/patrick/.claude/get-shit-done/workflows/execute-plan.md
@/Users/patrick/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@file_matcher.py (lines 814-870 - TextActionFormatter.format_duplicate_group)
@file_matcher.py (lines 1965-1990 - index_directory TTY progress pattern)
@file_matcher.py (lines 2260-2284 - compare mode call site)
@file_matcher.py (lines 2350-2372 - execute mode call site)
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add TTY-aware progress to TextActionFormatter.format_duplicate_group</name>
  <files>file_matcher.py</files>
  <action>
Modify `TextActionFormatter.format_duplicate_group` to accept optional `group_index` and `total_groups` parameters.

1. Add parameters to method signature (after cross_fs_files):
   - `group_index: int | None = None`
   - `total_groups: int | None = None`

2. At the START of the method (before any print output), if both group_index and total_groups are provided:
   - Detect TTY: `is_tty = hasattr(sys.stderr, 'isatty') and sys.stderr.isatty()`
   - In TTY mode, write progress to stderr:
     ```python
     if is_tty and group_index is not None and total_groups is not None:
         # Truncate master path for display
         display_path = master_file
         progress_prefix = f"[{group_index}/{total_groups}] "
         term_width = shutil.get_terminal_size().columns
         max_path = term_width - len(progress_prefix) - 1
         if len(display_path) > max_path:
             display_path = "..." + display_path[-(max_path-3):]
         progress_line = f"\r{progress_prefix}{display_path}"
         sys.stderr.write(progress_line.ljust(term_width) + '\r')
         sys.stderr.flush()
     ```

3. Note: The clearing of the progress line will happen at the caller level after all groups are done (existing pattern from index_directory).

Do NOT modify the base class `ActionFormatterBase.format_duplicate_group` or `JsonActionFormatter.format_duplicate_group` - they don't need progress since JSON outputs all at once at the end.
  </action>
  <verify>Method signature updated, grep for "group_index" shows it in TextActionFormatter</verify>
  <done>TextActionFormatter.format_duplicate_group accepts group_index/total_groups and writes TTY progress</done>
</task>

<task type="auto">
  <name>Task 2: Update call sites to pass group index</name>
  <files>file_matcher.py</files>
  <action>
Update the two call sites in main() that call `formatter.format_duplicate_group`:

1. **Compare/Preview mode** (around line 2273):
   The loop already has `i` from enumerate. Pass it:
   ```python
   formatter.format_duplicate_group(
       master_file, duplicates,
       action=args.action,
       file_hash=file_hash,
       file_sizes=file_sizes,
       cross_fs_files=cross_fs_to_show,
       group_index=i + 1,  # 1-indexed for display
       total_groups=len(sorted_results)
   )
   ```

2. **Execute mode** (around line 2354):
   Add enumerate to the loop and pass indices:
   ```python
   for i, (master_file, duplicates, reason, file_hash) in enumerate(sorted_results):
       ...
       action_formatter.format_duplicate_group(
           master_file, duplicates,
           action=args.action,
           file_hash=file_hash,
           file_sizes=file_sizes,
           cross_fs_files=cross_fs_to_show,
           group_index=i + 1,
           total_groups=len(sorted_results)
       )
   ```

3. **Clear progress after loops** - Add after both loops complete (before statistics):
   ```python
   # Clear progress line (TTY only)
   if hasattr(sys.stderr, 'isatty') and sys.stderr.isatty():
       sys.stderr.write('\r' + ' ' * shutil.get_terminal_size().columns + '\r')
       sys.stderr.flush()
   ```

   For compare mode: add this after the `for i, ...` loop ends (around line 2284, before unmatched section)
   For execute mode: add this after the `for i, ...` loop ends (around line 2371, before statistics)
  </action>
  <verify>grep for "group_index=" shows two call sites updated; grep for "Clear progress" shows two clear operations</verify>
  <done>Both call sites pass group_index and total_groups; progress line cleared after loops</done>
</task>

<task type="auto">
  <name>Task 3: Add test for TTY progress behavior</name>
  <files>tests/test_cli.py</files>
  <action>
Add a test that verifies TTY progress is written to stderr when isatty() returns True.

1. Create test method `test_group_output_tty_progress`:
   ```python
   def test_group_output_tty_progress(self):
       """Test that TTY mode shows inline progress on stderr."""
       # Create a mock stderr that claims to be a TTY
       mock_stderr = io.StringIO()
       mock_stderr.isatty = lambda: True

       with patch('sys.stderr', mock_stderr):
           with patch('sys.argv', ['file_matcher', str(self.dir1), str(self.dir2)]):
               # Run compare mode
               result = main()

       # Check stderr contains progress indicators [n/m]
       stderr_content = mock_stderr.getvalue()
       # Progress should have been written (and cleared)
       # The final clear leaves empty string, but we can check it was accessed
       self.assertEqual(result, 0)
   ```

2. Add a test `test_group_output_non_tty_no_progress`:
   ```python
   def test_group_output_non_tty_no_progress(self):
       """Test that non-TTY mode does not write progress to stderr."""
       mock_stderr = io.StringIO()
       # Default StringIO.isatty() returns False

       with patch('sys.stderr', mock_stderr):
           with patch('sys.argv', ['file_matcher', str(self.dir1), str(self.dir2)]):
               result = main()

       # stderr should be empty (no progress written)
       stderr_content = mock_stderr.getvalue()
       self.assertEqual(stderr_content, "")
       self.assertEqual(result, 0)
   ```

Add import `io` at top if not present.
  </action>
  <verify>python3 -m tests.test_cli passes, including new tests</verify>
  <done>Tests verify TTY progress behavior on stderr</done>
</task>

</tasks>

<verification>
1. Run full test suite: `python3 run_tests.py`
2. Manual TTY test: `python file_matcher.py test_dir1 test_dir2` - should show [1/N] progress
3. Manual non-TTY test: `python file_matcher.py test_dir1 test_dir2 | cat` - no progress on stderr
4. Verify colors still work: output should have green MASTER, yellow DUPLICATE
5. Verify verbose mode: `python file_matcher.py test_dir1 test_dir2 -v` shows hash
</verification>

<success_criteria>
- TTY mode shows inline [n/m] progress on stderr during group output
- Non-TTY mode outputs normally without progress indicator
- Progress line clears cleanly after all groups output
- All existing coloring preserved
- Verbose mode still shows hash
- All 204+ tests pass
</success_criteria>

<output>
After completion, create `.planning/quick/006-inline-progress-for-group-output-with-tt/006-SUMMARY.md`
</output>
