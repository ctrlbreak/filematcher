# Interactive Confirmation Pitfalls

**Domain:** Adding per-file interactive confirmation to existing CLI tool
**Researched:** 2026-01-28
**Confidence:** HIGH (based on project history, research, and industry patterns)

## Executive Summary

Adding interactive confirmation to File Matcher requires avoiding pitfalls from the prior failed attempt. The key challenges are: TTY behavior complexity, output flow integration with existing preview/execute modes, prompt positioning within group displays, and maintaining consistency across --verbose, --quiet, and --json flags. This research identifies 12 critical pitfalls organized by severity.

## Critical Pitfalls

These mistakes cause rewrites, major refactors, or feature abandonment.

### Pitfall 1: TTY Carriage Return Complexity

**What goes wrong:** Attempting to overwrite prompts in-place using carriage returns (\r) creates unreliable behavior across different terminals, especially when mixed with user input.

**Why it happens:**
- Developers assume \r behavior is consistent across terminals
- Mixing stderr output (progress) with stdin input (prompts) creates timing issues
- Raw mode vs cooked mode terminal behavior differs unpredictably

**Consequences:**
- Prompts overwrite group output unpredictably
- User input appears at wrong position
- Terminal state corruption requiring reset
- Works in testing, fails in production environments

**Prevention:**
- Do NOT attempt to overwrite prompts using carriage returns
- Keep prompts static - write once, don't erase
- Separate prompt display from progress updates
- Use simpler append-only output model

**Detection:**
- Testing reveals: "prompt overwrote previous line"
- Testing reveals: "cursor position wrong after input"
- Testing reveals: "works in terminal A, breaks in terminal B"

**Prior evidence:** File Matcher reverted attempt explicitly cited "TTY carriage return behavior was complex and unreliable"

---

### Pitfall 2: Output Flow Disconnection

**What goes wrong:** Showing all groups first, then prompting separately creates cognitive disconnect - users can't easily map prompts back to files they saw earlier.

**Why it happens:**
- Existing preview mode shows all groups at once
- Attempting to reuse preview output wholesale without redesign
- Not considering how humans track context during interaction

**Consequences:**
- Users scroll back to find which file they're being asked about
- Errors because users confirm wrong file
- Frustration leads to --yes flag abuse (defeating safety purpose)

**Prevention:**
- Integrate prompts inline with group display
- Show context immediately before each prompt
- Pattern: "Group N/M: [master] -> [duplicate] - Proceed? [y/n/a/c]"
- Each decision is self-contained, no scrollback needed

**Detection:**
- User feedback: "I forgot which file I'm confirming"
- Users press 'a' (all) immediately to skip tedious process
- Design review question: "Where would cursor be during prompt?"

**Example from research:** git add -p shows each hunk immediately before prompting, not all hunks then all prompts separately.

---

### Pitfall 3: Stdin Detection Failures

**What goes wrong:** Not properly detecting non-interactive environments leads to hanging prompts or cryptic errors when input is piped.

**Why it happens:**
- Checking only sys.stdin.isatty() without fallback behavior
- Forgetting that stdin can be redirected separately from stdout/stderr
- Not handling non-TTY environments gracefully

**Consequences:**
- Tool hangs waiting for input in CI/CD pipelines
- Scripts break silently
- Users confused by "Use --yes" message in contexts where that's not helpful

**Prevention:**
```python
def can_prompt_user() -> bool:
    """Check if we can safely prompt the user for input."""
    if not sys.stdin.isatty():
        return False
    if not sys.stdout.isatty() and not sys.stderr.isatty():
        return False  # Fully non-interactive
    return True
```

**Required behavior:**
- Non-interactive + no --yes flag → fail fast with clear message
- Non-interactive + --yes flag → proceed without prompts
- Interactive → show prompts

**Detection:**
- Test: `echo "test" | filematcher dir1 dir2 --action delete --execute`
- Should fail with: "Cannot run in interactive mode when stdin is not a TTY. Use --yes to skip prompts."
- Test: `filematcher dir1 dir2 --action delete --execute --yes < /dev/null`
- Should succeed without hanging

