# Phase 6: JSON Output - Context

**Gathered:** 2026-01-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Expose JSON output through CLI with `--json` flag. Users can pipe output to jq for scripting and automation. Works in both compare mode and action mode. Text output remains unchanged.

</domain>

<decisions>
## Implementation Decisions

### Schema Design
- Root structure: Object with sections (`matches`, `unmatchedDir1`, `unmatchedDir2`, `summary`)
- Comprehensive metadata at root: timestamp, directories compared, flags used, hash algorithm, file counts
- No schema version field needed — schema is simple enough for now

### Flag Interactions
- `--json --summary`: JSON output contains only summary section, no file lists
- `--json --action`: Full support — shows planned/executed actions in JSON format
- `--json --execute`: Include execution results (success/failure status, error messages per action)
- `--json --execute` requires `--yes` flag — no interactive prompts with JSON output

### Output Behavior
- Always pretty-printed (indented, human-readable)
- Errors: Both streams — errors go to stderr AND are noted in the JSON output
- Confirmation prompt requires `--yes` when using `--json --execute`

### jq Usability
- Field naming: camelCase (`filePath`, `isMaster`, `unmatchedDir1`)
- Paths: Absolute paths only — unambiguous, ready to use
- File sizes: Numeric bytes only — easy to filter/sort programmatically

### Claude's Discretion
- Per-file metadata fields (balance usefulness vs verbosity)
- `--json --verbose` behavior (whether verbose adds extra fields or is ignored)
- Progress message handling with `--json` (stderr vs suppressed)
- jq extraction pattern optimization (which use cases to prioritize)

</decisions>

<specifics>
## Specific Ideas

- Errors should be visible in both places: stderr for immediate visibility, and captured in JSON for programmatic handling
- `--json --execute` without `--yes` should error with clear message about requiring explicit confirmation

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 06-json-output*
*Context gathered: 2026-01-23*
