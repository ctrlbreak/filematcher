---
phase: quick-012
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - filematcher/formatters.py
  - tests/test_output_unification.py
autonomous: true

must_haves:
  truths:
    - "Mode banner is visually separated from scanning phase output"
    - "Blank line appears before banner line in non-quiet mode"
    - "Existing tests continue to pass"
  artifacts:
    - path: "filematcher/formatters.py"
      provides: "Separator line before mode banner"
      contains: "print()"
  key_links:
    - from: "filematcher/formatters.py:TextActionFormatter.format_banner"
      to: "stdout"
      via: "print() before banner line"
      pattern: "print\\(\\)"
---

<objective>
Add a separator line (blank line) before the mode banner to visually separate it from the scanning phase output.

Purpose: The scanning phase (logger messages to stderr like "Using MD5...", "Indexing directory...") runs directly into the mode banner on stdout with no visual separation. Adding a blank line improves readability.

Output: Updated format_banner() method that prints a blank line before the banner content.
</objective>

<execution_context>
@/Users/patrick/.claude/get-shit-done/workflows/execute-plan.md
@/Users/patrick/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@filematcher/formatters.py - TextActionFormatter.format_banner() method (lines 526-560)
@filematcher/cli.py - Uses format_banner() for both preview and execute modes
@tests/test_output_unification.py - Tests for unified header format
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add blank line before banner in TextActionFormatter.format_banner()</name>
  <files>filematcher/formatters.py</files>
  <action>
In `TextActionFormatter.format_banner()` (around line 526), add `print()` as the first line of the method body to output a blank line before the banner content.

The current method starts with:
```python
def format_banner(
    self,
    action: str,
    group_count: int,
    duplicate_count: int,
    space_bytes: int
) -> None:
    """Output unified banner with statistics and mode indicator."""
    action_bold = bold(action, self.cc)
    ...
```

Change to:
```python
def format_banner(
    self,
    action: str,
    group_count: int,
    duplicate_count: int,
    space_bytes: int
) -> None:
    """Output unified banner with statistics and mode indicator."""
    print()  # Separator from scanning phase output
    action_bold = bold(action, self.cc)
    ...
```

This ensures visual separation between stderr (scanning) and stdout (banner) output.
  </action>
  <verify>
Run: `python3 -m filematcher test_dir1 test_dir2 --action hardlink 2>&1 | head -10`
Expected: Blank line visible between "Skipped N files..." and "hardlink mode:..." lines
  </verify>
  <done>format_banner() outputs blank line before banner content</done>
</task>

<task type="auto">
  <name>Task 2: Verify all tests pass</name>
  <files>tests/test_output_unification.py</files>
  <action>
Run the test suite to ensure the blank line addition does not break existing tests.

The test_output_unification.py tests check for banner content but should not be sensitive to leading whitespace.

If any tests fail due to the new blank line:
- Tests using `assertIn` for banner content should still pass (blank line doesn't affect substring matching)
- Tests checking exact stdout format may need adjustment (unlikely based on current test patterns)
  </action>
  <verify>
Run: `python3 run_tests.py`
Expected: All 284+ tests pass
  </verify>
  <done>All existing tests pass with the separator line change</done>
</task>

</tasks>

<verification>
1. Visual check: `python3 -m filematcher test_dir1 test_dir2 --action hardlink 2>&1`
   - Should show blank line between scanning output and mode banner
2. Test suite: `python3 run_tests.py`
   - All tests pass
3. Compare mode: `python3 -m filematcher test_dir1 test_dir2 2>&1`
   - Should also show blank line before "compare mode:" banner
</verification>

<success_criteria>
- Blank line appears before mode banner in terminal output
- Visual separation improves readability between scanning phase and banner
- All 284+ tests pass
- No changes to JSON output format (JsonActionFormatter.format_banner is a no-op)
</success_criteria>

<output>
After completion, create `.planning/quick/012-add-separator-line-before-mode-banner/012-SUMMARY.md`
</output>
