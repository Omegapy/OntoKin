# Session checkpoint: LOCAL-MIGRATION-20261124

Follows the [template](../../templates/SESSION.md). Detailed evidence is linked, not
repeated. Machine paths are left out; places beside the clone are named relative to it.

## Identity

- Checkpoint time and author identity: 2026-11-25T09:22Z, Director `local-migration-0e9ea0a483b1`.
- Task, session, and agent or tool identity: LOCAL-MIGRATION-20261124; one Claude Code
  command-line session, model Claude Opus 5.5.
- Execution mode, and the entry document or record that declared it: `local`, declared by the
  [task record](task.json) and [LOCAL-START-HERE](../../../../LOCAL-START-HERE.md).
- Worktree and branch: `OntoKin-worktrees/local-migration-20261124` beside the clone, on
  `work/local-migration-20261124`.
- Current user objective and bounded milestone: carry out PLAN-20261125-CB551B16, the local
  development migration; this session's milestone was its implementation and checks up to
  the demonstration.
- Task, requirements, and plan paths: [task.json](task.json), [REQUIREMENTS](REQUIREMENTS.md),
  [PLAN](PLAN.md).

## Context loaded

- Entry file and registry revision: [LOCAL-START-HERE](../../../../LOCAL-START-HERE.md) and
  [registry](../../registry.json), schema 2, at the code checkpoint below.
- Required read-set actually opened, with revision or hash: AGENTS, GOAL, STATUS, ROLE,
  registry, CURRENT, PROTOCOL, HANDOFF and the six skills, first at base
  `6b346b1e4126332fe3c98a4a98f3e0b0e2f63774` and again as changed on this branch; the approved
  TRD, SHA-256 `12e905a76da826f52e61c1237977a836750ce89260e208ba8553ebc8aeb28d76`.
- Required files missing, truncated, or inaccessible: none of the read-set. The R06 handoff
  and its receipt are not on the machine.
- Current/deferred product work and applicable adopted contracts: no product work is
  selected. OK-ENG-006, OK-ENG-009, OK-ENG-010 and the GOAL invariants apply.

## Source

- Starting revision and current code checkpoint: `6b346b1e4126332fe3c98a4a98f3e0b0e2f63774` to
  `bb40268338b9a5e695e9836ebed5f84e7eb3a73e`, tree `f53be8e6813f1cedf72d559921a1d1929c07edf1`.
- Dirty and untracked state: the worktree was clean at that commit. The main checkout has no
  tracked change; its untracked `TRDs/` (equal to the committed copy) and
  `Implementation_Plans/` stay there on purpose.
- Actual remote observation, with command and time, or offline and stale:
  `git ls-remote --heads origin` at 2026-11-25T09:22Z: main `6b346b1e…`,
  `work/c271-missing-import-digest-control` `bef67902…`, `work/local-migration-20261124`
  `bb402683…`; no other head.
- Repository, actual main SHA/tree, and observation time: Omegapy/OntoKin, main
  `6b346b1e4126332fe3c98a4a98f3e0b0e2f63774`, tree `812a17de3880f7c152beacccf7b2e690381f9716`,
  same observation.
