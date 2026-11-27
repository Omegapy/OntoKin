# Session checkpoint: C271-P35 gate MH, host qualification of the readback methods

Follows current main's [session template](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/docs/workflow/templates/SESSION.md).
Detailed evidence is linked, not repeated. Machine paths are left out; places beside the clone
are named relative to it. Times are UTC. This is the commit C version of the checkpoint. It
records stages S2 and S3 of the MH plan, and the fixed state that holds from S4 to S8. The
declaration version is in this file's history at `16d4f9f4`.

## Identity

- Checkpoint time and author identity: 2026-11-27T04:13:21Z, Director `c271-p35-e38e3aa82ade`.
- Task, session, and agent or tool identity: C271, phase C271-P35-macos-host-qualification-mh;
  the same Claude Code session (model Claude Opus 5.5) that carried out C271-P30 to P34, working
  in the C271 worktree.
- Execution mode, and the entry document or record that declared it: `local`, from current main's
  [LOCAL-START-HERE](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/LOCAL-START-HERE.md),
  read again for this phase; C271's record names local mode since R07.
- Owner direction: on 2026-11-26 the owner was asked "Should I start gate MH, the first gate that
  runs Node?" and typed "Start gate MH" in this session. MH needs no download, and none is
  approved.
- Worktree and branch: `../OntoKin-worktrees/c271`, on `work/c271-missing-import-digest-control`.
- Current user objective and bounded milestone: gate MH of the adopted contract
  `ontokin.current-host-readback/0.2.0` ([phase declaration](../../../engineering/localized-repair-c271/macos-qualification-p35/PHASE.json),
  [MH plan](../../../engineering/localized-repair-c271/macos-qualification-p35/MH-PLAN.md)).
- Task, requirements, and plan paths: [task.json](task.json), [REQUIREMENTS](REQUIREMENTS.md)
  (section P35), [PLAN](PLAN.md) (section P35).

## Context loaded

- Entry file and registry revision: current main `51223c9b94a222f29d38eb6c33808f8e55e2bff9`, whose
  instruction files this branch carries since gate MB.
- Required read-set: the declaration version's list, unchanged. For S2 and S3 the Director also
  read the [N34-M review](../../../engineering/localized-repair-c271/macos-qualification-p35/n34m/N34-M-REVIEW.md),
  the three [tooling reviews](../../../engineering/localized-repair-c271/macos-qualification-p35/reviews/)
  and the author's [notes](../../../engineering/localized-repair-c271/macos-qualification-p35/authoring/TOOLING-AUTHOR-NOTES.md).
- Required files missing, truncated, or inaccessible: none.
- Current/deferred product work and applicable adopted contracts: no product work. P05's
  `ontokin.current-host-readback/0.1.0` and its plans `/0.1.1` to `/0.1.5` stay adopted and
  unchanged. GOAL's ceilings of 100,000 operations and 30,000 ms are unchanged.

## Source

- Starting revision: `c81cf07b5386ea7eba7904f3ef5700709b84b366`, the N34-M records, on top of the
  declaration `16d4f9f4`.
- Dirty and untracked state: before this commit, the worktree was clean, apart from its ignored
  `.venv`. The main checkout's owner items stay untouched.
- Actual remote observation, with command and time: `git ls-remote --heads origin` at
  2026-11-27T04:13:07Z read:
  - this branch at `c81cf07b`;
  - main at `51223c9b`;
  - `work/c271-p29-trd-record` at `880933a4`, which this phase does not touch.
