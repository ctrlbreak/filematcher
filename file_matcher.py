#!/usr/bin/env python3
"""
File Matcher - Find files with identical content across two directory trees.

This script compares two directory trees and finds files that have identical
content. By default, it reports all content matches regardless of filename.
Use --different-names-only to filter to only files with different names.

Version: 1.0.0
"""

from __future__ import annotations

from abc import ABC, abstractmethod
import argparse
from enum import Enum
import hashlib
import logging
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path

logger = logging.getLogger(__name__)


# ============================================================================
# ANSI Color Constants (16-color for compatibility)
# ============================================================================

# Reset
RESET = "\033[0m"

# Foreground colors (per 08-CONTEXT.md color palette)
GREEN = "\033[32m"      # Masters (protected files)
YELLOW = "\033[33m"     # Duplicates (removal candidates)
RED = "\033[31m"        # Warnings and errors
CYAN = "\033[36m"       # Statistics and summaries

# Styles
BOLD = "\033[1m"        # Emphasis
DIM = "\033[2m"         # De-emphasis (hash values)

# Compound styles
BOLD_YELLOW = "\033[1;33m"  # PREVIEW MODE banner


# ============================================================================
# Color Configuration
# ============================================================================

class ColorMode(Enum):
    """Color output mode."""
    AUTO = "auto"      # Enable color if TTY and no NO_COLOR
    NEVER = "never"    # Never use color
    ALWAYS = "always"  # Always use color (even in pipes)


class ColorConfig:
    """Determines whether to use color based on mode, environment, and TTY.

    Follows NO_COLOR standard (https://no-color.org/) and common CLI conventions.

    Priority order:
    1. Explicit mode (NEVER or ALWAYS) from --color/--no-color flags
    2. NO_COLOR environment variable (disables color)
    3. FORCE_COLOR environment variable (enables color, for CI systems)
    4. TTY detection on the output stream
    """

    def __init__(
        self,
        mode: ColorMode = ColorMode.AUTO,
        stream: object = None
    ):
        """Initialize color configuration.

        Args:
            mode: Color mode (AUTO, NEVER, ALWAYS)
            stream: Output stream for TTY detection (default: sys.stdout)
        """
        self.mode = mode
        self.stream = stream if stream is not None else sys.stdout
        self._enabled: bool | None = None

    @property
    def enabled(self) -> bool:
        """Determine if color should be used.

        Returns:
            True if color output should be used, False otherwise.
        """
        # Use cached value if already computed
        if self._enabled is not None:
            return self._enabled

        # NEVER mode: always disabled
        if self.mode == ColorMode.NEVER:
            self._enabled = False
            return False

        # ALWAYS mode: always enabled (explicit user intent overrides environment)
        if self.mode == ColorMode.ALWAYS:
            self._enabled = True
            return True

        # AUTO mode: check environment and TTY
        # NO_COLOR takes precedence (standard compliance)
        if os.environ.get('NO_COLOR'):
            self._enabled = False
            return False

        # FORCE_COLOR enables (used by CI systems like GitHub Actions)
        if os.environ.get('FORCE_COLOR'):
            self._enabled = True
            return True

        # TTY detection
        try:
            self._enabled = self.stream.isatty()
        except AttributeError:
            self._enabled = False

        return self._enabled

    def reset(self) -> None:
        """Reset cached enabled state (for testing)."""
        self._enabled = None


# ============================================================================
# Color Helper Functions
# ============================================================================

def colorize(text: str, code: str, color_config: ColorConfig) -> str:
    """Wrap text with ANSI color code if color is enabled.

    Args:
        text: Text to colorize
        code: ANSI escape code (e.g., GREEN, BOLD)
        color_config: ColorConfig instance determining if color is enabled

    Returns:
        Colorized text if enabled, original text otherwise.
    """
    if not color_config.enabled:
        return text
    return f"{code}{text}{RESET}"


def green(text: str, cc: ColorConfig) -> str:
    """Color text green (masters, protected files)."""
    return colorize(text, GREEN, cc)


def yellow(text: str, cc: ColorConfig) -> str:
    """Color text yellow (duplicates, removal candidates)."""
    return colorize(text, YELLOW, cc)


def red(text: str, cc: ColorConfig) -> str:
    """Color text red (warnings, errors)."""
    return colorize(text, RED, cc)


def cyan(text: str, cc: ColorConfig) -> str:
    """Color text cyan (statistics, summaries)."""
    return colorize(text, CYAN, cc)


def dim(text: str, cc: ColorConfig) -> str:
    """Dim text (hash values, de-emphasized content)."""
    return colorize(text, DIM, cc)


def bold(text: str, cc: ColorConfig) -> str:
    """Bold text (emphasis)."""
    return colorize(text, BOLD, cc)


def bold_yellow(text: str, cc: ColorConfig) -> str:
    """Bold yellow text (PREVIEW MODE banner)."""
    return colorize(text, BOLD_YELLOW, cc)


def determine_color_mode(args) -> ColorMode:
    """Determine color mode from CLI arguments.

    Args:
        args: Parsed command-line arguments

    Returns:
        ColorMode based on flags (AUTO if no flags, ALWAYS for --color, NEVER for --no-color)
    """
    # --json implies no color (JSON must never have ANSI codes)
    if args.json:
        return ColorMode.NEVER

    # Explicit flag takes precedence
    if args.color_mode == 'always':
        return ColorMode.ALWAYS
    elif args.color_mode == 'never':
        return ColorMode.NEVER

    # Default to AUTO (TTY detection)
    return ColorMode.AUTO


# ============================================================================
# Output Formatter ABCs
# ============================================================================

class ActionFormatter(ABC):
    """Abstract base class for formatting action mode output (preview/execute).

    Action mode shows master/duplicate relationships and actions to be taken.
    """

    def __init__(self, verbose: bool = False, preview_mode: bool = True, action: str | None = None):
        """Initialize the formatter with configuration.

        Args:
            verbose: If True, show additional details in output
            preview_mode: If True, format for preview; if False, format for execution
            action: Action type (compare, hardlink, symlink, delete) for action-specific formatting
        """
        self.verbose = verbose
        self.preview_mode = preview_mode
        self._action = action

    @abstractmethod
    def format_banner(self) -> None:
        """Format and output the mode banner (PREVIEW or EXECUTE)."""
        pass

    @abstractmethod
    def format_unified_header(self, action: str, dir1: str, dir2: str) -> None:
        """Format and output the unified mode header with directories.

        Args:
            action: Action type (hardlink, symlink, delete)
            dir1: Master directory path
            dir2: Duplicate directory path
        """
        pass

    @abstractmethod
    def format_summary_line(self, group_count: int, duplicate_count: int, space_savings: int) -> None:
        """Format and output the one-liner summary after header.

        Args:
            group_count: Number of duplicate groups found
            duplicate_count: Total number of duplicate files
            space_savings: Bytes reclaimable
        """
        pass

    @abstractmethod
    def format_warnings(self, warnings: list[str]) -> None:
        """Format and output warnings.

        Args:
            warnings: List of warning messages
        """
        pass

    @abstractmethod
    def format_duplicate_group(
        self,
        master_file: str,
        duplicates: list[str],
        action: str,
        file_hash: str | None = None,
        file_sizes: dict[str, int] | None = None,
        cross_fs_files: set[str] | None = None
    ) -> None:
        """Format and output a duplicate group showing master and duplicates.

        Args:
            master_file: Path to the master file (preserved)
            duplicates: List of duplicate file paths
            action: Action type (hardlink, symlink, delete)
            file_hash: Content hash for this group (for verbose mode)
            file_sizes: Optional dict mapping paths to file sizes (for verbose mode)
            cross_fs_files: Optional set of duplicates on different filesystem
        """
        pass

    @abstractmethod
    def format_statistics(
        self,
        group_count: int,
        duplicate_count: int,
        master_count: int,
        space_savings: int,
        action: str,
        cross_fs_count: int = 0
    ) -> None:
        """Format and output statistics footer.

        Args:
            group_count: Number of duplicate groups
            duplicate_count: Total number of duplicate files
            master_count: Number of master files (preserved)
            space_savings: Bytes that would be saved
            action: Action type for action-specific messaging
            cross_fs_count: Number of files that can't be hardlinked (cross-fs)
        """
        pass

    @abstractmethod
    def format_execution_summary(
        self,
        success_count: int,
        failure_count: int,
        skipped_count: int,
        space_saved: int,
        log_path: str,
        failed_list: list[tuple[str, str]]
    ) -> None:
        """Format and output execution summary after actions complete.

        Args:
            success_count: Number of successful operations
            failure_count: Number of failed operations
            skipped_count: Number of skipped operations
            space_saved: Total bytes saved
            log_path: Path to the audit log file
            failed_list: List of (file_path, error_message) tuples for failures
        """
        pass

    @abstractmethod
    def format_empty_result(self) -> None:
        """Format message when no duplicates found in dedup mode."""
        pass

    @abstractmethod
    def format_user_abort(self) -> None:
        """Format message when user aborts execution."""
        pass

    @abstractmethod
    def format_execute_prompt_separator(self) -> None:
        """Format blank line/separator before execute prompt."""
        pass

    @abstractmethod
    def format_execute_banner_line(self) -> str:
        """Return the execute banner text (for caller to print or embed)."""
        pass

    @abstractmethod
    def format_compare_summary(
        self,
        match_count: int,
        matched_files1: int,
        matched_files2: int,
        dir1_name: str,
        dir2_name: str
    ) -> None:
        """Format and output compare mode summary (--summary flag).

        Args:
            match_count: Number of unique content hashes with matches
            matched_files1: Number of files in dir1 with matches
            matched_files2: Number of files in dir2 with matches
            dir1_name: Label for first directory
            dir2_name: Label for second directory
        """
        pass

    @abstractmethod
    def format_unmatched_section(
        self,
        dir1_label: str,
        unmatched1: list[str],
        dir2_label: str,
        unmatched2: list[str]
    ) -> None:
        """Format and output the unmatched files section (--show-unmatched flag).

        Args:
            dir1_label: Label for first directory
            unmatched1: List of file paths in dir1 with no matches
            dir2_label: Label for second directory
            unmatched2: List of file paths in dir2 with no matches
        """
        pass

    @abstractmethod
    def finalize(self) -> None:
        """Finalize output (e.g., flush buffers, close files)."""
        pass


