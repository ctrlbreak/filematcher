# Stack Research: Python Package Refactoring

**Project:** File Matcher CLI refactoring from single-file to package structure
**Researched:** 2026-01-27
**Confidence:** HIGH (authoritative sources consulted)

## Recommendation

**Use flat layout with `pyproject.toml` entry points.** Do NOT use src layout.

**Rationale:** For this project, flat layout is the better choice because:

1. **Existing tests use `sys.path` manipulation** - The current `tests/__init__.py` adds the parent directory to `sys.path`. With flat layout, this continues to work. Src layout would require rewriting test imports.

2. **Backward compatibility for `python file_matcher.py`** - Flat layout allows keeping `file_matcher.py` as a thin wrapper in the project root. Src layout would complicate this.

3. **No complex build requirements** - The project is pure Python stdlib. The src layout's protection against "importing the wrong version" is less critical when there's no compilation step.

4. **Simpler migration path** - Flat layout means moving code into `filematcher/` directory without touching the test infrastructure significantly.

The src layout is generally recommended for libraries intended for PyPI distribution where import isolation is critical. For a CLI tool with existing test infrastructure, flat layout minimizes disruption.

## Package Structure

### Recommended: Flat Layout

```
filematcher/
├── pyproject.toml              # Already exists, update for package discovery
├── file_matcher.py             # KEEP as backward-compat wrapper (thin)
├── filematcher/                # NEW package directory
│   ├── __init__.py             # Public API exports + __version__
│   ├── __main__.py             # Enable `python -m filematcher`
│   ├── cli.py                  # main() and argparse logic
│   ├── core.py                 # Core matching logic
│   ├── hashing.py              # Hash functions (get_file_hash, get_sparse_hash)
│   ├── actions.py              # Action execution (hardlink/symlink/delete)
│   ├── output.py               # Formatters (TextActionFormatter, JsonActionFormatter)
│   ├── color.py                # ColorConfig, color helper functions
│   ├── logging.py              # Audit logging functions
│   └── filesystem.py           # Filesystem helpers (is_hardlink_to, etc.)
├── tests/                      # Keep existing structure
│   ├── __init__.py
│   └── ...
├── test_dir1/                  # Keep existing fixtures
├── test_dir2/
└── complex_test/
```

### Why NOT src Layout

| Factor | Flat | Src | Winner |
|--------|------|-----|--------|
| Existing test compatibility | Works as-is | Requires test rewrite | Flat |
| `python file_matcher.py` compat | Trivial wrapper | Complex path manipulation | Flat |
| Import isolation | Adequate with proper install | Strong | Tie for this project |
| Migration complexity | Lower | Higher | Flat |

### Alternative: src Layout (NOT recommended)

```
filematcher/
├── pyproject.toml
├── file_matcher.py             # Wrapper (harder to make work)
├── src/
│   └── filematcher/
│       ├── __init__.py
│       └── ...
└── tests/
    └── ...                     # Would need conftest.py or editable install
```

src layout would require all test runs to use `pip install -e .` first, which is more ceremony than this project needs.

## Entry Points

### pyproject.toml Configuration (Updated)

The existing `pyproject.toml` needs updates for package discovery:

```toml
[project]
name = "filematcher"
version = "1.1.0"
# ... existing metadata unchanged ...

[project.scripts]
filematcher = "filematcher.cli:main"

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[tool.setuptools]
packages = ["filematcher"]
# Remove py-modules = ["file_matcher"] after migration

[tool.pytest.ini_options]
testpaths = ["tests"]
```

### Key Changes from Current

| Current | After Refactor | Reason |
|---------|----------------|--------|
| `[project.scripts] filematcher = "file_matcher:main"` | `filematcher = "filematcher.cli:main"` | Points to package module |
| `[tool.setuptools] py-modules = ["file_matcher"]` | `packages = ["filematcher"]` | Package discovery instead of single module |

### Entry Point Pattern

The entry point should call a function that returns an exit code:

```python
# filematcher/cli.py
def main() -> int:
    """CLI entry point. Returns exit code."""
    # ... argparse and main logic ...
    return 0  # or 1 for error, 2 for partial failure
```

Console scripts automatically pass the return value to `sys.exit()`.

## Import Patterns

### Recommendation: Relative Imports Within Package

**Within the `filematcher/` package, use relative imports:**

```python
# filematcher/cli.py
from .core import find_matching_files, index_directory
from .hashing import get_file_hash
from .output import TextActionFormatter, JsonActionFormatter
from .color import ColorConfig, ColorMode
```

**Rationale:**
- Relative imports make the package self-contained
- Easier to rename/move the package later
- PEP 8 allows relative imports when they reduce verbosity
- The package is small enough that relative imports stay readable

### Public API in `__init__.py`

```python
# filematcher/__init__.py
"""File Matcher - Find and deduplicate files with identical content."""

__version__ = "1.1.0"
__author__ = "Patrick Myles"

# Public API exports (for programmatic use)
from .core import find_matching_files, index_directory
from .hashing import get_file_hash, get_sparse_hash
from .cli import main

__all__ = [
    "__version__",
    "find_matching_files",
    "index_directory",
    "get_file_hash",
    "get_sparse_hash",
    "main",
]
```

