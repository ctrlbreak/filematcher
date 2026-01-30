# Phase 21: Error Handling & Polish - Research

**Researched:** 2026-01-30
**Domain:** Python CLI error recovery, user feedback, and graceful termination
**Confidence:** HIGH

## Summary

This phase implements robust error handling for file operations during interactive and batch execution modes. The research confirms that Python's `OSError` hierarchy (including `PermissionError`) provides the necessary exception types. The exit code 130 convention for user-interrupted processes (SIGINT/Ctrl+C) is well-established in Unix shells (128 + signal_number, where SIGINT=2). The existing codebase already has continue-on-error patterns in `execute_all_actions()` that can be extended.

The key implementation areas are: (1) catching and displaying permission/access errors inline during execution, (2) handling the 'q' response and Ctrl+C to show a clean partial summary, (3) enhancing the final execution summary with user decision counts and comprehensive statistics. The existing formatter pattern (`TextActionFormatter` and `JsonActionFormatter`) provides the architecture for adding error display methods.

**Primary recommendation:** Extend the existing formatter ABC with `format_file_error()` method for inline error display, modify `interactive_execute()` to catch and continue on `OSError` subclasses, and add a `format_quit_summary()` method for clean 'q'/interrupt handling.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `OSError` | stdlib | Base exception for filesystem errors | Python 3.3+ unified hierarchy |
| `PermissionError` | stdlib | Access denied errors (EACCES, EPERM) | Specific subclass for permission issues |
| `errno` | stdlib | Error code constants (EACCES, EPERM, etc.) | Cross-platform error identification |
| `signal` | stdlib | Signal handling constants (SIGINT=2) | Exit code calculation (128 + signal_number) |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `filematcher.formatters` | internal | `ActionFormatter` ABC | Error display methods |
| `filematcher.actions` | internal | `execute_action()`, logging functions | Error capture and audit logging |
| `filematcher.types` | internal | `FailedOperation` namedtuple | Structured error tracking |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Catching `OSError` | Catching `Exception` | Too broad; may mask programming errors |
| Exit code 130 | Exit code 1 | 130 follows Unix convention for SIGINT interruption |
| Per-file errors | Abort on first error | Less user-friendly; already rejected by existing architecture |

**Installation:**
```bash
# No installation needed - all stdlib and internal modules
```

## Architecture Patterns

### Recommended Project Structure
```
filematcher/
  formatters.py
    |-- ActionFormatter ABC
    |     +-- format_file_error()         # NEW: inline error display
    |     +-- format_quit_summary()       # NEW: 'q'/interrupt summary
    |-- TextActionFormatter
    |     +-- implements all error display methods with color
    |-- JsonActionFormatter
    |     +-- accumulates errors in structured arrays
  cli.py
    |-- interactive_execute()             # MODIFY: catch OSError, call format_file_error()
    |-- _format_final_summary()           # NEW: comprehensive final summary helper
  actions.py
    |-- execute_action()                  # Already has error handling, returns (success, error, action)
    |-- create_audit_logger()             # MODIFY: fail-fast if log file cannot be written
```

### Pattern 1: Inline Error Display During Execution

**What:** Display error messages immediately when a file operation fails, then continue to next file
**When to use:** During interactive or batch execution when individual files fail
**Example:**
```python
# Source: Existing execute_all_actions() pattern in filematcher/actions.py

def execute_with_error_display(
    dup: str,
    master_file: str,
    action: Action,
    formatter: ActionFormatter,
    # ... other params
) -> tuple[bool, int]:
    """Execute action with inline error display.

    Returns: (success, file_size_if_success)
    """
    try:
        file_size = os.path.getsize(dup) if os.path.exists(dup) else 0
    except OSError as e:
        formatter.format_file_error(dup, str(e))
        return (False, 0)

    success, error, actual_action = execute_action(
        dup, master_file, action.value,
        fallback_symlink=fallback_symlink,
        target_dir=target_dir,
        dir2_base=dir2_base
    )

    if not success:
        formatter.format_file_error(dup, error)

    return (success, file_size if success else 0)
```

### Pattern 2: Quit Summary with Partial Results

