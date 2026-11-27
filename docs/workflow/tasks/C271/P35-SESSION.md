# Session checkpoint: C271-P35 gate MH, host qualification of the readback methods

Follows current main's [session template](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/docs/workflow/templates/SESSION.md).
Detailed evidence is linked, not repeated. Machine paths are left out; places beside the clone
are named relative to it. Times are UTC. This is the outcome version of the checkpoint, written at
stage S9 of the MH plan. It records stages S4 to S9. The commit C version is in this file's history
at `0eb9a551`, and the declaration version at `16d4f9f4`.

## Identity

- Checkpoint time and author identity: 2026-11-27T11:35:10Z, Director `c271-p35-e38e3aa82ade`.
- Task, session, and agent or tool identity: C271, phase C271-P35-macos-host-qualification-mh;
  the same Claude Code session (model Claude Opus 5.5) that carried out C271-P30 to P34, working
  in the C271 worktree.
- Execution mode, and the entry document or record that declared it: `local`, from current main's
  [LOCAL-START-HERE](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/LOCAL-START-HERE.md),
  read again for this phase; C271's record names local mode since R07.
- Owner direction: on 2026-11-26 the owner was asked "Should I start gate MH, the first gate that
  runs Node?" and typed "Start gate MH" in this session. MH needs no download, and none was made.
- Worktree and branch: `../OntoKin-worktrees/c271`, on `work/c271-missing-import-digest-control`.
- Current user objective and bounded milestone: gate MH of the adopted contract
  `ontokin.current-host-readback/0.2.0` ([phase declaration](../../../engineering/localized-repair-c271/macos-qualification-p35/PHASE.json),
  [MH plan](../../../engineering/localized-repair-c271/macos-qualification-p35/MH-PLAN.md),
  [outcome](../../../engineering/localized-repair-c271/macos-qualification-p35/OUTCOME.json)).
- Task, requirements, and plan paths: [task.json](task.json), [REQUIREMENTS](REQUIREMENTS.md)
  (section P35), [PLAN](PLAN.md) (section P35).

## Context loaded

- Entry file and registry revision: current main `51223c9b94a222f29d38eb6c33808f8e55e2bff9`, whose
  instruction files this branch carries since gate MB.
- Required read-set: the declaration version's list, unchanged. For S4 to S9 the Director also read
  every review, disposition and freeze it acted on, and the audit
  ([reviews](../../../engineering/localized-repair-c271/macos-qualification-p35/reviews/),
  [freezes](../../../engineering/localized-repair-c271/macos-qualification-p35/plans/),
  [audit](../../../engineering/localized-repair-c271/macos-qualification-p35/audit/AUDIT-001.md)).
- Required files missing, truncated, or inaccessible: none.
- Current/deferred product work and applicable adopted contracts: no product work. P05's
  `ontokin.current-host-readback/0.1.0` and its plans `/0.1.1` to `/0.1.5` stay adopted and
  unchanged. GOAL's ceilings of 100,000 operations and 30,000 ms are unchanged.

## Source

