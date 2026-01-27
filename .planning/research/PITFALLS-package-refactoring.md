# Pitfalls Research: Package Refactoring Risks

**Project:** File Matcher
**Context:** Refactoring single-file CLI (2,455 lines) to package structure
**Researched:** 2026-01-27
**Confidence:** HIGH (verified with official Python packaging documentation)

## Executive Summary

Refactoring a working single-file CLI to a package structure has well-documented pitfalls. The most critical risks for File Matcher are:

1. **Breaking existing imports** - Users who `from file_matcher import get_file_hash` will break
2. **Entry point misconfiguration** - The `filematcher` command stops working
3. **Test discovery failure** - 217 tests stop being discovered
4. **Circular imports** - Splitting into modules creates import loops

This document catalogs pitfalls in order of severity with actionable prevention strategies.

---

## Critical Pitfalls

These mistakes cause immediate breakage or require rewrites.

### 1. Breaking the Public API Import Contract

**Risk:** Users who import from `file_matcher` directly will get `ImportError` or `AttributeError` after restructure.

**Current state:**
```python
# Users can currently do:
from file_matcher import get_file_hash, find_matching_files, main
```

**What breaks:**
When code moves to `filematcher/hashing.py`, the old import path `from file_matcher import get_file_hash` fails because:
- `file_matcher.py` no longer exists (renamed to package)
- `get_file_hash` is now in `filematcher.hashing`, not at package root

**Warning signs:**
- Any external script importing from `file_matcher` fails
- CI pipelines that import functions fail
- Tests using direct imports fail

**Prevention:**
1. **Re-export in `__init__.py`** - Import and re-export all previously public symbols:
   ```python
   # filematcher/__init__.py
   from filematcher.hashing import get_file_hash, get_sparse_hash
   from filematcher.core import find_matching_files
   from filematcher.cli import main

   __all__ = ['get_file_hash', 'get_sparse_hash', 'find_matching_files', 'main']
   ```

2. **Define `__all__`** - Explicitly declare the public API to prevent accidental exposure of internals

3. **Test old import paths** - Add tests that verify `from file_matcher import X` still works

**Phase:** Must be addressed in Phase 1 (initial restructure) - cannot defer

