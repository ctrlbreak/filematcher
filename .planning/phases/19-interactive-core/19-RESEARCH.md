# Phase 19: Interactive Core - Research

**Researched:** 2026-01-29
**Domain:** Python CLI interactive prompt loop for per-group y/n/a/q confirmation
**Confidence:** HIGH

## Summary

This phase implements the core interactive confirmation loop in cli.py. The loop displays each duplicate group, prompts the user with y/n/a/q options, handles user response (case-insensitive), shows a position indicator [3/10], and re-prompts on invalid input. This builds on Phase 18's formatter methods (`format_group_prompt()`, `format_confirmation_status()`, `format_remaining_count()`).

The research confirms that Python's built-in `input()` function is the correct choice for interactive prompts. It automatically strips the trailing newline, integrates with readline for editing, and handles TTY operations correctly. The interactive loop follows the established pattern from `git add -p`: display item, show prompt with options, process response, give feedback, repeat. No external libraries are needed.

**Primary recommendation:** Use Python's built-in `input()` with a while loop for re-prompting on invalid input. Use `.casefold()` for case-insensitive comparison. Handle `KeyboardInterrupt` and `EOFError` exceptions for clean cancellation.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `builtins.input` | stdlib | Read user input with prompt | Built-in, strips newline, supports readline |
| `sys.stdin` | stdlib | TTY detection (already in codebase) | `isatty()` check for interactive mode |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `filematcher.formatters` | internal | `format_group_prompt()`, `format_confirmation_status()` | All prompt formatting (from Phase 18) |
| `filematcher.actions` | internal | `execute_action()` | Execute individual file actions |
| `filematcher.colors` | internal | Color helpers | Already used by formatters |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `input()` | `sys.stdin.readline()` | readline includes trailing newline, requires `.strip()`; input() is simpler |
| `input()` | `questionary`/`typer`/`rich` | External dependencies; overkill for simple y/n/a/q |
| `.casefold()` | `.lower()` | casefold is more aggressive for Unicode; safer for internationalization |

**Installation:**
```bash
# No installation needed - all stdlib and internal modules
```

## Architecture Patterns

### Recommended Project Structure
```
filematcher/
  cli.py
    |-- main()
    |     +-- calls interactive_execute() when --execute without --yes
    |
    +-- interactive_execute()           # NEW: main entry point
          +-- prompt_for_group()        # NEW: single group prompt loop
          +-- parse_response()          # NEW: validate and normalize input
```

### Pattern 1: Display-Prompt-Decide Loop

**What:** Process groups one at a time with user confirmation after each display
**When to use:** Interactive mode (`--execute` without `--yes`, stdin is TTY)
**Example:**
```python
# Source: git add -p pattern (https://git-scm.com/docs/git-add)

def interactive_execute(
    formatter: ActionFormatter,
    groups: list[DuplicateGroup],
    action: Action,
    # ... other params
) -> tuple[int, int, int, int, list[FailedOperation]]:
    """Interactive execution with per-group confirmation."""
    confirmed_groups = []
    skipped_groups = []
    confirm_all = False

    for i, group in enumerate(groups, start=1):
        # 1. Display the group
        formatter.format_duplicate_group(
            group.master_file, group.duplicates,
            action=action.value, group_index=i, total_groups=len(groups)
        )

        # 2. Auto-confirm if user chose "all"
        if confirm_all:
            formatter.format_confirmation_status(confirmed=True)
            confirmed_groups.append(group)
            continue

        # 3. Prompt and get decision
        response = prompt_for_group(formatter, i, len(groups), action.value)

        if response == 'y':
            formatter.format_confirmation_status(confirmed=True)
            confirmed_groups.append(group)
        elif response == 'n':
            formatter.format_confirmation_status(confirmed=False)
            skipped_groups.append(group)
        elif response == 'a':
            formatter.format_confirmation_status(confirmed=True)
            remaining = len(groups) - i
            formatter.format_remaining_count(remaining)
            confirmed_groups.append(group)
            confirm_all = True
        elif response == 'q':
            # Stop immediately, don't process more groups
            break

    # 4. Execute confirmed groups
    return execute_confirmed_groups(confirmed_groups, action, ...)
```

### Pattern 2: Prompt Loop with Re-prompt on Invalid Input

