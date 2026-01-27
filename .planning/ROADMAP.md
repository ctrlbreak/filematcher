# Roadmap: File Matcher

## Milestones

- v1.1 Deduplication - Phases 1-4 (shipped 2026-01-20)
- v1.3 Code Unification - Phases 5-10 (shipped 2026-01-23)
- **v1.4 Package Structure** - Phases 11-17 (in progress)

## Phases

<details>
<summary>v1.1 Deduplication (Phases 1-4) - SHIPPED 2026-01-20</summary>

### Phase 1: Master Directory Foundation
**Goal**: Designate master directory and validate structure
**Plans**: 3 plans

Plans:
- [x] 01-01: CLI flag and validation
- [x] 01-02: Master protection logic
- [x] 01-03: Testing and documentation

### Phase 2: Preview Mode Safety
**Goal**: Safe preview-by-default with execution guards
**Plans**: 3 plans

Plans:
- [x] 02-01: Preview mode implementation
- [x] 02-02: Execute flag and confirmation
- [x] 02-03: Testing preview/execute paths

### Phase 3: Deduplication Actions
**Goal**: Implement hardlink, symlink, and delete actions
**Plans**: 4 plans

Plans:
- [x] 03-01: Hardlink implementation
- [x] 03-02: Symlink implementation
- [x] 03-03: Delete action
- [x] 03-04: Cross-filesystem detection

### Phase 4: Audit Logging
**Goal**: Comprehensive modification tracking
**Plans**: 2 plans

Plans:
- [x] 04-01: Audit logger implementation
- [x] 04-02: Testing and log format validation

</details>

<details>
<summary>v1.3 Code Unification (Phases 5-10) - SHIPPED 2026-01-23</summary>

### Phase 5: Formatter Abstraction
**Goal**: Create unified output abstraction layer
**Requirements**: OUT-04
**Plans**: 3 plans
**Completed**: 2026-01-22

Plans:
- [x] 05-01: Define ABC hierarchy and Text implementations
- [x] 05-02: Wire TextActionFormatter into main()
- [x] 05-03: Wire TextCompareFormatter into main()

### Phase 6: JSON Output
**Goal**: Expose JSON output through CLI
**Requirements**: JSON-01, JSON-02, JSON-03, JSON-04
**Plans**: 3 plans
**Completed**: 2026-01-23

Plans:
- [x] 06-01: Implement Json formatters
- [x] 06-02: Add --json CLI flag
- [x] 06-03: Tests and documentation

### Phase 7: Output Unification
**Goal**: Consistent output structure with statistics
**Requirements**: OUT-01, OUT-02, OUT-03
**Plans**: 4 plans
**Completed**: 2026-01-23

Plans:
- [x] 07-01: Stream separation and --quiet flag
- [x] 07-02: Unified header format
- [x] 07-03: Statistics footer
- [x] 07-04: Tests and documentation

### Phase 8: Color Enhancement
**Goal**: TTY-aware color output
**Requirements**: UX-01, UX-02, UX-03
**Plans**: 3 plans
**Completed**: 2026-01-23

Plans:
- [x] 08-01: ColorConfig and ANSI helpers
- [x] 08-02: CLI flags and formatter integration
- [x] 08-03: Tests and documentation

### Phase 9: Unify Group Output
**Goal**: Consistent group format between modes
**Plans**: 1 plan
**Completed**: 2026-01-23

Plans:
- [x] 09-01: Hierarchical output format

### Phase 10: Unify Compare as Action
**Goal**: Refactor compare mode to use action code path
**Plans**: 4 plans
**Completed**: 2026-01-23

Plans:
- [x] 10-01: Add compare to action choices
- [x] 10-02: Extend ActionFormatter for compare
- [x] 10-03: Unify main() flow
- [x] 10-04: Delete CompareFormatter hierarchy

</details>

### v1.4 Package Structure (In Progress)

**Milestone Goal:** Refactor single-file implementation to package structure for better code navigation and AI tooling compatibility while maintaining full backward compatibility.

#### Phase 11: Package Scaffolding
**Goal**: Create filematcher/ package structure with re-export foundation
**Depends on**: Phase 10
**Requirements**: PKG-01, PKG-02
**Success Criteria** (what must be TRUE):
  1. `from filematcher import main` imports successfully
  2. `python -m filematcher --help` displays help text
  3. All 217 tests pass unchanged (no test modifications)
**Plans**: 1 plan
**Completed**: 2026-01-27

Plans:
- [x] 11-01-PLAN.md - Create package with __init__.py re-exports and __main__.py

#### Phase 12: Extract Foundation Modules
**Goal**: Extract leaf modules with no internal dependencies (color, hashing)
**Depends on**: Phase 11
**Requirements**: MOD-01, MOD-02
**Success Criteria** (what must be TRUE):
  1. `from filematcher.colors import ColorConfig, green, red` works
  2. `from filematcher.hashing import get_file_hash, get_sparse_hash` works
  3. Color and hashing tests pass without modification
  4. All 217 tests pass
