# Author notes: gate MR tooling (S3)

W2, the independent author of C271-P36's observational tooling, for Director
`c271-p36-14f7f8b219db`. These are the notes for the tooling review (W3). Sections 1 to 7 are
revision 1's notes, with two statements corrected in place for TR-05 (marked). Section 8 is
revision 2: what tooling review 001 found, what changed, which test shows it, and every start.
Machine paths are written as labels:
- `<worktree>`: the C271 worktree, read only, said to be clean at
  `d3b622d61745259c3477bc94be0fb4da05c23c56` (W2 started no Git, so this is the brief's statement);
- `<local>`: the places beside the clone;
- `<W2>`: `<local>/c271-p36/workers/W2`;
- `<home>` and `<tmp>`: the home directory and the temporary directory.

## 1. What was delivered

| Path under `<W2>` | What |
| --- | --- |
| `tooling/unit_log_outcomes.py` | the unit-log outcome collector (`collect`) and the baseline comparator (`compare`), one parser |
| `tooling/readback_evidence.py` | the readback evidence reader (`run`, `cohort`) |
| `tooling/README.md` | each tool's command line, checks, refusals, exit codes and limits, and the reuse table of MH's tools |
| `tooling/tests/` | 68 focused tests: `w2_support.py`, `test_collect.py`, `test_compare.py`, `test_readback_evidence.py`, `test_zz_hygiene.py` |
| `test-runs/` | the recorded test run (`TEST-RUN.txt`, its exit code, `TEST-RUN-COMMAND.json` with the tooling digests), and the collector's reading of that log (`TEST-RUN.outcomes.json`) |
| `validation/run-002/` | the validation runs on the retained runs (`RUN.json`, `outputs/`), the check against the records (`CHECK.json`) and the list-digest attempt; `validation/scripts/` holds the three scripts; `validation/run-001-superseded/` is an earlier run made with earlier tool bytes, kept and not cited |
| `work/` | exploration scripts and intermediate outputs, kept as they are; not cited |
| `rejected-001/` | revision 2: revision 1 exactly as review 001 checked it (`tooling/` and that `SHA256SUMS.txt`), unchanged since the copy |
| `committed-place-copy/` | revision 2: a byte-equal copy of revision 2's tooling at its committed place in a tree laid out as the worktree, run there (TR-07) |
| `test-runs/r2/` | revision 2: the three recorded suite runs, their commands and digests (`TEST-RUNS.json`), the copy of rejected-001 they ran against, and the analysis of that run |
| `validation/run-003/`, `validation/scripts-003/` | revision 2: validation run-003 and the revised scripts that made it; `validation/scripts/` and `run-002` stay as they were; `RUNNER-REFUSAL-CHECK.*` shows the new runner refusing an absent parent |
| `SHA256SUMS.txt` | the SHA-256 of every other file under `<W2>` |

The files meant for the repository are those under `tooling/`. They would go to
`<worktree>/docs/engineering/localized-repair-c271/macos-routine-p36/tooling/`. Everything else
under `<W2>` holds machine paths in its raw records, so it is not portable as it is.

## 2. Design decisions

**D-1. One parser for the collector and the comparator.** The comparator takes raw logs and
summaries, as the brief says, and must not trust a collector record (MH's TR-07). It therefore
parses both logs itself with the collector's reader. Putting both commands in one file means the
plan binds one tool and the two readings cannot diverge. The readback reader is a separate file:
it shares no code with the other one, and copying the common helpers is MH's convention.

**D-2. The log is read as unittest 3.12 writes it.** I read `unittest/runner.py`, `case.py`,
`suite.py`, `loader.py`, `result.py` and `util.py` of the framework interpreter (CPython 3.12.13).
The reader emulates `TextTestResult._newline`. Four facts of that implementation shape it:
- `expected failure` and `unexpected success` are written with `writeln`, so `_newline` stays
  unset after them;
- after a failing or skipped subtest, the test's own status repeats its description, or there is
  no own status at all;
- a test can have several events (a failure, then a tearDown error);
- class-level and module-level events are `_ErrorHolder` lines (`setUpClass (module.Class) ...
  ERROR`).

Everything else in the file is noise: stdout is block-buffered in the driver's log, stderr is
line-buffered, and children write directly.

The retained logs show the real cases:
- docstring lines (dozens per run);
- subtest lines (about 190 per default run);
- a `DeprecationWarning` and a forked child's line between a start and its `ok`;
- blocks of printed lines between tests.

**D-3. A status that does not follow its start is planned once** (corrected in revision 2, TR-05).
The candidates are the lines up to the next runner line: lines that are a status, and lines that
end with one (glued after noise). A following subtest line means that there is no direct status.
Revision 1 preferred an exact candidate and refused only candidates of different values within a
kind. It claimed that a wrong choice that changes a value is caught by the global checks. That
does not hold for statuses without a listing entry (`ok`, a skip, an expected failure) or for a
skip reason: W3's probe PR-3 swapped a skipped and a passing test, and replaced a skip reason, and
both logs were read "completely". Revision 2 refuses (`AMBIGUOUS`) any window with two or more
candidates, whatever their values. None of the 130 real logs that W3 read has such a window, and
none of the retained logs here does (run-003).

**D-4. The listing split must be unique.** The expected headers come from the progress section. The
line-anchored occurrences of all of them, in order of position, must be exactly the expected
sequence, starting at the first byte. So a traceback that quotes another expected header refuses
(tested). Where the listing starts is tried at each empty line followed by a separator and an
`ERROR:`/`FAIL:`/`UNEXPECTED SUCCESS:` header, and the first complete, consistent reading wins.
When none works, the refusal lists each attempt's rule.

**D-5. The first line of a reason** is the first line of the exception text of the chain's last
block. For a chained error this is the error that was raised (the earlier blocks' first lines are
kept in `chain_first_lines`). For a failed import it is unittest's own
`ImportError: Failed to import test module: <name>`. The migration's records use the same lines
(for example `prototypes.static_tray_admission_c201.schedule.LedgerError: Directory aliases and
missing ancestors are forbidden`).

**D-6. One record per raw test ID, with every run and event.** A combined `outcome` is computed
for the comparison: error, then failure, then unexpected success, then expected failure, then
skipped, then passed. Nothing is lost by it, because `runs` keeps each occurrence and each event.

Fixture IDs are unittest's own `_ErrorHolder` descriptions. This matters for R2: there, main's three
skipped readback tests become one `setUpClass (test_static_tray_readback_v01.ReadbackCPUControls)`
error, and the three test IDs are absent. The comparator lists the fixture under `added_ids` and
`new_not_passing`, and the three tests under `removed_ids` with their baseline outcome `skipped`
(tested).

**D-7. The item-4 categories** are defined in the README's table. Two choices need the review's
eye:
- `new_not_passing` includes an added ID that does not pass, and `no_longer_failing` includes a
  removed ID that did not pass. Such an ID is also in `added_ids` or `removed_ids`.
- Skipped and expected-failure outcomes are neither passing nor not passing: a change from or to
  them is a `different_outcome`. R1's three readback tests, skipped in main and passing in R1,
  appear there.

`exempt` is always empty, and an attribution only adds `attribution: {matches, source}` to an entry
that stays in its list.

**D-8. The normalization is declared, versioned and limited to the run's own paths.** Without it the
default pair shows three different reasons. All three are random `tempfile` names under the same
per-user temporary directory, and one also names the run's interpreter. The migration's record
says "machine paths replaced by labels". The rule replaces:
- the summary's interpreter, workspace, output directory and source root;
- the temporary directories that the command line gives for each run, with the one component
  below them.

The raw first lines stay beside the normalized ones in every entry. The comparison without
temporary directories was run and kept as evidence (`compare-*-without-temporary-directories`).

**D-9. The summary names its log.** The comparator refuses a log whose digest is not the
`unit-tests` step's `log_identity`. It also records whether `tools/check_local.py`'s own regular
expressions read the same counts from the log as the summary's `test_execution`.

**D-10. MC28's second half.** "R1's log against the same list" needed a join that no tool had. An
untracked harness is not admitted (P07 section 3). So `collect --inventory` takes MH's discovery
document unchanged, bound by digest. It recomputes the IDs and lists every difference, including
order. MH's `discover_inventory.py` is not changed.

**D-11. The reader takes the cohort root explicitly.** The provider makes the cohort root in one of
two ways:
- by default, `mkdtemp(prefix="current-host-cpu-", dir=<evidence root>)`, preserved as
  `...-preserved-<32 hex>` after the cohort, with the original removed;
- with `STATIC_TRAY_READBACK_CPU_OUTPUT`, a named directory kept in place.

In both cases the root lies in the selection's evidence root, which is an ancestor of the driver
output, not inside it. The reader does not search the evidence root. The freeze names the root,
and the reader checks every link to the driver run (§4, Q-2).

The cohort layout is exactly the one `audit_numeric.py --cohort-root` reads, so the harness needs
no adapter. The reader joins its record by digest: the harness file, the cohort root, the twelve
input bindings and the verdict.

**D-12. No process, `-B` first.** Neither tool imports `subprocess`. Each one checks
`sys.flags.dont_write_bytecode` right after `import sys`, before any other import (MH's TR2-05), and
refuses without `-B`.

**D-13. The tests are real unittest output, in process.** The synthetic logs are written by the
running interpreter's `TextTestRunner`, so their format cannot drift from unittest's. Text
written into the same stream stands for the noise. The tools' `main()` runs in the test process. An
audit hook counts process-creation events: the recorded run had zero. No test skips.

## 3. Validation on the retained runs (`validation/run-002/`)

**Inputs.**
- The four retained runs (main `8e847c15` resolved and default, baseline `6b346b1e` default and
  resolved). Their logs and summaries equal the digests and sizes in `BASELINE-CHECKS.json` and
  `INTEGRATION.json`.
- The frozen candidate `16c83df5`'s two runs, which equal `CANDIDATE-CHECKS.json`.
- The other retained candidate logs, bound by the digests computed at the run, since no record
  names them.

**Commands.** 28 tool commands, each `python3 -I -S -B <tool> ...` started by `run_validation.py`,
with argv, exit code, duration, stderr and output digest in `RUN.json`. `check_recorded.py` then
compared the outputs with the records: **83 items, 0 disagreements** (`CHECK.json`).

**Results**
- **6b346b1e resolved against 8e847c15 resolved:**
  - unchanged not passing: 1;
  - `new_not_passing`, `no_longer_failing`, `different_outcome`, `different_reason` and
    `different_subtests` are all empty;
  - 4,740 then 4,989 tests;
  - the steps equal except `documents`, failed then passed;
  - the pending cases and the skips equal.

  This is the record exactly. The record does not state the 249 added IDs, all passed; there are no
  removed IDs.
- **6b346b1e default against 8e847c15 default:** unchanged not passing 307 (230 errors and 77
  failures), and every other field as in the resolved pair, as recorded.
- **6b346b1e against the candidate 16c83df5:** the same, as `CANDIDATE-CHECKS.json` records.
- **The baseline's own lists in `BASELINE-CHECKS.json`.** For both runs these agree with the
  collector, item by item:
  - `ran`, the result and its detail (`failures=103, errors=311, skipped=3`; `failures=1,
    skipped=3`);
  - `distinct_not_passing` (307; 1);
  - the three skipped tests with their reasons;
  - `not_passing_by_module`;
  - every recorded not-passing test, with its number of subtests and its reason (the record's
    `'...'` and `<tmp>/*` forms read as patterns over the raw first lines);
  - no not-passing test missing from the record.
- **`list_digest_default_run` (307, `2681454e...`): its method is not established.** The program
  that made it is not in the repository or beside the clone. A declared grid of 8,640 encodings did
  not reproduce it. The grid varies the record's or the normalized reasons, five outcome forms, two
  ID forms, scalar or list reasons, three containers, three orders, eight JSON forms and a trailing
  line end (`LIST-DIGEST-ATTEMPT.json`). The record says the candidate's and main's lists give one
  digest, and the normalized 307-entry lists of the two runs are equal. The comparison rests on the
  item-by-item lists, not on that digest.
- **The other candidate logs.** Each of the 13 complete ones was read completely, with counts equal
  to its footer. The two logs of the runs stopped at `02797bb0` (`STOPPED.txt`) were refused with
  `FOOTER`, as they must be.
- **MH's real retained cohort** (`<local>/c271-p35/evidence/s7-001-cohort/run`, the kept-in-place
  route), read with `readback_evidence.py cohort` and MH's own audit record:
  - all 144 checks passed;
  - three starts were established (PIDs 33806, 33835 and 33862);
  - the audit's tool digest is `9140379c...`, MH's file.
- **The recorded test run's own log** was read by the collector as 68 passed. In that log the
  hygiene test's stderr line lies between a start and its `ok`.

## 4. Open questions for the operational freeze

- **Q-1. Temporary directories.** The freeze must state, for each run that the comparator reads,
  the temporary directory forms to give as `--baseline-tmpdir` and `--candidate-tmpdir`:
  - R1's resolved directory;
  - R2's default `/var/...` form;
  - main's resolved-directory run: the resolved form;
  - main's default-directory run: the per-user default.

  It must also state that the comparison is made with the normalization `.../1` and nothing else.
- **Q-2. R1's cohort route and root.**
  - **Default route.** The preserved root's name is known only after R1, so the freeze must say how
    it is identified, for example: exactly one `current-host-cpu-*-preserved-*` in the evidence
    root, and no other `current-host-cpu-*` entry.
  - **Override route** (`STATIC_TRAY_READBACK_CPU_OUTPUT` set for the driver, which passes it
    through: it is not in `UNIT_REMOVED_ENVIRONMENT`). The root is fixed before R1. W1's inventory
    should confirm what else reads that variable.

  Either way, the reader then takes it with `--cohort-root`.
- **Q-3. The audit run.** `audit_numeric.py --cohort-root <root> --output <absent path>` is one more
  start of the framework interpreter with `-I -S -B`, after R1. The freeze lists it with its output
  path and with the reader's run that joins it.
- **Q-4. Attributions.** D-18's two failing 0.1.0 driver tests need their exact IDs, their outcome
  and the first line of their reason before R1 and R2 run. A reason that names a run path must be
  written in its normalized form with the declared labels. For MC22 on R2, the freeze can attribute
  `setUpClass (test_static_tray_readback_v01.ReadbackCPUControls)` as `error` with its fixed reason;
  `collect --expect` checks the outcome only.
- **Q-5. MC23.** The seven readback methods can be stated as `collect --expect <exact ID>=passed`.
  The IDs carry discovery's `test_static_tray_readback_v01.` prefix, and the freeze must check that
  no fixture record of the two readback classes exists.
- **Q-6. Not done here** (closed in revision 2: the Director established it with Git, review 001's
  TR-10 and its disposition). MR-PLAN section 1 says "W2 confirms" that main changed no file under
  `tests/`, `tools/`, `ontokin/`, `prototypes/`, `fixtures/`, `schemas/` or `examples/` from
  `8e847c15` to `51223c9b`, and the documents that the `documents` stage reads. My brief for S3 was
  the tooling, and I was not to start Git, so I did not establish it. A Git-free way, for S4: the
  Director exports `51223c9b`'s inventory, and it is compared with the retained
  `source-before.json` of the `8e847c15` runs, which the comparator already binds by the summary.
- **Q-7. Exit codes.** For R1 and R2 the comparator will exit 1, because of the added IDs, S8's
  changes and D-18. The freeze's checker steps should read the record's lists, not only the exit
  code.
- **Q-8. A refusal of R1's log.** If R1's log is refused (for example, a test's output imitates a
  runner line), that is a finding of the tooling, not of the tests. The raw log is kept, and a
  corrected collector is a new tool, reviewed again. No such case occurred in the 19 complete
  retained logs read here; the 2 stopped ones were refused for their missing footer, as they must
  be.

## 5. Every start I made

Bash tool calls: 59. Each started the tool's shell; what that shell's profile starts was not
observed.

| Program | Starts | Notes |
| --- | ---: | --- |
| framework interpreter (`python3` on `PATH`), started directly | 83 | always `-I -S -B` |
| framework interpreter, started by `validation/scripts/run_validation.py` | 37 | `-I -S -B` (9 in run-001, 28 in run-002), with the environment `PATH`, `LANG`, `LC_ALL` and `TZ` |
| `ls` | 1 | **deviation**: one `ls -la` of a worktree documentation directory, by mistake, piped into the next |
| `head` | 2 | **deviation**: once as above (it failed on its argument), once to shorten a refusal record printed on stderr |
| Node, Git, `ldd`, `codesign`, the observer, `tools/check_local.py`, the unit suite | 0 | |

- **The test runs.** Within the 83 direct starts there were eight iteration runs of the focused
  tests and one recorded run. No test started a child (audit hook: zero events in the recorded
  run).
- **The last start** scans these notes and `tooling/` with the hygiene test's own derivation of the
  machine's private strings, then writes `SHA256SUMS.txt`.
- **The deviations.** Neither `ls` nor `head` wrote anything. After the second one, every command
  started only the framework interpreter.
- **Writes.** Only under `<W2>`. The agent harness itself saved two oversized command outputs in its
  own session directory under `<home>`; that was not a start of mine.

## 6. What I read

- **The brief's read set at the worktree:**
  - `AGENTS.md` (byte-equal to the copy loaded in the session), `ROLE.md`,
    `docs/workflow/PROTOCOL.md` (all), `docs/workflow/templates/WORKER.md`;
  - `MR-PLAN.md` and `PHASE.json`;
  - OK-ENG-009;
  - `tools/check_local.py` (all);
  - the readback provider `current_host_readback_v02.py` (header, I/O helpers, selection,
    workspace derivation, manifest, job, `guarded_run_process`, cohort setup and accounting) and
    its facade `current_host_readback_v01.py` (the 0.2.0 dispatch);
  - `supervisor_darwin_v01.py` (`run_process`) and `supervisor.py` (`Stop`, `Clock`);
  - `tests/test_static_tray_readback_v01.py`.
- **MH's tooling:** `README.md`, `audit_numeric.py` (all), `collect_outcomes.py` (to line 650),
  `tests/test_zz_hygiene.py` and `tests/mh_support.py` (the start).
- **MH's reviews:** the findings of `TOOLING-REVIEW-001`, `-002` and `-003` (their JSON form: all
  titles, and the text of TR-01, TR-03, TR-04, TR-07, TR-17, TR-18, TR2-02, TR2-05 and TR3-01). I did
  not read the disposition files or the Markdown forms.
- **MH's other records:** I searched `authoring/TOOLING-SHA256SUMS.txt` and `FREEZE-002.json` for
  the reused tools' digests.
- **Not read in full, reused unchanged:** `FAILURE-CAPTURE.md`, `capture_probe.py` and
  `discover_inventory.py`. Their binding is MH's, accepted by MH's tooling review 003.
- **Beside the clone:**
  - the retained runs' logs and summaries;
  - MH's retained cohort, its audit record and its discovery documents (their shape);
  - the migration records `BASELINE-CHECKS.json`, `INTEGRATION.json` and `CANDIDATE-CHECKS.json`.
- **Not opened:** nothing under `<local>/c271-macos/` was opened. The provider records name paths
  there, and the reader only compares those names.

## 7. Limits

**The collector**
- **One unittest version.** It is written for CPython 3.12's `TextTestResult` and was validated on
  3.12.13 logs. Another version's format is not established.
- **Contiguous writes.** It assumes that each runner write (`<description> ... `, a status line, a
  subtest line) is contiguous in the file. A concurrent writer that splits one would make the log
  unreadable, and it would then be refused.
- **Imitations** (corrected in revision 2, TR-05). Output that imitates a runner line can make a log
  unreadable, and it is then refused (tested). Revision 1's statement that it "can be misread only
  if the imitation changes no value and no count" did not hold (W3's PR-3). Revision 2 refuses
  every status window with two or more candidates. One case remains: a status token that a test
  writes, unbuffered, immediately after its own start is read as its status. It is caught when it
  changes a count or a listing entry, and not when it changes neither, for example a printed skip
  with another reason before a real skip. Two further cases are refused, not handled:
  - a subtest message with a line end;
  - a docstring line that ends in ` ... <status>`.
- **Unlabelled events.** A class-level event written right after an expected failure or an
  unexpected success has no description in unittest's output, and it is refused (`ATTRIBUTION`).
- **Exception groups.** Their indented traceback has no unindented exception line, so the first
  line of their reason falls back to the first line of the last block.

**The comparator**
- **The normalization** covers only the run's own paths. A reason that differs in another
  run-specific way (a PID, a time) is listed as different.
- **Duplicate IDs.** Run twice in a row with a failure status, a repeated description can be read as
  a second event of the first run. The counts check then refuses the log.

**The reader**
- **Real records.** It was validated on real provider records in `cohort` mode only, on MH's
  kept-in-place cohort. `run` mode and the preserved route rest on synthetic records, because no
  qualifying driver run exists yet.
- **Out of scope.** It recomputes no numerical row and repeats no provider check of HOST,
  dependencies or source.

**These notes** have been checked for private strings by the same derivation as the hygiene test
(see the last start).

## 8. Revision 2: tooling review 001 and its disposition

Review 001 (W3, a fresh agent) returned `REJECT_WITH_MANDATORY_FINDINGS`: TR-01 mandatory, TR-02 to
TR-11 not. I followed the Director's disposition (`TOOLING-REVIEW-DISPOSITION-001.json`, SHA-256
`0271f996…`, checked before use), which governs where it and the review differ.

