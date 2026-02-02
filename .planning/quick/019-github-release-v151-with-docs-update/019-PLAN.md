---
phase: quick
plan: 019
type: execute
wave: 1
depends_on: []
files_modified:
  - pyproject.toml
  - filematcher/__init__.py
  - file_matcher.py
  - CLAUDE.md
autonomous: true

must_haves:
  truths:
    - "Version 1.5.1 appears in pyproject.toml, __init__.py, file_matcher.py, and CLAUDE.md"
    - "GitHub release v1.5.1 exists with release notes"
    - "Release notes document code quality improvements from quick tasks 017-018"
  artifacts:
    - path: "pyproject.toml"
      provides: "Package version"
      contains: 'version = "1.5.1"'
    - path: "filematcher/__init__.py"
      provides: "Module version"
      contains: '__version__ = "1.5.1"'
    - path: "file_matcher.py"
      provides: "Compatibility wrapper version"
      contains: "Version: 1.5.1"
    - path: "CLAUDE.md"
      provides: "Documentation version reference"
      contains: "v1.5.1"
  key_links:
    - from: "GitHub release"
      to: "v1.5.1 tag"
      via: "gh release create"
---

<objective>
Release v1.5.1 patch version documenting code quality improvements since v1.5.0.

Purpose: Document internal improvements from quick tasks 017-018 (API surface reduction, exit code fix, main() complexity reduction) in a proper release.

Output: GitHub release v1.5.1 with release notes and updated version numbers across all files.
</objective>

<context>
@.planning/STATE.md
@pyproject.toml
@filematcher/__init__.py
@file_matcher.py
@CLAUDE.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Update version numbers to 1.5.1</name>
  <files>pyproject.toml, filematcher/__init__.py, file_matcher.py, CLAUDE.md</files>
  <action>
Update version from 1.5.0 to 1.5.1 in:

1. `pyproject.toml` line 3: `version = "1.5.0"` -> `version = "1.5.1"`

2. `filematcher/__init__.py` line 137: `__version__ = "1.5.0"` -> `__version__ = "1.5.1"`

3. `file_matcher.py` line 13: `Version: 1.1.0` -> `Version: 1.5.1` (sync to current)

4. `CLAUDE.md` line 7: `File Matcher (v1.5.0)` -> `File Matcher (v1.5.1)`
  </action>
  <verify>grep -r "1.5.1" pyproject.toml filematcher/__init__.py file_matcher.py CLAUDE.md shows all four files</verify>
  <done>All version references updated to 1.5.1</done>
</task>

<task type="auto">
  <name>Task 2: Commit version bump and create GitHub release</name>
  <files>N/A (git operations)</files>
  <action>
1. Stage and commit version changes:
   ```bash
   git add pyproject.toml filematcher/__init__.py file_matcher.py CLAUDE.md
   git commit -m "chore: bump version to 1.5.1"
   ```

2. Create GitHub release with gh CLI:
   ```bash
   gh release create v1.5.1 --title "v1.5.1 - Code Quality Improvements" --notes "$(cat <<'EOF'
## What's Changed

This patch release documents internal code quality improvements made since v1.5.0.

### Code Quality Improvements

- **Reduced public API surface** from 89 to 18 exports in `__init__.py` - cleaner, more focused public interface
- **Fixed exit code inconsistency** - partial failures now correctly return exit code 2 (was inconsistent)
- **Reduced main() complexity** from 425 to 145 lines through extraction of 6 helper functions:
  - `_validate_args()` - argument validation
  - `_setup_logging()` - audit log initialization
  - `_build_master_results()` - master directory result assembly
  - `_dispatch_compare_mode()` - compare mode handling
  - `_dispatch_execute_mode()` - execute mode handling
  - `_dispatch_preview_mode()` - preview mode handling

### Internal Changes

These changes improve maintainability without affecting user-facing behavior:
- Cleaner separation of concerns in CLI module
- Better testability through smaller functions
- Consistent exit codes across all code paths

**Full Changelog**: https://github.com/PatrickKoss/filematcher/compare/v1.5.0...v1.5.1
EOF
)"
   ```
  </action>
  <verify>gh release view v1.5.1 shows the release with correct title and notes</verify>
  <done>GitHub release v1.5.1 created with release notes documenting code quality improvements</done>
</task>

<task type="auto">
  <name>Task 3: Update STATE.md with release info</name>
  <files>.planning/STATE.md</files>
  <action>
Add quick task 019 to the "Quick Tasks Completed" table in STATE.md:

| 019 | GitHub release v1.5.1 with docs update | {date} | {commit} | [019-github-release-v151-with-docs-update](./quick/019-github-release-v151-with-docs-update/) |

Update "Current focus" line to reflect v1.5.1 shipped.
  </action>
  <verify>grep "019" .planning/STATE.md shows the new entry</verify>
  <done>STATE.md updated with quick task 019 completion record</done>
</task>

</tasks>

<verification>
- `python -c "import filematcher; print(filematcher.__version__)"` outputs "1.5.1"
- `gh release view v1.5.1` shows release exists with proper notes
- All tests still pass: `python3 run_tests.py`
</verification>

<success_criteria>
- Version 1.5.1 in pyproject.toml, __init__.py, file_matcher.py, CLAUDE.md
- GitHub release v1.5.1 created with release notes covering quick tasks 017-018
- STATE.md updated with quick task 019 completion
- All 308 tests pass
</success_criteria>

<output>
After completion, create `.planning/quick/019-github-release-v151-with-docs-update/019-SUMMARY.md`
</output>
