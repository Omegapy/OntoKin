# Tooling review 001: gate MR observational tooling (C271-P36, stage S3)

**Verdict: REJECT_WITH_MANDATORY_FINDINGS.** One finding is mandatory (TR-01): an attribution
cannot state a not-passing record exactly, and it reports a match when only one of the record's
reasons matches. D-18's first test is such a record, and MR-PLAN sections 5, 7 and 9 decide on
attribution "by exact test ID and reason". Ten findings are nonmandatory (TR-02 to TR-11).
Apart from these findings, the review established:
- the collector, the comparator and the reader read the real record layouts;
- the four reused MH files are byte-identical to MH's;
- the validation reproduces INTEGRATION.json's comparison exactly;
- the repository-bound files hold no private string.

After TR-01 is corrected, the change needs a repeated review (MR-PLAN section 2).

Reviewer: W3 (tooling review 001), a Claude Code subagent in a fresh context, for Director
`c271-p36-14f7f8b219db`. I took no part in writing the tooling. Written 2026-11-27 (UTC).

Labels:
- `<worktree>` is the C271 worktree, which the brief says is clean at `d3b622d6`. I started no Git.
- `<local>` is the place beside the clone.
- `<W2>` is `<local>/c271-p36/workers/W2`.
- `<W3>` is my directory, `<local>/c271-p36/workers/W3-tooling-001`.
- `<tmp>` is the per-user temporary directory.

## 1. The candidate

`<W2>/SHA256SUMS.txt` (SHA-256 `c7ec20ca970e6bdf2e668a8df98519af26cbb5cf78186b7dd827979f08cb8d29`)
lists 83 files. All 83 digests verify, and no other file exists under `<W2>`. The eight
repository-bound files are reviewed here. Their target is
`<worktree>/docs/engineering/localized-repair-c271/macos-routine-p36/tooling/`.

| File (under `tooling/`) | SHA-256 | Bytes | Mode |
| --- | --- | ---: | --- |
| `unit_log_outcomes.py` | `462022b5a857d0f50ea68afdccfddc3abdbc0cdfeb64a8a5b2e7a7dab906cc98` | 74353 | 0o644 |
| `readback_evidence.py` | `ad47b9931675eaeaa7584b42410a7952d7398b4ee039c4ebb58ca177f005c69d` | 47080 | 0o644 |
| `README.md` | `eada0ba989f66c21120e29f19e07f7635e7d43588da088c9077e32658cece902` | 23064 | 0o644 |
| `tests/w2_support.py` | `5e68c93ec736f7115d7aee5795e412bdf79269585672e05534ce994865770b70` | 27991 | 0o644 |
| `tests/test_collect.py` | `2335946effe632bf78f5fb05aedd9f0c079ac7031b875a33747c81f3111d4ac7` | 19543 | 0o644 |
| `tests/test_compare.py` | `66296e0bc772848f9e240060e7aa2ef954fb490548fc3a555a4ffc62796bae01` | 16148 | 0o644 |
| `tests/test_readback_evidence.py` | `3c1350b24a86bcd1163ced2d888e9e9a5e6628474ee975b3f558b4d8ef02656d` | 10452 | 0o644 |
| `tests/test_zz_hygiene.py` | `1594d614c0cacaa2e25a2a07a377c275bb24d2f03748b41c4ad0ed2c6df5c7fd` | 8810 | 0o644 |

I also read these, which are not for the repository:
- `<W2>/AUTHOR-NOTES.md` (`62dcea8f…`);
- `<W2>/test-runs/`;
- `<W2>/validation/run-002/` and `validation/scripts/` (`run_validation.py` is `50f15030…`).

## 2. Findings

### TR-01, mandatory: an attribution is matched by containment of one reason

- **Where:** `unit_log_outcomes.py:1083-1099` and `:1220-1235` (the test is at line 1228);
  `README.md:186-191`; `tests/test_compare.py:156-173`.