**What:** On 'q' response or Ctrl+C, show what was processed and what remains
**When to use:** User requests early termination via 'q' or signal
**Example:**
```python
# Source: Context from 21-CONTEXT.md decisions

def format_quit_summary(
    self,
    confirmed_count: int,
    skipped_count: int,
    remaining_count: int,
    space_saved: int,
    action: str
) -> None:
    """Display summary when user quits early.

    Shows:
    - What was completed
    - What was skipped
    - What remains unprocessed
    - Partial space savings
    - Hint to re-run
    """
    # Text mode
    print()
    print(f"Quit: {confirmed_count} processed, {skipped_count} skipped, {remaining_count} remaining")
    if space_saved > 0:
        space_str = format_file_size(space_saved)
        print(f"Freed {space_str} (quit before completing all)")
    print("Re-run command to process remaining files")
```

### Pattern 3: Comprehensive Final Summary

**What:** Single compact block showing all execution metrics
**When to use:** After all groups processed (normal completion)
**Example:**
```python
# Source: Context from 21-CONTEXT.md - single compact block requirement

def format_execution_summary_enhanced(
    self,
    confirmed_count: int,
    user_skipped_count: int,
    success_count: int,
    failure_count: int,
    skipped_count: int,  # Already linked/missing
    space_saved: int,
    log_path: str,
    failed_list: list[FailedOperation]
) -> None:
    """Display comprehensive execution summary.

    Three-way distinction:
    - confirmed: user said 'y' or 'a'
    - user-skipped: user said 'n'
    - error-failed: operation failed due to error

    Shows space saved in both formats: "1.2 GB (1,288,490,188 bytes)"
    Always shows audit log path.
    """
    print()
    # User decisions
    print(f"User confirmed: {confirmed_count}")
    print(f"User skipped: {user_skipped_count}")

    # Execution results
    print(f"Succeeded: {success_count}")
    print(f"Failed: {failure_count}")
    if skipped_count > 0:
        print(f"Already linked: {skipped_count}")

    # Space saved (human-readable AND bytes)
    space_str = format_file_size(space_saved)
    print(f"Space freed: {space_str} ({space_saved:,} bytes)")

    # Always show log path
    print(f"Audit log: {log_path}")

    # Show individual failures
    if failed_list:
        print()
        print("Failed files:")
        for path, error in sorted(failed_list):
            print(f"  {red('\u2717', self.cc)} {path}: {error}")
```

### Pattern 4: Audit Logger Fail-Fast

**What:** If audit log file cannot be created, abort before any file operations
**When to use:** During audit logger initialization
**Example:**
```python
# Source: Context from 21-CONTEXT.md - audit trail is required

def create_audit_logger(log_path: Path | None = None) -> tuple[logging.Logger, Path]:
    """Create audit logger, fail-fast if file cannot be written.

    Raises:
        SystemExit: If audit log file cannot be created (code 2)
    """
    if log_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = os.environ.get('FILEMATCHER_LOG_DIR')
        if log_dir:
            log_path = Path(log_dir) / f"filematcher_{timestamp}.log"
        else:
            log_path = Path(f"filematcher_{timestamp}.log")

    try:
        # Test write access before proceeding
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
    except OSError as e:
        logger.error(f"Cannot create audit log: {log_path}: {e}")
        logger.error("Audit trail is required for destructive operations. Aborting.")
        sys.exit(2)

    # ... rest of setup
```

### Anti-Patterns to Avoid

- **Suppressing errors silently:** Always display errors to user, even when continuing
- **Using bare `except:`:** Catches too much; use specific `OSError` subclasses
- **Exit code 0 on partial failure:** Use exit code 2 for partial success per CONTEXT.md
- **Losing error context:** Include the system error message (e.g., "Permission denied"), not just "Failed"
- **Continuing after audit log failure:** Per CONTEXT.md, abort if audit trail cannot be established

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Error message extraction | Custom parsing | `OSError.strerror` or `str(e)` | System provides localized message |
| Human-readable sizes | Manual division | `format_file_size()` in `actions.py` | Already handles all units (B, KB, MB, GB, TB) |
| Exit code for interruption | Arbitrary code | 128 + signal.SIGINT (=130) | Unix convention, recognized by shells |
| Error tracking | Ad-hoc lists | `FailedOperation` namedtuple | Already defined in `types.py` |
| Color output | Direct ANSI codes | `red()`, `green()`, `yellow()` | Respects ColorConfig settings |

**Key insight:** The existing codebase has most infrastructure. Phase 21 adds error display methods to formatters and wires them into the execution paths.

