# Session checkpoint: C271-P29-R07 local publication

Follows current main's [session template](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/docs/workflow/templates/SESSION.md).
Detailed evidence is linked, not repeated. Machine paths are left out; places beside the clone
are named relative to it. This version is the declaration checkpoint, written before the
candidate is committed; the records commit of this phase updates it with the outcome.

## Identity

- Checkpoint time and author identity: 2026-11-26T01:00Z, Director `c271-p29-r07-e586f7497142`.
- Task, session, and agent or tool identity: C271, phase C271-P29-R07-local-publication; one
  Claude Code session (model Claude Opus 5.5) started in the main checkout.
- Execution mode, and the entry document or record that declared it: `local`, declared by
  current main's [LOCAL-START-HERE](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/LOCAL-START-HERE.md)
  on the owner's direction of 2026-11-25 (approval of TRD-20261125-CE424ADD revision 2 and of
  PLAN-20261126-F3122BB2, and the instruction "execute PLAN-20261126-F3122BB2"); recorded in
  [task.json](task.json) and the [phase declaration](../../../engineering/localized-repair-c271/p29-local-publication-r07/PHASE.json).
- Worktree and branch: `../OntoKin-worktrees/c271` beside the clone, on
  `work/c271-missing-import-digest-control`, tracking origin.
- Current user objective and bounded milestone: exact publication of the accepted P29
  candidate on this branch, independently reviewed and read back from the remote; stop at that
  verified publication checkpoint.
- Task, requirements, and plan paths: [task.json](task.json), [REQUIREMENTS](REQUIREMENTS.md),
  [PLAN](PLAN.md); requirements source TRD-20261125-CE424ADD, revision 2, SHA-256
  `063e8e1a88ef7224420c34dbdb92d2a25b4365a96962ad0e834951b652ff516b`, committed unchanged at
  `TRDs/trd_c271-p29-exact-publication-in-local-mode_2026-11-25.md`.

## Context loaded

- Entry file and registry revision: current main `51223c9b94a222f29d38eb6c33808f8e55e2bff9`;
  LOCAL-START-HERE SHA-256 `96b5af2f5382692763049440f606c4124aad353d78c0de6bea517780fea8f830`,
  registry `750e17e1cf71620cc42f559cbae6a38154af0d5e8142505946f67578c88e9ff9`.
