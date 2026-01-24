---
phase: quick-007
plan: 01
subsystem: output
tags: [dataclass, color, refactor, tty]

requires:
  - phase: quick-006
    provides: inline TTY progress for group output

provides:
  - GroupLine dataclass for structured output
  - render_group_line() for clean color application
  - ColorConfig.is_tty for centralized TTY detection
  - Eliminated string parsing for color application

affects: [future-formatters, output-extensions]

tech-stack:
  added: [dataclasses]
  patterns: [structured-output, separation-of-concerns]

key-files:
  created: []
  modified:
    - file_matcher.py

key-decisions:
  - "GroupLine dataclass stores line_type, label, path, warning, prefix, indent"
  - "render_group_line() applies colors based on line_type not string content"
  - "ColorConfig.is_tty centralizes stdout TTY detection"

patterns-established:
  - "Structured output: use GroupLine for group lines, render at output time"
  - "TTY detection: use ColorConfig.is_tty for stdout TTY checks"

duration: 4min
completed: 2026-01-24
---

# Quick Task 007: Refactor Output Formatting for Modularity

**GroupLine dataclass separates structure from presentation, eliminating string parsing for color application**

## Performance

- **Duration:** 4 min
- **Started:** 2026-01-24T00:38:23Z
- **Completed:** 2026-01-24T00:42:13Z
- **Tasks:** 3
- **Files modified:** 1

## Accomplishments

- Created GroupLine dataclass for structured line representation
- Added render_group_line() to apply colors based on line_type
- Eliminated fragile string parsing for "MASTER:" and "[!cross-fs]"
- Centralized TTY detection in ColorConfig.is_tty property

## Task Commits

1. **Task 1: Create GroupLine dataclass and refactor format_group_lines** - `084f4d2` (refactor)
2. **Task 2: Update TextActionFormatter to use GroupLine** - `8ecb506` (refactor)
3. **Task 3: Centralize TTY detection and clean up main() prints** - `9d8db29` (refactor)

## Files Modified

- `file_matcher.py` - Added GroupLine dataclass, render_group_line(), ColorConfig.is_tty; refactored format_group_lines, format_duplicate_group, and TextActionFormatter

## Technical Details

### GroupLine Dataclass

```python
@dataclass
class GroupLine:
    line_type: str  # "master", "duplicate", "hash", "other"
    label: str      # "MASTER:", "WOULD DELETE:", etc.
    path: str       # File path or hash value
    warning: str = ""  # "[!cross-fs]" or empty
    prefix: str = ""   # "[1/3] " progress prefix or empty
    indent: str = ""   # "    " for duplicates or empty
```

### render_group_line()

Applies colors based on `line_type`:
- `"master"`: bold green label, green path
- `"duplicate"`: bold yellow label, yellow path, red warning
- `"hash"`: dim entire line
- `"other"`: no color

### ColorConfig.is_tty

```python
@property
def is_tty(self) -> bool:
    try:
        return self.stream.isatty()
    except AttributeError:
        return False
```

## Decisions Made

- GroupLine fields chosen to cover all current use cases (master, duplicate, hash)
- Kept warning as string field rather than boolean for flexibility
- Left stderr TTY check separate (different output stream)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Structured output foundation ready for future formatter extensions
- Pattern established for clean separation of data and presentation
- All 206 tests pass

---
*Quick Task: 007-refactor-output-formatting*
*Completed: 2026-01-24*
