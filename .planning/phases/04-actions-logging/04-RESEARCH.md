# Phase 4: Actions & Logging - Research

**Researched:** 2026-01-19
**Domain:** File system operations (hardlink, symlink, delete) and audit logging
**Confidence:** HIGH

## Summary

This phase implements the actual file modification operations (hardlink, symlink, delete) with comprehensive logging. The research covers Python standard library APIs for file operations, safe atomic replacement patterns, error handling strategies, and audit logging best practices.

The core challenge is safely replacing duplicate files with links while maintaining a complete audit trail. The user has specified key decisions in CONTEXT.md including: temp-rename safety pattern, continue-on-error behavior, plain-text verbose logging, and a `--fallback-symlink` option for cross-filesystem hardlinks.

**Primary recommendation:** Use Python's pathlib API (`Path.hardlink_to()`, `Path.symlink_to()`, `Path.unlink()`) with a temp-rename safety pattern for atomic-like operations, and Python's standard `logging.FileHandler` for audit logging.

## Standard Stack

The established libraries/tools for this domain:

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pathlib | stdlib (3.10+) | `Path.hardlink_to()`, `Path.symlink_to()`, `Path.unlink()` | Modern OO interface, cross-platform, integrated with Path objects |
| os | stdlib | `os.replace()`, `os.link()`, `os.symlink()` | Lower-level operations, atomic rename |
| logging | stdlib | FileHandler for audit logs | Built-in, configurable, handles file rotation |
| datetime | stdlib | Timestamps for logging | ISO 8601 format support |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| tempfile | stdlib | Generate unique temp file names | If temp-rename suffix collisions occur |
| stat | stdlib | Check file permissions | Pre-validation of write access |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pathlib | os module | os module is lower-level but more explicit; pathlib is cleaner but `hardlink_to()` requires Python 3.10+ |
| logging.FileHandler | Manual file writes | Manual gives more control over format but loses handler ecosystem benefits |
| Plain text logs | JSON logs | JSON is more parseable but user specified human-readable plain text |

**Installation:**
```bash
# No installation needed - all standard library
```

## Architecture Patterns

### Recommended Project Structure

No new files needed. All functionality extends `file_matcher.py`:

```
file_matcher.py      # Add action execution functions
tests/
  test_actions.py    # New: Unit tests for actions (TEST-04)
  test_cli.py        # Extend: Integration tests for flag combinations (TEST-05)
```

### Pattern 1: Temp-Rename Safety Pattern (User Decision)

**What:** Rename duplicate to .tmp, create link, delete .tmp. If link fails, restore.
**When to use:** All link operations (hardlink, symlink) per CONTEXT.md decision.
**Example:**
```python
# Source: CONTEXT.md decision + Python pathlib docs
from pathlib import Path
import os

def safe_replace_with_link(duplicate: Path, master: Path, action: str) -> tuple[bool, str]:
    """
    Safely replace duplicate with a link to master using temp-rename pattern.

    Returns: (success: bool, error_message: str or empty)
    """
    temp_path = duplicate.with_suffix(duplicate.suffix + '.tmp')

    try:
        # Step 1: Rename duplicate to temp location
        duplicate.rename(temp_path)
    except OSError as e:
        return (False, f"Failed to rename to temp: {e}")

    try:
        # Step 2: Create link at original duplicate location
        if action == 'hardlink':
            duplicate.hardlink_to(master)
        elif action == 'symlink':
            duplicate.symlink_to(master.resolve())  # Absolute path per CONTEXT.md

        # Step 3: Delete temp file on success
        temp_path.unlink()
        return (True, "")

    except OSError as e:
        # Rollback: restore temp to original location
        try:
            temp_path.rename(duplicate)
        except OSError:
            pass  # Best effort rollback
        return (False, f"Failed to create {action}: {e}")
```

### Pattern 2: Continue-on-Error Execution

