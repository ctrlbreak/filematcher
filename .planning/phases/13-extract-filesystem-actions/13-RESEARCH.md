# Phase 13: Extract Filesystem and Actions - Research

**Researched:** 2026-01-27
**Domain:** Python module extraction - filesystem helpers and action execution
**Confidence:** HIGH

## Summary

This phase extracts two related but independent modules from the monolithic `file_matcher.py`:

1. **`filesystem.py`** - Filesystem helper functions for detecting hardlinks, symlinks, cross-filesystem situations, and path utilities
2. **`actions.py`** - Action execution functions for hardlink/symlink/delete operations with rollback and audit logging

These modules are "near-leaf" modules - they have minimal dependencies:
- `filesystem.py` depends only on Python stdlib (os, pathlib)
- `actions.py` depends on `filesystem.py` (for `is_hardlink_to`, `is_symlink_to`) plus stdlib (os, pathlib, logging, datetime)

Neither module depends on colors, hashing, or the output formatters, making them suitable for extraction following the Phase 12 pattern.

**Primary recommendation:** Extract filesystem.py first as a pure leaf module, then extract actions.py which imports from filesystem.py. Use direct imports (not lazy `__getattr__`) since these are leaf/near-leaf modules with no circular import risk.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `os` | Python 3.9+ | File stat, path operations | Built-in for filesystem queries |
| Python stdlib `pathlib` | Python 3.9+ | Path manipulation, symlink/hardlink creation | Modern path API |
| Python stdlib `logging` | Python 3.9+ | Audit logging | Built-in logging framework |
| Python stdlib `datetime` | Python 3.9+ | Timestamps in audit logs | Built-in datetime handling |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Python stdlib `shutil` | Python 3.9+ | Terminal size (imported in file_matcher.py) | Not needed in extracted modules |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Direct import in __init__.py | Lazy `__getattr__` import | Direct is simpler for leaf modules, lazy only needed for circular import prevention |
| Separate audit_logging.py | Combine with actions.py | Audit logging is tightly coupled to action execution |

**Installation:** No new dependencies - all Python standard library.

## Architecture Patterns

### Recommended Project Structure
```
filematcher/
    __init__.py        # Re-exports (updated with filesystem, actions)
    __main__.py        # Entry point (unchanged)
    colors.py          # Phase 12: Color system
    hashing.py         # Phase 12: Hashing functions
    filesystem.py      # NEW: Filesystem helpers
    actions.py         # NEW: Action execution + audit logging
file_matcher.py        # Modified: imports from new modules
```

### Pattern 1: Filesystem Module (Pure Leaf)
**What:** Module with zero internal dependencies
**When to use:** Functions that only use stdlib
**Example:**
```python
# filematcher/filesystem.py
"""Filesystem helper functions for File Matcher.

This module provides utilities for:
- Hardlink/symlink detection and verification
- Cross-filesystem detection
- Path containment checks
"""
from __future__ import annotations

import os
from pathlib import Path


def get_device_id(path: str) -> int:
    """Get the device ID for a file's filesystem."""
    return os.stat(path).st_dev


def is_hardlink_to(file1: str, file2: str) -> bool:
    """Check if two files are already hard links to the same data."""
    try:
        stat1 = os.stat(file1)
        stat2 = os.stat(file2)
        return stat1.st_ino == stat2.st_ino and stat1.st_dev == stat2.st_dev
    except OSError:
        return False


def is_symlink_to(duplicate: str, master: str) -> bool:
    """Check if a duplicate file is a symlink pointing to the master file."""
    try:
        dup_path = Path(duplicate)
        if not dup_path.is_symlink():
            return False
        resolved_target = dup_path.resolve()
        resolved_master = Path(master).resolve()
        return resolved_target == resolved_master
    except OSError:
        return False


def check_cross_filesystem(master_file: str, duplicates: list[str]) -> set[str]:
    """Check which duplicates are on different filesystems than master."""
    # ... implementation


def filter_hardlinked_duplicates(
    master_file: str, duplicates: list[str]
) -> tuple[list[str], list[str]]:
    """Separate duplicates that are already hardlinked from those that aren't."""
    # ... implementation


def is_in_directory(filepath: str, directory: str) -> bool:
    """Check if a file path is within a directory."""
    return filepath.startswith(directory + os.sep) or filepath.startswith(directory)
```

