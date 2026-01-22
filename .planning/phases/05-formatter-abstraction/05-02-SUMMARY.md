---
phase: 05-formatter-abstraction
plan: 02
subsystem: formatting
tags: [action-mode, preview-mode, execute-mode, refactoring]

# Dependency graph
requires:
  - phase: 05-01
    provides: TextActionFormatter implementation with format_banner(), format_duplicate_group(), format_statistics(), format_warnings(), format_execution_summary()
provides:
  - Action mode output fully routed through TextActionFormatter
  - Preview and execute modes use formatter methods
  - Byte-identical output maintained (all 110 tests pass)
affects: [05-03, 06-json-output]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Formatter dependency injection via function parameters"
    - "Separate formatter instances for preview vs execute output"

key-files:
  created: []
  modified:
    - file_matcher.py

key-decisions:
  - "action_formatter always created with preview_mode=True for print_preview_output()"
  - "Separate action_formatter_exec instance for execution summary (preview_mode=False)"
  - "Preserved direct print() for 'No duplicates found' and blank lines (minimal refactoring scope)"

patterns-established:
  - "Formatter passed as parameter to helper functions for dependency injection"
  - "Helper functions accept formatter instead of calling format_* directly"

# Metrics
duration: 3min
completed: 2026-01-22
---

# Phase 05 Plan 02: Action Mode Formatter Integration Summary

**Action mode output fully routed through TextActionFormatter with preview banner, duplicate groups, statistics, and execution summary - all 110 tests pass with byte-identical output**

## Performance

- **Duration:** 3 min
- **Started:** 2026-01-22T01:44:13Z
- **Completed:** 2026-01-22T01:47:16Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- Preview mode output routes through formatter.format_banner(), formatter.format_duplicate_group(), formatter.format_statistics(), formatter.format_warnings()
- Execute mode execution summary routes through formatter.format_execution_summary()
- All 110 existing tests pass without modification (byte-identical output confirmed)
- master_results sorted by master file path for deterministic output (OUT-04)

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire TextActionFormatter into preview mode** - `ed3cffe` (feat)
2. **Task 2: Wire TextActionFormatter into execute mode** - `7db5ee0` (feat)

_Note: Task 2 execution summary changes were actually committed in a prior 05-03 commit (da75efa), so Task 2 only fixed the preview_mode issue._

## Files Created/Modified
- `file_matcher.py` - Wired TextActionFormatter into print_preview_output() helper and execution summary output

## Decisions Made

**1. action_formatter always preview_mode=True for print_preview_output()**
- Rationale: The print_preview_output() function always shows preview output (with PREVIEW banner and WOULD X labels), even when called from execute mode
- Impact: Fixed issue where execute mode was showing "=== EXECUTING ===" banner instead of "=== PREVIEW MODE ===" before the preview section

**2. Separate action_formatter_exec instance for execution summary**
- Rationale: Execution summary needs preview_mode=False to avoid "Use --execute to apply changes" footer
- Impact: Clean separation between preview output and execution summary output

**3. Preserved direct print() for edge cases**
- Rationale: "No duplicates found." message and blank lines between groups kept as direct print() to minimize refactoring scope
- Impact: Smaller diff, lower risk of breaking changes

## Deviations from Plan

None - plan executed exactly as written.

Note: During implementation, discovered that execution summary formatter changes were already committed in a prior 05-03 commit. This was not a deviation but a sequencing issue - the work was done, just in a different commit.

## Issues Encountered

**Issue: Execute mode showed wrong banner**
- **Problem:** When action_formatter created with `preview_mode=not args.execute`, execute mode created formatter with preview_mode=False, causing print_preview_output() to show "=== EXECUTING ===" instead of "=== PREVIEW MODE ==="
- **Resolution:** Changed action_formatter to always use preview_mode=True since print_preview_output() always shows preview
- **Committed in:** 7db5ee0 (Task 2)

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Action mode output fully abstracted through formatter
- Ready for Phase 6 JSON output implementation
- TextActionFormatter can be subclassed or replaced with JSONActionFormatter
- Compare mode still needs formatter integration (05-03 or later)

**Blockers/concerns:** None

---
*Phase: 05-formatter-abstraction*
*Completed: 2026-01-22*
