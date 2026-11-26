# Session checkpoint: C271-P31 macOS arm64 contract design (route C)

Follows current main's [session template](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/docs/workflow/templates/SESSION.md).
Detailed evidence is linked, not repeated. Machine paths are left out; places beside the clone
are named relative to it. Times are UTC. This is the outcome version of the checkpoint; the
declaration version is retrievable from commit `af6340debba1345dd7290c19ec8279c8568f3d8a`.

## Identity

- Checkpoint time and author identity: 2026-11-26T05:47Z, Director `c271-p31-a99073a9641d`.
- Task, session, and agent or tool identity: C271, phase C271-P31-macos-contract-design; the same
  Claude Code session (model Claude Opus 5.5) that carried out C271-P30, working in the C271
  worktree.
- Execution mode, and the entry document or record that declared it: `local`, from current main's
  [LOCAL-START-HERE](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/LOCAL-START-HERE.md);
  C271's record names local mode since R07.
- Owner direction: on 2026-11-25 (America/Denver), asked "Which route should C271 take next?",
  the owner answered "Design macOS contract (C)". The reply was relayed word for word from the
  session that started this one.
- Worktree and branch: `../OntoKin-worktrees/c271`, on `work/c271-missing-import-digest-control`.
- Current user objective and bounded milestone: route C's design-only phase. It is reached: the
  design is adopted, design only ([adoption](../../../engineering/localized-repair-c271/macos-contract-design-p31/ADOPTION.json)).
  The phase stops here.
- Task, requirements, and plan paths: [task.json](task.json), [REQUIREMENTS](REQUIREMENTS.md)
  (section P31), [PLAN](PLAN.md) (section P31).

## Context loaded

- Entry file and registry revision: current main `51223c9b94a222f29d38eb6c33808f8e55e2bff9`.
- Required read-set actually opened, with revision or hash: [READ-SET](../../../engineering/localized-repair-c271/macos-contract-design-p31/READ-SET.json),
  with its external Node.js facts and host facts. The independent reviewer recomputed every entry.
- Required files missing, truncated, or inaccessible: none.
- Current/deferred product work and applicable adopted contracts: no product work. P05's
  `ontokin.current-host-readback/0.1.0` and its plans `/0.1.1` to `/0.1.5` stay adopted and
  unchanged. GOAL's ceilings of 100,000 operations and 30,000 ms are unchanged.

## Source

- Starting revision and current code checkpoint: started at `7c3a8de1be4de988219a3fc056a7eacedcd15cc1`.
  Commits of this phase:
  - the declaration `af6340debba1345dd7290c19ec8279c8568f3d8a`;
  - revision 1 `4ee691aedc30dac1e3ec9a63917d7e6ac7493912`, rejected;
  - revision 2 `90e8a5fbff6a43a1ed08284662e16f9aa5e96a83`, rejected;
  - revision 3 `dd98e9830fffc0da96bf1cfc408c7f246867a20a`, accepted with nonmandatory findings;
  - this records commit, whose identity Git reveals.
- Dirty and untracked state: the worktree is clean apart from its ignored `.venv` after this
  commit. The main checkout's owner items stay untouched.
- Actual remote observation, with command and time, or offline and stale: `git ls-remote --heads origin`
  at 2026-11-26T05:34:20Z read this branch at `dd98e983` and main at `51223c9b`. It also read a
  branch that this phase did not create, `work/c271-p29-trd-record` at `880933a4`, which this phase
  does not touch. The push of this records commit is observed in the closing record.
- Repository, actual main SHA/tree, and observation time: `Omegapy/OntoKin`, main
  `51223c9b94a222f29d38eb6c33808f8e55e2bff9`, unchanged throughout the phase.
