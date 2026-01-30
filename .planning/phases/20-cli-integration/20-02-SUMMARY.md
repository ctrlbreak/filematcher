---
phase: 20
plan: 02
subsystem: cli
tags: [interactive, batch, mode-routing, banner]

dependency_graph:
  requires:
    - "Phase 19: Interactive core (interactive_execute, prompt_for_group)"
    - "Phase 20-01: Flag validation and format_execute_banner"
  provides:
    - "Mode routing between interactive and batch execution"
    - "Banner display for both execute modes"
  affects:
    - "Phase 21: Documentation updates"

tech_stack:
  added: []
  patterns:
    - "Mode routing based on --yes flag presence"
    - "Banner display before execution in both modes"

key_files:
  created: []
  modified:
    - "filematcher/cli.py"
    - "tests/test_safe_defaults.py"

decisions:
  - topic: "Banner display"
    choice: "Same banner format for interactive and batch modes"
    rationale: "Consistent UX regardless of confirmation method"
  - topic: "Existing test updates"
    choice: "Updated TestExecuteMode tests for new prompt format"
    rationale: "Tests expected old [y/N] format, now uses [y/n/a/q]"

metrics:
  duration: "5 minutes"
  completed: "2026-01-30"
---

# Phase 20 Plan 02: Mode Routing Summary

Mode routing wires interactive_execute() into CLI when --execute used without --yes, preserves batch execution with --yes.

## Performance

- **Duration:** 5 min
- **Started:** 2026-01-30T10:56:29Z
- **Completed:** 2026-01-30T11:01:00Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments

- Wired interactive_execute() into CLI for per-group prompting
- Banner displays for both interactive and batch execute modes
- 6 new integration tests for mode routing behavior
- All 284 tests pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Add mode routing** - `9612843` (feat)
2. **Task 2: Add integration tests** - `f770508` (test)
3. **Task 3: Verify full suite** - verification only (no commit)

## Files Created/Modified

- `filematcher/cli.py` - Added mode routing in execute_mode block, import format_execute_banner
- `tests/test_safe_defaults.py` - Added TestModeRouting class, updated TestExecuteMode tests

## Changes Made

### Task 1: Mode Routing (cli.py)

Modified the `execute_mode` block to:

1. **Display banner for both modes:**
   ```python
   banner, separator = format_execute_banner(
       args.action.value,
       space_info.group_count,
       space_info.duplicate_count,
       space_info.bytes_saved,
       color_config
   )
   ```

2. **Route based on --yes flag:**
   - `if args.yes:` - Batch mode via execute_with_logging()
   - `else:` - Interactive mode via interactive_execute()

3. **Interactive mode setup:**
   - Build file_hash_lookup and file_sizes_map
   - Create audit logger
   - Call interactive_execute() with all parameters
   - Display execution summary

### Task 2: Integration Tests (test_safe_defaults.py)

Added `TestModeRouting` class with 6 tests:
- `test_execute_without_yes_prompts_interactively`
- `test_execute_with_yes_no_prompts`
- `test_execute_shows_banner_before_prompts`
- `test_execute_batch_shows_banner`
- `test_execute_interactive_q_exits_cleanly`
- `test_execute_interactive_a_confirms_all`

Updated `TestExecuteMode` to match new interactive prompt format:
- Changed `test_execute_shows_will_labels_then_banner` to `test_execute_shows_will_labels_and_banner`
- Changed `test_execute_abort_shows_message` to `test_execute_skip_shows_summary`
- Updated `test_execute_prompts_for_confirmation` to expect `[y/n/a/q]`

### Task 3: Full Verification

- 284 tests pass (278 + 6 new)
- Banner format verified: "{action} mode: X groups, Y files, Z to save"
- 40-character separator verified

## Decisions Made

1. **Unified banner display:** Same banner appears in both interactive and batch modes
2. **Test updates:** Updated 3 existing tests to match new interactive prompt format - this is expected behavior change, not a deviation

## Deviations from Plan

None - plan executed exactly as written.

## Verification

```bash
# Interactive mode (prompts with [y/n/a/q])
echo "n" | python3 -m filematcher dir1 dir2 --action delete --execute
# (requires TTY mock in tests)

# Batch mode (no prompts)
python3 -m filematcher dir1 dir2 --action hardlink --execute --yes

# Banner format verified:
# "hardlink mode: 1 groups, 3 files, 69 B to save"
# "----------------------------------------"
```

## Next Phase Readiness

Phase 20 CLI Integration complete. All requirements met:
- `--execute` without `--yes` enters interactive mode with per-group [y/n/a/q] prompts
- `--execute --yes` runs batch mode without prompts
- Banner appears before first prompt/execution
- Exit codes preserved (0 success, 1 error, 2 partial)

Ready for Phase 21 (documentation and release).

---
*Phase: 20-cli-integration*
*Completed: 2026-01-30*
