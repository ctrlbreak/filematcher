"""File Matcher package - find and deduplicate files across directories.

This package provides tools for finding files with identical content across
two directory hierarchies and can deduplicate them using hardlinks, symlinks,
or deletion. It uses content hashing (MD5 or SHA-256) to identify matches.

The first directory (dir1) is the implicit master directory - files there
are preserved while duplicates in dir2 are candidates for action.

Basic usage:
    from filematcher import find_matching_files, main

    # Find matching files between two directories
    matches, unmatched1, unmatched2 = find_matching_files(dir1, dir2)

    # Run the CLI
    exit_code = main()
"""

from file_matcher import (
    # Color system
    ColorMode,
    ColorConfig,
    # Output formatters
    ActionFormatter,
    TextActionFormatter,
    JsonActionFormatter,
    # Structured output types
    GroupLine,
    SpaceInfo,
    # Color helper functions
    colorize,
    green,
    yellow,
    red,
    cyan,
    dim,
    bold,
    bold_yellow,
    bold_green,
    render_group_line,
    determine_color_mode,
    # Terminal helpers
    strip_ansi,
    visible_len,
    terminal_rows_for_line,
    # Hashing functions
    get_file_hash,
    get_sparse_hash,
    create_hasher,
    # Directory operations
    index_directory,
    find_matching_files,
    select_master_file,
    # Action execution
    execute_action,
    safe_replace_with_link,
    execute_all_actions,
    determine_exit_code,
    # Filesystem helpers
    is_hardlink_to,
    is_symlink_to,
    check_cross_filesystem,
    get_device_id,
    filter_hardlinked_duplicates,
    is_in_directory,
    # Audit logging
    create_audit_logger,
    log_operation,
    write_log_header,
    write_log_footer,
    # Utilities
    format_file_size,
    calculate_space_savings,
    confirm_execution,
    # Formatting helpers
    format_duplicate_group,
    format_group_lines,
    format_statistics_footer,
    format_confirmation_prompt,
    # Constants
    PREVIEW_BANNER,
    EXECUTE_BANNER,
    # Internal helpers (used by tests)
    select_oldest,
    build_file_hash_lookup,
    get_cross_fs_for_hardlink,
    get_cross_fs_count,
    build_file_sizes,
    build_log_flags,
    # Entry point
    main,
)

__version__ = "1.1.0"

__all__ = [
    # Version
    "__version__",
    # Color system
    "ColorMode",
    "ColorConfig",
    # Output formatters
    "ActionFormatter",
    "TextActionFormatter",
    "JsonActionFormatter",
    # Structured output types
    "GroupLine",
    "SpaceInfo",
    # Color helper functions
    "colorize",
    "green",
    "yellow",
    "red",
    "cyan",
    "dim",
    "bold",
    "bold_yellow",
    "bold_green",
    "render_group_line",
    "determine_color_mode",
    # Terminal helpers
    "strip_ansi",
    "visible_len",
    "terminal_rows_for_line",
    # Hashing functions
    "get_file_hash",
    "get_sparse_hash",
    "create_hasher",
    # Directory operations
    "index_directory",
    "find_matching_files",
    "select_master_file",
    # Action execution
    "execute_action",
    "safe_replace_with_link",
    "execute_all_actions",
    "determine_exit_code",
    # Filesystem helpers
    "is_hardlink_to",
    "is_symlink_to",
    "check_cross_filesystem",
    "get_device_id",
    "filter_hardlinked_duplicates",
    "is_in_directory",
    # Audit logging
    "create_audit_logger",
    "log_operation",
    "write_log_header",
    "write_log_footer",
    # Utilities
    "format_file_size",
    "calculate_space_savings",
    "confirm_execution",
    # Formatting helpers
    "format_duplicate_group",
    "format_group_lines",
    "format_statistics_footer",
    "format_confirmation_prompt",
    # Constants
    "PREVIEW_BANNER",
    "EXECUTE_BANNER",
    # Internal helpers (used by tests)
    "select_oldest",
    "build_file_hash_lookup",
    "get_cross_fs_for_hardlink",
    "get_cross_fs_count",
    "build_file_sizes",
    "build_log_flags",
    # Entry point
    "main",
]
