---
phase: 011
plan: 01
subsystem: output-formatting
completed: 2026-01-30
duration: "3m 51s"
tags: [refactor, banner, unification, consistency]

requires:
  - formatters module with TextActionFormatter and JsonActionFormatter
  - cli module with preview and execute mode banner display

provides:
  - Unified banner format across preview and execute modes
  - Consistent display of action, group count, file count, and space info
  - Clear mode indicators: (PREVIEW) and (EXECUTE)

affects:
  - Any future banner customization will use single format_banner method
  - Tests that check banner output format

tech-stack:
  patterns:
    - Strategy pattern: ActionFormatter with unified format_banner interface
    - Method signature extension: Added parameters to existing abstract method

key-files:
  modified:
    - filematcher/formatters.py: Updated ActionFormatter.format_banner signature, implemented unified format in TextActionFormatter
    - filematcher/cli.py: Updated to use formatter.format_banner with parameters
    - tests/test_safe_defaults.py: Updated assertions to check for new banner format

decisions:
  - "Unified banner shows: '{action} mode: {groups} groups, {files} files, {space} to save (MODE)'"
  - "Mode indicator appended to banner: (PREVIEW) in yellow or (EXECUTE) in red"
  - "Preview hint 'Use --execute to apply changes' shown below banner only in preview mode"
  - "Deprecated format_execute_banner() function kept for backward compatibility"
  - "Constants PREVIEW_BANNER and EXECUTE_BANNER kept for backward compatibility"
---

# Quick Task 011: Unify Compare Mode and Execute Mode Banners

**One-liner:** Unified preview and execute mode banners to show consistent informative format with action type, group count, file count, and space savings.

## Context

Previously there were two different banner implementations:
1. `format_banner()` in TextActionFormatter showed simple "=== PREVIEW MODE ===" or "=== EXECUTE MODE! ==="
2. `format_execute_banner()` standalone function showed "{action} mode: {groups} groups, {files} files, {space} to save"

The execute mode banner was more informative. This task unified both to use the same format.

## Changes Made

### 1. Updated ActionFormatter Interface
- Extended `format_banner()` abstract method signature with parameters:
  - `action: str` - Action type (hardlink, symlink, delete)
  - `group_count: int` - Number of duplicate groups
  - `duplicate_count: int` - Total number of duplicate files
  - `space_bytes: int` - Space in bytes to be saved
- Updated JsonActionFormatter to accept new parameters (no-op implementation)

### 2. Implemented Unified Banner in TextActionFormatter
- New format: `{action} mode: {groups} groups, {files} files, {space} to save (MODE)`
- Mode indicator appended based on execution state:
  - `(PREVIEW)` in yellow for preview mode
  - `(EXECUTE)` in red for execute mode
- Separator line: `----------------------------------------`
- Preview hint shown below banner only when in preview mode: "Use --execute to apply changes"

### 3. Updated CLI Integration
- Modified `print_preview_output()` to pass parameters to `format_banner()`
- Modified execute mode to use `action_formatter.format_banner()` instead of standalone function
- Removed import of `format_execute_banner` from cli.py

### 4. Deprecated Old Function
- Marked `format_execute_banner()` as deprecated with docstring note
- Kept function for backward compatibility
- Kept constants `PREVIEW_BANNER` and `EXECUTE_BANNER` for backward compatibility

### 5. Updated Tests
- Changed assertions from `"PREVIEW MODE"` to `"(PREVIEW)"` in test_safe_defaults.py
- Updated banner location checks to find new format (searches for `'mode:'` and `'groups'`)
- All 284 tests pass

## Example Output

### Preview Mode
```
Action mode (PREVIEW): hardlink test_dir1 vs test_dir2
Found 2 duplicate groups (2 files, 46 B reclaimable)

hardlink mode: 2 groups, 2 files, 46 B to save (PREVIEW)
----------------------------------------
Use --execute to apply changes
```

### Execute Mode
```
delete mode: 1 groups, 1 files, 5 B to save (EXECUTE)
----------------------------------------

Execution complete:
  Successful: 1
  Failed: 0
  Skipped: 0
```

## Benefits

1. **Consistency**: Same informative banner format in both preview and execute modes
2. **Clarity**: Mode indicator clearly shows whether changes will be applied
3. **Information density**: Banner shows all key metrics (action, groups, files, space) upfront
4. **Maintainability**: Single banner implementation instead of two separate paths
5. **Backward compatibility**: Old constants and function preserved for external users

## Deviations from Plan

None - plan executed exactly as written.

## Testing

- All 284 tests pass
- Manual verification:
  - Preview banner shows unified format with (PREVIEW) indicator
  - Execute banner shows unified format with (EXECUTE) indicator
  - Separator line and preview hint display correctly
  - No-color mode works (tested with --no-color flag)

## Next Phase Readiness

✓ No blockers
✓ No concerns
✓ Ready for future enhancements

## Commits

1. `97d85b6` - refactor(011-01): unify banner format in TextActionFormatter.format_banner()
2. `a1bd900` - test(011-01): update test assertions for unified banner format
