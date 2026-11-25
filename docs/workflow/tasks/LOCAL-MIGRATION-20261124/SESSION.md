# Session checkpoint: LOCAL-MIGRATION-20261124

Follows the [template](../../templates/SESSION.md). Detailed evidence is linked, not
repeated. Machine paths are left out; places beside the clone are named relative to it. The
**continuing session** wrote this record; the **demonstrating session** is the one that the
owner started for TASK-030.

## Identity

- Checkpoint time and author identity: 2026-11-25T20:12Z, Director `local-migration-f58a0f3c1d5a`.
- Task, session, and agent or tool identity: LOCAL-MIGRATION-20261124; the continuing
  session, one Claude Code command-line session in the main checkout, model Claude Opus 5.5.
- Execution mode, and the entry document or record that declared it: `local`, declared by the
  [task record](task.json) and [LOCAL-START-HERE](../../../../LOCAL-START-HERE.md). The amended
  rules bind this branch before integration
  ([DECISION](../../../engineering/local-migration-20261124/DECISION.md#prospective-effect)).
- Worktree and branch: `OntoKin-worktrees/local-migration-20261124` beside the clone, on
  `work/local-migration-20261124`.
- Current user objective and bounded milestone: the owner's instruction of 2026-11-25 is to
  continue executing PLAN-20261125-CB551B16, the local development migration; the milestone
  is the review, integration and closing of the audited candidate.
- Task, requirements, and plan paths: [task.json](task.json), [REQUIREMENTS](REQUIREMENTS.md),
  [PLAN](PLAN.md).

## Context loaded

- Entry file and registry revision: [LOCAL-START-HERE](../../../../LOCAL-START-HERE.md) and
  [registry](../../registry.json), schema 2, at the code checkpoint below.
- Required read-set actually opened, with revision or hash: the local read-set, HANDOFF, the
  three OntoKin skills, OK-ENG-006 and OK-ENG-009 on this branch; the task's requirements, plan and
  checkpoint; the approved TRD in full, SHA-256
  `12e905a76da826f52e61c1237977a836750ce89260e208ba8553ebc8aeb28d76`.
- Required files missing, truncated, or inaccessible: none.
- Current/deferred product work and applicable adopted contracts: no product work is
  selected. OK-ENG-006, OK-ENG-009, OK-ENG-010 and the GOAL invariants apply to the scope;
  the next action needs no further specification.

## Source

- Starting revision and current code checkpoint: `6b346b1e4126332fe3c98a4a98f3e0b0e2f63774` to
  `7a0d46f4fdb4e155a28d03640625bfed5cbd5b63`, tree `1b29a86acd4a812f4a0e0be3071d7cb0e33194e7`.
- Dirty and untracked state: the worktree was clean at that commit. The main checkout has no
  tracked change; its untracked `TRDs/` (equal to the committed copy) and
  `Implementation_Plans/` stay there on purpose.
- Actual remote observation, with command and time, or offline and stale:
  `git ls-remote --heads origin` at 2026-11-25T20:03Z: main `6b346b1e…`,
  `work/c271-missing-import-digest-control` `bef67902…`, `work/local-migration-20261124`
  `3d02d7e0…`; no other head.
- Repository, actual main SHA/tree, and observation time: Omegapy/OntoKin, main
  `6b346b1e4126332fe3c98a4a98f3e0b0e2f63774`, tree `812a17de3880f7c152beacccf7b2e690381f9716`,
  same observation.
- Active branch/head, open PR, and scope issue: this branch at the checkpoint above; no pull
  request yet; [scope277](https://github.com/Omegapy/OntoKin/issues/277) open.
- Local checkout identity and unpublished changes, if a workspace exists: clone with three
  linked worktrees: this one, and two detached ones that hold no unique work,
  `baseline-6b346b1e` and `candidate-checks` at `402a7d8e`. No unpublished commit, no stash.

## Work

- Requirements completed, incomplete, blocked, and excluded: the ledger marks none of the 42
  requirements done before the audit of TASK-031. Excluded: every C271 gate, product and
  native qualification, container profiles.
- Completed acceptance items and last completed gate: TASK-001 to TASK-031. Last completed gate:
  the [audit](../../../engineering/local-migration-20261124/REQUIREMENTS-AUDIT.md) that freezes the candidate.
  The Worktree criterion of TASK-030 is waived by the owner
  ([judgement](../../../engineering/local-migration-20261124/FRESH-SESSION-ACCEPTANCE.md)).
- Changed artifact paths and exact code/input identities: `git diff --name-status` from the
  base to the code checkpoint: 36 added, 21 modified, none deleted. No expectation, fixture,
  evidence file, workflow definition or C271 file is among them. Since
  `402a7d8ed8512535e2f87ed123c3f6a7b418dea0` only documents and records changed.
- Decisions made: [DECISION](../../../engineering/local-migration-20261124/DECISION.md), with
  the deviations recorded in [PLAN](PLAN.md#deviations-from-the-approved-plan); on the owner's
  direction of 2026-11-25 details of the machine's protection are kept off the public record.
- Remaining items: TASK-032 to TASK-036.
- Learning checkpoint result and capture preference: not performed yet; it belongs to the
  closing steps.

## Environment

- Profile and its readiness: `core` and `python-verification` ready;
  `visual-verification` mismatch (only Node.js 25.9.0 is installed, the target is 22);
  `package-smoke` not checked by the doctor, and proven at an earlier revision by its own
  [record](../../../engineering/local-migration-20261124/PACKAGE-SMOKE.json);
  `historical-native` not checked; `linux-container` unsupported.
- Interpreter, operating system and architecture: CPython 3.12.13 (Homebrew), macOS 26.6.2,
  arm64.
- Manifest and lock identities: `tools/local-environment.json` SHA-256
  `c70b9d43634f9a35170e4ac633a6e352e7a986a6fb8ab10639fa60a9c776f9b4`; macOS lock
  `b1e3e86668421539c6817faefe7f126b4dbf25153fcbb2fab6325e080cf7a81c`; Linux lock
  `a7f17491000c2e139ccc5d213ca0e8a6f917e5befb4b878fef29f5ff72ae780f` and six Agent pins
  `6d5fefcbd7ccced7d39bf8d20e87ec1c4401fc6b252aea41677d41d9124555d1`, both unchanged.
- Relevant tool versions: Git 2.50.1, Git LFS 3.7.1 (no LFS-tracked file), GitHub CLI 2.86.0.
- Terminal and executed interpreter/platform: zsh; the worktree's `.venv/bin/python`, and
  `python3.12` for the setup tool.
- Available read/write/conditional-update/merge operations: file and Git writes in the
  worktree, SSH push of this branch (observed), `gh` reads (observed); pull request and merge
  not used yet.
- Missing capabilities and their effect on this milestone: none.

## Verification

- Commands actually executed and observed outcomes: at `d4d486b3621e26e71830beddfe988ac8bc2e9461`
  in a scratch clone: documentation verifier and workflow check passed, 307 focused tests OK
  with a resolved TMPDIR; setup preview, setup, repeat and doctor run for real, the repeat
  unchanged. At `402a7d8ed8512535e2f87ed123c3f6a7b418dea0`: both driver runs, 307 focused tests, the
  documentation verifier and the workflow check. At the code checkpoint: documentation verifier
  and workflow check passed. The R06 identities were computed again and are equal.
- Failures: the driver reports failed. Its unit step ran 4,989 tests; one does not pass with a
  resolved TMPDIR and 307 with the default one, all unchanged from the
  [baseline](../../../engineering/local-migration-20261124/BASELINE-CHECKS.json)
  ([candidate record](../../../engineering/local-migration-20261124/CANDIDATE-CHECKS.json)).
- Pending and not-run checks: 16 external cases pending; three readback tests skipped;
  `--full`, `--force-agent`, hosted CI and Linux not run; independent review and resulting-main
  checks not run; Worktree observation not made (waived).
- Durable logs, review findings, and evidence links: records in
  [local-migration-20261124](../../../engineering/local-migration-20261124/); the
  [pre-reviews](../../../engineering/local-migration-20261124/PRE-REVIEWS.md) with every
  finding and disposition. They are not the review of TASK-032.
- Evidence locations and hashes: in the records above; raw logs are in `OntoKin-local/`
  beside the clone.
- Relevant validation/CI results and source revisions: as above. No hosted run was started.
- Current review eligibility and any changes since review: the commit that carries this record
  is the frozen candidate; not yet reviewed.

## Recovery

- Unpublished commits: none at the code checkpoint. The local ref that held a prepared commit
  was removed after that commit had been merged and pushed.
- Unique uncommitted files: none in this worktree. In the main checkout, the plan tracker in
  `Implementation_Plans/`, which no remote holds.
- Outstanding operations and owned processes: none.
- Unknown operation and its intended parent/tree/commit or request identity: none.
- Remote readback needed before retrying that operation: not applicable.
- Current blockers with concrete evidence: none.
- Unpublished work that must be recovered and its known location: none.
- Actual unpublished recovery payloads and declared external dependencies: none. The R06
  archive and its receipt are in the owner's ChatGPT Library, with copies beside the clone.

## Coordination

- Active workers and reserved files: none. The continuing session goes on writing here.
- Actual subagents, assigned scopes, and unresolved worker activity: none active. Desktop
  sessions of the owner that have this worktree as their folder: the two demonstrating sessions
  and two read-only checks; all ended their turn. One further desktop session has the main
  checkout as its folder and changed nothing.
- Integration owner, expiry, and latest verified ownership record: none; the lease was
  released on 2026-11-20 ([STATUS](../../../../STATUS.md#main-integration-lease)).
- Lease status: released, not acquired by this migration.
- Ownership released, renewed, transferred, or still uncertain: the Director role passed from
  `local-migration-0e9ea0a483b1`, whose process was observed to have ended on 2026-11-25, to
  `local-migration-f58a0f3c1d5a` on the owner's instruction. A session with Worktree mode on only
  reports; it takes no Director role and no lease.

## Continuation

- One exact next action, inputs, acceptance gate, and stopping condition: **TASK-032**: a separate
  reviewer examines the frozen candidate, the commit that carries this record. Mandatory findings
  are resolved with renewed review. Then TASK-033 to TASK-036 as [PLAN](PLAN.md) states them. The
  continuing session carries this out; **any other session reports the state and stops.**
- The condition that makes that action safe and useful to execute: the branch head on the remote
  is that commit, and no later change is made to it without renewed review.

## Delivery

- Local checkpoint status: committed on this branch.
- Verified push state, or unconfirmed: the code checkpoint and the later
  commit that carries this record are shown by Git and `git ls-remote`.
- Actual merge/resulting-main checks, or remaining integration gate: not integrated. Remaining:
  independent review, lease, merge and resulting-main checks.
- Branch retention/deletion evidence, or exact pending cleanup instruction: branch active. The
  two detached worktrees are removed in TASK-034.
- Durable evidence references: the records linked above.
- Integration state separate from saved-delivery state: not integrated; local mode needs no
  saved ZIP.
- Published checkpoint revision and readback result: shown by Git for this file.
- (browser) Required session ZIP delivery still open, with intended filename and folder: not
  applicable.
- (browser) Latest confirmed saved recovery/handoff identity, version, size and SHA-256: not
  applicable.