### 8.1 What changed

| File under `tooling/` | Revision 1 | Revision 2 |
| --- | --- | --- |
| `unit_log_outcomes.py` | `462022b5…` | `0b526940…` (85,540 bytes) |
| `README.md` | `eada0ba9…` | `c96faa07…` (29,824 bytes) |
| `tests/w2_support.py` | `5e68c93e…` | `741800d0…` |
| `tests/test_collect.py` | `2335946e…` | `21cfd2b9…` |
| `tests/test_compare.py` | `66296e0b…` | `e0e7627a…` |
| `tests/test_zz_hygiene.py` | `1594d614…` | `585a7bf1…` |
| `readback_evidence.py`, `tests/test_readback_evidence.py` | `ad47b993…`, `3c1350b2…` | unchanged |

Revision 1 is kept unchanged in `rejected-001/` with the `SHA256SUMS.txt` that review 001 checked
(`c7ec20ca…`). The output schemas are now `unit-log-outcomes/2`, `unit-log-comparison/2`,
`attributions/2` and `reason-normalization/2`.

### 8.2 Each finding, its change and its test

The tests named `test_trNN_` are the tests of each fix. In the run against a copy of rejected-001,
**all 18 of them for TR-01 to TR-06 fail**, each for the defect it targets (the analysis lists each
with its first line: `test-runs/r2/AGAINST-REJECTED-001-ANALYSIS.json`).

