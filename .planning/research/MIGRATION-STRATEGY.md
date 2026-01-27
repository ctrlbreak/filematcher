# Architecture Research: Package Migration Strategy

**Domain:** Python package refactoring (single file to package structure)
**Researched:** 2026-01-27
**Focus:** Minimizing risk while maintaining test coverage during refactoring

## Executive Summary

File Matcher is a 2,843-line single-file CLI tool (`file_matcher.py`) with 217 tests across 13 test modules. Refactoring to a package structure requires careful planning to:

1. Maintain backward compatibility for existing imports
2. Preserve `python file_matcher.py` direct invocation
3. Keep the `filematcher` console script working via pip install
4. Never break tests during migration

**Recommendation:** Use the **Facade Pattern with Re-export** approach - keep `file_matcher.py` as a compatibility shim that re-exports from the new package structure.

## Current State Analysis

### Single File Structure

```
file_matcher.py (2,843 lines)
├── ANSI Color Constants (lines 32-51)
├── Color Configuration (lines 54-175)
│   ├── ColorMode enum
│   ├── ColorConfig class
│   └── strip_ansi(), visible_len(), terminal_rows_for_line()
├── Structured Output Types (lines 200-227)
│   ├── GroupLine dataclass
│   └── SpaceInfo dataclass
├── Color Helper Functions (lines 229-345)
│   ├── colorize(), green(), yellow(), red(), cyan(), dim(), bold()
│   ├── render_group_line()
│   └── determine_color_mode()
├── Output Formatter Classes (lines 351-1186)
│   ├── ActionFormatter (ABC)
│   ├── JsonActionFormatter
│   └── TextActionFormatter
├── CLI Helpers (lines 1188-1326)
│   ├── confirm_execution()
│   ├── is_in_directory()
│   ├── select_oldest()
│   ├── build_* helper functions
│   └── select_master_file()
├── Formatting Functions (lines 1373-1636)
│   ├── format_group_lines()
│   ├── format_duplicate_group()
│   ├── format_confirmation_prompt()
│   ├── format_statistics_footer()
│   └── calculate_space_savings()
├── Filesystem Operations (lines 1638-1761)
│   ├── get_device_id()
│   ├── check_cross_filesystem()
│   ├── is_hardlink_to(), is_symlink_to()
│   └── filter_hardlinked_duplicates()
├── Action Execution (lines 1764-1998)
│   ├── safe_replace_with_link()
│   ├── execute_action()
│   ├── determine_exit_code()
│   └── execute_all_actions()
├── Utility Functions (lines 2001-2175)
│   ├── format_file_size()
│   └── Audit logging functions
├── Hashing Functions (lines 2177-2343)
│   ├── create_hasher()
│   ├── get_file_hash()
│   ├── get_sparse_hash()
│   └── index_directory()
├── Core Comparison (lines 2345-2402)
│   └── find_matching_files()
└── CLI Entry Point (lines 2405-end)
    └── main()
```

### Test Import Patterns

All 13 test modules import directly from `file_matcher`:

```python
# test_file_hashing.py
from file_matcher import get_file_hash, format_file_size

# test_cli.py
from file_matcher import main, execute_action, is_hardlink_to

# test_actions.py (most comprehensive)
from file_matcher import (
    is_hardlink_to, safe_replace_with_link, execute_action,
    execute_all_actions, determine_exit_code, create_audit_logger,
    log_operation, write_log_header, write_log_footer,
)

# test_directory_operations.py
from file_matcher import (
    index_directory, find_matching_files, get_file_hash,
    is_symlink_to, execute_action, is_hardlink_to,
    filter_hardlinked_duplicates, main
)

# test_safe_defaults.py
from file_matcher import main, PREVIEW_BANNER, EXECUTE_BANNER, confirm_execution
```

**27 unique symbols** are imported across test files:
- Functions: `main`, `get_file_hash`, `format_file_size`, `get_sparse_hash`, `find_matching_files`, `index_directory`, `execute_action`, `is_hardlink_to`, `is_symlink_to`, `safe_replace_with_link`, `execute_all_actions`, `determine_exit_code`, `create_audit_logger`, `log_operation`, `write_log_header`, `write_log_footer`, `filter_hardlinked_duplicates`, `confirm_execution`, `check_cross_filesystem`
- Constants: `PREVIEW_BANNER`, `EXECUTE_BANNER`
- Classes: `ColorConfig`, `ColorMode` (used indirectly via mocking)

### Entry Point Configuration

Current `pyproject.toml`:
```toml
[project.scripts]
filematcher = "file_matcher:main"

[tool.setuptools]
py-modules = ["file_matcher"]
```

## Migration Approach: Facade Pattern with Re-export

### Why This Approach