**Research evidence:** prompt-toolkit library explicitly asserts isatty() and breaks when piped because it's designed for user interaction only.

---

### Pitfall 4: Prompt/JSON Mode Conflict

**What goes wrong:** Interactive confirmation is fundamentally incompatible with --json output, but not designing for this creates impossible scenarios.

**Why it happens:**
- Features developed in isolation without considering interactions
- Attempting to support every combination of flags
- Not clearly defining mode exclusivity

**Consequences:**
- JSON output corrupted with human-readable prompts
- Parsers break on mixed format output
- User confusion about what flags do

**Prevention:**
- Explicitly disallow: `--json` + interactive mode without `--yes`
- Validation rule: `if args.json and args.execute and not args.yes and not can_prompt_user(): error`
- CLI help text must document: "--json with --execute requires --yes flag"
- Error message: "Interactive confirmation not available with --json output. Use --yes to skip prompts."

**Detection:**
- Test: `filematcher dir1 dir2 --action delete --execute --json` (without --yes)
- Should fail validation before any processing
- Error should suggest: `filematcher dir1 dir2 --action delete --execute --json --yes`

**Example from research:** Most CLI tools either disable interactive mode with machine output, or provide explicit --no-interactive flag.

---

### Pitfall 5: Inconsistent Group Display

**What goes wrong:** Preview mode shows groups one way, execute mode shows them differently, confusing users about what they're confirming.

**Why it happens:**
- Execute logic diverged from preview logic during development
- Not reusing formatter abstractions properly
- Treating preview and execute as separate code paths

**Consequences:**
- User confirms based on preview, but execute shows different information
- Trust erosion - tool feels unpredictable
- Bugs hide in duplicated formatting logic

**Prevention:**
- Use same DuplicateGroup data structure in both modes
- Reuse TextActionFormatter for both preview and interactive execute
- Display format: Preview shows "would X", Interactive shows "will X?" (verb tense only difference)
- Single source of truth for group rendering

**Architecture requirement:**
```python
# GOOD: Same formatter, different mode
formatter = TextActionFormatter(preview_mode=False, interactive=True)
for group in groups:
    formatter.format_duplicate_group(group)  # Show context
    if should_prompt:
        decision = prompt_user(group)  # Then prompt

# BAD: Different formatters, different display logic
preview_formatter.show_group(group)  # One way
execute_prompt.show_different_format(group)  # Different way
```

**Detection:**
- Side-by-side testing: preview output vs interactive output
- If they show different information or different ordering, pitfall is present
- Regression test: ensure group N in preview is same group N in interactive

**Project context:** File Matcher already has formatter abstraction (TextActionFormatter, JsonActionFormatter) - must be leveraged, not bypassed.

---

## Moderate Pitfalls

These mistakes cause delays, technical debt, or require refactoring.

### Pitfall 6: Verbose Flag Conflicts

**What goes wrong:** --verbose flag behavior conflicts with interactive prompts, creating noisy or confusing output.

**Why it happens:**
- Verbose mode designed for non-interactive progress display
- Not reconsidering what "verbose" means during interactive execution
- Attempting to show per-file progress while also prompting per-file

**Consequences:**
- Progress messages scroll prompt off screen
- Carriage return TTY updates fight with static prompts
- Users can't follow what's happening

**Prevention:**
- Interactive mode implies verbose is OFF for progress during prompts
- Verbose can still affect WHAT information is shown in each prompt
- Separate: progress (suppressed in interactive) vs detail (enhanced in interactive)

**Behavior matrix:**
| Mode | Verbose | Progress Display | Prompt Detail |
|------|---------|------------------|---------------|
| Preview | No | Summary only | N/A |
| Preview | Yes | Per-file listing | N/A |
| Execute --yes | No | Summary only | N/A |
| Execute --yes | Yes | TTY progress bar | N/A |
| Execute interactive | No | Suppressed | Basic prompt |
| Execute interactive | Yes | Suppressed | Detailed prompt (sizes, hashes) |

