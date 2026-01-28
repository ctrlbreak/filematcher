# File Matcher v1.4.0 Release Notes

**Release Date:** 2026-01-28

## Overview

File Matcher v1.4.0 refactors the codebase from a single-file implementation to a proper Python package structure. This improves code navigation, IDE support, and maintainability while maintaining full backward compatibility.

## What's New

### Package Structure

The codebase has been reorganized into a `filematcher/` package with focused modules:

```
filematcher/
├── __init__.py      # Package exports
├── __main__.py      # python -m filematcher support
├── cli.py           # Command-line interface and main()
├── colors.py        # TTY-aware color output
├── hashing.py       # MD5/SHA-256 content hashing
├── filesystem.py    # Filesystem helpers (hardlink detection, etc.)
├── actions.py       # Action execution and audit logging
├── formatters.py    # Text and JSON output formatters
└── directory.py     # Directory indexing and matching
```

### Installation Options

```bash
# Install via pip (recommended)
pip install .
filematcher dir1 dir2

# Or run directly (still works)
python file_matcher.py dir1 dir2
```

### Full Backward Compatibility

All existing usage patterns continue to work:

```bash
# CLI usage unchanged
python file_matcher.py dir1 dir2
filematcher dir1 dir2

# Imports still work
from file_matcher import get_file_hash, find_matching_files
from filematcher import get_file_hash, find_matching_files  # New preferred style
```

## Technical Details

- 7 modules in filematcher/ package
- file_matcher.py is now a thin wrapper (re-exports from package)
- 218 unit tests (217 original + 1 circular import verification test)
- No circular imports (verified via subprocess test)
- Pure Python standard library (no external dependencies)
- Python 3.9+ required

## Module Organization

| Module | Purpose |
|--------|---------|
| `cli.py` | Argument parsing, main() entry point, logging setup |
| `colors.py` | ColorConfig, ColorMode, ANSI helpers (green, red, etc.) |
| `hashing.py` | get_file_hash(), get_sparse_hash() for content hashing |
| `filesystem.py` | is_hardlink_to(), is_symlink_to(), check_cross_filesystem() |
| `actions.py` | execute_action(), safe_replace_with_link(), audit logging |
| `formatters.py` | ActionFormatter ABC, TextActionFormatter, JsonActionFormatter |
| `directory.py` | find_matching_files(), index_directory() |

## Upgrading from v1.3.0

v1.4.0 is fully backward compatible. No changes required to existing scripts or workflows.

**Optional migration**: Update imports from `file_matcher` to `filematcher`:

```python
# Old (still works)
from file_matcher import get_file_hash, find_matching_files

# New (preferred)
from filematcher import get_file_hash, find_matching_files
```

## Why Package Structure?

1. **Better IDE Support**: Jump-to-definition works across modules
2. **Easier Navigation**: Find code by module name instead of scrolling 2000+ lines
3. **AI Tooling**: LLMs can read focused modules instead of entire codebase
4. **Maintainability**: Changes to one module don't affect others
5. **Testing**: Easier to test individual modules in isolation

## Links

- [Full Documentation](README.md)
- [Changelog](CHANGELOG.md)
- [License](LICENSE)
