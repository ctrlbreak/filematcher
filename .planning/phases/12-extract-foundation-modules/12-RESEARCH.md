# Phase 12: Extract Foundation Modules - Research

**Researched:** 2026-01-27
**Domain:** Python module extraction and refactoring
**Confidence:** HIGH

## Summary

This phase extracts two "leaf modules" (modules with no internal dependencies on other filematcher code) from the monolithic `file_matcher.py` into separate files within the `filematcher/` package:
1. `colors.py` - Color system (ColorMode, ColorConfig, color helpers, terminal helpers)
2. `hashing.py` - Hashing functions (create_hasher, get_file_hash, get_sparse_hash)

These are ideal candidates for first extraction because:
- They have zero dependencies on other filematcher code
- They only depend on Python standard library (hashlib, os, sys, re)
- Tests can continue to work unchanged via re-exports
- The pattern establishes the approach for future module extractions

**Primary recommendation:** Extract modules using explicit imports in `__init__.py` with `__all__` to maintain full backward compatibility with existing test imports.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `hashlib` | Python 3.9+ | MD5/SHA256 hashing | Built-in, no external deps |
| Python stdlib `os` | Python 3.9+ | File size, environment vars | Built-in for file operations |
| Python stdlib `sys` | Python 3.9+ | stdout stream access | Built-in for TTY detection |
| Python stdlib `re` | Python 3.9+ | ANSI escape pattern matching | Built-in for strip_ansi |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Python stdlib `pathlib` | Python 3.9+ | Path type hints | Type annotations for file paths |
| Python stdlib `enum` | Python 3.9+ | ColorMode enum | Color mode enumeration |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Manual re-exports | `from .colors import *` | Would need `__all__` in submodule, less explicit |
| Relative imports | Absolute imports | Relative is standard for intra-package |

**Installation:** No new dependencies - all Python standard library.

## Architecture Patterns

### Recommended Project Structure
```
filematcher/
├── __init__.py        # Re-exports all public symbols (updated)
├── __main__.py        # python -m entry point (unchanged)
├── colors.py          # NEW: Color system extracted
└── hashing.py         # NEW: Hashing functions extracted
file_matcher.py        # Modified: imports from filematcher.colors, filematcher.hashing
```

### Pattern 1: Leaf Module Extraction
**What:** Extract code with no internal dependencies first
**When to use:** When refactoring a monolith into modules
**Example:**
```python
# filematcher/colors.py
"""Color system for terminal output."""
from __future__ import annotations

import os
import re
import sys
from enum import Enum

# ANSI Color Constants
RESET = "\033[0m"
GREEN = "\033[32m"
# ... rest of constants

class ColorMode(Enum):
    """Color output mode."""
    AUTO = "auto"
    NEVER = "never"
    ALWAYS = "always"

class ColorConfig:
    """Determines whether to use color..."""
    # Full implementation

# All helper functions: colorize, green, yellow, red, cyan, dim, bold, etc.
```

### Pattern 2: Re-export from Submodules
**What:** Package `__init__.py` imports from submodules and re-exports
**When to use:** Maintaining backward compatibility during migration
**Example:**
```python
# filematcher/__init__.py
"""File Matcher package."""

# Import from new submodules
from filematcher.colors import (
    ColorMode,
    ColorConfig,
    colorize,
    green,
    yellow,
    red,
    cyan,
    dim,
    bold,
    bold_yellow,
    bold_green,
    # ... all color exports
)

from filematcher.hashing import (
    create_hasher,
    get_file_hash,
    get_sparse_hash,
)

# Continue importing rest from file_matcher.py
from file_matcher import (
    # Everything NOT moved to colors.py or hashing.py
    ActionFormatter,
    TextActionFormatter,
    # ...
)

__all__ = [
    # All symbols as before
]
```

