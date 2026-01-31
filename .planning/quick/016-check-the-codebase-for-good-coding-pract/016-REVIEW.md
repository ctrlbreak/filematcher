# Code Quality Review Report

**Project:** filematcher v1.5.0
**Date:** 2026-01-31
**Scope:** filematcher package (~2,947 lines) and tests (~5,470 lines)

---

## 1. Code Duplication

### HIGH PRIORITY

#### 1.1 Massive Duplication in `interactive_execute()` (cli.py:143-283)

**Location:** `filematcher/cli.py` lines 143-283

The `interactive_execute()` function contains the same ~40-line code block repeated 3 times for handling 'y', 'a', and confirm_all cases. Each block performs:
- Get file size
- Handle OSError
- Log operation
- Call execute_action
- Track counts

```python
# Block 1: confirm_all case (lines 143-186)
for dup in duplicates:
    try:
        file_size = os.path.getsize(dup) if os.path.exists(dup) else 0
    except OSError as e:
        formatter.format_file_error(dup, str(e))
        if audit_logger:
            dup_hash = file_hashes.get(dup, "unknown") if file_hashes else "unknown"
            log_operation(audit_logger, action.value, dup, master_file,
                          0, dup_hash, success=False, error=str(e))
        failure_count += 1
        failed_list.append(FailedOperation(dup, str(e)))
        continue
    # ... ~20 more lines

# Block 2: response == 'y' case (lines 191-232) - IDENTICAL
# Block 3: response == 'a' case (lines 238-283) - IDENTICAL
```

**Recommendation:** Extract to helper function:
```python
def _execute_group_duplicates(
    duplicates, master_file, action, formatter, audit_logger,
    file_hashes, fallback_symlink, target_dir, dir2_base
) -> tuple[int, int, int, int, list[FailedOperation]]:
    """Execute action on all duplicates in a group."""
```

#### 1.2 Progress Display Pattern Duplication

**Locations:**
- `filematcher/directory.py` lines 58-91 (in `index_directory`)
- `filematcher/actions.py` lines 167-231 (in `execute_all_actions`)

Both contain nearly identical TTY-aware progress display logic:

```python
# directory.py:71-79
if is_tty:
    progress_line = f"\r[{processed_files}/{total_files}] Processing {filepath.name} ({size_str})"
    term_width = shutil.get_terminal_size().columns
    if len(progress_line) > term_width:
        progress_line = progress_line[:term_width-3] + "..."
    sys.stderr.write(progress_line.ljust(term_width) + '\r')
    sys.stderr.flush()
else:
    logger.debug(...)

# actions.py:200-208 - NEARLY IDENTICAL
```

**Recommendation:** Create shared progress display utility in `colors.py`:
```python
def display_progress(message: str, current: int, total: int, is_tty: bool) -> None:
    """Display progress with TTY-aware formatting."""
```

### MEDIUM PRIORITY

#### 1.3 File Size Retrieval Pattern

**Locations:**
- `filematcher/cli.py` lines 149-159, 196-206, 246-256 (3 times in `interactive_execute`)
- `filematcher/actions.py` lines 189-193

```python
try:
    file_size = os.path.getsize(dup) if os.path.exists(dup) else 0
except OSError as e:
    # error handling
```

**Recommendation:** Use existing `build_file_sizes()` or create `safe_get_file_size()` helper.

---

## 2. Simplification Opportunities

### HIGH PRIORITY

#### 2.1 `main()` Function Complexity (cli.py:401-826)

**Location:** `filematcher/cli.py` lines 401-826

The `main()` function is 425 lines with:
- Argument parsing (lines 403-463)
- Logging setup (lines 467-484)
- Directory matching (lines 489-537)
- Formatter creation (lines 542-557)
- Nested preview output function (lines 559-643)
- Complex branching for preview/execute modes (lines 644-823)

The cyclomatic complexity is high due to deep nesting:
```python
if preview_mode:
    ...
elif execute_mode:
    if args.json:
        ...
    else:
        if args.yes:
            ...
        else:
            # Interactive mode - 60+ lines of setup and execution
```

**Recommendation:** Break into smaller functions:
1. `_parse_and_validate_args()` -> returns validated config dataclass
2. `_setup_logging(config)` -> configures loggers
3. `_run_comparison(config)` -> returns matches, master_results
4. `_run_preview_mode(config, results, formatter)`
5. `_run_execute_mode(config, results, formatter)`

#### 2.2 Action Enum vs String Usage Inconsistency

**Locations:**
- `filematcher/types.py` - defines `Action` enum
- `filematcher/actions.py` - uses string comparisons with enum values
- `filematcher/formatters.py` - uses string comparisons

```python
# actions.py:45 - comparing string to enum
if action == Action.HARDLINK:

# actions.py:114 - comparing passed string to enum
if action == Action.HARDLINK:

# But execute_action signature takes str:
def execute_action(duplicate: str, master: str, action: str, ...) -> ...

# formatters.py:1002 - comparing to enum
if action == Action.COMPARE:
```