## Common Pitfalls

### Pitfall 1: Catching Too Broad Exceptions

**What goes wrong:** `except Exception:` masks programming bugs (TypeError, AttributeError)
**Why it happens:** Developer wants to "handle all errors" for robustness
**How to avoid:** Catch specific exception hierarchy: `except OSError as e:`
**Warning signs:** Unexplained silent failures, bugs hard to diagnose
```python
# BAD
try:
    os.unlink(path)
except Exception as e:  # Catches everything including bugs
    log_error(e)

# GOOD
try:
    os.unlink(path)
except OSError as e:  # Only filesystem errors
    log_error(e)
```

### Pitfall 2: Forgetting to Log Errors to Audit Log

**What goes wrong:** Error displayed to user but not recorded in audit log
**Why it happens:** Adding inline error display without updating logging call
**How to avoid:** Always call `log_operation()` with `success=False` and error message
**Warning signs:** Audit log shows fewer failures than user saw

### Pitfall 3: Inconsistent Error Display Between Modes

**What goes wrong:** Text mode shows red X, JSON mode doesn't include error
**Why it happens:** Implementing error display only in TextActionFormatter
**How to avoid:** Add method to ABC, implement in both formatters
**Warning signs:** `--json` output missing error information that `--no-json` shows

### Pitfall 4: Not Handling EOFError on Input

**What goes wrong:** Piped input (echo "" | filematcher) causes traceback
**Why it happens:** `input()` raises EOFError when stdin is exhausted
**How to avoid:** Catch both `KeyboardInterrupt` and `EOFError` together
**Warning signs:** Script crashes when input is piped
```python
# Source: Already correct in filematcher/cli.py interactive_execute()
except (KeyboardInterrupt, EOFError):
    print()  # Newline after ^C
```

### Pitfall 5: Exit Code 2 vs Exit Code 1 Confusion

**What goes wrong:** Scripts checking exit codes get wrong semantics
**Why it happens:** Using 1 for all errors instead of distinguishing types
**How to avoid:** Follow convention: 1=total failure, 2=partial/validation error, 130=user quit
**Warning signs:** Cannot distinguish "nothing worked" from "some things failed"
```python
# Current in actions.py determine_exit_code() returns:
# 0 = full success
# 1 = total failure (all operations failed)
# 3 = partial completion

# Per CONTEXT.md:
# 2 = partial success (any errors in batch mode)
# 130 = user quit (q response or SIGINT)
```

### Pitfall 6: Space Saved Calculation on Failed Operations

**What goes wrong:** Space saved includes files that weren't actually deleted/linked
**Why it happens:** Calculating space before checking operation success
**How to avoid:** Only add to space_saved AFTER successful operation
**Warning signs:** Summary shows space saved > actual disk change
```python
# Source: Already correct in filematcher/cli.py interactive_execute()
if success:
    success_count += 1
    space_saved += file_size  # Only on success
```

## Code Examples

Verified patterns from official sources:

### Formatter Method for Inline Error Display
```python
# Source: Extending existing filematcher/formatters.py pattern

# Add to ActionFormatter ABC
@abstractmethod
def format_file_error(self, file_path: str, error: str) -> None:
    """Output error message for a failed file operation.

    Args:
        file_path: Path to file that failed
        error: System error message (e.g., "Permission denied")
    """
    ...

# TextActionFormatter implementation
def format_file_error(self, file_path: str, error: str) -> None:
    """Display inline error with red X marker."""
    print(f"  {red('\u2717', self.cc)} {file_path}: {error}")

# JsonActionFormatter implementation
def format_file_error(self, file_path: str, error: str) -> None:
    """Accumulate error in errors array."""
    if "errors" not in self._data:
        self._data["errors"] = []
    self._data["errors"].append({
        "path": file_path,
        "error": error
    })
```

### Exit Code 130 for User Quit
```python
# Source: Unix signal convention, Python signal module

import signal

EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_PARTIAL = 2  # Per CONTEXT.md for batch mode with errors
EXIT_USER_QUIT = 128 + signal.SIGINT  # 130

# In main() after interactive_execute():
if user_quit:
    formatter.format_quit_summary(confirmed, skipped, remaining, space_saved, action)
    return EXIT_USER_QUIT

if failure_count > 0:
    return EXIT_PARTIAL  # Per CONTEXT.md

return EXIT_SUCCESS if success_count > 0 else EXIT_SUCCESS
```