**What:** Keep prompting until valid response received
**When to use:** When user enters invalid input (not y/n/a/q)
**Example:**
```python
# Source: Python best practices (https://stackabuse.com/bytes/handling-yes-no-user-input-in-python/)

VALID_RESPONSES = {'y', 'n', 'a', 'q', 'yes', 'no', 'all', 'quit'}

def prompt_for_group(
    formatter: ActionFormatter,
    group_index: int,
    total_groups: int,
    action: str
) -> str:
    """Prompt user for group decision, re-prompt on invalid input.

    Returns normalized single-char response: 'y', 'n', 'a', or 'q'.
    Raises KeyboardInterrupt or EOFError on user cancellation.
    """
    while True:
        prompt_text = formatter.format_group_prompt(group_index, total_groups, action)
        try:
            response = input(prompt_text).strip().casefold()
        except (KeyboardInterrupt, EOFError):
            # Re-raise for caller to handle gracefully
            raise

        normalized = parse_response(response)
        if normalized:
            return normalized

        # Invalid input - show error and re-prompt
        print("Invalid response. Please enter y (yes), n (no), a (all), or q (quit).")
```

### Pattern 3: Response Normalization

**What:** Normalize various input formats to single-char responses
**When to use:** Case-insensitive handling, accepting "yes"/"no"/"all"/"quit"
**Example:**
```python
# Source: Best practice for case-insensitive comparison
# (https://dev.to/bowmanjd/case-insensitive-string-comparison-in-python-using-casefold-not-lower-5fpi)

def parse_response(response: str) -> str | None:
    """Parse user response to normalized single-char or None if invalid.

    Accepts: y, yes, n, no, a, all, q, quit (case-insensitive)
    Returns: 'y', 'n', 'a', 'q', or None
    """
    response = response.casefold()

    if response in ('y', 'yes'):
        return 'y'
    elif response in ('n', 'no'):
        return 'n'
    elif response in ('a', 'all'):
        return 'a'
    elif response in ('q', 'quit'):
        return 'q'
    else:
        return None
```

### Pattern 4: Exception Handling for Clean Exit

**What:** Handle Ctrl+C and EOF gracefully
**When to use:** Wrap the main prompt loop
**Example:**
```python
# Source: Python exception handling (https://python.swaroopch.com/exceptions.html)

def interactive_execute(...) -> tuple[int, int, int, int, list[FailedOperation]]:
    """Interactive execution with graceful cancellation handling."""
    try:
        # ... main loop ...
    except KeyboardInterrupt:
        print()  # Newline after ^C
        print("Cancelled by user.")
        # Return summary of what was processed so far
        return (success, failure, skipped, space, failed_list)
    except EOFError:
        print()
        print("End of input.")
        return (success, failure, skipped, space, failed_list)
```

### Anti-Patterns to Avoid

- **Calling `input()` in formatter:** Formatters format output; CLI handles input. Keep separation of concerns.
- **Using `sys.stdin.readline()` directly:** Use `input()` which handles the prompt display and newline stripping automatically.
- **Using `.lower()` instead of `.casefold()`:** casefold handles edge cases like German eszett better.
- **Infinite loop without exit:** Always allow `q` to quit and handle exceptions.
- **Modifying group list during iteration:** Build a separate confirmed_groups list.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Prompt text with progress | Custom string formatting | `formatter.format_group_prompt()` | Consistent with formatter pattern (Phase 18) |
| Confirmation feedback | Direct `print()` calls | `formatter.format_confirmation_status()` | Respects color config, consistent output |
| Remaining count message | Ad-hoc print | `formatter.format_remaining_count()` | Consistent formatting |
| Case-insensitive comparison | Manual ASCII checks | `.casefold()` | Unicode-aware, built-in |
| TTY detection | Custom file descriptor checks | `sys.stdin.isatty()` | Standard, well-tested |

**Key insight:** Phase 18 provides all the formatting methods. Phase 19 focuses purely on the control flow logic: prompt, read, validate, decide, repeat.

## Common Pitfalls

### Pitfall 1: Not Handling Empty Input

**What goes wrong:** User presses Enter without typing anything, causes index error
**Why it happens:** Checking `response[0]` on empty string
**How to avoid:** Use `.strip()` first, then check if empty before indexing
**Warning signs:** `IndexError` on empty input
```python
# BAD
if response[0] in ('y', 'n'):  # IndexError if empty

# GOOD
response = response.strip()
if not response:
    continue  # Re-prompt
if response[0] in ('y', 'n'):
    ...
```

### Pitfall 2: Forgetting to Strip Input

**What goes wrong:** Comparison fails due to trailing whitespace/newline
**Why it happens:** `input()` strips newline but user may add spaces
**How to avoid:** Always `.strip()` before comparison
**Warning signs:** Valid-looking input not recognized

### Pitfall 3: Not Catching Exceptions

**What goes wrong:** Ctrl+C or Ctrl+D crashes with traceback
**Why it happens:** `input()` raises `KeyboardInterrupt` or `EOFError`
**How to avoid:** Wrap prompt loop in try/except
**Warning signs:** Ugly traceback on user cancellation
```python
# BAD
response = input(prompt)  # Crashes on Ctrl+C

# GOOD
try:
    response = input(prompt)
except (KeyboardInterrupt, EOFError):
    print("\nCancelled.")
    return summary_results
```

