# Technology Stack: Output Formatting and JSON Support

**Project:** File Matcher v1.2 Output Rationalisation
**Research Focus:** Structured text output and JSON generation
**Researched:** 2026-01-22
**Confidence:** HIGH

## Executive Summary

For unified output formatting and JSON support, use Python's standard library only. **Recommended stack:**

| Capability | Module | Rationale |
|------------|--------|-----------|
| JSON output | `json` | Standard library, full control, zero dependencies |
| Text formatting | `str.format()` | Already in use, powerful, no new imports |
| Data structures | `dataclasses` (optional) | Clean data modeling, easy JSON via `asdict()` |
| Pretty printing | ❌ Avoid `pprint` | Wrong abstraction for CLI output |

**Core principle:** Continue using string methods and `json.dumps()` from standard library. No new dependencies needed.

---

## Detailed Recommendations

### 1. JSON Output Generation

**Use:** `json` module (standard library)

#### Why json module?
- **Already familiar:** Project uses hashlib, argparse, logging — consistent stdlib approach
- **Full control:** `indent`, `sort_keys`, `separators` provide precise formatting
- **Zero overhead:** No new dependencies
- **Battle-tested:** Used everywhere, reliable, well-documented

#### Recommended pattern:

```python
import json

# For CLI output (readable)
def format_json_output(data, pretty=True):
    """Format data as JSON for CLI output."""
    if pretty:
        return json.dumps(data, indent=2, sort_keys=False, ensure_ascii=False)
    else:
        return json.dumps(data, separators=(',', ':'), ensure_ascii=False)

# Usage with --json flag
if args.json:
    output_data = build_output_dict(matches, stats, mode='compare')
    print(format_json_output(output_data))
else:
    # Current text output
    print_text_output(matches, stats)
```

#### Key parameters for CLI use:

| Parameter | Value | Why |
|-----------|-------|-----|
| `indent=2` | Pretty print | Human-readable when piped to files |
| `sort_keys=False` | Preserve order | Logical ordering (not alphabetical) |
| `ensure_ascii=False` | Unicode support | Handle international filenames correctly |
| `separators=(',', ':')` | Compact mode | Optional for `--json --compact` flag |

**What NOT to use:**
- ❌ `pprint` — Wrong abstraction (Python repr, not JSON)
- ❌ Third-party libraries (`orjson`, `ujson`) — Violates zero-dependency constraint

---

### 2. Structured Text Output

**Use:** `str.format()` with explicit formatting strings (current approach)

#### Why continue with str.format()?
- **Already in use:** Project already uses f-strings and format strings
- **Sufficient:** Handles alignment, padding, width control
- **No imports needed:** Built-in string method
- **Readable:** Clear what output will look like

#### Current pattern (continue this):

```python
# Already doing this well
def format_duplicate_group(master_file, duplicates, action=None, verbose=False):
    lines = []
    lines.append(f"[MASTER] {master_file}")
    for dup in sorted(duplicates):
        label = f"[DUP:{action}]" if action else "[DUP]"
        lines.append(f"    {label} {dup}")
    return lines
```

#### Enhancement opportunities:

```python
# For consistent column widths
def format_statistics_table(stats):
    """Format statistics with aligned columns."""
    rows = [
        ("Duplicate groups:", f"{stats['group_count']}"),
        ("Master files:", f"{stats['master_count']}"),
        ("Duplicate files:", f"{stats['duplicate_count']}"),
        ("Space savings:", format_file_size(stats['space_savings'])),
    ]

    # Calculate max width for alignment
    max_label_width = max(len(label) for label, _ in rows)

    return [f"{label:<{max_label_width}} {value}" for label, value in rows]
```

**What NOT to use:**
- ❌ `textwrap` — Not needed for current output patterns (no paragraph wrapping)
- ❌ `string.Template` — Less powerful than f-strings, no advantage here
- ❌ Third-party libraries (`rich`, `tabulate`) — Violates constraints

---

### 3. Data Structures (Optional Enhancement)

**Consider:** `dataclasses` for internal data modeling

#### Why dataclasses?
- **Clean schema:** Explicit structure for output data
- **JSON-ready:** `asdict()` converts directly to dict for `json.dumps()`
- **Type hints:** IDE support, maintainability
- **Standard library:** Python 3.7+ (project requires 3.9+)

#### Example usage:

```python
from dataclasses import dataclass, asdict
from typing import List

@dataclass
class DuplicateGroup:
    master_file: str
    duplicates: List[str]
    file_hash: str
    file_size: int
    selection_reason: str

@dataclass
class ComparisonOutput:
    mode: str  # "compare" or "action"
    statistics: dict
    duplicate_groups: List[DuplicateGroup]
    unmatched_files: dict = None

# Easy conversion to JSON
output = ComparisonOutput(...)
json_data = json.dumps(asdict(output), indent=2)
```

#### Benefits:
- **Schema documentation:** Clear what data structure looks like
- **Refactoring safety:** Changes propagate through IDE
- **Easy JSON:** `json.dumps(asdict(obj))` just works
- **No runtime overhead:** Pure Python, no validation unless you add it

#### When NOT to use:
- ❌ Simple dict is sufficient for current needs
- ❌ Don't want to refactor existing code
- ❌ Overhead not justified for single-use structures

**Decision:** Optional. Current dict-based approach is fine. Consider for v1.3+ if complexity grows.

---

### 4. What NOT to Add

