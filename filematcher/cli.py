"""Command-line interface for File Matcher."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from filematcher.colors import ColorConfig, determine_color_mode
from filematcher.filesystem import (
    check_cross_filesystem, filter_hardlinked_duplicates, is_in_directory,
)
from filematcher.actions import (
    create_audit_logger, write_log_header, log_operation, write_log_footer,
    execute_all_actions, execute_action, determine_exit_code,
)
from filematcher.types import Action, DuplicateGroup, FailedOperation
from filematcher.formatters import (
    SpaceInfo, TextActionFormatter, JsonActionFormatter, ActionFormatter,
    calculate_space_savings,
)
from filematcher.directory import find_matching_files, select_master_file

logger = logging.getLogger(__name__)

# Exit codes
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_PARTIAL = 2
EXIT_USER_QUIT = 130  # 128 + SIGINT (Unix convention)


def _normalize_response(response: str) -> str | None:
    """Normalize user response to single char or None if invalid.

    Accepts: y, yes, n, no, a, all, q, quit (case-insensitive)
    Returns: 'y', 'n', 'a', 'q', or None
    """
    response = response.casefold()
    if response in ('y', 'yes'):
        return 'y'
    elif response in ('n', 'no'):
        return 'n'
    elif response in ('a', 'all'):
        return 'a'
    elif response in ('q', 'quit'):
        return 'q'
    return None


def prompt_for_group(
    formatter: ActionFormatter,
    group_index: int,
    total_groups: int,
    action: str
) -> str:
    """Prompt user for group decision, re-prompt on invalid input.

    Returns normalized single-char response: 'y', 'n', 'a', or 'q'.
    Raises: KeyboardInterrupt, EOFError (for caller to handle)
    """
    while True:
        prompt_text = formatter.format_group_prompt(group_index, total_groups, action)
        response = input(prompt_text).strip()

        normalized = _normalize_response(response)
        if normalized is not None:
            return normalized

        print("Invalid response. Please enter y (yes), n (no), a (all), or q (quit).")


def interactive_execute(
    groups: list[DuplicateGroup],
    action: Action,
    formatter: ActionFormatter,
    fallback_symlink: bool = False,
    audit_logger: logging.Logger | None = None,
    file_hashes: dict[str, str] | None = None,
    target_dir: str | None = None,
    dir2_base: str | None = None,
    verbose: bool = False,
    file_sizes_map: dict[str, dict[str, int]] | None = None,
    cross_fs_files: set[str] | None = None,
) -> tuple[int, int, int, int, list[FailedOperation], int, int, int, bool]:
    """Execute with per-group interactive confirmation.

    Displays each group, prompts y/n/a/q, executes immediately on confirmation.

    Args:
        groups: List of DuplicateGroup tuples to process
        action: Action to execute (hardlink, symlink, delete)
        formatter: ActionFormatter for display/prompts
        fallback_symlink: Use symlink for cross-filesystem hardlinks
        audit_logger: Logger for audit trail
        file_hashes: Map of file path to hash
        target_dir: Target directory for links
        dir2_base: Base dir2 path for relative path computation
        verbose: Show verbose output
        file_sizes_map: Pre-computed file sizes keyed by master file
        cross_fs_files: Set of files on different filesystem

    Returns:
        Tuple of (success_count, failure_count, skipped_count, space_saved,
                  failed_list, confirmed_count, user_skipped_count, remaining_count, user_quit)
    """
    success_count = 0
    failure_count = 0
    skipped_count = 0
    space_saved = 0
    failed_list: list[FailedOperation] = []
    confirmed_count = 0
    user_skipped_count = 0
    remaining_count = 0
    user_quit = False
    confirm_all = False

    total_groups = len(groups)

    try:
        for i, group in enumerate(groups, start=1):
            master_file, duplicates, reason, file_hash = group

            # Get pre-computed file sizes if available
            file_sizes = file_sizes_map.get(master_file) if file_sizes_map else None

            # Display the group
            formatter.format_duplicate_group(
                master_file,
                duplicates,
                action=action.value,
                file_hash=file_hash if verbose else None,
                file_sizes=file_sizes,
                cross_fs_files=cross_fs_files,
                group_index=i,
                total_groups=total_groups,
                target_dir=target_dir,
                dir2_base=dir2_base
            )

            if confirm_all:
                # Auto-confirm: show status, execute immediately
                formatter.format_confirmation_status(confirmed=True)
                # Execute this group - mirror execute_all_actions pattern
                for dup in duplicates:
                    # Get file size BEFORE action (for space_saved calculation)
                    try:
                        file_size = os.path.getsize(dup) if os.path.exists(dup) else 0
                    except OSError as e:
                        formatter.format_file_error(dup, str(e))
                        if audit_logger:
                            dup_hash = file_hashes.get(dup, "unknown") if file_hashes else "unknown"
                            log_operation(audit_logger, action.value, dup, master_file,
                                          0, dup_hash, success=False, error=str(e))
                        failure_count += 1
                        failed_list.append(FailedOperation(dup, str(e)))
                        continue
                    dup_hash = file_hashes.get(dup, "unknown") if file_hashes else "unknown"

                    # Call execute_action with correct signature: (duplicate, master, action, ...)
                    success, error, actual_action = execute_action(
                        dup, master_file, action.value,
                        fallback_symlink=fallback_symlink,
                        target_dir=target_dir,
                        dir2_base=dir2_base
                    )

                    # Log operation if audit logger provided
                    if audit_logger:
                        log_operation(audit_logger, actual_action, dup, master_file,
                                      file_size, dup_hash, success, error)

                    # Track counts per execute_all_actions pattern
                    if actual_action == "skipped":
                        skipped_count += 1
                    elif success:
                        success_count += 1
                        space_saved += file_size
                    else:
                        formatter.format_file_error(dup, error)
                        failure_count += 1
                        failed_list.append(FailedOperation(dup, error))
                confirmed_count += 1
                continue

            # Prompt for decision
            response = prompt_for_group(formatter, i, total_groups, action.value)

            if response == 'y':
                formatter.format_confirmation_status(confirmed=True)
                # Execute this group - mirror execute_all_actions pattern
                for dup in duplicates:
                    # Get file size BEFORE action (for space_saved calculation)
                    try:
                        file_size = os.path.getsize(dup) if os.path.exists(dup) else 0
                    except OSError as e:
                        formatter.format_file_error(dup, str(e))
                        if audit_logger:
                            dup_hash = file_hashes.get(dup, "unknown") if file_hashes else "unknown"
                            log_operation(audit_logger, action.value, dup, master_file,
                                          0, dup_hash, success=False, error=str(e))
                        failure_count += 1
                        failed_list.append(FailedOperation(dup, str(e)))
                        continue
                    dup_hash = file_hashes.get(dup, "unknown") if file_hashes else "unknown"

                    # Call execute_action with correct signature: (duplicate, master, action, ...)
                    success, error, actual_action = execute_action(
                        dup, master_file, action.value,
                        fallback_symlink=fallback_symlink,
                        target_dir=target_dir,
                        dir2_base=dir2_base
                    )

                    # Log operation if audit logger provided
                    if audit_logger:
                        log_operation(audit_logger, actual_action, dup, master_file,
                                      file_size, dup_hash, success, error)

                    # Track counts per execute_all_actions pattern
                    if actual_action == "skipped":
                        skipped_count += 1
                    elif success:
                        success_count += 1
                        space_saved += file_size
                    else:
                        formatter.format_file_error(dup, error)
                        failure_count += 1
                        failed_list.append(FailedOperation(dup, error))
                confirmed_count += 1

            elif response == 'n':
                formatter.format_confirmation_status(confirmed=False)
                user_skipped_count += 1

            elif response == 'a':
                formatter.format_confirmation_status(confirmed=True)
                remaining = total_groups - i
                if remaining > 0:
                    formatter.format_remaining_count(remaining)
                # Execute this group - mirror execute_all_actions pattern
                for dup in duplicates:
                    # Get file size BEFORE action (for space_saved calculation)
                    try:
                        file_size = os.path.getsize(dup) if os.path.exists(dup) else 0
                    except OSError as e:
                        formatter.format_file_error(dup, str(e))
                        if audit_logger:
                            dup_hash = file_hashes.get(dup, "unknown") if file_hashes else "unknown"
                            log_operation(audit_logger, action.value, dup, master_file,
                                          0, dup_hash, success=False, error=str(e))
                        failure_count += 1
                        failed_list.append(FailedOperation(dup, str(e)))
                        continue
                    dup_hash = file_hashes.get(dup, "unknown") if file_hashes else "unknown"

                    # Call execute_action with correct signature: (duplicate, master, action, ...)
                    success, error, actual_action = execute_action(
                        dup, master_file, action.value,
                        fallback_symlink=fallback_symlink,
                        target_dir=target_dir,
                        dir2_base=dir2_base
                    )

                    # Log operation if audit logger provided
                    if audit_logger:
                        log_operation(audit_logger, actual_action, dup, master_file,
                                      file_size, dup_hash, success, error)

                    # Track counts per execute_all_actions pattern
                    if actual_action == "skipped":
                        skipped_count += 1
                    elif success:
                        success_count += 1
                        space_saved += file_size
                    else:
                        formatter.format_file_error(dup, error)
                        failure_count += 1
                        failed_list.append(FailedOperation(dup, error))
                confirmed_count += 1
                confirm_all = True

            elif response == 'q':
                remaining_count = total_groups - i + 1  # Current group wasn't processed
                user_quit = True
                break

    except (KeyboardInterrupt, EOFError):
        print()  # Newline after ^C
        # Calculate remaining based on last processed group
        # i is defined in loop scope; if we got here, we were in a group
        # Current group wasn't processed, so add 1
        remaining_count = total_groups - i + 1
        user_quit = True

    return (success_count, failure_count, skipped_count, space_saved,
            failed_list, confirmed_count, user_skipped_count, remaining_count, user_quit)


def build_file_hash_lookup(matches: dict[str, tuple[list[str], list[str]]]) -> dict[str, str]:
    """Build a mapping of file paths to their content hashes."""
    lookup: dict[str, str] = {}
    for file_hash, (files1, files2) in matches.items():
        for f in files1 + files2:
            lookup[f] = file_hash
    return lookup


def get_cross_fs_for_hardlink(action: Action, cross_fs_files: set[str]) -> set[str] | None:
    """Return cross-filesystem files set only for hardlink action."""
    return cross_fs_files if action == Action.HARDLINK else None


def get_cross_fs_count(action: Action, cross_fs_files: set[str]) -> int:
    """Return count of cross-filesystem files only for hardlink action."""
    return len(cross_fs_files) if action == Action.HARDLINK else 0


def build_file_sizes(paths: list[str]) -> dict[str, int]:
    """Build dict of file sizes with graceful error handling (0 if inaccessible)."""
    sizes: dict[str, int] = {}
    for p in paths:
        try:
            sizes[p] = os.path.getsize(p)
        except OSError as e:
            logger.debug(f"Could not get size for {p}: {e}")
            sizes[p] = 0
    return sizes


def build_log_flags(
    base_flags: list[str],
    verbose: bool = False,
    yes: bool = False,
    fallback_symlink: bool = False,
    log_path: str | None = None,
    target_dir: str | None = None
) -> list[str]:
    """Build flags list for audit log header."""
    flags = list(base_flags)
    if verbose:
        flags.append('--verbose')
    if yes:
        flags.append('--yes')
    if fallback_symlink:
        flags.append('--fallback-symlink')
    if log_path:
        flags.append(f'--log {log_path}')
    if target_dir:
        flags.append(f'--target-dir {target_dir}')
    return flags


def execute_with_logging(
    dir1: str,
    dir2: str,
    action: Action,
    master_results: list[DuplicateGroup],
    matches: dict[str, tuple[list[str], list[str]]],
    base_flags: list[str],
    verbose: bool = False,
    yes: bool = False,
    fallback_symlink: bool = False,
    log_path: str | None = None,
    target_dir: str | None = None,
) -> tuple[int, int, int, int, list[str], Path]:
    """Execute actions with audit logging and return results."""
    log_path_obj = Path(log_path) if log_path else None
    audit_logger, actual_log_path = create_audit_logger(log_path_obj)

    flags = build_log_flags(
        base_flags,
        verbose=verbose,
        yes=yes,
        fallback_symlink=fallback_symlink,
        log_path=log_path,
        target_dir=target_dir
    )

    write_log_header(audit_logger, dir1, dir2, dir1, action, flags)
    file_hash_lookup = build_file_hash_lookup(matches)

    success_count, failure_count, skipped_count, space_saved, failed_list = execute_all_actions(
        master_results,
        action,
        fallback_symlink=fallback_symlink,
        verbose=verbose,
        audit_logger=audit_logger,
        file_hashes=file_hash_lookup,
        target_dir=target_dir,
        dir2_base=dir2
    )

    write_log_footer(audit_logger, success_count, failure_count, skipped_count, space_saved, failed_list)

    return success_count, failure_count, skipped_count, space_saved, failed_list, actual_log_path


def main() -> int:
    """Main entry point. Returns 0 on success, 1 on error."""
    parser = argparse.ArgumentParser(description='Find files with identical content across two directories.')
    parser.add_argument('dir1', help='First directory to compare')
    parser.add_argument('dir2', help='Second directory to compare')
    parser.add_argument('--show-unmatched', '-u', action='store_true', help='Display files with no content match')
    parser.add_argument('--hash', '-H', choices=['md5', 'sha256'], default='md5',
                        help='Hash algorithm to use (default: md5)')
    parser.add_argument('--summary', '-s', action='store_true',
                        help='Show only counts of matched/unmatched files instead of listing them all')
    parser.add_argument('--fast', '-f', action='store_true',
                        help='Use fast mode for large files (uses file size + partial content sampling)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show detailed progress for each file being processed')
    parser.add_argument('--action', '-a', choices=['compare', 'hardlink', 'symlink', 'delete'],
                        default='compare',
                        help='Action: compare (default, no changes), hardlink, symlink, or delete')
    parser.add_argument('--execute', action='store_true',
                        help='Execute the action (without this flag, only preview)')
    parser.add_argument('--yes', '-y', action='store_true',
                        help='Skip confirmation prompt')
    parser.add_argument('--log', '-l', type=str, metavar='PATH',
                        help='Path for audit log file (default: filematcher_YYYYMMDD_HHMMSS.log)')
    parser.add_argument('--fallback-symlink', action='store_true',
                        help='Use symlink instead of hardlink for cross-filesystem duplicates')
    parser.add_argument('--target-dir', '-t', type=str, metavar='PATH',
                        help='Create links in this directory instead of in-place (dir2 files deleted after linking)')
    parser.add_argument('--different-names-only', '-d', action='store_true',
                        help='Only report files with identical content but different names (exclude same-name matches)')
    parser.add_argument('--json', '-j', action='store_true',
                        help='Output results in JSON format for scripting')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Suppress progress, warnings, and headers - only output data')
    parser.add_argument('--color', dest='color_mode', action='store_const',
                        const='always',
                        help='Force color output (even when piped)')
    parser.add_argument('--no-color', dest='color_mode', action='store_const',
                        const='never',
                        help='Disable color output')

    args = parser.parse_args()

    # Convert string action to enum for type safety
    args.action = Action(args.action)

    if args.json and args.execute and not args.yes:
        parser.error("--json with --execute requires --yes flag to confirm (no interactive prompts in JSON mode)")
    if args.quiet and args.execute and not args.yes:
        parser.error("--quiet and interactive mode are incompatible")
    if args.execute and not args.yes and args.action != Action.COMPARE:
        if not sys.stdin.isatty():
            parser.error("stdin is not a terminal")
    if args.execute and args.action == Action.COMPARE:
        parser.error("compare action doesn't modify files - remove --execute flag")
    if args.log and not args.execute:
        parser.error("--log requires --execute")
    if args.fallback_symlink and args.action != Action.HARDLINK:
        parser.error("--fallback-symlink only applies to --action hardlink")
    if args.target_dir:
        if args.action not in (Action.HARDLINK, Action.SYMLINK):
            parser.error("--target-dir only applies to --action hardlink or --action symlink")
        if not os.path.isdir(args.target_dir):
            parser.error(f"--target-dir must be an existing directory: {args.target_dir}")

    master_path = Path(args.dir1).resolve()

    if args.quiet:
        log_level = logging.ERROR
    elif args.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter('%(message)s'))

    # Configure filematcher loggers for CLI use
    # Clear and set to ensure correct output stream (especially important across test runs)
    for log in [logger,
                logging.getLogger('filematcher.directory'),
                logging.getLogger('filematcher.cli')]:
        log.handlers.clear()
        log.addHandler(handler)
        log.setLevel(log_level)

    color_mode = determine_color_mode(args)
    color_config = ColorConfig(mode=color_mode, stream=sys.stdout)

    if not os.path.isdir(args.dir1) or not os.path.isdir(args.dir2):
        logger.error("Error: Both arguments must be directories")
        return 1

    hash_algo = args.hash
    logger.info(f"Using {hash_algo.upper()} hashing algorithm")

    if args.fast:
        logger.info("Fast mode enabled: Using sparse sampling for large files")

    if args.verbose:
        logger.info("Verbose mode enabled: Showing progress for each file")

    matches, unmatched1, unmatched2 = find_matching_files(args.dir1, args.dir2, hash_algo, args.fast, args.verbose, args.different_names_only)

    matched_files1 = sum(len(files) for files, _ in matches.values())
    matched_files2 = sum(len(files) for _, files in matches.values())

    if master_path:
        master_results = []
        total_masters = 0
        total_duplicates = 0
        total_already_hardlinked = 0
        warnings = []

        for file_hash, (files1, files2) in matches.items():
            all_files = files1 + files2
            master_dir_str = str(master_path)

            master_files_in_group = [f for f in all_files if is_in_directory(f, master_dir_str)]
            if len(master_files_in_group) > 1:
                warnings.append(f"Warning: Multiple files in master directory have identical content: {', '.join(master_files_in_group)}")

            master_file, duplicates, reason = select_master_file(all_files, master_path)
            actionable_dups, hardlinked_dups = filter_hardlinked_duplicates(master_file, duplicates)
            total_already_hardlinked += len(hardlinked_dups)

            if actionable_dups:
                master_results.append(DuplicateGroup(master_file, actionable_dups, reason, file_hash))
                total_masters += 1
                total_duplicates += len(actionable_dups)

        if total_already_hardlinked > 0:
            logger.info(f"Skipped {total_already_hardlinked} files already hardlinked to master (no space savings)")

        cross_fs_files = set()
        if args.action == Action.HARDLINK:
            for master_file, duplicates, reason, _ in master_results:
                cross_fs_files.update(check_cross_filesystem(master_file, duplicates))

        preview_mode = not args.execute
        execute_mode = args.action != Action.COMPARE and args.execute

        if args.json:
            action_formatter = JsonActionFormatter(
                verbose=args.verbose,
                preview_mode=not args.execute,
                action=args.action
            )
            action_formatter.set_directories(args.dir1, args.dir2)
            action_formatter.set_hash_algorithm(hash_algo)
        else:
            action_formatter = TextActionFormatter(
                verbose=args.verbose,
                preview_mode=True,
                action=args.action,
                color_config=color_config,
                will_execute=args.execute
            )

        def print_preview_output(formatter: ActionFormatter, show_banner: bool = True) -> None:
            space_info = calculate_space_savings(master_results)

            if show_banner:
                formatter.format_banner(
                    args.action,
                    space_info.group_count,
                    space_info.duplicate_count,
                    space_info.bytes_saved
                )

            if args.summary:
                if args.action == Action.COMPARE:
                    formatter.format_compare_summary(
                        match_count=len(matches),
                        matched_files1=matched_files1,
                        matched_files2=matched_files2,
                        dir1_name=args.dir1,
                        dir2_name=args.dir2
                    )
                    if args.show_unmatched and not args.json:
                        print(f"\nUnmatched files summary:")
                        print(f"  Files in {args.dir1} with no match: {len(unmatched1)}")
                        print(f"  Files in {args.dir2} with no match: {len(unmatched2)}")
                else:
                    cross_fs_count = get_cross_fs_count(args.action, cross_fs_files)
                    formatter.format_statistics(
                        group_count=space_info.group_count,
                        duplicate_count=space_info.duplicate_count,
                        master_count=len(master_results),
                        space_savings=space_info.bytes_saved,
                        action=args.action,
                        cross_fs_count=cross_fs_count
                    )
            else:
                if not matches:
                    formatter.format_empty_result()
                else:
                    formatter.format_warnings(warnings)

                    sorted_results = sorted(master_results, key=lambda x: x[0])

                    for i, (master_file, duplicates, reason, file_hash) in enumerate(sorted_results):
                        file_sizes = None
                        if args.verbose or args.json:
                            file_sizes = build_file_sizes([master_file] + duplicates)

                        cross_fs_to_show = get_cross_fs_for_hardlink(args.action, cross_fs_files)
                        formatter.format_duplicate_group(
                            master_file, duplicates,
                            action=args.action,
                            file_hash=file_hash,
                            file_sizes=file_sizes,
                            cross_fs_files=cross_fs_to_show,
                            group_index=i + 1,
                            total_groups=len(sorted_results),
                            target_dir=args.target_dir,
                            dir2_base=args.dir2
                        )

                        if i < len(sorted_results) - 1 and not args.json and not color_config.is_tty:
                            print()

                    if color_config.is_tty:
                        print()

                if args.show_unmatched and args.action == Action.COMPARE:
                    formatter.format_unmatched_section(
                        dir1_label=args.dir1,
                        unmatched1=unmatched1,
                        dir2_label=args.dir2,
                        unmatched2=unmatched2
                    )

                if matches:
                    cross_fs_count = get_cross_fs_count(args.action, cross_fs_files)
                    formatter.format_statistics(
                        group_count=space_info.group_count,
                        duplicate_count=space_info.duplicate_count,
                        master_count=len(master_results),
                        space_savings=space_info.bytes_saved,
                        action=args.action,
                        cross_fs_count=cross_fs_count
                    )

        if preview_mode:
            print_preview_output(action_formatter, show_banner=True)
            action_formatter.finalize()

        elif execute_mode:
            if args.json:
                # JSON mode requires --yes, execute batch mode
                success_count, failure_count, skipped_count, space_saved, failed_list, actual_log_path = execute_with_logging(
                    dir1=args.dir1,
                    dir2=args.dir2,
                    action=args.action,
                    master_results=master_results,
                    matches=matches,
                    base_flags=['--execute', '--json', '--yes'],
                    verbose=args.verbose,
                    fallback_symlink=args.fallback_symlink,
                    log_path=args.log,
                    target_dir=args.target_dir
                )

                sorted_results = sorted(master_results, key=lambda x: x[0])
                for i, (master_file, duplicates, reason, file_hash) in enumerate(sorted_results):
                    file_sizes = None
                    if args.verbose or args.json:
                        file_sizes = build_file_sizes([master_file] + duplicates)
                    cross_fs_to_show = get_cross_fs_for_hardlink(args.action, cross_fs_files)
                    action_formatter.format_duplicate_group(
                        master_file, duplicates,
                        action=args.action,
                        file_hash=file_hash,
                        file_sizes=file_sizes,
                        cross_fs_files=cross_fs_to_show,
                        group_index=i + 1,
                        total_groups=len(sorted_results),
                        target_dir=args.target_dir,
                        dir2_base=args.dir2
                    )

                if color_config.is_tty:
                    print()

                preview_space_info = calculate_space_savings(master_results)
                cross_fs_count = get_cross_fs_count(args.action, cross_fs_files)
                action_formatter.format_statistics(
                    group_count=preview_space_info.group_count,
                    duplicate_count=preview_space_info.duplicate_count,
                    master_count=len(master_results),
                    space_savings=preview_space_info.bytes_saved,
                    action=args.action,
                    cross_fs_count=cross_fs_count
                )

                action_formatter.format_execution_summary(
                    success_count=success_count,
                    failure_count=failure_count,
                    skipped_count=skipped_count,
                    space_saved=space_saved,
                    log_path=str(actual_log_path),
                    failed_list=failed_list,
                    confirmed_count=len(master_results),
                    user_skipped_count=0
                )

                action_formatter.finalize()
                if failure_count > 0:
                    return EXIT_PARTIAL
                return EXIT_SUCCESS

            else:
                # Text mode: show banner for both interactive and batch modes
                space_info = calculate_space_savings(master_results)

                if not args.quiet:
                    action_formatter.format_banner(
                        args.action.value,
                        space_info.group_count,
                        space_info.duplicate_count,
                        space_info.bytes_saved
                    )

                if args.yes:
                    # Batch mode - execute without prompts
                    success_count, failure_count, skipped_count, space_saved, failed_list, actual_log_path = execute_with_logging(
                        dir1=args.dir1,
                        dir2=args.dir2,
                        action=args.action,
                        master_results=master_results,
                        matches=matches,
                        base_flags=['--execute', '--yes'],
                        verbose=args.verbose,
                        yes=args.yes,
                        fallback_symlink=args.fallback_symlink,
                        log_path=args.log,
                        target_dir=args.target_dir
                    )

                    action_formatter_exec = TextActionFormatter(
                        verbose=args.verbose,
                        preview_mode=False,
                        action=args.action,
                        color_config=color_config
                    )
                    action_formatter_exec.format_execution_summary(
                        success_count=success_count,
                        failure_count=failure_count,
                        skipped_count=skipped_count,
                        space_saved=space_saved,
                        log_path=str(actual_log_path),
                        failed_list=failed_list,
                        confirmed_count=len(master_results),
                        user_skipped_count=0
                    )

                    if failure_count > 0:
                        return EXIT_PARTIAL
                    return EXIT_SUCCESS
                else:
                    # Interactive mode - prompt for each group
                    file_hash_lookup = build_file_hash_lookup(matches)
                    file_sizes_map: dict[str, dict[str, int]] = {}
                    for master_file, duplicates, reason, file_hash in master_results:
                        file_sizes_map[master_file] = build_file_sizes([master_file] + duplicates)

                    cross_fs_to_show = get_cross_fs_for_hardlink(args.action, cross_fs_files)

                    # Create audit logger
                    log_path_obj = Path(args.log) if args.log else None
                    audit_logger, actual_log_path = create_audit_logger(log_path_obj)

                    base_flags = ['--execute']
                    flags = build_log_flags(base_flags, verbose=args.verbose,
                                           fallback_symlink=args.fallback_symlink,
                                           log_path=args.log, target_dir=args.target_dir)
                    write_log_header(audit_logger, args.dir1, args.dir2, args.dir1, args.action, flags)

                    (success_count, failure_count, skipped_count, space_saved,
                     failed_list, confirmed_count, user_skipped_count,
                     remaining_count, user_quit) = interactive_execute(
                        groups=sorted(master_results, key=lambda x: x[0]),
                        action=args.action,
                        formatter=action_formatter,
                        fallback_symlink=args.fallback_symlink,
                        audit_logger=audit_logger,
                        file_hashes=file_hash_lookup,
                        target_dir=args.target_dir,
                        dir2_base=args.dir2,
                        verbose=args.verbose,
                        file_sizes_map=file_sizes_map,
                        cross_fs_files=cross_fs_to_show
                    )

                    write_log_footer(audit_logger, success_count, failure_count,
                                   skipped_count, space_saved, failed_list)

                    if user_quit:
                        # User quit early via 'q' or Ctrl+C
                        action_formatter.format_quit_summary(
                            confirmed_count=confirmed_count,
                            skipped_count=user_skipped_count,
                            remaining_count=remaining_count,
                            space_saved=space_saved,
                            log_path=str(actual_log_path)
                        )
                        return EXIT_USER_QUIT

                    # Show execution summary
                    action_formatter.format_execution_summary(
                        success_count=success_count,
                        failure_count=failure_count,
                        skipped_count=skipped_count,
                        space_saved=space_saved,
                        log_path=str(actual_log_path),
                        failed_list=failed_list,
                        confirmed_count=confirmed_count,
                        user_skipped_count=user_skipped_count
                    )

                    if failure_count > 0:
                        return EXIT_PARTIAL
                    return EXIT_SUCCESS

    return 0
