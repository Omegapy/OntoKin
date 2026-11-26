# Amendment 001 to `ontokin.current-host-readback/0.2.0`: Darwin's group probe

**Identifier:** P33-AMENDMENT-001. It amends the adopted contract
`ontokin.current-host-readback/0.2.0`, profile `darwin-arm64-v1`
([CONTRACT](../macos-contract-design-p31/CONTRACT.md),
[CONTRACT.json](../macos-contract-design-p31/CONTRACT.json),
[adoption](../macos-contract-design-p31/ADOPTION.json)), as design revision 4. Machine-readable
form: [AMENDMENT-001.json](AMENDMENT-001.json). Both forms are generated from one source, so their
quoted texts agree.

**Decision state:** proposed by C271-P33's Director. Only a separate adoption record can adopt
it, after an independent review. Like the contract, it is design only.

**Revision history:**
- **Revision 1,** commit `5dc76ccf1a763a3454e34f97db842a2192d3129e`, was rejected by
  [AMENDMENT-001-REVIEW-001](AMENDMENT-001-REVIEW-001.md) on two mandatory findings:
  - A-01: no control told the amended rule from an unsafe one, and MC14 was inexact.
  - A-02: the version premise was inexact, and no label carried the design revision.
- **Revision 2,** commit `86a0e750ae48039798234585b8913f0ae9be7210`, was accepted with
  nonmandatory findings A-08 to A-12 by [AMENDMENT-001-REVIEW-002](AMENDMENT-001-REVIEW-002.md).
- **This final version** resolves A-08 to A-12 after that review, without a further review.
  [AMENDMENT-001-REVIEW-DISPOSITION](AMENDMENT-001-REVIEW-DISPOSITION.json) maps every finding to
  its change.

## 1. Version and premise

- **Identifiers:** the contract identifier and every schema identifier stay `0.2.0`.
- **Premise, as of the adoption:** no reviewed or accepted implementation exists under 0.2.0. No
  preparation exists, and no contract result or refusal document. The only implementations are
  MI's unreviewed working checkpoints on this branch:
  - W1, Darwin supervisor: `a23761919e92c41489f26a57d02fa1d5dc9d8e19`, revision 3's S4; superseded by this amendment and kept as failed evidence.
  - W2, preparer route: `939942e31b9bbfa8768269ff6274a66c183d2202`, revision 3's S6, unchanged by this amendment.
  - W4, driver: `b377ab969af5adc53d247bb714cc9fbfa89b938c`, S8, S9 and the Git binding, unchanged by this amendment.
  - W3, M0 and M1 observer: `579184134ab8dd2fcce0500672c0ded2c0e98471`, S3, S7 and S10, unchanged by this amendment.

  Worker W5's provider and probe are in progress and uncommitted.
- **Meaning from revision 4 on:** `ontokin.current-host-readback/0.2.0` means CONTRACT.md and
  CONTRACT.json as amended by P33-AMENDMENT-001. The adoption record states this.
- **Results:** every result names its design revision and adopted amendments. This is the row of
  section 3.4 for section 10.
- **Adopted files:** the adopted contract files stay byte-identical.

## 2. Finding P33-SUPERVISOR-001

The finding was observed on 2026-11-26 on macOS 26.6.2, build 25G83 (Darwin 25.6.0, arm64), with
CPython 3.12.13:

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
  `../OntoKin-local/c271-p33/workers/W1/`. They corroborate the module by traceback line
  numbers, not by bytes. [AMENDMENT-001-REVIEW-001](AMENDMENT-001-REVIEW-001.md) (R2, R3)
  reproduced the finding at the checkpoint's exact bytes.

  | Log | SHA-256 | Runs | Code |
  | --- | --- | --- | --- |
  | `01-test-run-draft.txt` | `fcacda9a15cba087165d34f12017545f40e27b1895fcace9b280e4387ecad652` | 1 | an earlier draft of the test file; the module's traceback lines match the checkpoint's |
  | `02-repeat-real-child-runs.txt` | `fcd1bbf192bf8798d4ce8392386b7d5f9fb3a51e01ce27c2da9eaf51ea49d67a` | 10 | an intermediate test file (its MC12 and MC13 calls at lines 393, 417 and 437, where the checkpoint has 395, 419 and 439); the module's traceback lines match the checkpoint's |
  | `03-test-run-final.txt` | `68b5f1a44d7de88ba0cfd7a3ceb71f2f1a36cf6ec3d05f5471f285d04f279e76` | 1 | the checkpoint's test file by its line numbers (line 419); the module's traceback lines match the checkpoint's |

  - **Failures across the 12 runs, each a `PermissionError`:**
    - MC12: 10 runs;
    - the MC13 timeout case: 3 runs;
    - the MC13 cancellation case: 1 run;
    - the positive case: none.
  - **Observation test:** the checkpoint's observation test records 0, then `EPERM`, then
    `ESRCH`.

