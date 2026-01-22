# Project Research Summary

**Project:** File Matcher v1.2 - Output Formatting and JSON Support
**Domain:** CLI tool output unification (text and structured formats)
**Researched:** 2026-01-22
**Confidence:** HIGH

## Executive Summary

File Matcher v1.2 aims to unify scattered output formatting across compare and action modes while adding JSON output support. Research shows this is achievable using only Python's standard library with minimal architectural changes. The recommended approach is a lightweight formatter abstraction (Protocol + TextFormatter + JsonFormatter) that wraps existing output functions, avoiding big-bang refactoring while enabling JSON output.

The critical risk is breaking existing user scripts that parse output with grep, awk, or sed. Industry best practice (Git, AWS CLI, jq) demonstrates that machine-readable output must exist BEFORE changing human-readable formats. File Matcher should implement --json flag first, document stability guarantees explicitly, and maintain text output compatibility during unification. The scattered output code (lines 1045-1340 of file_matcher.py) can be consolidated incrementally through a 4-phase refactor, with each phase passing existing tests before proceeding.

The research identifies standard CLI patterns for duplicate file finders (fdupes, jdupes, rdfind) and modern output expectations (stdout/stderr separation, TTY detection, null separators for safe scripting). With proper execution, this milestone delivers both improved maintainability through unified formatting and enhanced automation capabilities through structured JSON output.

## Key Findings

### Recommended Stack

The standard library approach continues File Matcher's zero-dependency philosophy while providing full control over output formatting.

**Core technologies:**
- **json module**: JSON serialization with indent, sort_keys, ensure_ascii control — battle-tested, full-featured, zero overhead
- **str.format()**: Structured text formatting (already in use) — sufficient for alignment, padding, width control without new imports
- **dataclasses (optional)**: Clean data modeling with asdict() for JSON conversion — Python 3.7+ standard library, type-safe

**What NOT to use:**
- pprint module — wrong abstraction (Python repr, not CLI output)
- textwrap module — not needed (no paragraph wrapping required)
- Third-party libraries (rich, tabulate, orjson) — violates zero-dependency constraint

**Key insight:** Continue with existing string methods and json.dumps() from standard library. Enhancement opportunity: flatten output using format functions, then route through formatter abstraction for text vs JSON output.

### Expected Features

Based on analysis of established CLI tools (fdupes, jdupes, rdfind, git, AWS CLI), the feature landscape reveals clear table stakes vs differentiators.

**Must have (table stakes):**
- Consistent output structure — same format across compare and action modes (currently inconsistent)
- JSON output foundation — --json flag producing valid, documented schema
- Human/machine separation — progress to stderr, results to stdout (Unix convention)
- Safe scripting support — null-separator option (-0 flag) for filenames with spaces/newlines
- Summary vs detailed modes — already implemented, maintain during unification

**Should have (competitive advantages):**
- Color-coded output (TTY only) — modern CLI pattern, low complexity, high UX value
- Rich metadata in JSON — file sizes, hashes, timestamps already available, just expose them
- Unified format across modes — File Matcher's dual modes (compare vs action) are unique, unified format is competitive advantage

**Defer to post-MVP:**
- JSON Lines (JSONL) streaming — for 10K+ file scans, implement after basic JSON works
- Table output format — like ls -l or Azure CLI, medium complexity
- Advanced metadata — filesystem IDs, modification times beyond basic needs

**Anti-features to avoid:**
- Mixed human and machine output on stdout — breaks parsing
- Custom/proprietary formats — no tooling support, use JSON
- Inconsistent flag names — maintain existing conventions
- Unsafe defaults — human-readable default, machine format opt-in

### Architecture Approach

The recommended pattern is a lightweight formatter abstraction that respects the single-file implementation constraint while providing clean separation of concerns.

**Pattern:** Protocol-based formatters (~150 lines added to file_matcher.py)

```
OutputFormatter (Protocol)
  ├─ format_banner(mode, execute)
  ├─ format_group(master, duplicates, ...)
  ├─ format_statistics(...)
  └─ finalize()

TextFormatter (~100 lines)
  └─ Wraps existing format_* functions

JsonFormatter (~80 lines)
  └─ Accumulates dict, outputs in finalize()
```

**Major components:**
1. **OutputFormatter Protocol** — minimal interface for text/JSON implementations
2. **TextFormatter** — delegates to existing format_duplicate_group(), format_statistics_footer() functions (preserves current output)
3. **JsonFormatter** — accumulates structured data, outputs valid JSON in finalize()
4. **output_results() function** — unified output logic extracted from four current branches in main()

**Integration points:**
- Create formatter after argparse: `formatter = create_formatter(args.format)`
- Replace lines 1045-1340 in main() with output_results() call
- Existing format_* helpers remain, called by TextFormatter only

**Build order:** Incremental refactoring in 5 phases (see Implications for Roadmap)

### Critical Pitfalls

Research identified 10 pitfalls specific to CLI output format changes, ranked by severity.

1. **Breaking scripts by changing default output** — users parse with grep/awk/sed. Prevention: Add --json BEFORE changing text format, document stability contract, test with parsing patterns.

