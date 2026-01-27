"""Output formatters for File Matcher CLI.

This module provides the Strategy pattern implementation for output formatting:
- ActionFormatter ABC: Abstract base class defining the formatter interface
- TextActionFormatter: Human-readable colored text output
- JsonActionFormatter: Machine-readable JSON output (accumulator pattern)

Also includes formatting helper functions:
- format_group_lines: Shared helper for group output structure
- format_duplicate_group: Format a single duplicate group
- format_confirmation_prompt: Format execution confirmation prompt
- format_statistics_footer: Format statistics section
- calculate_space_savings: Calculate space savings from duplicate groups

The formatters module depends on:
- filematcher.colors: ColorConfig, GroupLine, color helpers
- filematcher.actions: format_file_size
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
import shutil
import sys
from pathlib import Path

# Import from colors module (color system and structured types)
from filematcher.colors import (
    ColorMode,
    ColorConfig,
    GroupLine,
    red,
    cyan,
    bold_yellow,
    bold_green,
    render_group_line,
    terminal_rows_for_line,
)

# Import from actions module (file size formatting)
from filematcher.actions import format_file_size


# ============================================================================
# Structured Output Types
# ============================================================================

@dataclass
class SpaceInfo:
    """Space savings calculation results.

    Replaces tuple unpacking with named fields for clarity.
    """
    bytes_saved: int
    duplicate_count: int
    group_count: int


# ============================================================================
# Constants
# ============================================================================

PREVIEW_BANNER = "=== PREVIEW MODE - Use --execute to apply changes ==="
EXECUTE_BANNER = "=== EXECUTE MODE! ==="


# ============================================================================
# Output Formatter ABCs
# ============================================================================

class ActionFormatter(ABC):
    """Abstract base class for formatting action mode output (preview/execute).

    Action mode shows master/duplicate relationships and actions to be taken.
    """

    def __init__(self, verbose: bool = False, preview_mode: bool = True, action: str | None = None, will_execute: bool = False):
        """Initialize the formatter with configuration.

        Args:
            verbose: If True, show additional details in output
            preview_mode: If True, format for preview; if False, format for execution
            action: Action type (compare, hardlink, symlink, delete) for action-specific formatting
            will_execute: If True, execution will follow (changes labeling from "WOULD" to "WILL")
        """
        self.verbose = verbose
        self.preview_mode = preview_mode
        self._action = action
        self.will_execute = will_execute

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
        cross_fs_files: set[str] | None = None,
        group_index: int | None = None,
        total_groups: int | None = None
    ) -> None:
        """Format and output a duplicate group showing master and duplicates.

        Args:
            master_file: Path to the master file (preserved)
            duplicates: List of duplicate file paths
            action: Action type (hardlink, symlink, delete)
            file_hash: Content hash for this group (for verbose mode)
            file_sizes: Optional dict mapping paths to file sizes (for verbose mode)
            cross_fs_files: Optional set of duplicates on different filesystem
            group_index: Current group number for progress display (1-indexed)
            total_groups: Total number of groups for progress display
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


