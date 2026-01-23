---
phase: quick
plan: 005
type: execute
wave: 1
depends_on: []
files_modified:
  - run_tests.py
  - file_matcher.py
  - .gitignore
autonomous: true

must_haves:
  truths:
    - "Test logs are written to .logs_test/ directory, not project root"
    - ".logs_test/ is cleared at START of test run (logs inspectable after)"
    - ".logs_test/ is gitignored"
    - "Existing log files in project root are removed"
  artifacts:
    - path: "run_tests.py"
      provides: "Test runner that creates/clears .logs_test and sets env var"
      contains: "FILEMATCHER_LOG_DIR"
    - path: "file_matcher.py"
      provides: "create_audit_logger respects FILEMATCHER_LOG_DIR env var"
      contains: "FILEMATCHER_LOG_DIR"
    - path: ".gitignore"
      provides: ".logs_test/ entry"
      contains: ".logs_test/"
  key_links:
    - from: "run_tests.py"
      to: "file_matcher.py"
      via: "FILEMATCHER_LOG_DIR environment variable"
      pattern: "FILEMATCHER_LOG_DIR"
---

<objective>
Redirect test-generated log files to .logs_test/ directory instead of polluting project root.

Purpose: Keep project root clean; test logs are still available for inspection after test runs.
Output: Modified run_tests.py, file_matcher.py, .gitignore; clean project root.
</objective>

<execution_context>
@/Users/patrick/.claude/get-shit-done/workflows/execute-plan.md
@/Users/patrick/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@run_tests.py
@file_matcher.py (lines 1680-1720 - create_audit_logger function)
@.gitignore
</context>

<tasks>

<task type="auto">
  <name>Task 1: Update create_audit_logger to respect FILEMATCHER_LOG_DIR env var</name>
  <files>file_matcher.py</files>
  <action>
Modify the `create_audit_logger` function (around line 1688-1712) to check for `FILEMATCHER_LOG_DIR` environment variable when `log_path` is None:

1. After the `if log_path is None:` check, before generating the default name:
2. Check `os.environ.get('FILEMATCHER_LOG_DIR')`
3. If set, create the log file in that directory instead of CWD
4. Keep the same filename format: `filematcher_{timestamp}.log`

Example modification:
```python
if log_path is None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = os.environ.get('FILEMATCHER_LOG_DIR')
    if log_dir:
        log_path = Path(log_dir) / f"filematcher_{timestamp}.log"
    else:
        log_path = Path(f"filematcher_{timestamp}.log")
```

This is a minimal, backward-compatible change - existing behavior unchanged when env var not set.
  </action>
  <verify>Run `python3 -c "from file_matcher import create_audit_logger; import os; os.environ['FILEMATCHER_LOG_DIR']='/tmp/test_logs'; import tempfile; os.makedirs('/tmp/test_logs', exist_ok=True); _, p = create_audit_logger(None); print(f'Log created in: {p.parent}'); assert '/tmp/test_logs' in str(p)"`</verify>
  <done>create_audit_logger creates logs in FILEMATCHER_LOG_DIR when set, CWD otherwise</done>
</task>

<task type="auto">
  <name>Task 2: Update run_tests.py to manage .logs_test directory</name>
  <files>run_tests.py</files>
  <action>
Modify run_tests.py to:

1. At the start (before running tests), add imports: `shutil` and `Path` from pathlib
2. Define log directory path: `.logs_test` in project root
3. Clear the directory if it exists (remove and recreate), or create if missing
4. Set `FILEMATCHER_LOG_DIR` environment variable to absolute path of `.logs_test`
5. Keep clearing at START so logs can be inspected after tests complete

Add this block after the "Starting File Matcher tests" print and before test discovery:

```python
import shutil
from pathlib import Path

# Set up test log directory - clear at START so logs are inspectable after
logs_dir = Path(__file__).parent / '.logs_test'
if logs_dir.exists():
    shutil.rmtree(logs_dir)
logs_dir.mkdir(exist_ok=True)
os.environ['FILEMATCHER_LOG_DIR'] = str(logs_dir.resolve())
print(f"Test logs will be written to: {logs_dir}")
```

Note: `os` is already imported in run_tests.py.
  </action>
  <verify>Run `python3 run_tests.py 2>&1 | head -20` and confirm "Test logs will be written to: .logs_test" appears, and `.logs_test/` directory exists after</verify>
  <done>.logs_test directory created/cleared at test start, FILEMATCHER_LOG_DIR set</done>
</task>

<task type="auto">
  <name>Task 3: Update .gitignore and clean up existing logs</name>
  <files>.gitignore</files>
  <action>
1. Add `.logs_test/` to .gitignore (under "Unit test / coverage reports" section is logical)

2. Remove existing log files from project root:
   - Delete all files matching `filematcher_*.log` in project root
   - Do NOT commit the deletion (files are already gitignored via `*.log` on line 41)

For .gitignore, add after the existing test-related entries (around line 27):
```
.logs_test/
```

Note: Line 41 already has `*.log` so individual log files are already ignored, but explicitly ignoring the directory is cleaner.
  </action>
  <verify>
1. `grep -n ".logs_test" .gitignore` shows the entry
2. `ls filematcher_*.log 2>/dev/null | wc -l` returns 0 (no log files in project root)
3. `git status` shows .gitignore modified (not the deleted log files, since they were untracked)
  </verify>
  <done>.logs_test/ in .gitignore, no log files in project root</done>
</task>

</tasks>

<verification>
1. Run full test suite: `python3 run_tests.py`
2. Verify no new log files in project root: `ls filematcher_*.log 2>/dev/null`
3. Verify logs written to .logs_test: `ls .logs_test/filematcher_*.log`
4. Run `git status` - only modified files should be run_tests.py, file_matcher.py, .gitignore
</verification>

<success_criteria>
- All 204 tests pass
- Log files appear in .logs_test/ (not project root)
- .logs_test/ is gitignored
- Project root is clean of *.log files
</success_criteria>

<output>
After completion, create `.planning/quick/005-clean-up-test-logs-into-logs-test-direct/005-SUMMARY.md`
</output>
