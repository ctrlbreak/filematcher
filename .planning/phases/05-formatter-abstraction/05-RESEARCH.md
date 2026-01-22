# Phase 5: Formatter Abstraction - Research

**Researched:** 2026-01-22
**Domain:** Python ABC-based output formatter abstraction for CLI tool
**Confidence:** HIGH

## Summary

This phase creates a unified output abstraction layer using Python's ABC (Abstract Base Class) module to enable multiple output formats (text, JSON) while maintaining backward compatibility with existing output. The research confirms that ABC is well-suited for this use case, providing explicit interface contracts with runtime enforcement.

The key architectural decision is to use the **Strategy pattern** with ABC-defined formatters, where each mode (compare, action) has its own formatter protocol. The existing format functions (`format_duplicate_group`, `format_statistics_footer`, `format_preview_banner`, etc.) will be wrapped by `TextFormatter` implementations that produce byte-identical output.

**Primary recommendation:** Define two separate ABC classes (`CompareFormatter` and `ActionFormatter`) with medium-granularity methods. Use constructor injection for configuration (verbose mode, etc.) and instantiate formatters early in `main()`. Use internal buffering for JSON formatters to accumulate data before final output.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `abc` | stdlib | Abstract Base Classes | Python's built-in solution for interface contracts |
| `json` | stdlib | JSON serialization | Standard library, zero dependencies |
| `typing` | stdlib | Type hints | Improved code clarity and IDE support |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `io.StringIO` | stdlib | String buffering | If formatters need to buffer output before final print |
| `dataclasses` | stdlib | Data containers | For structured data passed to formatters |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| ABC | typing.Protocol | Protocol is structural (duck typing), ABC is nominal (explicit inheritance). ABC chosen per user decision for explicit runtime checks |
| Direct print | Return strings | Returning strings allows testing without stdout capture; chosen for flexibility |

**Installation:**
```bash
# All standard library - no installation required
```

## Architecture Patterns

### Recommended Project Structure
```
file_matcher.py (single file, maintaining existing pattern)
  |
  +-- ABC Definitions (CompareFormatter, ActionFormatter)
  |
  +-- Text Implementations (TextCompareFormatter, TextActionFormatter)
  |
  +-- JSON Implementations (JsonCompareFormatter, JsonActionFormatter) [Phase 6]
  |
  +-- Existing format_* functions (preserved, called by TextFormatter)
```

### Pattern 1: Strategy Pattern with ABC

**What:** Define abstract formatter interfaces, create concrete implementations for each output format
**When to use:** Multiple output formats sharing same data flow
**Example:**
```python
# Source: Python abc module documentation
from abc import ABC, abstractmethod

class CompareFormatter(ABC):
    """Abstract formatter for compare mode output."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    @abstractmethod
    def format_header(self, dir1: str, dir2: str, hash_algo: str) -> None:
        """Format and emit the header section."""
        ...

    @abstractmethod
    def format_match_group(
        self,
        file_hash: str,
        files_dir1: list[str],
        files_dir2: list[str]
    ) -> None:
        """Format and emit a single match group."""
        ...

    @abstractmethod
    def format_unmatched(
        self,
        dir_label: str,
        files: list[str]
    ) -> None:
        """Format and emit unmatched files section."""
        ...

    @abstractmethod
    def format_summary(
        self,
        match_count: int,
        matched_files1: int,
        matched_files2: int,
        unmatched1: int,
        unmatched2: int
    ) -> None:
        """Format and emit summary statistics."""
        ...

    @abstractmethod
    def finalize(self) -> None:
        """Complete output (e.g., flush JSON buffer)."""
        ...
```

### Pattern 2: Constructor Injection for Configuration