### Pitfall 4: Displaying Group After Prompt (Wrong Order)

**What goes wrong:** User sees prompt before seeing what they're confirming
**Why it happens:** Logic puts prompt before display
**How to avoid:** Always display group THEN prompt
**Warning signs:** User asks "wait, what am I confirming?"
```
CORRECT ORDER:
1. Display duplicate group (master, duplicates)
2. Show prompt [3/10] Delete duplicate? [y/n/a/q]
3. Wait for input
4. Show confirmation status
```

### Pitfall 5: Not Tracking User Decisions Separately from Execution

**What goes wrong:** Can't report "confirmed: 5, skipped: 3" in summary
**Why it happens:** Executing immediately without tracking decisions
**How to avoid:** Track confirmed/skipped groups, then execute in batch
**Warning signs:** Summary only shows execution results, not user choices

### Pitfall 6: Prompt on Wrong Stream

**What goes wrong:** Prompt not visible or gets mixed with program output
**Why it happens:** Using stderr for prompt when stdout expected, or vice versa
**How to avoid:** `input()` automatically writes prompt to stdout, reads from stdin
**Warning signs:** Prompt appears in wrong place or not at all

## Code Examples

Verified patterns from official sources:

### Main Interactive Execute Function
```python
# Source: Follows git add -p pattern, Python input() docs

def interactive_execute(
    groups: list[DuplicateGroup],
    action: Action,
    formatter: ActionFormatter,
    fallback_symlink: bool = False,
    audit_logger: logging.Logger | None = None,
    file_hashes: dict[str, str] | None = None,
    target_dir: str | None = None,
    dir2_base: str | None = None,
) -> tuple[int, int, int, int, list[FailedOperation], int, int]:
    """Execute with per-group interactive confirmation.

    Returns: (success, failure, skipped, space_saved, failed_list, confirmed_count, user_skipped_count)
    """
    confirmed_groups: list[DuplicateGroup] = []
    user_skipped_count = 0
    confirm_all = False
    quit_requested = False

    try:
        for i, group in enumerate(groups, start=1):
            # Display the group
            formatter.format_duplicate_group(
                group.master_file,
                group.duplicates,
                action=action.value,
                group_index=i,
                total_groups=len(groups)
            )

            if confirm_all:
                formatter.format_confirmation_status(confirmed=True)
                confirmed_groups.append(group)
                continue

            # Prompt for decision
            response = prompt_for_group(formatter, i, len(groups), action.value)

            if response == 'y':
                formatter.format_confirmation_status(confirmed=True)
                confirmed_groups.append(group)
            elif response == 'n':
                formatter.format_confirmation_status(confirmed=False)
                user_skipped_count += 1
            elif response == 'a':
                formatter.format_confirmation_status(confirmed=True)
                remaining = len(groups) - i
                if remaining > 0:
                    formatter.format_remaining_count(remaining)
                confirmed_groups.append(group)
                confirm_all = True
            elif response == 'q':
                quit_requested = True
                break

    except (KeyboardInterrupt, EOFError):
        print()  # Newline after ^C
        quit_requested = True

    # Execute confirmed groups
    if confirmed_groups:
        success, failure, skipped, space, failed_list = execute_all_actions(
            confirmed_groups, action,
            fallback_symlink=fallback_symlink,
            audit_logger=audit_logger,
            file_hashes=file_hashes,
            target_dir=target_dir,
            dir2_base=dir2_base
        )
    else:
        success, failure, skipped, space, failed_list = 0, 0, 0, 0, []

    return (success, failure, skipped, space, failed_list,
            len(confirmed_groups), user_skipped_count)
```

### Prompt Loop Function
```python
# Source: Python input() docs, Stack Abuse best practices

VALID_RESPONSES = frozenset({'y', 'yes', 'n', 'no', 'a', 'all', 'q', 'quit'})

def prompt_for_group(
    formatter: ActionFormatter,
    group_index: int,
    total_groups: int,
    action: str
) -> str:
    """Prompt user and return normalized response.

    Returns: 'y', 'n', 'a', or 'q'
    Raises: KeyboardInterrupt, EOFError (for caller to handle)
    """
    while True:
        prompt_text = formatter.format_group_prompt(group_index, total_groups, action)
        response = input(prompt_text).strip().casefold()

        normalized = _normalize_response(response)
        if normalized is not None:
            return normalized

        print("Invalid response. Please enter y (yes), n (no), a (all), or q (quit).")


def _normalize_response(response: str) -> str | None:
    """Normalize response to single char or None if invalid."""
    if response in ('y', 'yes'):
        return 'y'
    elif response in ('n', 'no'):
        return 'n'
    elif response in ('a', 'all'):
        return 'a'
    elif response in ('q', 'quit'):
        return 'q'
    return None
```

