# Phase 14: Extract Formatters and Directory - Research

**Researched:** 2026-01-27
**Domain:** Python module extraction - output formatters and directory operations
**Confidence:** HIGH

## Summary

This phase extracts two modules from the monolithic `file_matcher.py`:

1. **`formatters.py`** - Output formatter classes (ActionFormatter ABC, TextActionFormatter, JsonActionFormatter) plus supporting formatting functions and constants
2. **`directory.py`** - Directory indexing and matching operations (index_directory, find_matching_files, select_master_file)

These modules have more complex dependencies than the Phase 12/13 leaf modules:
- `formatters.py` depends on `filematcher.colors` (for color helpers, GroupLine, ColorConfig) and `filematcher.actions` (for format_file_size)
- `directory.py` depends on `filematcher.hashing` (for get_file_hash), `filematcher.actions` (for format_file_size), and `filematcher.filesystem` (for is_in_directory)

**Primary recommendation:** Extract formatters.py first since it has fewer external dependencies (only colors and actions). Then extract directory.py which depends on hashing, filesystem, and actions. Continue using direct imports since the dependency graph has no cycles.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `abc` | Python 3.9+ | Abstract base class for ActionFormatter | Built-in for interface definition |
| Python stdlib `json` | Python 3.9+ | JSON serialization in JsonActionFormatter | Built-in JSON handling |
| Python stdlib `datetime` | Python 3.9+ | Timestamps in JSON output | Built-in datetime handling |
| Python stdlib `os` | Python 3.9+ | File operations, path manipulation | Built-in filesystem access |
| Python stdlib `shutil` | Python 3.9+ | Terminal size detection | Built-in for TTY width |
| Python stdlib `sys` | Python 3.9+ | stdout/stderr access for TTY detection | Built-in for stream handling |
| Python stdlib `collections.defaultdict` | Python 3.9+ | Hash-to-files mapping in index_directory | Built-in data structure |
| Python stdlib `logging` | Python 3.9+ | Progress logging in directory operations | Built-in logging framework |
| Python stdlib `pathlib` | Python 3.9+ | Path manipulation | Modern path API |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Python stdlib `dataclasses` | Python 3.9+ | SpaceInfo dataclass | Structured return values |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Single formatters.py | Separate text_formatter.py and json_formatter.py | More files but cleaner separation; unnecessary given tight coupling |
| Keep format_file_size in actions | Duplicate in directory.py | Already duplicated in actions.py; prefer import from actions |

**Installation:** No new dependencies - all Python standard library.

## Architecture Patterns

### Recommended Project Structure
```
filematcher/
    __init__.py        # Re-exports (updated with formatters, directory)
    __main__.py        # Entry point (unchanged)
    colors.py          # Phase 12: Color system
    hashing.py         # Phase 12: Hashing functions
    filesystem.py      # Phase 13: Filesystem helpers
    actions.py         # Phase 13: Action execution + audit logging
    formatters.py      # NEW: Output formatters (ABC, Text, JSON)
    directory.py       # NEW: Directory indexing and matching
file_matcher.py        # Modified: imports from new modules
```

### Pattern 1: Formatter Module with ABC
**What:** Module containing abstract base class and concrete implementations
**When to use:** Strategy pattern for output formatting
**Example:**
```python
# filematcher/formatters.py
"""Output formatters for File Matcher.

This module provides:
- ActionFormatter: Abstract base class defining the formatter interface
- TextActionFormatter: Human-readable colored text output
- JsonActionFormatter: Machine-readable JSON output (accumulator pattern)
- Supporting constants (PREVIEW_BANNER, EXECUTE_BANNER)
- Formatting helpers (format_duplicate_group, format_group_lines, etc.)
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
import shutil
import sys
from pathlib import Path

# Internal imports
from filematcher.colors import (
    ColorMode, ColorConfig, GroupLine,
    red, cyan, bold_yellow, bold_green, green, yellow, dim,
    render_group_line, terminal_rows_for_line,
)
from filematcher.actions import format_file_size


# ============================================================================
# Structured Output Types
# ============================================================================

@dataclass
class SpaceInfo:
    """Space savings calculation results."""
    bytes_saved: int
    duplicate_count: int
    group_count: int


# ============================================================================
# Constants
# ============================================================================

PREVIEW_BANNER = "=== PREVIEW MODE - Use --execute to apply changes ==="
EXECUTE_BANNER = "=== EXECUTE MODE! ==="


# ============================================================================
# Output Formatter ABCs
# ============================================================================

class ActionFormatter(ABC):
    """Abstract base class for formatting action mode output."""

    def __init__(self, verbose: bool = False, preview_mode: bool = True,
                 action: str | None = None, will_execute: bool = False):
        self.verbose = verbose
        self.preview_mode = preview_mode
        self._action = action
        self.will_execute = will_execute

    @abstractmethod
    def format_banner(self) -> None: ...
    @abstractmethod
    def format_unified_header(self, action: str, dir1: str, dir2: str) -> None: ...
    # ... rest of abstract methods
```

