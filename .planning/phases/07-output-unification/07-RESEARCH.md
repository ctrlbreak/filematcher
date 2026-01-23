# Phase 7: Output Unification - Research

**Researched:** 2026-01-23
**Domain:** CLI output consistency, stream separation, unified formatting
**Confidence:** HIGH

## Summary

This phase unifies output formatting across compare mode and action mode, adds a statistics footer to all modes, and implements proper stdout/stderr stream separation. The key changes are: (1) consistent output structure with header, data sections, and statistics footer in both modes; (2) routing progress/status messages to stderr and data output to stdout; and (3) adding a `--quiet` flag to suppress non-essential output.

Research confirms that stdout/stderr separation follows well-established Unix conventions. Progress messages, warnings, and status updates belong on stderr so they don't pollute piped data. The existing JSON mode already routes logger messages to stderr correctly - text mode needs the same treatment. The `--quiet` flag is a standard Unix convention (`-q, --quiet`) found in tools like curl, grep, and httpie.

**Primary recommendation:** Implement stdout/stderr separation for text mode (matching JSON mode behavior), add `--quiet` flag to suppress progress/headers, and unify output sections across modes. Statistics footer should appear in both compare and action modes with consistent formatting.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `sys.stdout` / `sys.stderr` | stdlib | Stream output routing | Python's standard mechanism for stdout/stderr |
| `logging` | stdlib | Status/progress messages | Already used for logger, just needs stderr routing |
| `sys.stdout.isatty()` | stdlib | TTY detection | Standard way to detect interactive terminal |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `contextlib.redirect_stdout` | stdlib | Output capture in tests | Testing that output goes to correct stream |
| `unittest.mock.patch` | stdlib | Mocking streams | Testing stderr/stdout separation |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Routing logger to stderr | Separate print statements to stderr | Logger is cleaner, already configured |
| `--quiet` suppressing all non-data | `--silent` or `-s` | `--quiet/-q` is more conventional for this behavior |
| Per-mode header detection | TTY-only headers | Explicit --quiet is clearer than magic TTY detection |

**Installation:**
```bash
# All standard library - no installation required
```

## Architecture Patterns

### Recommended Output Structure

```
# Compare mode:
[HEADER: "Compare mode: dir1 vs dir2"]
[SUMMARY LINE: "Found 12 duplicate groups (47 files, 1.2GB reclaimable)"]

[DATA: match groups]

[FOOTER: statistics]

# Action mode (preview):
[HEADER: "Action mode (PREVIEW): hardlink dir1 vs dir2"]
[SUMMARY LINE: "Found 12 duplicate groups (47 files, 1.2GB reclaimable)"]

[DATA: master/duplicate groups with action markers]

[FOOTER: statistics]
```

### Pattern 1: Stream Separation (OUT-03)

**What:** Route progress/status to stderr, data output to stdout
**When to use:** All output operations
**Example:**
```python
# Source: https://clig.dev/
import sys
import logging

# Configure logger for stderr
handler = logging.StreamHandler(sys.stderr)  # Always stderr for status
logger.handlers = [handler]

# Data goes to stdout via formatter
print(formatted_data)  # Data to stdout
logger.info("Processing...")  # Status to stderr
```

### Pattern 2: Quiet Mode Flag (Standard Convention)

**What:** `--quiet/-q` suppresses progress, warnings, header - only data remains
**When to use:** Scripting, piping, automation
**Example:**
```python
# Source: https://tldp.org/LDP/abs/html/standard-options.html
parser.add_argument('--quiet', '-q', action='store_true',
                    help='Suppress progress, warnings, and headers')

# In main():
if args.quiet:
    logger.setLevel(logging.ERROR)  # Only errors get through
    skip_header = True
    skip_summary_line = True
# Data sections still output normally
```

### Pattern 3: Unified Section Structure

**What:** Both modes use identical section ordering: header -> summary -> data -> footer
**When to use:** All output modes (compare, action preview, action execute)
**Example:**
```python
# Source: CONTEXT.md decisions
def output_unified_structure(formatter, mode, ...):
    formatter.format_header(mode, dirs)          # Mode-specific header
    formatter.format_summary_line(stats)         # One-liner summary
    formatter.format_data_sections(groups)       # Match/duplicate groups
    formatter.format_statistics_footer(stats)    # Detailed stats
```

### Pattern 4: Mode-Explicit Headers

**What:** Header clearly indicates mode and distinguishes PREVIEW vs EXECUTING
**When to use:** All modes must have explicit headers
**Example:**
```
# Compare mode
Compare mode: /path/to/dir1 vs /path/to/dir2

# Action mode preview
Action mode (PREVIEW): hardlink /path/to/dir1 vs /path/to/dir2

# Action mode executing
Action mode (EXECUTING): hardlink /path/to/dir1 vs /path/to/dir2
```

### Anti-Patterns to Avoid