| Approach | Risk | Test Impact | Backward Compat | Complexity |
|----------|------|-------------|-----------------|------------|
| Big Bang | HIGH | All tests break initially | NONE | Low |
| Incremental Module Creation | MEDIUM | Tests need updates | NONE | Medium |
| **Facade with Re-export** | LOW | No test changes | FULL | Medium |
| src/ Layout | MEDIUM | Tests need path updates | Partial | High |

The Facade Pattern keeps `file_matcher.py` as the public API while internally organizing code into a package. Tests and existing scripts continue working without modification.

### Target Structure

```
filematcher/                    # New package directory
├── __init__.py                 # Re-exports all public symbols
├── color.py                    # ColorMode, ColorConfig, color helpers
├── formatters/
│   ├── __init__.py
│   ├── base.py                 # ActionFormatter ABC
│   ├── text.py                 # TextActionFormatter
│   └── json.py                 # JsonActionFormatter
├── hashing.py                  # get_file_hash, get_sparse_hash, index_directory
├── comparison.py               # find_matching_files
├── actions.py                  # execute_action, safe_replace_with_link, etc.
├── filesystem.py               # is_hardlink_to, is_symlink_to, etc.
├── logging.py                  # Audit logging functions
├── formatting.py               # format_* functions, GroupLine, SpaceInfo
├── utils.py                    # format_file_size, helpers
└── cli.py                      # main(), argparse setup

file_matcher.py                 # Compatibility shim (re-exports from filematcher)
```

### Compatibility Shim Pattern

After migration, `file_matcher.py` becomes:

```python
#!/usr/bin/env python3
"""
File Matcher - Compatibility module.

This module maintains backward compatibility for scripts that import from file_matcher.
The actual implementation has moved to the filematcher package.

Usage:
    # These all continue to work:
    python file_matcher.py dir1 dir2
    from file_matcher import main, get_file_hash
    filematcher dir1 dir2  # via pip install
"""

# Re-export all public symbols from package
from filematcher import (
    # Entry point
    main,

    # Hashing
    get_file_hash,
    get_sparse_hash,
    create_hasher,

    # Directory operations
    index_directory,
    find_matching_files,

    # Filesystem operations
    is_hardlink_to,
    is_symlink_to,
    filter_hardlinked_duplicates,
    check_cross_filesystem,
    get_device_id,

    # Action execution
    execute_action,
    safe_replace_with_link,
    execute_all_actions,
    determine_exit_code,

    # Audit logging
    create_audit_logger,
    log_operation,
    write_log_header,
    write_log_footer,

    # Formatting
    format_file_size,
    format_duplicate_group,
    format_confirmation_prompt,
    format_statistics_footer,
    calculate_space_savings,
    format_group_lines,
    render_group_line,

    # UI helpers
    confirm_execution,

    # Constants
    PREVIEW_BANNER,
    EXECUTE_BANNER,

    # Classes
    ColorMode,
    ColorConfig,
    GroupLine,
    SpaceInfo,
    ActionFormatter,
    TextActionFormatter,
    JsonActionFormatter,
)

# Support direct execution: python file_matcher.py dir1 dir2
if __name__ == "__main__":
    import sys
    sys.exit(main())
```

### Entry Point Changes

Update `pyproject.toml`:

```toml
[project.scripts]
filematcher = "filematcher:main"  # Points to package

[tool.setuptools]
packages = ["filematcher", "filematcher.formatters"]
py-modules = ["file_matcher"]  # Keep compatibility module
```

## Suggested Build Order

### Phase 1: Create Package Structure (No Code Movement)

**Goal:** Create empty package structure, verify imports work.

**Steps:**
1. Create `filematcher/` directory
2. Create `filematcher/__init__.py` that imports from `file_matcher.py`
3. Verify: `from filematcher import main` works
4. Update `pyproject.toml` to include package

**Test verification:** All 217 tests pass (no imports changed)

**Rollback:** Delete `filematcher/` directory

```python
# filematcher/__init__.py (Phase 1)
"""File Matcher package - transitional structure."""
# During migration, import from old module
from file_matcher import *
```

### Phase 2: Extract Color Module (Low Coupling)

**Goal:** Move color-related code to package, verify re-exports work.

**Why first:** Color module has minimal dependencies (only stdlib imports).

**Steps:**
1. Create `filematcher/color.py` with ColorMode, ColorConfig, color helpers
2. Update `filematcher/__init__.py` to import from color module
3. Update `file_matcher.py` to import from filematcher.color
4. Run tests

**Symbols moved:**
- `ColorMode`
- `ColorConfig`
- `strip_ansi()`, `visible_len()`, `terminal_rows_for_line()`
- `colorize()`, `green()`, `yellow()`, `red()`, `cyan()`, `dim()`, `bold()`
- `bold_yellow()`, `bold_green()`
- ANSI constants

