# Phase 3: Safe Defaults Refactor - Research

**Researched:** 2026-01-19
**Domain:** CLI safety patterns, argparse refactoring, interactive prompts
**Confidence:** HIGH

## Summary

This phase transforms the CLI from "destructive by default with opt-in preview" to "preview by default with opt-in execution" - a well-established pattern used by tools like git clean (`-n` vs `-f`), rsync (`--dry-run`), and package managers (`-y` to skip confirmation).

The implementation requires:
1. Removing the `--dry-run` flag (preview becomes default when `--action` is specified)
2. Adding `--execute` flag to enable actual file modifications
3. Adding interactive Y/N confirmation with `--yes/-y` bypass
4. Updating output terminology from "DRY RUN" to "PREVIEW MODE"

The codebase already has the infrastructure: `format_dry_run_banner()`, `format_statistics_footer()`, and action labels in `format_duplicate_group()`. This phase refactors the flag semantics and adds the confirmation prompt.

**Primary recommendation:** Implement using pure Python standard library (input(), sys.stdin.isatty()) with unittest.mock for testing - no external dependencies needed.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| argparse | stdlib | CLI argument parsing | Already in use, handles flag validation |
| sys.stdin | stdlib | TTY detection for prompts | `isatty()` determines interactive mode |
| builtins.input | stdlib | Interactive confirmation | Standard Python input mechanism |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| unittest.mock | stdlib | Testing interactive prompts | Mock `builtins.input` and `sys.stdin` |
| io.StringIO | stdlib | Simulating stdin in tests | Feed predefined input to tests |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| input() | click.confirm() | Adds dependency; project is pure stdlib |
| Manual Y/N parsing | prompt_toolkit | Overkill for simple Y/N; adds dependency |

**Installation:**
```bash
# No additional installation - all stdlib
```

## Architecture Patterns

### Recommended Confirmation Flow
```
User runs: filematcher dir1 dir2 --master dir1 --action hardlink --execute

1. Parse arguments (argparse)
2. Validate: --execute requires --master and --action
3. Run file matching (existing code)
4. Display preview output with "EXECUTING" banner
5. Display statistics
6. If not --yes: prompt "Proceed? [y/N]"
7. If confirmed: execute actions
8. Display completion summary
```

### Pattern 1: Defensive Flag Validation
**What:** Validate flag combinations in argparse before any file operations
**When to use:** Any flag that requires other flags to be meaningful
**Example:**
```python
# Existing pattern from Phase 2
if args.dry_run and not args.master:
    parser.error("--dry-run requires --master to be specified")

# New pattern for Phase 3
if args.execute and not (args.master and args.action):
    parser.error("--execute requires --master and --action")
```

### Pattern 2: TTY-Aware Confirmation
**What:** Only prompt interactively when stdin is a terminal
**When to use:** Confirmation prompts that should work in scripts
**Example:**
```python
def confirm_execution(skip_confirm: bool = False) -> bool:
    """
    Prompt user for confirmation before destructive operations.

    Args:
        skip_confirm: If True, skip prompt and return True (for --yes flag)

    Returns:
        True if user confirms, False otherwise
    """
    if skip_confirm:
        return True

    # In non-interactive mode, default to safe (no execution)
    if not sys.stdin.isatty():
        return False

    response = input("Proceed? [y/N] ").strip().lower()
    return response in ('y', 'yes')
```

### Pattern 3: Exit Code Semantics
**What:** Consistent exit codes for different outcomes
**When to use:** CLI tools that may be used in scripts
**Example:**
```python
# Exit codes (existing + new)
EXIT_SUCCESS = 0      # Normal completion (including user abort)
EXIT_ERROR = 1        # Runtime error
EXIT_VALIDATION = 2   # Argument validation error (argparse default)
```

### Anti-Patterns to Avoid
- **Defaulting to destructive:** Never execute file modifications without explicit `--execute`
- **Ignoring TTY state:** Don't prompt in non-interactive mode; fail safely instead
- **Ambiguous exit codes:** User abort is NOT an error; use exit code 0
- **Silent flag deprecation:** When removing `--dry-run`, make argparse explicitly reject it with clear error

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Y/N parsing | Complex input validation | Simple `in ('y', 'yes')` check | Edge cases minimal for Y/N |
| Flag validation | Custom validation logic | argparse `parser.error()` | Consistent exit code 2, proper help text |
| stdin mocking | Custom test infrastructure | `unittest.mock.patch('builtins.input')` | Mature, well-documented |
| TTY detection | Platform-specific code | `sys.stdin.isatty()` | Cross-platform stdlib |

**Key insight:** The project already uses argparse effectively for flag validation (see `--dry-run requires --master` pattern). Extend this pattern rather than inventing new validation approaches.

## Common Pitfalls

### Pitfall 1: Forgetting Non-Interactive Mode
**What goes wrong:** Prompt hangs forever when stdin is piped or redirected
**Why it happens:** `input()` blocks waiting for data that never comes
**How to avoid:** Check `sys.stdin.isatty()` before prompting; default to safe (no execution)
**Warning signs:** Tests pass but CI/scripts hang

### Pitfall 2: Case-Sensitive Confirmation
**What goes wrong:** User types "Y" or "YES" and it's rejected
**Why it happens:** Comparing against lowercase only
**How to avoid:** Always `.strip().lower()` the response
**Warning signs:** Manual testing with caps lock on

### Pitfall 3: Prompt Appearing in Captured Output
**What goes wrong:** Tests capture stdout but prompt goes to stderr or vice versa
**Why it happens:** `input(prompt)` writes prompt to stdout
**How to avoid:** Mock `builtins.input` entirely in tests; don't rely on output capture
**Warning signs:** Flaky tests depending on terminal state

