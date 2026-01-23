# Phase 9: Unify Default and Action Output for Groups - Research

**Researched:** 2026-01-23
**Domain:** CLI output format unification for duplicate file groups
**Confidence:** HIGH

## Summary

This phase unifies the output format between compare mode and action mode for displaying duplicate groups. Currently, compare mode uses a hash-centric format (`Hash: xxx... / Files in dir1: / Files in dir2:`) while action mode uses a master-centric format (`[MASTER] / [WOULD HARDLINK]`). The goal is to make both modes use a consistent group display structure while preserving mode-appropriate labels.

The key insight is that compare mode is fundamentally showing file groups with matching content across two directories, while action mode is showing master/duplicate relationships. However, the underlying data is the same (groups of files with identical content), and the display can be unified by adopting the master-centric [MASTER]/[DUP] structure for both modes. In compare mode without --action, there is no "master" per se, but dir1 files can be treated as masters for display consistency.

The research confirms that unifying to the [MASTER]/[DUP] format would provide: (1) consistent visual structure across modes, (2) clearer semantic meaning (one file is "primary", others are "duplicates"), and (3) simpler formatter implementation since TextActionFormatter already has the desired format.

**Primary recommendation:** Adopt the action mode's `[MASTER]`/`[DUP]` hierarchical format for compare mode, using `[GROUP]` or similar label when no action is specified. Keep hash display as a dim sub-line for technical reference. This provides unified visual structure while maintaining semantic accuracy.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `abc` | stdlib | Abstract Base Classes | Already used by formatters |
| `print()` | stdlib | Text output | Existing output mechanism |
| Color helpers | N/A | ANSI coloring | Implemented in Phase 8 |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Existing formatters | N/A | CompareFormatter ABC | Modify `format_match_group()` method |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Unified [MASTER]/[DUP] | Keep separate formats | Separate formats are confusing; unified is cleaner |
| [GROUP]/[FILE] labels | [DIR1]/[DIR2] labels | GROUP/FILE is more generic but less informative about source |
| Hash on first line | Hash as sub-line | Hash as sub-line keeps focus on files |

**Installation:**
```bash
# All standard library - no installation required
```

## Architecture Patterns

### Current Output Comparison

```
# COMPARE MODE (current):
Hash: bc746e25b4...
  Files in test_dir1:
    /path/to/file1.txt
  Files in test_dir2:
    /path/to/different_name.txt

# ACTION MODE (current):
[MASTER] /path/to/file1.txt
    [WOULD HARDLINK] /path/to/different_name.txt
```

### Proposed Unified Format

```
# COMPARE MODE (proposed):
[dir1] /path/to/file1.txt
    [dir2] /path/to/different_name.txt
  (Hash: bc746e25b4...)

# ACTION MODE (no change):
[MASTER] /path/to/file1.txt
    [WOULD HARDLINK] /path/to/different_name.txt
```

### Pattern 1: Directory-Based Labels for Compare Mode

**What:** Use directory names as labels instead of generic "MASTER"/"DUP" when no action specified
**When to use:** Compare mode (no --action flag)
**Example:**
```python
# Source: Existing TextCompareFormatter pattern
def format_match_group(self, file_hash: str, files_dir1: list[str], files_dir2: list[str]) -> None:
    """Format a group of matching files using unified structure."""
    # First file from dir1 is the "primary" for display purposes
    for i, f in enumerate(sorted(files_dir1)):
        if i == 0:
            # First dir1 file gets primary position
            print(green(f"[{self.dir1_name}] {f}", self.cc))
        else:
            # Additional dir1 files indented
            print(f"    [{self.dir1_name}] {f}")

    # Dir2 files are shown as "matches"
    for f in sorted(files_dir2):
        print(yellow(f"    [{self.dir2_name}] {f}", self.cc))

    # Hash as de-emphasized technical detail
    print(dim(f"  (Hash: {file_hash[:10]}...)", self.cc))
    print()
```

### Pattern 2: Consistent Indentation Hierarchy

**What:** 4-space indentation for "secondary" files (duplicates or matches)
**When to use:** All modes
**Example:**
```
[LABEL] /primary/file/path
    [LABEL] /secondary/file/path
    [LABEL] /another/secondary/path
```

### Pattern 3: Hash as Sub-Detail

