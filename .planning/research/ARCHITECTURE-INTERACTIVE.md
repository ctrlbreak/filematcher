# Architecture: Interactive Confirmation Integration

**Domain:** CLI interactive confirmation for file deduplication
**Researched:** 2026-01-28
**Confidence:** HIGH

## Executive Summary

This research analyzes how interactive per-group confirmation should integrate with File Matcher's existing output architecture. The current architecture uses a single end-of-preview confirmation prompt, but the desired behavior is to prompt after displaying each duplicate group.

**Key Finding:** Interactive confirmation requires fundamental changes to the output flow, shifting from "display all, then act" to "display group → prompt → act on confirmed groups". This must preserve consistency with preview mode while adding interactivity only when needed.

**Critical Constraint:** The formatter abstraction (`ActionFormatter`) is designed for batch output, not interactive prompts. Integration requires either extending the formatter protocol or bypassing it for prompts.

## Current Architecture Analysis

### Output Flow in Execute Mode (Current)

```
cli.py:main() [execute_mode=True]
  ├─> print_preview_output()              # Show all groups
  │   ├─> formatter.format_banner()       # "=== PREVIEW MODE ==="
  │   ├─> formatter.format_duplicate_group() (for each group)
  │   └─> formatter.format_statistics()
  ├─> formatter.format_execute_prompt_separator()  # Blank line
  ├─> print("=== EXECUTE MODE! ===")
  ├─> confirm_execution()                 # Single Y/N prompt
  │   └─> input("Proceed? [y/N] ")
  └─> execute_with_logging()              # Process all groups
      └─> execute_all_actions()
          └─> execute_action() (for each duplicate)
```

**Key Observation:** Preview output (`print_preview_output()`) and action execution (`execute_with_logging()`) are completely decoupled. All groups are displayed, then all groups are processed.

### Formatter Architecture

```python
# formatters.py

class ActionFormatter(ABC):
    """Strategy pattern for output formatting"""
    def format_duplicate_group(self, master_file, duplicates, ...) -> None
    def format_statistics(...) -> None
    def format_execution_summary(...) -> None
    # No prompt-related methods

class TextActionFormatter(ActionFormatter):
    """Human-readable text with color support"""
    def format_duplicate_group(self, ...):
        # Outputs MASTER / WILL DELETE lines
        # No return value, immediate print()

class JsonActionFormatter(ActionFormatter):
    """Machine-readable JSON (accumulator pattern)"""
    def format_duplicate_group(self, ...):
        # Accumulates to internal _data dict
        # No output until finalize()
```

**Integration Challenge:** `TextActionFormatter.format_duplicate_group()` immediately prints output. There's no natural place to insert a prompt because the method returns `None`, not structured data the caller could prompt about.

## Proposed Architecture Options

### Option 1: Per-Group Execution Loop (Recommended)

**Concept:** Instead of "display all → execute all", shift to "for each group: display → prompt → execute".

```python
# Pseudocode for cli.py

def execute_with_interactive_confirmation(
    master_results: list[DuplicateGroup],
    action: Action,
    formatter: ActionFormatter,
    ...
):
    """Execute with per-group interactive confirmation."""
    confirmed_groups = []

    formatter.format_banner()  # "=== INTERACTIVE MODE ==="

    for i, group in enumerate(master_results):
        # Display this group
        formatter.format_duplicate_group(
            group.master_file, group.duplicates, ...
        )

        # Prompt for confirmation
        response = prompt_for_group(group, action)

        if response == 'y':
            confirmed_groups.append(group)
            print("✓ Confirmed")
        elif response == 'n':
            print("✗ Skipped")
        elif response == 'a':  # Accept all remaining
            confirmed_groups.extend(master_results[i:])
            break
        elif response == 'q':  # Quit
            break

        print()  # Separator

    # Execute confirmed groups
    if confirmed_groups:
        execute_with_logging(confirmed_groups, action, ...)
```

**Integration Points:**
- **cli.py:** New function `execute_with_interactive_confirmation()` parallel to current `execute_with_logging()`
- **formatters.py:** Add new method `format_group_prompt(group, action) -> str` to generate prompt text
- **actions.py:** No changes needed (already processes subset of groups)

