# Tooling review 002: gate MR observational tooling, revision 2 (C271-P36, stage S3)

**Verdict: ACCEPT_WITH_NONMANDATORY_FINDINGS.** Revision 2 meets TR-01 to TR-11 as the disposition
requires them. The four details that W2 reports as different are each sound (section 2). No finding
is mandatory, so this tooling can be committed and then bound by the operational freeze. Five
findings are nonmandatory (TR2-01 to TR2-05, section 4). None of them affects MR's comparisons:
- R1 and R2 are expected to report no skip and no expected failure;
- the baseline logs are fixed bytes, and I checked them.

**TR-01**, the mandatory finding of review 001, is resolved:
- an attribution now states the complete not-passing record;
- it matches only by exact equality in one declared form;
- it says what differs.

In 24 adversarial probes of TR-01, each change was named and nothing matched by containment. These
include D-18's two tests in MI's retained log.

Reviewer: W3 (tooling review 002), a Claude Code subagent in a fresh context, for Director
`c271-p36-14f7f8b219db`. I took no part in writing the tooling or in review 001. Written
2026-11-27 (UTC).

Labels:
- `<worktree>` is the C271 worktree, which the brief says is clean at `d3b622d6`. I started no Git.
- `<local>` is the place beside the clone, and `<W2>` is `<local>/c271-p36/workers/W2`.
- `<W3>` is my directory, `<local>/c271-p36/workers/W3-tooling-002`.
- `<tmp>` is the per-user temporary directory.

## 1. The candidate

`<W2>/SHA256SUMS.txt` (SHA-256 `d9686c8d320ee2d705c658bffaaeeac9ac11b7bb57cdbcd53239adf3abf9ebde`)
lists 159 files. All 159 digests verify, and no other file exists under `<W2>`. The list itself is
the only file it does not cover.

These files are bound for the repository, at
`<worktree>/docs/engineering/localized-repair-c271/macos-routine-p36/tooling/`:

| File (under `tooling/`) | SHA-256 | Bytes | Mode | Against revision 1 |
| --- | --- | ---: | --- | --- |
| `unit_log_outcomes.py` | `0b5269402005584ffa8c0fe4510a1f1d728f7922414a0d38cf841851e29cc75b` | 85540 | 0o644 | changed |
| `readback_evidence.py` | `ad47b9931675eaeaa7584b42410a7952d7398b4ee039c4ebb58ca177f005c69d` | 47080 | 0o644 | unchanged |
| `README.md` | `c96faa076a1224be1fe02e561e5dbc7c4d9719a5c5ca8416bc6681551d8fcd9a` | 29824 | 0o644 | changed |
| `tests/w2_support.py` | `741800d05276642cda3fc2b7b318078c79a3b361b1e131265cd3c637dbca76b1` | 32143 | 0o644 | changed |
| `tests/test_collect.py` | `21cfd2b968954c03ca26d968d66d83a8a02f782a78f275a09d9bdac81fa8991d` | 26998 | 0o644 | changed |
| `tests/test_compare.py` | `e0e7627a56eaeb08e24d0161faaeb5ca86a16287ca1c8d1b0c840222c109cd44` | 28569 | 0o644 | changed |
| `tests/test_readback_evidence.py` | `3c1350b24a86bcd1163ced2d888e9e9a5e6628474ee975b3f558b4d8ef02656d` | 10452 | 0o644 | unchanged |
| `tests/test_zz_hygiene.py` | `585a7bf19d005466f96b1b26e52138a8d9f2fa34d727016fcfde14db114c6d63` | 10177 | 0o644 | changed |

I also read these files, which are not for the repository:
- `<W2>/AUTHOR-NOTES.md` (`9dec5fff…`), all of it, including section 8, which maps TR-01 to TR-11;
- `<W2>/test-runs/r2/` (`TEST-RUNS.json` `103ee521…`);
- `<W2>/validation/run-003/` (`RUN.json` `c8289257…`), and its runner
  `validation/scripts-003/run_validation.py` (`feae28e0…`);
- `<W2>/rejected-001/`, whose `SHA256SUMS.txt` is `c7ec20ca…`, the list that review 001 checked.
  Its eight files equal review 001's table.

The disposition `TOOLING-REVIEW-DISPOSITION-001.json` (`0271f996…`) and review 001 (`.md`
`d9846ec8…`, `.json` `dee4ca42…`) match the digests that each one records.