**Test verification:** All tests pass (imports unchanged, re-exports work)

**Rollback:** Revert color.py changes, restore inline code in file_matcher.py

### Phase 3: Extract Hashing Module

**Goal:** Move hashing functions to package.

**Why next:** Hashing has clear boundaries, used by multiple modules.

**Steps:**
1. Create `filematcher/hashing.py`
2. Move `create_hasher()`, `get_file_hash()`, `get_sparse_hash()`, `index_directory()`
3. Update imports in `file_matcher.py`
4. Run tests

**Dependencies to handle:**
- `format_file_size()` - keep in file_matcher.py initially, or move to utils first
- `logger` - pass as parameter or use module-level logger

**Test verification:** `test_file_hashing.py`, `test_fast_mode.py` pass

### Phase 4: Extract Filesystem Module

**Goal:** Move filesystem operations to package.

**Steps:**
1. Create `filematcher/filesystem.py`
2. Move `is_hardlink_to()`, `is_symlink_to()`, `filter_hardlinked_duplicates()`, `check_cross_filesystem()`, `get_device_id()`
3. Update imports

**Test verification:** `test_directory_operations.py` passes

### Phase 5: Extract Actions Module

**Goal:** Move action execution to package.

**Steps:**
1. Create `filematcher/actions.py`
2. Move `safe_replace_with_link()`, `execute_action()`, `execute_all_actions()`, `determine_exit_code()`
3. Update imports

**Dependencies:**
- `is_hardlink_to()`, `is_symlink_to()` from filesystem module
- `logger` - use module-level or pass as parameter

**Test verification:** `test_actions.py` passes

### Phase 6: Extract Formatters

**Goal:** Move formatter classes to package.

**Steps:**
1. Create `filematcher/formatters/` subpackage
2. Move `ActionFormatter` to `base.py`
3. Move `TextActionFormatter` to `text.py`
4. Move `JsonActionFormatter` to `json.py`
5. Update imports

**Dependencies:**
- Color helpers (from color module)
- Format helpers (keep in file_matcher.py initially)

**Test verification:** `test_json_output.py`, `test_color_output.py` pass

### Phase 7: Extract Formatting Functions

**Goal:** Move format_* functions.

**Steps:**
1. Create `filematcher/formatting.py`
2. Move `GroupLine`, `SpaceInfo`, `format_duplicate_group()`, `format_statistics_footer()`, `format_confirmation_prompt()`, `format_group_lines()`, `calculate_space_savings()`, `render_group_line()`
3. Update imports

**Test verification:** `test_output_unification.py` passes

### Phase 8: Extract Comparison Module

**Goal:** Move core comparison logic.

**Steps:**
1. Create `filematcher/comparison.py`
2. Move `find_matching_files()`
3. Update imports

**Dependencies:**
- `index_directory()` from hashing module

**Test verification:** `test_real_directories.py` passes

### Phase 9: Extract Utils and Logging

**Goal:** Move utility functions and audit logging.

**Steps:**
1. Create `filematcher/utils.py` with `format_file_size()`, helper functions
2. Create `filematcher/logging.py` with audit logging functions
3. Update imports

**Test verification:** Full test suite passes

### Phase 10: Create CLI Module and Finalize

**Goal:** Move main() and CLI setup to package.

**Steps:**
1. Create `filematcher/cli.py`
2. Move `main()` function
3. Update `file_matcher.py` to be pure compatibility shim
4. Update `pyproject.toml` entry points

**Test verification:** `test_cli.py`, `test_safe_defaults.py`, `test_master_directory.py` pass

### Phase 11: Clean Up and Verify

**Goal:** Ensure clean package structure, all tests pass.

**Steps:**
1. Add `__all__` to all modules
2. Verify all re-exports work
3. Run full test suite
4. Manual smoke test of CLI

## Test Migration Strategy

### Zero Test Changes During Migration

The key insight is that **tests should not need modification** during migration because:

1. `file_matcher.py` continues to exist as compatibility shim
2. All public symbols are re-exported from the shim
3. Import statements `from file_matcher import X` continue to work

### Verification Protocol

After each phase:

```bash
# Run full test suite
python3 run_tests.py

# Verify specific module tests pass
python3 -m tests.test_file_hashing
python3 -m tests.test_cli

# Verify direct invocation works
python file_matcher.py test_dir1 test_dir2

# Verify pip install works
pip install -e .
filematcher test_dir1 test_dir2
```

### Test Update (Optional, Phase 12+)

After migration is complete, tests can be optionally updated to import from package:

```python
# Before (works forever via compatibility shim)
from file_matcher import get_file_hash

# After (optional modernization)
from filematcher.hashing import get_file_hash
```

This is a future enhancement, not required for migration.

## Entry Point Configuration Changes

### Current Configuration

