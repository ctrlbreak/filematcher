# Phase 8: Color Enhancement - Research

**Researched:** 2026-01-23
**Domain:** Python TTY-aware ANSI color output for CLI tool
**Confidence:** HIGH

## Summary

This phase adds TTY-aware ANSI color highlighting to the file matcher CLI, following the established NO_COLOR standard and common CLI conventions (git, pytest, ripgrep). The implementation uses Python's standard library exclusively (no colorama, termcolor, or rich dependencies) to maintain the zero-dependency constraint.

The key architectural insight is that color should be implemented as a **decorator layer** around the existing formatter output, not by modifying the formatters themselves. This keeps the Text/JSON formatter separation clean and allows color to be toggled independently. The existing formatter abstraction (Phase 5) provides clean injection points for color-wrapped output.

The research confirms three standard approaches: (1) raw ANSI escape codes for zero dependencies; (2) per-stream TTY detection allowing independent stdout/stderr coloring; (3) a tri-state `--color=auto|never|always` flag pattern (git convention) or dual `--color`/`--no-color` flags (last-wins precedence per CONTEXT.md).

**Primary recommendation:** Implement a `ColorConfig` class that determines color state from environment and flags, then create `colorize()` helper functions that wrap text with ANSI codes. Pass `ColorConfig` to formatters via constructor, and apply color at the `print()` call sites within TextCompareFormatter and TextActionFormatter.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `sys.stdout.isatty()` | stdlib | TTY detection | Python's standard mechanism for terminal detection |
| `os.environ` | stdlib | Environment variable access | Check NO_COLOR, CLICOLOR, FORCE_COLOR |
| Built-in `\033[` codes | N/A | ANSI escape sequences | Zero dependencies, works on all Unix terminals, Windows 10+ |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `functools.lru_cache` | stdlib | Cache color state | Avoid repeated environment checks |
| `enum.Enum` | stdlib | Color mode enum | Type-safe auto/never/always values |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Raw ANSI codes | colorama | colorama adds Windows <10 support but adds dependency |
| Raw ANSI codes | termcolor | termcolor adds convenience API but adds dependency |
| Raw ANSI codes | rich | rich adds many features but massive dependency |
| Per-print coloring | Pre-colored strings in formatters | Would require duplicating formatters or complex inheritance |

**Installation:**
```bash
# All standard library - no installation required
```

## Architecture Patterns

### Recommended Project Structure
```
file_matcher.py (single file, maintaining existing pattern)
  |
  +-- ANSI Color Constants (module-level)
  |
  +-- ColorConfig class (determines color state)
  |
  +-- colorize() helper functions
  |
  +-- Modified Text Formatters (receive ColorConfig, apply color at print)
  |
  +-- JSON Formatters (unchanged - never colored)
```

### Pattern 1: Color Configuration Class

**What:** Single class that encapsulates all color decision logic
**When to use:** At startup, determine color state once and pass to formatters
**Example:**
```python
# Source: NO_COLOR standard (https://no-color.org/)
from enum import Enum
import os
import sys

class ColorMode(Enum):
    AUTO = "auto"
    NEVER = "never"
    ALWAYS = "always"

class ColorConfig:
    """Determines whether to use color based on environment and flags."""

    def __init__(
        self,
        mode: ColorMode = ColorMode.AUTO,
        stream: object = None  # sys.stdout or sys.stderr
    ):
        self.mode = mode
        self.stream = stream or sys.stdout
        self._enabled: bool | None = None

    @property
    def enabled(self) -> bool:
        """Determine if color should be used."""
        if self._enabled is not None:
            return self._enabled

        # NEVER mode: always disabled
        if self.mode == ColorMode.NEVER:
            self._enabled = False
            return False

        # ALWAYS mode: always enabled (unless NO_COLOR is set)
        if self.mode == ColorMode.ALWAYS:
            # NO_COLOR takes precedence even over --color
            # Per NO_COLOR spec: "command-line arguments should override"
            # But many tools still respect NO_COLOR even with --color
            # Decision: --color overrides NO_COLOR (user's explicit intent)
            self._enabled = True
            return True

        # AUTO mode: check NO_COLOR, then TTY
        if os.environ.get('NO_COLOR'):
            self._enabled = False
            return False

        # Check FORCE_COLOR (used by CI systems like GitHub Actions)
        if os.environ.get('FORCE_COLOR'):
            self._enabled = True
            return True

        # Check TTY
        try:
            self._enabled = self.stream.isatty()
        except AttributeError:
            self._enabled = False

        return self._enabled
```

