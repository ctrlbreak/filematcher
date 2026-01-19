# Phase 2: Dry-Run Preview & Statistics - Research

**Researched:** 2026-01-19
**Domain:** Python CLI output formatting, filesystem statistics, cross-device detection
**Confidence:** HIGH

## Summary

This phase adds a `--dry-run` flag to preview planned deduplication actions and display comprehensive statistics before any modifications occur. The implementation builds on Phase 1's master/duplicate identification infrastructure.

Key components:
1. **Output Format Refactoring:** Transition from Phase 1's arrow notation (`master -> dup1, dup2`) to the new `[MASTER]`/`[DUP]` indented format
2. **Dry-Run Mode:** New `--dry-run` flag that displays what would happen without making changes
3. **Statistics Calculation:** Compute and display duplicate counts, affected files, and space savings
4. **Cross-Filesystem Detection:** Proactively warn about hardlink limitations across filesystems

All functionality uses Python standard library. The main complexity is coordinating multiple output modes (`--dry-run`, `--summary`, `--verbose`) and implementing the new hierarchical output format.

**Primary recommendation:** Refactor output formatting into dedicated functions, use `os.stat().st_dev` for cross-filesystem detection, and compute space savings by summing duplicate file sizes.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `argparse` | stdlib | CLI argument parsing | Already used; supports mutually exclusive groups |
| `os` | stdlib | File stats via `os.stat()`, size via `os.path.getsize()` | Cross-platform filesystem operations |
| `pathlib` | stdlib | Path manipulation | Already used throughout codebase |
| `sys` | stdlib | stdout/stderr output | Standard interface |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `logging` | stdlib | Debug/verbose output | Already used for `--verbose` mode |
| `errno` | stdlib | Error code constants (EXDEV) | Cross-device link detection |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `os.stat().st_dev` | Try `os.link()` and catch EXDEV | Proactive detection better than fail-and-recover |
| Manual size formatting | External library (humanize) | Keep standard library only per project convention |

**Installation:**
```bash
# No additional packages required - all standard library
```

## Architecture Patterns

### Recommended Project Structure
```
file_matcher.py          # Single-file implementation (existing pattern)
    # Refactor: format_master_output() -> format_duplicate_group()
    # Add: format_dry_run_banner()
    # Add: format_statistics_footer()
    # Add: calculate_space_savings()
    # Add: check_cross_filesystem()
    # Modify: main() for --dry-run flag and new output format
```

### Pattern 1: Hierarchical Output Formatting (Phase 2 Target Format)
**What:** Group output with `[MASTER]` prefix and indented `[DUP:action]` lines
**When to use:** All master-mode output (replaces arrow notation from Phase 1)
**Example:**
```python
# Target output format per CONTEXT.md decisions
def format_duplicate_group(
    master_file: str,
    duplicates: list[str],
    action: str | None = None,  # None, "hardlink", "symlink", "delete"
    verbose: bool = False,
    file_sizes: dict[str, int] | None = None,
    cross_fs_files: set[str] | None = None
) -> list[str]:
    """
    Format a duplicate group for display.

    Returns list of formatted lines:
    [MASTER] /path/to/master/file.txt
        [DUP:hardlink] /path/to/dup1.txt
        [DUP:hardlink] /path/to/dup2.txt [!cross-fs]
    """
    lines = []

    # Master line
    master_line = f"[MASTER] {master_file}"
    if verbose and file_sizes:
        size = file_sizes.get(master_file, 0)
        master_line += f" ({len(duplicates)} duplicates, {format_file_size(size)})"
    lines.append(master_line)

    # Duplicate lines (indented)
    action_label = action if action else "?"
    for dup in sorted(duplicates):
        dup_line = f"    [DUP:{action_label}] {dup}"
        if cross_fs_files and dup in cross_fs_files:
            dup_line += " [!cross-fs]"
        lines.append(dup_line)

    return lines
```

