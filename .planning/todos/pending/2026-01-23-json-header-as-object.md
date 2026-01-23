---
created: 2026-01-23T17:53
title: Update JSON output header to object format
area: cli
files:
  - file_matcher.py:JsonActionFormatter
---

## Problem

The JSON output currently puts header information as plain text strings. This should be structured as an object with typed fields for better machine parsing.

Currently the header info (mode, directories, timestamp, etc.) may be mixed with other output. Moving this into a dedicated header object would provide cleaner structure for JSON consumers.

## Solution

TBD - Review current JsonActionFormatter and JsonCompareFormatter output structure. Consider adding a `header` object that contains:
- mode (compare/preview/execute)
- timestamp
- directories
- action type
- any other metadata currently output as strings
