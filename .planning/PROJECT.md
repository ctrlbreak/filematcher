# File Matcher

## What This Is

A Python CLI utility that finds files with identical content across two directory hierarchies and deduplicates them using hard links, symbolic links, or deletion. Features interactive per-file confirmation during execute mode, preview-by-default safety, master directory protection, comprehensive audit logging, JSON output for scripting (v2.0 schema), and TTY-aware color output. Implemented as a proper Python package (filematcher/) with full backward compatibility.

## Core Value

Safely deduplicate files across directories while preserving the master copy and logging all changes.

## Current State

**Shipped:** v1.5.0 (2026-01-31)

Architecture: filematcher/ package with 8 modules, interactive execute mode, and JSON v2.0 schema.

```
filematcher/
  __init__.py     (216 lines - 67 re-exports)
  __main__.py     (7 lines - python -m entry point)
  cli.py          (850+ lines - CLI, interactive execute)
  colors.py       (328 lines - ANSI colors, ColorConfig)
  hashing.py      (139 lines - MD5/SHA-256, sparse sampling)
  filesystem.py   (158 lines - hardlink/symlink detection)
  actions.py      (450+ lines - action execution, audit logging)
  formatters.py   (1300+ lines - Text/JSON formatters with prompts)
  directory.py    (207 lines - directory indexing)

file_matcher.py   (26 lines - backward compat wrapper)
```

**Tech stack:**
- argparse for CLI
- hashlib for content hashing
- pathlib for file operations
- os.link/symlink for deduplication actions
- logging module for audit trails
- ActionFormatter ABC with Text/JSON implementations (extended with prompt methods)

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
- ✓ Per-file confirmation prompts in execute mode (y/n/a/q) — v1.5
- ✓ Progress indicator showing group position [3/10] — v1.5
- ✓ Consistent output structure with preview mode — v1.5
- ✓ Visual feedback during interactive execution (✓/✗ status) — v1.5
- ✓ `--yes` flag bypasses all prompts (batch mode) — v1.5
- ✓ JSON schema v2.0 with unified header object — v1.5
- ✓ Fail-fast validation for incompatible flag combinations — v1.5
- ✓ Enhanced execution summary with user decision tracking — v1.5
- ✓ 308 tests pass with interactive mode coverage — v1.5

### Active

(None — planning next milestone)

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
| Interactive by default for --execute | Safer UX, user reviews each action; --yes for scripts | ✓ Good |
| y/n/a/q response pattern | Follows git add -p convention; intuitive for developers | ✓ Good |
| JSON schema v2.0 with header object | Cleaner structure, consistent directory naming | ✓ Good |
| Exit code 130 for user quit | Unix convention (128 + SIGINT) | ✓ Good |
| Fail-fast flag validation | Errors before file scanning saves time | ✓ Good |

---
*Last updated: 2026-01-31 after v1.5 milestone*
