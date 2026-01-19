# Phase 1: Master Directory Foundation - Research

**Researched:** 2026-01-19
**Domain:** Python CLI argument handling, path resolution, file timestamps
**Confidence:** HIGH

## Summary

This phase adds a `--master` flag to designate one directory as authoritative. The implementation involves:
1. Adding a new argparse argument for `--master`
2. Validating that the master path matches one of the compared directories
3. Modifying output formatting to show master/duplicate relationships
4. Using file timestamps to resolve duplicates within the master directory

The codebase already uses argparse, pathlib, and the logging module extensively. All required functionality is available in Python's standard library (Python 3.9+). The main complexity is path comparison (ensuring `./dir`, `../parent/dir`, and `/absolute/dir` all match correctly) and the output format changes.

**Primary recommendation:** Use `Path.resolve()` for canonical path comparison, `parser.error()` for validation failures (exit code 2), and `os.path.getmtime()` for timestamp-based master selection within duplicate sets.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `argparse` | stdlib | CLI argument parsing | Already used in codebase; official Python CLI tool |
| `pathlib` | stdlib | Path manipulation and resolution | Modern, object-oriented path handling |
| `os.path` | stdlib | Path comparison (`samefile`) | Filesystem-level path comparison |
| `sys` | stdlib | stderr output, exit codes | Standard interface for program I/O |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `os` | stdlib | File timestamps via `os.path.getmtime()` | For timestamp-based master selection |
| `logging` | stdlib | Debug/verbose output | Already used in codebase for `--verbose` mode |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `Path.resolve()` | `os.path.realpath()` | Both resolve symlinks; `Path.resolve()` integrates with pathlib used elsewhere |
| `os.path.samefile()` | String comparison after resolve | `samefile()` is authoritative but requires filesystem access |
| `parser.error()` | Custom error + `sys.exit()` | `parser.error()` provides consistent argparse error formatting |

**Installation:**
```bash
# No additional packages required - all standard library
```

## Architecture Patterns

### Recommended Project Structure
```
file_matcher.py          # Single-file implementation (existing pattern)
    # Add: validate_master_directory() function
    # Modify: find_matching_files() signature and return value
    # Modify: main() for new output formatting
```

### Pattern 1: Path Canonicalization for Comparison
**What:** Use `Path.resolve()` to normalize all path inputs before comparison
**When to use:** Validating `--master` against `dir1` and `dir2`
**Example:**
```python
# Source: https://docs.python.org/3/library/pathlib.html
from pathlib import Path

def validate_master_directory(master: str, dir1: str, dir2: str) -> Path:
    """
    Validate master is one of the compared directories.
    Returns the resolved master path, or raises ValueError.
    """
    master_resolved = Path(master).resolve()
    dir1_resolved = Path(dir1).resolve()
    dir2_resolved = Path(dir2).resolve()

    if master_resolved == dir1_resolved:
        return master_resolved
    if master_resolved == dir2_resolved:
        return master_resolved

    raise ValueError("Master must be one of the compared directories")
```

### Pattern 2: Argparse Validation with error()
**What:** Use `parser.error()` for argument validation failures
**When to use:** When `--master` path is invalid or not a compared directory
**Example:**
```python
# Source: https://docs.python.org/3/library/argparse.html
def main() -> int:
    parser = argparse.ArgumentParser(...)
    parser.add_argument('--master', '-m',
                        help='Designate one directory as master')
    args = parser.parse_args()

    if args.master:
        try:
            master_path = validate_master_directory(
                args.master, args.dir1, args.dir2
            )
        except ValueError as e:
            parser.error(str(e))  # Exits with code 2
```

### Pattern 3: Timestamp-Based Master Selection
**What:** Use file modification time to select master among duplicates in master directory
**When to use:** When same content appears multiple times in master directory
**Example:**
```python
# Source: https://docs.python.org/3/library/os.path.html
import os

def select_master_file(file_paths: list[str]) -> str:
    """
    Select the oldest file as master from a list of duplicate files.
    Returns the path with the earliest modification time.
    """
    return min(file_paths, key=lambda p: os.path.getmtime(p))
```

