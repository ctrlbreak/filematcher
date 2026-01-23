---
phase: 07-output-unification
plan: 01
subsystem: cli
tags: [output, stderr, quiet, unix-convention]
dependency_graph:
  requires: [06-json-output]
  provides: [stderr-routing, quiet-flag]
  affects: [07-02, 07-03]
tech_stack:
  added: []
  patterns: [unix-stream-convention]
key_files:
  created: []
  modified: [file_matcher.py, tests/test_cli.py]
decisions:
  - key: stderr-for-all-modes
    choice: "Route logger to stderr in all modes (text and JSON)"
    rationale: "Unix convention: status/progress to stderr, data to stdout"
  - key: quiet-log-level
    choice: "Use logging.ERROR level for --quiet"
    rationale: "Suppresses INFO/DEBUG but allows errors through"
metrics:
  duration: 5 min
  tasks: 3/3
  completed: 2026-01-23
---

# Phase 7 Plan 01: Stream Separation and Quiet Flag Summary

**One-liner:** Stderr routing for all modes and --quiet flag for clean piping

## What Was Built

### Stream Separation (Task 1)
Changed logger output to always use stderr, not just in JSON mode. Previously:
- JSON mode: logger -> stderr (correct)
- Text mode: logger -> stdout (mixed with data)

Now all modes send logger output to stderr, enabling clean piping:
```bash
filematcher dir1 dir2 | grep pattern       # Works - stdout has data only
filematcher dir1 dir2 2>/dev/null | wc -l  # Count data lines only
```

### Quiet Flag (Task 2)
Added `--quiet/-q` flag that sets log level to ERROR:
- Suppresses: "Using MD5...", "Indexing...", "Fast mode...", verbose progress
- Preserves: Error messages, data output (match groups, statistics)
- Precedence: --quiet overrides --verbose

```bash
filematcher dir1 dir2 --quiet              # Silent operation, data only
filematcher nonexistent nothere --quiet    # Errors still display
```

### Test Updates (Task 3)
Updated 3 CLI tests to check stderr for logger messages:
- `test_hash_algorithm_option` - checks stderr for "Using MD5..."
- `test_fast_mode_option` - checks stderr for "Fast mode enabled"
- `test_verbose_mode_option` - checks stderr for verbose progress

Added `run_main_capture_all()` helper that returns (stdout, stderr) tuple.

## Commits

| Commit | Type | Description |
|--------|------|-------------|
| 9ae195d | feat | Route logger to stderr for all modes |
| f13cfec | feat | Add --quiet/-q flag to suppress progress |
| ace98a1 | test | Update CLI tests for stderr routing |

## Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| stderr for all modes | Always use sys.stderr | Unix convention for status/data separation |
| --quiet log level | logging.ERROR | Only errors get through; suppresses INFO/DEBUG |
| --quiet precedence | Overrides --verbose | Quiet is explicit user intent for silence |

## Files Changed

### Modified
- `file_matcher.py` - stderr routing, --quiet flag argument and log level logic
- `tests/test_cli.py` - Updated 3 tests, added `run_main_capture_all()` helper

## Deviations from Plan

None - plan executed exactly as written.

## Verification Results

1. **Stream separation**: stdout shows data only, stderr shows status
2. **--quiet flag**: Suppresses progress, errors still display
3. **Tests**: All 154 tests pass
4. **JSON mode**: Unchanged behavior (already used stderr)

## Next Phase Readiness

**Ready for 07-02**: Unified header system with banner/status support
- Stream separation provides foundation for headers going to stderr
- --quiet flag will be extended to suppress headers in 07-02
