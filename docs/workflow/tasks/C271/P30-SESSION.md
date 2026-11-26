# Session checkpoint: C271-P30 /0.1.5 operational-plan review

Follows current main's [session template](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/docs/workflow/templates/SESSION.md).
Detailed evidence is linked, not repeated. Machine paths are left out; places beside the clone
are named relative to it. Times are UTC. This is the declaration version of the checkpoint; the
outcome version replaces it in a later commit, and Git keeps this one.

## Identity

- Checkpoint time and author identity: 2026-11-26T03:20Z, Director `c271-p30-55a168e30426`.
- Task, session, and agent or tool identity: C271, phase C271-P30-operational-plan-review; one
  Claude Code session (model Claude Opus 5.5), started from another Claude Code session of the
  owner and working in the C271 worktree.
- Execution mode, and the entry document or record that declared it: `local`, declared by
  starting from current main's [LOCAL-START-HERE](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/LOCAL-START-HERE.md).
  C271's record names local mode since R07 (`execution_mode_record` in [task.json](task.json)).
  The owner selected this phase on 2026-11-25 (America/Denver) with the reply "begin the /0.1.5",
  typed in the session that started this one and relayed here word for word
  ([phase declaration](../../../engineering/localized-repair-c271/operational-plan-review-p30/PHASE.json)).
  Before that selection, this session reported the startup items to the owner and asked whether a
  Linux x86-64 machine or VM should be considered as an existing executor; the reply named none.
- Worktree and branch: `../OntoKin-worktrees/c271` beside the clone, on
  `work/c271-missing-import-digest-control`, tracking origin.
- Current user objective and bounded milestone: the review of the `/0.1.5` operational plan
  against the published P29 candidate and current host facts, ending in an independently
  reviewed outcome or a concrete blocker.
- Task, requirements, and plan paths: [task.json](task.json), [REQUIREMENTS](REQUIREMENTS.md)
  (section P30), [PLAN](PLAN.md) (section P30). No TRD or plan-tracker document was made for this
  phase; the phase declaration holds its acceptance A1 to A8.

## Context loaded

- Entry file and registry revision: current main `51223c9b94a222f29d38eb6c33808f8e55e2bff9`.
- Required read-set actually opened, with revision or hash: [READ-SET](../../../engineering/localized-repair-c271/operational-plan-review-p30/READ-SET.json)
  lists every input with size and SHA-256: main's LOCAL-START-HERE, AGENTS, CLAUDE, GOAL, STATUS,
  ROLE, registry, CURRENT, PROTOCOL, HANDOFF, the session and worker templates, LOCAL-PROMPTS,
  `tools/local-environment.json`, OK-ENG-006, the local migration's check records and the three
  registered skills; and this branch's inputs at `4ee55b037b909b36cb8a6330aa07ccc78071af88`.
  The skill ontokin-session is loaded; ontokin-delivery and ontokin-learning are loaded for the
  closing steps.
- Required files missing, truncated, or inaccessible: none.
- Current/deferred product work and applicable adopted contracts: no product work. The adopted
  contracts reviewed are P05's `ontokin.current-host-readback/0.1.0` with the supplements
  through inspection-plan `/0.1.5`, and the unchanged C260 contract. GOAL's ceilings of 100,000
  operations and 30,000 ms are unchanged.

## Source

- Starting revision and current code checkpoint: `4ee55b037b909b36cb8a6330aa07ccc78071af88`,
  R07's closing record. The declaration commit carries this checkpoint; Git reveals it.
- Dirty and untracked state: the worktree held only this phase's declaration records before the
  commit, apart from its ignored `.venv`. The main checkout keeps the owner's modified
  `TRDs/INDEX.md`, the untracked `Implementation_Plans/` and the untracked R07 TRD file, untouched.
- Actual remote observation, with command and time, or offline and stale: `git ls-remote --heads origin`
  at about 2026-11-26T03:05Z read main `51223c9b94a222f29d38eb6c33808f8e55e2bff9` and this branch
  `4ee55b037b909b36cb8a6330aa07ccc78071af88`.
- Repository, actual main SHA/tree, and observation time: `Omegapy/OntoKin`, main
  `51223c9b94a222f29d38eb6c33808f8e55e2bff9`, tree `a92e46b353d0697483fd5154814c00946be73e8b`,
  2026-11-26T03:05Z.