**Where revision 3's S4 breaks.** The imported `group_exists` treats only `ESRCH` as an answer.
`EPERM` therefore escapes as `PermissionError` in three places:
- `terminate_group`'s polling;
- its three `killpg` signal sends, which catch only `ProcessLookupError`;
- `run_process`'s group check after exit.

The caller then receives `PermissionError` instead of the original `Stop`. No cleanup receipt is
recorded. After a timeout or a cancellation, the direct child can stay unreaped.

**What answers `EPERM`.** A group of unreaped members answers `EPERM` while it stays unreaped.
Three causes are known:
1. **The direct child** has exited, and the supervisor has not polled it yet. Brief.
2. **An orphaned descendant** has exited, and launchd has not reaped it yet. Brief: 1.5 to 1.8 ms
   observed.
3. **A member whose parent never reaps it.** A descendant moves itself into its own process
   group and never reaps its exited child, which stays in the owned group. The group then
   answers `EPERM` for as long as that parent lives, with no privilege needed. The review
   reproduced it (D4).

A genuine permission refusal answers `EPERM` too, for example a member that this process may not
signal.

This answers contract section 12's open question, "whether Darwin's `killpg(pid, 0)` counts a
zombie group member". On this host and build, the probe neither returns nor reports `ESRCH`: it
fails with `EPERM`.

## 3. Decision and replaced clauses

### 3.1 The rule

The Darwin variant re-implements `run_process`, `group_exists` and `terminate_group`.
- **Imports:** `Clock`, `Stop`, `LIMITS`, `inventory`, `json_bytes` and `_reap` come unchanged
  from `supervisor.py`. `supervisor.py` stays byte-identical, and it remains the Linux contract's
  supervisor.
- **The probe:** the group counts as absent only when the probe reports `ESRCH`. An `EPERM`
  answer counts as present.
- **The sends:** a send refused with `EPERM` is passed over and never taken as proof of absence.

### 3.2 Allowed differences

A token-level comparison of the three functions with the originals shows exactly five change
sites. Four of them handle `EPERM`. Nothing else differs, docstrings and comments included.

1. **`run_process`:** the precondition block. The original's three statements are replaced by
   statements that evaluate the Darwin precondition of contract section 5. They raise
   `Stop("OTRAY-E-BACKEND", …)` when it is unmet. The original statements are:
   - `libc = ctypes.CDLL(None, use_errno=True)`;
   - `if libc.prctl(36, 1, 0, 0, 0) != 0:`;
   - `raise Stop("OTRAY-E-BACKEND", "Cannot establish Linux descendant reaping")`.

   The body's names `group_exists` and `terminate_group` resolve to the re-implementations.
2. **`group_exists`:** the clause `except PermissionError:` / `return True` is inserted
   immediately before `except ProcessLookupError:`.
3. **`terminate_group`, the SIGTERM send:** `except ProcessLookupError:` becomes
   `except (ProcessLookupError, PermissionError):`.
4. **`terminate_group`, the SIGKILL send after the grace period:** the same change.
5. **`terminate_group`, the final SIGKILL send before the ceiling `Stop`:** the same change.

### 3.3 Fail-closed consequence

A group that keeps answering `EPERM` fails at the cleanup ceiling, with the original
`Stop("OTRAY-E-BACKEND", "Owned process group cleanup exceeded stage or transaction ceiling")`.
The receipt holds `cleanup: {"passed": false, "reason": …}` and an `error` equal to that `Stop`.
- That `Stop` replaces an earlier message of the same run, such as "Child exited while an owned
  descendant remained".
- The recorded reason does not tell apart the causes of a lasting `EPERM`: cause 3 of section 2,
  a permission refusal, or a slow reaping.
- A descendant that moved itself out of the group survives. This stays within "no enforcement
  against descendants".

### 3.4 Replaced clauses of CONTRACT.md