```toml
# pyproject.toml
[project.scripts]
filematcher = "file_matcher:main"

[tool.setuptools]
py-modules = ["file_matcher"]
```

### Final Configuration

```toml
# pyproject.toml
[project.scripts]
filematcher = "filematcher.cli:main"

[tool.setuptools]
packages = ["filematcher", "filematcher.formatters"]
py-modules = ["file_matcher"]  # Keep for backward compatibility

[tool.setuptools.package-data]
filematcher = ["py.typed"]
```

### Transitional Configuration (During Migration)

```toml
# pyproject.toml (Phases 1-9)
[project.scripts]
filematcher = "file_matcher:main"  # Still points to shim

[tool.setuptools]
packages = ["filematcher", "filematcher.formatters"]
py-modules = ["file_matcher"]
```

## Rollback Strategy

### Per-Phase Rollback

Each phase can be rolled back independently:

1. **Git revert:** Each phase should be a single commit
2. **Module removal:** Delete newly created module file
3. **Import restoration:** Restore inline code in file_matcher.py
4. **Test verification:** Run tests to confirm rollback success

### Emergency Full Rollback

If migration goes badly wrong:

```bash
# Revert to pre-migration state
git checkout <pre-migration-commit> -- file_matcher.py pyproject.toml
rm -rf filematcher/

# Verify
python3 run_tests.py
```

### Rollback Triggers

Rollback if:
- Any test fails after a phase
- Direct invocation (`python file_matcher.py`) breaks
- pip install breaks
- Import errors from external consumers

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Circular imports | Medium | High | Careful dependency ordering, use TYPE_CHECKING |
| Missing re-export | Low | Medium | Comprehensive __all__ lists, test verification |
| Entry point breaks | Low | High | Keep shim, test both invocation methods |
| Test failures | Low | Medium | Run tests after each phase |
| Import path confusion | Medium | Low | Clear documentation, deprecation warnings |

## Patterns to Follow

### 1. Re-export Pattern

```python
# filematcher/__init__.py
from filematcher.hashing import get_file_hash, get_sparse_hash
from filematcher.actions import execute_action

__all__ = [
    'get_file_hash',
    'get_sparse_hash',
    'execute_action',
    # ... all public symbols
]
```

### 2. TYPE_CHECKING for Circular Imports

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from filematcher.color import ColorConfig
```

### 3. Module-Level Logger

```python
# filematcher/hashing.py
import logging

logger = logging.getLogger(__name__)
```

### 4. Lazy Import for Performance

```python
# filematcher/__init__.py
def __getattr__(name):
    if name == 'JsonActionFormatter':
        from filematcher.formatters.json import JsonActionFormatter
        return JsonActionFormatter
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
```

## Anti-Patterns to Avoid

### 1. Breaking the Shim

DON'T remove or rename `file_matcher.py` until all external consumers have migrated.

### 2. Changing Public API

DON'T change function signatures during migration. This is a structural refactor, not an API change.

### 3. Moving Tests

DON'T move tests into the package directory. Tests should remain in `tests/` and import from the public API.

### 4. Partial Re-exports

DON'T selectively re-export - if a symbol was public before, it must remain public.

### 5. Big Bang Commits

DON'T combine multiple phases into one commit. Each phase should be atomic and revertible.

## Success Criteria

Migration is complete when:

- [ ] All 217 tests pass without modification
- [ ] `python file_matcher.py dir1 dir2` works
- [ ] `filematcher dir1 dir2` works after pip install
- [ ] `from file_matcher import X` works for all 27 public symbols
- [ ] `from filematcher import X` works for all 27 public symbols
- [ ] No circular import errors
- [ ] Package structure is clean and logical
- [ ] Each module has clear, single responsibility
- [ ] `__all__` defined in all modules

## Sources

Research informed by:

- [Structuring Your Project - The Hitchhiker's Guide to Python](https://docs.python-guide.org/writing/structure/) - Python project layout best practices
- [Python Package Structure - pyOpenSci](https://www.pyopensci.org/python-package-guide/package-structure-code/python-package-structure.html) - Modern package structure recommendations
- [Python Packaging Best Practices 2026](https://dasroot.net/posts/2026/01/python-packaging-best-practices-setuptools-poetry-hatch/) - Current packaging tools comparison
- [Why Refactoring? How to Restructure Python Package?](https://hackernoon.com/why-refactoring-how-to-restructure-python-package-51b89aa91987) - Migration strategies
- [PEP 387 - Backwards Compatibility Policy](https://peps.python.org/pep-0387/) - Python backward compatibility standards
- [Packaging Python Projects - PyPA](https://packaging.python.org/tutorials/packaging-projects/) - Official packaging tutorial

---

*Research completed: 2026-01-27*
*Focus: Package migration strategy for single-file CLI tool*
