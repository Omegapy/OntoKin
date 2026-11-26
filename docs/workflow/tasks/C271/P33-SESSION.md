# Session checkpoint: C271-P33 gate MI, implementation of the 0.2.0 adaptations

Follows current main's [session template](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/docs/workflow/templates/SESSION.md).
Detailed evidence is linked, not repeated. Machine paths are left out; places beside the clone
are named relative to it. Times are UTC. This is the outcome version of the checkpoint; the
declaration version is in Git history at `f3a5acf8`.

## Identity

- Checkpoint time and author identity: 2026-11-26T20:02:37Z, Director `c271-p33-a99647756bed`.
- Task, session, and agent or tool identity: C271, phase C271-P33-macos-implementation-mi; the
  same Claude Code session (model Claude Opus 5.5) that carried out C271-P30, P31 and P32, working
  in the C271 worktree.
- Execution mode, and the entry document or record that declared it: `local`, from current main's
  [LOCAL-START-HERE](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/LOCAL-START-HERE.md);
  C271's record names local mode since R07.
- Owner direction: on 2026-11-26, the owner was asked "Should I start gate MI, the implementation
  of the 0.2.0 macOS adaptations?" and typed "Start gate MI" in this session.
- Worktree and branch: `../OntoKin-worktrees/c271`, on `work/c271-missing-import-digest-control`.
- Current user objective and bounded milestone: gate MI of the adopted contract
  `ontokin.current-host-readback/0.2.0` ([phase declaration](../../../engineering/localized-repair-c271/macos-implementation-p33/PHASE.json),
  [implementation plan](../../../engineering/localized-repair-c271/macos-implementation-p33/IMPLEMENTATION-PLAN.md),
  [outcome](../../../engineering/localized-repair-c271/macos-implementation-p33/OUTCOME.json)).
- Task, requirements, and plan paths: [task.json](task.json), [REQUIREMENTS](REQUIREMENTS.md)
  (section P33), [PLAN](PLAN.md) (section P33).

## Context loaded

- Entry file and registry revision: current main `51223c9b94a222f29d38eb6c33808f8e55e2bff9`,
  which gate MB put on this branch. Main is unchanged. After each context compaction,
  LOCAL-START-HERE and PROTOCOL section 4 were opened again.
- Required read-set actually opened, with revision or hash: the adopted
  [CONTRACT](../../../engineering/localized-repair-c271/macos-contract-design-p31/CONTRACT.md) and
  [CONTRACT.json](../../../engineering/localized-repair-c271/macos-contract-design-p31/CONTRACT.json),
  and [AMENDMENT-001](../../../engineering/localized-repair-c271/macos-implementation-p33/AMENDMENT-001.md),
  adopted in this phase. P29's required-images controls and their companion list were read for
  [D-18](../../../engineering/localized-repair-c271/macos-implementation-p33/DIRECTOR-DECISIONS.md).
- Required files missing, truncated, or inaccessible: none.
- Current/deferred product work and applicable adopted contracts: no product work. P05's
  `ontokin.current-host-readback/0.1.0` and its plans `/0.1.1` to `/0.1.5` stay adopted and
  unchanged. GOAL's ceilings of 100,000 operations and 30,000 ms are unchanged.

## Source

- Starting revision: `1c2f25ba224a5c3419004d1d331d29e01378ae00`, which is P32's closing record.
- Reviewed candidate: `c534e7b72201dbf0ed6b366f5b0ec631415dedb0`. Its implementation and controls are
  those of `7b759de0`, which the final verification ran; the candidate adds only the checks
  records. The first review's candidate was `2d8d6d15cd04725e0d29050253e22768f58e2c78`.
- Outcome records: the commit that carries this checkpoint. Its push is read back in the
  closing record, `CLOSING.json` beside the outcome record.
- Dirty and untracked state: the worktree is clean apart from its ignored `.venv`. The main
  checkout's owner items stay untouched.
- Repository, actual main SHA, and observation time: `Omegapy/OntoKin`, main
  `51223c9b94a222f29d38eb6c33808f8e55e2bff9`, read with `git ls-remote --heads origin` at
  2026-11-26T20:02:25Z.