# ============================================================================
# Text Formatter Implementations
# ============================================================================

class TextCompareFormatter(CompareFormatter):
    """Text output formatter for compare mode (no action specified).

    Implements formatting inline - there are no existing format_* functions
    for compare mode to delegate to. Matches current output format exactly.
    """

    def __init__(
        self,
        verbose: bool = False,
        dir1_name: str = "dir1",
        dir2_name: str = "dir2",
        color_config: ColorConfig | None = None
    ):
        """Initialize the formatter with configuration.

        Args:
            verbose: If True, show additional details in output
            dir1_name: Label for first directory
            dir2_name: Label for second directory
            color_config: Color configuration (default: no color)
        """
        super().__init__(verbose, dir1_name, dir2_name)
        self.cc = color_config or ColorConfig(mode=ColorMode.NEVER)

    def format_header(self, dir1: str, dir2: str, hash_algo: str) -> None:
        """Format comparison header showing mode and directories."""
        header = f"Compare mode: {dir1} vs {dir2}"
        print(cyan(header, self.cc))

    def format_summary_line(self, group_count: int, duplicate_count: int, space_savings: int) -> None:
        """Format one-liner summary after header."""
        space_str = format_file_size(space_savings)
        summary = f"Found {group_count} duplicate groups ({duplicate_count} files, {space_str} reclaimable)"
        print(cyan(summary, self.cc))
        print()  # Blank line after summary

    def format_match_group(self, file_hash: str, files_dir1: list[str], files_dir2: list[str]) -> None:
        """Format a group of matching files with unified hierarchical structure.

        Args:
            file_hash: Content hash for this group
            files_dir1: List of file paths from first directory (sorted for determinism)
            files_dir2: List of file paths from second directory (sorted for determinism)
        """
        sorted_dir1 = sorted(files_dir1)  # Sorted for determinism (OUT-04)
        sorted_dir2 = sorted(files_dir2)  # Sorted for determinism (OUT-04)

        # Primary file: first from dir1 (green, unindented) - MASTER
        primary = sorted_dir1[0]
        # Count duplicates: all dir2 files + additional dir1 files (excluding primary)
        dup_count = len(sorted_dir2) + len(sorted_dir1) - 1

        # Build secondary files list with labels:
        # - Additional dir1 files get MASTER label (same source as primary)
        # - Dir2 files get DUPLICATE label
        secondary_files: list[tuple[str, str]] = []
        for f in sorted_dir1[1:]:
            secondary_files.append((f, "MASTER"))
        for f in sorted_dir2:
            secondary_files.append((f, "DUPLICATE"))

        # Build file_sizes dict for verbose mode
        file_sizes: dict[str, int] | None = None
        if self.verbose:
            try:
                file_sizes = {primary: os.path.getsize(primary)}
            except OSError:
                file_sizes = None

        # Delegate to shared helper for line generation
        lines = format_group_lines(
            primary_file=primary,
            secondary_files=secondary_files,
            primary_label="MASTER",
            verbose=self.verbose,
            file_sizes=file_sizes,
            dup_count=dup_count
        )

        # Apply colors and print
        for line in lines:
            if line.startswith("[MASTER]"):
                # Primary master line (green)
                print(green(line, self.cc))
            elif "    [MASTER]" in line:
                # Secondary master line (green)
                print(green(line, self.cc))
            elif "    [DUPLICATE]" in line:
                # Duplicate line (yellow)
                print(yellow(line, self.cc))
            else:
                print(line)

        # Hash as de-emphasized trailing detail (verbose only)
        if self.verbose:
            print(dim(f"  Hash: {file_hash[:10]}...", self.cc))
        print()

    def format_unmatched(self, dir_label: str, files: list[str]) -> None:
        """Format unmatched files for a directory.

        Args:
            dir_label: Label for the directory
            files: List of file paths with no matches (sorted for determinism)
        """
        if files:
            print(f"\nUnique files in {dir_label} ({len(files)}):")
            for f in sorted(files):  # Sorted for determinism (OUT-04)
                print(f"  {f}")
        else:
            print(f"\nNo unique files in {dir_label}")

    def format_summary(self, match_count: int, matched_files1: int, matched_files2: int, unmatched1: int, unmatched2: int) -> None:
        """Format comparison summary.

        Args:
            match_count: Number of unique content hashes with matches
            matched_files1: Number of files in dir1 with matches
            matched_files2: Number of files in dir2 with matches
            unmatched1: Number of unmatched files in dir1 (unused in summary)
            unmatched2: Number of unmatched files in dir2 (unused in summary)
        """
        print(f"\nMatched files summary:")
        print(f"  Unique content hashes with matches: {match_count}")
        print(f"  Files in {self.dir1_name} with matches in {self.dir2_name}: {matched_files1}")
        print(f"  Files in {self.dir2_name} with matches in {self.dir1_name}: {matched_files2}")

    def format_statistics(self, group_count: int, file_count: int, space_savings: int) -> None:
        """Format statistics footer matching action mode format."""
        print()
        print(cyan("--- Statistics ---", self.cc))
        print(f"Duplicate groups: {group_count}")
        print(f"Total files with matches: {file_count}")
        if space_savings > 0:
            print(f"Space reclaimable: {format_file_size(space_savings)}")
        else:
            print("Space reclaimable: (run with --action to calculate)")

    def format_empty_result(self, mode: str = "compare") -> None:
        """Format message when no matches found."""
        if mode == "dedup":
            print("No duplicates found.")
        else:
            print("No matching files found.")

    def format_unmatched_header(self) -> None:
        """Format the header for unmatched files section."""
        print("\nFiles with no content matches:")
        print("==============================")

    def finalize(self) -> None:
        """Finalize output. Text output is immediate, so nothing to do."""
        pass


