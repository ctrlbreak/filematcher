---
created: 2026-01-24T02:10
title: Fix execute mode showing PREVIEW labels incorrectly
area: cli
files:
  - file_matcher.py
---

## Problem

When running with `--execute`, the output still shows:
- "(PREVIEW)" in the mode header
- "WOULD HARDLINK:" instead of action labels like "HARDLINK:"
- "Use --execute to apply changes" footer

This is confusing because the user has already specified `--execute`. The preview pass happens before execution, but the labeling should reflect that execution will follow.

Example from test run:
```
Action mode (PREVIEW): hardlink ...
=== PREVIEW MODE - Use --execute to apply changes ===
WOULD HARDLINK: /path/to/file
Use --execute to apply changes

=== EXECUTING ===
...
```

The preview section should either be suppressed or clearly labeled as "pre-execution scan" when `--execute` is active.

## Solution

TBD - Options:
1. Suppress preview output entirely when `--execute` is set (just show execution results)
2. Change labels to "WILL HARDLINK:" during the scan phase
3. Add a clear separator like "Scanning files..." before showing what will be done
