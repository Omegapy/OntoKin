# Re-review of P33-AMENDMENT-001, revision 2

**Candidate:** commit `86a0e750ae48039798234585b8913f0ae9be7210`, tree `f579ca91…`, parent
`a97ef91d…`. It changes the two amendment files and adds the retained first review:

| File at `86a0e750` | Bytes | SHA-256 |
| --- | ---: | --- |
| `docs/engineering/localized-repair-c271/macos-implementation-p33/AMENDMENT-001.md` | 17,554 | `6faac1ef…c326` |
| `docs/engineering/localized-repair-c271/macos-implementation-p33/AMENDMENT-001.json` | 21,872 | `c325c79a…e567` |
| `…/AMENDMENT-001-REVIEW-001.md` and `.json` | 26,423 and 23,977 | `7fe34ca4…`, `82df3b37…`: byte-identical to my originals |

**Reviewer:** the author of AMENDMENT-001-REVIEW-001, re-reviewing for C271-P33 (Director
`c271-p33-a99647756bed`) in local mode, read-only in the repository. That review's context
carries over. I wrote none of revision 2. The review was completed on 2026-11-26 at about
15:55Z.

During the review, the head moved from `86a0e750` to `2fcf5505`, through:
- W4's checkpoint `b377ab96`;
- decisions `767aeafc`;
- W3's checkpoint `57918413`;
- decisions `2fcf5505`.

At that head, the amendment files, the P31 contract, `supervisor.py` and W1's module are
unchanged.

Paths are relative to the checkout. `<review>` stands for
`../../OntoKin-local/c271-p33/reviews/amendment-001`.

## Verdict: ACCEPT_WITH_NONMANDATORY_FINDINGS

- **The mandatory findings are resolved.** A-01 and A-02 are resolved, and so are A-03 to A-07.
- **The new controls work.** MC37 to MC39 tell the amended rule apart from the unsafe one, and
  their expected outcomes match the original receipts. I reproduced both.
- **The quotations are exact.** Every adopted value that revision 2 quotes matches the adopted
  contract exactly.
- **Five new findings, all nonmandatory,** A-08 to A-12. They correct precision and consistency
  points that revision 2 introduced or left. The two that matter most are in A-08:
  - MC37's frozen input must establish the child's exit independently of the probe.
  - MC39's simulated case needs a stated route and start count.
- **One observation** lies outside the amendment (O-01).

## 1. Checks run

| # | Check | Result |
| --- | --- | --- |
| K1 | Commit, tree, parent, diff stat | Four files: the two amendment files and the two retained review files. |
| K2 | Retained REVIEW-001 | **Byte-identical** to my originals. |
| K3 | Adopted payloads and code | CONTRACT.md (`42db98dc…`) and CONTRACT.json (`c843fc96…`) equal ADOPTION.json's digests. `supervisor.py` (`c47b84ab…`) and W1's module are unchanged. |
| K4 | Every "adopted" value in `replaces_contract_md` and `replaces_contract_json` (R10) | **0 mismatches.** The 14 CONTRACT.md quotations each occur exactly once after line wraps are joined, and the S4 and MC14 table cells are equal cell for cell. The 12 CONTRACT.json values are equal as parsed values. |
| K5 | Section 3.2's five change sites, against the first review's amended variant | They agree: one inserted clause in `group_exists`, three widened `except` clauses in `terminate_group`, and `run_process` unchanged apart from the precondition. |
| K6 | The change set in each place | Consistent, at five sites with four EPERM handlings, in rows 1, 8 and 11, in `supervisor.only_change` and in `substitutions.S4`. |
| K7 | Two forms of the amended text, and the JSON keys (R14) | See A-09. |
| K8 | Control entries | The amended entries add `amended_by` and `added_by`, keys that the adopted entries lack. They record provenance; no finding. |
| K9 | Callers | W3's committed observer reaches the supervisor through `supervisor_darwin_v01` and calls no Linux helper. Apart from `supervisor.py`, only `tools/check_local.py` calls `killpg` (O-01). |

## 2. Status of AMENDMENT-001-REVIEW-001's findings