For the collector and the tests, the diff against revision 1 contains only the changes that section
8 of the author notes declares. I read the revised README in full.

## 2. TR-01 to TR-11

| ID | Met | Evidence |
| --- | --- | --- |
| TR-01 (mandatory) | yes | `unit_log_outcomes.py:1174-1266` and `:1401-1418`. An attribution (`attributions/2`) states the outcome, the occurrences, its own events in order, and its failing and skipped subtests in order. It does so in one declared `form`. `matches` is true only on exact equality, and `observed` and `differences` name each field or item that differs. Revision 1's form is refused. See section 3. |
| TR-02 | yes | `:941-969`. `ID=missing`, `ID=OUTCOME` (exactly one occurrence) and `ID=OUTCOME*N`. Malformed rows refuse with `USAGE`. Probes E01 to E03. |
| TR-03 | yes | `:1301-1310` and `:1487-1488`. `reports_different` lists each report that differs or that one side lacks, and it enters the exit code. Probe R01. |
| TR-04 | yes | `:1370-1372`. A test that was skipped or an expected failure and does not pass now is listed in `new_not_passing` as well as `different_outcome`. Probe N01, which checks seven transitions. |
| TR-05 | yes, with the remaining case that W2 states | `:667-692`. Two or more candidates refuse with `AMBIGUOUS`, whatever their values. The remaining case is TR2-01, and a stale docstring is TR2-02. |
| TR-06 | yes | `:115`, `:117` and `:1052-1137`. Run paths are replaced only as whole components. Below a temporary directory, only `tmp` plus eight characters of `[a-z0-9_]` is masked. Each entry records `masked_temporary_names`. Probes M01 and A19. |
| TR-07 | yes | `tests/test_zz_hygiene.py:39` and `:49-50`. I ran the suite once in an APFS clone of the worktree, with the tooling at its committed place: 90 tests, OK. The strings that would be derived at the real worktree's place occur in no file (section 7). |
| TR-08 | yes | `:113` and `:334-346`. Dotted `_FailedTest` and `ModuleSkipped` names are read. Probe L01. |
| TR-09 | yes, for the README; the binding is carried to S6 | `README.md:33-40` states that the cohort root is cross-checked and recorded in `cohort_bindings`, and that the freeze binds it. |
| TR-10 | yes, outside the tooling | The Director's name-status input (`a3031678…`) lists ten documentation and record paths, none under the seven directories. AUTHOR-NOTES Q-6 is closed. |
| TR-11 | yes | `:816-831`. The log is decoded with universal newlines, and the record gains `equals_footer`. Probe D01 compares the result with the driver's own `Path.read_text` reading. |

**The four details that W2 reports as different are each sound:**
- **TR-06 masks only tempfile's default `tmp` prefix.** This errs on the safe side. Any other
  temporary name stays visible as a different reason, so a hidden difference cannot pass as
  unchanged. The README states it (`README.md:225-232`). The retained runs hold only default names
  (section 6).
  - A non-random name of exactly that shape would be masked. Probe M01 shows one, `tmpcache_01`.
  - Such a name is still recorded per entry, so the masking stays visible.
- **TR-01 declares `form` per attribution, not per file.** The disposition asks for one declared form
  per statement. One form applies to each statement as a whole (probe A19), and the freeze can use
  `raw` for one test and `normalized` for another.
- **TR-07 was shown only at a copy of the committed place.** I closed that gap: the suite passes in a
  clone of the whole worktree, with the tooling at its committed place. The real place's derived
  strings occur in no file.
- **TR-05 lets a status printed right after a start through.** The README states this. I judge it
  nonmandatory, with a cheap correction (TR2-01).

## 3. TR-01 in depth

I wrote my own synthetic logs with this interpreter's `unittest.TextTestRunner` (verbosity 2),
without W2's helpers. I wrote my own summaries, and I ran the comparator's `main()` in my process.
My base statement has D-18's first test's shape: an erroring subtest `(fail_after=False)` with a
`TypeError`, then the test's own `AssertionError` failure. Outcome `error`, one occurrence.

