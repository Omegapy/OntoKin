# Session checkpoint: C271-P36 gate MR, the complete default routine and R03 acceptance

Follows current main's [session template](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/docs/workflow/templates/SESSION.md).
Detailed evidence is linked, not repeated. Machine paths are left out; places beside the clone
are named relative to it. Times are UTC. This is the closing version of the checkpoint, written
when MR stopped at stage S6. The declaration version is in this file's history at `d3b622d6`, and
the commit B version at `4ca78142`.

## Identity

- Checkpoint time and author identity: 2026-11-27T22:40Z, Director `c271-p36-14f7f8b219db`.
- Task, session, and agent or tool identity: C271, phase C271-P36-macos-complete-routine-mr;
  the same Claude Code session (model Claude Opus 5.5) that carried out C271-P30 to P35, working
  in the C271 worktree. Its context was compacted after P35 and again during S6. After each
  compaction the verified read-set was kept, the live state reconciled, and the entry document
  and PROTOCOL's sections for the next step opened again.
- Execution mode, and the entry document or record that declared it: `local`, from current main's
  [LOCAL-START-HERE](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/LOCAL-START-HERE.md);
  C271's record names local mode since R07.
- Worktree and branch: `../OntoKin-worktrees/c271`, on `work/c271-missing-import-digest-control`.
- Current user objective and bounded milestone: gate MR of the adopted contract
  `ontokin.current-host-readback/0.2.0`, which is R03 on this executor. The owner typed "Start gate
  MR" ([phase declaration](../../../engineering/localized-repair-c271/macos-routine-p36/PHASE.json),
  [MR plan](../../../engineering/localized-repair-c271/macos-routine-p36/MR-PLAN.md)).
- Task, requirements, and plan paths: [task.json](task.json), [REQUIREMENTS](REQUIREMENTS.md)
  (sections R03 and P36), [PLAN](PLAN.md) (section P36).

## Context loaded

- Entry file and registry revision: current main `51223c9b94a222f29d38eb6c33808f8e55e2bff9`, whose
  instruction files this branch carries since gate MB. None of them changed during the phase.
- Required read-set actually opened, with revision or hash: as the declaration version lists, at
  `47cc579f`. For S6 and the closing, also opened at B:
  - the MR plan in full;
  - `tools/check_local.py`'s copy, Git and derivation code;
  - the provider's source and derivation code;
  - main's two baseline summaries;
  - LOCAL-START-HERE;
  - PROTOCOL sections 1, 2 and 8;
  - HANDOFF's local section;
  - the session template.
- Required files missing, truncated, or inaccessible: none.
- Current/deferred product work and applicable adopted contracts: no product work. P05's
  `ontokin.current-host-readback/0.1.0` and its plans `/0.1.1` to `/0.1.5` stay adopted and
  unchanged. GOAL's ceilings of 100,000 operations and 30,000 ms are unchanged.

## Source

- Starting revision and current code checkpoint: started at `47cc579f`. Commit B is
  `4ca781429c5411c67c0965bc69306b42c6cc74ad`, tree `0935162c72fd9d804681e920da6f6d6e9066ff28`. The
  records commit that carries this file follows B.
- Dirty and untracked state: from the observation plan's freeze until the closing records, the
  worktree was clean apart from its ignored `.venv`. The closing records are the only change. The
  main checkout's owner items stay untouched.
- Actual remote observation, with command and time: `git ls-remote --heads origin` at
  2026-11-27T22:38:02Z read:
  - this branch at `4ca78142`;
  - main at `51223c9b`;
  - `work/c271-p29-trd-record` at `880933a4`, which this phase does not touch.
- Repository, actual main SHA/tree, and observation time: `Omegapy/OntoKin`, main
  `51223c9b94a222f29d38eb6c33808f8e55e2bff9` at 22:38:02Z.