**What:** Process all files, collect failures, report summary at end.
**When to use:** Execution phase - user specified "don't halt on individual failure."
**Example:**
```python
# Source: CONTEXT.md decision
def execute_actions(
    duplicate_groups: list[tuple[str, list[str], str]],
    action: str,
    log_file: Path
) -> tuple[int, int, list[str]]:
    """
    Execute action on all duplicates.

    Returns: (success_count, failure_count, list of failed paths)
    """
    successes = 0
    failures = 0
    failed_paths = []

    for master_file, duplicates, _reason in duplicate_groups:
        for dup in duplicates:
            success, error = safe_replace_with_link(Path(dup), Path(master_file), action)
            if success:
                successes += 1
            else:
                failures += 1
                failed_paths.append(f"{dup}: {error}")

    return (successes, failures, failed_paths)
```

### Pattern 3: Exit Code Convention (User Decision)

**What:** Distinct exit codes for different outcomes.
**When to use:** main() return value.
**Example:**
```python
# Source: CONTEXT.md decision + existing argparse convention
# Exit codes:
# 0 = Full success (all operations completed)
# 1 = Total failure (no operations succeeded)
# 2 = Validation error (argparse convention, already used)
# 3 = Partial completion (some succeeded, some failed)

def determine_exit_code(success_count: int, failure_count: int) -> int:
    if failure_count == 0:
        return 0  # Full success
    elif success_count == 0:
        return 1  # Total failure
    else:
        return 3  # Partial completion
```

### Pattern 4: Audit Log Format (User Decision)

**What:** Plain text log with header, per-operation lines, and footer summary.
**When to use:** All executions - log created automatically.
**Example:**
```python
# Source: CONTEXT.md decision
# Log format example:
"""
================================================================================
File Matcher Execution Log
================================================================================
Timestamp: 2026-01-19T14:30:25
Directories: /path/to/master, /path/to/duplicates
Action: hardlink
Flags: --execute --verbose
================================================================================

[2026-01-19T14:30:25] HARDLINK /path/to/dup1.txt -> /path/to/master1.txt (1.2MB) [a1b2c3d4...] SUCCESS
[2026-01-19T14:30:25] HARDLINK /path/to/dup2.txt -> /path/to/master2.txt (500KB) [e5f6g7h8...] SUCCESS
[2026-01-19T14:30:26] HARDLINK /path/to/dup3.txt -> /path/to/master3.txt (2.0MB) [i9j0k1l2...] FAILED: Permission denied

================================================================================
Summary
================================================================================
Total files processed: 3
Successful: 2
Failed: 1
Space saved: 1.7MB

Failed files:
  - /path/to/dup3.txt: Permission denied
================================================================================
"""
```

### Anti-Patterns to Avoid

- **Direct unlink-then-link:** Never delete the duplicate before verifying the link can be created. Use temp-rename pattern.
- **Silent failures:** Always log and count failures. User expects summary.
- **Atomic assumptions:** `os.link()` is not atomic - the link creation itself cannot be undone if interrupted.
- **Relative symlinks:** User specified absolute paths for symlinks.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Timestamp formatting | Custom string formatting | `datetime.isoformat()` | ISO 8601 standard, handles timezone |
| Log file creation | Manual `open()` | `logging.FileHandler` | Handles encoding, buffering, errors |
| Temp file naming | Fixed `.tmp` suffix | UUID or `tempfile.mktemp` pattern | Avoid collisions if duplicate ends with `.tmp` |
| File size formatting | Custom division | Existing `format_file_size()` | Already implemented in codebase |
| Cross-filesystem detection | Manual stat | Existing `check_cross_filesystem()` | Already implemented in Phase 2 |

**Key insight:** The codebase already has helper functions for formatting and cross-filesystem detection. Reuse them.

## Common Pitfalls

### Pitfall 1: Symlink Following in index_directory

