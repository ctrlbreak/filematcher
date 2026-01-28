"""Filesystem helper functions for File Matcher.

Provides utilities for detecting file relationships with graceful OSError handling.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def get_device_id(path: str) -> int:
    """Get the device ID for a file's filesystem."""
    return os.stat(path).st_dev


def check_cross_filesystem(master_file: str, duplicates: list[str]) -> set[str]:
    """Return set of duplicates on different filesystems than master."""
    if not duplicates:
        return set()

    try:
        master_device = get_device_id(master_file)
    except OSError as e:
        logger.debug(f"Could not get device ID for master {master_file}: {e}")
        return set(duplicates)

    cross_fs = set()
    for dup in duplicates:
        try:
            if get_device_id(dup) != master_device:
                cross_fs.add(dup)
        except OSError as e:
            logger.debug(f"Could not get device ID for {dup}: {e}")
            cross_fs.add(dup)

    return cross_fs


def is_hardlink_to(file1: str, file2: str) -> bool:
    """Check if two files share the same inode and device (already hardlinked)."""
    try:
        stat1 = os.lstat(file1)
        stat2 = os.lstat(file2)
        return stat1.st_ino == stat2.st_ino and stat1.st_dev == stat2.st_dev
    except OSError as e:
        logger.debug(f"Could not stat files for hardlink check ({file1}, {file2}): {e}")
        return False


def is_symlink_to(duplicate: str, master: str) -> bool:
    """Check if duplicate is a symlink pointing to master."""
    try:
        dup_path = Path(duplicate)
        if not dup_path.is_symlink():
            return False
        resolved_target = dup_path.resolve()
        resolved_master = Path(master).resolve()
        return resolved_target == resolved_master
    except OSError as e:
        logger.debug(f"Could not check symlink status ({duplicate} -> {master}): {e}")
        return False


def filter_hardlinked_duplicates(
    master_file: str, duplicates: list[str]
) -> tuple[list[str], list[str]]:
    """Separate duplicates into (actionable, already_hardlinked)."""
    actionable = []
    hardlinked = []

    for dup in duplicates:
        if is_hardlink_to(master_file, dup):
            hardlinked.append(dup)
        else:
            actionable.append(dup)

    return actionable, hardlinked


def is_in_directory(filepath: str, directory: str) -> bool:
    """Check if a file path is within a directory."""
    try:
        Path(filepath).relative_to(directory)
        return True
    except ValueError:
        return False