### Pitfall 4: Breaking Existing Tests
**What goes wrong:** Removing `--dry-run` breaks 18 existing dry-run tests
**Why it happens:** Tests use `--dry-run` flag that no longer exists
**How to avoid:** Update tests to use new flag semantics (`--action` alone = preview)
**Warning signs:** Mass test failures after flag refactor

### Pitfall 5: Unclear Error Messages
**What goes wrong:** User doesn't understand what flags they need
**Why it happens:** Generic error like "missing required arguments"
**How to avoid:** Explicit message: "--execute requires --master and --action"
**Warning signs:** User support questions about flag combinations

## Code Examples

Verified patterns from official Python documentation and existing codebase:

### Adding --execute and --yes Flags
```python
# Pattern from existing codebase (argparse setup)
parser.add_argument('--execute', action='store_true',
                    help='Execute the action (without this flag, only preview)')
parser.add_argument('--yes', '-y', action='store_true',
                    help='Skip confirmation prompt')
```

### Removing --dry-run with Clear Error
```python
# Option 1: Remove entirely, let argparse give "unrecognized arguments" error
# (User gets: error: unrecognized arguments: --dry-run)

# Option 2: Keep as hidden argument that always errors (more descriptive)
# parser.add_argument('--dry-run', '-n', action='store_true', help=argparse.SUPPRESS)
# Then in validation:
# if args.dry_run:
#     parser.error("--dry-run is deprecated; preview is now the default. Use --execute to apply changes.")
```

### Confirmation Prompt Implementation
```python
def confirm_execution(skip_confirm: bool = False) -> bool:
    """Prompt user for Y/N confirmation."""
    if skip_confirm:
        return True
    if not sys.stdin.isatty():
        print("Non-interactive mode detected. Use --yes to skip confirmation.", file=sys.stderr)
        return False
    response = input("Proceed? [y/N] ").strip().lower()
    return response in ('y', 'yes')
```

### Testing Confirmation Prompt
```python
# Source: unittest.mock documentation, common pattern
from unittest.mock import patch

def test_confirmation_accepts_yes(self):
    """User typing 'y' confirms execution."""
    with patch('builtins.input', return_value='y'):
        result = confirm_execution()
        self.assertTrue(result)

def test_confirmation_rejects_no(self):
    """User typing 'n' or empty rejects execution."""
    with patch('builtins.input', return_value=''):
        result = confirm_execution()
        self.assertFalse(result)

def test_skip_confirmation_with_yes_flag(self):
    """--yes flag skips prompt entirely."""
    result = confirm_execution(skip_confirm=True)
    self.assertTrue(result)

def test_non_interactive_defaults_to_no(self):
    """Non-TTY stdin defaults to rejection."""
    with patch('sys.stdin.isatty', return_value=False):
        result = confirm_execution()
        self.assertFalse(result)
```

### Updated Banner Format
```python
# Current (Phase 2)
DRY_RUN_BANNER = "=== DRY RUN - No changes will be made ==="

# New (Phase 3)
PREVIEW_BANNER = "=== PREVIEW MODE - Use --execute to apply changes ==="
EXECUTE_BANNER = "=== EXECUTING ==="
```

### Action Label Updates for Preview
```python
# Current: [DUP:hardlink]
# New preview mode: [WOULD HARDLINK], [WOULD SYMLINK], [WOULD DELETE]
# Execute mode: Same as current or real-time progress (Claude's discretion)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `--dry-run` opt-in preview | Preview by default | This phase | Safer for new users |
| Immediate execution | `--execute` required | This phase | Prevents accidents |
| No confirmation | Y/N prompt | This phase | Extra safety layer |

**Deprecated/outdated:**
- `--dry-run` flag: Removed entirely. Preview is now the default when `--action` is specified.
- "DRY RUN" terminology: Replaced with "PREVIEW MODE" for clearer communication.

## Open Questions

Things that couldn't be fully resolved:

1. **Execute mode per-file output format**
   - What we know: Preview shows grouped output with statistics
   - What's unclear: Should execute mode show real-time progress (file-by-file) or same grouped output?
   - Recommendation: Claude's discretion per CONTEXT.md; suggest same format for consistency

2. **Handling deprecated --dry-run flag**
   - What we know: Flag should be removed
   - What's unclear: Should it error with helpful message or just "unrecognized argument"?
   - Recommendation: Helpful error message aids transition; slight extra code but better UX

## Sources

### Primary (HIGH confidence)
- Python argparse documentation - https://docs.python.org/3/library/argparse.html
- Existing `file_matcher.py` - established patterns for flag validation
- Existing `tests/test_dry_run.py` - testing patterns for CLI output

### Secondary (MEDIUM confidence)
- git-clean documentation - https://git-scm.com/docs/git-clean (`-n` dry-run, `-f` force pattern)
- rsync documentation - https://linux.die.net/man/1/rsync (`--dry-run` pattern)
- Python unittest.mock - gist examples for stdin mocking

### Tertiary (LOW confidence)
- Web search results on CLI safe defaults - general patterns, not library-specific

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Pure stdlib, patterns already in codebase
- Architecture: HIGH - Extends existing argparse patterns
- Pitfalls: HIGH - Common issues well-documented, some from existing test failures
- Code examples: HIGH - Based on existing codebase and stdlib docs

**Research date:** 2026-01-19
**Valid until:** 2026-02-19 (stable domain, stdlib-only)
