# Session checkpoint: C271-P36 gate MR, the complete default routine and R03 acceptance

Follows current main's [session template](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/docs/workflow/templates/SESSION.md).
Detailed evidence is linked, not repeated. Machine paths are left out; places beside the clone
are named relative to it. Times are UTC. This is the declaration version of the checkpoint.

## Identity

- Checkpoint time and author identity: 2026-11-27T15:46:53Z, Director `c271-p36-14f7f8b219db`.
- Task, session, and agent or tool identity: C271, phase C271-P36-macos-complete-routine-mr;
  the same Claude Code session (model Claude Opus 5.5) that carried out C271-P30 to P35, working
  in the C271 worktree. The session's context was compacted after P35; the read-set below was
  opened again afterwards.
- Execution mode, and the entry document or record that declared it: `local`, from current main's
  [LOCAL-START-HERE](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/LOCAL-START-HERE.md),
  read again for this phase; C271's record names local mode since R07.
- Owner direction: on 2026-11-27 the owner was asked "Should I start gate MR, the complete routine
  (R03)?" and typed "Start gate MR" in this session. MR needs no download, and none is approved.
- Worktree and branch: `../OntoKin-worktrees/c271`, on `work/c271-missing-import-digest-control`.
- Current user objective and bounded milestone: gate MR of the adopted contract
  `ontokin.current-host-readback/0.2.0`, which is R03 on this executor
  ([phase declaration](../../../engineering/localized-repair-c271/macos-routine-p36/PHASE.json),
  [MR plan](../../../engineering/localized-repair-c271/macos-routine-p36/MR-PLAN.md)).
- Task, requirements, and plan paths: [task.json](task.json), [REQUIREMENTS](REQUIREMENTS.md)
  (sections R03 and P36), [PLAN](PLAN.md) (section P36).

## Context loaded

- Entry file and registry revision: current main `51223c9b94a222f29d38eb6c33808f8e55e2bff9`, whose
  instruction files this branch carries since gate MB. After the compaction, the local read-set of
  the registry was opened again in full: LOCAL-START-HERE, AGENTS, GOAL, STATUS (apart from its
  anchor-only lines), ROLE, the registry, CURRENT and PROTOCOL.
- Required read-set actually opened, with revision or hash, at this branch's head `47cc579f`:
  - the adopted [CONTRACT](../../../engineering/localized-repair-c271/macos-contract-design-p31/CONTRACT.md),
    sections 1, 2 and 7 to 12;
  - the obligations that MI's [outcome](../../../engineering/localized-repair-c271/macos-implementation-p33/OUTCOME.json)
    and MH's [outcome](../../../engineering/localized-repair-c271/macos-qualification-p35/OUTCOME.json)
    carry to MR, and MI's [inventory additions](../../../engineering/localized-repair-c271/macos-implementation-p33/INVENTORY-ADDITIONS.json);
  - P05's contract, its Gate R;
  - [OK-ENG-009](../../../engineering/OK-ENG-009-development-integration-and-branch-lifecycle.md)
    section 3;
  - main's recorded macOS baseline:
    [BASELINE-CHECKS.json](../../../engineering/local-migration-20261124/BASELINE-CHECKS.json) and
    the resulting-main runs in [INTEGRATION.json](../../../engineering/local-migration-20261124/INTEGRATION.json);
  - `tools/check_local.py`, and the provider's selection and HOST cross-binding code.
- Required files missing, truncated, or inaccessible: none.
- Current/deferred product work and applicable adopted contracts: no product work. P05's
  `ontokin.current-host-readback/0.1.0` and its plans `/0.1.1` to `/0.1.5` stay adopted and
  unchanged. GOAL's ceilings of 100,000 operations and 30,000 ms are unchanged.

## Source

- Starting revision: `47cc579fa28e23d3424a46c72fd80a71d73440dc`, which is P35's closing record.
- Dirty and untracked state: the worktree was clean, apart from its ignored `.venv`. The main
  checkout's owner items stay untouched.
- Actual remote observation, with command and time: `git ls-remote --heads origin` at
  2026-11-27T15:32:05Z read:
  - this branch at `47cc579f`;
  - main at `51223c9b`;
  - `work/c271-p29-trd-record` at `880933a4`, which this phase does not touch.
- Repository, actual main SHA, and observation time: `Omegapy/OntoKin`, main
  `51223c9b94a222f29d38eb6c33808f8e55e2bff9` at 15:32:05Z.
- Active branch/head, open PR, and scope issue: [PR274](https://github.com/Omegapy/OntoKin/pull/274)
  open and draft, head `47cc579f`, MERGEABLE and CLEAN; [issue273](https://github.com/Omegapy/OntoKin/issues/273)
  open.

## Work

- Requirements: R01 and R02 done; R03, R04 and R05 not_done. P01 done, P02 in_progress. Task
  status `in_progress`.
- Acceptance items: A1 to A11 of the declaration. None is complete at this checkpoint.
- Workers: W1 to W4 of the MR plan, section 3. None is launched at this checkpoint.
- MH's HOST is not reused: it binds the source at MH's commit `0eb9a551`, and this branch's head
  has moved since. MR observes the host again (stages S4 and S5).

## Environment

- Profile and its readiness: as MP prepared it and MH left it. The doctor, run with `--node` at a
  nonexistent path so that it starts no Node, reports `core` ready and `python-verification` as
  `not_checked`, because pip is absent by design (D-21). The `.venv` holds no bytecode.
- Interpreter, operating system and architecture: CPython 3.12.13, macOS 26.6.2 (25G83), arm64;
  the boot session of 2026-11-23, the same as MH's.
- Node: the pinned runtime beside the clone, which MH started 9 times through its bounded routes. A
  Node.js installation of other software is on `PATH`; no MR step may start it (plan section 4).
- Available operations: Git reads, local commits, non-forced pushes; GitHub API reads and comments.
  No download.

## Verification

- Commands run for this checkpoint, each start of the framework interpreter with `-B`: the doctor
  as above, and the workflow check, which passed with 13 tasks.
- Commands planned: stages S2 to S9 of the MR plan.
- Not run in this phase at this checkpoint: M0, M1, the routine driver, any Node, `ldd` or
  `codesign` start, and the visual-verification profile.

## Recovery

- Unpublished commits: none after the push of this declaration, which the next checkpoint observes.
- Outstanding operations and owned processes: none.
- Current blockers with concrete evidence: none. P30-EXECUTOR-001 still blocks the Linux
  contract's H0 and H1 in local mode.

## Coordination

- Integration owner and lease status: none; main's lease is released and is not used.
- Ownership: owner `c271-p36-14f7f8b219db` holds this branch for the phase.

## Continuation

- One exact next action: stages S2 and S3 of the MR plan, the start-and-write inventory and the
  tooling, at the same time.
- Stopping condition: R03 accepted, with the audited runs and their records pushed and read back;
  or a concrete blocker.

No receipt of the receipt: Git reveals the commit that carries this record.
