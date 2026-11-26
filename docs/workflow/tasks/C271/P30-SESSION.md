# Session checkpoint: C271-P30 /0.1.5 operational-plan review

Follows current main's [session template](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/docs/workflow/templates/SESSION.md).
Detailed evidence is linked, not repeated. Machine paths are left out; places beside the clone
are named relative to it. Times are UTC. This is the outcome version of the checkpoint. The
declaration version is retrievable from commit `7a4ab16248ed071a211ded3e24e1558ec064f0b1`. Commit
`96847fae5c3f0a6d9e9d6da3095b056a8b929b62` added two lines to it after the declaration, recording the
startup question about a Linux machine; they are kept below.

## Identity

- Checkpoint time and author identity: 2026-11-26T04:20Z, Director `c271-p30-55a168e30426`.
- Task, session, and agent or tool identity: C271, phase C271-P30-operational-plan-review; one
  Claude Code session (model Claude Opus 5.5), started from another Claude Code session of the
  owner and working in the C271 worktree.
- Execution mode, and the entry document or record that declared it: `local`, declared by
  starting from current main's [LOCAL-START-HERE](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/LOCAL-START-HERE.md).
  C271's record names local mode since R07 (`execution_mode_record` in [task.json](task.json)).
- Owner direction: on 2026-11-25 (America/Denver), the owner selected this phase with the reply
  "begin the /0.1.5", typed in the session that started this one and relayed here word for word
  ([phase declaration](../../../engineering/localized-repair-c271/operational-plan-review-p30/PHASE.json)).
  - Before that selection, this session reported the startup items to the owner and asked whether
    a Linux x86-64 machine or VM should be considered as an existing executor; the reply named none.
  - During the phase, the owner asked through the same session for the outcome to be pushed, and
    for a statement of the next step.
- Worktree and branch: `../OntoKin-worktrees/c271` beside the clone, on
  `work/c271-missing-import-digest-control`, tracking origin.
- Current user objective and bounded milestone: the review of the `/0.1.5` operational plan
  against the published P29 candidate and current host facts. Its outcome is reached: concrete
  blocker P30-EXECUTOR-001, independently reviewed. The phase stops here.
- Task, requirements, and plan paths: [task.json](task.json), [REQUIREMENTS](REQUIREMENTS.md)
  (section P30), [PLAN](PLAN.md) (section P30). No TRD or plan-tracker document was made for this
  phase; the phase declaration holds its acceptance A1 to A8.

## Context loaded

- Entry file and registry revision: current main `51223c9b94a222f29d38eb6c33808f8e55e2bff9`.
- Required read-set actually opened, with revision or hash: [READ-SET](../../../engineering/localized-repair-c271/operational-plan-review-p30/READ-SET.json)
  and [READ-SET-ADDITIONS](../../../engineering/localized-repair-c271/operational-plan-review-p30/READ-SET-ADDITIONS.json)
  list every input with size and SHA-256, the three H0-plan directory trees and the extent each
  was read. The independent reviewer recomputed all 61 READ-SET entries and found all of them
  matching.
- Skills: ontokin-session, ontokin-delivery and ontokin-learning are loaded.
- Required files missing, truncated, or inaccessible: none.
- Current/deferred product work and applicable adopted contracts: no product work. The reviewed
  contracts are P05's `ontokin.current-host-readback/0.1.0` with the supplements through
  inspection-plan `/0.1.5`, and the unchanged C260 contract. GOAL's ceilings of 100,000 operations
  and 30,000 ms are unchanged.

## Source

- Starting revision and current code checkpoint: started at
  `4ee55b037b909b36cb8a6330aa07ccc78071af88`, R07's closing record. Commits of this phase:
  - the declaration `7a4ab16248ed071a211ded3e24e1558ec064f0b1`;
  - the outcome candidate `8aa4a80012a14a521a441b306635c4fad68ca573`, rejected by the first review;
  - the review record `b17963d4d4bc57183a494341176b7edacc9987d5`;
  - the corrected candidate `96847fae5c3f0a6d9e9d6da3095b056a8b929b62`, which the re-review accepted
    with nonmandatory findings;
  - this records commit, whose identity Git reveals.
- Dirty and untracked state: the worktree is clean apart from its ignored `.venv`. The main
  checkout keeps the owner's modified `TRDs/INDEX.md`, the untracked `Implementation_Plans/` and the
  untracked R07 TRD file, untouched.
- Actual remote observation, with command and time, or offline and stale: `git ls-remote --heads origin`
  read this branch at `96847fae5c3f0a6d9e9d6da3095b056a8b929b62` at 2026-11-26T04:04:05Z, and main at
  `51223c9b94a222f29d38eb6c33808f8e55e2bff9`. The push of this records commit is observed in the
  phase's closing record.
