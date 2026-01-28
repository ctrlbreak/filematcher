---
type: quick
id: "009"
description: "Add --target-dir flag for redirecting hardlink/symlink creation"
files_modified:
  - filematcher/cli.py
  - filematcher/actions.py
  - tests/test_actions.py
  - tests/test_cli.py
autonomous: true
---

<objective>
Add `--target-dir` CLI flag that allows duplicates in dir2 to be linked FROM a new location instead of in-place. When specified:
1. Link is created in target-dir (preserving relative path from dir2)
2. Original file in dir2 is deleted
3. Only valid with hardlink or symlink actions (not delete or compare)

Purpose: Enables workflows where users want to consolidate duplicates into a separate directory while maintaining the deduplication link to master.

Output: Working `--target-dir` flag with validation, execution logic, and tests.
</objective>

<context>
@filematcher/cli.py - CLI argument parsing and main execution flow
@filematcher/actions.py - execute_action() and safe_replace_with_link() functions
@tests/test_actions.py - Existing action test patterns
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add --target-dir CLI argument and validation</name>
  <files>filematcher/cli.py</files>
  <action>
1. Add argparse argument after --fallback-symlink:
   ```python
   parser.add_argument('--target-dir', '-t', type=str, metavar='PATH',
                       help='Create links in this directory instead of in-place (dir2 files deleted after linking)')
   ```

2. Add validation after existing validation block (around line 136):
   ```python
   if args.target_dir:
       if args.action not in ('hardlink', 'symlink'):
           parser.error("--target-dir only applies to --action hardlink or --action symlink")
       if not os.path.isdir(args.target_dir):
           parser.error(f"--target-dir must be an existing directory: {args.target_dir}")
   ```

3. Pass target_dir to execute_all_actions calls (2 locations around lines 336 and 431):
   Add `target_dir=args.target_dir` parameter

4. Update build_log_flags function signature to accept target_dir parameter and append to flags if present
  </action>
  <verify>
    python -c "from filematcher.cli import main; import sys; sys.argv = ['fm', '--help']" 2>&1 | grep -q "target-dir"
    # Also verify validation:
    python -c "from filematcher.cli import main; import sys; sys.argv = ['fm', 'test_dir1', 'test_dir2', '--target-dir', '/tmp', '--action', 'delete']; main()" 2>&1 | grep -q "only applies"
  </verify>
  <done>--target-dir argument parses correctly, validation rejects invalid action combinations</done>
</task>

<task type="auto">
  <name>Task 2: Implement target-dir execution logic in actions.py</name>
  <files>filematcher/actions.py, filematcher/cli.py</files>
  <action>
1. In actions.py, modify execute_action() signature to accept optional target_dir parameter:
   ```python
   def execute_action(
       duplicate: str,
       master: str,
       action: str,
       fallback_symlink: bool = False,
       target_dir: str | None = None,
       dir2_base: str | None = None  # needed to compute relative path
   ) -> tuple[bool, str, str]:
   ```

2. Add logic at start of execute_action() after existing skip checks:
   ```python
   if target_dir and dir2_base:
       # Compute relative path from dir2 to duplicate
       dup_path = Path(duplicate)
       dir2_path = Path(dir2_base).resolve()
       try:
           rel_path = dup_path.resolve().relative_to(dir2_path)
       except ValueError:
           return (False, f"Duplicate {duplicate} not under dir2 {dir2_base}", action)

       # Create target path preserving structure
       target_path = Path(target_dir) / rel_path
       target_path.parent.mkdir(parents=True, exist_ok=True)

       # Create link at target location
       master_path = Path(master)
       if action == 'hardlink':
           target_path.hardlink_to(master_path)
       elif action == 'symlink':
           target_path.symlink_to(master_path.resolve())

       # Delete original
       dup_path.unlink()
       return (True, "", action)
   ```

3. Modify execute_all_actions() signature to accept target_dir and dir2_base:
   ```python
   def execute_all_actions(
       duplicate_groups: list[tuple[str, list[str], str, str]],
       action: str,
       fallback_symlink: bool = False,
       verbose: bool = False,
       audit_logger: logging.Logger | None = None,
       file_hashes: dict[str, str] | None = None,
       target_dir: str | None = None,
       dir2_base: str | None = None
   ) -> tuple[int, int, int, int, list[tuple[str, str]]]:
   ```

