---
phase: quick-007
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - file_matcher.py
  - tests/test_color_output.py
autonomous: true

must_haves:
  truths:
    - "Colors are applied at print time, not via string parsing"
    - "TTY detection is centralized in ColorConfig"
    - "All output flows through formatters, no raw print() in main()"
    - "format_duplicate_group returns structured data, not pre-formatted strings"
  artifacts:
    - path: "file_matcher.py"
      provides: "Refactored output formatting"
      contains: "class GroupLine"
  key_links:
    - from: "TextActionFormatter.format_duplicate_group"
      to: "format_group_lines"
      via: "returns list[GroupLine] instead of list[str]"
      pattern: "GroupLine"
---

<objective>
Refactor output formatting to eliminate string-parsing for color application

Purpose: The current TextActionFormatter parses formatted strings looking for "MASTER:" and "[!cross-fs]" to apply colors after the fact. This is fragile and couples formatting to colorization. Refactor to use structured intermediate representation.

Output: Clean separation between data formatting and color/output handling
</objective>

<execution_context>
@/Users/patrick/.claude/get-shit-done/workflows/execute-plan.md
@/Users/patrick/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@file_matcher.py (lines 829-936 - TextActionFormatter.format_duplicate_group)
@file_matcher.py (lines 1133-1235 - format_group_lines and format_duplicate_group)
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create GroupLine dataclass and refactor format_group_lines</name>
  <files>file_matcher.py</files>
  <action>
1. Add a simple dataclass near the top of the file (after ColorConfig):

```python
from dataclasses import dataclass

@dataclass
class GroupLine:
    """Structured line for group output, enabling clean color application."""
    line_type: str  # "master", "duplicate", "hash", "other"
    label: str      # "MASTER:", "WOULD DELETE:", etc.
    path: str       # File path
    warning: str = ""  # "[!cross-fs]" or empty
    prefix: str = ""   # "[1/3] " progress prefix or empty
    indent: str = ""   # "    " for duplicates or empty
```

2. Refactor `format_group_lines()` (around line 1133) to return `list[GroupLine]` instead of `list[str]`:
   - Primary line becomes GroupLine(line_type="master", label=f"{primary_label}:", path=primary_file, ...)
   - Secondary lines become GroupLine(line_type="duplicate", label=f"{label}:", path=path, warning=cross_fs_marker, indent="    ")
   - Verbose info can be handled by adding suffix to path or separate line type

3. Refactor `format_duplicate_group()` (around line 1181) similarly - it calls format_group_lines, so it should also return `list[GroupLine]`.

4. Add a helper function `render_group_line(line: GroupLine, cc: ColorConfig) -> str` that applies colors based on line_type:
   - "master": bold_green label + green path
   - "duplicate": bold_yellow label + yellow path + red warning
   - "hash": dim the whole line
   - "other": no color

This separates structure (GroupLine) from presentation (render_group_line).
  </action>
  <verify>
Run `python3 -c "from file_matcher import GroupLine, format_group_lines, render_group_line"` succeeds.
  </verify>
  <done>GroupLine dataclass exists, format_group_lines returns list[GroupLine], render_group_line applies colors</done>
</task>

<task type="auto">
  <name>Task 2: Update TextActionFormatter to use GroupLine</name>
  <files>file_matcher.py</files>
  <action>
1. Simplify `TextActionFormatter.format_duplicate_group()` (lines 829-936):
   - Remove the string-parsing loop (lines 894-930 that check "MASTER:" in line)
   - Call format_duplicate_group() which now returns list[GroupLine]
   - Add hash line as GroupLine(line_type="hash", label="  Hash:", path=f"{file_hash[:10]}...", ...)
   - Add progress prefix by setting line.prefix on first line (for TTY inline mode)
   - Loop through lines and call render_group_line(line, self.cc) then print

2. The TTY inline progress logic (lines 878-889) stays but operates on GroupLine objects:
   - First GroupLine gets prefix = f"[{group_index}/{total_groups}] "
   - render_group_line handles outputting prefix + label + path

3. Ensure JsonActionFormatter still works (it may need GroupLine.to_dict() or just access fields directly for JSON building).

This eliminates all string searches for "MASTER:", "[!cross-fs]", etc.
  </action>
  <verify>
Run existing tests: `python3 -m tests.test_color_output` and `python3 -m tests.test_output_unification` pass.
Run `python3 file_matcher.py test_dir1 test_dir2 -a hardlink` shows colored output correctly.
  </verify>
  <done>TextActionFormatter uses GroupLine, no string parsing for color application</done>
</task>

<task type="auto">
  <name>Task 3: Centralize TTY detection and clean up main() prints</name>
  <files>file_matcher.py</files>
  <action>
1. Add `is_tty` property to ColorConfig class:
```python
@property
def is_tty(self) -> bool:
    """Check if output stream is a TTY."""
    try:
        return self.stream.isatty()
    except AttributeError:
        return False
```

2. Replace scattered TTY checks throughout the code with ColorConfig.is_tty:
   - Line 859: `is_tty = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()` -> use formatter's self.cc.is_tty
   - Lines 2351, 2356, 2450: TTY checks in main() -> pass color_config and use its is_tty

3. Route raw print() calls in main() through formatter methods:
   - Lines 2305-2307 (unmatched summary in summary mode) -> add to TextActionFormatter
   - Line 2353 (blank line between groups) -> already in formatter logic, just clean up
   - Line 2487 (banner_line print) -> use formatter method
   - Line 2506 (blank line after header) -> use formatter method

4. Ensure that after all changes:
   - ColorConfig is the single source for TTY detection
   - Formatters handle all output, main() just orchestrates

Note: Keep the existing behavior unchanged - this is a refactor, not a behavior change. All tests must pass.
  </action>
  <verify>
Run full test suite: `python3 run_tests.py` - all 206 tests pass.
Run with TTY simulation: output looks identical to before.
Run with pipe: `python3 file_matcher.py test_dir1 test_dir2 | cat` shows no color codes.
  </verify>
  <done>TTY detection centralized in ColorConfig.is_tty, no raw print() in main() output paths</done>
</task>

</tasks>

<verification>
1. All tests pass: `python3 run_tests.py`
2. Compare mode output unchanged: `python3 file_matcher.py test_dir1 test_dir2`
3. Action mode with colors: `python3 file_matcher.py test_dir1 test_dir2 -a hardlink --color`
4. Piped output (no colors): `python3 file_matcher.py test_dir1 test_dir2 -a hardlink | cat`
5. JSON output: `python3 file_matcher.py test_dir1 test_dir2 -a hardlink --json`
6. Code inspection: No string searches for "MASTER:", "[!cross-fs]" in color application
</verification>

<success_criteria>
- GroupLine dataclass provides structured representation
- render_group_line applies colors based on line_type, not string content
- ColorConfig.is_tty centralizes TTY detection
- All 206 tests pass
- Output behavior unchanged (refactor, not feature change)
</success_criteria>

<output>
After completion, create `.planning/quick/007-refactor-output-formatting-for-modularit/007-SUMMARY.md`
</output>
