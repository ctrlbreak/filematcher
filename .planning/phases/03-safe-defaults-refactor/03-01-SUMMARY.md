---
phase: 03
plan: 01
subsystem: cli
tags: [preview-mode, execute-flag, confirmation, safety]
dependency-graph:
  requires: [02-01, 02-02, 02-03]
  provides: [preview-default, execute-flag, confirmation-prompt]
  affects: [03-02, 04-xx]
tech-stack:
  added: []
  patterns: [preview-by-default, interactive-confirmation]
key-files:
  created: []
  modified: [file_matcher.py]
decisions:
  - id: SAFE-01
    choice: "Preview mode default when --action specified"
    rationale: "Safety-first design"
  - id: SAFE-02
    choice: "--execute flag triggers execution with confirmation"
    rationale: "Explicit intent required for file modifications"
  - id: SAFE-03
    choice: "Remove --dry-run entirely"
    rationale: "Clean break to new terminology"
  - id: SAFE-04
    choice: "WOULD X labels in preview mode"
    rationale: "Clear indication of what would happen"
metrics:
  duration: "3m 29s"
  completed: "2026-01-19"
---

# Phase 3 Plan 1: Safe Defaults Refactor Summary

**One-liner:** Preview-by-default CLI with --execute flag, interactive confirmation, and WOULD X action labels.

## What Was Built

This plan refactored the CLI to make preview mode the default when `--action` is specified:

1. **Flag changes:**
   - Removed `--dry-run/-n` flag entirely
   - Added `--execute` flag (no short flag, intentionally verbose)
   - Added `--yes/-y` flag for skipping confirmation
   - Validation: `--execute` requires both `--master` and `--action`

2. **Banner updates:**
   - Renamed `DRY_RUN_BANNER` to `PREVIEW_BANNER`: "=== PREVIEW MODE - Use --execute to apply changes ==="
   - Added `EXECUTE_BANNER`: "=== EXECUTING ==="
   - Functions renamed: `format_dry_run_banner()` -> `format_preview_banner()`, added `format_execute_banner()`

3. **Action labels:**
   - Preview mode uses "WOULD X" labels: `[WOULD HARDLINK]`, `[WOULD SYMLINK]`, `[WOULD DELETE]`
   - Execute mode keeps `[DUP:action]` format for progress display

4. **Confirmation prompt:**
   - `confirm_execution()` function with TTY detection
   - Prompt: "Proceed? [y/N]"
   - Non-interactive mode detection with clear message
   - User abort returns exit code 0

5. **Statistics footer:**
   - Added `preview_mode` parameter
   - Shows "Use --execute to apply changes" hint in preview mode

## Commits

| Commit | Description |
|--------|-------------|
| 6268bbd | Replace --dry-run with --execute and --yes flags |
| 8a85a67 | Update banners and action labels for preview mode |
| 3ac2a06 | Add confirmation prompt and wire preview-default behavior |

## Key Files Modified

- **file_matcher.py** - All changes in this plan

## Deviations from Plan

None - plan executed exactly as written.

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| preview_mode parameter defaults to True | Safe default - always preview unless explicitly executing |
| TTY detection for confirmation | Scripts and CI need --yes flag, interactive users get prompt |
| Exit code 0 on abort | User abort is clean exit, not an error |
| No short flag for --execute | Intentionally verbose for safety |

## Technical Notes

- The `format_duplicate_group()` function now accepts `preview_mode` parameter
- The `format_statistics_footer()` function now accepts `preview_mode` parameter
- Existing dry-run tests will fail (expected) - Plan 03-02 updates them
- Execution placeholder prints "Execution not yet implemented." - Phase 4 implements actual file modifications

## Verification Results

All success criteria met:

- [x] --dry-run flag removed from CLI
- [x] --execute flag added (no short flag)
- [x] --yes/-y flag added
- [x] --execute requires --master and --action (validation)
- [x] Preview mode is default when --action specified
- [x] Banner shows "PREVIEW MODE - Use --execute to apply changes"
- [x] Action labels show "[WOULD X]" in preview mode
- [x] Statistics footer shows "--execute" hint
- [x] confirm_execution() prompts with Y/N
- [x] User abort exits with code 0

## Test Status

- 35 tests passing
- 1 test module fails to import (test_dry_run.py references removed DRY_RUN_BANNER)
- This is expected; Plan 03-02 will update tests

## Next Phase Readiness

Phase 3 Plan 2 can proceed:
- All preview-default infrastructure is in place
- Test module needs updating to use new constants and behavior
- No blockers

---

*Summary created: 2026-01-19*