**Sources:**
- [Real Python: Public API Surface](https://realpython.com/ref/best-practices/public-api-surface/)
- [Understanding `__init__.py` in Python Packages](https://leapcell.io/blog/understanding-init-py-in-python-packages)

---

### 2. Entry Point Path Mismatch After Restructure

**Risk:** The `filematcher` console command stops working because pyproject.toml points to wrong location.

**Current state:**
```toml
# pyproject.toml
[project.scripts]
filematcher = "file_matcher:main"
```

**What breaks:**
After restructuring, the module name changes from `file_matcher` (single file) to `filematcher` (package). If pyproject.toml isn't updated, or is updated incorrectly:
- `pip install -e .` succeeds but `filematcher` command fails
- Error: `ModuleNotFoundError: No module named 'file_matcher'`

**Warning signs:**
- `filematcher` command returns "command not found" or module error
- Package installs without error but CLI doesn't work
- Works in development but fails after `pip install`

**Prevention:**
1. **Update entry point immediately** after creating package structure:
   ```toml
   [project.scripts]
   filematcher = "filematcher.cli:main"
   ```

2. **Verify the function exists** at the specified path before release

3. **Test CLI installation**:
   ```bash
   pip install -e .
   filematcher --help  # Must work
   ```

4. **Keep function signature unchanged** - Entry point functions must take no arguments (use argparse internally)

**Phase:** Must be addressed in Phase 1 - entry point is primary interface

**Sources:**
- [Python Packaging: Creating Command Line Tools](https://packaging.python.org/en/latest/guides/creating-command-line-tools/)
- [Setuptools Entry Points Documentation](https://setuptools.pypa.io/en/latest/userguide/entry_point.html)

---

### 3. Circular Import Deadlock

**Risk:** Splitting code into modules creates circular dependencies that cause `ImportError` at runtime.

**How it happens:**
```python
# filematcher/hashing.py
from filematcher.config import HASH_ALGORITHMS  # Needs config

# filematcher/config.py
from filematcher.hashing import get_file_hash  # Needs hashing for validation

# Result: ImportError - partially initialized module
```

**Why this is likely for File Matcher:**
- Color configuration (`ColorConfig`) is used throughout
- Logging configuration touches multiple areas
- Constants (thresholds, algorithms) are referenced across modules

**Warning signs:**
- `ImportError: cannot import name 'X' from partially initialized module`
- Tests pass individually but fail when run together
- Import works in REPL but fails in script

**Prevention:**
1. **Design module hierarchy first** - Draw dependency diagram before coding
   ```
   Constants (no imports from package)
       |
   Config (imports constants only)
       |
   Core functions (imports config, constants)
       |
   CLI (imports everything)
   ```

2. **Extract shared dependencies upward** - Constants and type definitions go in their own module that imports nothing from the package

3. **Use TYPE_CHECKING for type hints only**:
   ```python
   from typing import TYPE_CHECKING
   if TYPE_CHECKING:
       from filematcher.formatters import ActionFormatter
   ```

4. **Test import order** - Add test that imports package from fresh Python:
   ```python
   def test_no_circular_imports():
       import subprocess
       result = subprocess.run(['python', '-c', 'import filematcher'], capture_output=True)
       assert result.returncode == 0
   ```

**Phase:** Must be designed in Phase 1, verified throughout

**Sources:**
- [DataCamp: Python Circular Import](https://www.datacamp.com/tutorial/python-circular-import)
- [Brex Engineering: Avoiding Circular Imports in Python](https://medium.com/brexeng/avoiding-circular-imports-in-python-7c35ec8145ed)

---

### 4. Test Discovery Failure

**Risk:** unittest/pytest stops discovering tests after restructure, silently running 0 tests or subset.

**Current state:**
```python
# tests/__init__.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
```

**What breaks:**
- Path manipulation assumes flat layout, breaks with src layout
- Missing `__init__.py` in test directories breaks unittest discovery
- Import paths in tests reference old module name

**Warning signs:**
- `python -m pytest` runs 0 tests
- `unittest discover` finds fewer tests than expected
- Tests pass locally but fail in CI
- "module not found" errors when running tests

**Prevention:**
1. **Keep `__init__.py` in all test directories** - Required for unittest discovery (Python < 3.14)

2. **Update test imports** to use new package structure:
   ```python
   # Old:
   from file_matcher import main, get_file_hash

   # New:
   from filematcher import main, get_file_hash
   ```

3. **Remove sys.path hacks** after package is pip-installable:
   ```python
   # Delete this from tests/__init__.py after restructure:
   # sys.path.insert(0, ...)
   ```

4. **Verify test count** before and after:
   ```bash
   python -m pytest --collect-only | grep "test session starts" -A 5
   # Must show 217 tests
   ```

5. **Use `pip install -e .`** before running tests (ensures package is importable)

**Phase:** Must be verified immediately after Phase 1

**Sources:**
- [Python unittest documentation](https://docs.python.org/3/library/unittest.html)
- [pytest test discovery](https://docs.pytest.org/en/stable/example/pythoncollection.html)

---

## Medium-Risk Pitfalls

These cause development friction or technical debt but don't break production immediately.

### 5. Relative Import Confusion

**Risk:** Mixing relative and absolute imports causes inconsistent behavior between `python file.py` and `python -m package.file`.

**What breaks:**
```python
# filematcher/hashing.py
from .constants import SPARSE_THRESHOLD  # Relative import

# Running directly fails:
# $ python filematcher/hashing.py
# ImportError: attempted relative import with no known parent package
```

**Warning signs:**
- Code works when installed but not when run from source
- "attempted relative import with no known parent package"
- Tests work, scripts fail (or vice versa)

**Prevention:**
1. **Choose one style and enforce it** - Recommend absolute imports for clarity:
   ```python
   # Preferred:
   from filematcher.constants import SPARSE_THRESHOLD

   # Avoid:
   from .constants import SPARSE_THRESHOLD
   ```

2. **Never run module files directly** - Always use `python -m filematcher.hashing` or installed CLI

3. **Add `__main__.py`** for package-level execution:
   ```python
   # filematcher/__main__.py
   from filematcher.cli import main
   if __name__ == '__main__':
       main()
   ```

**Phase:** Decide import style in Phase 1, enforce throughout

**Sources:**
- [Python Import System Documentation](https://docs.python.org/3/reference/import.html)
- [Built In: ImportError Relative Import Solutions](https://builtin.com/articles/importerror-attempted-relative-import-no-known-parent-package)

---

### 6. Editable Install Breakage

**Risk:** `pip install -e .` stops working after restructure due to PEP 660 changes.

**Context:**
- Legacy editable installs (`setup.py develop`) deprecated in pip 24.2
- Modern editable installs require proper pyproject.toml configuration
- Support for legacy mechanism removed in pip 25.1

**What breaks:**
- Package installs but modules aren't importable
- `AttributeError: module 'filematcher' has no attribute 'main'`
- Works with `pip install .` but not `pip install -e .`

**Warning signs:**
- Editable install succeeds but imports fail
- Different behavior between fresh venv and existing venv
- Works in Python 3.9, fails in Python 3.12

**Prevention:**
1. **Ensure pyproject.toml has build-system**:
   ```toml
   [build-system]
   requires = ["setuptools >= 64"]
   build-backend = "setuptools.build_meta"
   ```

2. **Test editable install in fresh venv**:
   ```bash
   python -m venv test_venv
   source test_venv/bin/activate
   pip install -e .
   python -c "from filematcher import main; print('OK')"
   ```

3. **Clean old artifacts** before testing:
   ```bash
   pip uninstall filematcher
   rm -rf *.egg-info build dist
   ```

**Phase:** Verify in Phase 1, retest after any structural changes

**Sources:**
- [Setuptools: Development Mode](https://setuptools.pypa.io/en/latest/userguide/development_mode.html)
- [pip 24.2 Release Notes on Editable Installs](https://ichard26.github.io/blog/2024/08/whats-new-in-pip-24.2/)

---

### 7. src Layout Migration Pain

**Risk:** Attempting src layout without understanding implications causes confusion.

**Current layout (flat):**
```
filematcher/
  file_matcher.py
  pyproject.toml
  tests/
```

**src layout:**
```
filematcher/
  pyproject.toml
  src/
    filematcher/
      __init__.py
      ...
  tests/
```

**Trade-offs:**
| Aspect | Flat Layout | src Layout |
|--------|-------------|------------|
| Simplicity | Simpler | More complex |
| Accidental imports | Possible | Prevented |
| Run from source | Works | Requires install |
| Test isolation | Weaker | Stronger |

**Warning signs (if choosing src layout):**
- `python -m filematcher` fails from repo root
- Tests import source instead of installed package
- Confusion about which code is running

**Prevention:**
1. **Recommend staying with flat layout** for this project - it's working, team knows it, lower migration risk

2. **If migrating to src layout:**
   - Update pyproject.toml: `[tool.setuptools.packages.find] where = ["src"]`
   - Always `pip install -e .` before running tests
   - Update all documentation

**Phase:** Decision point in Phase 1 - recommend flat layout

**Sources:**
- [Python Packaging: src vs flat layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)
- [PyOpenSci: Python Package Structure](https://www.pyopensci.org/python-package-guide/package-structure-code/python-package-structure.html)

---

### 8. Logger Configuration Collision

**Risk:** Module-level logger setup causes issues when modules are imported vs run directly.

**Current state:**
```python
# file_matcher.py
logger = logging.getLogger(__name__)  # __name__ = "file_matcher" or "__main__"
```

**What breaks:**
- Logger name changes based on how module is invoked
- Duplicate log handlers when modules are imported multiple times
- Log configuration in one module doesn't apply to others

**Warning signs:**
- Duplicate log messages
- Some modules log, others don't
- Logging works in tests but not in production

**Prevention:**
1. **Centralize logger configuration** in one place:
   ```python
   # filematcher/logging_config.py
   import logging

   def setup_logging(verbose: bool = False):
       level = logging.DEBUG if verbose else logging.WARNING
       logging.basicConfig(level=level, format='%(message)s')
   ```

2. **Use package name for all loggers**:
   ```python
   # In each module:
   logger = logging.getLogger('filematcher.hashing')
   ```

3. **Configure logging only in CLI entry point**, not in library modules

**Phase:** Address in Phase 1 when creating module structure

---

## Low-Risk Pitfalls

These are annoyances or minor issues, easy to fix.

### 9. Version String Inconsistency

**Risk:** Version declared in multiple places gets out of sync.

**Current locations:**
- `pyproject.toml`: `version = "1.1.0"`
- `file_matcher.py` docstring: `Version: 1.0.0` (already inconsistent!)

**Prevention:**
1. **Single source of truth** - Use `importlib.metadata`:
   ```python
   # filematcher/__init__.py
   from importlib.metadata import version
   __version__ = version("filematcher")
   ```

2. **Or dynamic version in pyproject.toml**:
   ```toml
   [project]
   dynamic = ["version"]

   [tool.setuptools.dynamic]
   version = {attr = "filematcher.__version__"}
   ```

**Phase:** Fix in Phase 1

---

### 10. Constants Scattered Across Modules

**Risk:** Magic numbers and configuration constants end up in multiple places, making changes error-prone.

**Current examples in file_matcher.py:**
- `SPARSE_THRESHOLD` (implicit, 100MB for fast mode)
- Color codes (`GREEN`, `YELLOW`, etc.)
- Exit codes (0, 1, 2, 3)

**Prevention:**
1. **Create `filematcher/constants.py`** for all magic values:
   ```python
   # filematcher/constants.py
   SPARSE_THRESHOLD = 100 * 1024 * 1024  # 100MB
   SPARSE_SAMPLE_SIZE = 64 * 1024  # 64KB

   # Exit codes
   EXIT_SUCCESS = 0
   EXIT_ERROR = 1
   EXIT_PARTIAL = 3
   ```

2. **Import from constants module** everywhere else

**Phase:** Extract during Phase 1 module split

---

### 11. Forgetting to Update Documentation

**Risk:** README, CLAUDE.md, docstrings reference old structure.

**What to update:**
- Import examples in README
- Module paths in CLAUDE.md
- Docstrings referencing file locations
- Test commands

**Prevention:**
1. **Create checklist** of documentation to update
2. **Grep for old paths** after restructure:
   ```bash
   grep -r "file_matcher\." docs/ README.md CLAUDE.md
   grep -r "from file_matcher import" docs/ README.md
   ```

**Phase:** Final step of Phase 1

---

## Phase-Specific Risk Summary

| Phase | Pitfalls to Address | Must Verify |
|-------|---------------------|-------------|
| Phase 1: Structure | 1, 2, 3, 4, 5, 7, 8, 9, 10, 11 | Entry point works, 217 tests pass, imports work |
| Phase 2: Testing | 4 | All 217 tests discovered and passing |
| Phase 3: Polish | 6, 11 | Editable install works, docs updated |

---

## Verification Checklist

Before declaring restructure complete:

- [ ] `pip install -e .` succeeds
- [ ] `filematcher --help` works
- [ ] `python -c "from filematcher import main, get_file_hash"` succeeds
- [ ] `python -m pytest` discovers and runs 217 tests
- [ ] No circular import errors on fresh Python
- [ ] `filematcher test_dir1 test_dir2` produces same output as before
- [ ] Version string is consistent and accessible

---

## Sources

### Official Documentation
- [Python Packaging User Guide: Creating Command Line Tools](https://packaging.python.org/en/latest/guides/creating-command-line-tools/)
- [Python Packaging: src vs flat layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)
- [Setuptools: Entry Points](https://setuptools.pypa.io/en/latest/userguide/entry_point.html)
- [Setuptools: Development Mode](https://setuptools.pypa.io/en/latest/userguide/development_mode.html)
- [Python Import System](https://docs.python.org/3/reference/import.html)
- [Python unittest](https://docs.python.org/3/library/unittest.html)

### Community Resources
- [DataCamp: Python Circular Import](https://www.datacamp.com/tutorial/python-circular-import)
- [Brex Engineering: Avoiding Circular Imports](https://medium.com/brexeng/avoiding-circular-imports-in-python-7c35ec8145ed)
- [Real Python: Public API Surface](https://realpython.com/ref/best-practices/public-api-surface/)
- [Real Python: Python's __all__](https://realpython.com/python-all-attribute/)
- [Hitchhiker's Guide: Structuring Your Project](https://docs.python-guide.org/writing/structure/)
- [PyBites: Python Packaging](https://pybit.es/articles/python-packaging/)

### Issue Trackers (Real-World Problems)
- [setuptools #4141: entry_points console_scripts issue](https://github.com/pypa/setuptools/issues/4141)
- [pip #11457: Deprecate legacy editable mechanism](https://github.com/pypa/pip/issues/11457)

---
*Research completed: 2026-01-27*
