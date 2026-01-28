#!/usr/bin/env python3
"""
Release Package Creator for File Matcher

This script creates a release package for distribution on GitHub.
It creates a clean archive with only the necessary files for users.

To create a release package:
# Update version in create_release.py and pyproject.toml
python3 create_release.py 1.4.0
git tag -a v1.4.0 -m "Release version 1.4.0"
git push origin v1.4.0
# Then upload the new archives to GitHub
"""

import os
import shutil
import zipfile
import tarfile
from datetime import datetime
from pathlib import Path

def create_release_package(version="1.4.0"):
    """Create a release package for the specified version."""
    
    # Create release directory
    release_dir = f"filematcher-{version}"
    if os.path.exists(release_dir):
        shutil.rmtree(release_dir)
    os.makedirs(release_dir)
    
    # Files to include in release
    include_files = [
        "file_matcher.py",
        "pyproject.toml",
        "README.md",
        "CHANGELOG.md",
        f"RELEASE_NOTES_v{version}.md",
        "LICENSE",
        "requirements.txt",
        "run_tests.py"
    ]

    # Directories to include
    include_dirs = [
        "filematcher",
        "tests"
    ]
    
    # Copy main files
    for file in include_files:
        if os.path.exists(file):
            shutil.copy2(file, release_dir)
            print(f"✓ Added {file}")
    
    # Copy directories (excluding __pycache__)
    def ignore_pycache(directory, files):
        return [f for f in files if f == '__pycache__' or f.endswith('.pyc')]

    for dir_name in include_dirs:
        if os.path.exists(dir_name):
            shutil.copytree(dir_name, os.path.join(release_dir, dir_name), ignore=ignore_pycache)
            print(f"✓ Added directory {dir_name}")
    
    # Create test directories for users
    test_dirs = ["test_dir1", "test_dir2", "complex_test"]
    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            shutil.copytree(test_dir, os.path.join(release_dir, test_dir))
            print(f"✓ Added test directory {test_dir}")
    
    # Create installation instructions
    install_instructions = f"""# File Matcher {version} - Installation

## Quick Start

### Option 1: Install via pip (recommended)
```bash
pip install .
filematcher <master_dir> <duplicate_dir> [options]
```

### Option 2: Run directly
```bash
python3 file_matcher.py <master_dir> <duplicate_dir> [options]
```

**Requirements**: Python 3.9 or higher

## Running Tests

To verify the installation:
```bash
python3 run_tests.py
```

## Examples

### Finding Duplicate Files

```bash
# Basic comparison (dir1 is master, dir2 has duplicates)
filematcher test_dir1 test_dir2

# Show files with no matches
filematcher test_dir1 test_dir2 --show-unmatched

# Fast mode for large files
filematcher test_dir1 test_dir2 --fast

# Summary counts only
filematcher test_dir1 test_dir2 --summary

# JSON output for scripting
filematcher test_dir1 test_dir2 --json
```

### Deduplicating Files

```bash
# Preview hard link deduplication (safe - no changes made)
filematcher master_dir duplicate_dir --action hardlink

# Execute deduplication with confirmation
filematcher master_dir duplicate_dir --action hardlink --execute

# Execute without prompt (for scripts)
filematcher master_dir duplicate_dir --action hardlink --execute --yes

# With custom log file
filematcher master_dir duplicate_dir --action hardlink --execute --log changes.log
```

## Features

- Find files with identical content across directories
- Compare using MD5 or SHA-256 content hashing
- Fast mode with sparse sampling for large files (>100MB)
- **Deduplicate** with hard links, symbolic links, or deletion
- Safe by default: preview changes before executing
- Audit logging of all modifications
- JSON output for scripting
- TTY-aware color output
- No external dependencies

For more information, see README.md
"""
    
    with open(os.path.join(release_dir, "INSTALL.md"), "w") as f:
        f.write(install_instructions)
    print("✓ Created INSTALL.md")
    
    # Create version info file
    version_info = f"""# File Matcher Version Information

Version: {version}
Release Date: {datetime.now().strftime('%Y-%m-%d')}
Python Version: 3.9+
Dependencies: None (standard library only)

## What's New in {version}

Package structure refactoring for better code organization:

- Refactored to filematcher/ package structure
- pip installable via pyproject.toml
- Full backward compatibility with file_matcher.py
- JSON output for scripting (--json flag)
- TTY-aware color output (--color/--no-color flags)
- Unified output format across all modes
- 218 unit tests covering all functionality

## File Structure

- filematcher/ - Main package
  - cli.py - Command-line interface and main()
  - colors.py - TTY-aware color output
  - hashing.py - MD5/SHA-256 content hashing
  - filesystem.py - Filesystem helpers
  - actions.py - Action execution and audit logging
  - formatters.py - Text and JSON output formatters
  - directory.py - Directory indexing and matching
- file_matcher.py - Backward compatibility wrapper
- pyproject.toml - Package configuration
- README.md - Complete documentation
- CHANGELOG.md - Version history
- LICENSE - MIT license
- tests/ - Unit test suite (218 tests)
- test_dir1/, test_dir2/ - Example test directories
- complex_test/ - Advanced test scenarios
"""
    
    with open(os.path.join(release_dir, "VERSION.md"), "w") as f:
        f.write(version_info)
    print("✓ Created VERSION.md")
    
    # Create archives
    print("\nCreating release archives...")
    
    # ZIP archive
    zip_filename = f"filematcher-{version}.zip"
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(release_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, release_dir)
                zipf.write(file_path, arcname)
    print(f"✓ Created {zip_filename}")
    
    # TAR.GZ archive
    tar_filename = f"filematcher-{version}.tar.gz"
    with tarfile.open(tar_filename, "w:gz") as tar:
        tar.add(release_dir, arcname=os.path.basename(release_dir))
    print(f"✓ Created {tar_filename}")
    
    # Clean up release directory
    shutil.rmtree(release_dir)
    print(f"✓ Cleaned up temporary files")
    
    print(f"\n🎉 Release package created successfully!")
    print(f"📦 Files created:")
    print(f"   - {zip_filename}")
    print(f"   - {tar_filename}")
    print(f"\n📋 Next steps:")
    print(f"   1. Review the archives")
    print(f"   2. Create a GitHub release with tag v{version}")
    print(f"   3. Upload these archives to the GitHub release")
    print(f"   4. Update the release notes with the changelog")

if __name__ == "__main__":
    import sys

    version = "1.4.0"
    if len(sys.argv) > 1:
        version = sys.argv[1]

    print(f"Creating File Matcher release package v{version}")
    print("=" * 50)

    create_release_package(version)
