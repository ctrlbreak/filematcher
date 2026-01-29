# Phase 19: Interactive Core - Context

**Gathered:** 2026-01-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Build per-group display-prompt-decide loop in cli.py. User sees each duplicate group, responds to prompt (y/n/a/q), and action executes immediately after confirmation. Loop continues until all groups processed or user quits.

</domain>

<decisions>
## Implementation Decisions

### Execution Model
- Actions execute immediately after each 'y' response (not batched)
- Each group: display → prompt → response → execute (if confirmed) → next group
- No batch collection of decisions

### "Yes to All" Behavior
- Pressing 'a' confirms current group immediately + all remaining (no extra confirmation prompt)
- Shows "Processing N remaining groups..." message (already in Phase 18 formatter)
- Remaining groups are NOT displayed — process silently
- Shows "All groups processed." completion message before final summary

### Quit Behavior
- Already-processed groups stay processed (actions executed immediately, no rollback)
- Shows "Cancelled. Skipping X remaining groups." message
- Then shows summary (same format regardless of how quit happened)
- Quitting on first group: same behavior (0 processed, N skipped in summary)
- Exit code: 2 (partial) when user quits with unprocessed groups

### Invalid Input Handling
- Show inline error message + re-prompt (don't re-display full group)
- Error message: "Please enter y (yes), n (no), a (all), or q (quit): "
- Empty input (just Enter) treated as invalid
- No limit on consecutive invalid inputs — keep re-prompting

### Claude's Discretion
- Internal state management approach
- Whether to use a generator/iterator pattern
- Error handling for action execution failures (Phase 21 scope, but planner can note integration points)

</decisions>

<specifics>
## Specific Ideas

- "Actions should be processed after each individual prompt" — user wants immediate feedback, not batch
- Immediate execution model means 'q' is truly "stop asking, skip to summary" not "cancel everything"

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 19-interactive-core*
*Context gathered: 2026-01-29*
