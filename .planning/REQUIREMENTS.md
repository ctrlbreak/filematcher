# Requirements: File Matcher v1.2

**Defined:** 2026-01-22
**Core Value:** Safely deduplicate files across directories while preserving the master copy and logging all changes.

## v1.2 Requirements

Requirements for output rationalisation milestone. Each maps to roadmap phases.

### Output Consistency

- [x] **OUT-01**: Output structure is consistent between compare mode and action mode
- [x] **OUT-02**: Statistics footer appears in all modes (duplicate groups, file counts, space calculations)
- [x] **OUT-03**: Progress and status messages go to stderr, data output goes to stdout
- [x] **OUT-04**: Output is deterministic (same input produces same output ordering)

### Machine-Readable Output

- [x] **JSON-01**: `--json` flag outputs results in JSON format
- [x] **JSON-02**: JSON schema is documented and stable
- [x] **JSON-03**: JSON includes rich metadata (file sizes, hashes, timestamps)
- [x] **JSON-04**: `--json` works with all existing flags (--summary, --verbose, --action, etc.)

### Enhanced UX

- [x] **UX-01**: Color output for terminal (TTY-aware, automatically disabled in pipes)
- [x] **UX-02**: Color highlights key information (masters, duplicates, warnings, stats)
- [x] **UX-03**: `--no-color` flag to explicitly disable colors

## Future Requirements

Deferred to later milestones. Tracked but not in current roadmap.

### Null-Separated Output

- **NULL-01**: `-0` / `--null` flag outputs null-separated file paths for safe shell piping

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
| OUT-01 | Phase 7 | Complete |
| OUT-02 | Phase 7 | Complete |
| OUT-03 | Phase 7 | Complete |
| OUT-04 | Phase 5 | Complete |
| JSON-01 | Phase 6 | Complete |
| JSON-02 | Phase 6 | Complete |
| JSON-03 | Phase 6 | Complete |
| JSON-04 | Phase 6 | Complete |
| UX-01 | Phase 8 | Complete |
| UX-02 | Phase 8 | Complete |
| UX-03 | Phase 8 | Complete |

**Coverage:**
- v1.2 requirements: 11 total
- Mapped to phases: 11
- Unmapped: 0

**Phase Distribution:**
- Phase 5 (Formatter Abstraction): 1 requirement (OUT-04)
- Phase 6 (JSON Output): 4 requirements (JSON-01, JSON-02, JSON-03, JSON-04)
- Phase 7 (Output Unification): 3 requirements (OUT-01, OUT-02, OUT-03)
- Phase 8 (Color Enhancement): 3 requirements (UX-01, UX-02, UX-03)

**Notes:**
- OUT-03 (stderr/stdout separation) deferred from Phase 5 to Phase 7: The formatter abstraction (Phase 5) creates the infrastructure, but actual stream routing requires output unification work. Implementing OUT-03 during Phase 7 ensures all output paths are unified before splitting streams.

---
*Requirements defined: 2026-01-22*
*Last updated: 2026-01-23 - v1.2 complete (all 11 requirements implemented)*
