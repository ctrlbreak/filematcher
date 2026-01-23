---
phase: quick
plan: 002
type: execute
wave: 1
depends_on: []
files_modified:
  - file_matcher.py
autonomous: true

must_haves:
  truths:
    - "TextCompareFormatter.format_match_group delegates to shared helper"
    - "TextActionFormatter.format_duplicate_group delegates to same shared helper"
    - "Group output visual format is identical before and after refactor"
  artifacts:
    - path: "file_matcher.py"
      provides: "Shared group formatting helper function"
      contains: "def format_group_lines"
  key_links:
    - from: "TextCompareFormatter.format_match_group"
      to: "format_group_lines"
      via: "function call"
      pattern: "format_group_lines\\("
    - from: "TextActionFormatter.format_duplicate_group"
      to: "format_group_lines"
      via: "function call"
      pattern: "format_group_lines\\("
---

<objective>
Refactor group output formatting to reduce code duplication between compare mode and action mode.

Purpose: Phase 9 unified the visual format of group output ([MASTER]/[DUPLICATE] labels, indentation, hash display), but the implementation duplicates this logic in TextCompareFormatter.format_match_group (lines 510-547) and TextActionFormatter.format_duplicate_group (lines 1041-1096). Extract shared formatting to a helper function.

Output: Single shared function that both formatters delegate to, eliminating duplicated logic.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@file_matcher.py (lines 510-547: TextCompareFormatter.format_match_group)
@file_matcher.py (lines 1041-1096: TextActionFormatter.format_duplicate_group)
@file_matcher.py (lines 1258-1313: format_duplicate_group helper)
</context>

<tasks>

<task type="auto">
  <name>Task 1: Extract shared group formatting logic</name>
  <files>file_matcher.py</files>
  <action>
Create a new helper function `format_group_lines()` that encapsulates the shared visual format for group output:

```python
def format_group_lines(
    master_file: str,
    secondary_files: list[str],
    master_label: str = "MASTER",
    secondary_label: str = "DUPLICATE",
    verbose: bool = False,
    file_sizes: dict[str, int] | None = None,
    dup_count: int | None = None,
    cross_fs_files: set[str] | None = None
) -> list[str]:
    """
    Format group lines with unified visual structure.

    Returns list of lines (without colors) for:
    - Primary line: [MASTER_LABEL] path (optional: dup count, size)
    - Secondary lines: 4-space indent [SECONDARY_LABEL] path

    Callers apply colors after receiving lines.
    """
```

Key behaviors to extract:
1. Master line format: `[{master_label}] {path}` with optional verbose suffix `({dup_count} duplicates, {size})`
2. Secondary line format: `    [{secondary_label}] {path}` with 4-space indent
3. Cross-fs marker: ` [!cross-fs]` suffix when applicable
4. Sorting: Secondary files sorted alphabetically for determinism (OUT-04)

Place this function near the existing `format_duplicate_group()` function (around line 1258) since it serves a similar purpose.

Do NOT change any existing function signatures or behavior yet - this task only adds the new helper.
  </action>
  <verify>
Run `python3 -c "from file_matcher import format_group_lines; print(format_group_lines('/a/master.txt', ['/b/dup1.txt', '/b/dup2.txt']))"` shows expected output format.
  </verify>
  <done>New format_group_lines() function exists and produces correct line format</done>
</task>

<task type="auto">
  <name>Task 2: Refactor formatters to use shared helper</name>
  <files>file_matcher.py</files>
  <action>
Update both TextCompareFormatter.format_match_group and TextActionFormatter.format_duplicate_group to delegate to format_group_lines():

**TextCompareFormatter.format_match_group (lines 510-547):**
- Call format_group_lines() with:
  - master_file: first file from sorted_dir1
  - secondary_files: remaining dir1 files + all dir2 files
  - master_label: "MASTER"
  - secondary_label: Choose based on file source (MASTER for dir1, DUPLICATE for dir2)
  - verbose, file_sizes, dup_count as appropriate
- Apply colors to returned lines (green for MASTER, yellow for DUPLICATE)
- Print hash line in verbose mode (dim color)

Note: Compare mode has TWO types of secondary files (additional dir1 = MASTER, dir2 = DUPLICATE), so either:
  A) Call format_group_lines twice (once for extra masters, once for duplicates), OR
  B) Keep the loop but use format_group_lines for the primary line only

Choose option B for simplicity - use format_group_lines for primary master line, keep explicit loops for secondary files since they need different labels based on source directory.

**TextActionFormatter.format_duplicate_group (lines 1041-1096):**
- Already delegates to format_duplicate_group() helper (lines 1258-1313)
- Update format_duplicate_group() to call format_group_lines() internally
- This preserves the existing delegation pattern while using shared formatting

Preserve exact visual output - run tests to verify no format changes.
  </action>
  <verify>
`python3 run_tests.py` - all 198 tests pass with no changes to output format.
  </verify>
  <done>Both formatters use shared helper, all tests pass, output unchanged</done>
</task>

<task type="auto">
  <name>Task 3: Clean up redundant code</name>
  <files>file_matcher.py</files>
  <action>
Review and remove any duplicated logic that is now handled by format_group_lines():

1. In format_duplicate_group() (lines 1258-1313):
   - If Task 2 successfully delegates to format_group_lines(), verify no duplicate logic remains
   - The function should be simpler: call format_group_lines() and return result

2. In TextCompareFormatter.format_match_group:
   - Verify verbose size formatting uses format_file_size() consistently
   - Ensure sorting happens only once (in format_group_lines or caller, not both)

3. Verify consistent behavior:
   - Cross-fs marker only appears in action mode (compare mode doesn't have cross-fs concept)
   - Verbose mode shows file size and dup count consistently across both modes

Run final tests to confirm refactor is complete and behavior is preserved.
  </action>
  <verify>
`python3 run_tests.py` - all tests pass.
`python3 file_matcher.py test_dir1 test_dir2 -v` produces same output format as before.
`python3 file_matcher.py test_dir1 test_dir2 --action delete -v` produces same output format as before.
  </verify>
  <done>Code is cleaner with no duplication, all tests pass, visual output unchanged</done>
</task>

</tasks>

<verification>
1. All 198 tests pass: `python3 run_tests.py`
2. Compare mode output visually identical: `python3 file_matcher.py test_dir1 test_dir2`
3. Action mode output visually identical: `python3 file_matcher.py test_dir1 test_dir2 --action delete`
4. Verbose mode works in both: add `-v` flag to above commands
5. grep confirms shared function exists: `grep -n "def format_group_lines" file_matcher.py`
6. grep confirms delegation: `grep -n "format_group_lines" file_matcher.py` shows calls from both formatters
</verification>

<success_criteria>
- format_group_lines() helper function exists
- TextCompareFormatter uses shared helper (directly or via format_duplicate_group)
- TextActionFormatter uses shared helper (via format_duplicate_group)
- All 198 tests pass
- Visual output identical before and after refactor
- Less duplicated code in file_matcher.py
</success_criteria>

<output>
After completion, create `.planning/quick/002-refactor-group-output-reduce-duplication/002-SUMMARY.md`
</output>