**Plans**: 2 plans
**Completed**: 2026-01-27

Plans:
- [x] 12-01-PLAN.md - Extract color system to filematcher/colors.py
- [x] 12-02-PLAN.md - Extract hashing functions to filematcher/hashing.py

#### Phase 13: Extract Filesystem and Actions
**Goal**: Extract filesystem helpers and action execution modules
**Depends on**: Phase 12
**Requirements**: MOD-03, MOD-04
**Success Criteria** (what must be TRUE):
  1. `from filematcher.filesystem import is_hardlink_to, check_cross_filesystem` works
  2. `from filematcher.actions import execute_action, safe_replace_with_link` works
  3. Action and filesystem tests pass without modification
  4. All 217 tests pass
**Plans**: TBD

Plans:
- [ ] 13-01: TBD

#### Phase 14: Extract Formatters and Directory
**Goal**: Extract output formatters and directory operations modules
**Depends on**: Phase 13
**Requirements**: MOD-05, MOD-06
**Success Criteria** (what must be TRUE):
  1. `from filematcher.formatters import ActionFormatter, TextActionFormatter` works
  2. `from filematcher.directory import find_matching_files, index_directory` works
  3. JSON, color output, and directory operation tests pass
  4. All 217 tests pass
**Plans**: TBD

Plans:
- [ ] 14-01: TBD

#### Phase 15: Extract Logging and CLI
**Goal**: Extract audit logging and CLI modules, finalize entry points
**Depends on**: Phase 14
**Requirements**: MOD-07, MOD-08, PKG-03
**Success Criteria** (what must be TRUE):
  1. `from filematcher.logging import create_audit_logger` works
  2. `filematcher --help` works after pip install -e .
  3. `python -m filematcher <args>` executes correctly
  4. All 217 tests pass
**Plans**: TBD

Plans:
- [ ] 15-01: TBD

#### Phase 16: Backward Compatibility
**Goal**: Establish file_matcher.py as thin wrapper with full re-exports
**Depends on**: Phase 15
**Requirements**: COMPAT-01, COMPAT-02, COMPAT-03, COMPAT-04
**Success Criteria** (what must be TRUE):
  1. `python file_matcher.py dir1 dir2` works identically to before
  2. `filematcher dir1 dir2` works via pip install
  3. `from file_matcher import get_file_hash, find_matching_files` works (re-exports)
  4. All public symbols importable from `filematcher` package
  5. All 217 tests pass
**Plans**: TBD

Plans:
- [ ] 16-01: TBD

#### Phase 17: Verification and Cleanup
**Goal**: Verify all requirements met, update test imports, finalize documentation
**Depends on**: Phase 16
**Requirements**: TEST-01, TEST-02, TEST-03, PKG-04, PKG-05
**Success Criteria** (what must be TRUE):
  1. All 217 tests pass with `from filematcher import X` pattern
  2. No module exceeds 500 lines (improved maintainability)
  3. No circular imports (verified via fresh Python subprocess)
  4. Package imports cleanly from fresh venv
**Plans**: TBD

Plans:
- [ ] 17-01: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 11 -> 12 -> 13 -> 14 -> 15 -> 16 -> 17

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Master Directory | v1.1 | 3/3 | Complete | 2026-01-20 |
| 2. Preview Mode | v1.1 | 3/3 | Complete | 2026-01-20 |
| 3. Deduplication | v1.1 | 4/4 | Complete | 2026-01-20 |
| 4. Audit Logging | v1.1 | 2/2 | Complete | 2026-01-20 |
| 5. Formatter Abstraction | v1.3 | 3/3 | Complete | 2026-01-22 |
| 6. JSON Output | v1.3 | 3/3 | Complete | 2026-01-23 |
| 7. Output Unification | v1.3 | 4/4 | Complete | 2026-01-23 |
| 8. Color Enhancement | v1.3 | 3/3 | Complete | 2026-01-23 |
| 9. Unify Group Output | v1.3 | 1/1 | Complete | 2026-01-23 |
| 10. Unify Compare as Action | v1.3 | 4/4 | Complete | 2026-01-23 |
| 11. Package Scaffolding | v1.4 | 1/1 | Complete | 2026-01-27 |
| 12. Foundation Modules | v1.4 | 2/2 | Complete | 2026-01-27 |
| 13. Filesystem and Actions | v1.4 | 0/TBD | Not started | - |
| 14. Formatters and Directory | v1.4 | 0/TBD | Not started | - |
| 15. Logging and CLI | v1.4 | 0/TBD | Not started | - |
| 16. Backward Compatibility | v1.4 | 0/TBD | Not started | - |
| 17. Verification | v1.4 | 0/TBD | Not started | - |

---
*Last updated: 2026-01-27 - Phase 12 complete*
