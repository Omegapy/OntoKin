# Independent review of P33-AMENDMENT-001: Darwin's group probe

**Candidate:** commit `5dc76ccf1a763a3454e34f97db842a2192d3129e`, tree `c979be79…`, parent
`a2376191…` (W1's checkpoint). It adds two files and nothing else:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `docs/engineering/localized-repair-c271/macos-implementation-p33/AMENDMENT-001.md` | 8,899 | `8bc138a2…2ab3` |
| `docs/engineering/localized-repair-c271/macos-implementation-p33/AMENDMENT-001.json` | 6,358 | `7e204e78…a2a0` |

**Reviewer:** an independent reviewer with fresh context, read-only in the repository, for
C271-P33 (Director `c271-p33-a99647756bed`), in local mode. I wrote none of the reviewed
material. The review was completed on 2026-11-26 at about 15:40Z. Main was at `51223c9b…`.
During the review, the branch head moved to `a97ef91d…`, through W2's checkpoint `939942e3`
and the Director's decisions `a97ef91d`. At that head, the two files, the P31 contract
directory and `supervisor.py` are unchanged.

Paths are relative to the checkout. `<review>` stands for
`../../OntoKin-local/c271-p33/reviews/amendment-001`, the scratch directory of this review.

## Verdict: REJECT_WITH_MANDATORY_FINDINGS

There are two mandatory findings, A-01 and A-02, and five nonmandatory ones, A-03 to A-07.

- **The finding holds.** I reproduced P33-SUPERVISOR-001 from both sources, and its by-code
  claims deterministically.
- **The decision is sound.** It is correct, minimal and fail-closed. I found no path in which
  the EPERM handling passes a cleanup wrongly, hides a live member or leaves the direct child
  unreaped.
- **It cannot be adopted as written,** for two reasons:
  - No control is obliged to exercise the amended rule. The existing behavioural controls pass
    an implementation that counts EPERM as absent, and I reproduced this (A-01).
  - The decision to keep 0.2.0 rests on a premise that the candidate tree contradicts. It also
    rests on a label rule that no replaced clause carries (A-02).

## 1. Checks run

| # | Check | Result |
| --- | --- | --- |
| K1 | Commit, tree, parent, diff stat | Only the two files are added, 216 lines. |
| K2 | Adopted payloads at the candidate, against ADOPTION.json | CONTRACT.md (42,769 bytes, `42db98dc…`), CONTRACT.json (43,340 bytes, `c843fc96…`) and READ-SET.json (10,791 bytes, `9a5e7bed…`) are **byte-identical** to the adopted payloads. |
| K3 | `prototypes/static_tray_v01/supervisor.py` | SHA-256 `c47b84ab…`. Last changed in C199 (`74eba60c`), unchanged since, and equal to W1's record. |
| K4 | Host facts, read as files with no process start | `SystemVersion.plist` and its OS cryptex copy: 26.6.2, build 25G83. `os.uname()`: Darwin 25.6.0, arm64. The checkout's `.venv` is CPython 3.12.13. All **match** the amendment. |
| K5 | Links and JSON form | Every link in AMENDMENT-001.md resolves at the candidate. AMENDMENT-001.json parses, and its `replaces` has 12 keys. |
| K6 | Callers of the group helpers | Only `supervisor.py` calls `group_exists` and `terminate_group`. The 0.1.0 provider uses `run_process`, `inventory`, `Stop` and `Clock`, so no caller bypasses the Darwin versions. |
| K7 | Supervisor clauses of the contract, against the amendment's replacement list | See section 2, question 3, and findings A-01 to A-03. |
| K8 | Reproduction R1 to R8 | Section 4. |

## 2. Answers to the five questions

### Question 1: is the finding true?

Yes, and I reproduced it.

- **The Director's probe (R1):** three runs gave byte-identical output.
  - The exited, unreaped direct child answers EPERM, then ESRCH after `waitpid`.
  - The killed orphan answers EPERM for one 1 ms poll, then ESRCH, 1.5 ms after the kill.
- **W1's checkpoint `a2376191`,** extracted from Git (R2, R3):
  - In 12 runs, the observation test passed every time, with the sequence 0, EPERM, EPERM ×3,
    ESRCH.
  - In the same 12 runs, MC12 raised `PermissionError` 4 times and the MC13 timeout case 2 times.
    The cancellation case and the positive case never did.
  - In 20 more runs, MC12 raised it 10 times and the timeout case 4 times.
  - Each of these errors came from the same place, `run_process:138` → `terminate_group:135` →
    `group_exists:107`, with the original `Stop` as `__context__`.
  - The rates differ from W1's because the window is a race. The failure kind is the same.
- **The paths the amendment states by code only,** reproduced deterministically:
  - The send path (D2): `terminate_group` started on an exited, unreaped direct child raises
    `PermissionError` at line 127, the SIGTERM send.
  - The group check after exit (D4): it raises first, and the send then raises again.
- **W1's logs (R7):** they tally to the cited counts: 12 runs, with MC12 10, MC13 timeout 3, MC13
  cancellation 1 and the positive case 0, every failure `PermissionError`. Precision points are
  under A-06.

### Question 2: is the decision correct, minimal and fail-closed?

Yes.

- **`group_exists`:** absence requires ESRCH. EPERM counts as present. Any other error
  propagates, as in the original.
- **The sends:** POSIX `kill` fails with EPERM only when the caller may signal no receiving
  process. On this host, a group whose members have all exited answers the same way. Passing
  over that EPERM therefore never skips a signal that could have been delivered.
- **Passing a cleanup:** a cleanup passes only through `group_exists` returning false, that is,
  ESRCH. The direct child is a session leader, cannot leave its group, and is reaped only by
  this process. When the group is absent, the child has therefore been reaped, and `reaped: true`
  is accurate.
- **Persistent EPERM:** a group that keeps answering EPERM fails closed at the cleanup ceiling
  with the original `Stop`:
  - after 2,002 ms, simulated at the `os.killpg` boundary (D3);
  - after 2,148 ms, for real (D4).
- **The direct child:** no new unreaped-child path exists.
  - An exited direct child is reaped by the next `poll()`. D2 passes in 0.03 ms.
  - In a group that keeps answering EPERM, the direct child is already reaped, or it cannot be
    signalled.
  - The only remaining unreaped case is the original's final SIGKILL followed at once by
    `poll()`, which predates the amendment.
- **`run_process`'s check after exit:** a descendant that has exited but is not yet reaped now
  refuses the run, which is conservative.
- **The race at the check after exit:** it resolves in the same direction. The direct child is
  already reaped there, because the loop exits only after `poll()` returns.
- **Imports:** the list `Clock`, `Stop`, `LIMITS`, `inventory`, `json_bytes` and `_reap` is
  complete and minimal. The standard library's `signal` is also needed. `_reap` runs only after
  `Popen` has reaped the child, so it cannot hide the exit status.
- **`run_process`:** its body is token-identical to W1's. Its names `group_exists` and
  `terminate_group` resolve to the module's own definitions.
- **The amended variant (R4, R5):** built by exact text edits, it passed W1's four real-child
  cases 20 of 20 each. So did an unsafe variant, which A-01 addresses.

### Question 3: are the replaced clauses complete and consistent?

No. The gaps are:

- CONTRACT.json `controls` MC14, the machine-readable control table (A-01);
- the statement of the change set, which differs between row S4, `supervisor.only_change`, the
  section 5 comparison row and MC14 (A-01);
- section 10 and `labels.carried_with`, which the design-revision rule would change (A-02);
- `supervisor.assertion_meanings["cleanup.passed"]`, `supervisor.guarantees.kept`,
  `substitutions.S4`, row S4's Reason and Effect cells, section 5's "unchanged group check after
  exit" sentence, and the scope of "first list" (A-03).

These clauses need no change:

- section 1's "Kept unchanged" table;
- MC12's and MC13's expected outcomes, and MC17;
- `never_supported`;
- the meanings of `reaped` and `handles_closed`;
- `p05_control_map`, unless controls are added under A-01.

### Question 4: is the version decision acceptable?

Not as written (A-02).

- **For keeping 0.2.0:** no reviewed implementation, no preparation and no contract result
  exist. The change is fail-closed and confined to the supervisor. A design revision with an
  identified decision can be a sufficient version in that state.
- **Against it as written:**
  - The stated premise is contradicted by W1's 0.2.0-labelled module and tests in the
    candidate tree.
  - The safeguard that every result names its design revision appears in no replaced clause,
    and the amendment lists every label as unchanged.
  - Earlier semantic changes in this contract family each got their own version (inspection
    plans /0.1.2 to /0.1.4).

Once A-02's changes are made, keeping 0.2.0 is acceptable.

### Question 5: anything else?

- **A-04:** a group can keep answering EPERM with no permission refusal at all.
- **A-05:** the stricter meaning of absence, and launchd's reaping, depend on the host.
- **A-06:** the evidence is cited without digests, and the cited test runs without their logs.
- **A-07:** dependent phase records, and W1's development guard, still restate the superseded
  rule.

None of these makes the decision itself unsafe.

## 3. Findings

### A-01 (mandatory): no control exercises the amended rule, and MC14 is inexact

**Location:**
- AMENDMENT-001.md section 3, row "Section 9, MC14", and section 4, "Controls";
- AMENDMENT-001.json `replaces["CONTRACT.md section 9 MC14"]`;
- CONTRACT.json `controls` (MC12 to MC14) and `p05_control_map.CH19`.

**Issue:**
- **MC12 and MC13 cannot tell the rules apart.** The amendment keeps every control's expected
  outcome except MC14's. An unsafe scratch variant that counts EPERM as absent passed W1's four
  real-child cases 20 of 20, exactly like the amended variant (R5).
- **The unsafe variant hides failures.**
  - It passes a cleanup whose simulated member never exits: `passed`,
    `process_group_absent` and `reaped` are all true after 0.1 ms (D3).
  - It accepts a real run whose group still answers EPERM afterwards (D4).
- **MC14 is the only discriminator, and only by review.** A reviewer must read section 2 for it
  to work. Its amended expected outcome says where tokens may differ, not what the handling
  returns. The unsafe `except (ProcessLookupError, PermissionError): return False` also differs
  only at "the PermissionError clause of `group_exists`" (R4).
- **The counts disagree.**
  - MC14 says "the precondition and the three EPERM handlings".
  - The section 5 row says "three changes", and counts the precondition among them.
  - There are four EPERM handling sites: one in `group_exists` and three in `terminate_group`.
- **Row S4 and `supervisor.only_change` describe less.** They name only "the counting of an EPERM
  group answer as a present group", not the passing over of a refused send.
- **The fail-closed claim of section 2 has no control.**
- **CONTRACT.json `controls` is not named.** It holds the full control table (contract
  section 9), and its MC14 entry is named as replaced in neither form.
- **The rules call for it.** AGENTS.md asks for conformance evidence with a semantic change.
  Contract section 9 places such obligations in the controls, which an independent author
  freezes from the contract.

**Required change:**
1. Add NOT_RUN control obligations under CH19 in `p05_control_map`, with their Node and other
   start counts:
   - **(a), real:** a group whose only member is the supervisor's exited, unreaped direct child.
     `group_exists` is true; after reaping, it is false (as in D1).
   - **(b), real:** `terminate_group` started on that group returns the original passed
     receipt, with no `PermissionError` (as in D2).
   - **(c):** a group that keeps answering EPERM, either real as in D4, or simulated at the
     `os.killpg` boundary and labelled, as in D3. Expected: the original cleanup-ceiling `Stop`,
     `cleanup.passed` false, and never `process_group_absent: true`.
2. State the allowed token differences once, exactly, as token sequences:
   - in `group_exists`, `except PermissionError: return True`, placed before
     `except ProcessLookupError`;
   - in each of `terminate_group`'s three send clauses, `(ProcessLookupError, PermissionError)`.

   Use that one statement, with a correct count, in row S4, `supervisor.only_change`, the
   section 5 comparison row and MC14.
3. Name CONTRACT.json `controls` MC14, and every added control, among the replaced clauses in
   both forms.

### A-02 (mandatory): the version decision rests on an inaccurate premise and on an unrecorded label rule

**Location:**
- AMENDMENT-001.md, the "Contract version" paragraph, and section 3, "Unchanged" ("every label");
- AMENDMENT-001.json `contract_version_and_schemas` and `unchanged`.

**Issue:**
- **The premise is inaccurate.** The amendment says: "Nothing has been implemented, prepared or
  executed under 0.2.0, so no result or document exists that could be confused with an amended
  one."
  - The candidate tree contains W1's `prototypes/static_tray_v01/supervisor_darwin_v01.py` and
    `tests/test_supervisor_darwin_v01.py`.
  - Both are labelled `ontokin.current-host-readback/0.2.0` and implement revision 3's S4. The
    module's docstring says "Every other name comes unchanged from `supervisor.py`".
  - Their development tests were run, and section 1 of the amendment cites them.
  - After the candidate, `939942e3` committed W2's 0.2.0 preparer route.
- **The safeguard is not recorded in any clause.** "Every 0.2.0 result names the design
  revision it follows" is a new obligation on results.
  - Contract section 10 and `labels.carried_with` carry no design revision.
  - The amendment replaces neither, and it lists "every label" as unchanged.
  - The adopted files stay byte-identical, with `revision.number` 3 and no pointer to the
    amendment.
  - As written, nothing makes a result name revision 4.
- **Precedent.** Earlier semantic changes in this contract family each got their own version:
  inspection plans /0.1.2, /0.1.3 and /0.1.4, each "preserving earlier behaviour" (the P16, P17
  and P24 adoptions).
- **D-03 is outside the amendment.** The Director's decision D-03, recorded at `a97ef91d` after
  the candidate, states the intended rule: `"design_revision": 4` in every 0.2.0 document. But
  it is outside the amendment, and that file's own preamble says that contract changes go
  through an amendment.

**Required change:** either give the change its own version, or keep 0.2.0 and do three things:
1. State the premise exactly:
   - no reviewed or accepted implementation, no preparation, and no contract result or refusal
     document exists;
   - W1's checkpoint `a2376191` is the only implementation of revision 3: unreviewed,
     superseded, and kept as failed evidence.
2. Add the design revision and the amendment identifier to section 10's carried labels and to
   `labels.carried_with`, as replaced clauses in both forms. D-03's list can serve. Remove
   "every label" from the list of unchanged clauses.
3. Require the adoption record to state that from design revision 4 on,
   `ontokin.current-host-readback/0.2.0` means CONTRACT.md and CONTRACT.json as amended by
   P33-AMENDMENT-001.

### A-03 (nonmandatory): other affected clauses are left standing

**Location:**
- CONTRACT.json `supervisor.assertion_meanings["cleanup.passed"]`, `supervisor.guarantees.kept`
  and `substitutions.S4`;
- CONTRACT.md section 1, row S4's Reason and Effect cells, and section 5's first list and its
  "No descendant" paragraph.

**Issue:** the amendment says that everything else in the contract stands, yet these clauses are
affected:
- **`cleanup.passed`:** its MD row is replaced, but its JSON key is not.
- **`guarantees.kept`:**
  - It still reads "a live member of the child's process group after exit refuses the run".
    Under the amendment, an exited but unreaped member also refuses the run, and so does a
    member that this process may not signal.
  - "SIGTERM then SIGKILL of the group within 2,000 ms" does not say that a send refused with
    EPERM is passed over.
- **"The unchanged group check after exit" (section 5):** the check's tokens are unchanged, but
  its probe is not.
  - A descendant that has exited but that launchd has not yet reaped now refuses the run, with
    "Child exited while an owned descendant remained".
  - The amendment does not state this consequence of "Stricter".
- **Row S4 and `substitutions.S4`:** the Reason and Effect cells, and `substitutions.S4`, still
  describe only the precondition.
- **"Section 5, first list":** the amendment does not say whether the nested list "Everything
  else stays as in the original" is replaced. That list includes "`terminate_group`'s SIGTERM,
  mandatory SIGKILL and bounded reaping".

**Required change:** name each clause as replaced, with its amended text in both forms, or state
why it stands. For "first list" and row S4, quote the exact text that is replaced.

### A-04 (nonmandatory): a group can keep answering EPERM without any permission refusal

**Location:**
- AMENDMENT-001.md section 1 ("That last member is either…") and section 2 ("Fail-closed
  case");
- AMENDMENT-001.json `finding.effect_on_adopted_S4` and `decision.fail_closed`.

**Issue:**
- **The analysis names only two cases.** It says the unreaped last member is "either the direct
  child before the next poll, or a descendant before launchd reaps it". It attributes a lasting
  EPERM only to a genuine permission refusal.
- **D4 produces a third case, with no privilege.**
  - A descendant moves itself into its own process group and never reaps its exited child.
  - That child stays in the owned group, so the group answers EPERM until its parent ends.
- **The amended code handles it.** The run fails closed after 2,148 ms with the cleanup-ceiling
  `Stop`, which replaces "Child exited while an owned descendant remained". The escaped
  descendant survives, within "no enforcement against descendants".
- **The receipt cannot tell the causes apart:** this case, a permission refusal and a slow
  reaping look the same.

**Required change:** name this case in sections 1 and 2. State that the recorded reason does not
distinguish the causes of a lasting EPERM.

### A-05 (nonmandatory): the stricter meaning of absence, and launchd's reaping, depend on the host

**Location:**
- AMENDMENT-001.md section 2 ("Rule kept"), section 3 (the rows `process_group_absent` and
  section 12) and section 4 ("Stricter");
- AMENDMENT-001.json
  `replaces["CONTRACT.json supervisor.assertion_meanings.process_group_absent"]`.

**Issue:**
- **The meaning depends on this build.** "Absent means that no member, live or unreaped,
  remains" holds only because this build answers ESRCH after every member is reaped.
  - "The decision does not rely on the observation" is true for safety, since EPERM is never
    counted as absent.
  - It is not true for the stricter meaning.
- **The two forms differ.** The JSON says "which Darwin answers", where the MD says "on this
  host".
- **Reaping depends on launchd.** A cleanup with orphaned descendants passes only after launchd
  reaps them, outside the supervisor's control.
  - Observed: 1.5 ms to 1.8 ms.
  - A slower reaping can only delay or fail a cleanup.

**Required change:**
- Qualify the stricter meaning by the observed OS build, in both forms. Alternatively, make
  control A-01(a) part of each qualifying host's evidence.
- Add launchd's reaping to section 12's replacement as an assumption.

### A-06 (nonmandatory): evidence without digests, and run counts without their logs

**Location:** AMENDMENT-001.md section 1; AMENDMENT-001.json `finding.evidence`.

**Issue:**
- **The logs are outside Git.** The 12-run counts rest on W1's working logs:
  - `../../OntoKin-local/c271-p33/workers/W1/01-test-run-draft.txt` (`fcacda9a…`);
  - `02-repeat-real-child-runs.txt` (`fcd1bbf1…`);
  - `03-test-run-final.txt` (`68b5f1a4…`).

  The amendment cites none of them, though their tally matches (R7).
- **One run was not at the checkpoint.** Run 01 used a draft test file, whose source-binding
  test fails on `__name__`. At the checkpoint, that test passes. So "at the checkpoint above"
  holds for at most 11 of the 12 runs.
- **No digests.** The probe and its output are cited without SHA-256.

**Required change:**
- Cite the three logs by path and SHA-256, or retain them under `evidence/`.
- Give the evidence files' digests.
- Say which code each run used.

### A-07 (nonmandatory): dependent records still restate the superseded rule

**Location:**
- PHASE.json acceptance A2 ("a token-level comparison shows that only the precondition
  differs");
- IMPLEMENTATION-PLAN.md section 4.1 (it imports `group_exists` and `terminate_group`
  unchanged, and "Its only change");
- W1's checkpoint docstring, and its `IMPORTED` and body-globals development tests;
- W1's development guards `no_group_left` and `_gone`.

**Issue:**
- **The plan would conflict.** Once the amendment is adopted, these records contradict the
  contract. The plan treats such a difference as a defect.
- **W1's guards invert the rule.** They count EPERM as "gone", the opposite of the amended rule.
  A guard written that way would not report a group like D4's.

**Required change:**
- List these records in the adoption record, as follow-ups.
- Require the frozen controls' post-test checks to apply the amended rule: EPERM means present.

## 4. Reproduction

Every run used the checkout's `.venv/bin/python -I -S -B`, with
`TMPDIR="$(cd "$TMPDIR" && pwd -P)/"`, from the working directory `<review>/out`.

The inputs came from Git:
- `git archive a23761919e92c41489f26a57d02fa1d5dc9d8e19`, for `prototypes/__init__.py`,
  `prototypes/static_tray_v01/__init__.py`, `supervisor.py`, `supervisor_darwin_v01.py` and
  `tests/test_supervisor_darwin_v01.py`, extracted into `<review>/tree-a2376191`;
- the probe, through `git show 5dc76ccf:…/evidence/zombie_group_probe.py`. The copy is
  byte-identical to the committed probe: `baec807b…`.

The children are Python only.

| ID | Command | Observed |
| --- | --- | --- |
| R1 | `harness/zombie_group_probe.py` ×3 | Three byte-identical outputs (`4725c2f7…`). Case 1: EPERM, then ESRCH after `waitpid`. Case 2: 0 while the grandchild is alive; after SIGKILL, EPERM ×1, then ESRCH, at 1.5 ms. |
| R2 | `harness/run_w1_checkpoint.py <review>/tree-a2376191 12 …` | Observation test 12/12. Positive case 12/12. MC12: 8 passed, 4 `PermissionError`. MC13 timeout: 10 passed, 2 `PermissionError`. MC13 cancellation 12/12. |
| R3 | `harness/locate_w1_failures.py <review>/tree-a2376191 20 …` | MC12: 10 errors in 20. MC13 timeout: 4 in 20. Every error at `run_process:138 > terminate_group:135 > group_exists:107`, with `__context__` the original `Stop`. |
| R4 | `harness/build_variants.py <review>/tree-a2376191 <review>` | Two variants, built by exact text edits. Amended: one clause inserted in `group_exists`, three `except` clauses widened in `terminate_group` (six opcodes), `run_process` identical to W1's. The unsafe variant (EPERM counted as absent) differs from the original `group_exists` only by `(`, `, PermissionError )`. |
| R5 | `harness/run_w1_checkpoint.py <review>/tree-{amended,wrong} 20 … children-only` | Both variants pass the positive case, MC12, the MC13 timeout case and the MC13 cancellation case 20 of 20. |
| R6 | `harness/deterministic_checks.py <review>/tree-{a2376191,amended,wrong} …` | D1, D2 and D4 are real; D3 is simulated. See the table below. |
| R7 | Tally of `^(ERROR\|FAIL): ` in W1's three logs, and W1's three source tests at the checkpoint | 12 runs: MC12 10, MC13 timeout 3, MC13 cancellation 1, positive 0, all `PermissionError`. Run 01 used a draft test file; the checkpoint's source tests pass, 3 of 3. |
| R8 | `ps` for the review's children, and a listing of the temporary stages | None remain. |

R6 in detail:

| Case | Checkpoint `a2376191` | Amended | Unsafe variant |
| --- | --- | --- | --- |
| D1, real: `group_exists` on an exited, unreaped direct child | `PermissionError` at `group_exists:107` | true | false |
| D1, after reaping | ESRCH, false | ESRCH, false | ESRCH, false |
| D2, real: `terminate_group` on that child | `PermissionError` at `terminate_group:127`, the SIGTERM send | passed, in 0.03 ms | passed |
| D3, simulated: every `killpg` answers EPERM | `PermissionError` at the first send | the ceiling `Stop` after 2,002 ms: 167 calls, signals 0, 9 and 15 | **passed in 0.1 ms**, with `reaped` and `process_group_absent` true |
| D4, real: lasting EPERM | `PermissionError` at line 127, raised while handling the first `PermissionError` from the group check after exit | the ceiling `Stop` after 2,148 ms, `cleanup.passed` false | **run accepted**: exit status 0, cleanup passed, while the group still answers EPERM |

In D4, the escaped descendant is alive after the run in all three variants. The harness then
killed it, and every group in D4 answered ESRCH.

**Harness digests:**
- `build_variants.py` `9c5ebd88…`;
- `deterministic_checks.py` `6a70af27…`;
- `locate_w1_failures.py` `45436c22…`;
- `run_w1_checkpoint.py` `3aba04fc…`. This digest is the final text. R2 ran an earlier text that
  lacked only the optional `children-only` argument.

**Output digests:**
- `w1-checkpoint-12-runs.json` `28cf87fb…`;
- `w1-failure-sites-20-runs.json` `b39d06b2…`;
- `w1-tests-on-amended-20-runs.json` `832d3e9b…`;
- `w1-tests-on-wrong-20-runs.json` `9184c01b…`;
- `variant-token-comparison.json` `7f5e0c11…`;
- `deterministic-a2376191.json` `dfdb78ec…`;
- `deterministic-amended.json` `2ceccb1e…`;
- `deterministic-wrong.json` `02347144…`.

## 5. Scope and policy

- **Started:** the checkout's Python interpreter and its Python children, and Git, `tar`,
  `shasum`, `ps` and `grep` for reads.
- **Not started:** no Node, `ldd`, `codesign`, `sw_vers` or driver.
- **Nothing** was downloaded or installed.
- **Git:** read commands only. Two early `git status` runs did not pass `--no-optional-locks`,
  so they may have refreshed the index's stat cache. No object, ref, index entry or working file
  changed.
- **Writes:** this review's two files, and scratch material under `<review>`. The scratch
  material includes the two variant trees, which are not repository files.
- **Processes:** none was left running.
