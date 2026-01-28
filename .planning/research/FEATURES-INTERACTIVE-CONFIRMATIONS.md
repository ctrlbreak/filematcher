# Feature Landscape: Interactive CLI Confirmations

**Domain:** Interactive confirmation patterns in CLI tools
**Researched:** 2026-01-28
**Context:** Adding per-file interactive confirmation to File Matcher's action execution

## Executive Summary

Interactive CLI confirmations follow well-established Unix conventions with two primary patterns: **simple yes/no prompts** (used by apt, pip, most tools) and **rich interactive modes** (used by git add -p, rm -i). File Matcher should implement a hybrid: per-file prompts with batch control options (yes/no/all/skip/cancel).

**Key finding:** Users expect case-insensitive single-character responses, progress indicators showing "X of Y", and graceful error handling that allows skipping problematic files while continuing.

## Table Stakes Features

Features users expect from interactive confirmation modes. Missing any creates friction.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Case-insensitive responses | Unix convention: y/Y/yes all accepted | Low | Pattern: `[yY]` or `.lower()` comparison |
| Single-letter responses | rm -i, git add -p standard | Low | 'y' not 'yes', avoids typing fatigue |
| Progress indicator (X of Y) | Shows remaining work, prevents anxiety | Low | "Processing 5 of 47 files..." |
| Cancel entire operation | Escape hatch for "I made a mistake" | Low | Standard 'q' or 'c' command |
| Default behavior on Enter | Safe default (No) when user hits Enter | Low | Standard Unix pattern |
| Non-interactive detection | Auto-fail if stdin not TTY | Low | Check `sys.stdin.isatty()` |
| Bypass flag for automation | --yes or -y to skip all prompts | Low | Already exists in File Matcher |
| Display context per prompt | Show what file/action being confirmed | Medium | File path + action + size |
| Error handling continues | Permission denied shouldn't abort all | Medium | Log error, skip file, continue |

## Differentiators

Features that elevate File Matcher beyond basic implementations.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| 'Skip' option | Skip this file but continue with remaining | Low | Common in git add -p, rare elsewhere |
| Undo last action | Immediate rollback if user regrets | High | Complex state management, defer to future |
| Smart defaults | 'y' for small files, require 'yes' for large | Medium | Threshold-based safety |
| Show space savings per file | Decision support: "Deleting will save 4.2GB" | Low | Already calculated |
| Group-level operations | "Process all files in this hash group?" | Medium | Reduces prompt fatigue |
| Cross-filesystem warnings | Inline warning before fallback-symlink | Low | Context-aware prompting |
| Preview before prompt | Show file details, then prompt | Low | Improves decision quality |
| Help available | '?' shows available commands | Low | Self-documenting interface |
| Audit log preview | Show what will be logged before confirm | Medium | Transparency feature |

## Anti-Features

Features to explicitly NOT build to avoid complexity or poor UX.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Full-word responses | Typing "yes" repeatedly causes fatigue | Single-letter: 'y', 'n', 'a', 's', 'c' |
| Complex command syntax | git's 'e' (edit hunk) is expert-only | Keep commands simple and mnemonic |
| Modal editing | Vim-style modes confuse casual users | Single-level command set |
| Regex filtering | Over-engineered for file confirmation | User can filter before running tool |
| Colorized prompts in non-TTY | Breaks when piped | Respect ColorConfig.is_tty |
| Custom keybindings | Adds configuration complexity | Stick to established conventions |
| Multi-key sequences | Ctrl+X then Ctrl+C style commands | Direct single-key commands |
| Progress bars during prompts | Visual noise, hard to implement | Simple "X of Y" counter |
| Interactive search/filter | Feature creep | Keep it simple |

## Command Set Design

Based on git add -p and rm -i patterns, recommended command set:

| Command | Mnemonic | Action | Priority |
|---------|----------|--------|----------|
| y | yes | Perform action on this file | MUST HAVE |
| n | no | Skip this file, continue to next | MUST HAVE |
| a | all | Perform action on all remaining files | MUST HAVE |
| c | cancel | Abort entire operation, no more changes | MUST HAVE |
| s | skip | Same as 'n' (alternative for familiarity) | NICE TO HAVE |
| ? | help | Show available commands | NICE TO HAVE |
| q | quit | Same as 'c' (alternative for familiarity) | NICE TO HAVE |

**Rationale:**
- `y/n` - Universal yes/no convention
- `a` - Common in batch operations (git add -p uses this)
- `c/q` - Both common for "cancel" (c) and "quit" (q)
- `s` - Semantic clarity (skip vs no)
- `?` - Self-documenting help

## Prompt Format Patterns

### Pattern 1: Inline Context (Recommended)

```
MASTER: /path/to/master/file.txt (4.2 GB)
WILL DELETE: /path/to/duplicate/file.txt (4.2 GB, saves 4.2 GB)

Delete this file? [y/n/a/c/?] (1 of 47): _
```

**Advantages:**
- All context visible before decision
- Clear space savings
- Progress indicator reduces anxiety

