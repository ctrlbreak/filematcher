# Phase 6: JSON Output - Research

**Researched:** 2026-01-22
**Domain:** Python CLI JSON output with structured schema
**Confidence:** HIGH

## Summary

This phase adds machine-readable JSON output to the file matcher CLI. Research confirms that Python's stdlib provides everything needed (json, os.stat, datetime) with no external dependencies.

The standard approach for CLI JSON output is a single, complete JSON object (not JSON Lines) with 2-space indentation, a version field for schema evolution, and RFC 3339 timestamps. The `--json` flag should produce a single schema that optionally includes verbose metadata fields when combined with `--verbose`, maintaining backward compatibility by adding fields rather than changing structure.

**Primary recommendation:** Use single JSON object output (not JSONL) with 2-space indentation, RFC 3339 timestamps, version field "1.0". Include optional metadata fields in same schema based on `--verbose` flag.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `json` | stdlib | JSON serialization | Python's built-in, zero dependencies, handles encoding correctly |
| `os.stat` | stdlib | File metadata (size, timestamps) | Standard way to get mtime, size, ctime |
| `datetime` | stdlib | ISO 8601 timestamp formatting | `.isoformat()` produces RFC 3339 compliant strings |
| `argparse` | stdlib | CLI flag parsing | Adding --json flag to existing parser |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `sorted()` | builtin | Deterministic ordering | All collections in JSON must be sorted |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Single JSON object | JSON Lines (JSONL) | JSONL better for streaming/large datasets; single object better for CLI tools with complete results |
| 2-space indent | Compact (no indent) | Both acceptable; 2-space matches jq default, more human-readable |
| RFC 3339 timestamps | Unix epoch integers | Timestamps as strings (RFC 3339) are human-readable and self-documenting |

**Installation:**
```bash
# All standard library - no installation required
```

## Architecture Patterns

### Recommended Project Structure
```
file_matcher.py (single file, maintaining existing pattern)
  |
  +-- ABC Definitions (CompareFormatter, ActionFormatter) [Phase 5]
  |
  +-- Text Implementations (TextCompareFormatter, TextActionFormatter) [Phase 5]
  |
  +-- JSON Implementations (JsonCompareFormatter, JsonActionFormatter) [THIS PHASE]
        |
        +-- Accumulator pattern: buffer data, serialize in finalize()
        +-- sorted() for deterministic output
        +-- RFC 3339 timestamps via datetime.isoformat()
```

### Pattern 1: Single JSON Object with Version Field

**What:** Output complete results as one JSON object with schema version
**When to use:** CLI tools that produce finite results (not streaming)
**Example:**
```python
# Source: https://blog.kellybrazil.com/2021/12/03/tips-on-adding-json-output-to-your-cli-app/
import json

data = {
    "version": "1.0",
    "directories": {
        "dir1": "/path/to/dir1",
        "dir2": "/path/to/dir2"
    },
    "matches": [...],
    "statistics": {...}
}

print(json.dumps(data, indent=2))
```

### Pattern 2: RFC 3339 Timestamps for Metadata

**What:** Use ISO 8601 / RFC 3339 format for all timestamps
**When to use:** Any timestamp in JSON output (file mtimes, execution time)
**Example:**
```python
# Source: https://www.w3resource.com/python-exercises/date-time-exercise/python-date-time-exercise-51.php
from datetime import datetime, timezone

# For current time
timestamp = datetime.now(timezone.utc).isoformat()
# Produces: "2026-01-22T10:30:45.123456+00:00"

# For file mtime (Unix epoch float)
mtime = os.stat(filepath).st_mtime
timestamp = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
```

### Pattern 3: Optional Metadata Fields Based on --verbose