Each row quotes the adopted text and its replacement exactly. The same texts appear in
[AMENDMENT-001.json](AMENDMENT-001.json) under `replaces_contract_md`. CONTRACT.json's places are
there under `replaces_contract_json`:
- `supervisor.imported`, `.reimplemented`, `.only_change`, `.guarantees.kept`,
  `.assertion_meanings.process_group_absent` and `.assertion_meanings["cleanup.passed"]`;
- `substitutions.S4` and `executor_requirements.E13`;
- `controls[id=MC14]` and the appended controls MC37, MC38 and MC39;
- `p05_control_map.CH19`, `labels.carried_with` and `trust_assumptions[2]`.

| # | Place in CONTRACT.md | Adopted text | Amended text |
| --- | --- | --- | --- |
| 1 | section 1, row S4, macOS arm64 term | a Darwin variant with the same logic except that precondition (section 5) | a Darwin variant whose only changes are the precondition and the four `EPERM` handlings of P33-AMENDMENT-001 (section 5 as amended) |
| 2 | section 1, row S4, Reason | Darwin has no child-subreaper | Darwin has no child-subreaper, and its group probe answers `EPERM` for a group of unreaped members (P33-SUPERVISOR-001) |
| 3 | section 1, row S4, Effect on meaning | the lifecycle assertions keep their text with a narrowed meaning (section 5) | the lifecycle assertions keep their text with the meanings of section 5 as amended: narrower where descendants are re-parented to launchd, stricter where an unreaped or unsignalable member remains |
| 4 | section 2, row E13, Under 0.2.0 | substituted (S4) | substituted (S4, as amended by P33-AMENDMENT-001) |
| 5 | section 2, row E13, Reason and effect on meaning | narrowed meaning of the lifecycle assertions (section 5) | the meanings of the lifecycle assertions in section 5 as amended |
| 6 | section 5, first list, first item | It imports `Clock`, `Stop`, `LIMITS`, `inventory`, `group_exists`, `terminate_group` and `json_bytes` unchanged from the original `supervisor.py`. | It imports `Clock`, `Stop`, `LIMITS`, `inventory`, `json_bytes` and `_reap` unchanged from the original `supervisor.py`. |
| 7 | section 5, first list, second item, opening | It re-implements only `run_process`. In it, the Linux precondition `prctl(PR_SET_CHILD_SUBREAPER)` is replaced by a Darwin precondition: `sys.platform == "darwin"`, machine `arm64`, and `sysctl.proc_translated` equal to 0, read through `sysctlbyname`. If the precondition fails, it raises the same kind of `Stop`. Everything else stays as in the original: | It re-implements `run_process`, `group_exists` and `terminate_group`. In `run_process`, the Linux precondition `prctl(PR_SET_CHILD_SUBREAPER)` is replaced by a Darwin precondition: `sys.platform == "darwin"`, machine `arm64`, and `sysctl.proc_translated` equal to 0, read through `sysctlbyname`. If the precondition fails, it raises the same kind of `Stop`. `group_exists` and `terminate_group` handle `EPERM` as P33-AMENDMENT-001 section 3 states. Everything else stays as in the original: |
| 8 | section 5, nested list, group check item | the group check after exit | the group check after exit, whose tokens are unchanged and whose probe counts `EPERM` as present |
| 9 | section 5, nested list, terminate_group item | `terminate_group`'s SIGTERM, mandatory SIGKILL and bounded reaping | `terminate_group`'s SIGTERM, mandatory SIGKILL and bounded reaping; a send refused with `EPERM` is passed over, and the group must still become absent (`ESRCH`) within the ceiling |
| 10 | section 5, first list, third item | A reviewed token-level comparison with the original `run_process` must show only that change. | A reviewed token-level comparison of `run_process`, `group_exists` and `terminate_group` with the originals must show exactly the five change sites of P33-AMENDMENT-001 section 3.2 and nothing else. |
| 11 | section 5, table, row process_group_absent, 0.2.0 on Darwin | the same probe. Whether Darwin counts a zombie member is not established here. | the same probe failed with `ESRCH`. On the observed OS build (25G83), a group of unreaped members answers `EPERM` and counts as present, so absent means that no member remains, live or unreaped. A member this process may not signal also counts as present. |
| 12 | section 5, table, row cleanup.passed, 0.2.0 on Darwin | the same, with the two meanings above | the group became absent (`ESRCH`) within the cleanup ceiling, with the meanings of `reaped` and `process_group_absent` above |
| 13 | section 5, No descendant, last paragraph, first sentence | That property, the unchanged group check after exit, and the result labels together state the Darwin lifecycle. | That property, the group check after exit (its tokens unchanged, its probe counting `EPERM` as present), and the result labels together state the Darwin lifecycle. |
| 14 | section 9, row MC14, Case | token-level comparison with the original `run_process` | token-level comparison of `run_process`, `group_exists` and `terminate_group` with the originals |
| 15 | section 9, row MC14, Expected outcome | only the precondition differs | exactly the five change sites of P33-AMENDMENT-001 section 3.2, four of them `EPERM` handlings, and nothing else |
| 16 | section 10, first list, contract item | the contract `ontokin.current-host-readback/0.2.0`; | the contract `ontokin.current-host-readback/0.2.0`, with its design revision and its adopted amendments (from revision 4: `design_revision` 4 and `amendments` [`P33-AMENDMENT-001`]); |
| 17 | section 12, bullet Zombies | **Zombies:** whether Darwin's `killpg(pid, 0)` counts a zombie group member is not established. | **Unreaped members:** on the observed OS build (25G83), a group of unreaped members answers `EPERM` (P33-SUPERVISOR-001). Its safety does not rely on that answer, since `EPERM` never counts as absent. The stricter meaning of `process_group_absent` relies on `ESRCH` after the last reaping, and MC37 re-observes it on each qualifying host. **launchd's reaping:** orphaned descendants are reaped by launchd, observed within 1.5 to 1.8 ms; a slower reaping can only delay or fail a cleanup, never pass one. |

