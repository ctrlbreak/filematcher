# Architecture: Unified Output Formatting

**Domain:** CLI tool output formatting (text and JSON)
**Researched:** 2026-01-22
**Focus:** Unifying scattered output formatting for compare mode and action mode

## Current State Analysis

### Existing Output Code Paths

The current implementation has output code scattered throughout `main()`:

```
Lines 1045-1152: Master/action mode output (preview)
Lines 1158-1227: Master/action mode output (execute)
Lines 1228-1276: Master/compare mode output (no action)
Lines 1295-1340: Original compare mode output (legacy)
```

**Problems identified:**
1. Four distinct output code paths with duplication
2. Mix of direct `print()` calls and helper functions
3. Inconsistent formatting between modes
4. No JSON output support
5. Hard to test (tightly coupled to main())

### Existing Helper Functions

Good foundation exists:
- `format_duplicate_group()` (lines 93-148) - formats a single group
- `format_preview_banner()` (line 155-157) - banner text
- `format_execute_banner()` (line 160-162) - banner text
- `format_confirmation_prompt()` (lines 165-206) - confirmation UI
- `format_statistics_footer()` (lines 209-264) - summary statistics

**These functions are well-structured but:**
- Return strings/lists, then caller prints them
- No unified abstraction tying them together
- No JSON equivalent

## Recommended Architecture

### Pattern: Lightweight Formatter Abstraction

For a single-file implementation, use a simple protocol-based approach:

```
┌─────────────────────────────────────────┐
│           OutputFormatter               │
│  (Protocol/ABC - ~30 lines)             │
│                                         │
│  + format_banner(mode)                  │
│  + format_group(master, duplicates...)  │
│  + format_statistics(...)               │
│  + format_confirmation(...)             │
│  + output()  # write to stdout          │
└─────────────────────────────────────────┘
                    △
                    │ implements
        ┌───────────┴───────────┐
        │                       │
┌───────────────┐      ┌────────────────┐
│ TextFormatter │      │ JsonFormatter  │
│ (~100 lines)  │      │ (~80 lines)    │
│               │      │                │
│ Uses existing │      │ Builds dict    │
│ format_*()    │      │ structure      │
│ functions     │      │                │
└───────────────┘      └────────────────┘
```

### Minimal Interface

```python
from __future__ import annotations
from typing import Protocol
import json

class OutputFormatter(Protocol):
    """Protocol for output formatters."""

    def format_banner(self, mode: str, execute: bool = False) -> None:
        """Output banner for preview/execute mode."""
        ...

    def format_group(
        self,
        master_file: str,
        duplicates: list[str],
        action: str | None = None,
        verbose: bool = False,
        file_sizes: dict[str, int] | None = None,
        cross_fs_files: set[str] | None = None,
        preview_mode: bool = True
    ) -> None:
        """Output a single duplicate group."""
        ...

    def format_statistics(
        self,
        group_count: int,
        duplicate_count: int,
        master_count: int,
        space_savings: int,
        action: str | None = None,
        verbose: bool = False,
        cross_fs_count: int = 0,
        preview_mode: bool = True
    ) -> None:
        """Output summary statistics."""
        ...

    def format_confirmation_prompt(
        self,
        duplicate_count: int,
        action: str,
        space_savings: int,
        cross_fs_count: int = 0
    ) -> str:
        """Return confirmation prompt text (not output directly)."""
        ...

    def finalize(self) -> None:
        """Complete output (for JSON, dumps accumulated structure)."""
        ...
```

### TextFormatter Implementation

Wraps existing functions with minimal changes:

