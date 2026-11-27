# Session checkpoint: C271-P37, correction of the derived workspace's source check

Follows current main's [session template](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/docs/workflow/templates/SESSION.md).
Detailed evidence is linked, not repeated. Machine paths are left out; places beside the clone
are named relative to it. Times are UTC. This is the declaration version of the checkpoint.

## Identity

- Checkpoint time and author identity: 2026-11-27T23:16:33Z, Director `c271-p37-08beec34eb0a`.
- Task, session, and agent or tool identity: C271, phase C271-P37-derived-workspace-correction; the
  same Claude Code session (model Claude Opus 5.5) that carried out C271-P30 to P36, working in the
  C271 worktree.
- Execution mode, and the entry document or record that declared it: `local`, from current main's
  [LOCAL-START-HERE](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/LOCAL-START-HERE.md),
  read again for this phase; C271's record names local mode since R07.
- Owner direction: after gate MR stopped, the owner was asked "Should I start that correction phase
  now, or leave it for later?" and selected "Start the correction" in this session. The correction
  needs no download, and none is approved.
- Worktree and branch: `../OntoKin-worktrees/c271`, on `work/c271-missing-import-digest-control`.
- Current user objective and bounded milestone: the correction of FZ-01, gate MR's implementation
  blocker ([phase declaration](../../../engineering/localized-repair-c271/derived-workspace-p37/PHASE.json),
  [correction plan](../../../engineering/localized-repair-c271/derived-workspace-p37/CORRECTION-PLAN.md)).
- Task, requirements, and plan paths: [task.json](task.json), [REQUIREMENTS](REQUIREMENTS.md)
  (section P37), [PLAN](PLAN.md) (section P37).

## Context loaded

- Entry file and registry revision: current main `51223c9b94a222f29d38eb6c33808f8e55e2bff9`, whose
  instruction files this branch carries since gate MB. None of them changed.
- Required read-set actually opened, with revision or hash, at this branch's head `07d4e3c3`:
  - the verified read-set of P36's checkpoint, kept;
  - LOCAL-START-HERE;
  - PROTOCOL sections 1 to 5 and 8;
  - HANDOFF's local section;
  - the 0.2.0 [contract](../../../engineering/localized-repair-c271/macos-contract-design-p31/CONTRACT.md),
    sections 1, 7, 8, 9 and 11;
  - P05's [contract](../../../engineering/localized-repair-c271/current-host-p05/CONTRACT.md) section 3;
  - MI's implementation plan and its amendment's adoption record;
  - MI's frozen controls for MC19;
  - the driver's copy, inventory and Git code, and the 0.2.0 and 0.1.0 providers' source checks.
- Required files missing, truncated, or inaccessible: none.
- Current/deferred product work and applicable adopted contracts: no product work. P05's
  `ontokin.current-host-readback/0.1.0` and its plans `/0.1.1` to `/0.1.5` stay adopted and
  unchanged. GOAL's ceilings of 100,000 operations and 30,000 ms are unchanged.

## Source

- Starting revision and current code checkpoint: `07d4e3c31e31054b147b586569f29cff3d945d5b`, P36's
  closing record. This declaration is the next commit.
- Dirty and untracked state: the worktree was clean apart from its ignored `.venv`. The main
  checkout's owner items stay untouched.
- Actual remote observation, with command and time: `git ls-remote --heads origin` at
  2026-11-27T23:13:44Z read:
  - this branch at `07d4e3c3`;
  - main at `51223c9b`;
  - `work/c271-p29-trd-record` at `880933a4`, which this phase does not touch.
- Repository, actual main SHA/tree, and observation time: `Omegapy/OntoKin`, main
  `51223c9b94a222f29d38eb6c33808f8e55e2bff9` at 23:13:44Z.
