# Phase 7: Output Unification - Context

**Gathered:** 2026-01-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Unify output formatting across compare and action modes. Both modes use identical structure with statistics in all modes. Progress/warnings go to stderr, data to stdout. No new capabilities — just consistent presentation of existing functionality.

</domain>

<decisions>
## Implementation Decisions

### Section structure
- Directory header at top showing what's being compared
- Master-first grouping: each duplicate group shows master file, then its duplicates
- Unmatched files: keep current behavior (separate section, only with --show-unmatched flag)
- Statistics placement: one-liner summary at header, detailed stats at footer

### Statistics content
- Always show: duplicate groups count, file counts (scanned/matched/unmatched), space savings calculation
- Header summary: one-liner format ("Found 12 duplicate groups (47 files, 1.2GB reclaimable)")
- Action mode adds action-specific stats ("5 hardlinked, 2 deleted")
- Compare mode shows same base stats without action counts

### Stream separation
- Add --quiet flag: suppresses progress, warnings, header — only file listings remain
- Verbose info (--verbose) goes to same stream as related output
- Claude's discretion: what goes to stderr vs stdout for progress/warnings (follow Unix conventions)
- Claude's discretion: whether header summary goes to stdout or stderr

### Mode alignment
- Identical structure between compare and action modes (same sections, same ordering)
- Action display: both inline markers ("[hardlinked]") AND summary section
- Preview mode: show planned actions ("file.txt [will hardlink]") not just duplicates
- Header must explicitly indicate mode: "Compare mode: dir1 vs dir2" or "Action mode (PREVIEW): hardlink"
- **CRITICAL**: Header must clearly distinguish PREVIEW vs EXECUTING mode
- **CRITICAL**: Preserve interactive confirmation for --execute unless --yes flag is set (existing behavior)

### Claude's Discretion
- Exact space savings format (human-readable vs both human and bytes)
- stderr/stdout split for progress messages and warnings
- Header summary stream placement

</decisions>

<specifics>
## Specific Ideas

- Preview vs execute distinction must be unmistakable in header — user should never accidentally execute
- Interactive confirmation flow unchanged — --yes bypasses, otherwise prompt remains

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 07-output-unification*
*Context gathered: 2026-01-23*
