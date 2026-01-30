# Phase 20: CLI Integration - Research

**Researched:** 2026-01-30
**Domain:** Python CLI argument parsing, TTY detection, mode routing
**Confidence:** HIGH

## Summary

Phase 20 wires the interactive mode (built in Phase 19) into the CLI with proper flag validation, TTY detection, and mode routing. The codebase already has:
- `interactive_execute()` function in `cli.py` that handles per-group prompting
- `confirm_execution()` function for single Y/N confirmation (legacy batch confirmation)
- `sys.stdin.isatty()` checks scattered throughout for non-interactive detection
- `parser.error()` calls for flag validation errors (exit code 2)

The primary work is consolidating mode routing logic, adding new flag conflict validations, and ensuring proper error messages match the existing error style.

**Primary recommendation:** Add flag validation early in main() using parser.error() for conflicts; route to either interactive_execute() or execute_all_actions() based on --yes flag presence; check TTY before finding matches (fail fast).

## Standard Stack

This phase uses only Python standard library - no new dependencies.

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| argparse | stdlib | CLI argument parsing | Already used, parser.error() for validation |
| sys | stdlib | stdin.isatty() for TTY detection | Already used in codebase |

### Already in Codebase
| Component | Location | Purpose |
|-----------|----------|---------|
| `interactive_execute()` | `cli.py:80-262` | Per-group interactive confirmation loop |
| `execute_all_actions()` | `actions.py` | Batch execution without prompts |
| `confirm_execution()` | `cli.py:29-37` | Single Y/N confirmation for batch mode |
| `parser.error()` | `cli.py:409-421` | Flag conflict validation |
| `TextActionFormatter` | `formatters.py` | Output formatting with color support |

## Architecture Patterns

### Pattern 1: Fail-Fast Flag Validation
**What:** Validate flag conflicts immediately after argument parsing, before any expensive operations
**When to use:** Flag conflicts that make execution impossible
**Example:**
```python
# Source: Existing pattern in cli.py:409-421
args = parser.parse_args()

# Validate flag conflicts before finding matches (expensive operation)
if args.json and args.execute and not args.yes:
    parser.error("--json with --execute requires --yes flag")
if args.quiet and args.execute and not args.yes:
    parser.error("--quiet with --execute requires --yes flag")
if args.execute and not args.yes and not sys.stdin.isatty():
    parser.error("stdin is not a terminal, use --yes to confirm")
```

### Pattern 2: Mode Routing
**What:** Single decision point that routes to interactive or batch execution
**When to use:** After all validation passes, before execution begins
**Example:**
```python
# Source: Based on CONTEXT.md decision for separate functions
if execute_mode:
    if args.yes:
        # Batch mode - use existing execute_all_actions()
        results = execute_all_actions(groups, action, ...)
    else:
        # Interactive mode - TTY already validated
        results = interactive_execute(groups, action, formatter, ...)
```

### Pattern 3: Banner Display Before Groups
**What:** Show informational banner with statistics before first group prompt
**When to use:** At start of both interactive and batch execution modes
**Example:**
```python
# Source: CONTEXT.md banner decision
def format_execute_banner(action: Action, groups: list, space_info: SpaceInfo) -> str:
    """Format banner: bold action, stats."""
    action_bold = bold(action.value, color_config)
    return f"{action_bold} mode: {space_info.group_count} groups, {space_info.duplicate_count} files, {format_file_size(space_info.bytes_saved)} to save"
```

### Recommended Code Organization
```
cli.py changes:
├── Flag validation block (near line 404)     # New validation cases
├── Mode routing decision (near line 607)     # Route to interactive vs batch
├── format_execute_banner() (new function)    # Banner formatting
└── Separator: 40-char dashed line            # Visual separation
```

### Anti-Patterns to Avoid
- **Validation scattered throughout:** All flag conflict checks should be in one place early in main()
- **TTY check at prompt time:** Check TTY once at startup, not when user interaction needed
- **Implicit --yes:** Do NOT implicitly add --yes for any flag combination (per CONTEXT.md decision)

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| TTY detection | Custom terminal detection | `sys.stdin.isatty()` | Standard Python, handles edge cases |
| Exit codes | Custom error exit logic | `parser.error()` | Consistent exit code 2, proper stderr format |
| File size formatting | String formatting | `format_file_size()` | Already exists in formatters.py |
| Color output | Manual ANSI codes | `bold()`, `ColorConfig` | Already exists in colors.py |

**Key insight:** The codebase already has all the building blocks - this phase is primarily about wiring them together correctly.

## Common Pitfalls

### Pitfall 1: Testing Non-TTY Before Expensive Operations
**What goes wrong:** Running find_matching_files() then discovering stdin isn't a TTY
**Why it happens:** Natural to validate at point of use (prompt time)
**How to avoid:** Check `sys.stdin.isatty()` immediately after parsing args, before find_matching_files()
**Warning signs:** Error messages appearing after "Processing..." output

### Pitfall 2: Error Message Format Inconsistency
**What goes wrong:** Custom error messages that don't match argparse style
**Why it happens:** Using print() instead of parser.error() for validation errors
**How to avoid:** Always use `parser.error()` for argument validation errors
**Warning signs:** Exit code 1 instead of 2, messages going to stdout instead of stderr

### Pitfall 3: Missing TTY Check for Quiet Mode
**What goes wrong:** `--quiet --execute` without `--yes` silently waits for input that can't be provided
**Why it happens:** Quiet mode suppresses prompts but doesn't disable them
**How to avoid:** Per CONTEXT.md, require explicit `--yes` when `--quiet --execute` is used
**Warning signs:** Program hangs in CI/CD pipelines