| Probe | Case | Result |
| --- | --- | --- |
| A01 | exact two-part statement | `matches: true`, no difference. `observed` equals the statement. The entry stays in `new_not_passing` with `attribution`, and `exempt` is `[]`. |
| A02 | changed subtest reason | no match: `failing_subtests[0]`, with both items given in full |
| A03 / A04 | added subtest / removed subtest | no match: `failing_subtests[1]` / `outcome` and `failing_subtests[0]` |
| A05 / A06 | added own event (tearDown error) / removed own event | no match: `events[1]` / `events[0]` |
| A07 / A08 | changed outcome (the subtest fails instead of erroring) / changed own reason | no match: `outcome` and `failing_subtests[0]` / `events[0]` |
| A09 / A10 / A11 | subtests reordered / description `(fail_after=0)` / added skipped subtest | no match: `[0]` and `[1]` / `failing_subtests[0]` / `skipped_subtests[0]` |
| A12 / A13 | ID runs twice: one-occurrence statement / two-occurrence statement | no match (`occurrences`, `events[1]`, `failing_subtests[1]`) / match |
| A14 | ID runs twice; the same events distributed differently over the two runs | both match: a limit (TR2-03) |
| A24 | ID runs twice; the second run starts with a direct `FAIL` | the log is refused (`PARSE`, attempts `COUNTS` and `LISTING`): fail-closed, but not in the README (TR2-03) |
| A15 | the not-passing statement for a test that passes | no match: `outcome`, `events[0]` and `failing_subtests[0]` |
| A16 / A23 | a statement of a passing record / a self-inconsistent statement | accepted. The first matches and the second can never match (TR2-04). |
| A17 | ID absent from the log | no match: `{"field": "id", "expected": "present", "observed": "missing"}` |
| A18 | 13 malformed files | each one is refused with exit 2 and `ATTRIBUTIONS`. They cover an ID attributed twice, revision 1's form, a mixed row, `occurrences` true or 0, a missing or undeclared form, extra or missing event keys, an unknown status and an outcome named `exempt`. |
| A19 | declared form | `normalized` with the directory given: match. No match in three cases: `raw`; `normalized` without the directory; and a name that does not have tempfile's shape. |
| A20 | reason whose later lines differ | match. By design, a statement states only first lines (disposition: "status and first line"). |
| A21 | class-level fixture `setUpClass (...)` | the same reason matches. A changed reason gives `events[0]`. |
| A22 | **D-18's two tests in MI's retained log of the 0.1.0 driver module** (`8a58d3fc…`), with statements written by reading the log | both match. A changed subtest reason, a missing subtest and a wrong outcome each name their field, and the second test still matches. |

Against `rejected-001`, all nine `test_tr01_` tests fail, but for two different reasons:
- Five fail on the verdict itself: containment (4) or the ignored form (1).
- Four fail only because revision 1 gives no `observed` or `differences`. Revision 1 already gave
  the right verdict for a changed outcome, a removed own event and an absent ID. For the exact
  statement it gave `matches: true`, which is also right.

The disposition requires the output to say what differs, so these four tests also target TR-01's
defect. W2's analysis states this split correctly.

## 4. Findings

None is mandatory.

### TR2-01, not mandatory: a bare status printed right after a start can still be misread

- **Where:**
  - `unit_log_outcomes.py:636-639`, where a start whose rest is exactly a status token takes it
    without looking at the window;
  - `README.md:97-100` and `:167-169`.
- **What happens:** a test can print a status token with a line end, unbuffered, right after its own
  start. That token is then taken as the test's status, and unittest's real status stands alone on
  the next line as noise.
  - Probe S03: a printed `skipped '...'` replaces the real skip reason.
  - Probe S04: a passing test and a skipped test swap outcomes. Every count is equal, and the
    collector exits 0.
- **The README's reason does not hold.** It says "nothing in the file tells the two apart". But the
  real status remains in the file as a line that is a status token.
- **Closing it costs nothing on real logs.** Both revisions read 130 real logs, with 101,150 starts.
  None of their noise lines is a status token or ends with one: 0 exact and 0 glued.
- **Why it is not mandatory:**
  - Every misread of this kind that changes a count or a listing entry is refused (probe S05).
  - With zero skips and zero expected failures in the footer, every misread changes one of them.
  - R1 must have zero of each, and R2 is expected to, after its readback class fails at setup.
  - The baseline logs hold no such line.
- **Recommended:**
  - refuse (`AMBIGUOUS`) when, after a direct status, a noise line before the next runner line is a
    status token or ends with one;
  - or record such lines in the output, so that the freeze's checker can require none;
  - and correct the README sentence.

