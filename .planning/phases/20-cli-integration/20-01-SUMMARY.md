---
phase: 20
plan: 01
subsystem: cli
tags: [validation, interactive, fail-fast, banner]

dependency_graph:
  requires:
    - "Phase 19: Interactive core (prompt_for_group, interactive_execute)"
  provides:
    - "Fail-fast flag validation for interactive mode"
    - "format_execute_banner function for banner display"
  affects:
    - "Phase 20-02: Batch/interactive mode routing"

tech_stack:
  added: []
  patterns:
    - "Fail-fast validation pattern (parser.error before file scanning)"

key_files:
  created: []
  modified:
    - "filematcher/cli.py"
    - "filematcher/formatters.py"
    - "tests/test_safe_defaults.py"

decisions:
  - topic: "Non-TTY validation timing"
    choice: "Fail at parser level with exit code 2"
    rationale: "Fail-fast before expensive file scanning"
  - topic: "Updated existing test"
    choice: "Modified test_non_tty_defaults_to_abort for new behavior"
    rationale: "Old behavior was soft fail, new is hard fail-fast"

metrics:
  duration: "3 minutes"
  completed: "2026-01-30"
---

# Phase 20 Plan 01: Flag Validation and Banner Summary

Fail-fast flag validation and format_execute_banner function for interactive execute mode.

## One-liner

Added fail-fast validation for --quiet/--json/non-TTY + --execute conflicts, plus format_execute_banner() for displaying execute mode statistics.

## Changes Made

### Task 1: Fail-fast Flag Validation (cli.py)

Added three validation checks immediately after `parser.parse_args()`:

1. **--quiet + --execute without --yes**: Error "--quiet and interactive mode are incompatible"
2. **Non-TTY stdin + --execute without --yes**: Error "stdin is not a terminal"
3. **--json + --execute without --yes**: (Already existed) Error message

All validations use `parser.error()` for consistent exit code 2 and happen BEFORE `find_matching_files()` is called.

### Task 2: format_execute_banner Function (formatters.py)

Added function to format execute mode banner:

```python
def format_execute_banner(
    action: str,
    group_count: int,
    duplicate_count: int,
    space_bytes: int,
    color_config: ColorConfig | None = None
) -> tuple[str, str]:
```

Returns tuple of (banner_line, separator_line):
- Banner: `"{bold action} mode: X groups, Y files, Z to save"`
- Separator: 40-character dashed line

Also added:
- `EXECUTE_BANNER_SEPARATOR` constant
- `bold` import from colors module

### Task 3: Unit Tests (test_safe_defaults.py)

Added `TestInteractiveFlagValidation` class with 5 tests:
- `test_quiet_execute_without_yes_fails`
- `test_quiet_execute_with_yes_succeeds`
- `test_non_tty_execute_without_yes_fails`
- `test_json_execute_without_yes_fails`
- `test_json_execute_with_yes_succeeds`

Updated existing `test_non_tty_defaults_to_abort` to expect fail-fast behavior (exit code 2) instead of soft abort (return 0).

## Deviations from Plan

### Modified Existing Test

**1. [Rule 1 - Bug] Updated test_non_tty_defaults_to_abort**

- **Found during:** Task 3
- **Issue:** Existing test expected old behavior (soft fail with return 0) but new fail-fast validation exits with code 2
- **Fix:** Updated test to expect SystemExit with code 2 and verify error message contains "stdin" and "terminal"
- **Files modified:** tests/test_safe_defaults.py
- **Commit:** 4cc5ac1

This is correct behavior per the plan's requirement for fail-fast validation BEFORE file scanning.

## Test Results

All 278 tests pass (273 existing + 5 new).

## Verification

```bash
# Non-TTY validation (exit code 2)
echo "" | python3 -m filematcher dir1 dir2 --action delete --execute
# error: stdin is not a terminal

# --quiet validation (exit code 2)
python3 -m filematcher dir1 dir2 --action delete --execute --quiet
# error: --quiet and interactive mode are incompatible

# --json validation (exit code 2)
python3 -m filematcher dir1 dir2 --action delete --execute --json
# error: --json with --execute requires --yes flag...

# Fail-fast timing (< 0.1s, not scanning /tmp)
time (echo "" | python3 -m filematcher /tmp /tmp --action delete --execute)
# 0.056 total
```

## Commits

| Hash | Type | Description |
|------|------|-------------|
| 3b9cae0 | feat | add fail-fast flag validation for interactive mode |
| ba56871 | feat | add format_execute_banner function |
| 4cc5ac1 | test | add unit tests for interactive flag validation |

## Next Phase Readiness

Ready for 20-02: Mode routing logic. The validation layer ensures invalid flag combinations are rejected early, and format_execute_banner is available for banner display in both interactive and batch modes.
