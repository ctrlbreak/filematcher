# Roadmap: File Matcher Deduplication

**Created:** 2026-01-19
**Core Value:** Safely deduplicate files across directories while preserving the master copy and logging all changes.

## Overview

This roadmap delivers deduplication capabilities in three phases: foundation (master directory concept), preview (dry-run and statistics), and actions (execution with logging). Each phase builds incrementally - Phase 1 establishes master/duplicate identification, Phase 2 adds preview capabilities, and Phase 3 enables actual modifications with audit trails.

## Phases

### Phase 1: Master Directory Foundation

**Goal:** Users can designate a master directory and see which files are duplicates vs masters.

**Dependencies:** None (builds on existing file matching capability)

**Plans:** 2 plans

Plans:
- [x] 01-01-PLAN.md — Add --master flag, validation, and master-aware output formatting
- [x] 01-02-PLAN.md — Unit tests for master directory validation (TEST-01)

**Requirements:**
- MSTR-01: User can designate one directory as "master" via `--master` flag
- MSTR-02: Files in master directory are never modified or deleted
- MSTR-03: Tool validates master directory is one of the compared directories
- TEST-01: Unit tests for master directory validation

**Success Criteria:**
1. User can run `filematcher dir1 dir2 --master dir1` and see output that clearly distinguishes master files from duplicates
2. User receives a clear error if `--master` points to a directory not being compared
3. Output labels files as "master" or "duplicate" based on which directory they reside in

---

### Phase 2: Dry-Run Preview & Statistics

**Goal:** Users can preview what would happen and see aggregate statistics before any modification occurs.

**Dependencies:** Phase 1 (requires master directory identification)

**Requirements:**
- DRY-01: User can preview planned changes with `--dry-run` flag
- DRY-02: Dry-run shows list of files that would be modified
- DRY-03: Dry-run shows what action would be taken on each file
- DRY-04: Dry-run shows estimated space savings before execution
- STAT-01: Display count of duplicate groups found
- STAT-02: Display count of files that would be affected
- STAT-03: Display total space that would be saved/reclaimed
- TEST-02: Unit tests for dry-run output formatting

**Success Criteria:**
1. User can run `filematcher dir1 dir2 --master dir1 --dry-run` and see exactly which files would be affected
2. User sees count of duplicate groups, affected files, and estimated space savings in the output
3. No files are modified when `--dry-run` is active (filesystem unchanged)
4. Each planned change shows: duplicate file path, proposed action, and which master file it matches

---

### Phase 3: Actions & Logging

**Goal:** Users can execute deduplication actions with a complete audit trail of all changes.

**Dependencies:** Phase 2 (requires dry-run planning infrastructure)

**Requirements:**
- EXEC-01: Support `--action` flag for specifying action type (hardlink, symlink, delete)
- EXEC-02: Auto execution mode runs without prompts when action specified
- EXEC-03: Action requires both `--master` and `--action` flags to be set
- ACT-01: Replace duplicate files with hard links to master
- ACT-02: Replace duplicate files with symbolic links to master
- ACT-03: Delete duplicate files (keeping master only)
- ACT-04: Links preserve original filename (pointing to master file)
- LOG-01: All planned changes are logged with timestamp
- LOG-02: Log includes: action type, source file path, target file path
- LOG-03: Log file path configurable via `--log` flag
- TEST-03: Unit tests for change logging
- TEST-04: Integration tests for CLI flag combinations

**Success Criteria:**
1. User can run `filematcher dir1 dir2 --master dir1 --action hardlink` and duplicate files are replaced with hard links to their master copies
2. User can run with `--action symlink` and duplicate files are replaced with symbolic links
3. User can run with `--action delete` and duplicate files are deleted (master preserved)
4. Links preserve the original filename at the duplicate location (pointing to master)
5. User cannot run an action without specifying `--master` flag (clear error message)
6. User can run with `--log changes.log` and find timestamped entries for every modification
7. Log entries contain: timestamp, action type, duplicate file path, master file path

---

## Progress

| Phase | Status | Requirements | Completed |
|-------|--------|--------------|-----------|
| 1 - Master Directory Foundation | ✓ Complete | 4 | 4 |
| 2 - Dry-Run Preview & Statistics | Pending | 8 | 0 |
| 3 - Actions & Logging | Pending | 12 | 0 |

**Total:** 24 requirements across 3 phases

## Coverage

All v1 requirements mapped:

| Category | Requirements | Phase |
|----------|--------------|-------|
| Master Directory | MSTR-01, MSTR-02, MSTR-03 | Phase 1 |
| Testing | TEST-01 | Phase 1 |
| Dry-Run Preview | DRY-01, DRY-02, DRY-03, DRY-04 | Phase 2 |
| Summary Statistics | STAT-01, STAT-02, STAT-03 | Phase 2 |
| Testing | TEST-02 | Phase 2 |
| Execution Infrastructure | EXEC-01, EXEC-02, EXEC-03 | Phase 3 |
| Actions | ACT-01, ACT-02, ACT-03, ACT-04 | Phase 3 |
| Change Logging | LOG-01, LOG-02, LOG-03 | Phase 3 |
| Testing | TEST-03, TEST-04 | Phase 3 |

---
*Roadmap created: 2026-01-19*
*Last revised: 2026-01-19*
*Phase 1 completed: 2026-01-19*
