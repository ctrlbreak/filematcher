---
phase: 12-extract-foundation-modules
plan: 02
subsystem: hashing
tags: [md5, sha256, hashlib, sparse-hashing, content-deduplication]

# Dependency graph
requires:
  - phase: 12-01
    provides: Package structure and colors module extraction pattern
provides:
  - filematcher/hashing.py standalone hashing module
  - MD5 and SHA-256 file hashing
  - Sparse sampling for fast large file comparison
affects: [12-03-filesystems, tests, file_matcher]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Leaf module extraction (no internal dependencies)
    - Direct import for leaf modules (not __getattr__ lazy)
    - Backward compatibility through re-exports

key-files:
  created:
    - filematcher/hashing.py
  modified:
    - filematcher/__init__.py
    - file_matcher.py

key-decisions:
  - "Direct import for hashing (not lazy) since it's a leaf module with no circular import risk"
  - "Removed hashing from __getattr__ lazy loader since now directly imported"

patterns-established:
  - "Leaf module pattern: stdlib-only imports, no internal filematcher dependencies"
  - "Direct import for leaf modules in __init__.py (simpler than lazy loading)"

# Metrics
duration: 2min
completed: 2026-01-27
---

# Phase 12 Plan 02: Extract Hashing Module Summary

**Hashing functions (create_hasher, get_file_hash, get_sparse_hash) extracted to filematcher/hashing.py as standalone leaf module with zero internal dependencies**

## Performance

- **Duration:** 2 min (116 seconds)
- **Started:** 2026-01-27T01:23:32Z
- **Completed:** 2026-01-27T01:25:28Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Extracted all hashing functions to standalone filematcher/hashing.py module (139 lines)
- Maintained full backward compatibility for all three import paths
- All 217 tests pass without modification
- No circular imports - hashing is a clean leaf module

## Task Commits

Each task was committed atomically:

1. **Task 1: Create filematcher/hashing.py with hashing functions** - `5de9e6d` (feat)
2. **Task 2: Update __init__.py and file_matcher.py imports** - `d1314a5` (feat)

## Files Created/Modified
- `filematcher/hashing.py` - New standalone hashing module with create_hasher, get_file_hash, get_sparse_hash
- `filematcher/__init__.py` - Added direct import from filematcher.hashing, removed from lazy loader
- `file_matcher.py` - Added import from filematcher.hashing, removed original function definitions (~100 lines)

## Decisions Made
- **Direct import vs lazy loading:** Used direct import for hashing module in __init__.py since it's a leaf module with no internal dependencies, eliminating circular import risk. This is simpler than __getattr__ lazy loading used for file_matcher imports.
- **Removed from __getattr__:** Since hashing functions are now directly imported, removed them from the lazy loader mapping to avoid redundancy.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - extraction followed the established pattern from 12-01 colors extraction.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Hashing module extracted as leaf module
- Pattern established: leaf modules use direct import, complex modules use lazy __getattr__
- Ready for 12-03: Extract filesystem helpers module
- index_directory and find_matching_files remain in file_matcher.py (depend on module-level logger)

---
*Phase: 12-extract-foundation-modules*
*Completed: 2026-01-27*