- Active branch/head, open PR, and scope issue: this branch at the checkpoint above; no pull
  request yet; [scope277](https://github.com/Omegapy/OntoKin/issues/277) open.
- Local checkout identity and unpublished changes, if a workspace exists: clone with three
  linked worktrees: this one, and two detached ones that hold no unique work,
  `baseline-6b346b1e` and `candidate-checks` at `ebcfee8c`. No unpublished commit, no stash.

## Work

- Requirements completed, incomplete, blocked, and excluded: the ledger marks none of the 42
  requirements done before the audit of TASK-031. Excluded: every C271 gate, product and
  native qualification, container profiles.
- Completed acceptance items and last completed gate: TASK-001 to TASK-005 and TASK-009 to
  TASK-028. Last completed gate: TASK-027, the candidate checks against the baseline, with
  the second-worktree test of TASK-028.
- Changed artifact paths and exact code/input identities: `git diff --name-status` from the
  base to the code checkpoint: 29 added, 21 modified, none deleted. No expectation, fixture,
  evidence file, workflow definition or C271 file is among them.
- Decisions made: [DECISION](../../../engineering/local-migration-20261124/DECISION.md), with
  the recorded deviations.
- Remaining items: TASK-029 closes with this record; TASK-006 to TASK-008; TASK-030;
  TASK-031 to TASK-036.
- Learning checkpoint result and capture preference: not performed yet; it belongs to the
  closing steps.

## Environment

- Profile and its readiness: `core` and `python-verification` ready;
  `visual-verification` mismatch (only Node.js 25.9.0 is installed, the target is 22);
  `package-smoke` proven by its own [record](../../../engineering/local-migration-20261124/PACKAGE-SMOKE.json);
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
  worktree, SSH push of this branch (observed), `gh` reads and issue writes (observed);
  pull request and merge not used yet.
- Missing capabilities and their effect on this milestone: no access to the ChatGPT Library,
  so TASK-006 waits; no graphical session, so TASK-030 waits for the owner.

## Verification

- Commands actually executed and observed outcomes: documentation verifier passed, workflow
  check passed with 12 tasks, 259 focused tests OK, two routine driver runs, second-worktree
  test: [candidate checks](../../../engineering/local-migration-20261124/CANDIDATE-CHECKS.json),
  [second worktree](../../../engineering/local-migration-20261124/SECOND-WORKTREE.json).
- Failures: the driver reports failed. Its unit step ran 4,941 tests; one does not pass with
  a resolved TMPDIR and 307 with the default one, all unchanged from the
  [baseline](../../../engineering/local-migration-20261124/BASELINE-CHECKS.json).
- Pending and not-run checks: 16 external cases pending; three readback tests skipped;
  `--full`, `--force-agent`, hosted CI and Linux not run; fresh-session demonstration,
  independent review and resulting-main checks not run.
- Durable logs, review findings, and evidence links: records in
  [local-migration-20261124](../../../engineering/local-migration-20261124/); two independent
  pre-reviews (documents and tools) ended, and their findings are closed on this branch.
  They are not the review of TASK-032.
- Evidence locations and hashes: digests of the raw logs are in the two records above; the
  logs are in `OntoKin-local/` beside the clone.
- Relevant validation/CI results and source revisions: candidate
  `ebcfee8ccb6402e7c1b99ef63ce406966ba9909a`; no hosted run was started.
- Current review eligibility and any changes since review: not eligible until TASK-031
  freezes a candidate.

## Recovery

- Unpublished commits: none at the code checkpoint.
- Unique uncommitted files: none in this worktree. In the main checkout, the plan tracker in
  `Implementation_Plans/`, which no remote holds.
- Outstanding operations and owned processes: none; both driver runs ended.
- Unknown operation and its intended parent/tree/commit or request identity: none.
- Remote readback needed before retrying that operation: not applicable.
- Current blockers with concrete evidence: TASK-006: the R06 archive (41,730,084 bytes) and
  its receipt (149,563 bytes) were not found on the machine at 2026-11-25T08:58Z; identities
  in the [task record](task.json). TASK-030: needs the owner.
- Unpublished work that must be recovered and its known location: none.
- Actual unpublished recovery payloads and declared external dependencies: none; R06 stays
  in the owner's ChatGPT Library.

## Coordination

- Active workers and reserved files: none. This session reserves no file after publishing
  this checkpoint, until the demonstration of TASK-030 has ended or the owner says otherwise.
- Actual subagents, assigned scopes, and unresolved worker activity: the two pre-reviewers
  above, read-only; both ended.
- Integration owner, expiry, and latest verified ownership record: none; the lease was
  released on 2026-11-20 ([STATUS](../../../../STATUS.md#main-integration-lease)).
- Lease status: released, not acquired by this migration.
- Ownership released, renewed, transferred, or still uncertain: the branch stays with the
  Director token above; FRESH-SESSION.md is handed to the demonstrating session.

## Continuation

- One exact next action, inputs, acceptance gate, and stopping condition: **TASK-030, in the
  session that the owner starts in the Claude Desktop Code tab with the instruction
  `Continue`.** Report the startup items. Then write
  `docs/engineering/local-migration-20261124/FRESH-SESSION.md` from this session's own
  observation: application version and bundled Claude Code version as read from the
  application itself; folder, branch, head and Worktree setting; which instruction files were
  present without being opened and which were opened; the project skills it sees; its account
  of the selected task, environment, completed work, last completed gate, next action and
  blockers, compared with [CURRENT](../../CURRENT.json), the [task record](task.json) and this
  checkpoint; and whether any earlier conversation, ZIP or Library download was used. Commit
  only that file on this branch and stop. Gate: the acceptance of TASK-030 in
  [PLAN](PLAN.md). TASK-006 to TASK-008 are not part of it, even if the R06 files have
  arrived.
- The condition that makes that action safe and useful to execute: the worktree is clean at
  the head that carries this checkpoint, the remote shows the same head, and no other session
  is writing in this worktree.

## Delivery

- Local checkpoint status: committed on this branch.
- Verified push state, or unconfirmed: code checkpoint `bb402683…` confirmed on the remote by
  `git ls-remote`; the later commit that carries this record is shown by Git.
- Actual merge/resulting-main checks, or remaining integration gate: not integrated. Remaining:
  TASK-006 to TASK-008, TASK-030, audit, independent review, lease and merge.
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