```python
class TextFormatter:
    """Text output formatter using existing helper functions."""

    def __init__(self):
        pass  # Stateless, or minimal state

    def format_banner(self, mode: str, execute: bool = False) -> None:
        if execute:
            print(format_execute_banner())
        else:
            print(format_preview_banner())
        print()

    def format_group(
        self,
        master_file: str,
        duplicates: list[str],
        action: str | None = None,
        verbose: bool = False,
        file_sizes: dict[str, int] | None = None,
        cross_fs_files: set[str] | None = None,
        preview_mode: bool = True
    ) -> None:
        # Delegate to existing function
        lines = format_duplicate_group(
            master_file, duplicates, action, verbose,
            file_sizes, cross_fs_files, preview_mode
        )
        for line in lines:
            print(line)

    def format_statistics(self, ...) -> None:
        lines = format_statistics_footer(...)
        for line in lines:
            print(line)

    def format_confirmation_prompt(self, ...) -> str:
        # Delegate to existing function
        return format_confirmation_prompt(...)

    def finalize(self) -> None:
        pass  # Nothing to do for text output
```

### JsonFormatter Implementation

Accumulates structured data, outputs at end:

```python
class JsonFormatter:
    """JSON output formatter."""

    def __init__(self):
        self.data = {
            "mode": None,
            "execute": False,
            "groups": [],
            "statistics": {},
            "warnings": []
        }

    def format_banner(self, mode: str, execute: bool = False) -> None:
        self.data["mode"] = mode
        self.data["execute"] = execute

    def format_group(
        self,
        master_file: str,
        duplicates: list[str],
        action: str | None = None,
        verbose: bool = False,
        file_sizes: dict[str, int] | None = None,
        cross_fs_files: set[str] | None = None,
        preview_mode: bool = True
    ) -> None:
        group = {
            "master": master_file,
            "duplicates": sorted(duplicates),
            "action": action,
        }
        if verbose and file_sizes:
            group["master_size"] = file_sizes.get(master_file, 0)
            group["duplicate_count"] = len(duplicates)
        if cross_fs_files:
            group["cross_filesystem"] = [d for d in duplicates if d in cross_fs_files]
        self.data["groups"].append(group)

    def format_statistics(
        self,
        group_count: int,
        duplicate_count: int,
        master_count: int,
        space_savings: int,
        action: str | None = None,
        verbose: bool = False,
        cross_fs_count: int = 0,
        preview_mode: bool = True
    ) -> None:
        self.data["statistics"] = {
            "duplicate_groups": group_count,
            "master_files": master_count,
            "duplicate_files": duplicate_count,
            "space_to_reclaim": space_savings,
            "space_to_reclaim_human": format_file_size(space_savings)
        }
        if action == 'hardlink' and cross_fs_count > 0:
            self.data["statistics"]["cross_filesystem_files"] = cross_fs_count

    def format_confirmation_prompt(self, ...) -> str:
        # JSON mode doesn't use interactive prompts
        # Return empty string or store in data structure
        return ""

    def finalize(self) -> None:
        print(json.dumps(self.data, indent=2))
```

## Integration with main()

### Current main() Flow

```python
def main() -> int:
    # Parse args
    # Find matches

    # CURRENT: Four branches with duplicate output logic
    if master_path:
        if preview_mode:
            # 50 lines of output code
        elif execute_mode:
            # 70 lines of output code
        elif args.summary:
            # 10 lines
        else:
            # 35 lines
    else:
        if args.summary:
            # 10 lines
        else:
            # 30 lines
```

### Proposed main() Flow