- Repository, actual main SHA/tree, and observation time: `Omegapy/OntoKin`, main
  `51223c9b94a222f29d38eb6c33808f8e55e2bff9`, tree `a92e46b353d0697483fd5154814c00946be73e8b`,
  unchanged throughout the phase.
- Active branch/head, open PR, and scope issue: `work/c271-missing-import-digest-control`;
  [PR274](https://github.com/Omegapy/OntoKin/pull/274) open, draft, unmerged and conflicting with
  main; [issue273](https://github.com/Omegapy/OntoKin/issues/273) open.
- Local checkout identity and unpublished changes, if a workspace exists: the C271 worktree; no
  unpublished commit after the push of this records commit.

## Work

- Requirements completed, incomplete, blocked, and excluded: R01 and R02 done; R03, R04 and R05
  not_done. P01 done, P02 in_progress. The task stays `in_progress`: P30-EXECUTOR-001 blocks the
  Linux contract's H0 and H1 in local mode, and the owner has selected route C. Excluded: the list
  in the phase declaration.
- Completed acceptance items and last completed gate: A1 to A8 of the declaration. The last
  completed gate is this review's outcome:
  [REVIEW-OUTCOME](../../../engineering/localized-repair-c271/operational-plan-review-p30/REVIEW-OUTCOME.md),
  [OUTCOME](../../../engineering/localized-repair-c271/operational-plan-review-p30/OUTCOME.json).
  - No existing executor available to a local session meets the adopted contract.
  - No further preparation is selected.
  - Routes A to E were left for the owner. The review recommended, if C271 is to reach R03 and R04
    in local mode, a design-only decision between route C and route E, otherwise route D. The
    owner chose route C (see Continuation).
- Changed artifact paths and exact code/input identities: this phase's records under
  `docs/engineering/localized-repair-c271/operational-plan-review-p30/`, this checkpoint, the P30
  sections of REQUIREMENTS and PLAN, and the current-state fields of task.json and the branch
  CURRENT (replaced values kept in `p30_prior_current_fields`). No product, test, pin, contract or
  expectation changed.
- Decisions made: the scope, acceptance and exclusions as declared; the outcome; the redaction of
  installed application names from the public copies of the review.
- Remaining items: none in this phase after the closing record.
- Learning checkpoint result and capture preference: one supported lesson, recorded in
  [LEARNING-DECISION](../../../engineering/localized-repair-c271/operational-plan-review-p30/LEARNING-DECISION.md)
  and not captured, because `docs/workflow/memory.json` is one of the six files in conflict with
  main; left for capture at or after R04.
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
- Terminal and executed interpreter/platform: zsh. The worktree's `.venv/bin/python` ran this
  branch's checks; the main checkout's `.venv/bin/python` ran the doctor and main's workflow check
  before the declaration.
- Available read/write/conditional-update/merge operations: Git reads, local commits and
  non-forced pushes over the owner's remote; GitHub API reads and comments. No merge into main.
- Missing capabilities and their effect on this milestone: none for the review. The executor that
  later gates need is what P30-EXECUTOR-001 records as missing.
- Test and environment facts that stay visible and unchanged: those that R07's checkpoint lists
  (the routine run on resulting main recorded as failed, 16 pending external cases, the visual
  profile not prepared, `--full`, `--force-agent`, Linux validation and hosted CI not run). This
  phase neither changes nor qualifies any of them.

## Verification

- Commands actually executed and observed outcomes:
  - this branch's workflow check and documentation verifier, and `git diff --check` on the staged
    files, passed at the baseline, the declaration, the candidate, the review record, the corrected
    candidate and this records commit ([checks](../../../engineering/localized-repair-c271/operational-plan-review-p30/CHECKS.json));
  - read-only host inspection ([executor inventory](../../../engineering/localized-repair-c271/operational-plan-review-p30/EXECUTOR-INVENTORY.json))
    and the downloads comparison ([record](../../../engineering/localized-repair-c271/operational-plan-review-p30/R06-DOWNLOADS-COPIES.json));
  - independent review: the first review rejected candidate `8aa4a800` on mandatory finding F-01
    ([review](../../../engineering/localized-repair-c271/operational-plan-review-p30/INDEPENDENT-REVIEW-001.md));
    the re-review accepted `96847fae` with nonmandatory findings F-12 to F-18, which were resolved
    afterwards without a further review ([re-review](../../../engineering/localized-repair-c271/operational-plan-review-p30/INDEPENDENT-REVIEW-002.md)).
- Failures: none in a required check. The first candidate's mandatory finding is resolved by the
  corrected candidate; both versions are retained.
- Pending and not-run checks: H0, H1, Node, `ldd`, the routine driver, the unit suite and every
  behavioural test are excluded from this phase and belong to later gates. No hosted run was
  started.
- Durable logs, review findings, and evidence links: the phase records above. The raw inventory
  output, the reviewer's original review files and all check outputs are kept in
  `../OntoKin-local/c271-p30/` beside the clone.
- Evidence locations and hashes: in the phase records.
- Relevant validation/CI results and source revisions: workflows are manual-only; none ran.
- Current review eligibility and any changes since review: the reviewed corrected candidate is
  `96847fae`; this records commit adds the closing records and changes no reviewed statement.

## Recovery

- Unpublished commits: none after the push of this records commit, which the closing record
  observes.
- Unique uncommitted files: none in the worktree. The main checkout's items stay in place.
- Outstanding operations and owned processes: none.
- Unknown operation and its intended parent/tree/commit or request identity: none in this phase.
- Remote readback needed before retrying that operation: not applicable.
- Current blockers with concrete evidence: P30-EXECUTOR-001
  ([executor inventory](../../../engineering/localized-repair-c271/operational-plan-review-p30/EXECUTOR-INVENTORY.json),
  [contract requirements](../../../engineering/localized-repair-c271/operational-plan-review-p30/CONTRACT-REQUIREMENTS.json)).
- Unpublished work that must be recovered and its known location: none.
- Actual unpublished recovery payloads and declared external dependencies: none. This local phase
  produces no handoff ZIP.

## Coordination

- Active workers and reserved files: none.
- Actual subagents, assigned scopes, and unresolved worker activity: one fresh-context independent
  reviewer, read-only, writing only in the working evidence directory; it reviewed twice and
  finished. It wrote nothing to the repository.
- Integration owner, expiry, and latest verified ownership record: none. Main's lease is released
  and was not used by this phase.
- Lease status: released (main STATUS).
- Ownership released, renewed, transferred, or still uncertain: owner `c271-p30-55a168e30426` is
  released once the phase's closing record is on the remote and the checkpoint comments are on
  PR274 and issue273. It makes no write after them.

## Continuation

- Owner decision after the outcome: on 2026-11-25 (America/Denver), asked "Which route should C271
  take next?", the owner answered "Design macOS contract (C)", typed in the session that started
  this one and relayed here word for word. Route C of
  [REVIEW-OUTCOME](../../../engineering/localized-repair-c271/operational-plan-review-p30/REVIEW-OUTCOME.md)
  section 6 is selected.
- One exact next action, inputs, acceptance gate, and stopping condition: route C's first phase,
  design only.
  - A new, versioned contract for the owner's macOS arm64 executor that substitutes, explicitly,
    the items route C lists: the Node build (`v24.22.1` kept, a darwin-arm64 build pinned by its
    own bytes), the qualification Python, the host inspection, the process supervisor, the
    preparer and the provider's and probe's host bindings.
  - It keeps the original test meaning: the seven method bodies, the reader bytes, the thresholds
    and limits, three real checker starts, the no-skip rule and the numerical audit.
  - It labels every result with that executor and keeps the unmet Linux-contract gates unmet.
  - It also decides the driver's selection rule for main's ordinary local routine, which R04
    needs (REVIEW-OUTCOME section 7).
  - It is declared in C271's records before its substantive work, independently reviewed and
    adopted before any implementation. It installs no host tooling and implements nothing.
- The condition that makes that action safe and useful to execute: the owner's selection above;
  the branch head read from the remote equal to, or descended from, the commit that adds this
  phase's closing record; no other writer on this branch.
- Open gates after it, each a separate phase: implementation of the adopted contract, the
  substituted executor's qualification in place of H0 and H1, N34 and N57 for the Linux contract
  (unchanged), the required regression (R03), reviewed integration with actual-main verification
  (R04), and parent completion with final delivery (R05). H0 and H1 under `/0.1.5` stay unmet:
  P30-EXECUTOR-001.
- Where a session that starts from main finds C271: main's `STATUS.md` and `CURRENT.json` still
  describe C271 as observed on 2026-11-25. This phase does not write main. The current state is on
  this branch.

## Delivery

- Local checkpoint status: the records commit that carries this checkpoint, followed by one small
  closing record.
- Verified push state, or unconfirmed: the corrected candidate was read back from the remote at
  04:04:05Z. The push of this commit is observed by the closing record, and the push of the
  closing record by the final report.
- Actual merge/resulting-main checks, or remaining integration gate: R04, a later phase. Main is
  unchanged.
- Branch retention/deletion evidence, or exact pending cleanup instruction: the branch is
  retained for unfinished C271. The worktree and the working evidence directory stay in place.
- Durable evidence references: the phase records named above.
- Integration state separate from saved-delivery state: not integrated. In local mode no Library
  save is required for this phase.
- Published checkpoint revision and readback result: see the closing record.

No receipt of the receipt: Git reveals the commit that carries this record.