2. **JSON schema drift without versioning** — renaming keys or changing types breaks downstream tools. Prevention: Document schema from day one, version explicitly, follow append-only evolution, validate in CI.

3. **Mixing human messages with machine output on stdout** — breaks jq parsing. Prevention: All data to stdout, messages to stderr; detect TTY; test with pipes.

4. **Inconsistent flag interactions** — --verbose with --json behaves unpredictably. Prevention: Design interaction matrix upfront, make modes mutually exclusive where appropriate, test all combinations.

5. **No migration path from old to new output** — forces immediate script rewrites. Prevention: Overlap period with both formats, provide --format=legacy flag, announce deprecation cycle.

**File Matcher specific risks:**
- Multiple output branches (lines 1045-1340) with different patterns — risk breaking existing grep patterns like `grep '^\[MASTER\]'`
- Label proliferation: [MASTER], [DUP:?], [WOULD HARDLINK] etc. — any label change breaks parsing
- Summary vs detailed has different structure — unifying might accidentally change summary format
- Verbose mode changes line format — inconsistent JSON representation risk

**Mitigation strategy:** Implement --json with stable schema FIRST, then unify text output while maintaining labels and structure. Test with common parsing patterns before release.

## Implications for Roadmap

Based on research, recommended build order follows incremental refactoring with testability at each step.

### Phase 1: Formatter Abstraction (Foundation)
**Rationale:** Create abstraction layer without changing behavior — lowest risk, enables subsequent phases
**Delivers:** OutputFormatter Protocol, TextFormatter, JsonFormatter classes added to file_matcher.py (~150 lines)
**Addresses:** Architecture requirement for unified formatting
**Avoids:** Pitfall #3 (stdout/stderr mixing) by designing interface correctly from start
**Complexity:** Low — pure addition, no existing code changes
**Research needed:** None — standard patterns well-documented

### Phase 2: Extract Unified Output Logic (Refactor)
**Rationale:** Consolidate four output branches into single output_results() function — reduces duplication, maintains compatibility
**Delivers:** New output_results() function that uses formatter interface
**Uses:** TextFormatter (wraps existing format_* functions)
**Addresses:** Code maintainability, prepares for JSON implementation
**Avoids:** Pitfall #1 (breaking scripts) by preserving exact text output
**Complexity:** Medium — requires careful testing of all modes
**Research needed:** None — uses existing functionality

### Phase 3: CLI Integration for JSON (Feature)
**Rationale:** Expose JSON output through --json flag — delivers user-facing capability
**Delivers:** --json flag, documented JSON schema, null-separator support (-0 flag)
**Implements:** JsonFormatter connected to CLI
**Addresses:** Table stakes features (JSON output, safe scripting)
**Avoids:** Pitfall #2 (schema drift) by documenting schema upfront, Pitfall #4 (flag interactions) with tested combinations
**Complexity:** Low-Medium — formatter exists, just wire it up
**Research needed:** Phase-specific research on JSON schema design and validation patterns

### Phase 4: Enhancements (Polish)
**Rationale:** Add color support and rich metadata — improves UX without breaking compatibility
**Delivers:** TTY-aware color output, rich metadata in JSON (sizes, hashes)
**Addresses:** Differentiator features (color-coded output, rich metadata)
**Avoids:** Pitfall #8 (color in pipes) by detecting TTY, Pitfall #9 (inconsistent ordering) by explicit sorting
**Complexity:** Low — well-understood patterns
**Research needed:** None — NO_COLOR standard, TTY detection are standard

### Phase 5: Testing and Documentation (Quality)
**Rationale:** Verify no breakage, document stability guarantees — prevents support burden
**Delivers:** Comprehensive test suite for formatters, stability documentation, migration guide
**Addresses:** Quality assurance, user confidence
**Avoids:** Pitfall #1 (breaking scripts), #5 (no migration path), #6 (undocumented guarantees)
**Complexity:** Medium — requires thorough testing matrix
**Research needed:** None — testing patterns established

### Phase Ordering Rationale

1. **Foundation before features:** Create abstraction (Phase 1) before using it (Phase 2), avoiding big-bang refactor
2. **Compatibility preserved:** TextFormatter wraps existing functions (Phase 2) before adding JSON (Phase 3), ensuring text output unchanged
3. **Early value delivery:** JSON output available by Phase 3, enhancements in Phase 4 are optional polish
4. **Risk mitigation:** Each phase passes tests before proceeding, incremental approach prevents compounding errors
5. **Dependencies respected:** Formatter abstraction required for unified output, unified output required for JSON, base JSON required before enhancements

### Research Flags

**Phases with standard patterns (skip research-phase):**
- **Phase 1:** Protocol pattern well-documented in Python docs, no new research needed
- **Phase 2:** Refactoring existing code, internal change only
- **Phase 4:** TTY detection, color standards (NO_COLOR) are established patterns
- **Phase 5:** Standard testing approaches

