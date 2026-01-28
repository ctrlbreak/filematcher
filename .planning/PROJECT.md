# File Matcher

## What This Is

A Python CLI utility that finds files with identical content across two directory hierarchies and deduplicates them using hard links, symbolic links, or deletion. Features preview-by-default safety, master directory protection, comprehensive audit logging, JSON output for scripting, and TTY-aware color output. Implemented as a proper Python package (filematcher/) with full backward compatibility.

## Core Value

Safely deduplicate files across directories while preserving the master copy and logging all changes.

## Current State

**Shipped:** v1.4.0 (2026-01-28)

Architecture: filematcher/ package with 8 modules and thin file_matcher.py wrapper for backward compatibility.

```
filematcher/
  __init__.py     (216 lines - 67 re-exports)
  __main__.py     (7 lines - python -m entry point)
  cli.py          (614 lines - CLI entry point)
  colors.py       (328 lines - ANSI colors, ColorConfig)
  hashing.py      (139 lines - MD5/SHA-256, sparse sampling)
  filesystem.py   (158 lines - hardlink/symlink detection)
  actions.py      (437 lines - action execution, audit logging)
  formatters.py   (1174 lines - Text/JSON formatters)
  directory.py    (207 lines - directory indexing)

file_matcher.py   (26 lines - backward compat wrapper)
```

**Tech stack:**
- argparse for CLI
- hashlib for content hashing
- pathlib for file operations
- os.link/symlink for deduplication actions
- logging module for audit trails
- ActionFormatter ABC with Text/JSON implementations

## Requirements

### Validated

- ✓ Find files with identical content across two directories — v1.1
- ✓ Compare files using content hashing (MD5 or SHA-256) — v1.1
- ✓ Fast mode using sparse sampling for large files (>100MB) — v1.1
- ✓ Show unmatched files in either directory — v1.1
- ✓ Summary mode showing counts instead of file lists — v1.1
- ✓ Verbose mode showing per-file progress — v1.1
- ✓ Recursive directory traversal — v1.1
- ✓ Designate one directory as "master" (files preserved) — v1.1
- ✓ Replace duplicate files with hard links to master — v1.1
- ✓ Replace duplicate files with symbolic links to master — v1.1
- ✓ Delete duplicate files (keeping master) — v1.1
- ✓ Links preserve original filename (pointing to master file) — v1.1
- ✓ Preview mode by default (--execute required for changes) — v1.1
- ✓ Confirmation prompt before execution — v1.1
- ✓ Log all modifications (file path, action taken, target) — v1.1
- ✓ Unified output format across compare and action modes — v1.3
- ✓ Statistics shown in all modes — v1.3
- ✓ JSON output format for scripting (`--json` flag) — v1.3
- ✓ TTY-aware color output with `--color`/`--no-color` flags — v1.3
- ✓ Progress to stderr, data to stdout (Unix convention) — v1.3
- ✓ Deterministic output ordering — v1.3
- ✓ filematcher/ package structure with 8 logical modules — v1.4
- ✓ Backward compatibility for `python file_matcher.py` invocation — v1.4
- ✓ Pip install functionality (`filematcher` command) — v1.4
- ✓ All 218 tests pass with package imports — v1.4

### Active

**v1.5 Interactive Execute:**
- [ ] Per-file confirmation prompts in execute mode (yes/no/all/cancel)
- [ ] Consistent output structure with preview mode
- [ ] Visual feedback during interactive execution
- [ ] Maintain `--yes` flag behavior (skip all prompts)

### Out of Scope

- Merging directories — tool compares, doesn't reorganize
- Renaming files to match master — links preserve original names
- Backup/restore functionality — user responsible for backups
- Multi-directory (3+) comparison — current two-directory model sufficient
- GUI interface — CLI-focused tool
- Undo/rollback functionality — log file serves as record; manual recovery
- CSV/XML output — JSON is more flexible; CSV can be derived from JSON with jq
- Interactive output selection — flags are sufficient
- Progress bars — current verbose mode sufficient; adds dependency complexity

## Constraints

- **Tech stack**: Pure Python standard library only — no external dependencies
- **Compatibility**: Python 3.9+ (uses `from __future__ import annotations`)
- **Backward compat**: `python file_matcher.py` and `pip install -e .` must continue working

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Master directory model | Simpler than per-file decisions; clear which files are preserved | ✓ Good |
| Links keep original filename | Preserves directory structure and existing references | ✓ Good |
| Preview-by-default with --execute | Safety-first design prevents accidental modifications | ✓ Good |
| Temp-rename safety pattern | Atomic operations prevent data loss on failure | ✓ Good |
| Separate audit logger | Avoids mixing audit logs with console output | ✓ Good |
| Exit codes 0/1/2/3 | Clear signal for success/all-fail/validation/partial | ✓ Good |
| ActionFormatter ABC hierarchy | Single code path for all modes; 513 lines removed | ✓ Good |
| compare is default action | Always have meaningful action value, unified CLI model | ✓ Good |
| JSON accumulator pattern | format_* methods collect data, finalize() serializes | ✓ Good |
| stderr for progress/status | Unix convention enables clean piping of data output | ✓ Good |
| 16-color ANSI codes | Maximum terminal compatibility vs 256-color/truecolor | ✓ Good |
| NO_COLOR environment support | Industry standard (no-color.org) for accessibility | ✓ Good |
| Re-export all symbols from package | Full backward compatibility during/after migration | ✓ Good |
| Direct imports for leaf modules | No circular import risk for hashing, filesystem, colors | ✓ Good |
| Thin wrapper pattern | file_matcher.py re-exports from filematcher, 26 lines | ✓ Good |
| Audit logging in actions.py | Cohesive module, both concern file modifications | ✓ Good |

## Current Milestone: v1.5 Interactive Execute

**Goal:** Redesign execute mode with per-file interactive confirmation that maintains consistency with preview mode output.

**Target features:**
- Per-file yes/no/all/cancel prompts during execute mode
- Output structure consistent with preview mode (same group display)
- Visual feedback showing progress and results inline
- `--yes` flag continues to skip all prompts

---
*Last updated: 2026-01-28 after starting v1.5 milestone*
