
## Phase 7 Gap: Formatter Abstraction Edge Cases

**Added:** 2026-01-23
**Source:** Phase 7 verification (07-VERIFICATION.md)
**Priority:** Low (technical debt, not user-facing)

Route 6 edge case print() calls through formatter abstraction:

- [ ] Line 1939: "No duplicates found." → add `format_empty_result()` method
- [ ] Line 2083: "Aborted. No changes made." → add `format_user_abort()` method  
- [ ] Line 2186: "No matching files found." → use `format_empty_result()`
- [ ] Lines 2073, 2076: Blank line, execute banner → route through formatter
- [ ] Lines 2179-2180, 2196-2197: Unmatched section headers → route through `format_unmatched()`

**Why:** Phase 8 (color enhancement) will need to modify these separately from formatters. Routing through formatters enables consistent color/formatting control.

**Fix with:** `/gsd:quick` when ready
