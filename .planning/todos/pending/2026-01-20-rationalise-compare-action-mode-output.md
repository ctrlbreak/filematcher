---
created: 2026-01-20T01:38
title: Rationalise output from compare mode and action mode
area: cli
files:
  - file_matcher.py
---

## Problem

The tool currently has two distinct operational modes:
1. **Compare mode** (default): Shows files with matching content across directories
2. **Action mode** (with `--action`): Previews/executes deduplication actions

Each mode has evolved independently, resulting in inconsistent output formatting between them. Users may find it confusing when output structure changes based on mode. The output should feel cohesive regardless of which mode is active.

## Solution

TBD - Review current output formats for both modes and design a unified approach that:
- Maintains backward compatibility where reasonable
- Uses consistent formatting patterns (headers, indentation, separators)
- Provides appropriate detail level for each mode while feeling cohesive
