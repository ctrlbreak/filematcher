# Phase 3: Safe Defaults Refactor - Context

**Gathered:** 2026-01-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Refactor the CLI so preview mode is the default behavior when `--action` is specified. Actual file modifications require explicit `--execute` flag. Remove `--dry-run` flag entirely. Add interactive confirmation before execution.

</domain>

<decisions>
## Implementation Decisions

### Transition Messaging
- Use "PREVIEW MODE" banner (not "DRY RUN") with text: "PREVIEW MODE - Use --execute to apply changes"
- No mention of deprecated --dry-run — clean break to new terminology
- `--execute` hint appears in both banner AND statistics footer
- When `--execute` is used, show "EXECUTING" banner before confirmation prompt

### Interactive Confirmation
- `--execute` triggers interactive Y/N confirmation prompt
- Show full preview output + statistics, then prompt: "Proceed? [y/N]"
- Default is No (pressing Enter cancels)
- Add `--yes/-y` flag to skip confirmation for CI/scripting
- Abort message: "Aborted. No changes made."

### Flag Semantics
- Remove `--dry-run` flag entirely — argparse error if used
- `--execute` without `--action` is an error: "--execute requires --master and --action"
- `--execute` has no short flag — intentionally verbose for safety
- Required combination for execution: `--master` + `--action` + `--execute`

### Error Handling
- Missing required flags for `--execute`: generic error message listing all required flags
- `--yes/-y` without `--execute`: silently ignored (no effect)
- Validation errors (missing flags): exit code 2 (argparse convention)
- User aborts at confirmation: exit code 0 (clean exit, not an error)

### Output Differentiation
- Preview mode: action labels use "would" prefix — [WOULD HARDLINK], [WOULD SYMLINK], [WOULD DELETE]
- Preview stats: "Would save X bytes" / Execute stats: "Saved X bytes" (same format, different verb)
- After successful execution: detailed summary — "Completed: X hardlinks created, Y bytes saved."

### Claude's Discretion
- Execute mode per-file output format (real-time progress vs summary)
- Exact wording of confirmation prompt
- Color/formatting of banners if terminal supports it

</decisions>

<specifics>
## Specific Ideas

- Confirmation prompt should feel like common Unix tools — show what will happen, then ask
- The `--yes` flag pattern follows apt, dnf, and similar tools

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-safe-defaults-refactor*
*Context gathered: 2026-01-19*
