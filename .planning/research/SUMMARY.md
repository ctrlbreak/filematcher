# Project Research Summary

**Project:** File Matcher v1.4 - Package Refactoring
**Domain:** Python CLI package structure migration
**Researched:** 2026-01-27
**Confidence:** HIGH

## Executive Summary

File Matcher is a 2,843-line single-file CLI tool with 217 tests that needs refactoring to a package structure for better code navigation and AI tooling compatibility. The research reveals this is a well-documented migration pattern with clear best practices: use flat layout (not src layout), maintain backward compatibility through re-exports, and extract modules incrementally while keeping all tests passing.

The recommended approach is the **Facade Pattern with Re-export** - keep `file_matcher.py` as a thin compatibility shim that re-exports from the new `filematcher/` package structure. This ensures zero breaking changes: existing imports continue working, the CLI remains functional, and all 217 tests pass without modification. The existing code already has clean section boundaries (marked with `# ===` comments) that map directly to proposed modules, making this primarily a code-movement exercise rather than a logic restructure.

Critical risks are well-understood and preventable: circular imports (mitigate through careful module hierarchy), entry point misconfiguration (update pyproject.toml immediately), and test discovery failure (verify 217 tests pass after each phase). The zero-dependency stdlib constraint remains, with no new external packages needed. This is a low-risk refactoring if executed incrementally with continuous test verification.

## Key Findings

### Recommended Stack

**Use flat layout with pyproject.toml entry points. Do NOT use src layout.**

**Core technologies:**
- **Flat package layout** — Simpler migration path, maintains existing test infrastructure without rewrites
- **pyproject.toml** — Already in use, update `packages = ["filematcher"]` for package discovery
- **Relative imports within package** — Self-contained package, easier to rename/move later
- **Re-export pattern in `__init__.py`** — Maintains backward compatibility for all existing imports

**Why flat over src layout:**
1. Existing tests use `sys.path` manipulation that works with flat layout
2. `python file_matcher.py` backward compatibility trivial with flat layout
3. Pure Python stdlib project doesn't need src layout's import isolation
4. Lower migration complexity - move code to `filematcher/` without touching test infrastructure

**Entry points:**
- `filematcher` console script → `filematcher.cli:main`
- `python -m filematcher` → new `__main__.py` module
- `python file_matcher.py` → thin wrapper (maintained for backward compat)

**Module structure (8 modules + utils):**
- `cli.py` (~300 lines) - main(), argparse, CLI orchestration
- `core.py` (~400 lines) - find_matching_files(), index_directory(), select_master_file()
- `hashing.py` (~150 lines) - get_file_hash(), get_sparse_hash()
- `actions.py` (~300 lines) - execute_action(), safe_replace_with_link()
- `output.py` (~400 lines) - ActionFormatter, TextActionFormatter, JsonActionFormatter
- `color.py` (~150 lines) - ColorMode, ColorConfig, color helpers
- `logging.py` (~150 lines) - Audit logging functions
- `filesystem.py` (~200 lines) - is_hardlink_to(), check_cross_filesystem()
- `__init__.py` (~30 lines) - Public API exports, __version__
- `__main__.py` (~10 lines) - python -m support

### Module Organization

**The existing section structure already defines clean module boundaries.** Current `file_matcher.py` uses `# ===` comment sections that map directly to proposed modules with minimal coupling.

**Recommended structure:**
```
filematcher/
    __init__.py          # Package metadata, public API re-exports
    __main__.py          # Entry point: python -m filematcher
    cli.py               # Argument parsing, main() orchestration
    core.py              # Core matching logic, directory indexing
    hashing.py           # Hash computation (MD5/SHA-256, sparse sampling)
    actions.py           # Action execution (hardlink/symlink/delete)
    output.py            # Formatters (text/JSON), output strategies
    color.py             # Color configuration, ANSI helpers
    logging.py           # Audit logging
    filesystem.py        # Filesystem operations (hardlink detection, etc.)
    utils.py             # format_file_size(), small helpers
    types.py             # GroupLine, SpaceInfo dataclasses
```

**Dependency flow (acyclic):**
```
cli.py
  → core.py → hashing.py → utils.py
  → actions.py → filesystem.py
  → output.py → color.py → types.py
  → logging.py → utils.py
```

**Why this structure:**
- Mirrors existing `# ===` section comments
- Single responsibility per module
- Test modules already organized by function (test_file_hashing.py → hashing.py)
- Minimal coupling - dependencies flow downward
- Familiar pattern from Click/Typer CLI tools