**What:** Pass configuration (verbose, etc.) via constructor, not per-method
**When to use:** Configuration affects multiple methods consistently
**Example:**
```python
# Source: Python best practices
class TextCompareFormatter(CompareFormatter):
    def __init__(self, verbose: bool = False):
        super().__init__(verbose)
        # Configuration stored for all methods to use

    def format_match_group(self, file_hash: str, files_dir1: list[str], files_dir2: list[str]) -> None:
        # self.verbose available here
        if self.verbose:
            # Include file sizes
            pass
```

### Pattern 3: Accumulator Pattern for JSON

**What:** Buffer structured data during processing, serialize at finalize()
**When to use:** JSON output requires complete data structure
**Example:**
```python
# Source: Common Python pattern
class JsonCompareFormatter(CompareFormatter):
    def __init__(self, verbose: bool = False):
        super().__init__(verbose)
        self._data = {
            "version": "1.0",
            "matches": [],
            "unmatched": {"dir1": [], "dir2": []}
        }

    def format_match_group(self, file_hash: str, files_dir1: list[str], files_dir2: list[str]) -> None:
        self._data["matches"].append({
            "hash": file_hash,
            "files_dir1": files_dir1,
            "files_dir2": files_dir2
        })

    def finalize(self) -> None:
        import json
        print(json.dumps(self._data, indent=2))
```

### Anti-Patterns to Avoid

- **God Formatter:** Single class trying to handle both compare and action modes with if/else branches. Use separate ABC hierarchies per CONTEXT.md decision.
- **Method explosion:** Too many fine-grained methods (format_single_file, format_file_size, etc.). Stick to medium granularity per CONTEXT.md.
- **Inheritance for configuration:** Don't create VerboseTextFormatter subclass; use constructor parameter instead.
- **Direct stdout in ABC:** Don't call print() in abstract methods; implementations decide output mechanism.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON serialization | Custom string building | `json.dumps()` | Handles escaping, unicode, edge cases correctly |
| Abstract interfaces | Duck typing with NotImplementedError | ABC with @abstractmethod | ABC catches missing implementations at instantiation time, not runtime |
| Output buffering | List of strings with join | `io.StringIO` | Handles encoding, efficient for large output |
| Deterministic ordering | Manual dict sorting | `sorted()` on items | Consistent, readable, tested |

**Key insight:** The existing format_* functions already handle the complex formatting logic. The abstraction layer should delegate to these functions (for TextFormatter), not reimplement them.

## Common Pitfalls

### Pitfall 1: Breaking Existing Output

**What goes wrong:** TextFormatter produces slightly different output than current code
**Why it happens:** Subtle differences in whitespace, newlines, or ordering
**How to avoid:**
1. Capture current output as reference before refactoring
2. TextFormatter must call existing format_* functions, not reimplement
3. Compare output byte-by-byte in tests
**Warning signs:** Test failures mentioning string differences, user reports of broken scripts

### Pitfall 2: Forgetting ABC Decorator Order

**What goes wrong:** TypeError when combining @property with @abstractmethod
**Why it happens:** @abstractmethod must be innermost decorator
**How to avoid:** Follow pattern: `@property` then `@abstractmethod`
**Warning signs:** TypeError at class definition time

### Pitfall 3: Testing Formatters in Isolation vs Integration

**What goes wrong:** Formatter unit tests pass but integration fails
**Why it happens:** Mocking hides real data flow issues
**How to avoid:**
1. Unit test formatter methods with known inputs
2. Integration test full flow through main()
3. Keep existing CLI tests unchanged (they validate integration)
**Warning signs:** Unit tests green, CLI tests red

### Pitfall 4: Non-Deterministic Output

**What goes wrong:** Same input produces different output ordering between runs
**Why it happens:** Dict iteration order (pre-3.7), set iteration, or unsorted file lists
**How to avoid:**
1. Always sort file lists before formatting
2. Use sorted() when iterating over collections for output
3. The existing code already sorts in some places (e.g., `sorted_results = sorted(master_results, key=lambda x: x[0])`)
**Warning signs:** Flaky tests, diff tools showing order changes