### Pattern 2: Cross-Filesystem Detection
**What:** Check if two files are on different filesystems before hardlink operations
**When to use:** When `--action hardlink` is specified, detect problematic cases proactively
**Example:**
```python
# Source: https://docs.python.org/3/library/os.html (st_dev)
import os

def get_device_id(path: str) -> int:
    """Get the device ID for a file's filesystem."""
    return os.stat(path).st_dev

def check_cross_filesystem(master_file: str, duplicates: list[str]) -> set[str]:
    """
    Check which duplicates are on different filesystems than master.

    Returns set of duplicate paths that cannot be hardlinked to master.
    """
    cross_fs = set()
    master_dev = get_device_id(master_file)

    for dup in duplicates:
        try:
            if get_device_id(dup) != master_dev:
                cross_fs.add(dup)
        except OSError:
            # File may have been deleted; treat as cross-fs for safety
            cross_fs.add(dup)

    return cross_fs
```

### Pattern 3: Space Savings Calculation
**What:** Calculate how much disk space would be saved by deduplication
**When to use:** Dry-run statistics, summary output
**Example:**
```python
import os

def calculate_space_savings(
    duplicate_groups: list[tuple[str, list[str]]]
) -> tuple[int, int, int]:
    """
    Calculate space that would be saved by deduplication.

    Args:
        duplicate_groups: List of (master_file, duplicates_list) tuples

    Returns:
        Tuple of (total_duplicate_bytes, duplicate_file_count, group_count)
    """
    total_bytes = 0
    total_files = 0

    for master, duplicates in duplicate_groups:
        if not duplicates:
            continue
        # All duplicates have same size as master
        file_size = os.path.getsize(master)
        # Space saved = size * number_of_duplicates
        total_bytes += file_size * len(duplicates)
        total_files += len(duplicates)

    return total_bytes, total_files, len(duplicate_groups)
```

### Pattern 4: Dry-Run Banner and Footer
**What:** Clear visual indicators that no changes will be made
**When to use:** When `--dry-run` flag is present
**Example:**
```python
DRY_RUN_BANNER = "=== DRY RUN - No changes will be made ==="

def format_dry_run_banner() -> str:
    """Return the dry-run header banner."""
    return DRY_RUN_BANNER

def format_statistics_footer(
    group_count: int,
    duplicate_count: int,
    master_count: int,
    space_savings: int,
    verbose: bool = False
) -> list[str]:
    """
    Format the statistics footer for dry-run output.

    Returns list of lines for the footer.
    """
    lines = [
        "",
        "--- Statistics ---",
        f"Duplicate groups: {group_count}",
        f"Master files preserved: {master_count}",
        f"Duplicate files: {duplicate_count}",
        f"Space to be reclaimed: {format_file_size(space_savings)}",
    ]
    if verbose:
        lines.append(f"  ({space_savings:,} bytes)")
    return lines
```

### Pattern 5: CLI Flag Interaction
**What:** `--dry-run` requires `--master`, optionally takes `--action`
**When to use:** Argument validation in main()
**Example:**
```python
# In argument parsing
parser.add_argument('--dry-run', '-n', action='store_true',
                    help='Preview changes without executing them')
parser.add_argument('--action', '-a', choices=['hardlink', 'symlink', 'delete'],
                    help='Action to take on duplicates (used with --dry-run)')

# Validation after parsing
if args.dry_run and not args.master:
    parser.error("--dry-run requires --master to be specified")
```

### Anti-Patterns to Avoid
- **Mixing output modes in single function:** Keep banner, groups, and footer formatting separate
- **Computing stats during output:** Calculate all statistics before printing to enable running totals
- **Silent cross-fs failures:** Always warn proactively when hardlinks won't work
- **Changing behavior without `--dry-run`:** Existing non-dry-run output must remain unchanged

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| File size formatting | Custom division/rounding | Existing `format_file_size()` | Already in codebase, handles edge cases |
| Device detection | Parse mount tables | `os.stat().st_dev` | Cross-platform, simple integer comparison |
| Path sorting | Custom comparators | `sorted()` on strings | Alphabetical sorting per CONTEXT.md |
| CLI argument validation | Custom if/else chains | `parser.error()` | Consistent error format, exit code 2 |