class JsonCompareFormatter(CompareFormatter):
    """JSON output formatter for compare mode (no action specified).

    Implements accumulator pattern - collects data during format_* calls,
    then serializes to JSON in finalize().
    """

    def __init__(self, verbose: bool = False, dir1_name: str = "dir1", dir2_name: str = "dir2"):
        """Initialize the formatter with configuration.

        Args:
            verbose: If True, include per-file metadata in output
            dir1_name: Label for first directory (default: "dir1")
            dir2_name: Label for second directory (default: "dir2")
        """
        super().__init__(verbose, dir1_name, dir2_name)
        self._data: dict = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "directories": {
                "dir1": "",
                "dir2": ""
            },
            "hashAlgorithm": "",
            "matches": [],
            "unmatchedDir1": [],
            "unmatchedDir2": [],
            "summary": {}
        }
        # Track metadata for verbose mode
        self._metadata: dict[str, dict] = {}
        # Track statistics (set by format_statistics)
        self._statistics: dict | None = None

    def format_header(self, dir1: str, dir2: str, hash_algo: str) -> None:
        """Format comparison header by storing directory and algorithm info.

        Args:
            dir1: First directory path (stored as absolute)
            dir2: Second directory path (stored as absolute)
            hash_algo: Hash algorithm used (md5, sha256)
        """
        self._data["directories"]["dir1"] = str(Path(dir1).resolve())
        self._data["directories"]["dir2"] = str(Path(dir2).resolve())
        self._data["hashAlgorithm"] = hash_algo

    def format_match_group(self, file_hash: str, files_dir1: list[str], files_dir2: list[str]) -> None:
        """Accumulate a group of matching files.

        Args:
            file_hash: Content hash for this group
            files_dir1: List of file paths from first directory
            files_dir2: List of file paths from second directory
        """
        # Sort file lists for determinism (OUT-04)
        sorted_files1 = sorted(files_dir1)
        sorted_files2 = sorted(files_dir2)

        match_group = {
            "hash": file_hash,
            "filesDir1": sorted_files1,
            "filesDir2": sorted_files2
        }
        self._data["matches"].append(match_group)

        # Collect metadata for verbose mode
        if self.verbose:
            for f in sorted_files1 + sorted_files2:
                try:
                    stat = os.stat(f)
                    self._metadata[f] = {
                        "sizeBytes": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()
                    }
                except OSError:
                    pass  # Skip files that can't be accessed

    def format_unmatched(self, dir_label: str, files: list[str]) -> None:
        """Accumulate unmatched files for a directory.

        Args:
            dir_label: Label for the directory (used to determine which list)
            files: List of file paths with no matches
        """
        # Sort for determinism (OUT-04)
        sorted_files = sorted(files)

        # Determine which list to append to based on dir_label
        if dir_label == self.dir1_name:
            self._data["unmatchedDir1"] = sorted_files
        else:
            self._data["unmatchedDir2"] = sorted_files

        # Collect metadata for verbose mode
        if self.verbose:
            for f in sorted_files:
                try:
                    stat = os.stat(f)
                    self._metadata[f] = {
                        "sizeBytes": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()
                    }
                except OSError:
                    pass  # Skip files that can't be accessed

    def format_summary(self, match_count: int, matched_files1: int, matched_files2: int, unmatched1: int, unmatched2: int) -> None:
        """Accumulate comparison summary statistics.

        Args:
            match_count: Number of unique content hashes with matches
            matched_files1: Number of files in dir1 with matches
            matched_files2: Number of files in dir2 with matches
            unmatched1: Number of unmatched files in dir1
            unmatched2: Number of unmatched files in dir2
        """
        self._data["summary"] = {
            "matchCount": match_count,
            "matchedFilesDir1": matched_files1,
            "matchedFilesDir2": matched_files2,
            "unmatchedFilesDir1": unmatched1,
            "unmatchedFilesDir2": unmatched2
        }

    def format_statistics(self, group_count: int, file_count: int, space_savings: int) -> None:
        """Store statistics data for JSON output."""
        self._statistics = {
            "duplicateGroups": group_count,
            "totalFilesWithMatches": file_count,
            "spaceReclaimable": space_savings,
            "spaceReclaimableFormatted": format_file_size(space_savings) if space_savings > 0 else None
        }

    def format_summary_line(self, group_count: int, duplicate_count: int, space_savings: int) -> None:
        """Store summary line data for JSON output."""
        # For JSON, summary line data is integrated into the summary structure
        # This ensures the one-liner info is available in JSON output
        if "summary" not in self._data:
            self._data["summary"] = {}
        self._data["summary"]["duplicateGroups"] = group_count
        self._data["summary"]["duplicateFiles"] = duplicate_count
        self._data["summary"]["spaceReclaimable"] = space_savings

    def format_empty_result(self, mode: str = "compare") -> None:
        """No-op for JSON - empty results represented in JSON structure."""
        pass

    def format_unmatched_header(self) -> None:
        """No-op for JSON - section headers not needed."""
        pass

    def finalize(self) -> None:
        """Finalize output by sorting collections and printing JSON."""
        # Sort matches by (first file in dir1, hash) for determinism
        self._data["matches"].sort(
            key=lambda m: (m["filesDir1"][0] if m["filesDir1"] else "", m["hash"])
        )

        # Add metadata if verbose mode
        if self.verbose and self._metadata:
            self._data["metadata"] = self._metadata

        # Add statistics if set
        if self._statistics:
            self._data["statistics"] = self._statistics

        # Output JSON
        print(json.dumps(self._data, indent=2))


