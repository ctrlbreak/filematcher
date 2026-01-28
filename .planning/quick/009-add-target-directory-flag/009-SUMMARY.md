# Quick Task 009: Add --target-dir Flag Summary

## One-liner

Added `--target-dir/-t` flag to redirect hardlink/symlink creation to a separate directory while preserving relative paths and deleting originals.

## What Was Done

### Task 1: CLI Argument and Validation (4e2955a)

Added `--target-dir/-t` argument with validation:
- Only applies to `--action hardlink` or `--action symlink` (not delete/compare)
- Directory must exist
- Updated `build_log_flags()` to include target_dir in audit logs
- Passed target_dir and dir2_base to both `execute_all_actions()` call sites

### Task 2: Execution Logic (22c72c6)

Implemented target-dir mode in `actions.py`:
- Modified `execute_action()` to accept `target_dir` and `dir2_base` parameters
- When target_dir is specified:
  1. Compute relative path from dir2_base to duplicate
  2. Create parent directories in target_dir as needed
  3. Create hardlink/symlink at target location
  4. Delete original file in dir2
- Modified `execute_all_actions()` to pass through new parameters

### Task 3: Comprehensive Tests (1f712f0)

Added 10 new tests:

**TestTargetDir (test_actions.py):**
- `test_hardlink_to_target_dir` - verifies hardlink creation and original deletion
- `test_symlink_to_target_dir` - verifies symlink creation and original deletion
- `test_preserves_subdirectory_structure` - nested paths preserved in target
- `test_target_dir_creates_parent_directories` - mkdir -p behavior
- `test_target_dir_not_under_dir2_fails` - error when duplicate not under dir2
- `test_without_target_dir_behaves_normally` - no regression for normal mode

**TestTargetDirValidation (test_cli.py):**
- `test_target_dir_requires_link_action` - rejected with delete/compare
- `test_target_dir_requires_existing_directory` - rejected if dir doesn't exist
- `test_target_dir_accepted_with_hardlink` - accepted in preview mode
- `test_target_dir_accepted_with_symlink` - accepted in preview mode

Also fixed existing mock functions to accept new parameters.

## Files Modified

| File | Changes |
|------|---------|
| filematcher/cli.py | Added --target-dir argument, validation, parameter passing |
| filematcher/actions.py | Added target_dir/dir2_base params, target-dir execution logic |
| tests/test_actions.py | Added TestTargetDir class (6 tests), fixed mock signature |
| tests/test_cli.py | Added TestTargetDirValidation class (4 tests), fixed mock signature |

## Test Results

- Total tests: 228 (218 existing + 10 new)
- All passing
- No regressions

## Usage Example

```bash
# Create hardlinks in /backup/deduped preserving relative paths from /data/duplicates
filematcher /data/master /data/duplicates --action hardlink --target-dir /backup/deduped --execute --yes

# Result:
# - /data/duplicates/sub/file.txt (deleted)
# - /backup/deduped/sub/file.txt (hardlink to /data/master/file.txt)
```

## Deviations from Plan

None - plan executed exactly as written.

## Completion

- Duration: ~15 minutes
- Completed: 2026-01-28
