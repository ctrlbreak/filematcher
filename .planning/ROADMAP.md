# Roadmap: File Matcher Deduplication

**Created:** 2026-01-19
**Core Value:** Safely deduplicate files across directories while preserving the master copy and logging all changes.

## Overview

This roadmap delivers deduplication capabilities in four phases: foundation (master directory concept), preview (dry-run and statistics), safe defaults refactor, and actions (execution with logging). Each phase builds incrementally - Phase 1 establishes master/duplicate identification, Phase 2 adds preview capabilities, Phase 3 makes preview the safe default, and Phase 4 enables actual modifications with audit trails.

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

**Plans:** 4 plans

Plans:
- [x] 02-01-PLAN.md — Refactor output to [MASTER]/[DUP] hierarchical format
- [x] 02-02-PLAN.md — Add statistics calculation and cross-filesystem detection
- [x] 02-03-PLAN.md — Implement --dry-run flag with banner and statistics footer
- [x] 02-04-PLAN.md — Unit tests for dry-run output formatting (TEST-02)

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

### Phase 3: Safe Defaults Refactor

**Goal:** Preview mode becomes the default behavior; actual modifications require explicit `--execute` flag for safety.

**Dependencies:** Phase 2 (refactors existing dry-run infrastructure)

**Plans:** 2 plans

Plans:
- [x] 03-01-PLAN.md — Refactor CLI for preview-by-default with --execute flag
- [x] 03-02-PLAN.md — Unit tests for safe default behavior (TEST-03)

**Requirements:**
- SAFE-01: Preview mode is the default when `--action` is specified (no `--dry-run` needed)
- SAFE-02: `--execute` flag enables actual file modifications
- SAFE-03: `--dry-run` flag removed (preview is always default without `--execute`)
- SAFE-04: Clear messaging when preview mode is active ("use --execute to apply changes")
- TEST-03: Unit tests for safe default behavior and --execute flag

**Success Criteria:**
1. User can run `filematcher dir1 dir2 --master dir1 --action hardlink` and see a preview (no files modified)
2. User must add `--execute` to actually perform modifications
3. Banner clearly indicates "PREVIEW MODE" when `--execute` is not specified
4. Statistics footer suggests `--execute` flag to apply changes
5. All existing dry-run tests updated to reflect new default behavior

---

### Phase 4: Actions & Logging

**Goal:** Users can execute deduplication actions with a complete audit trail of all changes.

**Dependencies:** Phase 3 (requires --execute flag infrastructure)

**Plans:** 4 plans

Plans:
- [ ] 04-01-PLAN.md — Action execution engine (hardlink, symlink, delete)
- [ ] 04-02-PLAN.md — Audit logging system with --log flag
- [ ] 04-03-PLAN.md — CLI integration (--fallback-symlink, confirmation, progress)
- [ ] 04-04-PLAN.md — Unit and integration tests (TEST-04, TEST-05)

**Requirements:**
- EXEC-01: Support `--action` flag for specifying action type (hardlink, symlink, delete)
- EXEC-02: Execution mode runs when `--execute` flag is specified with `--action`
- EXEC-03: Execution requires `--master`, `--action`, and `--execute` flags
- ACT-01: Replace duplicate files with hard links to master
- ACT-02: Replace duplicate files with symbolic links to master
- ACT-03: Delete duplicate files (keeping master only)
- ACT-04: Links preserve original filename (pointing to master file)
- LOG-01: All changes are logged with timestamp
- LOG-02: Log includes: action type, source file path, target file path
- LOG-03: Log file path configurable via `--log` flag
- TEST-04: Unit tests for change logging
- TEST-05: Integration tests for CLI flag combinations

**Success Criteria:**
1. User can run `filematcher dir1 dir2 --master dir1 --action hardlink --execute` and duplicate files are replaced with hard links
2. User can run with `--action symlink --execute` and duplicate files are replaced with symbolic links
3. User can run with `--action delete --execute` and duplicate files are deleted (master preserved)
4. Links preserve the original filename at the duplicate location (pointing to master)
5. User cannot execute without all three flags: `--master`, `--action`, and `--execute`
6. User can run with `--log changes.log` and find timestamped entries for every modification
7. Log entries contain: timestamp, action type, duplicate file path, master file path

---

## Progress

| Phase | Status | Requirements | Completed |
|-------|--------|--------------|-----------|
| 1 - Master Directory Foundation | Complete | 4 | 4 |
| 2 - Dry-Run Preview & Statistics | Complete | 8 | 8 |
| 3 - Safe Defaults Refactor | Complete | 5 | 5 |
| 4 - Actions & Logging | Planned | 12 | 0 |

**Total:** 29 requirements across 4 phases

## Coverage

All v1 requirements mapped:

| Category | Requirements | Phase |
|----------|--------------|-------|
| Master Directory | MSTR-01, MSTR-02, MSTR-03 | Phase 1 |
| Testing | TEST-01 | Phase 1 |
| Dry-Run Preview | DRY-01, DRY-02, DRY-03, DRY-04 | Phase 2 |
| Summary Statistics | STAT-01, STAT-02, STAT-03 | Phase 2 |
| Testing | TEST-02 | Phase 2 |
| Safe Defaults | SAFE-01, SAFE-02, SAFE-03, SAFE-04 | Phase 3 |
| Testing | TEST-03 | Phase 3 |
| Execution Infrastructure | EXEC-01, EXEC-02, EXEC-03 | Phase 4 |
| Actions | ACT-01, ACT-02, ACT-03, ACT-04 | Phase 4 |
| Change Logging | LOG-01, LOG-02, LOG-03 | Phase 4 |
| Testing | TEST-04, TEST-05 | Phase 4 |

---
*Roadmap created: 2026-01-19*
*Last revised: 2026-01-19*
*Phase 1 completed: 2026-01-19*
*Phase 2 completed: 2026-01-19*
*Phase 3 added: 2026-01-19 (safe defaults refactor)*
*Phase 3 planned: 2026-01-19*
*Phase 3 completed: 2026-01-19*
*Phase 4 planned: 2026-01-19*
