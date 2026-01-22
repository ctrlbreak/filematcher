# Requirements: File Matcher v1.2

**Defined:** 2026-01-22
**Core Value:** Safely deduplicate files across directories while preserving the master copy and logging all changes.

## v1.2 Requirements

Requirements for output rationalisation milestone. Each maps to roadmap phases.

### Output Consistency

- [ ] **OUT-01**: Output structure is consistent between compare mode and action mode
- [ ] **OUT-02**: Statistics footer appears in all modes (duplicate groups, file counts, space calculations)
- [ ] **OUT-03**: Progress and status messages go to stderr, data output goes to stdout
- [ ] **OUT-04**: Output is deterministic (same input produces same output ordering)

### Machine-Readable Output

- [ ] **JSON-01**: `--json` flag outputs results in JSON format
- [ ] **JSON-02**: JSON schema is documented and stable
- [ ] **JSON-03**: JSON includes rich metadata (file sizes, hashes, timestamps)
- [ ] **JSON-04**: `--json` works with all existing flags (--summary, --verbose, --action, etc.)
- [ ] **NULL-01**: `-0` / `--null` flag outputs null-separated file paths for safe shell piping

### Enhanced UX

- [ ] **UX-01**: Color output for terminal (TTY-aware, automatically disabled in pipes)
- [ ] **UX-02**: Color highlights key information (masters, duplicates, warnings, stats)
- [ ] **UX-03**: `--no-color` flag to explicitly disable colors

## Future Requirements

Deferred to later milestones. Tracked but not in current roadmap.

### Streaming Output

- **STREAM-01**: `--jsonl` flag for JSON Lines streaming (one object per line)
- **STREAM-02**: JSONL enables processing large datasets without loading all results

### Advanced Formatting

- **FMT-01**: `--format` flag for custom output templates
- **FMT-02**: Table format output option

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| CSV output | JSON is more flexible; CSV can be derived from JSON with jq |
| XML output | No user demand; JSON covers machine-readable needs |
| Interactive output selection | Adds complexity; flags are sufficient |
| Localization/i18n | English-only tool; defer until user demand |
| Progress bars | Current verbose mode sufficient; adds dependency complexity |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| OUT-01 | Phase 7 | Pending |
| OUT-02 | Phase 7 | Pending |
| OUT-03 | Phase 5 | Pending |
| OUT-04 | Phase 5 | Pending |
| JSON-01 | Phase 6 | Pending |
| JSON-02 | Phase 6 | Pending |
| JSON-03 | Phase 6 | Pending |
| JSON-04 | Phase 6 | Pending |
| NULL-01 | Phase 6 | Pending |
| UX-01 | Phase 8 | Pending |
| UX-02 | Phase 8 | Pending |
| UX-03 | Phase 8 | Pending |

**Coverage:**
- v1.2 requirements: 12 total
- Mapped to phases: 12
- Unmapped: 0

**Phase Distribution:**
- Phase 5 (Formatter Abstraction): 2 requirements (OUT-03, OUT-04)
- Phase 6 (JSON Output): 5 requirements (JSON-01, JSON-02, JSON-03, JSON-04, NULL-01)
- Phase 7 (Output Unification): 2 requirements (OUT-01, OUT-02)
- Phase 8 (Color Enhancement): 3 requirements (UX-01, UX-02, UX-03)

---
*Requirements defined: 2026-01-22*
*Last updated: 2026-01-22 after roadmap creation (100% coverage)*
