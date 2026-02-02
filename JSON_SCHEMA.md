# JSON Schema Reference

File Matcher JSON output schema (v2.0). Use `--json` flag to enable.

## Compare Mode

```bash
filematcher master_dir other_dir --json
```

| Field | Type | Description |
|-------|------|-------------|
| `header.name` | string | "filematcher" |
| `header.version` | string | Schema version (e.g., "2.0") |
| `header.timestamp` | string | Execution time (RFC 3339) |
| `header.mode` | string | "compare" |
| `header.hashAlgorithm` | string | "md5" or "sha256" |
| `header.directories.master` | string | Master directory path (absolute) |
| `header.directories.duplicate` | string | Duplicate directory path (absolute) |
| `matches` | array | Groups of files with matching content |
| `matches[].hash` | string | Content hash for the group |
| `matches[].filesDir1` | array | File paths from master_dir (sorted) |
| `matches[].filesDir2` | array | File paths from other_dir (sorted) |
| `unmatchedMaster` | array | Unmatched files in master dir (with `--show-unmatched`) |
| `unmatchedDuplicate` | array | Unmatched files in duplicate dir (with `--show-unmatched`) |
| `summary.matchCount` | number | Number of unique content hashes with matches |
| `summary.matchedFilesDir1` | number | Files with matches in master_dir |
| `summary.matchedFilesDir2` | number | Files with matches in other_dir |
| `metadata` | object | Per-file metadata (with `--verbose`) |
| `metadata[path].sizeBytes` | number | File size in bytes |
| `metadata[path].modified` | string | Last modified time (RFC 3339) |

## Action Mode (Preview/Execute)

```bash
filematcher master_dir other_dir --action hardlink --json
filematcher master_dir other_dir --action hardlink --execute --yes --json
```

| Field | Type | Description |
|-------|------|-------------|
| `header.name` | string | "filematcher" |
| `header.version` | string | Schema version (e.g., "2.0") |
| `header.timestamp` | string | Execution time (RFC 3339) |
| `header.mode` | string | "preview" or "execute" |
| `header.action` | string | "hardlink", "symlink", or "delete" |
| `header.hashAlgorithm` | string | Hash algorithm used |
| `header.directories.master` | string | Master directory path (absolute) |
| `header.directories.duplicate` | string | Duplicate directory path (absolute) |
| `warnings` | array | Warning messages |
| `duplicateGroups` | array | Groups of duplicates |
| `duplicateGroups[].masterFile` | string | Master file path (preserved) |
| `duplicateGroups[].duplicates` | array | Duplicate file objects |
| `duplicateGroups[].duplicates[].path` | string | Duplicate file path |
| `duplicateGroups[].duplicates[].sizeBytes` | number | File size in bytes |
| `duplicateGroups[].duplicates[].action` | string | Action to apply |
| `duplicateGroups[].duplicates[].crossFilesystem` | boolean | True if on different filesystem |
| `duplicateGroups[].duplicates[].targetPath` | string | Target path (with `--target-dir`) |
| `statistics.groupCount` | number | Number of duplicate groups |
| `statistics.duplicateCount` | number | Total duplicate files |
| `statistics.masterCount` | number | Number of master files |
| `statistics.spaceSavingsBytes` | number | Bytes that would be/were saved |
| `statistics.crossFilesystemCount` | number | Files that cannot be hardlinked |

### Execution Results (with `--execute`)

| Field | Type | Description |
|-------|------|-------------|
| `execution.successCount` | number | Successful operations |
| `execution.failureCount` | number | Failed operations |
| `execution.skippedCount` | number | Skipped operations |
| `execution.spaceSavedBytes` | number | Actual bytes saved |
| `execution.logPath` | string | Path to audit log file |
| `execution.failures` | array | Failed operation details |
| `execution.failures[].path` | string | File that failed |
| `execution.failures[].error` | string | Error message |

## jq Examples

### Compare Mode

```bash
# List matching file pairs (first match from each directory)
filematcher master_dir other_dir --json | \
  jq -r '.matches[] | "\(.filesDir1[0]) <-> \(.filesDir2[0])"'

# Get match count
filematcher master_dir other_dir --json | jq '.summary.matchCount'

# List all matched files from master_dir
filematcher master_dir other_dir --json | jq -r '.matches[].filesDir1[]'

# Show matches with file count per group
filematcher master_dir other_dir --json | \
  jq -r '.matches[] | "\(.filesDir1 | length) in master, \(.filesDir2 | length) in other: \(.hash[:12])..."'
```

### Action Mode (Preview)

```bash
# Summary with human-readable space savings
filematcher master_dir other_dir --action hardlink --json | \
  jq '{groups: .statistics.groupCount, files: .statistics.duplicateCount,
       savings_mb: (.statistics.spaceSavingsBytes / 1048576 | floor)}'

# List duplicate paths (one per line)
filematcher master_dir other_dir --action hardlink --json | \
  jq -r '.duplicateGroups[].duplicates[].path'

# Show master → duplicate mappings
filematcher master_dir other_dir --action hardlink --json | \
  jq -r '.duplicateGroups[] | "\(.masterFile) -> \(.duplicates[].path)"'

# Find large duplicates (>100MB)
filematcher master_dir other_dir --action hardlink --json | \
  jq -r '.duplicateGroups[].duplicates[] | select(.sizeBytes > 104857600) | .path'

# List cross-filesystem files (can't hardlink)
filematcher master_dir other_dir --action hardlink --json | \
  jq -r '.duplicateGroups[].duplicates[] | select(.crossFilesystem) | .path'

# Count duplicates by extension
filematcher master_dir other_dir --action hardlink --json | \
  jq -r '[.duplicateGroups[].duplicates[].path | split(".") | .[-1]] | group_by(.) | map({ext: .[0], count: length}) | sort_by(-.count)[]'
```

### Execution Results

```bash
# Get execution summary
filematcher master_dir other_dir --action hardlink --execute --yes --json | \
  jq '{success: .execution.successCount, failed: .execution.failureCount,
       skipped: .execution.skippedCount, saved_mb: (.execution.spaceSavedBytes / 1048576 | floor)}'

# List failures with error messages
filematcher master_dir other_dir --action hardlink --execute --yes --json | \
  jq -r '.execution.failures[] | "\(.path): \(.error)"'

# Check if all operations succeeded
filematcher master_dir other_dir --action hardlink --execute --yes --json | \
  jq '.execution.failureCount == 0'
```

## Notes

- All file paths are absolute
- All lists are sorted for deterministic output
- Progress/status goes to stderr, JSON to stdout
- Timestamps use RFC 3339 format with timezone
- `--json --execute` requires `--yes` (no interactive prompts)
