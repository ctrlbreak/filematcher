---
created: 2026-01-27T00:28
title: Split Python code into multiple modules
area: architecture
files:
  - file_matcher.py
---

## Problem

The entire application is implemented in a single `file_matcher.py` file. While this was convenient during initial development, the file has grown to include:

- Color system (ColorMode, ColorConfig, color helpers)
- Output formatters (ActionFormatter hierarchy)
- Hashing functions (get_file_hash, get_sparse_hash)
- Directory operations (index_directory, find_matching_files)
- Action execution (safe_replace_with_link, execute_action, execute_all_actions)
- Filesystem helpers (is_hardlink_to, is_symlink_to, check_cross_filesystem)
- Audit logging (create_audit_logger, log_operation)
- CLI (argument parsing, main)

This violates Python best practices for module organization and makes the codebase harder to navigate, test, and maintain.

## Solution

Split into a package structure:

```
filematcher/
  __init__.py      # Public API exports
  __main__.py      # Entry point for `python -m filematcher`
  cli.py           # Argument parsing, main()
  hashing.py       # get_file_hash, get_sparse_hash, create_hasher
  directory.py     # index_directory, find_matching_files
  actions.py       # Action execution, safe_replace_with_link
  filesystem.py    # is_hardlink_to, is_symlink_to, cross-fs detection
  logging.py       # Audit logging functions
  output/
    __init__.py
    colors.py      # ColorMode, ColorConfig, color helpers
    formatters.py  # ActionFormatter hierarchy
```

Key considerations:
- Maintain backward compatibility for `python file_matcher.py` invocation
- Keep single-file install option (consider keeping `file_matcher.py` as thin wrapper)
- Update imports in test suite
- Preserve current API for external use
