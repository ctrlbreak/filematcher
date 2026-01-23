---
phase: 06-json-output
plan: 02
subsystem: cli
tags: [json, argparse, formatter, output]

# Dependency graph
requires:
  - phase: 06-01
    provides: JsonCompareFormatter and JsonActionFormatter classes
provides:
  - --json CLI flag for machine-readable output
  - JSON output in compare mode and action mode
  - Proper flag interaction handling (--summary, --verbose, --show-unmatched)
affects: [07-output-unification, 08-color-enhancement]

# Tech tracking
tech-stack:
  added: []
  patterns: [conditional formatter selection, stderr for progress in JSON mode]

key-files:
  modified: [file_matcher.py]

key-decisions:
  - "Logger output to stderr when --json used (keep stdout clean for JSON)"
  - "--json --execute requires --yes flag (no interactive prompts in JSON mode)"
  - "JSON formatters always collect file sizes (needed for space calculations)"

patterns-established:
  - "Conditional formatter instantiation based on --json flag"
  - "print() statements conditionally skipped in JSON mode"

# Metrics
duration: 3min
completed: 2026-01-23
---

# Phase 06 Plan 02: --json CLI Flag and Wiring Summary

**Working `--json` flag wired into main() with proper formatter selection, flag validation, and stderr/stdout separation**

## Performance

- **Duration:** 3 min
- **Started:** 2026-01-23T09:52:13Z
- **Completed:** 2026-01-23T09:55:01Z
- **Tasks:** 3 (2 with code changes, 1 verification-only)
- **Files modified:** 1

## Accomplishments

- Added `--json`/`-j` CLI flag for machine-readable JSON output
- Wired JsonCompareFormatter for compare mode (no --action)
- Wired JsonActionFormatter for action mode (--action specified)
- Added validation: `--json --execute` requires `--yes` flag
- Progress messages sent to stderr when --json is used
- All 113 existing tests pass (text output unchanged)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add --json CLI argument** - `e454a03` (feat)
2. **Task 2: Wire JSON formatters into main()** - `168ab57` (feat)
3. **Task 3: Handle --json flag interactions** - No commit (verified, no code changes needed)

## Files Modified

- `file_matcher.py` - Added --json argument, conditional formatter selection, stderr logging for JSON mode

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Logger to stderr when --json | Keep stdout clean for JSON parsing; Unix convention for progress/debug |
| --json --execute requires --yes | No interactive prompts possible when outputting JSON |
| Always collect file_sizes with --json | JsonActionFormatter needs sizes for space calculations |

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Next Phase Readiness

- JSON output fully functional for both compare and action modes
- All flag combinations verified working
- Ready for Phase 06-03: JSON output tests (if planned)
- Ready for Phase 07: Output Unification

---
*Phase: 06-json-output*
*Completed: 2026-01-23*