**Detection:**
- Run: `filematcher dir1 dir2 --action delete --execute --verbose` (interactive)
- If carriage return progress appears, pitfall present
- Correct: prompts appear cleanly without overwriting

**Research evidence:** CLI tools with progress bars (rsync, git clone) disable them during interactive prompts to avoid conflicts.

---

### Pitfall 7: Confirmation State Management

**What goes wrong:** Losing track of user decisions across groups leads to incorrect "all" or "cancel" behavior.

**Why it happens:**
- Confirmation logic embedded in execution loop
- Global state for user choice not properly scoped
- Edge cases like "user chose 'all' then Ctrl+C" not handled

**Consequences:**
- "All" applies to wrong scope (current group vs all groups)
- Cancel doesn't actually stop all processing
- Ctrl+C leaves partial modifications without clear state

**Prevention:**
```python
class ConfirmationState:
    """Track user decisions across interactive session."""
    def __init__(self):
        self.apply_all = False
        self.cancelled = False
        self.decisions: list[tuple[str, str]] = []  # (file, decision)

    def should_skip_prompt(self) -> bool:
        return self.apply_all or self.cancelled

    def record_decision(self, file: str, decision: str):
        self.decisions.append((file, decision))
        if decision == 'a':
            self.apply_all = True
        elif decision == 'c':
            self.cancelled = True
```

**Required semantics:**
- y = yes to this file only
- n = no to this file only (skip, continue with next)
- a = yes to all remaining files
- c = cancel, stop processing (no more actions)

**Detection:**
- Test: choose 'a' on file 3 of 10
- Verify: files 4-10 processed without prompts
- Test: choose 'c' on file 5 of 10
- Verify: files 6-10 NOT processed, clean exit

**Example from research:** git add -p implements this with clear state tracking for 'a' (stage all remaining) and 'q' (quit).

---

### Pitfall 8: Prompt Response Validation

**What goes wrong:** Accepting invalid responses or not providing help leads to user errors and frustration.

**Why it happens:**
- Simple `input().lower()[0]` without validation
- Not showing available options clearly
- No help command for confused users

**Consequences:**
- User types "yes" but only "y" is recognized, nothing happens
- Typo "u" instead of "y" requires re-running entire command
- Users don't know 'a' and 'c' options exist

**Prevention:**
```python
def prompt_for_decision(context: str) -> str:
    """Prompt user with clear options and validation."""
    while True:
        print(f"{context}")
        response = input("  [y]es / [n]o / [a]ll / [c]ancel / [?]help: ").strip().lower()

        if response in ('y', 'yes'):
            return 'y'
        elif response in ('n', 'no'):
            return 'n'
        elif response in ('a', 'all'):
            return 'a'
        elif response in ('c', 'cancel', 'q', 'quit'):
            return 'c'
        elif response in ('?', 'h', 'help'):
            print_help()
            continue
        else:
            print(f"  Invalid response: '{response}'. Type ? for help.")
            continue
```

**Required features:**
- Accept both short and long forms (y/yes, n/no)
- Loop until valid response received
- Show options clearly in prompt
- Provide help command
- Handle empty input (treat as 'n' or re-prompt)

**Detection:**
- Test: type "maybe" at prompt
- Should see: "Invalid response. Type ? for help."
- Test: type "?" at prompt
- Should see: help text explaining each option

**Research evidence:** Git interactive commands provide '?' help and accept multiple response formats for user convenience.

---

### Pitfall 9: Audit Log Timing

**What goes wrong:** Audit log written before user confirmation creates false record of actions that were skipped.

**Why it happens:**
- Logging hook placed in execution function, not after confirmation
- Not distinguishing between "attempted" and "confirmed" actions
- Reusing non-interactive logging without modification

**Consequences:**
- Log shows files that were never actually processed
- Compliance issues - log doesn't reflect reality
- Can't reconstruct actual execution from log

**Prevention:**
- Log entry MUST be written AFTER user confirms (or skips)
- Log entry for skipped files should show: "skipped (user declined)"
- Log should include user decision: confirmed_by: "user_interactive" vs "auto_yes_flag"