### Pattern 2: Actions Module (Near-Leaf with Internal Dependency)
**What:** Module that depends on another filematcher module (filesystem)
**When to use:** When there's a clear dependency chain without cycles
**Example:**
```python
# filematcher/actions.py
"""Action execution for File Matcher.

This module provides:
- safe_replace_with_link: Atomic file replacement with rollback
- execute_action: Single action dispatch (hardlink/symlink/delete)
- execute_all_actions: Batch processing with continue-on-error
- determine_exit_code: Exit code calculation
- Audit logging functions
"""
from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path

# Internal import from filesystem module
from filematcher.filesystem import is_hardlink_to, is_symlink_to


def safe_replace_with_link(duplicate: Path, master: Path, action: str) -> tuple[bool, str]:
    """Safely replace duplicate file with a link to master using temp-rename pattern."""
    # ... implementation


def execute_action(
    duplicate: str,
    master: str,
    action: str,
    fallback_symlink: bool = False
) -> tuple[bool, str, str]:
    """Execute an action on a duplicate file."""
    # Uses is_hardlink_to and is_symlink_to from filesystem module
    # ... implementation


def execute_all_actions(...) -> tuple[int, int, int, int, list[tuple[str, str]]]:
    """Process all duplicate groups and execute the specified action."""
    # Uses execute_action, log_operation
    # ... implementation


# Audit logging functions
def create_audit_logger(log_path: Path | None = None) -> tuple[logging.Logger, Path]:
    """Create a separate logger for audit logging to file."""
    # ... implementation


def write_log_header(...) -> None: ...
def log_operation(...) -> None: ...
def write_log_footer(...) -> None: ...
```

### Pattern 3: Direct Import for Leaf Modules (Per Phase 12 Decision)
**What:** Use explicit imports in `__init__.py`, not lazy `__getattr__`
**When to use:** Modules with no circular import risk
**Example:**
```python
# filematcher/__init__.py
# Import from filesystem submodule (direct, no circular import risk)
from filematcher.filesystem import (
    get_device_id,
    is_hardlink_to,
    is_symlink_to,
    check_cross_filesystem,
    filter_hardlinked_duplicates,
    is_in_directory,
)

# Import from actions submodule (direct, depends on filesystem but no cycles)
from filematcher.actions import (
    safe_replace_with_link,
    execute_action,
    execute_all_actions,
    determine_exit_code,
    create_audit_logger,
    log_operation,
    write_log_header,
    write_log_footer,
)

# Remove these from __getattr__ lazy loader (moved to direct imports)
```

### Anti-Patterns to Avoid
- **Circular imports:** `actions.py` imports from `filesystem.py`, but `filesystem.py` must NOT import from `actions.py`
- **Importing from file_matcher.py in extracted modules:** Leaf modules must only import from stdlib and other filematcher submodules
- **Breaking test imports:** Tests use `from file_matcher import is_hardlink_to` - must continue working
- **Missing format_file_size dependency:** `actions.py` uses `format_file_size` for logging - keep in file_matcher.py and pass formatted strings, OR extract to a utility module

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Atomic file replacement | Manual rename/link/delete | `safe_replace_with_link` with temp-rename pattern | Existing rollback logic is tested |
| Audit logging | Print statements | `logging` module with separate logger | Standard Python logging, file rotation support |
| Path manipulation | String concatenation | `pathlib.Path` | Cross-platform, type-safe |

**Key insight:** These functions are already well-implemented and tested. The extraction is about organization, not reimplementation.

## Common Pitfalls

### Pitfall 1: format_file_size Dependency in actions.py
**What goes wrong:** `log_operation` and `write_log_footer` call `format_file_size()` which is defined in file_matcher.py
**Why it happens:** format_file_size is a utility function used by both formatting and logging
**How to avoid:** Three options:
  1. Import from file_matcher (creates dependency back to main file - NOT recommended)
  2. Duplicate function in actions.py (code duplication - acceptable for small function)
  3. Extract format_file_size to a separate utilities module (cleanest but adds complexity)
**Recommendation:** Duplicate `format_file_size` in actions.py - it's a simple 15-line function, and keeping actions.py self-contained is more important than DRY for this case

