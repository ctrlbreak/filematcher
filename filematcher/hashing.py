"""Hashing functions for File Matcher.

This module provides content hashing functions for file comparison:
- create_hasher: Factory for hash objects (MD5, SHA-256)
- get_file_hash: Calculate file hash with optional fast mode for large files
- get_sparse_hash: Sparse sampling hash for very large files

The hashing module is a leaf module with no internal filematcher dependencies,
making it suitable for import anywhere in the package.

Fast Mode:
For files larger than size_threshold (default 100MB), fast mode uses sparse
sampling instead of hashing the entire file. This provides faster comparison
at the cost of a small chance of hash collision for modified files.

Sparse sampling reads from 5 positions:
- Start of file
- 1/4 mark
- Middle (1/2 mark)
- 3/4 mark
- End of file

Plus the exact file size is included in the hash to catch size differences.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path


def create_hasher(hash_algorithm: str = 'md5') -> hashlib._Hash:
    """Create a hash object for the specified algorithm.

    Args:
        hash_algorithm: 'md5' or 'sha256'

    Returns:
        Hash object ready for update() calls

    Raises:
        ValueError: If hash_algorithm is not supported
    """
    if hash_algorithm == 'md5':
        return hashlib.md5()
    elif hash_algorithm == 'sha256':
        return hashlib.sha256()
    else:
        raise ValueError(f"Unsupported hash algorithm: {hash_algorithm}")


def get_file_hash(filepath: str | Path, hash_algorithm: str = 'md5', fast_mode: bool = False, size_threshold: int = 100*1024*1024) -> str:
    """
    Calculate hash of file content using the specified algorithm.

    Args:
        filepath: Path to the file to hash
        hash_algorithm: Hashing algorithm to use ('md5' or 'sha256')
        fast_mode: If True, use faster methods for large files
        size_threshold: Size threshold (in bytes) for when to apply fast methods

    Returns:
        Hexadecimal digest of the hash
    """
    file_size = os.path.getsize(filepath)

    # For small files or when fast_mode is disabled, use the standard method
    if not fast_mode or file_size < size_threshold:
        h = create_hasher(hash_algorithm)

        with open(filepath, 'rb') as f:
            # Read file in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(4096), b''):
                h.update(chunk)
        return h.hexdigest()

    # Fast mode for large files
    else:
        # Use sparse block hashing for large files in fast mode
        return get_sparse_hash(filepath, hash_algorithm, file_size)


def get_sparse_hash(filepath: str | Path, hash_algorithm: str = 'md5', file_size: int | None = None, sample_size: int = 1024*1024) -> str:
    """
    Create a hash based on sparse sampling of a large file.

    Args:
        filepath: Path to the file to hash
        hash_algorithm: Hashing algorithm to use
        file_size: Size of file in bytes (will be calculated if None)
        sample_size: Size of samples to take at each position

    Returns:
        Hexadecimal digest of the hash
    """
    h = create_hasher(hash_algorithm)

    if file_size is None:
        file_size = os.path.getsize(filepath)

    # First include the exact file size in the hash
    h.update(str(file_size).encode('utf-8'))

    # For very small files, hash the whole thing
    if file_size <= 3 * sample_size:
        with open(filepath, 'rb') as f:
            h.update(f.read())
        return h.hexdigest()

    with open(filepath, 'rb') as f:
        # Sample the beginning
        start_data = f.read(sample_size)
        h.update(start_data)

        # Sample from the middle
        middle_pos = file_size // 2 - sample_size // 2
        f.seek(middle_pos)
        middle_data = f.read(sample_size)
        h.update(middle_data)

        # Sample from near 1/4 mark
        quarter_pos = file_size // 4 - sample_size // 2
        f.seek(quarter_pos)
        quarter_data = f.read(sample_size)
        h.update(quarter_data)

        # Sample from near 3/4 mark
        three_quarter_pos = (file_size * 3) // 4 - sample_size // 2
        f.seek(three_quarter_pos)
        three_quarter_data = f.read(sample_size)
        h.update(three_quarter_data)

        # Sample the end
        f.seek(max(0, file_size - sample_size))
        end_data = f.read(sample_size)
        h.update(end_data)

    return h.hexdigest()