**Log format for interactive mode:**
```
2026-01-28 10:15:23 | hardlink | /path/to/dup.txt | /path/to/master.txt | 1024 | abc123 | confirmed | user_interactive
2026-01-28 10:15:25 | hardlink | /path/to/dup2.txt | /path/to/master.txt | 1024 | abc123 | skipped | user_declined
2026-01-28 10:15:27 | hardlink | /path/to/dup3.txt | /path/to/master.txt | 1024 | abc123 | confirmed | auto_all
```

**Detection:**
- Run interactive mode, decline first file
- Check audit log immediately
- If it shows action was taken, pitfall is present
- Correct: log shows "skipped | user_declined"

**Project context:** File Matcher already has audit logging (log_operation in actions.py) - needs extension for interactive mode, not replacement.

---

### Pitfall 10: Prompt Text Ambiguity

**What goes wrong:** Unclear prompt text leads to users confirming wrong action or not understanding consequences.

**Why it happens:**
- Generic prompts: "Proceed? [y/n]"
- Not restating the action in the prompt
- Assuming user remembers context from earlier output

**Consequences:**
- User thinks they're confirming "skip" when they're confirming "delete"
- Irreversible actions (delete) performed due to misunderstanding
- User complaints: "I didn't know that would delete the file!"

**Prevention:**
- Action must be explicit in every prompt
- Irreversible actions need WARNING prefix
- Show consequence clearly

**Good prompt examples:**
```
Group 3/10: photo.jpg (2.5 MB)
  Master: /master/photos/photo.jpg
  Duplicate: /backup/old/photo.jpg
  Action: Replace duplicate with HARDLINK to master
  Proceed? [y]es / [n]o / [a]ll / [c]ancel:

Group 5/10: document.pdf (512 KB)
  Master: /master/docs/document.pdf
  Duplicate: /backup/document.pdf
  WARNING: This will PERMANENTLY DELETE the duplicate file
  Proceed? [y]es / [n]o / [a]ll / [c]ancel:
```

**Bad prompt examples:**
```
Proceed? [y/n]  # What am I proceeding with?
Delete this? [y/n]  # Delete what? Where is it?
Continue? [y/n]  # Continue what action?
```

**Detection:**
- Usability test: show prompt in isolation (no context)
- If tester can't explain what will happen, prompt is ambiguous
- If action word not present in prompt, pitfall is present

**Research evidence:** Nielsen Norman Group research shows confirmation dialogs must describe the action, not just ask "are you sure?"

---

## Minor Pitfalls

These mistakes cause annoyance but are easily fixable.

### Pitfall 11: No Progress Indicator Between Prompts

**What goes wrong:** User doesn't know how many more prompts to expect, making the process feel endless.

**Why it happens:**
- Focus on individual prompt, not overall progress
- Not counting total items before prompting starts
- Treating each prompt as isolated event

**Consequences:**
- User frustration: "How many more?"
- Users choose 'a' (all) prematurely out of impatience
- Feels worse than batch confirmation

**Prevention:**
- Always show: "Group N/M" or "File N/M"
- Calculate total before prompting starts
- Show percentage or progress bar between groups

**Format:**
```
[Group 3/15 - 20%] Replace duplicate with hardlink?
[Group 8/15 - 53%] Replace duplicate with hardlink?
```

**Detection:**
- Run interactive mode
- If user can't tell total count or position, pitfall present

**Example from research:** git add -p shows hunk numbers (Hunk 2/5) so users know progress.

---

### Pitfall 12: Quiet Flag Contradiction

**What goes wrong:** --quiet flag conflicts with interactive mode - you can't suppress output AND prompt for input.

**Why it happens:**
- Not considering flag interactions
- Treating quiet as "suppress everything"
- No explicit validation of conflicting flags

**Consequences:**
- Quiet mode shows prompts anyway (contradicts flag name)
- Or prompts are hidden, user hangs waiting for invisible prompt
- Confusion about what flags do

