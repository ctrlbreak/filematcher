"""Action execution and audit logging for File Matcher."""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from filematcher.filesystem import is_hardlink_to, is_symlink_to
from filematcher.types import Action, DuplicateGroup, FailedOperation

logger = logging.getLogger(__name__)


def format_file_size(size_bytes: int | float) -> str:
    """Convert file size in bytes to human-readable format (e.g., "1.5 MB")."""
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
    """Safely replace duplicate with a link to master using temp-rename pattern with rollback."""
    temp_path = duplicate.with_suffix(duplicate.suffix + '.filematcher_tmp')

    try:
        duplicate.rename(temp_path)
    except OSError as e:
        return (False, f"Failed to rename to temp: {e}")

    try:
        if action == Action.HARDLINK:
            duplicate.hardlink_to(master)
        elif action == Action.SYMLINK:
            duplicate.symlink_to(master.resolve())
        elif action == Action.DELETE:
            pass
        else:
            temp_path.rename(duplicate)
            return (False, f"Unknown action: {action}")

        temp_path.unlink()
        return (True, "")

    except OSError as e:
        try:
            temp_path.rename(duplicate)
        except OSError as rollback_err:
            logger.error(f"CRITICAL: Rollback failed for {duplicate}, temp file left as {temp_path}: {rollback_err}")
        return (False, f"Failed to create {action}: {e}")


def execute_action(
    duplicate: str,
    master: str,
    action: str,
    fallback_symlink: bool = False,
    target_dir: str | None = None,
    dir2_base: str | None = None
) -> tuple[bool, str, str]:
    """Execute an action on a duplicate file. Returns (success, error, actual_action_used)."""
    dup_path = Path(duplicate)
    master_path = Path(master)

    if is_symlink_to(duplicate, master):
        return (True, "symlink to master", "skipped")
    if is_hardlink_to(duplicate, master):
        return (True, "hardlink to master", "skipped")

    # Target directory mode: create link in target_dir, delete original
    if target_dir and dir2_base:
        dir2_path = Path(dir2_base).resolve()
        try:
            rel_path = dup_path.resolve().relative_to(dir2_path)
        except ValueError:
            return (False, f"Duplicate {duplicate} not under dir2 {dir2_base}", action)

        target_path = Path(target_dir) / rel_path
        target_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if action == Action.HARDLINK:
                target_path.hardlink_to(master_path)
            elif action == Action.SYMLINK:
                target_path.symlink_to(master_path.resolve())
            else:
                return (False, f"Target-dir mode only supports hardlink/symlink, not {action}", action)

            # Delete original
            dup_path.unlink()
            return (True, "", action)
        except OSError as e:
            # Clean up target if created
            if target_path.exists() or target_path.is_symlink():
                try:
                    target_path.unlink()
                except OSError as cleanup_err:
                    logger.warning(f"Could not clean up partial target {target_path}: {cleanup_err}")
            return (False, f"Failed to create {action} in target dir: {e}", action)

    if action == Action.HARDLINK:
        success, error = safe_replace_with_link(dup_path, master_path, Action.HARDLINK)
        if not success and fallback_symlink:
            error_lower = error.lower()
            if 'cross-device' in error_lower or 'invalid cross-device link' in error_lower or 'errno 18' in error_lower:
                success, error = safe_replace_with_link(dup_path, master_path, Action.SYMLINK)
                if success:
                    return (True, "", "symlink (fallback)")
                return (False, error, "symlink (fallback)")
        return (success, error, Action.HARDLINK)

    elif action == Action.SYMLINK:
        success, error = safe_replace_with_link(dup_path, master_path, Action.SYMLINK)
        return (success, error, Action.SYMLINK)

    elif action == Action.DELETE:
        success, error = safe_replace_with_link(dup_path, master_path, Action.DELETE)
        return (success, error, Action.DELETE)

    else:
        return (False, f"Unknown action: {action}", action)


def determine_exit_code(success_count: int, failure_count: int) -> int:
    """Determine exit code: 0=full success, 1=total failure, 3=partial completion."""
    if failure_count == 0:
        return 0  # Full success
    elif success_count == 0 and failure_count > 0:
        return 1  # Total failure
    else:
        return 3  # Partial completion


def execute_all_actions(
    duplicate_groups: list[DuplicateGroup],
    action: str,
    fallback_symlink: bool = False,
    verbose: bool = False,
    audit_logger: logging.Logger | None = None,
    file_hashes: dict[str, str] | None = None,
    target_dir: str | None = None,
    dir2_base: str | None = None
) -> tuple[int, int, int, int, list[FailedOperation]]:
    """Process all duplicate groups with continue-on-error. Returns (success, fail, skip, bytes, failed_list)."""
    success_count = 0
    failure_count = 0
    skipped_count = 0
    space_saved = 0
    failed_list: list[FailedOperation] = []

    total_duplicates = sum(len(group.duplicates) for group in duplicate_groups)
    processed = 0

    for group in duplicate_groups:
        if not os.path.exists(group.master_file):
            logger.warning(f"Master file missing, skipping group: {group.master_file}")
            continue

        try:
            master_size = os.path.getsize(group.master_file)
        except OSError:
            master_size = 0

        for dup in group.duplicates:
            processed += 1

            if verbose:
                print(f"Processing {processed}/{total_duplicates}...", file=sys.stderr)

            if not os.path.exists(dup):
                logger.info(f"Duplicate no longer exists: {dup}")
                skipped_count += 1
                continue

            try:
                file_size = os.path.getsize(dup)
            except OSError:
                file_size = master_size

            success, error, actual_action = execute_action(
                dup, group.master_file, action, fallback_symlink,
                target_dir=target_dir, dir2_base=dir2_base
            )

            if audit_logger:
                file_hash = file_hashes.get(dup, "unknown") if file_hashes else "unknown"
                log_operation(audit_logger, actual_action, dup, group.master_file, file_size, file_hash, success, error)

            if actual_action == "skipped":
                skipped_count += 1
            elif success:
                success_count += 1
                space_saved += file_size
            else:
                failure_count += 1
                failed_list.append(FailedOperation(dup, error))

    return (success_count, failure_count, skipped_count, space_saved, failed_list)


def create_audit_logger(log_path: Path | None = None) -> tuple[logging.Logger, Path]:
    """Create a separate logger for audit logging to file. Returns (logger, actual_log_path)."""
    if log_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = os.environ.get('FILEMATCHER_LOG_DIR')
        if log_dir:
            log_path = Path(log_dir) / f"filematcher_{timestamp}.log"
        else:
            log_path = Path(f"filematcher_{timestamp}.log")

    audit_logger = logging.getLogger('filematcher.audit')
    audit_logger.setLevel(logging.INFO)
    audit_logger.handlers = []

    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(message)s'))
    audit_logger.addHandler(file_handler)
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
    """Write header block to audit log with run information."""
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
    """Write a single operation line to the audit log."""
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
    failed_list: list[FailedOperation]
) -> None:
    """Write footer block to audit log with summary statistics."""
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
        for failure in failed_list:
            audit_logger.info(f"  - {failure.file_path}: {failure.error_message}")

    audit_logger.info("=" * 80)