### Pitfall 5: Mixing stdout and stderr

**What goes wrong:** Progress messages appear in piped data output
**Why it happens:** Forgot to route progress to stderr
**How to avoid:** Per OUT-03, formatters output to stdout; progress/status uses `logger` which goes to stderr
**Warning signs:** JSON output contains progress text, piped output unusable

## Code Examples

Verified patterns from official sources:

### ABC Definition with Abstract Methods
```python
# Source: https://docs.python.org/3/library/abc.html
from abc import ABC, abstractmethod

class ActionFormatter(ABC):
    """Abstract formatter for action mode (preview/execute) output."""

    def __init__(self, verbose: bool = False, preview_mode: bool = True):
        self.verbose = verbose
        self.preview_mode = preview_mode

    @abstractmethod
    def format_banner(self) -> None:
        """Emit the mode banner (PREVIEW or EXECUTING)."""
        ...

    @abstractmethod
    def format_duplicate_group(
        self,
        master_file: str,
        duplicates: list[str],
        action: str,
        file_sizes: dict[str, int] | None = None,
        cross_fs_files: set[str] | None = None
    ) -> None:
        """Format and emit a single duplicate group."""
        ...

    @abstractmethod
    def format_statistics(
        self,
        group_count: int,
        duplicate_count: int,
        master_count: int,
        space_savings: int,
        action: str,
        cross_fs_count: int = 0
    ) -> None:
        """Format and emit statistics footer."""
        ...

    @abstractmethod
    def finalize(self) -> None:
        """Complete output."""
        ...
```

### TextFormatter Wrapping Existing Functions
```python
# Pattern: Delegate to existing format_* functions
class TextActionFormatter(ActionFormatter):
    """Text output formatter using existing format functions."""

    def format_banner(self) -> None:
        if self.preview_mode:
            print(format_preview_banner())
        else:
            print(format_execute_banner())
        print()

    def format_duplicate_group(
        self,
        master_file: str,
        duplicates: list[str],
        action: str,
        file_sizes: dict[str, int] | None = None,
        cross_fs_files: set[str] | None = None
    ) -> None:
        lines = format_duplicate_group(
            master_file=master_file,
            duplicates=duplicates,
            action=action,
            verbose=self.verbose,
            file_sizes=file_sizes,
            cross_fs_files=cross_fs_files,
            preview_mode=self.preview_mode
        )
        for line in lines:
            print(line)

    def format_statistics(
        self,
        group_count: int,
        duplicate_count: int,
        master_count: int,
        space_savings: int,
        action: str,
        cross_fs_count: int = 0
    ) -> None:
        lines = format_statistics_footer(
            group_count=group_count,
            duplicate_count=duplicate_count,
            master_count=master_count,
            space_savings=space_savings,
            action=action,
            verbose=self.verbose,
            cross_fs_count=cross_fs_count,
            preview_mode=self.preview_mode
        )
        for line in lines:
            print(line)

    def finalize(self) -> None:
        pass  # Text output is immediate, nothing to finalize
```

