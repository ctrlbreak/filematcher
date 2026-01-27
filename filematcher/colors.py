"""Color system for File Matcher CLI output.

This module provides ANSI color support with TTY-aware automatic detection,
NO_COLOR/FORCE_COLOR environment variable support, and color helper functions.

The color system is a leaf module with no internal filematcher dependencies,
making it suitable for import anywhere in the package.

Color Palette (16-color for compatibility):
- GREEN: Masters (protected files)
- YELLOW: Duplicates (removal candidates)
- RED: Warnings and errors
- CYAN: Statistics and summaries
- BOLD: Emphasis
- DIM: De-emphasis (hash values)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import os
import re
import sys


# ============================================================================
# ANSI Color Constants (16-color for compatibility)
# ============================================================================

# Reset
RESET = "\033[0m"

# Foreground colors (per 08-CONTEXT.md color palette)
GREEN = "\033[32m"      # Masters (protected files)
YELLOW = "\033[33m"     # Duplicates (removal candidates)
RED = "\033[31m"        # Warnings and errors
CYAN = "\033[36m"       # Statistics and summaries

# Styles
BOLD = "\033[1m"        # Emphasis
DIM = "\033[2m"         # De-emphasis (hash values)

# Compound styles
BOLD_GREEN = "\033[1;32m"   # Master labels
BOLD_YELLOW = "\033[1;33m"  # PREVIEW MODE banner, duplicate labels


# ============================================================================
# Color Configuration
# ============================================================================

class ColorMode(Enum):
    """Color output mode."""
    AUTO = "auto"      # Enable color if TTY and no NO_COLOR
    NEVER = "never"    # Never use color
    ALWAYS = "always"  # Always use color (even in pipes)


class ColorConfig:
    """Determines whether to use color based on mode, environment, and TTY.

    Follows NO_COLOR standard (https://no-color.org/) and common CLI conventions.

    Priority order:
    1. Explicit mode (NEVER or ALWAYS) from --color/--no-color flags
    2. NO_COLOR environment variable (disables color)
    3. FORCE_COLOR environment variable (enables color, for CI systems)
    4. TTY detection on the output stream
    """

    def __init__(
        self,
        mode: ColorMode = ColorMode.AUTO,
        stream: object = None
    ):
        """Initialize color configuration.

        Args:
            mode: Color mode (AUTO, NEVER, ALWAYS)
            stream: Output stream for TTY detection (default: sys.stdout)
        """
        self.mode = mode
        self.stream = stream if stream is not None else sys.stdout
        self._enabled: bool | None = None

    @property
    def enabled(self) -> bool:
        """Determine if color should be used.

        Returns:
            True if color output should be used, False otherwise.
        """
        # Use cached value if already computed
        if self._enabled is not None:
            return self._enabled

        # NEVER mode: always disabled
        if self.mode == ColorMode.NEVER:
            self._enabled = False
            return False

        # ALWAYS mode: always enabled (explicit user intent overrides environment)
        if self.mode == ColorMode.ALWAYS:
            self._enabled = True
            return True

        # AUTO mode: check environment and TTY
        # NO_COLOR takes precedence (standard compliance)
        if os.environ.get('NO_COLOR'):
            self._enabled = False
            return False

        # FORCE_COLOR enables (used by CI systems like GitHub Actions)
        if os.environ.get('FORCE_COLOR'):
            self._enabled = True
            return True

        # TTY detection
        try:
            self._enabled = self.stream.isatty()
        except AttributeError:
            self._enabled = False

        return self._enabled

    def reset(self) -> None:
        """Reset cached enabled state (for testing)."""
        self._enabled = None

    @property
    def is_tty(self) -> bool:
        """Check if output stream is a TTY."""
        try:
            return self.stream.isatty()
        except AttributeError:
            return False


# ============================================================================
# Terminal Helper Functions
# ============================================================================

# Regex pattern for ANSI escape sequences
_ANSI_ESCAPE_PATTERN = re.compile(r'\x1b\[[0-9;]*m')


def strip_ansi(text: str) -> str:
    """Strip ANSI escape sequences from text.

    Args:
        text: Text that may contain ANSI color codes

    Returns:
        Text with all ANSI escape sequences removed
    """
    return _ANSI_ESCAPE_PATTERN.sub('', text)


def visible_len(text: str) -> int:
    """Calculate visible length of text, excluding ANSI codes.

    Args:
        text: Text that may contain ANSI color codes

    Returns:
        Number of visible characters (excluding escape sequences)
    """
    return len(strip_ansi(text))


def terminal_rows_for_line(text: str, term_width: int) -> int:
    """Calculate how many terminal rows a line will occupy.

    When a line exceeds terminal width, it wraps to additional rows.
    This is needed for cursor movement calculations in TTY mode.

    Args:
        text: Line of text (may contain ANSI codes)
        term_width: Terminal width in columns

    Returns:
        Number of terminal rows this line occupies (minimum 1)
    """
    if term_width <= 0:
        return 1
    vis_len = visible_len(text)
    if vis_len == 0:
        return 1
    # Ceiling division: how many rows needed
    return (vis_len + term_width - 1) // term_width


# ============================================================================
# Structured Output Types
# ============================================================================

@dataclass
class GroupLine:
    """Structured line for group output, enabling clean color application.

    This separates data structure from presentation, allowing colors to be
    applied based on line_type rather than string parsing.
    """
    line_type: str  # "master", "duplicate", "hash", "other"
    label: str      # "MASTER:", "WOULD DELETE:", etc.
    path: str       # File path or hash value
    warning: str = ""  # "[!cross-fs]" or empty
    prefix: str = ""   # "[1/3] " progress prefix or empty
    indent: str = ""   # "    " for duplicates or empty


# ============================================================================
# Color Helper Functions
# ============================================================================

def colorize(text: str, code: str, color_config: ColorConfig) -> str:
    """Wrap text with ANSI color code if color is enabled.

    Args:
        text: Text to colorize
        code: ANSI escape code (e.g., GREEN, BOLD)
        color_config: ColorConfig instance determining if color is enabled

    Returns:
        Colorized text if enabled, original text otherwise.
    """
    if not color_config.enabled:
        return text
    return f"{code}{text}{RESET}"


def green(text: str, cc: ColorConfig) -> str:
    """Color text green (masters, protected files)."""
    return colorize(text, GREEN, cc)


def yellow(text: str, cc: ColorConfig) -> str:
    """Color text yellow (duplicates, removal candidates)."""
    return colorize(text, YELLOW, cc)


def red(text: str, cc: ColorConfig) -> str:
    """Color text red (warnings, errors)."""
    return colorize(text, RED, cc)


def cyan(text: str, cc: ColorConfig) -> str:
    """Color text cyan (statistics, summaries)."""
    return colorize(text, CYAN, cc)


def dim(text: str, cc: ColorConfig) -> str:
    """Dim text (hash values, de-emphasized content)."""
    return colorize(text, DIM, cc)


def bold(text: str, cc: ColorConfig) -> str:
    """Bold text (emphasis)."""
    return colorize(text, BOLD, cc)


def bold_yellow(text: str, cc: ColorConfig) -> str:
    """Bold yellow text (PREVIEW MODE banner, duplicate labels)."""
    return colorize(text, BOLD_YELLOW, cc)


def bold_green(text: str, cc: ColorConfig) -> str:
    """Bold green text (master labels)."""
    return colorize(text, BOLD_GREEN, cc)


def render_group_line(line: GroupLine, cc: ColorConfig) -> str:
    """Render a GroupLine to a string with appropriate colors.

    Applies colors based on line_type, separating structure from presentation.

    Args:
        line: GroupLine with structured data
        cc: ColorConfig for color decisions

    Returns:
        Formatted string with colors applied
    """
    if line.line_type == "master":
        # Master line: bold green label, green path
        label_colored = bold_green(line.label, cc)
        path_colored = green(line.path, cc)
        return f"{line.prefix}{line.indent}{label_colored}{path_colored}"

    elif line.line_type == "duplicate":
        # Duplicate line: bold yellow label, yellow path, red warning
        label_colored = bold_yellow(line.label, cc)
        path_colored = yellow(line.path, cc)
        warning_colored = red(line.warning, cc) if line.warning else ""
        return f"{line.prefix}{line.indent}{label_colored}{path_colored}{warning_colored}"

    elif line.line_type == "hash":
        # Hash line: all dim
        full_line = f"{line.indent}{line.label}{line.path}"
        return dim(full_line, cc)

    else:
        # Other: no color
        return f"{line.prefix}{line.indent}{line.label}{line.path}"


def determine_color_mode(args) -> ColorMode:
    """Determine color mode from CLI arguments.

    Args:
        args: Parsed command-line arguments

    Returns:
        ColorMode based on flags (AUTO if no flags, ALWAYS for --color, NEVER for --no-color)
    """
    # --json implies no color (JSON must never have ANSI codes)
    if args.json:
        return ColorMode.NEVER

    # Explicit flag takes precedence
    if args.color_mode == 'always':
        return ColorMode.ALWAYS
    elif args.color_mode == 'never':
        return ColorMode.NEVER

    # Default to AUTO (TTY detection)
    return ColorMode.AUTO