**Keep `__all__` focused.** Only export what external code might actually use. Internal implementation details (formatters, color helpers) stay internal.

### `__main__.py` for `python -m filematcher`

```python
# filematcher/__main__.py
"""Enable `python -m filematcher`."""
import sys
from .cli import main

sys.exit(main())
```

**No `if __name__ == '__main__'` check needed** in `__main__.py` - this file only runs when invoked as a module.

## Backward Compatibility

### Wrapper Pattern for `python file_matcher.py`

Keep `file_matcher.py` in the project root as a thin wrapper:

```python
#!/usr/bin/env python3
"""
Backward compatibility wrapper.

This file maintains compatibility with:
  python file_matcher.py dir1 dir2 [options]

For new usage, prefer:
  filematcher dir1 dir2 [options]
  python -m filematcher dir1 dir2 [options]
"""
import sys
from filematcher.cli import main

if __name__ == "__main__":
    sys.exit(main())
```

**Size:** ~10 lines vs current 2,843 lines.

### Three Invocation Methods (All Supported)

| Method | How It Works | Status |
|--------|--------------|--------|
| `filematcher dir1 dir2` | Console script entry point | Already works |
| `python -m filematcher dir1 dir2` | `__main__.py` | NEW after refactor |
| `python file_matcher.py dir1 dir2` | Thin wrapper script | MAINTAINED for compat |

### Test Compatibility

The existing tests import from `file_matcher`:

```python
# Current test imports
from file_matcher import get_file_hash, find_matching_files, main
```

**Two approaches to maintain compatibility:**

**Option A: Alias in wrapper (simpler)**
```python
# file_matcher.py (updated wrapper)
from filematcher import *  # Re-export everything
from filematcher.cli import main
```

Then existing tests work unchanged.

**Option B: Update test imports (cleaner)**
```python
# tests/test_file_hashing.py
from filematcher import get_file_hash  # Changed from file_matcher
```

**Recommendation: Option B** - Clean imports are better long-term. The test updates are mechanical (find/replace) and can be done in one commit.

## What NOT to Add

### Do NOT add type stubs or py.typed marker

The codebase already has inline type hints (`from __future__ import annotations`). Adding `py.typed` marker would promise PEP 561 compliance which isn't necessary for a CLI tool.

### Do NOT add setuptools-scm or other version management

Current manual versioning (`__version__ = "1.1.0"`) is fine for this project size. Adding SCM-based versioning adds complexity without benefit.

### Do NOT add namespace packages

The project has a single package (`filematcher`). Namespace packages are for splitting a package across multiple distributions.

### Do NOT add `setup.py`

The project already uses `pyproject.toml` with setuptools backend. Modern Python (3.9+) doesn't need `setup.py` for pure Python packages.

### Do NOT add external dependencies

The zero-dependency constraint is a feature. Resist adding:
- `click` (argparse works fine)
- `rich` (the custom color system works fine)
- `attrs`/`pydantic` (dataclasses work fine)

### Do NOT use absolute imports within the package

Within `filematcher/`, prefer relative imports (`.core`, `.hashing`). This keeps the package self-contained.

## Module Split Recommendation

Based on the current 2,843-line `file_matcher.py`, here's the recommended module breakdown:

| Module | Lines (est.) | Contents |
|--------|--------------|----------|
| `cli.py` | ~300 | `main()`, argparse setup, CLI flow |
| `core.py` | ~400 | `find_matching_files()`, `index_directory()`, `select_master_file()` |
| `hashing.py` | ~150 | `get_file_hash()`, `get_sparse_hash()`, hash algorithm selection |
| `actions.py` | ~300 | `execute_action()`, `execute_all_actions()`, `safe_replace_with_link()` |
| `output.py` | ~400 | `ActionFormatter`, `TextActionFormatter`, `JsonActionFormatter` |
| `color.py` | ~150 | `ColorMode`, `ColorConfig`, color helpers (`green()`, `red()`, etc.) |
| `logging.py` | ~150 | `create_audit_logger()`, `log_operation()`, header/footer |
| `filesystem.py` | ~200 | `is_hardlink_to()`, `is_symlink_to()`, `check_cross_filesystem()` |
| `__init__.py` | ~30 | Version, public API exports |
| `__main__.py` | ~10 | Module invocation support |

**Total: ~2,090 lines** (reduction from shared constants, cleaner organization)

## Sources

### Authoritative (HIGH confidence)
- [Python Packaging User Guide: src layout vs flat layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)
- [Python Packaging User Guide: Writing pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
- [Python docs: __main__ module](https://docs.python.org/3/library/__main__.html)
- [setuptools: Package Discovery](https://setuptools.pypa.io/en/latest/userguide/package_discovery.html)
- [setuptools: Entry Points](https://setuptools.pypa.io/en/latest/userguide/entry_point.html)

### Community Best Practices (MEDIUM confidence)
- [Real Python: Absolute vs Relative Imports](https://realpython.com/absolute-vs-relative-python-imports/)
- [Real Python: Python __init__.py](https://realpython.com/python-init-py/)
- [PyOpenSci: Python Package Structure](https://www.pyopensci.org/python-package-guide/package-structure-code/python-package-structure.html)

---
*Research completed: 2026-01-27*
