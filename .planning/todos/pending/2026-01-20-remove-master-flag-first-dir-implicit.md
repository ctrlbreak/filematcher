---
created: 2026-01-20T01:37
title: Remove master flag, first directory is implicit master
area: cli
files:
  - file_matcher.py
---

## Problem

Currently the `--master` flag must be explicitly specified to designate which directory contains the authoritative copies during deduplication. This adds friction since the first positional directory argument is the natural "source of truth" in typical usage patterns.

Users must type:
```bash
filematcher dir1 dir2 --master dir1 --action hardlink
```

When the simpler form would suffice:
```bash
filematcher dir1 dir2 --action hardlink
```

## Solution

- Remove the `--master` CLI flag
- Treat the first positional directory argument as the implicit master
- Update help text and documentation to clarify this convention
- Simplify internal logic that validates master directory