- **Mixing stdout and stderr for same logical output type:** All data must go to stdout, all status to stderr. Never mix.
- **Magic TTY-based suppression without explicit flag:** Provide `--quiet` rather than silently suppressing based on TTY detection.
- **Different structure between modes:** Both modes must use identical section ordering for consistency.
- **Ambiguous mode indicators:** Must always be clear whether in PREVIEW or EXECUTING mode.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Stream routing | Custom print-to-stream function | logger to stderr, print to stdout | Logger already handles formatting, timestamps |
| TTY detection | Custom isatty logic | `sys.stdout.isatty()` | Standard, handles edge cases |
| Quiet mode parsing | Custom flag parsing | argparse `--quiet/-q` | Conventional, well-documented |
| Output buffering | Manual string building | Formatter classes from Phase 5 | Already structured, tested |

**Key insight:** Phase 5 created the formatter abstraction. Phase 7 should modify how formatters receive configuration (quiet mode) and ensure formatters write to correct streams - not reimplement formatting logic.

## Common Pitfalls

### Pitfall 1: Breaking Existing Text Mode Behavior

**What goes wrong:** Moving logger to stderr changes user scripts that parse stdout
**Why it happens:** Users may have been parsing "Using MD5..." and "Indexing directory..." lines
**How to avoid:**
1. Document in release notes that status messages now go to stderr
2. Provide `--quiet` as migration path for scripts
3. Test that data output (match groups, statistics) remains identical
**Warning signs:** User reports "output changed", scripts break on upgrade

### Pitfall 2: Forgetting to Update Test Assertions

**What goes wrong:** Tests capture stdout but status messages moved to stderr
**Why it happens:** Tests use `redirect_stdout` only
**How to avoid:**
1. Update tests to capture both streams: `redirect_stdout` + `redirect_stderr`
2. Assert status messages appear on stderr, data on stdout
3. Verify JSON mode tests still work (already uses stderr for status)
**Warning signs:** Tests fail after stream separation

### Pitfall 3: Inconsistent Statistics Between Modes

**What goes wrong:** Compare mode shows different statistics than action mode
**Why it happens:** Different code paths compute different stats
**How to avoid:**
1. Use shared statistics calculation function
2. Both modes show: group count, file counts, space calculations
3. Action mode adds action-specific counts on top of base stats
**Warning signs:** Users confused why stats differ between modes

### Pitfall 4: Header Not Distinguishing PREVIEW vs EXECUTING

**What goes wrong:** User accidentally runs --execute thinking they're in preview
**Why it happens:** Header doesn't clearly indicate mode
**How to avoid:**
1. PREVIEW header: "Action mode (PREVIEW): hardlink"
2. EXECUTING header: "Action mode (EXECUTING): hardlink"
3. Use caps/emphasis to make EXECUTING unmistakable
4. Preserve interactive confirmation unless --yes
**Warning signs:** Users report accidentally executing actions

### Pitfall 5: --quiet Suppressing Too Much or Too Little

**What goes wrong:** --quiet suppresses data, or doesn't suppress enough noise
**Why it happens:** Unclear boundary between "data" and "status"
**How to avoid:**
1. Define clearly: data = match groups, statistics footer, JSON structure
2. Define clearly: status = progress, indexing messages, header banner, summary line
3. --quiet suppresses status, never data
4. Errors always display (even with --quiet) per httpie convention
**Warning signs:** Users get unexpected output with --quiet

## Code Examples

Verified patterns from official sources and existing codebase:

### Stream Routing Configuration

```python
# Source: https://clig.dev/ and existing JSON mode pattern
def configure_logging(verbose: bool, json_mode: bool, quiet: bool) -> None:
    """Configure logger for stderr routing."""
    log_level = logging.ERROR if quiet else (logging.DEBUG if verbose else logging.INFO)

    # ALWAYS use stderr for logging - this is the key change
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger.handlers = [handler]
    logger.setLevel(log_level)
```

### Unified Header Format

```python
# Source: CONTEXT.md decisions
def format_unified_header(
    mode: str,  # "compare" or "action"
    action: str | None,  # "hardlink", "symlink", "delete" or None
    dir1: str,
    dir2: str,
    preview: bool = True
) -> str:
    """Generate mode-explicit header line."""
    if mode == "compare":
        return f"Compare mode: {dir1} vs {dir2}"
    elif mode == "action":
        state = "PREVIEW" if preview else "EXECUTING"
        return f"Action mode ({state}): {action} {dir1} vs {dir2}"
```

### Summary Line Format

```python
# Source: CONTEXT.md - "Found 12 duplicate groups (47 files, 1.2GB reclaimable)"
def format_summary_line(
    group_count: int,
    duplicate_count: int,
    space_savings: int
) -> str:
    """Generate one-liner summary for header area."""
    space_str = format_file_size(space_savings)
    return f"Found {group_count} duplicate groups ({duplicate_count} files, {space_str} reclaimable)"
```

### Quiet Mode Integration

```python
# Source: https://tldp.org/LDP/abs/html/standard-options.html convention
# Add to argparse:
parser.add_argument('--quiet', '-q', action='store_true',
                    help='Suppress progress, headers, and warnings - only output data')

# In main():
if not args.quiet:
    formatter.format_header(...)
    formatter.format_summary_line(...)
# Data always outputs
formatter.format_data_sections(...)
formatter.format_statistics_footer(...)
```