### Pattern 2: Minimal (Too sparse)

```
Delete /path/to/duplicate/file.txt? [y/n]: _
```

**Problem:** No context about master file or savings

### Pattern 3: Verbose (Too much)

```
═══════════════════════════════════════════════════
File Group 3 (Hash: a1b2c3d4...)
Master Directory: /path/to/master
Master File: file.txt (4.2 GB)
Duplicate File: /path/to/duplicate/file.txt (4.2 GB)
Space Savings: 4.2 GB
Cross-filesystem: No
═══════════════════════════════════════════════════

Delete duplicate file? [y/n/a/c/?] (3 of 47): _
```

**Problem:** Too much visual noise, slows down batch operations

## Error Handling Strategy

### Permission Denied / Access Errors

**Pattern from research:** Continue processing, log error, show count at end

```
MASTER: /master/file1.txt
WILL DELETE: /dup/file1.txt
Delete this file? [y/n/a/c/?] (1 of 3): y
✗ Permission denied: /dup/file1.txt (skipped)

MASTER: /master/file2.txt
WILL DELETE: /dup/file2.txt
Delete this file? [y/n/a/c/?] (2 of 3): y
✓ Deleted /dup/file2.txt

...

Summary:
  Success: 2 files
  Failed: 1 file (permission denied)
  Skipped: 0 files
```

**Key behaviors:**
- Show error inline, don't abort
- Continue to next file
- Summarize errors at end
- Include error details in audit log

### Non-Interactive Context

**Current behavior (KEEP):**
```python
if not sys.stdin.isatty():
    print("Non-interactive mode detected. Use --yes to skip confirmation.",
          file=sys.stderr)
    return False
```

This prevents hanging in scripts/CI.

### User Cancellation

**Pattern:** Clean exit with summary of work done so far

```
Cancelled by user.

Summary (before cancellation):
  Success: 3 files (12.6 GB saved)
  Skipped: 0 files
  Cancelled: 44 files not processed

No further changes will be made.
```

## Progress and Feedback

### Counter Format

**Recommended:** `(X of Y)` pattern
- Shows progress: `(5 of 47)`
- Shows completion: `(47 of 47)`
- Simple, universally understood

**Anti-pattern:** Percentage `(10.6%)`
- Harder to mentally track
- Less intuitive than absolute count

### ETA Display

**Recommendation:** Defer to future version
- Complexity: Need to track timing
- Benefit: Marginal (user can estimate from X of Y)
- User control: Interactive means user controls pace

### Completion Message

```
✓ Operation complete

Summary:
  Success: 45 files (180 GB saved)
  Failed: 2 files (see audit log)
  Skipped: 0 files

Audit log: filematcher_20260128_143022.log
```

## State Management Considerations

### What to Track

| State | Why | Used For |
|-------|-----|----------|
| Total files | Progress indicator | "X of Y" display |
| Current index | Progress indicator | "X of Y" display |
| Success count | Summary | Final report |
| Failure count | Summary | Final report + exit code |
| Skipped count | Summary | Final report |
| Space saved | Summary | Final report |
| Failed file list | Audit log | Debugging |

### What NOT to Track

- **Undo history:** Complex, defer to future
- **Per-file timing:** Not needed for summary
- **User response history:** Not needed (audit log has results)

## Integration with Existing Features

### --yes Flag Behavior

**Current (KEEP):** Bypass single confirmation prompt before batch execution

**New behavior:** Also bypass per-file prompts (maintain current --yes semantics)

### --verbose Flag Interaction

**Recommendation:** In interactive mode, show more detail in prompt

```
# Normal interactive:
MASTER: /master/file.txt (4.2 GB)
WILL DELETE: /dup/file.txt
Delete this file? [y/n/a/c/?] (1 of 5): _

# Verbose interactive:
MASTER: /master/file.txt (4.2 GB, md5: a1b2c3d4...)
WILL DELETE: /dup/file.txt (4.2 GB, md5: a1b2c3d4...)
Delete this file? [y/n/a/c/?] (1 of 5): _
```

### JSON Output Mode

**Behavior:** Interactive prompts incompatible with JSON output

**Current validation (KEEP):**
```python
if args.json and args.execute and not args.yes:
    parser.error("--json with --execute requires --yes flag")
```

### Audit Logging

**Enhancement:** Log user responses

```
[2026-01-28 14:30:22] ACTION: delete /dup/file1.txt (user: yes)
[2026-01-28 14:30:23] SUCCESS: deleted /dup/file1.txt (saved 4.2 GB)
[2026-01-28 14:30:25] ACTION: delete /dup/file2.txt (user: skip)
[2026-01-28 14:30:25] SKIPPED: /dup/file2.txt (user declined)
```

## Implementation Phases

### Phase 1: Basic Interactive Mode (MVP)

**Commands:** y, n, a, c
**Features:**
- Per-file prompts with context
- Progress counter (X of Y)
- Summary at end
- Error handling continues

### Phase 2: Enhanced Interactions

