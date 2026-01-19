#!/usr/bin/env python3
"""
File Matcher - Find files with identical content in different directory trees.

This script compares two directory trees and finds files that have identical
content but potentially different names or locations.

Version: 1.0.0
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import os
import sys
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)


def validate_master_directory(master: str, dir1: str, dir2: str) -> Path:
    """
    Validate that master directory is one of the compared directories.

    Args:
        master: Path to the master directory
        dir1: First directory being compared
        dir2: Second directory being compared

    Returns:
        Resolved Path to the master directory

    Raises:
        ValueError: If master is not one of the compared directories
    """
    master_resolved = Path(master).resolve()
    dir1_resolved = Path(dir1).resolve()
    dir2_resolved = Path(dir2).resolve()

    if master_resolved == dir1_resolved or master_resolved == dir2_resolved:
        return master_resolved
    raise ValueError("Master must be one of the compared directories")


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
                # Store full absolute path
                hash_to_files[file_hash].append(str(filepath.absolute()))
            except (PermissionError, OSError) as e:
                logger.error(f"Error processing {filepath}: {e}")
                if verbose:
                    processed_files += 1

    if verbose:
        logger.debug(f"Completed indexing {directory}: {len(hash_to_files)} unique file contents found")
    
    return hash_to_files


def find_matching_files(dir1: str | Path, dir2: str | Path, hash_algorithm: str = 'md5', fast_mode: bool = False, verbose: bool = False) -> tuple[dict[str, tuple[list[str], list[str]]], list[str], list[str]]:
    """
    Find files that have identical content but different names
    across two directory hierarchies.
    
    Args:
        dir1: First directory to scan
        dir2: Second directory to scan
        hash_algorithm: Hashing algorithm to use
        fast_mode: If True, use faster hashing for large files
        verbose: If True, show progress for each file being processed
        
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
        # Only include if we've found files with different names
        files1 = hash_to_files1[file_hash]
        files2 = hash_to_files2[file_hash]
        
        # Filter out files with exactly the same name
        # (We're looking for identical content with different names)
        if not all(f1 == f2 for f1 in files1 for f2 in files2):
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
    parser = argparse.ArgumentParser(description='Find files with identical content but different names across two directories.')
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
    parser.add_argument('--master', '-m',
                        help='Designate one directory as master (files in master are never modified)')

    args = parser.parse_args()

    # Validate master directory if specified
    master_path = None
    if args.master:
        try:
            master_path = validate_master_directory(args.master, args.dir1, args.dir2)
        except ValueError as e:
            parser.error(str(e))

    # Configure logging based on verbosity
    log_level = logging.DEBUG if args.verbose else logging.INFO
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger.handlers = [handler]
    logger.setLevel(log_level)

    if not os.path.isdir(args.dir1) or not os.path.isdir(args.dir2):
        logger.error("Error: Both arguments must be directories")
        return 1

    hash_algo = args.hash
    logger.info(f"Using {hash_algo.upper()} hashing algorithm")

    if args.fast:
        logger.info("Fast mode enabled: Using sparse sampling for large files")

    if args.verbose:
        logger.info("Verbose mode enabled: Showing progress for each file")
    
    matches, unmatched1, unmatched2 = find_matching_files(args.dir1, args.dir2, hash_algo, args.fast, args.verbose)
    
    # Count total matched files in each directory
    matched_files1 = sum(len(files) for files, _ in matches.values())
    matched_files2 = sum(len(files) for _, files in matches.values())
    
    # Display matching files results
    if args.summary:
        print(f"\nMatched files summary:")
        print(f"  Unique content hashes with matches: {len(matches)}")
        print(f"  Files in {args.dir1} with matches in {args.dir2}: {matched_files1}")
        print(f"  Files in {args.dir2} with matches in {args.dir1}: {matched_files2}")
        
        if args.show_unmatched:
            print(f"\nUnmatched files summary:")
            print(f"  Files in {args.dir1} with no match: {len(unmatched1)}")
            print(f"  Files in {args.dir2} with no match: {len(unmatched2)}")
    else:
        # Detailed output
        if not matches:
            print("No matching files with different names found.")
        else:
            print(f"\nFound {len(matches)} hashes with matching files:\n")
            for file_hash, (files1, files2) in matches.items():
                print(f"Hash: {file_hash[:10]}...")
                print(f"  Files in {args.dir1}:")
                for f in files1:
                    print(f"    {f}")
                print(f"  Files in {args.dir2}:")
                for f in files2:
                    print(f"    {f}")
                print()
    
        # Optionally display unmatched files (detailed mode)
        if args.show_unmatched and not args.summary:
            print("\nFiles with no content matches:")
            print("==============================")
            
            if unmatched1:
                print(f"\nUnique files in {args.dir1} ({len(unmatched1)}):")
                for f in sorted(unmatched1):
                    print(f"  {f}")
            else:
                print(f"\nNo unique files in {args.dir1}")
            
            if unmatched2:
                print(f"\nUnique files in {args.dir2} ({len(unmatched2)}):")
                for f in sorted(unmatched2):
                    print(f"  {f}")
            else:
                print(f"\nNo unique files in {args.dir2}")

    return 0


if __name__ == "__main__":
    sys.exit(main()) 