- Active branch/head, open PR, and scope issue: [PR274](https://github.com/Omegapy/OntoKin/pull/274)
  open and draft; [issue273](https://github.com/Omegapy/OntoKin/issues/273) open.

## Work

- Requirements: R01 and R02 done; R03, R04 and R05 not_done. P01 done, P02 in_progress. Task
  status `in_progress`.
- Acceptance items: A1 to A8 of the declaration are met, A2 as amended and A7 with D-18's stated
  exception. The closing record completes A9
  ([outcome](../../../engineering/localized-repair-c271/macos-implementation-p33/OUTCOME.json)).
- Workers: W1 to W7 of the implementation plan, section 3, all returned. They were actual Claude
  Code subagents in fresh contexts, with the session's model. Their briefs and logs are kept beside
  the clone, in `../OntoKin-local/c271-p33/workers/`.
- Amendment: [P33-AMENDMENT-001](../../../engineering/localized-repair-c271/macos-implementation-p33/AMENDMENT-001.md)
  (design revision 4), adopted after a rejecting review and an accepting re-review.
- Decisions: D-01 to D-21 in [DIRECTOR-DECISIONS](../../../engineering/localized-repair-c271/macos-implementation-p33/DIRECTOR-DECISIONS.md).
- Independent review: [review 001](../../../engineering/localized-repair-c271/macos-implementation-p33/INDEPENDENT-REVIEW-001.md)
  accepted `2d8d6d15` with nonmandatory findings I-01 to I-08. D-20 fixed I-01, I-07 and part of
  I-02, and carried or noted the rest. The independent control author added controls for I-01
  and I-08 in refreeze 002. [Review 002](../../../engineering/localized-repair-c271/macos-implementation-p33/INDEPENDENT-REVIEW-002.md)
  of that change: ACCEPT_WITH_NONMANDATORY_FINDINGS. Its two findings, I-09 and I-10, concern records and are resolved at closing (D-21).

## Environment

- Profile and its readiness: the doctor reported `core` ready and `python-verification` missing
  at the phase start. The worktree's `.venv` holds none of the seven pinned packages; gate MP
  prepares them. MI used the standard library only.
- Interpreter, operating system and architecture: CPython 3.12.13 (Homebrew), macOS 26.6.2 (25G83), arm64.
- Node is installed on this host and reachable through `PATH`. No MI check started it
  ([process-start audit](../../../engineering/localized-repair-c271/macos-implementation-p33/CHECKS.json)).

## Verification

- Commands run: see [CHECKS](../../../engineering/localized-repair-c271/macos-implementation-p33/CHECKS.json).
  It records the sixteen modules, the workflow check, the documentation verifier, the
  whitespace and byte-identity checks, and the process-start audit.
- Results:
  - The frozen controls pass, 151 tests with no skip. Their independent author refroze six cases
    after the first run with no expected outcome changed, and added two cases for the review's
    findings.
  - The six new modules pass.
  - Every existing module keeps its phase-start results, except the two 0.1.0 driver tests that
    assert the refusal S8 removes (D-18).
- Not run in this phase: Node, `ldd`, `codesign`, downloads, installs, M0 and M1 on the real
  host, the qualifying cohort, and the routine driver.

## Recovery

- Unpublished commits: none once the outcome records are pushed; the closing record observes
  that push.
- Outstanding operations and owned processes: none; no process started by MI is left.
- Current blockers with concrete evidence: none for MI. P30-EXECUTOR-001 still blocks the Linux
  contract's H0 and H1 in local mode.

## Coordination

- Integration owner and lease status: none; main's lease is released and was not used.
- Ownership: owner `c271-p33-a99647756bed` held this branch for the phase and releases it with
  the closing record.

## Continuation

- One exact next action: gate MP, the reviewed preparation of the Node runtime, the Python
  verification packages and the reader tree. It is a separate phase. It needs the owner's
  selection, and the owner's explicit approval of the download of
  `node-v24.22.1-darwin-arm64.tar.gz` (about 53 MB) from nodejs.org.
- Stopping condition: reached. The reviewed implementation is pushed and read back with its
  records.

No receipt of the receipt: Git reveals the commit that carries this record.