```python
def main() -> int:
    # Parse args
    args = parser.parse_args()

    # NEW: Create formatter based on --format flag
    formatter = create_formatter(args.format)  # 'text' or 'json'

    # Find matches (unchanged)
    matches, unmatched1, unmatched2 = find_matching_files(...)

    # Process into master/duplicate groups (unchanged)
    if args.action:
        master_results = []
        for file_hash, (files1, files2) in matches.items():
            master_file, duplicates, reason = select_master_file(...)
            master_results.append((master_file, duplicates, reason))

    # NEW: Unified output using formatter
    output_results(
        formatter=formatter,
        master_results=master_results,
        matches=matches,
        args=args,
        cross_fs_files=cross_fs_files
    )

    # Execute actions if needed (unchanged)
    if args.execute:
        success, failure, skipped, space, failed = execute_all_actions(...)
        formatter.finalize()
        return determine_exit_code(success, failure)

    formatter.finalize()
    return 0


def output_results(
    formatter: OutputFormatter,
    master_results: list,
    matches: dict,
    args: argparse.Namespace,
    cross_fs_files: set
) -> None:
    """Unified output function using formatter abstraction."""

    # Banner
    if args.action:
        formatter.format_banner(
            mode="action",
            execute=args.execute
        )

    # Groups
    if not args.summary:
        sorted_results = sorted(master_results, key=lambda x: x[0])
        for master_file, duplicates, reason in sorted_results:
            file_sizes = None
            if args.verbose:
                all_paths = [master_file] + duplicates
                file_sizes = {p: os.path.getsize(p) for p in all_paths}

            formatter.format_group(
                master_file=master_file,
                duplicates=duplicates,
                action=args.action,
                verbose=args.verbose,
                file_sizes=file_sizes,
                cross_fs_files=cross_fs_files if args.action == 'hardlink' else None,
                preview_mode=not args.execute
            )

    # Statistics
    bytes_saved, dup_count, grp_count = calculate_space_savings(master_results)
    formatter.format_statistics(
        group_count=grp_count,
        duplicate_count=dup_count,
        master_count=len(master_results),
        space_savings=bytes_saved,
        action=args.action,
        verbose=args.verbose,
        cross_fs_count=len(cross_fs_files) if args.action == 'hardlink' else 0,
        preview_mode=not args.execute
    )
```

## Build Order (Incremental Refactoring)

### Phase 1: Create Formatter Abstraction (Low Risk)

**What:** Define Protocol and TextFormatter
**Where:** Add ~150 lines at top of file_matcher.py (after imports)
**Tests:** No new tests yet - TextFormatter wraps existing functions

```python
# After line 23 (after logger setup), add:

# Output Formatter Protocol and Implementations
# (Lines 24-180)

class OutputFormatter(Protocol):
    ...

class TextFormatter:
    ...

class JsonFormatter:
    ...

def create_formatter(format_type: str) -> OutputFormatter:
    if format_type == 'json':
        return JsonFormatter()
    else:
        return TextFormatter()
```

**Verification:** Code still compiles, existing tests pass

### Phase 2: Extract output_results() Function (Medium Risk)

**What:** Extract unified output logic from main()
**Where:** New function after format_* helpers (~line 270)
**Tests:** Modify test_cli.py to verify output still correct

```python
def output_results(
    formatter: OutputFormatter,
    master_results: list,
    matches: dict,
    args: argparse.Namespace,
    cross_fs_files: set
) -> None:
    """Unified output function."""
    # Implementation as shown above
```

**Verification:** Run existing CLI tests, manual smoke test

### Phase 3: Refactor main() to Use Formatter (High Risk)

**What:** Replace four output branches with formatter calls
**Where:** main() function (lines 1045-1340)
**Tests:** All existing tests must pass

**Approach:**
1. Create formatter at start of main()
2. Replace first output branch (preview mode)
3. Run tests
4. Replace second output branch (execute mode)
5. Run tests
6. Replace remaining branches
7. Run tests

**Verification:** Full test suite + manual testing of all modes

### Phase 4: Add --format CLI Flag (Low Risk)

**What:** Add JSON output support
**Where:** argparse setup in main()
**Tests:** New tests for JSON output

```python
parser.add_argument('--format', '-F', choices=['text', 'json'], default='text',
                    help='Output format (default: text)')
```

**Verification:** New test_json_output.py test file

### Phase 5: Remove Duplication (Clean-up)

**What:** Remove now-unused output code paths
**Where:** main() function
**Tests:** Verify tests still pass

**Verification:** Code coverage check, manual testing

## Integration Points

### Where Formatter is Created

```python
# In main(), line ~1000 (after argparse, before find_matching_files)
formatter = create_formatter(args.format)
```

