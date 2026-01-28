# Technology Stack: Interactive CLI Confirmation

**Project:** File Matcher - Interactive Per-File Confirmation
**Researched:** 2026-01-28
**Overall Confidence:** HIGH

## Executive Summary

**Recommendation: Pure Python standard library using `input()` and `sys.stdin.isatty()`**

File Matcher already uses this approach for the single "Proceed?" prompt. Extending it to per-file interactive confirmation requires no new dependencies and follows established patterns from Unix tools like `rm -i`, `git add -p`, and rsync. The existing codebase has mature testing infrastructure for mocking interactive prompts.

## Recommended Stack

### Core Input Handling

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `input()` builtin | Python 3.9+ | User prompt and response | Simple, automatically strips newline, writes prompt to correct stream |
| `sys.stdin.isatty()` | Python 3.9+ | TTY detection | Prevents hanging on piped/redirected stdin; already used in codebase |
| `sys.stderr` | Python 3.9+ | Error/prompt output | Separates prompts from program results when stdout is piped |

### Testing Infrastructure (Already Present)

| Technology | Version | Purpose | Current Usage |
|------------|---------|---------|---------------|
| `unittest.mock.patch` | Python 3.9+ | Mock `input()` and `isatty()` | Extensively used in test_cli.py, test_safe_defaults.py |
| `io.StringIO` | Python 3.9+ | Capture stdout/stderr | Used throughout test suite |

## Implementation Approach

### Pure `input()` Pattern (Recommended)

**What:** Direct use of Python's built-in `input()` function with response parsing.

**Why:**
- Zero dependencies (fits stdlib-only constraint)
- Simple, readable code
- Works with existing test infrastructure
- Proven in current codebase (`confirm_execution()` in cli.py)
- Standard practice for Python CLI tools

**Example pattern:**
```python
def prompt_for_action(file_path: str, action: str) -> str:
    """Prompt user for action on a specific file.

    Returns: 'y', 'n', 'a' (all), 'q' (quit/cancel)
    """
    if not sys.stdin.isatty():
        # Non-interactive mode: default to safe behavior
        return 'n'

    prompt = f"{action} {file_path}? [y/n/a/q] "
    response = input(prompt).strip().lower()

    # Handle common variations
    if response in ('y', 'yes'):
        return 'y'
    elif response in ('n', 'no'):
        return 'n'
    elif response in ('a', 'all'):
        return 'a'
    elif response in ('q', 'quit', 'cancel'):
        return 'q'
    else:
        # Invalid input: re-prompt
        print("Invalid input. Please enter y, n, a, or q.", file=sys.stderr)
        return prompt_for_action(file_path, action)
```

**Testing approach (already validated in codebase):**
```python
with patch('builtins.input', return_value='y'):
    with patch('sys.stdin.isatty', return_value=True):
        result = prompt_for_action("/path/to/file", "Delete")
        assert result == 'y'
```

## Alternatives Considered

### External Libraries (Not Recommended)

