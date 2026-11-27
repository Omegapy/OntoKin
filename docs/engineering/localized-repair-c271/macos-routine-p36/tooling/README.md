# Gate MR observational tooling

Phase C271-P36, gate MR of `ontokin.current-host-readback/0.2.0` at design revision 4, stage S3 of
`../MR-PLAN.md`, section 5. Author: W2, the independent author, who wrote none of the code under
test. Revision 2, after tooling review 001 (`REJECT_WITH_MANDATORY_FINDINGS`) and its
disposition; W2's author notes map each finding TR-01 to TR-11 to its change and its test.

The tooling observes. It changes no test, no implementation file, no contract, no amendment and no
frozen control of MI, and it never edits its inputs. Every plan that uses a tool binds it by path,
SHA-256, size and mode. Nothing here classifies a test as exempt.

| Piece of MR-PLAN section 5 | Here |
| --- | --- |
| Unit-log outcome collector | `unit_log_outcomes.py collect` |
| Baseline comparator | `unit_log_outcomes.py compare`, which re-reads both raw logs with the same parser |
| Readback evidence reader | `readback_evidence.py run` (a driver run) and `readback_evidence.py cohort` (one cohort root) |
| Reused from MH | the failure-capture procedure, the runtime-discovery collector and the numerical-audit harness, unchanged; see [the reuse table](#reused-from-mh-unchanged) |

The collector and the comparator share one file on purpose: the comparator must not trust a
collector record (MH's TR-07), so it parses the raw logs itself, and one parser cannot disagree
with itself.

## Shared rules

- **Placement.** This directory lies outside the unit stage's start directory `tests/` and outside
  the provider's source set, so it changes neither the default inventory (MC28) nor what the
  provider binds. Its `tests/` directory is not discovered by the unit stage.
- **Standard library only.** No tool imports another tool, a project module or `subprocess`.
- **No process.** No tool starts a process. Each reads its inputs and writes one output file.
- **`-B` first (N-09, MH's TR-17 and TR2-05).** Each tool's first statements are `import sys` and a
  check of `sys.flags.dont_write_bytecode`: a start without `-B` refuses with exit 2 and one JSON
  line on stderr before any other module is imported.
- **Bound inputs.** Every input file of `collect` and `compare`, and the summary and the audit
  record of the reader, is bound by a SHA-256 given on the command line, or by a digest that
  another bound input records (a summary names its log; a selection names its parent). A digest
  that differs refuses. **The reader's cohort root is not bound that way (TR-09):** neither the
  command line nor the summary gives a digest of its files. The reader cross-checks them with one
  another and with the derived selection, and records the binding of every file it read in
  `cohort_bindings`. The operational freeze fixes the cohort route and root and binds those
  bindings for the audit. Files are opened without following a final link, and a change during
  the read refuses. Every path argument must be canonical (its own realpath); on macOS that means
  `/private/var/...`, not `/var/...`.
- **Outputs.** A tool writes only to the absent output path given to it, in an existing canonical
  directory. It refuses an existing one and never replaces anything. The file is created
  exclusively (`O_EXCL`) and fsynced with its directory.
- **Self-identification.** Every output records the tool's path, SHA-256, size and mode;
  `sys.argv` and `sys.orig_argv`, the cwd and the PID; the Python version, build string,
  executable and `sys.flags`; the start and finish times (UTC) and the elapsed time; and
  `loaded_project_files`, which is always empty.
- **Refusals and failures.** A refusal is written to the output when the output path is valid, and
  as one JSON line on stderr (`ontokin.c271.p36-tool-refusal/1`, with its `rule`). An unexpected
  failure is reported as `UNKNOWN` (`ontokin.c271.p36-tool-failure/1`), never as a result.
- **Exit codes.** 0 is the tool's success predicate, 1 means that the work completed and something
  differs, 2 is a refusal, 3 an unknown outcome. Each section says what 0 means.
- **Launch.** `python3 -I -S -B <tool> ...`, with the framework interpreter. `-I` and `-S` are
  admitted and not required.

## unit_log_outcomes.py collect: unit-log outcomes

**Input.** One unit-stage log: the combined stdout and stderr of
`python -B -m unittest discover -s tests -v` that `tools/check_local.py` keeps as
`<output>/logs/unit-tests.log`.

```
unit_log_outcomes.py collect --log LOG --log-sha256 H [--expect ID=OUTCOME[*N] | --expect ID=missing ...] \
                             [--inventory DISCOVERY --inventory-sha256 H] --output OUT
```

**How the log is read**
- **The footer first.** The last occurrence of the separator line of 70 `-`, `Ran N test(s) in
  S.SSSs`, an empty line and the result line (`OK`, `FAILED` or `NO TESTS RAN`, with unittest's
  counts in unittest's order). The result word must fit the counts. Text after the footer, such as
  stdout flushed at exit, is kept as `trailing_text` (bytes, lines, digest). Earlier
  footer-shaped text, such as a test's own output, is counted.
- **The progress section** is read as CPython 3.12's `TextTestResult` writes it, with its
  `_newline` state emulated:
  - a start, `<description> ... `, where the description is `method (module.Class.method)`,
    followed on a second line by the docstring's first line when there is one. For the loader's
    own tests of a module that failed to import or was skipped (`unittest.loader._FailedTest`,
    `unittest.loader.ModuleSkipped`), the method is the module's name, dotted for a module inside
    a test package (TR-08);
  - a status written directly after the start: `ok`, `FAIL`, `ERROR`, `skipped '<reason>'`,
    `expected failure` or `unexpected success`;
  - `  <subtest description> ... FAIL|ERROR|skipped '...'` for each failing or skipped subtest;
  - a status line that repeats the description, for a test's further events (a failure, then a
    tearDown error, for example) or its own status after subtest lines;
  - the fixture lines `setUpClass (module.Class)`, `tearDownClass (...)`, `setUpModule (module)`
    and `tearDownModule (...)`, with `ERROR` or a skip.
- **Text from tests and their children** (block-buffered stdout, warnings, child output) is kept as
  noise, with its line numbers and digest. This includes noise glued in front of a runner line and
  noise between a start and its status.
- **A status that does not directly follow its start (TR-05)** is taken only when it is the one
  candidate among the lines up to the next runner line. A candidate is a line that is exactly a
  status, a line that ends with one (glued after noise), or text after the start's ` ... ` that
  ends with one. Two or more candidates refuse the log (`AMBIGUOUS`), whatever their values,
  because one of them was printed and any choice would be a guess, even one that keeps every count.
  A status token that a test writes, unbuffered, immediately after its own start and before the
  real status is read as the status, since nothing in the file tells the two apart. Such a misread
  is refused when it changes a count or a listing entry. It is not detected when it changes neither,
  for example a printed `skipped '<another reason>'` before a real skip (see the limits).
- **The listing** (the ERROR entries, then the FAIL entries, then the unexpected successes) must
  consist of exactly the headers that the progress section implies, in that order. Every header text
  must occur exactly as often as expected, so the split is unique. Each entry's text gives the
  reason.
- **The first line of a reason** is taken from the last block of the traceback chain. The blocks
  are separated by unittest's two chain lines, each between empty lines. The exception text starts
  at the first line after the frames, which are the lines indented by two spaces after
  `Traceback (most recent call last):`. The first line of every block, the line count and a digest
  of the whole text are kept too.

**Checks.** The parsed counts must equal the log's own footer:
- the tests started equal `Ran N`;
- the failures, errors, skips, expected failures and unexpected successes each equal the result
  line's count;
- the listing entries equal the failures and errors;
- every test has a status.

A log that cannot be read completely and consistently is refused, never repaired.

**Output** (`ontokin.c271.p36-unit-log-outcomes/2`)
- **`tests`:** one record per raw test ID as unittest prints it, in run order. Each record holds:
  - `outcome`: `passed`, `failure`, `error`, `skipped`, `expected_failure` or `unexpected_success`.
    An error outranks a failure, which outranks the other outcomes. A skip inside a subtest makes
    the test `skipped`;
  - `reasons`: the first line of each failure or error;
  - `skip_reasons`, decoded from unittest's repr;
  - `failing_subtests` and `skipped_subtests`;
  - `special`: `failed_import_or_load` for `unittest.loader._FailedTest.<module>`, or
    `module_skipped` for `unittest.loader.ModuleSkipped.<module>`, where `<module>` may be dotted;
  - `runs`: every occurrence, with its line and its events, so a test ID that runs twice keeps
    both.
- **`fixtures`:** one record per class-level or module-level ID, `setUpClass (module.Class)` and
  so on, as unittest's `_ErrorHolder` names it.
- **`footer`, `counts` and `checks`.**
- **`driver_reading`:** what `tools/check_local.py`'s own regular expressions read from this log,
  decoded as the driver decodes it (`Path.read_text`, universal newlines, so a carriage return is a
  line end; TR-11), and `equals_footer`, whether that reading equals the footer read here. The
  comparator checks it against the summary's `test_execution`.
- **`noise`.**
- **`expectations` (TR-02):** one row per `--expect`, for exact IDs, for example MC23's seven
  readback methods and the absence of their classes' fixture records:
  - `ID=OUTCOME` holds when the ID's record has that outcome and occurs exactly once;
  - `ID=OUTCOME*N` holds when it has that outcome and occurs exactly N times;
  - `ID=missing` holds when no test or fixture record has that ID.

  Each row gives the expected and observed outcome and number of occurrences.
- **`inventory`,** when `--inventory` is given. The document is the output of MH's
  `discover_inventory.py discover` (`ontokin.c271.p35-runtime-discovery/2`, state `COMPLETE`). Its
  IDs are recomputed from `ids_in_discovery_order`. The record lists the started IDs that are not in
  it, its IDs that never started, the IDs started a different number of times, and whether the
  sequence of starts equals the discovery order. This is MC28's "the log against the same list".

**Refusals:** `USAGE`, `OUTPUT`, `PYTHON`, `LOG` (an unreadable or non-canonical log), `DIGEST`,
`FOOTER`, `PARSE` (no complete reading; its `attempts` give `COUNTS`, `LISTING`, `STATUS`,
`AMBIGUOUS` or `ATTRIBUTION` for each possible listing start), `INVENTORY`.

**Exit:** 0 when the log was read completely, every expectation holds and the inventory, if given,
matches; 1 when the log was read but an expectation or the inventory differs; 2 for a refusal; 3 for
an unknown outcome.

**Limits**
- **One unittest version.** It reads CPython 3.12's `TextTestResult` format. Another version's
  format is not established.
- **Contiguous writes.** Each runner write (a start, a status line, a subtest line) is assumed to be
  contiguous in the file. A concurrent writer that splits one makes the log unreadable, and it is
  refused.
- **A status printed right after a start.** A status token that a test writes unbuffered
  immediately after its own start is read as its status. It is refused only when it changes a count
  or a listing entry.
- **Refused, not read:**
  - a subtest message that holds a line end;
  - a docstring line that itself ends in ` ... <status>`;
  - a class-level event written right after an expected failure or an unexpected success, which
    unittest prints without a description (`ATTRIBUTION`);
  - a log with carriage-return line ends, since the footer needs `\n` (a carriage return inside a
    line is kept as text).
- **Exception groups.** Their indented traceback has no unindented exception line, so the first line
  of their reason falls back to the first line of the last block.

## unit_log_outcomes.py compare: the baseline comparison (OK-ENG-009 section 3 item 4)

```
unit_log_outcomes.py compare \
  --baseline-log L --baseline-log-sha256 H --baseline-summary S --baseline-summary-sha256 H [--baseline-tmpdir T ...] \
  --candidate-log L --candidate-log-sha256 H --candidate-summary S --candidate-summary-sha256 H [--candidate-tmpdir T ...] \
  [--attributions A --attributions-sha256 H] --output OUT
```

**Bindings.** Each summary must be an `ontokin.local-checks/0.1` document whose `unit-tests` step
names the given log by its `log_identity` digest (`BINDING` otherwise). Both logs are parsed by the
collector's reader above, and a log that cannot be read refuses the comparison.

**The lists,** per raw test ID and per fixture ID. "Not passing" means failure, error or unexpected
success.

| List | Meaning |
| --- | --- |
| `unchanged` | per outcome, the IDs present in both with the same outcome, the same reasons, the same subtests and the same skip reasons; the not-passing, skipped and expected-failure ones are also listed |
| `new_not_passing` | not passing in the candidate, and passing, skipped, an expected failure or absent in the baseline (TR-04: a skipped or expected-failure baseline entry is also in `different_outcome`) |
| `no_longer_failing` | not passing in the baseline, and passing or absent in the candidate |
| `different_outcome` | present in both with another outcome not covered above, for example skipped and then error, or skipped and then passed |
| `different_reason` | the same outcome, with other reasons or other own events |
| `different_subtests` | the same outcome, with another set of failing or skipped subtests |
| `different_skip_reason`, `different_occurrences` | the same outcome, with another skip reason or another number of runs |
| `added_ids`, `removed_ids` | present on one side only, with the outcome on the other side |

Each entry gives both sides' outcomes, normalized and raw reasons, skip reasons, subtest counts and
`masked_temporary_names`, the temporary names that the normalization replaced in that side's
texts. `exempt` is always empty.

**Normalization (`ontokin.c271.p36-reason-normalization/2`, TR-06).** Reasons and subtest names
are compared after only the run's own paths are replaced, longest first, and only as whole path
components: a path is replaced where it starts the text or follows a delimiter (a space, a quote,
a bracket, `,`, `;`, `:` or `=`), and where it ends the text or is followed by `/` or a delimiter.
A sibling such as `workspace2` beside `workspace` is never taken for it.
- from each run's summary:
  - the driver's interpreter (`environment.python_executable`) becomes `<python>`;
  - the workspace (the unit step's `cwd`) becomes `<workspace>`;
  - the output directory becomes `<output>`;
  - the source root becomes `<source>`;
- from `--*-tmpdir`, each temporary directory of that run:
  - as given, it becomes `<tmp>`;
  - resolved, it becomes `<tmp:resolved>`;
  - for a resolved `/private/...` form, its alias without `/private` becomes `<tmp:alias>`;
  - the component directly below it becomes `*` only when it has `tempfile`'s own name shape,
    `tmp` and eight characters of `[a-z0-9_]`. Any other name stays as it is, so two different
    directories there never compare as equal.

Nothing else changes, and the raw texts stay beside the normalized ones. The freeze states the
temporary directories of each run. Without them, a reason that names a random temporary path
differs from run to run and is listed under `different_reason`. A temporary directory made with
another prefix (`mkdtemp(prefix=...)`) is not masked and shows as a different reason.

**Attributions** (`ontokin.c271.p36-attributions/2`, supplied by the operational freeze; TR-01).
The file is `{"schema", "attributions": [...]}`, one row per exact ID:

```
{"id": "<raw ID>", "form": "raw" | "normalized", "outcome": "error", "occurrences": 1,
 "events": [{"status": "FAIL", "reason_first_line": "AssertionError: ..."}],
 "failing_subtests": [{"subtest": "(fail_after=False)", "status": "ERROR", "reason_first_line": "TypeError: ..."}],
 "skipped_subtests": [], "source": "D-18", "note": "..."}
```

- **The statement is complete.** It gives the test's outcome, its number of occurrences, its own
  events in the order unittest wrote them (a `FAIL` or `ERROR` with its first line, a skip with its
  reason, or a bare status), and its failing and skipped subtests in their order.
- **One declared form.** `form` applies to the whole statement. `raw` compares the texts as read;
  `normalized` compares them after the candidate's declared normalization.
- **Exact equality only.** `matches` is true only when the candidate's record, stated the same
  way, equals the statement exactly. Nothing is matched by containment. `observed` gives the
  candidate's statement, and `differences` lists every field or item that differs
  (`outcome`, `occurrences`, `events[i]`, `failing_subtests[i]`, `skipped_subtests[i]`), or the ID's
  absence.
- **Nothing is exempt.** An attributed entry keeps its place in every list and only gains an
  `attribution` member. Whether a matching attribution is accepted is the R03 review's decision,
  not this tool's.
- **Refused:** revision 1's single-reason form, an incomplete or malformed statement, an undeclared
  form, an unknown outcome, and an ID attributed twice (`ATTRIBUTIONS`).

**The summaries side by side:**
- each step's status, its report outcomes and its pending cases;
- `steps_equal` and `steps_different`;
- `reports_different` (TR-03): every report whose summarized outcomes differ, or that one side
  lacks, with its step, its path and both sides' outcomes;
- the pending external cases as multisets, with the cases found on one side only;
- `not_executed_steps`;
- and, per run, its status, profile, roles, readback selection status and run kind, environment,
  Git head and tree, source inventory digest and count.

`driver_reading_matches_summary` says whether the driver's own reading of each log equals the
`test_execution` that its summary records.

**Refusals:** `USAGE`, `OUTPUT`, `PYTHON`, `SUMMARY`, `LOG`, `DIGEST`, `BINDING`, `ATTRIBUTIONS`, and
those of the reader above.

**Exit:** 0 when every list above is empty, `steps_different` and `reports_different` are empty, and
the pending cases and not-executed steps are equal; 1 when the comparison completed and something
differs; 2 for a refusal; 3 for an unknown outcome.

## readback_evidence.py: the readback evidence reader

**Where the records are.** In the unit stage of a qualifying run:
- the driver passes the derived selection `<output>/readback-binding/selection.json`, which the
  driver derived with the workspace binding;
- the readback class's setup creates the cohort root inside the selection's evidence root:
  - by default `mkdtemp` makes `current-host-cpu-XXXXXXXX`, and `finish_cpu_cohort` copies it to
    `...-preserved-<32 hex>` with `PRESERVATION.json` and `CLEANUP.json`, then removes the
    original;
  - with `STATIC_TRAY_READBACK_CPU_OUTPUT`, the named directory is used and kept in place.

The cohort root holds:
- `setup.pending.json`, `setup.json`, the manifest `supplemental-cpu.json` and `cohort.json`;
- one stage per case (`Q01-positive`, `Q03-positive`, `Q01-changed-reference`), with
  `synthetic.glb`, `synthetic-audit.json`, `job.json`, `probe.json` and the supervisor's
  `synthetic-readback.process.json`, `.stdout.log` and `.stderr.log`;
- one ledger per case under `provider-ledgers/`: `reserved.json`, `preflight.json`,
  `started.json`, `supervisor-outcome.json` and `result.json`.

```
readback_evidence.py run    --summary S --summary-sha256 H --cohort-root C --audit A --audit-sha256 H \
                            --audit-tool-sha256 H --output OUT
readback_evidence.py cohort --cohort-root C --audit A --audit-sha256 H --audit-tool-sha256 H --output OUT
```

**The numerical rows go to MH's harness unchanged.** The cohort root is exactly the layout that
`audit_numeric.py --cohort-root` reads, so no adapter changes MH's file. The Director runs
`python3 -I -S -B <MH tooling>/audit_numeric.py --cohort-root C --output A`. This reader then
requires:
- that A's tool is the file whose SHA-256 `--audit-tool-sha256` gives;
- that A ran with `-B`;
- that it read this cohort root;
- that its twelve input bindings are the bytes this reader found;
- that every case, the negative fixture and the whole audit passed.

**`cohort` checks** (each a named boolean in `checks`; a missing or unreadable file fails its
checks and nothing is inferred from the provider's own flags alone):
- **the tree:**
  - exactly the expected files and directories;
  - no link or special file;
  - no finalization-failure marker;
  - the unused native schedule absent;
- **the preserved route:**
  - `PRESERVATION.json` names this root and lists exactly the retained files with their bytes;
  - `CLEANUP.json` names the original, and the original is absent now;
- **the setup:**
  - schema and identity;
  - passed, qualifying, no start, labels `real` and `qualifying`;
  - it binds the manifest's bytes and observed the boot;
- **the manifest:** it names the cohort root, the schedule root and the setup's selection, and it
  has twelve structural slots;
- **`cohort.json`:**
  - passed, with three starts and the three expected cases;
  - each attempt descriptor binds its `result.json`;
- **for each case:**
  - the result's state: `COMPLETED`, or `SUPERVISOR_REFUSAL` for the negative, with exactly
    `{"code": "OTRAY-E-BACKEND", "reason": "Child exited with status 1", "state": "REJECTED"}`;
  - one expected and one actual start, no provider failure, preflight equal to postflight;
  - labels `real` and `qualifying`, the boot unchanged;
  - the receipt's exit status (0, or 1 for the negative), its cleanup, handles, PID and own group,
    label and cwd;
  - the argv equal to the manifest's template with this job, carrying the selection digest and
    starting the manifest's runtime;
  - the supervisor's receipt file and `supervisor-outcome.json` equal to the ledger;
  - `started.json` is this start (PID, argv, start time) and its PID is positive;
  - `reserved.json` is the initial ledger;
  - the job names its stage and binds its inputs and the manifest;
  - the preflight binds the job, its inputs and the selection;
  - `artifacts_after` equals the retained stage bytes;
  - the report's outcome fits the case;
- **the starts:** a start is established only by a started record with a positive PID (P07 section
  4), and exactly three are required. The record lists each case's PID, group and executable.

**`run` adds the driver run.** The summary, bound by SHA-256, must be qualifying and
`workspace_bound`, with the original selection's digest supplied and observed. Then:
- **the binding directory:** `<output>/readback-binding/` holds exactly its four files;
- **the summary's `derived` member:**
  - it names the binding's `selection.json` and `workspace-binding.json` by path and digest;
  - its parent digest is the original's;
- **the derived selection:**
  - its parent names the original selection, whose file still has those bytes;
  - it binds the workspace binding;
  - its source root is the workspace, inside whose evidence root the output lies;
- **the workspace binding:**
  - its roles are the workspace, the source root, the commit and tree of the summary's Git record,
    and the workspace's provider and probe;
  - it binds the binding's two inventory files;
- **the inventories:** the provider's two inventories equal the driver's `source-before.json`, which
  is the summary's source inventory;
- **the unit step:** it was started with the derived selection's path and digest,
  `PYTHONNOUSERSITE=1` and `PYTHONDONTWRITEBYTECODE=1`;
- **the links to the cohort:**
  - the cohort's setup names the derived selection and the workspace;
  - the cohort, and its original root, lie inside the evidence root;
  - every attempt's source is the selection's source;
  - the manifest's probe is the workspace's probe.

**Refusals:** `USAGE`, `OUTPUT`, `PYTHON`, `SUMMARY`, `COHORT`, `AUDIT`, `BINDING`, `DIGEST`.

**Exit:** 0 when every check passes; 1 when a check fails; 2 for a refusal; 3 for an unknown
outcome.

**What it does not establish**
- It recomputes no numerical row; MH's harness does.
- It does not re-verify the provider's own HOST, dependency or source checks.
- It sees no start that leaves no started record. The audit hook, MC11's scan and the freeze's
  start accounting cover those routes.
- It reads the records after the run; it cannot show that nothing was written and removed during
  the run.

## Reused from MH, unchanged

These files are bound by digest exactly as they are at the worktree's commit. The same digests
appear in MH's `../../macos-qualification-p35/authoring/TOOLING-SHA256SUMS.txt` and in
`../../macos-qualification-p35/plans/freeze-002/FREEZE-002.json`. A needed change would be a new
tool in this directory, never an edit of MH's file.

| Role | Path (in the worktree) | SHA-256 | Bytes | Mode |
| --- | --- | --- | ---: | --- |
| The failure-capture procedure | `docs/engineering/localized-repair-c271/macos-qualification-p35/tooling/FAILURE-CAPTURE.md` | `f387fb3ec0ed306366f6d3f22820ec344f1ac843008775475258c5de9634c99c` | 13147 | 0o644 |
| Its own probe tool, which the procedure binds | `docs/engineering/localized-repair-c271/macos-qualification-p35/tooling/capture_probe.py` | `db5fb5250909effa7e3fe3d66feadc5183160b4e6088178a763e6fc41567048f` | 29076 | 0o644 |
| The runtime-discovery collector (MC28) | `docs/engineering/localized-repair-c271/macos-qualification-p35/tooling/discover_inventory.py` | `980c80883f3106706a3ecd3b03e908efe31a5c572a67a0d71dc650f85cfb695e` | 35270 | 0o644 |
| The numerical-audit harness | `docs/engineering/localized-repair-c271/macos-qualification-p35/tooling/audit_numeric.py` | `9140379c61bc70f29939bd7b216ef5ca5e2f5e6cab5b4a452e50018651bac4e3` | 40667 | 0o644 |

How each fits MR:
- `discover_inventory.py discover` and `compare` work at B unchanged, with MH's frozen-environment
  rules.
- `collect --inventory` joins a discovery document with R1's log.
- `audit_numeric.py` reads a driver run's cohort root unchanged.

## Tests

```
python3 -I -S -B -m unittest discover -s tests -v
```

Run from this directory with the framework interpreter. `-B` is required.
`W2_TOOLING_UNDER_TEST=<directory>` runs the same tests against another copy of the tools; against
revision 1, a test writes an attribution in that revision's only form, so that each test of a fix
fails on what the fix changes.

**Where the suite was run (TR-07).** For revision 2 the suite was run:
- from W2's tooling directory beside the clone;
- from a copy at the committed place, `docs/engineering/localized-repair-c271/macos-routine-p36/tooling/`
  inside a tree laid out as the worktree, under the phase's worker directory;
- once against a copy of the rejected revision 1, where each new test for TR-01 to TR-06 fails.

The hygiene test's outcome does not depend on where the checkout lies or on this host's
interpreter prefix. It treats the project's task, phase and worker names (C271, C271-P36, W2,
W3-tooling-001) as public vocabulary, and it searches every other component of the directories
above the tooling.

**What the tests do**
- **No process.** The tests start no process: each tool is loaded from its file and its `main()`
  runs in the test process. An audit hook counts every process-creation event, and the last test
  requires zero.
- **Real unittest output.** The synthetic logs are written by the interpreter's own
  `unittest.TextTestRunner` at verbosity 2, so their format is unittest's own. They cover:
  - every outcome kind;
  - docstring lines;
  - failing, erroring and skipped subtests;
  - several events of one test;
  - chained and multi-line reasons;
  - `setUpClass`, `tearDownClass`, `setUpModule`, class skips, and failed imports of a flat and of
    a dotted module name;
  - repeated IDs, expectations of absence and of a number of occurrences, and the driver's
    reading of a carriage return.
- **Interleaved text.** Text written into the same stream stands for the output of tests and
  children: full lines, partial lines glued to statuses and starts, warning-like lines, footer-like
  and header-like text, and trailing text. Two candidates after a start refuse, whatever their
  values.
- **Refusals.** Handwritten logs cover ambiguity, truncation at several points, count, footer,
  listing, digest, usage, output and path refusals.
- **The comparator** is tested on two runs that differ in every way item 4 names. The tests also
  cover the normalization (tempfile's name shape only, component boundaries, the masked names),
  complete attributions (an exact two-part match and every kind of mismatch), pending cases, step
  statuses, report summaries, bindings, and an ordinary run whose readback class fails at setup
  where the baseline skipped it.
- **W3's probes of review 001** (PR-1 to PR-8) are tests here, each named for its finding.
- **The reader** is tested on consistent synthetic provider records of a qualifying driver run, by
  both routes, and on mutations of starts, attempts, stages, links, the audit and the driver run.
- **The hygiene test** derives the private strings of the machine at run time and also searches
  joined string literals. No file holds them, and a failure names only the file and the kind.
- **No test skips.**