**Advantages:**
- Preserves formatter abstraction (formatters still just format, don't prompt)
- Prompt logic stays in cli.py (appropriate layer)
- Supports "accept all" / "quit" options naturally
- Can show running count: "[3/10 confirmed] Group 4:"

**Disadvantages:**
- Requires new top-level function in cli.py
- Can't use existing `print_preview_output()` helper

### Option 2: Prompt Method in Formatter (Not Recommended)

**Concept:** Add `prompt_user(question) -> str` method to `ActionFormatter` ABC.

```python
class ActionFormatter(ABC):
    @abstractmethod
    def prompt_user(self, question: str) -> str:
        """Prompt for user input. Returns response."""
        ...

class TextActionFormatter(ActionFormatter):
    def prompt_user(self, question: str) -> str:
        if not sys.stdin.isatty():
            raise RuntimeError("Non-interactive mode")
        return input(question).strip().lower()

class JsonActionFormatter(ActionFormatter):
    def prompt_user(self, question: str) -> str:
        raise NotImplementedError("JSON mode is non-interactive")
```

**Why Not Recommended:**
- Violates single responsibility principle (formatters should format, not interact)
- Makes JsonActionFormatter implementation awkward
- Prompting is control flow, not presentation
- Obscures where interactivity happens in codebase

### Option 3: Callback-Based Execution (Over-Engineering)

**Concept:** `execute_all_actions()` accepts optional callback `confirm_fn(group) -> bool`.

**Why Not Recommended:**
- Actions module shouldn't know about confirmation (separation of concerns)
- Makes action execution logic more complex
- Testing becomes harder (need to mock callbacks)

## Recommended Integration Architecture

### Component Boundaries

```
┌─────────────────────────────────────────────────────────────┐
│ cli.py: Orchestration & Control Flow                        │
├─────────────────────────────────────────────────────────────┤
│ - Parses flags (--interactive)                              │
│ - Chooses execution path:                                   │
│   • Preview: show all, no execution                         │
│   • Batch: show all → single prompt → execute all           │
│   • Interactive: per-group display/prompt/execute           │
│ - Calls formatters for output                               │
│ - Calls input() for prompts (not delegated)                 │
│ - Calls actions for execution                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ formatters.py: Presentation                                  │
├─────────────────────────────────────────────────────────────┤
│ - format_duplicate_group(): Display group details           │
│ - format_group_prompt(): Generate prompt text [NEW]         │
│ - format_confirmation_status(): Show "✓ Confirmed" [NEW]    │
│ - NO input() calls (remain pure formatters)                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ actions.py: Execution                                        │
├─────────────────────────────────────────────────────────────┤
│ - execute_all_actions(): Process list of groups             │
│ - Already supports partial group lists                      │
│ - No awareness of how groups were confirmed                 │
└─────────────────────────────────────────────────────────────┘
```

### New Methods to Add

#### formatters.py Extensions

```python
class ActionFormatter(ABC):
    @abstractmethod
    def format_group_prompt(
        self,
        group_index: int,
        total_groups: int,
        duplicate_count: int,
        action: Action
    ) -> str:
        """Generate prompt text for a group.

        Example: "Process 3 duplicates with hardlink? [y/n/a/q] "
        """
        ...

    @abstractmethod
    def format_confirmation_status(self, confirmed: bool) -> None:
        """Display confirmation result (✓ Confirmed / ✗ Skipped)."""
        ...

    @abstractmethod
    def format_interactive_header(self, action: Action, total_groups: int) -> None:
        """Display header for interactive mode."""
        ...
```

**Text Implementation:**
```python
def format_group_prompt(self, group_index, total_groups, duplicate_count, action):
    action_verb = {"hardlink": "hardlink", "symlink": "symlink", "delete": "DELETE"}
    verb = action_verb.get(action, action)
    prompt = f"[{group_index}/{total_groups}] Process {duplicate_count} duplicates with {verb}? "
    prompt += "[y=yes, n=no, a=all, q=quit] "
    return prompt

def format_confirmation_status(self, confirmed):
    if confirmed:
        print(green("  ✓ Confirmed", self.cc))
    else:
        print(dim("  ✗ Skipped", self.cc))

def format_interactive_header(self, action, total_groups):
    print(cyan(f"=== INTERACTIVE MODE: {action.upper()} ===", self.cc))
    print(cyan(f"You will be prompted for each of {total_groups} duplicate groups.", self.cc))
    print()
```

**JSON Implementation:**
```python
def format_group_prompt(self, group_index, total_groups, duplicate_count, action):
    # JSON mode is non-interactive, return empty string
    return ""

def format_confirmation_status(self, confirmed):
    # JSON mode doesn't show interactive status
    pass

def format_interactive_header(self, action, total_groups):
    # JSON mode doesn't show interactive header
    pass
```

#### cli.py New Function

```python
def execute_with_interactive_confirmation(
    master_results: list[DuplicateGroup],
    action: Action,
    formatter: ActionFormatter,
    verbose: bool,
    color_config: ColorConfig,
    cross_fs_files: set[str],
    target_dir: str | None,
    dir2_base: str,
    # ... other args for execute_with_logging
) -> int:
    """Execute actions with per-group confirmation prompts.

    Returns exit code.
    """
    if not sys.stdin.isatty():
        print("Error: Interactive mode requires a TTY. Use --yes for non-interactive.", file=sys.stderr)
        return 1

    formatter.format_interactive_header(action, len(master_results))

    confirmed_groups: list[DuplicateGroup] = []
    auto_confirm_remaining = False

    for i, group in enumerate(master_results, start=1):
        # Display group
        file_sizes = build_file_sizes([group.master_file] + group.duplicates) if verbose else None
        cross_fs_to_show = cross_fs_files if action == Action.HARDLINK else None

        formatter.format_duplicate_group(
            group.master_file, group.duplicates,
            action=action,
            file_hash=group.file_hash,
            file_sizes=file_sizes,
            cross_fs_files=cross_fs_to_show,
            group_index=i,
            total_groups=len(master_results),
            target_dir=target_dir,
            dir2_base=dir2_base
        )

        # Prompt (unless auto-confirming)
        if auto_confirm_remaining:
            confirmed_groups.append(group)
            formatter.format_confirmation_status(confirmed=True)
        else:
            prompt = formatter.format_group_prompt(i, len(master_results), len(group.duplicates), action)
            response = input(prompt).strip().lower()

            if response in ('y', 'yes'):
                confirmed_groups.append(group)
                formatter.format_confirmation_status(confirmed=True)
            elif response in ('n', 'no'):
                formatter.format_confirmation_status(confirmed=False)
            elif response in ('a', 'all'):
                confirmed_groups.extend(master_results[i-1:])  # Include current + remaining
                auto_confirm_remaining = True
                formatter.format_confirmation_status(confirmed=True)
            elif response in ('q', 'quit'):
                print("Aborted by user.")
                break
            else:
                print(f"Invalid response: {response}. Skipping group.")
                formatter.format_confirmation_status(confirmed=False)

        print()  # Separator between groups

    # Execute confirmed groups
    if confirmed_groups:
        print()
        print(f"Executing {len(confirmed_groups)} confirmed groups...")
        print()

        success, failure, skipped, space_saved, failed_list, log_path = execute_with_logging(
            dir1=...,  # Pass through all needed args
            dir2=...,
            action=action,
            master_results=confirmed_groups,  # Only confirmed groups
            matches=...,
            base_flags=...,
            # ... rest of args
        )

        # Show summary
        exec_formatter = TextActionFormatter(verbose=verbose, preview_mode=False, action=action, color_config=color_config)
        exec_formatter.format_execution_summary(success, failure, skipped, space_saved, str(log_path), failed_list)

        return determine_exit_code(success, failure)
    else:
        print("No groups confirmed. No changes made.")
        return 0
```

### CLI Flag Integration

**New flag:**
```python
parser.add_argument('--interactive', '-i', action='store_true',
                    help='Prompt for confirmation for each duplicate group (requires TTY)')
```

**Validation:**
```python
if args.interactive and not args.execute:
    parser.error("--interactive requires --execute")
if args.interactive and args.yes:
    parser.error("--interactive and --yes are mutually exclusive")
if args.interactive and args.json:
    parser.error("--interactive requires text output (not compatible with --json)")
```

**Routing logic:**
```python
execute_mode = args.action != Action.COMPARE and args.execute

if execute_mode:
    if args.interactive:
        return execute_with_interactive_confirmation(...)
    elif args.json:
        # Existing JSON execution path
        ...
    else:
        # Existing batch execution path (show all → prompt → execute all)
        ...
```

## Consistency with Preview Mode

**Requirement:** Interactive mode should display groups the same way preview mode does.

**Solution:** Both modes use the same `formatter.format_duplicate_group()` method.

```python
# Preview mode (current):
for group in master_results:
    formatter.format_duplicate_group(group.master_file, group.duplicates, ...)
formatter.format_statistics(...)

# Interactive mode (new):
for group in master_results:
    formatter.format_duplicate_group(group.master_file, group.duplicates, ...)  # Same call
    prompt = formatter.format_group_prompt(...)  # New: prompt after each group
    response = input(prompt)
    # Handle response
```

**Consistency maintained:**
- Same formatter instance
- Same `format_duplicate_group()` parameters
- Same color config, verbose settings
- Same MASTER / WILL DELETE labels

**Difference:** Prompts appear immediately after each group, not at the end.

## Interaction Patterns

### Prompt Options

```
[y] yes      - Confirm this group, continue
[n] no       - Skip this group, continue
[a] all      - Confirm this group + all remaining (batch mode)
[q] quit     - Abort, execute nothing
```

**Why these options:**
- `y/n` are standard
- `a` (all) provides escape hatch: "I've reviewed enough, just do the rest"
- `q` (quit) provides clean exit without executing anything

**Alternative considered:** `[s] skip remaining` - decided against because `a` + `q` covers the use cases.

### Sample Output Flow

```
=== INTERACTIVE MODE: HARDLINK ===
You will be prompted for each of 3 duplicate groups.

[1/3] MASTER: /dir1/photo.jpg
        WILL HARDLINK: /dir2/photo.jpg
        WILL HARDLINK: /dir2/backup/photo.jpg
[1/3] Process 2 duplicates with hardlink? [y=yes, n=no, a=all, q=quit] y
  ✓ Confirmed

[2/3] MASTER: /dir1/document.pdf
        WILL HARDLINK: /dir2/document.pdf
[2/3] Process 1 duplicate with hardlink? [y=yes, n=no, a=all, q=quit] n
  ✗ Skipped

[3/3] MASTER: /dir1/video.mp4
        WILL HARDLINK: /dir2/video.mp4
[3/3] Process 1 duplicate with hardlink? [y=yes, n=no, a=all, q=quit] y
  ✓ Confirmed

Executing 2 confirmed groups...

=== EXECUTE MODE: hardlink ===

Execution complete:
  Successful: 3
  Failed: 0
  Skipped: 0
  Space saved: 150.5 MB
  Log file: filematcher_20260128_103045.log
```

## Error Handling

### Non-TTY Environment

```python
if args.interactive and not sys.stdin.isatty():
    print("Error: --interactive requires a terminal (stdin is not a TTY).", file=sys.stderr)
    print("Use --yes for non-interactive batch execution.", file=sys.stderr)
    return 1
```

**Rationale:** Interactive prompts require TTY. Don't silently fail or fall back to batch mode.

### EOF During Prompts

```python
try:
    response = input(prompt)
except EOFError:
    print("\nInterrupted by EOF. Aborting.", file=sys.stderr)
    return 1
```

**Rationale:** Handle Ctrl+D gracefully.

### Invalid Response

```python
response = input(prompt).strip().lower()
if response not in ('y', 'yes', 'n', 'no', 'a', 'all', 'q', 'quit'):
    print(f"Invalid response: '{response}'. Skipping group.")
    formatter.format_confirmation_status(confirmed=False)
```

**Rationale:** Don't hang on invalid input. Skip and continue (safe default).

## Testing Strategy

### Unit Tests

**formatters.py:**
```python
def test_format_group_prompt_text():
    formatter = TextActionFormatter(...)
    prompt = formatter.format_group_prompt(2, 5, 3, Action.HARDLINK)
    assert "[2/5]" in prompt
    assert "3 duplicates" in prompt
    assert "hardlink" in prompt
    assert "[y=yes" in prompt

def test_format_confirmation_status_confirmed():
    formatter = TextActionFormatter(...)
    # Capture stdout
    formatter.format_confirmation_status(confirmed=True)
    # Assert "✓ Confirmed" appears
```

**cli.py:**
```python
def test_interactive_validation_requires_execute():
    # Mock argparse
    with pytest.raises(SystemExit):
        # --interactive without --execute should error
        ...

def test_interactive_conflicts_with_yes():
    # --interactive --yes should error
    ...

def test_interactive_conflicts_with_json():
    # --interactive --json should error
    ...
```

### Integration Tests

**Simulated input:**
```python
def test_interactive_confirmation_all_yes(tmp_path, monkeypatch):
    # Create test files
    # Mock stdin to provide "y\ny\ny\n"
    inputs = iter(["y", "y", "y"])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))

    # Run with --interactive --execute
    result = main([str(dir1), str(dir2), '--action', 'hardlink', '--execute', '--interactive'])

    # Assert all groups processed
    assert result == 0

def test_interactive_confirmation_mixed(tmp_path, monkeypatch):
    # Mock stdin: y, n, y
    inputs = iter(["y", "n", "y"])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))

    result = main([...])

    # Assert only confirmed groups processed (check audit log)
    assert "2 successful" in captured_output

def test_interactive_accept_all(tmp_path, monkeypatch):
    # Mock stdin: n, a (accept all after skipping first)
    inputs = iter(["n", "a"])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))

    result = main([...])

    # Assert first skipped, rest processed
    ...

def test_interactive_quit_early(tmp_path, monkeypatch):
    # Mock stdin: y, q
    inputs = iter(["y", "q"])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))

    result = main([...])

    # Assert only first group processed
    ...
```

## Performance Considerations

### Impact on Large Datasets

**Scenario:** 1000 duplicate groups.

**Batch mode (current):**
1. Display all 1000 groups (fast, pure output)
2. Single prompt
3. Execute all 1000 groups

**Interactive mode (new):**
1. Display group 1
2. Prompt (waits for user)
3. Display group 2
4. Prompt (waits for user)
... (1000 prompts)

**Mitigation:**
- Provide "accept all" option early (user can switch to batch mode mid-way)
- Consider showing group count in header: "You will be prompted for each of 1000 groups" (may discourage interactive mode for large sets)
- Document: Interactive mode is intended for small to medium datasets (~10-100 groups)

**Alternative for large datasets:** `--interactive-sample=N` - prompt for first N groups, then batch rest. (Future enhancement, not MVP)

## Comparison with Similar Tools

### Git Interactive Rebase (`git rebase -i`)

**Pattern:**
1. Show all commits in editor
2. User edits action list
3. Git processes edited list

**Difference:** File Matcher's interactive mode prompts during display, not after editing a batch file.

**Why different:** Git's model requires understanding all commits before deciding. File deduplication decisions are independent per group.

### APT/DNF Package Installation

**Pattern:**
```
The following packages will be installed:
  package1 package2 package3
Do you want to continue? [Y/n]
```

**Single prompt for batch.** File Matcher's batch mode matches this.

**Interactive mode analogy:**
```
Install package1? [y/n] y
Install package2? [y/n] n
Install package3? [y/n] y
```

This exists in some package managers as `--interactive` or step-by-step mode.

### fdupes --delete

**Pattern:**
```
Set 1 of 3:
  [1] /path/to/file1.txt
  [2] /path/to/file2.txt
  [3] /path/to/file3.txt
Preserve files [1 - 3, all]: 1
```

**Difference:** fdupes asks "which to keep" per group. File Matcher has implicit master, asks "proceed with this group?"

**Similarity:** Both prompt per group for interactive control.

## Risks and Mitigation

### Risk: User Confusion Between Modes

**Problem:** Three modes (preview, batch execute, interactive execute) may confuse users.

**Mitigation:**
- Clear banner: "=== INTERACTIVE MODE ===" vs "=== EXECUTE MODE! ==="
- Documentation clearly explains: preview (no execution), batch (show all, confirm once), interactive (confirm each)
- Error messages guide: "For per-group confirmation, use --interactive"

### Risk: Inconsistent Output Between Modes

**Problem:** Interactive mode might format groups differently than preview.

**Mitigation:**
- Use same `formatter.format_duplicate_group()` method in all modes
- Test suite verifies identical group formatting
- Unit test: capture formatter output in both paths, assert equality

### Risk: JSON Mode Interaction

**Problem:** User tries `--json --interactive`.

**Mitigation:**
- Validation error at CLI parsing: "JSON mode is non-interactive, remove --json or --interactive"
- Clear error message explains incompatibility

### Risk: Prompt Interpretation Errors

**Problem:** User types "y " (with space) or "Y" (uppercase), not recognized.

**Mitigation:**
- Use `.strip().lower()` on input
- Accept multiple forms: `y`, `yes`, `Y`, `Yes`, ` y ` all work

## Phase Structure Recommendations

Based on this architecture analysis, recommended implementation phases:

**Phase 1: Formatter Extensions (1-2 hours)**
- Add `format_group_prompt()` to `ActionFormatter` ABC
- Add `format_confirmation_status()` to `ActionFormatter` ABC
- Add `format_interactive_header()` to `ActionFormatter` ABC
- Implement in `TextActionFormatter` (with color support)
- Implement no-ops in `JsonActionFormatter`
- Unit tests for new methods

**Phase 2: Interactive Execution Function (2-3 hours)**
- Add `execute_with_interactive_confirmation()` to cli.py
- Implement per-group loop: display → prompt → track confirmation
- Handle y/n/a/q responses
- Error handling (non-TTY, EOF, invalid input)
- Pass confirmed groups to `execute_with_logging()`

**Phase 3: CLI Integration (1 hour)**
- Add `--interactive` flag with validation
- Route to new function when flag present
- Update help text
- Integration tests with mocked input

**Phase 4: Documentation & Polish (1 hour)**
- Update README with interactive mode example
- Add to help output
- Error message refinement

**Total estimate:** 5-7 hours for full interactive confirmation feature.

## Open Questions for Implementation

1. **Should "all" option show remaining count?**
   - Current: `[a] all` - Confirm this group + all remaining
   - Alternative: `[a] all (N remaining)`
   - Recommendation: Yes, show count for clarity

2. **Should interactive mode show running summary?**
   - Example: `[3 confirmed, 1 skipped so far]`
   - Recommendation: Defer to post-MVP (adds complexity)

3. **Should there be a "preview next" option?**
   - Example: `[p] preview next before deciding`
   - Recommendation: No, out of scope (adds complexity)

4. **How to handle Ctrl+C during prompts?**
   - Current: Python's default KeyboardInterrupt
   - Recommendation: Catch and treat like quit (clean up, exit gracefully)

5. **Should confirmed groups be logged before execution?**
   - Example: "User confirmed groups: [hash1, hash2, ...]" in audit log
   - Recommendation: Yes, helps with auditing (add to log header)

## Sources

**Architecture Patterns:**
- File Matcher codebase (cli.py, formatters.py, actions.py) - analyzed 2026-01-28
- Strategy pattern from Gang of Four Design Patterns
- CLI interaction patterns from Unix philosophy

**Similar Tools:**
- [fdupes man page](https://linux.die.net/man/1/fdupes) - Interactive deletion mode
- [Git interactive rebase](https://git-scm.com/docs/git-rebase#_interactive_mode) - Interactive editing pattern
- APT package manager - Batch confirmation pattern

**Best Practices:**
- [CLI Guidelines (clig.dev)](https://clig.dev/) - Interactivity, TTY detection
- Existing File Matcher research: FEATURES.md, PITFALLS.md

## Confidence Assessment

| Area | Level | Reason |
|------|-------|--------|
| Integration points | HIGH | Direct codebase analysis of cli.py and formatters.py |
| Formatter extension approach | HIGH | Follows existing strategy pattern cleanly |
| Execution flow | HIGH | Verified against current execute_with_logging() |
| Testing strategy | MEDIUM | Based on existing test patterns, not yet validated |
| User experience | MEDIUM | Patterns from similar tools, needs user validation |

## Conclusion

Interactive confirmation requires a new execution path in cli.py that interleaves display and prompting, rather than the current "display all, then prompt once" approach. The recommended architecture extends the formatter protocol with prompt-related methods while keeping actual input handling in the CLI layer, preserving separation of concerns. This approach maintains consistency with preview mode by reusing the same `format_duplicate_group()` method, ensuring users see identical output formatting across all modes.