| Finding | Change | Tests (class.method) | Against rejected-001 |
| --- | --- | --- | --- |
| TR-01 (mandatory) | An attribution (`attributions/2`) states the complete not-passing record: outcome, occurrences, own events in order (status with first line or skip reason), failing and skipped subtests in order, in one declared `form` (`raw` or `normalized`) that applies to the whole record. `matches` only on exact equality; `observed` gives the candidate's statement and `differences` every differing field or item, or the ID's absence. Revision 1's single-reason form is refused. README rewritten. | `Attributions.test_tr01_`: an exact two-part statement (erroring subtest plus own failure) matches; a changed subtest reason, an added subtest, an added own event, a removed own event, a changed outcome, W3's PR-5 (changed subtest reason plus an extra erroring subtest), an absent ID, and the declared form, each does not match with its exact differences; `test_malformed_attributions_refuse` | all 9 fail: `matches` true by containment (4), the declared form ignored, so both forms match (1), or no `observed` or `differences`, which revision 1 cannot give (4) |
| TR-02 | `--expect ID=missing`, and `ID=OUTCOME` holds only for exactly one occurrence, `ID=OUTCOME*N` for N; each row gives expected and observed occurrences. | `Expectations.test_tr02_probe_pr1_a_fixture_record_that_must_be_absent` (W3's PR-1), `test_tr02_probe_pr2_an_id_that_starts_twice_does_not_meet_a_single_expectation` (PR-2); `test_malformed_expectations_refuse` | both fail: `=missing` is refused; a twice-run ID meets `=passed` |
| TR-03 | `summaries.reports_different` (step, report path, both outcomes, presence), part of the exit predicate. | `Probes.test_tr03_probe_pr7_a_report_summary_that_differs_with_equal_statuses` (PR-7); `reports_different == []` added to two existing tests | fails: exit 0, no list |
| TR-04 | Skipped or an expected failure in the baseline and not passing in the candidate: in `new_not_passing` as well as `different_outcome`. | `Probes.test_tr04_probe_pr8_a_skipped_baseline_test_that_errors_is_newly_not_passing` (PR-8), `test_tr04_an_expected_failure_that_now_fails_is_newly_not_passing`; the category test now expects it | both fail: `new_not_passing` empty |
| TR-05 | Two or more status candidates after a start refuse (`AMBIGUOUS`), whatever their values; the module docstring, the README, the record's `limits` and D-3 and section 7 here are corrected. | `InterleavedOutput.test_tr05_two_candidates_after_a_start_refuse_even_when_they_agree`, `test_tr05_probe_pr3_printed_imitations_that_keep_every_count_are_refused` (PR-3, PR-3b) | both fail: read as `PARSED` |
| TR-06 | `reason-normalization/2`: run paths only at component boundaries; below a temporary directory only `tmp` plus eight characters of `[a-z0-9_]` (tempfile's default name) becomes `*`; each entry records `masked_temporary_names`. | `Probes.test_tr06_probe_pr6_a_non_random_name_below_the_temporary_directory_is_not_masked` (PR-6), `test_tr06_a_run_path_is_replaced_only_at_component_boundaries`; masked names asserted in the normalization test | both fail: masked as unchanged; replaced as a substring |
| TR-07 | The hygiene test treats the task, phase and worker names as public vocabulary, and no longer requires a component of the interpreter prefix; README says where the suite ran. | `Hygiene.test_tr07_the_projects_own_names_are_public_wherever_the_checkout_lies`; the suite passes at a committed-place copy (90 OK) | passes (test-side change) |
| TR-08 | The parser accepts the dotted module name of the loader's `_FailedTest` and `ModuleSkipped`, and `special` is set for it; README says so. | `LoaderTests.test_tr08_probe_pr4_a_failed_import_inside_a_test_package_is_read` (PR-4) | fails: the dotted name is refused |
| TR-09 | README's binding rule corrected: the cohort root's files are cross-checked and recorded in `cohort_bindings`, not bound by a supplied digest; the freeze binds them. | none (documentation) | n/a |
| TR-10 | None: the Director established main's change with Git (disposition). My Q-6 is closed by it. | none | n/a |
| TR-11 | `driver_reading` decodes as the driver does (universal newlines) and gives `equals_footer`. | `DriverReading.test_tr11_the_drivers_reading_translates_line_ends_as_the_driver_does` | fails: 14 read where the driver reads 9 |

### 8.3 Runs

- **From `<W2>/tooling`:** 90 tests, OK, no skip, 0 process-creation events.
- **At the committed place**
  (`<W2>/committed-place-copy/worktree/docs/engineering/localized-repair-c271/macos-routine-p36/tooling/`,
  a byte-equal copy): 90 tests, OK. The hygiene test derives the checkout's parent there, and passes.
- **The real worktree's place.** The last start also scans the tooling with the strings that the
  hygiene test derives for the real committed place in `<worktree>`, without writing there.
- **Against a copy of rejected-001** (`W2_TOOLING_UNDER_TEST`): 90 tests, FAILED (failures=18,
  errors=8):
  - every one of the 18 `test_tr01_` to `test_tr06_` tests fails, as above;
  - 7 other tests fail: TR-08's and TR-11's, and five that assert revision 2's new fields or lists;
  - the 25 failing tests give 26 entries, because one TR-05 test fails in both of its subtests.
- **Validation run-003** (`validation/scripts-003/run_validation.py`, 28 tool commands):
  - **The record:** 91 items, 0 disagreements with BASELINE-CHECKS.json, INTEGRATION.json and
    CANDIDATE-CHECKS.json, as in run-002. Resolved pair: 1 unchanged not passing. Default pair: 307.
    Every item-4 list is empty.
  - **The exit codes** are the same as run-002's.
  - **TR-03:** `reports_different` is empty.
  - **TR-05:** no retained log is refused as ambiguous. The 19 complete logs read completely; the 2
    stopped ones are refused by their footer.
  - **TR-11:** the driver's reading equals the footer in every log.
  - **TR-06:** the mask replaced six names, all of tempfile's shape, in exactly the three default
    reasons that W3 found.
  - **`list_digest_default_run`:** still not established.
- **The new runner** creates its run directory itself or refuses: `RUNNER-REFUSAL-CHECK.*` shows
  exit 2, one line, nothing started or written, for an absent parent.

### 8.4 Findings adopted with a different detail, and not adopted

- **TR-06, the mask's shape.** The review allowed "a prefix plus eight characters". I mask only
  tempfile's default prefix `tmp` plus eight characters. With an arbitrary prefix, almost any long
  lower-case name would match: `a-differently-named-directory` ends in eight such characters. So a
  directory made with `mkdtemp(prefix=...)` is not masked and shows as a different reason. The
  README states this. On the retained runs only default names occur.
- **TR-01, where the form is declared.** `form` is declared per attribution, for its whole record,
  not once per file. The disposition asks for "one declared form" per statement, and the freeze may
  need `raw` for one test and `normalized` for another.
- **TR-02.** Adopted both ways that the disposition allows: exactly one occurrence for `ID=OUTCOME`,
  and an explicit count `ID=OUTCOME*N`.
- **TR-07.** I could not run the suite inside the real worktree, since I write only under `<W2>`. I
  ran it at a byte-equal copy in a tree laid out as the worktree, and scanned the files with the
  strings derived for the real committed place.
- **TR-05, one remaining case.** A token printed unbuffered right after the start is still read as
  the status (README limits).
- **Not adopted:** nothing.

### 8.5 Every start in revision 2

**Bash tool calls:** 16, each starting the tool's shell. No shell utility was started: only builtins
(`cd`, `echo`) and redirections.

| Program | Starts | Notes |
| --- | ---: | --- |
| framework interpreter, started directly | 26 | always `-I -S -B` |
| framework interpreter, started by `validation/scripts-003/run_validation.py` | 28 | run-003's tool commands, `-I -S -B` |
| any other program | 0 | |

- **What the direct starts were:** the suite runs (three iteration runs and three recorded runs),
  the analysis of the run against rejected-001, the runner's refusal check (which started nothing),
  run-003 with its check and its digest attempt, copies, record writes, the digest checks, and the
  last start for the scan and `SHA256SUMS.txt`.
- **Not started:** Git, Node, `ldd`, `codesign`, `otool`, the observer, `tools/check_local.py`, the
  repository's unit tests and child agents.
- **Writes:** only under `<W2>`.
- **Revision 1's starts** are in section 5.