### Where Formatter is Used

```python
# In main(), replace lines 1045-1340 with:
if master_path:
    # Process master results
    output_results(formatter, master_results, matches, args, cross_fs_files)
else:
    # Legacy compare mode (defer refactor)
    output_legacy_compare_mode(matches, unmatched1, unmatched2, args)
```

### Where Format Helpers Stay

Existing `format_*()` functions remain but are called only by TextFormatter:
- `format_duplicate_group()` - called by TextFormatter.format_group()
- `format_statistics_footer()` - called by TextFormatter.format_statistics()
- `format_preview_banner()` - called by TextFormatter.format_banner()
- `format_execute_banner()` - called by TextFormatter.format_banner()
- `format_confirmation_prompt()` - called by TextFormatter (special case)

### Test Impact

**Low impact on existing tests:**
- Tests using `test_cli.py` patterns continue to work
- Tests check stdout strings - TextFormatter produces same output
- New tests needed for JsonFormatter

**New test files:**
- `test_json_output.py` - verify JSON structure
- `test_formatters.py` - unit tests for formatter classes

## Patterns to Follow

### 1. Incremental Refactoring

DO NOT attempt big-bang refactor. Each phase must:
- Keep existing code working
- Pass existing tests
- Be deployable independently

### 2. Formatter Lifecycle

```python
# Create
formatter = create_formatter(args.format)

# Use (multiple calls)
formatter.format_banner(...)
formatter.format_group(...)
formatter.format_group(...)
formatter.format_statistics(...)

# Finalize (outputs JSON if JsonFormatter)
formatter.finalize()
```

### 3. Confirmation Prompts (Special Case)

TextFormatter returns string for `format_confirmation_prompt()` - caller handles input().
JsonFormatter ignores confirmation (execute mode not used with JSON).

```python
if args.execute and not args.yes:
    prompt = formatter.format_confirmation_prompt(...)
    if not confirm_execution(skip_confirm=False, prompt=prompt):
        return 0
```

### 4. Error Handling

Formatters should not raise exceptions. If JSON serialization fails, fall back to text:

```python
def finalize(self) -> None:
    try:
        print(json.dumps(self.data, indent=2))
    except (TypeError, ValueError) as e:
        logger.error(f"JSON serialization failed: {e}")
        # Fall back to text output
        print(f"Error: {e}")
```

## Anti-Patterns to Avoid

### 1. Over-Engineering

DON'T create abstract factory patterns, registry systems, or plugin architectures.
This is a single-file tool with two output formats - keep it simple.

### 2. Changing Existing Functions Unnecessarily

DON'T refactor `format_duplicate_group()` and related helpers in Phase 1.
Use them as-is - TextFormatter calls them.

### 3. Breaking Test Compatibility

DON'T change text output format during refactor.
TextFormatter must produce identical output to current code.

### 4. JSON Mode Side Effects

DON'T allow JsonFormatter to write anything except final JSON.
Accumulate all data, output once in finalize().

### 5. Mixing Formatter Concerns

DON'T put business logic in formatters.
Formatters only format - calculation logic stays in main().

## Comparison with Alternatives

### Alternative 1: Cliff Framework