**Key insight:** The existing `format_file_size()` function handles human-readable size formatting. Reuse it for space savings display.

## Common Pitfalls

### Pitfall 1: Output Format Regression
**What goes wrong:** Changing Phase 1 output format breaks existing tests and user expectations
**Why it happens:** Refactoring output without maintaining backward compatibility
**How to avoid:** The refactoring to `[MASTER]`/`[DUP]` format should be a separate prep task before Phase 2 implementation. Update tests first to expect new format.
**Warning signs:** Test failures mentioning "arrow notation" or "->"

### Pitfall 2: Space Savings Miscalculation
**What goes wrong:** Counting space savings incorrectly (e.g., including master file size)
**Why it happens:** Confusion about what "savings" means
**How to avoid:** Space saved = sum of duplicate file sizes only. Master is preserved, not deleted.
**Warning signs:** Stats show savings greater than total duplicate space

### Pitfall 3: Cross-Filesystem False Negatives
**What goes wrong:** Not detecting cross-fs case until actual hardlink fails
**Why it happens:** Checking st_dev only on duplicates, not master
**How to avoid:** Compare each duplicate's st_dev against master's st_dev
**Warning signs:** Hardlink operations fail with EXDEV in Phase 3

### Pitfall 4: Verbose Mode Inconsistency
**What goes wrong:** `--verbose` output differs between dry-run and normal modes
**Why it happens:** Different code paths for each mode
**How to avoid:** Extract verbose formatting into shared functions
**Warning signs:** Users report different information in verbose dry-run vs verbose execution

### Pitfall 5: Summary Mode Interaction
**What goes wrong:** `--dry-run --summary` shows different stats than `--dry-run` alone
**Why it happens:** Summary mode and dry-run have separate stat calculations
**How to avoid:** Single source of truth for statistics; summary mode just omits file listing
**Warning signs:** Different numbers in summary vs detailed output

### Pitfall 6: Action Preview Without Action
**What goes wrong:** `--dry-run` without `--action` shows `[DUP:?]` which confuses users
**Why it happens:** User forgets to specify action
**How to avoid:** Per CONTEXT.md, this is the intended behavior. Document clearly that `[DUP:?]` means "action not specified"
**Warning signs:** Users asking "what does ? mean?"

## Code Examples

Verified patterns from official sources and existing codebase:

### Cross-Filesystem Detection
```python
# Source: https://docs.python.org/3/library/os.html
import os

def files_on_same_filesystem(path1: str, path2: str) -> bool:
    """Check if two files are on the same filesystem."""
    try:
        stat1 = os.stat(path1)
        stat2 = os.stat(path2)
        return stat1.st_dev == stat2.st_dev
    except OSError:
        return False  # Assume cross-fs if we can't stat
```

### Argparse Mutually Exclusive Groups (if needed)
```python
# Source: https://docs.python.org/3/library/argparse.html
# Note: Not needed for Phase 2 as --dry-run and --action can coexist

parser = argparse.ArgumentParser()
# --dry-run can be used alone or with --action
parser.add_argument('--dry-run', '-n', action='store_true')
parser.add_argument('--action', '-a', choices=['hardlink', 'symlink', 'delete'])

# Validation: --action without --dry-run is fine (Phase 3)
# --dry-run without --action shows [DUP:?] placeholder
```

### Statistics Collection Pattern
```python
# Pattern from existing main() refactored for reuse
def collect_duplicate_statistics(
    matches: dict[str, tuple[list[str], list[str]]],
    master_path: Path
) -> list[tuple[str, list[str], str]]:
    """
    Process matches into master/duplicate pairs with statistics.

    Returns list of (master_file, duplicates, selection_reason) tuples.
    """
    results = []
    for file_hash, (files1, files2) in matches.items():
        all_files = files1 + files2
        master_file, duplicates, reason = select_master_file(all_files, master_path)
        results.append((master_file, duplicates, reason))
    return results
```

