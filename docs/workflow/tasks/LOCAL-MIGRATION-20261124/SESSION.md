# Session checkpoint: LOCAL-MIGRATION-20261124

Follows the [template](../../templates/SESSION.md). Detailed evidence is linked, not
repeated. Machine paths are left out; places beside the clone are named relative to it. The
**implementing session** wrote this record; the **demonstrating session** is the one that the
owner starts for TASK-030.

## Identity

- Checkpoint time and author identity: 2026-11-25T15:27Z, Director `local-migration-0e9ea0a483b1`.
- Task, session, and agent or tool identity: LOCAL-MIGRATION-20261124; the implementing
  session, one Claude Code command-line session, model Claude Opus 5.5.
- Execution mode, and the entry document or record that declared it: `local`, declared by the
  [task record](task.json) and [LOCAL-START-HERE](../../../../LOCAL-START-HERE.md). The amended
  rules bind this branch before integration
  ([DECISION](../../../engineering/local-migration-20261124/DECISION.md#prospective-effect)).
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
  selected. OK-ENG-006, OK-ENG-009, OK-ENG-010 and the GOAL invariants apply to the scope;
  the next action needs no further specification.

## Source

- Starting revision and current code checkpoint: `6b346b1e4126332fe3c98a4a98f3e0b0e2f63774` to
  `03d61c2dfd386698e0b6dead00c35b1fea70422a`, tree `998fefdbac11ac1ef3a6896e8575da5d6f7570db`.
- Dirty and untracked state: the worktree was clean at that commit. The main checkout has no
  tracked change; its untracked `TRDs/` (equal to the committed copy) and
  `Implementation_Plans/` stay there on purpose.
- Actual remote observation, with command and time, or offline and stale:
  `git ls-remote --heads origin` at 2026-11-25T15:24Z: main `6b346b1e…`,
  `work/c271-missing-import-digest-control` `bef67902…`, `work/local-migration-20261124`
  `03d61c2d…`; no other head.
- Repository, actual main SHA/tree, and observation time: Omegapy/OntoKin, main
  `6b346b1e4126332fe3c98a4a98f3e0b0e2f63774`, tree `812a17de3880f7c152beacccf7b2e690381f9716`,
  same observation.
- Active branch/head, open PR, and scope issue: this branch at the checkpoint above; no pull
  request yet; [scope277](https://github.com/Omegapy/OntoKin/issues/277) open.
- Local checkout identity and unpublished changes, if a workspace exists: clone with three
  linked worktrees: this one, and two detached ones that hold no unique work,
  `baseline-6b346b1e` and `candidate-checks` at `03d61c2d`. No unpublished commit, no stash.

## Work

- Requirements completed, incomplete, blocked, and excluded: the ledger marks none of the 42
  requirements done before the audit of TASK-031. Excluded: every C271 gate, product and
  native qualification, container profiles.
- Completed acceptance items and last completed gate: TASK-001 to TASK-005 and TASK-009 to
  TASK-029. Last completed gate: TASK-027, the candidate checks against the baseline, with
  the second-worktree test of TASK-028; TASK-029 is this record.
- Changed artifact paths and exact code/input identities: `git diff --name-status` from the
  base to the code checkpoint: 31 added, 21 modified, none deleted. No expectation, fixture,
  evidence file, workflow definition or C271 file is among them.
- Decisions made: [DECISION](../../../engineering/local-migration-20261124/DECISION.md), with
  the deviations recorded in [PLAN](PLAN.md#deviations-from-the-approved-plan); on the owner's
  direction of 2026-11-25 details of the machine's protection are kept off the public record.
- Remaining items: TASK-006 to TASK-008 (blocked, see Recovery); TASK-030; TASK-031 to
  TASK-036.
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
  check passed with 12 tasks, 307 focused tests OK with a resolved TMPDIR (with the default
  one two do not pass, unchanged from the baseline), routine driver runs, second-worktree
  test: [candidate checks](../../../engineering/local-migration-20261124/CANDIDATE-CHECKS.json),
  [second worktree](../../../engineering/local-migration-20261124/SECOND-WORKTREE.json).
- Failures: the driver reports failed. Its unit step ran 4,989 tests; one does not pass with
  a resolved TMPDIR and 307 with the default one, all unchanged from the
  [baseline](../../../engineering/local-migration-20261124/BASELINE-CHECKS.json).
- Pending and not-run checks: 16 external cases pending; three readback tests skipped;
  `--full`, `--force-agent`, hosted CI and Linux not run; fresh-session demonstration,
  independent review and resulting-main checks not run.
- Durable logs, review findings, and evidence links: records in
  [local-migration-20261124](../../../engineering/local-migration-20261124/); the
  [pre-reviews](../../../engineering/local-migration-20261124/PRE-REVIEWS.md) with every
  finding and disposition. They are not the review of TASK-032.
- Evidence locations and hashes: digests of the raw logs are in the two records above; the
  logs are in `OntoKin-local/` beside the clone.
- Relevant validation/CI results and source revisions: the candidate record binds
  `1d9e56847cce24345276053c9483e671dbadb332`. The tools were corrected after it; driver runs at
  `f81a95a592b53aabc6a9668a33ef88e059eb839f` and `2a220d2f295a2f4ec68eebdf6c8cd0d4282f475e` had the
  same comparison result, and the one commit after them changed documents only. The record is
  made again for the frozen candidate. No hosted run was started.
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
  its receipt (149,563 bytes) were not found on the machine at 2026-11-25T15:24Z; identities
  in the [task record](task.json). TASK-030: needs the owner.
- Unpublished work that must be recovered and its known location: none.
- Actual unpublished recovery payloads and declared external dependencies: none; R06 stays
  in the owner's ChatGPT Library.

## Coordination

- Active workers and reserved files: none. The implementing session writes nothing in this
  worktree after publishing this checkpoint, until FRESH-SESSION.md is on the branch or the
  owner says otherwise. The demonstrating session need not ask again.
- Actual subagents, assigned scopes, and unresolved worker activity: the reviewers, the
  auditor and the rehearsal named in the pre-review record, read-only; all ended.
- Integration owner, expiry, and latest verified ownership record: none; the lease was
  released on 2026-11-20 ([STATUS](../../../../STATUS.md#main-integration-lease)).
- Lease status: released, not acquired by this migration.
- Ownership released, renewed, transferred, or still uncertain: the branch, the ledger and
  CURRENT stay with the Director token above. The demonstrating session acts as a worker for
  one file, FRESH-SESSION.md; it takes no Director role and no lease.

## Continuation

- One exact next action, inputs, acceptance gate, and stopping condition: **TASK-030, for the
  demonstrating session.** That is the session which the owner starts in the Claude Desktop
  Code tab with this worktree as its folder, Worktree mode off, and the instruction
  `Continue`. It recognises itself by its own process: the running Claude Code lies in the
  desktop application's support directory, under `claude-code/VERSION/`
  (`ps -o command= -p $PPID` from its shell). **Any other session that reads this, and any
  session that finds FRESH-SESSION.md already present, reports the state and stops.**
  1. Report the startup items.
  2. Write `docs/engineering/local-migration-20261124/FRESH-SESSION.md` from this session's own
     observation, without machine paths: the application version
     (`CFBundleShortVersionString` of the installed application) and the bundled Claude Code
     version (from that process path, not from a terminal's `claude --version`); the checkout
     relative to the clone, branch, head and Worktree setting; the instruction files that were
     present without being opened, and those that were opened; the project skills it sees; its
     account of the selected task, the environment, the completed work, the last completed
     gate, the next action and the blockers, compared with [CURRENT](../../CURRENT.json), the
     [task record](task.json) and this checkpoint; and whether any earlier conversation, ZIP
     or Library download was used. Name every difference.
  3. Run `.venv/bin/python -B docs/maintenance/reorganization-2026-10-17/verify_reorganization.py`
     and `.venv/bin/python -B tools/chat_workflow.py check`.
  4. Commit only that file, push this branch, confirm the push with `git ls-remote`, and
     stop. The implementing session then updates the ledger, CURRENT and this checkpoint.

  Gate: the acceptance of TASK-030 in [PLAN](PLAN.md), except its Worktree criterion. For that
  one the owner starts a second, read-only session with Worktree mode on and the prompt
  "Check where a session works" of [LOCAL-PROMPTS](../../LOCAL-PROMPTS.md); the implementing
  session records it. TASK-006 to TASK-008 are no part of this action, even if the R06 files
  have arrived.
- The condition that makes that action safe and useful to execute: the worktree is clean at
  the head that carries this checkpoint, and the remote shows the same head.

## Delivery

- Local checkpoint status: committed on this branch.
- Verified push state, or unconfirmed: code checkpoint `03d61c2d…` confirmed on the remote by
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
