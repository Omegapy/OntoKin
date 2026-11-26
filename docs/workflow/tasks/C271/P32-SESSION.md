# Session checkpoint: C271-P32 gate MB, merge of main into the branch

Follows current main's [session template](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/docs/workflow/templates/SESSION.md),
which is now also this branch's template. This is the outcome version; the declaration version is
retrievable from commit `6fb6525f670ac619857d4830cda0a3e2bf298d93`. Times are UTC.

## Identity

- Checkpoint time and author identity: 2026-11-26T06:17Z, Director `c271-p32-08e8ceaa9140`.
- Task, session, and agent or tool identity: C271, phase C271-P32-main-merge-mb; the same Claude
  Code session (model Claude Opus 5.5) that carried out C271-P30 and P31.
- Execution mode, and the entry document or record that declared it: `local`, from current main's
  LOCAL-START-HERE, which this branch now carries too.
- Owner direction: "Start gate MB", typed by the owner in this session.
- Worktree and branch: `../OntoKin-worktrees/c271`, on `work/c271-missing-import-digest-control`.
- Current user objective and bounded milestone: gate MB. It is reached: the reviewed merge is
  pushed. The phase stops here.

## Context loaded

- Governing instructions: current main `51223c9b`, now merged into this branch.
- Inputs: MAIN-CONFLICTS.md, both sides of the six overlaps, and main's `tools/chat_workflow.py`
  schema-2 rules.

## Source

- Commits of this phase:
  - the declaration `6fb6525f`;
  - the merge `5f30f26b313946d1fdd763670b340341d2eed489`, tree
    `f0a017e2a01aaecd22340a3e7b20e5d686ea57f6`, with parents `6fb6525f` and `51223c9b` and merge base
    `e1a48f7d`;
  - this records commit, which Git reveals.
- Remote observation: `git ls-remote --heads origin` at 2026-11-26T06:16:00Z read this branch at
  `5f30f26b` and main at `51223c9b`. The push of this commit is observed by the closing record.
- PR274: open and draft, head `5f30f26b`; GitHub's mergeability was being recomputed. issue273 is
  open.
- Dirty and untracked state: clean apart from `.venv` after this commit. The main checkout's owner
  items are untouched.

## Work

- Requirements: R01 and R02 done; R03 to R05 not_done; P01 done, P02 in_progress. Task
  `in_progress`.
- Completed acceptance: A1 to A6 of the
  [declaration](../../../engineering/localized-repair-c271/main-merge-p32/PHASE.json). Each overlap
  is resolved by meaning ([resolution](../../../engineering/localized-repair-c271/main-merge-p32/MERGE-RESOLUTION.md)).
- `CURRENT.json` is schema 2. The schema-1 file is retained as `CURRENT-C271-schema1.json` (SHA-256
  `b0f51618…`), with all 40 of its top-level keys named in the history entry.
- Learning checkpoint: no new lesson. Keeping a replaced workflow file as bound history follows
  main's own migration practice. The deferred lessons of R07, P30 and P31 can now be captured,
  because `memory.json` is reconciled; capturing them is left to a later phase.
- Remaining follow-ups, not in this phase:
  - `TRDs/INDEX.md` does not list the branch's R07 TRD. Regenerate it with the TRD tool later.
  - STATUS on this branch shows main's dated view of C271 until R04.

## Environment

- The doctor now diagnoses this worktree: `core` ready; `python-verification` missing, because the
  `.venv` holds none of the seven pinned packages. Preparing it belongs to gate MP. The doctor was
  given a non-existent Node path, so no Node process started.
- Interpreter and platform: CPython 3.12.13 (Homebrew), macOS 26.6.2, arm64.

## Verification

- On the merged tree: main's workflow check (13 tasks), the documentation verifier, a scoped
  whitespace check and the 33 focused driver tests passed
  ([checks](../../../engineering/localized-repair-c271/main-merge-p32/CHECKS.json)).
- Independent review of the exact merge commit: accepted with nonmandatory findings M-01 to M-06
  ([review](../../../engineering/localized-repair-c271/main-merge-p32/INDEPENDENT-REVIEW.md)).
  - M-01 and M-02 are corrected in MERGE-RESOLUTION.md.
  - M-03 and M-04 are resolved here: CURRENT's history entry names all 40 keys, and
    `p32_fields_index` is added.
  - M-05 and M-06 are left as stated above.
- Not run: no routine driver, readback method, behavioural test or Node.

## Recovery

- Unpublished commits: none after the push of this commit. No unknown operation. No other writer
  on this branch.

## Coordination

- One fresh-context independent reviewer, read-only, finished. Its temporary detached worktree is
  removed. No lease is held.
- Owner `c271-p32-08e8ceaa9140` is released with the closing record.

## Continuation

- Next action: gate MI of the adopted contract.
  - It implements the 0.2.0 adaptations: the Darwin supervisor variant, the provider and probe host
    bindings, the preparer route, the driver environment, the Git binding and the selection rule.
  - Non-runtime controls are frozen independently, and the result is reviewed independently.
  - It is a separate phase that needs the owner's selection.
- After MI: MP (preparation, with the owner's approval of the Node download), MH, MR (R03), R04
  and R05.
- Safe when: the owner selects it; the remote head equals, or descends from, the commit that adds
  this phase's closing record; no other writer.

## Delivery

- Not integrated into main. The branch is retained. No Library save is required in local mode.

No receipt of the receipt: Git reveals the commit that carries this record.
