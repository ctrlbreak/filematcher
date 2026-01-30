# Phase 21: Error Handling & Polish - Context

**Gathered:** 2026-01-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Ensure robust error recovery during file operations with comprehensive user feedback. Handle permission/access errors gracefully, provide clean summaries on quit, and show comprehensive final results including space saved and audit log location.

</domain>

<decisions>
## Implementation Decisions

### Error display format
- Claude decides inline vs separate line placement (fit existing formatter pattern)
- Include system error detail (e.g., "Permission denied", "No space left on device")
- Red color for error messages, green for success
- JSON output: both per-file error field AND top-level errors array

### Quit summary content
- Show completed actions AND remaining groups not processed
- Include partial space savings with note: "Freed 1.2 GB (quit before completing all)"
- Brief hint to re-run: "Re-run command to process remaining files"
- Exit code 130 (SIGINT convention) for user quit

### Final summary layout
- Single compact block (no section headers)
- Three-way distinction: confirmed, user-skipped (pressed 'n'), error-failed
- Space saved shows human-readable AND bytes: "Freed 1.2 GB (1,288,490,188 bytes)"
- Always show audit log path regardless of error status

### Error recovery behavior
- No automatic retries — fail once, log error, move on
- Abort execution if audit log file cannot be written (audit trail is required)
- Fully isolated group processing — errors in one group don't affect others
- Exit code 2 on any errors in batch mode (partial success = exit 2)

### Claude's Discretion
- Exact placement of inline error messages within formatter output
- Error message wording beyond including the system error
- Summary block visual styling and spacing

</decisions>

<specifics>
## Specific Ideas

- Exit code 130 matches shell convention for Ctrl+C/SIGINT interruption
- Audit log is mandatory — tool refuses to delete files without audit trail
- "Partial success = exit 2" enables scripts to detect incomplete operations

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 21-error-handling-polish*
*Context gathered: 2026-01-30*