### Pattern 2: ANSI Color Constants

**What:** Module-level constants for ANSI escape codes (16-color, widely supported)
**When to use:** Define once, use throughout for consistent colors
**Example:**
```python
# Source: ANSI Standard (https://en.wikipedia.org/wiki/ANSI_escape_code)
# Using 16-color SGR codes for maximum compatibility

# Reset
RESET = "\033[0m"

# Foreground colors (per CONTEXT.md decisions)
GREEN = "\033[32m"      # Masters (protected files)
YELLOW = "\033[33m"     # Duplicates (removal candidates)
RED = "\033[31m"        # Warnings and errors
CYAN = "\033[36m"       # Statistics and summaries

# Styles
BOLD = "\033[1m"        # PREVIEW MODE banner emphasis
DIM = "\033[2m"         # Hash values (de-emphasized)

# Compound styles
BOLD_YELLOW = "\033[1;33m"  # PREVIEW MODE banner
```

### Pattern 3: Colorize Helper Functions

**What:** Functions that wrap text with ANSI codes if color is enabled
**When to use:** At every print call site in TextFormatters
**Example:**
```python
# Source: Common Python CLI pattern
def colorize(text: str, color: str, color_config: ColorConfig) -> str:
    """Wrap text with color codes if color is enabled."""
    if not color_config.enabled:
        return text
    return f"{color}{text}{RESET}"

def green(text: str, cc: ColorConfig) -> str:
    """Color text green (masters)."""
    return colorize(text, GREEN, cc)

def yellow(text: str, cc: ColorConfig) -> str:
    """Color text yellow (duplicates)."""
    return colorize(text, YELLOW, cc)

def red(text: str, cc: ColorConfig) -> str:
    """Color text red (warnings)."""
    return colorize(text, RED, cc)

def cyan(text: str, cc: ColorConfig) -> str:
    """Color text cyan (statistics)."""
    return colorize(text, CYAN, cc)

def dim(text: str, cc: ColorConfig) -> str:
    """Dim text (hash values)."""
    return colorize(text, DIM, cc)

def bold_yellow(text: str, cc: ColorConfig) -> str:
    """Bold yellow text (PREVIEW banner)."""
    return colorize(text, BOLD_YELLOW, cc)
```

### Pattern 4: Flag Parsing with Last-Wins Precedence

**What:** Parse `--color` and `--no-color` flags with last-wins semantics
**When to use:** Per CONTEXT.md: "Flag precedence: last one wins when both specified"
**Example:**
```python
# Source: CONTEXT.md decisions, git convention
# Option 1: Dual flags with store_const
parser.add_argument('--color', dest='color_mode', action='store_const',
                    const='always', help='Force color output')
parser.add_argument('--no-color', dest='color_mode', action='store_const',
                    const='never', help='Disable color output')
# Default is None (auto mode)

# In main():
if args.color_mode == 'always':
    mode = ColorMode.ALWAYS
elif args.color_mode == 'never':
    mode = ColorMode.NEVER
else:
    mode = ColorMode.AUTO

# Option 2: Single tri-state flag (git style)
parser.add_argument('--color', choices=['auto', 'never', 'always'],
                    default='auto', nargs='?', const='always',
                    help='Color output: auto (default), never, always')
```

### Pattern 5: Per-Stream Color Configuration

**What:** Independent color config for stdout and stderr
**When to use:** When `filematcher dir1 dir2 2>/dev/null` should still have colored stdout
**Example:**
```python
# Source: CONTEXT.md - "Per-stream TTY detection"
# Create separate configs for each stream
stdout_color = ColorConfig(mode=color_mode, stream=sys.stdout)
stderr_color = ColorConfig(mode=color_mode, stream=sys.stderr)

# Pass appropriate config to formatters
text_formatter = TextCompareFormatter(
    verbose=args.verbose,
    dir1_name=dir1_name,
    dir2_name=dir2_name,
    color_config=stdout_color
)

# Logger could use stderr_color for colored warnings
```

### Anti-Patterns to Avoid