**What goes wrong:** `Path.is_file()` follows symlinks by default. A symlink pointing to a file returns `True`.
**Why it happens:** If a duplicate is itself a symlink, it gets processed. Replacing a symlink with a new link to master is usually fine, but it may be unexpected.
**How to avoid:** Document this behavior. The assumption from CONTEXT.md ("duplicates should always be regular files") is correct in most cases, but edge cases exist.
**Warning signs:** A duplicate path that doesn't exist after replacement (was a broken symlink).

### Pitfall 2: Cross-Device Hardlink Failure

**What goes wrong:** `os.link()` raises `OSError` with errno `EXDEV` when source and target are on different filesystems.
**Why it happens:** Hard links cannot span filesystems - this is a kernel limitation.
**How to avoid:** User specified `--fallback-symlink` flag behavior. Without flag, count as failure; with flag, auto-fallback to symlink.
**Warning signs:** OSError with "Invalid cross-device link" message.

### Pitfall 3: Permission Errors on Different Platforms

**What goes wrong:** Exception types vary by platform. Removing a directory raises `IsADirectoryError` on Linux but `PermissionError` on macOS.
**Why it happens:** Python wraps OS-specific errno values differently.
**How to avoid:** Catch `OSError` as the parent class, then inspect `.errno` if needed for specific handling.
**Warning signs:** Tests pass on one platform but fail on another.

### Pitfall 4: Race Conditions Between Scan and Execute

**What goes wrong:** File is deleted or moved between scanning and execution.
**Why it happens:** Other processes or users modify the filesystem.
**How to avoid:** User specified "don't re-verify content" and "missing duplicate = warning, missing master = failure." Handle gracefully.
**Warning signs:** `FileNotFoundError` during execution phase.

### Pitfall 5: Temp File Name Collisions

**What goes wrong:** If duplicate path is `/path/to/file.txt.tmp`, the temp rename creates `/path/to/file.txt.tmp.tmp`.
**Why it happens:** Simple suffix appending doesn't check for existing .tmp extension.
**How to avoid:** Use a more unique suffix like `.filematcher_tmp` or timestamp-based suffix.
**Warning signs:** Unexpected file left behind after failed operation.

### Pitfall 6: Already-Linked Files

**What goes wrong:** Attempting to hardlink a file that's already a hard link to the master.
**Why it happens:** Previous run, or files were already linked.
**How to avoid:** Check inode numbers - if duplicate already has same inode as master, skip (already linked).
**Warning signs:** Unnecessary operations that don't save space.

## Code Examples

Verified patterns from official sources:

### Create Hard Link (pathlib)
```python
# Source: https://docs.python.org/3/library/pathlib.html
from pathlib import Path

link_path = Path('/path/to/link')
target_path = Path('/path/to/target')
link_path.hardlink_to(target_path)  # Creates hard link at link_path pointing to target_path
```

### Create Symbolic Link (pathlib)
```python
# Source: https://docs.python.org/3/library/pathlib.html
from pathlib import Path

link_path = Path('/path/to/link')
target_path = Path('/path/to/target')
link_path.symlink_to(target_path.resolve())  # Absolute path for symlink
```

### Delete File (pathlib)
```python
# Source: https://docs.python.org/3/library/pathlib.html
from pathlib import Path

file_path = Path('/path/to/file')
file_path.unlink(missing_ok=False)  # Raises FileNotFoundError if missing
```

### Atomic Rename (os)
```python
# Source: https://docs.python.org/3/library/os.html
import os

# os.replace() is atomic on POSIX systems
os.replace('/path/to/source', '/path/to/destination')
```

### Check Same Inode (Detect Already Linked)
```python
# Source: Python os module documentation
import os

def already_hardlinked(file1: str, file2: str) -> bool:
    """Check if two files are already hard links to same data."""
    try:
        stat1 = os.stat(file1)
        stat2 = os.stat(file2)
        return stat1.st_ino == stat2.st_ino and stat1.st_dev == stat2.st_dev
    except OSError:
        return False
```

