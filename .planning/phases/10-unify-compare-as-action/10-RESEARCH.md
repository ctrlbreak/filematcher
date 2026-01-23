# Phase 10: Unify Compare as Action - Research

**Researched:** 2026-01-23
**Domain:** Python CLI refactoring - unifying code paths
**Confidence:** HIGH

## Summary

This phase refactors the default compare mode into a "compare" action that reuses the action code path, eliminating duplicate formatter classes and branching logic in `main()`. The codebase currently has two parallel hierarchies: `CompareFormatter` (ABC + Text/JSON implementations) and `ActionFormatter` (ABC + Text/JSON implementations), with the `main()` function containing a top-level `if master_path:` branch that creates completely separate code paths.

The refactoring is purely internal - no external library research is needed. The work involves:
1. Adding "compare" to the action choices in argparse
2. Handling compare-specific validation (--execute with compare is an error)
3. Adapting ActionFormatter to handle the compare case (no banner, "Action: none" header)
4. Deleting CompareFormatter hierarchy entirely
5. Collapsing the main() branching to use the unified action flow

This is a straightforward refactoring pattern: remove duplication by generalizing the more feature-rich path (action mode) to handle the simpler case (compare mode). The key complexity is maintaining backward compatibility while changing internal structure.

**Primary recommendation:** Refactor incrementally - first make compare flow through ActionFormatter, verify tests pass, then delete CompareFormatter classes. Do not attempt big-bang replacement.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `abc` | stdlib | Abstract Base Classes | Already used for formatters |
| `argparse` | stdlib | CLI parsing | Already handles action choices |
| Python refactoring patterns | N/A | Incremental migration | Standard practice |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `unittest` | stdlib | Test verification | Verify no regressions |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Incremental refactoring | Big-bang rewrite | Big-bang risks test failures; incremental is safer |
| Delete CompareFormatter | Deprecate CompareFormatter | Clean deletion preferred - no users outside codebase |

**Installation:**
```bash
# All standard library - no installation required
```

## Architecture Patterns

### Current Architecture (Before)

```
main()
├── if master_path (action mode):
│   ├── ActionFormatter (JSON or Text)
│   ├── print_preview_output()
│   ├── execute_all_actions()
│   └── ~300 lines of action-specific code
│
└── else (compare mode):
    ├── CompareFormatter (JSON or Text)
    └── ~75 lines of compare-specific code
```

**Lines of code:**
- CompareFormatter ABC: lines 215-322 (~108 lines)
- TextCompareFormatter: lines 473-626 (~154 lines)
- JsonCompareFormatter: lines 629-794 (~166 lines)
- Compare mode branch in main(): lines 2601-2674 (~74 lines)
- **Total to remove/refactor: ~502 lines**

### Target Architecture (After)

```
main()
└── Action mode (action = compare|hardlink|symlink|delete):
    ├── ActionFormatter (JSON or Text)
    ├── if action != "compare": show banner
    ├── print_preview_output()
    ├── if action == "compare": skip execute path
    └── Unified ~350 lines
```

### Pattern 1: Action as Default with Explicit Option

**What:** Add "compare" as the default action value when no --action specified
**When to use:** CLI argument parsing
**Example:**
```python
# Source: Existing argparse pattern in file_matcher.py
parser.add_argument('--action', '-a',
    choices=['compare', 'hardlink', 'symlink', 'delete'],
    default='compare',  # Compare is default
    help='Action to take on duplicates (default: compare)')
```

### Pattern 2: Conditional Banner Display

**What:** Skip PREVIEW/EXECUTING banner for compare action
**When to use:** ActionFormatter.format_banner() and related
**Example:**
```python
# Source: Adapted from TextActionFormatter.format_banner (line 1030)
def format_banner(self) -> None:
    """Format banner - skip for compare action."""
    if self._action == "compare":
        return  # Compare mode doesn't show PREVIEW/EXECUTING
    if self.preview_mode:
        print(bold_yellow(format_preview_banner(), self.cc))
    else:
        print(format_execute_banner())
    print()
```

### Pattern 3: Header Shows "Action: none" for Compare

