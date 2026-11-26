# Amendment 001 to `ontokin.current-host-readback/0.2.0`: Darwin's group probe

**Identifier:** P33-AMENDMENT-001. It amends the adopted contract
`ontokin.current-host-readback/0.2.0`, profile `darwin-arm64-v1`
([CONTRACT](../macos-contract-design-p31/CONTRACT.md),
[CONTRACT.json](../macos-contract-design-p31/CONTRACT.json),
[adoption](../macos-contract-design-p31/ADOPTION.json)), as design revision 4. Machine-readable
form: [AMENDMENT-001.json](AMENDMENT-001.json).

**Decision state:** proposed by C271-P33's Director. Only a separate adoption record can adopt
it, after an independent review. Like the contract, it is design only.

**Revision history:**
- Revision 1 (commit `5dc76ccf1a763a3454e34f97db842a2192d3129e`) was rejected by
  [AMENDMENT-001-REVIEW-001](AMENDMENT-001-REVIEW-001.md) on two mandatory findings:
  - A-01: no control told the amended rule from an unsafe one, and MC14 was inexact;
  - A-02: the version premise was inexact, and no label carried the design revision.
- This revision 2 resolves A-01 to A-07, as section 6 maps.

## 1. Version and premise

- **Identifier:** the contract identifier and every schema identifier stay `0.2.0`.
- **Premise:** at this amendment, no reviewed or accepted implementation exists under 0.2.0. No
  preparation exists either, and no contract result or refusal document. The only
  implementations are MI's unreviewed working checkpoints:
  - W1's Darwin supervisor (`a23761919e92c41489f26a57d02fa1d5dc9d8e19`) implements revision
    3's S4. This amendment supersedes it, and it is kept as failed evidence.
  - W2's preparer route (`939942e31b9bbfa8768269ff6274a66c183d2202`) implements revision 3's
    S6, which this amendment does not change.
- **Meaning from revision 4 on:** `ontokin.current-host-readback/0.2.0` means CONTRACT.md and
  CONTRACT.json as amended by P33-AMENDMENT-001. The adoption record states this, and every
  result names its design revision and adopted amendments (section 3, row 10).
- **Adopted files:** the adopted contract files stay byte-identical.

## 2. Finding P33-SUPERVISOR-001

**Host:** macOS 26.6.2, build 25G83, Darwin 25.6.0, arm64, CPython 3.12.13. Observed on
2026-11-26:

| Group state | `os.killpg(pgid, 0)` |
| --- | --- |
| a member is alive | returns |
| every remaining member has exited, none is reaped yet | fails with `EPERM` (`PermissionError`) |
| after reaping | fails with `ESRCH` (`ProcessLookupError`) |

**Evidence:**
- **The Director's probe:** [zombie_group_probe.py](evidence/zombie_group_probe.py) (SHA-256
  `baec807b7b269d95dbf1a691b10da7e86f1af5b7d823e3d70fbcaf330b05ba29`) and its output
  [zombie_group_probe.out.json](evidence/zombie_group_probe.out.json) (SHA-256
  `1394f206341698e37ace67c878ca598fae5926959941dde51af0ddcd869854dd`).
  - A direct child in its own group, exited and not reaped, answered `EPERM`. After `waitpid`
    it answered `ESRCH`.
  - An orphaned grandchild, once killed, answered `EPERM` for one 1 ms poll, then `ESRCH`.
    launchd had reaped it within 1.8 ms.
- **W1's development tests.** Their working logs are kept beside the clone in
  `../OntoKin-local/c271-p33/workers/W1/`:

  | Log | SHA-256 | Runs | Code |
  | --- | --- | --- | --- |
  | `01-test-run-draft.txt` | `fcacda9a15cba087165d34f12017545f40e27b1895fcace9b280e4387ecad652` | 1 | an earlier draft of the test file; the module as at the checkpoint |
  | `02-repeat-real-child-runs.txt` | `fcd1bbf192bf8798d4ce8392386b7d5f9fb3a51e01ce27c2da9eaf51ea49d67a` | 10 | checkpoint `a2376191` |
  | `03-test-run-final.txt` | `68b5f1a44d7de88ba0cfd7a3ceb71f2f1a36cf6ec3d05f5471f285d04f279e76` | 1 | checkpoint `a2376191` |

  - **Failures across the 12 runs, each a `PermissionError`:**
    - MC12: 10 runs;
    - the MC13 timeout case: 3 runs;
    - the MC13 cancellation case: 1 run;
    - the positive case: none.
  - **Observation test:** it records the sequence 0, then `EPERM`, then `ESRCH`.
