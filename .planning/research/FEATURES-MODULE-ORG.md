# Features Research: Module Organization for Package Refactoring

**Domain:** Python CLI package structure and module organization
**Researched:** 2026-01-27
**Confidence:** HIGH (based on official Python packaging docs, established patterns)
**Context:** Refactoring single-file CLI tool (~2800 lines) to package structure

## Executive Summary

File Matcher's current `file_matcher.py` is a well-organized single file with clear section comments, but at ~2800 lines it's approaching the practical limit for single-file maintainability. Analysis of the codebase reveals 8 distinct functional areas that naturally map to modules with minimal coupling.

**Key Finding:** The existing section structure (marked with `# ===` comments) already defines clean module boundaries. The refactoring is mostly about extracting existing sections into files, not restructuring the logic.

## Recommended Module Structure

Based on analysis of the actual codebase and Python CLI best practices:

```
filematcher/
    __init__.py          # Package metadata, public API exports
    __main__.py          # Entry point: `python -m filematcher`
    cli.py               # Argument parsing, main() orchestration (~500 lines)
    core/
        __init__.py
        hashing.py       # get_file_hash, get_sparse_hash, create_hasher (~150 lines)
        directory.py     # index_directory, find_matching_files (~200 lines)
        matching.py      # select_master_file, filter_hardlinked_duplicates (~150 lines)
    actions/
        __init__.py
        executor.py      # execute_action, execute_all_actions, safe_replace_with_link (~250 lines)
        filesystem.py    # is_hardlink_to, is_symlink_to, check_cross_filesystem (~100 lines)
    output/
        __init__.py
        formatters.py    # ActionFormatter ABC, TextActionFormatter, JsonActionFormatter (~500 lines)
        color.py         # ColorMode, ColorConfig, color helpers (~200 lines)
        formatting.py    # format_duplicate_group, format_statistics_footer, GroupLine (~300 lines)
    logging/
        __init__.py
        audit.py         # create_audit_logger, log_operation, write_log_header/footer (~150 lines)
    utils.py             # format_file_size, small helpers (~50 lines)
    types.py             # GroupLine, SpaceInfo dataclasses (~50 lines)
```

**Total: 14 files** (including `__init__.py` files)

### Why This Structure

1. **Mirrors existing sections** - The `# ===` comments in file_matcher.py already define these boundaries
2. **Single responsibility** - Each module has one job (hashing, actions, formatting)
3. **Testable units** - Existing test modules already test these areas separately
4. **Minimal coupling** - Dependency flow is mostly downward (cli -> core -> utils)
5. **Familiar pattern** - Matches what developers expect from Click/Typer CLI tools

## Table Stakes

Features users expect from a well-organized Python package. Missing = maintenance pain.

### 1. Clear Entry Point

| Feature | Why Expected | Current Status |
|---------|--------------|----------------|
| `__main__.py` for `python -m filematcher` | Standard Python pattern | Missing (single file) |
| `console_scripts` entry point | pip-installed command | Already in pyproject.toml |
| Clean import path | `from filematcher import find_matching_files` | N/A (single module) |

**Implementation:**
```python
# filematcher/__main__.py
from filematcher.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
```

### 2. Flat Public API

| Feature | Why Expected | Implementation |
|---------|--------------|----------------|
| Top-level exports in `__init__.py` | Users shouldn't need to know internal structure | Export key functions |
| Version in `__init__.py` | `filematcher.__version__` convention | Add `__version__ = "1.1.0"` |
| Minimal internal exposure | Hide implementation details | Use `__all__` |

**Implementation:**
```python
# filematcher/__init__.py
from filematcher.core.hashing import get_file_hash, get_sparse_hash
from filematcher.core.directory import index_directory, find_matching_files
from filematcher.core.matching import select_master_file

__version__ = "1.1.0"
__all__ = [
    "get_file_hash",
    "get_sparse_hash",
    "index_directory",
    "find_matching_files",
    "select_master_file",
    "__version__",
]
```

### 3. Type-Safe Boundaries

| Feature | Why Expected | Notes |
|---------|--------------|-------|
| Type hints on public API | IDE support, self-documenting | Already present in file_matcher.py |
| Dataclasses for structured data | Avoid dict/tuple soup | GroupLine, SpaceInfo already exist |
| Protocol classes for interfaces | Testability, loose coupling | ActionFormatter ABC already exists |

