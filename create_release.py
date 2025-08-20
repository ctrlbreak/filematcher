#!/usr/bin/env python3
"""
Release Package Creator for File Matcher

This script creates a release package for distribution on GitHub.
It creates a clean archive with only the necessary files for users.

To create a release package:
# Update version in create_release.py and file_matcher.py
python3 create_release.py 1.1.0
git tag -a v1.1.0 -m "Release version 1.1.0"
git push origin v1.1.0
# Then upload the new archives to GitHub
"""

import os
import shutil
import zipfile
import tarfile
from datetime import datetime
from pathlib import Path

def create_release_package(version="1.0.0"):
    """Create a release package for the specified version."""
    
    # Create release directory
    release_dir = f"filematcher-{version}"
    if os.path.exists(release_dir):
        shutil.rmtree(release_dir)
    os.makedirs(release_dir)
    
    # Files to include in release
    include_files = [
        "file_matcher.py",
        "README.md",
        "CHANGELOG.md",
        "requirements.txt",
        "run_tests.py"
    ]
    
    # Directories to include
    include_dirs = [
        "tests"
    ]
    
    # Copy main files
    for file in include_files:
        if os.path.exists(file):
            shutil.copy2(file, release_dir)
            print(f"✓ Added {file}")
    
    # Copy directories
    for dir_name in include_dirs:
        if os.path.exists(dir_name):
            shutil.copytree(dir_name, os.path.join(release_dir, dir_name))
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

1. **No installation required** - this is a standalone Python script
2. **Requirements**: Python 3.6 or higher
3. **Usage**: python3 file_matcher.py <dir1> <dir2> [options]

## Running Tests

To verify the installation:
```bash
python3 run_tests.py
```

## Examples

Compare two directories:
```bash
python3 file_matcher.py test_dir1 test_dir2
```

Use fast mode for large files:
```bash
python3 file_matcher.py test_dir1 test_dir2 --fast
```

Get summary only:
```bash
python3 file_matcher.py test_dir1 test_dir2 --summary
```

## Features

- File matching using content hashing (MD5/SHA-256)
- Fast mode for large files (>100MB)
- Summary and detailed output modes
- Cross-platform compatibility
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
Python Version: 3.6+
Dependencies: None (standard library only)

## What's New in {version}

This is the first stable release of File Matcher, featuring:

- Complete file matching functionality
- Fast mode for large files
- Comprehensive test suite
- Cross-platform compatibility
- No external dependencies

## File Structure

- file_matcher.py - Main script
- README.md - Complete documentation
- CHANGELOG.md - Version history
- tests/ - Unit test suite
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
    
    version = "1.0.0"
    if len(sys.argv) > 1:
        version = sys.argv[1]
    
    print(f"Creating File Matcher release package v{version}")
    print("=" * 50)
    
    create_release_package(version)
