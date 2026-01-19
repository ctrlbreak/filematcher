# Phase 1: Master Directory Foundation - Context

**Gathered:** 2026-01-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can designate one directory as "master" via `--master` flag. Output clearly distinguishes master files from duplicates. This phase establishes the master/duplicate concept without any actions — just identification and labeling.

</domain>

<decisions>
## Implementation Decisions

### Flag behavior
- `--master` takes a path (full or relative): `--master /path/to/dir`
- Paths resolve to canonical form (handles `./`, `../`, symlinks — all resolve to same target)
- Without `--master`, tool runs in report-only mode (current behavior unchanged)
- `--master` is valid standalone (without action flags) — just labels output

### Output labeling
- Group output by role: master file first, duplicates listed after
- Arrow notation for grouped output: `/master/file.txt -> /dup/file.txt, /dup/other.txt`
- Multiple masters (same content in master dir): Warn about it, but continue
- Duplicates within master directory: **Actionable** — oldest file by timestamp becomes the preserved master, newer duplicates treated same as cross-directory duplicates

### Error messages
- Invalid `--master` path: "Master must be one of the compared directories" (short, minimal)
- Same error for non-existent path or wrong directory (no distinction)
- Errors go to stderr
- Exit code: Claude's discretion based on conventions

### Output changes
- `--show-unmatched` / `-u` behavior unchanged — `--master` just adds labels
- `--summary` mode: Add master/duplicate counts ("X master files, Y duplicates")
- `--verbose` mode: Show master/duplicate resolution reasoning (which file chosen and why)
- No duplicates found: Print "No duplicates found", exit 0

### Claude's Discretion
- Exit code for validation failures (convention-based)
- Exact wording of warning for multiple masters
- Verbose output format for resolution reasoning

</decisions>

<specifics>
## Specific Ideas

- Arrow notation was explicitly preferred: `/master/file.txt -> /dup/file.txt, /dup/other.txt`
- Duplicates within master directory should use timestamp to pick which becomes the true master (oldest = master)
- Error messages should be minimal, not hand-holding

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-master-directory-foundation*
*Context gathered: 2026-01-19*