### Pitfall 2: Logger Dependency in execute_all_actions
**What goes wrong:** `execute_all_actions` uses module-level `logger` for debug messages
**Why it happens:** The function logs warnings about missing master files
**How to avoid:** Pass logger or use module-level logger in actions.py:
```python
# filematcher/actions.py
import logging
logger = logging.getLogger(__name__)
```
**Warning signs:** Tests that check logging output may need adjustment

### Pitfall 3: Missing Functions in __getattr__
**What goes wrong:** After extraction, `from filematcher import is_hardlink_to` fails
**Why it happens:** Function moved from file_matcher.py but not removed from `__getattr__` lazy loader
**How to avoid:** Remove extracted functions from `__getattr__` dict AND add direct imports from new modules
**Warning signs:** `AttributeError: module 'filematcher' has no attribute 'X'`

### Pitfall 4: Import Order in __init__.py
**What goes wrong:** ImportError when loading filematcher package
**Why it happens:** actions.py imports from filesystem.py, so filesystem must be imported first
**How to avoid:** Import filesystem.py before actions.py in __init__.py
**Warning signs:** Circular import errors or partially initialized module errors

### Pitfall 5: Test Imports from file_matcher
**What goes wrong:** Tests fail with ImportError
**Why it happens:** Tests do `from file_matcher import is_hardlink_to`
**How to avoid:** file_matcher.py must import and use the functions from filematcher modules
**Verification:** Run existing tests without modification - they must pass

## Code Examples

### filesystem.py Complete Structure
```python
# filematcher/filesystem.py
"""Filesystem helper functions for File Matcher.

This module provides utilities for detecting file relationships:
- is_hardlink_to: Check if two files share the same inode
- is_symlink_to: Check if a file is a symlink pointing to another
- check_cross_filesystem: Detect files on different filesystems
- filter_hardlinked_duplicates: Separate already-linked files
- get_device_id: Get filesystem device ID for a path
- is_in_directory: Check path containment

These functions handle OSError gracefully, returning safe defaults
rather than raising exceptions for missing files.
"""
from __future__ import annotations

import os
from pathlib import Path


def get_device_id(path: str) -> int:
    """Get the device ID for a file's filesystem.

    Args:
        path: Path to the file

    Returns:
        Device ID (st_dev from os.stat)

    Raises:
        OSError: If file cannot be accessed
    """
    return os.stat(path).st_dev


def is_hardlink_to(file1: str, file2: str) -> bool:
    """Check if two files are already hard links to the same data.

    Args:
        file1: Path to first file
        file2: Path to second file

    Returns:
        True if both files share the same inode and device,
        False otherwise or if either file cannot be accessed
    """
    try:
        stat1 = os.stat(file1)
        stat2 = os.stat(file2)
        return stat1.st_ino == stat2.st_ino and stat1.st_dev == stat2.st_dev
    except OSError:
        return False


def is_symlink_to(duplicate: str, master: str) -> bool:
    """Check if a duplicate file is a symlink pointing to the master file.

    Args:
        duplicate: Path to the potential symlink
        master: Path to the master file

    Returns:
        True if duplicate is a symlink whose target resolves to master,
        False otherwise or if either file cannot be accessed
    """
    try:
        dup_path = Path(duplicate)
        if not dup_path.is_symlink():
            return False
        resolved_target = dup_path.resolve()
        resolved_master = Path(master).resolve()
        return resolved_target == resolved_master
    except OSError:
        return False


def check_cross_filesystem(master_file: str, duplicates: list[str]) -> set[str]:
    """Check which duplicates are on different filesystems than master.

    Returns set of duplicate paths that cannot be hardlinked to master.

    Args:
        master_file: Path to the master file
        duplicates: List of paths to check

    Returns:
        Set of duplicate paths on different filesystems
    """
    if not duplicates:
        return set()

    try:
        master_device = get_device_id(master_file)
    except OSError:
        return set(duplicates)

    cross_fs = set()
    for dup in duplicates:
        try:
            if get_device_id(dup) != master_device:
                cross_fs.add(dup)
        except OSError:
            cross_fs.add(dup)

    return cross_fs


def filter_hardlinked_duplicates(
    master_file: str, duplicates: list[str]
) -> tuple[list[str], list[str]]:
    """Separate duplicates already hardlinked to master from those that aren't.

    Args:
        master_file: Path to the master file
        duplicates: List of paths to potential duplicate files

    Returns:
        Tuple of (actionable_duplicates, already_hardlinked)
    """
    actionable = []
    hardlinked = []

    for dup in duplicates:
        if is_hardlink_to(master_file, dup):
            hardlinked.append(dup)
        else:
            actionable.append(dup)

    return actionable, hardlinked


def is_in_directory(filepath: str, directory: str) -> bool:
    """Check if a file path is within a directory.

    Args:
        filepath: The file path to check
        directory: The directory to check against

    Returns:
        True if filepath is in or under directory
    """
    return filepath.startswith(directory + os.sep) or filepath.startswith(directory)
```