**What:** Same JSON schema, but verbose adds optional metadata fields
**When to use:** Maintaining backward compatibility while offering richer data
**Example:**
```python
# Source: https://blog.kellybrazil.com/2021/12/03/tips-on-adding-json-output-to-your-cli-app/
def format_match_group(self, file_hash, files_dir1, files_dir2):
    group = {
        "hash": file_hash,
        "files_dir1": sorted(files_dir1),
        "files_dir2": sorted(files_dir2)
    }

    # Add optional metadata when verbose=True
    if self.verbose:
        group["metadata"] = {
            "file_sizes": {...},
            "modified_times": {...}
        }

    self._data["matches"].append(group)
```

### Anti-Patterns to Avoid

- **JSON Lines (JSONL) for CLI tools with complete results:** JSONL is for streaming/incremental output. CLI tools that process all input before outputting should use single JSON object.
- **Errors to stdout in JSON mode:** Errors should still go to stderr, even with `--json`. Only successful data goes to stdout. Prevents unparseable output with multiple JSON objects.
- **Dynamic keys in JSON:** Avoid using filenames or hashes as object keys. Use arrays of objects with static keys instead.
- **Large numbers without quotes:** File sizes are fine as integers, but UUIDs or very large IDs should be strings to prevent precision loss.
- **Mixing text and JSON on stdout:** With `--json`, ALL output to stdout must be valid JSON. Progress/status messages must go to stderr (already handled by logger).

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON escaping | Manual string concatenation | `json.dumps()` | Handles Unicode, special chars, escaping correctly |
| Timestamp formatting | Manual date string building | `datetime.isoformat()` | Produces RFC 3339 compliant timestamps |
| Deterministic JSON ordering | Custom sorting logic | `sorted()` on all collections | Simple, consistent, Pythonic |

**Key insight:** The Phase 5 formatter abstraction already provides the structure. Phase 6 just adds JsonCompareFormatter and JsonActionFormatter implementations that accumulate data and serialize with `json.dumps()`.

## Common Pitfalls

### Pitfall 1: Errors to stdout Breaking JSON Parsability

**What goes wrong:** Running `filematcher dir1 dir2 --json` outputs error messages to stdout, creating unparseable output with multiple JSON objects
**Why it happens:** Forgetting that stdout must contain ONLY valid JSON in JSON mode
**How to avoid:**
1. ALL errors/warnings go to stderr (already handled by logger)
2. Only successful data goes to stdout
3. Exit code indicates success/failure
4. In JSON mode, if operation fails completely, output valid JSON with error info, not text
**Warning signs:** `jq` fails to parse output, "parse error" messages

### Pitfall 2: JSON Lines When Single Object is Better

**What goes wrong:** Using JSONL format for CLI tool that processes everything before output
**Why it happens:** Seeing tools like ripgrep use JSONL and assuming it's the standard
**How to avoid:**
1. JSONL is for streaming/incremental output (like grep searching millions of files)
2. Single JSON object is for "complete results" tools (like file matcher that indexes both dirs first)
3. User can pipe single JSON to `jq` just as easily as JSONL
**Warning signs:** Every match group is a separate JSON object on stdout during execution

### Pitfall 3: Verbose Changes Schema Structure

**What goes wrong:** `--json` and `--json --verbose` produce incompatible schemas
**Why it happens:** Trying to make verbose mode "totally different" rather than "extended"
**How to avoid:**
1. Same schema structure always
2. Verbose adds optional fields (e.g., "metadata" object)
3. Non-verbose omits those fields
4. Parsers that ignore unknown fields work with both
**Warning signs:** Need different parsers for verbose vs non-verbose JSON

### Pitfall 4: Non-Deterministic JSON Output

**What goes wrong:** Same input produces different JSON output ordering between runs
**Why it happens:** Dict iteration, unsorted file lists
**How to avoid:**
1. Use `sorted()` on ALL collections before adding to JSON structure
2. Sort match groups by a consistent key (e.g., first file in dir1)
3. Sort file lists within groups
4. Sort statistics keys if using dict comprehensions
**Warning signs:** Git diffs show reordering with no actual changes, flaky tests

### Pitfall 5: Timestamps as Unix Epoch Integers

