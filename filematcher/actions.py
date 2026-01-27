"""Action execution and audit logging for File Matcher.

This module provides:
- safe_replace_with_link: Atomic replacement with rollback on failure
- execute_action: Single action dispatch with skip detection
- execute_all_actions: Batch processing with continue-on-error
- determine_exit_code: Exit code calculation per convention
- Audit logging: create_audit_logger, write_log_header, log_operation, write_log_footer
"""
from __future__ import annotations

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Internal import from filesystem module (extracted in Plan 01)
from filematcher.filesystem import is_hardlink_to, is_symlink_to

# Module-level logger for debug messages in execute_all_actions
logger = logging.getLogger(__name__)


def format_file_size(size_bytes: int | float) -> str:
    """
    Convert file size in bytes to human-readable format.

    Duplicated from file_matcher.py to keep actions module self-contained.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string with appropriate unit
    """
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024.0 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    if i == 0:
        return f"{int(size_bytes)} {size_names[i]}"
    else:
        return f"{size_bytes:.1f} {size_names[i]}"


def safe_replace_with_link(duplicate: Path, master: Path, action: str) -> tuple[bool, str]:
    """
    Safely replace duplicate file with a link to master using temp-rename pattern.

    The temp-rename pattern ensures the original file can be recovered if link
    creation fails:
    1. Rename duplicate to temp location
    2. Create link at original duplicate location
    3. Delete temp file on success
    4. On failure, restore temp to original location

    Args:
        duplicate: Path to the duplicate file to replace
        master: Path to the master file to link to
        action: Action type ("hardlink", "symlink", or "delete")

    Returns:
        Tuple of (success: bool, error_message: str)
        error_message is empty string on success
    """
    # Create temp path with unique suffix to avoid collisions
    temp_path = duplicate.with_suffix(duplicate.suffix + '.filematcher_tmp')

    try:
        # Step 1: Rename duplicate to temp location
        duplicate.rename(temp_path)
    except OSError as e:
        return (False, f"Failed to rename to temp: {e}")

    try:
        # Step 2: Create link at original duplicate location (or skip for delete)
        if action == 'hardlink':
            duplicate.hardlink_to(master)
        elif action == 'symlink':
            # Use absolute path for symlink per CONTEXT.md
            duplicate.symlink_to(master.resolve())
        elif action == 'delete':
            # For delete, no link creation - just proceed to delete temp
            pass
        else:
            # Unknown action - restore and fail
            temp_path.rename(duplicate)
            return (False, f"Unknown action: {action}")

        # Step 3: Delete temp file on success
        temp_path.unlink()
        return (True, "")

    except OSError as e:
        # Rollback: restore temp to original location (best effort)
        try:
            temp_path.rename(duplicate)
        except OSError:
            pass  # Best effort rollback
        return (False, f"Failed to create {action}: {e}")


def execute_action(
    duplicate: str,
    master: str,
    action: str,
    fallback_symlink: bool = False
) -> tuple[bool, str, str]:
    """
    Execute an action on a duplicate file.

    Main dispatch function that handles hardlink, symlink, and delete actions
    with optional symlink fallback for cross-device hardlink failures.

    Args:
        duplicate: Path to the duplicate file
        master: Path to the master file
        action: Action type ("hardlink", "symlink", or "delete")
        fallback_symlink: If True, fall back to symlink when hardlink fails
                         due to cross-device error

    Returns:
        Tuple of (success: bool, error_message: str, actual_action_used: str)
        actual_action_used can be: "hardlink", "symlink", "symlink (fallback)",
        "delete", or "skipped"
    """
    dup_path = Path(duplicate)
    master_path = Path(master)

    # Check if duplicate is a symlink pointing to master (skip if so)
    if is_symlink_to(duplicate, master):
        return (True, "symlink to master", "skipped")

    # Check if already hardlinked to master (skip if so for any action)
    if is_hardlink_to(duplicate, master):
        return (True, "hardlink to master", "skipped")

    # Execute the action
    if action == 'hardlink':
        success, error = safe_replace_with_link(dup_path, master_path, 'hardlink')
        if not success and fallback_symlink:
            # Check for cross-device error indicators
            error_lower = error.lower()
            if 'cross-device' in error_lower or 'invalid cross-device link' in error_lower or 'errno 18' in error_lower:
                # Fallback to symlink
                success, error = safe_replace_with_link(dup_path, master_path, 'symlink')
                if success:
                    return (True, "", "symlink (fallback)")
                return (False, error, "symlink (fallback)")
        return (success, error, "hardlink")

    elif action == 'symlink':
        success, error = safe_replace_with_link(dup_path, master_path, 'symlink')
        return (success, error, "symlink")

    elif action == 'delete':
        success, error = safe_replace_with_link(dup_path, master_path, 'delete')
        return (success, error, "delete")

    else:
        return (False, f"Unknown action: {action}", action)