The `execute_action` and `execute_all_actions` functions accept `action: str` but compare against `Action` enum members. This works because `Action(str, Enum)` but is confusing.

**Recommendation:** Consistent typing - accept `Action` enum everywhere, convert at CLI boundary.

### MEDIUM PRIORITY

#### 2.3 Nested Conditionals in `determine_color_mode()` (colors.py:178-186)

**Location:** `filematcher/colors.py` lines 178-186

```python
def determine_color_mode(args) -> ColorMode:
    if args.json:
        return ColorMode.NEVER
    if args.color_mode == 'always':
        return ColorMode.ALWAYS
    elif args.color_mode == 'never':
        return ColorMode.NEVER
    return ColorMode.AUTO
```

**Recommendation:** Use dict mapping:
```python
_COLOR_MODE_MAP = {'always': ColorMode.ALWAYS, 'never': ColorMode.NEVER}

def determine_color_mode(args) -> ColorMode:
    if args.json:
        return ColorMode.NEVER
    return _COLOR_MODE_MAP.get(args.color_mode, ColorMode.AUTO)
```

#### 2.4 Label Dictionaries Could Be Consolidated (formatters.py:920-921)

**Location:** `filematcher/formatters.py` lines 920-921

```python
_WOULD_LABELS = {"hardlink": "WOULD HARDLINK", "symlink": "WOULD SYMLINK", "delete": "WOULD DELETE"}
_WILL_LABELS = {"hardlink": "WILL HARDLINK", "symlink": "WILL SYMLINK", "delete": "WILL DELETE"}
```

**Recommendation:** Single dict with computed labels:
```python
def _get_action_label(action: str, will_execute: bool) -> str:
    prefix = "WILL" if will_execute else "WOULD"
    return f"{prefix} {action.upper()}"
```

---

## 3. Python Best Practices

### HIGH PRIORITY

#### 3.1 Type Hint Completeness

**Location:** `filematcher/formatters.py` lines 76, 284, etc.

Several methods have `action: str | None` when they should use `Action | None`:

```python
# formatters.py:76
def __init__(self, ..., action: str | None = None, ...):

# Should be:
def __init__(self, ..., action: Action | None = None, ...):
```

Also, the `JsonActionFormatter._data` dictionary is typed as `dict` without specificity:
```python
# formatters.py:286
self._data: dict = {...}
```

**Recommendation:** Use `TypedDict` or more specific annotations.

#### 3.2 Missing Docstrings

**Locations with missing/incomplete docstrings:**
- `filematcher/cli.py:559` - `print_preview_output()` inner function
- `filematcher/formatters.py:534-543` - `_convert_statistics_to_summary()`
- `filematcher/directory.py:19-23` - `select_oldest()` missing Args/Returns

**Recommendation:** Add Google-style docstrings with Args, Returns, Raises sections.

### MEDIUM PRIORITY

#### 3.3 Unused Import

**Location:** `filematcher/formatters.py` line 17

```python
from pathlib import Path
```

`Path` is used, but this could be flagged by linters if not caught.

#### 3.4 Magic Numbers

**Location:** `filematcher/actions.py` line 144

```python
return 3  # Partial completion
```

The magic number 3 should use a named constant like the ones defined in cli.py:
```python
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_PARTIAL = 2
```

Note: There's an inconsistency - `determine_exit_code` returns 3 for partial, but `cli.py` defines `EXIT_PARTIAL = 2`.

**Recommendation:** Centralize exit codes in `types.py` and use consistently.

#### 3.5 Error Message String Formatting

**Location:** `filematcher/actions.py` lines 62-63

```python
logger.error(f"CRITICAL: Rollback failed for {duplicate}, temp file left as {temp_path}: {rollback_err}")
return (False, f"Failed to create {action}: {e}")
```

Error messages mix f-strings with logging. Consider structured logging for better observability.

---

## 4. Architecture and Design Patterns

### HIGH PRIORITY

#### 4.1 Large `__all__` Export List (89 items)

**Location:** `filematcher/__init__.py` lines 139-229

The package exports 89 items, many of which are internal implementation details:
- ANSI constants (RESET, GREEN, etc.) - 9 items
- Low-level helpers (strip_ansi, visible_len) - internal use only
- Internal functions (build_file_hash_lookup, get_cross_fs_for_hardlink)

This makes the public API unclear and increases API surface area maintenance burden.

**Recommendation:**
1. Define clear public API (~20 items): `main`, `find_matching_files`, `execute_action`, `Action`, `DuplicateGroup`, formatters
2. Keep internal items private (no export)
3. Document public API in `__init__.py` docstring

#### 4.2 Formatter Method Explosion

**Location:** `filematcher/formatters.py` `ActionFormatter` ABC

The `ActionFormatter` class has 15 abstract methods, making it cumbersome to implement new formatters. Many methods are no-ops for `JsonActionFormatter`:

