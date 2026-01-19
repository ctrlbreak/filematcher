# Phase 2: Dry-Run Preview & Statistics - Context

**Gathered:** 2026-01-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can preview what would happen and see aggregate statistics before any modification occurs. Includes `--dry-run` flag, planned change listing, and comprehensive statistics. Actual execution of actions is Phase 3.

</domain>

<decisions>
## Implementation Decisions

### Output format
- Grouped by duplicate set (master file, then duplicates underneath)
- Full absolute paths for all files
- --dry-run alone shows duplicates with `[DUP:?]` placeholder; with --action shows specific action
- Verbose mode (-v) adds file sizes and hashes per file
- Existing --summary/-s flag: shows only statistics, no file listing (repurposed for dry-run)
- Clear DRY-RUN banner at top: `=== DRY RUN - No changes will be made ===`

### Statistics presentation
- Footer only, with inline running totals as groups are shown
- Human-readable space savings; verbose mode adds exact bytes
- Comprehensive breakdown: groups, duplicates, masters preserved, total files scanned, space current vs after
- Action-aware stats when --action provided (e.g., "X files would become links" vs "X files would be removed")

### File grouping
- Groups ordered by master file path (alphabetical)
- Duplicates within group ordered alphabetically by path
- Visual format: `[MASTER]` prefix at base level, `[DUP]` prefix indented underneath
- Blank line between groups
- Skip groups where master has no duplicates in non-master directories
- Verbose mode shows duplicate count with master: `[MASTER] /path/file (3 duplicates)`

### Action previews
- Action shown in DUP label: `[DUP:hardlink]`, `[DUP:symlink]`, `[DUP:delete]`
- Without --action: `[DUP:?]` placeholder
- Warnings shown inline AND in summary (e.g., `[!cross-fs]` for cross-filesystem hardlink issues)
- Symlink target path shown in verbose mode only

### Claude's Discretion
- Exact banner/divider styling
- Running total format details
- Warning detection implementation
- Error message wording

</decisions>

<specifics>
## Specific Ideas

- Phase 1 output format should be refactored to match new `[MASTER]`/`[DUP]` indented style before Phase 2 implementation (separate prep task)
- Cross-filesystem warnings are important for hardlinks - detect and warn proactively

</specifics>

<deferred>
## Deferred Ideas

- Refactor Phase 1 output format to `[MASTER]`/`[DUP]` style — prep task before Phase 2

</deferred>

---

*Phase: 02-dry-run-preview*
*Context gathered: 2026-01-19*