- **What the code does:**
  - An attribution row holds one `reason_first_line`.
  - An ID may not repeat.
  - `matches` is true when that reason is one of the candidate's reasons, raw or normalized.
  - The test's other reasons and its failing subtests are never compared.
- **Why it matters:** a not-passing record that has more than one reason, or a failing subtest,
  cannot be attributed exactly. A change in its other parts still gives `matches: true`.
  - Probe PR-5 shows this. The candidate's subtest reason changed, and a second subtest errors.
    The comparator still reported `matches: true`.
  - D-18's first test is such a record. In MI's retained final-003 run of the 0.1.0 driver module,
    `test_failed_prelaunch_is_recorded_unexecuted_even_if_later_inventory_fails` has two parts:
    - an erroring subtest `(fail_after=False)`, whose first line is a `TypeError`;
    - its own failure, whose first line is an `AssertionError`.

    Its outcome is `error`.
  - MR-PLAN section 9 makes a not-passing test that is not attributed "by exact ID and reason" a
    finding. So with this rule, S7's checker could clear a changed D-18 failure.
- **Required change:**
  1. An attribution states the complete not-passing record:
     - the outcome;
     - the list of status and first line of the test's own events;
     - the failing and skipped subtests, each with its status and its first line or skip reason.
  2. `matches` is true only when the candidate's record equals that statement exactly. One declared
     form, raw or normalized, applies to the whole record.
  3. The output says what differs.
  4. Focused tests cover:
     - an exact match of a two-event record, with an erroring subtest and the test's own failure;
     - three mismatches: a changed subtest reason, an added subtest and an added own event.
  5. The README's attribution paragraph describes the new rule.

### Nonmandatory findings

**TR-02. `--expect` cannot state an absence and ignores repetition.**
- Where: `unit_log_outcomes.py:901-914`; `README.md:123-124`.
- Only the six outcomes are accepted, so no row can expect an ID to be `missing`. MC23 needs that
  for the fixture records of the two readback classes.
- `met` ignores `occurrences`. In probe PR-2, a test that ran twice still met `=passed`.
- Probe PR-1: the seven readback methods pass while the CPU class's `tearDownClass`, the cohort
  accounting, errors. `collect` exits 0 with `expectations_met: true`.
- The failure would still show elsewhere:
  - the comparator lists the fixture as an added ID that does not pass;
  - the reader fails `cohort_passed_with_three_starts` when the accounting itself fails;
  - W2's Q-5 tells the freeze to check the fixtures.
- Recommended: accept `missing`, and make `met` require one occurrence. Otherwise the freeze binds
  both checks explicitly.

**TR-03. Report-summary differences do not reach the top level.**
- Where: `unit_log_outcomes.py:1119-1159` and `:1301-1303`; `README.md:193-199` and `:207-209`.
- When a report summary changes and every step status stays equal, only
  `steps[].report_outcomes_equal: false` shows it.
- `steps_different` stays empty, and the exit code can be 0. Probe PR-7 changed the `source`
  report's summary and got exit 0.
- MR-PLAN section 5 names "its report summaries" next to the statuses and the pending cases.
- Recommended: add a `reports_different` list, include it in the exit rule, and test it.

**TR-04. A test that was skipped and now fails is not in `new_not_passing`.**
- Where: `unit_log_outcomes.py:1185-1192`; `README.md:157-161`; AUTHOR-NOTES D-7.
- A test that was skipped or an expected failure in the baseline, and does not pass in the
  candidate, is listed only under `different_outcome` (probe PR-8).
- Main's three skipped readback tests would fall there in R1 if they did not pass. MC23 covers that
  case.
- Recommended: flag such entries as new not-passing as well. Otherwise the freeze's checker treats
  every `different_outcome` entry that does not pass in the candidate as new.

**TR-05. Some misreads change no count, so the log is not refused.**
- Where: `unit_log_outcomes.py:639-662` and `:40-41`; `README.md:80-85` and `:103`;
  AUTHOR-NOTES lines 303-307.