### Statistics Footer (Unified)

```python
# Both modes use same base statistics, action mode adds action-specific stats
def format_statistics_footer(
    group_count: int,
    duplicate_count: int,
    master_count: int,
    space_savings: int,
    action: str | None = None,  # If action mode
    action_stats: dict | None = None  # {"hardlinked": 5, "deleted": 2}
) -> list[str]:
    """Format unified statistics footer."""
    lines = []
    lines.append("")
    lines.append("--- Statistics ---")
    lines.append(f"Duplicate groups: {group_count}")
    lines.append(f"Total files: {master_count + duplicate_count}")
    lines.append(f"Master files: {master_count}")
    lines.append(f"Duplicate files: {duplicate_count}")
    lines.append(f"Space reclaimable: {format_file_size(space_savings)}")

    # Action-specific stats (only in action mode after execution)
    if action_stats:
        lines.append("")
        for action_name, count in action_stats.items():
            lines.append(f"  {action_name}: {count}")

    return lines
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| All output to stdout | Data to stdout, status to stderr | Unix convention | Enables clean piping |
| No quiet flag | `--quiet/-q` standard | Long-standing convention | Standard across tools |
| Mode-implicit headers | Mode-explicit headers | Best practice | Clear user understanding |
| Different stats per mode | Unified stats footer | Output rationalization | Consistent user experience |

**Deprecated/outdated:**
- **Mixing status and data on stdout:** Breaks piping, should use stderr for status
- **TTY-based magic suppression:** Prefer explicit `--quiet` flag for clarity
- **Mode-ambiguous headers:** Always indicate PREVIEW vs EXECUTING explicitly

## Open Questions

Things that couldn't be fully resolved:

1. **Header summary to stdout or stderr?**
   - What we know: CONTEXT.md marks this as Claude's discretion
   - Options: stdout (part of data) or stderr (part of status)
   - Recommendation: stdout - it's summary of data, useful for scripted consumption
   - When --quiet is used, suppress header AND summary line but keep data/footer

2. **Verbose mode output stream**
   - What we know: CONTEXT.md says "Verbose info goes to same stream as related output"
   - Recommendation: Verbose file-by-file progress goes to stderr (status), verbose statistics go to stdout (data)

3. **Space savings format**
   - What we know: CONTEXT.md leaves exact format to Claude's discretion
   - Options: human-readable only ("1.2 GB") vs both ("1.2 GB (1,234,567,890 bytes)")
   - Recommendation: Default human-readable, verbose adds exact bytes
   - Rationale: Consistent with existing format_file_size() function

## Implementation Notes

### Current State Analysis

**Compare mode (no --action):**
- Header: "Using MD5..." + "Indexing directory..." (logger to stdout currently)
- Data: "Found N hashes...\n\nHash: xxx..." (print to stdout)
- Footer: None (no statistics in compare mode currently)

**Action mode (--action):**
- Header: "Using MD5..." + "Indexing..." + "=== PREVIEW MODE ==="
- Data: "[MASTER]...\n    [WOULD HARDLINK]..."
- Footer: "--- Statistics ---" with group/file counts

**Changes needed for OUT-01, OUT-02, OUT-03:**
1. Route logger to stderr in all modes (currently only JSON does this)
2. Add statistics footer to compare mode
3. Add unified header format showing mode explicitly
4. Add summary one-liner to both modes
5. Add --quiet flag to suppress header/progress
6. Ensure identical section structure in both modes

### Breaking Changes

This phase introduces a breaking change to text mode output:
- Status messages (Using MD5..., Indexing...) move from stdout to stderr
- Mitigation: Document in changelog, provide --quiet for scripts

This is acceptable because:
1. JSON mode already works this way
2. Unix convention supports this behavior
3. It enables proper piping (`filematcher dir1 dir2 | grep pattern`)

## Sources

### Primary (HIGH confidence)
- [Command Line Interface Guidelines (clig.dev)](https://clig.dev/) - stdout/stderr separation, quiet mode conventions
- [Standard Command-Line Options (TLDP)](https://tldp.org/LDP/abs/html/standard-options.html) - `-q, --quiet` convention
- Phase 5 RESEARCH.md - Formatter abstraction architecture
- Phase 6 RESEARCH.md - JSON output patterns

### Secondary (MEDIUM confidence)
- [12 Factor CLI Apps](https://medium.com/@jdxcode/12-factor-cli-apps-dd3c227a0e46) - CLI design philosophy
- [Python CLI Streams](https://julienharbulot.com/python-cli-streams.html) - Python-specific stream handling
- [HTTPie quiet output docs](https://httpie.io/docs/cli/quiet-output) - --quiet flag behavior reference

### Tertiary (LOW confidence)
- Various GitHub issues on --quiet flag implementations (gh cli, flow, spinnaker)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All stdlib, patterns from prior phases
- Architecture: HIGH - Follows Unix conventions, clear CONTEXT.md decisions
- Pitfalls: MEDIUM - Based on general CLI experience and prior phase learnings

**Research date:** 2026-01-23
**Valid until:** 2026-02-23 (30 days - stable domain)
