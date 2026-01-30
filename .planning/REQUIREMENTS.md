# Requirements: v1.5 Interactive Execute

## Milestone Goal

Redesign execute mode with per-file interactive confirmation that maintains consistency with preview mode output. Interactive prompts become the default behavior for `--execute`, with `--yes` as the opt-out for batch execution.

## v1.5 Requirements

### Interactive Confirmation (INT)

- [x] **INT-01**: Per-file prompts with y/n/a/q responses during execute mode
  - `y` = yes, execute action on this group
  - `n` = no, skip this group, continue to next
  - `a` = all, execute action on this and all remaining groups
  - `q` = quit, stop processing (no more actions)

- [x] **INT-02**: Progress indicator showing group position in each prompt
  - Format: `[3/10]` or similar prefix on prompt line
  - User knows how many prompts remain

- [x] **INT-03**: Case-insensitive response handling
  - Accept `y`, `Y`, `yes`, `YES` etc.
  - Accept `n`, `N`, `no`, `NO` etc.
  - Invalid input re-prompts with error message

- [x] **INT-04**: Non-TTY detection with clear error message
  - If stdin is not a TTY, print error to stderr and exit
  - Error message guides user to use `--yes` flag

- [x] **INT-05**: `--yes` flag bypasses all prompts (batch mode)
  - Current behavior preserved: `--execute --yes` = no prompts
  - `--execute` alone (without --yes) = per-file prompts (NEW)

### Output Flow (OUT)

- [x] **OUT-01**: Statistics shown BEFORE groups in interactive mode
  - Banner: "EXECUTE MODE"
  - Statistics upfront: X groups, Y files, Z space to reclaim
  - Then per-group prompting begins

- [x] **OUT-02**: Same group display format as preview mode
  - Reuse existing `format_duplicate_group()` method
  - MASTER and WILL labels match preview output

- [x] **OUT-03**: Prompt appears immediately after each group
  - Display group → prompt → response → status → next group
  - Not: display all → prompt batch → execute all

- [x] **OUT-04**: Confirmation status shown after response
  - Show `✓ Confirmed` or `✗ Skipped` after each decision
  - Visual feedback that input was received

### Error Handling (ERR)

- [ ] **ERR-01**: Permission/access errors skip file and continue
  - Log error to audit log
  - Show error inline (e.g., `✗ Permission denied: /path`)
  - Continue to next file/group

- [ ] **ERR-02**: Clean summary on cancellation (q response)
  - Show count of files already processed
  - Show count of files skipped
  - Exit cleanly (not an error)

- [ ] **ERR-03**: Execution Complete summary shows comprehensive counts
  - User decisions: N confirmed, M skipped
  - Execution results: X succeeded, Y failed
  - Space saved from successful actions
  - Audit log path

### Flag Interactions (FLAG)

- [x] **FLAG-01**: `--json` with `--execute` requires `--yes`
  - Error message: "JSON output requires --yes flag with --execute"
  - Interactive prompts incompatible with JSON output

- [x] **FLAG-02**: `--quiet` with `--execute` requires explicit `--yes`
  - Can't suppress output AND prompt for input
  - Error if --quiet --execute used without --yes

### Code Architecture (ARCH)

- [x] **ARCH-01**: Consistent flow between compare, preview, and execute modes
  - All modes use same formatter methods for group display
  - Statistics use same calculation functions
  - Only differences: banners, prompts, and action execution
  - Avoid duplicating display/formatting logic between modes

- [x] **ARCH-02**: Single code path for group formatting
  - Reuse `format_duplicate_group()` in all modes
  - No mode-specific formatting functions
  - Parameters control behavior (preview_mode, execute status), not separate methods

## Future Requirements (Deferred)

- Help command (?) showing available options
- Undo last action
- Group-level prompts ("process all files in this hash group?")
- Smart defaults based on file size
- Progress bars

## Out of Scope

- Undo/rollback functionality
- Interactive mode for JSON output
- Progress bars (TTY complexity)
- Carriage return prompt overwriting

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| INT-01 | Phase 19 | Complete |
| INT-02 | Phase 19 | Complete |
| INT-03 | Phase 19 | Complete |
| INT-04 | Phase 20 | Complete |
| INT-05 | Phase 20 | Complete |
| OUT-01 | Phase 20 | Complete |
| OUT-02 | Phase 18 | Complete |
| OUT-03 | Phase 19 | Complete |
| OUT-04 | Phase 18 | Complete |
| ERR-01 | Phase 21 | Pending |
| ERR-02 | Phase 21 | Pending |
| ERR-03 | Phase 21 | Pending |
| FLAG-01 | Phase 20 | Complete |
| FLAG-02 | Phase 20 | Complete |
| ARCH-01 | Phase 18 | Complete |
| ARCH-02 | Phase 18 | Complete |

---
*Requirements defined: 2026-01-28*
*Based on research: SUMMARY-v1.5.md*
*Phase assignments: 2026-01-29*