### 4. Test Module Mapping

| Feature | Why Expected | Notes |
|---------|--------------|-------|
| Tests mirror package structure | Easy to find tests for code | Current tests already organized by function |
| Imports work in tests | No sys.path hacks needed | src-layout prevents this issue |

**Current test structure maps well:**
- `test_file_hashing.py` -> `core/hashing.py`
- `test_directory_operations.py` -> `core/directory.py`
- `test_actions.py` -> `actions/executor.py`
- `test_color_output.py` -> `output/color.py`
- `test_json_output.py` -> `output/formatters.py`
- `test_cli.py` -> `cli.py`

## Differentiators

Good-to-have patterns that improve maintainability. Not expected, but valued by maintainers.

### 1. Lazy Imports for CLI Startup

| Feature | Value | Complexity |
|---------|-------|------------|
| Defer heavy imports until needed | Faster `--help` response | Medium |
| Only import what's needed for current action | Reduce memory footprint | Medium |

**Example:**
```python
# filematcher/cli.py
def main():
    args = parse_args()  # argparse only

    # Defer imports until we know what we need
    if args.action != "compare":
        from filematcher.actions import execute_all_actions
    if args.json:
        from filematcher.output.formatters import JsonActionFormatter
```

**Recommendation:** LOW priority. Current startup time is fine for a file utility.

### 2. Plugin-Ready Architecture

| Feature | Value | Complexity |
|---------|-------|------------|
| Formatter as replaceable interface | Custom output formats | Already done (ABC) |
| Hash algorithm registry | Easy to add algorithms | Low |
| Action executor interface | Custom dedup strategies | Medium |

**Current state:** ActionFormatter ABC already enables this. No changes needed.

### 3. Configuration Module

| Feature | Value | Complexity |
|---------|-------|------------|
| Centralized defaults | Single place to change constants | Low |
| Environment variable overrides | FILEMATCHER_LOG_DIR pattern | Already done |

**Recommendation:** LOW priority. Constants are already minimal and well-placed.

## Anti-Features

Over-engineering to explicitly avoid. Common mistakes when refactoring to packages.

### 1. Too Many Layers of Abstraction

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Service layer between CLI and core | Adds indirection without benefit | CLI directly calls core functions |
| Repository pattern for files | Files aren't a database | Keep os/pathlib usage direct |
| Event system for operations | No async needs, no observers | Simple function calls |

**File Matcher is a batch CLI tool, not a web service.** Don't add patterns designed for different domains.

### 2. Excessive Module Splitting

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| One class per file | Python isn't Java | Keep related classes together |
| Separate `models.py`, `services.py`, `repositories.py` | Web framework pattern | Group by domain (hashing, actions, output) |
| More than 3 levels deep | Hard to navigate | Max 2 subpackage levels |

**Bad example:**
```
filematcher/
    core/
        hashing/
            algorithms/
                md5.py
                sha256.py
            sparse/
                sampler.py
```

**Good example:**
```
filematcher/
    core/
        hashing.py  # Contains all hash functions
```

### 3. Premature Configuration Injection

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Config objects passed everywhere | Clutters function signatures | Use module-level defaults |
| Dependency injection framework | Overkill for CLI | Direct imports, constructor params |
| Global singleton for settings | Hidden dependencies | Explicit arguments |

**Current file_matcher.py does this right:** Functions take explicit parameters, no hidden state.

### 4. Circular Import Traps

| Anti-Feature | Why Avoid | Prevention |
|--------------|-----------|------------|
| Formatter imports from CLI | Bidirectional dependency | CLI imports formatter, not vice versa |
| Types module importing implementations | Import loop | Types stay dependency-free |
| `__init__.py` importing everything | Slow startup, import errors | Import only what's exported |

## Module Dependency Graph

Arrows show "imports from" relationships. Designed to be acyclic.

```
cli.py
  |
  +---> core/hashing.py
  |       |
  |       +---> utils.py (format_file_size)
  |
  +---> core/directory.py
  |       |
  |       +---> core/hashing.py
  |
  +---> core/matching.py
  |       |
  |       +---> actions/filesystem.py (is_hardlink_to)
  |
  +---> actions/executor.py
  |       |
  |       +---> actions/filesystem.py
  |       +---> logging/audit.py
  |
  +---> output/formatters.py
  |       |
  |       +---> output/color.py
  |       +---> output/formatting.py
  |       +---> types.py (GroupLine, SpaceInfo)
  |
  +---> output/color.py
  |
  +---> logging/audit.py
          |
          +---> utils.py (format_file_size)

types.py  (no imports from filematcher - only stdlib)
utils.py  (no imports from filematcher - only stdlib)
```