**What goes wrong:** JSON contains `"mtime": 1737546645.123`
**Why it happens:** Using raw `os.stat().st_mtime` value
**How to avoid:**
1. Convert to RFC 3339 string: `datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()`
2. Human-readable, self-documenting
3. Includes timezone info
4. Standard for JSON/API timestamps
**Warning signs:** Timestamps are large integers, users need to convert manually

### Pitfall 6: Missing Schema Version Field

**What goes wrong:** JSON output has no version field, breaking when schema evolves
**Why it happens:** Thinking version isn't needed for "v1"
**How to avoid:**
1. Always include `"version": "1.0"` from the start
2. Allows future schema changes with backward compatibility
3. Parsers can switch behavior based on version
**Warning signs:** No version field in JSON root object

## Code Examples

Verified patterns from official sources:

### JsonCompareFormatter Implementation Skeleton

```python
# Pattern: Accumulate data, serialize on finalize
import json
from datetime import datetime, timezone

class JsonCompareFormatter(CompareFormatter):
    """JSON output formatter for compare mode."""

    def __init__(self, verbose: bool = False):
        super().__init__(verbose)
        self._data = {
            "version": "1.0",
            "directories": {},
            "hash_algorithm": "",
            "matches": [],
            "unmatched": {},
            "statistics": {}
        }

    def format_header(self, dir1: str, dir2: str, hash_algo: str) -> None:
        self._data["directories"] = {
            "dir1": dir1,
            "dir2": dir2
        }
        self._data["hash_algorithm"] = hash_algo

    def format_match_group(
        self,
        file_hash: str,
        files_dir1: list[str],
        files_dir2: list[str]
    ) -> None:
        group = {
            "hash": file_hash,
            "files_dir1": sorted(files_dir1),
            "files_dir2": sorted(files_dir2)
        }

        # Add optional metadata when verbose
        if self.verbose:
            metadata = {}
            for filepath in files_dir1 + files_dir2:
                stat_info = os.stat(filepath)
                metadata[filepath] = {
                    "size_bytes": stat_info.st_size,
                    "modified": datetime.fromtimestamp(
                        stat_info.st_mtime,
                        tz=timezone.utc
                    ).isoformat()
                }
            group["metadata"] = metadata

        self._data["matches"].append(group)

    def format_unmatched(self, dir_label: str, files: list[str]) -> None:
        self._data["unmatched"][dir_label] = sorted(files)

    def format_summary(
        self,
        match_count: int,
        matched_files1: int,
        matched_files2: int,
        unmatched1: int,
        unmatched2: int
    ) -> None:
        self._data["statistics"] = {
            "match_groups": match_count,
            "matched_files_dir1": matched_files1,
            "matched_files_dir2": matched_files2,
            "unmatched_files_dir1": unmatched1,
            "unmatched_files_dir2": unmatched2
        }

    def finalize(self) -> None:
        # Sort match groups for deterministic output
        self._data["matches"].sort(key=lambda g: (g["files_dir1"][0] if g["files_dir1"] else "", g["hash"]))

        # Output with 2-space indentation
        print(json.dumps(self._data, indent=2))
```

### File Metadata Extraction with RFC 3339 Timestamps

