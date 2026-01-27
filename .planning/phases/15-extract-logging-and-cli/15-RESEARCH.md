# Phase 15: Extract Logging and CLI - Research

**Researched:** 2026-01-27
**Domain:** Python module extraction - CLI and entry point configuration
**Confidence:** HIGH

## Summary

Phase 15 extracts the CLI module and finalizes entry points. However, research reveals that **MOD-07 (Extract audit logging to `filematcher/logging.py`) is already complete** - audit logging functions were extracted to `filematcher/actions.py` in Phase 13 (Plan 13-02). The requirement was satisfied with a different module structure.

The remaining work for Phase 15 is:
1. **MOD-08**: Extract CLI and main() to `filematcher/cli.py`
2. **PKG-03**: Update pyproject.toml entry point from `file_matcher:main` to `filematcher.cli:main`

This phase completes the modular extraction by moving all remaining functions from `file_matcher.py` to the `filematcher` package, establishing `file_matcher.py` as a thin wrapper for backward compatibility.

**Primary recommendation:** Extract the CLI module (`filematcher/cli.py`) containing `main()` and its helper functions, then update pyproject.toml to point the `filematcher` script to `filematcher.cli:main`.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `argparse` | Python 3.9+ | CLI argument parsing | Built-in, full-featured arg parser |
| Python stdlib `logging` | Python 3.9+ | Logger configuration | Built-in logging framework |
| Python stdlib `sys` | Python 3.9+ | argv, exit, stdin/stdout | Built-in for CLI operations |
| Python stdlib `pathlib` | Python 3.9+ | Path manipulation | Modern path API |
| Python stdlib `os` | Python 3.9+ | OS-level file checks | Built-in filesystem access |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| setuptools | 61.0+ | Entry point configuration | pyproject.toml-based packaging |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| argparse | click | Better UX but external dependency; project requires stdlib-only |
| Single cli.py | Separate cli.py and main.py | Unnecessary complexity for this size |

**Installation:** No new dependencies - all Python standard library.

## Architecture Patterns

### Recommended Project Structure (Final State)
```
filematcher/
    __init__.py        # Re-exports public API
    __main__.py        # Entry point for python -m filematcher
    cli.py             # NEW: main() and CLI helpers
    colors.py          # Color system
    hashing.py         # Hashing functions
    filesystem.py      # Filesystem helpers
    actions.py         # Action execution + audit logging
    formatters.py      # Output formatters
    directory.py       # Directory indexing
file_matcher.py        # Backward-compat wrapper (imports from filematcher)
```

### Pattern 1: CLI Module Structure
**What:** Module containing main() entry point and CLI-specific helpers
**When to use:** CLI applications with complex argument parsing
**Example:**
```python
# filematcher/cli.py
"""Command-line interface for File Matcher.

This module provides:
- main(): CLI entry point (returns exit code)
- confirm_execution(): User confirmation prompt
- Helper functions for main() workflow
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

# Import from sibling modules
from filematcher.colors import ColorConfig, determine_color_mode
from filematcher.directory import find_matching_files
from filematcher.actions import (
    create_audit_logger, write_log_header, write_log_footer,
    execute_all_actions, determine_exit_code
)
from filematcher.formatters import (
    TextActionFormatter, JsonActionFormatter, calculate_space_savings
)
from filematcher.filesystem import filter_hardlinked_duplicates, is_in_directory

logger = logging.getLogger(__name__)


def confirm_execution(skip_confirm: bool = False, prompt: str = "Proceed? [y/N] ") -> bool:
    """Prompt user for Y/N confirmation before executing changes."""
    # ... implementation


def main() -> int:
    """Main entry point. Returns 0 on success, 1 on error."""
    # ... implementation
```

### Pattern 2: Entry Point Configuration in pyproject.toml
**What:** Console script entry point pointing to package module
**When to use:** Installable CLI tools via pip
**Example:**
```toml
[project.scripts]
filematcher = "filematcher.cli:main"
```

