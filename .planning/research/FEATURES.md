# Feature Landscape: File Deduplication CLI Tools

**Domain:** File deduplication CLI utilities
**Researched:** 2026-01-19
**Reference Tools:** fdupes, jdupes, rdfind, rmlint

## Table Stakes

Features users expect from any file deduplication tool.

| Feature | Why Expected | Complexity |
|---------|--------------|------------|
| **Dry-run mode** | Users MUST see what will change before destructive operations | Low |
| **Delete duplicates** | Core action users need | Low |
| **Hard link replacement** | Primary space-saving mechanism | Low |
| **Symbolic link replacement** | Alternative when hard links not possible | Low |
| **Preserve master copy** | Clear "which file survives" semantics | Low |
| **Verbose output** | Users need to understand what happened | Low |
| **Summary statistics** | Quick overview of space saved | Low |
| **Error handling with continuation** | Don't stop on first permission error | Low |

## Differentiators

Features that would set File Matcher apart.

| Feature | Value Proposition | Complexity |
|---------|-------------------|------------|
| **Interactive mode per-file prompts** | Fine-grained control for cautious users | Medium |
| **JSON/machine-readable output** | Integration with other tools | Low |
| **Undo log / change manifest** | Recovery from mistakes | Medium |
| **Space savings estimate before action** | User can decide if worth it | Low |

## Anti-Features

Features to explicitly NOT build.

| Anti-Feature | Why Avoid |
|--------------|-----------|
| Automatic selection of "best" file | Unclear semantics; users don't trust heuristics |
| In-place dedup without explicit action flag | Too dangerous as default |
| Recursive link following by default | Can cause infinite loops |
| Automatic backup creation | Scope creep; user's responsibility |
| Multi-directory master selection | Complexity explosion |

## Feature Dependencies

```
Dry-run mode (MUST have before any action)
    |
    +---> Delete action
    +---> Hard link action
    +---> Symbolic link action
    |
    v
Interactive mode (optional layer)
    |
    v
Change logging (enhances all actions)
```

## Recommended CLI Pattern

```bash
filematcher dir1 dir2                           # Report only (current)
filematcher dir1 dir2 --master dir1 --dry-run   # Preview changes
filematcher dir1 dir2 --master dir1 --hardlink  # Execute hard linking
filematcher dir1 dir2 --master dir1 --delete    # Execute deletion
filematcher dir1 dir2 --master dir1 --hardlink --interactive  # Prompt per group
```

## Safety Features

| Safety Feature | Criticality |
|----------------|-------------|
| Dry-run as explicit mode | CRITICAL |
| Require `--master` for any action | HIGH |
| Never modify files in master directory | CRITICAL |
| Log all changes | HIGH |
| Verify link creation | MEDIUM |

---

*Features research: 2026-01-19*