#### pprint module — Wrong abstraction
- **Purpose:** Debug Python objects, not CLI output
- **Limitation:** Produces Python repr, not custom formats
- **Not needed:** We need custom formatting (labels, indentation), not generic pretty-printing

```python
# Don't do this:
import pprint
pprint.pp(matches)  # Wrong: shows Python dict repr, not user-friendly output
```

#### textwrap module — Not applicable
- **Purpose:** Paragraph wrapping (e.g., help text, documentation)
- **Not needed:** We output structured lists, not flowing paragraphs
- **Current output:** Already has explicit indentation and structure

```python
# Don't need this:
import textwrap
textwrap.fill(long_file_path, width=80)  # Wrong: file paths shouldn't wrap
```

#### Third-party libraries — Violates constraints
Project explicitly requires "Pure Python standard library only" (see PROJECT.md, CONSTRAINTS).

```python
# Don't add these:
import rich      # ❌ External dependency
import tabulate  # ❌ External dependency
import orjson    # ❌ External dependency
```

---

## Implementation Guide

### Phase 1: JSON Output Structure

Define consistent output schema:

```python
def build_json_output(mode, matches, stats, unmatched=None):
    """Build JSON-serializable output structure.

    Args:
        mode: "compare" or "action" (action includes preview/execute)
        matches: Dict of file hash -> (files1, files2) or master/dup groups
        stats: Statistics dict
        unmatched: Optional unmatched files data

    Returns:
        Dict suitable for json.dumps()
    """
    output = {
        "version": "1.2",
        "mode": mode,
        "statistics": stats,
        "duplicate_groups": format_duplicate_groups_json(matches),
    }

    if unmatched:
        output["unmatched_files"] = unmatched

    return output
```

### Phase 2: Unified Text Output

Extract common formatting functions:

```python
def format_statistics_footer(stats, mode):
    """Format statistics footer (same for all modes)."""
    lines = ["", "--- Statistics ---"]
    lines.extend(format_statistics_table(stats))
    return lines

def format_duplicate_group_text(group, mode, action=None):
    """Format a duplicate group (unified across modes)."""
    # Common structure for compare and action modes
    pass
```

### Phase 3: Output Dispatcher

Route to correct formatter:

```python
def write_output(data, output_format='text', pretty=True):
    """Write output in requested format.

    Args:
        data: Structured data (dict or dataclass)
        output_format: 'text' or 'json'
        pretty: For JSON, whether to pretty-print
    """
    if output_format == 'json':
        print(format_json_output(data, pretty))
    else:
        print_text_output(data)
```

---

## Integration with Existing Code

### Current CLI flags:
```python
parser.add_argument('--summary', '-s')     # Existing: brief vs detailed
parser.add_argument('--verbose', '-v')     # Existing: extra detail
```

### New flags needed:
```python
parser.add_argument('--json', action='store_true',
                    help='Output in JSON format (for scripting/pipelines)')
parser.add_argument('--compact', action='store_true',
                    help='Compact output (with --json, removes whitespace)')
```

### Compatibility:
- `--json` overrides text output (mutually exclusive)
- `--json --summary` and `--json --verbose` control what data is included
- `--json --compact` produces minimal JSON (for parsing, not humans)

---

## Testing Strategy

### Unit tests needed:

```python
def test_json_output_structure():
    """Verify JSON output has expected schema."""
    output = build_json_output('compare', matches, stats)
    assert 'version' in output
    assert 'mode' in output
    assert 'statistics' in output
    assert output['mode'] == 'compare'

def test_json_valid_syntax():
    """Ensure output is valid JSON."""
    output = build_json_output('compare', matches, stats)
    json_str = json.dumps(output)
    parsed = json.loads(json_str)  # Should not raise
    assert parsed == output

def test_unified_statistics_footer():
    """Statistics appear in all modes."""
    # Test compare mode
    # Test action preview mode
    # Test action execute mode
```

### Integration tests:

```bash
# Verify JSON is parseable
filematcher dir1 dir2 --json | jq .

# Verify text output unchanged (backward compatibility)
filematcher dir1 dir2 > output.txt
diff output.txt expected_output.txt
```

---

## Sources

**Official Documentation:**
- [json — JSON encoder and decoder — Python 3.14.2](https://docs.python.org/3/library/json.html)
- [textwrap — Text wrapping and filling](https://docs.python.org/3/library/textwrap.html)
- [string — Common string operations](https://docs.python.org/3/library/string.html)
- [pprint — Data pretty printer](https://docs.python.org/3/library/pprint.html)
- [dataclasses — Data Classes](https://docs.python.org/3/library/dataclasses.html)

**Community Resources:**
- [How to Pretty Print JSON in Python | DigitalOcean](https://www.digitalocean.com/community/tutorials/python-pretty-print-json)
- [Working With JSON Data in Python – Real Python](https://realpython.com/python-json/)
- [Everything You Can Do with Python's textwrap Module | Martin Heinz](https://martinheinz.dev/blog/108)
- [Python print() Output: Practical Patterns, Pitfalls, and Modern Workflows (2026) – TheLinuxCode](https://thelinuxcode.com/python-print-output-practical-patterns-pitfalls-and-modern-workflows-2026/)

**Standard Library Reference:**
- json module: Provides `dumps()`, `dump()` with `indent`, `sort_keys`, `separators`, `ensure_ascii` for full control
- str.format(): Already in use, sufficient for structured text output
- dataclasses: Optional enhancement for data modeling, provides `asdict()` for easy JSON conversion

---

*Research complete: 2026-01-22*
*Confidence level: HIGH (all solutions verified in official Python documentation)*
