---
phase: quick
plan: 018
type: execute
wave: 1
depends_on: []
files_modified:
  - filematcher/cli.py
autonomous: true

must_haves:
  truths:
    - "main() function has reduced cyclomatic complexity"
    - "All 308 tests pass unchanged"
    - "No behavioral changes - pure refactoring"
  artifacts:
    - path: "filematcher/cli.py"
      provides: "Refactored CLI with extracted helpers"
      contains: "_setup_logging"
  key_links:
    - from: "main()"
      to: "extracted helpers"
      via: "function calls"
      pattern: "_validate_args|_setup_logging|_build_master_results|_execute_batch|_execute_interactive"
---

<objective>
Reduce complexity of the main() function in filematcher/cli.py by extracting cohesive helper functions.

Purpose: The main() function is 425 lines (lines 380-805) with deep nesting and multiple execution paths. This refactoring improves maintainability and testability without changing behavior.

Output: Refactored cli.py with main() reduced to ~100-150 lines through extraction of 4-5 helper functions.
</objective>

<execution_context>
@/Users/patrick/.claude/get-shit-done/workflows/execute-plan.md
@/Users/patrick/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@filematcher/cli.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Extract argument validation and setup helpers</name>
  <files>filematcher/cli.py</files>
  <action>
Extract two helpers from main():

1. `_validate_args(args, parser) -> None`
   - Move argument validation logic (lines 425-442)
   - All the parser.error() calls for incompatible flags
   - Raises parser.error() on invalid combinations

2. `_setup_logging(args) -> logging.Handler`
   - Move logging configuration (lines 446-463)
   - Determine log level from quiet/verbose
   - Create and configure handlers
   - Return the handler for potential cleanup

Update main() to call these helpers in sequence. Keep the same behavior - just extract cohesive chunks.
  </action>
  <verify>python3 run_tests.py passes (308 tests)</verify>
  <done>_validate_args() and _setup_logging() extracted, main() reduced by ~40 lines</done>
</task>

<task type="auto">
  <name>Task 2: Extract master results building logic</name>
  <files>filematcher/cli.py</files>
  <action>
Extract the master results processing into a helper:

`_build_master_results(matches, master_path, action) -> tuple[list[DuplicateGroup], set[str], list[str], int]`

Returns: (master_results, cross_fs_files, warnings, total_already_hardlinked)

Move lines 487-516:
- Loop over matches to build master_results
- Master file selection per group
- Warning generation for multiple masters
- Cross-filesystem detection for hardlink action
- Filter out already-hardlinked duplicates

This is a pure data transformation - takes matches dict, returns processed results.
  </action>
  <verify>python3 run_tests.py passes (308 tests)</verify>
  <done>_build_master_results() extracted, master selection logic isolated</done>
</task>

<task type="auto">
  <name>Task 3: Extract execute mode dispatch helpers</name>
  <files>filematcher/cli.py</files>
  <action>
The execute mode (lines 627-802) has three branches with duplicated patterns. Extract:

1. `_execute_json_batch(args, master_results, matches, cross_fs_files, action_formatter, color_config) -> int`
   - JSON mode execution path (lines 628-689)
   - Returns exit code

2. `_execute_text_batch(args, master_results, matches, cross_fs_files, color_config) -> int`
   - Text mode with --yes flag (lines 703-738)
   - Returns exit code

3. `_execute_interactive(args, master_results, matches, cross_fs_files, action_formatter, color_config) -> int`
   - Interactive mode (lines 740-802)
   - Returns exit code

Update main() execute_mode branch to dispatch:
```python
if args.json:
    return _execute_json_batch(...)
elif args.yes:
    return _execute_text_batch(...)
else:
    return _execute_interactive(...)
```

Also move `print_preview_output` from a nested function to a module-level `_print_preview_output()` helper.
  </action>
  <verify>python3 run_tests.py passes (308 tests)</verify>
  <done>Execute mode branches extracted, main() reduced to orchestration logic (~100-150 lines)</done>
</task>

</tasks>

<verification>
1. All 308 tests pass: `python3 run_tests.py`
2. main() function is ~100-150 lines (down from 425)
3. Extracted helpers are cohesive single-purpose functions
4. No behavior changes - pure refactoring
</verification>

<success_criteria>
- main() function reduced from 425 lines to ~100-150 lines
- 4-6 new helper functions extracted
- All tests pass without modification
- CLI behavior identical (same outputs, same exit codes)
</success_criteria>

<output>
After completion, create `.planning/quick/018-improve-the-complexity-of-the-main-funct/018-SUMMARY.md`
</output>
