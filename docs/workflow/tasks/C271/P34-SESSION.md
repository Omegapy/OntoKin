# Session checkpoint: C271-P34 gate MP, preparation of the runtime, reader tree and .venv

Follows current main's [session template](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/docs/workflow/templates/SESSION.md).
Detailed evidence is linked, not repeated. Machine paths are left out; places beside the clone
are named relative to it. Times are UTC. This is the declaration version of the checkpoint.

## Identity

- Checkpoint time and author identity: 2026-11-26T21:01:00Z, Director `c271-p34-ec1a7de2360d`.
- Task, session, and agent or tool identity: C271, phase C271-P34-macos-preparation-mp; the same
  Claude Code session (model Claude Opus 5.5) that carried out C271-P30 to P33, working in the
  C271 worktree.
- Execution mode, and the entry document or record that declared it: `local`, from current main's
  [LOCAL-START-HERE](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/LOCAL-START-HERE.md),
  read again for this phase; C271's record names local mode since R07.
- Owner direction:
  - **Phase selection:** on 2026-11-26 the owner was asked "Should I start gate MP, the
    preparation phase?" and typed "Start gate MP" in this session.
  - **Downloads:** asked to approve two downloads, each named with its source and size, the owner
    selected both in this session's question dialog. They are the Node archive (53,062,778 bytes)
    and the seven wheels (5,447,056 bytes). The exact question and answer are in the
    [declaration](../../../engineering/localized-repair-c271/macos-preparation-p34/PHASE.json).
- Worktree and branch: `../OntoKin-worktrees/c271`, on `work/c271-missing-import-digest-control`.
- Current user objective and bounded milestone: gate MP of the adopted contract
  `ontokin.current-host-readback/0.2.0` ([phase declaration](../../../engineering/localized-repair-c271/macos-preparation-p34/PHASE.json),
  [preparation plan](../../../engineering/localized-repair-c271/macos-preparation-p34/PREPARATION-PLAN.md)).
- Task, requirements, and plan paths: [task.json](task.json), [REQUIREMENTS](REQUIREMENTS.md)
  (section P34), [PLAN](PLAN.md) (section P34).

## Context loaded

- Entry file and registry revision: current main `51223c9b94a222f29d38eb6c33808f8e55e2bff9`, whose
  instruction files this branch carries since gate MB; LOCAL-START-HERE was opened again for this
  phase.
- Required read-set actually opened, with revision or hash:
  - the adopted [CONTRACT](../../../engineering/localized-repair-c271/macos-contract-design-p31/CONTRACT.md),
    sections 3, 4, 6, 11 and 12;
  - MI's [outcome](../../../engineering/localized-repair-c271/macos-implementation-p33/OUTCOME.json),
    with its obligations for MP;
  - the preparer's [interface note](../../../engineering/localized-repair-c271/macos-implementation-p33/interfaces/W2-PREPARER.md);
  - the [setup guide](../../../development/LOCAL-SETUP.md) and OK-ENG-006 section 3;
  - the macOS lock and its provenance record.
- Required files missing, truncated, or inaccessible: none.
- Current/deferred product work and applicable adopted contracts: no product work. P05's
  `ontokin.current-host-readback/0.1.0` and its plans `/0.1.1` to `/0.1.5` stay adopted and
  unchanged. GOAL's ceilings of 100,000 operations and 30,000 ms are unchanged.

## Source

- Starting revision: `180075b7952fb4df50ec35eb64106410bfa1d8f9`, which is P33's closing record.
- Dirty and untracked state: the worktree was clean, apart from its ignored `.venv`. The main
  checkout's owner items stay untouched.
- Actual remote observation, with command and time: `git ls-remote --heads origin` at
  2026-11-26T20:42:12Z read:
  - this branch at `180075b7`;
  - main at `51223c9b`;
  - `work/c271-p29-trd-record` at `880933a4`, which this phase does not touch.
- Repository, actual main SHA, and observation time: `Omegapy/OntoKin`, main
  `51223c9b94a222f29d38eb6c33808f8e55e2bff9` at 20:42:12Z.
- Active branch/head, open PR, and scope issue: [PR274](https://github.com/Omegapy/OntoKin/pull/274)
  open and draft; [issue273](https://github.com/Omegapy/OntoKin/issues/273) open.

## Work

- Requirements: R01 and R02 done; R03, R04 and R05 not_done. P01 done, P02 in_progress. Task
  status `in_progress`.
- Acceptance items: A1 to A9 of the declaration. None is complete at this checkpoint.
- Workers: W1 and W2 of the preparation plan, section 4. Neither is launched at this checkpoint.

## Environment

- Profile and its readiness: the doctor reports `core` ready and `python-verification` missing
  (the seven packages). It ran with a non-existent Node, so it started none. The worktree's `.venv`
  was created without pip, and its `site-packages` is empty.
- Interpreter, operating system and architecture: CPython 3.12.13 (Homebrew), macOS 26.6.2 (25G83),
  arm64.
- Node: a Node.js installation of other software is on `PATH`. No MP step starts it or any other
  Node.
- Available operations: Git reads, local commits, non-forced pushes; GitHub API reads and comments;
  the two approved downloads.

## Verification

- Commands planned: the preparation plan, sections 3 and 5.
- Not run in this phase: Node, `ldd`, `codesign`, M0, M1, N34-M, the qualifying cohort, the routine
  driver, and the visual-verification profile.

## Recovery

- Unpublished commits: none after the push of this declaration, which the next checkpoint observes.
- Outstanding operations and owned processes: none.
- Current blockers with concrete evidence: none. P30-EXECUTOR-001 still blocks the Linux
  contract's H0 and H1 in local mode.

## Coordination

- Integration owner and lease status: none; main's lease is released and is not used.
- Ownership: owner `c271-p34-ec1a7de2360d` holds this branch for the phase.

## Continuation

- One exact next action: the two approved downloads (plan step 2).
- Stopping condition: the reviewed preparation pushed and read back with its records, or a
  concrete blocker.

No receipt of the receipt: Git reveals the commit that carries this record.
