# Phase 18: Formatter Extensions - Research

**Researched:** 2026-01-29
**Domain:** Python ABC method extension for CLI interactive prompts
**Confidence:** HIGH

## Summary

This phase extends the existing ActionFormatter ABC with three new methods to support interactive execution mode: `format_group_prompt()`, `format_confirmation_status()`, and `format_remaining_count()`. The research confirms that extending Python ABCs with new abstract methods is straightforward using the existing `@abstractmethod` decorator pattern already established in formatters.py.

The key architectural insight is that the existing formatter infrastructure (colors.py helpers, GroupLine dataclass, render functions) provides all the building blocks needed. The new methods follow the same patterns as existing methods: TextActionFormatter produces colored text output using the color helpers, while JsonActionFormatter returns no-ops (silent) since JSON mode does not support interactive prompts (per CONTEXT.md decision).

**Primary recommendation:** Add three new abstract methods to ActionFormatter ABC, implement in TextActionFormatter using existing `dim()`, `green()`, `yellow()` color helpers, and implement as no-ops in JsonActionFormatter. Use the established patterns from Phase 5's formatter abstraction research.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `abc` | stdlib | Abstract Base Classes | Already used in formatters.py for ActionFormatter |
| `sys` | stdlib | TTY detection | Already used for `is_tty` check in ColorConfig |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `filematcher.colors` | internal | Color helpers (dim, green, yellow) | All colored text output |
| `filematcher.types` | internal | Action enum | Action-specific verbs |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Unicode symbols | ASCII (y/n) | Unicode is more visual; already using color which implies terminal support |
| Emoji symbols | Unicode checkmark | Emoji may not render correctly in all terminals; unicode symbols more reliable |

**Installation:**
```bash
# No installation needed - all stdlib and internal modules
```

## Architecture Patterns

### Recommended Project Structure
```
filematcher/
  formatters.py
    |-- ActionFormatter (ABC)
    |     +-- format_group_prompt()      # NEW
    |     +-- format_confirmation_status()  # NEW
    |     +-- format_remaining_count()   # NEW (for 'a' response)
    |
    |-- TextActionFormatter
    |     +-- All three new methods with colored output
    |
    |-- JsonActionFormatter
          +-- All three new methods as no-ops
```

### Pattern 1: Extending Existing ABC with New Abstract Methods

**What:** Add `@abstractmethod` decorated methods to existing ABC class
**When to use:** When extending interface without breaking existing pattern
**Example:**
```python
# Source: Existing formatters.py pattern
from abc import ABC, abstractmethod

class ActionFormatter(ABC):
    # ... existing methods ...

    @abstractmethod
    def format_group_prompt(
        self,
        group_index: int,
        total_groups: int,
        action: str
    ) -> str:
        """Format the interactive prompt for a duplicate group.

        Returns prompt string (for input() call in CLI layer).
        """
        ...

    @abstractmethod
    def format_confirmation_status(self, confirmed: bool) -> None:
        """Output checkmark/x after user decision."""
        ...

    @abstractmethod
    def format_remaining_count(self, remaining: int) -> None:
        """Output message after 'a' (all) response."""
        ...
```

### Pattern 2: Action-Specific Verb Mapping

**What:** Map action types to user-friendly verbs for prompts
**When to use:** Prompt text that varies by action type
**Example:**
```python
# Source: CONTEXT.md decision - action-specific verbs
_ACTION_PROMPT_VERBS = {
    Action.DELETE: "Delete duplicate?",
    Action.HARDLINK: "Create hardlink?",
    Action.SYMLINK: "Create symlink?",
}

def format_group_prompt(self, group_index: int, total_groups: int, action: str) -> str:
    verb = _ACTION_PROMPT_VERBS.get(Action(action), f"Process {action}?")
    progress = dim(f"[{group_index}/{total_groups}]", self.cc)
    return f"{progress} {verb} [y/n/a/q] "
```

### Pattern 3: No-Op Implementation for Unsupported Modes

