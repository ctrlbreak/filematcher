---
status: resolved
trigger: "hardlinks-shown-as-duplicates"
created: 2026-01-24T00:00:00Z
updated: 2026-01-24T01:56:00Z
---

## Current Focus

hypothesis: CONFIRMED - is_hardlink_to() exists but is only called in execute_action() (line 1793), not during display/comparison phase
test: Found that find_matching_files() and calculate_space_savings() never check inode - they only check content hash
expecting: Need to filter out already-hardlinked files from duplicates list before displaying or calculating space
next_action: COMPLETE - Fix implemented and verified

## Symptoms

expected: Files that are already hardlinks (same inode) should not be shown as duplicates to reclaim, since they're already the same file on disk
actual: Hardlinked files appear as normal duplicate matches. The tool reports "7.9 GB reclaimable" for files that share the same inode.
errors: No errors, just incorrect behavior
reproduction: |
  python3 ./file_matcher.py /mnt/user/torrents/download/Radarr/ /mnt/user/torrents/new-media/Films/ --verbose --fast
  Output shows:
  [366/366] MASTER: /mnt/user/torrents/download/Radarr/tl-sc/Short.Circuit.1986.1080p.BluRay.x264-TiMELORDS.mkv (1 duplicates, 7.9 GB)
      DUPLICATE: /mnt/user/torrents/new-media/Films/Short Circuit (1986)/Short Circuit 1986 1080p BluRay DTS x264-TiMELORDS.mkv
  But `ls -ali` shows both files have same inode `649644249350940051` and link count of 2.
started: Unknown - may have always been this way

## Eliminated

## Evidence

- timestamp: 2026-01-24T00:01:00Z
  checked: is_hardlink_to() function usage in codebase
  found: |
    - is_hardlink_to() exists at line 1660 and correctly checks if two files share same inode+device
    - ONLY called in execute_action() at line 1793 to skip files already hardlinked during ACTION execution
    - NEVER called during comparison/display phase
  implication: The check happens too late - files are displayed as duplicates before execution even starts

- timestamp: 2026-01-24T00:01:00Z
  checked: find_matching_files() function (line 2285)
  found: |
    - Indexes directories by content hash
    - Returns all files with matching hashes across both directories
    - No inode checking whatsoever
  implication: Core matching logic treats hardlinked files as separate duplicates because they have matching content hash

- timestamp: 2026-01-24T00:01:00Z
  checked: calculate_space_savings() function (line 1577)
  found: |
    - Counts all duplicates and sums their sizes
    - No check for whether duplicates are already hardlinked to master
    - Reports full size of hardlinked files as "reclaimable" space
  implication: Space savings calculation is inflated for already-hardlinked files

- timestamp: 2026-01-24T00:01:00Z
  checked: main() master_results processing (lines 2454-2466)
  found: |
    - select_master_file() called for each match group
    - Duplicates list includes all non-master files
    - No filtering of already-hardlinked duplicates
  implication: The issue is in the results processing - duplicates already linked to master should be filtered out

## Resolution

root_cause: |
  is_hardlink_to() check only happens during execute_action() (line 1793), but display and
  space calculations happen in preview phase before execution. Files that are already hardlinked
  share the same inode so they're essentially the same file on disk - but the tool only checks
  content hash during comparison, reporting them as "duplicates" with reclaimable space when
  no space would actually be saved. The check needs to happen earlier, when building master_results.

fix: |
  1. Added filter_hardlinked_duplicates() helper function after is_symlink_to() (line 1703)
     - Takes master_file and duplicates list
     - Returns (actionable_duplicates, already_hardlinked) tuple
     - Uses existing is_hardlink_to() for inode comparison

  2. Modified master_results loop in main() (line 2494-2505)
     - Call filter_hardlinked_duplicates() after select_master_file()
     - Track total_already_hardlinked count
     - Only add groups to master_results if there are actionable duplicates

  3. Added logger.info() message when hardlinked files are skipped (line 2508-2509)
     - "Skipped N files already hardlinked to master (no space savings)"

  4. Fixed test fixtures in test_dir2/ - removed accidental hardlinks

verification: |
  - All 222 tests pass (6 new tests added)
  - Manual test with hardlink + copy:
    - dir1/original.txt -> dir2/already_linked.txt (hardlink)
    - dir1/original.txt copied to dir2/real_copy.txt
    - Tool correctly shows only real_copy.txt as duplicate
    - Reports "1 files, 31 B reclaimable" (not 2 files, 62 B)
    - Logs "Skipped 1 files already hardlinked to master"

files_changed:
  - file_matcher.py (added filter_hardlinked_duplicates, modified main())
  - tests/test_directory_operations.py (added TestFilterHardlinkedDuplicates)
  - tests/test_cli.py (added 2 integration tests)
  - test_dir2/different_name.txt (recreated without hardlink)
  - test_dir2/also_different_name.txt (recreated without hardlink)