- **Subclassing for color:** Don't create ColoredTextCompareFormatter. Use composition (color config passed to existing formatter).
- **Global color state:** Don't use module-level `USE_COLOR` variable. Use ColorConfig objects for testability.
- **Coloring JSON output:** JSON must NEVER have ANSI codes. The JsonCompareFormatter and JsonActionFormatter should ignore color config entirely.
- **Forgetting RESET:** Every colored segment must end with RESET to prevent color bleeding.
- **256-color or true-color:** Stick to 16-color SGR codes for compatibility. 256/true-color not reliably supported.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| TTY detection | Custom file descriptor checks | `stream.isatty()` | Handles edge cases (pipes, redirects, pseudo-terminals) |
| Environment checks | Custom getenv with defaults | `os.environ.get('NO_COLOR')` | Standard pattern, None-safe |
| Flag precedence | Complex if/else chains | argparse `store_const` with None default | Last flag wins naturally |
| Color stripping for tests | Regex on output | ColorConfig with NEVER mode | Cleaner, no regex needed |

**Key insight:** The existing TextCompareFormatter and TextActionFormatter already have all the output logic. Color is purely additive - wrap existing strings at print time, don't restructure the formatters.

## Common Pitfalls

### Pitfall 1: Color Codes in JSON Output

**What goes wrong:** ANSI codes appear in JSON, breaking parsers
**Why it happens:** Color applied globally without checking output format
**How to avoid:**
1. JsonCompareFormatter and JsonActionFormatter ignore color_config entirely
2. Pass `ColorConfig(mode=ColorMode.NEVER)` when JSON mode is active
3. Add assertion in JSON formatters: `assert not color_config.enabled`
**Warning signs:** `jq` fails to parse output, ANSI codes visible in JSON

### Pitfall 2: Color Bleeding Across Lines

**What goes wrong:** Color from one line affects subsequent lines
**Why it happens:** Forgot to add RESET at end of colored segment
**How to avoid:**
1. Always use `colorize()` helper which adds RESET
2. Each print statement should end in normal state
3. Test: pipe output through `cat -v` to see escape codes
**Warning signs:** Entire terminal turns green after running tool

### Pitfall 3: Hardcoded Color Decisions

**What goes wrong:** Color state determined at import time, not runtime
**Why it happens:** Using module-level `USE_COLOR = sys.stdout.isatty()`
**How to avoid:**
1. ColorConfig evaluated lazily in `enabled` property
2. Don't cache at module level
3. Pass ColorConfig through dependency injection
**Warning signs:** Tests fail because module was imported before stream redirection

### Pitfall 4: Ignoring NO_COLOR with --color Flag

**What goes wrong:** User sets NO_COLOR globally but `--color` doesn't override
**Why it happens:** Checking NO_COLOR after flag processing
**How to avoid:**
1. Per CONTEXT.md: flags override environment
2. `--color` means "force color on" regardless of NO_COLOR
3. Document this behavior (controversial - some tools do it differently)
**Warning signs:** User confusion when `--color` doesn't work

### Pitfall 5: Breaking Text Content Equality

**What goes wrong:** Output differs between color/no-color modes (beyond ANSI codes)
**Why it happens:** Color logic adds/removes actual text, not just codes
**How to avoid:**
1. Success criteria: "Text content is identical with or without color"
2. Test: strip ANSI codes and compare
3. colorize() should ONLY add escape codes, never modify text
**Warning signs:** Tests comparing output fail when color is enabled

### Pitfall 6: Windows Compatibility

**What goes wrong:** ANSI codes display as garbage on older Windows
**Why it happens:** Windows <10 doesn't support ANSI by default
**How to avoid:**
1. Windows 10 (1511+) supports ANSI natively
2. Older Windows: either use colorama or disable color
3. Simplest: detect Windows < 10 and set color to NEVER
4. Zero-dependency approach: let users disable with --no-color
**Warning signs:** Windows users report "garbage characters"

## Code Examples

Verified patterns from official sources:

### Complete ColorConfig Implementation