- **The independent review:** its R and D records reproduced each path, and its counts matched
  the logs.

**Where revision 3's S4 breaks:** the imported `group_exists` treats only `ESRCH` as an answer.
`EPERM` escapes as `PermissionError` in three places:
- `terminate_group`'s polling;
- `terminate_group`'s three `killpg` signal sends, which catch only `ProcessLookupError`;
- `run_process`'s group check after the child exits.

**The caller then:**
- receives `PermissionError` instead of the original `Stop`;
- gets no cleanup receipt;
- after a timeout or a cancellation, can be left with an unreaped direct child.

**What answers `EPERM`.** A group of unreaped members answers `EPERM` while it stays unreaped.
Three causes are known:
1. **The direct child,** after it exits and before the supervisor's next `poll()`. This lasts
   briefly.
2. **An orphaned descendant,** after it exits and before launchd reaps it. This lasts briefly;
   1.5 to 1.8 ms were observed.
3. **A member whose parent never reaps it.** A descendant moves itself into its own process
   group and never reaps its exited child, which stays in the owned group. The group then
   answers `EPERM` for as long as that parent lives. No privilege is needed. The review
   reproduced this case (D4).

A genuine permission refusal answers `EPERM` too, for example a member that this process may
not signal.

This answers contract section 12's open question, "whether Darwin's `killpg(pid, 0)` counts a
zombie group member". On this host and build, such a member makes the probe fail with `EPERM`.
The probe neither returns nor reports `ESRCH`.

## 3. Decision and replaced clauses

### 3.1 The rule

The Darwin variant re-implements `run_process`, `group_exists` and `terminate_group`. It imports
`Clock`, `Stop`, `LIMITS`, `inventory`, `json_bytes` and `_reap` unchanged from `supervisor.py`.
`supervisor.py` stays byte-identical, and it remains the Linux contract's supervisor.

The group counts as absent only when the probe reports `ESRCH`. An `EPERM` answer counts as
present, and a send refused with `EPERM` is passed over. It is never taken as proof of
absence.

### 3.2 Allowed differences

A token-level comparison of the three functions with the originals shows exactly five change
sites, four of which handle `EPERM`. Nothing else differs, docstrings and comments included.

1. **`run_process`:** the precondition block. The original's three statements
   `libc = ctypes.CDLL(None, use_errno=True)`, `if libc.prctl(36, 1, 0, 0, 0) != 0:` and
   `raise Stop("OTRAY-E-BACKEND", "Cannot establish Linux descendant reaping")` are replaced by
   statements that evaluate the Darwin precondition of contract section 5 and raise
   `Stop("OTRAY-E-BACKEND", …)` when it is unmet. The body's names `group_exists` and
   `terminate_group` resolve to the re-implementations.
2. **`group_exists`:** the clause `except PermissionError:` / `return True` is inserted
   immediately before `except ProcessLookupError:`.
3. **`terminate_group`,** the SIGTERM send: `except ProcessLookupError:` becomes
   `except (ProcessLookupError, PermissionError):`.
4. **`terminate_group`,** the SIGKILL send after the grace period: the same change.
5. **`terminate_group`,** the final SIGKILL send before the ceiling `Stop`: the same change.

### 3.3 Fail-closed consequence

A group that keeps answering `EPERM` fails at the cleanup ceiling. It fails with the original
`Stop("OTRAY-E-BACKEND", "Owned process group cleanup exceeded stage or transaction ceiling")`,
and the receipt holds `cleanup: {"passed": false, "reason": …}`.
- **Message:** this `Stop` replaces an earlier message of the same run, such as "Child exited
  while an owned descendant remained".
- **Causes not told apart:** the recorded reason does not tell the causes of a lasting `EPERM`
  apart: cause 3 of section 2, a permission refusal, or a slow reaping.
- **Escaped descendant:** a descendant that moved itself out of the group survives, within
  "no enforcement against descendants".

### 3.4 Replaced clauses

Each place below is given in short with its amended text. [AMENDMENT-001.json](AMENDMENT-001.json)
holds the exact amended text of each contract place.

