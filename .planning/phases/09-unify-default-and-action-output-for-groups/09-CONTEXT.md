# Phase 9: Unify Default and Action Output for Groups - Context

**Gathered:** 2026-01-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Unify how duplicate file groups are displayed between compare mode (default) and action mode (--action). Both modes should use the same [MASTER]/[DUPLICATE] hierarchical format and share a single code path.

</domain>

<decisions>
## Implementation Decisions

### Label Format
- Always use `[MASTER]` and `[DUPLICATE]` labels in both modes
- When `--action` is specified, duplicates show action type: `[WOULD HARDLINK]`, `[WOULD DELETE]`, etc.
- In compare mode (no --action), duplicates show `[DUPLICATE]`

### Primary File Selection
- Use existing logic that picks the oldest file (by mtime) as master
- Only ONE master per group — additional dir1 files with same hash are duplicates too
- First file listed (the master) is unindented, all others indented

### Hash Display
- Hash is NOT shown by default (removed from default output)
- Hash shown only with `--verbose` flag
- When shown: full hash, de-emphasized (dim/gray), trailing line after files
- Hash behavior is the same for both compare mode AND action mode

### Color Semantics
- Green for `[MASTER]` label
- Yellow for `[DUPLICATE]` / `[WOULD X]` labels
- Dim/gray for hash line (when shown with --verbose)

### Code Consolidation
- Merge into single unified formatter — one code path for both modes
- Enhance `format_duplicate_group()` function to handle both compare and action modes
- Merge separate ABCs (CompareFormatter, ActionFormatter) into single `OutputFormatter` ABC
- Result: One ABC, one TextFormatter, one JsonFormatter

### Claude's Discretion
- Exact function signatures for unified formatter
- How to handle edge cases in formatter consolidation
- Test organization after merging formatters

</decisions>

<specifics>
## Specific Ideas

- Output should look the same between modes except for the action labels
- The master selection logic (oldest file) already exists — respect it
- This is a breaking change for text output parsing, but JSON provides stable interface

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 09-unify-default-and-action-output-for-groups*
*Context gathered: 2026-01-23*
