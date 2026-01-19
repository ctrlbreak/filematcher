# Coding Conventions

**Analysis Date:** 2025-01-19

## Naming Patterns

**Files:**
- Main module: `snake_case.py` (e.g., `file_matcher.py`)
- Test files: `test_*.py` prefix (e.g., `test_file_hashing.py`, `test_cli.py`)
- Utility scripts: `snake_case.py` (e.g., `run_tests.py`, `create_release.py`)

**Functions:**
- `snake_case` for all functions (e.g., `get_file_hash`, `find_matching_files`, `format_file_size`)
- Verb-first naming: `get_*`, `find_*`, `index_*`, `format_*`
- Private functions: Not used in this codebase (no underscore prefix)

**Variables:**
- `snake_case` for all variables (e.g., `file_size`, `hash_to_files`, `size_threshold`)
- Descriptive names preferred over abbreviations
- Loop variables: single letter acceptable for simple iterations (`f`, `h`, `i`)

**Types:**
- Type hints use Python 3.9+ style: `list[str]`, `dict[str, list[str]]`
- Union types: `str | Path`, `int | float`, `int | None`
- Classes: `PascalCase` (e.g., `BaseFileMatcherTest`, `TestCLI`)

**Constants:**
- Inline numeric constants with comments explaining purpose
- No module-level constant definitions (values passed as parameters)
- Default thresholds: `100*1024*1024` (100MB), `4096` (chunk size), `1024*1024` (sample size)

## Code Style

**Formatting:**
- No automated formatter configured (no `.prettierrc`, `black.toml`, etc.)
- 4-space indentation (Python standard)
- Line length: approximately 100-120 characters observed
- Single blank line between functions within a file
- Two blank lines not enforced

**Linting:**
- No linter configuration files present (no `.flake8`, `ruff.toml`, `pylint.rc`)
- Type hints present but no mypy configuration (`.mypy_cache` exists from ad-hoc runs)

## Import Organization

**Order:**
1. Future imports (`from __future__ import annotations`)
2. Standard library imports (alphabetical: `argparse`, `hashlib`, `logging`, `os`, `sys`)
3. Third-party imports (none used - stdlib only project)
4. Local imports (`from file_matcher import ...`, `from tests.test_base import ...`)

**Style:**
- `import module` for standard library modules
- `from module import function` for specific items
- No wildcard imports (`from x import *`)

**Path Aliases:**
- None configured
- Tests use `sys.path.insert(0, ...)` in `tests/__init__.py` for import resolution

## Error Handling

**Patterns:**
- Use `try/except` with specific exception types:
  ```python
  except (PermissionError, OSError) as e:
      logger.error(f"Error processing {filepath}: {e}")
  ```
- Raise `ValueError` for invalid arguments:
  ```python
  raise ValueError(f"Unsupported hash algorithm: {hash_algorithm}")
  ```
- Return exit codes from `main()`: `0` for success, `1` for error
- Early validation with early return:
  ```python
  if not os.path.isdir(args.dir1) or not os.path.isdir(args.dir2):
      logger.error("Error: Both arguments must be directories")
      return 1
  ```

**Error Messages:**
- Include context: file path, variable value in error message
- Use f-strings for interpolation
- Prefix user-facing errors with "Error:"

## Logging

**Framework:** Standard library `logging` module

**Setup Pattern:**
```python
import logging
logger = logging.getLogger(__name__)

# In main():
log_level = logging.DEBUG if args.verbose else logging.INFO
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(message)s'))
logger.handlers = [handler]
logger.setLevel(log_level)
```

**Usage Guidelines:**
- `logger.error()` - For errors that prevent operation
- `logger.info()` - For status messages (algorithm choice, mode enabled)
- `logger.debug()` - For verbose progress (file processing, counts)
- `print()` - For program output/results (matches, summaries)

**Key Distinction:**
- Logging is for status/debug information
- Print is for actual program results

## Comments

**When to Comment:**
- Module-level docstring required (purpose, version)
- Function docstrings with Args/Returns sections
- Inline comments for non-obvious logic

**Docstring Format:**
```python
def function_name(param1: type, param2: type) -> return_type:
    """
    Brief description of what the function does.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value
    """
```

**Inline Comments:**
- Placed on same line for short explanations: `h = hashlib.md5()  # Faster but less secure`
- Placed above for block explanations

## Function Design

**Size:**
- Functions range from 10-50 lines
- `main()` is longest at ~90 lines (handles all CLI logic)
- Single responsibility: one function per major operation

**Parameters:**
- Use type hints for all parameters
- Default values for optional parameters
- Boolean flags for modes: `fast_mode: bool = False`, `verbose: bool = False`
- Path parameters accept `str | Path` union type

**Return Values:**
- Use type hints for return types
- Functions return single values or tuples for multiple outputs
- Complex returns: `tuple[dict[str, tuple[list[str], list[str]]], list[str], list[str]]`
- Exit codes: `int` from `main()`

## Module Design

**Exports:**
- No `__all__` definition (all public functions available)
- All functions at module level (no classes in main module)

**Barrel Files:**
- Not used
- `tests/__init__.py` handles path setup only

**Single-File Architecture:**
- Core logic in single file: `file_matcher.py`
- No package structure for main code
- Tests in separate `tests/` directory

## Argument Parsing

**Pattern:**
```python
parser = argparse.ArgumentParser(description='...')
parser.add_argument('positional', help='...')
parser.add_argument('--flag', '-f', action='store_true', help='...')
parser.add_argument('--option', '-o', choices=['a', 'b'], default='a', help='...')
args = parser.parse_args()
```

**Naming:**
- Long form: `--show-unmatched`, `--hash`, `--summary`, `--fast`, `--verbose`
- Short form: single letter `-u`, `-H`, `-s`, `-f`, `-v`
- Positional: plain names `dir1`, `dir2`

## File I/O

**Reading Files:**
```python
with open(filepath, 'rb') as f:
    for chunk in iter(lambda: f.read(4096), b''):
        h.update(chunk)
```

**Writing Files:**
```python
with open(path, "w") as f:
    f.write(content)
```

**Path Handling:**
- Use `pathlib.Path` for modern operations
- Use `os.path` for compatibility checks (`os.path.isdir`, `os.path.getsize`)
- Store paths as absolute strings in results

---

*Convention analysis: 2025-01-19*
