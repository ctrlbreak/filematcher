"""Output formatters for File Matcher CLI.

Provides ActionFormatter ABC with two implementations:
- TextActionFormatter: Human-readable colored text output
- JsonActionFormatter: Machine-readable JSON output (accumulator pattern)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import shutil

logger = logging.getLogger(__name__)

# Import from colors module (color system and structured types)
from filematcher.colors import (
    ColorMode,
    ColorConfig,
    GroupLine,
    dim,
    green,
    yellow,
    red,
    cyan,
    bold,
    bold_yellow,
    bold_green,
    render_group_line,
    terminal_rows_for_line,
)

from filematcher.types import Action, DuplicateGroup, FailedOperation

# Import from actions module (file size formatting)
from filematcher.actions import format_file_size


def compute_target_path(duplicate: str, target_dir: str, dir2_base: str) -> str | None:
    """Compute the target path for a duplicate when using --target-dir."""
    try:
        dup_path = Path(duplicate).resolve()
        dir2_path = Path(dir2_base).resolve()
        rel_path = dup_path.relative_to(dir2_path)
        return str(Path(target_dir) / rel_path)
    except ValueError:
        return None


@dataclass
class SpaceInfo:
    """Space savings calculation results.

    Replaces tuple unpacking with named fields for clarity.
    """
    bytes_saved: int
    duplicate_count: int
    group_count: int


PREVIEW_BANNER = "=== PREVIEW MODE - Use --execute to apply changes ==="
BANNER_SEPARATOR = "-" * 40


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
    def format_banner(
        self,
        action: str,
        group_count: int,
        duplicate_count: int,
        space_bytes: int
    ) -> None:
        """Output the mode banner with action statistics.

        Args:
            action: Action type (hardlink, symlink, delete)
            group_count: Number of duplicate groups
            duplicate_count: Total number of duplicate files
            space_bytes: Space in bytes to be saved
        """
        ...

    @abstractmethod
    def format_warnings(self, warnings: list[str]) -> None:
        """Output warning messages."""
        ...

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
        total_groups: int | None = None,
        target_dir: str | None = None,
        dir2_base: str | None = None
    ) -> None:
        """Output a duplicate group showing master and duplicates."""
        ...

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
        """Output statistics footer."""
        ...

    @abstractmethod
    def format_execution_summary(
        self,
        success_count: int,
        failure_count: int,
        skipped_count: int,
        space_saved: int,
        log_path: str,
        failed_list: list[FailedOperation],
        confirmed_count: int = 0,
        user_skipped_count: int = 0
    ) -> None:
        """Output execution summary after actions complete.

        Args:
            success_count: Number of files successfully processed
            failure_count: Number of files that failed
            skipped_count: Number of files skipped (already linked)
            space_saved: Total bytes saved
            log_path: Path to audit log file
            failed_list: List of failed operations with paths and errors
            confirmed_count: Number of groups user confirmed (y/a)
            user_skipped_count: Number of groups user skipped (n)
        """
        ...

    @abstractmethod
    def format_empty_result(self) -> None:
        """Output message when no duplicates found."""
        ...

    @abstractmethod
    def format_user_abort(self) -> None:
        """Output message when user aborts execution."""
        ...

    @abstractmethod
    def format_execute_prompt_separator(self) -> None:
        """Output separator before execute prompt."""
        ...

    @abstractmethod
    def format_compare_summary(
        self,
        match_count: int,
        matched_files1: int,
        matched_files2: int,
        dir1_name: str,
        dir2_name: str
    ) -> None:
        """Output compare mode summary."""
        ...

    @abstractmethod
    def format_unmatched_section(
        self,
        dir1_label: str,
        unmatched1: list[str],
        dir2_label: str,
        unmatched2: list[str]
    ) -> None:
        """Output the unmatched files section."""
        ...

    @abstractmethod
    def finalize(self) -> None:
        """Finalize output (flush buffers, print JSON, etc.)."""
        ...

    @abstractmethod
    def format_group_prompt(
        self,
        group_index: int,
        total_groups: int,
        action: str
    ) -> str:
        """Format the interactive prompt for a duplicate group.

        Args:
            group_index: Current group number (1-indexed)
            total_groups: Total number of groups
            action: Action type (delete, hardlink, symlink)

        Returns:
            Prompt string for input() call. Caller handles actual prompting.
        """
        ...

    @abstractmethod
    def format_confirmation_status(self, confirmed: bool, lines_back: int = 0, has_prompt: bool = True) -> None:
        """Output confirmation symbol after user decision.

        Args:
            confirmed: True for checkmark (confirmed), False for X (skipped)
            lines_back: Deprecated, ignored by TextActionFormatter.
                       Terminal rows are calculated automatically.
            has_prompt: True if a prompt line was shown (normal interactive mode),
                       False if no prompt (auto-confirm mode). Affects cursor positioning.
        """
        ...

    @abstractmethod
    def format_remaining_count(self, remaining: int) -> None:
        """Output message after 'a' (all) response.

        Shows how many groups will be processed automatically.
        """
        ...

    @abstractmethod
    def format_file_error(self, file_path: str, error: str) -> None:
        """Output error message for a failed file operation.

        Args:
            file_path: Path to the file that failed
            error: System error message (e.g., "Permission denied")
        """
        ...

    @abstractmethod
    def format_quit_summary(
        self,
        confirmed_count: int,
        skipped_count: int,
        remaining_count: int,
        space_saved: int,
        log_path: str
    ) -> None:
        """Display summary when user quits early via 'q' or Ctrl+C.

        Args:
            confirmed_count: Number of groups processed
            skipped_count: Number of groups user skipped with 'n'
            remaining_count: Number of groups not yet started
            space_saved: Bytes freed before quit
            log_path: Path to audit log file
        """
        ...


class JsonActionFormatter(ActionFormatter):
    """JSON output formatter using accumulator pattern."""

    def __init__(self, verbose: bool = False, preview_mode: bool = True, action: str | None = None, will_execute: bool = False):
        super().__init__(verbose, preview_mode, action, will_execute)
        self._data: dict = {
            "warnings": [],
            "duplicateGroups": [],
            "statistics": {}
        }
        # Track directories separately for header construction
        self._master_dir = ""
        self._duplicate_dir = ""
        # Track action type for execution results
        self._action_type = ""
        # Track hash algorithm for compare mode JSON
        self._hash_algorithm = "md5"
        # Track metadata for verbose mode (compare mode compatible)
        self._metadata: dict[str, dict] = {}

    def _build_header(self, mode: str, action: str | None = None) -> dict:
        """Build the header object with run metadata.

        Args:
            mode: One of "compare", "preview", or "execute"
            action: Action type (only included for non-compare modes)

        Returns:
            Header dictionary with name, version, timestamp, mode, hashAlgorithm, directories
        """
        header: dict = {
            "name": "filematcher",
            "version": "2.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": mode,
            "hashAlgorithm": self._hash_algorithm,
            "directories": {
                "master": self._master_dir,
                "duplicate": self._duplicate_dir
            }
        }
        if action and mode != "compare":
            header["action"] = action
        return header

    # No-op in JSON mode (data captured in structure)
    def format_banner(
        self,
        action: str,
        group_count: int,
        duplicate_count: int,
        space_bytes: int
    ) -> None:
        pass

    def format_warnings(self, warnings: list[str]) -> None:
        self._data["warnings"] = list(warnings)

    def format_duplicate_group(
        self,
        master_file: str,
        duplicates: list[str],
        action: str,
        file_hash: str | None = None,
        file_sizes: dict[str, int] | None = None,
        cross_fs_files: set[str] | None = None,
        group_index: int | None = None,
        total_groups: int | None = None,
        target_dir: str | None = None,
        dir2_base: str | None = None
    ) -> None:
        self._action_type = action
        sorted_duplicates = sorted(duplicates)
        dup_objects = []
        for dup in sorted_duplicates:
            dup_obj: dict = {
                "path": dup,
                "action": action,
                "crossFilesystem": cross_fs_files is not None and dup in cross_fs_files
            }
            if file_sizes and dup in file_sizes:
                dup_obj["sizeBytes"] = file_sizes[dup]
            else:
                try:
                    dup_obj["sizeBytes"] = os.path.getsize(dup)
                except OSError as e:
                    logger.debug(f"Could not get size for {dup}: {e}")
                    dup_obj["sizeBytes"] = 0
            if target_dir and dir2_base:
                target_path = compute_target_path(dup, target_dir, dir2_base)
                if target_path:
                    dup_obj["targetPath"] = target_path
            dup_objects.append(dup_obj)

        group: dict = {
            "masterFile": master_file,
            "duplicates": dup_objects
        }
        if file_hash:
            group["hash"] = file_hash
        self._data["duplicateGroups"].append(group)

        if self.verbose:
            all_files = [master_file] + sorted_duplicates
            for f in all_files:
                try:
                    stat = os.stat(f)
                    self._metadata[f] = {
                        "sizeBytes": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()
                    }
                except OSError as e:
                    logger.debug(f"Could not get metadata for {f}: {e}")

    def format_statistics(
        self,
        group_count: int,
        duplicate_count: int,
        master_count: int,
        space_savings: int,
        action: str,
        cross_fs_count: int = 0
    ) -> None:
        self._action_type = action
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
        failed_list: list[FailedOperation],
        confirmed_count: int = 0,
        user_skipped_count: int = 0
    ) -> None:
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
            "failures": failures,
            "userConfirmedCount": confirmed_count,
            "userSkippedCount": user_skipped_count
        }

    def set_directories(self, master_dir: str, duplicate_dir: str) -> None:
        self._master_dir = str(Path(master_dir).resolve())
        self._duplicate_dir = str(Path(duplicate_dir).resolve())

    def set_hash_algorithm(self, algorithm: str) -> None:
        self._hash_algorithm = algorithm

    def format_empty_result(self) -> None: pass

    def format_compare_summary(
        self,
        match_count: int,
        matched_files1: int,
        matched_files2: int,
        dir1_name: str,
        dir2_name: str
    ) -> None:
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
        self._data["unmatchedMaster"] = sorted(unmatched1)
        self._data["unmatchedDuplicate"] = sorted(unmatched2)
        if "summary" not in self._data:
            self._data["summary"] = {}
        self._data["summary"]["unmatchedFilesMaster"] = len(unmatched1)
        self._data["summary"]["unmatchedFilesDuplicate"] = len(unmatched2)

        if self.verbose:
            for f in unmatched1 + unmatched2:
                try:
                    stat = os.stat(f)
                    self._metadata[f] = {
                        "sizeBytes": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()
                    }
                except OSError as e:
                    logger.debug(f"Could not get metadata for {f}: {e}")

    # No-ops for JSON mode
    def format_user_abort(self) -> None: pass
    def format_execute_prompt_separator(self) -> None: pass

    def format_group_prompt(
        self,
        group_index: int,
        total_groups: int,
        action: str
    ) -> str:
        # JSON mode never prompts interactively
        return ""

    def format_confirmation_status(self, confirmed: bool, lines_back: int = 0, has_prompt: bool = True) -> None:
        # No-op: JSON mode doesn't show inline status
        pass

    def format_remaining_count(self, remaining: int) -> None:
        # No-op: JSON mode doesn't show inline messages
        pass

    def format_file_error(self, file_path: str, error: str) -> None:
        """Accumulate error in errors array."""
        if "errors" not in self._data:
            self._data["errors"] = []
        self._data["errors"].append({"path": file_path, "error": error})

    def format_quit_summary(
        self,
        confirmed_count: int,
        skipped_count: int,
        remaining_count: int,
        space_saved: int,
        log_path: str
    ) -> None:
        """Add quit status to data for JSON output."""
        self._data["quit"] = {
            "processedCount": confirmed_count,
            "skippedCount": skipped_count,
            "remainingCount": remaining_count,
            "spaceSavedBytes": space_saved,
            "logPath": log_path
        }

    def _convert_statistics_to_summary(self) -> dict:
        stats = self._data.get("statistics", {})
        return {
            "matchCount": stats.get("groupCount", 0),
            "matchedFilesMaster": stats.get("duplicateCount", 0),
            "matchedFilesDuplicate": stats.get("duplicateCount", 0),
            "unmatchedFilesMaster": 0,
            "unmatchedFilesDuplicate": 0
        }

    def finalize(self) -> None:
        """Finalize output by sorting collections and printing JSON."""
        if self._action == "compare":
            # Convert to compare-mode JSON schema with header
            matches = []
            total_files = 0
            for group in self._data.get("duplicateGroups", []):
                master = group.get("masterFile", "")
                duplicates = [d["path"] for d in group.get("duplicates", [])]
                match_entry = {
                    "hash": group.get("hash", ""),
                    "filesMaster": [master],
                    "filesDuplicate": sorted(duplicates)
                }
                matches.append(match_entry)
                total_files += 1 + len(duplicates)

            matches.sort(key=lambda m: m["filesMaster"][0] if m["filesMaster"] else "")

            # Build header for compare mode
            header = self._build_header(mode="compare")

            compare_data: dict = {
                "header": header,
                "matches": matches,
                "unmatchedMaster": self._data.get("unmatchedMaster", []),
                "unmatchedDuplicate": self._data.get("unmatchedDuplicate", []),
                "summary": self._convert_statistics_to_summary()
            }

            if "summary" in self._data and "unmatchedFilesMaster" in self._data["summary"]:
                compare_data["summary"]["unmatchedFilesMaster"] = self._data["summary"]["unmatchedFilesMaster"]
                compare_data["summary"]["unmatchedFilesDuplicate"] = self._data["summary"]["unmatchedFilesDuplicate"]

            if self.verbose and self._metadata:
                compare_data["metadata"] = self._metadata

            group_count = len(matches)
            compare_data["statistics"] = {
                "duplicateGroups": group_count,
                "totalFilesWithMatches": total_files,
                "spaceReclaimable": 0,  # Compare mode doesn't compute space
                "spaceReclaimableFormatted": None
            }

            print(json.dumps(compare_data, indent=2))
            return

        # Action modes: build header and sort for determinism
        mode = "preview" if self.preview_mode else "execute"
        header = self._build_header(mode=mode, action=self._action_type)

        self._data["duplicateGroups"].sort(key=lambda g: g["masterFile"])
        for group in self._data["duplicateGroups"]:
            group["duplicates"].sort(key=lambda d: d["path"])

        # Build action mode output with header at top
        output_data: dict = {
            "header": header,
            "warnings": self._data.get("warnings", []),
            "duplicateGroups": self._data["duplicateGroups"],
            "statistics": self._data.get("statistics", {})
        }

        # Add execution summary if present (execute mode)
        if "execution" in self._data:
            output_data["execution"] = self._data["execution"]

        # Add errors array if present (operation failures)
        if "errors" in self._data:
            output_data["errors"] = self._data["errors"]

        # Add quit status if present (user quit early)
        if "quit" in self._data:
            output_data["quit"] = self._data["quit"]

        print(json.dumps(output_data, indent=2))


class TextActionFormatter(ActionFormatter):
    """Text output formatter with color support."""

    def __init__(
        self,
        verbose: bool = False,
        preview_mode: bool = True,
        action: str | None = None,
        color_config: ColorConfig | None = None,
        will_execute: bool = False
    ):
        super().__init__(verbose, preview_mode, action, will_execute)
        self.cc = color_config or ColorConfig(mode=ColorMode.NEVER)
        # Track terminal rows for cursor movement in interactive mode
        self._last_duplicate_rows: int = 0

    def format_banner(
        self,
        action: str,
        group_count: int,
        duplicate_count: int,
        space_bytes: int
    ) -> None:
        """Output unified banner with statistics and mode indicator."""
        print()  # Separator from scanning phase output
        action_bold = bold(action, self.cc)
        space_str = format_file_size(space_bytes)

        if action == "compare":
            # Compare mode: informational, no action taken
            banner = f"{action_bold} mode: {group_count} groups, {duplicate_count} files, {space_str} reclaimable"
            mode_indicator = cyan(" (COMPARE)", self.cc)
            print(banner + mode_indicator)
            print(BANNER_SEPARATOR)
            return

        # Action modes (hardlink/symlink/delete)
        banner = f"{action_bold} mode: {group_count} groups, {duplicate_count} files, {space_str} to save"

        # Add mode indicator
        if self.will_execute:
            mode_indicator = red(" (EXECUTE)", self.cc)
        else:
            mode_indicator = yellow(" (PREVIEW)", self.cc)

        print(banner + mode_indicator)
        print(BANNER_SEPARATOR)

        # Show preview hint if in preview mode
        if not self.will_execute and self.preview_mode:
            print(dim("Use --execute to apply changes", self.cc))
            print()

    def format_warnings(self, warnings: list[str]) -> None:
        for warning in warnings:
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
        total_groups: int | None = None,
        target_dir: str | None = None,
        dir2_base: str | None = None
    ) -> None:
        lines: list[GroupLine] = format_duplicate_group(
            master_file=master_file,
            duplicates=duplicates,
            action=action,
            verbose=self.verbose,
            file_sizes=file_sizes,
            cross_fs_files=cross_fs_files,
            preview_mode=self.preview_mode,
            will_execute=self.will_execute,
            target_dir=target_dir,
            dir2_base=dir2_base
        )

        if self.verbose and file_hash:
            lines.append(GroupLine(line_type="hash", label="  Hash: ", path=f"{file_hash[:10]}..."))

        # Add group index prefix to first line if provided
        if group_index is not None and total_groups is not None and lines:
            lines[0].prefix = f"[{group_index}/{total_groups}] "

        # Track terminal rows for non-master lines (for cursor movement)
        term_width = shutil.get_terminal_size().columns
        self._last_duplicate_rows = 0
        for line in lines:
            rendered = render_group_line(line, self.cc)
            print(rendered)
            # Count rows for non-master lines (duplicates and hash)
            if line.line_type != "master":
                self._last_duplicate_rows += terminal_rows_for_line(rendered, term_width)

    def format_statistics(
        self,
        group_count: int,
        duplicate_count: int,
        master_count: int,
        space_savings: int,
        action: str,
        cross_fs_count: int = 0
    ) -> None:
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
        failed_list: list[FailedOperation],
        confirmed_count: int = 0,
        user_skipped_count: int = 0
    ) -> None:
        print()
        print("Execution complete:")
        print(f"  User confirmed: {confirmed_count}")
        print(f"  User skipped: {user_skipped_count}")
        print(f"  Succeeded: {success_count}")
        print(f"  Failed: {failure_count}")
        if skipped_count > 0:
            print(f"  Already linked: {skipped_count}")
        print(f"  Space freed: {format_file_size(space_saved)} ({space_saved:,} bytes)")
        print(f"  Audit log: {log_path}")
        if failed_list:
            print()
            print("Failed files:")
            x_mark = red("\u2717", self.cc)
            for path, error in sorted(failed_list):
                print(f"  {x_mark} {path}: {error}")

    def format_empty_result(self) -> None:
        print("No matching files found." if self._action == "compare" else "No duplicates found.")

    def format_compare_summary(
        self,
        match_count: int,
        matched_files1: int,
        matched_files2: int,
        dir1_name: str,
        dir2_name: str
    ) -> None:
        print("\nMatched files summary:")
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
        print("Aborted. No changes made.")

    def format_execute_prompt_separator(self) -> None:
        print()

    def finalize(self) -> None:
        pass

    def format_group_prompt(
        self,
        group_index: int,
        total_groups: int,
        action: str
    ) -> str:
        """Format interactive prompt with progress and action verb."""
        verb = _ACTION_PROMPT_VERBS.get(Action(action), f"Process {action}?")
        progress = dim(f"[{group_index}/{total_groups}]", self.cc)
        return f"{progress} {verb} [y/n/a/q] "

    def format_confirmation_status(self, confirmed: bool, lines_back: int = 0, has_prompt: bool = True) -> None:
        """Output checkmark or X after user response.

        Args:
            confirmed: True for checkmark (confirmed), False for X (skipped)
            lines_back: Deprecated, ignored. Terminal rows are now calculated
                       automatically based on the last displayed group.
            has_prompt: True if a prompt line was shown (normal interactive mode),
                       False if no prompt (auto-confirm mode). Affects cursor positioning.
        """
        if confirmed:
            symbol = green("\u2713", self.cc)
        else:
            symbol = red("\u2717", self.cc)

        # Use tracked terminal rows from last group
        # Add +1 for prompt line only if a prompt was shown
        prompt_offset = 1 if has_prompt else 0
        rows_up = self._last_duplicate_rows + prompt_offset if self._last_duplicate_rows > 0 else 0

        if rows_up > 0:
            # Move cursor up, print status at start of line
            # \033[nA = move cursor up n lines
            # \r = carriage return to start of line
            # \033[nB = move cursor down n lines
            # \033[K = clear from cursor to end of line
            if has_prompt:
                # Move up to duplicate line, print status, move down to prompt line, clear it
                print(f"\033[{rows_up}A\r{symbol}   \033[{rows_up - 1}B\r\033[K", end="")
                # Cursor now at start of cleared prompt line - next output overwrites it
            else:
                # No prompt line - move up to duplicate line, print status, move back down
                # End with \r to return cursor to column 0 for next group
                print(f"\033[{rows_up}A\r{symbol}   \033[{rows_up}B\r", end="", flush=True)
        else:
            # Fallback: print on current line
            print(symbol)

    def format_remaining_count(self, remaining: int) -> None:
        """Output message after 'a' (all) response."""
        print(f"Processing {remaining} remaining groups...")

    def format_file_error(self, file_path: str, error: str) -> None:
        """Print indented error line with red X marker."""
        x_mark = red("\u2717", self.cc)
        print(f"  {x_mark} {file_path}: {error}")

    def format_quit_summary(
        self,
        confirmed_count: int,
        skipped_count: int,
        remaining_count: int,
        space_saved: int,
        log_path: str
    ) -> None:
        """Print quit message block with processing summary."""
        print()
        print(f"Quit: {confirmed_count} processed, {skipped_count} skipped, {remaining_count} remaining")
        if space_saved > 0:
            print(f"Freed {format_file_size(space_saved)} (quit before completing all)")
        print("Re-run command to process remaining files")
        print(f"Audit log: {log_path}")


# Helper functions

def format_group_lines(
    primary_file: str,
    secondary_files: list[tuple[str, str]],
    primary_label: str = "MASTER",
    verbose: bool = False,
    file_sizes: dict[str, int] | None = None,
    dup_count: int | None = None,
    cross_fs_files: set[str] | None = None
) -> list[GroupLine]:
    """Format group lines returning structured GroupLine objects."""
    lines: list[GroupLine] = []

    if verbose and file_sizes:
        size = file_sizes.get(primary_file, 0)
        size_str = format_file_size(size)
        effective_dup_count = dup_count if dup_count is not None else len(secondary_files)
        path_with_info = f"{primary_file} ({effective_dup_count} duplicates, {size_str})"
    else:
        path_with_info = primary_file

    lines.append(GroupLine(line_type="master", label=f"{primary_label}: ", path=path_with_info))

    for path, label in sorted(secondary_files, key=lambda x: x[0]):
        warning = " [!cross-fs]" if cross_fs_files and path in cross_fs_files else ""
        lines.append(GroupLine(line_type="duplicate", label=f"{label}: ", path=path, warning=warning, indent="    "))

    return lines


# Action label mappings for duplicate groups
_WOULD_LABELS = {"hardlink": "WOULD HARDLINK", "symlink": "WOULD SYMLINK", "delete": "WOULD DELETE"}
_WILL_LABELS = {"hardlink": "WILL HARDLINK", "symlink": "WILL SYMLINK", "delete": "WILL DELETE"}


def format_duplicate_group(
    master_file: str,
    duplicates: list[str],
    action: str | None = None,
    verbose: bool = False,
    file_sizes: dict[str, int] | None = None,
    cross_fs_files: set[str] | None = None,
    preview_mode: bool = True,
    will_execute: bool = False,
    target_dir: str | None = None,
    dir2_base: str | None = None
) -> list[GroupLine]:
    """Format a duplicate group returning structured GroupLine objects."""
    if action == "compare":
        action_label = "DUPLICATE"
    elif action and preview_mode and will_execute:
        action_label = _WILL_LABELS.get(action, f"WILL {action.upper()}")
    elif action and preview_mode:
        action_label = _WOULD_LABELS.get(action, f"WOULD {action.upper()}")
    elif action:
        action_label = f"DUP:{action}"
    else:
        action_label = "DUP:?"

    # When target_dir is specified, show target paths instead of duplicate paths
    if target_dir and dir2_base:
        secondary_files = []
        for dup in duplicates:
            target_path = compute_target_path(dup, target_dir, dir2_base)
            display_path = target_path if target_path else dup
            secondary_files.append((display_path, action_label))
    else:
        secondary_files = [(dup, action_label) for dup in duplicates]

    return format_group_lines(
        primary_file=master_file,
        secondary_files=secondary_files,
        primary_label="MASTER",
        verbose=verbose,
        file_sizes=file_sizes,
        dup_count=len(duplicates),
        cross_fs_files=cross_fs_files
    )


_ACTION_PROMPT_VERBS = {
    Action.DELETE: "Delete duplicate?",
    Action.HARDLINK: "Create hardlink?",
    Action.SYMLINK: "Create symlink?",
}


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
    """Format the statistics footer for preview/execute output."""
    lines = ["", "--- Statistics ---"]
    lines.append(f"Total files with matches: {master_count + duplicate_count}")
    lines.append(f"Duplicate groups: {group_count}")

    if action != 'compare':
        lines.append(f"Master files preserved: {master_count}")
        lines.append(f"Duplicate files: {duplicate_count}")

    space_str = format_file_size(space_savings)
    if verbose:
        lines.append(f"Space to be reclaimed: {space_str}  ({space_savings:,} bytes)")
    else:
        lines.append(f"Space to be reclaimed: {space_str}")

    if action == Action.COMPARE:
        lines.extend(["", "Use --action to deduplicate (hardlink, symlink, or delete)"])
    elif preview_mode and not will_execute:
        lines.extend(["", "Use --execute to apply changes"])

    return lines


def calculate_space_savings(
    duplicate_groups: list[DuplicateGroup]
) -> SpaceInfo:
    """Calculate space that would be saved by deduplication."""
    if not duplicate_groups:
        return SpaceInfo(0, 0, 0)

    total_bytes = 0
    total_duplicates = 0
    groups_with_duplicates = 0

    for master_file, duplicates, _reason, _hash in duplicate_groups:
        if duplicates:
            file_size = os.path.getsize(master_file)
            total_bytes += file_size * len(duplicates)
            total_duplicates += len(duplicates)
            groups_with_duplicates += 1

    return SpaceInfo(total_bytes, total_duplicates, groups_with_duplicates)