```python
# formatters.py:447, 491-492
def format_empty_result(self) -> None: pass
def format_user_abort(self) -> None: pass
def format_execute_prompt_separator(self) -> None: pass
```

**Recommendation:**
1. Consider splitting into smaller interfaces (Formattable, Interactive, Summary)
2. Or use default implementations in ABC with NotImplementedError for truly required methods

### MEDIUM PRIORITY

#### 4.3 Module Boundary Concerns

`cli.py` imports from all other modules, creating a fan-in pattern. This is acceptable for the CLI entry point, but some functions in `cli.py` could be moved:

- `build_file_hash_lookup()` - belongs in `directory.py`
- `build_file_sizes()` - belongs in `filesystem.py`
- `build_log_flags()` - belongs in `actions.py`

**Recommendation:** Move helper functions to appropriate modules.

#### 4.4 Circular Import Prevention

The current import structure in `__init__.py` uses careful ordering to avoid circular imports. This is fragile.

```python
# __init__.py comments indicate awareness
# This import is safe and has no dependencies on file_matcher
from filematcher.colors import (...)
# This import depends on colors.py and actions.py
from filematcher.formatters import (...)
```

**Recommendation:** Document import order requirements or restructure to eliminate order dependency.

---

## 5. Test Code Quality

### HIGH PRIORITY

#### 5.1 Test Setup Duplication

**Locations:**
- `tests/test_actions.py` lines 35-41, 124-130, 238-245, etc.
- `tests/test_cli.py` similar patterns

Multiple test classes repeat the same setup pattern:
```python
def setUp(self):
    self.temp_dir = tempfile.mkdtemp()
    self.master = Path(self.temp_dir) / "master.txt"
    self.duplicate = Path(self.temp_dir) / "duplicate.txt"

def tearDown(self):
    shutil.rmtree(self.temp_dir)
```

**Recommendation:** Create additional base classes or mixins:
```python
class TempDirTestCase(unittest.TestCase):
    """Provides temp directory with automatic cleanup."""

class MasterDuplicateTestCase(TempDirTestCase):
    """Provides master and duplicate file setup."""
```

#### 5.2 Helper Method Inconsistency

**Location:** `tests/test_cli.py`

Two nearly identical helper methods:
```python
def run_main_with_args(self, args: list[str]) -> str:  # line 19
def run_main_capture_all(self, args: list[str]) -> tuple[str, str]:  # line 26
```

And `TestActionExecution` has its own:
```python
def run_main_capture_output(self) -> tuple[str, int]:  # line 168
```

**Recommendation:** Consolidate into `BaseFileMatcherTest`:
```python
def run_main(self, args: list[str], capture_stderr: bool = False) -> MainResult:
```

### MEDIUM PRIORITY

#### 5.3 Test File Organization

Test files range from 64 lines (`test_base.py`) to 700+ lines (`test_actions.py`). Consider splitting larger test files by functionality.

#### 5.4 Missing Edge Case Tests

Based on code review, some edge cases may lack tests:
- `safe_replace_with_link` rollback failure path (line 59-62)
- `get_sparse_hash` with exactly 3*sample_size file
- `terminal_rows_for_line` with zero-length string

**Recommendation:** Add edge case tests during future development.

---

## Summary of Priorities

### High Priority (Address Soon)
| Issue | Location | Impact |
|-------|----------|--------|
| `interactive_execute()` duplication | cli.py:143-283 | Maintainability |
| `main()` function complexity | cli.py:401-826 | Readability, Testing |
| Action enum/string inconsistency | Multiple files | Type safety |
| Large `__all__` export list | __init__.py | API clarity |
| Test setup duplication | tests/*.py | Test maintainability |

### Medium Priority (Address When Convenient)
| Issue | Location | Impact |
|-------|----------|--------|
| Progress display duplication | directory.py, actions.py | Code reuse |
| Exit code inconsistency | actions.py:144 vs cli.py:32 | Correctness |
| Module boundary concerns | cli.py helpers | Architecture |
| Test helper inconsistency | test_cli.py | Test clarity |

### Low Priority (Nice to Have)
| Issue | Location | Impact |
|-------|----------|--------|
| Nested conditionals | colors.py:178-186 | Readability |
| Label dict consolidation | formatters.py:920-921 | Minor cleanup |
| Missing docstrings | Various | Documentation |
| Magic numbers | actions.py:144 | Code clarity |

---

## Recommendations Summary

1. **Extract helper function** from `interactive_execute()` to eliminate 120 lines of duplication
2. **Refactor `main()`** into 5 smaller functions for improved testability
3. **Standardize Action enum usage** across all modules
4. **Reduce public API surface** in `__init__.py` to ~20 essential exports
5. **Create test base classes** for common setup patterns
6. **Fix exit code inconsistency** between `determine_exit_code()` and CLI constants

These changes would significantly improve maintainability without changing external behavior.
