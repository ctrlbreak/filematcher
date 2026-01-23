---
phase: quick
plan: 003
type: execute
wave: 1
depends_on: []
files_modified:
  - file_matcher.py
  - tests/test_cli.py
autonomous: true

must_haves:
  truths:
    - "Verbose progress updates in-place on single line during indexing"
    - "Final line shows completion message (not overwritten)"
    - "Non-TTY output falls back to multi-line (log files stay readable)"
  artifacts:
    - path: "file_matcher.py"
      provides: "Single-line progress updates in index_directory"
      contains: "carriage return progress"
    - path: "tests/test_cli.py"
      provides: "Updated verbose test expectations"
  key_links:
    - from: "index_directory"
      to: "stderr"
      via: "sys.stderr.write with carriage return"
      pattern: "sys\\.stderr\\.write.*\\\\r"
---

<objective>
Reduce verbose output lines by updating progress in-place (single line) instead of printing one line per file during indexing.

Purpose: Current verbose mode prints N lines for N files, creating excessive output noise. Single-line progress (like pip, cargo, npm) is cleaner.
Output: Verbose mode shows "[X/N] Processing filename (size)" updating in-place, with final completion message on new line.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@file_matcher.py (lines 1904-1944: index_directory function)
@tests/test_cli.py (lines 106-130: verbose mode tests)

Current behavior (line 1931):
```python
logger.debug(f"[{processed_files}/{total_files}] Processing {filepath.name} ({size_str})")
```
This prints one line per file, creating N lines of output for N files.

Target behavior:
- Use sys.stderr.write() with carriage return (\r) to overwrite same line
- Only update in-place if stderr is a TTY
- Print final completion on new line so it persists
- Non-TTY (pipes, log files) falls back to current multi-line behavior
</context>

<tasks>

<task type="auto">
  <name>Task 1: Implement single-line progress in index_directory</name>
  <files>file_matcher.py</files>
  <action>
Modify index_directory() to use in-place line updates:

1. At start of verbose block (after counting files), detect TTY:
   ```python
   is_tty = hasattr(sys.stderr, 'isatty') and sys.stderr.isatty()
   ```

2. Replace the logger.debug progress line with:
   ```python
   if is_tty:
       # Single-line progress update (overwrite previous)
       progress_line = f"\r[{processed_files}/{total_files}] Processing {filepath.name} ({size_str})"
       # Truncate to terminal width and pad to clear previous line
       term_width = shutil.get_terminal_size().columns
       if len(progress_line) > term_width:
           progress_line = progress_line[:term_width-3] + "..."
       sys.stderr.write(progress_line.ljust(term_width) + '\r')
       sys.stderr.flush()
   else:
       # Multi-line for non-TTY (logs, pipes)
       logger.debug(f"[{processed_files}/{total_files}] Processing {filepath.name} ({size_str})")
   ```

3. After the for loop completes, clear the progress line and print completion:
   ```python
   if verbose and is_tty:
       # Clear progress line and move to new line
       sys.stderr.write('\r' + ' ' * shutil.get_terminal_size().columns + '\r')
       sys.stderr.flush()
   ```
   Then the existing logger.debug completion message runs normally.

4. Add `import shutil` at top of file if not already present.

Note: The "Found X files" and "Completed indexing" messages should remain as logger.debug - they appear BEFORE and AFTER the progress loop, so they naturally get their own lines.
  </action>
  <verify>
    Run `python file_matcher.py test_dir1 test_dir2 -v 2>&1 | head -20` in a terminal and observe:
    - Initial "Found X files" message appears
    - Progress updates on single line
    - "Completed indexing" appears on new line after progress
  </verify>
  <done>
    Verbose indexing shows single-line updating progress in TTY, falls back to multi-line in pipes/logs
  </done>
</task>

<task type="auto">
  <name>Task 2: Update verbose mode tests</name>
  <files>tests/test_cli.py</files>
  <action>
Update test_verbose_mode_option to account for single-line progress behavior:

Since tests capture stderr as a string (not TTY), verbose output will use multi-line fallback.
The existing assertions should still work because:
- "Found X files to process" still logged (before loop)
- "Processing" still logged (multi-line fallback for non-TTY)
- "Completed indexing" still logged (after loop)

Verify the test still passes. If any assertions fail due to the is_tty check, ensure:
1. The test is running with mocked stderr that reports isatty() = False
2. Multi-line fallback produces the expected "Processing" lines

Add a comment explaining the TTY behavior:
```python
# Note: stderr in tests is not a TTY, so verbose progress uses multi-line fallback
# In actual terminal use, progress updates in-place on a single line
```
  </action>
  <verify>
    python3 -m tests.test_cli TestCLI.test_verbose_mode_option
  </verify>
  <done>
    Verbose tests pass and document TTY behavior
  </done>
</task>

<task type="auto">
  <name>Task 3: Run full test suite</name>
  <files>N/A</files>
  <action>
Run the complete test suite to verify no regressions:
```bash
python3 run_tests.py
```

All 198 tests must pass.
  </action>
  <verify>
    python3 run_tests.py shows all tests pass
  </verify>
  <done>
    198 tests pass, no regressions from single-line progress change
  </done>
</task>

</tasks>

<verification>
1. Terminal test: `python file_matcher.py test_dir1 test_dir2 -v` shows clean single-line progress
2. Pipe test: `python file_matcher.py test_dir1 test_dir2 -v 2>&1 | cat` shows multi-line fallback
3. All tests pass: `python3 run_tests.py`
</verification>

<success_criteria>
- Verbose mode in TTY: single-line updating progress during indexing
- Verbose mode in non-TTY: multi-line fallback (log-friendly)
- Final "Completed indexing" message appears on its own line
- All 198 existing tests pass
</success_criteria>

<output>
After completion, create `.planning/quick/003-verbose-progress-single-line/003-SUMMARY.md`
</output>
