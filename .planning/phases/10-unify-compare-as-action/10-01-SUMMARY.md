---
phase: 10-unify-compare-as-action
plan: 01
subsystem: cli
tags: [argparse, validation, action-model]

# Dependency graph
requires:
  - phase: 05-formatter-abstraction
    provides: CompareFormatter and ActionFormatter ABCs
provides:
  - compare as explicit action choice
  - default='compare' for backward compatibility
  - validation preventing --execute with compare
affects: [10-02, 10-03]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - action-based CLI model where compare is a valid action

key-files:
  created: []
  modified:
    - file_matcher.py
    - tests/test_safe_defaults.py

key-decisions:
  - "compare is default action (not None)"
  - "master_path only set for modifying actions"

patterns-established:
  - "Action choices: compare|hardlink|symlink|delete with compare as default"

# Metrics
duration: 2min
completed: 2026-01-23
---

# Phase 10 Plan 01: Add Compare Action Summary

**Added compare to --action choices with default value and validation for incompatible flags**

## Performance

- **Duration:** 2 min (93 seconds)
- **Started:** 2026-01-23T16:28:59Z
- **Completed:** 2026-01-23T16:30:32Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments

- Added 'compare' to --action choices enabling explicit `--action compare` for scripting
- Set default='compare' maintaining backward compatibility for users running without flags
- Added validation preventing --execute with compare action (clear error message)
- Updated master_path logic to only set for modifying actions (hardlink, symlink, delete)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add compare to action choices with default** - `0430a22` (feat)
2. **Task 2: Update validation for compare action** - `aff9552` (feat)
3. **Task 3: Verify backward compatibility** - `38cd10e` (test)

## Files Created/Modified

- `file_matcher.py` - Updated argparse --action argument and validation logic
- `tests/test_safe_defaults.py` - Updated test for new validation behavior

## Decisions Made

- **compare is default action**: Rather than keeping None as default and checking `if args.action`, we set `default='compare'` so action always has a meaningful value
- **master_path only for modifying actions**: Changed condition from `if args.action:` to `if args.action in ('hardlink', 'symlink', 'delete'):` since compare action doesn't need master designation

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated master_path condition**
- **Found during:** Task 2 (validation update)
- **Issue:** `if args.action:` would always be true with default='compare', setting master_path unnecessarily
- **Fix:** Changed to `if args.action in ('hardlink', 'symlink', 'delete'):`
- **Files modified:** file_matcher.py
- **Verification:** Default mode works correctly, action mode works correctly
- **Committed in:** aff9552 (Task 2 commit)

**2. [Rule 1 - Bug] Updated test for new validation message**
- **Found during:** Task 3 (backward compatibility verification)
- **Issue:** test_execute_requires_action expected old error message
- **Fix:** Renamed test and updated expected error message
- **Files modified:** tests/test_safe_defaults.py
- **Verification:** All 198 tests pass
- **Committed in:** 38cd10e (Task 3 commit)

---

**Total deviations:** 2 auto-fixed (2 bugs)
**Impact on plan:** Both fixes necessary for correctness. No scope creep.

## Issues Encountered

None - plan executed smoothly.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- compare action now recognized by argparse
- Ready for Phase 10 Plan 02: Wire compare action to CompareFormatter
- All 198 tests passing

---
*Phase: 10-unify-compare-as-action*
*Completed: 2026-01-23*
