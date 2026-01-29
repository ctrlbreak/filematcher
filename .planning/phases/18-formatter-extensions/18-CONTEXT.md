# Phase 18: Formatter Extensions - Context

**Gathered:** 2026-01-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Add prompt formatting methods to the existing ActionFormatter ABC. This extends the Strategy pattern to support interactive execution mode with group prompts, progress indicators, and confirmation feedback. The formatter layer provides consistent output formatting; the interactive loop itself is Phase 19.

</domain>

<decisions>
## Implementation Decisions

### Prompt Text Design
- Brief explanation style: "Delete duplicate? [y/n/a/q]" (action-specific verb with options hint)
- Action-specific verbs: "Delete duplicate?", "Create hardlink?", "Create symlink?" — matches the action
- No file path in prompt — group display already showed the files
- Options hint at end of prompt line: "Delete duplicate? [y/n/a/q]"

### Progress Indicator Format
- Format: `[3/10]` — square brackets, slash separator
- Placement: Start of prompt line — "[3/10] Delete duplicate? [y/n/a/q]"
- Color: Dimmed/gray so it doesn't compete with the prompt text
- After 'a' (all): Show remaining count message like "Processing 7 remaining groups..."

### Confirmation Feedback
- Confirmed actions (y): Green checkmark (✓)
- Skipped actions (n): Yellow X mark (✗)
- Placement: Same line as prompt, appended after response
- Content: Symbol only — no path, no action text

### JSON Interactive Behavior
- JSON mode does NOT support interactive prompts
- `--json --execute` without `--yes` is an error
- Error message: "--json --execute requires --yes (non-interactive mode)"
- Validation happens at CLI layer (fails fast during argument parsing)

### Claude's Discretion
- Whether JsonActionFormatter implements prompt methods as no-ops or raises errors
- Exact wording variations if needed for grammar
- How to handle terminal width constraints

</decisions>

<specifics>
## Specific Ideas

- Prompt should feel like standard Unix interactive tools (rm -i, git add -p)
- Progress indicator dimmed so user's eye goes to the action, not the counter

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 18-formatter-extensions*
*Context gathered: 2026-01-29*