**Alternative considered (minimal structure):**
Could reduce to 6 larger files (cli, core, actions, output, logging, utils) with 500-600 lines each. Acceptable if team prefers fewer files. **Reject deep nesting** - no more than 2 levels of subpackages.

### Migration Strategy

**Use the Facade Pattern with Re-export approach** to maintain full backward compatibility during migration.

**Phase structure:**
1. **Create empty package** - Verify filematcher/__init__.py imports work
2. **Extract by dependency order** - Start with leaf modules (no internal deps), work up to CLI
3. **Keep file_matcher.py as shim** - Re-exports all public symbols from filematcher package
4. **Zero test changes** - Tests import from file_matcher, which re-exports from filematcher
5. **Verify after each phase** - All 217 tests pass, CLI works, imports unchanged

**Incremental extraction order:**
1. **Phase 1** - Create package structure (no code movement yet)
2. **Phase 2** - Extract color module (minimal dependencies)
3. **Phase 3** - Extract hashing module
4. **Phase 4** - Extract filesystem module
5. **Phase 5** - Extract actions module
6. **Phase 6** - Extract formatters
7. **Phase 7** - Extract formatting functions
8. **Phase 8** - Extract comparison logic
9. **Phase 9** - Extract utils and logging
10. **Phase 10** - Create CLI module, finalize entry points
11. **Phase 11** - Clean up, verify all entry points

**Compatibility shim pattern:**
```python
# file_matcher.py (after migration)
"""Backward compatibility wrapper."""
from filematcher import (
    main, get_file_hash, get_sparse_hash, find_matching_files,
    # ... all 27 public symbols
)

if __name__ == "__main__":
    import sys
    sys.exit(main())
```

**Entry point changes:**
- Current: `filematcher = "file_matcher:main"`
- Final: `filematcher = "filematcher.cli:main"`
- During migration: Keep pointing to file_matcher until Phase 10

**Test strategy:**
- **Zero test modifications during migration** - Compatibility shim maintains all imports
- Verify test count stays 217 after each phase
- Optional: Update test imports to `from filematcher import X` after migration complete (Phase 12+)

**Rollback strategy:**
- Each phase is single commit
- Per-phase rollback: git revert, delete new module, restore inline code
- Emergency full rollback: checkout pre-migration commit, rm -rf filematcher/

### Critical Pitfalls

1. **Breaking the Public API Import Contract**
   - **Risk:** Users who `from file_matcher import get_file_hash` get ImportError after restructure
   - **Prevention:** Re-export all 27 public symbols in filematcher/__init__.py with explicit __all__
   - **Phase:** Must address in Phase 1 (initial restructure)
   - **Test:** Add test that verifies old import paths still work

2. **Entry Point Path Mismatch**
   - **Risk:** `filematcher` console command stops working because pyproject.toml points to wrong location
   - **Prevention:** Update entry point to `filematcher.cli:main` immediately in Phase 10, test with `pip install -e . && filematcher --help`
   - **Phase:** Phase 10 (CLI module creation)
   - **Symptom:** ModuleNotFoundError when running filematcher command

3. **Circular Import Deadlock**
   - **Risk:** Splitting into modules creates import loops causing ImportError at runtime
   - **Prevention:** Design module hierarchy first with clear dependency flow (constants → config → core → CLI), extract shared dependencies upward, use TYPE_CHECKING for type-only imports
   - **Phase:** Design in Phase 1, verify throughout
   - **Test:** Add test that imports package from fresh Python subprocess

4. **Test Discovery Failure**
   - **Risk:** unittest stops discovering tests after restructure, silently runs 0 tests or subset
   - **Prevention:** Keep __init__.py in all test directories, update test imports to filematcher (or keep file_matcher via shim), remove sys.path hacks after package is pip-installable, verify 217 tests discovered
   - **Phase:** Verify immediately after Phase 1, recheck after every phase
   - **Test:** `python -m pytest --collect-only` must show 217 tests

5. **Editable Install Breakage**
   - **Risk:** `pip install -e .` stops working due to PEP 660 changes or incorrect pyproject.toml
   - **Prevention:** Ensure pyproject.toml has `[build-system] requires = ["setuptools >= 64"]`, test in fresh venv, clean old artifacts before testing
   - **Phase:** Verify in Phase 1, retest after structural changes
   - **Test:** Fresh venv, `pip install -e .`, `python -c "from filematcher import main"`

**Medium-risk pitfalls:**
- Relative import confusion (choose absolute imports, enforce consistently)
- Logger configuration collision (centralize in one place, use package name for all loggers)
- Version string inconsistency (use importlib.metadata for single source of truth)
- Constants scattered across modules (create constants.py for magic values)

