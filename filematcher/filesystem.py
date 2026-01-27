"""Filesystem helper functions for File Matcher.

This module provides utilities for detecting file relationships:
- is_hardlink_to: Check if two files share the same inode
- is_symlink_to: Check if a file is a symlink pointing to another
- check_cross_filesystem: Detect files on different filesystems
- filter_hardlinked_duplicates: Separate already-linked files
- get_device_id: Get filesystem device ID for a path
- is_in_directory: Check path containment

These functions handle OSError gracefully, returning safe defaults
rather than raising exceptions for missing files.
"""
from __future__ import annotations

import os
from pathlib import Path


def get_device_id(path: str) -> int:
    """
    Get the device ID for a file's filesystem.

    Args:
        path: Path to the file

    Returns:
        Device ID (st_dev from os.stat)

    Raises:
        OSError: If file cannot be accessed
    """
    return os.stat(path).st_dev


def check_cross_filesystem(master_file: str, duplicates: list[str]) -> set[str]:
    """
    Check which duplicates are on different filesystems than master.

    Returns set of duplicate paths that cannot be hardlinked to master
    (they're on a different filesystem).

    Args:
        master_file: Path to the master file
        duplicates: List of paths to check

    Returns:
        Set of duplicate paths on different filesystems
    """
    if not duplicates:
        return set()

    try:
        master_device = get_device_id(master_file)
    except OSError:
        # If we can't access master, all duplicates are considered cross-filesystem
        return set(duplicates)

    cross_fs = set()
    for dup in duplicates:
        try:
            if get_device_id(dup) != master_device:
                cross_fs.add(dup)
        except OSError:
            # If we can't access duplicate, treat as cross-filesystem for safety
            cross_fs.add(dup)

    return cross_fs


def is_hardlink_to(file1: str, file2: str) -> bool:
    """
    Check if two files are already hard links to the same data.

    Args:
        file1: Path to first file
        file2: Path to second file

    Returns:
        True if both files share the same inode and device (already linked),
        False otherwise or if either file cannot be accessed
    """
    try:
        stat1 = os.stat(file1)
        stat2 = os.stat(file2)
        return stat1.st_ino == stat2.st_ino and stat1.st_dev == stat2.st_dev
    except OSError:
        return False


def is_symlink_to(duplicate: str, master: str) -> bool:
    """
    Check if a duplicate file is a symlink pointing to the master file.

    Args:
        duplicate: Path to the potential symlink
        master: Path to the master file

    Returns:
        True if duplicate is a symlink whose target resolves to master,
        False otherwise or if either file cannot be accessed
    """
    try:
        dup_path = Path(duplicate)
        if not dup_path.is_symlink():
            return False
        # Resolve both paths to compare actual file locations
        resolved_target = dup_path.resolve()
        resolved_master = Path(master).resolve()
        return resolved_target == resolved_master
    except OSError:
        return False


def filter_hardlinked_duplicates(
    master_file: str, duplicates: list[str]
) -> tuple[list[str], list[str]]:
    """
    Separate duplicates that are already hardlinked to master from those that aren't.

    Files that are already hardlinks to the master share the same inode, meaning
    they occupy no additional disk space. These should not be counted as
    "reclaimable" duplicates.

    Args:
        master_file: Path to the master file
        duplicates: List of paths to potential duplicate files

    Returns:
        Tuple of (actionable_duplicates, already_hardlinked)
        - actionable_duplicates: Duplicates that are not hardlinked (need action)
        - already_hardlinked: Duplicates that are already hardlinked (skip)
    """
    actionable = []
    hardlinked = []

    for dup in duplicates:
        if is_hardlink_to(master_file, dup):
            hardlinked.append(dup)
        else:
            actionable.append(dup)

    return actionable, hardlinked


def is_in_directory(filepath: str, directory: str) -> bool:
    """Check if a file path is within a directory.

    Handles both exact match and subdirectory containment.

    Args:
        filepath: The file path to check
        directory: The directory to check against

    Returns:
        True if filepath is in or under directory
    """
    return filepath.startswith(directory + os.sep) or filepath.startswith(directory)