### Pattern 3: Original Module Imports from Package
**What:** `file_matcher.py` imports from filematcher submodules
**When to use:** After extraction, to avoid code duplication
**Example:**
```python
# file_matcher.py (modified)
# Instead of defining ColorMode, ColorConfig locally:
from filematcher.colors import (
    ColorMode,
    ColorConfig,
    RESET, GREEN, YELLOW, RED, CYAN, BOLD, DIM,
    BOLD_GREEN, BOLD_YELLOW,
    colorize, green, yellow, red, cyan, dim, bold,
    bold_yellow, bold_green,
    strip_ansi, visible_len, terminal_rows_for_line,
    render_group_line, determine_color_mode,
    GroupLine,  # dataclass
)

from filematcher.hashing import (
    create_hasher,
    get_file_hash,
    get_sparse_hash,
)
```

### Anti-Patterns to Avoid
- **Circular imports:** `colors.py` must NOT import from `file_matcher.py` or other filematcher modules
- **Breaking test imports:** Tests import from `file_matcher` - these must continue to work
- **Forgetting re-exports:** If a symbol isn't in `__init__.py`, import fails
- **Modifying tests:** Phase requirement: tests pass WITHOUT modification

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Module re-exports | Manual attribute copying | Explicit `from X import Y` in `__init__.py` | Standard Python pattern, IDE support |
| Backward compat | Deprecation warnings | Direct re-export | No deprecation needed - just re-export |
| Import verification | Custom import checks | `python -c "from filematcher import X"` | Standard verification method |

**Key insight:** This is a straightforward Python module extraction. Use standard patterns, no custom tooling needed.

## Common Pitfalls

### Pitfall 1: Circular Import on Color Constants
**What goes wrong:** `file_matcher.py` imports from `filematcher.colors`, but `colors.py` tries to import something from `file_matcher.py`
**Why it happens:** Accidental dependency or helper function in wrong place
**How to avoid:** Colors module must ONLY use stdlib imports. Verify with: `python -c "from filematcher.colors import ColorConfig"`
**Warning signs:** ImportError mentioning circular import or partially initialized module

### Pitfall 2: Missing Re-exports in __init__.py
**What goes wrong:** `from filematcher import green` fails after extraction
**Why it happens:** Forgot to add the symbol to __init__.py's imports from colors.py
**How to avoid:** Compare __all__ before/after, verify each symbol with direct import test
**Warning signs:** ImportError: cannot import name 'X' from 'filematcher'

### Pitfall 3: Breaking Test Imports from file_matcher
**What goes wrong:** Tests that do `from file_matcher import ColorConfig` fail
**Why it happens:** Removed code from file_matcher.py but didn't import it back
**How to avoid:** `file_matcher.py` must import from `filematcher.colors` and `filematcher.hashing`
**Warning signs:** Test failures with ImportError

### Pitfall 4: ANSI Constants Not Re-exported
**What goes wrong:** Tests like `test_color_output.py` use constants like `GREEN`, `RESET`, `BOLD_GREEN`
**Why it happens:** Constants are lowercase in helper functions but tests import them directly
**How to avoid:** Include ANSI constants in colors.py exports AND re-export in __init__.py
**Warning signs:** NameError or ImportError for RESET, GREEN, etc.

