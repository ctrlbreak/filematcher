---
phase: quick-001
plan: 01
subsystem: output-formatting
tags: [formatters, edge-cases, refactoring]
dependency-graph:
  requires: [phase-06-json-output, phase-07-output-unification]
  provides: [unified-edge-case-output]
  affects: [phase-08-color-enhancement]
tech-stack:
  patterns: [formatter-abstraction, abc-pattern]
key-files:
  modified:
    - file_matcher.py
    - tests/test_cli.py
decisions:
  - id: DEC-Q001-01
    description: "Add format_empty_result to both CompareFormatter and ActionFormatter"
    rationale: "Action mode (dedup) needs empty result message through ActionFormatter, not CompareFormatter"
metrics:
  duration: "5 min"
  completed: "2026-01-23"
---

# Quick Task 001: Route Edge Case Prints Through Formatter Summary

Route 6 edge case print() calls through formatter abstractions to enable consistent formatting/coloring in Phase 8.

## What Was Done

### Task 1: Add Formatter Methods for Edge Cases
Added 6 new abstract methods to formatter ABCs with implementations:

**CompareFormatter ABC:**
- `format_empty_result(mode)` - Message when no matches found (compare or dedup mode)
- `format_unmatched_header()` - Header for unmatched files section

**ActionFormatter ABC:**
- `format_empty_result()` - Message when no duplicates found in dedup mode
- `format_user_abort()` - Message when user aborts execution
- `format_execute_prompt_separator()` - Blank line before execute prompt
- `format_execute_banner_line()` - Execute banner text

**Implementations:**
- TextCompareFormatter: Produces original output format
- JsonCompareFormatter: No-ops (JSON structure handles empty results)
- TextActionFormatter: Produces original output format
- JsonActionFormatter: No-ops (JSON structure handles these cases)

### Task 2: Route Edge Case Prints Through Formatters
Updated 6 call sites in main() to use formatter methods:

1. Dedup mode no duplicates: `formatter.format_empty_result()`
2. Execute prompt separator: `action_formatter.format_execute_prompt_separator()`
3. Execute banner: `action_formatter.format_execute_banner_line()`
4. User abort: `action_formatter.format_user_abort()`
5. Compare mode no matches: `compare_formatter.format_empty_result(mode="compare")`
6. Unmatched header: `compare_formatter.format_unmatched_header()`

Removed `if not args.json` guards since JSON formatters handle these as no-ops.

### Task 3: Add Tests for New Formatter Methods
Added `TestFormatterEdgeCases` class with 4 tests:
- `test_empty_result_compare_mode` - Verifies "No matching files found" message
- `test_empty_result_dedup_mode` - Verifies "No duplicates found" message
- `test_unmatched_header_text_mode` - Verifies unmatched section header
- `test_unmatched_header_json_mode` - Verifies JSON mode omits text header

## Commits

| Hash | Type | Description |
|------|------|-------------|
| 7c8efa2 | feat | Add formatter methods for edge cases |
| 21124a5 | refactor | Route edge case prints through formatters |
| 8d46057 | test | Add tests for formatter edge case methods |

## Test Results

- All 183 tests pass (179 existing + 4 new)
- New tests cover all edge case formatter methods

## Verification

1. No direct print() calls remain for edge cases outside formatter implementations
2. Text output identical to before (no behavioral change)
3. JSON output unchanged (formatters are no-ops for edge cases)

## Deviations from Plan

**1. [Rule 2 - Missing Critical] Added format_empty_result to ActionFormatter**
- **Found during:** Task 2
- **Issue:** Plan specified adding format_empty_result only to CompareFormatter, but dedup mode uses ActionFormatter
- **Fix:** Added format_empty_result to ActionFormatter ABC and both implementations
- **Files modified:** file_matcher.py
- **Commit:** 21124a5