**What:** Display "Action: none" instead of "Action: compare"
**When to use:** format_unified_header()
**Example:**
```python
# Source: Adapted from TextActionFormatter.format_unified_header (line 1039)
def format_unified_header(self, action: str, dir1: str, dir2: str) -> None:
    """Format unified header."""
    if action == "compare":
        # Compare mode: no state (never modifies), show "none"
        header = f"Compare mode: {dir1} vs {dir2}"
        print(cyan(header, self.cc))
        # Note: No (PREVIEW)/(EXECUTING) for compare
    else:
        state = "PREVIEW" if self.preview_mode else "EXECUTING"
        header = f"Action mode ({state}): {action} {dir1} vs {dir2}"
        print(cyan(header, self.cc))
```

### Pattern 4: Incremental Migration via Adapter

**What:** Initially make compare flow use ActionFormatter via adapter, then simplify
**When to use:** During transition to minimize test changes
**Example:**
```python
# Temporary adapter pattern (may not be needed if direct works)
def compare_to_action_adapter(file_hash, files_dir1, files_dir2):
    """Convert compare mode data to action mode format."""
    # First file in dir1 is "master" for display purposes
    sorted_dir1 = sorted(files_dir1)
    sorted_dir2 = sorted(files_dir2)
    master_file = sorted_dir1[0]

    # Build duplicates list: other dir1 files + all dir2 files
    duplicates = sorted_dir1[1:] + sorted_dir2

    return master_file, duplicates, file_hash
```

### Anti-Patterns to Avoid

