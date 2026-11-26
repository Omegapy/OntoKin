# Amendment 001 to `ontokin.current-host-readback/0.2.0`: Darwin's group probe

**Identifier:** P33-AMENDMENT-001. It amends the adopted contract
`ontokin.current-host-readback/0.2.0`, profile `darwin-arm64-v1`
([CONTRACT](../macos-contract-design-p31/CONTRACT.md),
[CONTRACT.json](../macos-contract-design-p31/CONTRACT.json),
[adoption](../macos-contract-design-p31/ADOPTION.json)), as design revision 4. Machine-readable
form: [AMENDMENT-001.json](AMENDMENT-001.json).

**Decision state:** proposed by C271-P33's Director. Only a separate adoption record can adopt
it, after an independent review. Like the contract, it is design only.

**Contract files:** the adopted contract files stay byte-identical. This amendment replaces only
the clauses named in section 3, and everything else in the contract stands.

**Contract version:** the version and every schema identifier stay `0.2.0`. Nothing has been
implemented, prepared or executed under 0.2.0, so no result or document exists that could be
confused with an amended one. Every 0.2.0 result names the design revision it follows.

## 1. Finding P33-SUPERVISOR-001

Gate MI's first implementation of the Darwin supervisor followed S4 exactly: `run_process`
re-implemented with the Darwin precondition, and `group_exists` and `terminate_group`
imported unchanged (checkpoint `a23761919e92c41489f26a57d02fa1d5dc9d8e19`). Its development
tests showed that S4's premise does not hold on Darwin.

The host was macOS 26.6.2, build 25G83, with Darwin 25.6.0 on arm64 and CPython 3.12.13. On
2026-11-26 it gave:

| Group state | `os.killpg(pgid, 0)` |
| --- | --- |
| a member is alive | returns |
| every remaining member has exited, none is reaped yet | fails with `EPERM` (`PermissionError`) |
| after reaping | fails with `ESRCH` (`ProcessLookupError`) |

The evidence comes from two independent sources:

- **The Director's probe:** [zombie_group_probe.py](evidence/zombie_group_probe.py), output
  [zombie_group_probe.out.json](evidence/zombie_group_probe.out.json).
  - A direct child in its own group, exited but not reaped, answered `EPERM`. After
    `waitpid` it answered `ESRCH`.
  - An orphaned grandchild, once killed, answered `EPERM` for one 1 ms poll, then `ESRCH`.
    launchd had reaped it within 1.8 ms.
- **Worker W1's development tests,** at the checkpoint above:
  - an observation test records the sequence 0, then `EPERM`, then `ESRCH`;
  - across 12 runs, the MC12 case failed 10 times, the MC13 timeout case 3 times and the MC13
    cancellation case once, each time with `PermissionError`;
  - the positive case never failed.

Where it breaks, by the code of `supervisor.py`:

1. **The group check.** `group_exists` treats only `ESRCH` as an answer, so `EPERM` escapes as
   `PermissionError`. `terminate_group` polls `group_exists` after each `process.poll()`.
   Between the last member's exit and its reaping, the probe answers `EPERM`. That last member
   is either the direct child before the next poll, or a descendant before launchd reaps it.
2. **The signal sends.** `terminate_group` sends `killpg(…, SIGTERM)` and `killpg(…, SIGKILL)`
   three times. Each send catches only `ProcessLookupError`.
3. **The caller.** The caller receives `PermissionError` instead of the original `Stop`. The
   cleanup receipt stays empty, and after a timeout or a cancellation the direct child can
   stay unreaped.

This also answers the open question of contract section 12, "whether Darwin's
`killpg(pid, 0)` counts a zombie group member". On this host the probe neither succeeds nor
reports `ESRCH` for such a member: it fails with `EPERM`.

## 2. Decision

The Darwin variant re-implements `group_exists` and `terminate_group` as well as `run_process`.
Every other name it uses stays imported unchanged from `supervisor.py`: `Clock`, `Stop`,
`LIMITS`, `inventory`, `json_bytes` and `_reap`. `supervisor.py` stays byte-identical, and it
remains the Linux contract's supervisor.

- **`group_exists(pid)`**
  - It uses the same probe, `os.killpg(pid, 0)`.
  - It returns `True` when the probe returns, or when it fails with `PermissionError` (`EPERM`).
  - It returns `False` only on `ProcessLookupError` (`ESRCH`).
  - Any other error propagates unchanged.