**Phase needing focused research:**
- **Phase 3:** JSON schema design — specific to File Matcher's data model (duplicate groups, master/dup relationships, statistics). Recommend phase-specific research for:
  - JSON Schema validation syntax and tooling
  - Optimal structure for jq querying (flat vs nested)
  - Error representation in JSON output
  - Schema versioning approaches

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All solutions verified in official Python documentation, standard library only |
| Features | HIGH | Verified with official documentation from multiple established tools (fdupes, jdupes, git, AWS CLI) |
| Architecture | HIGH | Pattern validated against Cliff framework, OpenStack CLI tools, standard Python practices |
| Pitfalls | HIGH | Cross-referenced multiple authoritative sources (clig.dev, Kelly Brazil's CLI JSON guide, Git porcelain docs, Azure CLI BC policy) |

**Overall confidence:** HIGH

Research leveraged authoritative sources:
- Official Python 3.14.2 documentation (json, dataclasses, argparse modules)
- Man pages for established tools (fdupes, jdupes, rdfind, git-status)
- Industry-standard CLI guidelines (clig.dev, Rust CLI recommendations)
- Real-world implementation examples (AWS CLI, Azure CLI, Vagrant, Salesforce CLI)
- Expert practitioner guidance (Kelly Brazil's blog post based on jc project experience)

### Gaps to Address

**No critical gaps identified.** Research was comprehensive with high-quality sources. Minor considerations for implementation:

- **JSON Schema tooling:** During Phase 3, evaluate json-schema-validator for CI validation vs manual testing — quick proof-of-concept will determine best approach
- **jq query patterns:** Test common jq expressions during JSON structure design to ensure usability — straightforward validation step
- **Parsing pattern testing:** Create test suite with actual grep/awk/sed commands users might write — good practice, low risk

**Validation during implementation:**
- **Phase 2:** Manual testing of all modes (compare, action preview, action execute, summary, verbose) to verify text output unchanged
- **Phase 3:** Smoke test with real users' jq queries (if available in GitHub issues) to validate JSON structure
- **Phase 5:** Acceptance testing with common automation patterns

**No research blockers.** Ready to proceed with roadmap creation and implementation.

## Sources

### Primary (HIGH confidence)

**Python Standard Library Documentation:**
- [json — JSON encoder and decoder — Python 3.14.2](https://docs.python.org/3/library/json.html)
- [dataclasses — Data Classes](https://docs.python.org/3/library/dataclasses.html)
- [argparse — Parser for command-line options](https://docs.python.org/3/library/argparse.html)

**CLI Tool Official Documentation:**
- [fdupes man page](https://linux.die.net/man/1/fdupes)
- [jdupes Debian manpage](https://manpages.debian.org/testing/jdupes/jdupes.1.en.html)
- [git-status man page](https://linux.die.net/man/1/git-status) — --porcelain stable format
- [AWS CLI Output Format](https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-output-format.html)

**Industry Standards:**
- [Command Line Interface Guidelines (clig.dev)](https://clig.dev/) — Comprehensive CLI best practices
- [JSON Lines specification](https://jsonlines.org/) — Streaming JSON standard
- [Semantic Versioning 2.0.0](https://semver.org/)

### Secondary (MEDIUM confidence)

**Expert Practitioner Guides:**
- [Tips on Adding JSON Output to Your CLI App — Kelly Brazil](https://blog.kellybrazil.com/2021/12/03/tips-on-adding-json-output-to-your-cli-app/) — Based on jc project experience
- [Things I've learned about building CLI tools in Python — Simon Willison](https://simonwillison.net/2023/Sep/30/cli-tools-python/)
- [Python print() Output: Practical Patterns (2026) — TheLinuxCode](https://thelinuxcode.com/python-print-output-practical-patterns-pitfalls-and-modern-workflows-2026/)

**Architecture Patterns:**
- [Cliff Framework Documentation](https://docs.openstack.org/cliff/latest/) — Industry-standard formatter patterns
- [Rust CLI Recommendations - Machine-readable output](https://rust-cli-recommendations.sunshowers.io/machine-readable-output/)

**Community Standards:**
- [CLI Best Practices — HackMD Community](https://hackmd.io/@arturtamborski/cli-best-practices)
- [ANSI Color Standards](http://bixense.com/clicolors/) — NO_COLOR, CLICOLOR conventions
- [Choosing Readable ANSI Colors](https://trentm.com/2024/09/choosing-readable-ansi-colors-for-clis.html)

**Breaking Change Management:**
- [Azure CLI Breaking Change Pre-Announcement](https://techcommunity.microsoft.com/blog/azuretoolsblog/azure-cli-breaking-change-pre-announcement/4403454)
- [Arduino CLI Backward compatibility policy](https://arduino.github.io/arduino-cli/0.35/versioning/)

### Tertiary (for context)

**Design Patterns:**
- [Python Design Patterns - Command](https://www.tutorialspoint.com/python_design_patterns/python_design_patterns_command.htm)
- [Hexagonal Architecture Design (2026)](https://johal.in/hexagonal-architecture-design-python-ports-and-adapters-for-modularity-2026/)

---
*Research completed: 2026-01-22*
*Ready for roadmap: YES*
