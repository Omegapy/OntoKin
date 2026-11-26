# Session checkpoint: C271-P35 gate MH, host qualification of the readback methods

Follows current main's [session template](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/docs/workflow/templates/SESSION.md).
Detailed evidence is linked, not repeated. Machine paths are left out; places beside the clone
are named relative to it. Times are UTC. This is the declaration version of the checkpoint.

## Identity

- Checkpoint time and author identity: 2026-11-26T23:08:24Z, Director `c271-p35-e38e3aa82ade`.
- Task, session, and agent or tool identity: C271, phase C271-P35-macos-host-qualification-mh;
  the same Claude Code session (model Claude Opus 5.5) that carried out C271-P30 to P34, working
  in the C271 worktree.
- Execution mode, and the entry document or record that declared it: `local`, from current main's
  [LOCAL-START-HERE](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/LOCAL-START-HERE.md),
  read again for this phase; C271's record names local mode since R07.
- Owner direction: on 2026-11-26 the owner was asked "Should I start gate MH, the first gate that
  runs Node?" and typed "Start gate MH" in this session. MH needs no download, and none is
  approved.
- Worktree and branch: `../OntoKin-worktrees/c271`, on `work/c271-missing-import-digest-control`.
- Current user objective and bounded milestone: gate MH of the adopted contract
  `ontokin.current-host-readback/0.2.0` ([phase declaration](../../../engineering/localized-repair-c271/macos-qualification-p35/PHASE.json),
  [MH plan](../../../engineering/localized-repair-c271/macos-qualification-p35/MH-PLAN.md)).
- Task, requirements, and plan paths: [task.json](task.json), [REQUIREMENTS](REQUIREMENTS.md)
  (section P35), [PLAN](PLAN.md) (section P35).

## Context loaded

- Entry file and registry revision: current main `51223c9b94a222f29d38eb6c33808f8e55e2bff9`, whose
  instruction files this branch carries since gate MB; LOCAL-START-HERE was opened again for this
  phase.
- Required read-set actually opened, with revision or hash:
  - the adopted [CONTRACT](../../../engineering/localized-repair-c271/macos-contract-design-p31/CONTRACT.md),
    sections 7, 9, 10, 11 and 12;
  - MI's [outcome](../../../engineering/localized-repair-c271/macos-implementation-p33/OUTCOME.json),
    with its obligations for MH, the findings F-01 to F-10 of its frozen controls, and its
    inventory additions;
  - the observer's and the provider's interface notes:
    [W3-OBSERVER](../../../engineering/localized-repair-c271/macos-implementation-p33/interfaces/W3-OBSERVER.md)
    sections 1, 2 and 7, and
    [W5-PROVIDER](../../../engineering/localized-repair-c271/macos-implementation-p33/interfaces/W5-PROVIDER.md)
    sections 3 and 12;
  - P07's [qualification plan](../../../engineering/localized-repair-c271/host-inspection-p07/QUALIFICATION-PLAN.md),
    sections 3 to 6;
  - MP's outcome and closing record.
- Required files missing, truncated, or inaccessible: none.
- Current/deferred product work and applicable adopted contracts: no product work. P05's
  `ontokin.current-host-readback/0.1.0` and its plans `/0.1.1` to `/0.1.5` stay adopted and
  unchanged. GOAL's ceilings of 100,000 operations and 30,000 ms are unchanged.

## Source

- Starting revision: `30e00d83df8bd87216b15ec1e4a4f0ca349fc78d`, which is P34's closing record.
- Dirty and untracked state: the worktree was clean, apart from its ignored `.venv`. The main
  checkout's owner items stay untouched.
- Actual remote observation, with command and time: `git ls-remote --heads origin` at
  2026-11-26T23:06:49Z read:
  - this branch at `30e00d83`;
  - main at `51223c9b`;
  - `work/c271-p29-trd-record` at `880933a4`, which this phase does not touch.
- Repository, actual main SHA, and observation time: `Omegapy/OntoKin`, main
  `51223c9b94a222f29d38eb6c33808f8e55e2bff9` at 23:06:49Z.
- Active branch/head, open PR, and scope issue: [PR274](https://github.com/Omegapy/OntoKin/pull/274)
  open and draft, head `30e00d83`; [issue273](https://github.com/Omegapy/OntoKin/issues/273) open.

## Work

- Requirements: R01 and R02 done; R03, R04 and R05 not_done. P01 done, P02 in_progress. Task
  status `in_progress`.
- Acceptance items: A1 to A10 of the declaration. None is complete at this checkpoint.
- Workers: W1 to W4 of the MH plan, section 3. None is launched at this checkpoint.

## Environment

- Profile and its readiness: as MP left it. The doctor reports `core` ready, and
  `python-verification` as `not_checked`, because pip is absent by design (D-21). The framework
  and the `.venv` are byte-identical to MP's after-snapshot (inventory digest
  `c277bdd3ac6aa731…`), and the `.venv` holds no bytecode.
- Interpreter, operating system and architecture: CPython 3.12.13, macOS 26.6.2 (25G83), arm64;
  the boot session of 2026-11-23.
- Node: the pinned runtime beside the clone has never run. A Node.js installation of other
  software is on `PATH`; no MH step starts it.
- Available operations: Git reads, local commits, non-forced pushes; GitHub API reads and comments.
  No download.

## Verification

- Commands planned: stages S2 to S8 of the MH plan.
- Not run in this phase at this checkpoint: N34-M, M0, M1, the cohort, any Node, `ldd` or
  `codesign` start, the routine driver, and the visual-verification profile.

## Recovery

- Unpublished commits: none after the push of this declaration, which the next checkpoint observes.
- Outstanding operations and owned processes: none.
- Current blockers with concrete evidence: none. P30-EXECUTOR-001 still blocks the Linux
  contract's H0 and H1 in local mode.

## Coordination

- Integration owner and lease status: none; main's lease is released and is not used.
- Ownership: owner `c271-p35-e38e3aa82ade` holds this branch for the phase.

## Continuation

- One exact next action: stages S2 and S3 of the MH plan, N34-M and the tooling, at the same time.
- Stopping condition: the audited cohort pushed and read back with its records, or a concrete
  blocker.

No receipt of the receipt: Git reveals the commit that carries this record.
