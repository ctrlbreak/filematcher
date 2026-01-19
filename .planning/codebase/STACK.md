# Technology Stack

**Analysis Date:** 2026-01-19

## Languages

**Primary:**
- Python 3.9+ - Core application and all supporting scripts

**Secondary:**
- None

## Runtime

**Environment:**
- Python 3.9 or higher (supports 3.9, 3.10, 3.11, 3.12, 3.13)
- Uses `from __future__ import annotations` for forward reference type hints

**Package Manager:**
- pip / setuptools
- No lockfile (no external dependencies)

## Frameworks

**Core:**
- None - Pure Python standard library implementation

**Testing:**
- unittest (standard library) - Test framework
- unittest.mock - Mocking for CLI tests

**Build/Dev:**
- setuptools >= 61.0 - Build backend for packaging

## Key Dependencies

**Critical:**
- None - Zero external dependencies

**Standard Library Modules Used:**
- `argparse` - CLI argument parsing (`file_matcher.py`)
- `hashlib` - MD5/SHA-256 file hashing (`file_matcher.py`)
- `logging` - Status output and debug logging (`file_matcher.py`)
- `os` - File system operations (`file_matcher.py`)
- `sys` - Exit codes and path manipulation (`file_matcher.py`)
- `pathlib.Path` - Path handling (`file_matcher.py`)
- `collections.defaultdict` - Hash-to-files mapping (`file_matcher.py`)

**Test-Only Standard Library:**
- `unittest` - Test framework (`run_tests.py`, `tests/*.py`)
- `unittest.mock.patch` - CLI argument mocking (`tests/test_cli.py`)
- `tempfile` - Temporary test directories (`tests/test_base.py`)
- `shutil` - Test directory cleanup (`tests/test_base.py`)
- `random` - Test data generation (`tests/test_base.py`)
- `contextlib.redirect_stdout` - CLI output capture (`tests/test_cli.py`)
- `io` - String buffer for output capture (`tests/test_cli.py`)

**Release Script Only:**
- `zipfile` - ZIP archive creation (`create_release.py`)
- `tarfile` - TAR.GZ archive creation (`create_release.py`)
- `datetime` - Release date stamping (`create_release.py`)

## Configuration

**Environment:**
- No environment variables required
- No configuration files needed
- All options passed via CLI arguments

**Build:**
- `pyproject.toml` - Package metadata and build configuration
- Entry point: `filematcher = "file_matcher:main"`

**Test:**
- `pyproject.toml` contains `[tool.pytest.ini_options]` with `testpaths = ["tests"]`
- Tests use unittest (not pytest) despite pytest config

## Platform Requirements

**Development:**
- Python 3.9+
- No additional setup required
- Install editable: `pip install -e .`

**Production:**
- Standalone script - no installation required
- Can be run directly: `python3 file_matcher.py <dir1> <dir2>`
- Or installed via pip: `pip install .` then use `filematcher` command

## Package Distribution

**Entry Point:**
- CLI command: `filematcher`
- Maps to: `file_matcher:main` function

**Installation Methods:**
1. Direct execution: `python3 file_matcher.py`
2. Editable install: `pip install -e .`
3. Standard install: `pip install .`

**Release Artifacts:**
- `filematcher-X.X.X.zip` - ZIP archive for GitHub releases
- `filematcher-X.X.X.tar.gz` - TAR archive for GitHub releases
- Created via `create_release.py` script

---

*Stack analysis: 2026-01-19*
