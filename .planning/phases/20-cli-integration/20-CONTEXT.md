# Phase 20: CLI Integration - Context

**Gathered:** 2026-01-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Wire interactive mode into CLI with proper flag validation, TTY detection, and mode routing logic. Users running `--execute` without `--yes` enter interactive mode; flag conflicts and non-TTY scenarios produce clear errors.

</domain>

<decisions>
## Implementation Decisions

### Banner/Statistics Display
- Informative single-line banner with action type, total groups, total files, space to be saved
- Action type in **bold** for emphasis
- No key guide in banner (prompt already shows [y/n/a/q])
- Horizontal rule (40 dashes) separates banner from first group
- Banner shown in both interactive and batch modes
- JSON mode includes banner info as a JSON field

### Error Message Wording
- Full error messages in red text
- "Error:" prefix before message
- Focus on the conflict, not the resolution ("--json and interactive mode are incompatible")
- Name the problematic flag, not both flags
- Never suggest the fix in error messages
- Match existing stderr/stdout behavior for errors
- Match argparse default exit code for argument errors

### Flag Interaction Logic
- `--quiet --execute` requires explicit `--yes` (does NOT imply --yes)
- `--json --execute` without `--yes` is an error
- Non-TTY stdin without `--yes` is an error
- `--execute --yes` shows banner but runs batch mode

### Mode Routing
- Separate functions: `execute_interactive()` and `execute_batch()`
- Validation (TTY check, flag conflicts) happens before finding matches (fail fast)

### Claude's Discretion
- TTY detection method (stdin.isatty() or both stdin/stdout)
- Where in code the routing decision lives
- Exact banner text phrasing
- JSON field name/structure for banner info

</decisions>

<specifics>
## Specific Ideas

- Banner example: "**hardlink** mode: 15 groups, 47 files, 1.2 GB to save"
- 40-character dashed separator after banner

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 20-cli-integration*
*Context gathered: 2026-01-30*
