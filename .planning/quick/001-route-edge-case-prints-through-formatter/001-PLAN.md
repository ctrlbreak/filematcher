---
phase: quick-001
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - file_matcher.py
  - tests/test_cli.py
autonomous: true

must_haves:
  truths:
    - "All user-visible messages route through formatter abstractions"
    - "No direct print() calls for empty results, aborts, or section headers"
    - "Text and JSON formatters handle all edge cases appropriately"
  artifacts:
    - path: "file_matcher.py"
      provides: "New formatter methods and updated call sites"
      contains: "format_empty_result"
    - path: "tests/test_cli.py"
      provides: "Coverage for new formatter methods"
      contains: "test_empty_result"
  key_links:
    - from: "main() in file_matcher.py"
      to: "CompareFormatter.format_empty_result()"
      via: "method call instead of direct print"
      pattern: "compare_formatter\\.format_empty_result"
---

<objective>
Route 6 edge case print() calls through formatter abstractions to enable consistent formatting/coloring in Phase 8.

Purpose: Technical debt cleanup from Phase 7 verification - all user-visible output should flow through formatters for consistent styling control.

Output: Updated formatter ABCs with new methods, implementations in Text/Json formatters, and updated call sites in main().
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@file_matcher.py (lines 32-250 for formatter ABCs, lines 1930-2200 for call sites)
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add formatter methods for edge cases</name>
  <files>file_matcher.py</files>
  <action>
Add new abstract methods to formatter ABCs and implement them:

**CompareFormatter ABC (add after format_statistics):**
```python
@abstractmethod
def format_empty_result(self, mode: str = "compare") -> None:
    """Format message when no matches found.

    Args:
        mode: "compare" for compare mode, "dedup" for dedup mode
    """
    pass

@abstractmethod
def format_unmatched_header(self) -> None:
    """Format the header for unmatched files section."""
    pass
```

**TextCompareFormatter implementation:**
```python
def format_empty_result(self, mode: str = "compare") -> None:
    if mode == "dedup":
        print("No duplicates found.")
    else:
        print("No matching files found.")

def format_unmatched_header(self) -> None:
    print("\nFiles with no content matches:")
    print("==============================")
```

