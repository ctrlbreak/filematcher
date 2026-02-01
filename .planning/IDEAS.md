# Feature Ideas

Potential features for future milestones. Not prioritized or committed.

## Filtering & Selection

- `--min-size` / `--max-size` - Only process files within size range
- `--include` / `--exclude` - Glob patterns for file filtering (e.g., `--include "*.mkv"`)
- `--newer-than` / `--older-than` - Date-based filtering
- `--max-depth` - Limit recursion depth

## Actions & Output

- `--action move` - Move duplicates to a trash/archive directory instead of delete
- `--action copy` - Copy master files to target directory (inverse of current flow)
- `--report html` - Generate HTML report with file previews
- `--export csv` - Export results to CSV for spreadsheet analysis

## Performance

- `--parallel N` - Multi-threaded hashing for faster indexing
- `--cache` / `--db PATH` - Persist hashes to avoid re-indexing unchanged files
- `--verify` - Verify existing hardlinks still point to same content

## Multi-Directory

- Support 3+ directories (one master, multiple duplicate sources)
- `--recursive-master` - Find best master from any directory, not just dir1

## Usability

- `--config FILE` - Load options from config file
- `--undo LOG` - Reverse operations using audit log (where possible)
- `--watch` - Monitor directories and report new duplicates

## Analysis

- `--duplicates-only` - Show files that exist in both dirs (no unmatched)
- `--stats` - Detailed statistics (duplicates by extension, size distribution)

---
*Created: 2026-02-01*