- Active branch/head, open PR, and scope issue: [PR274](https://github.com/Omegapy/OntoKin/pull/274)
  open and draft; [issue273](https://github.com/Omegapy/OntoKin/issues/273) open.

## Work

- Requirements: R01 and R02 done; R03, R04 and R05 not_done. P01 done, P02 in_progress. Task
  status `in_progress`.
- Acceptance items of the declaration:
  - A1 met: the declaration `16d4f9f4`, pushed and read back.
  - A2 met: N34-M accepted with nonmandatory findings N-01 to N-09, recorded at `c81cf07b` before
    any execution plan existed.
  - A3: the tooling has a review without mandatory findings and is in this commit, commit C. It is
    met once this commit is pushed and read back.
    - Review 001 rejected the first version, with five mandatory findings.
    - Review 002 accepted revision 2, with six nonmandatory findings, which are carried to the S6
      freeze.
    - The Director's run of the suite at its committed place then failed one test, whose premise
      held only outside the root (IP-01).
    - Review 003 accepted revision 3, which corrects that test only.
    - At the committed place, revision 3's suite passes 91 of 91.
  - A4 to A10: not started.
- Workers: W1 carried out N34-M. W2 wrote the tooling in three revisions. Each of the three tooling
  reviews was a fresh W3. No worker made a Git write or edited the worktree. The
  [dispositions](../../../engineering/localized-repair-c271/macos-qualification-p35/reviews/)
  record each worker's reported deviations.

## Environment

- Profile and its readiness: as MP left it.
  - N34-M's reviewer computed the installation inventory digest `c277bdd3ac6aa731…`, equal to MP's
    after-snapshot.
  - Every start of the framework interpreter in MH so far carried `-B` or ran with
    `PYTHONDONTWRITEBYTECODE=1`, as the workers' reports and the Director's log record.
  - At 03:22Z no bytecode file newer than the declaration was found in the `.venv` or in the
    interpreter's installation.
  - M0 computes the inventory again.
- Interpreter, operating system and architecture: CPython 3.12.13, macOS 26.6.2 (25G83), arm64;
  the boot session of 2026-11-23, unchanged.
- Node: the pinned runtime beside the clone has never run. Other software installed on this host
  runs Node processes of its own. None descends from a shell of MH, and MH counts its starts by
  audit events and process lineage, never by image name.
- Available operations: Git reads, local commits, non-forced pushes; GitHub API reads and comments.
  No download.

## Verification

- Commands run for this commit (Python always with `-B`):
  - the tooling's suite at its committed place, three times ([disposition 003](../../../engineering/localized-repair-c271/macos-qualification-p35/reviews/TOOLING-REVIEW-DISPOSITION-003.json)):
    - revision 2 failed one test at 03:06Z (IP-01);
    - revision 3 passed 91 of 91 at 03:22Z;
    - revision 3 passed 91 of 91 again from 04:12:12Z to 04:12:26Z, with this commit's other files
      in place, recording its command, working directory and environment;
    - each run left the worktree's status unchanged, wrote no bytecode and left no process;
  - `tools/chat_workflow.py check` and the documentation check
    `docs/maintenance/reorganization-2026-10-17/verify_reorganization.py`, both passed;
  - `git diff --cached --check`, which fails only on the three verbatim test-run records of
    `tooling/tests/`: their 13 trailing spaces are unittest's own output, kept because the reviews
    bind those bytes. Every authored file passes;
  - a search of every file of this commit for private strings derived at run time, directly and in
    each Python file's joined string constants, with no hit apart from the public repository's
    own name;
  - the [check record](../../../engineering/localized-repair-c271/macos-qualification-p35/checks/commit-c/CHECKS.json)
    gives each command and its output.
- Not run in this phase at this checkpoint: M0, M1, the cohort, any Node, `ldd` or `codesign`
  start, the routine driver, and the visual-verification profile.

## Recovery

- Unpublished commits: none after the push of this commit, which the next checkpoint observes.
- Outstanding operations and owned processes: none.
- Current blockers with concrete evidence: none. P30-EXECUTOR-001 still blocks the Linux
  contract's H0 and H1 in local mode.

## Coordination

- Integration owner and lease status: none; main's lease is released and is not used.
- Ownership: owner `c271-p35-e38e3aa82ade` holds this branch for the phase.

## Continuation

- One exact next action: stage S4 of the MH plan. W2 writes the observation plan at this commit,
  outside Git. A fresh W3 reviews it, and the Director takes the plan's digest from the review
  record.
- From the observation plan's freeze to the audit, the MH plan's section 5 holds:
  - one boot;
  - HEAD fixed at this commit;
  - the worktree clean, and no commit;
  - the framework interpreter started only with `-B`.

  A reboot restarts at S4. The plan, HOST, the freeze and the evidence stay beside the clone until
  the audit.
- Stopping condition: the audited cohort pushed and read back with its records, or a concrete
  blocker.

No receipt of the receipt: Git reveals the commit that carries this record.