```python
# Source: NO_COLOR spec + Python stdlib
from enum import Enum
import os
import sys

class ColorMode(Enum):
    AUTO = "auto"
    NEVER = "never"
    ALWAYS = "always"

# ANSI escape codes (16-color for compatibility)
RESET = "\033[0m"
GREEN = "\033[32m"      # Masters
YELLOW = "\033[33m"     # Duplicates
RED = "\033[31m"        # Warnings
CYAN = "\033[36m"       # Statistics
BOLD = "\033[1m"
DIM = "\033[2m"
BOLD_YELLOW = "\033[1;33m"  # PREVIEW banner

class ColorConfig:
    """Color configuration with NO_COLOR standard compliance."""

    def __init__(self, mode: ColorMode = ColorMode.AUTO, stream=None):
        self.mode = mode
        self.stream = stream or sys.stdout
        self._enabled: bool | None = None

    @property
    def enabled(self) -> bool:
        if self._enabled is not None:
            return self._enabled

        if self.mode == ColorMode.NEVER:
            self._enabled = False
        elif self.mode == ColorMode.ALWAYS:
            self._enabled = True
        else:  # AUTO
            # NO_COLOR takes precedence
            if os.environ.get('NO_COLOR'):
                self._enabled = False
            # FORCE_COLOR enables (CI systems)
            elif os.environ.get('FORCE_COLOR'):
                self._enabled = True
            # TTY detection
            else:
                try:
                    self._enabled = self.stream.isatty()
                except AttributeError:
                    self._enabled = False

        return self._enabled

def colorize(text: str, code: str, cc: ColorConfig) -> str:
    """Wrap text with ANSI code if color enabled."""
    if not cc.enabled:
        return text
    return f"{code}{text}{RESET}"
```

### Formatter Integration

```python
# Source: Existing TextCompareFormatter pattern
class TextCompareFormatter(CompareFormatter):
    def __init__(
        self,
        verbose: bool = False,
        dir1_name: str = "dir1",
        dir2_name: str = "dir2",
        color_config: ColorConfig | None = None
    ):
        super().__init__(verbose, dir1_name, dir2_name)
        self.cc = color_config or ColorConfig(mode=ColorMode.NEVER)

    def format_match_group(self, file_hash: str, files_dir1: list[str], files_dir2: list[str]) -> None:
        # Hash in dim
        hash_display = colorize(f"Hash: {file_hash[:10]}...", DIM, self.cc)
        print(hash_display)

        # Dir1 files in green (master-like)
        print(f"  Files in {self.dir1_name}:")
        for f in sorted(files_dir1):
            print(f"    {colorize(f, GREEN, self.cc)}")

        # Dir2 files in yellow (duplicate-like)
        print(f"  Files in {self.dir2_name}:")
        for f in sorted(files_dir2):
            print(f"    {colorize(f, YELLOW, self.cc)}")
        print()

    def format_statistics(self, group_count: int, file_count: int, space_savings: int) -> None:
        print()
        header = colorize("--- Statistics ---", CYAN, self.cc)
        print(header)
        # ... rest of statistics
```

### Argument Parsing

```python
# Source: CONTEXT.md decisions
# Dual-flag approach with last-wins semantics
parser.add_argument(
    '--color',
    dest='color_mode',
    action='store_const',
    const='always',
    help='Force color output (overrides NO_COLOR)'
)
parser.add_argument(
    '--no-color',
    dest='color_mode',
    action='store_const',
    const='never',
    help='Disable color output'
)

# In main():
def determine_color_mode(args) -> ColorMode:
    """Determine color mode from args and environment."""
    # --json implies no color
    if hasattr(args, 'json') and args.json:
        return ColorMode.NEVER

    # Explicit flag takes precedence
    if args.color_mode == 'always':
        return ColorMode.ALWAYS
    elif args.color_mode == 'never':
        return ColorMode.NEVER

    # Default to AUTO
    return ColorMode.AUTO
```

### Testing Color Output

