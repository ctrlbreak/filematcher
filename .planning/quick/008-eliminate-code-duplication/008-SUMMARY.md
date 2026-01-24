---
phase: quick-008
plan: 01
subsystem: core
tags: [refactor, deduplication, helpers]

dependency-graph:
  requires: []
  provides: [centralized-hashing, path-helpers, oldest-selection]
  affects: []

tech-stack:
  added: []
  patterns: [helper-extraction, DRY]

key-files:
  created: []
  modified:
    - file_matcher.py

decisions:
  - id: DEC-Q008-01
    choice: "Add helper functions with full docstrings despite line count increase"
    why: "Maintainability and code clarity outweigh line count reduction"

metrics:
  duration: 5 min
  completed: 2026-01-24
---

# Quick Task 008: Eliminate Code Duplication Summary

**One-liner:** Extracted create_hasher(), is_in_directory(), select_oldest() helpers; inlined banner functions; consolidated space savings calculation

## What Changed

### Task 1: Extract Helper Functions

Added three new helper functions to centralize repeated patterns:

1. **`create_hasher(hash_algorithm)`** - Centralizes hash algorithm selection
   - Previously duplicated in `get_file_hash()` and `get_sparse_hash()`
   - Now both functions call `create_hasher()` instead of if/elif/else blocks

2. **`is_in_directory(filepath, directory)`** - Path containment check
   - Replaces `f.startswith(dir + os.sep) or f.startswith(dir)` pattern
   - Used in `select_master_file()` and `main()` warning check

3. **`select_oldest(file_paths)`** - Oldest file by mtime selection
   - Returns `(oldest_file, list_of_other_files)` tuple
   - Used 3 times in `select_master_file()` for DRY

### Task 2: Inline Banners and Consolidate Calculations

1. **Removed banner wrapper functions**
   - Deleted `format_preview_banner()` and `format_execute_banner()`
   - Callers now use `PREVIEW_BANNER` and `EXECUTE_BANNER` constants directly

2. **Consolidated `calculate_space_savings()` calls**
   - Pre-calculate `space_info` once at start of `print_preview_output()`
   - Reuse cached value for summary line, summary mode stats, and footer stats
   - Compare mode handled specially (space_info=None)

3. **Removed useless concatenation**
   - Changed `other_files + []` to `other_files`

### Task 3: Verification

All success criteria verified:
- `create_hasher()` eliminates duplicate hash algorithm selection
- `is_in_directory()` eliminates duplicate path containment checks
- `select_oldest()` eliminates duplicate oldest-file-with-remainder logic
- Banner wrapper functions removed, constants used directly
- `calculate_space_savings()` called once per output path
- No useless `+ []` concatenation
- All 206 tests pass

## Deviations from Plan

### Line Count

**Plan expected:** ~60 line reduction
**Actual result:** +32 lines (76 insertions, 44 deletions)

**Reason:** The plan underestimated the size of proper docstrings for new helper functions. Each helper has a complete docstring with Args/Returns sections. This is the correct trade-off - better documentation and maintainability outweigh raw line count.

## Commits

| Hash | Description |
|------|-------------|
| 1fd0caf | Extract create_hasher(), is_in_directory(), select_oldest() |
| af8e6ff | Inline banners, consolidate calculate_space_savings() |

## Verification

```bash
python3 run_tests.py        # 206 tests pass
python3 file_matcher.py test_dir1 test_dir2              # compare works
python3 file_matcher.py test_dir1 test_dir2 -a hardlink -f  # fast mode works
python3 file_matcher.py test_dir1 test_dir2 --json       # JSON works
```

## Files Modified

- `file_matcher.py` - Added helpers, removed wrappers, consolidated calculations