| Library | Purpose | Why Not |
|---------|---------|---------|
| [click](https://click.palletsprojects.com/) | CLI framework with `click.confirm()` | Adds dependency; project is pure stdlib; overkill for simple prompts |
| [prompt_toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit) | Rich interactive prompts | External dependency; requires complex terminal control for simple y/n/a/q |
| [questionary](https://pypi.org/project/questionary/) | Beautiful CLI prompts | External dependency; adds visual complexity not needed |
| [rich](https://rich.readthedocs.io/) | Fancy terminal output | External dependency; File Matcher already has working color system |
| [blessed](https://pypi.org/project/blessed/) | Terminal control | Released 2026-01-20; external dependency; unnecessary complexity |

### Curses Library (Standard Library, Not Recommended)

**What:** Python's `curses` module for terminal control and full-screen apps.

**Why not:**
- Overkill for simple line-by-line prompts
- Complex API (requires `initscr()`, `endwin()`, window management)
- Not cross-platform (Windows support requires `windows-curses` package)
- Difficult to test
- Takes over entire terminal (File Matcher needs to show progress, not full-screen UI)

**When to use curses:** Building full TUI applications with multiple windows, forms, or complex layouts. Not for simple interactive prompts.

### `sys.stdin.readline()` (Standard Library, Not Recommended)

**What:** Direct reading from stdin without prompt handling.

**Why not:**
- More verbose than `input()`: requires manual prompt writing to stderr, manual newline stripping
- No advantage for interactive use case
- Less readable code
- `input()` is specifically designed for this pattern

**When to use:** Bulk reading from piped input or when processing line-by-line streams. Not for interactive prompts.

## Real-World Patterns

### Unix Tools Analysis

| Tool | Interactive Pattern | Implementation |
|------|---------------------|----------------|
| `rm -i` | "remove 'file'? " prompt, accepts y/n | C, uses stdio for prompts, simple y/n check |
| `git add -p` | "Stage this hunk [y,n,q,a,d,s,e,?]?" | Perl (legacy) or Go (modern), line-oriented prompts |
| `rsync -i` | Non-interactive logging mode, not user prompts | C, writes progress to stdout |
| `cp -i` | "overwrite 'file'? " prompt | C, similar to rm -i pattern |

**Key observation:** All use simple stdin reading with y/n/a/q patterns. None use curses or fancy terminal libraries for this use case.

### Git's Interactive Add Pattern

Git's `add -p` (patch mode) is the gold standard for per-item interactive prompts. From the [Git Book](https://git-scm.com/book/en/v2/Git-Tools-Interactive-Staging) and [community guides](https://nuclearsquid.com/writings/git-add/):

**Prompt format:**
```
Stage this hunk [y,n,q,a,d,s,e,?]?
```

**Options:**
- `y` - yes, stage this hunk
- `n` - no, don't stage this hunk
- `q` - quit, don't stage this or any remaining hunks
- `a` - all, stage this and all remaining hunks in the file
- `d` - don't stage this or any remaining hunks
- `s` - split the hunk into smaller hunks
- `e` - manually edit the hunk
- `?` - help

**File Matcher mapping:**
- `y` - yes, perform action on this file
- `n` - no, skip this file
- `a` - all, perform action on all remaining files
- `q` - quit, cancel all remaining operations

### Modern CLI Best Practices

From [CLI Guidelines (clig.dev)](https://clig.dev/) and [UX patterns for CLI tools](https://lucasfcosta.com/2022/06/01/ux-patterns-cli-tools.html):

**Dangerous operation levels:**
- **Mild:** Deleting a single file → `-i` flag enables prompt
- **Moderate:** Bulk operations → prompt by default, `--yes` to skip
- **Severe:** Destructive remote operations → require explicit confirmation

**File Matcher's pattern:** Moderate (bulk hardlink/symlink/delete). Current behavior (prompt once) is appropriate, per-file prompts are enhancement for cautious users.

## Integration with Existing Code

### Current Confirmation Function

File Matcher already has `confirm_execution()` in `filematcher/cli.py`:

```python
def confirm_execution(skip_confirm: bool = False, prompt: str = "Proceed? [y/N] ") -> bool:
    """Prompt user for Y/N confirmation before executing changes."""
    if skip_confirm:
        return True
    if not sys.stdin.isatty():
        print("Non-interactive mode detected. Use --yes to skip confirmation.", file=sys.stderr)
        return False
    response = input(prompt).strip().lower()
    return response in ('y', 'yes')
```

**Strengths:**
- Already handles TTY detection
- Uses `input()` correctly
- Writes errors to stderr
- Well-tested with unittest.mock

**Extension needed:**
- Support 'a' (all) and 'q' (quit) options
- Support per-file prompts in loop
- Handle invalid input gracefully

### Formatter Integration

File Matcher uses Strategy pattern with `ActionFormatter` ABC. Interactive prompts are orthogonal to formatting:

- `TextActionFormatter`: Shows human-readable progress, continues to work with interactive prompts
- `JsonActionFormatter`: Accumulates results, incompatible with interactive mode (requires `--yes` or error)

**Constraint:** Interactive mode is text-only. `--json` + `--interactive` should error or imply `--yes`.

## Testing Strategy

### Existing Test Infrastructure (Verified)

File Matcher has 228 tests with extensive mock usage:

**Pattern 1: Mock input response**
```python
with patch('builtins.input', return_value='y'):
    with patch('sys.stdin.isatty', return_value=True):
        # Test interactive acceptance
```

**Pattern 2: Mock non-TTY**
```python
with patch('sys.stdin.isatty', return_value=False):
    # Test non-interactive rejection
```

**Pattern 3: Mock multiple responses**
```python
with patch('builtins.input', side_effect=['y', 'n', 'a']):
    # Test sequence of user inputs
```

### New Test Cases Needed

- [ ] Test 'a' (all) response stops prompting for remaining files
- [ ] Test 'q' (quit) response stops all operations
- [ ] Test invalid input causes re-prompt
- [ ] Test non-TTY mode with interactive flag errors or defaults safely
- [ ] Test --json + --interactive combination error

## Configuration Handling

### New CLI Flags

| Flag | Purpose | Default |
|------|---------|---------|
| `--interactive` / `-i` | Enable per-file prompts | False (batch prompt only) |

**Interaction with existing flags:**
- `--interactive` + `--yes` → Error (contradictory)
- `--interactive` + `--json` → Error (interactive requires text mode)
- `--interactive` + `--execute` → Required (compare mode has no actions)
- Non-TTY + `--interactive` → Error with helpful message

### Prompt Output Stream

**Current behavior:** `input()` writes prompt to stdout, reads from stdin.

**Problem:** If stdout is redirected, prompts disappear.

**Solution:** Write prompt to stderr explicitly when needed:
```python
# For stderr prompt:
sys.stderr.write(prompt)
sys.stderr.flush()
response = sys.stdin.readline().strip().lower()
```

**When to use:** Only if stdout redirection is a concern. For File Matcher, `input()` is sufficient (users redirecting output should use `--yes`).

## Implementation Checklist

- [ ] Extend `confirm_execution()` to support y/n/a/q responses
- [ ] Add per-file prompt in `execute_all_actions()` loop
- [ ] Handle 'a' (all) flag to skip remaining prompts
- [ ] Handle 'q' (quit) flag to stop execution with proper cleanup
- [ ] Invalid input re-prompts instead of failing
- [ ] Add `--interactive` / `-i` CLI flag
- [ ] Validate flag combinations (error on contradictions)
- [ ] Add tests for all response types
- [ ] Add tests for non-TTY behavior
- [ ] Update documentation

## Performance Considerations

**Concern:** Does per-file prompting slow down execution?

**Answer:** No. Interactive mode is for careful review. Users wanting speed use `--yes` to skip all prompts. Prompt overhead (milliseconds) is negligible compared to filesystem operations (seconds).

## Sources

### High Confidence (Official Documentation)

- [Python 3.14 curses documentation](https://docs.python.org/3/howto/curses.html) - Last updated 2026-01-27
- [Python 3.14 cmd module](https://docs.python.org/3/library/cmd.html)
- [Python stdin documentation](https://docs.python.org/3/library/sys.html)
- [Git Interactive Staging](https://git-scm.com/book/en/v2/Git-Tools-Interactive-Staging)
- [rsync man page](https://man7.org/linux/man-pages/man1/rsync.1.html)
- [rm man page](https://man7.org/linux/man-pages/man1/rm.1.html)

### Medium Confidence (Community Resources)

- [Git add --patch guide](https://nuclearsquid.com/writings/git-add/)
- [CLI Guidelines](https://clig.dev/)
- [UX patterns for CLI tools](https://lucasfcosta.com/2022/06/01/ux-patterns-cli-tools.html)
- [GeeksforGeeks: input() vs sys.stdin.readline()](https://www.geeksforgeeks.org/python/difference-between-input-and-sys-stdin-readline/)
- [Interactive vs Redirected Input Guide](https://runebook.dev/en/docs/python/library/sys/sys.stdin)

### Verified in Codebase

- Existing `confirm_execution()` implementation in `filematcher/cli.py`
- Extensive `unittest.mock` usage in test suite (test_cli.py, test_safe_defaults.py)
- Proven TTY detection with `sys.stdin.isatty()`

## Confidence Assessment

| Area | Level | Rationale |
|------|-------|-----------|
| Input handling | HIGH | `input()` + `isatty()` proven in current codebase, standard Python practice |
| Testing approach | HIGH | Existing test infrastructure already mocks these functions successfully |
| Library selection | HIGH | stdlib-only constraint eliminates alternatives; `input()` is canonical choice |
| Real-world patterns | HIGH | Unix tools (rm, git) use identical patterns; well-documented |
| Non-TTY safety | HIGH | Already implemented and tested in codebase |

## Final Recommendation

**Use pure Python standard library with `input()` and `sys.stdin.isatty()`.**

This approach:
- ✅ Requires zero new dependencies
- ✅ Extends existing, proven code patterns
- ✅ Works with existing test infrastructure
- ✅ Follows Unix tool conventions (rm -i, git add -p)
- ✅ Simple, readable implementation
- ✅ Safe in non-TTY environments

**Do not use:**
- ❌ External libraries (violates stdlib-only constraint)
- ❌ curses module (overkill, complex, testing difficulty)
- ❌ sys.stdin.readline() directly (less readable than input())

The implementation is straightforward: extend the existing `confirm_execution()` to support y/n/a/q options, integrate into the action execution loop, and add appropriate tests using the proven mock patterns.