def determine_exit_code(success_count: int, failure_count: int) -> int:
    """
    Determine the appropriate exit code based on operation results.

    Exit codes per CONTEXT.md:
    - 0: Full success (all operations completed)
    - 1: Total failure (no operations succeeded)
    - 3: Partial completion (some succeeded, some failed)
    Note: Exit code 2 is reserved for validation errors (argparse convention)

    Args:
        success_count: Number of successful operations
        failure_count: Number of failed operations

    Returns:
        Exit code (0, 1, or 3)
    """
    if failure_count == 0:
        return 0  # Full success
    elif success_count == 0 and failure_count > 0:
        return 1  # Total failure
    else:
        return 3  # Partial completion


def execute_all_actions(
    duplicate_groups: list[tuple[str, list[str], str, str]],
    action: str,
    fallback_symlink: bool = False,
    verbose: bool = False,
    audit_logger: logging.Logger | None = None,
    file_hashes: dict[str, str] | None = None
) -> tuple[int, int, int, int, list[tuple[str, str]]]:
    """
    Process all duplicate groups and execute the specified action.

    Implements continue-on-error behavior: individual failures don't halt
    processing of remaining files.

    Args:
        duplicate_groups: List of (master_file, duplicates_list, reason, hash) tuples
        action: Action type ("hardlink", "symlink", or "delete")
        fallback_symlink: If True, fall back to symlink for cross-device hardlink
        verbose: If True, print progress to stderr
        audit_logger: Optional logger for audit trail
        file_hashes: Optional dict mapping file paths to their content hashes

    Returns:
        Tuple of (success_count, failure_count, skipped_count, space_saved, failed_list)
        - success_count: Number of operations that succeeded
        - failure_count: Number of operations that failed
        - skipped_count: Duplicates that no longer exist + already-linked files
        - space_saved: Total bytes saved by successful operations
        - failed_list: List of (duplicate_path, error_message) for failed ops
    """
    success_count = 0
    failure_count = 0
    skipped_count = 0
    space_saved = 0
    failed_list: list[tuple[str, str]] = []

    # Count total duplicates for progress tracking
    total_duplicates = sum(len(dups) for _, dups, _, _ in duplicate_groups)
    processed = 0

    for master_file, duplicates, _reason, _hash in duplicate_groups:
        # Check if master file exists
        if not os.path.exists(master_file):
            logger.warning(f"Master file missing, skipping group: {master_file}")
            # Don't count as failure per CONTEXT.md - skip entire group
            continue

        # Get master file size for logging and space calculations
        try:
            master_size = os.path.getsize(master_file)
        except OSError:
            master_size = 0

        for dup in duplicates:
            processed += 1

            if verbose:
                print(f"Processing {processed}/{total_duplicates}...", file=sys.stderr)

            # Check if duplicate exists
            if not os.path.exists(dup):
                logger.info(f"Duplicate no longer exists: {dup}")
                skipped_count += 1
                continue

            # Get file size before operation (for space tracking and logging)
            try:
                file_size = os.path.getsize(dup)
            except OSError:
                file_size = master_size  # Fall back to master size

            # Execute the action
            success, error, actual_action = execute_action(
                dup, master_file, action, fallback_symlink
            )

            # Log the operation if audit logger is provided
            if audit_logger:
                file_hash = file_hashes.get(dup, "unknown") if file_hashes else "unknown"
                log_operation(audit_logger, actual_action, dup, master_file, file_size, file_hash, success, error)

            if actual_action == "skipped":
                # Already linked
                skipped_count += 1
            elif success:
                success_count += 1
                space_saved += file_size
            else:
                failure_count += 1
                failed_list.append((dup, error))

    return (success_count, failure_count, skipped_count, space_saved, failed_list)


