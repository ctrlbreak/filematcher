# File Matcher

## What This Is

A Python CLI utility that finds files with identical content across two directory hierarchies and optionally performs deduplication actions on them. Users can identify duplicate files, then choose to replace them with links or delete them entirely.

## Core Value

Safely deduplicate files across directories while preserving the master copy and logging all changes.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

- ✓ Find files with identical content across two directories — existing
- ✓ Compare files using content hashing (MD5 or SHA-256) — existing
- ✓ Fast mode using sparse sampling for large files (>100MB) — existing
- ✓ Show unmatched files in either directory — existing
- ✓ Summary mode showing counts instead of file lists — existing
- ✓ Verbose mode showing per-file progress — existing
- ✓ Recursive directory traversal — existing

### Active

<!-- Current scope. Building toward these. -->

- [ ] Designate one directory as "master" (files preserved, others modified)
- [ ] Replace duplicate files with hard links to master
- [ ] Replace duplicate files with symbolic links to master
- [ ] Delete duplicate files (keeping master)
- [ ] Links preserve original filename (pointing to master file)
- [ ] Dry-run mode showing what would change without modifying anything
- [ ] Interactive mode prompting for confirmation on each change
- [ ] Auto mode executing all changes without prompts
- [ ] Log all modifications (file path, action taken, target)

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- Merging directories — tool compares, doesn't reorganize
- Renaming files to match master — links preserve original names
- Backup/restore functionality — user responsible for backups
- Multi-directory (3+) comparison — current two-directory model sufficient
- GUI interface — CLI-focused tool

## Context

File Matcher is an existing single-file Python CLI tool with zero external dependencies. It uses content hashing to identify duplicate files across directories. The new features add the ability to act on matches, not just report them.

Current architecture: single module (`file_matcher.py`) with functional design, CLI parsing via argparse, logging via standard library.

## Constraints

- **Tech stack**: Pure Python standard library only — no external dependencies
- **Compatibility**: Python 3.9+ (uses `from __future__ import annotations`)
- **Architecture**: Maintain single-file implementation pattern

## Key Decisions

<!-- Decisions that constrain future work. Add throughout project lifecycle. -->

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Master directory model | Simpler than per-file decisions; clear which files are preserved | — Pending |
| Links keep original filename | Preserves directory structure and existing references | — Pending |
| Three execution modes (dry-run, interactive, auto) | Balances safety with convenience | — Pending |

---
*Last updated: 2026-01-19 after initialization*