### FileHandler Logging Setup
```python
# Source: https://docs.python.org/3/library/logging.handlers.html
import logging
from pathlib import Path
from datetime import datetime

def create_log_file(log_path: Path | None = None) -> logging.Logger:
    """Create audit logger with FileHandler."""
    if log_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = Path(f"filematcher_{timestamp}.log")

    logger = logging.getLogger('filematcher.audit')
    logger.setLevel(logging.INFO)

    handler = logging.FileHandler(log_path, encoding='utf-8')
    handler.setFormatter(logging.Formatter('%(message)s'))  # Plain messages
    logger.addHandler(handler)

    return logger
```

### Cross-Filesystem Fallback Pattern
```python
# Source: CONTEXT.md decision + research
def execute_with_fallback(
    duplicate: Path,
    master: Path,
    action: str,
    fallback_symlink: bool
) -> tuple[bool, str, str]:
    """
    Execute action with optional symlink fallback for cross-filesystem.

    Returns: (success, error_message, actual_action_used)
    """
    if action == 'hardlink':
        success, error = safe_replace_with_link(duplicate, master, 'hardlink')
        if not success and 'cross-device' in error.lower() and fallback_symlink:
            # Fallback to symlink
            success, error = safe_replace_with_link(duplicate, master, 'symlink')
            if success:
                return (True, "", "symlink (fallback)")
        return (success, error, "hardlink")
    else:
        success, error = safe_replace_with_link(duplicate, master, action)
        return (success, error, action)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `os.link(src, dst)` | `Path(dst).hardlink_to(src)` | Python 3.10 | Cleaner pathlib API, note argument order reversal |
| Manual file logging | `logging.FileHandler` | Always available | Better error handling, encoding support |
| `os.path.exists()` before operation | Try/except with `OSError` | Best practice | TOCTOU race condition avoidance |

**Deprecated/outdated:**
- None relevant - all standard library APIs are stable

## Open Questions

Things that couldn't be fully resolved:

1. **Temp suffix naming**
   - What we know: Need unique suffix to avoid collisions
   - What's unclear: Best suffix format (`.filematcher_tmp`, `.tmp_{timestamp}`, UUID?)
   - Recommendation: Use `.filematcher_tmp` for simplicity; document edge case

2. **Log rotation**
   - What we know: Single execution = single log file per CONTEXT.md
   - What's unclear: Should very large operations use rotating handler?
   - Recommendation: No rotation for v1 - one log per execution

3. **Progress output destination**
   - What we know: Progress counter needed ("Processing 5/47...")
   - What's unclear: stdout vs stderr for progress
   - Recommendation: stderr for progress (stdout reserved for results)

## Sources

### Primary (HIGH confidence)
- [Python pathlib documentation](https://docs.python.org/3/library/pathlib.html) - Path.unlink(), Path.symlink_to(), Path.hardlink_to(), Path.replace()
- [Python os documentation](https://docs.python.org/3/library/os.html) - os.link(), os.symlink(), os.replace()
- [Python logging.handlers documentation](https://docs.python.org/3/library/logging.handlers.html) - FileHandler class

### Secondary (MEDIUM confidence)
- [Atomic symlink replacement patterns](https://blog.moertel.com/posts/2005-08-22-how-to-change-symlinks-atomically.html) - temp-rename atomic pattern
- [alexwlchan: Cross-filesystem atomic moves](https://alexwlchan.net/2019/atomic-cross-filesystem-moves-in-python/) - cross-device handling
- [Python Built-in Exceptions](https://docs.python.org/3/library/exceptions.html) - OSError hierarchy

### Tertiary (LOW confidence)
- None - all findings verified with official documentation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all stdlib, verified with official docs
- Architecture patterns: HIGH - based on user decisions in CONTEXT.md
- Pitfalls: HIGH - verified with official docs and known Python behavior
- Error handling: MEDIUM - platform-specific behavior varies

**Research date:** 2026-01-19
**Valid until:** 2026-02-19 (30 days - stable stdlib APIs)