### Test Pattern for Interactive Loop
```python
# Source: Existing test patterns in test_safe_defaults.py

def test_interactive_yes_confirms_group(self):
    """User typing 'y' confirms the group for execution."""
    with patch('sys.argv', ['filematcher', self.test_dir1, self.test_dir2,
                            '--action', 'hardlink', '--execute']):
        with patch('sys.stdin.isatty', return_value=True):
            with patch('builtins.input', return_value='y'):
                output = self.run_main_with_args([])
                # Should execute, not abort
                self.assertIn("Execution complete:", output)

def test_interactive_all_confirms_remaining(self):
    """User typing 'a' confirms current and all remaining groups."""
    responses = iter(['n', 'a'])  # Skip first, then all
    with patch('sys.argv', ['filematcher', self.test_dir1, self.test_dir2,
                            '--action', 'hardlink', '--execute']):
        with patch('sys.stdin.isatty', return_value=True):
            with patch('builtins.input', side_effect=lambda _: next(responses)):
                output = self.run_main_with_args([])
                self.assertIn("Processing", output)  # "Processing N remaining groups..."

def test_interactive_quit_stops_early(self):
    """User typing 'q' stops processing immediately."""
    with patch('sys.argv', ['filematcher', self.test_dir1, self.test_dir2,
                            '--action', 'hardlink', '--execute']):
        with patch('sys.stdin.isatty', return_value=True):
            with patch('builtins.input', return_value='q'):
                output = self.run_main_with_args([])
                # Should not execute any actions
                self.assertNotIn("Execution complete:", output)

def test_interactive_invalid_reprompts(self):
    """Invalid input causes re-prompt."""
    responses = iter(['invalid', 'maybe', 'y'])  # Invalid, invalid, valid
    with patch('sys.argv', ['filematcher', self.test_dir1, self.test_dir2,
                            '--action', 'hardlink', '--execute']):
        with patch('sys.stdin.isatty', return_value=True):
            with patch('builtins.input', side_effect=lambda _: next(responses)):
                output = self.run_main_with_args([])
                self.assertIn("Invalid response", output)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Batch confirmation (all or nothing) | Per-group confirmation | v1.5 Phase 19 | More control for users |
| Single Y/N prompt | y/n/a/q options | v1.5 Phase 19 | Matches git add -p UX |

**Deprecated/outdated:**
- External prompt libraries (questionary, rich.prompt): Overkill for simple y/n/a/q; stdlib `input()` sufficient
- Python 2's `raw_input()`: Use `input()` in Python 3

## Open Questions

Things that couldn't be fully resolved:

1. **Should 'q' show partial summary before exit?**
   - What we know: `q` should stop processing immediately
   - What's unclear: Whether to show "Processed X groups, Y remaining" message
   - Recommendation: Show brief summary (covered in Phase 21 - Error Handling & Polish)

2. **Keyboard interrupt during execution (not prompt)**
   - What we know: Can happen if user presses Ctrl+C during `execute_action()`
   - What's unclear: Whether to catch at execution level or let it propagate
   - Recommendation: Let Phase 21 handle - this is error recovery scope

3. **Empty group list edge case**
   - What we know: If no groups to process, should skip interactive loop
   - What's unclear: Whether to show "No groups to process" or just return
   - Recommendation: Check at start, return early with success (0, 0, 0, ...)

## Sources

### Primary (HIGH confidence)
- [Python input() documentation](https://docs.python.org/3/library/functions.html#input) - Official builtin docs
- [Git add --patch documentation](https://git-scm.com/docs/git-add) - Interactive CLI UX pattern
- [Python exception handling](https://python.swaroopch.com/exceptions.html) - KeyboardInterrupt/EOFError handling

### Secondary (MEDIUM confidence)
- [Case-insensitive comparison best practices](https://dev.to/bowmanjd/case-insensitive-string-comparison-in-python-using-casefold-not-lower-5fpi) - casefold vs lower
- [Handling Yes/No User Input](https://stackabuse.com/bytes/handling-yes-no-user-input-in-python/) - Prompt loop patterns
- [Difference between input() and sys.stdin.readline()](https://www.geeksforgeeks.org/python/difference-between-input-and-sys-stdin-readline/) - Input methods comparison

### Tertiary (LOW confidence)
- Existing codebase patterns (test_safe_defaults.py, test_cli.py) - Test mocking patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All stdlib, verified against official docs
- Architecture: HIGH - Follows established git add -p pattern, existing codebase patterns
- Pitfalls: HIGH - Common Python gotchas, verified with official docs and community best practices

**Research date:** 2026-01-29
**Valid until:** 2026-02-28 (30 days - stable domain, stdlib only)
