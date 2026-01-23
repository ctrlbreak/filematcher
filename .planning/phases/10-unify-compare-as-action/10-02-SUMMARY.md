---
phase: 10-unify-compare-as-action
plan: 02
subsystem: formatter
tags: [actionformatter, json, text-output]

# Dependency graph
requires:
  - phase: 10-01
    provides: compare action added to argparse choices with default
  - phase: 05-formatter-abstraction
    provides: ActionFormatter ABC base class
provides:
  - ActionFormatter hierarchy supports compare action
  - TextActionFormatter produces "Compare mode:" header without banner
  - JsonActionFormatter produces compare-compatible JSON schema
affects: [10-03]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - action parameter in formatter constructor for action-specific behavior
    - conditional schema generation in JSON finalize()

key-files:
  created: []
  modified:
    - file_matcher.py

key-decisions:
  - "Standardized __init__ signature: (verbose, preview_mode, action)"
  - "Compare mode skips PREVIEW banner (not a preview of destructive actions)"
  - "JsonActionFormatter stores hash algorithm for compare mode JSON"

patterns-established:
  - "Action parameter flows from CLI to formatter to format methods"
  - "finalize() checks _action to produce appropriate JSON schema"

# Metrics
duration: 4min
completed: 2026-01-23
---

# Phase 10 Plan 02: Extend ActionFormatter for Compare Action Summary

**TextActionFormatter shows "Compare mode:" header without banner; JsonActionFormatter produces compare-compatible JSON schema with hashAlgorithm, matches, summary fields**

## Performance

- **Duration:** 4 min (264 seconds)
- **Started:** 2026-01-23T16:33:07Z
- **Completed:** 2026-01-23T16:37:31Z
- **Tasks:** 3
- **Files modified:** 1

## Accomplishments

- Added action parameter to ActionFormatter ABC with standardized signature order
- TextActionFormatter skips PREVIEW/EXECUTING banner for compare action
- TextActionFormatter shows "Compare mode:" header instead of "Action mode (STATE):"
- JsonActionFormatter produces compare-compatible JSON with hashAlgorithm, matches, summary fields
- Updated all formatter creation sites to pass action parameter

## Task Commits

Each task was committed atomically:

1. **Task 3: Update ActionFormatter ABC for action parameter** - `a1bc96f` (feat)
2. **Task 1: Update TextActionFormatter for compare action** - `72cef70` (feat)
3. **Task 2: Update JsonActionFormatter for compare action** - `c397ade` (feat)

_Note: Task 3 executed first as it was a prerequisite for Tasks 1 and 2_

## Files Created/Modified

- `file_matcher.py` - Added action parameter to ActionFormatter, TextActionFormatter, JsonActionFormatter; updated format_banner() and format_unified_header(); added set_hash_algorithm() and compare mode JSON schema in finalize()

## Decisions Made

- **Standardized __init__ signature order**: (verbose, preview_mode, action) with subclass-specific params (like color_config) after base params - ensures consistent call pattern
- **Compare mode skips banner**: Compare is not a preview of destructive actions, so PREVIEW banner is inappropriate
- **JsonActionFormatter stores hash algorithm**: Added _hash_algorithm attribute and set_hash_algorithm() method to capture hash algo for compare mode JSON output

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - straightforward implementation following plan specifications.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- ActionFormatter hierarchy now supports compare action
- Ready for Phase 10 Plan 03: Wire compare action to ActionFormatter
- All 198 tests passing
- Text output verified: "Compare mode:" header without PREVIEW banner
- JSON output verified: Valid JSON with compare-compatible schema ready

---
*Phase: 10-unify-compare-as-action*
*Completed: 2026-01-23*