- Required read-set actually opened, with revision or hash: the files below, the approved TRD
  (SHA-256 above) and, on GitHub, the R06 terminal record, comment 7136207682 on PR274, with
  its identical issue273 copy 7136203591.

  | Revision | File | SHA-256 |
  | --- | --- | --- |
  | main `51223c9b` | `LOCAL-START-HERE.md` | `96b5af2f5382692763049440f606c4124aad353d78c0de6bea517780fea8f830` |
  | main `51223c9b` | `AGENTS.md` | `c2783b51b8c33db6f06bf56112cad141521af2c779580750264ff138783c9c87` |
  | main `51223c9b` | `CLAUDE.md` | `b0d99d2ffc41749e03de12afa1933e7def68f8b47fa5acc4b0c82409e4da368b` |
  | main `51223c9b` | `GOAL.md` | `0a978bd65d03b76a6fb0009b95fbd04557b73cd8f800ca5ef2ec58d92c3d6b65` |
  | main `51223c9b` | `STATUS.md` | `5aae6b1cb8711c249d9bcf86da7536ccda3997e359c36362416e85df4ce1baad` |
  | main `51223c9b` | `ROLE.md` | `818fff3bf7fac9cde2235c7ef6aaf550dde60ad86a11c3059c7ec168d0eaedaf` |
  | main `51223c9b` | `docs/workflow/registry.json` | `750e17e1cf71620cc42f559cbae6a38154af0d5e8142505946f67578c88e9ff9` |
  | main `51223c9b` | `docs/workflow/CURRENT.json` | `d997c3f64453f4cc9c1e6269f31af47cafd8389dfb1c40844ee3a33041fa3069` |
  | main `51223c9b` | `docs/workflow/PROTOCOL.md` | `57e5e46ca86242292a8d9955d854ae66b1c3caf542698c90fcb1fe9828c4d6fb` |
  | main `51223c9b` | `docs/workflow/HANDOFF.md` | `699a67e52970b564ccc8680e36c8dd7bdd4536ef5deadf276bf64cba77d65dad` |
  | main `51223c9b` | `docs/workflow/templates/SESSION.md` | `1d4948964837ed9f2e14157b36d367da13b2f897ab53108cc6efb6fbe6c1bcfd` |
  | main `51223c9b` | `docs/workflow/templates/WORKER.md` | `47068e4ca8372629ead0c0e1d25ea6de009e027f4497f3765711c391779debc8` |
  | main `51223c9b` | `.agents/skills/ontokin-session/SKILL.md` | `dbc36dab6b08f8d82e83daebbb324b69d3a23174279b5f6e4257eaf5d31fa757` |
  | main `51223c9b` | `.agents/skills/ontokin-delivery/SKILL.md` | `3b6641f56d13a251ea807ec8bf39c8b231f848dc4e71dd29829ea8f344897c84` |
  | main `51223c9b` | `.agents/skills/ontokin-learning/SKILL.md` | `3e16354300c3002c8b5f895877a3b520bba0b1b2a6d44d20632127e0197b31de` |
  | main `51223c9b` | `docs/development/LOCAL-SETUP.md` | `289f1b18b7ad64a105b3ce3caecb71200a5dc8383bfc59315dd76faa57af2e2c` |
  | main `51223c9b` | `docs/engineering/local-migration-20261124/DECISION.md` | `b874ff5637ff904d13c71d61f934f8e26a3a377af3490eecf482eee958ab3a86` |
  | main `51223c9b` | `docs/engineering/local-migration-20261124/RECONCILIATION.md` | `63be603485d22bcf5709922ff894853a562fb0a675b62bdae7c2a25c80b4623f` |
  | main `51223c9b` | `docs/engineering/local-migration-20261124/R06-VERIFICATION.json` | `93cebb646669a01063b6f09c202f26a2b5c2ec073b570e9be7bfc3c3fbaafa3a` |
  | main `51223c9b` | `docs/workflow/tasks/LOCAL-MIGRATION-20261124/SESSION.md` | `9a2b132f78ffe6372968ec05b3bdbb61102f2ab2873a7b318345f9c54e6d1b74` |
  | c271 `bef67902` | `docs/workflow/tasks/C271/REQUIREMENTS.md` | `eec4c9023658f84f02b108d0584100861eb9addb1d667033f3040b8c1ddcf1b5` |
  | c271 `bef67902` | `docs/workflow/tasks/C271/PLAN.md` | `7b5bfc90eb71376ca327d9fedcef74291c654529f061065e00f716bf1f31b29d` |
  | c271 `bef67902` | `docs/workflow/tasks/C271/task.json` | `06aa614e893812c89ed86065c492fa48f2193ec1511c4ee6fb23977b1c664914` |
  | c271 `bef67902` | `docs/workflow/tasks/C271/SESSION.md` | `6531fced54428c39937363facc8aed2ec73408e8d847d4620a3fa119944f1582` |
  | c271 `bef67902` | `docs/workflow/CURRENT.json` | `46024c296602ecad251573fca0cf23b461d015f74d8743db5e80476abffc1a34` |
  | c271 `bef67902` | `docs/engineering/localized-repair-c271/p29-publication-recovery-r02-20261123/NEXT-ACTION.md` | `e6f30a020a62cd7318cdc98153601b4650b6fb3373be393fe90578b29b5cec75` |
  | c271 `bef67902` | `docs/engineering/localized-repair-c271/p29-publication-recovery-r02-20261123/PUBLICATION-BLOCKER.json` | `1dced0836e2c17462ef114251d08aa7c9ada509c9a4daf74228bc3db538056e0` |
  | c271 `bef67902` | `docs/engineering/localized-repair-c271/p29-publication-recovery-r02-20261123/SUMMARY.md` | `35a3691b50c6d8d89407c7c7a2d4e3c8ccf13fb194bff8050249db6d4814d9ed` |
  | c271 `bef67902` | `docs/engineering/localized-repair-c271/p29-publication-recovery-r02-20261123/PHASE.json` | `b726e5374e44676837aad62d9b39d57b8821fe770954eb13be942f034dbbd86b` |
  | c271 `bef67902` | `docs/engineering/localized-repair-c271/p29-publication-recovery-r02-20261123/REMOTE-BLOB-DISPOSITION.json` | `d45b995554eb61f7634b673384f4b9b12a68b557745dbdaf4f02ce8669cf2dcf` |
  | c271 `bef67902` | `AGENTS.md` | `ce0fef82308e1c329dcf0514c99e81e89c340bbb550cf0cdcdb589599ae42822` |