### Pitfall 5: GroupLine and SpaceInfo Dataclasses
**What goes wrong:** `GroupLine` used by `render_group_line` in colors - should it move too?
**Why it happens:** Dataclass used by color rendering function
**How to avoid:** Move `GroupLine` to colors.py (it's used by render_group_line). Keep `SpaceInfo` in file_matcher.py (used elsewhere)
**Warning signs:** ImportError for GroupLine

## Code Examples

### colors.py Structure
```python
# filematcher/colors.py
"""Color system for terminal output.

This module provides:
- ANSI color constants for 16-color terminal compatibility
- ColorMode enum for color output control (AUTO/NEVER/ALWAYS)
- ColorConfig class for determining color state
- Color helper functions (green, yellow, red, cyan, dim, bold, etc.)
- Terminal helper functions (strip_ansi, visible_len, terminal_rows_for_line)
- GroupLine dataclass for structured output
- render_group_line for colorized output rendering
"""
from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from enum import Enum


# ============================================================================
# ANSI Color Constants (16-color for compatibility)
# ============================================================================
RESET = "\033[0m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"
BOLD = "\033[1m"
DIM = "\033[2m"
BOLD_GREEN = "\033[1;32m"
BOLD_YELLOW = "\033[1;33m"


# ============================================================================
# Color Configuration
# ============================================================================
class ColorMode(Enum):
    """Color output mode."""
    AUTO = "auto"
    NEVER = "never"
    ALWAYS = "always"


class ColorConfig:
    """Determines whether to use color based on mode, environment, and TTY."""
    # ... full implementation


# ============================================================================
# Structured Output Types
# ============================================================================
@dataclass
class GroupLine:
    """Structured line for group output."""
    line_type: str
    label: str
    path: str
    warning: str = ""
    prefix: str = ""
    indent: str = ""


# ============================================================================
# Terminal Helper Functions
# ============================================================================
_ANSI_ESCAPE_PATTERN = re.compile(r'\x1b\[[0-9;]*m')

def strip_ansi(text: str) -> str: ...
def visible_len(text: str) -> int: ...
def terminal_rows_for_line(text: str, term_width: int) -> int: ...


# ============================================================================
# Color Helper Functions
# ============================================================================
def colorize(text: str, code: str, color_config: ColorConfig) -> str: ...
def green(text: str, cc: ColorConfig) -> str: ...
def yellow(text: str, cc: ColorConfig) -> str: ...
def red(text: str, cc: ColorConfig) -> str: ...
def cyan(text: str, cc: ColorConfig) -> str: ...
def dim(text: str, cc: ColorConfig) -> str: ...
def bold(text: str, cc: ColorConfig) -> str: ...
def bold_yellow(text: str, cc: ColorConfig) -> str: ...
def bold_green(text: str, cc: ColorConfig) -> str: ...
def render_group_line(line: GroupLine, cc: ColorConfig) -> str: ...
def determine_color_mode(args) -> ColorMode: ...
```

### hashing.py Structure
```python
# filematcher/hashing.py
"""File hashing functions.

This module provides:
- create_hasher: Create a hash object for md5 or sha256
- get_file_hash: Hash file content with optional fast mode
- get_sparse_hash: Fast sparse sampling hash for large files
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path


def create_hasher(hash_algorithm: str = 'md5') -> hashlib._Hash:
    """Create a hash object for the specified algorithm."""
    # ... implementation


def get_file_hash(
    filepath: str | Path,
    hash_algorithm: str = 'md5',
    fast_mode: bool = False,
    size_threshold: int = 100*1024*1024
) -> str:
    """Calculate hash of file content."""
    # ... implementation


def get_sparse_hash(
    filepath: str | Path,
    hash_algorithm: str = 'md5',
    file_size: int | None = None,
    sample_size: int = 1024*1024
) -> str:
    """Create a hash based on sparse sampling of a large file."""
    # ... implementation
```

### Updated __init__.py Pattern
```python
# filematcher/__init__.py
"""File Matcher package - find and deduplicate files across directories."""

# Import from new submodules
from filematcher.colors import (
    # Constants
    RESET, GREEN, YELLOW, RED, CYAN, BOLD, DIM, BOLD_GREEN, BOLD_YELLOW,
    # Classes
    ColorMode,
    ColorConfig,
    GroupLine,
    # Functions
    colorize,
    green,
    yellow,
    red,
    cyan,
    dim,
    bold,
    bold_yellow,
    bold_green,
    render_group_line,
    determine_color_mode,
    strip_ansi,
    visible_len,
    terminal_rows_for_line,
)

from filematcher.hashing import (
    create_hasher,
    get_file_hash,
    get_sparse_hash,
)

# Import remaining from file_matcher.py (which now imports from above)
from file_matcher import (
    # Output formatters
    ActionFormatter,
    TextActionFormatter,
    JsonActionFormatter,
    # ... rest of exports
)

__version__ = "1.1.0"
__all__ = [
    # ... all symbols
]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single-file modules | Package with submodules | Python 3.3+ (namespace packages) | Better organization |
| `from X import *` | Explicit imports with `__all__` | Best practice since PEP 8 | Clearer API |
| Monolithic file_matcher.py | Gradual extraction to package | This refactoring | Maintainability |

**Deprecated/outdated:**
- Implicit namespace packages without `__init__.py`: Still supported but explicit is clearer
- `from module import *` without `__all__`: Considered poor practice, hard to maintain

## Open Questions

1. **Should ANSI constants have a module-level `__all__`?**
   - What we know: Tests directly import `GREEN`, `RESET`, `BOLD_GREEN` from `file_matcher`
   - What's unclear: Whether to expose constants in colors.py's `__all__` or just export classes/functions
   - Recommendation: Include all constants in `__all__` since tests use them directly

2. **Should `determine_color_mode` stay in colors.py?**
   - What we know: It depends on `args.json` and `args.color_mode` from argparse
   - What's unclear: Whether this creates coupling to CLI module
   - Recommendation: Include in colors.py - it takes generic args object, doesn't import argparse

## Sources

### Primary (HIGH confidence)
- Codebase analysis: `file_matcher.py` (lines 32-345 for colors, 2177-2284 for hashing)
- Codebase analysis: `filematcher/__init__.py` (current re-export structure)
- Codebase analysis: `tests/test_color_output.py`, `tests/test_file_hashing.py`, `tests/test_fast_mode.py` (import patterns)
- Phase 11 documentation: `.planning/phases/11-package-scaffolding/` (established patterns)

### Secondary (MEDIUM confidence)
- [Python Packages Guide - Package Structure](https://py-pkgs.org/04-package-structure.html) - Standard package organization
- [The Correct Way to Re-Export Modules from __init__.py](https://www.pythontutorials.net/blog/correct-way-to-re-export-modules-from-init-py/) - Re-export patterns
- [Python Refactoring Best Practices](https://www.codesee.io/learning-center/python-refactoring) - Refactoring techniques
- [ArjanCodes - Python Code Structuring](https://arjancodes.com/blog/organizing-python-code-with-packages-and-modules/) - Package best practices

### Tertiary (LOW confidence)
- WebSearch for 2026 Python practices - General patterns confirmed

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Python stdlib only, well-documented
- Architecture: HIGH - Standard Python package patterns
- Pitfalls: HIGH - Based on actual codebase analysis and test imports

**Research date:** 2026-01-27
**Valid until:** 90 days (Python patterns are stable)

## Extraction Checklist

### Colors Module (`colors.py`)
Must include:
- [x] ANSI constants: RESET, GREEN, YELLOW, RED, CYAN, BOLD, DIM, BOLD_GREEN, BOLD_YELLOW
- [x] ColorMode enum
- [x] ColorConfig class
- [x] GroupLine dataclass (used by render_group_line)
- [x] Terminal helpers: `_ANSI_ESCAPE_PATTERN`, strip_ansi, visible_len, terminal_rows_for_line
- [x] Color helpers: colorize, green, yellow, red, cyan, dim, bold, bold_yellow, bold_green
- [x] render_group_line function
- [x] determine_color_mode function

Dependencies (stdlib only):
- os (for environ)
- sys (for stdout)
- re (for ANSI pattern)
- enum (for ColorMode)
- dataclasses (for GroupLine)

### Hashing Module (`hashing.py`)
Must include:
- [x] create_hasher function
- [x] get_file_hash function
- [x] get_sparse_hash function

Dependencies (stdlib only):
- hashlib
- os (for getsize)
- pathlib (for Path type)

### Test Compatibility
Tests that import color-related symbols from `file_matcher`:
- `test_color_output.py`: strip_ansi, GREEN, RESET, BOLD_GREEN, visible_len, terminal_rows_for_line, YELLOW

Tests that import hashing-related symbols from `file_matcher`:
- `test_file_hashing.py`: get_file_hash
- `test_fast_mode.py`: get_file_hash, get_sparse_hash

All must continue to work via `from file_matcher import X` after extraction.