def create_audit_logger(log_path: Path | None = None) -> tuple[logging.Logger, Path]:
    """
    Create a separate logger for audit logging to file.

    Args:
        log_path: Path for the log file. If None, generates default name
                  in current directory: filematcher_YYYYMMDD_HHMMSS.log

    Returns:
        Tuple of (logger, actual_log_path)
    """
    if log_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = os.environ.get('FILEMATCHER_LOG_DIR')
        if log_dir:
            log_path = Path(log_dir) / f"filematcher_{timestamp}.log"
        else:
            log_path = Path(f"filematcher_{timestamp}.log")

    # Create a new logger separate from the main logger
    audit_logger = logging.getLogger('filematcher.audit')
    audit_logger.setLevel(logging.INFO)

    # Remove any existing handlers to avoid duplicates
    audit_logger.handlers = []

    # Create file handler with utf-8 encoding
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(message)s'))
    audit_logger.addHandler(file_handler)

    # Prevent propagation to root logger
    audit_logger.propagate = False

    return audit_logger, log_path


def write_log_header(
    audit_logger: logging.Logger,
    dir1: str,
    dir2: str,
    master: str,
    action: str,
    flags: list[str]
) -> None:
    """
    Write header block to audit log with run information.

    Args:
        audit_logger: The audit logger instance
        dir1: First directory path
        dir2: Second directory path
        master: Master directory path
        action: Action type (hardlink, symlink, delete)
        flags: List of CLI flags used
    """
    timestamp = datetime.now().isoformat()
    flags_str = ', '.join(flags) if flags else 'none'

    audit_logger.info("=" * 80)
    audit_logger.info("File Matcher Execution Log")
    audit_logger.info("=" * 80)
    audit_logger.info(f"Timestamp: {timestamp}")
    audit_logger.info(f"Directories: {dir1}, {dir2}")
    audit_logger.info(f"Master: {master}")
    audit_logger.info(f"Action: {action}")
    audit_logger.info(f"Flags: {flags_str}")
    audit_logger.info("=" * 80)
    audit_logger.info("")


def log_operation(
    audit_logger: logging.Logger,
    action: str,
    duplicate: str,
    master: str,
    file_size: int,
    file_hash: str,
    success: bool,
    error: str = ""
) -> None:
    """
    Write a single operation line to the audit log.

    Args:
        audit_logger: The audit logger instance
        action: Action type (hardlink, symlink, delete)
        duplicate: Path to the duplicate file
        master: Path to the master file
        file_size: Size of the file in bytes
        file_hash: Content hash of the file
        success: Whether the operation succeeded
        error: Error message if operation failed
    """
    timestamp = datetime.now().isoformat()
    action_upper = action.upper()
    size_str = format_file_size(file_size)
    hash_prefix = file_hash[:8] if len(file_hash) >= 8 else file_hash

    if success:
        result = "SUCCESS"
    else:
        result = f"FAILED: {error}" if error else "FAILED"

    if action.lower() == 'delete':
        audit_logger.info(f"[{timestamp}] {action_upper} {duplicate} ({size_str}) [{hash_prefix}...] {result}")
    else:
        audit_logger.info(f"[{timestamp}] {action_upper} {duplicate} -> {master} ({size_str}) [{hash_prefix}...] {result}")


def write_log_footer(
    audit_logger: logging.Logger,
    success_count: int,
    failure_count: int,
    skipped_count: int,
    space_saved: int,
    failed_list: list[tuple[str, str]]
) -> None:
    """
    Write footer block to audit log with summary statistics.

    Args:
        audit_logger: The audit logger instance
        success_count: Number of successful operations
        failure_count: Number of failed operations
        skipped_count: Number of skipped operations
        space_saved: Total bytes saved
        failed_list: List of (path, error) tuples for failed operations
    """
    total = success_count + failure_count + skipped_count
    space_str = format_file_size(space_saved)

    audit_logger.info("")
    audit_logger.info("=" * 80)
    audit_logger.info("Summary")
    audit_logger.info("=" * 80)
    audit_logger.info(f"Total files processed: {total}")
    audit_logger.info(f"Successful: {success_count}")
    audit_logger.info(f"Failed: {failure_count}")
    audit_logger.info(f"Skipped: {skipped_count}")
    audit_logger.info(f"Space saved: {space_str}")

    if failed_list:
        audit_logger.info("")
        audit_logger.info("Failed files:")
        for path, err in failed_list:
            audit_logger.info(f"  - {path}: {err}")

    audit_logger.info("=" * 80)