### Pattern 2: Directory Module with Logging
**What:** Module that uses module-level logger for progress reporting
**When to use:** Functions that report progress during long operations
**Example:**
```python
# filematcher/directory.py
"""Directory indexing and matching operations for File Matcher.

This module provides:
- index_directory: Recursively index files by content hash
- find_matching_files: Find content-identical files across directories
- select_master_file: Choose master from duplicate set
"""
from __future__ import annotations

from collections import defaultdict
import logging
import os
import shutil
import sys
from pathlib import Path

# Internal imports
from filematcher.hashing import get_file_hash
from filematcher.actions import format_file_size
from filematcher.filesystem import is_in_directory

logger = logging.getLogger(__name__)


def index_directory(
    directory: str | Path,
    hash_algorithm: str = 'md5',
    fast_mode: bool = False,
    verbose: bool = False
) -> dict[str, list[str]]:
    """Recursively index all files by content hash."""
    # ... implementation with verbose progress logging
```

### Pattern 3: Internal Import Chain
**What:** New modules import from previously extracted modules
**When to use:** When building on lower-level abstractions
**Dependency graph (no cycles):**
```
formatters.py -> colors.py (for ColorConfig, helpers)
              -> actions.py (for format_file_size)

directory.py  -> hashing.py (for get_file_hash)
              -> actions.py (for format_file_size)
              -> filesystem.py (for is_in_directory)
```

### Anti-Patterns to Avoid
- **Importing from file_matcher.py:** Extracted modules must NOT import from the main file
- **Circular dependencies:** formatters.py must not import from directory.py and vice versa
- **Breaking test imports:** Tests use `from file_matcher import ActionFormatter` - must continue working
- **Missing format_duplicate_group:** This function is used by TextActionFormatter.format_duplicate_group but is defined separately

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON accumulator pattern | Manual dict building | JsonActionFormatter's existing pattern | Already tested, handles edge cases |
| Color rendering | String interpolation | render_group_line from colors.py | Centralized color logic |
| Progress display | Print statements | Logger with TTY-aware formatting | Standard Python pattern |

**Key insight:** These modules are already well-implemented and tested. The extraction is about organization, not reimplementation.

## Common Pitfalls

### Pitfall 1: format_duplicate_group Function vs Method
**What goes wrong:** TextActionFormatter.format_duplicate_group() calls a standalone format_duplicate_group() function
**Why it happens:** The method delegates to a standalone function for reuse
**How to avoid:** Both the method AND the standalone function must be in formatters.py
**Warning signs:** NameError for format_duplicate_group inside TextActionFormatter

### Pitfall 2: SpaceInfo Dataclass Location
**What goes wrong:** SpaceInfo is used by formatters (format_statistics) and main() for space calculations
**Why it happens:** Shared data structure across modules
**How to avoid:** Move SpaceInfo to formatters.py since it's primarily used for output formatting
**Warning signs:** ImportError when file_matcher.py tries to use SpaceInfo

### Pitfall 3: format_file_size Import in Directory
**What goes wrong:** index_directory calls format_file_size for verbose progress display
**Why it happens:** Need to format byte counts for human-readable output
**How to avoid:** Import format_file_size from filematcher.actions (where it was duplicated in Phase 13)
**Warning signs:** NameError for format_file_size in directory.py

### Pitfall 4: Logger Name Collision
**What goes wrong:** Both directory.py and file_matcher.py define module-level `logger`
**Why it happens:** Standard pattern for module-level logging
**How to avoid:** Use `logging.getLogger(__name__)` which gives unique names per module
**Warning signs:** Logging going to wrong handler

