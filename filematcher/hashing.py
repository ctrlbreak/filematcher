"""Hashing functions for File Matcher.

Provides content hashing with optional fast mode using sparse sampling for large files.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

# Size constants
LARGE_FILE_THRESHOLD = 100 * 1024 * 1024  # 100 MB - files larger than this use sparse hashing in fast mode
SPARSE_SAMPLE_SIZE = 1024 * 1024  # 1 MB - size of each sample point in sparse hashing
READ_CHUNK_SIZE = 4096  # 4 KB - chunk size for reading files during full hashing


def create_hasher(hash_algorithm: str = 'md5') -> hashlib._Hash:
    """Create a hash object for the specified algorithm ('md5' or 'sha256')."""
    if hash_algorithm == 'md5':
        return hashlib.md5()
    elif hash_algorithm == 'sha256':
        return hashlib.sha256()
    else:
        raise ValueError(f"Unsupported hash algorithm: {hash_algorithm}")


def get_file_hash(filepath: str | Path, hash_algorithm: str = 'md5', fast_mode: bool = False, size_threshold: int = LARGE_FILE_THRESHOLD) -> str:
    """Calculate hash of file content, using sparse sampling for large files in fast mode."""
    file_size = os.path.getsize(filepath)

    if not fast_mode or file_size < size_threshold:
        h = create_hasher(hash_algorithm)
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(READ_CHUNK_SIZE), b''):
                h.update(chunk)
        return h.hexdigest()
    else:
        return get_sparse_hash(filepath, hash_algorithm, file_size)


def get_sparse_hash(filepath: str | Path, hash_algorithm: str = 'md5', file_size: int | None = None, sample_size: int = SPARSE_SAMPLE_SIZE) -> str:
    """Create hash from sparse sampling (start, 1/4, middle, 3/4, end) of a large file."""
    h = create_hasher(hash_algorithm)

    if file_size is None:
        file_size = os.path.getsize(filepath)

    h.update(str(file_size).encode('utf-8'))

    if file_size <= 3 * sample_size:
        with open(filepath, 'rb') as f:
            h.update(f.read())
        return h.hexdigest()

    with open(filepath, 'rb') as f:
        # Sequential seek order for I/O optimization: start → 1/4 → middle → 3/4 → end
        h.update(f.read(sample_size))

        f.seek(file_size // 4 - sample_size // 2)
        h.update(f.read(sample_size))

        f.seek(file_size // 2 - sample_size // 2)
        h.update(f.read(sample_size))

        f.seek((file_size * 3) // 4 - sample_size // 2)
        h.update(f.read(sample_size))

        f.seek(max(0, file_size - sample_size))
        h.update(f.read(sample_size))

    return h.hexdigest()
