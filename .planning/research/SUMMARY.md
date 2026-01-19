# Research Summary: File Deduplication Actions

**Project:** File Matcher - Deduplication Actions Milestone
**Completed:** 2026-01-19

## Key Findings

### Stack

**Core APIs (Python standard library):**
- `os.link(src, dst)` — Create hard links
- `os.symlink(src, dst)` — Create symbolic links
- `Path.unlink()` — Delete files
- `os.replace()` — Atomic file replacement (safe)
- `os.path.samefile()` — Verify hard links share inode

**No external dependencies required.** All operations available in Python 3.9+.

### Table Stakes Features

1. **Dry-run mode** — Non-negotiable safety feature
2. **Delete action** — Remove duplicates, keep master
3. **Hard link action** — Replace duplicates with hard links
4. **Symbolic link action** — Alternative to hard links
5. **Change logging** — Audit trail of all modifications
6. **Summary statistics** — Space saved feedback

### Watch Out For

| Pitfall | Severity | Mitigation |
|---------|----------|------------|
| Race conditions (file changes between scan and action) | CRITICAL | Re-verify before each action |
| Deleting master instead of duplicate | CRITICAL | Clear naming, never modify master dir |
| Cross-filesystem hard links | HIGH | Catch EXDEV error, suggest symlink |
| Windows symlink privileges | MEDIUM | Detect and warn, prefer hard links |
| Circular symlinks during scan | HIGH | Don't follow symlinks in traversal |

### Recommended Architecture

```
find_matching_files() [existing]
         |
         v
identify_duplicates() [new]
         |
         v
plan_actions() [new]
         |
         v
execute_plan() [new - dry-run/interactive/auto]
         |
         v
log_changes() [new]
```

**Build order:**
1. Data structures and identify_duplicates
2. Action planning and CLI args
3. Dry-run execution (safe first)
4. Action implementations (hardlink, symlink, delete)
5. Auto execution
6. Interactive mode
7. Change logging

### CLI Pattern

```bash
filematcher dir1 dir2                           # Report only (existing)
filematcher dir1 dir2 --master dir1 --dry-run   # Preview changes
filematcher dir1 dir2 --master dir1 --hardlink  # Execute hard linking
filematcher dir1 dir2 --master dir1 --delete    # Execute deletion
filematcher dir1 dir2 --master dir1 --symlink   # Execute symlinking
```

**Execution modes:**
- `--dry-run` — Show what would happen (default when action specified)
- `--interactive` — Prompt for each change
- `--auto` — Execute without prompts

## Research Files

| File | Purpose |
|------|---------|
| STACK.md | Standard library APIs for link/delete operations |
| FEATURES.md | Table stakes vs differentiators vs anti-features |
| ARCHITECTURE.md | How to integrate with existing codebase |
| PITFALLS.md | Common mistakes and prevention strategies |

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Python standard library APIs | HIGH | Stable, well-documented |
| Cross-platform behavior | MEDIUM | Windows symlinks need testing |
| Feature patterns | MEDIUM | Based on fdupes/jdupes/rdfind patterns |
| Architecture recommendations | HIGH | Follows existing codebase patterns |

---

*Research synthesis: 2026-01-19*
