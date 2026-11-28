# Session checkpoint: C271-P37, correction of the derived workspace's source check

Follows current main's [session template](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/docs/workflow/templates/SESSION.md).
Detailed evidence is linked, not repeated. Machine paths are left out; places beside the clone
are named relative to it. Times are UTC. This is the closing version of the checkpoint. The
declaration version is in this file's history at `2f728998`.

## Identity

- Checkpoint time and author identity: 2026-11-28T02:40Z, Director `c271-p37-08beec34eb0a`.
- Task, session, and agent or tool identity: C271, phase C271-P37-derived-workspace-correction; the
  same Claude Code session (model Claude Opus 5.5) that carried out C271-P30 to P36, working in the
  C271 worktree.
- Execution mode, and the entry document or record that declared it: `local`, from current main's
  [LOCAL-START-HERE](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/LOCAL-START-HERE.md);
  C271's record names local mode since R07.
- Owner direction: "Start the correction", in this session, after gate MR stopped.
- Worktree and branch: `../OntoKin-worktrees/c271`, on `work/c271-missing-import-digest-control`.
- Current user objective and bounded milestone: the correction of FZ-01 and FZ-02
  ([phase declaration](../../../engineering/localized-repair-c271/derived-workspace-p37/PHASE.json),
  [correction plan](../../../engineering/localized-repair-c271/derived-workspace-p37/CORRECTION-PLAN.md)).
- Task, requirements, and plan paths: [task.json](task.json), [REQUIREMENTS](REQUIREMENTS.md)
  (section P37), [PLAN](PLAN.md) (section P37).

## Context loaded

- Entry file and registry revision: current main `51223c9b94a222f29d38eb6c33808f8e55e2bff9`, whose
  instruction files this branch carries since gate MB. None of them changed.
- Required read-set actually opened, with revision or hash: as the declaration version lists, at
  `07d4e3c3`.
- Required files missing, truncated, or inaccessible: none.
- Current/deferred product work and applicable adopted contracts: no product work. P05's
  `ontokin.current-host-readback/0.1.0` and its plans `/0.1.1` to `/0.1.5` stay adopted and
  unchanged. GOAL's ceilings are unchanged.

## Source

- Starting revision and current code checkpoint: started at `07d4e3c3`. The declaration is
  `2f728998`, and candidate C is `5a3502e22d0fa4b29fbff2c867f1aab8271c4235` (tree `9249fdeb`). The
  records commit that carries this file follows C.
- Dirty and untracked state: the worktree was clean at C through the routine and the review. The
  records are the only change since. The main checkout's owner items stay untouched.
- Actual remote observation, with command and time: `git ls-remote --heads origin` at
  2026-11-28T01:09:35Z read this branch at `5a3502e2` and main at `51223c9b`. The records push is
  observed in the phase's `CLOSING.json`, which the next commit adds.
- Repository, actual main SHA/tree, and observation time: `Omegapy/OntoKin`, main `51223c9b` at
  01:09:35Z.