### actions.py Core Functions
```python
# filematcher/actions.py
"""Action execution and audit logging for File Matcher.

This module provides:
- safe_replace_with_link: Atomic replacement with rollback on failure
- execute_action: Single action dispatch with skip detection
- execute_all_actions: Batch processing with continue-on-error
- determine_exit_code: Exit code calculation per convention
- Audit logging: create_audit_logger, write_log_header, log_operation, write_log_footer
"""
from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path

from filematcher.filesystem import is_hardlink_to, is_symlink_to

logger = logging.getLogger(__name__)


def format_file_size(size_bytes: int | float) -> str:
    """Convert file size in bytes to human-readable format.

    Duplicated from file_matcher.py to keep actions module self-contained.
    """
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024.0 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    if i == 0:
        return f"{int(size_bytes)} {size_names[i]}"
    else:
        return f"{size_bytes:.1f} {size_names[i]}"


def safe_replace_with_link(duplicate: Path, master: Path, action: str) -> tuple[bool, str]:
    """Safely replace duplicate file with a link using temp-rename pattern.

    The temp-rename pattern ensures the original can be recovered if link fails.
    """
    temp_path = duplicate.with_suffix(duplicate.suffix + '.filematcher_tmp')

    try:
        duplicate.rename(temp_path)
    except OSError as e:
        return (False, f"Failed to rename to temp: {e}")

    try:
        if action == 'hardlink':
            duplicate.hardlink_to(master)
        elif action == 'symlink':
            duplicate.symlink_to(master.resolve())
        elif action == 'delete':
            pass  # No link creation for delete
        else:
            temp_path.rename(duplicate)
            return (False, f"Unknown action: {action}")

        temp_path.unlink()
        return (True, "")

    except OSError as e:
        try:
            temp_path.rename(duplicate)
        except OSError:
            pass
        return (False, f"Failed to create {action}: {e}")


def execute_action(
    duplicate: str,
    master: str,
    action: str,
    fallback_symlink: bool = False
) -> tuple[bool, str, str]:
    """Execute an action on a duplicate file."""
    dup_path = Path(duplicate)
    master_path = Path(master)

    if is_symlink_to(duplicate, master):
        return (True, "symlink to master", "skipped")

    if is_hardlink_to(duplicate, master):
        return (True, "hardlink to master", "skipped")

    if action == 'hardlink':
        success, error = safe_replace_with_link(dup_path, master_path, 'hardlink')
        if not success and fallback_symlink:
            error_lower = error.lower()
            if 'cross-device' in error_lower or 'invalid cross-device link' in error_lower:
                success, error = safe_replace_with_link(dup_path, master_path, 'symlink')
                if success:
                    return (True, "", "symlink (fallback)")
                return (False, error, "symlink (fallback)")
        return (success, error, "hardlink")

    elif action == 'symlink':
        success, error = safe_replace_with_link(dup_path, master_path, 'symlink')
        return (success, error, "symlink")

    elif action == 'delete':
        success, error = safe_replace_with_link(dup_path, master_path, 'delete')
        return (success, error, "delete")

    else:
        return (False, f"Unknown action: {action}", action)


def determine_exit_code(success_count: int, failure_count: int) -> int:
    """Determine the appropriate exit code based on operation results.

    Exit codes: 0=full success, 1=total failure, 3=partial completion
    """
    if failure_count == 0:
        return 0
    elif success_count == 0 and failure_count > 0:
        return 1
    else:
        return 3
```

