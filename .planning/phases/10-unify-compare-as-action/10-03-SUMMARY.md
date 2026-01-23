---
phase: 10
plan: 03
subsystem: output-formatting
tags: [unification, formatter, compare, action]

dependency-graph:
  requires: [10-01, 10-02]
  provides: ["unified-action-flow", "compare-via-actionformatter"]
  affects: [10-04]

tech-stack:
  added: []
  patterns: ["unified-code-path"]

key-files:
  created: []
  modified:
    - file_matcher.py

decisions:
  - key: master_path_always_set
    choice: "Always set master_path for unified flow"
    rationale: "Allows single code path for all action types"
  - key: compare_specific_methods
    choice: "Add format_compare_summary and format_unmatched_section to ActionFormatter"
    rationale: "Compare mode needs different summary format and unmatched file support"
  - key: execute_mode_guard
    choice: "execute_mode = args.action != 'compare' and args.execute"
    rationale: "Compare action cannot enter execute mode (validation enforced in 10-01)"

metrics:
  duration: 8 min
  completed: 2026-01-23
---

# Phase 10 Plan 03: Unify Main Flow Summary

Compare mode now flows through the ActionFormatter code path instead of CompareFormatter.

## One-liner

Unified main() to route all modes (compare, hardlink, symlink, delete) through ActionFormatter code path with compare-specific formatting methods.

## What Changed

### Task 1: Always set master_path for unified action flow

**Commit:** 49ad75c

- Removed conditional `if args.action in ('hardlink', 'symlink', 'delete'):` check
- master_path now always set to `Path(args.dir1).resolve()`
- Comment updated to explain compare action uses master_path for display only
- Added compare-specific handling in `format_duplicate_group` (DUPLICATE label)
- Added compare-specific handling in `format_statistics_footer` (total files, no space calc)
- Updated `print_preview_output` to pass 0 space savings for compare mode

### Task 2: Update formatter comment for unified action flow

**Commit:** 4e5339d

- Updated comment from "always in preview mode for print_preview_output" to "handles all actions including compare"

### Task 3: Handle compare action in action mode flow

**Commit:** 443a047

Added new methods to ActionFormatter hierarchy:
- `format_compare_summary()` - Compare-specific summary format ("Matched files summary:")
- `format_unmatched_section()` - Support for --show-unmatched flag

Updated main() flow:
- Summary mode uses `format_compare_summary` for compare action
- Detailed mode shows unmatched files section for compare with --show-unmatched
- Empty result shows "No matching files found." for compare (not "No duplicates found.")

Fixed JsonActionFormatter:
- `finalize()` now preserves unmatched data from `_data`
- Metadata collection includes unmatched files in verbose mode

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed compare mode output formatting in action path**

- **Found during:** Task 1 verification
- **Issue:** Output showed [WOULD COMPARE] instead of [DUPLICATE], wrong statistics format
- **Fix:** Added compare-specific handling in format_duplicate_group and format_statistics_footer
- **Commit:** 49ad75c

**2. [Rule 1 - Bug] Fixed compare mode features in unified action path**

- **Found during:** Task 3 test verification
- **Issue:** Summary mode, unmatched files, empty result, JSON unmatched arrays all broken
- **Fix:** Added format_compare_summary, format_unmatched_section methods and related handling
- **Commit:** 443a047

## Verification Results

| Check | Result |
|-------|--------|
| Default compare mode output | Identical to previous behavior |
| Explicit --action compare | Identical to default |
| --action hardlink | Works correctly with PREVIEW banner |
| JSON compare mode | Valid JSON with correct schema |
| All 198 tests | Pass |

## Key Code Changes

```python
# master_path always set (line ~2335)
master_path = Path(args.dir1).resolve()

# preview/execute mode determination (line ~2418)
preview_mode = not args.execute
execute_mode = args.action != 'compare' and args.execute

# compare-specific format_duplicate_group label (line ~1419)
if action == "compare":
    action_label = "DUPLICATE"

# compare-specific statistics footer (line ~1539)
if action == 'compare':
    total_files = master_count + duplicate_count
    lines.append(f"Total files with matches: {total_files}")
    lines.append("Space reclaimable: (run with --action to calculate)")
    return lines
```

## Next Phase Readiness

**Ready for Plan 04:** The `else:` branch (lines ~2797-2869) is now dead code since master_path is always truthy. Plan 04 will delete:
- Lines 2797-2869: Dead compare formatter code path
- CompareFormatter ABC and implementations (if no longer needed)

## Impact

- All compare mode output now flows through ActionFormatter
- Single code path for all action types in main()
- JSON schema compatibility maintained
- All existing tests pass without modification
