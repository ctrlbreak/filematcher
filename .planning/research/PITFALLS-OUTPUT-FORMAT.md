# Domain Pitfalls: CLI Output Format Changes

**Domain:** CLI tool output format unification and JSON output addition
**Researched:** 2026-01-22
**Project:** File Matcher
**Confidence:** HIGH

## Executive Summary

Changing CLI output format is one of the highest-risk changes a CLI tool can make. Users often parse output with `grep`, `awk`, `sed`, and other text processing tools in automation scripts. A seemingly minor formatting change can break production pipelines without warning. Research shows that approximately one-third of all software releases introduce breaking changes, but in CLI tools, output format changes are particularly dangerous because they affect the implicit contract between tool and user scripts.

The key insight from the research: **human-readable output changes are acceptable and even encouraged for usability, but only when machine-readable alternatives exist for automation.**

## Critical Pitfalls

These mistakes cause rewrites, break user scripts, or create support burden.

### Pitfall 1: Breaking Scripts by Changing Default Output Format

**What goes wrong:** You change how the default output looks (spacing, ordering, labels, indentation) without providing a stable alternative. User scripts that parse output with `grep`, `awk`, or `sed` suddenly fail in production.

**Why it happens:**
- Developers think "it's just prettier formatting"
- No visibility into how users actually consume the output
- Testing focuses on human readability, not parsing stability
- "No one complained" fallacy (users quietly abandon the tool)

**Consequences:**
- Silent breakage in CI/CD pipelines
- Loss of user trust ("I can't rely on this tool")
- Support burden from debugging user scripts
- Users pin to old versions, missing security updates
- Negative reputation in the ecosystem

**Prevention:**
1. **Add machine-readable format BEFORE changing human format.** Implement `--json` or `--format=json` flag first, announce it, give users time to migrate.
2. **Document the stability guarantee explicitly.** State in docs: "Default output format is NOT stable. Use --json for scripting."
3. **Test with real parsing patterns.** Create test suite that parses output like users do:
   ```bash
   # Test that these patterns don't break
   output | grep '^\[MASTER\]' | wc -l
   output | awk '{print $2}'
   output | sed -n '/Hash:/p'
   ```
4. **Survey actual usage.** Check GitHub code search for how your tool is used in scripts before making changes.
5. **Provide migration guide.** When changing format, show side-by-side examples of old parsing vs new approach.

**Detection:**
- User bug reports about "tool stopped working" after upgrade
- Issues mention grep/awk/sed in the error context
- Scripts work on version N but fail on N+1
- Users ask "how do I parse this output?"

**Which phase:** Phase 1 (Design & Planning) - Decide output stability contract upfront