```python
# Source: Python testing best practices
import re
import unittest
from io import StringIO

ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*m')

def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    return ANSI_ESCAPE.sub('', text)

class TestColorOutput(unittest.TestCase):
    def test_content_identical_with_without_color(self):
        """Success criteria: text content identical with or without color."""
        # Run with color
        colored_output = run_cli(['dir1', 'dir2', '--color'])
        # Run without color
        plain_output = run_cli(['dir1', 'dir2', '--no-color'])

        # Strip ANSI and compare
        self.assertEqual(strip_ansi(colored_output), plain_output)

    def test_no_color_env_disables_color(self):
        """NO_COLOR environment variable respected."""
        with patch.dict(os.environ, {'NO_COLOR': '1'}):
            output = run_cli(['dir1', 'dir2'])
            self.assertNotIn('\033[', output)

    def test_color_flag_overrides_no_color_env(self):
        """--color overrides NO_COLOR per CONTEXT.md."""
        with patch.dict(os.environ, {'NO_COLOR': '1'}):
            output = run_cli(['dir1', 'dir2', '--color'])
            # Should have color codes
            self.assertIn('\033[', output)

    def test_json_never_colored(self):
        """JSON output must never have ANSI codes."""
        output = run_cli(['dir1', 'dir2', '--json', '--color'])
        self.assertNotIn('\033[', output)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| colorama required on Windows | Native ANSI on Windows 10+ | Windows 10 v1511 (2016) | Zero dependencies possible |
| No standard for disabling | NO_COLOR env standard | 2017 | 400+ tools support it |
| Per-tool color flags | `--color=auto\|never\|always` convention | git popularized ~2008 | User expectations set |
| 8-color only | 16-color widely supported | Decades | More readable color options |

**Deprecated/outdated:**
- **colorama for basic use:** Windows 10+ supports ANSI natively. Only needed for Windows 7/8.
- **TERM=dumb check:** Most tools now use NO_COLOR instead.
- **CLICOLOR without NO_COLOR:** NO_COLOR is the newer standard, though CLICOLOR still works.

## Open Questions

Things that couldn't be fully resolved:

1. **FORCE_COLOR priority vs --no-color**
   - What we know: FORCE_COLOR is used by CI systems (GitHub Actions) to enable color
   - What's unclear: Should `--no-color` override FORCE_COLOR?
   - Recommendation: Yes, explicit user flag always wins. Order: flags > NO_COLOR > FORCE_COLOR > TTY

2. **Colored warnings to stderr**
   - What we know: Per CONTEXT.md, per-stream TTY detection
   - What's unclear: Should logger warnings be colored?
   - Recommendation: Yes, create stderr ColorConfig. Warnings in red.

3. **Hash value coloring**
   - What we know: CONTEXT.md says "dim/gray" for de-emphasis
   - What's unclear: DIM may not render well on all terminals
   - Recommendation: Use DIM (\033[2m). If issues reported, consider removing.

4. **Action labels coloring**
   - What we know: CONTEXT.md marks as "Claude's discretion"
   - Options: Color action labels (HARDLINK, DELETE) or keep plain
   - Recommendation: Keep action labels plain. Color the paths only (green master, yellow duplicate).

## Sources

### Primary (HIGH confidence)
- [NO_COLOR Standard](https://no-color.org/) - Environment variable specification
- [CLICOLOR Standard](http://bixense.com/clicolors/) - CLICOLOR, CLICOLOR_FORCE, NO_COLOR precedence
- [ANSI Escape Codes (Wikipedia)](https://en.wikipedia.org/wiki/ANSI_escape_code) - SGR code reference
- [Python sys.stdout.isatty()](https://docs.python.org/3/library/sys.html) - TTY detection

### Secondary (MEDIUM confidence)
- [Git Color Configuration](https://git-scm.com/book/sv/v2/Customizing-Git-Git-Configuration) - `--color=auto|never|always` pattern
- [Adam Johnson: Git Force Colourization](https://adamj.eu/tech/2025/01/03/git-force-colourization/) - Modern color flag patterns
- Project's own research/PITFALLS-OUTPUT-FORMAT.md - Pitfall 8 (color in pipes)
- Project's own research/FEATURES.md - Color-coded output section

### Tertiary (LOW confidence)
- [Python ANSI Codes Gist](https://gist.github.com/rene-d/9e584a7dd2935d0f461904b9f2950007) - Example implementation
- Various CLI color discussions (pytest, mypy issues)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All stdlib, well-documented ANSI codes
- Architecture: HIGH - Clear integration points with existing formatter abstraction
- Pitfalls: HIGH - NO_COLOR standard and TTY detection well-established
- Color palette: MEDIUM - Conventions exist but readability varies by terminal theme

**Research date:** 2026-01-23
**Valid until:** 2026-02-23 (30 days - stable domain, no fast-moving dependencies)