### Pattern 4: CLI Testing with sys.argv Patching
**What:** Use `unittest.mock.patch` on sys.argv for CLI tests
**When to use:** Testing argument parsing and validation
**Example:**
```python
# Source: Existing pattern in tests/test_cli.py
from unittest.mock import patch

def test_master_validation(self):
    with patch('sys.argv', ['file_matcher.py',
                           self.test_dir1, self.test_dir2,
                           '--master', self.test_dir1]):
        output = self.run_main_with_args([])
        # assertions
```

### Anti-Patterns to Avoid
- **String comparison for paths:** Never compare paths as strings; use `Path.resolve()` comparison or `os.path.samefile()`
- **Exit code 1 for argument errors:** Argparse convention is exit code 2 for argument errors; use `parser.error()` for consistency
- **Printing errors to stdout:** Errors should go to stderr; use `parser.error()` which handles this automatically

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Path normalization | Custom string manipulation | `Path.resolve()` | Handles symlinks, `..`, `.`, platform differences |
| Path equality | String comparison | `Path.resolve()` comparison | Same path can have many string representations |
| CLI error messages | Custom print + sys.exit | `parser.error()` | Consistent format, correct exit code, goes to stderr |
| File timestamps | Custom stat parsing | `os.path.getmtime()` | Cross-platform, handles edge cases |
| Argument parsing | Custom parsing | `argparse` | Already in use, battle-tested |

**Key insight:** Path comparison is deceptively complex. `./dir`, `dir`, `/full/path/to/dir`, and `/full/path/to/../path/to/dir` can all refer to the same directory. Never use string comparison.

## Common Pitfalls

### Pitfall 1: Path String Comparison
**What goes wrong:** `"./dir1" != "/Users/user/project/dir1"` even when they're the same directory
**Why it happens:** Paths can be expressed many ways; string comparison is naive
**How to avoid:** Always resolve paths before comparison: `Path(p1).resolve() == Path(p2).resolve()`
**Warning signs:** Tests pass with absolute paths but fail with relative paths

### Pitfall 2: Symlink Handling in Path Comparison
**What goes wrong:** A symlink to the master directory isn't recognized as master
**Why it happens:** Without resolution, symlink path differs from target path
**How to avoid:** `Path.resolve()` follows symlinks by default; this is the desired behavior per CONTEXT.md
**Warning signs:** User provides symlinked path and gets "not a compared directory" error

### Pitfall 3: Exit Code Inconsistency
**What goes wrong:** Using exit code 1 for argument errors breaks scripts expecting argparse conventions
**Why it happens:** Developer manually calls `sys.exit(1)` instead of `parser.error()`
**How to avoid:** Use `parser.error()` which exits with code 2 for argument errors
**Warning signs:** Tool behavior differs from other argparse-based tools

### Pitfall 4: Timestamp Cross-Platform Issues
**What goes wrong:** Creation time (`st_ctime`) means different things on Windows vs Unix
**Why it happens:** On Unix, `st_ctime` is metadata change time, not creation time
**How to avoid:** Use modification time (`st_mtime`) via `os.path.getmtime()` - it's consistent cross-platform and is what CONTEXT.md specifies ("oldest file by timestamp")
**Warning signs:** Different behavior on macOS/Linux vs Windows

### Pitfall 5: Output Mode Interaction
**What goes wrong:** `--master` output format not properly integrated with `--summary`, `--verbose`
**Why it happens:** Each output mode has different formatting requirements
**How to avoid:** Plan output format for all combinations: default, `--summary`, `--verbose`, `--show-unmatched`
**Warning signs:** Inconsistent or broken output with flag combinations

## Code Examples

Verified patterns from official sources:

### Path Resolution and Comparison
```python
# Source: https://docs.python.org/3/library/pathlib.html
from pathlib import Path

# Resolves symlinks and normalizes path
p = Path('./subdir/../file.txt')
canonical = p.resolve()  # Returns absolute path with symlinks resolved

# Compare paths for equality
path1 = Path('/some/./path/../path/to/dir').resolve()
path2 = Path('/some/path/to/dir').resolve()
assert path1 == path2  # True - same canonical path
```