- Active branch/head, open PR, and scope issue: [PR274](https://github.com/Omegapy/OntoKin/pull/274)
  open, draft, unmerged and conflicting with main; [issue273](https://github.com/Omegapy/OntoKin/issues/273) open.
- Local checkout identity and unpublished changes, if a workspace exists: none after the push.

## Work

- Requirements completed, incomplete, blocked, and excluded: R01 and R02 done; R03, R04 and R05
  not_done. P01 done, P02 in_progress. Task status `in_progress`. Excluded: the declaration's list.
- Completed acceptance items and last completed gate: A1 to A9. The last completed gate is MD, the
  adopted design of `ontokin.current-host-readback/0.2.0` ([contract](../../../engineering/localized-repair-c271/macos-contract-design-p31/CONTRACT.md),
  [machine-readable](../../../engineering/localized-repair-c271/macos-contract-design-p31/CONTRACT.json)).
  - **Substituted:**
    - the Node build: the official `v24.22.1` darwin-arm64 archive, SHA-256
      `89c682593d76cd44233fa53b1563264e7de9cbb189cad169135c5b4fadfbc0a7`;
    - the qualification Python, by its installation-tree inventory;
    - the host observation, M0 and M1;
    - the supervisor, as a Darwin variant without the child-subreaper precondition;
    - the preparer, with the official archive's member policy;
    - the provider's and probe's host bindings, with the boot check moved to the provider;
    - the driver environment and the Git binding;
    - the OS-supplied `__CF_USER_TEXT_ENCODING`, which is admitted.
  - **Kept:** the 0.1.0 argv and the original test meaning.
  - **Selection rule:** ordinary runs proceed and fail the readback class visibly at setup.
  - **Controls:** 36 declarative controls, NOT_RUN.
- Changed artifact paths and exact code/input identities: this phase's records under
  `docs/engineering/localized-repair-c271/macos-contract-design-p31/`, this checkpoint, the P31
  sections of REQUIREMENTS and PLAN, and the current-state fields of task.json and the branch
  CURRENT. No product, test, pin, contract or expectation of the existing versions changed.
- Decisions made: the design and its adoption, design only. In revision 2 the permission-model
  launch was withdrawn, and the ordinary-run skip of revision 1 was replaced by a visible setup
  error.
- Remaining items: none in this phase after the closing record.
- Learning checkpoint result and capture preference: two observations, recorded in
  [LEARNING-DECISION](../../../engineering/localized-repair-c271/macos-contract-design-p31/LEARNING-DECISION.md)
  and not captured, because `docs/workflow/memory.json` conflicts with main.

## Environment

- Profile and its readiness: unchanged from C271-P30's record; nothing was prepared.
- Interpreter, operating system and architecture: CPython 3.12.13 (Homebrew), macOS 26.6.2 (25G83), arm64.
- Terminal and executed interpreter/platform: zsh; the worktree's `.venv/bin/python` ran the
  record checks.
- Available read/write/conditional-update/merge operations: Git reads, local commits, non-forced
  pushes; GitHub API reads and comments; HTTPS reads of public pages (no download).
- Missing capabilities and their effect on this milestone: none.

## Verification

- Commands actually executed and observed outcomes: this branch's workflow check, documentation
  verifier and scoped whitespace check passed at the declaration, at each revision and at this
  records commit ([checks](../../../engineering/localized-repair-c271/macos-contract-design-p31/CHECKS.json)).
  Read-only host facts and the Node.js checksum file are in the read set.
- Independent review: three reviews by one fresh-context reviewer.
  - Revisions 1 and 2 were rejected:
    [first review](../../../engineering/localized-repair-c271/macos-contract-design-p31/INDEPENDENT-REVIEW-001.md),
    [second](../../../engineering/localized-repair-c271/macos-contract-design-p31/INDEPENDENT-REVIEW-002.md).
  - Revision 3 was accepted with nonmandatory findings G-20 to G-22, which were resolved
    afterwards without a further review:
    [third](../../../engineering/localized-repair-c271/macos-contract-design-p31/INDEPENDENT-REVIEW-003.md),
    [dispositions](../../../engineering/localized-repair-c271/macos-contract-design-p31/REVIEW-DISPOSITION.json).
- Failures: none in a required check; the rejected revisions are retained.
- Pending and not-run checks: every control of the contract is NOT_RUN. No Node, test, driver,
  download or installation ran.
- Durable logs, review findings, and evidence links: the phase records; the reviewer's originals
  and the check outputs are in `../OntoKin-local/c271-p31/` beside the clone.
- Current review eligibility and any changes since review: the accepted revision is `dd98e983`;
  the final payloads add the G-20 to G-22 corrections, and ADOPTION.json binds their exact bytes.

## Recovery

- Unpublished commits: none after the push of this records commit, which the closing record
  observes.
- Unique uncommitted files: none.
- Outstanding operations and owned processes: none; the reviewer finished.
- Unknown operation: none.
- Current blockers with concrete evidence: none for this phase. P30-EXECUTOR-001 still blocks the
  Linux contract's H0 and H1 in local mode.

## Coordination

- Active workers and reserved files: none.
- Actual subagents, assigned scopes, and unresolved worker activity: one independent reviewer,
  read-only, three reviews, finished. It reported temporary scratch files outside its assigned
  directory in its first review, since removed. A fetch worker read the public Node.js pages.
- Integration owner and lease status: none; main's lease is released and was not used.
- Ownership: owner `c271-p31-a99073a9641d` is released with the phase's closing record.

## Continuation

- One exact next action, inputs, acceptance gate, and stopping condition: gate MB of the adopted
  contract.
  - A reviewed merge of main into this branch that resolves the six overlaps by meaning
    ([MAIN-CONFLICTS](../../../engineering/localized-repair-c271/p29-local-publication-r07/MAIN-CONFLICTS.md)).
  - It brings main's macOS lock, local environment specification and tools.
  - It does not integrate into main.
  - It is a separate phase that needs the owner's selection.
- Then: MI (implementation), MP (preparation, with the owner's approval of the Node download),
  MH (qualification on the owner's executor), MR (the complete qualifying routine, R03), R04 and
  R05.
- The condition that makes that action safe and useful to execute: the owner's selection of MB;
  the branch head read from the remote equal to, or descended from, the commit that adds this
  phase's closing record; no other writer on this branch.
- Where a session that starts from main finds C271: main's `STATUS.md` and `CURRENT.json` still
  describe C271 as observed on 2026-11-25. The current state is on this branch.

## Delivery

- Local checkpoint status: the records commit that carries this checkpoint, followed by one small
  closing record.
- Verified push state, or unconfirmed: revision 3 was read back at 05:34:20Z; the push of this
  commit is observed by the closing record.
- Actual merge/resulting-main checks, or remaining integration gate: R04. Main is unchanged.
- Branch retention: retained for unfinished C271.
- Integration state separate from saved-delivery state: not integrated; no Library save is required
  in local mode.

No receipt of the receipt: Git reveals the commit that carries this record.