- Starting revision: `0eb9a5517f4e19705178a2c59b8d8d33fb87867a`, commit C.
- Dirty and untracked state: from S4 to the end of the audit the worktree was clean at C, apart from
  its ignored `.venv` (P05, Q03, the audit's own reading of the index). This commit adds only this
  phase's records. The main checkout's owner items stay untouched.
- Actual remote observation, with command and time: `git ls-remote --heads origin` at
  2026-11-27T11:35:10Z read:
  - this branch at `0eb9a551`;
  - main at `51223c9b`;
  - `work/c271-p29-trd-record` at `880933a4`, which this phase does not touch.
- Active branch/head, open PR, and scope issue: [PR274](https://github.com/Omegapy/OntoKin/pull/274)
  open and draft, head `0eb9a551`; [issue273](https://github.com/Omegapy/OntoKin/issues/273) open.

## Work

- Requirements: R01 and R02 done; R03, R04 and R05 not_done. MH is not MR (R03). Task status
  `in_progress`.
- Acceptance items of the declaration:
  - A1 to A3: met, as the commit C version records.
  - A4 met: observation plan 001, accepted by plan review 001.
  - A5 met: M0 and M1 ran once, with one Git and one Node start, and HOST review 001 accepted HOST.
  - A6 met:
    - freeze review 001 rejected operational freeze 001 with two mandatory findings, and it never
      ran;
    - freeze review 002 accepted freeze 002, and its disposition settled the remaining readings
      before S7.
  - A7 met: freeze 002's 72 commands ran once each, and every check was met. The seven methods
    passed 7 of 7.
  - A8 met: the independent audit returned `PASS_WITH_NONBLOCKING_FINDINGS`.
  - A9 met by this commit's checks.
  - A10: met once this commit is pushed and read back and the comments are posted. The closing
    record says so.
- Workers:
  - W1 carried out N34-M;
  - W2 wrote the tooling, the observation plan and both freezes;
  - seven fresh W3 agents reviewed them;
  - W4 audited.

  No worker made a Git write or edited the worktree. Every deviation is listed in the
  [outcome](../../../engineering/localized-repair-c271/macos-qualification-p35/OUTCOME.json).

## Environment

- Profile and its readiness: as MP left it, unchanged.
  - The Python installation inventory stayed `c277bdd3ac6aa731…` at Q01 and at the audit's end.
  - Every start of the framework interpreter in MH carried `-B` or ran with
    `PYTHONDONTWRITEBYTECODE=1`.
- Interpreter, operating system and architecture: CPython 3.12.13, macOS 26.6.2 (25G83), arm64;
  the boot session of 2026-11-23, unchanged from S4 to the audit.
- Node: the pinned runtime started 9 times, each through the bounded routes the freeze names:
  - M1;
  - the direct-probe runner, 3 starts and then 2;
  - the cohort, 3 starts.

  No `ldd` or `codesign` start was made.
- Available operations: Git reads, local commits, non-forced pushes; GitHub API reads and comments.
  No download.

## Verification

- Commands run for the outcome (Python always with `-B`):
  - S5's `observe`, its readback and its probe;
  - S7's 72 frozen commands, through the bound wrapper in the shell tool's background mode, each
    with its frozen bound timer ([launch lines](../../../engineering/localized-repair-c271/macos-qualification-p35/director/s7/LAUNCH-LINES.json));
  - the independent audit's recomputation;
  - for this commit, the workflow check, the documentation verifier, a scoped whitespace check and
    a privacy search of every committed file
    ([check record](../../../engineering/localized-repair-c271/macos-qualification-p35/checks/s9/CHECKS.json)).
- Not run in this phase: `ldd`, `codesign`, the routine driver, the complete default routine (MR),
  and the visual-verification profile.

## Recovery

- Unpublished commits: none after the push of this commit, which the closing record observes.
- Outstanding operations and owned processes: none. Every MH process is absent, and no capture
  record exists.
- Current blockers with concrete evidence: none. P30-EXECUTOR-001 still blocks the Linux
  contract's H0 and H1 in local mode.

## Coordination

- Integration owner and lease status: none; main's lease is released and is not used.
- Ownership: owner `c271-p35-e38e3aa82ade` holds this branch for the phase and releases it with the
  closing record.

## Continuation

- One exact next action: MR (R03), the complete routine of gate R on this executor, a separate phase
  that needs the owner's selection. Then R04 and R05.
- Retained beside the clone, unchanged:
  - the exact records under `../OntoKin-local/c271-p35/`, with the digests of
    [EXACT-RECORDS.json](../../../engineering/localized-repair-c271/macos-qualification-p35/EXACT-RECORDS.json);
  - MP's prepared inputs.

  HOST stays valid only while the Python inventory and the language and region settings stay as
  observed.
- Stopping condition: met. The audited cohort and its records are pushed and read back.

No receipt of the receipt: Git reveals the commit that carries this record.
