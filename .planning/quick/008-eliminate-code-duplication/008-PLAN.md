---
phase: quick-008
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - file_matcher.py
autonomous: true

must_haves:
  truths:
    - "Hash algorithm selection is centralized in create_hasher()"
    - "Oldest file selection logic is centralized in select_oldest()"
    - "Path-in-directory checks use is_in_directory() helper"
    - "Banner constants are used directly (no wrapper functions)"
    - "Space savings calculated once and reused"
    - "No useless + [] concatenation remains"
  artifacts:
    - path: "file_matcher.py"
      provides: "Deduplicated helper functions"
      contains: "def create_hasher"
  key_links:
    - from: "get_file_hash"
      to: "create_hasher"
      via: "function call for hash algorithm selection"
      pattern: "create_hasher"
    - from: "get_sparse_hash"
      to: "create_hasher"
      via: "function call for hash algorithm selection"
      pattern: "create_hasher"
---

<objective>
Eliminate code duplication by extracting common patterns into helper functions

Purpose: Reduce code repetition and improve maintainability. Target ~60 lines reduction through helper extraction, inlining, and cleanup.

Output: Cleaner codebase with DRY principles applied to hashing, file selection, and banner formatting
</objective>

<execution_context>
@/Users/patrick/.claude/get-shit-done/workflows/execute-plan.md
@/Users/patrick/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@file_matcher.py (lines 1965-2003 - duplicate hash algorithm selection)
@file_matcher.py (lines 1140-1163 - select_master_file with repeated oldest/duplicate logic)
@file_matcher.py (lines 1283-1295 - banner functions)
@file_matcher.py (lines 2320-2430 - calculate_space_savings called 3x)
</context>

<tasks>

<task type="auto">
  <name>Task 1: Extract create_hasher() and is_in_directory() helpers</name>
  <files>file_matcher.py</files>
  <action>
1. Add `create_hasher()` helper near the hashing functions (around line 1950):

```python
def create_hasher(hash_algorithm: str = 'md5') -> hashlib._Hash:
    """Create a hash object for the specified algorithm.

    Args:
        hash_algorithm: 'md5' or 'sha256'

    Returns:
        Hash object ready for update() calls

    Raises:
        ValueError: If hash_algorithm is not supported
    """
    if hash_algorithm == 'md5':
        return hashlib.md5()
    elif hash_algorithm == 'sha256':
        return hashlib.sha256()
    else:
        raise ValueError(f"Unsupported hash algorithm: {hash_algorithm}")
```

2. Update `get_file_hash()` (lines 1965-1970) to use it:
   - Replace the if/elif/else block with: `h = create_hasher(hash_algorithm)`

3. Update `get_sparse_hash()` (lines 1998-2003) to use it:
   - Replace the if/elif/else block with: `h = create_hasher(hash_algorithm)`

4. Add `is_in_directory()` helper near `select_master_file()` (around line 1125):

```python
def is_in_directory(filepath: str, directory: str) -> bool:
    """Check if a file path is within a directory.

    Handles both exact match and subdirectory containment.

    Args:
        filepath: The file path to check
        directory: The directory to check against

    Returns:
        True if filepath is in or under directory
    """
    return filepath.startswith(directory + os.sep) or filepath.startswith(directory)
```

5. Update `select_master_file()` (line 1142) to use it:
   - Change: `master_files = [f for f in file_paths if f.startswith(master_dir_str + os.sep) or f.startswith(master_dir_str)]`
   - To: `master_files = [f for f in file_paths if is_in_directory(f, master_dir_str)]`

6. Update main() (line 2282) to use it:
   - Change: `if f.startswith(master_dir_str + os.sep) or f.startswith(master_dir_str)`
   - To: `if is_in_directory(f, master_dir_str)`

Estimated savings: ~12 lines from create_hasher, ~4 lines from is_in_directory
  </action>
  <verify>
Run: `python3 -c "from file_matcher import create_hasher, is_in_directory; h = create_hasher('md5'); print(type(h)); print(is_in_directory('/foo/bar.txt', '/foo'))"` - outputs hash type and True.
Run: `python3 -m tests.test_file_hashing` - all tests pass.
Run: `python3 -m tests.test_fast_mode` - all tests pass (sparse hash uses create_hasher).
  </verify>
  <done>create_hasher() and is_in_directory() extracted, all callers updated</done>
</task>

<task type="auto">
  <name>Task 2: Inline banners, extract select_oldest(), consolidate space savings</name>
  <files>file_matcher.py</files>
  <action>
1. **Inline banner functions** (lines 1287-1295):
   - Delete `format_preview_banner()` and `format_execute_banner()` functions
   - Update callers to use constants directly:
     - Line 858: `format_preview_banner()` -> `PREVIEW_BANNER`
     - Line 860: `format_execute_banner()` -> `EXECUTE_BANNER`
     - Line 1091: `format_execute_banner()` -> `EXECUTE_BANNER`
   Savings: ~8 lines

