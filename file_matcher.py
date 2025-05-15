#!/usr/bin/env python3

import os
import hashlib
import argparse
from collections import defaultdict
from pathlib import Path


def get_file_hash(filepath, hash_algorithm='md5'):
    """
    Calculate hash of file content using the specified algorithm.
    
    Args:
        filepath: Path to the file to hash
        hash_algorithm: Hashing algorithm to use ('md5' or 'sha256')
    
    Returns:
        Hexadecimal digest of the hash
    """
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


def index_directory(directory, hash_algorithm='md5'):
    """
    Recursively index all files in a directory and its subdirectories.
    Returns a dict mapping content hashes to lists of file paths.
    
    Args:
        directory: Directory path to index
        hash_algorithm: Hashing algorithm to use
    """
    hash_to_files = defaultdict(list)
    directory_path = Path(directory)
    
    for filepath in directory_path.rglob('*'):
        if filepath.is_file():
            try:
                file_hash = get_file_hash(filepath, hash_algorithm)
                # Store full absolute path
                hash_to_files[file_hash].append(str(filepath.absolute()))
            except (PermissionError, OSError) as e:
                print(f"Error processing {filepath}: {e}")
    
    return hash_to_files


def find_matching_files(dir1, dir2, hash_algorithm='md5'):
    """
    Find files that have identical content but different names
    across two directory hierarchies.
    
    Args:
        dir1: First directory to scan
        dir2: Second directory to scan
        hash_algorithm: Hashing algorithm to use
        
    Returns:
        - matches: Dict where keys are content hashes and values are tuples of (files_from_dir1, files_from_dir2)
        - unmatched1: List of files in dir1 with no content match in dir2
        - unmatched2: List of files in dir2 with no content match in dir1
    """
    print(f"Indexing directory: {dir1}")
    hash_to_files1 = index_directory(dir1, hash_algorithm)
    
    print(f"Indexing directory: {dir2}")
    hash_to_files2 = index_directory(dir2, hash_algorithm)
    
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


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Find files with identical content but different names across two directories.')
    parser.add_argument('dir1', help='First directory to compare')
    parser.add_argument('dir2', help='Second directory to compare')
    parser.add_argument('--show-unmatched', '-u', action='store_true', help='Display files with no content match')
    parser.add_argument('--hash', '-H', choices=['md5', 'sha256'], default='md5',
                        help='Hash algorithm to use (default: md5)')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.dir1) or not os.path.isdir(args.dir2):
        print("Error: Both arguments must be directories")
        return 1
    
    hash_algo = args.hash
    print(f"Using {hash_algo.upper()} hashing algorithm")
    
    matches, unmatched1, unmatched2 = find_matching_files(args.dir1, args.dir2, hash_algo)
    
    # Display matching files results
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
    
    # Optionally display unmatched files
    if args.show_unmatched:
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


if __name__ == "__main__":
    main() 