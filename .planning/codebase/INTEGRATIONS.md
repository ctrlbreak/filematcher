# External Integrations

**Analysis Date:** 2026-01-19

## APIs & External Services

**None:**
- This is a standalone CLI tool with no external service dependencies
- All operations are local filesystem operations

## Data Storage

**Databases:**
- None - No database usage

**File Storage:**
- Local filesystem only
- Reads files from two user-specified directories
- No file writes (read-only analysis)

**Caching:**
- None - No persistent caching
- In-memory hash-to-files mapping during execution only

## Authentication & Identity

**Auth Provider:**
- None - No authentication required
- Tool operates on local filesystem with user's permissions

## Monitoring & Observability

**Error Tracking:**
- None - Errors printed to stderr via `logging` module

**Logs:**
- Python `logging` module with module-level `logger`
- INFO level: Progress messages (directory indexing status)
- DEBUG level: Per-file processing details (verbose mode)
- ERROR level: File access errors (PermissionError, OSError)
- Output controlled by `--verbose/-v` CLI flag

## CI/CD & Deployment

**Hosting:**
- GitHub repository
- No automated deployment

**CI Pipeline:**
- None detected
- Manual test execution: `python3 run_tests.py`

**Release Process:**
- Manual via `create_release.py` script
- Creates ZIP and TAR.GZ archives
- Intended for GitHub Releases upload

## Environment Configuration

**Required env vars:**
- None

**Secrets location:**
- Not applicable - no secrets needed

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

## Network Dependencies

**None:**
- Tool operates entirely offline
- No network requests made
- No external URLs accessed

## Operating System Integration

**Filesystem Access:**
- Read access to two user-specified directories
- Recursive directory traversal via `pathlib.Path.rglob()`
- Binary file reading for hash computation

**Permissions Required:**
- Read permission on target directories and files
- Gracefully handles PermissionError with logged warning

**Cross-Platform:**
- Works on Windows, macOS, Linux
- Uses `pathlib` for platform-agnostic path handling
- No platform-specific code

---

*Integration audit: 2026-01-19*
