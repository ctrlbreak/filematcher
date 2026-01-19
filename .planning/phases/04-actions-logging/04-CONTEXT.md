# Phase 4: Actions & Logging - Context

**Gathered:** 2026-01-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Execute deduplication actions (hardlink, symlink, delete) with a complete audit trail of all changes. Requires `--master`, `--action`, and `--execute` flags. Preview mode (from Phase 3) shows what would happen; execution mode performs the modifications with logging.

</domain>

<decisions>
## Implementation Decisions

### Error handling
- Continue with remaining files on individual operation failure (don't halt)
- Summary at end: "12 succeeded, 3 failed" with failed paths listed
- Exit code 3 for partial completion (0=full success, 1=total failure, 3=partial)
- No retry on failure — fail once, log it, move on
- Cross-filesystem hardlinks: add `--fallback-symlink` flag to auto-fallback to symlink; without flag, count as failure
- Missing duplicate at execution time: warning in summary, doesn't affect exit code
- Don't re-verify file content before replacing (trust the scan)
- Missing master at execution time: skip entire group, count as failure

### Log format
- Plain text format: human-readable lines
- Verbose content: timestamp, action, duplicate path, master path, file size, result (success/failed/skipped), file hash, failure reason if any
- Default log location: current directory as `filematcher_YYYYMMDD_HHMMSS.log`
- `--log` flag to specify custom path
- Include header (run info: timestamp, directories, action type, flags) and footer (summary with totals)

### Confirmation flow
- Interactive confirmation prompt by default with `--execute`
- `--yes/-y` flag to skip prompt for non-interactive/CI use
- Prompt shows brief summary + space savings: "47 files will be replaced with hardlinks. ~2.3GB will be saved. Proceed? [y/N]"
- Progress counter during execution ("Processing 5/47...")
- Per-file output when `--verbose` is enabled
- Exit 0 if user declines confirmation (valid outcome, not an error)

### Action behavior
- Three action types only: hardlink, symlink, delete
- Symlinks use absolute paths to master
- Delete is permanent (os.unlink), not trash
- Extra warning message in confirmation prompt for delete action about irreversibility
- Temp-rename approach for safety: rename duplicate to .tmp, create link, delete .tmp
- If link creation fails, restore .tmp to original filename
- Links preserve original filename at duplicate location (per ACT-04)
- No batch size limits — process all files in one run

### Assumptions to verify
- `index_directory()` already skips symlinks (uses `Path.is_file()`) — duplicates should always be regular files

### Claude's Discretion
- Exact log line format within the verbose constraint
- .tmp file naming convention for temp-rename
- How to detect "already linked to master" edge case if it can occur
- Progress counter implementation details

</decisions>

<specifics>
## Specific Ideas

- Exit codes should be distinct: 0 (success), 1 (total failure), 2 (validation error — existing), 3 (partial completion)
- Confirmation prompt should match standard CLI conventions: "[y/N]" with N as default
- Log filename format: `filematcher_YYYYMMDD_HHMMSS.log`

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 04-actions-logging*
*Context gathered: 2026-01-19*