- Required files missing, truncated, or inaccessible: none.
- Current/deferred product work and applicable adopted contracts: no product work. Current
  main's instructions govern; this branch's earlier AGENTS, PROTOCOL and HANDOFF and the
  handoff archives' instructions are data. GOAL's ceilings of 100,000 operations and 30,000 ms
  stay unchanged.

## Source

- Starting revision and current code checkpoint: branch head `bef6790291d0cddc8c6d7de9dc0a92fb5a98c448`;
  this record is carried by the declaration commit, whose identity Git reveals.
- Dirty and untracked state: the worktree was clean before this commit; its `.venv` is ignored.
  The main checkout keeps its untracked plan tracker, the untracked TRD file and a modified
  `TRDs/INDEX.md` (listed in the starting state).
- Actual remote observation, with command and time, or offline and stale: `git ls-remote --heads origin`
  at 2026-11-26T00:51:10Z: main `51223c9b94a222f29d38eb6c33808f8e55e2bff9`, this branch
  `bef6790291d0cddc8c6d7de9dc0a92fb5a98c448`; no other head.
- Repository, actual main SHA/tree, and observation time: `Omegapy/OntoKin`, main
  `51223c9b94a222f29d38eb6c33808f8e55e2bff9`, tree `a92e46b353d0697483fd5154814c00946be73e8b`,
  2026-11-26T00:46Z.