- **`terminate_group(process, clock)`**
  - It keeps the original logic, limits, order and receipt.
  - In each of its three `os.killpg(…, SIGTERM|SIGKILL)` sends, a `PermissionError` is treated
    like `ProcessLookupError`: the send is passed over and the procedure continues.
  - Its polling uses the Darwin `group_exists`.
- **`run_process`**
  - It is as adopted: only the precondition differs.
  - Its body's names `group_exists` and `terminate_group` resolve to the Darwin
    re-implementations, so its tokens stay identical apart from the precondition.

**Rule kept.** The group counts as absent only when the probe reports `ESRCH`. That rule holds
whichever of the three answers a group of unreaped members gives, so the decision does not rely
on the observation, which only explains the defect.

**Fail-closed case.** A genuine permission refusal answers `EPERM` too: for example, a member
that this process may not signal. This probe cannot tell it from an unreaped group. It counts
as present, so a group that never empties fails at the cleanup ceiling with the original
`Stop("OTRAY-E-BACKEND", "Owned process group cleanup exceeded stage or transaction ceiling")`.
A send that fails with `EPERM` is never taken as proof of absence.

## 3. Replaced clauses

| Contract place | Adopted text, in short | Amended text |
| --- | --- | --- |
| Section 1, row S4 | "a Darwin variant with the same logic except that precondition" | a Darwin variant whose only changes are the precondition and the counting of an `EPERM` group answer as a present group (section 2 of this amendment) |
| Section 5, first list | imports `group_exists` and `terminate_group` unchanged; re-implements only `run_process` | imports `Clock`, `Stop`, `LIMITS`, `inventory`, `json_bytes` and `_reap` unchanged, and re-implements `run_process`, `group_exists` and `terminate_group` as section 2 of this amendment states |
| Section 5, "A reviewed token-level comparison with the original `run_process` must show only that change" | one function, one change | a reviewed token-level comparison of the three re-implemented functions with the originals shows only three changes: the precondition block of `run_process`, the `PermissionError` clause of `group_exists`, and the `PermissionError` additions to the three `except` clauses of `terminate_group` |
| Section 5, table row `process_group_absent` | "the same probe. Whether Darwin counts a zombie member is not established here." | the same probe failed with `ESRCH`. A group whose remaining members are all unreaped answers `EPERM` on this host and counts as present. Absent means that no member, live or unreaped, remains. A genuine permission refusal also counts as present and fails closed at the cleanup ceiling. |
| Section 5, table row `cleanup.passed` | "the same, with the two meanings above" | the group became absent (`ESRCH`) within the cleanup ceiling, with the meanings of `reaped` and `process_group_absent` above |
| Section 9, MC14 | "token-level comparison with the original `run_process`" → "only the precondition differs" | "token-level comparison of `run_process`, `group_exists` and `terminate_group` with the originals" → "only the precondition and the three `EPERM` handlings of this amendment differ" |
| Section 12, bullet "Zombies" | "whether Darwin's `killpg(pid, 0)` counts a zombie group member is not established" | on this host and OS build, a group of unreaped members answers `EPERM` (finding P33-SUPERVISOR-001). The amended rule does not rely on it. Other OS builds are not observed. |
| CONTRACT.json `supervisor` | `imported`, `reimplemented`, `only_change`, `assertion_meanings.process_group_absent` | replaced as [AMENDMENT-001.json](AMENDMENT-001.json) states |
| CONTRACT.json `trust_assumptions`, third entry | the zombie assumption | replaced by the finding, as above |

**Unchanged:**
- every other clause, among them MC12, MC13 and MC17, with their expected outcomes;
- the meaning of `reaped`: the direct child was reaped, and orphaned descendants go to launchd;
- `handles_closed`;
- every label, and the list of claims that results never support, including the absence of
  any enforcement against descendants.

## 4. Effect on meaning

- **Stricter:** absence now means that no member is alive or unreaped.
- **Conservative:** the one ambiguous answer, `EPERM`, now counts as present, so it can only
  delay or fail a cleanup. It can never pass one.
- **Unchanged:** the lifecycle assertions keep their text. The Linux supervisor and the Linux
  contract are unchanged.
- **Controls:** no control's expected outcome changes, except MC14's statement of which tokens
  may differ.
