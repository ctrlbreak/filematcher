---
phase: quick
plan: 013
type: execute
wave: 1
depends_on: []
files_modified:
  - filematcher/cli.py
  - filematcher/__init__.py
  - filematcher/formatters.py
  - tests/test_safe_defaults.py
autonomous: true
must_haves:
  truths:
    - "No function is defined but never called in the codebase"
    - "No import statement imports symbols that are never used"
    - "Public API exports only used functions"
  artifacts:
    - path: "filematcher/cli.py"
      provides: "CLI module without dead code"
    - path: "filematcher/__init__.py"
      provides: "Package exports without dead code"
  key_links:
    - from: "filematcher/__init__.py"
      to: "filematcher/cli.py"
      via: "re-exports"
      pattern: "from filematcher.cli import"
---

<objective>
Remove redundant unused code identified in the filematcher package.

Purpose: Clean up legacy code that was superseded by Phase 19 (Interactive Execute) but never removed.

Output: Cleaner codebase with no dead code.
</objective>

<context>
@.planning/STATE.md
@filematcher/cli.py
@filematcher/__init__.py
@filematcher/formatters.py
@tests/test_safe_defaults.py
</context>

<analysis>
## Identified Dead Code

### 1. `confirm_execution()` in `filematcher/cli.py` (lines 29-37)

**Status:** DEAD - defined but never called

**History:** This function was added in Phase 3 (Safe Defaults) for the original batch confirmation flow. In Phase 19 (Interactive Execute), the code was refactored to use `interactive_execute()` and `prompt_for_group()` instead. The old confirmation flow was replaced but `confirm_execution()` was never removed.

**Evidence:**
- Grep for `confirm_execution(` shows only the definition (line 29) and no calls in filematcher/
- The function is exported in `__init__.py` but never called anywhere
- Tests import it but don't use it (test_safe_defaults.py line 12)

### 2. `format_confirmation_prompt()` in `filematcher/formatters.py` (lines 827-845)

**Status:** DEAD - defined but never called

**History:** This function was added in Phase 4 (Actions/Logging) to format the batch confirmation prompt. In Phase 19 (Interactive Execute), per-group prompts replaced the batch confirmation. The function is still imported in cli.py but never called.

**Evidence:**
- Grep for `format_confirmation_prompt(` in cli.py shows import but no usage
- No tests use this function
- The formatter classes use `format_group_prompt()` instead

### 3. Unused import in `tests/test_safe_defaults.py`

**Status:** DEAD IMPORT - imported but never used

The import `from filematcher import main, PREVIEW_BANNER, confirm_execution` includes `confirm_execution` which is never used in the file.
</analysis>

<tasks>

<task type="auto">
  <name>Task 1: Remove confirm_execution and format_confirmation_prompt</name>
  <files>
    filematcher/cli.py
    filematcher/__init__.py
    filematcher/formatters.py
  </files>
  <action>
Remove the dead code:

1. In `filematcher/cli.py`:
   - Remove the `confirm_execution()` function (lines 29-37)
   - Remove `format_confirmation_prompt` from the imports at line 22

2. In `filematcher/__init__.py`:
   - Remove `confirm_execution` from the import statement at line 131
   - Remove `"confirm_execution"` from the `__all__` list (line 215)
   - Remove `format_confirmation_prompt` from the import statement at line 113
   - Remove `"format_confirmation_prompt"` from the `__all__` list (line 220)

3. In `filematcher/formatters.py`:
   - Remove the `format_confirmation_prompt()` function (lines 827-845)
   - Remove the `_ACTION_VERBS` dict if only used by format_confirmation_prompt (lines 814-818)
  </action>
  <verify>
Run: `python3 -c "from filematcher import main; print('Import OK')"`
Run: `python3 -c "from filematcher.cli import main; print('CLI import OK')"`
Run: `grep -n "confirm_execution" filematcher/*.py` - should return no matches
Run: `grep -n "format_confirmation_prompt" filematcher/*.py` - should return no matches
  </verify>
  <done>
- confirm_execution() removed from cli.py
- format_confirmation_prompt() removed from formatters.py
- Both removed from __init__.py exports
- Package imports work correctly
  </done>
</task>

<task type="auto">
  <name>Task 2: Fix test imports and run tests</name>
  <files>
    tests/test_safe_defaults.py
  </files>
  <action>
1. In `tests/test_safe_defaults.py`:
   - Change line 12 from `from filematcher import main, PREVIEW_BANNER, confirm_execution`
   - To: `from filematcher import main, PREVIEW_BANNER`

2. Run the full test suite to verify no regressions.
  </action>
  <verify>
Run: `python3 run_tests.py` - all 284 tests should pass
  </verify>
  <done>
- Unused import removed from test_safe_defaults.py
- All tests pass (284 tests)
  </done>
</task>

<task type="auto">
  <name>Task 3: Verify no other dead code and commit</name>
  <files>N/A</files>
  <action>
1. Run a final check for any remaining unused functions by searching for functions defined but not called:
   - Check `colorize()` - used internally by color helpers (green, yellow, etc.)
   - Check `strip_ansi()` - used by `visible_len()`
   - Check all other exports are used

2. Update STATE.md with the quick task completion.

3. Commit the changes.
  </action>
  <verify>
Run: `python3 -m filematcher test_dir1 test_dir2` - should work correctly
Run: `git diff --stat` - shows only expected files changed
  </verify>
  <done>
- No other dead code found
- STATE.md updated
- Changes committed
  </done>
</task>

</tasks>

<verification>
1. Package imports work: `python3 -c "from filematcher import main"`
2. CLI works: `python3 -m filematcher test_dir1 test_dir2`
3. All 284 tests pass: `python3 run_tests.py`
4. No references to removed functions: `grep -r "confirm_execution\|format_confirmation_prompt" filematcher/`
</verification>

<success_criteria>
- confirm_execution() removed from codebase
- format_confirmation_prompt() removed from codebase
- All imports updated to not reference removed functions
- All 284 tests pass
- CLI functionality unchanged
</success_criteria>

<output>
After completion, update `.planning/STATE.md` with:
- Quick task 013 completed
- Note: Removed legacy confirm_execution() and format_confirmation_prompt() (superseded by Phase 19)
</output>
