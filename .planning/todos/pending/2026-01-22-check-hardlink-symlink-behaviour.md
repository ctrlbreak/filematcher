---
created: 2026-01-22T02:30
title: Check and refine behaviour if matched files are hardlinks or symlinks
area: cli
files:
  - file_matcher.py
---

## Problem

When comparing directories, filematcher may encounter files that are already hardlinks or symlinks. The current behaviour in these edge cases is unclear:

- What happens if a "duplicate" is already a hardlink to the master?
- What happens if a file being compared is a symlink?
- Should symlinks be followed or treated as separate entities?
- When using --action hardlink, should we skip files already hardlinked to master?

The `already_hardlinked()` function exists for execute mode, but the compare/discovery phase may not handle these cases optimally.

## Solution

TBD - Investigate current behaviour and decide on desired semantics:
- Document expected behaviour for symlinks in comparison
- Ensure already-hardlinked files are handled consistently
- Consider adding --follow-symlinks or --no-follow-symlinks flag
- Add tests for edge cases
