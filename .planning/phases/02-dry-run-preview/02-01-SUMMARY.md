---
phase: 02-dry-run-preview
plan: 01
subsystem: output-formatting
tags: [cli-output, formatting, master-mode]

dependency_graph:
  requires: [01-01, 01-02]
  provides: [format_duplicate_group, hierarchical-output]
  affects: [02-03, 02-04]

tech_stack:
  added: []
  patterns: [hierarchical-output-format]

key_files:
  created: []
  modified:
    - file_matcher.py
    - tests/test_master_directory.py

decisions:
  - id: hierarchical-format
    choice: "[MASTER]/[DUP:?] format with 4-space indent"
    rationale: "Supports future action labels like [DUP:hardlink], [DUP:symlink]"
  - id: alphabetical-sorting
    choice: "Groups sorted by master file path"
    rationale: "Consistent, predictable output ordering"

metrics:
  duration: "~5 minutes"
  completed: "2026-01-19"
---

# Phase 2 Plan 01: Output Format Refactor Summary

**One-liner:** Refactored master-mode output from arrow notation to hierarchical [MASTER]/[DUP:?] format with sorted groups and blank line separators.

## What Was Built

### format_duplicate_group() Function
New function that formats duplicate groups for display:

```python
def format_duplicate_group(
    master_file: str,
    duplicates: list[str],
    action: str | None = None,
    verbose: bool = False,
    file_sizes: dict[str, int] | None = None
) -> list[str]:
```

**Output format:**
- Master line: `[MASTER] /path/to/master/file.txt`
- Duplicate lines (4-space indent): `    [DUP:?] /path/to/dup.txt`
- Verbose mode: `[MASTER] /path/file.txt (3 duplicates, 1.5 MB)`
- Duplicates sorted alphabetically within each group

### main() Output Integration
Updated main() to use the new format:
- Groups sorted alphabetically by master file path
- Blank lines between groups (except after last group)
- Verbose mode passes file_sizes dict for size display
- Replaced format_master_output() call with format_duplicate_group()

### Test Updates
Updated test_master_directory.py tests to expect new format:
- `test_master_output_format()` - Checks for [MASTER] and [DUP:?]
- `test_master_output_master_first()` - Verifies master dir in [MASTER] lines
- `test_master_verbose_shows_details()` - Checks duplicate count in verbose
- `test_duplicate_group_has_correct_structure()` - New test for group structure
- `test_oldest_file_becomes_master()` - Updated for new format
- `test_master_dir_file_preferred()` - Updated for new format

## Output Example

**Before (arrow notation):**
```
/path/master.txt -> /path/dup1.txt, /path/dup2.txt
```

**After ([MASTER]/[DUP:?] format):**
```
[MASTER] /path/master.txt
    [DUP:?] /path/dup1.txt
    [DUP:?] /path/dup2.txt
```

**Verbose mode:**
```
[MASTER] /path/master.txt (2 duplicates, 1.5 MB)
    [DUP:?] /path/dup1.txt
    [DUP:?] /path/dup2.txt
```

## Verification Results

All success criteria met:
- [x] Arrow notation removed from master-mode output
- [x] [MASTER]/[DUP:?] format displays correctly
- [x] Verbose mode shows duplicate count and file sizes
- [x] Groups separated by blank lines
- [x] All 35 tests passing with updated expectations

## Deviations from Plan

None - plan executed exactly as written.

## Commits

| Hash | Type | Description |
|------|------|-------------|
| 8ebc089 | feat | add format_duplicate_group() function |
| 40cc911 | feat | update main() to use [MASTER]/[DUP:?] format |

## Next Phase Readiness

Ready for plan 02-03 (--dry-run flag integration):
- format_duplicate_group() accepts `action` parameter for future action labels
- Output structure supports adding action-specific labels like [DUP:hardlink]
- Cross-filesystem functions from 02-02 available for hardlink warnings

---
*Summary created: 2026-01-19*