- **Keeping CompareFormatter "just in case":** Delete entirely - dead code causes confusion
- **Parallel if/else for compare vs other actions everywhere:** Use action type checks sparingly, prefer unified paths
- **Changing JSON schema:** JSON output must remain identical for backward compatibility
- **Breaking --execute validation:** `--execute` with compare MUST error (compare doesn't modify files)

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Test compatibility | Custom test adapters | Incremental refactoring | Existing tests should pass without modification |
| Argument validation | Complex conditionals | argparse error() | Already used for --execute validation |
| Output format | New compare action output | Existing ActionFormatter output | ActionFormatter already produces correct format |

**Key insight:** The ActionFormatter/TextActionFormatter already produces the output format we want for compare mode (hierarchical [MASTER]/[DUPLICATE]). The task is making compare mode use this existing code, not writing new formatting code.

## Common Pitfalls

### Pitfall 1: Test Breakage During Transition

**What goes wrong:** Tests fail because they check for exact output that changes mid-refactor
**Why it happens:** Compare mode output structure may differ slightly from action mode
**How to avoid:**
1. Phase 9 already unified the group output format - leverage this
2. Verify current compare mode output matches action mode structure before starting
3. Run full test suite after each incremental change
4. If tests fail, investigate whether the change is correct (tests may need updating) or incorrect (revert)
**Warning signs:** Multiple test failures in test_output_unification.py or test_determinism.py

### Pitfall 2: JSON Schema Incompatibility

**What goes wrong:** JSON output structure changes, breaking downstream scripts
**Why it happens:** ActionFormatter JSON structure differs from CompareFormatter JSON structure
**How to avoid:**
1. Document current JsonCompareFormatter output schema
2. Ensure JsonActionFormatter can produce identical output for compare action
3. May need to special-case JSON output for compare action to maintain schema
4. Test with exact JSON comparison, not just structural checks
**Warning signs:** test_json_output.py failures, especially test_json_has_required_fields

### Pitfall 3: Breaking --execute Validation

**What goes wrong:** `--execute` works with compare action (should error)
**Why it happens:** Validation logic in main() doesn't account for new compare action
**How to avoid:**
1. Add explicit validation: if args.execute and args.action == "compare": parser.error()
2. Add this validation BEFORE any other processing
3. Write a test that verifies this error case
**Warning signs:** Compare mode accidentally allowing --execute flag

### Pitfall 4: Statistics Calculation Divergence

**What goes wrong:** Statistics show different values for compare vs action
**Why it happens:** Compare mode doesn't compute space_savings (shows 0), action mode does
**How to avoid:**
1. For compare action, continue showing 0 space_savings with "(run with --action to calculate)"
2. This is correct behavior - compare mode cannot know which files would be deleted
3. Don't try to "compute" space savings for compare - it's philosophically wrong
**Warning signs:** Space calculations appearing in compare mode

### Pitfall 5: Infinite Recursion Risk

**What goes wrong:** Default action="compare" causes unexpected recursion or loops
**Why it happens:** Code assumes action is None when no --action specified
**How to avoid:**
1. Search for `args.action` and `if action` checks - update all
2. Distinguish between "no action specified" and "compare action"
3. Since compare IS the default, there's no "no action" case anymore
**Warning signs:** TypeError or infinite loops when running without --action

## Code Examples

Verified patterns from existing codebase:

### Current Compare Mode Entry Point (to be removed)

```python
# Source: file_matcher.py lines 2601-2674
else:
    # Original output format (no master mode / compare mode)
    if args.json:
        compare_formatter = JsonCompareFormatter(
            verbose=args.verbose,
            dir1_name=args.dir1,
            dir2_name=args.dir2
        )
    else:
        compare_formatter = TextCompareFormatter(
            verbose=args.verbose,
            dir1_name=args.dir1,
            dir2_name=args.dir2,
            color_config=color_config
        )
    # ... 70+ more lines of compare-specific logic
```

### Current Action Mode Validation (to be extended)

```python
# Source: file_matcher.py lines 2256-2266
# Validate --execute requires --action
if args.execute and not args.action:
    parser.error("--execute requires --action")

# Validate --log requires --execute
if args.log and not args.execute:
    parser.error("--log requires --execute")

# Validate --fallback-symlink only applies to hardlink action
if args.fallback_symlink and args.action != 'hardlink':
    parser.error("--fallback-symlink only applies to --action hardlink")
```

### Current Branching Condition (to be modified)

```python
# Source: file_matcher.py lines 2311-2312
if master_path:
    # ~300 lines of action mode code
```

**Change to:**
```python
# Always set master_path for action mode (including compare)
master_path = Path(args.dir1).resolve()  # Always set now

# Action mode code handles all cases including compare
```

### Proposed Unified Validation

```python
# Add compare to action choices
parser.add_argument('--action', '-a',
    choices=['compare', 'hardlink', 'symlink', 'delete'],
    default='compare',
    help='Action to take: compare (default, no changes), hardlink, symlink, or delete')

# Later in validation:
# Validate --execute not allowed with compare (compare doesn't modify)
if args.execute and args.action == 'compare':
    parser.error("compare action doesn't modify files - remove --execute flag")

# Validate --yes silently ignored with compare (no confirmation needed)
# (No error needed - just don't prompt)
```

### Proposed Header Logic

```python
def format_unified_header(self, action: str, dir1: str, dir2: str) -> None:
    """Format unified header - handles both compare and action modes."""
    if action == "compare":
        # Compare mode: show directories, no state banner
        header = f"Compare mode: {dir1} vs {dir2}"
    else:
        # Action mode: show state (PREVIEW/EXECUTING)
        state = "PREVIEW" if self.preview_mode else "EXECUTING"
        header = f"Action mode ({state}): {action} {dir1} vs {dir2}"
    print(cyan(header, self.cc))
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Separate CompareFormatter/ActionFormatter | Unified ActionFormatter | This phase | Simpler codebase, single code path |
| `if master_path:` branching | Always action mode | This phase | Removes ~75 lines of duplicate code |
| `--action` required for master | `--action compare` as default | This phase | Backward compatible, clearer semantics |

**Deprecated/outdated:**
- **CompareFormatter ABC**: Replaced by ActionFormatter handling compare
- **TextCompareFormatter**: Replaced by TextActionFormatter with compare support
- **JsonCompareFormatter**: Replaced by JsonActionFormatter with compare support
- **`if master_path:` top-level branch**: Removed - always in action mode now

## Open Questions

Things that couldn't be fully resolved:

1. **JSON Schema Compatibility**
   - What we know: JsonCompareFormatter has fields: timestamp, directories, hashAlgorithm, matches, summary
   - What we know: JsonActionFormatter has fields: timestamp, mode, action, directories, warnings, duplicateGroups, statistics
   - What's unclear: Should compare action JSON use CompareFormatter schema or ActionFormatter schema?
   - Recommendation: Use CompareFormatter schema for compare action to maintain backward compatibility
   - This may require special-casing in JsonActionFormatter or keeping JsonCompareFormatter output logic

2. **Exact Test Compatibility**
   - What we know: Success criteria states "All existing tests pass without modification"
   - What's unclear: Are there any tests that check for specific error messages or exact output?
   - Recommendation: Run full test suite early and often; be prepared to adjust approach if tests reveal issues
   - May need to update test assertions if output format evolved during Phases 7-9

3. **Internal Action Naming**
   - What we know: CLI uses "compare", header shows "Action: none"
   - What's unclear: Should internal variables use "compare" or None for compare action?
   - Recommendation: Use "compare" consistently internally, translate to "none" only for display
   - This is cleaner than using None which could indicate "not set"

## Implementation Notes

### Files to Modify

1. **file_matcher.py** - Main implementation
   - argparse: Add "compare" to choices, set as default
   - Validation: Add --execute with compare error
   - ActionFormatter: Handle compare case (no banner, "none" action display)
   - main(): Remove compare-specific else branch, make action branch universal
   - Delete: CompareFormatter ABC (~108 lines)
   - Delete: TextCompareFormatter (~154 lines)
   - Delete: JsonCompareFormatter (~166 lines)

2. **tests/test_json_output.py** - JSON tests
   - May need updates if JSON schema changes
   - Verify backward compatibility

3. **tests/test_output_unification.py** - Output format tests
   - Tests check for "Compare mode:" header - should still pass
   - Tests check statistics footer - should still pass

4. **tests/test_master_directory.py** - Master directory tests
   - Already checks for [MASTER]/[DUPLICATE] in compare mode (line 69-71)
   - Should continue to pass

### Scope

**In scope:**
- Adding "compare" as default action
- Validation for --execute with compare
- Making compare flow through ActionFormatter
- Deleting CompareFormatter hierarchy
- Maintaining backward compatibility

**NOT in scope:**
- Changing user-visible output format (already unified in Phase 9)
- Changing JSON schema (must remain compatible)
- Adding new features
- Changing test assertions (success criteria: pass without modification)

### Estimated Changes

**Deletions:**
- CompareFormatter ABC: ~108 lines
- TextCompareFormatter: ~154 lines
- JsonCompareFormatter: ~166 lines
- Compare mode branch in main(): ~74 lines
- **Total deletions: ~502 lines**

**Additions:**
- Action choices update: ~5 lines
- Validation for --execute with compare: ~3 lines
- Compare-specific handling in ActionFormatter: ~20 lines
- JSON output special-casing for compare: ~30 lines
- **Total additions: ~58 lines**

**Net impact: ~444 lines removed** (significant simplification)

### Refactoring Sequence

1. **Plan 1: CLI and Validation**
   - Add "compare" to action choices
   - Set default to "compare"
   - Add --execute with compare validation
   - Add --yes with compare handling (silent ignore)
   - Tests: Verify --action compare works, --execute compare errors

2. **Plan 2: ActionFormatter Compare Support**
   - Modify TextActionFormatter for compare case (no banner, header format)
   - Modify JsonActionFormatter for compare case (maintain JSON schema)
   - Update format_unified_header, format_banner, format_statistics
   - Tests: Verify output unchanged

3. **Plan 3: Main() Unification**
   - Remove `if master_path:` condition - always use action path
   - Remove compare-specific else branch
   - Verify all compare mode tests pass
   - Tests: Full regression test

4. **Plan 4: Cleanup**
   - Delete CompareFormatter ABC
   - Delete TextCompareFormatter class
   - Delete JsonCompareFormatter class
   - Final verification
   - Tests: Ensure no references remain

## Sources

### Primary (HIGH confidence)
- Existing codebase: `file_matcher.py` (comprehensive review of lines 1-2680)
- Existing tests: `tests/test_json_output.py`, `tests/test_output_unification.py`
- Phase 9 CONTEXT.md: Unified group output already implemented
- Phase 10 CONTEXT.md: Implementation decisions locked

### Secondary (MEDIUM confidence)
- Python refactoring best practices (incremental migration, test-driven)
- argparse documentation for choices with defaults

### Tertiary (LOW confidence)
- None - this is purely internal refactoring with no external dependencies

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All existing code, no new dependencies
- Architecture: HIGH - Clear pattern (action generalizes compare)
- Pitfalls: HIGH - Well-understood refactoring risks

**Research date:** 2026-01-23
**Valid until:** 2026-02-23 (30 days - stable domain, internal refactoring)