**What:** JSON formatter implements prompt methods as silent no-ops
**When to use:** When JSON mode doesn't support interactive features
**Example:**
```python
# Source: CONTEXT.md decision - JSON does not support interactive
class JsonActionFormatter(ActionFormatter):
    def format_group_prompt(self, group_index: int, total_groups: int, action: str) -> str:
        # Return empty string - JSON mode never prompts
        return ""

    def format_confirmation_status(self, confirmed: bool) -> None:
        # No-op - JSON mode doesn't show inline status
        pass

    def format_remaining_count(self, remaining: int) -> None:
        # No-op - JSON mode doesn't show inline messages
        pass
```

### Anti-Patterns to Avoid

- **Prompt logic in formatter:** Don't put `input()` calls in formatters - they format output, CLI handles prompting
- **Raising errors in JSON no-ops:** Don't raise NotImplementedError; return empty/no-op (CONTEXT.md leaves this to discretion, no-op is cleaner)
- **Hardcoding terminal width:** Don't assume width; use the pattern from `format_duplicate_group()` which gets terminal width dynamically

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Colored progress indicator | Manual ANSI codes | `dim()` from colors.py | Consistent with existing codebase |
| Green checkmark | Inline `\033[32m` | `green()` from colors.py | Respects NO_COLOR, ColorConfig |
| Yellow X mark | Inline `\033[33m` | `yellow()` from colors.py | Respects NO_COLOR, ColorConfig |
| TTY detection | Direct `sys.stdout.isatty()` | `ColorConfig.is_tty` | Already abstracted, tested |

**Key insight:** All the building blocks exist in colors.py. The new formatter methods are thin wrappers that compose existing primitives.

## Common Pitfalls

### Pitfall 1: Forgetting to Return Prompt String

**What goes wrong:** `format_group_prompt()` prints instead of returns
**Why it happens:** Other formatter methods print; this one is different
**How to avoid:**
- Document clearly: "Returns prompt string for input() call"
- Unit test that return value is non-empty string
**Warning signs:** Input prompt appears on wrong line or not at all

### Pitfall 2: Color Codes in Prompt String

**What goes wrong:** ANSI codes interfere with user input
**Why it happens:** Colored prompt text gets mixed with user typing
**How to avoid:**
- Only colorize progress indicator prefix `[3/10]`
- Keep question text and options hint uncolored
- Test with `--color` flag
**Warning signs:** Terminal cursor behaves strangely during input

### Pitfall 3: Unicode Symbols on Windows

**What goes wrong:** Checkmark/X renders as garbage on older Windows terminals
**Why it happens:** Code page mismatch
**How to avoid:**
- Use simple Unicode: U+2713 checkmark, U+2717 X mark
- Document as known limitation for legacy Windows cmd.exe
- Modern Windows Terminal handles Unicode correctly
**Warning signs:** Test failures on Windows CI, user reports of garbled output

### Pitfall 4: Breaking Existing Tests

**What goes wrong:** Adding abstract methods breaks subclass tests
**Why it happens:** Existing test mocks may not implement new methods
**How to avoid:**
- Update all test mocks that create ActionFormatter instances
- Search for `ActionFormatter` in tests/ before committing
**Warning signs:** Immediate test failures after adding abstract methods

### Pitfall 5: Inconsistent Newline Handling

**What goes wrong:** Extra blank lines or missing separators
**Why it happens:** Unclear where newlines belong (formatter vs caller)
**How to avoid:**
- `format_confirmation_status()` should NOT add newline (appears on same line as prompt)
- `format_remaining_count()` SHOULD include its own newline (standalone message)
- Match existing patterns: `format_banner()` prints newline after, `format_statistics()` adds separator
**Warning signs:** Visual gaps or cramped output

## Code Examples

Verified patterns from official sources:

### format_group_prompt() Implementation
```python
# Source: Follows git add -p pattern from https://git-scm.com/docs/git-add
# Progress indicator dimmed per CONTEXT.md decision

_ACTION_PROMPT_VERBS = {
    Action.DELETE: "Delete duplicate?",
    Action.HARDLINK: "Create hardlink?",
    Action.SYMLINK: "Create symlink?",
}

def format_group_prompt(
    self,
    group_index: int,
    total_groups: int,
    action: str
) -> str:
    """Format interactive prompt with progress and action verb.

    Returns prompt string - caller passes to input().
    """
    verb = _ACTION_PROMPT_VERBS.get(Action(action), f"Process {action}?")
    progress = dim(f"[{group_index}/{total_groups}]", self.cc)
    return f"{progress} {verb} [y/n/a/q] "
```