### TR2-02, not mandatory: two statements still describe revision 1

- **The `Progress` class docstring** (`unit_log_outcomes.py:464-468`) still says "Exact candidates come
  first; candidates with different statuses refuse the log". That is revision 1's rule. It
  contradicts:
  - the corrected module docstring (`:43-46`);
  - `plan_direct` (`:667-692`).

  The disposition asked for "the docstring" to be corrected.
- **`README.md:201`** defines `different_outcome` as "another outcome not covered above, for example
  skipped and then error". Line 199 says such an entry is in `new_not_passing` as well.
- **Recommended:** correct both.

### TR2-03, not mandatory: repeated IDs, two limits not stated in the README

- **Where:** `unit_log_outcomes.py:1188-1201`, `:532-549` and `:605-611`; `README.md:130-131` and
  `:244-246`.
- **The two limits:**
  1. A statement joins the events and subtests of every occurrence into one list. So for an ID
     that runs more than once, it does not fix which occurrence holds which event. In probe A14,
     two different distributions both match.
  2. A later run of the same ID may start with a direct `FAIL`, `ERROR` or skip. That run is then
     read as a further event of the earlier run, and the log is refused (probe A24). The refusal is
     fail-closed. AUTHOR-NOTES section 7 states it. The README does not, and it says that a twice-run
     ID "keeps both".
- **No effect on MR:**
  - The retained baseline and main logs repeat no ID (`duplicate_test_ids` is 0 in each).
  - D-18's tests run once.
  - `occurrences` is compared.
- **Recommended:** state both limits in the README, or state events per occurrence.

### TR2-04, not mandatory: statements outside a not-passing record are accepted

- **Where:** `unit_log_outcomes.py:1222-1243`; `README.md:234-258`.
- **What happens:** two kinds of statement are accepted:
  - one whose outcome is `passed` (probe A16);
  - one whose outcome contradicts its own events (probe A23: outcome `passed` with a `FAIL` event).
- **Why it is harmless:**
  - Nothing is exempt.
  - A contradictory statement never matches.
- **Why it is a finding:** the disposition describes an attribution as the test's not-passing
  record.
- **Recommended:** refuse a statement whose outcome does not follow from its own events and
  subtests, or state the rule in the README.

### TR2-05, not mandatory: the suite pins none of the documented limits

- **Where:** `tests/test_collect.py` and `tests/test_compare.py`.
- **What is missing:** no test covers:
  - the undetected remaining case of TR-05 (probes S03 and S04);
  - the refusal of a repeated ID (probe A24);
  - a removed subtest (probe A04).
- **Why it matters:** each behaviour is right or documented, but nothing would show a change in it.
- **Recommended:** add tests that pin these behaviours.

### Observations, not findings

- **`reports_different` compares report outcomes only.** A difference that lies only in two read
  errors is not listed (probe R01). This cannot happen in MR: main's report steps passed with
  readable reports.
- **TR-05's stricter rule can refuse R1's log.** It now refuses any window with two candidates, so R1's
  log is refused if it holds a noise line that ends with `ok` (for example "notebook") before a status.
  None of the 130 real logs has one. AUTHOR-NOTES Q-8 governs that case: it is a finding of the tooling.
- **A statement states first lines only, by design** (probe A20).

## 5. No regression from revision 1

**The parser.** My `w3_regression.py` read 145 retained logs with both revisions, in one process.
These are the logs that review 001 listed, under `<local>/checks/`, `c271-p33/checks/` and `c271-p35/`.
- 130 were read by both revisions. Their `tests`, `fixtures`, `footer`, `counts`, `checks`,
  `listing`, `noise` and `text` are identical, and so is `driver_reading`, apart from the new
  `equals_footer`. `equals_footer` is true in all 130.
- 15 were refused by both, with the same rule:
  - 2 with `FOOTER`: the two stopped runs;
  - 13 with `PARSE`: the dot-format logs.
- No log was refused as `AMBIGUOUS`.

**The comparator's lists.** On all six real comparisons, the rerun's item-4 lists, its `unchanged`
counts and its `steps_different` equal revision 1's run-002.

**The readback reader.** Its file is byte-identical to the one that review 001 accepted. On MH's
retained cohort it reads `READ`, with all 144 checks passed and exit 0. This output equals W2's
run-003.

