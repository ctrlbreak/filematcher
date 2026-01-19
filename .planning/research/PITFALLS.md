# Pitfalls: File Deduplication Operations

**Domain:** File deduplication with hard links, symlinks, and deletion
**Researched:** 2026-01-19

## Critical Pitfalls

### 1. Data Loss from Race Conditions

**What goes wrong:** File changes between scan and action execution. You delete a file thinking it's a duplicate, but the master was modified or deleted.

**Warning signs:**
- Long time between scan completion and action execution
- Multi-user environments
- Automated processes modifying same directories

**Prevention:**
- Re-verify master file exists before each action
- Optionally re-verify content hash matches before destructive action
- Use atomic operations where possible

**Phase to address:** Action Implementation (Phase 4)

### 2. Cross-Filesystem Hard Link Failure

**What goes wrong:** `os.link()` fails with `EXDEV` when source and target are on different filesystems.

**Warning signs:**
- Comparing directories on different mount points
- Network drives vs local drives
- Docker volumes

**Prevention:**
```python
try:
    os.link(target, source)
except OSError as e:
    if e.errno == errno.EXDEV:
        logger.error(f"Cannot create hard link across filesystems: {source}")
        # Offer symlink as fallback or skip
```

**Phase to address:** Action Implementation (Phase 4)

### 3. Symbolic Link Privilege Issues on Windows

**What goes wrong:** `os.symlink()` fails on Windows without admin privileges or Developer Mode.

**Warning signs:**
- Windows users getting "A required privilege is not held by the client"
- Tests passing on Unix but failing on Windows

**Prevention:**
- Detect Windows and warn about privilege requirements
- Fall back to hard links if symlinks fail
- Document Windows requirements

**Phase to address:** Action Implementation (Phase 4)

### 4. Deleting the Wrong File (Master vs Duplicate)

**What goes wrong:** Logic error causes master file to be deleted instead of duplicate.

**Warning signs:**
- Confusing variable names (which is source, which is target?)
- Complex logic for determining master

**Prevention:**
- Clear naming: `master_file` vs `duplicate_file`
- Never call delete on any file in master directory
- Add assertion: `assert not str(file_to_delete).startswith(str(master_dir))`
- Test with distinct content in each directory

**Phase to address:** Planning (Phase 2), Testing throughout

### 5. Infinite Loops from Circular Symlinks

**What goes wrong:** Directory traversal follows symlinks, encounters a circular link, hangs or crashes.

**Warning signs:**
- Hanging during directory scan
- Stack overflow errors
- Unexpectedly large file counts

**Prevention:**
- Don't follow symlinks during scan (or track visited inodes)
- Set maximum recursion depth
- Current codebase uses `rglob('*')` which can follow symlinks

**Phase to address:** Should be addressed before action features (Phase 0/Foundation)

### 6. Permission Errors Stopping All Processing

**What goes wrong:** Single unreadable file causes entire operation to fail.

**Warning signs:**
- Partial results with no indication of skipped files
- Different results when run as different users

**Prevention:**
- Catch permission errors per-file, log and continue
- Existing codebase handles this for reading; extend to actions
- Report summary of skipped files at end

**Phase to address:** Action Implementation (Phase 4)

### 7. Lost Filename Information

**What goes wrong:** After creating link, you can't tell what the original filename was.

**Warning signs:**
- Users asking "what was this file called before?"
- No audit trail of changes

**Prevention:**
- Log format includes: timestamp, action, original_path, target_path
- Change log is machine-parseable for potential undo

**Phase to address:** Change Logging (Phase 7)

### 8. Space Not Actually Freed (Hard Links)

**What goes wrong:** User expects disk space to be freed after "deleting" duplicates via hard links, but hard links don't free space until all links are removed.

**Warning signs:**
- User complaints about disk space not changing
- Confusion about hard link semantics

**Prevention:**
- Clear documentation: "Hard links save space for future writes, not immediate space recovery"
- Distinguish between "delete" action (frees space) and "hardlink" action (deduplicates)
- Show different messaging for each action type

**Phase to address:** Dry-run output (Phase 3), Documentation

### 9. Broken Symlinks After Moving Directories

**What goes wrong:** Symlinks use absolute paths. If master directory is moved, all symlinks break.

**Warning signs:**
- "File not found" errors after reorganizing files
- Symlinks pointing to non-existent paths

**Prevention:**
- Offer relative symlink option (`--relative-links`)
- Default to absolute but document the tradeoff
- Relative: portable but fragile if link moves
- Absolute: stable reference but breaks if target moves

**Phase to address:** Action Implementation (Phase 4), as option

### 10. Testing with Production Data

**What goes wrong:** Destructive operations tested against real user data.

**Warning signs:**
- No isolated test environment
- Tests that require specific file structures

**Prevention:**
- All tests use temporary directories (existing pattern in test_base.py)
- Never hardcode paths to real directories
- Dry-run mode tested extensively before auto mode

**Phase to address:** All phases - testing discipline

## Platform-Specific Pitfalls

### macOS

| Issue | Impact | Mitigation |
|-------|--------|------------|
| Case-insensitive filesystem | May treat `File.txt` and `file.txt` as same | Use `os.path.samefile()` for comparison |
| Extended attributes | Hard links share xattrs | Usually fine; document if relevant |

### Windows

| Issue | Impact | Mitigation |
|-------|--------|------------|
| Symlink privileges | Requires admin or Developer Mode | Detect and warn; prefer hard links |
| File locking | Can't delete open files | Catch PermissionError, report |
| Path length limits | 260 char limit without opt-in | Use `\\?\` prefix for long paths |

### Linux

| Issue | Impact | Mitigation |
|-------|--------|------------|
| Cross-filesystem | Hard links fail across mount points | Detect EXDEV error, suggest symlink |
| Filesystem limits | Some filesystems limit hard links per inode | Rare; catch error if it occurs |

## Severity Matrix

| Pitfall | Severity | Likelihood | Detection Difficulty |
|---------|----------|------------|---------------------|
| Data loss from race conditions | CRITICAL | Medium | Hard |
| Deleting wrong file | CRITICAL | Low | Medium |
| Cross-filesystem hard link | HIGH | Medium | Easy |
| Infinite symlink loops | HIGH | Low | Medium |
| Windows symlink privileges | MEDIUM | Medium | Easy |
| Space not freed (hard links) | LOW | High | Easy (just confusion) |

---

*Pitfalls research: 2026-01-19*