class JsonActionFormatter(ActionFormatter):
    """JSON output formatter for action mode (preview/execute).

    Implements accumulator pattern - collects data during format_* calls,
    then serializes to JSON in finalize().
    """

    def __init__(self, verbose: bool = False, preview_mode: bool = True, action: str | None = None, will_execute: bool = False):
        """Initialize the formatter with configuration.

        Args:
            verbose: If True, include additional details in output
            preview_mode: If True, mode is "preview"; if False, mode is "execute"
            action: Action type (compare, hardlink, symlink, delete)
            will_execute: If True, execution will follow (not used in JSON, but accepted for API consistency)
        """
        super().__init__(verbose, preview_mode, action, will_execute)
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
        cross_fs_files: set[str] | None = None,
        group_index: int | None = None,
        total_groups: int | None = None
    ) -> None:
        """Accumulate a duplicate group.

        Args:
            master_file: Path to the master file (preserved)
            duplicates: List of duplicate file paths
            action: Action type (hardlink, symlink, delete)
            file_hash: Content hash for this group (included in JSON)
            file_sizes: Optional dict mapping paths to file sizes
            cross_fs_files: Optional set of duplicates on different filesystem
            group_index: Ignored for JSON (no inline progress)
            total_groups: Ignored for JSON (no inline progress)
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
        # Compare mode: produce compare-compatible JSON schema
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
        color_config: ColorConfig | None = None,
        will_execute: bool = False
    ):
        """Initialize the formatter with configuration.

        Args:
            verbose: If True, show additional details in output
            preview_mode: If True, format for preview; if False, format for execution
            action: Action type (compare, hardlink, symlink, delete)
            color_config: Color configuration (default: no color)
            will_execute: If True, execution will follow (changes labeling from "WOULD" to "WILL")
        """
        super().__init__(verbose, preview_mode, action, will_execute)
        self.cc = color_config or ColorConfig(mode=ColorMode.NEVER)
        self._prev_group_row_count = 0  # Track terminal rows for inline TTY updates

    def format_banner(self) -> None:
        """Format and output the mode banner (PREVIEW or EXECUTE)."""
        if self._action == "compare":
            return  # Compare mode doesn't show PREVIEW/EXECUTING banner
        if self.will_execute:
            # Pre-execution display: show EXECUTE banner in red (execution will follow)
            print(red(EXECUTE_BANNER, self.cc))
        elif self.preview_mode:
            # PREVIEW banner in bold yellow (attention-grabbing safety warning)
            print(bold_yellow(PREVIEW_BANNER, self.cc))
        else:
            # Execute mode: show EXECUTE banner in red
            print(red(EXECUTE_BANNER, self.cc))
        print()

    def format_unified_header(self, action: str, dir1: str, dir2: str) -> None:
        """Format unified header showing mode, state, action and directories."""
        if action == "compare":
            # Compare mode: no (PREVIEW)/(EXECUTING) state indicator
            header = f"Compare mode: {dir1} vs {dir2}"
        elif self.will_execute:
            # Pre-execution display: no state indicator (execution will follow)
            header = f"Action mode: {action} {dir1} vs {dir2}"
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
        cross_fs_files: set[str] | None = None,
        group_index: int | None = None,
        total_groups: int | None = None
    ) -> None:
        """Format and output a duplicate group.

        Uses structured GroupLine objects and render_group_line for clean
        color application without string parsing.

        Colors applied based on line_type:
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
            group_index: Current group number (1-indexed) for progress display
            total_groups: Total number of groups for progress display
        """
        # Check for TTY inline progress mode using centralized TTY detection
        inline_progress = self.cc.is_tty and group_index is not None and total_groups is not None

        # Get structured GroupLine objects from format_duplicate_group
        lines: list[GroupLine] = format_duplicate_group(
            master_file=master_file,
            duplicates=duplicates,
            action=action,
            verbose=self.verbose,
            file_sizes=file_sizes,
            cross_fs_files=cross_fs_files,
            preview_mode=self.preview_mode,
            will_execute=self.will_execute
        )

        # Add hash line as GroupLine if verbose
        if self.verbose and file_hash:
            lines.append(GroupLine(
                line_type="hash",
                label="  Hash: ",
                path=f"{file_hash[:10]}..."
            ))

        # In TTY inline mode: clear previous group, add progress prefix
        if inline_progress:
            # Get terminal width for row calculation
            term_width = shutil.get_terminal_size().columns

            # Move cursor up and clear previous group rows (if not first group)
            if self._prev_group_row_count > 0:
                # Move up N rows and clear each
                for _ in range(self._prev_group_row_count):
                    sys.stdout.write('\033[A')  # Move up one row
                    sys.stdout.write('\033[K')  # Clear line
                sys.stdout.flush()

            # Add progress prefix to first line
            if lines:
                lines[0].prefix = f"[{group_index}/{total_groups}] "

        # Output lines using render_group_line for clean color application
        row_count = 0
        for line in lines:
            rendered = render_group_line(line, self.cc)
            print(rendered)
            # In TTY mode, count terminal rows (accounts for line wrapping)
            if inline_progress:
                row_count += terminal_rows_for_line(rendered, term_width)
            else:
                row_count += 1

        # Track row count for next group (TTY mode only)
        if inline_progress:
            self._prev_group_row_count = row_count

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
            preview_mode=self.preview_mode,
            will_execute=self.will_execute
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
        """Return the execute banner text (empty if already shown via will_execute)."""
        if self.will_execute:
            return ""  # Banner already shown at top of output
        return EXECUTE_BANNER

    def finalize(self) -> None:
        """Finalize output. Text output is immediate, so nothing to do."""
        pass


# ============================================================================
# Formatting Helper Functions
# ============================================================================

def format_group_lines(
    primary_file: str,
    secondary_files: list[tuple[str, str]],
    primary_label: str = "MASTER",
    verbose: bool = False,
    file_sizes: dict[str, int] | None = None,
    dup_count: int | None = None,
    cross_fs_files: set[str] | None = None
) -> list[GroupLine]:
    """
    Format group lines with unified visual structure.

    This is the shared helper for both compare mode and action mode group output.
    Returns structured GroupLine objects for clean color application.

    Args:
        primary_file: Path to the primary file (shown unindented)
        secondary_files: List of (path, label) tuples for secondary files
        primary_label: Label for the primary file (default: "MASTER")
        verbose: If True, show file size and dup count on primary line
        file_sizes: Dict mapping paths to file sizes (for verbose mode)
        dup_count: Number of duplicates (for verbose mode display)
        cross_fs_files: Set of paths on different filesystems (adds [!cross-fs] marker)

    Returns:
        List of GroupLine objects:
        - Primary line: line_type="master", label, path (with optional verbose suffix)
        - Secondary lines: line_type="duplicate", indent="    ", label, path, warning
    """
    lines: list[GroupLine] = []

    # Format primary line (LABEL: path format)
    if verbose and file_sizes:
        size = file_sizes.get(primary_file, 0)
        size_str = format_file_size(size)
        effective_dup_count = dup_count if dup_count is not None else len(secondary_files)
        path_with_info = f"{primary_file} ({effective_dup_count} duplicates, {size_str})"
    else:
        path_with_info = primary_file

    lines.append(GroupLine(
        line_type="master",
        label=f"{primary_label}: ",
        path=path_with_info
    ))

    # Format secondary lines (4-space indent, sorted alphabetically by path for determinism)
    for path, label in sorted(secondary_files, key=lambda x: x[0]):
        warning = " [!cross-fs]" if cross_fs_files and path in cross_fs_files else ""
        lines.append(GroupLine(
            line_type="duplicate",
            label=f"{label}: ",
            path=path,
            warning=warning,
            indent="    "
        ))

    return lines


def format_duplicate_group(
    master_file: str,
    duplicates: list[str],
    action: str | None = None,
    verbose: bool = False,
    file_sizes: dict[str, int] | None = None,
    cross_fs_files: set[str] | None = None,
    preview_mode: bool = True,
    will_execute: bool = False
) -> list[GroupLine]:
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
        will_execute: If True and preview_mode is True, use "WILL X" labels instead of "WOULD X"

    Returns:
        List of GroupLine objects for this group
    """
    # Determine action label based on preview_mode, will_execute, and action type
    if action == "compare":
        # Compare mode: always use DUPLICATE label (no WOULD/execution states)
        action_label = "DUPLICATE"
    elif action and preview_mode and will_execute:
        # Pre-execution display: use "WILL X" labels (execution will follow)
        action_labels = {
            "hardlink": "WILL HARDLINK",
            "symlink": "WILL SYMLINK",
            "delete": "WILL DELETE"
        }
        action_label = action_labels.get(action, f"WILL {action.upper()}")
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
    preview_mode: bool = True,
    will_execute: bool = False
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
        will_execute: If True, skip the --execute hint (execution will follow)

    Returns:
        List of lines for the footer
    """
    lines = []
    lines.append("")  # Blank line before statistics
    lines.append("--- Statistics ---")
    lines.append(f"Total files with matches: {master_count + duplicate_count}")
    lines.append(f"Duplicate groups: {group_count}")

    if action != 'compare':
        # Action modes: show master/duplicate breakdown
        lines.append(f"Master files preserved: {master_count}")
        lines.append(f"Duplicate files: {duplicate_count}")

    # Space to be reclaimed
    space_str = format_file_size(space_savings)
    if verbose:
        lines.append(f"Space to be reclaimed: {space_str}  ({space_savings:,} bytes)")
    else:
        lines.append(f"Space to be reclaimed: {space_str}")

    # Add hint about next steps
    if action == 'compare':
        lines.append("")
        lines.append("Use --action to deduplicate (hardlink, symlink, or delete)")
    elif preview_mode and not will_execute:
        # Only show --execute hint in true preview mode (not when execution will follow)
        lines.append("")
        lines.append("Use --execute to apply changes")

    return lines


def calculate_space_savings(
    duplicate_groups: list[tuple[str, list[str], str, str]]
) -> SpaceInfo:
    """
    Calculate space that would be saved by deduplication.

    Args:
        duplicate_groups: List of (master_file, duplicates_list, reason, hash) tuples
                         (matches output from select_master_file with hash)

    Returns:
        SpaceInfo with bytes_saved, duplicate_count, group_count
    """
    if not duplicate_groups:
        return SpaceInfo(0, 0, 0)

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

    return SpaceInfo(total_bytes, total_duplicates, groups_with_duplicates)