2. **Extract select_oldest() helper** (add near select_master_file, around line 1125):

```python
def select_oldest(file_paths: list[str]) -> tuple[str, list[str]]:
    """Select the oldest file by mtime and return it with remaining files.

    Args:
        file_paths: Non-empty list of file paths

    Returns:
        Tuple of (oldest_file, list_of_other_files)
    """
    oldest = min(file_paths, key=lambda p: os.path.getmtime(p))
    others = [f for f in file_paths if f != oldest]
    return oldest, others
```

3. **Update select_master_file()** to use select_oldest():
   - Lines 1151-1153 (multiple files in master):
     ```python
     oldest_master, other_master_files = select_oldest(master_files)
     return oldest_master, other_master_files + other_files, "oldest in master directory"
     ```
   - Lines 1156-1158 (no files in master):
     ```python
     oldest, duplicates = select_oldest(file_paths)
     return oldest, duplicates, "oldest file (none in master directory)"
     ```
   - Lines 1161-1163 (no master_dir set):
     ```python
     oldest, duplicates = select_oldest(file_paths)
     return oldest, duplicates, "oldest file"
     ```
   Savings: ~6 lines

4. **Remove useless + []** (line 1148):
   - Change: `return master_files[0], other_files + [], "only file in master directory"`
   - To: `return master_files[0], other_files, "only file in master directory"`
   Savings: trivial but cleaner

5. **Consolidate calculate_space_savings()** (lines 2331, 2354, 2414):
   The function is called 3 times with identical `master_results` argument.
   Refactor `print_preview_output()` to calculate once at the top:

   At the start of print_preview_output():
   ```python
   # Pre-calculate space savings once for non-compare actions
   space_info = None
   if args.action != 'compare':
       space_info = calculate_space_savings(master_results)
   ```

   Then use `space_info` tuple unpacking where needed:
   - Line 2331: `bytes_saved, dup_count, grp_count = space_info`
   - Line 2354: `bytes_saved, dup_count, grp_count = space_info`
   - Line 2414: `bytes_saved, dup_count, grp_count = space_info`

   Savings: ~4 lines (2 redundant calls removed)

Total estimated savings: ~30 lines (combined with Task 1's ~16 = ~46 lines)
  </action>
  <verify>
Run: `python3 -c "from file_matcher import PREVIEW_BANNER, EXECUTE_BANNER, select_oldest; print(PREVIEW_BANNER); print(select_oldest(['/a', '/b']))"` - outputs banner and tuple.
Run: `python3 -m tests.test_master_directory` - all tests pass.
Run: `python3 run_tests.py` - all 206 tests pass.
Run: `python3 file_matcher.py test_dir1 test_dir2 -a hardlink` - output unchanged.
  </verify>
  <done>Banners inlined, select_oldest extracted, space savings consolidated, + [] removed</done>
</task>

<task type="auto">
  <name>Task 3: Verify line reduction and final cleanup</name>
  <files>file_matcher.py</files>
  <action>
1. Count lines before (should be around 2611) and after changes
2. Verify all tests still pass
3. Remove any orphaned comments that referenced the old code
4. Ensure no regressions in functionality:
   - Compare mode
   - Action modes (hardlink, symlink, delete)
   - Preview and execute modes
   - Fast mode (sparse hashing)
   - JSON output

If line reduction is less than expected (~60 target), look for additional opportunities:
- Any other repeated patterns in the codebase
- Unused imports or variables
- Overly verbose docstrings that can be tightened
  </action>
  <verify>
Run: `wc -l file_matcher.py` - should show ~2550 or fewer lines (60+ reduction from 2611)
Run: `python3 run_tests.py` - all 206 tests pass
Run: `python3 file_matcher.py test_dir1 test_dir2` - compare works
Run: `python3 file_matcher.py test_dir1 test_dir2 -a hardlink -f` - fast mode works
Run: `python3 file_matcher.py test_dir1 test_dir2 --json` - JSON output valid
  </verify>
  <done>Line count reduced by ~60, all functionality preserved, all tests pass</done>
</task>

</tasks>

<verification>
1. All tests pass: `python3 run_tests.py` (206 tests)
2. Helper functions work: `python3 -c "from file_matcher import create_hasher, is_in_directory, select_oldest"`
3. No functional regression: test all modes manually
4. Line count reduced: `wc -l file_matcher.py` shows ~2550 or fewer
5. Code inspection: no duplicate hash selection, no duplicate oldest-file logic, no wrapper banner functions
</verification>

<success_criteria>
- create_hasher() eliminates duplicate hash algorithm selection
- is_in_directory() eliminates duplicate path containment checks
- select_oldest() eliminates duplicate oldest-file-with-remainder logic
- Banner wrapper functions removed, constants used directly
- calculate_space_savings() called once per output path
- No useless + [] concatenation
- All 206 tests pass
- ~60 lines reduction achieved
</success_criteria>

<output>
After completion, create `.planning/quick/008-eliminate-code-duplication/008-SUMMARY.md`
</output>