**The reused MH files.** I computed these values on the worktree's files. The brief says the worktree
is clean at `d3b622d6`; without Git, I could not compare them with the committed blobs.

| File | SHA-256 | Bytes | Mode |
| --- | --- | ---: | --- |
| `FAILURE-CAPTURE.md` | `f387fb3ec0ed306366f6d3f22820ec344f1ac843008775475258c5de9634c99c` | 13147 | 0o644 |
| `capture_probe.py` | `db5fb5250909effa7e3fe3d66feadc5183160b4e6088178a763e6fc41567048f` | 29076 | 0o644 |
| `discover_inventory.py` | `980c80883f3106706a3ecd3b03e908efe31a5c572a67a0d71dc650f85cfb695e` | 35270 | 0o644 |
| `audit_numeric.py` | `9140379c61bc70f29939bd7b216ef5ca5e2f5e6cab5b4a452e50018651bac4e3` | 40667 | 0o644 |

Each value equals three records:
- the table in W2's README;
- MH's `authoring/TOOLING-SHA256SUMS.txt`;
- MH's `FREEZE-002.json`.

## 6. Tests and validation

**Three suite runs.** Each was a single start of `python3 -I -S -B -m unittest discover -s tests -v`,
with a `TMPDIR` inside `<W3>`.

| Run | Result | Log SHA-256 |
| --- | --- | --- |
| from `<W2>/tooling` | 90 tests, OK, no skip, 0 process-creation events | `544562c3…` |
| against my copy of `rejected-001`, with revision 2's tests copied byte-equal into `<W3>` and `W2_TOOLING_UNDER_TEST` set | 90 tests, `FAILED (failures=18, errors=8)` | `273b5810…` |
| in an APFS clone of `<worktree>`, without `.git` and `.venv` (22,965 files and links), with the tooling at its committed place | 90 tests, OK, no skip, 0 events. I removed the clone afterwards. | `a7141d5c…` |

**What the runs show:**
- **Against `rejected-001`, all 18 `test_tr01_` to `test_tr06_` tests fail.** I read the log with the
  collector itself. Each one fails for its defect:
  - TR-01: section 3;
  - TR-02: `=missing` is refused, and a test that ran twice meets `=passed`;
  - TR-03: exit 0 with a differing report;
  - TR-04: `new_not_passing` is empty;
  - TR-05: `PARSED` instead of `REFUSED`;
  - TR-06: the substring `<workspace>2`, and a masked non-random name.
- **TR-08's and TR-11's tests fail too.** So do five tests that read revision 2's new members.
- **TR-07's test passes there,** as it must, because the change lies in the test.
- **None of the three runs wrote** into `<W2>`, the clone or the worktree. Each left no bytecode, and
  each `TMPDIR` was empty afterwards.

**Adequacy.** The tests cover each finding of review 001, and W3's probes PR-1 to PR-8 are among
them. They depend neither on where they lie nor on this host, and they skip nothing. The gaps are
TR2-05.

**Validation.** I started W2's run-003 runner once, into `<W3>/runs/validation-run-003-rerun`. The
runner creates that directory itself; its parent existed. It used the same per-user `TMPDIR` as
run-003, and it started 28 tool commands.

My `w3_validation_check.py` made 12 checks, and all 12 agree:
- **Exit codes:** 20 times 0, 6 times 1 and 2 times 2, as in run-003 and run-002.
- **Outputs:** all 28 equal run-003's, apart from `invocation` and the times.
- **INTEGRATION.json's `comparison_with_baseline` is reproduced exactly:**
  - resolved pair: 1 unchanged;
  - default pair: 307 unchanged (230 errors and 77 failures);
  - all five difference lists are empty;
  - 4,740 then 4,989 tests;
  - only `documents` changed, from failed to passed;
  - the pending cases and the skips are equal.
- **The facts that the record does not state:**
  - the 249 added IDs all passed;
  - no ID was removed;
  - no skip reason or number of occurrences differs, and no report differs;
  - the driver's reading equals each summary;
  - no ID repeats.

**Does the masking hide a real difference?** No. I compared both pairs, 4,740 shared IDs each. For
every ID with the same outcome, I compared the raw statement of each side: its own first lines, its
failing subtests and its skipped subtests.
- **The resolved pair** has no raw difference at all.
- **The default pair** has 3. The tool calls all 3 unchanged, and all 3 vanish under my own
  canonicalization, which replaces only each run's declared paths and tempfile-shaped names below
  `<tmp>`.
  - The six masked names all have tempfile's default shape.
  - None of them occurs in both runs.
  - Without the temporary directories, those 3 are the only different reasons.

