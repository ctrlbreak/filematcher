# Technology Stack: File Deduplication Operations

**Project:** File Matcher - Deduplication Actions Milestone
**Researched:** 2026-01-19
**Constraint:** Pure Python standard library only (no external dependencies)

## Recommended Stack for Deduplication Operations

### Link Creation

| Module | Function | Purpose | Why Recommended |
|--------|----------|---------|-----------------|
| `os` | `os.link(src, dst)` | Create hard links | Standard POSIX call, Python 3.9+. Creates additional filesystem reference to same inode. |
| `os` | `os.symlink(src, dst)` | Create symbolic links | Standard POSIX call. Creates pointer file to target path. |
| `pathlib` | `Path.symlink_to(target)` | Create symbolic links (OOP) | Available Python 3.9+. Cleaner syntax. |

**Recommendation:** Use `os.link()` and `os.symlink()` for compatibility with Python 3.9 minimum.

### File Deletion

| Module | Function | Purpose | Why Recommended |
|--------|----------|---------|-----------------|
| `pathlib` | `Path.unlink(missing_ok=False)` | Delete a file (OOP) | `missing_ok` parameter handles race conditions. |

**Recommendation:** Use `Path.unlink()` for consistency with existing pathlib usage.

### Atomic Operations

| Module | Function | Purpose | Why Recommended |
|--------|----------|---------|-----------------|
| `os` | `os.replace(src, dst)` | Atomic file replacement | POSIX atomic rename. Cross-platform. |

**Recommendation:** Use `os.replace()` for any operation that replaces an existing file.

### Link Verification

| Module | Function | Purpose |
|--------|----------|---------|
| `os.path` | `os.path.islink(path)` | Check if path is symlink |
| `os.path` | `os.path.samefile(p1, p2)` | Check if same inode (hard link verification) |

## Cross-Platform Considerations

### Hard Links

| Platform | Support | Limitations |
|----------|---------|-------------|
| Linux/macOS | Full | Cannot span filesystems |
| Windows | Partial | Requires NTFS. May require admin privileges. |

**Error Handling:**
```python
import errno
try:
    os.link(master_path, duplicate_path)
except OSError as e:
    if e.errno == errno.EXDEV:  # Cross-device link
        # Fall back or warn user
```

### Symbolic Links

| Platform | Support | Limitations |
|----------|---------|-------------|
| Linux/macOS | Full | No restrictions |
| Windows | Partial | Requires privileges or Developer Mode |

## What NOT to Use

| Function | Why Avoid |
|----------|-----------|
| `shutil.copy*` | Duplicates data instead of linking |
| `os.rename()` | Not atomic on Windows when destination exists |
| `Path.hardlink_to()` | Added Python 3.10; project supports 3.9+ |

## Recommended Import Block

```python
import errno  # For cross-platform error code handling
import json   # For structured change logging (optional)
from datetime import datetime  # For change log timestamps
```

No new external dependencies required.

---

*Stack research: 2026-01-19*