- The parser prefers an exact status candidate and ignores a glued candidate of another value.
  Misreads among statuses that have no listing entry (ok, skipped, expected failure), and misreads
  of a skip reason, are caught only by the counts.
- Probe PR-3:
  - Two printed imitations swapped a skipped test and a passing test.
  - One imitation replaced a recorded skip reason.
  - Both logs were read "completely", with exit 0.
- So two claims do not hold:
  - the module docstring's "refused" rule for a guess that changes an outcome;
  - the AUTHOR-NOTES statement "misread only if the imitation changes no value and no count".
- On 130 real logs with 101,150 starts, only 105 windows needed a choice, and none had more than
  one candidate.
- Recommended:
  - refuse a window with more than one candidate (that refuses none of the 130 real logs);
  - correct both statements;
  - keep the probes as tests.

**TR-06. The normalization can hide a different directory name.**
- Where: `unit_log_outcomes.py:1040-1048`; `README.md:169-184`.
- The `*` replaces any one component directly below a given temporary directory, not only
  `tempfile`'s random names. Probe PR-6: two reasons that named different directories there
  compared as unchanged.
- Summary paths are replaced as plain substrings, without a component boundary (lines 1043-1044).
- On the retained runs, only `tempfile` names were masked (section 7).
- Recommended:
  - restrict `*` to `tempfile`'s name shape, or record the masked components in each entry;
  - replace summary paths only at component boundaries.

**TR-07. The hygiene test depends on where the checkout lies.**
- Where: `tests/test_zz_hygiene.py:42-43`, `:57-62` and `:109`; `README.md:341-374`.
- The test treats every non-generic component of the checkout's parent as private.
- I ran it in an APFS clone placed under the phase's worker directory, with the tooling at its
  committed place. Three subtests failed, in README.md, `unit_log_outcomes.py` and
  `readback_evidence.py`. The cause is the phase directory's name, which those files write as the
  phase ID. The other 67 of the 68 tests passed.
- At the real worktree, the parent's components do not occur in the tooling (checked), so the test
  should pass there.
- Line 109 also requires a non-generic component in the interpreter prefix, which ties the test to
  this host.
- The README does not say this. MH's review 003 (Q4 and Q5) accepted the same behaviour for MH's
  test.
- Recommended: exclude the project's own task and phase names from the derived components, or
  document where the suite must run.

**TR-08. A failed import inside a test package makes the log unreadable.**
- Where: `unit_log_outcomes.py:322-344`; `README.md:63-79`.
- A failed import of `pkg.test_x` is refused with `PARSE` and `LISTING` (probe PR-4). The method is
  taken as the last dotted part of the ID.
- This cannot happen in this repository: `tests/` has no package, and 3.12's discovery recurses only
  into packages. The refusal is fail-closed, but the limit is not stated.
- Recommended: document it, or accept a dotted name for `_FailedTest` and `ModuleSkipped`.

**TR-09. The README's binding rule does not cover the reader's cohort root.**
- Where: `README.md:32-36`; `readback_evidence.py:337-522` and `:677-707`.
- The README says that every input is bound by a supplied digest, or by a bound input's record. That
  does not hold for the cohort root's files:
  - they are cross-checked with one another and with the derived selection;
  - their bindings are recorded in `cohort_bindings`;
  - no supplied digest and no field of the summary binds them.