class JsonActionFormatter(ActionFormatter):
    """JSON output formatter for action mode (preview/execute).

    Implements accumulator pattern - collects data during format_* calls,
    then serializes to JSON in finalize().
    """

    def __init__(self, verbose: bool = False, preview_mode: bool = True, action: str | None = None):
        """Initialize the formatter with configuration.

        Args:
            verbose: If True, include additional details in output
            preview_mode: If True, mode is "preview"; if False, mode is "execute"
            action: Action type (compare, hardlink, symlink, delete)
        """
        super().__init__(verbose, preview_mode, action)
        self._data: dict = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": "preview" if preview_mode else "execute",
            "action": "",
            "directories": {
                "master": "",
                "duplicate": ""
            },
            "warnings": [],
            "duplicateGroups": [],
            "statistics": {}
        }
        # Track action type for execution results
        self._action_type = ""
        # Track hash algorithm for compare mode JSON
        self._hash_algorithm = "md5"
        # Track metadata for verbose mode (compare mode compatible)
        self._metadata: dict[str, dict] = {}

    def format_banner(self) -> None:
        """Format banner - in JSON mode, this is a no-op (mode is in data structure)."""
        pass

    def format_unified_header(self, action: str, dir1: str, dir2: str) -> None:
        """Store header data for JSON output."""
        self._data["action"] = action
        # Directories are already set via set_directories, this ensures action is captured

    def format_summary_line(self, group_count: int, duplicate_count: int, space_savings: int) -> None:
        """Store summary line data for JSON output."""
        # For JSON, summary line data goes into statistics structure
        if "statistics" not in self._data or not self._data["statistics"]:
            self._data["statistics"] = {}
        self._data["statistics"]["summaryDuplicateGroups"] = group_count
        self._data["statistics"]["summaryDuplicateFiles"] = duplicate_count
        self._data["statistics"]["summarySpaceReclaimable"] = space_savings

    def format_warnings(self, warnings: list[str]) -> None:
        """Accumulate warnings.

        Args:
            warnings: List of warning messages
        """
        self._data["warnings"] = list(warnings)  # Copy to avoid mutation

    def format_duplicate_group(
        self,
        master_file: str,
        duplicates: list[str],
        action: str,
        file_hash: str | None = None,
        file_sizes: dict[str, int] | None = None,
        cross_fs_files: set[str] | None = None
    ) -> None:
        """Accumulate a duplicate group.

        Args:
            master_file: Path to the master file (preserved)
            duplicates: List of duplicate file paths
            action: Action type (hardlink, symlink, delete)
            file_hash: Content hash for this group (included in JSON)
            file_sizes: Optional dict mapping paths to file sizes
            cross_fs_files: Optional set of duplicates on different filesystem
        """
        # Store action type for later use
        self._action_type = action
        self._data["action"] = action

        # Build duplicate objects with sorted paths for determinism
        sorted_duplicates = sorted(duplicates)
        dup_objects = []
        for dup in sorted_duplicates:
            dup_obj: dict = {
                "path": dup,
                "action": action,
                "crossFilesystem": cross_fs_files is not None and dup in cross_fs_files
            }
            # Always include sizeBytes (needed for space calculations)
            if file_sizes and dup in file_sizes:
                dup_obj["sizeBytes"] = file_sizes[dup]
            else:
                # Try to get size if not provided
                try:
                    dup_obj["sizeBytes"] = os.path.getsize(dup)
                except OSError:
                    dup_obj["sizeBytes"] = 0

            dup_objects.append(dup_obj)

        group: dict = {
            "masterFile": master_file,
            "duplicates": dup_objects
        }
        if file_hash:
            group["hash"] = file_hash
        self._data["duplicateGroups"].append(group)

        # Collect metadata for verbose mode (compare mode compatible)
        if self.verbose:
            all_files = [master_file] + sorted_duplicates
            for f in all_files:
                try:
                    stat = os.stat(f)
                    self._metadata[f] = {
                        "sizeBytes": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()
                    }
                except OSError:
                    pass  # Skip files that can't be accessed

    def format_statistics(
        self,
        group_count: int,
        duplicate_count: int,
        master_count: int,
        space_savings: int,
        action: str,
        cross_fs_count: int = 0
    ) -> None:
        """Accumulate statistics.

        Args:
            group_count: Number of duplicate groups
            duplicate_count: Total number of duplicate files
            master_count: Number of master files (preserved)
            space_savings: Bytes that would be saved
            action: Action type for action-specific messaging
            cross_fs_count: Number of files that can't be hardlinked (cross-fs)
        """
        self._data["action"] = action
        self._data["statistics"] = {
            "groupCount": group_count,
            "duplicateCount": duplicate_count,
            "masterCount": master_count,
            "spaceSavingsBytes": space_savings,
            "crossFilesystemCount": cross_fs_count
        }

    def format_execution_summary(
        self,
        success_count: int,
        failure_count: int,
        skipped_count: int,
        space_saved: int,
        log_path: str,
        failed_list: list[tuple[str, str]]
    ) -> None:
        """Accumulate execution summary (only in execute mode).

        Args:
            success_count: Number of successful operations
            failure_count: Number of failed operations
            skipped_count: Number of skipped operations
            space_saved: Total bytes saved
            log_path: Path to the audit log file
            failed_list: List of (file_path, error_message) tuples for failures
        """
        # Convert failed_list to JSON-friendly format with sorted paths
        failures = [
            {"path": path, "error": error}
            for path, error in sorted(failed_list)
        ]

        self._data["execution"] = {
            "successCount": success_count,
            "failureCount": failure_count,
            "skippedCount": skipped_count,
            "spaceSavedBytes": space_saved,
            "logPath": log_path,
            "failures": failures
        }

    def set_directories(self, master_dir: str, duplicate_dir: str) -> None:
        """Set the directory paths for JSON output.

        Args:
            master_dir: Path to the master directory
            duplicate_dir: Path to the duplicate directory
        """
        self._data["directories"]["master"] = str(Path(master_dir).resolve())
        self._data["directories"]["duplicate"] = str(Path(duplicate_dir).resolve())

    def set_hash_algorithm(self, algorithm: str) -> None:
        """Set the hash algorithm for JSON output (used in compare mode).

        Args:
            algorithm: Hash algorithm name (md5, sha256)
        """
        self._hash_algorithm = algorithm

    def format_empty_result(self) -> None:
        """No-op for JSON - empty results represented in JSON structure."""
        pass

    def format_compare_summary(
        self,
        match_count: int,
        matched_files1: int,
        matched_files2: int,
        dir1_name: str,
        dir2_name: str
    ) -> None:
        """Store compare mode summary data for JSON output."""
        # Update summary with compare-specific counts
        self._data["summary"] = {
            "matchCount": match_count,
            "matchedFilesDir1": matched_files1,
            "matchedFilesDir2": matched_files2,
            "unmatchedFilesDir1": 0,
            "unmatchedFilesDir2": 0
        }

    def format_unmatched_section(
        self,
        dir1_label: str,
        unmatched1: list[str],
        dir2_label: str,
        unmatched2: list[str]
    ) -> None:
        """Store unmatched files for JSON output."""
        # Store sorted unmatched files for determinism
        self._data["unmatchedDir1"] = sorted(unmatched1)
        self._data["unmatchedDir2"] = sorted(unmatched2)
        # Update summary counts
        if "summary" not in self._data:
            self._data["summary"] = {}
        self._data["summary"]["unmatchedFilesDir1"] = len(unmatched1)
        self._data["summary"]["unmatchedFilesDir2"] = len(unmatched2)

        # Collect metadata for verbose mode (unmatched files too)
        if self.verbose:
            for f in unmatched1 + unmatched2:
                try:
                    stat = os.stat(f)
                    self._metadata[f] = {
                        "sizeBytes": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()
                    }
                except OSError:
                    pass  # Skip files that can't be accessed

    def format_user_abort(self) -> None:
        """No-op for JSON - abort status represented in JSON structure."""
        pass

    def format_execute_prompt_separator(self) -> None:
        """No-op for JSON - visual separators not needed."""
        pass

    def format_execute_banner_line(self) -> str:
        """Return empty string for JSON mode - banners not needed."""
        return ""

    def _convert_statistics_to_summary(self) -> dict:
        """Convert action-mode statistics to compare-mode summary format."""
        stats = self._data.get("statistics", {})
        return {
            "matchCount": stats.get("groupCount", stats.get("summaryDuplicateGroups", 0)),
            "matchedFilesDir1": stats.get("summaryDuplicateFiles", 0),
            "matchedFilesDir2": stats.get("summaryDuplicateFiles", 0),
            "unmatchedFilesDir1": 0,
            "unmatchedFilesDir2": 0
        }

    def finalize(self) -> None:
        """Finalize output by sorting collections and printing JSON."""
        # Compare mode: produce JsonCompareFormatter-compatible schema
        if self._action == "compare":
            # Convert duplicateGroups to matches format for compare mode
            matches = []
            total_files = 0
            for group in self._data.get("duplicateGroups", []):
                master = group.get("masterFile", "")
                duplicates = [d["path"] for d in group.get("duplicates", [])]
                # In compare mode, master goes to filesDir1, duplicates to filesDir2
                match_entry = {
                    "hash": group.get("hash", ""),
                    "filesDir1": [master],
                    "filesDir2": sorted(duplicates)
                }
                matches.append(match_entry)
                total_files += 1 + len(duplicates)  # master + duplicates

            # Sort matches by first file in filesDir1 for determinism
            matches.sort(key=lambda m: m["filesDir1"][0] if m["filesDir1"] else "")

            compare_data: dict = {
                "timestamp": self._data["timestamp"],
                "directories": {
                    "dir1": self._data["directories"].get("master", ""),
                    "dir2": self._data["directories"].get("duplicate", "")
                },
                "hashAlgorithm": self._hash_algorithm,
                "matches": matches,
                "unmatchedDir1": self._data.get("unmatchedDir1", []),
                "unmatchedDir2": self._data.get("unmatchedDir2", []),
                "summary": self._convert_statistics_to_summary()
            }

            # Update summary with unmatched counts if available
            if "summary" in self._data and "unmatchedFilesDir1" in self._data["summary"]:
                compare_data["summary"]["unmatchedFilesDir1"] = self._data["summary"]["unmatchedFilesDir1"]
                compare_data["summary"]["unmatchedFilesDir2"] = self._data["summary"]["unmatchedFilesDir2"]

            # Add metadata if verbose mode (compare mode compatible)
            if self.verbose and self._metadata:
                compare_data["metadata"] = self._metadata

            # Add statistics (compare mode format)
            group_count = len(matches)
            compare_data["statistics"] = {
                "duplicateGroups": group_count,
                "totalFilesWithMatches": total_files,
                "spaceReclaimable": 0,  # Compare mode doesn't compute space
                "spaceReclaimableFormatted": None
            }

            print(json.dumps(compare_data, indent=2))
            return

        # Action modes: use existing schema
        # Sort duplicateGroups by master file path for determinism
        self._data["duplicateGroups"].sort(key=lambda g: g["masterFile"])

        # Sort duplicates within each group by path (already done in format_duplicate_group,
        # but ensure consistency)
        for group in self._data["duplicateGroups"]:
            group["duplicates"].sort(key=lambda d: d["path"])

        # Output JSON
        print(json.dumps(self._data, indent=2))