| Finding | Status | Basis |
| --- | --- | --- |
| A-01 (M) | **Resolved** | **Controls:** MC37 to MC39 are added, with start counts, and CH19 is updated. **Change set:** the five sites are stated once, in section 3.2, as exact tokens, and are used identically in rows 1, 8 and 11, `only_change` and `substitutions.S4`. **JSON:** CONTRACT.json `controls` is named. **Reproduced (R12):** the amended variant meets all three controls; the unsafe variant fails MC37 and MC39. **Residual:** A-08. |
| A-02 (M) | **Resolved** | **Premise:** stated exactly for the committed checkpoints at `86a0e750`: W1's `a2376191` and W2's `939942e3`. **Labels:** section 10 and `labels.carried_with` now carry the design revision and the amendments. "Every label" is no longer listed as unchanged. **Meaning:** from revision 4 on, `0.2.0` means the amended contract, and the adoption record is to state this. **Residuals:** a wrong cross-reference (A-09); D-03 and the premise list are time-scoped (A-12). |
| A-03 | **Resolved** | Rows 1 to 10, 15 and 16 name each place, and every adopted quotation matches (K4). Section 5 states the refusal at the group check after exit. **Residual:** E13 (A-09). |
| A-04 | **Resolved** | Cause 3 appears in section 2. Section 3.3 states that the reason does not distinguish the causes. |
| A-05 | **Resolved** | Rows 9 and 14 and `trust_assumptions[2]` qualify the meaning by build 25G83. MC37 runs again at MH. launchd's reaping is an assumption. The JSON no longer says "which Darwin answers". |
| A-06 | **Resolved in form** | Logs and evidence are cited by path and SHA-256, and the digests are correct. **Residual:** the code attribution of log 02 is inaccurate (A-10). |
| A-07 | **Resolved as a commitment** | The adoption record is to list the superseded records and W1's follow-ups. The rule for post-test checks is stated in section 4. **Residual:** further follow-ups (A-12). |

## 3. The three questions

### Question 1: is each finding resolved?

Yes, as section 2 shows. Residuals A-08 to A-12 are nonmandatory.

### Question 2: do MC37 to MC39 discriminate, and do their expected outcomes match the original receipts?

They discriminate, and their outcomes match (R12). I ran each control as worded against four
variants of the Darwin module:
- the revision-3 checkpoint;
- the amended variant;
- the unsafe variant, which counts EPERM as absent;
- a variant that counts EPERM as present but keeps the original sends.

Results:
- **The unsafe variant**
  - fails MC37: `group_exists` is false while the child is unreaped;
  - fails MC39 (a): the run is accepted, with `process_group_absent: true`;
  - fails both routes of MC39 (b);
  - passes MC38. Section 4 rightly does not claim otherwise.
- **The variant that keeps the original sends** fails MC38 and MC39 with `PermissionError`.
  MC38 therefore covers the sends.
