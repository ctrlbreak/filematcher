#!/usr/bin/env python3

import os
import hashlib
import argparse
from collections import defaultdict
from pathlib import Path


def get_file_hash(filepath, hash_algorithm='md5', fast_mode=False, size_threshold=100*1024*1024):  # 100MB threshold
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


def get_sparse_hash(filepath, hash_algorithm='md5', file_size=None, sample_size=1024*1024):
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


def index_directory(directory, hash_algorithm='md5', fast_mode=False):
    """
    Recursively index all files in a directory and its subdirectories.
    Returns a dict mapping content hashes to lists of file paths.
    
    Args:
        directory: Directory path to index
        hash_algorithm: Hashing algorithm to use
        fast_mode: If True, use faster hashing for large files
    """
    hash_to_files = defaultdict(list)
    directory_path = Path(directory)
    
    for filepath in directory_path.rglob('*'):
        if filepath.is_file():
            try:
                file_hash = get_file_hash(filepath, hash_algorithm, fast_mode)
                # Store full absolute path
                hash_to_files[file_hash].append(str(filepath.absolute()))
            except (PermissionError, OSError) as e:
                print(f"Error processing {filepath}: {e}")
    
    return hash_to_files


def find_matching_files(dir1, dir2, hash_algorithm='md5', fast_mode=False):
    """
    Find files that have identical content but different names
    across two directory hierarchies.
    
    Args:
        dir1: First directory to scan
        dir2: Second directory to scan
        hash_algorithm: Hashing algorithm to use
        fast_mode: If True, use faster hashing for large files
        
    Returns:
        - matches: Dict where keys are content hashes and values are tuples of (files_from_dir1, files_from_dir2)
        - unmatched1: List of files in dir1 with no content match in dir2
        - unmatched2: List of files in dir2 with no content match in dir1
    """
    print(f"Indexing directory: {dir1}")
    hash_to_files1 = index_directory(dir1, hash_algorithm, fast_mode)
    
    print(f"Indexing directory: {dir2}")
    hash_to_files2 = index_directory(dir2, hash_algorithm, fast_mode)
    
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
    parser.add_argument('--summary', '-s', action='store_true', 
                        help='Show only counts of matched/unmatched files instead of listing them all')
    parser.add_argument('--fast', '-f', action='store_true',
                        help='Use fast mode for large files (uses file size + partial content sampling)')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.dir1) or not os.path.isdir(args.dir2):
        print("Error: Both arguments must be directories")
        return 1
    
    hash_algo = args.hash
    print(f"Using {hash_algo.upper()} hashing algorithm")
    
    if args.fast:
        print("Fast mode enabled: Using sparse sampling for large files")
    
    matches, unmatched1, unmatched2 = find_matching_files(args.dir1, args.dir2, hash_algo, args.fast)
    
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


if __name__ == "__main__":
    main() 