## Extraction Checklist

### Filesystem Module (`filesystem.py`)
Must include:
- [ ] `get_device_id(path: str) -> int`
- [ ] `is_hardlink_to(file1: str, file2: str) -> bool`
- [ ] `is_symlink_to(duplicate: str, master: str) -> bool`
- [ ] `check_cross_filesystem(master_file: str, duplicates: list[str]) -> set[str]`
- [ ] `filter_hardlinked_duplicates(master_file: str, duplicates: list[str]) -> tuple[list[str], list[str]]`
- [ ] `is_in_directory(filepath: str, directory: str) -> bool`

Dependencies (stdlib only):
- os
- pathlib.Path

### Actions Module (`actions.py`)
Must include:
- [ ] `format_file_size(size_bytes: int | float) -> str` (duplicated for self-containment)
- [ ] `safe_replace_with_link(duplicate: Path, master: Path, action: str) -> tuple[bool, str]`
- [ ] `execute_action(duplicate: str, master: str, action: str, fallback_symlink: bool = False) -> tuple[bool, str, str]`
- [ ] `execute_all_actions(...) -> tuple[int, int, int, int, list[tuple[str, str]]]`
- [ ] `determine_exit_code(success_count: int, failure_count: int) -> int`
- [ ] `create_audit_logger(log_path: Path | None = None) -> tuple[logging.Logger, Path]`
- [ ] `write_log_header(audit_logger, dir1, dir2, master, action, flags) -> None`
- [ ] `log_operation(audit_logger, action, duplicate, master, file_size, file_hash, success, error) -> None`
- [ ] `write_log_footer(audit_logger, success_count, failure_count, skipped_count, space_saved, failed_list) -> None`

Dependencies:
- Python stdlib: os, logging, datetime, pathlib.Path
- Internal: filematcher.filesystem (is_hardlink_to, is_symlink_to)

### Test Compatibility
Tests that import filesystem-related symbols from `file_matcher`:
- `test_actions.py`: is_hardlink_to, safe_replace_with_link, execute_action, execute_all_actions, determine_exit_code, create_audit_logger, log_operation, write_log_header, write_log_footer
- `test_directory_operations.py`: is_symlink_to, execute_action, is_hardlink_to, filter_hardlinked_duplicates

All must continue to work via `from file_matcher import X` after extraction.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single monolithic file | Modular package with submodules | This refactoring | Better testability, clearer API |
| Functions mixed in main file | Domain-specific modules | Best practice | Easier navigation, single responsibility |

**Deprecated/outdated:**
- None - this is standard Python module organization

## Open Questions

1. **Should format_file_size be in a separate utils.py module?**
   - What we know: Used by both actions.py (logging) and file_matcher.py (formatting)
   - What's unclear: Is duplication acceptable or should we have a shared module?
   - Recommendation: Duplicate in actions.py for now - it's small and keeps actions self-contained. Can refactor to utils.py later if more functions need sharing.

2. **Should execute_all_actions move to actions.py?**
   - What we know: It uses module logger and calls execute_action
   - What's unclear: It's tightly coupled to the main workflow
   - Recommendation: Yes, move it - it's the core action execution loop and belongs with execute_action

## Sources

### Primary (HIGH confidence)
- Codebase analysis: `file_matcher.py` lines 926-939 (is_in_directory), 1356-1404 (filesystem helpers), 1407-1480 (hardlink/symlink functions), 1482-1716 (action execution), 1744-1892 (audit logging)
- Codebase analysis: `tests/test_actions.py` and `tests/test_directory_operations.py` (import patterns)
- Phase 12 documentation: `.planning/phases/12-extract-foundation-modules/12-RESEARCH.md` (established patterns)
- Phase 11/12 decisions: Direct imports for leaf modules, `__getattr__` only for circular import prevention

### Secondary (MEDIUM confidence)
- Python stdlib documentation for pathlib.Path hardlink_to, symlink_to
- Python logging module best practices

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Python stdlib only, well-documented
- Architecture: HIGH - Follows established Phase 12 pattern
- Pitfalls: HIGH - Based on actual codebase analysis and existing test patterns

**Research date:** 2026-01-27
**Valid until:** 90 days (Python patterns are stable)
