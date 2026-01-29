# Roadmap: File Matcher v1.5 Interactive Execute

## Milestones

- v1.1 Deduplication - Phases 1-4 (shipped 2026-01-20)
- v1.3 Code Unification - Phases 5-10 (shipped 2026-01-23)
- v1.4 Package Structure - Phases 11-17 (shipped 2026-01-28)
- **v1.5 Interactive Execute** - Phases 18-21 (in progress)

## Overview

Transform execute mode from batch-only to interactive-by-default with per-file y/n/a/q confirmation. This milestone extends the existing formatter architecture with new prompt methods, builds the interactive execution loop, integrates flag validation into CLI, and ensures robust error handling with comprehensive summaries.

## Phases

- [ ] **Phase 18: Formatter Extensions** - Add prompt formatting methods to ActionFormatter ABC
- [ ] **Phase 19: Interactive Core** - Build per-group prompt loop with y/n/a/q handling
- [ ] **Phase 20: CLI Integration** - Wire flags, TTY validation, and routing logic
- [ ] **Phase 21: Error Handling & Polish** - Error recovery, cancellation, and final summary

## Phase Details

### Phase 18: Formatter Extensions

**Goal**: Establish formatter foundation for interactive prompts using existing Strategy pattern
**Depends on**: Phase 17
**Requirements**: OUT-02, OUT-04, ARCH-01, ARCH-02
**Success Criteria** (what must be TRUE):
  1. `format_duplicate_group()` is used consistently in preview, execute, and interactive modes
  2. New `format_group_prompt()` method outputs progress indicator and prompt text
  3. New `format_confirmation_status()` method outputs checkmark/x after user decision
  4. TextActionFormatter and JsonActionFormatter both implement new methods
  5. No mode-specific formatting functions exist outside formatters.py
**Plans**: TBD

### Phase 19: Interactive Core

**Goal**: Implement per-group display-prompt-decide loop in cli.py
**Depends on**: Phase 18
**Requirements**: INT-01, INT-02, INT-03, OUT-03
**Success Criteria** (what must be TRUE):
  1. User sees group display followed immediately by prompt (no batch display)
  2. Prompt shows position indicator like `[3/10]`
  3. Responses y/n/a/q work case-insensitively (Y, yes, YES all valid)
  4. Invalid input re-prompts with error message
  5. `a` response confirms current and all remaining groups without further prompts
  6. `q` response stops prompting immediately
**Plans**: TBD

### Phase 20: CLI Integration

**Goal**: Wire interactive mode into CLI with proper flag validation
**Depends on**: Phase 19
**Requirements**: INT-04, INT-05, FLAG-01, FLAG-02, OUT-01
**Success Criteria** (what must be TRUE):
  1. `--execute` without `--yes` enters interactive mode (prompts for each group)
  2. `--execute --yes` runs batch mode without prompts (existing behavior)
  3. Non-TTY stdin with `--execute` (no `--yes`) errors with message directing to `--yes`
  4. `--json --execute` without `--yes` errors with clear message
  5. `--quiet --execute` implies `--yes` (runs batch mode)
  6. Interactive mode shows banner and statistics before first prompt
**Plans**: TBD

### Phase 21: Error Handling & Polish

**Goal**: Ensure robust error recovery and comprehensive feedback
**Depends on**: Phase 20
**Requirements**: ERR-01, ERR-02, ERR-03
**Success Criteria** (what must be TRUE):
  1. Permission/access errors on individual files are logged and skipped (execution continues)
  2. User sees inline error message for failed files
  3. `q` response shows clean summary (files processed, files skipped) and exits cleanly
  4. Final summary shows user decisions (confirmed/skipped), execution results (success/failed), space saved, and audit log path
  5. All tests pass and edge cases covered
**Plans**: TBD

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 18. Formatter Extensions | v1.5 | 0/TBD | Not started | - |
| 19. Interactive Core | v1.5 | 0/TBD | Not started | - |
| 20. CLI Integration | v1.5 | 0/TBD | Not started | - |
| 21. Error Handling & Polish | v1.5 | 0/TBD | Not started | - |

---

## Coverage Validation

All 16 v1 requirements mapped:

| Requirement | Phase | Description |
|-------------|-------|-------------|
| INT-01 | 19 | Per-file prompts with y/n/a/q responses |
| INT-02 | 19 | Progress indicator in prompts |
| INT-03 | 19 | Case-insensitive response handling |
| INT-04 | 20 | Non-TTY detection with error message |
| INT-05 | 20 | --yes flag bypasses prompts |
| OUT-01 | 20 | Statistics shown before groups |
| OUT-02 | 18 | Same group display format as preview |
| OUT-03 | 19 | Prompt appears immediately after group |
| OUT-04 | 18 | Confirmation status after response |
| ERR-01 | 21 | Permission errors skip and continue |
| ERR-02 | 21 | Clean summary on cancellation |
| ERR-03 | 21 | Comprehensive execution summary |
| FLAG-01 | 20 | --json --execute requires --yes |
| FLAG-02 | 20 | --quiet --execute implies --yes |
| ARCH-01 | 18 | Consistent flow between modes |
| ARCH-02 | 18 | Single code path for group formatting |

**Coverage: 16/16 requirements mapped**

---
*Roadmap created: 2026-01-29*
*Phases continue from v1.4 (ended at Phase 17)*
