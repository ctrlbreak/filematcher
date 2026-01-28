---
created: 2026-01-28T23:50
title: Redesign interactive confirmation UX for execute mode
area: cli
files:
  - filematcher/cli.py
  - filematcher/actions.py
  - filematcher/formatters.py
---

## Problem

The current execute mode workflow needs better interactive confirmation:
- User wants (yes/no/all/cancel) style prompts for each file
- Current approach of showing all files then prompting separately is disconnected
- TTY carriage return behavior for overwriting prompts is complex and unreliable
- Need to maintain consistency with preview mode and JSON output

## Solution

Needs research and careful design:
1. How should statistics, group details, and prompts flow together?
2. Should prompts be inline with group display or separate?
3. How to handle the relationship between preview output and execute output?
4. What UX patterns do similar CLI tools use (rsync, git interactive, etc.)?
5. How does this interact with --verbose, --quiet, --json flags?

This should be a milestone feature, not a quick task.
