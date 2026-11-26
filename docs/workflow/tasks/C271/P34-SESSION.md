# Session checkpoint: C271-P34 gate MP, preparation of the runtime, reader tree and .venv

Follows current main's [session template](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/docs/workflow/templates/SESSION.md).
Detailed evidence is linked, not repeated. Machine paths are left out; places beside the clone
are named relative to it. Times are UTC. This is the outcome version of the checkpoint; the
declaration version is in Git history at `6d08e026`.

## Identity

- Checkpoint time and author identity: 2026-11-26T22:32:39Z, Director `c271-p34-ec1a7de2360d`.
- Task, session, and agent or tool identity: C271, phase C271-P34-macos-preparation-mp; the same
  Claude Code session (model Claude Opus 5.5) that carried out C271-P30 to P33, working in the
  C271 worktree.
- Execution mode, and the entry document or record that declared it: `local`, from current main's
  [LOCAL-START-HERE](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/LOCAL-START-HERE.md);
  C271's record names local mode since R07.
- Owner direction: "Start gate MP", and the approval of exactly two downloads, both given in this
  session and quoted in the [declaration](../../../engineering/localized-repair-c271/macos-preparation-p34/PHASE.json).
- Worktree and branch: `../OntoKin-worktrees/c271`, on `work/c271-missing-import-digest-control`.
- Current user objective and bounded milestone: gate MP of the adopted contract
  `ontokin.current-host-readback/0.2.0`. See the
  [preparation plan](../../../engineering/localized-repair-c271/macos-preparation-p34/PREPARATION-PLAN.md)
  and the [outcome](../../../engineering/localized-repair-c271/macos-preparation-p34/OUTCOME.json).
- Task, requirements, and plan paths: [task.json](task.json), [REQUIREMENTS](REQUIREMENTS.md)
  (section P34), [PLAN](PLAN.md) (section P34).

## Context loaded

- Entry file and registry revision: current main `51223c9b94a222f29d38eb6c33808f8e55e2bff9`, whose
  instruction files this branch carries since gate MB; LOCAL-START-HERE was opened again for this
  phase.
- Required read-set actually opened, with revision or hash:
  - the adopted contract, sections 3, 4, 6, 11 and 12;
  - MI's outcome, with its obligations for MP;
  - the preparer's interface note and code;
  - the setup guide and OK-ENG-006 section 3;
  - the macOS lock and its provenance.
- Required files missing, truncated, or inaccessible: none.
- Current/deferred product work and applicable adopted contracts: no product work. P05's
  `ontokin.current-host-readback/0.1.0` and its plans `/0.1.1` to `/0.1.5` stay adopted and
  unchanged. GOAL's ceilings of 100,000 operations and 30,000 ms are unchanged.

## Source

- Starting revision: `180075b7952fb4df50ec35eb64106410bfa1d8f9`, which is P33's closing record.
- Bound commit of the preparation (D-17): `601f39361940422179ff7683aa602c2b36622944`. It adds the
  reviewed plans' portable copies and digests, and changes no input or import-closure file since
  the reviewed `6d08e026`.
- Outcome records: the commit that carries this checkpoint. Its push is read back in the closing
  record, `CLOSING.json` beside the outcome record.
- Dirty and untracked state: the worktree was clean at the bound commit before and after every
  preparation run, with only `.venv/` ignored. The main checkout's owner items stay untouched.
- Repository, actual main SHA, and observation time: `Omegapy/OntoKin`, main
  `51223c9b94a222f29d38eb6c33808f8e55e2bff9`, read with `git ls-remote --heads origin` at
  2026-11-26T22:33:15Z.
- Active branch/head, open PR, and scope issue: [PR274](https://github.com/Omegapy/OntoKin/pull/274)
  open and draft; [issue273](https://github.com/Omegapy/OntoKin/issues/273) open.

## Work

- Requirements: R01 and R02 done; R03, R04 and R05 not_done. P01 done, P02 in_progress. Task
  status `in_progress`.
- Acceptance items: A1 to A8 of the declaration are met, A6 with the doctor's stated limit. The
  closing record completes A9.
- Workers: W1, the independent preparation author, and W2, the independent reviewer. They were
  actual Claude Code subagents in fresh contexts, with the session's model.
  - W2 reviewed the plans before execution ([PLAN-REVIEW-001](../../../engineering/localized-repair-c271/macos-preparation-p34/reviews/PLAN-REVIEW-001.md)),
    with findings P-01 to P-10, all adopted.
  - W2 then reviewed the results ([RESULT-REVIEW-001](../../../engineering/localized-repair-c271/macos-preparation-p34/reviews/RESULT-REVIEW-001.md)),
    with findings R-01 to R-03, resolved or carried to MH.
  - Both reviews were ACCEPT_WITH_NONMANDATORY_FINDINGS.
- Prepared:
  - the Node.js `v24.22.1` runtime, exactly `bin/node` and `NODE-SOURCE.json`;
  - the 24-file reader tree;
  - the worktree's `.venv`, with exactly the seven pinned packages and no pip.

  Both trees are under `../OntoKin-local/c271-macos/`, outside Git, and both are `INSTALLED_EXACT`.

## Environment

- Profile and its readiness: the doctor reports `core` ready. It reports `python-verification` as
  `not_checked`, because pip is absent by design. Lock, packages, imports and the native reader
  are ready. Its rebuild advice is not followed (D-21).
- Interpreter, operating system and architecture: CPython 3.12.13, macOS 26.6.2 (25G83), arm64.
- Node: no MP step started Node, `ldd` or `codesign`
  ([audit](../../../engineering/localized-repair-c271/macos-preparation-p34/AUDIT-SUMMARY.json)).
  The pinned runtime has never run.

## Verification

- Commands run: the preparation plan, sections 5 and 7, through `run_preparation.sh` from the
  bound commit. The run log, the receipts and the checks are in the phase records as portable
  copies; the exact files are beside the clone, and their SHA-256 values are recorded.
- One recorded failure: the Director's exact `.venv` check crashed on its first run, on
  single-quoted markers. It was fixed and rerun on the retained snapshots, and it passed
  ([record](../../../engineering/localized-repair-c271/macos-preparation-p34/run-001/venv-verify-rerun.md)).
- Not run in this phase: Node, `ldd`, `codesign`, M0, M1, N34-M, the qualifying cohort, the
  routine driver, and the visual-verification profile.

## Recovery

- Unpublished commits: none once the outcome records are pushed; the closing record observes
  that push.
- Outstanding operations and owned processes: none.
- Retained for MH:
  - both archives;
  - the two exact apply plans and the two install receipts, at their paths and with their modes;
  - the prepared trees, which are not to be opened in Finder;
  - the rule that the `.venv` runs only with `-B` until MH has frozen the Python inventory and
    run M0.
- Current blockers with concrete evidence: none. P30-EXECUTOR-001 still blocks the Linux
  contract's H0 and H1 in local mode.

## Coordination

- Integration owner and lease status: none; main's lease is released and was not used.
- Ownership: owner `c271-p34-ec1a7de2360d` held this branch for the phase and releases it with
  the closing record.

## Continuation

- One exact next action: gate MH.
  - It runs N34-M, then M0 and M1 on this host, then the qualifying cohort of the seven readback
    methods and the direct negatives, with an independent audit.
  - It is the first gate that starts the pinned Node, under the supervisor's bounds.
  - It is a separate phase that needs the owner's selection.
- Stopping condition: reached. The reviewed preparation is pushed and read back with its records.

No receipt of the receipt: Git reveals the commit that carries this record.
