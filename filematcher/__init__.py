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

# Import from colors submodule (extracted module)
# This import is safe and has no dependencies on file_matcher
from filematcher.colors import (
    # ANSI constants
    RESET,
    GREEN,
    YELLOW,
    RED,
    CYAN,
    BOLD,
    DIM,
    BOLD_GREEN,
    BOLD_YELLOW,
    # Classes
    ColorMode,
    ColorConfig,
    GroupLine,
    # Terminal helpers
    strip_ansi,
    visible_len,
    terminal_rows_for_line,
    # Color helpers
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
)

# Import from hashing submodule (extracted module)
# This import is safe and has no dependencies on file_matcher
from filematcher.hashing import (
    create_hasher,
    get_file_hash,
    get_sparse_hash,
    LARGE_FILE_THRESHOLD,
    SPARSE_SAMPLE_SIZE,
    READ_CHUNK_SIZE,
)

# Import from filesystem submodule (extracted module)
# This import is safe - filesystem.py has only stdlib dependencies
from filematcher.filesystem import (
    get_device_id,
    is_hardlink_to,
    is_symlink_to,
    check_cross_filesystem,
    filter_hardlinked_duplicates,
    is_in_directory,
)

# Import from types submodule (shared type definitions)
from filematcher.types import (
    Action,
    DuplicateGroup,
    FailedOperation,
)

# Import from actions submodule (extracted module)
# This import is safe - actions.py depends only on filesystem.py, types.py, and stdlib
from filematcher.actions import (
    format_file_size,
    safe_replace_with_link,
    execute_action,
    execute_all_actions,
    determine_exit_code,
    create_audit_logger,
    write_log_header,
    log_operation,
    write_log_footer,
)

# Import from formatters submodule (extracted module)
# This import depends on colors.py and actions.py
from filematcher.formatters import (
    # Structured types
    SpaceInfo,
    # Constants
    PREVIEW_BANNER,
    BANNER_SEPARATOR,
    # Formatter classes
    ActionFormatter,
    TextActionFormatter,
    JsonActionFormatter,
    # Formatting functions
    format_group_lines,
    format_duplicate_group,
    format_statistics_footer,
    calculate_space_savings,
)

# Import from directory submodule (extracted module)
# This import depends on hashing.py, actions.py, and filesystem.py
from filematcher.directory import (
    index_directory,
    find_matching_files,
    select_master_file,
    select_oldest,
)

# Import from cli submodule (extracted module)
# This import depends on all other filematcher modules
from filematcher.cli import (
    main,
    build_file_hash_lookup,
    get_cross_fs_for_hardlink,
    get_cross_fs_count,
    build_file_sizes,
    build_log_flags,
)

__version__ = "1.5.1"

__all__ = [
    # Version
    "__version__",

    # Core types
    "Action",
    "DuplicateGroup",
    "FailedOperation",

    # Configuration
    "ColorMode",
    "ColorConfig",

    # Formatters (public API for custom output)
    "ActionFormatter",
    "TextActionFormatter",
    "JsonActionFormatter",

    # Core operations
    "find_matching_files",
    "index_directory",
    "select_master_file",
    "execute_action",
    "execute_all_actions",

    # Filesystem utilities
    "is_hardlink_to",
    "is_symlink_to",
    "check_cross_filesystem",

    # Entry point
    "main",
]
