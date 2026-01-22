---
phase: 05-formatter-abstraction
plan: 01
subsystem: output
tags: [abc, formatters, refactoring, text-output]

# Dependency graph
requires:
  - phase: 04-audit-logging
    provides: "Complete file matcher with actions and logging"
provides:
  - "OutputFormatter ABC hierarchy (CompareFormatter, ActionFormatter)"
  - "TextCompareFormatter for compare mode output"
  - "TextActionFormatter for action mode output"
  - "Foundation for JSON output (Phase 6)"
affects: [06-json-output, 07-output-unification]

# Tech tracking
tech-stack:
  added: [abc module]
  patterns: [ABC-based formatter protocol, delegation pattern for text formatters]

key-files:
  created: []
  modified: [file_matcher.py]

key-decisions:
  - "Used ABC instead of typing.Protocol for explicit inheritance and runtime checks"
  - "Separate CompareFormatter and ActionFormatter ABCs reflect distinct output structures"
  - "TextCompareFormatter implements inline (no existing format_* functions to delegate to)"
  - "TextActionFormatter delegates to existing format_* functions for byte-identical output"
  - "All file lists sorted for deterministic output (OUT-04)"

patterns-established:
  - "Formatter lifecycle: Instantiated with config (verbose, preview_mode), used via abstract methods"
  - "Delegation pattern: TextActionFormatter delegates to existing format_duplicate_group() and format_statistics_footer()"
  - "Inline pattern: TextCompareFormatter implements formatting directly with print statements"

# Metrics
duration: 6min
completed: 2026-01-22
---

# Phase 5 Plan 1: Formatter Abstraction Foundation Summary

**ABC hierarchy with CompareFormatter and ActionFormatter base classes, plus TextCompareFormatter and TextActionFormatter implementations for byte-identical text output**

## Performance

- **Duration:** 6 min
- **Started:** 2026-01-22T05:39:56Z
- **Completed:** 2026-01-22T05:46:02Z
- **Tasks:** 3
- **Files modified:** 1 (file_matcher.py)

## Accomplishments
- Defined CompareFormatter ABC with 5 abstract methods for compare mode output
- Defined ActionFormatter ABC with 6 abstract methods for action mode output
- Implemented TextCompareFormatter with inline formatting matching current output
- Implemented TextActionFormatter delegating to existing format_* functions
- Verified all 106 existing tests pass without modification (byte-identical output)

## Task Commits

Each task was committed atomically:

1. **Task 1: Define CompareFormatter and ActionFormatter ABCs** - `ab0bbe9` (feat)
2. **Task 2: Implement TextCompareFormatter** - `ebbb1e4` (feat)
3. **Task 3: Implement TextActionFormatter** - `ab78260` (feat)

## Files Created/Modified
- `file_matcher.py` - Added ABC imports, defined CompareFormatter and ActionFormatter base classes, implemented TextCompareFormatter and TextActionFormatter

## Decisions Made

**1. ABC vs typing.Protocol**
- Used `abc.ABC` with `@abstractmethod` decorators instead of `typing.Protocol`
- Rationale: Explicit inheritance with runtime checks, more familiar pattern, aligns with CONTEXT.md decision

**2. Separate ABCs for compare and action modes**
- CompareFormatter handles compare mode (no action specified, showing file matches)
- ActionFormatter handles action mode (preview/execute with master/duplicate relationships)
- Rationale: Distinct output structures and method signatures between modes

**3. Inline vs delegation implementation strategy**
- TextCompareFormatter implements inline with print statements (no existing functions to delegate to)
- TextActionFormatter delegates to existing format_duplicate_group() and format_statistics_footer()
- Rationale: Preserves byte-identical output, leverages battle-tested functions

**4. Sorting for determinism (OUT-04)**
- All file lists sorted before output
- TextCompareFormatter sorts in format_match_group() and format_unmatched()
- TextActionFormatter relies on existing functions (already sort) plus sorts failed_list
- Rationale: Ensures deterministic output for testing and user consistency

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Foundation complete for JSON output (Phase 6):**
- ABC hierarchy provides structure for JsonCompareFormatter and JsonActionFormatter
- TextFormatter implementations demonstrate the pattern
- All existing tests pass (confirms output unchanged)

**Ready for Phase 6 (JSON output):**
- Implement JsonCompareFormatter and JsonActionFormatter
- Wire formatters into main() with --json flag
- Add JSON schema documentation

**No blockers or concerns**

---
*Phase: 05-formatter-abstraction*
*Completed: 2026-01-22*