- Active branch/head, open PR, and scope issue: `work/c271-missing-import-digest-control`;
  [PR274](https://github.com/Omegapy/OntoKin/pull/274) open, draft, unmerged and conflicting with
  main; [issue273](https://github.com/Omegapy/OntoKin/issues/273) open.
- Local checkout identity and unpublished changes, if a workspace exists: the C271 worktree; the
  declaration commit is pushed as this phase's first step.

## Work

- Requirements completed, incomplete, blocked, and excluded: R01 and R02 done; R03, R04 and R05
  not_done. P01 done, P02 in_progress. Excluded: the list in the phase declaration.
- Completed acceptance items and last completed gate: none of A1 to A8 yet; the last completed
  gate is R07's exact publication of the P29 candidate.
- Changed artifact paths and exact code/input identities: this phase's records under
  `docs/engineering/localized-repair-c271/operational-plan-review-p30/`, this checkpoint, the P30
  sections of REQUIREMENTS and PLAN, and the current-state fields of task.json and the branch
  CURRENT (replaced values kept in `p30_prior_current_fields`).
- Decisions made: the phase's scope, acceptance and exclusions as declared.
- Remaining items: A1 to A8.
- Learning checkpoint result and capture preference: not yet assessed.
- Dated note: the R06 archive and its receipt in the owner's downloads folder are byte-identical
  to the copies that R07 used beside the clone (`cmp` exits 0 for both; recorded sizes and
  SHA-256). R07's records call them not observed, which held for the R07 session; they stay
  unchanged. R07's working evidence is in `../OntoKin-local/c271-p29-r07/` beside the clone
  ([record](../../../engineering/localized-repair-c271/operational-plan-review-p30/R06-DOWNLOADS-COPIES.json)).

## Environment

- Profile and its readiness: in the main checkout, `core` and `python-verification` ready,
  `visual-verification` mismatched (Node.js 25.9.0; the target is 22; npm packages not installed),
  `linux-container` unsupported, `historical-native` not checked. The C271 worktree has no
  environment specification, so the doctor cannot diagnose it.
- Interpreter, operating system and architecture: CPython 3.12.13 (Homebrew), macOS 26.6.2, arm64.
- Manifest and lock identities: current main's `tools/local-environment.json`, SHA-256
  `c70b9d43634f9a35170e4ac633a6e352e7a986a6fb8ab10639fa60a9c776f9b4`. The worktree's `.venv` holds
  no package.
- Relevant tool versions: Git 2.50.1; the GitHub CLI is authenticated.
- Terminal and executed interpreter/platform: zsh. The worktree's `.venv/bin/python` runs this
  branch's checks; the main checkout's `.venv/bin/python` ran the doctor and main's workflow check.
- Available read/write/conditional-update/merge operations: Git reads, local commits and
  non-forced pushes over the owner's remote; GitHub API reads and comments. No merge into main.
- Missing capabilities and their effect on this milestone: none known at declaration.

## Verification

- Commands actually executed and observed outcomes: main's doctor (exit 0) and workflow check
  (passed, 12 tasks); this branch's workflow check (passed, 12 tasks) and documentation verifier
  (passed) at `4ee55b03` ([baseline](../../../engineering/localized-repair-c271/operational-plan-review-p30/CHECKS-BASELINE.json)).
- Failures: none.
- Pending and not-run checks: the checks of this phase's records after the outcome. Excluded: the
  routine driver, the unit suite and every behavioural test, H0 and H1.
- Durable logs, review findings, and evidence links: working evidence in `../OntoKin-local/c271-p30/`
  beside the clone; the phase records.
- Evidence locations and hashes: in the phase records.
- Relevant validation/CI results and source revisions: workflows are manual-only; none runs.
- Current review eligibility and any changes since review: no review yet.

## Recovery

- Unpublished commits: none before the declaration commit; it is pushed next.
- Unique uncommitted files: none after the declaration commit. The main checkout's items stay in place.
- Outstanding operations and owned processes: none.
- Unknown operation and its intended parent/tree/commit or request identity: none in this phase.
- Remote readback needed before retrying that operation: not applicable.
- Current blockers with concrete evidence: none at declaration.
- Unpublished work that must be recovered and its known location: none.
- Actual unpublished recovery payloads and declared external dependencies: none.

## Coordination

- Active workers and reserved files: none at declaration.
- Actual subagents, assigned scopes, and unresolved worker activity: none yet; the independent
  reviewer is a fresh-context worker later in the phase.
- Integration owner, expiry, and latest verified ownership record: none. Main's lease is released
  and is not used by this phase.
- Lease status: released (main STATUS).
- Ownership released, renewed, transferred, or still uncertain: owner `c271-p30-55a168e30426`
  holds this branch for the phase and releases it with the phase's closing record.

## Continuation

- One exact next action, inputs, acceptance gate, and stopping condition: carry out acceptance
  A2 to A8 of the [phase declaration](../../../engineering/localized-repair-c271/operational-plan-review-p30/PHASE.json)
  on the inputs of its read set, and stop at the independently reviewed outcome or the first
  concrete blocker.
- The condition that makes that action safe and useful to execute: the branch head read from the
  remote equals, or descends from, the declaration commit; no other writer on this branch.

## Delivery

- Local checkpoint status: the declaration commit on this branch.
- Verified push state, or unconfirmed: read from the remote after the push.
- Actual merge/resulting-main checks, or remaining integration gate: R04, a later phase. Main is
  unchanged.
- Branch retention/deletion evidence, or exact pending cleanup instruction: the branch is
  retained for unfinished C271.
- Durable evidence references: the phase records named above.
- Integration state separate from saved-delivery state: not integrated. In local mode no Library
  save is required (R07's delivery reconciliation).
- Published checkpoint revision and readback result: pending the push.

No receipt of the receipt: Git reveals the commit that carries this record.