### Argparse Error Handling
```python
# Source: https://docs.python.org/3/library/argparse.html
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--master', help='Master directory')

args = parser.parse_args()

if args.master and not is_valid_master(args.master):
    parser.error("Master must be one of the compared directories")
    # Prints to stderr: "usage: prog [-h] ..."
    #                   "prog: error: Master must be one of the compared directories"
    # Exits with code 2
```

### File Modification Time
```python
# Source: https://docs.python.org/3/library/os.path.html
import os

# Get modification time as Unix timestamp
mtime = os.path.getmtime('/path/to/file')

# Find oldest file in a list
oldest = min(file_list, key=os.path.getmtime)
```

### Printing to stderr
```python
# Source: Python documentation
import sys

# Method 1: print with file parameter
print("Error message", file=sys.stderr)

# Method 2: direct write (no newline added)
sys.stderr.write("Error message\n")
```

### Testing CLI Arguments
```python
# Source: Existing pattern in tests/test_cli.py
from unittest.mock import patch
import sys

class TestMasterDirectory(BaseFileMatcherTest):
    def test_master_flag_valid(self):
        with patch('sys.argv', ['file_matcher.py',
                               self.test_dir1, self.test_dir2,
                               '--master', self.test_dir1]):
            result = main()
            self.assertEqual(result, 0)

    def test_master_flag_invalid(self):
        with patch('sys.argv', ['file_matcher.py',
                               self.test_dir1, self.test_dir2,
                               '--master', '/some/other/dir']):
            with self.assertRaises(SystemExit) as cm:
                main()
            self.assertEqual(cm.exception.code, 2)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `os.path.abspath()` | `Path.resolve()` | pathlib mature (Python 3.4+) | Prefer pathlib for new code |
| Manual argument parsing | `argparse` | Python 2.7+ | Standard for all CLI tools |
| `os.path.realpath()` | `Path.resolve()` | pathlib preferred | Either works; resolve() is more Pythonic |

**Deprecated/outdated:**
- `argparse.FileType`: Deprecated in 3.14, but not relevant here (we use paths, not file handles)
- Nested mutually exclusive groups: Removed in 3.14, but not needed for this feature

## Open Questions

Things that couldn't be fully resolved:

1. **Arrow notation exact format**
   - What we know: CONTEXT.md specifies `/master/file.txt -> /dup/file.txt, /dup/other.txt`
   - What's unclear: Whether to show relative or absolute paths; whether to truncate long paths
   - Recommendation: Use paths consistent with current output (absolute); planner decides on truncation

2. **Multiple masters warning wording**
   - What we know: CONTEXT.md says "Warn about it, but continue"
   - What's unclear: Exact message format; whether to list all files or just indicate count
   - Recommendation: Keep it simple, e.g., "Warning: Multiple files in master directory have identical content"

3. **Verbose mode resolution reasoning format**
   - What we know: Should show "which file chosen and why"
   - What's unclear: Exact format for verbose output
   - Recommendation: Align with existing verbose patterns in codebase; planner decides specifics

## Sources

### Primary (HIGH confidence)
- [Python pathlib documentation](https://docs.python.org/3/library/pathlib.html) - `Path.resolve()`, `samefile()` methods
- [Python argparse documentation](https://docs.python.org/3/library/argparse.html) - `parser.error()`, exit codes, type functions
- [Python os.path documentation](https://docs.python.org/3/library/os.path.html) - `samefile()`, `realpath()`, `getmtime()`
- Existing codebase: `file_matcher.py`, `tests/test_cli.py` - established patterns

### Secondary (MEDIUM confidence)
- [Argparse testing patterns](https://jugmac00.github.io/blog/testing-argparse-applications-the-better-way/) - sys.argv mocking patterns
- [Python stderr best practices](https://learnpython.com/blog/python-standard-error-stream/) - error output patterns

### Tertiary (LOW confidence)
- Exit code conventions - while BSD sysexits defines codes, the argparse convention (exit 2 for errors) is authoritative for this context

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all standard library, already used in codebase
- Architecture: HIGH - patterns verified against official docs and existing code
- Pitfalls: HIGH - common issues documented in official Python docs

**Research date:** 2026-01-19
**Valid until:** 60 days (stable standard library, unlikely to change)
