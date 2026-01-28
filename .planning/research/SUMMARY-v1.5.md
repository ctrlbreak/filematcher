# v1.5 Research Summary: Interactive Execute

**Project:** File Matcher v1.5 - Interactive Execute
**Domain:** CLI per-file interactive confirmation
**Researched:** 2026-01-28
**Confidence:** HIGH

## Executive Summary

Interactive per-file confirmation for File Matcher is a well-understood pattern with clear implementation paths. The key insight from research is that File Matcher already has all the infrastructure needed: `input()` with `sys.stdin.isatty()` for prompts (proven in `confirm_execution()`), the Strategy pattern formatters for consistent output, and comprehensive test mocking. The implementation requires extending existing code, not building new systems.

The recommended approach follows git add -p conventions: display each duplicate group using the existing `format_duplicate_group()` method, then immediately prompt with y/n/a/q options. This "display-prompt-decide" loop replaces the current "display all, prompt once, execute all" flow. The architecture research strongly recommends adding a new `execute_with_interactive_confirmation()` function in cli.py rather than trying to modify the existing execution path.

The primary risk is TTY complexity. A prior File Matcher attempt at interactive confirmation failed due to carriage return behavior issues. The mitigation is explicit: use append-only output (no overwriting prompts), skip TTY progress displays during interactive mode, and fail fast with clear errors in non-TTY environments. The existing `--yes` flag continues to work unchanged, bypassing all prompts.

## Key Findings

### Recommended Stack

Pure Python standard library with `input()` and `sys.stdin.isatty()`. No external dependencies needed.

**Core technologies:**
- `input()` builtin: User prompts and response capture - already proven in `confirm_execution()`
- `sys.stdin.isatty()`: TTY detection - prevents hanging in pipelines, already used in codebase
- `unittest.mock.patch`: Test mocking - extensive existing test coverage uses this pattern

The existing `confirm_execution()` function handles TTY detection and `input()` correctly. The new interactive mode extends this pattern with y/n/a/q responses instead of simple y/n.

### Expected Features

**Must have (table stakes):**
- Case-insensitive single-letter responses (y/Y both accepted)
- Progress indicator showing "X of Y" for each prompt
- Cancel entire operation option (q/c)
- Default to safe behavior (Enter = skip file)
- Non-interactive detection (fail fast with helpful message)
- `--yes` flag bypass (existing behavior maintained)

**Should have (differentiators):**
- Help command (?) showing available options
- Display context immediately before each prompt (MASTER / WILL DELETE lines)
- Error handling that continues (skip failed file, log error, continue)
- Inline cross-filesystem warnings before fallback-symlink prompt

**Defer (v2+):**
- Undo last action (complex state management)
- Group-level "process all files in this hash group" prompts
- Smart defaults based on file size
- ETA display

### Architecture Approach

Interactive confirmation requires a new execution path that interleaves display and prompting. The key change is shifting from "display all -> prompt once -> execute all" to "for each group: display -> prompt -> track decision". After prompting completes, confirmed groups are passed to the existing `execute_with_logging()` function.

**Major components:**
1. **cli.py: `execute_with_interactive_confirmation()`** - New function for per-group prompt loop, parallel to existing execute path
2. **formatters.py: New methods** - `format_group_prompt()`, `format_confirmation_status()`, `format_interactive_header()` added to ActionFormatter ABC
3. **actions.py: Unchanged** - Already accepts partial group lists, no awareness of how groups were confirmed

**Critical constraint:** Keep prompting logic in cli.py (control flow), formatting logic in formatters.py (presentation). Do NOT add `prompt_user()` to formatters - that violates separation of concerns.

### Critical Pitfalls

1. **TTY carriage return complexity** - Do NOT attempt to overwrite prompts with \r. Use append-only output. This was the exact failure mode of the prior attempt.

2. **Output flow disconnection** - Do NOT show all groups then prompt separately. Users can't map prompts back to files. Integrate prompts inline immediately after each group display.

3. **Stdin detection failures** - Check `sys.stdin.isatty()` and fail fast with clear message if non-interactive. Don't hang waiting for input in CI/CD.