### Pitfall 5: select_oldest and Helper Functions
**What goes wrong:** select_master_file calls select_oldest which is still in file_matcher.py
**Why it happens:** Helper functions not identified during extraction
**How to avoid:** Move select_oldest with select_master_file (they're tightly coupled)
**Warning signs:** NameError for select_oldest in directory.py

### Pitfall 6: Test Import Paths
**What goes wrong:** Tests that do `from file_matcher import JsonActionFormatter` fail
**Why it happens:** Classes moved but file_matcher.py doesn't import them back
**How to avoid:** file_matcher.py must import and re-export all moved symbols
**Verification:** Run all 217 tests without modification

## Code Examples

### formatters.py Structure
```python
# filematcher/formatters.py
"""Output formatters for File Matcher.

This module provides:
- ActionFormatter: Abstract base class for output formatting (Strategy pattern)
- TextActionFormatter: Human-readable colored text output
- JsonActionFormatter: Machine-readable JSON output
- SpaceInfo: Structured space savings calculation result
- Formatting functions: format_duplicate_group, format_group_lines, format_statistics_footer
- Constants: PREVIEW_BANNER, EXECUTE_BANNER
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
import shutil
import sys
from pathlib import Path

# Internal imports
from filematcher.colors import (
    ColorMode, ColorConfig, GroupLine,
    red, cyan, bold_yellow, bold_green, green, yellow, dim,
    render_group_line, terminal_rows_for_line,
)
from filematcher.actions import format_file_size


# ============================================================================
# Structured Output Types
# ============================================================================

@dataclass
class SpaceInfo:
    """Space savings calculation results."""
    bytes_saved: int
    duplicate_count: int
    group_count: int


# ============================================================================
# Constants
# ============================================================================

PREVIEW_BANNER = "=== PREVIEW MODE - Use --execute to apply changes ==="
EXECUTE_BANNER = "=== EXECUTE MODE! ==="


# ============================================================================
# Formatting Helper Functions
# ============================================================================

def format_group_lines(...) -> list[GroupLine]:
    """Format group lines with unified visual structure."""
    # ... implementation

def format_duplicate_group(...) -> list[GroupLine]:
    """Format a duplicate group for display."""
    # ... implementation

def format_confirmation_prompt(...) -> str:
    """Format confirmation prompt showing action summary."""
    # ... implementation

def format_statistics_footer(...) -> list[str]:
    """Format the statistics footer for preview/execute output."""
    # ... implementation

def calculate_space_savings(...) -> SpaceInfo:
    """Calculate space that would be saved by deduplication."""
    # ... implementation


# ============================================================================
# Output Formatter ABCs
# ============================================================================

class ActionFormatter(ABC):
    """Abstract base class for formatting action mode output."""
    # ... full implementation

class JsonActionFormatter(ActionFormatter):
    """JSON output formatter using accumulator pattern."""
    # ... full implementation

class TextActionFormatter(ActionFormatter):
    """Text output formatter with colors."""
    # ... full implementation
```

### directory.py Structure
```python
# filematcher/directory.py
"""Directory indexing and file matching operations for File Matcher.

This module provides:
- index_directory: Recursively index files by content hash
- find_matching_files: Find content-identical files across two directories
- select_master_file: Choose which file is the "master" from a duplicate group
- select_oldest: Helper to find oldest file by mtime
"""
from __future__ import annotations

from collections import defaultdict
import logging
import os
import shutil
import sys
from pathlib import Path

# Internal imports
from filematcher.hashing import get_file_hash
from filematcher.actions import format_file_size
from filematcher.filesystem import is_in_directory

logger = logging.getLogger(__name__)


def select_oldest(file_paths: list[str]) -> tuple[str, list[str]]:
    """Select the oldest file by mtime and return it with remaining files."""
    oldest = min(file_paths, key=lambda p: os.path.getmtime(p))
    others = [f for f in file_paths if f != oldest]
    return oldest, others


def select_master_file(
    file_paths: list[str],
    master_dir: Path | None
) -> tuple[str, list[str], str]:
    """Select which file should be considered the master."""
    # ... implementation


def index_directory(
    directory: str | Path,
    hash_algorithm: str = 'md5',
    fast_mode: bool = False,
    verbose: bool = False
) -> dict[str, list[str]]:
    """Recursively index all files in a directory."""
    # ... implementation


def find_matching_files(
    dir1: str | Path,
    dir2: str | Path,
    hash_algorithm: str = 'md5',
    fast_mode: bool = False,
    verbose: bool = False,
    different_names_only: bool = False
) -> tuple[dict[str, tuple[list[str], list[str]]], list[str], list[str]]:
    """Find files that have identical content across two directories."""
    # ... implementation
```

### Updated __init__.py Pattern
```python
# filematcher/__init__.py (additions)

# Import from formatters submodule (direct import)
from filematcher.formatters import (
    # Structured types
    SpaceInfo,
    # Constants
    PREVIEW_BANNER,
    EXECUTE_BANNER,
    # Formatter classes
    ActionFormatter,
    TextActionFormatter,
    JsonActionFormatter,
    # Formatting functions
    format_group_lines,
    format_duplicate_group,
    format_confirmation_prompt,
    format_statistics_footer,
    calculate_space_savings,
)

# Import from directory submodule (direct import)
from filematcher.directory import (
    index_directory,
    find_matching_files,
    select_master_file,
    select_oldest,
)

# Remove these from __getattr__ lazy loader (moved to direct imports)
```

## Extraction Checklist

### Formatters Module (`formatters.py`)
Must include:
- [ ] `SpaceInfo` dataclass
- [ ] `PREVIEW_BANNER` constant
- [ ] `EXECUTE_BANNER` constant
- [ ] `ActionFormatter` ABC with all abstract methods
- [ ] `JsonActionFormatter` class (full implementation)
- [ ] `TextActionFormatter` class (full implementation)
- [ ] `format_group_lines()` function
- [ ] `format_duplicate_group()` function
- [ ] `format_confirmation_prompt()` function
- [ ] `format_statistics_footer()` function
- [ ] `calculate_space_savings()` function

Dependencies:
- Python stdlib: abc, dataclasses, datetime, json, os, shutil, sys, pathlib
- Internal: filematcher.colors (ColorMode, ColorConfig, GroupLine, color helpers)
- Internal: filematcher.actions (format_file_size)

### Directory Module (`directory.py`)
Must include:
- [ ] `select_oldest()` function
- [ ] `select_master_file()` function
- [ ] `index_directory()` function
- [ ] `find_matching_files()` function

Dependencies:
- Python stdlib: collections.defaultdict, logging, os, shutil, sys, pathlib
- Internal: filematcher.hashing (get_file_hash)
- Internal: filematcher.actions (format_file_size)
- Internal: filematcher.filesystem (is_in_directory)

### Test Compatibility
Tests that import formatter-related symbols from `file_matcher`:
- `test_json_output.py`: JsonActionFormatter (direct import)
- `test_safe_defaults.py`: PREVIEW_BANNER, EXECUTE_BANNER

Tests that import directory-related symbols from `file_matcher`:
- `test_directory_operations.py`: index_directory, find_matching_files
- `test_real_directories.py`: index_directory, find_matching_files
- `test_fast_mode.py`: find_matching_files

All must continue to work via `from file_matcher import X` after extraction.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| All classes in one file | Separate formatter module | This refactoring | Better testability |
| Directory ops mixed with CLI | Dedicated directory module | This refactoring | Reusable API |

**Deprecated/outdated:**
- None - this is standard Python module organization following Strategy pattern

## Open Questions

1. **Should confirm_execution() move to formatters.py or stay in file_matcher.py?**
   - What we know: It's UI-related but not a formatter method
   - What's unclear: Whether it belongs with formatters or stays in CLI
   - Recommendation: Keep in file_matcher.py - it's CLI interaction, not formatting

2. **Should utility functions (build_file_sizes, build_log_flags, etc.) be extracted?**
   - What we know: They're used by main() for building data structures
   - What's unclear: Whether they should move with formatters/directory or stay
   - Recommendation: Keep in file_matcher.py for now - they're main() helpers, not core functionality

## Sources

### Primary (HIGH confidence)
- Codebase analysis: `file_matcher.py` lines 77-927 (formatters, SpaceInfo, constants, format functions)
- Codebase analysis: `file_matcher.py` lines 949-1097 (select_oldest, select_master_file)
- Codebase analysis: `file_matcher.py` lines 1364-1480 (index_directory, find_matching_files)
- Codebase analysis: `tests/test_json_output.py`, `tests/test_directory_operations.py` (import patterns)
- Phase 12/13 documentation: Established extraction patterns

### Secondary (MEDIUM confidence)
- Python ABC documentation for abstract base class patterns
- Python Strategy pattern best practices

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Python stdlib only, well-documented
- Architecture: HIGH - Follows established Phase 12/13 patterns
- Pitfalls: HIGH - Based on actual codebase analysis and dependency tracing

**Research date:** 2026-01-27
**Valid until:** 90 days (Python patterns are stable)

## Dependency Graph Summary

```
file_matcher.py
    imports from: colors, hashing, filesystem, actions, formatters (NEW), directory (NEW)

filematcher/
    colors.py       [LEAF] - no internal deps
    hashing.py      [LEAF] - no internal deps
    filesystem.py   [LEAF] - no internal deps
    actions.py      -> filesystem.py
    formatters.py   -> colors.py, actions.py           [NEW]
    directory.py    -> hashing.py, actions.py, filesystem.py  [NEW]
```

No cycles exist in this dependency graph.
