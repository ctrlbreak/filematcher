# File Matcher

## What This Is

A Python CLI utility that finds files with identical content across two directory hierarchies and deduplicates them using hard links, symbolic links, or deletion. Features preview-by-default safety, master directory protection, comprehensive audit logging, JSON output for scripting, and TTY-aware color output.

## Core Value

Safely deduplicate files across directories while preserving the master copy and logging all changes.

## Requirements

### Validated

<!-- Shipped and confirmed working. -->

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

### Active

<!-- Current scope. Building toward these. -->

- [ ] Split file_matcher.py into filematcher/ package structure — v1.4
- [ ] Maintain backward compatibility for `python file_matcher.py` invocation — v1.4
- [ ] Maintain pip install functionality (`filematcher` command) — v1.4
- [ ] All existing tests pass without major rewrites — v1.4

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- Merging directories — tool compares, doesn't reorganize
- Renaming files to match master — links preserve original names
- Backup/restore functionality — user responsible for backups
- Multi-directory (3+) comparison — current two-directory model sufficient
- GUI interface — CLI-focused tool
- Undo/rollback functionality — log file serves as record; manual recovery
- CSV/XML output — JSON is more flexible; CSV can be derived from JSON with jq
- Interactive output selection — flags are sufficient
- Progress bars — current verbose mode sufficient; adds dependency complexity

## Context

**Current state:** v1.4 milestone — refactoring to package structure.

- 2,455 lines Python (file_matcher.py)
- 217 tests, all passing
- Pure Python standard library (no external dependencies)
- Python 3.9+ compatibility

**Architecture:** Single-file implementation (`file_matcher.py`) being refactored to `filematcher/` package with ActionFormatter hierarchy for all output modes (compare, hardlink, symlink, delete). CLI parsing via argparse, logging via standard library.

**Tech stack:**
- argparse for CLI
- hashlib for content hashing
- pathlib for file operations
- os.link/symlink for deduplication actions
- logging module for audit trails
- ActionFormatter ABC with Text/JSON implementations

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

## Current Milestone: v1.4 Package Structure

**Goal:** Split file_matcher.py into a proper Python package for better code navigation and AI tooling compatibility.

**Target features:**
- filematcher/ package with logical module separation
- Backward-compatible file_matcher.py wrapper
- All 217 tests passing with minimal import changes

---
*Last updated: 2026-01-27 after v1.4 milestone started*