- `run` and the preserved route rest on synthetic records only.
- Recommended: correct the README. The freeze fixes the route and the root (W2's Q-2) and binds
  `cohort_bindings` for the audit.

**TR-10. MR-PLAN section 1's confirmation by W2 is still open.**
- Where: AUTHOR-NOTES lines 228-233 (Q-6); `MR-PLAN.md:54-57`.
- W2 did not confirm, with exact inputs, that main changed nothing under the seven directories
  between `8e847c15` and `51223c9b`. W2 started no Git.
- The Director's name-status input lists ten documentation and record files only.
- The `documents` stage's inputs did change.
- This lies outside section 5. It stays open for S4.

**TR-11. `driver_reading` translates no line ends.**
- Where: `unit_log_outcomes.py:786-794`; `tools/check_local.py:684`.
- `driver_reading` decodes the log without translating line ends. The driver's `read_text` turns
  carriage returns into line ends.
- A carriage return next to a `Ran` line or a result line could make the two readings differ.
- No retained log has one, and the field is informational.
- Recommended: decode as the driver does, or state the difference.

## 3. Requirement coverage, MR-PLAN section 5

| Requirement | Status | Evidence |
| --- | --- | --- |
| Collector: every outcome kind, one record per raw ID | met | `outcome_of`, `test_records`; EveryOutcomeKind |
| Collector: first line of each failure or error reason | met | `reason_analysis` (chains and multi-line lines included) |
| Collector: failing subtests | met | `failing_subtests` and `skipped_subtests` |
| Collector: class-level and module-level fixture errors, and import failures | met; one limit | fixture records, `_FailedTest`. A dotted failed import is refused (TR-08). |
| Collector: interleaved output | met; one limit | noise handling. All 130 real logs were read. Count-neutral misreads (TR-05). |
| Collector: count checks against `Ran` and the result line | met | `consistency`. Started equals `Ran` in every real log. |
| Collector: refusal of an incomplete, unparsable or digest-mismatched log | met | `FOOTER`, `PARSE`, `DIGEST`. The two stopped logs and 13 dot-format logs were refused. |
| Comparator: item 4's lists | met | unchanged, `new_not_passing`, `no_longer_failing`, different outcome, reason and subtests, added and removed IDs. See TR-04 for the category choice. |
| Comparator: logs and summaries bound by SHA-256; the summary names its log | met | `bound_input`; the `BINDING` refusal |
| Comparator: summary-level comparison of step statuses, report summaries and pending cases | partly | Statuses and pending cases are compared. Report summaries are compared but not surfaced (TR-03). |
| Comparator: attributions only from a frozen file, by exact ID and reason | not met | exact ID only; the reason is matched by containment (TR-01) |
| Comparator: nothing classified as exempt by the tool | met | `exempt` is always `[]` |
| Comparator: inputs never edited | met | inputs are opened read-only; the output is written with `O_EXCL` to an absent path |
| Reader: selection, derived binding, three attempts, starts, receipts, reports | met | Checked against the provider's code. `cohort` passed 144 checks on MH's real cohort. `run` is synthetic only (TR-09). |
| Reader: handover to MH's numerical-audit harness | met | joined by the tool digest, `-B`, the root and the twelve input bindings. MH's audit reads the root unchanged. |
| Reused from MH: unchanged, bound by digest | met | section 5 |
| README and reuse table | met; TR-03, TR-09 and TR-11 corrections | the table's digests, sizes and modes are verified |

## 4. Correctness risks (brief, item 2)

**Normalization.** It can mask a non-random directory name (TR-06). On the retained runs it was
needed for no reason that genuinely differed (section 7). The labels `<tmp>`, `<tmp:resolved>` and
`<tmp:alias>` stay distinct, so the alias-versus-resolved difference stays visible.

**Parse ambiguity: are IDs dropped or merged?** IDs come only from runner lines, and a repeated
start is kept as an occurrence. A start that is lost or imitated breaks `started == Ran`, or the
listing check for not-passing tests.
- An independent reading of the listing headers of the six recorded logs gives exactly the
  collector's not-passing IDs and fixture IDs.
- The header counts equal failures plus errors.
- The count-neutral exception is TR-05.

**`--expect` for MC23.** IDs and outcomes are matched exactly. An absence or a repetition cannot be
stated (TR-02).

**`--inventory` for MC28.** It is exact: the IDs are recomputed and the sequence must be equal. On
MH's two real discovery documents:
- the format is accepted;
- all 4,989 tests started in main's log are in each document, in the same form;
- the common tests ran in exactly the discovery order;
- the only differences are the IDs that the branch adds (598 and 1,005).

**Location.** The tools depend on their place only for self-identification (`__file__` in
`tool_record`, the cwd in `invocation_record`). At the committed place, in a clone, they behaved as
in `<W2>`. Only the hygiene test depends on the location (TR-07).

**Fail-closed refusals.**
- Every refusal exits 2 and gives no result.
- An unexpected exception exits 3 with `UNKNOWN`.
- The comparator refuses when either log cannot be read.
- An existing output is never replaced, and an input is never written.

## 5. Reuse

I computed these SHA-256 values on the worktree's files. The brief states that the worktree is clean
at `d3b622d6`. Without Git, I could not check them against the committed blobs.

| MH file | SHA-256 | Bytes | Mode |
| --- | --- | ---: | --- |
| `FAILURE-CAPTURE.md` | `f387fb3ec0ed306366f6d3f22820ec344f1ac843008775475258c5de9634c99c` | 13147 | 0o644 |
| `capture_probe.py` | `db5fb5250909effa7e3fe3d66feadc5183160b4e6088178a763e6fc41567048f` | 29076 | 0o644 |
| `discover_inventory.py` | `980c80883f3106706a3ecd3b03e908efe31a5c572a67a0d71dc650f85cfb695e` | 35270 | 0o644 |
| `audit_numeric.py` | `9140379c61bc70f29939bd7b216ef5ca5e2f5e6cab5b4a452e50018651bac4e3` | 40667 | 0o644 |

Each value equals three records: W2's README table, MH's `authoring/TOOLING-SHA256SUMS.txt` and MH's
`FREEZE-002.json`. No W2 tool imports an MH tool. W2 uses MH's tools only through their output
documents:
- the discovery document, `ontokin.c271.p35-runtime-discovery/2` with state `COMPLETE`;
- the audit record, `ontokin.c271.p35-numerical-audit/2`.

## 6. Tests

- **Two runs.**
  - From `<W2>/tooling`: 68 tests, OK, no skip, 0 process-creation events.
  - In the clone at the committed place: 67 passed, and the hygiene test failed in 3 subtests
    (TR-07).
- **Writes.** Neither run wrote into `<W2>` or the clone: no newer file, no bytecode, and every
  digest still verifies. Both runs used a `TMPDIR` inside `<W3>`, which was empty afterwards.
- **Dependencies.** The tests depend on no file beside the clone. They use only the tooling
  directory and fresh temporary directories.
- **Gaps against the risks above:**
  - no multi-reason attribution (TR-01);
  - no absence or repetition expectation (TR-02);
  - no report-summary exit test (TR-03);
  - no count-neutral misread (TR-05);
  - no non-random masked component (TR-06);
  - no dotted failed import (TR-08).

## 7. Validation (brief, item 5)

**The runner.** W2's runner was started once. It failed at its own `os.mkdir(OUTPUTS)`, because I
gave it an outputs path whose parent did not exist. It started no child and wrote nothing. It is
kept in `runs/failed-runner-attempt/`, and I did not start it again.

**The reproduction.** My `scripts/w3_validate.py` built the runner's 28 argument lists exactly. It
called each tool's `main()` in the script's own process, with `-B` and the same `TMPDIR` as W2's
run-002.
- The exit codes were 20 × 0, 6 × 1 and 2 × 2, as in run-002.
- Every output equals W2's run-002 output, apart from the volatile fields.
- 140 checks found 0 disagreements.

**INTEGRATION.json's comparison is reproduced exactly:**
- resolved pair: 1 unchanged not-passing test;
- default pair: 307 unchanged not-passing tests (230 errors and 77 failures);
- all five difference lists are empty;
- 4,740 then 4,989 tests;
- only `documents` changed, from failed to passed;
- the pending cases and the skips are equal.

The record does not state four facts, which the reproduction adds:
- the 249 added IDs all passed;
- no ID was removed;
- every report outcome is equal;
- the driver's own reading equals each summary.

CANDIDATE-CHECKS.json's comparison is reproduced as well. The collector agrees with
BASELINE-CHECKS.json's own not-passing IDs, module counts and skipped IDs.

**Was the normalization needed for a reason that genuinely differed?** No.
- Without any normalization, the resolved pair shows no difference.
- The default pair shows three different reasons:
  - two in `test_force_evidence_collection`;
  - one in `test_local_checks`.
- Each pair of reasons differs only in a random `tmp` plus eight characters, directly below the
  given temporary directory.
- The `test_local_checks` reason also names each run's own interpreter.
- With the declared normalization, all 307 are unchanged.

## 8. Privacy

I derived the private strings at run time and wrote none of them.

**What I checked:**
- the account name and its parts;
- the parts of the account's full name;
- the home directory;
- the ancestors and non-generic components of these paths: the worktree, the place beside the
  clone, the interpreter prefix and executable, the temporary directory and my script's path;
- the names of the applications in the system and user application folders;
- the names of the package manager's installed formulas;
- e-mail-shaped text;
- absolute-path literals;
- string literals joined across adjacent constants, sums, statements and f-string parts.

**Result:** no machine path, account name, personal name, e-mail address or application name occurs
in any of the eight files, also not split across constants. The only matches are false positives:
- two ordinary English words that are also names of applications bundled with the operating system,
  used in their ordinary sense;
- the generic `/private/var` form, used to describe macOS's link;
- the word for the plan's own JavaScript runtime, used as an identifier.

## 9. What I ran

**Bash calls.** I made 104 Bash tool calls. Each started a shell and the utilities it names: `ls`,
`cat`, `sed`, `grep` (an alias of `ugrep` here), `head`, `tail`, `wc`, `shasum`, `stat`, `find`,
`awk`, `cut`, `sort`, `uniq`, `paste`, `tr`, `xargs`, `date`, `touch`, `mkdir`, `mv`, `rm`,
`rmdir`, `cp -c`, `du`, `mount`, `which`, `getconf`, `id`, `ps` and `pgrep`.

**The framework interpreter: 25 starts, each `python3 -I -S -B`.**
- 16 one-liners (`-c`): reading my own records, and a final check that the JSON record parses;
- 6 runs of my five scripts in `scripts/` (one of them failed and was run again);
- 1 start of W2's validation runner, which failed and started no child;
- 2 starts of W2's suite, one in `<W2>` and one in the clone.

My scripts load W2's tools from their files and call them in their own process. None of them starts
a process.

**Never started:** Node, Git, `ldd`, `codesign`, the observer, `tools/check_local.py` and the
repository's unit tests. At the end, no process of mine was running.

**Deviations:**
- **DV-1, a background loop.** It started one `grep` per file over 19,501 files under `<local>`, read
  only, until I stopped it. The number of `grep` starts is unknown, at most 19,501. It also wrote a
  list of file names into the session's scratch directory, which is outside `<W3>`. I removed that
  file at once and checked that no process remained.
- **DV-2, an earlier loop.** It started at most 400 `grep` starts, each a read.
- **DV-3, W2's runner.** The failed attempt is described in section 7.
- **DV-4, a refused call.** One call was refused by the session's permission check before it ran. It
  held an interpreter start without `-I -S -B`. Nothing started.
- **DV-5, my own script errors.** Two of my runs failed on errors in my scripts. Both are kept and
  counted.

**Records.**
- The raw records under `runs/` hold machine paths. They stay beside the clone and are not portable.
- `TOOLING-REVIEW-001.md` and `.json` use labels.
- `SHA256SUMS.txt` lists every file I wrote.

**Not checked:**
- the documentation verifier on the README at B (not in my allowed starts);
- the reader's `run` command and the preserved route on real records (no qualifying run exists);
- R1's own log;
- the worktree's Git state.