- Active branch/head, open PR, and scope issue: [PR274](https://github.com/Omegapy/OntoKin/pull/274)
  open and draft, head `4ca78142`, MERGEABLE and CLEAN; [issue273](https://github.com/Omegapy/OntoKin/issues/273)
  open.
- Local checkout identity and unpublished changes: the C271 worktree; the records commit is
  unpublished until its push, which the phase's `CLOSING.json`, added by the next commit, records.

## Work

- Requirements: R01 and R02 done; R03, R04 and R05 not_done. Task status `in_progress`.
- Acceptance items: A1 to A5 met; A6 not met; A7, A8 and A9 not run; A10 partly met; A11 is this
  closing, whose push, readback and comments CLOSING.json records
  ([outcome](../../../engineering/localized-repair-c271/macos-routine-p36/OUTCOME.json)).
- Last completed gate: S5. HOST `858ef72a949ce7575787290601ae70d117090a460781b2e660a3b0d4f0162666` was
  accepted by an independent review, after M0 and M1 made one Git and one Node start.
- **The blocker, FZ-01.** [Freeze review 001](../../../engineering/localized-repair-c271/macos-routine-p36/reviews/freeze-review-001/FREEZE-REVIEW-001.md)
  rejected operational freeze 001, and the Director confirmed the reason by reading
  ([disposition](../../../engineering/localized-repair-c271/macos-routine-p36/reviews/FREEZE-REVIEW-DISPOSITION-001.json)).
  - R1 would refuse in the driver's preparation at B.
  - The driver copies only its source directories and root files into the workspace. B's seven
    tracked `.claude/` entries are therefore deleted there, and the provider's derived source check
    refuses them.
  - Main's own baseline summaries record those seven deletions.
  - The cause lies in the implementation. So MR stopped at S6 under MR-PLAN section 9, and R1, R2,
    the audit and the R03 review never ran.
- Changed artifact paths: the phase directory's `plans/`, `host/`, `director/` and `reviews/` (the
  portable copies, with [EXACT-RECORDS.json](../../../engineering/localized-repair-c271/macos-routine-p36/EXACT-RECORDS.json));
  `OUTCOME.json`, `LEARNING-DECISION.md`, `README-PORTABLE.md`, `checks/closing/`; task.json,
  CURRENT.json, memory.json, REQUIREMENTS, PLAN and this file.
- Decisions made:
  - MR stops at S6.
  - No run is frozen that would expect the refusal.
  - R2 is not run alone in P36.
  - FZ-02 to FZ-09 are carried to the next MR freeze.
- Remaining items: the next phase, which the owner selects.
- Learning checkpoint result and capture preference: one lesson captured,
  `memory-c271-derived-workspace-tracked-paths` ([decision](../../../engineering/localized-repair-c271/macos-routine-p36/LEARNING-DECISION.md)).

## Environment

- Profile and its readiness: as MP prepared it and MH left it. The doctor reports `core` ready and
  `python-verification` as `not_checked`, by design (D-21). The `.venv` holds no bytecode.
- Interpreter, operating system and architecture: CPython 3.12.13, macOS 26.6.2 (25G83), arm64;
  the boot session `C90010BA`, unchanged through the phase.
- Manifest and lock identities: unchanged since MP.
- Relevant tool versions: Git `git version 2.50.1 (Apple Git-155)` and the pinned Node `v24.22.1`,
  as HOST records them.
- Terminal and executed interpreter/platform: Claude Code's shell tool in the desktop app. Every
  start of the framework interpreter used `-B`, apart from one reviewer start that had
  `PYTHONDONTWRITEBYTECODE=1` set.
- Available operations: Git reads, local commits, non-forced pushes; GitHub API reads and comments.
  No download.
- Missing capabilities and their effect: none for this milestone.

## Verification

- Commands actually executed and observed outcomes:
  - static, `STATIC_READY`, with no start;
  - observe, exit 0, `OBSERVED_UNAPPROVED`, one Git and one Node start;
  - the workers' read-only starts, which their records list;
  - the Director's Git reads of HEAD, status and B's tree;
  - the records checks ([check record](../../../engineering/localized-repair-c271/macos-routine-p36/checks/closing/CHECKS.json)).
- Failures: the freeze review's rejection (FZ-01), and tooling review 001's earlier rejection.
- Pending and not-run checks: R1, R2, the audit and the R03 review; the complete routine at B.
- Durable logs, review findings, and evidence links: the [portable records](../../../engineering/localized-repair-c271/macos-routine-p36/README-PORTABLE.md).
  The exact files stay beside the clone under `../OntoKin-local/c271-p36/`.
- Evidence locations and hashes: EXACT-RECORDS.json lists each exact file with its SHA-256.
- Relevant validation/CI results: no hosted CI was used or awaited.
- Current review eligibility: commit B's freeze was rejected, so B cannot be run for MR.

## Recovery

- Unpublished commits: the records commit until its push; CLOSING.json records the readback.
- Unique uncommitted files: none in the worktree. The exact records beside the clone are durable
  there and listed by digest.
- Outstanding operations and owned processes: none. No routine, observer or Node process is left.
- Unknown operation: none.
- Remote readback needed before retrying an operation: not applicable.
- Current blockers with concrete evidence: FZ-01 blocks MR at B. P30-EXECUTOR-001 still blocks the
  Linux contract's H0 and H1 in local mode.
- Unpublished work that must be recovered: none.
- Actual unpublished recovery payloads and declared external dependencies: none.

## Coordination

- Active workers and reserved files: none. Every worker returned, and none made a Git write or
  edited the worktree.
- Actual subagents and assigned scopes: W1, W2 (tooling, plan and freeze authors), W3 (two tooling
  reviews, the plan, HOST and freeze reviews), each in a fresh context, as
  [the worker log](../../../engineering/localized-repair-c271/macos-routine-p36/director/WORKERS.md)
  lists. W4 was never started.
- Integration owner and lease status: none; main's lease is released and was not used.
- Ownership: owner `c271-p36-14f7f8b219db` releases the branch at this closing.

## Continuation

- One exact next action: the owner selects the next phase. The recommended one is a correction for
  FZ-01. It decides, under contract section 7 and MC19, how a derived workspace treats tracked
  paths that the driver does not copy. It adds controls that exercise the derived route on a tree
  that tracks such paths, and it passes the routine checks with `PATH` fixed as D-P1 fixes it.
  MR then runs again at the corrected commit, with a new observation plan, HOST and freeze.
- The condition that makes that action safe and useful: the owner's selection; the fixed state of
  MR-PLAN section 6 ends with this closing, and the next MR attempt starts at S4 with new records.

## Delivery

- Local checkpoint status: the records commit on this branch.
- Verified push state: recorded in CLOSING.json after the push.
- Actual merge/resulting-main checks: none; nothing is integrated into main.
- Branch retention: the branch and PR274 stay open, and PR274 stays draft.
- Durable evidence references: the phase directory and `../OntoKin-local/c271-p36/`.
- Integration state separate from saved-delivery state: not integrated; the records are pushed.
- Published checkpoint revision and readback result: in CLOSING.json.

No receipt of the receipt: Git reveals the commit that carries this record.
