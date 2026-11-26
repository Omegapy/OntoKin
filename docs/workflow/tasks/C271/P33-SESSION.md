# Session checkpoint: C271-P33 gate MI, implementation of the 0.2.0 adaptations

Follows current main's [session template](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/docs/workflow/templates/SESSION.md).
Detailed evidence is linked, not repeated. Machine paths are left out; places beside the clone
are named relative to it. Times are UTC. This is the declaration version of the checkpoint.

## Identity

- Checkpoint time and author identity: 2026-11-26T14:36:34Z, Director `c271-p33-a99647756bed`.
- Task, session, and agent or tool identity: C271, phase C271-P33-macos-implementation-mi; the
  same Claude Code session (model Claude Opus 5.5) that carried out C271-P30, P31 and P32, working
  in the C271 worktree.
- Execution mode, and the entry document or record that declared it: `local`, from current main's
  [LOCAL-START-HERE](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/LOCAL-START-HERE.md);
  C271's record names local mode since R07.
- Owner direction: on 2026-11-26, the owner was asked "Should I start gate MI, the implementation
  of the 0.2.0 macOS adaptations?" and typed "Start gate MI" in this session.
- Worktree and branch: `../OntoKin-worktrees/c271`, on `work/c271-missing-import-digest-control`.
- Current user objective and bounded milestone: gate MI of the adopted contract
  `ontokin.current-host-readback/0.2.0` ([phase declaration](../../../engineering/localized-repair-c271/macos-implementation-p33/PHASE.json),
  [implementation plan](../../../engineering/localized-repair-c271/macos-implementation-p33/IMPLEMENTATION-PLAN.md)).
- Task, requirements, and plan paths: [task.json](task.json), [REQUIREMENTS](REQUIREMENTS.md)
  (section P33), [PLAN](PLAN.md) (section P33).

## Context loaded

- Entry file and registry revision: current main `51223c9b94a222f29d38eb6c33808f8e55e2bff9`,
  which this session read for P30 to P32. Main is unchanged, and gate MB put the same bytes on
  this branch. After a context compaction, LOCAL-START-HERE and PROTOCOL section 4 were opened
  again.
- Required read-set actually opened, with revision or hash: the adopted
  [CONTRACT](../../../engineering/localized-repair-c271/macos-contract-design-p31/CONTRACT.md)
  (42,769 bytes, SHA-256 `42db98dc…`) and [CONTRACT.json](../../../engineering/localized-repair-c271/macos-contract-design-p31/CONTRACT.json)
  (43,340 bytes, SHA-256 `c843fc96…`), both read in full, together with the outlines of the
  0.1.0 provider, probe, preparer, supervisor and driver.
- Required files missing, truncated, or inaccessible: none.
- Current/deferred product work and applicable adopted contracts: no product work. P05's
  `ontokin.current-host-readback/0.1.0` and its plans `/0.1.1` to `/0.1.5` stay adopted and
  unchanged. GOAL's ceilings of 100,000 operations and 30,000 ms are unchanged.

## Source

- Starting revision: `1c2f25ba224a5c3419004d1d331d29e01378ae00`, which is P32's closing record.
- Dirty and untracked state: the worktree was clean, apart from its ignored `.venv`. The main
  checkout's owner items stay untouched.
- Actual remote observation, with command and time: `git ls-remote --heads origin` at
  2026-11-26T14:24:42Z and again at 14:35:07Z read:
  - this branch at `1c2f25ba`;
  - main at `51223c9b`;
  - `work/c271-p29-trd-record` at `880933a4`, which this phase does not touch.
- Repository, actual main SHA, and observation time: `Omegapy/OntoKin`, main
  `51223c9b94a222f29d38eb6c33808f8e55e2bff9` at 14:35:07Z.
- Active branch/head, open PR, and scope issue: [PR274](https://github.com/Omegapy/OntoKin/pull/274)
  open, draft, mergeable and clean against main; [issue273](https://github.com/Omegapy/OntoKin/issues/273) open.

## Work

- Requirements: R01 and R02 done; R03, R04 and R05 not_done. P01 done, P02 in_progress. Task
  status `in_progress`.
- Acceptance items: A1 to A9 of the declaration. None is complete at this checkpoint.
- Workers: W1 to W7 of the implementation plan, section 3. None is launched at this checkpoint.

## Environment

- Profile and its readiness: the doctor reports `core` ready and `python-verification` missing.
  The worktree's `.venv` holds none of the seven pinned packages, and preparing them is gate MP's.
  MI uses the standard library only.
- Interpreter, operating system and architecture: CPython 3.12.13 (Homebrew), macOS 26.6.2 (25G83), arm64.
- Available operations: Git reads, local commits, non-forced pushes; GitHub API reads and comments.

## Verification

- Commands planned: the implementation plan, section 7. The routine driver is not run, because
  its complete routine is gate MR's.
- Not run in this phase: Node, `ldd`, `codesign`, downloads, installs, M0 and M1 on the real
  host, the qualifying cohort.

## Recovery

- Unpublished commits: none after the push of this declaration, which the next checkpoint observes.
- Outstanding operations and owned processes: none.
- Current blockers with concrete evidence: none. P30-EXECUTOR-001 still blocks the Linux
  contract's H0 and H1 in local mode.

## Coordination

- Integration owner and lease status: none; main's lease is released and is not used.
- Ownership: owner `c271-p33-a99647756bed` holds this branch for the phase.

## Continuation

- One exact next action: launch W1, W2 and W3 of the implementation plan.
- Stopping condition: the reviewed implementation pushed and read back with its records, or a
  concrete blocker.

No receipt of the receipt: Git reveals the commit that carries this record.
