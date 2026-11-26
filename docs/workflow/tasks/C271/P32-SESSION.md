# Session checkpoint: C271-P32 gate MB, merge of main into the branch

Follows current main's [session template](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/docs/workflow/templates/SESSION.md).
This is the declaration version; the outcome version replaces it, and Git keeps this one. Times
are UTC.

## Identity

- Checkpoint time and author identity: 2026-11-26T05:53Z, Director `c271-p32-08e8ceaa9140`.
- Task, session, and agent or tool identity: C271, phase C271-P32-main-merge-mb; the same Claude
  Code session (model Claude Opus 5.5) that carried out C271-P30 and P31.
- Execution mode, and the entry document or record that declared it: `local`, from current main's
  LOCAL-START-HERE; C271's record names local mode since R07.
- Owner direction: the owner answered "Start gate MB", typed in this session, to the question
  "Should I start gate MB next: a reviewed merge of main into the C271 branch?".
- Worktree and branch: `../OntoKin-worktrees/c271`, on `work/c271-missing-import-digest-control`.
- Current user objective and bounded milestone: gate MB of the adopted contract
  `ontokin.current-host-readback/0.2.0`. That is one reviewed merge commit of main `51223c9b` into
  this branch, which resolves the six overlaps by meaning, pushed and read back. Main is not written.
- Task, requirements, and plan paths: [task.json](task.json), [REQUIREMENTS](REQUIREMENTS.md),
  [PLAN](PLAN.md); acceptance A1 to A6 in the
  [phase declaration](../../../engineering/localized-repair-c271/main-merge-p32/PHASE.json).

## Source

- Starting revision: `07d0ff5a41338f05810e9c086df00d48a22874f4`, C271-P31's closing record.
- Remote observation: `git ls-remote --heads origin` at 2026-11-26T05:52:26Z read this branch at
  `07d0ff5a` and main at `51223c9b`.
- Merge base `e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d`. A dry run of the merge
  (`git merge-tree`, which changes no ref or file) gives the same six files as
  [MAIN-CONFLICTS](../../../engineering/localized-repair-c271/p29-local-publication-r07/MAIN-CONFLICTS.md):
  - five with content conflicts: `STATUS.md`, `docs/workflow/CURRENT.json`,
    `docs/workflow/memory.json`, `tests/test_local_checks.py` and `tools/check_local.py`;
  - one clean: `docs/README.md`.
- PR274 open and draft; issue273 open.

## Work, verification and recovery

- Requirements: R01 and R02 done; R03 to R05 not_done; P01 done, P02 in_progress.
- Remaining: A1 to A6.
- Unpublished commits: none after the declaration push. No unknown operation. No other writer on
  this branch.

## Continuation

- Next action: carry out A2 to A6 and stop at the reviewed, pushed merge or a concrete blocker.