**Section 9, added rows,** exactly as they join the table after MC36:

| ID | Route | Case | Expected outcome | Node | Other |
| --- | --- | --- | --- | ---: | ---: |
| MC37 | supervisor | real: a group whose only member is the supervisor's own direct child, exited and not reaped; the exit is established before the probe, without reaping and independently of the code under test, through kqueue `EVFILT_PROC` with `NOTE_EXIT` | `group_exists` is true while the child is unreaped and false after it is reaped; part of MI's evidence, and run again on each qualifying host at MH | 0 | 1 |
| MC38 | supervisor | real: `terminate_group` started on such a group, with the exit established in the same way | the original receipt `{"passed": true, "process_group_absent": true, "reaped": true, "elapsed_ms": …}` within 2,000 ms; no `PermissionError` reaches the caller; this also covers the handling of a send refused with `EPERM` | 0 | 1 |
| MC39 | supervisor | a group that keeps answering `EPERM`, through `run_process`, with one start per case: (a) real, a descendant that moves itself into its own process group and never reaps its exited child, which stays in the owned group; (b) one real child, with the probe `os.killpg(pid, 0)` made to fail with `PermissionError` at the `os.killpg` boundary while real signals pass through, labelled simulated | the original cleanup-ceiling `Stop`; the receipt holds `cleanup: {"passed": false, "reason": …}` and an `error` equal to that `Stop`, and never `process_group_absent: true`; in (a) the control's own teardown removes the escaped descendant and its unreaped child | 0 | 2 |

### 3.5 Unchanged

- every other clause, including section 5's opening sentence: the module still supplies
  `run_process` with the original signature and receipt fields;
- MC12, MC13 and MC17, with their expected outcomes;
- the meanings of `reaped` and `handles_closed`;
- every label other than the contract item of section 10;
- the claims that results never support, including the absence of any enforcement against
  descendants;
- `supervisor.py` and the Linux contract.

## 4. The added controls

- **Subject:** MC37, MC38 and MC39, above, come under P05's CH19, beside MC12 to MC14.
- **Freezing:** an independent author freezes their exact inputs before they run.
- **What they tell apart:** they distinguish the amended rule from two unsafe alternatives.
  - Counting `EPERM` as absent fails MC37 and MC39.
  - Keeping the original sends fails MC38 and MC39.
- **Post-test checks:** the checks after every frozen supervisor control apply the amended rule:
  `EPERM` means present.
- **Gates:** MI executes all three controls. MC37 runs again on each qualifying host at MH.

## 5. Effect on meaning

- **Stricter:** on the observed OS build, absence means that no member remains, live or unreaped.
  A descendant that has exited but is not yet reaped by launchd now refuses the run at the group
  check after exit.
- **Conservative:** the ambiguous answer, `EPERM`, counts as present. It can only delay or fail a
  cleanup, never pass one.
- **Unchanged:** the lifecycle assertions keep their text. The Linux supervisor and the Linux
  contract are unchanged.