**JsonCompareFormatter implementation:**
- format_empty_result: no-op (JSON structure handles empty results)
- format_unmatched_header: no-op (JSON doesn't need section headers)

**ActionFormatter ABC (add after format_execution_summary):**
```python
@abstractmethod
def format_user_abort(self) -> None:
    """Format message when user aborts execution."""
    pass

@abstractmethod
def format_execute_prompt_separator(self) -> None:
    """Format blank line/separator before execute prompt."""
    pass

@abstractmethod
def format_execute_banner_line(self) -> str:
    """Return the execute banner text (for caller to print or embed)."""
    pass
```

**TextActionFormatter implementation:**
```python
def format_user_abort(self) -> None:
    print("Aborted. No changes made.")

def format_execute_prompt_separator(self) -> None:
    print()

def format_execute_banner_line(self) -> str:
    return format_execute_banner()
```

**JsonActionFormatter implementation:**
- format_user_abort: no-op (JSON reports via status field)
- format_execute_prompt_separator: no-op
- format_execute_banner_line: return empty string
  </action>
  <verify>grep -n "format_empty_result\|format_user_abort\|format_unmatched_header" file_matcher.py | wc -l should show 12+ occurrences (ABCs + impls + calls)</verify>
  <done>All 6 new abstract methods defined in ABCs with implementations in Text and Json formatter classes</done>
</task>

<task type="auto">
  <name>Task 2: Route edge case prints through formatters</name>
  <files>file_matcher.py</files>
  <action>
Update the 6 call sites in main() to use new formatter methods:

**Line ~1939 (dedup mode, no duplicates):**
Replace:
```python
if not args.json:
    print("No duplicates found.")
```
With:
```python
formatter.format_empty_result(mode="dedup")
```

**Line ~2083 (user abort):**
Replace:
```python
print("Aborted. No changes made.")
```
With:
```python
action_formatter.format_user_abort()
```

**Line ~2186 (compare mode, no matches):**
Replace:
```python
if not args.json:
    print("No matching files found.")
```
With:
```python
compare_formatter.format_empty_result(mode="compare")
```

**Lines ~2073, 2076 (execute prompt separator and banner):**
Replace:
```python
print()
print(format_execute_banner())
```
With:
```python
action_formatter.format_execute_prompt_separator()
print(action_formatter.format_execute_banner_line())
```

**Lines ~2196-2197 (unmatched section header):**
Replace:
```python
if not args.json:
    print("\nFiles with no content matches:")
    print("==============================")
```
With:
```python
compare_formatter.format_unmatched_header()
```

Note: The `if not args.json` guards can be removed since JSON formatters handle these as no-ops.
  </action>
  <verify>grep -n "print.*No duplicates\|print.*Aborted\|print.*No matching\|print.*no content matches" file_matcher.py should return 0 lines</verify>
  <done>All 6 edge case print() calls replaced with formatter method calls</done>
</task>

<task type="auto">
  <name>Task 3: Add tests for new formatter methods</name>
  <files>tests/test_cli.py</files>
  <action>
Add test coverage for new formatter methods:

```python
class TestFormatterEdgeCases(BaseFileMatcherTest):
    """Tests for edge case formatter methods added for output unification."""

    def test_empty_result_compare_mode(self):
        """Test format_empty_result in compare mode."""
        # Create dirs with no matching files
        self.create_file('dir1/unique1.txt', 'content1')
        self.create_file('dir2/unique2.txt', 'content2')

        result = subprocess.run(
            ['python', 'file_matcher.py', self.dir1, self.dir2],
            capture_output=True, text=True
        )
        self.assertIn("No matching files found", result.stdout)

    def test_empty_result_dedup_mode(self):
        """Test format_empty_result in dedup mode."""
        # Create dir with no duplicates
        self.create_file('dir1/file1.txt', 'unique1')
        self.create_file('dir1/file2.txt', 'unique2')

        result = subprocess.run(
            ['python', 'file_matcher.py', self.dir1, self.dir1, '--action', 'hardlink'],
            capture_output=True, text=True
        )
        self.assertIn("No duplicates found", result.stdout)

    def test_unmatched_header_text_mode(self):
        """Test format_unmatched_header routes through formatter."""
        self.create_file('dir1/unique.txt', 'unique')
        self.create_file('dir2/other.txt', 'other')

        result = subprocess.run(
            ['python', 'file_matcher.py', self.dir1, self.dir2, '-u'],
            capture_output=True, text=True
        )
        self.assertIn("Files with no content matches", result.stdout)

    def test_unmatched_header_json_mode(self):
        """Test JSON mode doesn't output unmatched header text."""
        self.create_file('dir1/unique.txt', 'unique')
        self.create_file('dir2/other.txt', 'other')

        result = subprocess.run(
            ['python', 'file_matcher.py', self.dir1, self.dir2, '-u', '--json'],
            capture_output=True, text=True
        )
        # JSON mode should NOT have the text header
        self.assertNotIn("Files with no content matches", result.stdout)
        # But should have valid JSON
        import json
        output = json.loads(result.stdout)
        self.assertIn('unmatched', output)
```

Place these tests in the existing test_cli.py file, after the existing test classes.
  </action>
  <verify>python3 -m pytest tests/test_cli.py -v -k "test_empty_result or test_unmatched_header" should pass all 4 tests</verify>
  <done>4 new tests covering format_empty_result (compare and dedup modes) and format_unmatched_header (text and json modes)</done>
</task>

</tasks>

<verification>
1. Run full test suite: `python3 run_tests.py` - all tests pass
2. Manual verification of each edge case:
   - Compare mode with no matches: `python file_matcher.py /tmp/empty1 /tmp/empty2`
   - Dedup mode with no duplicates: `python file_matcher.py dir --action hardlink`
   - Unmatched header: `python file_matcher.py dir1 dir2 -u`
   - JSON mode suppresses text headers: `python file_matcher.py dir1 dir2 -u --json`
3. No direct print() calls remain for these edge cases: `grep -n "print.*No duplicates\|print.*Aborted\|print.*No matching" file_matcher.py` returns nothing
</verification>

<success_criteria>
- All 6 edge case print() calls route through formatter methods
- Text formatters produce identical output to before (no behavioral change)
- JSON formatters handle edge cases as no-ops (structure unchanged)
- All existing tests pass
- New tests cover the formatter edge case methods
</success_criteria>

<output>
After completion, create `.planning/quick/001-route-edge-case-prints-through-formatter/001-SUMMARY.md`
</output>
