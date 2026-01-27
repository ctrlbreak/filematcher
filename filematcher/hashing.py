"""Hashing functions for File Matcher.

Provides content hashing with optional fast mode using sparse sampling for large files.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path


def create_hasher(hash_algorithm: str = 'md5') -> hashlib._Hash:
    """Create a hash object for the specified algorithm ('md5' or 'sha256')."""
    if hash_algorithm == 'md5':
        return hashlib.md5()
    elif hash_algorithm == 'sha256':
        return hashlib.sha256()
    else:
        raise ValueError(f"Unsupported hash algorithm: {hash_algorithm}")


def get_file_hash(filepath: str | Path, hash_algorithm: str = 'md5', fast_mode: bool = False, size_threshold: int = 100*1024*1024) -> str:
    """Calculate hash of file content, using sparse sampling for large files in fast mode."""
    file_size = os.path.getsize(filepath)

    if not fast_mode or file_size < size_threshold:
        h = create_hasher(hash_algorithm)
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                h.update(chunk)
        return h.hexdigest()
    else:
        return get_sparse_hash(filepath, hash_algorithm, file_size)


def get_sparse_hash(filepath: str | Path, hash_algorithm: str = 'md5', file_size: int | None = None, sample_size: int = 1024*1024) -> str:
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
        h.update(f.read(sample_size))

        f.seek(file_size // 2 - sample_size // 2)
        h.update(f.read(sample_size))

        f.seek(file_size // 4 - sample_size // 2)
        h.update(f.read(sample_size))

        f.seek((file_size * 3) // 4 - sample_size // 2)
        h.update(f.read(sample_size))

        f.seek(max(0, file_size - sample_size))
        h.update(f.read(sample_size))

    return h.hexdigest()
