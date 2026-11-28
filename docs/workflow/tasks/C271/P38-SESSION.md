# Session checkpoint: C271-P38, gate MR's second attempt

Follows current main's [session template](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/docs/workflow/templates/SESSION.md).
Detailed evidence is linked, not repeated. Machine paths are left out; places beside the clone are
named relative to it. Times are UTC. This is the declaration version of the checkpoint.

## Identity

- Checkpoint time and author identity: 2026-11-28T02:35:52Z, Director `c271-p38-1e501e005f79`.
- Task, session, and agent or tool identity: C271, phase C271-P38-macos-complete-routine-mr-2; the same
  Claude Code session (model Claude Opus 5.5) that carried out C271-P30 to P37, in the C271 worktree.
- Execution mode, and the entry document or record that declared it: `local`, from current main's
  [LOCAL-START-HERE](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/LOCAL-START-HERE.md);
  C271's record names local mode since R07.
- Owner direction: after C271-P37 closed, the owner was asked "Start gate MR again now, or leave it for
  later?" and selected "Start gate MR". No download is needed, and none is approved.
- Worktree and branch: `../OntoKin-worktrees/c271`, on `work/c271-missing-import-digest-control`.
- Current user objective and bounded milestone: gate MR's second attempt
  ([phase declaration](../../../engineering/localized-repair-c271/macos-routine-p38/PHASE.json),
  [plan](../../../engineering/localized-repair-c271/macos-routine-p38/MR-PLAN-2.md), which follows
  [P36's MR plan](../../../engineering/localized-repair-c271/macos-routine-p36/MR-PLAN.md)).
- Task, requirements, and plan paths: [task.json](task.json), [REQUIREMENTS](REQUIREMENTS.md)
  (section P38), [PLAN](PLAN.md) (section P38).

## Context loaded

- Entry file and registry revision: current main `51223c9b94a222f29d38eb6c33808f8e55e2bff9`, whose
  instruction files this branch carries since gate MB. None of them changed.
- Required read-set actually opened, with revision or hash: the verified read-sets of P36's and P37's
  checkpoints, kept; P36's MR plan; P37's outcome and review.
- Required files missing, truncated, or inaccessible: none.
- Current/deferred product work and applicable adopted contracts: no product work. P05's
  `ontokin.current-host-readback/0.1.0` and its plans `/0.1.1` to `/0.1.5` stay adopted and
  unchanged. GOAL's ceilings are unchanged.

## Source

- Starting revision and current code checkpoint: `e7f05fc95adff2c258f1c9322a9a3fec69616f27`, P37's closing
  record. Its code is P37's candidate `5a3502e2`, unchanged. This declaration is the next commit.
- Dirty and untracked state: the worktree was clean apart from its ignored `.venv`. The main checkout's
  owner items stay untouched.
- Actual remote observation, with command and time: `git ls-remote --heads origin` at
  2026-11-28T02:34:45Z read this branch at `e7f05fc9`, main at `51223c9b` and
  `work/c271-p29-trd-record` at `880933a4`.
- Repository, actual main SHA/tree, and observation time: `Omegapy/OntoKin`, main `51223c9b` at
  02:34:45Z.
- Active branch/head, open PR, and scope issue: [PR274](https://github.com/Omegapy/OntoKin/pull/274)
  open and draft; [issue273](https://github.com/Omegapy/OntoKin/issues/273) open.
- Local checkout identity and unpublished changes: the C271 worktree; this declaration until its push.

## Work

- Requirements: R01 and R02 done; R03, R04 and R05 not_done. Task status `in_progress`.
- Acceptance items: A1 is met by this commit's push; A2 to A11 not yet.
- Changed artifact paths: the phase directory's `PHASE.json` and `MR-PLAN-2.md`; task.json, CURRENT.json,
  REQUIREMENTS, PLAN and this file.
- Decisions made: none beyond the plan.
- Remaining items: stages S2 to S10.
- Learning checkpoint result and capture preference: at the phase's close.

## Environment

- Profile and its readiness: as MP prepared it. The Python installation inventory was `c277bdd3` at
  P37's routine run. The `.venv` holds no bytecode.
- Interpreter, operating system and architecture: CPython 3.12.13, macOS 26.6.2 (25G83), arm64; the
  boot session `C90010BA`.
- Manifest and lock identities: unchanged since MP.
- Relevant tool versions: HOST's Git, `git version 2.50.1 (Apple Git-155)`; the pinned Node `v24.22.1`.
- Terminal and executed interpreter/platform: Claude Code's shell tool in the desktop app; every start of
  the framework interpreter with `-B`.
- Available read/write/conditional-update/merge operations: Git reads, local commits, non-forced pushes;
  GitHub API reads and comments. No download.
- Missing capabilities and their effect on this milestone: no prepared Git LFS client (P37's recorded
  limit).

## Verification

- Commands actually executed and observed outcomes: this commit's records checks.
- Failures: none at this checkpoint.
- Pending and not-run checks: stages S2 to S10.
- Durable logs, review findings, and evidence links: P36's and P37's outcomes.
- Evidence locations and hashes: under `../OntoKin-local/c271-p38/` as the phase proceeds.
- Relevant validation/CI results and source revisions: no hosted CI is used or awaited.
- Current review eligibility and any changes since review: P37's candidate is reviewed and accepted;
  this phase's bound commit B2 adds only records.

## Recovery

- Unpublished commits: this declaration until its push.
- Unique uncommitted files: none.
- Outstanding operations and owned processes: none.
- Unknown operation: none.
- Remote readback needed before retrying that operation: not applicable.
- Current blockers with concrete evidence: none. P30-EXECUTOR-001 still blocks the Linux contract's H0
  and H1 in local mode.
- Unpublished work that must be recovered: none.
- Actual unpublished recovery payloads and declared external dependencies: none.

## Coordination

- Active workers and reserved files: none yet.
- Actual subagents, assigned scopes, and unresolved worker activity: none yet.
- Integration owner, expiry, and latest verified ownership record: none; main's lease is released and is
  not used.
- Lease status: not used.
- Ownership released, renewed, transferred, or still uncertain: owner `c271-p38-1e501e005f79` holds this
  branch for the phase.

## Continuation

- One exact next action: stage S2, the inventory addendum by a fresh W1, read only.
- The condition that makes that action safe and useful: this declaration pushed and read back. From the
  observation plan's freeze to the end of the audit, P36's host rules apply again.

## Delivery

- Local checkpoint status: this declaration commit.
- Verified push state, or unconfirmed: observed after the push.
- Actual merge/resulting-main checks, or remaining integration gate: none; R04 integrates.
- Branch retention/deletion evidence, or exact pending cleanup instruction: the branch and PR274 stay
  open; PR274 stays draft.
- Durable evidence references: the phase directory and `../OntoKin-local/c271-p38/`.
- Integration state separate from saved-delivery state: not integrated.
- Published checkpoint revision and readback result: observed after the push.

No receipt of the receipt: Git reveals the commit that carries this record.