| # | Contract place | Adopted text | Amended text |
| --- | --- | --- | --- |
| 1 | CONTRACT.md section 1, row S4, "macOS arm64 term" | "a Darwin variant with the same logic except that precondition (section 5)" | "a Darwin variant whose only changes are the precondition and the four `EPERM` handlings of P33-AMENDMENT-001 (section 5 as amended)" |
| 2 | Same row, "Reason" | "Darwin has no child-subreaper" | "Darwin has no child-subreaper, and its group probe answers `EPERM` for a group of unreaped members (P33-SUPERVISOR-001)" |
| 3 | Same row, "Effect on meaning" | "the lifecycle assertions keep their text with a narrowed meaning (section 5)" | "the lifecycle assertions keep their text with the meanings of section 5 as amended: narrower where descendants are re-parented to launchd, stricter where an unreaped or unsignalable member remains" |
| 4 | CONTRACT.md section 5, first list, first item | "It imports `Clock`, `Stop`, `LIMITS`, `inventory`, `group_exists`, `terminate_group` and `json_bytes` unchanged from the original `supervisor.py`." | "It imports `Clock`, `Stop`, `LIMITS`, `inventory`, `json_bytes` and `_reap` unchanged from the original `supervisor.py`." |
| 5 | Same list, second item, opening | "It re-implements only `run_process`. In it, the Linux precondition … is replaced by a Darwin precondition: … If the precondition fails, it raises the same kind of `Stop`. Everything else stays as in the original:" | "It re-implements `run_process`, `group_exists` and `terminate_group`. In `run_process`, the Linux precondition … is replaced by a Darwin precondition: … If the precondition fails, it raises the same kind of `Stop`. `group_exists` and `terminate_group` handle `EPERM` as P33-AMENDMENT-001 section 3 states. Everything else stays as in the original:" (the elided parts unchanged) |
| 6 | Same nested list, "the group check after exit" | "the group check after exit" | "the group check after exit, whose tokens are unchanged and whose probe counts `EPERM` as present" |
| 7 | Same nested list, "`terminate_group`'s SIGTERM, mandatory SIGKILL and bounded reaping" | that text | "`terminate_group`'s SIGTERM, mandatory SIGKILL and bounded reaping; a send refused with `EPERM` is passed over, and the group must still become absent (`ESRCH`) within the ceiling" |
| 8 | Same list, third item | "A reviewed token-level comparison with the original `run_process` must show only that change." | "A reviewed token-level comparison of `run_process`, `group_exists` and `terminate_group` with the originals must show exactly the five change sites of P33-AMENDMENT-001 section 3.2 and nothing else." |
| 9 | CONTRACT.md section 5, table, rows `process_group_absent` and `cleanup.passed` (Darwin column) | "the same probe. Whether Darwin counts a zombie member is not established here." / "the same, with the two meanings above" | `process_group_absent`: "the same probe failed with `ESRCH`. On the observed OS build (25G83), a group of unreaped members answers `EPERM` and counts as present, so absent means that no member remains, live or unreaped. A member this process may not signal also counts as present." `cleanup.passed`: "the group became absent (`ESRCH`) within the cleanup ceiling, with the meanings of `reaped` and `process_group_absent` above" |
| 10 | CONTRACT.md section 5, "No descendant", its last paragraph's first sentence | "That property, the unchanged group check after exit, and the result labels together state the Darwin lifecycle." | "That property, the group check after exit (its tokens unchanged, its probe counting `EPERM` as present), and the result labels together state the Darwin lifecycle." |
| 11 | CONTRACT.md section 9, MC14 | case "token-level comparison with the original `run_process`"; expected "only the precondition differs" | case "token-level comparison of `run_process`, `group_exists` and `terminate_group` with the originals"; expected "exactly the five change sites of P33-AMENDMENT-001 section 3.2, four of them `EPERM` handlings, and nothing else" |
| 12 | CONTRACT.md section 9, added rows | none | MC37, MC38 and MC39 (section 4 below) |
| 13 | CONTRACT.md section 10, first list, "the contract `ontokin.current-host-readback/0.2.0`" | that item | "the contract `ontokin.current-host-readback/0.2.0`, with its design revision and its adopted amendments (from revision 4: `design_revision` 4 and `amendments` [`P33-AMENDMENT-001`])" |
| 14 | CONTRACT.md section 12, bullet "Zombies" | "whether Darwin's `killpg(pid, 0)` counts a zombie group member is not established." | "**Unreaped members:** on the observed OS build (25G83), a group of unreaped members answers `EPERM` (P33-SUPERVISOR-001). Its safety does not rely on that answer, since `EPERM` never counts as absent. The stricter meaning of `process_group_absent` relies on `ESRCH` after the last reaping. MC37 re-observes it on each qualifying host. **launchd's reaping:** orphaned descendants are reaped by launchd, observed within 1.5 to 1.8 ms. A slower reaping can only delay or fail a cleanup, never pass one." |
| 15 | CONTRACT.json `supervisor.imported`, `.reimplemented`, `.only_change`, `.guarantees.kept`, `.assertion_meanings.process_group_absent`, `.assertion_meanings["cleanup.passed"]` | the revision-3 values | the values in AMENDMENT-001.json |
| 16 | CONTRACT.json `substitutions.S4`, `controls` (MC14 replaced; MC37, MC38 and MC39 added), `p05_control_map.CH19`, `labels.carried_with`, `trust_assumptions[2]` | the revision-3 values | the values in AMENDMENT-001.json |