```python
# Source: https://docs.python.org/3/library/os.html#os.stat
# Source: https://www.w3resource.com/python-exercises/date-time-exercise/python-date-time-exercise-51.php
import os
from datetime import datetime, timezone

def get_file_metadata(filepath: str) -> dict:
    """Extract file metadata with RFC 3339 timestamps."""
    stat_info = os.stat(filepath)

    return {
        "size_bytes": stat_info.st_size,
        "modified": datetime.fromtimestamp(
            stat_info.st_mtime,
            tz=timezone.utc
        ).isoformat(),
        # Note: st_ctime is metadata change time on Unix, creation time on Windows
        # Only include if explicitly valuable
    }

# Produces: "modified": "2026-01-22T10:30:45.123456+00:00"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Unix epoch integers for timestamps | RFC 3339 strings | ~2015 (JSON API best practices) | Human-readable, self-documenting, timezone-aware |
| JSON Lines for all CLI tools | Single JSON object for complete results, JSONL for streaming | ~2018 (jq, ripgrep patterns) | Better fit for different use cases |
| Compact JSON output | 2-space indented JSON or compact | ~2019 (jq default) | More human-readable, jq can reformat anyway |
| No schema versioning | Always include "version" field | ~2020 (API versioning patterns) | Enables schema evolution |
| SchemaVer (MODEL-REVISION-ADDITION) | SemVer for schema versions | Ongoing debate | Most CLIs use simple "1.0" string, not full semver |

**Deprecated/outdated:**
- **JSONL for non-streaming CLIs:** Use single JSON object for tools that process everything before outputting results
- **Timestamps as integers:** Use RFC 3339 strings for human readability and timezone info
- **Errors to stdout in JSON mode:** Always use stderr for errors, stdout for data only

## Open Questions

Things that couldn't be fully resolved:

1. **Schema documentation format**
   - What we know: Tools exist to generate markdown from JSON Schema (jsonschema2md, jsonschema-markdown), but adding full JSON Schema spec might be overkill for Phase 6
   - What's unclear: Whether to write JSON Schema file, markdown table, or inline comments
   - Recommendation: Start with markdown table in README or man page showing field names, types, and descriptions. Add formal JSON Schema later if users request it.

2. **--json interaction with --summary**
   - What we know: `--summary` currently shows only summary statistics, no match groups
   - What's unclear: Should `--json --summary` output minimal JSON with only statistics, or full JSON?
   - Recommendation: `--json --summary` outputs same full JSON structure but with empty/omitted match details. Keeps schema consistent, parsers work the same.

3. **File metadata richness**
   - What we know: `os.stat()` provides size, mtime, ctime (varies by platform), atime
   - What's unclear: Which timestamps to include in verbose mode
   - Recommendation: Include only size and mtime in verbose mode. mtime is most useful (when file content changed), size is essential. Avoid ctime (platform-dependent meaning) and atime (often disabled for performance).

## Sources

### Primary (HIGH confidence)
- [Python json module documentation](https://docs.python.org/3/library/json.html) - json.dumps(), indent parameter, separators
- [Python os.stat documentation](https://docs.python.org/3/library/stat.html) - File metadata, stat_result attributes
- [Python datetime documentation](https://docs.python.org/3/library/datetime.html) - isoformat() for RFC 3339
- [ripgrep man page](https://manpages.debian.org/testing/ripgrep/rg.1.en.html) - --json message types and schema

### Secondary (MEDIUM confidence)
- [Tips on Adding JSON Output to Your CLI App](https://blog.kellybrazil.com/2021/12/03/tips-on-adding-json-output-to-your-cli-app/) - Best practices, schema design, dos/don'ts
- [Command Line Interface Guidelines (clig.dev)](https://clig.dev/) - stdout/stderr separation, flag design
- [jdupes JSON output](https://manpages.debian.org/testing/jdupes/jdupes.1.en.html) - -j/--json flag (duplicate file finder, similar tool)
- [ISO 8601 vs RFC 3339 Guide](https://toolshref.com/iso-8601-vs-rfc-3339-json-api-dates/) - Timestamp format best practices
- [JSONL vs JSON comparison](https://jsonltools.com/jsonl-vs-json) - When to use each format
- [Python RFC 3339 timestamps](https://www.w3resource.com/python-exercises/date-time-exercise/python-date-time-exercise-51.php) - datetime.isoformat() usage

### Tertiary (LOW confidence)
- [WebSearch: CLI JSON output patterns](https://oclif.io/docs/json/) - oclif framework patterns (different from Python, but informative)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All stdlib, well-documented, stable APIs
- Architecture: HIGH - Patterns well-established in Phase 5, JSON output conventions clear
- Pitfalls: MEDIUM - Based on general Python/JSON experience and documented issues in npm/cli and forcedotcom/cli GitHub issues, not file-matcher-specific

**Research date:** 2026-01-22
**Valid until:** 2026-02-22 (30 days - stable domain, Python stdlib doesn't change frequently)