class TextActionFormatter(ActionFormatter):
    """Text output formatter for action mode (preview/execute).

    Delegates to existing format_* functions to ensure byte-identical output.
    These functions are already battle-tested and produce the expected format.
    """

    def __init__(
        self,
        verbose: bool = False,
        preview_mode: bool = True,
        action: str | None = None,
        color_config: ColorConfig | None = None
    ):
        """Initialize the formatter with configuration.

        Args:
            verbose: If True, show additional details in output
            preview_mode: If True, format for preview; if False, format for execution
            action: Action type (compare, hardlink, symlink, delete)
            color_config: Color configuration (default: no color)
        """
        super().__init__(verbose, preview_mode, action)
        self.cc = color_config or ColorConfig(mode=ColorMode.NEVER)

    def format_banner(self) -> None:
        """Format and output the mode banner (PREVIEW or EXECUTE)."""
        if self._action == "compare":
            return  # Compare mode doesn't show PREVIEW/EXECUTING banner
        if self.preview_mode:
            # PREVIEW banner in bold yellow (attention-grabbing safety warning)
            print(bold_yellow(format_preview_banner(), self.cc))
        else:
            print(format_execute_banner())
        print()

    def format_unified_header(self, action: str, dir1: str, dir2: str) -> None:
        """Format unified header showing mode, state, action and directories."""
        if action == "compare":
            # Compare mode: no (PREVIEW)/(EXECUTING) state indicator
            header = f"Compare mode: {dir1} vs {dir2}"
        else:
            state = "PREVIEW" if self.preview_mode else "EXECUTING"
            header = f"Action mode ({state}): {action} {dir1} vs {dir2}"
        print(cyan(header, self.cc))

    def format_summary_line(self, group_count: int, duplicate_count: int, space_savings: int) -> None:
        """Format one-liner summary after header."""
        space_str = format_file_size(space_savings)
        summary = f"Found {group_count} duplicate groups ({duplicate_count} files, {space_str} reclaimable)"
        print(cyan(summary, self.cc))
        print()  # Blank line after summary

    def format_warnings(self, warnings: list[str]) -> None:
        """Format and output warnings.

        Args:
            warnings: List of warning messages
        """
        for warning in warnings:
            # Warnings in red (attention needed)
            print(red(warning, self.cc))
        if warnings:
            print()

    def format_duplicate_group(
        self,
        master_file: str,
        duplicates: list[str],
        action: str,
        file_hash: str | None = None,
        file_sizes: dict[str, int] | None = None,
        cross_fs_files: set[str] | None = None
    ) -> None:
        """Format and output a duplicate group.

        Delegates to existing format_duplicate_group function and applies colors:
        - Master file paths in green (protected)
        - Duplicate file paths in yellow (removal candidates)
        - Cross-filesystem warnings in red
        - Hash line in dim (verbose only)

        Args:
            master_file: Path to the master file (preserved)
            duplicates: List of duplicate file paths
            action: Action type (hardlink, symlink, delete)
            file_hash: Content hash for this group (for verbose mode)
            file_sizes: Optional dict mapping paths to file sizes (for verbose mode)
            cross_fs_files: Optional set of duplicates on different filesystem
        """
        # DELEGATE to existing format_duplicate_group function
        # Note: format_duplicate_group already sorts duplicates (line 144: sorted(duplicates))
        lines = format_duplicate_group(
            master_file=master_file,
            duplicates=duplicates,
            action=action,
            verbose=self.verbose,
            file_sizes=file_sizes,
            cross_fs_files=cross_fs_files,
            preview_mode=self.preview_mode
        )
        for line in lines:
            if line.startswith("[MASTER]"):
                # Master file path in green (protected)
                print(green(line, self.cc))
            elif line.startswith("    ["):
                # Duplicate file path in yellow (removal candidate)
                # Check for cross-fs warning and color that part red
                if "[!cross-fs]" in line:
                    # Split and color the warning part red
                    main_part = line.replace(" [!cross-fs]", "")
                    warning_part = " [!cross-fs]"
                    print(yellow(main_part, self.cc) + red(warning_part, self.cc))
                else:
                    print(yellow(line, self.cc))
            else:
                print(line)

        # Hash as de-emphasized trailing detail (verbose only)
        if self.verbose and file_hash:
            print(dim(f"  Hash: {file_hash[:10]}...", self.cc))

    def format_statistics(
        self,
        group_count: int,
        duplicate_count: int,
        master_count: int,
        space_savings: int,
        action: str,
        cross_fs_count: int = 0
    ) -> None:
        """Format and output statistics footer.

        Delegates to existing format_statistics_footer function and applies colors:
        - Statistics header in cyan

        Args:
            group_count: Number of duplicate groups
            duplicate_count: Total number of duplicate files
            master_count: Number of master files (preserved)
            space_savings: Bytes that would be saved
            action: Action type for action-specific messaging
            cross_fs_count: Number of files that can't be hardlinked (cross-fs)
        """
        # DELEGATE to existing format_statistics_footer function
        lines = format_statistics_footer(
            group_count=group_count,
            duplicate_count=duplicate_count,
            master_count=master_count,
            space_savings=space_savings,
            action=action,
            verbose=self.verbose,
            cross_fs_count=cross_fs_count,
            preview_mode=self.preview_mode
        )
        for line in lines:
            if line == "--- Statistics ---":
                print(cyan(line, self.cc))
            else:
                print(line)

    def format_execution_summary(
        self,
        success_count: int,
        failure_count: int,
        skipped_count: int,
        space_saved: int,
        log_path: str,
        failed_list: list[tuple[str, str]]
    ) -> None:
        """Format and output execution summary.

        Args:
            success_count: Number of successful operations
            failure_count: Number of failed operations
            skipped_count: Number of skipped operations
            space_saved: Total bytes saved
            log_path: Path to the audit log file
            failed_list: List of (file_path, error_message) tuples for failures
        """
        print()
        print(f"Execution complete:")
        print(f"  Successful: {success_count}")
        print(f"  Failed: {failure_count}")
        print(f"  Skipped: {skipped_count}")
        print(f"  Space saved: {format_file_size(space_saved)}")
        print(f"  Log file: {log_path}")
        if failed_list:
            print()
            print("Failed files:")
            for path, error in sorted(failed_list):  # Sorted for determinism (OUT-04)
                print(f"  - {path}: {error}")

    def format_empty_result(self) -> None:
        """Format message when no duplicates found."""
        if self._action == "compare":
            print("No matching files found.")
        else:
            print("No duplicates found.")

    def format_compare_summary(
        self,
        match_count: int,
        matched_files1: int,
        matched_files2: int,
        dir1_name: str,
        dir2_name: str
    ) -> None:
        """Format and output compare mode summary."""
        print(f"\nMatched files summary:")
        print(f"  Unique content hashes with matches: {match_count}")
        print(f"  Files in {dir1_name} with matches in {dir2_name}: {matched_files1}")
        print(f"  Files in {dir2_name} with matches in {dir1_name}: {matched_files2}")

    def format_unmatched_section(
        self,
        dir1_label: str,
        unmatched1: list[str],
        dir2_label: str,
        unmatched2: list[str]
    ) -> None:
        """Format and output the unmatched files section."""
        print("\nFiles with no content matches:")
        print("==============================")
        if unmatched1:
            print(f"\nUnique files in {dir1_label}:")
            for f in sorted(unmatched1):
                print(f"  {f}")
        if unmatched2:
            print(f"\nUnique files in {dir2_label}:")
            for f in sorted(unmatched2):
                print(f"  {f}")

    def format_user_abort(self) -> None:
        """Format message when user aborts execution."""
        print("Aborted. No changes made.")

    def format_execute_prompt_separator(self) -> None:
        """Format blank line/separator before execute prompt."""
        print()

    def format_execute_banner_line(self) -> str:
        """Return the execute banner text."""
        return format_execute_banner()

    def finalize(self) -> None:
        """Finalize output. Text output is immediate, so nothing to do."""
        pass


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