## 7. Privacy of the repository-bound files

My `w3_privacy.py` derived 255 strings at run time, and it writes none of them. It searched the
eight files, and in each Python file it also searched the joined forms of its string literals:
- adjacent constants in any list of children;
- chains of `+`;
- the constant parts of f-strings;
- all of a file's constants, joined in source order.

**What it searched for:**
- the account name and its parts;
- the parts of the account's full name;
- the user name and e-mail in the Git configuration file, read as text with no Git started;
- the home directory;
- these paths, with their ancestors as text and their components as words: the worktree (which
  covers the real committed place's parent), the place beside the clone, the interpreter's prefix
  and executable, the temporary directory and my script's path;
- the names of the applications in the system, local and user application folders;
- the names of the package manager's formulas and casks;
- e-mail-shaped text and absolute-path literals.

**Result:** no machine path, account or personal name, e-mail address or name of an installed
application occurs in any of the eight files, and none is split across literals. The only matches
are false positives:
- three ordinary English words that are also names of applications, used in their ordinary sense;
- the word for the plan's JavaScript runtime, used as an identifier and as an AST variable;
- the generic `/private/var` form that describes macOS's link;
- the shebang;
- a synthetic `/tmp` component name in two tests.

## 8. What I ran

**Bash calls.** I made 70 Bash tool calls, the last of which wrote and checked `SHA256SUMS.txt`.
Each started a shell and the utilities it names: `ls`, `cat`, `sed`, `grep`, `head`, `tail`, `wc`,
`shasum`, `stat`, `find`, `awk`, `cut`, `sort`, `uniq`, `tr`, `diff`, `du`, `mount`, `getconf`, `id`,
`ps`, `tee`, `date`, `basename`, `dirname`, `mkdir`, `touch`, `sleep`, `cp`, `mv`, `rm` and `rmdir`.
`cp -c` ran 28 times for the clone.

**The framework interpreter: 54 starts, each one with `-I -S -B`:**
- 26 direct starts:
  - 16 one-liners (`-c`) that read records. Two of them checked that my JSON records parse: one
    before my last edits, and one in the final call;
  - 6 runs of my five scripts: `w3_regression.py`, `w3_probes.py` (twice), `w3_suite_analysis.py`,
    `w3_validation_check.py` and `w3_privacy.py`;
  - 3 suite runs;
  - 1 start of W2's runner;
- 28 tool commands started by W2's runner.

My scripts load the tools from their files and call them in their own process. An audit hook in the
probe script counted 0 process-creation events.

**Never started:** Node, Git, `ldd`, `codesign`, `otool`, the observer, `tools/check_local.py`, the
repository's unit tests and child agents. At the end, no process of mine was running.

**Deviations:**
- **DV-1, my own script error.** The first run of `w3_probes.py` stopped on an error of mine: probe A14's
  first design hit the repeated-ID refusal that A24 now shows. Its partial outputs are kept in
  `runs/probes-attempt-1-failed/`. The corrected script ran once, into a fresh directory. Both starts
  are counted.
- **DV-2, a redirection typo.** One early read-only pipeline had a redirection to a path that does not
  exist, and the shell reported an error. Nothing was written.

**Reads outside the brief's list, all read-only:**
- MI's retained driver log under `<local>/c271-p33/checks/final-003/`, for A22;
- review 001's `status-choices.json` and the 145 logs that it lists;
- the Git configuration file and the listings of the application and package folders, for the
  privacy derivation. Nothing from them is recorded.

**Records:**
- The raw records under `runs/` hold machine paths. They stay beside the clone and are not portable.
- `TOOLING-REVIEW-002.md` and `.json` and the scripts use labels.
- `SHA256SUMS.txt` lists every file I wrote.

**Not checked:**
- the documentation verifier on the README (not one of my allowed starts);
- the committed blobs at `d3b622d6` (I started no Git);
- the reader's `run` command and the preserved route on real records, since no qualifying run
  exists yet;
- R1's and R2's own logs;
- a run at the real worktree's committed place: I ran only a clone, because nothing may be written
  into the worktree.
