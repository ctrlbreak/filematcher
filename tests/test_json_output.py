#!/usr/bin/env python3
"""Tests for JSON output functionality (--json flag).

These tests verify that the --json flag produces valid, correctly-structured
JSON output for both compare mode and action mode.
"""

from __future__ import annotations

import io
import json
import os
import re
import subprocess
import unittest
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from file_matcher import main
from tests.test_base import BaseFileMatcherTest


class TestJsonOutput(BaseFileMatcherTest):
    """Test JSON output in compare mode."""

    def run_with_json(self, *args) -> tuple[str, str, int]:
        """Helper to run file_matcher with --json and return (stdout, stderr, exit_code)."""
        cmd = ['python3', 'file_matcher.py', '--json'] + list(args)
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout, result.stderr, result.returncode

    def run_main_with_json(self, extra_args: list[str] | None = None) -> tuple[dict, str, int]:
        """Helper to run main() with --json and parse output.

        Returns:
            Tuple of (parsed_json, stderr_output, exit_code)
        """
        args = ['filematcher', self.test_dir1, self.test_dir2, '--json']
        if extra_args:
            args.extend(extra_args)

        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        with patch('sys.argv', args):
            with redirect_stdout(stdout_capture):
                with redirect_stderr(stderr_capture):
                    exit_code = main()

        stdout_val = stdout_capture.getvalue()
        stderr_val = stderr_capture.getvalue()

        # Parse JSON from stdout
        if stdout_val.strip():
            data = json.loads(stdout_val)
        else:
            data = {}

        return data, stderr_val, exit_code

    # =========================================================================
    # Basic Structure Tests
    # =========================================================================

    def test_json_output_is_valid_json(self):
        """Output parses as valid JSON."""
        data, stderr, exit_code = self.run_main_with_json()
        self.assertEqual(exit_code, 0)
        # If we got here without json.loads throwing, it's valid JSON
        self.assertIsInstance(data, dict)

    def test_json_has_required_fields(self):
        """JSON has all required top-level fields: timestamp, directories, hashAlgorithm, matches, summary."""
        data, stderr, exit_code = self.run_main_with_json()
        self.assertEqual(exit_code, 0)

        required_fields = ['timestamp', 'directories', 'hashAlgorithm', 'matches', 'summary']
        for field in required_fields:
            self.assertIn(field, data, f"Missing required field: {field}")

    def test_json_timestamp_format(self):
        """Timestamp is in RFC 3339 / ISO 8601 format."""
        data, stderr, exit_code = self.run_main_with_json()
        self.assertEqual(exit_code, 0)

        timestamp = data['timestamp']
        # RFC 3339 format: YYYY-MM-DDTHH:MM:SS with optional fractional seconds and timezone
        # Examples: 2026-01-23T10:30:00+00:00 or 2026-01-23T10:30:00.123456+00:00
        rfc3339_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(\+\d{2}:\d{2}|Z)?$'
        self.assertRegex(timestamp, rfc3339_pattern, f"Timestamp not RFC 3339: {timestamp}")

        # Verify it's parseable
        try:
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            self.fail(f"Timestamp not parseable as ISO format: {timestamp}")

    def test_json_directories_absolute_paths(self):
        """Directory paths in JSON are absolute."""
        data, stderr, exit_code = self.run_main_with_json()
        self.assertEqual(exit_code, 0)

        dir1 = data['directories']['dir1']
        dir2 = data['directories']['dir2']

        self.assertTrue(os.path.isabs(dir1), f"dir1 not absolute: {dir1}")
        self.assertTrue(os.path.isabs(dir2), f"dir2 not absolute: {dir2}")

    # =========================================================================
    # Compare Mode Tests
    # =========================================================================

    def test_json_matches_structure(self):
        """Each match has hash, filesDir1, filesDir2."""
        data, stderr, exit_code = self.run_main_with_json()
        self.assertEqual(exit_code, 0)

        self.assertIsInstance(data['matches'], list)

        # Should have at least one match based on test fixtures
        self.assertGreater(len(data['matches']), 0, "Expected at least one match")

        for match in data['matches']:
            self.assertIn('hash', match)
            self.assertIn('filesDir1', match)
            self.assertIn('filesDir2', match)
            self.assertIsInstance(match['hash'], str)
            self.assertIsInstance(match['filesDir1'], list)
            self.assertIsInstance(match['filesDir2'], list)

    def test_json_unmatched_with_flag(self):
        """--show-unmatched includes unmatched file arrays."""
        data, stderr, exit_code = self.run_main_with_json(['--show-unmatched'])
        self.assertEqual(exit_code, 0)

        # Should have unmatched arrays
        self.assertIn('unmatchedDir1', data)
        self.assertIn('unmatchedDir2', data)
        self.assertIsInstance(data['unmatchedDir1'], list)
        self.assertIsInstance(data['unmatchedDir2'], list)

        # Based on test fixtures, there should be unmatched files
        # file2.txt in dir1 has unique content, file4.txt in dir2 has unique content
        total_unmatched = len(data['unmatchedDir1']) + len(data['unmatchedDir2'])
        self.assertGreater(total_unmatched, 0, "Expected unmatched files in test fixtures")

    def test_json_unmatched_without_flag(self):
        """Without --show-unmatched, unmatched arrays are empty."""
        data, stderr, exit_code = self.run_main_with_json()
        self.assertEqual(exit_code, 0)

        # Arrays should exist but be empty when not requested
        self.assertEqual(data['unmatchedDir1'], [])
        self.assertEqual(data['unmatchedDir2'], [])

    def test_json_summary_only(self):
        """--summary mode produces output with summary statistics."""
        data, stderr, exit_code = self.run_main_with_json(['--summary'])
        self.assertEqual(exit_code, 0)

        # Summary should have expected fields
        self.assertIn('summary', data)
        summary = data['summary']
        self.assertIn('matchCount', summary)
        self.assertIn('matchedFilesDir1', summary)
        self.assertIn('matchedFilesDir2', summary)

    def test_json_verbose_includes_metadata(self):
        """--verbose adds file metadata (size, modified time)."""
        data, stderr, exit_code = self.run_main_with_json(['--verbose'])
        self.assertEqual(exit_code, 0)

        # With verbose mode, should have metadata field
        self.assertIn('metadata', data)
        metadata = data['metadata']
        self.assertIsInstance(metadata, dict)

        # Each metadata entry should have sizeBytes and modified
        if metadata:  # Only check if there's metadata
            for filepath, info in metadata.items():
                self.assertIn('sizeBytes', info)
                self.assertIn('modified', info)
                self.assertIsInstance(info['sizeBytes'], int)
                self.assertIsInstance(info['modified'], str)

    # =========================================================================
    # Action Mode Tests
    # =========================================================================

    def test_json_action_mode_structure(self):
        """Action mode JSON has mode, action, duplicateGroups."""
        data, stderr, exit_code = self.run_main_with_json(['--action', 'hardlink'])
        self.assertEqual(exit_code, 0)

        self.assertIn('mode', data)
        self.assertIn('action', data)
        self.assertIn('duplicateGroups', data)

        self.assertEqual(data['action'], 'hardlink')
        self.assertIsInstance(data['duplicateGroups'], list)

    def test_json_action_preview_mode(self):
        """Mode is 'preview' when --execute is not used."""
        data, stderr, exit_code = self.run_main_with_json(['--action', 'hardlink'])
        self.assertEqual(exit_code, 0)

        self.assertEqual(data['mode'], 'preview')

    def test_json_action_execute_mode(self):
        """Mode is 'execute' when --execute --yes is used."""
        data, stderr, exit_code = self.run_main_with_json(['--action', 'hardlink', '--execute', '--yes'])
        self.assertEqual(exit_code, 0)

        self.assertEqual(data['mode'], 'execute')
        # Should have execution summary
        self.assertIn('execution', data)
        exec_info = data['execution']
        self.assertIn('successCount', exec_info)
        self.assertIn('failureCount', exec_info)
        self.assertIn('skippedCount', exec_info)
        self.assertIn('spaceSavedBytes', exec_info)
        self.assertIn('logPath', exec_info)

    def test_json_duplicate_group_structure(self):
        """Each duplicate group has masterFile and duplicates array."""
        data, stderr, exit_code = self.run_main_with_json(['--action', 'hardlink'])
        self.assertEqual(exit_code, 0)

        for group in data['duplicateGroups']:
            self.assertIn('masterFile', group)
            self.assertIn('duplicates', group)
            self.assertIsInstance(group['masterFile'], str)
            self.assertIsInstance(group['duplicates'], list)

            # Each duplicate has path, action, sizeBytes
            for dup in group['duplicates']:
                self.assertIn('path', dup)
                self.assertIn('action', dup)
                self.assertIn('sizeBytes', dup)

    def test_json_action_directories(self):
        """Action mode has master and duplicate directory paths."""
        data, stderr, exit_code = self.run_main_with_json(['--action', 'hardlink'])
        self.assertEqual(exit_code, 0)

        self.assertIn('directories', data)
        self.assertIn('master', data['directories'])
        self.assertIn('duplicate', data['directories'])
        self.assertTrue(os.path.isabs(data['directories']['master']))
        self.assertTrue(os.path.isabs(data['directories']['duplicate']))

    def test_json_action_statistics(self):
        """Action mode has statistics with groupCount, duplicateCount, spaceSavingsBytes."""
        data, stderr, exit_code = self.run_main_with_json(['--action', 'hardlink'])
        self.assertEqual(exit_code, 0)

        self.assertIn('statistics', data)
        stats = data['statistics']
        self.assertIn('groupCount', stats)
        self.assertIn('duplicateCount', stats)
        self.assertIn('spaceSavingsBytes', stats)

    # =========================================================================
    # Determinism Tests
    # =========================================================================

    def test_json_output_deterministic(self):
        """Same input produces identical JSON output (excluding timestamp)."""
        data1, _, _ = self.run_main_with_json()
        data2, _, _ = self.run_main_with_json()

        # Remove timestamps for comparison
        data1_copy = dict(data1)
        data2_copy = dict(data2)
        del data1_copy['timestamp']
        del data2_copy['timestamp']

        self.assertEqual(data1_copy, data2_copy)

    def test_json_matches_sorted(self):
        """Matches are sorted by first file in dir1."""
        data, stderr, exit_code = self.run_main_with_json()
        self.assertEqual(exit_code, 0)

        matches = data['matches']
        if len(matches) > 1:
            first_files = [m['filesDir1'][0] for m in matches if m['filesDir1']]
            self.assertEqual(first_files, sorted(first_files))

    def test_json_files_within_groups_sorted(self):
        """Files within each match group are sorted alphabetically."""
        data, stderr, exit_code = self.run_main_with_json()
        self.assertEqual(exit_code, 0)

        for match in data['matches']:
            files1 = match['filesDir1']
            files2 = match['filesDir2']
            self.assertEqual(files1, sorted(files1), "filesDir1 not sorted")
            self.assertEqual(files2, sorted(files2), "filesDir2 not sorted")

    def test_json_action_groups_sorted(self):
        """Duplicate groups in action mode are sorted by master file path."""
        data, stderr, exit_code = self.run_main_with_json(['--action', 'hardlink'])
        self.assertEqual(exit_code, 0)

        groups = data['duplicateGroups']
        if len(groups) > 1:
            master_files = [g['masterFile'] for g in groups]
            self.assertEqual(master_files, sorted(master_files))

    def test_json_duplicates_within_groups_sorted(self):
        """Duplicates within each group are sorted by path."""
        data, stderr, exit_code = self.run_main_with_json(['--action', 'hardlink'])
        self.assertEqual(exit_code, 0)

        for group in data['duplicateGroups']:
            paths = [d['path'] for d in group['duplicates']]
            self.assertEqual(paths, sorted(paths), "Duplicates not sorted by path")

    # =========================================================================
    # Field Naming Tests
    # =========================================================================

    def test_json_camel_case_fields(self):
        """All fields use camelCase naming convention."""
        data, stderr, exit_code = self.run_main_with_json(['--show-unmatched'])
        self.assertEqual(exit_code, 0)

        # Check top-level fields
        expected_camel = ['timestamp', 'directories', 'hashAlgorithm', 'matches',
                        'unmatchedDir1', 'unmatchedDir2', 'summary']
        for field in expected_camel:
            self.assertIn(field, data, f"Missing camelCase field: {field}")

        # Check no snake_case variants
        snake_case_bad = ['hash_algorithm', 'unmatched_dir1', 'unmatched_dir2',
                         'files_dir1', 'files_dir2']
        for field in snake_case_bad:
            self.assertNotIn(field, data, f"Found snake_case field: {field}")

    def test_json_action_mode_camel_case(self):
        """Action mode fields use camelCase."""
        data, stderr, exit_code = self.run_main_with_json(['--action', 'hardlink'])
        self.assertEqual(exit_code, 0)

        # Check action mode specific fields
        self.assertIn('duplicateGroups', data)
        self.assertIn('spaceSavingsBytes', data.get('statistics', {}))

        # Check duplicate objects
        for group in data['duplicateGroups']:
            self.assertIn('masterFile', group)
            for dup in group['duplicates']:
                self.assertIn('sizeBytes', dup)
                self.assertIn('crossFilesystem', dup)

    def test_json_summary_camel_case(self):
        """Summary fields use camelCase."""
        data, stderr, exit_code = self.run_main_with_json()
        self.assertEqual(exit_code, 0)

        summary = data['summary']
        expected = ['matchCount', 'matchedFilesDir1', 'matchedFilesDir2',
                   'unmatchedFilesDir1', 'unmatchedFilesDir2']
        for field in expected:
            self.assertIn(field, summary, f"Missing camelCase summary field: {field}")

    # =========================================================================
    # Integration Tests
    # =========================================================================

    def test_json_with_hash_sha256(self):
        """hashAlgorithm shows correct value when using SHA-256."""
        data, stderr, exit_code = self.run_main_with_json(['--hash', 'sha256'])
        self.assertEqual(exit_code, 0)

        self.assertEqual(data['hashAlgorithm'], 'sha256')

    def test_json_with_hash_md5(self):
        """hashAlgorithm shows correct value when using MD5 (default)."""
        data, stderr, exit_code = self.run_main_with_json()
        self.assertEqual(exit_code, 0)

        self.assertEqual(data['hashAlgorithm'], 'md5')

    def test_json_with_different_names_only(self):
        """--different-names-only filter is applied before JSON output."""
        # Run without filter
        data_all, _, _ = self.run_main_with_json()

        # Run with filter
        data_filtered, _, _ = self.run_main_with_json(['--different-names-only'])

        # With our test fixtures:
        # - file1.txt in dir1 matches different_name.txt in dir2 (different names)
        # - common_name.txt exists in both but with different content (no match)
        # The filtered version should only include matches where names differ
        # This may result in fewer or equal matches

        # Both should be valid JSON with matches array
        self.assertIn('matches', data_all)
        self.assertIn('matches', data_filtered)

    # NOTE: Stream separation (logger to stderr) is tested in test_output_unification.py

    def test_json_execute_requires_yes(self):
        """--json with --execute requires --yes flag."""
        stderr_capture = io.StringIO()
        with patch('sys.argv', ['filematcher', self.test_dir1, self.test_dir2,
                                '--json', '--action', 'hardlink', '--execute']):
            with redirect_stderr(stderr_capture):
                with self.assertRaises(SystemExit) as cm:
                    main()

        self.assertEqual(cm.exception.code, 2)
        error_output = stderr_capture.getvalue()
        self.assertIn('--json with --execute requires --yes', error_output)

    def test_json_action_warnings_field(self):
        """Action mode JSON includes warnings array."""
        data, stderr, exit_code = self.run_main_with_json(['--action', 'hardlink'])
        self.assertEqual(exit_code, 0)

        self.assertIn('warnings', data)
        self.assertIsInstance(data['warnings'], list)

    def test_json_with_fast_mode(self):
        """JSON output works correctly with --fast flag."""
        data, stderr, exit_code = self.run_main_with_json(['--fast'])
        self.assertEqual(exit_code, 0)

        # Should still have valid JSON structure
        self.assertIn('matches', data)
        self.assertIn('summary', data)

        # Fast mode message should be in stderr
        self.assertIn('Fast mode enabled', stderr)

    # =========================================================================
    # Action Type Tests (symlink, delete)
    # =========================================================================

    def test_json_action_symlink(self):
        """--action symlink produces correct JSON with action='symlink'."""
        data, stderr, exit_code = self.run_main_with_json(['--action', 'symlink'])
        self.assertEqual(exit_code, 0)

        self.assertEqual(data['action'], 'symlink')
        self.assertEqual(data['mode'], 'preview')

        # Verify duplicate objects have correct action
        for group in data['duplicateGroups']:
            for dup in group['duplicates']:
                self.assertEqual(dup['action'], 'symlink')

    def test_json_action_delete(self):
        """--action delete produces correct JSON with action='delete'."""
        data, stderr, exit_code = self.run_main_with_json(['--action', 'delete'])
        self.assertEqual(exit_code, 0)

        self.assertEqual(data['action'], 'delete')
        self.assertEqual(data['mode'], 'preview')

        # Verify duplicate objects have correct action
        for group in data['duplicateGroups']:
            for dup in group['duplicates']:
                self.assertEqual(dup['action'], 'delete')

    # =========================================================================
    # Statistics Field Coverage
    # =========================================================================

    def test_json_statistics_all_fields(self):
        """Statistics contains all expected fields including masterCount and crossFilesystemCount."""
        data, stderr, exit_code = self.run_main_with_json(['--action', 'hardlink'])
        self.assertEqual(exit_code, 0)

        stats = data['statistics']
        expected_fields = ['groupCount', 'duplicateCount', 'masterCount',
                          'spaceSavingsBytes', 'crossFilesystemCount']
        for field in expected_fields:
            self.assertIn(field, stats, f"Missing statistics field: {field}")
            self.assertIsInstance(stats[field], int, f"{field} should be int")

    # =========================================================================
    # Edge Case Tests
    # =========================================================================

    def test_json_empty_directories(self):
        """Empty directories produce valid JSON with empty matches array."""
        import tempfile
        with tempfile.TemporaryDirectory() as empty1:
            with tempfile.TemporaryDirectory() as empty2:
                args = ['filematcher', empty1, empty2, '--json']
                stdout_capture = io.StringIO()
                stderr_capture = io.StringIO()

                with patch('sys.argv', args):
                    with redirect_stdout(stdout_capture):
                        with redirect_stderr(stderr_capture):
                            exit_code = main()

                self.assertEqual(exit_code, 0)
                data = json.loads(stdout_capture.getvalue())

                # Should have valid structure with empty matches
                self.assertEqual(data['matches'], [])
                self.assertEqual(data['summary']['matchCount'], 0)
                self.assertEqual(data['summary']['matchedFilesDir1'], 0)
                self.assertEqual(data['summary']['matchedFilesDir2'], 0)

    def test_json_verbose_metadata_timestamp_format(self):
        """Verbose mode metadata timestamps are in RFC 3339 format."""
        data, stderr, exit_code = self.run_main_with_json(['--verbose'])
        self.assertEqual(exit_code, 0)

        self.assertIn('metadata', data)
        rfc3339_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(\+\d{2}:\d{2}|Z)?$'

        for filepath, info in data['metadata'].items():
            modified = info['modified']
            self.assertRegex(modified, rfc3339_pattern,
                           f"Metadata timestamp not RFC 3339: {modified}")
            # Verify it's parseable
            try:
                datetime.fromisoformat(modified.replace('Z', '+00:00'))
            except ValueError:
                self.fail(f"Metadata timestamp not parseable: {modified}")

    def test_json_combined_flags(self):
        """--json --verbose --show-unmatched together produces valid output."""
        data, stderr, exit_code = self.run_main_with_json(['--verbose', '--show-unmatched'])
        self.assertEqual(exit_code, 0)

        # Should have all the features
        self.assertIn('metadata', data)  # From --verbose
        self.assertIn('unmatchedDir1', data)  # From --show-unmatched
        self.assertIn('unmatchedDir2', data)

        # Metadata should include unmatched files too
        if data['unmatchedDir1'] or data['unmatchedDir2']:
            # If there are unmatched files, they should have metadata
            all_unmatched = data['unmatchedDir1'] + data['unmatchedDir2']
            for filepath in all_unmatched:
                self.assertIn(filepath, data['metadata'],
                            f"Unmatched file missing from metadata: {filepath}")

    def test_json_different_names_only_filters_results(self):
        """--different-names-only actually filters out same-name matches."""
        # Run without filter
        data_all, _, _ = self.run_main_with_json()

        # Run with filter
        data_filtered, _, _ = self.run_main_with_json(['--different-names-only'])

        # Both should have valid structure
        self.assertIn('matches', data_all)
        self.assertIn('matches', data_filtered)

        # Count matches where all files have same basename
        def has_same_name_match(matches):
            for match in matches:
                basenames1 = {os.path.basename(f) for f in match['filesDir1']}
                basenames2 = {os.path.basename(f) for f in match['filesDir2']}
                if basenames1 & basenames2:  # Intersection - same names
                    return True
            return False

        # Filtered should not have any same-name matches
        self.assertFalse(has_same_name_match(data_filtered['matches']),
                        "Filtered results should not contain same-name matches")


