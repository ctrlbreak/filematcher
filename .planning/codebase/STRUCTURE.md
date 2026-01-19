# Codebase Structure

**Analysis Date:** 2026-01-19

## Directory Layout

```
filematcher/
├── file_matcher.py      # Main implementation (single module)
├── run_tests.py         # Test runner script
├── pyproject.toml       # Package configuration
├── requirements.txt     # Dependencies (minimal)
├── CLAUDE.md            # Development instructions
├── README.md            # User documentation
├── LICENSE              # MIT license
├── CHANGELOG.md         # Version history
├── create_release.py    # Release automation script
├── tests/               # Test suite
│   ├── __init__.py      # Path setup for imports
│   ├── test_base.py     # Base test class with fixtures
│   ├── test_cli.py      # CLI tests
│   ├── test_directory_operations.py  # Directory scanning tests
│   ├── test_fast_mode.py            # Sparse hashing tests
│   ├── test_file_hashing.py         # Hash function tests
│   └── test_real_directories.py     # Integration tests
├── test_dir1/           # Simple test fixtures
│   ├── subdir/
│   └── *.txt
├── test_dir2/           # Simple test fixtures
│   ├── subdir/
│   └── *.txt
├── complex_test/        # Complex test fixtures
│   ├── dir1/
│   │   ├── subdir1/
│   │   └── subdir2/
│   └── dir2/
│       ├── subdir1/
│       └── subdir2/
└── .planning/           # GSD planning documents
    └── codebase/
```

## Directory Purposes

**Root Directory:**
- Purpose: Project root with main implementation
- Contains: Single-file implementation, configuration, documentation
- Key files: `file_matcher.py`, `pyproject.toml`, `run_tests.py`

**tests/:**
- Purpose: Unit and integration tests
- Contains: Test modules organized by functionality
- Key files: `test_base.py` (shared fixtures), `test_*.py` (test modules)

**test_dir1/, test_dir2/:**
- Purpose: Simple test fixtures for basic matching scenarios
- Contains: Text files with controlled content for testing
- Key files: Files with identical content but different names

**complex_test/:**
- Purpose: Complex test fixtures for edge cases
- Contains: Nested directories with asymmetric matches, multiple copies
- Key files: Files testing many-to-many matching patterns

## Key File Locations

**Entry Points:**
- `file_matcher.py`: Main module and CLI entry point
- `run_tests.py`: Test execution entry point

**Configuration:**
- `pyproject.toml`: Package metadata, entry point, Python version requirements
- `requirements.txt`: Runtime dependencies (currently empty/minimal)

**Core Logic:**
- `file_matcher.py`: All implementation code (functions listed below)
  - `format_file_size()` - lines 24-46
  - `get_file_hash()` - lines 49-82
  - `get_sparse_hash()` - lines 85-146
  - `index_directory()` - lines 149-189
  - `find_matching_files()` - lines 192-245
  - `main()` - lines 248-338

**Testing:**
- `tests/test_base.py`: `BaseFileMatcherTest` class with setUp/tearDown
- `tests/test_*.py`: Individual test modules

## Naming Conventions

**Files:**
- Python modules: `snake_case.py` (e.g., `file_matcher.py`, `test_base.py`)
- Test modules: `test_*.py` pattern (e.g., `test_cli.py`)
- Config files: Standard names (e.g., `pyproject.toml`, `requirements.txt`)

**Directories:**
- Test directories: `snake_case` (e.g., `test_dir1`, `complex_test`)
- Package directories: `snake_case` (e.g., `tests`)

**Functions:**
- All functions: `snake_case` (e.g., `get_file_hash`, `find_matching_files`)
- Private functions: Not used; all functions are module-level public

**Variables:**
- Local variables: `snake_case` (e.g., `file_hash`, `hash_to_files`)
- Constants: None explicitly defined; inline values used

**Classes:**
- Test classes: `PascalCase` (e.g., `BaseFileMatcherTest`, `TestCLI`)

## Where to Add New Code

**New Feature (core functionality):**
- Primary code: Add function to `file_matcher.py`
- Tests: Add test class/methods to appropriate `tests/test_*.py`

**New CLI Option:**
- Implementation: Add to `argparse` setup in `main()` function in `file_matcher.py`
- Tests: Add tests to `tests/test_cli.py`

**New Hash Algorithm:**
- Implementation: Extend `get_file_hash()` and `get_sparse_hash()` in `file_matcher.py`
- Tests: Add tests to `tests/test_file_hashing.py`

**New Test Fixtures:**
- Simple cases: Add files to `test_dir1/` and `test_dir2/`
- Complex cases: Add to `complex_test/dir1/` and `complex_test/dir2/`

**Utilities:**
- Shared helpers: Add to `file_matcher.py` (keep single-file design)
- Test utilities: Add to `tests/test_base.py`

## Special Directories

**tests/:**
- Purpose: Test suite with shared base class
- Generated: No
- Committed: Yes

**test_dir1/, test_dir2/, complex_test/:**
- Purpose: Static test fixtures
- Generated: No
- Committed: Yes

**.mypy_cache/:**
- Purpose: mypy type checking cache
- Generated: Yes
- Committed: No (in .gitignore)

**.planning/:**
- Purpose: GSD planning and codebase analysis documents
- Generated: Yes (by GSD commands)
- Committed: Optional

---

*Structure analysis: 2026-01-19*