### JSON Formatter Accumulator Pattern
```python
# Pattern: Accumulate data, serialize on finalize
import json

class JsonActionFormatter(ActionFormatter):
    """JSON output formatter - accumulates data for structured output."""

    def __init__(self, verbose: bool = False, preview_mode: bool = True):
        super().__init__(verbose, preview_mode)
        self._data = {
            "version": "1.0",
            "mode": "preview" if preview_mode else "execute",
            "groups": [],
            "statistics": {}
        }

    def format_banner(self) -> None:
        # No banner in JSON - mode is in data structure
        pass

    def format_duplicate_group(
        self,
        master_file: str,
        duplicates: list[str],
        action: str,
        file_sizes: dict[str, int] | None = None,
        cross_fs_files: set[str] | None = None
    ) -> None:
        group = {
            "master": master_file,
            "duplicates": sorted(duplicates),  # Deterministic ordering
            "action": action
        }
        if file_sizes and self.verbose:
            group["sizes"] = {k: file_sizes[k] for k in sorted(file_sizes.keys())}
        if cross_fs_files:
            group["cross_fs"] = sorted(cross_fs_files)
        self._data["groups"].append(group)

    def format_statistics(
        self,
        group_count: int,
        duplicate_count: int,
        master_count: int,
        space_savings: int,
        action: str,
        cross_fs_count: int = 0
    ) -> None:
        self._data["statistics"] = {
            "group_count": group_count,
            "duplicate_count": duplicate_count,
            "master_count": master_count,
            "space_savings_bytes": space_savings,
            "action": action,
            "cross_fs_count": cross_fs_count
        }

    def finalize(self) -> None:
        # Sort groups by master file for deterministic output
        self._data["groups"].sort(key=lambda g: g["master"])
        print(json.dumps(self._data, indent=2))
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| NotImplementedError for abstract methods | ABC with @abstractmethod | Python 2.6/3.0 (2008) | Catches errors at instantiation, not runtime |
| typing.Protocol for interfaces | ABC for explicit inheritance | Both valid, different use cases | ABC chosen per user decision for explicit contracts |
| Formatter module (stdlib) | Removed from stdlib | Python 3.10 (2021) | Custom implementations preferred |

**Deprecated/outdated:**
- `formatter` module: Removed from Python stdlib in 3.10. Don't use; build custom formatters.
- `abc.abstractproperty`: Use `@property` combined with `@abstractmethod` instead.

## Open Questions

Things that couldn't be fully resolved:

1. **Golden file testing strategy**
   - What we know: Libraries like pytest-golden and ApprovalTests.Python exist for snapshot testing
   - What's unclear: Whether existing test coverage is sufficient, or golden files would add value
   - Recommendation: Assess existing test_cli.py coverage first. If output-sensitive tests exist, likely sufficient. Add golden file tests only if gaps found during implementation.

2. **Error/warning formatting location**
   - What we know: Currently warnings use `logger.warning()` and errors use `logger.error()`
   - What's unclear: Whether formatters should handle warnings/errors or keep them in logger
   - Recommendation: Keep errors/warnings with logger (stderr). Formatters handle data output (stdout). This aligns with OUT-03 requirement.

3. **Context object vs explicit parameters**
   - What we know: Both patterns work; explicit is more testable, context is more extensible
   - What's unclear: Whether future phases will add many more parameters
   - Recommendation: Start with explicit parameters. If Phase 6-8 shows parameter explosion, refactor to context object then.

## Sources

### Primary (HIGH confidence)
- [Python abc module documentation](https://docs.python.org/3/library/abc.html) - ABC class, @abstractmethod, decorator ordering
- [PEP 3119](https://peps.python.org/pep-3119/) - ABC specification and rationale

### Secondary (MEDIUM confidence)
- [Python Protocols vs ABCs comparison](https://medium.com/@pouyahallaj/introduction-1616b3a4a637) - Design decision rationale for ABC vs Protocol
- [jc CLI tool](https://kellyjonbrazil.github.io/jc/) - Example of CLI tool with multiple output formats
- [pytest-golden](https://pypi.org/project/pytest-golden/) - Golden file testing library (if needed)
- [ApprovalTests.Python](https://github.com/approvals/ApprovalTests.Python) - Snapshot testing alternative

### Tertiary (LOW confidence)
- General design pattern articles - Strategy pattern implementation (common knowledge, not tool-specific)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All stdlib, well-documented
- Architecture: HIGH - ABC patterns well-established, decisions locked in CONTEXT.md
- Pitfalls: MEDIUM - Based on general Python experience, not formatter-specific case studies

**Research date:** 2026-01-22
**Valid until:** 2026-02-22 (30 days - stable domain, no fast-moving dependencies)