**What:** Move hash from header position to trailing detail
**When to use:** Compare mode (action mode doesn't show hash)
**Example:**
```python
# Hash shown as dim, indented technical note
print(dim(f"  (Hash: {file_hash[:10]}...)", self.cc))
```

### Anti-Patterns to Avoid

- **Different structures per mode:** Both modes should use the same hierarchical layout (primary file, indented secondaries)
- **Hash as prominent header:** Hash is technical detail; file paths are what users care about
- **Generic labels everywhere:** Labels should communicate meaning ([dir1] vs [dir2] or [MASTER] vs [WOULD X])
- **Breaking action mode format:** Action mode format is already good; compare mode should adapt to it

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| File sorting | Custom sort logic | `sorted()` already in place | Determinism already implemented (OUT-04) |
| Color application | New color scheme | Existing green/yellow/dim helpers | Phase 8 already established palette |
| Label formatting | Format strings everywhere | Consistent f-string pattern | Maintainability |
| Indentation | Manual spaces | Constant `INDENT = "    "` | Single source of truth |

**Key insight:** The action mode format is well-designed. The task is adapting compare mode to use a similar structure, not inventing something new.

## Common Pitfalls

### Pitfall 1: Breaking Backward Compatibility

**What goes wrong:** Scripts parsing compare mode output break
**Why it happens:** Output structure changes from hash-first to file-first
**How to avoid:**
1. Document breaking change in release notes
2. Provide --json for reliable machine parsing (already implemented)
3. The change is intentional - human readability is improved
**Warning signs:** User reports of broken grep/awk scripts

### Pitfall 2: Losing Hash Information

**What goes wrong:** Users can't see which files share content
**Why it happens:** Hash hidden or removed
**How to avoid:**
1. Keep hash as trailing detail line
2. In verbose mode, could show full hash
3. Hash remains in JSON output (unchanged)
**Warning signs:** Users asking "how do I see the hash?"

### Pitfall 3: Ambiguous Primary Selection in Compare Mode

**What goes wrong:** Unclear which file is "primary" when multiple files in dir1
**Why it happens:** Compare mode doesn't have master concept
**How to avoid:**
1. Use deterministic selection (first alphabetically in dir1)
2. Or show all dir1 files as equally positioned
3. Document behavior
**Warning signs:** Users confused about ordering

### Pitfall 4: Inconsistent Color Application

**What goes wrong:** Compare mode colors don't match action mode semantics
**Why it happens:** Applying master/duplicate colors when there's no master
**How to avoid:**
1. In compare mode: dir1 = green (like master), dir2 = yellow (like duplicate)
2. This maintains visual consistency without implying master/duplicate relationship
3. Or use neutral colors for both in compare mode
**Warning signs:** Color meanings conflict between modes

### Pitfall 5: Verbose Mode Divergence

**What goes wrong:** Verbose mode shows different info per mode
**Why it happens:** Each mode evolved independently
**How to avoid:**
1. Define what verbose adds: file sizes, full hashes, timestamps
2. Apply consistently in both modes
3. Use same formatting patterns
**Warning signs:** Verbose output looks different between modes

## Code Examples

Verified patterns from existing codebase:

### Current Compare Mode Implementation (to be modified)

```python
# Source: TextCompareFormatter.format_match_group (line 508-524)
def format_match_group(self, file_hash: str, files_dir1: list[str], files_dir2: list[str]) -> None:
    # Hash in dim (de-emphasize technical details)
    print(dim(f"Hash: {file_hash[:10]}...", self.cc))
    print(f"  Files in {self.dir1_name}:")
    for f in sorted(files_dir1):
        print(f"    {f}")
    print(f"  Files in {self.dir2_name}:")
    for f in sorted(files_dir2):
        print(f"    {f}")
    print()
```

### Action Mode Implementation (reference pattern)

```python
# Source: format_duplicate_group function (line 1224-1279)
def format_duplicate_group(
    master_file: str,
    duplicates: list[str],
    action: str | None = None,
    ...
) -> list[str]:
    lines = []

    # Format master line
    if verbose and file_sizes:
        size = file_sizes.get(master_file, 0)
        size_str = format_file_size(size)
        dup_count = len(duplicates)
        lines.append(f"[MASTER] {master_file} ({dup_count} duplicates, {size_str})")
    else:
        lines.append(f"[MASTER] {master_file}")

    # Format duplicate lines (4-space indent)
    for dup in sorted(duplicates):
        lines.append(f"    [{action_label}] {dup}")

    return lines
```

### Proposed Unified Compare Mode

```python
# Proposed: TextCompareFormatter.format_match_group
def format_match_group(self, file_hash: str, files_dir1: list[str], files_dir2: list[str]) -> None:
    """Format a group of matching files with unified structure.

    Uses hierarchical format similar to action mode:
    - First dir1 file as "primary" (unindented)
    - Additional dir1 files and all dir2 files indented
    - Hash as trailing technical detail
    """
    sorted_dir1 = sorted(files_dir1)
    sorted_dir2 = sorted(files_dir2)

    # Primary file: first from dir1 (green, unindented)
    primary = sorted_dir1[0]
    print(green(f"[{self.dir1_name}] {primary}", self.cc))

    # Additional dir1 files (indented, same color)
    for f in sorted_dir1[1:]:
        print(green(f"    [{self.dir1_name}] {f}", self.cc))

    # Dir2 files (indented, yellow like duplicates)
    for f in sorted_dir2:
        print(yellow(f"    [{self.dir2_name}] {f}", self.cc))

    # Hash as de-emphasized detail
    print(dim(f"  Hash: {file_hash[:10]}...", self.cc))
    print()
```

### Alternative: All Files Equal (No Primary)

```python
# Alternative approach: no primary designation
def format_match_group(self, file_hash: str, files_dir1: list[str], files_dir2: list[str]) -> None:
    """Format match group with equal treatment of all files."""
    sorted_dir1 = sorted(files_dir1)
    sorted_dir2 = sorted(files_dir2)

    # All dir1 files (green)
    for f in sorted_dir1:
        print(green(f"[{self.dir1_name}] {f}", self.cc))

    # All dir2 files (yellow, indented to show "matching")
    for f in sorted_dir2:
        print(yellow(f"    [{self.dir2_name}] {f}", self.cc))

    # Hash detail
    print(dim(f"  Hash: {file_hash[:10]}...", self.cc))
    print()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hash-centric display | File-centric display | This phase | User focus on files, not hashes |
| Separate mode formats | Unified hierarchical format | This phase | Consistent UX |
| Hash as header | Hash as detail | This phase | De-emphasize technical info |

**Deprecated/outdated:**
- **Hash: xxx header line**: Moving to trailing position as implementation detail
- **"Files in dirX:" sub-headers**: Replaced by inline labels `[dirX]`

## Open Questions

Things that couldn't be fully resolved:

1. **Primary file selection in compare mode**
   - What we know: No natural "master" in compare mode
   - Options: (A) First file alphabetically from dir1, (B) All files at same level
   - Recommendation: Option A - first file as primary matches action mode structure
   - Rationale: Visual consistency trumps semantic purity

2. **Multiple files in same directory**
   - What we know: A hash can match multiple files in dir1 (intra-directory duplicates)
   - What's unclear: Should they all be primary, or first-as-primary?
   - Recommendation: First alphabetically as primary, others indented with same label
   - This mirrors action mode behavior (one master, rest as duplicates)

3. **Hash display format**
   - What we know: Currently truncated to 10 chars
   - Options: Keep truncated, show full in verbose, remove entirely
   - Recommendation: Keep truncated, show full hash in verbose mode
   - Rationale: Hash is useful for verification but not primary information

4. **Color semantics in compare mode**
   - What we know: Action mode uses green=protected, yellow=will-be-modified
   - What's unclear: Same semantics appropriate for compare mode?
   - Recommendation: Use same colors (green=dir1, yellow=dir2) for visual consistency
   - The slight semantic mismatch is acceptable for UX consistency

5. **Breaking change communication**
   - What we know: This changes compare mode output structure
   - Recommendation: Note in CHANGELOG as breaking change, recommend --json for scripts

## Implementation Notes

### Files to Modify

1. **TextCompareFormatter.format_match_group()** - Main change
   - Change from hash-header to file-hierarchy format
   - Apply color per directory
   - Add hash as trailing detail

2. **JsonCompareFormatter.format_match_group()** - No change needed
   - JSON structure already file-centric
   - Hash included as property

3. **Tests: test_cli.py** - Update expected output patterns
   - Tests that check compare mode text output will need updating

### Scope

This phase is focused specifically on:
- `format_match_group()` method in `TextCompareFormatter`
- Related tests

NOT in scope:
- Modifying action mode (already good)
- JSON output (already unified)
- Statistics footer (already unified in Phase 7)
- Headers/banners (already unified in Phase 7)

### Estimated Changes

- ~30 lines modified in `TextCompareFormatter.format_match_group()`
- ~50 lines test updates (expected output changes)
- Documentation updates (README output examples)

## Sources

### Primary (HIGH confidence)
- Existing codebase: `file_matcher.py` lines 508-524 (TextCompareFormatter.format_match_group)
- Existing codebase: `file_matcher.py` lines 1224-1279 (format_duplicate_group function)
- Phase 7 RESEARCH.md - Output unification patterns
- Phase 8 RESEARCH.md - Color application patterns

### Secondary (MEDIUM confidence)
- General CLI UX principles - consistent output formats across modes
- Unix convention - tools should have predictable output structure

### Tertiary (LOW confidence)
- None - this is primarily internal consistency work

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All existing code, no new dependencies
- Architecture: HIGH - Clear pattern to follow (action mode format)
- Pitfalls: MEDIUM - Breaking change management requires care

**Research date:** 2026-01-23
**Valid until:** 2026-02-23 (30 days - stable domain, internal refactoring)