### Pattern 3: __main__.py Delegation
**What:** Entry point delegates to cli module for python -m invocation
**When to use:** Package invocation via `python -m package`
**Example:**
```python
# filematcher/__main__.py (updated)
"""Entry point for python -m filematcher."""
import sys
from filematcher.cli import main

if __name__ == "__main__":
    sys.exit(main())
```

### Anti-Patterns to Avoid
- **Circular imports:** cli.py must not import from file_matcher.py (it's the other way around)
- **Hardcoding paths:** Use `__name__` for logger names to get hierarchical namespacing
- **Breaking backward compat:** `from file_matcher import main` must continue working

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Argument parsing | Manual argv parsing | argparse | Handles help, validation, types |
| Exit codes | Custom scheme | Standard codes (0, 1, 2, 3) | Unix conventions understood by shells |
| Logger config | Global config | Module-level getLogger(__name__) | Hierarchical, testable |

**Key insight:** CLI organization follows standard Python patterns - no custom solutions needed.

## Common Pitfalls

### Pitfall 1: MOD-07 Already Satisfied
**What goes wrong:** Trying to create a separate `filematcher/logging.py` module
**Why it happens:** Original requirement defined before Phase 13 implementation
**How to avoid:** Recognize audit logging is already in `filematcher/actions.py` - don't create duplicate module
**Warning signs:** Confusion about where `create_audit_logger` should live

**Resolution:** MOD-07 requirement is SATISFIED by Phase 13. Success criterion `from filematcher.logging import create_audit_logger` should be adjusted to `from filematcher import create_audit_logger` OR a simple re-export module can be created.

### Pitfall 2: Logger Configuration Scope
**What goes wrong:** Logger for CLI messages doesn't display properly
**Why it happens:** `logger = logging.getLogger(__name__)` creates `filematcher.cli` logger, needs handler configuration
**How to avoid:** main() must configure both `filematcher.cli` logger AND sibling module loggers
**Warning signs:** Progress messages not appearing or appearing twice

### Pitfall 3: Entry Point Module Path
**What goes wrong:** `filematcher` command fails after pip install
**Why it happens:** pyproject.toml entry point path wrong
**How to avoid:** Use `filematcher.cli:main` (module path, not file path)
**Warning signs:** `ModuleNotFoundError` when running installed command

### Pitfall 4: Circular Import from file_matcher.py
**What goes wrong:** `ImportError` when cli.py tries to import helpers
**Why it happens:** cli.py imports from filematcher modules which might import from file_matcher.py
**How to avoid:** cli.py only imports from filematcher.* modules, never from file_matcher
**Warning signs:** Import loops during module loading

### Pitfall 5: __main__.py Import Path
**What goes wrong:** `python -m filematcher` fails after cli.py extraction
**Why it happens:** __main__.py still imports from `filematcher` package-level main
**How to avoid:** Update __main__.py to import directly from `filematcher.cli`
**Warning signs:** `AttributeError: module 'filematcher' has no attribute 'main'`

### Pitfall 6: Helper Function Dependencies
**What goes wrong:** main() calls helpers that still live in file_matcher.py
**Why it happens:** Not all helper functions moved to cli.py
**How to avoid:** Move ALL helper functions used by main(): `confirm_execution`, `build_file_hash_lookup`, `get_cross_fs_for_hardlink`, `get_cross_fs_count`, `build_file_sizes`, `build_log_flags`
**Warning signs:** NameError for helper functions during execution

## Code Examples

### cli.py Module Structure
```python
# filematcher/cli.py
"""Command-line interface for File Matcher.

This module provides:
- main(): CLI entry point (returns exit code)
- confirm_execution(): User confirmation prompt
- Helper functions for building data structures
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

# Import from sibling modules (all extracted)
from filematcher.colors import ColorConfig, determine_color_mode
from filematcher.hashing import get_file_hash
from filematcher.filesystem import (
    is_in_directory, check_cross_filesystem, filter_hardlinked_duplicates
)
from filematcher.actions import (
    format_file_size,
    create_audit_logger, write_log_header, write_log_footer, log_operation,
    execute_all_actions, determine_exit_code
)
from filematcher.formatters import (
    TextActionFormatter, JsonActionFormatter,
    SpaceInfo, calculate_space_savings,
    format_confirmation_prompt, PREVIEW_BANNER, EXECUTE_BANNER
)
from filematcher.directory import (
    find_matching_files, select_master_file
)

logger = logging.getLogger(__name__)


def confirm_execution(skip_confirm: bool = False, prompt: str = "Proceed? [y/N] ") -> bool:
    """Prompt user for Y/N confirmation before executing changes."""
    if skip_confirm:
        return True
    if not sys.stdin.isatty():
        print("Non-interactive mode detected. Use --yes to skip confirmation.", file=sys.stderr)
        return False
    response = input(prompt).strip().lower()
    return response in ('y', 'yes')


def build_file_hash_lookup(matches: dict[str, tuple[list[str], list[str]]]) -> dict[str, str]:
    """Build a mapping of file paths to their content hashes."""
    lookup: dict[str, str] = {}
    for file_hash, (files1, files2) in matches.items():
        for f in files1 + files2:
            lookup[f] = file_hash
    return lookup


# ... other helper functions ...


def main() -> int:
    """Main entry point. Returns 0 on success, 1 on error."""
    # Argument parser setup
    parser = argparse.ArgumentParser(description='Find files with identical content across two directories.')
    # ... argument definitions ...

    # Configure logging
    # ... logger configuration ...

    # Main workflow
    # ... find matches, format output, execute actions ...

    return 0
```

### Updated __init__.py Re-exports
```python
# filematcher/__init__.py (additions/changes)

# Import from cli submodule (extracted module)
from filematcher.cli import (
    main,
    confirm_execution,
    build_file_hash_lookup,
    get_cross_fs_for_hardlink,
    get_cross_fs_count,
    build_file_sizes,
    build_log_flags,
)

# Remove these from __getattr__ lazy loader (now directly imported)
```

### Updated __main__.py
```python
# filematcher/__main__.py (updated)
"""Entry point for python -m filematcher."""
import sys
from filematcher.cli import main

if __name__ == "__main__":
    sys.exit(main())
```

### Updated pyproject.toml
```toml
[project.scripts]
filematcher = "filematcher.cli:main"

[tool.setuptools]
packages = ["filematcher"]
# Remove py-modules = ["file_matcher"] if still present
```

### Backward-Compat file_matcher.py (Final State)
```python
# file_matcher.py (becomes thin wrapper)
"""
File Matcher - Backward compatibility wrapper.

This script is preserved for backward compatibility.
The implementation has moved to the filematcher package.

Usage (all equivalent):
    python file_matcher.py <args>
    python -m filematcher <args>
    filematcher <args>  # after pip install
"""
from __future__ import annotations

# Re-export everything from the filematcher package
from filematcher import *
from filematcher.cli import main

if __name__ == "__main__":
    import sys
    sys.exit(main())
```

## Extraction Checklist

### CLI Module (`cli.py`)
Must include:
- [ ] `confirm_execution()` function
- [ ] `build_file_hash_lookup()` function
- [ ] `get_cross_fs_for_hardlink()` function
- [ ] `get_cross_fs_count()` function
- [ ] `build_file_sizes()` function
- [ ] `build_log_flags()` function
- [ ] `main()` function (full implementation)
- [ ] Module-level logger: `logger = logging.getLogger(__name__)`

Dependencies:
- Python stdlib: argparse, logging, os, sys, pathlib
- Internal: filematcher.colors, filematcher.hashing, filematcher.filesystem, filematcher.actions, filematcher.formatters, filematcher.directory

### Entry Point Updates
- [ ] pyproject.toml: `filematcher = "filematcher.cli:main"`
- [ ] __main__.py: import from `filematcher.cli`
- [ ] __init__.py: re-export cli symbols

### Test Compatibility
Tests that import CLI-related symbols from `file_matcher`:
- `test_cli.py`: main, execute_action, is_hardlink_to
- `test_safe_defaults.py`: main, PREVIEW_BANNER, EXECUTE_BANNER, confirm_execution
- `test_master_directory.py`: main
- `test_json_output.py`: main

All must continue to work via `from file_matcher import X` after extraction.

## MOD-07 Status

**MOD-07 (Extract audit logging to `filematcher/logging.py`)** was originally planned but the implementation decision in Phase 13 combined audit logging with action execution in `filematcher/actions.py`. This is a valid architectural choice:

**Current state (actions.py contains):**
- `create_audit_logger()`
- `write_log_header()`
- `log_operation()`
- `write_log_footer()`

**Success criterion adjustment:**
- Original: `from filematcher.logging import create_audit_logger` works
- Actual: `from filematcher import create_audit_logger` works (via re-export from actions.py)

**Options:**
1. **Accept current structure** - MOD-07 is satisfied via actions.py, no separate logging.py needed
2. **Create re-export shim** - `filematcher/logging.py` that re-exports from actions.py (for literal requirement compliance)

**Recommendation:** Option 1 - accept current structure. The audit logging functions are properly extracted and accessible. Creating a separate module adds complexity without benefit.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single file_matcher.py | filematcher package with modules | This refactoring | Better maintainability |
| py-modules in setup | packages in pyproject.toml | Modern packaging | Standard practice |

**Deprecated/outdated:**
- setup.py for simple packages (use pyproject.toml)
- py-modules when you have a package directory

## Open Questions

1. **Should file_matcher.py become a pure re-export wrapper?**
   - What we know: After cli.py extraction, file_matcher.py has no unique code
   - What's unclear: Whether to keep shebang and `if __name__ == "__main__"` block
   - Recommendation: Keep both for backward compat (`python file_matcher.py` must work)

2. **Should we create filematcher/logging.py as re-export shim?**
   - What we know: Audit logging is in actions.py and works fine
   - What's unclear: Whether literal requirement compliance matters
   - Recommendation: Skip the shim, update success criteria to match reality

3. **How should pyproject.toml handle both file_matcher.py and filematcher/ package?**
   - What we know: setuptools can handle both
   - What's unclear: Whether both are needed in pyproject.toml
   - Recommendation: List `packages = ["filematcher"]` and `py-modules = ["file_matcher"]`

## Sources

### Primary (HIGH confidence)
- Codebase analysis: `file_matcher.py` lines 92-646 (remaining functions to extract)
- Codebase analysis: `filematcher/actions.py` (audit logging already extracted)
- Codebase analysis: `pyproject.toml` (current entry point configuration)
- Phase 13 documentation: `13-02-PLAN.md` (shows audit logging in actions.py)
- Python Packaging Guide: pyproject.toml entry points

### Secondary (MEDIUM confidence)
- setuptools documentation for entry_points configuration

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Python stdlib only, well-documented patterns
- Architecture: HIGH - Follows established Phase 12-14 patterns
- Pitfalls: HIGH - Based on actual codebase analysis and Phase 13 learnings

**Research date:** 2026-01-27
**Valid until:** 90 days (Python packaging patterns are stable)

## Dependency Graph Summary (Final State)

```
filematcher/
    colors.py       [LEAF] - no internal deps
    hashing.py      [LEAF] - no internal deps
    filesystem.py   [LEAF] - no internal deps
    actions.py      -> filesystem.py (includes audit logging)
    formatters.py   -> colors.py, actions.py
    directory.py    -> hashing.py, actions.py, filesystem.py
    cli.py          -> colors, hashing, filesystem, actions, formatters, directory [NEW]
    __init__.py     -> all modules (re-exports)
    __main__.py     -> cli.py

file_matcher.py     -> filematcher/* (backward compat wrapper)
```

No cycles exist in this dependency graph.
