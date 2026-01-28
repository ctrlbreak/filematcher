# Requirements: File Matcher v1.4

**Defined:** 2026-01-27
**Core Value:** Safely deduplicate files across directories while preserving the master copy and logging all changes.

## v1.4 Requirements

Requirements for package structure refactoring. Each maps to roadmap phases.

### Package Structure

- [x] **PKG-01**: Create `filematcher/` package directory with `__init__.py`
- [x] **PKG-02**: Add `__main__.py` enabling `python -m filematcher` invocation
- [x] **PKG-03**: Update pyproject.toml entry point to `filematcher.cli:main`
- [x] **PKG-04**: No circular imports between modules

### Module Organization

- [x] **MOD-01**: Extract color system to `filematcher/colors.py`
- [x] **MOD-02**: Extract hashing functions to `filematcher/hashing.py`
- [x] **MOD-03**: Extract filesystem helpers to `filematcher/filesystem.py`
- [x] **MOD-04**: Extract action execution to `filematcher/actions.py`
- [x] **MOD-05**: Extract output formatters to `filematcher/formatters.py`
- [x] **MOD-06**: Extract directory operations to `filematcher/directory.py`
- [x] **MOD-07**: Extract audit logging to `filematcher/actions.py` (combined with action execution)
- [x] **MOD-08**: Extract CLI and main to `filematcher/cli.py`

### Backward Compatibility

- [x] **COMPAT-01**: `python file_matcher.py <args>` continues to work
- [x] **COMPAT-02**: `filematcher <args>` command via pip install works
- [x] **COMPAT-03**: All public symbols importable from `filematcher` package
- [x] **COMPAT-04**: `file_matcher.py` serves as thin wrapper importing from package

### Test Migration

- [x] **TEST-01**: All 218 tests pass after refactoring (217 original + 1 circular import test)
- [x] **TEST-02**: Test imports updated to `from filematcher import X` pattern
- [x] **TEST-03**: No major test file rewrites required (import changes only)

## Future Requirements

Deferred to future milestones. Tracked but not in current roadmap.

### Documentation

- **DOC-01**: Update CLAUDE.md with new package structure
- **DOC-02**: Add architecture diagram showing module dependencies

### Optional Enhancements

- **ENH-01**: Deprecation warnings for direct `file_matcher` imports
- **ENH-02**: Type stubs (`.pyi` files) for better IDE support

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| src/ layout | Flat layout better suits existing test infrastructure |
| Namespace packages | Overkill for single-package project |
| Separate distribution packages | Single package is simpler, no benefit from splitting |
| Breaking backward compat | Core constraint of this milestone |
| External dependencies | Maintains pure stdlib requirement |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| PKG-01 | Phase 11 | Complete |
| PKG-02 | Phase 11 | Complete |
| PKG-03 | Phase 15 | Complete |
| PKG-04 | Phase 17 | Complete |
| MOD-01 | Phase 12 | Complete |
| MOD-02 | Phase 12 | Complete |
| MOD-03 | Phase 13 | Complete |
| MOD-04 | Phase 13 | Complete |
| MOD-05 | Phase 14 | Complete |
| MOD-06 | Phase 14 | Complete |
| MOD-07 | Phase 13 | Complete |
| MOD-08 | Phase 15 | Complete |
| COMPAT-01 | Phase 16 | Complete |
| COMPAT-02 | Phase 16 | Complete |
| COMPAT-03 | Phase 16 | Complete |
| COMPAT-04 | Phase 16 | Complete |
| TEST-01 | Phase 17 | Complete |
| TEST-02 | Phase 17 | Complete |
| TEST-03 | Phase 17 | Complete |

**Coverage:**
- v1.4 requirements: 19 total
- Mapped to phases: 19
- Unmapped: 0

---
*Requirements defined: 2026-01-27*
*Last updated: 2026-01-28 - All v1.4 requirements complete*
