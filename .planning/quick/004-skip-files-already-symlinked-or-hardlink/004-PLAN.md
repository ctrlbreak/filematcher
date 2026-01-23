---
phase: quick
plan: 004
type: execute
wave: 1
depends_on: []
files_modified:
  - file_matcher.py
  - tests/test_directory_operations.py
autonomous: true

must_haves:
  truths:
    - "Symlinks pointing to master files are detected and skipped during execution"
    - "Hardlinks to master files are detected and skipped during execution (all actions, not just hardlink)"
    - "Skipped files show reason in output (symlink to master / hardlink to master)"
    - "Skipped symlinks/hardlinks increment skipped_count, not failure_count"
  artifacts:
    - path: "file_matcher.py"
      provides: "Detection functions and execute_action integration"
      contains: "is_symlink_to_master"
    - path: "tests/test_directory_operations.py"
      provides: "Tests for symlink and hardlink detection"
      contains: "test_skip_symlink_to_master"
  key_links:
    - from: "execute_action()"
      to: "is_symlink_to_master() / already_hardlinked()"
      via: "early detection before action execution"
      pattern: "is_symlink_to_master.*master"
---

<objective>
Detect and skip duplicate files that are already symlinks or hardlinks to master files during action execution.

Purpose: Avoid redundant operations and clearly communicate in output why certain files were skipped.

Output: Updated file_matcher.py with detection logic and tests covering symlink/hardlink edge cases.
</objective>

<execution_context>
@/Users/patrick/.claude/get-shit-done/workflows/execute-plan.md
@/Users/patrick/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@file_matcher.py (lines 1380-1398 - already_hardlinked function)
@file_matcher.py (lines 1457-1512 - execute_action function)
@file_matcher.py (lines 1539-1630 - execute_all_actions function)
@tests/test_directory_operations.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add symlink-to-master detection and extend hardlink check to all actions</name>
  <files>file_matcher.py</files>
  <action>
1. Add `is_symlink_to_master(duplicate: str, master: str) -> bool` function near `already_hardlinked()`:
   - Check if `Path(duplicate).is_symlink()` returns True
   - If symlink, resolve the target with `Path(duplicate).resolve()`
   - Compare resolved target to `Path(master).resolve()`
   - Return True if they match (duplicate is symlink pointing to master)
   - Handle OSError gracefully (return False)

2. Modify `execute_action()` function (around line 1484):
   - Add symlink detection check BEFORE the existing hardlink check:
     ```python
     # Check if duplicate is a symlink pointing to master (skip if so)
     if is_symlink_to_master(duplicate, master):
         return (True, "symlink to master", "skipped")
     ```
   - Move the existing `already_hardlinked()` check to apply to ALL actions (not just hardlink):
     ```python
     # Check if already hardlinked to master (skip if so for any action)
     if already_hardlinked(duplicate, master):
         return (True, "hardlink to master", "skipped")
     ```
   - Update the error message from "already linked" to "hardlink to master" for consistency

3. The existing skip handling in `execute_all_actions()` (lines 1620-1622) already handles `actual_action == "skipped"` correctly, no changes needed there.
  </action>
  <verify>
Run: `python3 -c "from file_matcher import is_symlink_to_master, already_hardlinked; print('Functions exist')"`
Verify function exists and is importable.
  </verify>
  <done>
- `is_symlink_to_master()` function exists and correctly detects symlinks to master
- `execute_action()` checks symlinks before hardlinks
- `execute_action()` checks hardlinks for all actions (symlink, delete), not just hardlink action
- Skip reasons are specific: "symlink to master" or "hardlink to master"
  </done>
</task>

<task type="auto">
  <name>Task 2: Add tests for symlink and hardlink skip detection</name>
  <files>tests/test_directory_operations.py</files>
  <action>
Add test class `TestSkipAlreadyLinked` with the following tests:

1. `test_is_symlink_to_master_true()`:
   - Create temp master file with content
   - Create symlink in dup directory pointing to master
   - Assert `is_symlink_to_master(symlink_path, master_path)` returns True

2. `test_is_symlink_to_master_false_different_target()`:
   - Create master file and separate other file
   - Create symlink pointing to other file (not master)
   - Assert `is_symlink_to_master(symlink_path, master_path)` returns False

3. `test_is_symlink_to_master_false_regular_file()`:
   - Create master file and regular duplicate file
   - Assert `is_symlink_to_master(duplicate_path, master_path)` returns False

4. `test_execute_action_skips_symlink_to_master()`:
   - Create master file and symlink pointing to it
   - Call `execute_action(symlink, master, 'hardlink')`
   - Assert returns `(True, "symlink to master", "skipped")`
   - Assert symlink still exists (not modified)

5. `test_execute_action_skips_hardlink_to_master_all_actions()`:
   - Create master file and hardlink to it
   - Test with action='symlink': assert returns `(True, "hardlink to master", "skipped")`
   - Test with action='delete': assert returns `(True, "hardlink to master", "skipped")`
   - Assert hardlink still exists (not modified)

Import `is_symlink_to_master` and `execute_action` from file_matcher at top of test file.
  </action>
  <verify>
Run: `python3 -m pytest tests/test_directory_operations.py -v -k "TestSkipAlreadyLinked" --tb=short`
All new tests pass.
  </verify>
  <done>
- 5 new tests covering symlink and hardlink detection
- Tests verify functions return correct skip reasons
- Tests verify files are not modified when skipped
- All tests pass
  </done>
</task>

<task type="auto">
  <name>Task 3: Run full test suite and verify no regressions</name>
  <files></files>
  <action>
Run the complete test suite to ensure:
1. All existing tests still pass (no regressions)
2. New tests pass
3. The existing "already linked" test case (if any) works with updated message

If existing tests fail due to changed error message (from "already linked" to "hardlink to master"), update those tests to match new message.
  </action>
  <verify>
Run: `python3 run_tests.py`
All 198+ tests pass.
  </verify>
  <done>
- Full test suite passes (198+ tests)
- No regressions in existing functionality
- New symlink/hardlink skip detection works correctly
  </done>
</task>

</tasks>

<verification>
1. Manual test with actual symlink:
   ```bash
   # Create test scenario
   mkdir -p /tmp/fm_test/master /tmp/fm_test/dup
   echo "content" > /tmp/fm_test/master/file.txt
   ln -s /tmp/fm_test/master/file.txt /tmp/fm_test/dup/link.txt

   # Run filematcher with action
   python file_matcher.py /tmp/fm_test/master /tmp/fm_test/dup -a hardlink --execute -y

   # Should show skipped count = 1, reason = symlink to master
   ```

2. Manual test with actual hardlink:
   ```bash
   mkdir -p /tmp/fm_test2/master /tmp/fm_test2/dup
   echo "content" > /tmp/fm_test2/master/file.txt
   ln /tmp/fm_test2/master/file.txt /tmp/fm_test2/dup/linked.txt

   python file_matcher.py /tmp/fm_test2/master /tmp/fm_test2/dup -a delete --execute -y

   # Should show skipped count = 1, reason = hardlink to master
   ```
</verification>

<success_criteria>
- `is_symlink_to_master()` correctly detects symlinks pointing to master
- `execute_action()` skips symlinks to master with reason "symlink to master"
- `execute_action()` skips hardlinks to master for ALL actions (not just hardlink)
- Skip reason changed from generic "already linked" to specific "hardlink to master"
- All 198+ tests pass
- New tests cover symlink and hardlink edge cases
</success_criteria>

<output>
After completion, create `.planning/quick/004-skip-files-already-symlinked-or-hardlink/004-SUMMARY.md`
</output>
