---
created: 2026-01-19T23:56
title: Update README for new features
area: docs
files:
  - README.md
---

## Problem

After Phase 4 is complete, the README.md will be outdated. It needs to reflect the new deduplication features added across all 4 phases:
- Master directory support (Phase 1)
- Dry-run preview and statistics (Phase 2)
- Safe defaults with --execute flag and confirmation prompts (Phase 3)
- File actions (hardlink, symlink, delete) and logging (Phase 4)

The README should also be simplified where possible to improve clarity.

## Solution

TBD - After Phase 4 completion:
- Document new CLI flags (--master, --action, --execute, --yes, --dry-run)
- Update usage examples with deduplication workflows
- Simplify existing content where possible
- Ensure feature descriptions match implementation