**Prevention:**
- Validation: --quiet + interactive mode → error or auto-enable --yes
- Better: --quiet implies --yes in execute mode
- Document: "Note: --quiet automatically enables --yes in execute mode"

**Behavior:**
```python
if args.quiet and args.execute and not args.yes:
    # Auto-enable --yes when quiet + execute
    args.yes = True
    logger.info("Auto-enabled --yes due to --quiet flag")
```

**Alternative validation:**
```python
if args.quiet and args.execute and not args.yes:
    parser.error("--quiet with --execute requires --yes flag (cannot suppress interactive prompts)")
```

**Detection:**
- Test: `filematcher dir1 dir2 --action delete --execute --quiet` (no --yes)
- Should either: auto-enable --yes OR fail with clear error
- Should NOT: show prompts (contradicts --quiet)

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation Strategy |
|-------------|----------------|---------------------|
| Prompt design | Pitfall 2 (output flow), Pitfall 10 (ambiguous text) | Prototype prompt format first, review before implementation |
| TTY integration | Pitfall 1 (carriage return), Pitfall 3 (stdin detection) | Use append-only output, comprehensive isatty checks |
| Formatter integration | Pitfall 5 (inconsistent display), Pitfall 6 (verbose conflict) | Reuse TextActionFormatter, add interactive=True parameter |
| State management | Pitfall 7 (confirmation state), Pitfall 9 (audit timing) | Create ConfirmationState class, log after decision |
| Flag validation | Pitfall 4 (JSON conflict), Pitfall 12 (quiet conflict) | Add validation phase before execution, explicit error messages |
| User input | Pitfall 8 (response validation) | Validation loop with help command |
| Progress display | Pitfall 11 (no progress indicator) | Calculate totals upfront, show N/M in each prompt |

---

## Research Confidence

| Area | Confidence | Source |
|------|------------|--------|
| TTY behavior | HIGH | Prior File Matcher failure, tty-prompt issue #137 |
| Output flow | HIGH | CLI UX patterns research, git add -p example |
| Stdin detection | HIGH | Python documentation, prompt-toolkit limitations |
| JSON interaction | HIGH | Industry practice, CLI design guidelines |
| Formatter consistency | HIGH | File Matcher codebase analysis |
| Verbose conflicts | MEDIUM | Inferred from progress display research |
| State management | HIGH | Git interactive mode, rm -i patterns |
| Response validation | HIGH | Git help system, CLI best practices |
| Audit logging | HIGH | Compliance requirements, File Matcher existing logs |
| Prompt clarity | HIGH | Nielsen Norman Group confirmation research |
| Progress indicators | MEDIUM | User experience best practices |
| Quiet flag | MEDIUM | CLI convention analysis |

---

## Implementation Recommendations

### DO:
1. Use append-only output model (no carriage return erasure)
2. Integrate prompts inline with group display
3. Check sys.stdin.isatty() with proper fallbacks
4. Validate --json + interactive as incompatible
5. Reuse existing TextActionFormatter infrastructure
6. Suppress verbose progress during interactive prompts
7. Implement ConfirmationState for decision tracking
8. Validate and loop on user input with help option
9. Log AFTER user decision, not before
10. Make action explicit in every prompt text
11. Show progress (N/M) in prompts
12. Auto-enable --yes with --quiet flag

### DON'T:
1. Don't use carriage returns to overwrite prompts
2. Don't show all groups then prompt separately
3. Don't assume stdin is always available
4. Don't allow --json without --yes in interactive mode
5. Don't create separate display logic for interactive
6. Don't show TTY progress during prompts
7. Don't use global booleans for confirmation state
8. Don't accept invalid responses silently
9. Don't log before user confirms
10. Don't use generic "Proceed?" prompts
11. Don't make users guess how many prompts remain
12. Don't show prompts in --quiet mode

---

## Prior Attempt Lessons

File Matcher previously attempted interactive confirmation and reverted it. Key lessons:

### What Failed:
- **TTY carriage return behavior**: Complex and unreliable across terminals
- **Output flow integration**: Didn't integrate well with existing preview mode
- **Prompt positioning**: Wasn't clear how prompts should fit with group display