**Cliff** ([cliff framework docs](https://docs.openstack.org/cliff/latest/)) provides built-in formatter support via ShowOne/Lister base classes.

**Pros:**
- Industry-standard approach
- Multiple output formats (JSON, CSV, YAML, table)
- Tested and maintained

**Cons:**
- Heavy dependency for single-file tool
- Requires restructuring around commands/subcommands
- Breaks existing CLI interface
- Overkill for this use case

**Verdict:** NOT RECOMMENDED for file_matcher (single-file constraint)

### Alternative 2: Direct json.dumps() Calls

**Pattern:** Add `if args.format == 'json'` checks throughout code

**Pros:**
- Zero abstraction
- Very simple

**Cons:**
- Duplicates conditional logic everywhere
- Hard to test
- Mixes concerns (formatting with business logic)

**Verdict:** NOT RECOMMENDED (unmaintainable)

### Alternative 3: Template-Based (string.Template)

**Pattern:** Use template strings for text, dict for JSON

**Pros:**
- Separates format from data

**Cons:**
- Templates harder to read than functions
- Doesn't solve unification problem
- Complex template syntax for nested structures

**Verdict:** NOT RECOMMENDED

### Alternative 4: Rich Library

**Rich** library provides excellent formatted output for terminals.

**Pros:**
- Beautiful table/tree rendering
- Color support
- JSON output via rich.console.Console(record=True)

**Cons:**
- New dependency (breaks single-file pattern)
- Significant API changes
- JSON output is secondary feature

**Verdict:** Consider for future enhancement, NOT for this phase

## Recommended Approach: Lightweight Protocol

**Why this is best for file_matcher:**

1. Single-file compatible (~150 lines added)
2. Incremental refactoring (low risk)
3. Minimal API surface
4. Reuses existing format_*() functions
5. Easy to test
6. No dependencies

## Testing Strategy

### Unit Tests (New)

```python
# test_formatters.py
class TestTextFormatter(unittest.TestCase):
    def test_format_group_output(self):
        """Verify TextFormatter produces expected output."""
        formatter = TextFormatter()
        # Capture stdout
        # Call formatter.format_group(...)
        # Assert output matches existing format

class TestJsonFormatter(unittest.TestCase):
    def test_format_group_structure(self):
        """Verify JSON structure is correct."""
        formatter = JsonFormatter()
        formatter.format_group(...)
        formatter.finalize()
        # Parse JSON output
        # Assert structure
```

### Integration Tests (Modified)

```python
# test_cli.py
class TestCLI(BaseFileMatcherTest):
    def test_json_output_format(self):
        """Test --format json produces valid JSON."""
        with patch('sys.argv', ['file_matcher.py', self.test_dir1,
                                self.test_dir2, '--format', 'json']):
            output = self.run_main_with_args([])
            data = json.loads(output)
            self.assertIn('groups', data)
            self.assertIn('statistics', data)
```

### Manual Testing Checklist

After each phase:

- [ ] Compare mode with text output
- [ ] Action mode (preview) with text output
- [ ] Action mode (execute) with text output
- [ ] Summary mode with text output
- [ ] Verbose mode with text output
- [ ] JSON output for each mode (Phase 4+)

## Success Criteria

Refactoring is complete when:

- [ ] Single formatter abstraction handles all output
- [ ] main() has ~50% less output code
- [ ] All existing tests pass
- [ ] JSON output works for all modes
- [ ] No change to text output format (backward compatible)
- [ ] Code is more testable (formatter can be unit tested)
- [ ] New --format flag documented

## Sources

Architecture patterns and best practices researched from:

- [Python print() Output: Practical Patterns (2026)](https://thelinuxcode.com/python-print-output-practical-patterns-pitfalls-and-modern-workflows-2026/) - Modern Python CLI output practices
- [Things I've learned about building CLI tools in Python](https://simonwillison.net/2023/Sep/30/cli-tools-python/) - Real-world CLI design wisdom
- [Cliff Framework Documentation](https://docs.openstack.org/cliff/latest/) - Industry-standard output formatter patterns
- [Hexagonal Architecture Design (2026)](https://johal.in/hexagonal-architecture-design-python-ports-and-adapters-for-modularity-2026/) - Ports and adapters for modularity
- [Python Design Patterns - Command](https://www.tutorialspoint.com/python_design_patterns/python_design_patterns_command.htm) - Command pattern for CLI
- [Python argparse Documentation](https://docs.python.org/3/library/argparse.html) - Built-in formatter patterns
- [JSON encoder and decoder — Python 3.14.2 documentation](https://docs.python.org/3/library/json.html) - Standard JSON handling

---

*Architecture research: 2026-01-22*
*Focus: Unified output formatting for CLI tool with text/JSON modes*
