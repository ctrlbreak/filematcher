# Feature Landscape: CLI Output Formatting

**Domain:** CLI tool output formatting and JSON output
**Researched:** 2026-01-22
**Confidence:** HIGH

## Executive Summary

This research examines how established CLI tools format output, focusing on duplicate file finders (fdupes, jdupes, rdfind) and general CLI patterns (git, ls, find, AWS CLI). The goal is identifying table stakes vs. differentiators for unified output formatting and JSON output in File Matcher.

**Key Finding:** Modern CLI tools in 2026 provide three output modes: (1) human-readable structured text, (2) machine-readable structured formats (JSON/JSONL), and (3) null-separated output for safe scripting. Tools that mix these modes poorly create friction.

## Table Stakes

Features users expect. Missing = product feels incomplete.

### 1. Consistent Output Structure

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Same format across modes | Users build mental model | Low | File Matcher currently has compare mode (hash groups) vs action mode (master/dup) inconsistency |
| Blank line group separators | Universal CLI pattern | Low | Already implemented in File Matcher |
| One item per line | Scriptability baseline | Low | Standard across fdupes, jdupes, rdfind |
| Sorted output | Predictability for diffs | Low | Alphabetical sorting is standard |

**Sources:**
- [fdupes man page](https://linux.die.net/man/1/fdupes) - Default format: groups separated by blank lines
- [jdupes documentation](https://manpages.debian.org/testing/jdupes/jdupes.1.en.html) - "One file path per line, match sets separated by blank line"

### 2. Human-Readable vs Machine-Readable Separation

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Progress to stderr, results to stdout | Unix convention | Low | Allows `tool \| jq` without contamination |
| Machine format without progress bars | CI/automation compatibility | Low | Git `--porcelain`, AWS CLI `--output json` follow this |
| Clear labels in human mode | Reduces cognitive load | Low | `[MASTER]`, `[DUP]` labels (already in File Matcher) |

**Sources:**
- [Git porcelain format](https://git-scm.com/docs/pretty-formats) - Machine-readable, minimal output
- [CLI Best Practices](https://clig.dev/) - "Send messages to stderr if stdout outputs data"

### 3. JSON Output Foundation

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| `--json` or `-j` flag | Established convention | Low | jdupes uses `-j`, AWS CLI uses `--output json` |
| Valid JSON document | Basic parsability | Low | Single object or array |
| Predictable schema | Downstream tools depend on this | Medium | Schema should be documented |
| Proper error handling | JSON must be valid even on error | Medium | Error cases return JSON error object |

**Sources:**
- [jdupes JSON output](https://manpages.debian.org/testing/jdupes/jdupes.1.en.html) - `-j, --json: produce JSON output`
- [CLI JSON Best Practices](https://blog.kellybrazil.com/2021/12/03/tips-on-adding-json-output-to-your-cli-app/) - Schema documentation, error handling

### 4. Safe Scripting Support

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Null-separator option | Handles spaces/newlines in filenames | Low | `find -print0`, `xargs -0` pattern |
| Exit codes (0=success, 1=error) | Shell script conditionals | Low | Already implemented in File Matcher |
| No ANSI codes when not TTY | Prevents escape codes in logs | Low | Check `sys.stdout.isatty()` |

**Sources:**
- [jdupes null separator](https://manpages.debian.org/testing/jdupes/jdupes.1.en.html) - `-0, --print-null: use null bytes instead of CR/LF`
- [Null separator pattern](https://www.baeldung.com/linux/zero-null-command-line) - "Completely unambiguous format"

### 5. Summary vs Detailed Modes

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| `--summary` shows counts only | Quick overview without scrolling | Low | Already implemented in File Matcher |
| Default shows file paths | Primary use case | Low | Current behavior |
| Optional verbose details | Power users need file sizes | Low | Already implemented with `-v` |

**Sources:**
- [fdupes summary](https://linux.die.net/man/1/fdupes) - `-m, --summarize: summarize duplicate info`
- [rdfind output modes](https://rdfind.pauldreik.se/rdfind.1.html) - Console progress + results file

## Differentiators

Features that set product apart. Not expected, but valued.

### 1. JSON Lines (JSONL) for Streaming

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| JSONL format option | Process results progressively | Medium | One JSON object per line, enables `\| jq -s` |
| Works with large datasets | No memory buffer entire result | Medium | Critical for 10K+ file scans |
| Compatible with jq streaming | Modern data pipeline pattern | Low | jq can process line-by-line |

**Why Differentiator:** fdupes/jdupes output JSON as complete document. JSONL is modern pattern (2026) but not yet universal in CLI duplicate finders.

**Sources:**
- [JSON Lines specification](https://jsonlines.org/) - Standard for streaming JSON
- [JSONL for CLI tools](https://blog.kellybrazil.com/2021/12/03/tips-on-adding-json-output-to-your-cli-app/) - "For unlimited output, use JSON Lines"
- [JSONL in 2026](https://ndjson.com/) - "Most used standard for streaming data"

### 2. Unified Format Across Modes

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Compare and action modes use same structure | Single mental model | Medium | File Matcher currently has two different formats |
| Master/duplicate always explicit | Reduces ambiguity | Low | Action mode has this, compare mode should adopt |
| Consistent field ordering | Easier to parse visually | Low | Master first, duplicates indented |

**Why Differentiator:** Most duplicate finders have single mode. File Matcher's dual modes (compare vs action) are unique, so unified format is competitive advantage.

### 3. Rich Metadata in JSON

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| File sizes in JSON | Enables downstream filtering | Low | Already calculated, just expose |
| Modification times | Support time-based selection | Low | Available from os.stat |
| Hash values in output | Verification and debugging | Low | Already computed |
| Filesystem device IDs | Cross-fs warnings | Medium | Already implemented for hardlink checking |

**Why Differentiator:** Competitors output minimal data. Rich metadata enables advanced workflows without re-scanning.

### 4. Color-Coded Output (TTY Only)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Color master files differently | Visual hierarchy | Low | Green for master, yellow for duplicates |
| Warning colors for cross-fs | Attention to limitations | Low | Red text for cross-filesystem hardlink failures |
| Auto-disable when not TTY | CI compatibility | Low | Already standard practice |

**Why Differentiator:** Most duplicate finders don't use color. Modern CLIs (git, ls with `--color`, ripgrep) do.

**Sources:**
- [CLI Color Best Practices](http://bixense.com/clicolors/) - NO_COLOR, CLICOLOR, CLICOLOR_FORCE env vars
- [ANSI Color Guidelines](https://trentm.com/2024/09/choosing-readable-ansi-colors-for-clis.html) - Avoid blue, bright yellow

### 5. Table Output Format

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| `--format table` option | Columnar alignment | Medium | Like `ls -l` or Azure CLI |
| Auto-width columns | Fits terminal width | Medium | Use text/tabwriter pattern |
| Header row | Self-documenting columns | Low | Type, Size, Path |

**Why Differentiator:** No duplicate finder offers tabular output. Common in cloud CLIs (AWS, Azure, kubectl).

**Sources:**
- [Azure CLI table format](https://learn.microsoft.com/en-us/cli/azure/format-output-azure-cli) - "Easy to read and scan"
- [Go tabwriter](https://reintech.io/blog/a-guide-to-gos-text-tabwriter-package-aligning-text) - Standard library for aligned columns

## Anti-Features

Features to explicitly NOT build. Common mistakes in this domain.

### 1. Mixed Human and Machine Output

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Progress bars in JSON output | Breaks JSON parsers | Always send progress to stderr, JSON to stdout |
| Colored output in pipes | Escape codes pollute logs | Only color when `isatty()` true |
| Headers in machine formats | Non-standard JSON | Headers are anti-pattern in JSON (schema serves that role) |

**Evidence:** Git `--porcelain` explicitly avoids this. AWS CLI separates `--output json` from progress messages.

**Sources:**
- [CLI UX Best Practices](https://evilmartians.com/chronicles/cli-ux-best-practices-3-patterns-for-improving-progress-displays) - "If stdout is not TTY, don't display animations"

### 2. Custom/Proprietary Formats

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Inventing new structured format | No tooling support | Use JSON or JSONL (universal parsers) |
| CSV for hierarchical data | Poor fit for nested groups | JSON handles nesting naturally |
| XML output | Heavy, outdated | JSON is 2026 standard |

**Evidence:** Modern tools converge on JSON. Even older tools (systemd, Docker) added JSON output.

### 3. Inconsistent Flag Names

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| `--json` in one mode, `--format json` in another | Frustrates users | Pick one convention, use everywhere |
| Short flags that conflict with standards | Breaks muscle memory | `-v` = verbose, `-j` = JSON (jdupes pattern) |
| Non-standard exit codes | Shell scripts break | 0=success, 1=error, 2=invalid args (argparse standard) |

**Evidence:** File Matcher already follows this (consistent flags across modes).

### 4. Redundant Output

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Repeating file paths in JSON | Bloats output | Use references or IDs |
| Printing hash for every file | Noise in human output | Hash once per group or only in verbose |
| Multiple summary sections | Confusing | Single summary at end |

**Evidence:** jdupes minimal output: one line per file, blank line separator. Clean.

### 5. Unsafe Defaults

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Default to machine format | Confuses new users | Human-readable is default, machine format opt-in |
| Assuming filenames have no special chars | Scripts break on spaces/newlines | Offer null-separator for safety |
| Silent truncation | Data loss | Warn if output truncated |

**Evidence:** All mature CLI tools (git, find, ls) default to human-readable, require flags for machine format.

## Feature Dependencies

```
JSON Output Foundation (Table Stakes)
  └─> JSON Lines Streaming (Differentiator)
       └─> Rich Metadata in JSON (Differentiator)

Consistent Output Structure (Table Stakes)
  └─> Unified Format Across Modes (Differentiator)

Safe Scripting Support (Table Stakes)
  └─> Null-separator option

Human vs Machine Separation (Table Stakes)
  └─> Color-Coded Output (Differentiator, TTY only)
  └─> Table Output Format (Differentiator)
```

## MVP Recommendation

For MVP unified output + JSON milestone, prioritize:

### Must Have (Table Stakes)
1. **Consistent output structure** - Unify compare and action modes to same format
2. **JSON output foundation** - `--json` flag producing valid JSON with documented schema
3. **Human/machine separation** - Progress to stderr, results to stdout
4. **Safe scripting support** - Null-separator option (`-0` flag)
5. **Summary vs detailed** - Already implemented, maintain consistency

### Should Have (Quick Wins)
6. **Color-coded output** - Low complexity, high UX value for TTY users
7. **Rich metadata in JSON** - Data already available, just expose it

### Defer to Post-MVP
- **JSON Lines streaming** - Implement after basic JSON works
- **Table output format** - Medium complexity, lower priority
- **Advanced metadata** - Nice-to-have, not critical

## Implementation Sequence

**Phase 1: Unification (Week 1)**
- Adopt action mode's master/duplicate structure in compare mode
- Ensure consistent formatting functions across both modes
- Update existing tests

**Phase 2: JSON Foundation (Week 1)**
- Add `--json` flag
- Design and document schema
- Implement JSON serialization for duplicate groups
- Error handling in JSON mode

**Phase 3: Enhancements (Week 2)**
- Null-separator output (`-0` flag)
- TTY detection and color output
- Rich metadata in JSON (sizes, times, hashes)

**Phase 4: Advanced (Post-MVP)**
- JSONL streaming format
- Table output format
- Performance optimization for large result sets

## User Expectations from Domain Research

Based on 2026 duplicate file finder user expectations:

**Performance:** Users expect "fast, accurate detection" with "multicore processing"
**Control:** Users want "complete control over files to delete" - no auto-deletion
**Automation:** Power users need "CLI tool for scripting and automation workflows"
**Safety:** Tools must "not delete files by itself" and give clear preview

**Sources:**
- [Duplicate finder user reviews](https://www.linuxlinks.com/dupster-duplicate-file-finder/) - "Built for developers, sysadmins, power users"
- [DuoBolt review](https://sourceforge.net/directory/duplicate-file-finders/) - "Fast detection for large data volumes"

## Confidence Assessment

| Area | Level | Reason |
|------|-------|--------|
| Table stakes features | HIGH | Verified with official documentation from multiple tools |
| Differentiators | HIGH | Cross-referenced modern CLI patterns (AWS, Azure, git) |
| Anti-features | MEDIUM | Based on community wisdom, less documented |
| JSON standards | HIGH | Official specifications (JSON Lines, NDJSON) and CLI tools expert blog |
| User expectations | MEDIUM | Based on reviews and tool descriptions, not direct user research |

## Gaps and Future Research

**Not covered in this research:**
- Accessibility considerations (screen readers, high contrast)
- Internationalization (i18n) for output messages
- Specific JSON schema design (deferred to implementation phase)
- Performance benchmarks for JSONL vs JSON on large datasets

**Recommend phase-specific research for:**
- JSONL implementation patterns in Python
- Terminal width detection and wrapping strategies for table format
- ANSI color library selection (colorama vs termcolor vs rich)

## Sources Summary

**Authoritative Documentation:**
- [fdupes man page](https://linux.die.net/man/1/fdupes)
- [jdupes Debian manpage](https://manpages.debian.org/testing/jdupes/jdupes.1.en.html)
- [rdfind official documentation](https://rdfind.pauldreik.se/rdfind.1.html)
- [Git pretty-formats](https://git-scm.com/docs/pretty-formats)
- [JSON Lines specification](https://jsonlines.org/)

**Best Practices Guides:**
- [CLI JSON Best Practices - Kelly Brazil](https://blog.kellybrazil.com/2021/12/03/tips-on-adding-json-output-to-your-cli-app/)
- [Command Line Interface Guidelines (clig.dev)](https://clig.dev/)
- [CLI UX Best Practices - Evil Martians](https://evilmartians.com/chronicles/cli-ux-best-practices-3-patterns-for-improving-progress-displays)
- [ANSI Color Standards](http://bixense.com/clicolors/)
- [Choosing Readable ANSI Colors](https://trentm.com/2024/09/choosing-readable-ansi-colors-for-clis.html)

**Community Research:**
- [NDJSON.com - JSONL Resource](https://ndjson.com/)
- [Baeldung: Null Separator Pattern](https://www.baeldung.com/linux/zero-null-command-line)
- [Azure CLI Output Formats](https://learn.microsoft.com/en-us/cli/azure/format-output-azure-cli)
- [Duplicate Finder User Expectations](https://www.linuxlinks.com/dupster-duplicate-file-finder/)
