#!/usr/bin/env python3
"""
Release Script for File Matcher

Creates a GitHub release with notes extracted from CHANGELOG.md.
GitHub automatically generates source archives from tags.

Usage:
    python3 create_release.py 1.5.1        # Create release for version
    python3 create_release.py 1.5.1 --dry-run  # Preview without creating
"""

import re
import subprocess
import sys
from pathlib import Path


def get_version_from_files() -> dict[str, str]:
    """Read version from all source files."""
    versions = {}

    # pyproject.toml
    pyproject = Path("pyproject.toml")
    if pyproject.exists():
        match = re.search(r'version\s*=\s*"([^"]+)"', pyproject.read_text())
        if match:
            versions["pyproject.toml"] = match.group(1)

    # filematcher/__init__.py
    init_file = Path("filematcher/__init__.py")
    if init_file.exists():
        match = re.search(r'__version__\s*=\s*"([^"]+)"', init_file.read_text())
        if match:
            versions["filematcher/__init__.py"] = match.group(1)

    # file_matcher.py
    wrapper = Path("file_matcher.py")
    if wrapper.exists():
        match = re.search(r'Version:\s*(\S+)', wrapper.read_text())
        if match:
            versions["file_matcher.py"] = match.group(1)

    return versions


def extract_changelog_section(version: str) -> str | None:
    """Extract the changelog section for a specific version."""
    changelog = Path("CHANGELOG.md")
    if not changelog.exists():
        return None

    content = changelog.read_text()

    # Match from ## [version] to the next ## [version] or end
    pattern = rf'## \[{re.escape(version)}\][^\n]*\n(.*?)(?=\n## \[|\Z)'
    match = re.search(pattern, content, re.DOTALL)

    if match:
        return match.group(1).strip()
    return None


def check_tag_exists(version: str) -> bool:
    """Check if git tag already exists."""
    result = subprocess.run(
        ["git", "tag", "-l", f"v{version}"],
        capture_output=True, text=True
    )
    return bool(result.stdout.strip())


def check_release_exists(version: str) -> bool:
    """Check if GitHub release already exists."""
    result = subprocess.run(
        ["gh", "release", "view", f"v{version}"],
        capture_output=True, text=True
    )
    return result.returncode == 0


def create_release(version: str, dry_run: bool = False) -> bool:
    """Create a GitHub release for the specified version."""

    print(f"{'[DRY RUN] ' if dry_run else ''}Creating release v{version}")
    print("=" * 50)

    # 1. Verify version consistency
    print("\n1. Checking version consistency...")
    versions = get_version_from_files()

    all_match = all(v == version for v in versions.values())
    for file, ver in versions.items():
        status = "✓" if ver == version else "✗"
        print(f"   {status} {file}: {ver}")

    if not all_match:
        print(f"\n✗ Version mismatch! Update files to {version} first.")
        return False
    print("   All versions match.")

    # 2. Extract changelog
    print("\n2. Extracting changelog section...")
    changelog_section = extract_changelog_section(version)

    if not changelog_section:
        print(f"   ✗ No changelog entry found for [{version}]")
        print("   Add an entry to CHANGELOG.md first.")
        return False
    print(f"   ✓ Found changelog ({len(changelog_section)} chars)")

    # 3. Check if tag exists
    print("\n3. Checking git tag...")
    tag_exists = check_tag_exists(version)
    if tag_exists:
        print(f"   ✓ Tag v{version} exists")
    else:
        print(f"   Tag v{version} does not exist, will create")

    # 4. Check if release exists
    print("\n4. Checking GitHub release...")
    release_exists = check_release_exists(version)
    if release_exists:
        print(f"   ✗ Release v{version} already exists!")
        print("   Use 'gh release edit' to update, or delete and recreate.")
        return False
    print(f"   ✓ Release v{version} does not exist")

    # 5. Show preview
    print("\n5. Release notes preview:")
    print("-" * 50)
    # Truncate for preview if very long
    preview = changelog_section[:500] + "..." if len(changelog_section) > 500 else changelog_section
    print(preview)
    print("-" * 50)

    if dry_run:
        print("\n[DRY RUN] Would create:")
        print(f"   - Git tag: v{version}")
        print(f"   - GitHub release: v{version}")
        print("\nRun without --dry-run to create the release.")
        return True

    # 6. Create tag if needed
    if not tag_exists:
        print(f"\n6. Creating git tag v{version}...")
        result = subprocess.run(
            ["git", "tag", "-a", f"v{version}", "-m", f"Release version {version}"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"   ✗ Failed to create tag: {result.stderr}")
            return False
        print(f"   ✓ Created tag v{version}")

        # Push tag
        print(f"   Pushing tag to origin...")
        result = subprocess.run(
            ["git", "push", "origin", f"v{version}"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"   ✗ Failed to push tag: {result.stderr}")
            return False
        print(f"   ✓ Pushed tag v{version}")
    else:
        print("\n6. Tag already exists, skipping creation")

    # 7. Create GitHub release
    print(f"\n7. Creating GitHub release...")

    # Format release notes
    release_notes = f"## What's Changed\n\n{changelog_section}"

    result = subprocess.run(
        ["gh", "release", "create", f"v{version}",
         "--title", f"v{version}",
         "--notes", release_notes],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        print(f"   ✗ Failed to create release: {result.stderr}")
        return False

    print(f"   ✓ Created release v{version}")

    # 8. Get release URL
    result = subprocess.run(
        ["gh", "release", "view", f"v{version}", "--json", "url", "-q", ".url"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"\n🎉 Release created successfully!")
        print(f"   {result.stdout.strip()}")

    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 create_release.py <version> [--dry-run]")
        print("Example: python3 create_release.py 1.5.2")
        sys.exit(1)

    version = sys.argv[1]
    dry_run = "--dry-run" in sys.argv

    success = create_release(version, dry_run)
    sys.exit(0 if success else 1)
