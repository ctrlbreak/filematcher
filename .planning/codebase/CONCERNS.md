# Codebase Concerns

**Analysis Date:** 2026-01-19

## Tech Debt

**Duplicated Hash Algorithm Validation:**
- Issue: Hash algorithm validation logic (`if hash_algorithm == 'md5' ... elif hash_algorithm == 'sha256' ... else: raise ValueError`) is duplicated in both `get_file_hash()` and `get_sparse_hash()`
- Files: `file_matcher.py` (lines 66-71, 99-104)
- Impact: Maintenance burden; adding a new hash algorithm requires changes in multiple locations
- Fix approach: Extract hash algorithm validation and hasher creation into a helper function

**Monkeypatching in Tests:**
- Issue: Test code manipulates function default parameters directly (`file_matcher.get_file_hash.__defaults__`) to change size threshold for testing
- Files: `tests/test_fast_mode.py` (lines 117-118, 134-135)
- Impact: Fragile test that depends on internal function implementation; could break with refactoring
- Fix approach: Make size threshold configurable via environment variable or pass through function chain

**Test Real Directories Coupling:**
- Issue: `test_real_directories.py` depends on committed test fixtures (`test_dir1/`, `test_dir2/`, `complex_test/`) existing in the repo
- Files: `tests/test_real_directories.py` (lines 13-19, 112-117)
- Impact: Tests skip silently if fixtures missing; coupling to repo structure
- Fix approach: Generate fixtures in setUp or use pytest fixtures with clear failure messages

## Known Bugs

**None detected.** All 18 tests pass. No TODO/FIXME comments in source code.

## Security Considerations

**MD5 as Default Hash Algorithm:**
- Risk: MD5 is cryptographically broken and susceptible to collision attacks. While not a security issue for file comparison (content matching, not integrity verification), it could cause false positives if comparing files from untrusted sources
- Files: `file_matcher.py` (line 255, default in function signatures)
- Current mitigation: SHA-256 option available via `--hash sha256`
- Recommendations: Consider changing default to SHA-256, or document MD5 collision risk in README

**No Path Sanitization:**
- Risk: Directory paths from CLI are used directly without sanitization
- Files: `file_matcher.py` (lines 273, 286)
- Current mitigation: Only reads files; `os.path.isdir()` check prevents non-directory inputs
- Recommendations: Low risk for current use case; no action needed unless accepting untrusted input

## Performance Bottlenecks

**Double Directory Traversal in Verbose Mode:**
- Problem: In verbose mode, `index_directory()` traverses the directory twice - once to count files, once to process them
- Files: `file_matcher.py` (lines 164-167)
- Cause: `sum(1 for filepath in directory_path.rglob('*') if filepath.is_file())` iterates all files just for count
- Improvement path: Collect file list once, then iterate; or remove total count and show only current progress

**No Parallel Processing:**
- Problem: File hashing is single-threaded, which is CPU-bound
- Files: `file_matcher.py` (lines 169-184)
- Cause: Sequential iteration with `for filepath in directory_path.rglob('*')`
- Improvement path: Use `concurrent.futures.ThreadPoolExecutor` or `ProcessPoolExecutor` for parallel hashing

**Fast Mode Threshold Fixed at 100MB:**
- Problem: 100MB threshold is hardcoded; cannot be adjusted for different use cases
- Files: `file_matcher.py` (line 49: `size_threshold: int = 100*1024*1024`)
- Cause: No CLI option to configure threshold
- Improvement path: Add `--fast-threshold` CLI option

## Fragile Areas

**CLI Test Pattern:**
- Files: `tests/test_cli.py` (lines 17-22)
- Why fragile: Tests rely on `redirect_stdout` to capture output, but `main()` uses both `print()` for results and `logger` for status; if logging configuration changes, tests may fail to capture expected output
- Safe modification: Ensure tests run with known logger configuration
- Test coverage: Good coverage but tightly coupled to output format

**Sparse Hash Sample Positions:**
- Files: `file_matcher.py` (lines 119-144)
- Why fragile: Sample positions (start, 1/4, middle, 3/4, end) are hardcoded; changes affect hash values for all large files
- Safe modification: Do not change sample positions without considering backward compatibility
- Test coverage: Tested in `test_fast_mode.py`

## Scaling Limits

**Memory Usage with Many Files:**
- Current capacity: Hash-to-files dictionary grows with number of files
- Limit: Millions of files could consume significant memory storing all paths
- Scaling path: For very large directories, could stream results or use database-backed index

**No Progress Persistence:**
- Current capacity: Single-run only; if interrupted, must restart from beginning
- Limit: Very large directory comparisons (millions of files) cannot be resumed
- Scaling path: Add checkpoint/resume functionality for long-running comparisons

## Dependencies at Risk

**No External Dependencies:**
- The tool uses only Python standard library (hashlib, argparse, pathlib, logging, os, sys, collections)
- No third-party packages to maintain or update
- Low risk for dependency issues

## Missing Critical Features

**No Symlink Handling:**
- Problem: Symbolic links are followed by default (`rglob('*')` follows symlinks)
- Blocks: Could cause infinite loops with circular symlinks; could report false matches on symlink targets
- Files: `file_matcher.py` (line 169)

**No File Exclusion Patterns:**
- Problem: Cannot exclude files by pattern (e.g., `*.log`, `.git/`)
- Blocks: Comparing directories with generated or cache files requires manual cleanup first

**No Output Format Options:**
- Problem: Output is human-readable only; no JSON/CSV export
- Blocks: Integration with other tools or automated processing

## Test Coverage Gaps

**Error Path Testing:**
- What's not tested: Behavior when files become unreadable mid-scan, symlink edge cases, files that change during scan
- Files: `file_matcher.py` (lines 181-184)
- Risk: Error handling code (`except (PermissionError, OSError)`) is not explicitly tested
- Priority: Low (errors are logged and skipped, reasonable behavior)

**Edge Case File Content:**
- What's not tested: Empty files, binary vs text files, files with null bytes, very long file paths
- Files: `tests/test_base.py` creates only small text files
- Risk: Could miss issues with specific file types
- Priority: Low (hashing should handle all byte content)

**Invalid CLI Arguments:**
- What's not tested: Behavior with non-existent directories, same directory twice, invalid hash algorithm (handled by argparse)
- Files: `tests/test_cli.py`
- Risk: CLI error messages may not be user-friendly
- Priority: Low (argparse handles most validation)

---

*Concerns audit: 2026-01-19*