class TestJsonOutputMocked(BaseFileMatcherTest):
    """Tests requiring mocking for edge cases."""

    def test_json_cross_filesystem_detection(self):
        """Cross-filesystem duplicates have crossFilesystem=true."""
        # The JsonActionFormatter receives cross_fs_files set from the caller
        # We test that it correctly populates the crossFilesystem field
        from file_matcher import JsonActionFormatter

        formatter = JsonActionFormatter(verbose=False, preview_mode=True)
        formatter.set_directories('/master', '/duplicate')

        # Simulate a duplicate group with one cross-filesystem file
        cross_fs_files = {'/duplicate/file2.txt'}
        formatter.format_duplicate_group(
            master_file='/master/file.txt',
            duplicates=['/duplicate/file1.txt', '/duplicate/file2.txt'],
            action='hardlink',
            file_sizes={'/duplicate/file1.txt': 100, '/duplicate/file2.txt': 100},
            cross_fs_files=cross_fs_files
        )

        formatter.format_statistics(1, 2, 1, 200, 'hardlink', cross_fs_count=1)

        # Capture output
        stdout_capture = io.StringIO()
        with redirect_stdout(stdout_capture):
            formatter.finalize()

        data = json.loads(stdout_capture.getvalue())

        # Find the duplicates and check crossFilesystem flags
        group = data['duplicateGroups'][0]
        dups_by_path = {d['path']: d for d in group['duplicates']}

        self.assertFalse(dups_by_path['/duplicate/file1.txt']['crossFilesystem'])
        self.assertTrue(dups_by_path['/duplicate/file2.txt']['crossFilesystem'])

        # Statistics should reflect cross-fs count
        self.assertEqual(data['statistics']['crossFilesystemCount'], 1)

    def test_json_execution_with_failures(self):
        """Execution mode with failures includes failure details."""
        from file_matcher import JsonActionFormatter

        formatter = JsonActionFormatter(verbose=False, preview_mode=False)  # Execute mode
        formatter.set_directories('/master', '/duplicate')

        # Simulate a duplicate group
        formatter.format_duplicate_group(
            master_file='/master/file.txt',
            duplicates=['/duplicate/file1.txt', '/duplicate/file2.txt'],
            action='hardlink',
            file_sizes={'/duplicate/file1.txt': 100, '/duplicate/file2.txt': 100}
        )

        formatter.format_statistics(1, 2, 1, 200, 'hardlink')

        # Simulate execution with one failure
        formatter.format_execution_summary(
            success_count=1,
            failure_count=1,
            skipped_count=0,
            space_saved=100,
            log_path='/tmp/audit.log',
            failed_list=[('/duplicate/file2.txt', 'Permission denied')]
        )

        # Capture output
        stdout_capture = io.StringIO()
        with redirect_stdout(stdout_capture):
            formatter.finalize()

        data = json.loads(stdout_capture.getvalue())

        # Check execution summary
        self.assertEqual(data['mode'], 'execute')
        self.assertIn('execution', data)
        exec_info = data['execution']

        self.assertEqual(exec_info['successCount'], 1)
        self.assertEqual(exec_info['failureCount'], 1)
        self.assertEqual(exec_info['skippedCount'], 0)
        self.assertEqual(exec_info['spaceSavedBytes'], 100)
        self.assertEqual(exec_info['logPath'], '/tmp/audit.log')

        # Check failures array
        self.assertEqual(len(exec_info['failures']), 1)
        failure = exec_info['failures'][0]
        self.assertEqual(failure['path'], '/duplicate/file2.txt')
        self.assertEqual(failure['error'], 'Permission denied')

    def test_json_execution_failures_sorted(self):
        """Execution failures are sorted by path for determinism."""
        from file_matcher import JsonActionFormatter

        formatter = JsonActionFormatter(verbose=False, preview_mode=False)
        formatter.set_directories('/master', '/duplicate')

        # Simulate execution with multiple failures (unsorted input)
        formatter.format_execution_summary(
            success_count=0,
            failure_count=3,
            skipped_count=0,
            space_saved=0,
            log_path='/tmp/audit.log',
            failed_list=[
                ('/z/file.txt', 'Error Z'),
                ('/a/file.txt', 'Error A'),
                ('/m/file.txt', 'Error M'),
            ]
        )

        # Capture output
        stdout_capture = io.StringIO()
        with redirect_stdout(stdout_capture):
            formatter.finalize()

        data = json.loads(stdout_capture.getvalue())
        failures = data['execution']['failures']

        # Should be sorted by path
        paths = [f['path'] for f in failures]
        self.assertEqual(paths, sorted(paths))


class TestJsonOutputSubprocess(BaseFileMatcherTest):
    """Test JSON output via subprocess for true integration testing."""

    def test_json_output_parseable_by_jq_pattern(self):
        """JSON output can be parsed for common jq patterns."""
        result = subprocess.run(
            ['python3', 'file_matcher.py', self.test_dir1, self.test_dir2, '--json'],
            capture_output=True, text=True
        )

        self.assertEqual(result.returncode, 0)

        # Parse the JSON
        data = json.loads(result.stdout)

        # Simulate common jq operations
        # 1. Get match count
        match_count = len(data['matches'])
        self.assertGreaterEqual(match_count, 0)

        # 2. Get first file from each match (like jq '.matches[].filesDir1[0]')
        first_files = [m['filesDir1'][0] for m in data['matches'] if m['filesDir1']]
        self.assertIsInstance(first_files, list)

        # 3. Get summary stats (like jq '.summary.matchCount')
        self.assertIn('matchCount', data['summary'])


if __name__ == "__main__":
    unittest.main()
