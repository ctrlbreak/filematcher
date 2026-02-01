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

- Size pre-filtering - Skip hashing files with unique sizes (see research below)
- Partial hash - Hash first 4KB before full hash (see research below)
- `--verify` - Verify existing hardlinks still point to same content
- `--parallel N` - Multi-threaded hashing (note: may hurt performance on HDDs due to seek overhead)

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

## Research: Performance Optimizations

*Researched 2026-02-01*

### Current Implementation Status

| Feature | Status | Location |
|---------|--------|----------|
| Size pre-filtering | **No** | `index_directory()` hashes every file |
| Partial hash | **No** | Goes straight to full hash |
| Sparse sampling (fast mode) | **Yes** | For files >100MB, samples 5×1MB chunks |
| Early hardlink detection | **No** | Doesn't check inodes before hashing |

Current flow in `directory.py:53-94`:
```python
for each file in directory:
    hash = get_file_hash(file)  # hashes EVERYTHING
    group_by_hash[hash].append(file)
```

The sparse hash in `hashing.py:42-72` is good but only activates for >100MB files in fast mode.

### Optimization 1: Size Pre-filtering (Biggest Win)

Files with unique sizes cannot be duplicates. Skip hashing them entirely.

**Proposed approach:**
```python
# Phase 1: Collect sizes (very fast - just stat calls)
dir1_sizes = {path: size for path, size in walk(dir1)}
dir2_sizes = {path: size for path, size in walk(dir2)}

# Phase 2: Find common sizes across both directories
common_sizes = set(dir1_sizes.values()) & set(dir2_sizes.values())

# Phase 3: Only hash files with sizes that exist in both dirs
for path, size in dir1_sizes.items():
    if size in common_sizes:
        hash_file(path)
```

**Impact:** In typical directories, 50-80% of files have unique sizes → zero hashing needed.

**Implementation notes:**
- Requires refactoring `index_directory()` to accept size filter
- Or refactor `find_matching_files()` to do cross-directory size analysis first
- ~30-50 lines of code change

### Optimization 2: Partial Hash (Second Win)

For files with matching sizes, hash first 4KB before computing full hash.

**Proposed approach:**
```python
partial_hash = hash(first_4KB)
if partial_hashes_match_across_dirs:
    full_hash = hash(entire_file)
else:
    skip  # different content confirmed with minimal I/O
```

**Impact:** Rules out most "same size, different content" files with minimal I/O.

**Implementation notes:**
- Add `get_partial_hash()` function to `hashing.py`
- Two-phase comparison: partial hash first, full hash only on partial match
- More complex control flow but significant I/O savings

### Optimization 3: Early Hardlink Detection

Before hashing, check if files are already hardlinked to each other.

**Proposed approach:**
```python
if stat(file1).st_ino == stat(file2).st_ino and stat(file1).st_dev == stat(file2).st_dev:
    skip  # already hardlinked, no action needed
```

**Impact:** Avoids re-hashing files already processed in previous runs.

**Implementation notes:**
- Already partially implemented in `is_hardlink_to()` in `filesystem.py`
- Need to call earlier in the pipeline, before hashing

### Why Not Parallel Hashing?

Parallel hashing (`--parallel N`) can actually **hurt** performance on spinning HDDs:
- Random seeks between files kill sequential read performance
- HDDs are optimized for sequential access, not parallel random access
- Only beneficial on SSDs or when files are on different physical disks

### Recommended Priority

1. **Size pre-filtering** - Biggest win, moderate refactoring
2. **Cache** (see above) - Huge win on re-runs, already researched
3. **Partial hash** - Good win, more complex implementation
4. **Early hardlink detection** - Minor win, easy implementation

---
*Created: 2026-02-01*