### JSON Error Array Structure
```python
# Source: Extending existing filematcher/formatters.py JsonActionFormatter

# In finalize(), ensure errors are included:
output_data = {
    "header": header,
    "warnings": self._data.get("warnings", []),
    "duplicateGroups": self._data["duplicateGroups"],
    "statistics": self._data.get("statistics", {}),
    "errors": self._data.get("errors", []),  # Per-file errors
}

if "execution" in self._data:
    output_data["execution"] = self._data["execution"]
    # execution.failures already has the failed list
```

### Test Pattern for Permission Error
```python
# Source: Existing test_actions.py patterns

def test_permission_error_displays_and_continues(self):
    """Permission denied shows error but continues to next file."""
    master = self.master_dir / "file.txt"
    dup1 = self.dup_dir / "readonly.txt"
    dup2 = self.dup_dir / "writable.txt"
    master.write_text("content")
    dup1.write_text("content")
    dup2.write_text("content")

    # Make dup1 parent readonly to cause permission error
    # Alternative: mock execute_action to return permission error
    with patch('filematcher.actions.execute_action') as mock_exec:
        def side_effect(dup, master, action, **kwargs):
            if 'readonly' in dup:
                return (False, "Permission denied", action)
            # Actually execute for writable
            return execute_action(dup, master, action, **kwargs)

        mock_exec.side_effect = side_effect

        result = interactive_execute(
            groups=[
                DuplicateGroup(str(master), [str(dup1), str(dup2)], "test", "hash")
            ],
            action=Action.DELETE,
            formatter=self.formatter
        )

    success, failure, *_ = result
    self.assertEqual(failure, 1)  # readonly failed
    self.assertEqual(success, 1)  # writable succeeded
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Abort on first error | Continue-on-error with reporting | Already in codebase | More resilient |
| Exit code 1 for all errors | Distinct codes (1, 2, 130) | Phase 21 | Better scripting support |
| Silent skip of inaccessible files | Inline error display | Phase 21 | Better user feedback |

**Deprecated/outdated:**
- Python 2's IOError: Use OSError (unified in Python 3.3+)
- Catching by errno value: Use specific exception subclasses (PermissionError, etc.)

## Open Questions

Things that couldn't be fully resolved:

1. **Should 'q' show audit log path?**
   - What we know: Final summary always shows log path
   - What's unclear: Whether quit summary should also show it
   - Recommendation: YES, show log path in quit summary too (consistency)

2. **Error display position relative to group**
   - What we know: CONTEXT.md says "inline error message"
   - What's unclear: Exact placement (after group header? after each duplicate?)
   - Recommendation: After each duplicate line that fails, indented to align

3. **Exit code when user skips all via 'n' responses**
   - What we know: User skipped everything, nothing executed
   - What's unclear: Is this success (0) or something else?
   - Recommendation: Exit 0 - user made intentional choices, no errors occurred

## Sources

### Primary (HIGH confidence)
- [Python Built-in Exceptions](https://docs.python.org/3/library/exceptions.html) - OSError hierarchy, PermissionError
- [Python Errors and Exceptions](https://docs.python.org/3/tutorial/errors.html) - Exception handling patterns
- Existing codebase: `filematcher/actions.py` execute_all_actions() - continue-on-error pattern
- Existing codebase: `filematcher/cli.py` interactive_execute() - KeyboardInterrupt/EOFError handling

### Secondary (MEDIUM confidence)
- [Baeldung Linux Status Codes](https://www.baeldung.com/linux/status-codes) - Exit code conventions
- [TLDP Exit Codes](https://tldp.org/LDP/abs/html/exitcodes.html) - 128+signal convention
- [Real Python PermissionError](https://realpython.com/ref/builtin-exceptions/permissionerror/) - Permission error handling

### Tertiary (LOW confidence)
- WebSearch results on exit code 130 - Multiple sources confirm convention but no single authoritative source

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All stdlib, well-documented Python exception hierarchy
- Architecture: HIGH - Extends existing patterns already in codebase
- Pitfalls: HIGH - Based on code review and common Python gotchas
- Exit codes: MEDIUM - Convention is well-known but varies slightly across shells

**Research date:** 2026-01-30
**Valid until:** 2026-02-28 (30 days - stable domain, stdlib only)
