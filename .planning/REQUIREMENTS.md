# Requirements: File Matcher Deduplication

**Defined:** 2026-01-19
**Core Value:** Safely deduplicate files across directories while preserving the master copy and logging all changes.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Master Directory

- [x] **MSTR-01**: User can designate one directory as "master" via `--master` flag
- [x] **MSTR-02**: Files in master directory are never modified or deleted
- [x] **MSTR-03**: Tool validates master directory is one of the compared directories

### Dry-Run Preview

- [x] **DRY-01**: User can preview planned changes with `--dry-run` flag
- [x] **DRY-02**: Dry-run shows list of files that would be modified
- [x] **DRY-03**: Dry-run shows what action would be taken on each file
- [x] **DRY-04**: Dry-run shows estimated space savings before execution

### Change Logging

- [ ] **LOG-01**: All planned changes are logged with timestamp
- [ ] **LOG-02**: Log includes: action type, source file path, target file path
- [ ] **LOG-03**: Log file path configurable via `--log` flag

### Summary Statistics

- [x] **STAT-01**: Display count of duplicate groups found
- [x] **STAT-02**: Display count of files that would be affected
- [x] **STAT-03**: Display total space that would be saved/reclaimed

### Execution Infrastructure

- [ ] **EXEC-01**: Support `--action` flag for specifying action type (hardlink, symlink, delete)
- [ ] **EXEC-02**: Auto execution mode runs without prompts when action specified
- [ ] **EXEC-03**: Action requires both `--master` and `--action` flags to be set

### Actions

- [ ] **ACT-01**: Replace duplicate files with hard links to master
- [ ] **ACT-02**: Replace duplicate files with symbolic links to master
- [ ] **ACT-03**: Delete duplicate files (keeping master only)
- [ ] **ACT-04**: Links preserve original filename (pointing to master file)

### Testing

- [x] **TEST-01**: Unit tests for master directory validation
- [x] **TEST-02**: Unit tests for dry-run output formatting
- [ ] **TEST-03**: Unit tests for change logging
- [ ] **TEST-04**: Integration tests for CLI flag combinations

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Interactive Mode

- **INT-01**: Interactive mode prompts for confirmation on each change
- **INT-02**: User can approve, skip, or quit during interactive mode
- **INT-03**: "Approve all remaining" option in interactive mode

### Advanced Features

- **ADV-01**: Relative symlinks option for portable links
- **ADV-02**: JSON output format for scripting integration

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Automatic backup creation | User responsibility; adds complexity |
| Multi-directory (3+) master selection | Complexity explosion with unclear priority |
| GUI interface | CLI-focused tool |
| Undo/rollback functionality | Log file serves as record; manual recovery |
| File renaming to match master | Links preserve original names by design |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| MSTR-01 | Phase 1 | Complete |
| MSTR-02 | Phase 1 | Complete |
| MSTR-03 | Phase 1 | Complete |
| TEST-01 | Phase 1 | Complete |
| DRY-01 | Phase 2 | Complete |
| DRY-02 | Phase 2 | Complete |
| DRY-03 | Phase 2 | Complete |
| DRY-04 | Phase 2 | Complete |
| STAT-01 | Phase 2 | Complete |
| STAT-02 | Phase 2 | Complete |
| STAT-03 | Phase 2 | Complete |
| TEST-02 | Phase 2 | Complete |
| EXEC-01 | Phase 3 | Pending |
| EXEC-02 | Phase 3 | Pending |
| EXEC-03 | Phase 3 | Pending |
| LOG-01 | Phase 3 | Pending |
| LOG-02 | Phase 3 | Pending |
| LOG-03 | Phase 3 | Pending |
| TEST-03 | Phase 3 | Pending |
| TEST-04 | Phase 3 | Pending |
| ACT-01 | Phase 3 | Pending |
| ACT-02 | Phase 3 | Pending |
| ACT-03 | Phase 3 | Pending |
| ACT-04 | Phase 3 | Pending |

**Coverage:**
- v1 requirements: 24 total
- Mapped to phases: 24
- Unmapped: 0

---
*Requirements defined: 2026-01-19*
*Last updated: 2026-01-19 (Phase 2 complete)*
