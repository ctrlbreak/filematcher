# Phase 5: Formatter Abstraction - Context

**Gathered:** 2026-01-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Create a unified output abstraction layer (OutputFormatter protocol with TextFormatter and JsonFormatter implementations) without changing any user-visible behavior. This is internal refactoring — the foundation for JSON output (Phase 6) and unified formatting (Phase 7) in later phases.

</domain>

<decisions>
## Implementation Decisions

### Protocol design
- Medium granularity for methods: format_group(), format_file(), format_banner(), format_statistics() — balanced between simplicity and flexibility
- Use ABC (Abstract Base Class) for the protocol, not typing.Protocol — explicit inheritance with runtime checks
- Separate protocols for compare mode and action mode: CompareFormatter and ActionFormatter
- Verbose mode handled via config parameter to formatter constructor, not separate methods

### Formatter lifecycle
- Formatters instantiated early in main(), passed to functions that need them
- Claude's Discretion: How output is collected (direct print vs return strings vs internal buffering)
- Claude's Discretion: Whether to pass formatter explicitly or bundle in context object
- Claude's Discretion: Error/warning formatting approach (formatter methods vs keep with logging)

### Backward compatibility
- No requirement for backward compatibility with older versions
- Going forward: refactoring should not change output — fix to match original if output diverges
- Claude's Discretion: Whether to add golden file tests based on current coverage assessment

### Claude's Discretion
- Output collection mechanism (print vs return vs buffer)
- Parameter passing pattern (explicit vs context object)
- Error/warning handling location
- Golden file test strategy

</decisions>

<specifics>
## Specific Ideas

- Separate CompareFormatter and ActionFormatter protocols reflects the distinct output structures between modes
- ABC chosen over Protocol for familiarity and explicit runtime checks

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 05-formatter-abstraction*
*Context gathered: 2026-01-22*
