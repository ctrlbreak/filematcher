# Phase 8: Color Enhancement - Context

**Gathered:** 2026-01-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Add TTY-aware ANSI color formatting to CLI output highlighting key information. Colors auto-enable on TTY, auto-disable when piped. NO_COLOR environment variable and --no-color flag disable colors. Text content remains identical with or without color (only ANSI codes added).

</domain>

<decisions>
## Implementation Decisions

### Color Palette
- **Masters (protected files):** Green — standard convention for safe/keep
- **Duplicates (removal candidates):** Yellow — warning/caution tone
- **Warnings and errors:** Red — attention needed
- **Statistics and summaries:** Cyan — informational, distinct from action colors

### TTY Detection Behavior
- Add `--color` flag to force colors on when piped (useful for `less -R` or colored logs)
- Add `--no-color` flag to explicitly disable colors
- `--color` with `--json`: silently ignore `--color` (JSON must never have ANSI codes)
- Per-stream TTY detection: each stream (stdout/stderr) colored independently based on its own TTY status
- Flag precedence: last one wins when both `--color` and `--no-color` specified (allows alias overrides)
- Respect `NO_COLOR` environment variable (standard compliance)

### Semantic Highlighting
- **File paths colored:** Master paths green, duplicate paths yellow — clearer at a glance
- **File sizes:** Plain, no color — informational, not actionable
- **PREVIEW MODE banner:** Yellow/bold — attention-grabbing safety warning
- **Hash values:** Dim/gray — de-emphasize technical details

### Claude's Discretion
- NO_COLOR compliance details and other environment variables like FORCE_COLOR
- Exact ANSI code implementation (16-color vs 256-color)
- Section headers and dividers formatting
- Action labels (hardlink, symlink, delete) formatting
- Bold vs regular intensity choices beyond banner

</decisions>

<specifics>
## Specific Ideas

- Convention-following color scheme: green=keep, yellow=caution, red=error, cyan=info
- Per-stream detection allows `filematcher dir1 dir2 2>/dev/null` to still have colored stdout
- Last-wins flag precedence is standard shell convention

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 08-color-enhancement*
*Context gathered: 2026-01-23*
