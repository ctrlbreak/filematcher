# Requirements: File Matcher v1.4

**Defined:** 2026-01-27
**Core Value:** Safely deduplicate files across directories while preserving the master copy and logging all changes.

## v1.4 Requirements

Requirements for package structure refactoring. Each maps to roadmap phases.

### Package Structure

- [ ] **PKG-01**: Create `filematcher/` package directory with `__init__.py`
- [ ] **PKG-02**: Add `__main__.py` enabling `python -m filematcher` invocation
- [ ] **PKG-03**: Update pyproject.toml entry point to `filematcher.cli:main`
- [ ] **PKG-04**: Each module is under 500 lines (improved maintainability)
- [ ] **PKG-05**: No circular imports between modules

### Module Organization

- [ ] **MOD-01**: Extract color system to `filematcher/colors.py`
- [ ] **MOD-02**: Extract hashing functions to `filematcher/hashing.py`
- [ ] **MOD-03**: Extract filesystem helpers to `filematcher/filesystem.py`
- [ ] **MOD-04**: Extract action execution to `filematcher/actions.py`
- [ ] **MOD-05**: Extract output formatters to `filematcher/formatters.py`
- [ ] **MOD-06**: Extract directory operations to `filematcher/directory.py`
- [ ] **MOD-07**: Extract audit logging to `filematcher/logging.py`
- [ ] **MOD-08**: Extract CLI and main to `filematcher/cli.py`

### Backward Compatibility

- [ ] **COMPAT-01**: `python file_matcher.py <args>` continues to work
- [ ] **COMPAT-02**: `filematcher <args>` command via pip install works
- [ ] **COMPAT-03**: All public symbols importable from `filematcher` package
- [ ] **COMPAT-04**: `file_matcher.py` serves as thin wrapper importing from package

### Test Migration

- [ ] **TEST-01**: All 217 tests pass after refactoring
- [ ] **TEST-02**: Test imports updated to `from filematcher import X` pattern
- [ ] **TEST-03**: No major test file rewrites required (import changes only)

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
| PKG-01 | TBD | Pending |
| PKG-02 | TBD | Pending |
| PKG-03 | TBD | Pending |
| PKG-04 | TBD | Pending |
| PKG-05 | TBD | Pending |
| MOD-01 | TBD | Pending |
| MOD-02 | TBD | Pending |
| MOD-03 | TBD | Pending |
| MOD-04 | TBD | Pending |
| MOD-05 | TBD | Pending |
| MOD-06 | TBD | Pending |
| MOD-07 | TBD | Pending |
| MOD-08 | TBD | Pending |
| COMPAT-01 | TBD | Pending |
| COMPAT-02 | TBD | Pending |
| COMPAT-03 | TBD | Pending |
| COMPAT-04 | TBD | Pending |
| TEST-01 | TBD | Pending |
| TEST-02 | TBD | Pending |
| TEST-03 | TBD | Pending |

**Coverage:**
- v1.4 requirements: 20 total
- Mapped to phases: 0
- Unmapped: 20 (pending roadmap)

---
*Requirements defined: 2026-01-27*
*Last updated: 2026-01-27 after initial definition*