**Verification checklist:**
- [ ] `pip install -e .` succeeds
- [ ] `filematcher --help` works
- [ ] `python -c "from filematcher import main, get_file_hash"` succeeds
- [ ] `python -m pytest` discovers 217 tests
- [ ] No circular import errors on fresh Python
- [ ] Output matches pre-migration behavior

## Implications for Roadmap

Based on research, suggest 11-phase incremental migration with continuous test verification.

### Phase 1: Create Package Structure
**Rationale:** Establish foundation without moving code - lowest risk entry point
**Delivers:** Empty filematcher/ package with __init__.py that imports from file_matcher.py
**Verification:** `from filematcher import main` works, all 217 tests pass unchanged
**Avoids:** Breaking changes (Pitfall #1) - re-exports work before any code moves
**Research needed:** No - standard pattern, well-documented

### Phase 2: Extract Color Module
**Rationale:** Color has zero internal dependencies, perfect first extraction to validate approach
**Delivers:** filematcher/color.py with ColorMode, ColorConfig, ANSI helpers
**Addresses:** Reduce coupling, test re-export pattern
**Avoids:** Circular imports (Pitfall #3) - leaf module with no internal dependencies
**Research needed:** No - straightforward extraction

### Phase 3: Extract Hashing Module
**Rationale:** Clear boundaries, used by multiple modules, tests already organized (test_file_hashing.py)
**Delivers:** filematcher/hashing.py with get_file_hash(), get_sparse_hash(), index_directory()
**Dependencies:** utils.py (format_file_size) - extract utils first or pass as parameter
**Research needed:** No - pure functions with minimal coupling

### Phase 4: Extract Filesystem Module
**Rationale:** Self-contained filesystem operations, no upward dependencies
**Delivers:** filematcher/filesystem.py with is_hardlink_to(), check_cross_filesystem()
**Tests:** test_directory_operations.py validates this module
**Research needed:** No - OS abstraction already working

### Phase 5: Extract Actions Module
**Rationale:** Depends on filesystem module (Phase 4), enables testing action execution separately
**Delivers:** filematcher/actions.py with execute_action(), safe_replace_with_link()
**Dependencies:** filesystem.py (Phase 4), logging.py (extract in Phase 9 or couple temporarily)
**Tests:** test_actions.py validates this module
**Research needed:** No - established action execution patterns

### Phase 6: Extract Formatters
**Rationale:** Large section (~400 lines), depends on color module (Phase 2)
**Delivers:** filematcher/output.py with ActionFormatter ABC, TextActionFormatter, JsonActionFormatter
**Dependencies:** color.py (Phase 2), types.py (GroupLine, SpaceInfo)
**Tests:** test_json_output.py, test_color_output.py validate
**Research needed:** No - strategy pattern already implemented

### Phase 7: Extract Formatting Functions
**Rationale:** Support functions for formatters, extract after Phase 6
**Delivers:** filematcher/formatting.py with format_duplicate_group(), format_statistics_footer()
**Dependencies:** color.py, types.py
**Tests:** test_output_unification.py validates
**Research needed:** No

### Phase 8: Extract Comparison Logic
**Rationale:** Core functionality, depends on hashing (Phase 3)
**Delivers:** filematcher/comparison.py with find_matching_files()
**Dependencies:** hashing.py (index_directory)
**Tests:** test_real_directories.py validates
**Research needed:** No

### Phase 9: Extract Utils and Logging
**Rationale:** Utilities used by multiple modules, extract late to avoid circular deps
**Delivers:** filematcher/utils.py (format_file_size), filematcher/logging.py (audit)
**Dependencies:** None (leaf modules)
**Tests:** test_actions.py validates logging
**Research needed:** No

### Phase 10: Create CLI Module and Finalize Entry Points
**Rationale:** Last step - CLI orchestrates all other modules
**Delivers:** filematcher/cli.py with main(), __main__.py for python -m support
**Updates:** pyproject.toml entry point to `filematcher.cli:main`, file_matcher.py becomes pure shim
**Avoids:** Entry point breakage (Pitfall #2) - test both console script and direct invocation
**Tests:** test_cli.py, test_safe_defaults.py, test_master_directory.py validate
**Research needed:** No - standard CLI patterns

### Phase 11: Clean Up and Verify
**Rationale:** Final verification, documentation updates
**Delivers:** __all__ in all modules, updated CLAUDE.md, verified entry points
**Verification:** Full test suite (217 tests), manual smoke tests, documentation accuracy
**Research needed:** No

### Phase Ordering Rationale

**Why this order:**
1. **Dependency-driven** - Extract leaf modules first (color, hashing), work up to CLI
2. **Risk-minimizing** - Each phase is independently revertible with clear rollback
3. **Test-preserving** - Compatibility shim means zero test changes during migration
4. **Incremental validation** - Run all 217 tests after each phase to catch issues early
5. **Architecture-aligned** - Follows existing section structure, minimal logic changes

**Why incremental over big-bang:**
- 11 small commits vs 1 massive commit
- Each phase takes 30-60 minutes, can pause/resume
- Clear verification point after each phase
- Easy rollback if issues discovered

**Why this grouping:**
- Color → Hashing → Filesystem → Actions follows dependency chain
- Formatters grouped together (output, formatting) as cohesive subsystem
- Utils and logging extracted late to avoid becoming circular dependency hubs
- CLI last because it depends on everything else

### Research Flags

**All phases use standard patterns - no additional research needed.**

The migration is code movement, not feature development. All patterns are well-documented:
- Flat layout package structure (official Python packaging docs)
- Re-export pattern for backward compat (established pattern)
- Incremental module extraction (standard refactoring technique)
- Entry point configuration (setuptools documentation)

**If unexpected issues arise during planning:**
- **Circular import problems:** Review DataCamp/Brex resources on circular import resolution
- **Test discovery issues:** Consult pytest/unittest test collection docs
- **Entry point failures:** Reference setuptools entry point troubleshooting

No phase requires `/gsd:research-phase` - proceed directly to requirements definition.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Official Python packaging docs, established flat layout pattern |
| Module Organization | HIGH | Existing code structure maps cleanly to proposed modules |
| Migration Strategy | HIGH | Facade pattern is proven, multiple sources validate approach |
| Pitfalls | HIGH | All major pitfalls documented with prevention strategies |

**Overall confidence:** HIGH

### Gaps to Address

**No significant gaps identified.** Research covered:
- Package layout decision (flat vs src) - decided based on project constraints
- Module organization - based on existing section structure
- Migration approach - Facade pattern with re-exports
- Entry point configuration - pyproject.toml updates specified
- Backward compatibility - compatibility shim pattern defined
- Test preservation - zero-modification strategy
- Rollback strategy - per-phase and emergency rollback documented

**Minor points to clarify during planning:**
- Exact line counts per module (estimated in research, verify during extraction)
- Whether to create types.py or keep dataclasses inline (minor decision)
- Logger configuration centralization details (straightforward implementation choice)

**These are implementation details, not research gaps.** Proceed to requirements definition.

## Sources

### Primary (HIGH confidence)
- [Python Packaging User Guide: src vs flat layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/) - Layout decision
- [Python Packaging User Guide: Writing pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) - Configuration
- [Python Packaging User Guide: Creating CLI Tools](https://packaging.python.org/en/latest/guides/creating-command-line-tools/) - Entry points
- [Setuptools: Package Discovery](https://setuptools.pypa.io/en/latest/userguide/package_discovery.html) - Package structure
- [Setuptools: Entry Points](https://setuptools.pypa.io/en/latest/userguide/entry_point.html) - Console scripts
- [Python docs: __main__ module](https://docs.python.org/3/library/__main__.html) - python -m support
- [PEP 387: Backwards Compatibility Policy](https://peps.python.org/pep-0387/) - Compatibility standards

### Secondary (MEDIUM confidence)
- [Real Python: Absolute vs Relative Imports](https://realpython.com/absolute-vs-relative-python-imports/) - Import strategy
- [Real Python: Python __init__.py](https://realpython.com/python-init-py/) - Package initialization
- [PyOpenSci: Python Package Structure](https://www.pyopensci.org/python-package-guide/package-structure-code/python-package-structure.html) - Best practices
- [Hitchhiker's Guide: Structuring Your Project](https://docs.python-guide.org/writing/structure/) - Organization patterns
- [DataCamp: Python Circular Import](https://www.datacamp.com/tutorial/python-circular-import) - Circular import resolution
- [Brex Engineering: Avoiding Circular Imports](https://medium.com/brexeng/avoiding-circular-imports-in-python-7c35ec8145ed) - Enterprise patterns
- [clig.dev: CLI Guidelines](https://clig.dev/) - CLI design principles

### Tertiary (Context validation)
- Existing file_matcher.py codebase - Section structure analysis
- Test suite organization - Module mapping validation
- pyproject.toml current config - Entry point baseline

---
*Research completed: 2026-01-27*
*Ready for roadmap: YES*