4. Pass target_dir and dir2_base to execute_action() call inside execute_all_actions()

5. In cli.py, pass dir2_base=args.dir2 along with target_dir to execute_all_actions() calls
  </action>
  <verify>
    # Create test scenario and run:
    mkdir -p /tmp/fm_test/{master,dups,target}
    echo "content" > /tmp/fm_test/master/file.txt
    echo "content" > /tmp/fm_test/dups/file.txt
    python -m filematcher /tmp/fm_test/master /tmp/fm_test/dups --action hardlink --target-dir /tmp/fm_test/target --execute --yes
    # Verify: target/file.txt exists and is hardlink to master, dups/file.txt deleted
    test -f /tmp/fm_test/target/file.txt && ! test -f /tmp/fm_test/dups/file.txt && echo "PASS"
    rm -rf /tmp/fm_test
  </verify>
  <done>Links created in target-dir with proper relative paths, original files in dir2 deleted</done>
</task>

<task type="auto">
  <name>Task 3: Add comprehensive tests for --target-dir</name>
  <files>tests/test_actions.py, tests/test_cli.py</files>
  <action>
1. In tests/test_actions.py, add TestTargetDir class:
   ```python
   class TestTargetDir(unittest.TestCase):
       """Tests for --target-dir functionality."""

       def setUp(self):
           self.temp_dir = tempfile.mkdtemp()
           self.master_dir = Path(self.temp_dir) / "master"
           self.dup_dir = Path(self.temp_dir) / "dups"
           self.target_dir = Path(self.temp_dir) / "target"
           self.master_dir.mkdir()
           self.dup_dir.mkdir()
           self.target_dir.mkdir()

       def tearDown(self):
           shutil.rmtree(self.temp_dir)

       def test_hardlink_to_target_dir(self):
           """Hardlink created in target-dir, original deleted."""
           master = self.master_dir / "file.txt"
           dup = self.dup_dir / "file.txt"
           master.write_text("content")
           dup.write_text("content")

           success, error, action = execute_action(
               str(dup), str(master), "hardlink",
               target_dir=str(self.target_dir),
               dir2_base=str(self.dup_dir)
           )

           self.assertTrue(success)
           target_file = self.target_dir / "file.txt"
           self.assertTrue(target_file.exists())
           self.assertFalse(dup.exists())
           self.assertTrue(is_hardlink_to(str(master), str(target_file)))

       def test_symlink_to_target_dir(self):
           """Symlink created in target-dir, original deleted."""
           # Similar test for symlink action

       def test_preserves_subdirectory_structure(self):
           """Nested paths in dir2 are preserved in target-dir."""
           subdir = self.dup_dir / "sub" / "dir"
           subdir.mkdir(parents=True)
           master = self.master_dir / "file.txt"
           dup = subdir / "file.txt"
           master.write_text("content")
           dup.write_text("content")

           execute_action(
               str(dup), str(master), "hardlink",
               target_dir=str(self.target_dir),
               dir2_base=str(self.dup_dir)
           )

           target_file = self.target_dir / "sub" / "dir" / "file.txt"
           self.assertTrue(target_file.exists())
   ```

2. In tests/test_cli.py, add validation tests:
   ```python
   def test_target_dir_requires_link_action(self):
       """--target-dir rejected with delete or compare actions."""
       # Test that parser.error is triggered

   def test_target_dir_requires_existing_directory(self):
       """--target-dir rejected if directory doesn't exist."""
   ```

Run: python3 run_tests.py
  </action>
  <verify>python3 run_tests.py 2>&1 | tail -5</verify>
  <done>All new tests pass, no regressions in existing 218 tests</done>
</task>

</tasks>

<verification>
1. `python3 run_tests.py` - All tests pass (existing + new target-dir tests)
2. `python -m filematcher --help` - Shows --target-dir in help output
3. Manual test: Create hardlinks in target directory, verify originals deleted
4. Validation: --target-dir with --action delete produces error
</verification>

<success_criteria>
- --target-dir flag accepted and validated (only with hardlink/symlink)
- Links created in target directory preserving relative path structure
- Original files in dir2 deleted after successful link creation
- All tests pass (no regressions)
- Help text documents the flag behavior
</success_criteria>