### 3.5 Unchanged

- every other clause, among them section 5's opening sentence: the module still supplies
  `run_process` with the original signature and receipt fields;
- MC12, MC13 and MC17, with their expected outcomes;
- the meaning of `reaped`: the direct child was reaped, and orphaned descendants go to launchd;
- `handles_closed`;
- every label other than row 13's;
- the list of claims results never support, including the absence of any enforcement against
  descendants;
- `supervisor.py` and the Linux contract.

## 4. Added controls (NOT_RUN)

These controls fall under P05's CH19, beside MC12 to MC14. An independent author freezes their
exact inputs before they run.

| ID | Route | Case | Expected outcome | Node | Other |
| --- | --- | --- | --- | ---: | ---: |
| MC37 | supervisor | Real. A group whose only member is the supervisor's own exited, unreaped direct child. | `group_exists` is true while the child is unreaped, and false after it is reaped. This is part of MI's evidence, and it is run again on each qualifying host at MH. | 0 | 1 |
| MC38 | supervisor | Real. `terminate_group` started on such a group. | It returns the original receipt `{"passed": true, "process_group_absent": true, "reaped": true, …}` within 2,000 ms. No `PermissionError` reaches the caller. | 0 | 1 |
| MC39 | supervisor | A group that keeps answering `EPERM`. Case (a) is real: section 2's cause 3, run through `run_process`. Case (b) is simulated at the `os.killpg` boundary and labelled simulated. | The original cleanup-ceiling `Stop`. The receipt holds `cleanup: {"passed": false, …}` and never `process_group_absent: true`. In (a), the control's own teardown removes the escaped descendant and its unreaped child. | 0 | 1 |

These controls tell the amended rule from the unsafe alternative that counts `EPERM` as
absent. That alternative fails MC37, while the group is unreaped, and fails MC39. The
post-test checks of every frozen supervisor control apply the amended rule: `EPERM` means
present.

## 5. Effect on meaning

- **Stricter.** On the observed OS build, absence means that no member remains, live or
  unreaped. A descendant that has exited but is not yet reaped by launchd now refuses the run at
  the group check after exit, as an unreaped member also does under the Linux contract.
- **Conservative.** The ambiguous answer, `EPERM`, counts as present, so it can only delay or
  fail a cleanup. It can never pass one.
- **Unchanged.** The lifecycle assertions keep their text. The Linux supervisor and the Linux
  contract are unchanged.

## 6. Review findings and their resolution

| Finding | Resolution |
| --- | --- |
| A-01 (mandatory) | MC37 to MC39 added (section 4). The five change sites are stated once, exactly (section 3.2), and used in rows 1, 8 and 11 and in `supervisor.only_change`. CONTRACT.json `controls` is named (row 16). |
| A-02 (mandatory) | The premise is stated exactly (section 1). Results name the design revision and the amendments (row 13; `labels.carried_with` in row 16). "every label" is removed from the unchanged list. The adoption record must state the meaning from revision 4 on (section 1). |
| A-03 | The affected clauses are named with their amended text: rows 1 to 10, 15 and 16. The stricter consequence for an unreaped descendant is stated in section 5. |
| A-04 | Cause 3 is named in section 2. That the reason does not tell the causes apart is stated in section 3.3. |
| A-05 | The stricter meaning is qualified by the observed build, and MC37 runs again on each qualifying host (rows 9 and 14). launchd's reaping is an assumption (row 14). |
| A-06 | The three logs are cited by path, SHA-256 and code, and the evidence files by SHA-256 (section 2). |
| A-07 | The adoption record lists the records that the amendment supersedes, and the follow-ups to W1's checkpoint. The rule for post-test checks is in section 4. |
