"""Color system for File Matcher CLI output.

Provides ANSI color support with TTY-aware automatic detection,
NO_COLOR/FORCE_COLOR environment variable support, and color helper functions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import os
import re
import sys

RESET = "\033[0m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"
BOLD = "\033[1m"
DIM = "\033[2m"
BOLD_GREEN = "\033[1;32m"
BOLD_YELLOW = "\033[1;33m"


class ColorMode(Enum):
    """Color output mode: AUTO, NEVER, or ALWAYS."""
    AUTO = "auto"
    NEVER = "never"
    ALWAYS = "always"


class ColorConfig:
    """Determines whether to use color based on mode, environment, and TTY."""

    def __init__(self, mode: ColorMode = ColorMode.AUTO, stream: object = None):
        self.mode = mode
        self.stream = stream if stream is not None else sys.stdout
        self._enabled: bool | None = None

    @property
    def enabled(self) -> bool:
        """Determine if color should be used."""
        if self._enabled is not None:
            return self._enabled

        if self.mode == ColorMode.NEVER:
            self._enabled = False
            return False

        if self.mode == ColorMode.ALWAYS:
            self._enabled = True
            return True

        if os.environ.get('NO_COLOR'):
            self._enabled = False
            return False

        if os.environ.get('FORCE_COLOR'):
            self._enabled = True
            return True

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


_ANSI_ESCAPE_PATTERN = re.compile(r'\x1b\[[0-9;]*m')


def strip_ansi(text: str) -> str:
    """Strip ANSI escape sequences from text."""
    return _ANSI_ESCAPE_PATTERN.sub('', text)


def visible_len(text: str) -> int:
    """Calculate visible length of text, excluding ANSI codes."""
    return len(strip_ansi(text))


def terminal_rows_for_line(text: str, term_width: int) -> int:
    """Calculate how many terminal rows a line will occupy (for cursor movement)."""
    if term_width <= 0:
        return 1
    vis_len = visible_len(text)
    if vis_len == 0:
        return 1
    # Ceiling division: how many rows needed
    return (vis_len + term_width - 1) // term_width


@dataclass
class GroupLine:
    """Structured line for group output, enabling clean color application."""
    line_type: str
    label: str
    path: str
    warning: str = ""
    prefix: str = ""
    indent: str = ""


def colorize(text: str, code: str, color_config: ColorConfig) -> str:
    """Wrap text with ANSI color code if color is enabled."""
    if not color_config.enabled:
        return text
    return f"{code}{text}{RESET}"


def green(text: str, cc: ColorConfig) -> str:
    return colorize(text, GREEN, cc)


def yellow(text: str, cc: ColorConfig) -> str:
    return colorize(text, YELLOW, cc)


def red(text: str, cc: ColorConfig) -> str:
    return colorize(text, RED, cc)


def cyan(text: str, cc: ColorConfig) -> str:
    return colorize(text, CYAN, cc)


def dim(text: str, cc: ColorConfig) -> str:
    return colorize(text, DIM, cc)


def bold(text: str, cc: ColorConfig) -> str:
    return colorize(text, BOLD, cc)


def bold_yellow(text: str, cc: ColorConfig) -> str:
    return colorize(text, BOLD_YELLOW, cc)


def bold_green(text: str, cc: ColorConfig) -> str:
    return colorize(text, BOLD_GREEN, cc)


def render_group_line(line: GroupLine, cc: ColorConfig) -> str:
    """Render a GroupLine to a string with appropriate colors based on line_type."""
    if line.line_type == "master":
        label_colored = bold_green(line.label, cc)
        path_colored = green(line.path, cc)
        return f"{line.prefix}{line.indent}{label_colored}{path_colored}"

    elif line.line_type == "duplicate":
        label_colored = bold_yellow(line.label, cc)
        path_colored = yellow(line.path, cc)
        warning_colored = red(line.warning, cc) if line.warning else ""
        return f"{line.prefix}{line.indent}{label_colored}{path_colored}{warning_colored}"

    elif line.line_type == "hash":
        full_line = f"{line.indent}{line.label}{line.path}"
        return dim(full_line, cc)

    else:
        return f"{line.prefix}{line.indent}{line.label}{line.path}"


def determine_color_mode(args) -> ColorMode:
    """Determine color mode from CLI arguments."""
    if args.json:
        return ColorMode.NEVER
    if args.color_mode == 'always':
        return ColorMode.ALWAYS
    elif args.color_mode == 'never':
        return ColorMode.NEVER
    return ColorMode.AUTO