def select_master_file(file_paths: list[str], master_dir: Path | None) -> tuple[str, list[str], str]:
    """
    Select which file should be considered the master from a list of duplicates.

    When a master directory is set, files in that directory are preferred.
    Among files in the master directory (or all files if none in master),
    the oldest by modification time is selected.

    Args:
        file_paths: List of file paths with identical content
        master_dir: Resolved path to the master directory, or None

    Returns:
        Tuple of (master_file_path, list_of_duplicate_paths, selection_reason)
    """
    if not file_paths:
        raise ValueError("file_paths cannot be empty")

    if len(file_paths) == 1:
        return file_paths[0], [], "only file"

    if master_dir:
        master_dir_str = str(master_dir)
        # Separate files into master directory files and others
        master_files = [f for f in file_paths if f.startswith(master_dir_str + os.sep) or f.startswith(master_dir_str)]
        other_files = [f for f in file_paths if f not in master_files]

        if master_files:
            # Select oldest file in master directory
            if len(master_files) == 1:
                return master_files[0], other_files + [], "only file in master directory"
            else:
                # Multiple files in master - pick oldest by mtime
                oldest_master = min(master_files, key=lambda p: os.path.getmtime(p))
                other_master_files = [f for f in master_files if f != oldest_master]
                return oldest_master, other_master_files + other_files, "oldest in master directory"
        else:
            # No files in master directory - pick oldest overall
            oldest = min(file_paths, key=lambda p: os.path.getmtime(p))
            duplicates = [f for f in file_paths if f != oldest]
            return oldest, duplicates, "oldest file (none in master directory)"
    else:
        # No master directory set - pick oldest overall
        oldest = min(file_paths, key=lambda p: os.path.getmtime(p))
        duplicates = [f for f in file_paths if f != oldest]
        return oldest, duplicates, "oldest file"


def format_group_lines(
    primary_file: str,
    secondary_files: list[tuple[str, str]],
    primary_label: str = "MASTER",
    verbose: bool = False,
    file_sizes: dict[str, int] | None = None,
    dup_count: int | None = None,
    cross_fs_files: set[str] | None = None
) -> list[str]:
    """
    Format group lines with unified visual structure.

    This is the shared helper for both compare mode and action mode group output.
    Callers apply colors after receiving lines.

    Args:
        primary_file: Path to the primary file (shown unindented)
        secondary_files: List of (path, label) tuples for secondary files
        primary_label: Label for the primary file (default: "MASTER")
        verbose: If True, show file size and dup count on primary line
        file_sizes: Dict mapping paths to file sizes (for verbose mode)
        dup_count: Number of duplicates (for verbose mode display)
        cross_fs_files: Set of paths on different filesystems (adds [!cross-fs] marker)

    Returns:
        List of formatted lines:
        - Primary line: [PRIMARY_LABEL] path (optional: dup count, size)
        - Secondary lines: 4-space indent [LABEL] path
    """
    lines = []

    # Format primary line
    if verbose and file_sizes:
        size = file_sizes.get(primary_file, 0)
        size_str = format_file_size(size)
        effective_dup_count = dup_count if dup_count is not None else len(secondary_files)
        lines.append(f"[{primary_label}] {primary_file} ({effective_dup_count} duplicates, {size_str})")
    else:
        lines.append(f"[{primary_label}] {primary_file}")

    # Format secondary lines (4-space indent, sorted alphabetically by path for determinism)
    for path, label in sorted(secondary_files, key=lambda x: x[0]):
        cross_fs_marker = " [!cross-fs]" if cross_fs_files and path in cross_fs_files else ""
        lines.append(f"    [{label}] {path}{cross_fs_marker}")

    return lines


def format_duplicate_group(
    master_file: str,
    duplicates: list[str],
    action: str | None = None,
    verbose: bool = False,
    file_sizes: dict[str, int] | None = None,
    cross_fs_files: set[str] | None = None,
    preview_mode: bool = True
) -> list[str]:
    """
    Format a duplicate group for display.

    Args:
        master_file: Path to the master file
        duplicates: List of paths to duplicate files
        action: Action type (None, "hardlink", "symlink", "delete")
        verbose: If True, show additional details
        file_sizes: Dict mapping paths to file sizes (for verbose mode)
        cross_fs_files: Set of duplicate paths on different filesystems (for warnings)
        preview_mode: If True and action is set, use "WOULD X" labels; if False, use "[DUP:action]"

    Returns:
        List of formatted lines for this group
    """
    # Determine action label based on preview_mode and action type
    if action == "compare":
        # Compare mode: always use DUPLICATE label (no WOULD/execution states)
        action_label = "DUPLICATE"
    elif action and preview_mode:
        # Preview mode: use "WOULD X" labels
        action_labels = {
            "hardlink": "WOULD HARDLINK",
            "symlink": "WOULD SYMLINK",
            "delete": "WOULD DELETE"
        }
        action_label = action_labels.get(action, f"WOULD {action.upper()}")
    elif action:
        # Execute mode: use "[DUP:action]" format
        action_label = f"DUP:{action}"
    else:
        action_label = "DUP:?"

    # Build secondary files list with labels
    secondary_files = [(dup, action_label) for dup in duplicates]

    # Delegate to shared helper
    return format_group_lines(
        primary_file=master_file,
        secondary_files=secondary_files,
        primary_label="MASTER",
        verbose=verbose,
        file_sizes=file_sizes,
        dup_count=len(duplicates),
        cross_fs_files=cross_fs_files
    )


PREVIEW_BANNER = "=== PREVIEW MODE - Use --execute to apply changes ==="
EXECUTE_BANNER = "=== EXECUTING ==="


def format_preview_banner() -> str:
    """Return the preview mode header banner."""
    return PREVIEW_BANNER


def format_execute_banner() -> str:
    """Return the execute mode header banner."""
    return EXECUTE_BANNER


def format_confirmation_prompt(
    duplicate_count: int,
    action: str,
    space_savings: int,
    cross_fs_count: int = 0
) -> str:
    """
    Format confirmation prompt showing action summary.

    Args:
        duplicate_count: Number of duplicate files to process
        action: Action type (hardlink, symlink, delete)
        space_savings: Estimated bytes to be saved
        cross_fs_count: Number of cross-filesystem files (for hardlink with fallback)

    Returns:
        Formatted confirmation prompt string
    """
    action_verbs = {
        "hardlink": "replaced with hard links",
        "symlink": "replaced with symbolic links",
        "delete": "permanently deleted"
    }
    action_verb = action_verbs.get(action, f"processed with {action}")
    space_str = format_file_size(space_savings)

    prompt_parts = []

    # Add irreversibility warning for delete action
    if action == 'delete':
        prompt_parts.append("WARNING: This action is IRREVERSIBLE.")

    # Main prompt line
    prompt_parts.append(f"{duplicate_count} files will be {action_verb}. ~{space_str} will be saved.")

    # Add fallback note for cross-fs hardlinks
    if cross_fs_count > 0 and action == 'hardlink':
        prompt_parts.append(f"Note: {cross_fs_count} files on different filesystem will use symlink fallback.")

    prompt_parts.append("Proceed? [y/N] ")

    return "\n".join(prompt_parts)


def format_statistics_footer(
    group_count: int,
    duplicate_count: int,
    master_count: int,
    space_savings: int,
    action: str | None = None,
    verbose: bool = False,
    cross_fs_count: int = 0,
    preview_mode: bool = True
) -> list[str]:
    """
    Format the statistics footer for preview/execute output.

    Args:
        group_count: Number of duplicate groups
        duplicate_count: Total number of duplicate files
        master_count: Number of master files (preserved)
        space_savings: Bytes that would be saved
        action: Action type for action-specific messaging
        verbose: If True, show exact bytes
        cross_fs_count: Number of files that can't be hardlinked (cross-fs)
        preview_mode: If True, add hint about using --execute

    Returns:
        List of lines for the footer
    """
    lines = []
    lines.append("")  # Blank line before statistics
    lines.append("--- Statistics ---")
    lines.append(f"Duplicate groups: {group_count}")

    # Compare mode: show total files, not master/duplicate breakdown
    if action == 'compare':
        total_files = master_count + duplicate_count
        lines.append(f"Total files with matches: {total_files}")
        lines.append("Space reclaimable: (run with --action to calculate)")
        return lines

    # Action modes: show master/duplicate breakdown
    lines.append(f"Master files preserved: {master_count}")
    lines.append(f"Duplicate files: {duplicate_count}")

    # Action-specific messaging
    if action == 'hardlink':
        lines.append(f"Files to become hard links: {duplicate_count}")
        if cross_fs_count > 0:
            lines.append(f"  Warning: {cross_fs_count} files on different filesystem (cannot hardlink)")
    elif action == 'symlink':
        lines.append(f"Files to become symbolic links: {duplicate_count}")
    elif action == 'delete':
        lines.append(f"Files to be deleted: {duplicate_count}")

    # Space to be reclaimed
    space_str = format_file_size(space_savings)
    if verbose:
        lines.append(f"Space to be reclaimed: {space_str}  ({space_savings:,} bytes)")
    else:
        lines.append(f"Space to be reclaimed: {space_str}")

    # Add hint about --execute in preview mode
    if preview_mode:
        lines.append("")
        lines.append("Use --execute to apply changes")

    return lines


