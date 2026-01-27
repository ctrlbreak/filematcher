"""Command-line interface for File Matcher.

This module provides:
- main(): CLI entry point (returns exit code)
- confirm_execution(): User confirmation prompt
- Helper functions for building data structures
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

# Import color system from filematcher.colors module
from filematcher.colors import (
    ColorConfig, determine_color_mode,
)

# Import filesystem helpers from filematcher.filesystem module
from filematcher.filesystem import (
    check_cross_filesystem,
    filter_hardlinked_duplicates,
    is_in_directory,
)

# Import action execution and audit logging from filematcher.actions module
from filematcher.actions import (
    create_audit_logger,
    write_log_header,
    log_operation,
    write_log_footer,
    execute_all_actions,
    determine_exit_code,
)

# Import formatters from filematcher.formatters module
from filematcher.formatters import (
    SpaceInfo,
    TextActionFormatter,
    JsonActionFormatter,
    ActionFormatter,
    format_confirmation_prompt,
    calculate_space_savings,
)

# Import directory operations from filematcher.directory module
from filematcher.directory import (
    find_matching_files,
    select_master_file,
)

logger = logging.getLogger(__name__)


def confirm_execution(skip_confirm: bool = False, prompt: str = "Proceed? [y/N] ") -> bool:
    """
    Prompt user for Y/N confirmation before executing changes.

    Args:
        skip_confirm: If True, skip prompt and return True (for --yes flag)
        prompt: Custom prompt string to display

    Returns:
        True if user confirms, False otherwise
    """
    if skip_confirm:
        return True
    if not sys.stdin.isatty():
        print("Non-interactive mode detected. Use --yes to skip confirmation.", file=sys.stderr)
        return False
    response = input(prompt).strip().lower()
    return response in ('y', 'yes')


def build_file_hash_lookup(matches: dict[str, tuple[list[str], list[str]]]) -> dict[str, str]:
    """Build a mapping of file paths to their content hashes.

    Args:
        matches: Dict mapping hash -> (files_in_dir1, files_in_dir2)

    Returns:
        Dict mapping file_path -> hash
    """
    lookup: dict[str, str] = {}
    for file_hash, (files1, files2) in matches.items():
        for f in files1 + files2:
            lookup[f] = file_hash
    return lookup


def get_cross_fs_for_hardlink(action: str, cross_fs_files: set[str]) -> set[str] | None:
    """Return cross-filesystem files set only for hardlink action.

    Args:
        action: The action being performed
        cross_fs_files: Set of files on different filesystems

    Returns:
        cross_fs_files if action is hardlink, None otherwise
    """
    return cross_fs_files if action == 'hardlink' else None


def get_cross_fs_count(action: str, cross_fs_files: set[str]) -> int:
    """Return count of cross-filesystem files only for hardlink action.

    Args:
        action: The action being performed
        cross_fs_files: Set of files on different filesystems

    Returns:
        Count of cross_fs_files if action is hardlink, 0 otherwise
    """
    return len(cross_fs_files) if action == 'hardlink' else 0


def build_file_sizes(paths: list[str]) -> dict[str, int]:
    """Build dict of file sizes with graceful error handling.

    Args:
        paths: List of file paths

    Returns:
        Dict mapping path -> size (0 if file inaccessible)
    """
    sizes: dict[str, int] = {}
    for p in paths:
        try:
            sizes[p] = os.path.getsize(p)
        except OSError:
            sizes[p] = 0
    return sizes


def build_log_flags(
    base_flags: list[str],
    verbose: bool = False,
    yes: bool = False,
    fallback_symlink: bool = False,
    log_path: str | None = None
) -> list[str]:
    """Build flags list for audit log header.

    Args:
        base_flags: Starting flags (e.g., ['--execute'] or ['--execute', '--json', '--yes'])
        verbose: Include --verbose flag
        yes: Include --yes flag
        fallback_symlink: Include --fallback-symlink flag
        log_path: Include --log with path if provided

    Returns:
        Complete list of flags for logging
    """
    flags = list(base_flags)
    if verbose:
        flags.append('--verbose')
    if yes:
        flags.append('--yes')
    if fallback_symlink:
        flags.append('--fallback-symlink')
    if log_path:
        flags.append(f'--log {log_path}')
    return flags


def main() -> int:
    """Main entry point. Returns 0 on success, 1 on error."""
    # Set up argument parser
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
    parser.add_argument('--different-names-only', '-d', action='store_true',
                        help='Only report files with identical content but different names (exclude same-name matches)')
    parser.add_argument('--json', '-j', action='store_true',
                        help='Output results in JSON format for scripting')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Suppress progress, warnings, and headers - only output data')
    # Color output control
    parser.add_argument('--color', dest='color_mode', action='store_const',
                        const='always',
                        help='Force color output (even when piped)')
    parser.add_argument('--no-color', dest='color_mode', action='store_const',
                        const='never',
                        help='Disable color output')
    # Default is None (auto mode - color on TTY, no color when piped)

    args = parser.parse_args()

    # Validate --json with --execute requires --yes (no interactive prompts in JSON mode)
    if args.json and args.execute and not args.yes:
        parser.error("--json with --execute requires --yes flag to confirm (no interactive prompts in JSON mode)")

    # Validate --execute not allowed with compare action (compare doesn't modify files)
    if args.execute and args.action == 'compare':
        parser.error("compare action doesn't modify files - remove --execute flag")

    # Validate --log requires --execute
    if args.log and not args.execute:
        parser.error("--log requires --execute")

    # Validate --fallback-symlink only applies to hardlink action
    if args.fallback_symlink and args.action != 'hardlink':
        parser.error("--fallback-symlink only applies to --action hardlink")

    # Set master to first directory - always set now (all modes are "action" modes)
    # For compare action, master_path is used for display purposes only (no modifications)
    master_path = Path(args.dir1).resolve()

    # Configure logging based on verbosity and quiet mode
    # --quiet suppresses all status messages (only errors get through)
    if args.quiet:
        log_level = logging.ERROR
    elif args.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    log_stream = sys.stderr  # Always stderr for progress/status (Unix convention)
    handler = logging.StreamHandler(log_stream)
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger.handlers = [handler]
    logger.setLevel(log_level)

    # Also configure filematcher.directory logger (for extracted module)
    directory_logger = logging.getLogger('filematcher.directory')
    directory_logger.handlers = [handler]
    directory_logger.setLevel(log_level)

    # Also configure filematcher.cli logger (this module when imported from package)
    cli_logger = logging.getLogger('filematcher.cli')
    cli_logger.handlers = [handler]
    cli_logger.setLevel(log_level)

    # Determine color mode and create color config
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

    # Count total matched files in each directory
    matched_files1 = sum(len(files) for files, _ in matches.values())
    matched_files2 = sum(len(files) for _, files in matches.values())

    # Master-aware output formatting
    if master_path:
        # Process matches into master/duplicate pairs
        master_results = []
        total_masters = 0
        total_duplicates = 0
        total_already_hardlinked = 0
        warnings = []

        for file_hash, (files1, files2) in matches.items():
            all_files = files1 + files2
            master_dir_str = str(master_path)

            # Check for multiple files in master directory (warning case)
            master_files_in_group = [f for f in all_files if is_in_directory(f, master_dir_str)]
            if len(master_files_in_group) > 1:
                warnings.append(f"Warning: Multiple files in master directory have identical content: {', '.join(master_files_in_group)}")

            master_file, duplicates, reason = select_master_file(all_files, master_path)

            # Filter out duplicates already hardlinked to master (same inode = no space savings)
            actionable_dups, hardlinked_dups = filter_hardlinked_duplicates(master_file, duplicates)
            total_already_hardlinked += len(hardlinked_dups)

            # Only add to results if there are actionable duplicates
            if actionable_dups:
                master_results.append((master_file, actionable_dups, reason, file_hash))
                total_masters += 1
                total_duplicates += len(actionable_dups)

        # Log skipped hardlinks (helpful for users to understand why counts may differ)
        if total_already_hardlinked > 0:
            logger.info(f"Skipped {total_already_hardlinked} files already hardlinked to master (no space savings)")

        # Check cross-filesystem for hardlink action
        cross_fs_files = set()
        if args.action == 'hardlink':
            for master_file, duplicates, reason, _ in master_results:
                cross_fs_files.update(check_cross_filesystem(master_file, duplicates))

        # Determine mode: preview (default) or execute
        # For compare action, always preview mode (validation prevents --execute with compare)
        preview_mode = not args.execute
        execute_mode = args.action != 'compare' and args.execute

        # Create formatter for action mode (handles all actions including compare)
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

        # Helper function to print preview output
        def print_preview_output(formatter: ActionFormatter, show_banner: bool = True) -> None:
            # Pre-calculate space savings once for non-compare actions
            space_info = calculate_space_savings(master_results)

            # Output unified header and summary line (unless --quiet)
            if not args.quiet:
                formatter.format_unified_header(args.action, args.dir1, args.dir2)
                formatter.format_summary_line(
                    space_info.group_count, space_info.duplicate_count, space_info.bytes_saved
                )

            if show_banner:
                formatter.format_banner()

            if args.summary:
                # Summary mode: show only statistics (no file listing)
                if args.action == 'compare':
                    # Compare mode: use compare-specific summary format
                    formatter.format_compare_summary(
                        match_count=len(matches),
                        matched_files1=matched_files1,
                        matched_files2=matched_files2,
                        dir1_name=args.dir1,
                        dir2_name=args.dir2
                    )
                    # Show unmatched summary if requested
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
                # Detailed output
                if not matches:
                    formatter.format_empty_result()
                else:
                    # Print warnings first
                    formatter.format_warnings(warnings)

                    # Sort master_results by master file path (alphabetical) for determinism (OUT-04)
                    sorted_results = sorted(master_results, key=lambda x: x[0])

                    for i, (master_file, duplicates, reason, file_hash) in enumerate(sorted_results):
                        # Build file_sizes dict for verbose mode (JSON always needs sizes)
                        file_sizes = None
                        if args.verbose or args.json:
                            file_sizes = build_file_sizes([master_file] + duplicates)

                        # Format group
                        cross_fs_to_show = get_cross_fs_for_hardlink(args.action, cross_fs_files)
                        formatter.format_duplicate_group(
                            master_file, duplicates,
                            action=args.action,
                            file_hash=file_hash,
                            file_sizes=file_sizes,
                            cross_fs_files=cross_fs_to_show,
                            group_index=i + 1,
                            total_groups=len(sorted_results)
                        )

                        # Print blank line between groups (non-TTY text mode only)
                        # In TTY mode with progress, groups overwrite each other
                        if i < len(sorted_results) - 1 and not args.json and not color_config.is_tty:
                            print()

                    # Add blank line after last group in TTY inline mode
                    if color_config.is_tty:
                        print()

                # Optionally display unmatched files (compare mode) - outside matches check
                if args.show_unmatched and args.action == 'compare':
                    formatter.format_unmatched_section(
                        dir1_label=args.dir1,
                        unmatched1=unmatched1,
                        dir2_label=args.dir2,
                        unmatched2=unmatched2
                    )

                # Print statistics footer (only if there were matches)
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

        # Preview mode (default when --action specified without --execute)
        if preview_mode:
            print_preview_output(action_formatter, show_banner=True)
            action_formatter.finalize()

        # Execute mode (--action with --execute)
        elif execute_mode:
            if args.json:
                # JSON mode: skip preview, execute directly, output JSON with results
                # Create audit logger
                log_path = Path(args.log) if args.log else None
                audit_logger, actual_log_path = create_audit_logger(log_path)

                # Build flags list for log header
                flags = build_log_flags(
                    ['--execute', '--json', '--yes'],
                    verbose=args.verbose,
                    fallback_symlink=args.fallback_symlink,
                    log_path=args.log
                )

                # Write log header
                write_log_header(audit_logger, args.dir1, args.dir2, args.dir1, args.action, flags)

                # Build hash lookup for logging
                file_hash_lookup = build_file_hash_lookup(matches)

                # Execute actions with logging
                success_count, failure_count, skipped_count, space_saved, failed_list = execute_all_actions(
                    master_results,
                    args.action,
                    fallback_symlink=args.fallback_symlink,
                    verbose=args.verbose,
                    audit_logger=audit_logger,
                    file_hashes=file_hash_lookup
                )

                # Write log footer
                write_log_footer(audit_logger, success_count, failure_count, skipped_count, space_saved, failed_list)

                # Collect duplicate groups for JSON (need to rebuild since execution may have changed files)
                # Sort master_results for determinism
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
                        total_groups=len(sorted_results)
                    )

                # Add blank line after last group in TTY inline mode
                if color_config.is_tty:
                    print()

                # Add statistics
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

                # Add execution summary to JSON
                action_formatter.format_execution_summary(
                    success_count=success_count,
                    failure_count=failure_count,
                    skipped_count=skipped_count,
                    space_saved=space_saved,
                    log_path=str(actual_log_path),
                    failed_list=failed_list
                )

                action_formatter.finalize()
                return determine_exit_code(success_count, failure_count)

            else:
                # Text mode: show preview first, then execute
                # First show preview so user sees what will happen
                print_preview_output(action_formatter, show_banner=True)
                action_formatter.format_execute_prompt_separator()

                # Then show execute banner and prompt for confirmation
                banner_line = action_formatter.format_execute_banner_line()
                if banner_line:
                    print(banner_line)

                # Calculate space savings for confirmation prompt
                confirm_space_info = calculate_space_savings(master_results)
                cross_fs_count = get_cross_fs_count(args.action, cross_fs_files)
                prompt = format_confirmation_prompt(
                    confirm_space_info.duplicate_count, args.action,
                    confirm_space_info.bytes_saved, cross_fs_count if args.fallback_symlink else 0
                )
                if not confirm_execution(skip_confirm=args.yes, prompt=prompt):
                    action_formatter.format_user_abort()
                    return 0

                # Show EXECUTING header after confirmation (unless --quiet)
                if not args.quiet:
                    action_formatter_exec_header = TextActionFormatter(
                        verbose=args.verbose,
                        preview_mode=False,
                        action=args.action,
                        color_config=color_config
                    )
                    action_formatter_exec_header.format_unified_header(args.action, args.dir1, args.dir2)
                    print()

                # Create audit logger
                log_path = Path(args.log) if args.log else None
                audit_logger, actual_log_path = create_audit_logger(log_path)

                # Build flags list for log header
                flags = build_log_flags(
                    ['--execute'],
                    verbose=args.verbose,
                    yes=args.yes,
                    fallback_symlink=args.fallback_symlink,
                    log_path=args.log
                )

                # Write log header
                write_log_header(audit_logger, args.dir1, args.dir2, args.dir1, args.action, flags)

                # Build hash lookup for logging
                file_hash_lookup = build_file_hash_lookup(matches)

                # Execute actions with logging
                success_count, failure_count, skipped_count, space_saved, failed_list = execute_all_actions(
                    master_results,
                    args.action,
                    fallback_symlink=args.fallback_symlink,
                    verbose=args.verbose,
                    audit_logger=audit_logger,
                    file_hashes=file_hash_lookup
                )

                # Write log footer
                write_log_footer(audit_logger, success_count, failure_count, skipped_count, space_saved, failed_list)

                # Print execution summary via formatter
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
                    failed_list=failed_list
                )

                # Return appropriate exit code
                return determine_exit_code(success_count, failure_count)

    return 0
