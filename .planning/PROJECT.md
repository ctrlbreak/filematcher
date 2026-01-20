# File Matcher

## What This Is

A Python CLI utility that finds files with identical content across two directory hierarchies and deduplicates them using hard links, symbolic links, or deletion. Features preview-by-default safety, master directory protection, and comprehensive audit logging.

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

### Active

<!-- Current scope. Building toward these. -->

(None — next milestone not yet defined)

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- Merging directories — tool compares, doesn't reorganize
- Renaming files to match master — links preserve original names
- Backup/restore functionality — user responsible for backups
- Multi-directory (3+) comparison — current two-directory model sufficient
- GUI interface — CLI-focused tool
- Undo/rollback functionality — log file serves as record; manual recovery

## Context

**Current state:** v1.1 shipped with full deduplication capability.

- 1,374 lines Python (file_matcher.py)
- 1,996 lines tests (114 tests, all passing)
- Pure Python standard library (no external dependencies)
- Python 3.9+ compatibility

**Architecture:** Single-file implementation (`file_matcher.py`) with functional design, CLI parsing via argparse, logging via standard library.

**Tech stack:**
- argparse for CLI
- hashlib for content hashing
- pathlib for file operations
- os.link/symlink for deduplication actions
- logging module for audit trails

## Constraints

- **Tech stack**: Pure Python standard library only — no external dependencies
- **Compatibility**: Python 3.9+ (uses `from __future__ import annotations`)
- **Architecture**: Maintain single-file implementation pattern

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Master directory model | Simpler than per-file decisions; clear which files are preserved | ✓ Good |
| Links keep original filename | Preserves directory structure and existing references | ✓ Good |
| Preview-by-default with --execute | Safety-first design prevents accidental modifications | ✓ Good |
| Temp-rename safety pattern | Atomic operations prevent data loss on failure | ✓ Good |
| Separate audit logger | Avoids mixing audit logs with console output | ✓ Good |
| Exit codes 0/1/2/3 | Clear signal for success/all-fail/validation/partial | ✓ Good |

---
*Last updated: 2026-01-20 after v1.1 milestone*
