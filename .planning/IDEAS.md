# Feature Ideas

Potential features for future milestones. Not prioritized or committed.

## Likely Next

These features are researched and ready to implement:

- `--include` / `--exclude` - Glob patterns for file filtering (e.g., `--include "*.mkv"`)
- `--cache` - Persist hashes to avoid re-indexing unchanged files (see research below)

## Filtering & Selection

- `--min-size` / `--max-size` - Only process files within size range
- `--newer-than` / `--older-than` - Date-based filtering
- `--max-depth` - Limit recursion depth

## Actions & Output

- `--action move` - Move duplicates to a trash/archive directory instead of delete
- `--action copy` - Copy master files to target directory (inverse of current flow)
- `--report html` - Generate HTML report with file previews
- `--export csv` - Export results to CSV for spreadsheet analysis

## Performance

- `--parallel N` - Multi-threaded hashing for faster indexing
- `--verify` - Verify existing hardlinks still point to same content

## Multi-Directory

- Support 3+ directories (one master, multiple duplicate sources)
- `--recursive-master` - Find best master from any directory, not just dir1

## Usability

- `--config FILE` - Load options from config file
- `--undo LOG` - Reverse operations using audit log (where possible)
- `--watch` - Monitor directories and report new duplicates

## Analysis

- `--duplicates-only` - Show files that exist in both dirs (no unmatched)
- `--stats` - Detailed statistics (duplicates by extension, size distribution)

---

## Research: Hash Caching

*Researched 2026-02-01*

### How Existing Tools Do It

| Tool | Cache Storage | Invalidation | Notes |
|------|---------------|--------------|-------|
| **jdupes** | Text file | Path-based lookup | Still "under development"; path normalization quirks |
| **rmlint** | Extended attributes (xattr) | mtime | Cache travels with file; not all FS support xattrs |
| **fclones** | Database in ~/.cache | mtime + size + inode | Uses inode as key (survives renames) |
| **fdupes** | None | N/A | Third-party SQLite wrappers exist |

### Recommended Simple Approach

**Validation tuple:** `(size, mtime_ns)` — matches rsync's proven approach
- Skip inode tracking (accept re-hash on file moves)
- Use nanosecond mtime where available (`os.stat().st_mtime_ns`)
- Any mismatch → re-hash (conservative = safe)

**Storage:** Start with JSON
- Location: `~/.cache/filematcher/hashcache.json` (XDG-compliant)
- Human-readable for debugging
- Migrate to SQLite only if >10K entries becomes slow

**Minimal schema:**
```json
{
  "version": 1,
  "entries": {
    "/absolute/path/to/file": {
      "hash": "abc123...",
      "size": 1048576,
      "mtime_ns": 1706745600123456789
    }
  }
}
```

### Edge Cases & Risks

| Risk | Mitigation |
|------|------------|
| mtime spoofed with `touch` | Also check size; accept small risk |
| NFS clock skew | Check size too; NTP sync recommended |
| File moved | Re-hash (acceptable for simplicity) |
| mmap'd files | Accept small race window |
| Cache grows stale | Lazy cleanup on access; optional `--clear-cache` |

### CLI Options (minimal)

```
--cache              Enable hash caching (default location)
--cache-file PATH    Use specific cache file
--no-cache           Disable caching for this run
--clear-cache        Purge cache before running
```

### Key Insight

From rmlint: *"As a security measure, replay will ignore files whose mtime changed."*

The cache is an **optimization, not a guarantee**. When in doubt, re-hash. This keeps implementation simple while maintaining correctness.

### References

- jdupes: https://manpages.debian.org/testing/jdupes/jdupes.1.en.html
- rmlint: https://rmlint.readthedocs.io/en/latest/rmlint.1.html
- fclones: https://github.com/pkolaczk/fclones
- mtime analysis: https://apenwarr.ca/log/20181113
- XDG spec: https://wiki.archlinux.org/title/XDG_Base_Directory

---
*Created: 2026-02-01*
