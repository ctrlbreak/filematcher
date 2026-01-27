"""Directory indexing and file matching operations for File Matcher."""

from __future__ import annotations

import logging
import os
import shutil
import sys
from collections import defaultdict
from pathlib import Path

from filematcher.hashing import get_file_hash
from filematcher.actions import format_file_size
from filematcher.filesystem import is_in_directory

logger = logging.getLogger(__name__)


def select_oldest(file_paths: list[str]) -> tuple[str, list[str]]:
    """Select the oldest file by mtime and return it with remaining files."""
    oldest = min(file_paths, key=lambda p: os.path.getmtime(p))
    others = [f for f in file_paths if f != oldest]
    return oldest, others


def select_master_file(file_paths: list[str], master_dir: Path | None) -> tuple[str, list[str], str]:
    """Select master file from duplicates, preferring files in master_dir, then oldest by mtime."""
    if not file_paths:
        raise ValueError("file_paths cannot be empty")

    if len(file_paths) == 1:
        return file_paths[0], [], "only file"

    if master_dir:
        master_dir_str = str(master_dir)
        master_files = [f for f in file_paths if is_in_directory(f, master_dir_str)]
        other_files = [f for f in file_paths if f not in master_files]

        if master_files:
            if len(master_files) == 1:
                return master_files[0], other_files, "only file in master directory"
            else:
                oldest_master, other_master_files = select_oldest(master_files)
                return oldest_master, other_master_files + other_files, "oldest in master directory"
        else:
            oldest, duplicates = select_oldest(file_paths)
            return oldest, duplicates, "oldest file (none in master directory)"
    else:
        oldest, duplicates = select_oldest(file_paths)
        return oldest, duplicates, "oldest file"


def index_directory(directory: str | Path, hash_algorithm: str = 'md5', fast_mode: bool = False, verbose: bool = False) -> dict[str, list[str]]:
    """Recursively index all files in a directory. Returns dict mapping hash -> list of paths."""
    hash_to_files = defaultdict(list)
    directory_path = Path(directory)

    if verbose:
        total_files = sum(1 for filepath in directory_path.rglob('*') if filepath.is_file())
        processed_files = 0
        logger.debug(f"Found {total_files} files to process in {directory}")
        is_tty = hasattr(sys.stderr, 'isatty') and sys.stderr.isatty()

    for filepath in directory_path.rglob('*'):
        if filepath.is_file():
            try:
                if verbose:
                    processed_files += 1
                    file_size = os.path.getsize(filepath)
                    size_str = format_file_size(file_size)
                    if is_tty:
                        progress_line = f"\r[{processed_files}/{total_files}] Processing {filepath.name} ({size_str})"
                        term_width = shutil.get_terminal_size().columns
                        if len(progress_line) > term_width:
                            progress_line = progress_line[:term_width-3] + "..."
                        sys.stderr.write(progress_line.ljust(term_width) + '\r')
                        sys.stderr.flush()
                    else:
                        logger.debug(f"[{processed_files}/{total_files}] Processing {filepath.name} ({size_str})")

                file_hash = get_file_hash(filepath, hash_algorithm, fast_mode)
                hash_to_files[file_hash].append(str(filepath.resolve()))
            except (PermissionError, OSError) as e:
                logger.error(f"Error processing {filepath}: {e}")
                if verbose:
                    processed_files += 1

    if verbose:
        if is_tty:
            sys.stderr.write('\r' + ' ' * shutil.get_terminal_size().columns + '\r')
            sys.stderr.flush()
        logger.debug(f"Completed indexing {directory}: {len(hash_to_files)} unique file contents found")

    return hash_to_files


def find_matching_files(dir1: str | Path, dir2: str | Path, hash_algorithm: str = 'md5', fast_mode: bool = False, verbose: bool = False, different_names_only: bool = False) -> tuple[dict[str, tuple[list[str], list[str]]], list[str], list[str]]:
    """Find files with identical content across two directories. Returns (matches, unmatched1, unmatched2)."""
    if not verbose:
        logger.info(f"Indexing directory: {dir1}")
    hash_to_files1 = index_directory(dir1, hash_algorithm, fast_mode, verbose)

    if not verbose:
        logger.info(f"Indexing directory: {dir2}")
    hash_to_files2 = index_directory(dir2, hash_algorithm, fast_mode, verbose)

    common_hashes = set(hash_to_files1.keys()) & set(hash_to_files2.keys())
    unique_hashes1 = set(hash_to_files1.keys()) - common_hashes
    unique_hashes2 = set(hash_to_files2.keys()) - common_hashes

    matches = {}
    for file_hash in common_hashes:
        files1 = hash_to_files1[file_hash]
        files2 = hash_to_files2[file_hash]

        if different_names_only:
            names1 = {os.path.basename(f) for f in files1}
            names2 = {os.path.basename(f) for f in files2}
            if names1 == names2 and len(names1) == 1:
                continue

        matches[file_hash] = (files1, files2)

    unmatched1 = []
    for file_hash in unique_hashes1:
        unmatched1.extend(hash_to_files1[file_hash])

    unmatched2 = []
    for file_hash in unique_hashes2:
        unmatched2.extend(hash_to_files2[file_hash])

    return matches, unmatched1, unmatched2