### Circular Import Risk Analysis

| Risk | Modules Involved | Mitigation |
|------|------------------|------------|
| LOW | output/formatters <-> output/formatting | formatters imports formatting, never reverse |
| LOW | core/matching <-> actions/filesystem | matching imports is_hardlink_to only |
| NONE | types.py | No filematcher imports |
| NONE | utils.py | No filematcher imports |

**Key insight:** Current file_matcher.py has no circular dependencies between its sections. The proposed module structure preserves this.

## Alternate Structures Considered

### Flat Structure (Rejected)

```
filematcher/
    __init__.py
    __main__.py
    cli.py
    hashing.py
    directory.py
    matching.py
    actions.py
    formatters.py
    color.py
    audit.py
```

**Why rejected:** 10 modules at same level becomes hard to navigate. Grouping (core/, output/, actions/) provides better organization for related code.

### Minimal Structure (Acceptable Alternative)

```
filematcher/
    __init__.py
    __main__.py
    cli.py
    core.py          # All hashing, directory, matching
    actions.py       # All action execution
    output.py        # All formatters, colors, formatting
    logging.py       # Audit logging
```

**Why acceptable:** 6 files is very manageable. Would work well if team prefers fewer, larger files.

**Tradeoff:** core.py and output.py would be 500-600 lines each - still readable but less granular.

### Deep Nesting (Rejected)

```
filematcher/
    core/
        hashing/
            __init__.py
            algorithms.py
            sparse.py
        directory/
            __init__.py
            indexer.py
            matcher.py
```

**Why rejected:** Over-engineering. Small functions don't need their own modules.

## Migration Path

### Phase 1: Extract types and utils (Low risk)
1. Create `types.py` with GroupLine, SpaceInfo
2. Create `utils.py` with format_file_size
3. Update file_matcher.py imports
4. Run tests

### Phase 2: Extract output subsystem
1. Create `output/color.py` (no internal deps)
2. Create `output/formatting.py` (imports color)
3. Create `output/formatters.py` (imports both)
4. Update file_matcher.py imports
5. Run tests

### Phase 3: Extract core subsystem
1. Create `core/hashing.py`
2. Create `core/directory.py` (imports hashing)
3. Create `core/matching.py`
4. Update file_matcher.py imports
5. Run tests

### Phase 4: Extract actions and logging
1. Create `actions/filesystem.py`
2. Create `actions/executor.py`
3. Create `logging/audit.py`
4. Update file_matcher.py imports
5. Run tests

### Phase 5: Convert cli and finalize
1. Rename file_matcher.py to cli.py
2. Move remaining code (mainly main())
3. Create `__init__.py` with exports
4. Create `__main__.py`
5. Update pyproject.toml
6. Full test run

## Quality Checklist

- [x] Module boundaries are clear and logical - follows existing section structure
- [x] Circular import risks identified - all LOW or NONE risk
- [x] Size/complexity appropriate for each module - 50-500 lines per module
- [x] Test mapping verified - current tests align with proposed modules
- [x] Entry points defined - `__main__.py` and console_scripts
- [x] Public API identified - core functions for library use

## Sources

- [Python Packaging User Guide - Creating CLI Tools](https://packaging.python.org/en/latest/guides/creating-command-line-tools/) - Official entry point documentation
- [Real Python - Python Application Layouts](https://realpython.com/python-application-layouts/) - src-layout patterns
- [The Hitchhiker's Guide to Python - Structuring Your Project](https://docs.python-guide.org/writing/structure/) - Module organization best practices
- [DataCamp - Python Circular Import](https://www.datacamp.com/tutorial/python-circular-import) - Avoiding circular dependencies
- [Medium/Brex - Avoiding Circular Imports in Python](https://medium.com/brexeng/avoiding-circular-imports-in-python-7c35ec8145ed) - Enterprise patterns
- [clig.dev - CLI Guidelines](https://clig.dev/) - CLI design principles

---
*Research completed: 2026-01-27*