**Real-world example:** Git learned this lesson and provides `--porcelain` flag for "stable, easy-to-parse format for scripts" that is "guaranteed not to change in the future, making it safe for scripts." [Source: Linux man page for git-status](https://linux.die.net/man/1/git-status)

---

### Pitfall 2: JSON Schema Drift Without Versioning

**What goes wrong:** You add JSON output but don't document a schema or version it. Later changes (adding fields, renaming keys, changing types) break downstream tools without clear communication.

**Why it happens:**
- "It's just JSON" attitude - assuming flexibility means no contracts
- No formal schema documentation
- Adding "helpful" new fields without considering BC
- Changing field names for clarity
- Not understanding JSON as a public API

**Consequences:**
- jq queries break when field names change
- Automation scripts fail on missing keys
- Type mismatches (number becomes string)
- Duplicate key errors from dynamic keys
- No clear upgrade path for users

**Prevention:**
1. **Document JSON schema from day one.** Even informal documentation helps:
   ```markdown
   ## JSON Output Schema

   Root is an array of objects with:
   - `master_file`: string (absolute path)
   - `duplicates`: array of strings (absolute paths)
   - `size_bytes`: integer
   - `hash`: string (hash prefix, 8 chars)
   ```

2. **Use JSON Schema for validation.** Create schema file, test output against it in CI:
   ```bash
   filematcher --json | json-schema-validate schema.json
   ```

3. **Version the schema explicitly.** Include version in output or flag:
   ```json
   {
     "schema_version": "1.0",
     "results": [...]
   }
   ```
   Or use flags: `--format json-v1`, `--format json-v2`

4. **Follow append-only evolution.** Within a major version:
   - ADD new fields (OK)
   - RENAME fields (BREAKING - need new version)
   - CHANGE types (BREAKING - need new version)
   - REMOVE fields (BREAKING - need new version)

5. **Test schema stability.** Automated tests that fail if schema changes:
   ```python
   def test_json_schema_stability():
       output = run_cli(['--json'])
       data = json.loads(output)
       # Assert all expected keys exist
       # Assert types are correct
   ```

**Detection:**
- Users report "KeyError" or "field not found"
- jq expressions that used to work now fail
- Type conversion errors in parsing code
- Requests for "old format" or "version 1 output"

**Which phase:** Phase 1 (Design & Planning) and Phase 2 (Implementation) - Design schema upfront, enforce in tests

**Real-world example:** Kelly Brazil's blog post on adding JSON to CLI tools emphasizes: "Document a schema for the JSON output when possible...All possible fields, item types, and valid values should be listed there explicitly and kept up to date with code changes." [Source: Tips on Adding JSON Output to Your CLI App](https://blog.kellybrazil.com/2021/12/03/tips-on-adding-json-output-to-your-cli-app/)

---

### Pitfall 3: Mixing Human Messages with Machine-Readable Output on stdout

**What goes wrong:** You output both structured data (JSON, parseable text) and human messages (progress, warnings, status) to stdout. When users pipe to `jq` or parse the output, the extra messages break parsing.

**Why it happens:**
- Not understanding stdout vs stderr separation
- Adding "helpful" progress messages in machine mode
- Status output bleeding into data output
- Color codes in machine-readable output
- Banner messages or headers in piped output

**Consequences:**
- `filematcher --json | jq` fails with "parse error"
- `grep` captures human messages instead of data
- `wc -l` counts include header lines
- Scripts need complex filtering to extract data
- Users resort to `tail -n +N` hacks

**Prevention:**
1. **All data to stdout, all messages to stderr.**
   ```python
   # Correct
   print(json.dumps(data))  # Data to stdout
   print(f"Processing {count} files...", file=sys.stderr)  # Message to stderr
   ```

2. **Detect TTY and suppress non-data output.**
   ```python
   is_tty = sys.stdout.isatty()
   if is_tty:
       print("=== PREVIEW MODE ===")  # OK for interactive use
   print_data()  # Always output data
   ```

3. **Disable colors and formatting in pipes.**
   ```python
   # Disable colors when:
   # - stdout not a TTY
   # - NO_COLOR environment variable set
   # - --no-color flag passed
   # - TERM=dumb
   ```

4. **Test with pipes.** Automated test:
   ```bash
   # This should be valid JSON
   filematcher --json | jq . > /dev/null

   # This should be parseable
   filematcher | grep '^\[MASTER\]' | head -1
   ```

5. **Provide --quiet flag.** Suppress all stderr output for truly silent machine mode:
   ```bash
   filematcher --json --quiet | jq '.[] | .master_file'
   ```

**Detection:**
- "Invalid JSON" errors when piping to jq
- Extra lines in `wc -l` counts
- Color codes visible in piped output
- Headers mixed with data rows
- Users asking "how do I skip the first N lines?"

**Which phase:** Phase 2 (Implementation) - Core requirement for output formatting

**Real-world example:** The Command Line Interface Guidelines state: "Log messages, errors, and similar messaging should be sent to stderr so that when commands are piped together, these messages are displayed to the user and not fed into the next command." [Source: Command Line Interface Guidelines](https://clig.dev/)

---

### Pitfall 4: Inconsistent Flag/Output Mode Interactions

**What goes wrong:** Different output modes (`--json`, `--summary`, `--verbose`) interact unpredictably. Adding `--verbose` to `--json` breaks parsing, or `--summary --action` shows different data than `--action` alone.

**Why it happens:**
- Each mode implemented independently
- No decision matrix for flag combinations
- Copy-paste code with slight variations
- "It seemed logical at the time"
- Testing modes in isolation, not combinations

**Consequences:**
- Users confused by what flags do together
- Some combinations silently ignored
- Documentation can't explain behavior clearly
- Support burden: "What happens if I use X with Y?"
- Scripts break when adding seemingly unrelated flags

**Prevention:**
1. **Design interaction matrix upfront.**
   ```markdown
   | Mode      | --verbose | --summary | --json   |
   |-----------|-----------|-----------|----------|
   | compare   | +details  | counts    | +details |
   | --action  | +progress | counts    | +details |
   | --execute | +progress | counts    | +audit   |
   ```

2. **Make modes mutually exclusive where appropriate.**
   ```python
   if args.json and args.summary:
       parser.error("--json and --summary are mutually exclusive")
   ```

3. **Define clear precedence rules.**
   - Output format (--json, --plain) takes precedence over style (--verbose)
   - Machine formats ignore human flags (verbose, color)
   - Document: "--json ignores --verbose; use --json for full data"

4. **Test all reasonable combinations.**
   ```python
   @pytest.mark.parametrize("flags", [
       ["--json"],
       ["--json", "--verbose"],
       ["--json", "--action", "hardlink"],
       ["--summary"],
       ["--summary", "--verbose"],
       ["--action", "hardlink"],
       ["--action", "hardlink", "--verbose"],
   ])
   def test_flag_combinations(flags):
       # Verify output is valid and consistent
   ```

5. **Document flag interactions explicitly.**
   ```markdown
   ## Flag Interactions

   - `--json` ignores `--verbose` (full data always included in JSON)
   - `--summary` incompatible with `--action` (use preview mode for summary)
   - `--plain` removes colors/formatting but keeps structure
   ```

**Detection:**
- Users asking "does --verbose work with --json?"
- Bug reports: "Adding --X broke my script"
- Contradictory behavior between similar commands
- Documentation needs "except when" clauses
- Test matrix has gaps

**Which phase:** Phase 1 (Design & Planning) - Define interactions before implementation

**Real-world example:** AWS CLI documentation explicitly states flag interaction rules and provides comprehensive examples of combinations. [Source: Setting the output format in the AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-output-format.html)

---

## Moderate Pitfalls

These cause delays, confusion, or technical debt.

### Pitfall 5: No Migration Path from Old to New Output

**What goes wrong:** You change output format without providing a way to get the old format back. Users with scripts must either pin to old version or rewrite all scripts immediately.

**Why it happens:**
- Assuming new format is "better" so everyone will adapt
- Not wanting to maintain two formats
- No feedback from users before release
- Treating format as implementation detail

**Consequences:**
- Users stuck on old versions
- Angry GitHub issues: "You broke my workflow"
- Forced to maintain old version in parallel
- Reputation damage: "This tool is unreliable"

**Prevention:**
1. **Overlap period with both formats.** Deprecation cycle:
   - v1.0: Old format is default
   - v1.1: Add `--format=new` flag, announce deprecation of old
   - v1.5: Add `--format=legacy` flag, make new format default (with warnings)
   - v2.0: Remove old format

2. **Environment variable for compatibility mode.**
   ```bash
   FILEMATCHER_LEGACY_OUTPUT=1 filematcher dir1 dir2
   ```

3. **Provide conversion scripts.**
   ```bash
   # Help users migrate
   scripts/convert-output-format.sh old-script.sh > new-script.sh
   ```

4. **Pre-announce breaking changes.** Follow Azure CLI pattern:
   - Announce 6+ months before change
   - Coordinate breaking changes into scheduled releases
   - Provide exact migration instructions

**Detection:**
- "How do I get the old format back?"
- Users refusing to upgrade
- Requests to revert the change
- Forks maintaining old behavior

**Which phase:** Phase 1 (Design & Planning) - Plan migration before implementing change

---

### Pitfall 6: Undocumented Output Guarantees

**What goes wrong:** Documentation doesn't state what is stable vs what may change. Users assume everything is stable or nothing is stable.

**Why it happens:**
- Documentation written after implementation
- Assuming "it's obvious" what's stable
- Fear of commitment to stability
- Not thinking about user scripts

**Consequences:**
- Users scared to write scripts
- Every release potentially breaking
- No clear contract for automation
- Support questions about stability

**Prevention:**
1. **Document stability explicitly in README and man page.**
   ```markdown
   ## Output Stability Guarantees

   - **Default output**: NOT stable. May change formatting, ordering, or content
     between minor versions. For human consumption only.

   - **JSON output** (--json): Stable within major versions. Changes follow semver:
     - Patch: Bug fixes only
     - Minor: New fields added (append-only)
     - Major: Field renames, removals, or type changes

   - **Plain output** (--plain): Stable line format. One item per line, suitable
     for grep/awk/sed. Ordering may change but format will not.
   ```

2. **Add stability markers to help output.**
   ```bash
   $ filematcher --help
   Output formats:
     --json         Machine-readable JSON (stable, versioned)
     --plain        Plain text output (stable for parsing)
     (default)      Human-readable output (NOT stable, may change)
   ```

3. **Version machine-readable output.**
   ```bash
   --format=json-v1    # Explicit version
   --format=json       # Latest version (alias)
   ```

**Detection:**
- Users asking "is this stable?"
- Scripts breaking on minor updates
- Feature requests for stable format

**Which phase:** Phase 1 (Design & Planning) - Document contract upfront

---

### Pitfall 7: Deeply Nested JSON Structures

**What goes wrong:** JSON output uses deeply nested objects that are hard to query with jq. Users need complex expressions for simple data access.

**Why it happens:**
- Mirroring internal data structures in output
- "More organized" nesting
- Not testing actual jq usage
- Python/dict-thinking instead of user-thinking

**Consequences:**
- Complex jq expressions: `.results[] | .groups[] | .files[] | .metadata.hash`
- User frustration with "why is this so nested?"
- More likely to parse incorrectly
- Documentation needs jq cookbook

**Prevention:**
1. **Flatten when possible.** Use prefixed keys:
   ```json
   // Bad (deeply nested)
   {
     "group": {
       "master": {
         "path": "/foo",
         "size": 1024,
         "metadata": {"hash": "abc123"}
       }
     }
   }

   // Good (flattened)
   {
     "master_path": "/foo",
     "master_size": 1024,
     "master_hash": "abc123"
   }
   ```

2. **Use arrays of flat objects.**
   ```json
   // Users can: jq '.[] | select(.type == "duplicate") | .path'
   [
     {"type": "master", "path": "/a", "hash": "abc", "size": 1024},
     {"type": "duplicate", "path": "/b", "hash": "abc", "size": 1024}
   ]
   ```

3. **Test common jq patterns.**
   - Get all master files: `jq '.[].master_path'`
   - Count duplicates: `jq 'map(.duplicates | length) | add'`
   - Filter by size: `jq '.[] | select(.size_bytes > 1000000)'`

**Detection:**
- Users sharing complex jq snippets
- Documentation needs jq examples for basic queries
- Requests for "simpler output format"

**Which phase:** Phase 2 (Implementation) - JSON structure design

**Real-world example:** Kelly Brazil advises: "Use a flat array of objects structure to make getting to the data easy - just loop over the array, filter by type if needed, and pull attributes from the top-level of each object." [Source: Tips on Adding JSON Output to Your CLI App](https://blog.kellybrazil.com/2021/12/03/tips-on-adding-json-output-to-your-cli-app/)

---

## Minor Pitfalls

These cause annoyance but are fixable.

### Pitfall 8: Color Codes in Non-TTY Output

**What goes wrong:** Color escape codes appear in piped or redirected output, breaking parsing and creating garbage in files.

**Why it happens:**
- Not detecting TTY
- Forcing color always
- Ignoring NO_COLOR convention
- Not testing with pipes

**Consequences:**
- ANSI codes visible in logs: `[32mSUCCESS[0m`
- grep/awk see extra characters
- Stored output contains garbage
- Users disable colors entirely

**Prevention:**
1. **Detect TTY automatically.**
   ```python
   import sys
   use_color = sys.stdout.isatty()
   ```

2. **Respect NO_COLOR environment variable.** Standard: if `NO_COLOR` is set (any non-empty value), disable colors.

3. **Provide --no-color flag.** Let users explicitly disable.

4. **Don't force colors in machine mode.**
   ```python
   if args.json or not sys.stdout.isatty():
       use_color = False
   ```

**Detection:**
- Color codes in redirected output
- Complaints about "garbage characters"
- `cat output.txt` shows escape codes

**Which phase:** Phase 2 (Implementation) - Output formatting

---

### Pitfall 9: Inconsistent Sort Order Between Runs

**What goes wrong:** Output order changes between identical runs (dict iteration order, file system order), making diffs impossible and confusing users.

**Why it happens:**
- Python dict order (pre-3.7)
- File system iteration order
- Hash iteration
- Not sorting before output

**Consequences:**
- `diff old.txt new.txt` shows false changes
- Hard to track actual changes
- Flaky tests
- Users think tool is broken

**Prevention:**
1. **Sort output explicitly.**
   ```python
   # Sort by path
   for master, dups, reason in sorted(results, key=lambda x: x[0]):
       print_group(master, dups)

   # Sort duplicates within group
   for dup in sorted(duplicates):
       print(f"  {dup}")
   ```

2. **Document sort order.**
   ```markdown
   Output is sorted:
   1. Groups sorted by master file path (alphabetical)
   2. Duplicates within group sorted alphabetically
   3. Unmatched files sorted alphabetically
   ```

3. **Test for stability.**
   ```python
   def test_output_deterministic():
       out1 = run_cli(['dir1', 'dir2'])
       out2 = run_cli(['dir1', 'dir2'])
       assert out1 == out2
   ```

**Detection:**
- Output differs between runs
- Test flakiness
- Users report "order keeps changing"

**Which phase:** Phase 2 (Implementation) - Output formatting

---

### Pitfall 10: Missing Error Context in Machine-Readable Output

**What goes wrong:** JSON output only includes success data. Errors are printed to stderr in human format, losing structure in automated systems.

**Why it happens:**
- Errors added as afterthought
- Assuming stderr is sufficient
- Not considering error handling in scripts

**Consequences:**
- Scripts can't distinguish error types
- Exit codes alone insufficient
- Logging systems can't categorize errors
- Users parse stderr (fragile)

**Prevention:**
1. **Include errors in JSON output.**
   ```json
   {
     "status": "partial_success",
     "groups": [...],
     "errors": [
       {
         "type": "permission_denied",
         "path": "/foo/bar",
         "message": "Permission denied"
       }
     ]
   }
   ```

2. **Use structured error output.**
   ```python
   if args.json:
       result = {
         "success": False,
         "error": {"code": "INVALID_PATH", "message": "..."}
       }
       print(json.dumps(result))
   else:
       print(f"Error: Invalid path", file=sys.stderr)
   ```

3. **Document error codes.** Let users programmatically handle errors.

**Detection:**
- Scripts parsing stderr for errors
- Requests for "error in JSON"
- Can't distinguish error types

**Which phase:** Phase 2 (Implementation) - Error handling

---

## Phase-Specific Warnings

| Phase | Likely Pitfall | Mitigation |
|-------|---------------|------------|
| Phase 1: Design & Planning | Pitfall 1: No machine-readable format before changing human output | Define stability contract, plan --json flag, create interaction matrix |
| Phase 1: Design & Planning | Pitfall 4: Inconsistent flag interactions | Create decision matrix for all flag combinations upfront |
| Phase 1: Design & Planning | Pitfall 6: Undocumented stability guarantees | Write stability policy in README before implementation |
| Phase 2: Implementation | Pitfall 2: JSON schema drift | Document schema, create validation tests, version explicitly |
| Phase 2: Implementation | Pitfall 3: Mixing stdout/stderr | Test with pipes, separate data (stdout) from messages (stderr) |
| Phase 2: Implementation | Pitfall 7: Deeply nested JSON | Design flat structure, test common jq queries |
| Phase 2: Implementation | Pitfall 8: Color codes in pipes | Detect TTY, respect NO_COLOR |
| Phase 2: Implementation | Pitfall 9: Inconsistent ordering | Sort all output explicitly |
| Phase 3: Testing | Pitfall 1: Breaking parsing patterns | Test output with grep/awk/sed/jq patterns |
| Phase 3: Testing | Pitfall 4: Untested flag combinations | Test all reasonable flag combinations |
| Phase 4: Documentation | Pitfall 5: No migration path | Document deprecation timeline, provide conversion scripts |
| Phase 4: Documentation | Pitfall 6: Unclear stability | Document what's stable vs what may change |

## File Matcher Specific Warnings

Based on the current codebase analysis:

### Current State
- Tool has two distinct modes: compare mode (default) and action mode (with `--action`)
- Compare mode shows matching files across directories
- Action mode has preview (default) and execute (`--execute`) submodes
- Output formatting already quite sophisticated with multiple labels: `[MASTER]`, `[DUP:?]`, `[WOULD HARDLINK]`, etc.

### High Risk Areas

1. **Multiple output branches** (lines 1045-1340)
   - Compare mode without action (line 1296+)
   - Master mode without action (line 1228+)
   - Preview mode with action (line 1154)
   - Execute mode with action (line 1158)
   - Each has different output patterns
   - **Risk:** Changes to unify these could break existing scripts

2. **Label proliferation**
   - `[MASTER]`, `[DUP:?]`, `[WOULD HARDLINK]`, `[WOULD SYMLINK]`, `[WOULD DELETE]`
   - Different labels in preview vs execute mode
   - **Risk:** Any label changes break grep patterns like `grep '^\[MASTER\]'`

3. **Summary vs detailed output** (lines 1084-1151, 1229-1238)
   - Different structure with `--summary` flag
   - Statistics footer format changes based on mode
   - **Risk:** Unifying might accidentally change summary format

4. **Verbose mode adds file sizes** (lines 120-126, 1116-1120)
   - Changes line format when enabled
   - **Risk:** Inconsistent JSON representation of verbose data

### Specific Recommendations for File Matcher

1. **Before changing any output:**
   - Add `--json` flag that outputs stable structure
   - Document that default format may change
   - Test with common parsing patterns:
     ```bash
     # Existing scripts likely do this
     filematcher dir1 dir2 | grep '^\[MASTER\]' | wc -l
     filematcher dir1 dir2 --action hardlink | grep WOULD
     ```

2. **For JSON output design:**
   ```json
   {
     "schema_version": "1.0",
     "mode": "compare|action",
     "action": null|"hardlink"|"symlink"|"delete",
     "executed": false,
     "groups": [
       {
         "hash": "abc123...",
         "master_file": "/path/to/master",
         "duplicates": [
           {
             "path": "/path/to/dup",
             "size_bytes": 1024,
             "would_cross_filesystem": false
           }
         ]
       }
     ],
     "statistics": {
       "group_count": 5,
       "duplicate_count": 12,
       "space_savings_bytes": 12345
     }
   }
   ```

3. **Unification strategy:**
   - Keep labels consistent across modes
   - Use same indentation/spacing everywhere
   - Make statistics footer identical structure
   - But ADD JSON mode first before touching human output

## Success Metrics

You've successfully avoided these pitfalls when:

- [ ] Machine-readable format (--json) exists BEFORE changing human output
- [ ] JSON schema documented and versioned
- [ ] All data to stdout, messages to stderr
- [ ] Tests verify grep/awk/jq parsing patterns don't break
- [ ] Flag interaction matrix documented
- [ ] Stability guarantees explicitly stated in docs
- [ ] Color codes disabled in non-TTY output
- [ ] Output order deterministic and documented
- [ ] Migration path provided for format changes
- [ ] Users can write scripts confidently without fear of breakage

## Sources

This research synthesized best practices from multiple authoritative sources:

### CLI Design Guidelines
- [Command Line Interface Guidelines (clig.dev)](https://clig.dev/) - Comprehensive CLI design best practices
- [CLI Best Practices - HackMD](https://hackmd.io/@arturtamborski/cli-best-practices) - Community-curated best practices
- [Azure CLI Breaking Change Pre-Announcement](https://techcommunity.microsoft.com/blog/azuretoolsblog/azure-cli-breaking-change-pre-announcement/4403454) - How Microsoft handles breaking changes

### JSON Output Best Practices
- [Tips on Adding JSON Output to Your CLI App](https://blog.kellybrazil.com/2021/12/03/tips-on-adding-json-output-to-your-cli-app/) - Kelly Brazil's comprehensive guide from jc project experience
- [Hacker News discussion on JSON CLI output](https://news.ycombinator.com/item?id=29435786) - Community insights
- [jq Manual](https://jqlang.org/manual/) - Understanding JSON querying patterns

### Machine-Readable Output
- [Vagrant Machine Readable Output](https://developer.hashicorp.com/vagrant/docs/cli/machine-readable) - HashiCorp's approach
- [Using Salesforce CLI Output and Scripting](https://developer.salesforce.com/blogs/2020/02/using-salesforce-cli-output-and-scripting) - Enforcing --json for stability
- [Rust CLI Recommendations - Machine-readable output](https://rust-cli-recommendations.sunshowers.io/machine-readable-output) - Versioning and stability

### Backward Compatibility
- [Semantic Versioning 2.0.0](https://semver.org/) - Versioning principles
- [Arduino CLI Backward compatibility policy](https://arduino.github.io/arduino-cli/0.35/versioning/) - Real-world BC policy
- [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) - Communicating breaking changes

### Git as Example
- [git-status man page](https://linux.die.net/man/1/git-status) - --porcelain flag for stable parsing
- [Git Configuration](https://git-scm.com/book/sv/v2/Customizing-Git-Git-Configuration) - Color and output control

### Output Formatting Research
- [Python print() Output: Practical Patterns, Pitfalls, and Modern Workflows (2026)](https://thelinuxcode.com/python-print-output-practical-patterns-pitfalls-and-modern-workflows-2026/) - Recent perspectives on CLI output
- [AWS CLI Output Format](https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-output-format.html) - Flag interaction examples
