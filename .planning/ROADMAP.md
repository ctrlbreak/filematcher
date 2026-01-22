# Roadmap: File Matcher

## Milestones

- ✅ **v1.1 Deduplication** - Phases 1-4 (shipped 2026-01-20)
- 🚧 **v1.2 Output Rationalisation** - Phases 5-8 (in progress)

## Phases

<details>
<summary>✅ v1.1 Deduplication (Phases 1-4) - SHIPPED 2026-01-20</summary>

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

### 🚧 v1.2 Output Rationalisation (In Progress)

**Milestone Goal:** Unify output formatting across modes and add machine-readable JSON output for scripting and automation.

#### Phase 5: Formatter Abstraction ✓
**Goal**: Create unified output abstraction layer without changing user-visible behavior
**Depends on**: Phase 4
**Requirements**: OUT-04
**Success Criteria** (what must be TRUE):
  1. OutputFormatter ABC hierarchy exists (CompareFormatter, ActionFormatter)
  2. TextFormatter implementations wrap existing format functions and produce identical output
  3. All existing tests pass without modification
  4. Output is deterministic across multiple runs with same input
**Plans**: 3 plans
**Completed**: 2026-01-22

Plans:
- [x] 05-01-PLAN.md — Define ABC hierarchy (CompareFormatter, ActionFormatter) and TextFormatter implementations
- [x] 05-02-PLAN.md — Wire TextActionFormatter into main() action mode branches
- [x] 05-03-PLAN.md — Wire TextCompareFormatter into main() compare mode branches

#### Phase 6: JSON Output
**Goal**: Expose JSON output through CLI with stable schema and comprehensive metadata
**Depends on**: Phase 5
**Requirements**: JSON-01, JSON-02, JSON-03, JSON-04
**Success Criteria** (what must be TRUE):
  1. User can run `filematcher dir1 dir2 --json` and receive valid JSON output
  2. JSON schema is documented with version field and examples
  3. JSON includes rich metadata (file sizes, hashes, timestamps, action types)
  4. `--json` works correctly with all existing flags (--summary, --verbose, --action, --execute)
  5. Text output remains unchanged (no breaking changes to default format)
**Plans**: TBD

Plans:
- [ ] 06-01: TBD

#### Phase 7: Output Unification
**Goal**: Consistent output structure across compare and action modes with statistics in all modes
**Depends on**: Phase 6
**Requirements**: OUT-01, OUT-02, OUT-03
**Success Criteria** (what must be TRUE):
  1. Compare mode and action mode use identical output structure (same sections, same ordering)
  2. Statistics footer appears in all modes (compare, action preview, action execute)
  3. Statistics include duplicate groups count, file counts, and space calculations
  4. All output routes through formatter abstraction (no direct print statements)
  5. Progress messages go to stderr, data output goes to stdout
**Plans**: TBD

Plans:
- [ ] 07-01: TBD

#### Phase 8: Color Enhancement
**Goal**: TTY-aware color output highlighting key information
**Depends on**: Phase 7
**Requirements**: UX-01, UX-02, UX-03
**Success Criteria** (what must be TRUE):
  1. Color output automatically enabled when stdout is a TTY
  2. Color automatically disabled when piped or redirected
  3. Colors highlight masters (green), duplicates (yellow), warnings (red), statistics (cyan)
  4. `--no-color` flag explicitly disables colors
  5. NO_COLOR environment variable is respected
  6. Text content is identical with or without color (only ANSI codes added)
**Plans**: TBD

Plans:
- [ ] 08-01: TBD

## Progress

**Execution Order:** Phases execute in numeric order: 5 → 6 → 7 → 8

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Master Directory | v1.1 | 3/3 | Complete | 2026-01-20 |
| 2. Preview Mode | v1.1 | 3/3 | Complete | 2026-01-20 |
| 3. Deduplication | v1.1 | 4/4 | Complete | 2026-01-20 |
| 4. Audit Logging | v1.1 | 2/2 | Complete | 2026-01-20 |
| 5. Formatter Abstraction | v1.2 | 3/3 | Complete | 2026-01-22 |
| 6. JSON Output | v1.2 | 0/? | Not started | - |
| 7. Output Unification | v1.2 | 0/? | Not started | - |
| 8. Color Enhancement | v1.2 | 0/? | Not started | - |

---
*Last updated: 2026-01-22 - Phase 5 complete*