### format_confirmation_status() Implementation
```python
# Source: Uses unicode symbols for visual clarity
# Color per CONTEXT.md: green checkmark for y, yellow X for n

def format_confirmation_status(self, confirmed: bool) -> None:
    """Output symbol after user response (same line as prompt)."""
    if confirmed:
        # Green checkmark for confirmed
        print(green("\u2713", self.cc), end="")
    else:
        # Yellow X for skipped
        print(yellow("\u2717", self.cc), end="")
    print()  # Complete the line
```

### format_remaining_count() Implementation
```python
# Source: CONTEXT.md decision - show remaining count after 'a'

def format_remaining_count(self, remaining: int) -> None:
    """Output message after 'a' (all) response."""
    print(f"Processing {remaining} remaining groups...")
```

### Test Pattern for New Methods
```python
# Source: Follows existing test patterns in test_color_output.py

def test_format_group_prompt_includes_progress(self):
    """Prompt should include [index/total] progress indicator."""
    formatter = TextActionFormatter(
        verbose=False,
        preview_mode=False,
        action="delete",
        color_config=ColorConfig(mode=ColorMode.NEVER)
    )
    prompt = formatter.format_group_prompt(3, 10, "delete")
    self.assertIn("[3/10]", prompt)
    self.assertIn("Delete duplicate?", prompt)
    self.assertIn("[y/n/a/q]", prompt)

def test_json_formatter_prompt_returns_empty(self):
    """JSON formatter should return empty string for prompt."""
    formatter = JsonActionFormatter(verbose=False, preview_mode=False, action="delete")
    prompt = formatter.format_group_prompt(3, 10, "delete")
    self.assertEqual(prompt, "")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Per-mode format functions | Strategy pattern with ABC | Phase 5 (2026-01-22) | Unified output, easier to extend |
| Direct ANSI codes | Color helper functions | Phase 8 (2026-01-23) | NO_COLOR support, testable |

**Deprecated/outdated:**
- Direct `print()` of ANSI codes: Use `colors.py` helpers instead
- Separate compare/action formatters: Unified into ActionFormatter ABC (Phase 10)

## Open Questions

Things that couldn't be fully resolved:

1. **Exact print behavior for confirmation status**
   - What we know: Should appear on same line as prompt, after user input
   - What's unclear: Whether `input()` includes newline that needs handling
   - Recommendation: Use `print(symbol, end="")` then `print()` to complete line. Test interactively.

2. **Terminal width constraints for prompt**
   - What we know: Long paths could make prompts wrap awkwardly
   - What's unclear: Whether to truncate or let terminal wrap
   - Recommendation: Let terminal wrap. Paths already displayed in `format_duplicate_group()`, prompt is short. This matches git add -p behavior.

3. **ColorConfig access in methods**
   - What we know: TextActionFormatter has `self.cc` attribute
   - What's unclear: Whether to pass explicitly or use instance attribute
   - Recommendation: Use `self.cc` like existing methods. Consistent with pattern.

## Sources

### Primary (HIGH confidence)
- [Python abc module documentation](https://docs.python.org/3/library/abc.html) - ABC extension patterns
- [Git add --patch documentation](https://git-scm.com/docs/git-add) - Interactive prompt conventions
- File Matcher codebase (formatters.py, colors.py) - Existing patterns and infrastructure

### Secondary (MEDIUM confidence)
- [Build your own Command Line with ANSI escape codes](https://www.lihaoyi.com/post/BuildyourownCommandLinewithANSIescapecodes.html) - Terminal color patterns
- [Unicode checkmark printing in Python](https://python-forum.io/thread-25939.html) - Unicode symbol usage

### Tertiary (LOW confidence)
- General CLI design patterns - Industry conventions

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All components already in codebase
- Architecture: HIGH - Direct extension of established Phase 5 patterns
- Pitfalls: HIGH - Based on existing test patterns and CONTEXT.md decisions

**Research date:** 2026-01-29
**Valid until:** 2026-02-28 (30 days - stable domain, no external dependencies)
