---
created: 2026-01-24T02:06
title: Improve verbose output during execution mode
area: cli
files:
  - file_matcher.py
---

## Problem

In execution mode with `--verbose`, the progress indicator shows "Processing x/y" but doesn't include details about which file is being processed. During compare/indexing phase, verbose mode shows the filename and size, but during action execution it only shows the count.

User feedback: would be helpful to see file details during execution to monitor progress on large directories.

## Solution

TBD - Consider showing filename (possibly truncated) and size during action execution, similar to indexing phase output.
