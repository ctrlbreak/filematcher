# Architecture Patterns: Deduplication Actions

**Domain:** File deduplication CLI tool with action execution
**Researched:** 2026-01-19

## Current Architecture

The existing `file_matcher.py` follows a clean functional pipeline:

```
CLI Layer (main)
    |
    v
Core Layer (find_matching_files)
    |
    +-- index_directory(dir1)  --> hash_to_files dict
    +-- index_directory(dir2)  --> hash_to_files dict
    |
    v
Set Operations (common_hashes, unique_hashes)
    |
    v
Output Layer (print matches, unmatched)
```

## Recommended Architecture for Deduplication

### Extended Pipeline

```
CLI Layer (main)
    |
    v
Core Layer (find_matching_files)  <-- existing, unchanged
    |
    v
NEW: Action Planning Layer
    |
    +-- identify_duplicates() --> list of DuplicateGroup
    +-- plan_actions(groups, master_dir, action_type) --> ActionPlan
    |
    v
NEW: Execution Layer
    |
    +-- dry_run_executor
    +-- interactive_executor
    +-- auto_executor
    |
    v
NEW: Change Logging Layer
```

### New Data Structures

```python
from dataclasses import dataclass
from enum import Enum

class ActionType(Enum):
    HARDLINK = "hardlink"
    SYMLINK = "symlink"
    DELETE = "delete"

class ExecutionMode(Enum):
    DRY_RUN = "dry-run"
    INTERACTIVE = "interactive"
    AUTO = "auto"

@dataclass
class DuplicateGroup:
    content_hash: str
    master_file: Path
    duplicates: list[Path]

@dataclass
class PlannedAction:
    action_type: ActionType
    source: Path
    target: Path | None
    space_savings: int
```

### Integration with Existing Code

```python
# In main(), after existing comparison:
matches, unmatched1, unmatched2 = find_matching_files(...)

# NEW: If action mode is enabled
if args.action:
    groups = identify_duplicates(matches, args.master)
    plan = plan_actions(groups, args.action_type)

    if args.execution_mode == ExecutionMode.DRY_RUN:
        display_plan(plan)
    else:
        result = execute_plan(plan, args.execution_mode)
        log_changes(result, args.change_log)
```

### Build Order

**Phase 1: Foundation**
1. Data structures (ActionType, ExecutionMode, etc.)
2. `identify_duplicates()` function
3. Tests for identify_duplicates

**Phase 2: Planning**
4. `plan_actions()` function
5. CLI argument additions (--master, --action, --mode)

**Phase 3: Dry-run**
6. `dry_run_executor()`
7. Integration with main()

**Phase 4: Action Implementations**
8. `create_hardlink()`, `create_symlink()`, `delete_duplicate()`
9. Unit tests with temp directories

**Phase 5: Auto Execution**
10. `auto_executor()`
11. Integration tests

**Phase 6: Interactive Mode**
12. `interactive_executor()`
13. Tests with mocked input

**Phase 7: Change Logging**
14. `log_changes()` function
15. CLI argument (--log)

### Error Handling Strategy

1. Never delete without verifying master exists
2. Verify content hash matches before action
3. Use atomic operations (os.replace)
4. Log failures but continue processing

---

*Architecture research: 2026-01-19*