**Commands:** Add s, q, ?
**Features:**
- Help text
- Alternative command names
- Better error messages

### Phase 3: Smart Features (Future)

**Features:**
- Group-level prompts
- Smart defaults based on file size
- Undo support

## Edge Cases to Handle

| Edge Case | Expected Behavior |
|-----------|------------------|
| EOF on stdin | Treat as 'cancel' |
| Invalid input | Re-prompt with error message |
| Repeated invalid input | After 3 attempts, treat as 'cancel' |
| Ctrl+C (SIGINT) | Treat as 'cancel', clean summary |
| Empty input (Enter) | Treat as 'no' (safe default) |
| Whitespace around input | Strip and process |
| Multiple characters | Take first character only |
| All files already processed | Skip prompts, show summary |

## Testing Strategy

### Unit Tests Needed

- Input parsing (case insensitivity, whitespace)
- Progress counter accuracy
- State tracking (counts, space saved)
- Error handling (permission denied, etc.)
- Default behavior (Enter → no)

### Integration Tests Needed

- Full workflow: y on some, n on others
- 'a' command processes all remaining
- 'c' command stops immediately
- Non-TTY detection
- --yes bypass works correctly

### Manual Testing Scenarios

- Large batch (100+ files) for fatigue testing
- Mixed responses (y/n/a/c patterns)
- Error injection (permission issues mid-batch)
- Ctrl+C during execution

## Sources

### CLI Conventions and Best Practices
- [Command Line Interface Guidelines](https://clig.dev/)
- [Create Interactive Bash Scripts With Yes, No, Cancel Prompt - OSTechNix](https://ostechnix.com/create-interactive-bash-scripts-with-yes-no-cancel-prompt/)
- [How to prompt for Yes/No/Cancel input in a Linux shell script - GeeksforGeeks](https://www.geeksforgeeks.org/linux-unix/how-to-prompt-for-yes-no-cancel-input-in-a-linux-shell-script/)

### Interactive Mode Examples

**rm -i:**
- [Linux Rm Command](https://www.computerhope.com/unix/urm.htm)
- [rm man page](https://linuxcommand.org/lc3_man_pages/rm1.html)
- [Mastering the `rm -i` Command in Linux - LinuxVox.com](https://linuxvox.com/blog/rm-interactive-linux/)

**git add -p:**
- [Git - Interactive Staging](https://git-scm.com/book/ms/v2/Git-Tools-Interactive-Staging)
- [Staging patches with git add · Simon Holywell](https://www.simonholywell.com/post/git-add-p/)
- [git add --patch and --interactive](https://nuclearsquid.com/writings/git-add/)
- [Explaining the 'git add -p' command (with examples)](https://www.slingacademy.com/article/explaining-git-add-p-command-examples/)

**APT:**
- [Chapter 2. Debian package management](https://www.debian.org/doc/manuals/debian-reference/ch02.en.html)
- ["apt install -y" Command Explained For Beginners!](https://embeddedinventor.com/apt-install-y-command-explained-for-beginners/)
- [Quiet and unattended installation with apt-get | peteris.rocks](https://peteris.rocks/blog/quiet-and-unattended-installation-with-apt-get/)

**pip:**
- [pip uninstall - pip documentation v25.3](https://pip.pypa.io/en/stable/cli/pip_uninstall/)
- [Pip install and uninstall in silent, non-interactive mode | bobbyhadz](https://bobbyhadz.com/blog/python-pip-install-silent-non-interactive-mode)

### Error Handling Patterns
- [Request: skip & continue when directories/files do not have permission · Issue #75](https://github.com/Byron/dua-cli/issues/75)
- [Linux / Unix Find Command Avoid Permission Denied Messages - nixCraft](https://www.cyberciti.biz/faq/bash-find-exclude-all-permission-denied-messages/)

### Progress Indicators
- [CLI UX best practices: 3 patterns for improving progress displays—Martian Chronicles](https://evilmartians.com/chronicles/cli-ux-best-practices-3-patterns-for-improving-progress-displays)
- [cli-progress - npm](https://www.npmjs.com/package/cli-progress)
- [Advanced cli progress bars • cli](https://cli.r-lib.org/articles/progress-advanced.html)

### Input Conventions
- [Create Yes/No Prompt in Bash Script (Linux)](https://linuxconfig.org/bash-script-yes-no-prompt-example)
- [Bash Script: YES/NO Prompt Example](https://www.dotlinux.net/blog/bash-script-yes-no-prompt-example/)
- [GNU Readline Library - Command Line Editing](https://web.mit.edu/gnu/doc/html/rlman_1.html)
- [Keyboard Shortcuts every Command Line Hacker should know about GNU Readline - Mastering Emacs](https://www.masteringemacs.org/article/keyboard-shortcuts-every-command-line-hacker-should-know-about-gnu-readline)

### Safety Best Practices
- [Is It Possible to Undo a Command in Shell? | Baeldung on Linux](https://www.baeldung.com/linux/shell-undo)
