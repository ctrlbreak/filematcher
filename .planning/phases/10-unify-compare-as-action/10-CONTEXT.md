# Phase 10: Unify Compare as Action - Context

**Gathered:** 2026-01-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Refactor default compare mode into a "compare" action that reuses the action code path, eliminating duplicate code paths between compare and action modes. This unifies the formatter hierarchy and main() flow while maintaining backwards compatibility for users who run without flags.

</domain>

<decisions>
## Implementation Decisions

### CLI behavior
- Default mode (no --action) implicitly uses "compare" action - backwards compatible
- `--action compare` is a valid explicit option for scripting clarity
- `--execute` with compare action = error ("compare action doesn't modify files")
- `--yes` with compare action = silently ignored (no confirmation needed anyway)
- Action choices in --help ordered: `{compare,hardlink,symlink,delete}` with compare marked as default

### Code path unification
- CompareFormatter ABC and all implementations (Text, JSON) deleted entirely
- Single action branch in main() - all modes go through same action processing code
- Action type determines behavior within unified flow
- JsonCompareFormatter also removed - JSON output uses same formatter for all actions
- Clean removal: ABC, TextCompareFormatter, JsonCompareFormatter all gone

### Output format
- Text output can evolve (not byte-identical) - JSON exists for machine parsing
- Header shows "Action: none" for compare mode (explicitly indicates no modifications)
- Compare mode does NOT show PREVIEW/EXECUTING state (never modifies files)
- Statistics footer keeps current behavior: shows 0 space savings with hint about --action

### Internal action naming
- Internal action name is "compare" (`--action compare`)
- Displayed as "Action: none" in output header (not "Action: compare")
- Compare is the default action when no --action flag specified

### Claude's Discretion
- Exact refactoring sequence to maintain test compatibility during transition
- How to handle any edge cases in the unified action flow
- Internal variable naming for the unified action type

</decisions>

<specifics>
## Specific Ideas

- "Action: none" clearly communicates to users that compare mode doesn't modify files
- The unified code path should be a natural extension of the action mode pattern established in v1.1
- Error message for --execute with compare should be helpful: "compare action doesn't modify files"

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope

</deferred>

---

*Phase: 10-unify-compare-as-action*
*Context gathered: 2026-01-23*