- Active branch/head, open PR, and scope issue: [PR274](https://github.com/Omegapy/OntoKin/pull/274)
  open and draft, head `07d4e3c3`; [issue273](https://github.com/Omegapy/OntoKin/issues/273) open.
- Local checkout identity and unpublished changes: the C271 worktree; this declaration until its push.

## Work

- Requirements: R01 and R02 done; R03, R04 and R05 not_done. Task status `in_progress`.
- Acceptance items: A1 is met by this commit's push; A2 to A8 not yet.
- Changed artifact paths: the phase directory's `PHASE.json` and `CORRECTION-PLAN.md`; task.json,
  CURRENT.json, REQUIREMENTS, PLAN and this file.
- Decisions made: none on the rule. The independent author makes that decision at S3.
- Remaining items: stages S2 to S8 of the plan.
- Learning checkpoint result and capture preference: at the phase's close.

## Environment

- Profile and its readiness: as MP prepared it. The doctor, run with `--node` at a nonexistent path,
  reports `core` ready and `python-verification` as `not_checked`, because pip is absent by design
  (D-21). Its advice to rebuild the `.venv` is not followed. The `.venv` holds no bytecode.
- Interpreter, operating system and architecture: CPython 3.12.13, macOS 26.6.2 (25G83), arm64.
- Manifest and lock identities: unchanged since MP.
- Relevant tool versions: HOST's Git, `git version 2.50.1 (Apple Git-155)`.
- Terminal and executed interpreter/platform: Claude Code's shell tool in the desktop app; every start
  of the framework interpreter with `-B`.
- Available read/write/conditional-update/merge operations: Git reads, local commits, non-forced
  pushes; GitHub API reads and comments. No download.
- Missing capabilities and their effect on this milestone: none.

## Verification

- Commands actually executed and observed outcomes:
  - the doctor as above;
  - the workflow check, which passed with 13 tasks;
  - this commit's records checks.
- Failures: none at this checkpoint.
- Pending and not-run checks: S2 to S8.
- Durable logs, review findings, and evidence links: gate MR's [outcome](../../../engineering/localized-repair-c271/macos-routine-p36/OUTCOME.json)
  and its freeze review hold FZ-01 and FZ-02.
- Evidence locations and hashes: under `../OntoKin-local/c271-p37/` as the phase proceeds.
- Relevant validation/CI results and source revisions: no hosted CI is used or awaited.
- Current review eligibility and any changes since review: not applicable yet.

## Recovery

- Unpublished commits: this declaration until its push.
- Unique uncommitted files: none.
- Outstanding operations and owned processes: none.
- Unknown operation: none.
- Remote readback needed before retrying that operation: not applicable.
- Current blockers with concrete evidence: FZ-01 blocks gate MR, which this phase corrects.
  P30-EXECUTOR-001 still blocks the Linux contract's H0 and H1 in local mode.
- Unpublished work that must be recovered: none.
- Actual unpublished recovery payloads and declared external dependencies: none.

## Coordination

- Active workers and reserved files: none yet; the plan's section 3 reserves each worker's files.
- Actual subagents, assigned scopes, and unresolved worker activity: none yet.
- Integration owner, expiry, and latest verified ownership record: none; main's lease is released
  and is not used.
- Lease status: not used.
- Ownership: owner `c271-p37-08beec34eb0a` holds this branch for the phase.

## Continuation

- One exact next action: stage S2 of the plan, FZ-02's measurement in a workspace that the driver's
  own `prepare_workspace` copies from the clean worktree at this commit, outside the checkout.
- The condition that makes that action safe and useful: this declaration pushed and read back; the
  worktree clean; no Node, `ldd` or `codesign` start.

## Delivery

- Local checkpoint status: this declaration commit.
- Verified push state, or unconfirmed: observed after the push.
- Actual merge/resulting-main checks, or remaining integration gate: none; R04 integrates.
- Branch retention/deletion evidence, or exact pending cleanup instruction: the branch and PR274
  stay open; PR274 stays draft.
- Durable evidence references: the phase directory and `../OntoKin-local/c271-p37/`.
- Integration state separate from saved-delivery state: not integrated.
- Published checkpoint revision and readback result: observed after the push.

No receipt of the receipt: Git reveals the commit that carries this record.