- **The amended variant meets every expected outcome:**
  - **MC37:** true while the child is unreaped, false after reaping.
  - **MC38:** the original four-key receipt `{"passed": true, "elapsed_ms": 0.04, "process_group_absent": true, "reaped": true}`.
  - **MC39 through `run_process`:** the ceiling `Stop` (`OTRAY-E-BACKEND`, "Owned process group
    cleanup exceeded stage or transaction ceiling", `REJECTED`), after 2,126 ms real and
    2,021 ms simulated. The receipt holds `cleanup: {"passed": false, "reason": "Owned process
    group cleanup exceeded stage or transaction ceiling"}` with `error` equal to that `Stop`.
    This is exactly what the original `run_process` records when `terminate_group` raises.
- **Afterwards:** every started group answered ESRCH in every variant.

Two conditions of the control specification decide whether this holds (A-08).

### Question 3: does revision 2 introduce anything new that is wrong or inconsistent?

Nothing that is unsafe. Every adopted quotation is exact (K4). The nonmandatory points are:
- a wrong cross-reference, differences between the two forms of the amended text, two JSON keys
  that do not resolve as written, and E13 (A-09);
- an inaccurate code attribution of log 02 (A-10);
- an unsupported comparison with the Linux contract (A-11);
- follow-ups that the adoption record should carry (A-12).

## 4. New findings

### A-08 (nonmandatory): two conditions decide whether MC37 to MC39 discriminate

**Location:** AMENDMENT-001.md section 4; AMENDMENT-001.json
`replaces_contract_json["controls (added)"]`.

**Issue:**
- **MC37 and MC38 need the child to have exited first.** If the child is still alive when the
  probe runs, `killpg` returns 0, and both the amended and the unsafe rule answer true, so MC37
  would not discriminate.
  - The case says "exited, unreaped", but not how that state is established independently of
    the code under test.
  - In the qualification Python, `os.waitid` is not available, and `os.kill(pid, 0)` returns 0
    for the unreaped child, so neither can establish the exit.
  - kqueue `NOTE_EXIT` can: right after it, `killpg` answered EPERM three times (R11).
- **MC39 (b) has no stated route.**
  - The expected receipt `cleanup: {"passed": false, …}` exists only through `run_process`,
    which starts a child. MC39 counts one other start, and case (a) already uses it.
  - Through `terminate_group` with a stand-in process, there is no start and no receipt, only
    the raised `Stop`.
  - Both routes discriminate (R12).

**Required change:**
- In MC37 and MC38, state that the exit is established before the probe, without reaping and
  independently of the code under test, for example through kqueue `NOTE_EXIT`.
- State MC39 (b)'s route. Either count its start, which gives two other starts through
  `run_process`, or give (b)'s expected outcome as the raised `Stop` alone.
- Optionally, say that MC38 covers the send handling.

### A-09 (nonmandatory): text consistency

**Location:**
- AMENDMENT-001.md section 1 ("section 3, row 10") and section 3.4, rows 1, 2, 3 and 11 to 14;
- AMENDMENT-001.json `replaces_contract_md`, and the keys of `replaces_contract_json`;
- CONTRACT.md section 2, row E13.

**Issue:**
- **A wrong row reference.** Section 1 points to "section 3, row 10" for the labels. Row 10 is
  the "No descendant" sentence; the labels are row 13.
- **The two forms differ.** Section 3.4 says that the JSON holds the exact amended text, but
  (R14):
  - rows 1, 2 and 11 lose their code spans in the JSON, for example `EPERM` and `run_process`;
  - row 13 differs by its final semicolon;
  - row 14 differs in wording: separate sentences in the MD, semicolons in the JSON;
  - for section 9's added rows, the JSON gives only the identifiers, not the rows.
- **Two JSON place keys do not resolve as written** (R14):
  - `supervisor.assertion_meanings.cleanup.passed`: the actual key is `"cleanup.passed"`;
  - `controls.MC14`: `controls` is a list.
- **E13 is left standing.** Row 3 now says the meanings are "narrower … stricter …", while
  CONTRACT.md section 2's E13 row still says "narrowed meaning of the lifecycle assertions
  (section 5)", and the amendment does not name it.

**Required change:**
- Point section 1 to row 13.
- Make the MD's quoted amended texts identical to the JSON's. Keep CONTRACT.md's Markdown in the
  JSON's CONTRACT.md places, and give the exact text of the added rows.
- Write the two keys as the MD does: `assertion_meanings["cleanup.passed"]` and
  `controls[id=MC14]`.
- Name E13's cell, or state why it stands.

### A-10 (nonmandatory): the code attribution of W1's log 02

**Location:** AMENDMENT-001.md section 2, the table of logs, column "Code"; AMENDMENT-001.json
`finding.evidence`.

**Issue:**
- **Log 02 was run on a different test file.** It is attributed to "checkpoint `a2376191`", but
  its tracebacks place the MC12, MC13 timeout and MC13 cancellation calls at test-file lines
  393, 417 and 437. The checkpoint has them at 395, 419 and 439. Those ten runs used an
  intermediate test file (R13).
- **What does agree:** the module's traceback lines (106, 107, 126 and 138) match the checkpoint
  in all three logs, and log 03 matches the checkpoint's test line 419.
- **No log shows byte identity.** REVIEW-001's R2 and R3 reproduced the finding at the exact
  checkpoint bytes.

**Required change:** attribute log 02 to an intermediate test file whose module line numbers
match the checkpoint's. Say that the logs corroborate the module by line numbers, not by bytes.

### A-11 (nonmandatory): an unsupported comparison with the Linux contract

**Location:** AMENDMENT-001.md section 5, "Stricter" ("as an unreaped member also does under the
Linux contract").

**Issue:**
- **Nothing records the Linux answer.** No evidence in the amendment, the contract or the
  repository records what Linux's `killpg(pid, 0)` answers for an unreaped member. The
  Linux-side files that mention zombies concern reaping only.
- **It cannot be observed here.** Local mode has no Linux executor (P30-EXECUTOR-001).
- **The JSON form does not carry the claim.**

**Required change:** drop the comparison, or mark it as not observed in this phase.

### A-12 (nonmandatory): follow-ups for the adoption record

**Location:** AMENDMENT-001.md sections 1 and 6 (A-07); IMPLEMENTATION-PLAN.md section 6;
DIRECTOR-DECISIONS.md, decisions D-03 and D-04.

**Issue:**
- **The plan omits the new controls.** Its control assignment does not list MC37 to MC39. MI
  executes all three, and MC37 runs again at MH.
- **D-03 and D-04 name fewer label fields.** They name only `design_revision`. Revision 2's
  label carries `design_revision` 4 and `amendments` [`P33-AMENDMENT-001`].
- **The premise's list is already outdated.** It is exact at `86a0e750`. After it, W4's
  checkpoint `b377ab96` and W3's `57918413` were committed. They implement clauses that the
  amendment does not change.

**Required change:** have the adoption record list these items with A-07's follow-ups, and
restate the premise as of the adoption.

## 5. Observation outside the amendment

**O-01:** `tools/check_local.py` `stop_process` is unchanged from main `51223c9b`. It catches only
`ProcessLookupError` around its SIGTERM `killpg`.

On Darwin, a step may time out at the moment its last group member has exited but is not yet
reaped. A `PermissionError` then escapes `stop_process`, and the caller's `except OSError`
records the step as "unavailable" instead of as the timeout.

This is by code only and was not observed. It lies outside S4 and needs no change to the
amendment. It could be recorded for the driver's owner.

## 6. Reproduction

All runs used the checkout's `.venv/bin/python -I -S -B`, with
`TMPDIR="$(cd "$TMPDIR" && pwd -P)/"`, from `<review>/rev2`. The inputs came from
`git show 86a0e750:…`. Children are Python only.

| ID | Command | Observed |
| --- | --- | --- |
| R10 | `harness/check_adopted_quotes.py inputs/CONTRACT.md inputs/CONTRACT.json inputs/AMENDMENT-001.json inputs/ADOPTION.json` | 0 mismatches across 26 places. The adopted digests equal ADOPTION.json's. |
| R11 | Inline kqueue check: one child in a new session, then stdin closed | `os.waitid` absent. `NOTE_EXIT`: 1 event. Right after it, `killpg` answers EPERM ×3 and `os.kill(pid, 0)` returns 0. After `wait`, ESRCH and exit status 0. |
| R12 | `harness/mc37_39_checks.py <review>/tree-{a2376191,amended,wrong,nosend} <label> <review>/rev2/mc37-39-<label>.json`. `tree-nosend` is `tree-amended` with its three send clauses restored to `except ProcessLookupError:`. | See the table below. |
| R13 | `grep` of the traceback line numbers in W1's logs 01 to 03, compared with the checkpoint's files | Log 02: test lines 393, 417 and 437, against the checkpoint's 395, 419 and 439. Module lines 106, 107, 126 and 138 match in all logs. Log 03 matches at 419. Log 01 has the draft's lines (241, 345, 369). |
| R14 | Inline comparison of the section 3.4 table with `replaces_contract_md`, and resolution of the JSON keys | Rows 1, 2 and 11 differ by code spans, row 13 by a semicolon, row 14 in wording. `assertion_meanings["cleanup"]` raises `KeyError`. |
| R15 | `ps` for the review's children, and a listing of the temporary stages | None remain. |

R12 in detail:

| Control | Revision-3 checkpoint | Amended | Unsafe (EPERM counted as absent) | Original sends kept |
| --- | --- | --- | --- | --- |
| MC37, real (exit through `NOTE_EXIT`) | `PermissionError` while unreaped | true, then false | **false while unreaped** | true, then false |
| MC38, real | `PermissionError` at the SIGTERM send | passed receipt in 0.04 ms | passed | `PermissionError` |
| MC39 (a), real, through `run_process` (1 start) | `PermissionError` | ceiling `Stop` after 2,126 ms; `cleanup` `{"passed": false, "reason": …}`; `error` equals the `Stop` | **run accepted**, `process_group_absent: true` | `PermissionError` |
| MC39 (b), simulated, through `run_process` (1 start) | `PermissionError` | ceiling `Stop` after 2,021 ms; same receipt | **run accepted** | `PermissionError` |
| MC39 (b), simulated, through `terminate_group` with a stand-in (0 starts) | `PermissionError` | ceiling `Stop` after 2,002 ms; no receipt on this route | **passed** | `PermissionError` |

In every variant, every started group answered ESRCH after the post-test wait. In MC39 (a), the
escaped descendant was alive after the run until the harness killed it.

**Digests:**
- `harness/check_adopted_quotes.py` `496dd0d5…`
- `harness/mc37_39_checks.py` `1d500e4f…`
- `rev2/adopted-quotes.json` `3027a865…`
- `rev2/mc37-39-a2376191.json` `4cbbf505…`
- `rev2/mc37-39-amended.json` `1f218ac5…`
- `rev2/mc37-39-wrong.json` `73aa8f58…`
- `rev2/mc37-39-nosend.json` `e47aa48b…`

## 7. Scope and policy

- **Started:** the checkout's Python interpreter and its Python children, and `git` (all with
  `--no-optional-locks`), `tar`, `shasum`, `ps`, `grep`, `stat` and `cp` for reads and scratch
  copies.
- **Not started:** no Node, `ldd`, `codesign` or driver.
- **Nothing** was downloaded or installed.
- **Repository:** no write to the repository or its index.
- **Writes:** this review's two files, and scratch material under `<review>`.
- **Processes:** none was left running.