### Pitfall 4: Banner Before or After Groups?
**What goes wrong:** Showing banner after group output in interactive mode
**Why it happens:** Reusing preview mode flow which shows groups first
**How to avoid:** Banner and 40-dash separator must appear BEFORE first group prompt
**Warning signs:** User sees group before understanding context

### Pitfall 5: JSON Mode with Interactive
**What goes wrong:** Attempting to interleave JSON output with prompts
**Why it happens:** Not validating --json + --execute without --yes
**How to avoid:** parser.error() early if --json --execute without --yes
**Warning signs:** Malformed JSON output, prompts breaking JSON structure

## Code Examples

### TTY Detection (Already in Codebase)
```python
# Source: cli.py:33-36
if not sys.stdin.isatty():
    print("Non-interactive mode detected. Use --yes to skip confirmation.", file=sys.stderr)
    return False
```

### Flag Validation Pattern (Existing)
```python
# Source: cli.py:409-410
if args.json and args.execute and not args.yes:
    parser.error("--json with --execute requires --yes flag to confirm (no interactive prompts in JSON mode)")
```

### Error Message Format (Per CONTEXT.md)
```python
# Error format: "Error:" prefix, red text, name the problematic flag
# Source: CONTEXT.md decision
parser.error("--json and interactive mode are incompatible")  # Good
parser.error("Error: use --yes with --json --execute")        # Bad (suggests fix)
```

### Interactive Execute (Existing)
```python
# Source: cli.py:80-262
def interactive_execute(
    groups: list[DuplicateGroup],
    action: Action,
    formatter: ActionFormatter,
    ...
) -> tuple[int, int, int, int, list[FailedOperation], int, int]:
    """Execute with per-group interactive confirmation."""
```

### Banner Format (Per CONTEXT.md)
```python
# Banner example from CONTEXT.md:
# "**hardlink** mode: 15 groups, 47 files, 1.2 GB to save"
# Followed by 40-character dashed separator
def format_banner(action: str, group_count: int, file_count: int, space: int) -> str:
    space_str = format_file_size(space)
    return f"{bold(action)} mode: {group_count} groups, {file_count} files, {space_str} to save"

BANNER_SEPARATOR = "-" * 40
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single Y/N for all | Per-group y/n/a/q | Phase 19 | More granular control |
| --yes required for batch | --execute alone = interactive | Phase 20 | Better UX for interactive use |
| Implicit --yes for --quiet | Explicit --yes required | Phase 20 (CONTEXT.md) | Safer default behavior |

**Deprecated/outdated:**
- confirm_execution() for interactive mode: Still used for batch confirmation prompt, but interactive mode uses interactive_execute()

## Open Questions

All questions were resolved in CONTEXT.md:

1. **TTY detection method** - Claude's discretion (recommend stdin.isatty() only, matching existing pattern)
2. **Where routing decision lives** - Claude's discretion (recommend single block in main() after validation)
3. **Exact banner text** - Decided: "{bold action} mode: X groups, Y files, Z to save"
4. **JSON field for banner** - Claude's discretion (recommend "executionInfo" or similar)

## Sources

### Primary (HIGH confidence)
- `/Users/patrick/dev/cursor_projects/filematcher/filematcher/cli.py` - Existing implementation
- `/Users/patrick/dev/cursor_projects/filematcher/filematcher/formatters.py` - Formatter classes
- `/Users/patrick/dev/cursor_projects/filematcher/tests/test_interactive.py` - Phase 19 tests
- `/Users/patrick/dev/cursor_projects/filematcher/tests/test_safe_defaults.py` - Existing flag tests
- [Python argparse documentation](https://docs.python.org/3/library/argparse.html) - parser.error() exit code 2

### Secondary (MEDIUM confidence)
- [Python sys.stdin.isatty()](https://thelinuxcode.com/python-file-isatty-method/) - TTY detection patterns
- [Rosetta Code - Check input device is terminal](https://rosettacode.org/wiki/Check_input_device_is_a_terminal) - Cross-platform TTY detection

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Using only existing codebase components
- Architecture: HIGH - Patterns directly from CONTEXT.md and existing code
- Pitfalls: HIGH - Derived from codebase analysis and existing tests

**Research date:** 2026-01-30
**Valid until:** 60 days (stable domain, no external dependencies)

## Existing Code References

### Key Functions to Modify
1. `main()` in cli.py (line 364-725) - Add flag validation, mode routing
2. Possibly add `format_execute_banner()` helper

### Key Functions to Use (No Modification)
1. `interactive_execute()` - Already complete from Phase 19
2. `execute_all_actions()` - Existing batch execution
3. `parser.error()` - Existing validation pattern
4. `calculate_space_savings()` - For banner statistics

### Test Files to Extend
1. `test_safe_defaults.py` - Add tests for new flag combinations
2. `test_cli.py` - Integration tests for mode routing
3. `test_interactive.py` - May need edge case tests

### Existing Error Message Patterns
```python
# From cli.py - match this style:
parser.error("--json with --execute requires --yes flag to confirm (no interactive prompts in JSON mode)")
parser.error("compare action doesn't modify files - remove --execute flag")
parser.error("--log requires --execute")
parser.error("--fallback-symlink only applies to --action hardlink")
parser.error(f"--target-dir must be an existing directory: {args.target_dir}")
```