### File Size Aggregation
```python
# Using existing format_file_size from file_matcher.py
import os

def get_total_duplicate_size(
    duplicate_groups: list[tuple[str, list[str]]]
) -> int:
    """
    Calculate total size of all duplicate files.

    Args:
        duplicate_groups: List of (master_file, duplicates) tuples

    Returns:
        Total bytes that would be saved
    """
    total = 0
    for master, duplicates in duplicate_groups:
        if duplicates:
            # All duplicates same size as master
            size = os.path.getsize(master)
            total += size * len(duplicates)
    return total
```

### Test Pattern for Output Verification
```python
# Following existing test_cli.py pattern
from unittest.mock import patch
import io
from contextlib import redirect_stdout

class TestDryRunOutput(BaseFileMatcherTest):
    def test_dry_run_banner_displayed(self):
        """Verify dry-run banner appears at top of output."""
        with patch('sys.argv', [
            'file_matcher.py', self.test_dir1, self.test_dir2,
            '--master', self.test_dir1, '--dry-run'
        ]):
            output = self.run_main_with_args([])
            # Banner should be first non-empty line
            self.assertIn("DRY RUN", output)
            self.assertIn("No changes will be made", output)

    def test_dry_run_statistics_footer(self):
        """Verify statistics appear in footer."""
        with patch('sys.argv', [
            'file_matcher.py', self.test_dir1, self.test_dir2,
            '--master', self.test_dir1, '--dry-run'
        ]):
            output = self.run_main_with_args([])
            self.assertIn("Duplicate groups:", output)
            self.assertIn("Space to be reclaimed:", output)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Arrow notation (`->`) | `[MASTER]`/`[DUP]` prefixes | Phase 2 prep | More structured, supports actions |
| Inline statistics | Footer-only statistics | Phase 2 | Cleaner output, running totals |
| No cross-fs detection | Proactive `st_dev` check | Phase 2 | Warns before Phase 3 execution |

**Deprecated/outdated:**
- Arrow notation output: Will be replaced in Phase 2 prep task
- No explicit action preview: `[DUP:?]` placeholder added for clarity

## Open Questions

Things that couldn't be fully resolved:

1. **Running Totals Format**
   - What we know: CONTEXT.md says "footer only, with inline running totals as groups are shown"
   - What's unclear: Exact format of running totals (every group? every N groups?)
   - Recommendation: Show running total after each group in verbose mode only; keep output clean in normal mode

2. **Warning Aggregation**
   - What we know: Warnings shown inline AND in summary
   - What's unclear: Whether to deduplicate warnings (same warning for multiple files)
   - Recommendation: Show inline per-file, then summary count at end

3. **Action-Specific Statistics**
   - What we know: Stats should be action-aware ("X files would become links")
   - What's unclear: Exact wording for each action type
   - Recommendation: Planner decides wording; keep it concise

## Sources

### Primary (HIGH confidence)
- [Python os module documentation](https://docs.python.org/3/library/os.html) - `os.stat()`, `st_dev`, `os.link()`, EXDEV handling
- [Python stat module documentation](https://docs.python.org/3/library/stat.html) - `ST_DEV`, `ST_INO` constants
- [Python errno module documentation](https://docs.python.org/3/library/errno.html) - `EXDEV` cross-device link error
- [Python argparse documentation](https://docs.python.org/3/library/argparse.html) - argument groups, validation
- Existing codebase: `file_matcher.py` - `format_file_size()`, `select_master_file()`, output patterns
- Phase 1 implementation: Established patterns for CLI, testing, output formatting

### Secondary (MEDIUM confidence)
- [zetcode os.stat guide](https://zetcode.com/python/os-stat/) - `st_dev` usage examples
- [GitHub gist: hard link detection](https://gist.github.com/simonw/229186) - `st_dev` + `st_ino` comparison pattern

### Tertiary (LOW confidence)
- None - all Phase 2 functionality is well-documented in standard library

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all standard library, already used in codebase
- Architecture patterns: HIGH - patterns from existing code and official docs
- Cross-filesystem detection: HIGH - well-documented `st_dev` approach
- Output formatting: MEDIUM - some details left to planner discretion per CONTEXT.md

**Research date:** 2026-01-19
**Valid until:** 60 days (stable standard library, unlikely to change)
