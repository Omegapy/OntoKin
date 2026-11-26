# Session checkpoint: C271-P31 macOS arm64 contract design (route C)

Follows current main's [session template](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/docs/workflow/templates/SESSION.md).
Detailed evidence is linked, not repeated. Machine paths are left out; places beside the clone
are named relative to it. Times are UTC. This is the declaration version of the checkpoint; the
outcome version replaces it in a later commit, and Git keeps this one.

## Identity

- Checkpoint time and author identity: 2026-11-26T04:24Z, Director `c271-p31-a99073a9641d`.
- Task, session, and agent or tool identity: C271, phase C271-P31-macos-contract-design; the same
  Claude Code session (model Claude Opus 5.5) that carried out C271-P30, working in the C271
  worktree.
- Execution mode, and the entry document or record that declared it: `local`, declared by starting
  from current main's [LOCAL-START-HERE](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/LOCAL-START-HERE.md);
  C271's record names local mode since R07.
- Owner direction: on 2026-11-25 (America/Denver), asked "Which route should C271 take next?",
  the owner answered "Design macOS contract (C)". The reply was typed in the session that started
  this one and relayed here word for word
  ([phase declaration](../../../engineering/localized-repair-c271/macos-contract-design-p31/PHASE.json)).
- Worktree and branch: `../OntoKin-worktrees/c271` beside the clone, on
  `work/c271-missing-import-digest-control`, tracking origin.
- Current user objective and bounded milestone: route C's design-only phase, a new versioned
  current-host readback contract for the owner's macOS arm64 executor, ending in an independently
  reviewed and adopted design or a concrete design blocker.
- Task, requirements, and plan paths: [task.json](task.json), [REQUIREMENTS](REQUIREMENTS.md)
  (section P31), [PLAN](PLAN.md) (section P31). The phase declaration holds acceptance A1 to A9.

## Context loaded

- Entry file and registry revision: current main `51223c9b94a222f29d38eb6c33808f8e55e2bff9`, read
  at the start of this session (C271-P30's read set).
- Required read-set actually opened, with revision or hash: C271-P30's
  [READ-SET](../../../engineering/localized-repair-c271/operational-plan-review-p30/READ-SET.json)
  and [additions](../../../engineering/localized-repair-c271/operational-plan-review-p30/READ-SET-ADDITIONS.json);
  this phase's own read set follows in its design records.
- Required files missing, truncated, or inaccessible: none at declaration.
- Current/deferred product work and applicable adopted contracts: no product work. P05's contract
  `ontokin.current-host-readback/0.1.0` and its supplements through `/0.1.5` stay adopted and
  unchanged; the new contract would be a separate version. GOAL's ceilings of 100,000 operations
  and 30,000 ms are unchanged.

## Source

- Starting revision and current code checkpoint: `7c3a8de1be4de988219a3fc056a7eacedcd15cc1`, C271-P30's
  closing record. The declaration commit carries this checkpoint; Git reveals it.
- Dirty and untracked state: the worktree held only this declaration before its commit, apart from
  its ignored `.venv`. The main checkout's owner items stay untouched.
- Actual remote observation, with command and time, or offline and stale: `git ls-remote --heads origin`
  at 2026-11-26T04:21:24Z read this branch at `7c3a8de1` and main at `51223c9b`.
- Repository, actual main SHA/tree, and observation time: `Omegapy/OntoKin`, main
  `51223c9b94a222f29d38eb6c33808f8e55e2bff9`, tree `a92e46b353d0697483fd5154814c00946be73e8b`.
- Active branch/head, open PR, and scope issue: [PR274](https://github.com/Omegapy/OntoKin/pull/274)
  open, draft, unmerged and conflicting with main; [issue273](https://github.com/Omegapy/OntoKin/issues/273) open.
- Local checkout identity and unpublished changes, if a workspace exists: the C271 worktree; the
  declaration commit is pushed as this phase's first step.

## Work

- Requirements completed, incomplete, blocked, and excluded: R01 and R02 done; R03, R04 and R05
  not_done. P01 done, P02 in_progress. Excluded: the list in the phase declaration.
- Completed acceptance items and last completed gate: none of A1 to A9 yet; the last completed gate
  is C271-P30's reviewed outcome.
- Changed artifact paths and exact code/input identities: this phase's declaration, this
  checkpoint, the P31 sections of REQUIREMENTS and PLAN, and the current-state fields of task.json
  and the branch CURRENT (replaced values kept in `p31_prior_current_fields`).
- Decisions made: the phase's scope, acceptance and exclusions as declared.
- Remaining items: A1 to A9.
- Learning checkpoint result and capture preference: not yet assessed.

## Environment

- Profile and its readiness: as C271-P30's checkpoint records them; nothing is prepared in this
  phase.
- Interpreter, operating system and architecture: CPython 3.12.13 (Homebrew), macOS 26.6.2, arm64.
- Terminal and executed interpreter/platform: zsh; the worktree's `.venv/bin/python` runs this
  branch's record checks.
- Available read/write/conditional-update/merge operations: Git reads, local commits and
  non-forced pushes; GitHub API reads and comments; HTTPS reads of public pages. No merge into main.
- Missing capabilities and their effect on this milestone: none known at declaration.

## Verification

- Commands actually executed and observed outcomes: this branch's workflow check, documentation
  verifier and scoped whitespace check of the declaration, before its commit.
- Failures: none.
- Pending and not-run checks: the design's independent review and the records' checks. Excluded:
  any Node, test or driver execution.
- Durable logs, review findings, and evidence links: working evidence in `../OntoKin-local/c271-p31/`
  beside the clone.

## Recovery

- Unpublished commits: none after the declaration push.
- Unique uncommitted files: none after the declaration commit.
- Outstanding operations and owned processes: none.
- Unknown operation: none.
- Current blockers with concrete evidence: none for this design phase. P30-EXECUTOR-001 still
  blocks the Linux contract's H0 and H1 in local mode.

## Coordination

- Active workers and reserved files: none at declaration.
- Integration owner and lease status: none; main's lease is released and not used.
- Ownership: owner `c271-p31-a99073a9641d` holds this branch for the phase and releases it with
  the phase's closing record.

## Continuation

- One exact next action, inputs, acceptance gate, and stopping condition: carry out A1 to A9 of
  the [phase declaration](../../../engineering/localized-repair-c271/macos-contract-design-p31/PHASE.json)
  and stop at the adopted design or a concrete design blocker.
- The condition that makes that action safe and useful to execute: the branch head read from the
  remote equals, or descends from, the declaration commit; no other writer on this branch.

## Delivery

- Local checkpoint status: the declaration commit on this branch.
- Verified push state, or unconfirmed: read from the remote after the push.
- Actual merge/resulting-main checks, or remaining integration gate: R04, a later phase.
- Branch retention: retained for unfinished C271.
- Integration state separate from saved-delivery state: not integrated; no Library save is
  required in local mode.

No receipt of the receipt: Git reveals the commit that carries this record.