4. **Prompt/JSON conflict** - Interactive prompts are incompatible with `--json` output. Validate at CLI parsing: `--json --execute` requires `--yes`, otherwise error.

5. **Inconsistent group display** - Reuse `format_duplicate_group()` in both preview and interactive modes. Same formatter, same parameters. The only difference should be prompt appearing after each group.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Formatter Extensions
**Rationale:** Foundation must exist before CLI integration. Small, testable changes.
**Delivers:** Three new methods on ActionFormatter ABC with Text and JSON implementations
**Addresses:** Table stakes features (prompt text, progress indicator, confirmation feedback)
**Avoids:** Pitfall 5 (inconsistent display) - uses existing formatter infrastructure
**Estimate:** 1-2 hours

### Phase 2: Interactive Execution Function
**Rationale:** Core logic depends on formatter methods. Largest chunk of work.
**Delivers:** `execute_with_interactive_confirmation()` function with full prompt loop
**Uses:** New formatter methods, existing `execute_with_logging()` for confirmed groups
**Implements:** Per-group display-prompt-decide loop, y/n/a/q handling
**Avoids:** Pitfall 1 (TTY complexity) - append-only output; Pitfall 2 (flow disconnect) - inline prompts
**Estimate:** 2-3 hours

### Phase 3: CLI Integration
**Rationale:** Flag wiring depends on execution function existing. Includes validation.
**Delivers:** `--interactive` flag, routing logic, flag combination validation
**Addresses:** Table stakes (non-interactive detection, --yes interaction)
**Avoids:** Pitfall 3 (stdin detection), Pitfall 4 (JSON conflict), Pitfall 12 (quiet conflict)
**Estimate:** 1 hour

### Phase 4: Testing and Polish
**Rationale:** Integration tests need complete feature. Documentation after behavior finalized.
**Delivers:** Comprehensive test coverage, updated help text, error message refinement
**Estimate:** 1 hour

**Total estimate:** 5-7 hours

### Phase Ordering Rationale

- Formatter extensions first because they have no dependencies and are easily unit-tested in isolation
- Execution function second because it's the core complexity and needs formatter methods
- CLI integration third because it wires together everything else and validates flag combinations
- Testing/polish last because it validates the complete system

### Research Flags

Phases with standard patterns (skip additional research):
- **All phases:** Implementation is straightforward extension of existing patterns. No novel technical challenges. Research is complete.

No phases need deeper research during planning. The patterns are well-established (git add -p, rm -i) and File Matcher already has all infrastructure components.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Pure stdlib, proven in existing codebase, no new dependencies |
| Features | HIGH | Well-documented Unix conventions, clear user expectations |
| Architecture | HIGH | Direct codebase analysis, clear component boundaries |
| Pitfalls | HIGH | Prior failure documented, industry patterns studied |

**Overall confidence:** HIGH

### Gaps to Address

- **Ctrl+C handling during prompts:** Research mentions handling gracefully but doesn't specify exact behavior. Recommend: catch KeyboardInterrupt, treat as cancel, show clean summary.

- **Repeated invalid input:** Features doc suggests "after 3 attempts, treat as cancel" but this may be too aggressive. Recommend: re-prompt indefinitely until valid response (matches git behavior).

- **Verbose flag in interactive mode:** Research says suppress progress but enhance prompt detail. Need to define exactly what "enhanced detail" means (probably: show hashes, show file sizes).

## Sources

### Primary (HIGH confidence)
- Python 3.14 sys.stdin documentation - TTY detection patterns
- Python 3.14 curses documentation - Confirmed curses is overkill
- Git Interactive Staging documentation - y/n/a/q pattern
- File Matcher codebase - Existing formatter and cli infrastructure

### Secondary (MEDIUM confidence)
- CLI Guidelines (clig.dev) - Interactivity best practices
- Git add --patch community guides - User interaction patterns
- Nielsen Norman Group confirmation dialog research - Prompt clarity
- tty-prompt issue #137 - Carriage return TTY issues

### Tertiary (LOW confidence)
- ETA display patterns - Deferred, not researched deeply

---
*Research completed: 2026-01-28*
*Ready for roadmap: yes*