- Active branch/head, open PR, and scope issue: [PR274](https://github.com/Omegapy/OntoKin/pull/274)
  open and draft; [issue273](https://github.com/Omegapy/OntoKin/issues/273) open.
- Local checkout identity and unpublished changes: the C271 worktree; the records commit until its
  push.

## Work

- Requirements: R01 and R02 done; R03, R04 and R05 not_done. Task status `in_progress`.
- Acceptance items: A1 to A7 met. A8 is this closing, whose push, readback and comments the closing
  record captures ([outcome](../../../engineering/localized-repair-c271/derived-workspace-p37/OUTCOME.json)).
- Changed artifact paths and exact code/input identities:
  - **At C:** `tools/check_local.py` (`3136f52c`), the 0.2.0 provider (`bab89614`), two test modules
    with 21 new tests, a new control module with 46 frozen controls (`c0eebef7`), `DECISION-001.md`
    (`7a1626cb`), the interface note and `CONTROLS-FROZEN.json` (`7c5f86ca`).
  - **In the records commit:** the phase directory's portable records, `INVENTORY-ADDITIONS.json`,
    `OUTCOME.json` and `LEARNING-DECISION.md`; task.json, CURRENT.json, memory.json, REQUIREMENTS,
    PLAN and this file.
- Decisions made:
  - DECISION-001 by the independent author: within P05 section 3 and MC19, with no amendment.
  - The review's disposition: RV-01 to RV-06 applied or carried.
- Remaining items: the next phase, which the owner selects.
- Learning checkpoint result and capture preference: two lessons captured
  ([decision](../../../engineering/localized-repair-c271/derived-workspace-p37/LEARNING-DECISION.md)).

## Environment

- Profile and its readiness: as MP prepared it. The doctor reports `core` ready and
  `python-verification` as `not_checked` by design (D-21). The `.venv` holds no bytecode.
- Interpreter, operating system and architecture: CPython 3.12.13, macOS 26.6.2 (25G83), arm64.
- Manifest and lock identities: unchanged since MP.
- Relevant tool versions: HOST's Git, `git version 2.50.1 (Apple Git-155)`.
- Terminal and executed interpreter/platform: Claude Code's shell tool in the desktop app; every start
  of the framework interpreter with `-B`. The Python installation inventory was `c277bdd3` before and
  after the routine.
- Available read/write/conditional-update/merge operations: Git reads, local commits, non-forced
  pushes; GitHub API reads and comments. No download.
- Missing capabilities and their effect on this milestone: no prepared Git LFS client, so the storage
  module's LFS tests do not reach the new index refresh on this host (recorded as a limit).

## Verification

- Commands actually executed and observed outcomes:
  - FZ-02's measurement;
  - eleven focused modules once each;
  - the complete ordinary routine at C, exit 1, with the unit stage failed as expected and six stages
    passed;
  - the discovery of C;
  - the records checks.
- Failures:
  - the routine's 92 not-passing tests, recorded and not classified, with MC22's setup error;
  - the storage module's 8 known not-passing tests;
  - the 0.1.0 modules' recorded failures, D-18's among them.
- Pending and not-run checks: gate MR (R1 with a real HOST, R2, the audit and the R03 review).
- Durable logs, review findings, and evidence links: the
  [portable records](../../../engineering/localized-repair-c271/derived-workspace-p37/README-PORTABLE.md);
  the exact files under `../OntoKin-local/c271-p37/`.
- Evidence locations and hashes: the phase's `EXACT-RECORDS.json`.
- Relevant validation/CI results and source revisions: no hosted CI was used or awaited.
- Current review eligibility and any changes since review: C is reviewed and accepted, and unchanged
  since.

## Recovery

- Unpublished commits: the records commit until its push.
- Unique uncommitted files: none in the worktree. The exact records beside the clone are durable there.
  The scripts behind cited evidence were copied there from the session's scratchpad (RV-02).
- Outstanding operations and owned processes: none.
- Unknown operation: none.
- Remote readback needed before retrying that operation: not applicable.
- Current blockers with concrete evidence: none for this phase. P30-EXECUTOR-001 still blocks the Linux
  contract's H0 and H1 in local mode.
- Unpublished work that must be recovered: none.
- Actual unpublished recovery payloads and declared external dependencies: none.

## Coordination

- Active workers and reserved files: none. W1, W2 and W3 returned, and none made a Git write.
- Actual subagents, assigned scopes, and unresolved worker activity: as
  [the worker log](../../../engineering/localized-repair-c271/derived-workspace-p37/director/WORKERS.md)
  lists.
- Integration owner, expiry, and latest verified ownership record: none; main's lease is released and
  was not used.
- Lease status: not used.
- Ownership released, renewed, transferred, or still uncertain: owner `c271-p37-08beec34eb0a` releases
  the branch at this closing.

## Continuation

- One exact next action: the owner selects the next phase. The recommended one is gate MR again at C,
  with a new observation plan, HOST and freeze, carrying the outcome's items.
- The condition that makes that action safe and useful: the owner's selection, and this closing pushed
  and read back.

## Delivery

- Local checkpoint status: the records commit on this branch.
- Verified push state, or unconfirmed: recorded in the phase's `CLOSING.json` after the push.
- Actual merge/resulting-main checks, or remaining integration gate: none; R04 integrates.
- Branch retention/deletion evidence, or exact pending cleanup instruction: the branch and PR274 stay
  open; PR274 stays draft.
- Durable evidence references: the phase directory and `../OntoKin-local/c271-p37/`.
- Integration state separate from saved-delivery state: not integrated; the records are pushed.
- Published checkpoint revision and readback result: in the phase's `CLOSING.json`.

No receipt of the receipt: Git reveals the commit that carries this record.