### Root Causes:
1. Attempted to be too clever with TTY manipulation
2. Didn't redesign output flow, tried to bolt prompts onto existing system
3. Lacked clear architectural plan for preview/execute/interactive relationship

### Success Criteria for Redesign:
1. Simple, reliable output (append-only, no overwriting)
2. Unified output model across modes (same formatters)
3. Clear architectural design before implementation
4. Explicit handling of all flag interactions
5. Comprehensive testing across terminal types

---

## Validation Checklist

Before considering interactive confirmation complete:

- [ ] Works in: Terminal.app, iTerm2, VSCode terminal, SSH session
- [ ] Test: `filematcher --execute` prompts correctly
- [ ] Test: `filematcher --execute --yes` skips prompts
- [ ] Test: `echo | filematcher --execute` fails with clear error
- [ ] Test: `filematcher --execute --json` fails validation
- [ ] Test: `filematcher --execute --quiet` auto-enables --yes
- [ ] Test: choose 'y' on one file, works correctly
- [ ] Test: choose 'n' on one file, skips correctly
- [ ] Test: choose 'a' on file N, applies to all remaining
- [ ] Test: choose 'c' on file N, stops processing
- [ ] Test: type "invalid" at prompt, shows error and re-prompts
- [ ] Test: type "?" at prompt, shows help
- [ ] Verify: audit log shows correct user decisions
- [ ] Verify: preview and interactive show same group format
- [ ] Verify: prompt shows action clearly (hardlink/symlink/delete)
- [ ] Verify: prompts show progress (N/M)
- [ ] Verify: no carriage return overwriting occurs
- [ ] Verify: Ctrl+C exits cleanly

---

## Sources

### CLI Design Patterns:
- [Command Line Interface Guidelines](https://clig.dev/)
- [UX patterns for CLI tools](https://www.lucasfcosta.com/blog/ux-patterns-cli-tools)
- [CLI UX best practices - Evil Martians](https://evilmartians.com/chronicles/cli-ux-best-practices-3-patterns-for-improving-progress-displays)
- [10 design principles for delightful CLIs - Atlassian](https://www.atlassian.com/blog/it-teams/10-design-principles-for-delightful-clis)

### Interactive Confirmation Examples:
- [Git Interactive Staging](https://git-scm.com/book/en/v2/Git-Tools-Interactive-Staging)
- [git add --patch and --interactive](https://nuclearsquid.com/writings/git-add/)
- [Enable Confirmation Alert When Removing Files - Baeldung](https://www.baeldung.com/linux/confirmation-alert-when-removing-files-directories)

### Confirmation UX Research:
- [Confirmation Dialogs Can Prevent User Errors - Nielsen Norman Group](https://www.nngroup.com/articles/confirmation-dialog/)
- [Double-check user actions - LogRocket](https://blog.logrocket.com/ux-design/double-check-user-actions-confirmation-dialog/)

### TTY and Terminal Behavior:
- [Carriage return is missing on asynchronous output - tty-prompt issue #137](https://github.com/piotrmurach/tty-prompt/issues/137)
- [Broken when piped to - prompt-toolkit issue #502](https://github.com/prompt-toolkit/python-prompt-toolkit/issues/502)
- [How Does sys.stdin.isatty() Help in Detecting Interactive Mode?](https://www.mindstick.com/forum/161329/how-does-sys-stdin-isatty-help-in-detecting-interactive-mode)

### Python CLI Best Practices:
- [Python argparse documentation](https://docs.python.org/3/library/argparse.html)
- [Build Command-Line Interfaces With Python's argparse - Real Python](https://realpython.com/command-line-interfaces-python-argparse/)

### Project Context:
- File Matcher codebase analysis (filematcher/cli.py, filematcher/formatters.py, filematcher/actions.py)
- .planning/todos/pending/2026-01-28-interactive-confirmation-ux.md
- Git history: commits related to TTY behavior, verbose progress, confirmation prompts