def calculate_space_savings(
    duplicate_groups: list[tuple[str, list[str], str, str]]
) -> tuple[int, int, int]:
    """
    Calculate space that would be saved by deduplication.

    Args:
        duplicate_groups: List of (master_file, duplicates_list, reason, hash) tuples
                         (matches output from select_master_file with hash)

    Returns:
        Tuple of (total_bytes_saved, total_duplicate_count, group_count)
    """
    if not duplicate_groups:
        return (0, 0, 0)

    total_bytes = 0
    total_duplicates = 0
    groups_with_duplicates = 0

    for master_file, duplicates, _reason, _hash in duplicate_groups:
        if not duplicates:
            continue
        # All duplicates have same size as master
        file_size = os.path.getsize(master_file)
        total_bytes += file_size * len(duplicates)
        total_duplicates += len(duplicates)
        groups_with_duplicates += 1

    return (total_bytes, total_duplicates, groups_with_duplicates)


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


def already_hardlinked(file1: str, file2: str) -> bool:
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

    # Check if already hardlinked (skip if so)
    if action == 'hardlink' and already_hardlinked(duplicate, master):
        return (True, "already linked", "skipped")

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


def format_file_size(size_bytes: int | float) -> str:
    """
    Convert file size in bytes to human-readable format.

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


def get_file_hash(filepath: str | Path, hash_algorithm: str = 'md5', fast_mode: bool = False, size_threshold: int = 100*1024*1024) -> str:
    """
    Calculate hash of file content using the specified algorithm.
    
    Args:
        filepath: Path to the file to hash
        hash_algorithm: Hashing algorithm to use ('md5' or 'sha256')
        fast_mode: If True, use faster methods for large files
        size_threshold: Size threshold (in bytes) for when to apply fast methods
    
    Returns:
        Hexadecimal digest of the hash
    """
    file_size = os.path.getsize(filepath)
    
    # For small files or when fast_mode is disabled, use the standard method
    if not fast_mode or file_size < size_threshold:
        if hash_algorithm == 'md5':
            h = hashlib.md5()  # Faster but less secure
        elif hash_algorithm == 'sha256':
            h = hashlib.sha256()  # Slower but more secure
        else:
            raise ValueError(f"Unsupported hash algorithm: {hash_algorithm}")
            
        with open(filepath, 'rb') as f:
            # Read file in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(4096), b''):
                h.update(chunk)
        return h.hexdigest()
    
    # Fast mode for large files
    else:
        # Use sparse block hashing for large files in fast mode
        return get_sparse_hash(filepath, hash_algorithm, file_size)


def get_sparse_hash(filepath: str | Path, hash_algorithm: str = 'md5', file_size: int | None = None, sample_size: int = 1024*1024) -> str:
    """
    Create a hash based on sparse sampling of a large file.
    
    Args:
        filepath: Path to the file to hash
        hash_algorithm: Hashing algorithm to use
        file_size: Size of file in bytes (will be calculated if None)
        sample_size: Size of samples to take at each position
    
    Returns:
        Hexadecimal digest of the hash
    """
    # Create the appropriate hasher
    if hash_algorithm == 'md5':
        h = hashlib.md5()
    elif hash_algorithm == 'sha256':
        h = hashlib.sha256()
    else:
        raise ValueError(f"Unsupported hash algorithm: {hash_algorithm}")
    
    if file_size is None:
        file_size = os.path.getsize(filepath)
    
    # First include the exact file size in the hash
    h.update(str(file_size).encode('utf-8'))
    
    # For very small files, hash the whole thing
    if file_size <= 3 * sample_size:
        with open(filepath, 'rb') as f:
            h.update(f.read())
        return h.hexdigest()
    
    with open(filepath, 'rb') as f:
        # Sample the beginning
        start_data = f.read(sample_size)
        h.update(start_data)
        
        # Sample from the middle
        middle_pos = file_size // 2 - sample_size // 2
        f.seek(middle_pos)
        middle_data = f.read(sample_size)
        h.update(middle_data)
        
        # Sample from near 1/4 mark
        quarter_pos = file_size // 4 - sample_size // 2
        f.seek(quarter_pos)
        quarter_data = f.read(sample_size)
        h.update(quarter_data)
        
        # Sample from near 3/4 mark
        three_quarter_pos = (file_size * 3) // 4 - sample_size // 2
        f.seek(three_quarter_pos)
        three_quarter_data = f.read(sample_size)
        h.update(three_quarter_data)
        
        # Sample the end
        f.seek(max(0, file_size - sample_size))
        end_data = f.read(sample_size)
        h.update(end_data)
    
    return h.hexdigest()


def index_directory(directory: str | Path, hash_algorithm: str = 'md5', fast_mode: bool = False, verbose: bool = False) -> dict[str, list[str]]:
    """
    Recursively index all files in a directory and its subdirectories.
    Returns a dict mapping content hashes to lists of file paths.
    
    Args:
        directory: Directory path to index
        hash_algorithm: Hashing algorithm to use
        fast_mode: If True, use faster hashing for large files
        verbose: If True, show progress for each file being processed
    """
    hash_to_files = defaultdict(list)
    directory_path = Path(directory)
    
    # Count total files first if verbose mode is enabled
    if verbose:
        total_files = sum(1 for filepath in directory_path.rglob('*') if filepath.is_file())
        processed_files = 0
        logger.debug(f"Found {total_files} files to process in {directory}")
    
    for filepath in directory_path.rglob('*'):
        if filepath.is_file():
            try:
                if verbose:
                    processed_files += 1
                    file_size = os.path.getsize(filepath)
                    size_str = format_file_size(file_size)
                    logger.debug(f"[{processed_files}/{total_files}] Processing {filepath.name} ({size_str})")

                file_hash = get_file_hash(filepath, hash_algorithm, fast_mode)
                # Store full resolved path (resolve() handles symlinks for consistent comparison)
                hash_to_files[file_hash].append(str(filepath.resolve()))
            except (PermissionError, OSError) as e:
                logger.error(f"Error processing {filepath}: {e}")
                if verbose:
                    processed_files += 1

    if verbose:
        logger.debug(f"Completed indexing {directory}: {len(hash_to_files)} unique file contents found")
    
    return hash_to_files


def find_matching_files(dir1: str | Path, dir2: str | Path, hash_algorithm: str = 'md5', fast_mode: bool = False, verbose: bool = False, different_names_only: bool = False) -> tuple[dict[str, tuple[list[str], list[str]]], list[str], list[str]]:
    """
    Find files that have identical content across two directory hierarchies.

    Args:
        dir1: First directory to scan
        dir2: Second directory to scan
        hash_algorithm: Hashing algorithm to use
        fast_mode: If True, use faster hashing for large files
        verbose: If True, show progress for each file being processed
        different_names_only: If True, only include matches where filenames differ

    Returns:
        - matches: Dict where keys are content hashes and values are tuples of (files_from_dir1, files_from_dir2)
        - unmatched1: List of files in dir1 with no content match in dir2
        - unmatched2: List of files in dir2 with no content match in dir1
    """
    if not verbose:
        logger.info(f"Indexing directory: {dir1}")
    hash_to_files1 = index_directory(dir1, hash_algorithm, fast_mode, verbose)

    if not verbose:
        logger.info(f"Indexing directory: {dir2}")
    hash_to_files2 = index_directory(dir2, hash_algorithm, fast_mode, verbose)
    
    # Find hashes that exist in both directories
    common_hashes = set(hash_to_files1.keys()) & set(hash_to_files2.keys())
    
    # Find hashes that only exist in one directory
    unique_hashes1 = set(hash_to_files1.keys()) - common_hashes
    unique_hashes2 = set(hash_to_files2.keys()) - common_hashes
    
    # Create the result data structure for matches
    matches = {}
    for file_hash in common_hashes:
        files1 = hash_to_files1[file_hash]
        files2 = hash_to_files2[file_hash]

        if different_names_only:
            # Filter to only include groups where at least one pair has different basenames
            names1 = {os.path.basename(f) for f in files1}
            names2 = {os.path.basename(f) for f in files2}
            # Skip if all files have the same name (e.g., both dirs have only "file.txt")
            if names1 == names2 and len(names1) == 1:
                continue

        matches[file_hash] = (files1, files2)
    
    # Create lists of unmatched files
    unmatched1 = []
    for file_hash in unique_hashes1:
        unmatched1.extend(hash_to_files1[file_hash])
    
    unmatched2 = []
    for file_hash in unique_hashes2:
        unmatched2.extend(hash_to_files2[file_hash])
    
    return matches, unmatched1, unmatched2


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
        warnings = []

        for file_hash, (files1, files2) in matches.items():
            all_files = files1 + files2
            master_dir_str = str(master_path)

            # Check for multiple files in master directory (warning case)
            master_files_in_group = [f for f in all_files
                                     if f.startswith(master_dir_str + os.sep) or f.startswith(master_dir_str)]
            if len(master_files_in_group) > 1:
                warnings.append(f"Warning: Multiple files in master directory have identical content: {', '.join(master_files_in_group)}")

            master_file, duplicates, reason = select_master_file(all_files, master_path)
            master_results.append((master_file, duplicates, reason, file_hash))
            total_masters += 1
            total_duplicates += len(duplicates)

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
                color_config=color_config
            )

        # Helper function to print preview output
        def print_preview_output(formatter: ActionFormatter, show_banner: bool = True) -> None:
            # Output unified header and summary line (unless --quiet)
            if not args.quiet:
                formatter.format_unified_header(args.action, args.dir1, args.dir2)
                # Calculate space savings for summary line
                # Compare mode: show 0 space savings and total matched files count
                if args.action == 'compare':
                    # For compare mode, show total files (master + duplicates) and 0 space
                    total_files = matched_files1 + matched_files2
                    formatter.format_summary_line(len(matches), total_files, 0)
                else:
                    bytes_saved, dup_count, grp_count = calculate_space_savings(master_results)
                    formatter.format_summary_line(grp_count, dup_count, bytes_saved)

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
                    bytes_saved, dup_count, grp_count = calculate_space_savings(master_results)
                    cross_fs_count = len(cross_fs_files) if args.action == 'hardlink' else 0
                    formatter.format_statistics(
                        group_count=grp_count,
                        duplicate_count=dup_count,
                        master_count=len(master_results),
                        space_savings=bytes_saved,
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
                            all_paths = [master_file] + duplicates
                            file_sizes = {p: os.path.getsize(p) for p in all_paths}

                        # Format group
                        cross_fs_to_show = cross_fs_files if args.action == 'hardlink' else None
                        formatter.format_duplicate_group(
                            master_file, duplicates,
                            action=args.action,
                            file_hash=file_hash,
                            file_sizes=file_sizes,
                            cross_fs_files=cross_fs_to_show
                        )

                        # Print blank line between groups (but not after the last one) - text mode only
                        if i < len(sorted_results) - 1 and not args.json:
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
                    bytes_saved, dup_count, grp_count = calculate_space_savings(master_results)
                    cross_fs_count = len(cross_fs_files) if args.action == 'hardlink' else 0
                    formatter.format_statistics(
                        group_count=grp_count,
                        duplicate_count=dup_count,
                        master_count=len(master_results),
                        space_savings=bytes_saved,
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
                flags = ['--execute', '--json', '--yes']
                if args.verbose:
                    flags.append('--verbose')
                if args.fallback_symlink:
                    flags.append('--fallback-symlink')
                if args.log:
                    flags.append(f'--log {args.log}')

                # Write log header
                write_log_header(audit_logger, args.dir1, args.dir2, args.dir1, args.action, flags)

                # Build hash lookup for logging
                file_hash_lookup: dict[str, str] = {}
                for file_hash, (files1, files2) in matches.items():
                    for f in files1 + files2:
                        file_hash_lookup[f] = file_hash

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
                for master_file, duplicates, reason, file_hash in sorted_results:
                    file_sizes = None
                    if args.verbose or args.json:
                        all_paths = [master_file] + duplicates
                        file_sizes = {}
                        for p in all_paths:
                            try:
                                file_sizes[p] = os.path.getsize(p)
                            except OSError:
                                file_sizes[p] = 0  # File may have been deleted/replaced
                    cross_fs_to_show = cross_fs_files if args.action == 'hardlink' else None
                    action_formatter.format_duplicate_group(
                        master_file, duplicates,
                        action=args.action,
                        file_hash=file_hash,
                        file_sizes=file_sizes,
                        cross_fs_files=cross_fs_to_show
                    )

                # Add statistics
                bytes_saved_preview, dup_count, grp_count = calculate_space_savings(master_results)
                cross_fs_count = len(cross_fs_files) if args.action == 'hardlink' else 0
                action_formatter.format_statistics(
                    group_count=grp_count,
                    duplicate_count=dup_count,
                    master_count=len(master_results),
                    space_savings=bytes_saved_preview,
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
                bytes_saved, dup_count, _ = calculate_space_savings(master_results)
                cross_fs_count = len(cross_fs_files) if args.action == 'hardlink' else 0
                prompt = format_confirmation_prompt(dup_count, args.action, bytes_saved, cross_fs_count if args.fallback_symlink else 0)
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
                flags = ['--execute']
                if args.verbose:
                    flags.append('--verbose')
                if args.yes:
                    flags.append('--yes')
                if args.fallback_symlink:
                    flags.append('--fallback-symlink')
                if args.log:
                    flags.append(f'--log {args.log}')

                # Write log header
                write_log_header(audit_logger, args.dir1, args.dir2, args.dir1, args.action, flags)

                # Build hash lookup for logging
                file_hash_lookup: dict[str, str] = {}
                for file_hash, (files1, files2) in matches.items():
                    for f in files1 + files2:
                        file_hash_lookup[f] = file_hash

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

    else:
        # Original output format (no master mode / compare mode)
        if args.json:
            compare_formatter = JsonCompareFormatter(
                verbose=args.verbose,
                dir1_name=args.dir1,
                dir2_name=args.dir2
            )
            compare_formatter.format_header(args.dir1, args.dir2, hash_algo)
        else:
            compare_formatter = TextCompareFormatter(
                verbose=args.verbose,
                dir1_name=args.dir1,
                dir2_name=args.dir2,
                color_config=color_config
            )
            # Output unified header (unless --quiet)
            if not args.quiet:
                compare_formatter.format_header(args.dir1, args.dir2, hash_algo)
                # Summary line with 0 space savings (compare mode doesn't compute it)
                compare_formatter.format_summary_line(
                    group_count=len(matches),
                    duplicate_count=matched_files1 + matched_files2,
                    space_savings=0
                )

        if args.summary:
            # Summary mode: only show statistics
            compare_formatter.format_summary(
                match_count=len(matches),
                matched_files1=matched_files1,
                matched_files2=matched_files2,
                unmatched1=len(unmatched1),
                unmatched2=len(unmatched2)
            )

            if args.show_unmatched and not args.json:
                print(f"\nUnmatched files summary:")
                print(f"  Files in {args.dir1} with no match: {len(unmatched1)}")
                print(f"  Files in {args.dir2} with no match: {len(unmatched2)}")
        else:
            # Detailed output
            if not matches:
                compare_formatter.format_empty_result(mode="compare")
            else:
                # Sort hash keys for deterministic output (OUT-04)
                for file_hash in sorted(matches.keys()):
                    files1, files2 = matches[file_hash]
                    compare_formatter.format_match_group(file_hash, files1, files2)

            # Optionally display unmatched files (detailed mode)
            if args.show_unmatched:
                compare_formatter.format_unmatched_header()
                compare_formatter.format_unmatched(args.dir1, unmatched1)
                compare_formatter.format_unmatched(args.dir2, unmatched2)

            # Add statistics footer (compare mode doesn't compute space savings)
            compare_formatter.format_statistics(
                group_count=len(matches),
                file_count=matched_files1 + matched_files2,
                space_savings=0  # Compare mode doesn't determine master/duplicate
            )

            # Always call format_summary for JSON to ensure summary field is populated
            if args.json:
                compare_formatter.format_summary(
                    match_count=len(matches),
                    matched_files1=matched_files1,
                    matched_files2=matched_files2,
                    unmatched1=len(unmatched1),
                    unmatched2=len(unmatched2)
                )

        compare_formatter.finalize()

    return 0


if __name__ == "__main__":
    sys.exit(main())