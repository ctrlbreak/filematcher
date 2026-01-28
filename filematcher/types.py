"""Type definitions for File Matcher.

Provides structured types for clarity and type safety.
"""

from __future__ import annotations

from typing import NamedTuple


class DuplicateGroup(NamedTuple):
    """A group of files with identical content."""
    master_file: str          # The file to keep (from master directory)
    duplicates: list[str]     # Files to act on (replace/delete)
    reason: str               # Why these were grouped (e.g., "content match")
    file_hash: str            # Hash of the shared content


class FailedOperation(NamedTuple):
    """Record of a failed file operation."""
    file_path: str            # Path of the file that failed
    error_message: str        # Description of the failure