- Active branch/head, open PR, and scope issue: `work/c271-missing-import-digest-control`;
  [PR274](https://github.com/Omegapy/OntoKin/pull/274) open, draft, unmerged, conflicting with
  main; [issue273](https://github.com/Omegapy/OntoKin/issues/273) open.
- Local checkout identity and unpublished changes, if a workspace exists: the C271 worktree; no
  unpublished commit before the declaration commit.

## Work

- Requirements completed, incomplete, blocked, and excluded: R01 and R02 done; R03, R04 and R05
  not_done. P01 done, P02 in_progress. The TRD's REQ-001 to REQ-034 govern this phase; none is
  met yet beyond the declaration. Excluded: the TRD's out-of-scope list.
- Completed acceptance items and last completed gate: starting state, destination inspection
  and baseline checks recorded; phase declared.
- Changed artifact paths and exact code/input identities: the declaration commit adds the phase
  records, this checkpoint and the TRD file, and adds dated entries to task.json,
  REQUIREMENTS.md, PLAN.md and the branch CURRENT.json. No accepted byte is committed yet.
- Decisions made: phase name, record locations, worktree, executor, checks, reconciliation
  rules and readback form as the approved plan decided them; see the phase declaration.
- Remaining items: authenticate and stage the candidate, candidate commit, conflicts record,
  record reconciliation, merge commit, checks, independent review, push, readback, records,
  resumability evidence, audit, closing record, PR and issue comments, final report.
- Learning checkpoint result and capture preference: not yet assessed; assessed before closing.

## Environment

- Profile and its readiness: in the main checkout, `core` and `python-verification` ready,
  `visual-verification` mismatch (Node.js 25.9.0, target 22). The C271 worktree has no
  environment specification, so the doctor cannot diagnose it.
- Interpreter, operating system and architecture: CPython 3.12.13 (Homebrew), macOS 26.6.2,
  arm64.
- Manifest and lock identities: current main's `tools/local-environment.json` SHA-256
  `c70b9d43634f9a35170e4ac633a6e352e7a986a6fb8ab10639fa60a9c776f9b4`; the worktree's `.venv`
  was created with `venv --without-pip` and holds no package.
- Relevant tool versions: Git 2.50.1, Git LFS 3.7.1 (no LFS rule matches the candidate),
  GitHub CLI authenticated with repository scope.
- Terminal and executed interpreter/platform: zsh; the worktree's `.venv/bin/python` for this
  branch's checks, the main checkout's `.venv/bin/python` for the doctor and main's workflow
  check.
- Available read/write/conditional-update/merge operations: Git reads and fetches over the
  owner's SSH remote; GitHub API reads; local commits. Write access over SSH is first observed
  by the declaration push.
- Missing capabilities and their effect on this milestone: none known.

## Verification

- Commands actually executed and observed outcomes: [baseline](../../../engineering/localized-repair-c271/p29-local-publication-r07/CHECKS-BASELINE.json):
  doctor and main's workflow check passed in the main checkout; this branch's workflow check
  and documentation verifier passed at `bef67902`.
- Failures: none so far.
- Pending and not-run checks: the checks of the declaration tree and of later commits; the
  routine driver, the unit suite, H0, H1 and behavioral reruns are excluded from this phase.
- Durable logs, review findings, and evidence links: phase records under
  `docs/engineering/localized-repair-c271/p29-local-publication-r07/`; raw logs in
  `../OntoKin-local/c271-p29-r07/` beside the clone.
- Evidence locations and hashes: in the phase records.
- Relevant validation/CI results and source revisions: no hosted run is requested; the
  workflows are manual-only.
- Current review eligibility and any changes since review: no candidate exists yet.

## Recovery

- Unpublished commits: none before the declaration commit.
- Unique uncommitted files: none in the worktree; the main checkout's items stay in place.
- Outstanding operations and owned processes: none.
- Unknown operation and its intended parent/tree/commit or request identity: none in this
  phase. Historical unknown operations stay as the R02 phase lists them; none is replayed.
- Remote readback needed before retrying that operation: before any push, read
  `git ls-remote --heads origin` and require that the pushed head descends from the observed
  remote head.
- Current blockers with concrete evidence: P29-PUBLICATION-SIZE-001 remains open until the
  readback succeeds.
- Unpublished work that must be recovered and its known location: none; the accepted bytes are
  in the R06 archive beside the clone and in the owner's Library.
- Actual unpublished recovery payloads and declared external dependencies: the R06 archive
  (41,730,084 bytes, SHA-256 `4b8fae8b846c6f2b27ed5e2630c71240739786791cf39f043e787c55ad727bc9`)
  and its receipt (149,563 bytes, SHA-256 `24aa014cb430d9b7269ee2e39ff08e7005d3630e8dd41c109f824e80039909d8`).

## Coordination

- Active workers and reserved files: none besides the Director.
- Actual subagents, assigned scopes, and unresolved worker activity: none yet; the independent
  reviewer and the resumability worker are assigned later.
- Integration owner, expiry, and latest verified ownership record: none; main's lease is
  released and not used by this phase.
- Lease status: released (main STATUS).
- Ownership released, renewed, transferred, or still uncertain: this phase is owned by
  `c271-p29-r07-e586f7497142`; the last recorded owner, `c271-p29-r06-ed94fcf35220` (R06), is
  released by its identical terminal comments on PR274 and issue273.

## Continuation

- One exact next action, inputs, acceptance gate, and stopping condition: continue this phase
  at its first unmet step after the declaration: verify the R06 archive chain and the 245-row
  inventory in memory, stage the accepted files outside every checkout, then build the
  candidate commit; stop at the verified publication checkpoint.
- The condition that makes that action safe and useful to execute: the declaration commit is on
  the remote, the R06 archive and receipt have their recorded identities, and no other writer
  holds this branch.

## Delivery

- Local checkpoint status: the declaration commit.
- Verified push state, or unconfirmed: read from the remote after the push; recorded in the
  later phase records.
- Actual merge/resulting-main checks, or remaining integration gate: R04, a later phase.
- Branch retention/deletion evidence, or exact pending cleanup instruction: the branch is
  retained for unfinished C271.
- Durable evidence references: the phase records named above.
- Integration state separate from saved-delivery state: not integrated; in local mode no
  Library save is required for this phase.
- Published checkpoint revision and readback result: pending.

No receipt of the receipt: Git reveals the commit that carries this record.
