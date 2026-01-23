# Roadmap: File Matcher

## Milestones

- ✅ **v1.1 Deduplication** - Phases 1-4 (shipped 2026-01-20)
- ✅ **v1.3 Code Unification** - Phases 5-10 (shipped 2026-01-23)

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

<details>
<summary>✅ v1.3 Code Unification (Phases 5-10) - SHIPPED 2026-01-23</summary>

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

## Progress

**All phases complete. Use `/gsd:new-milestone` to start next milestone.**

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

---
*Last updated: 2026-01-23 - v1.3 milestone archived*
