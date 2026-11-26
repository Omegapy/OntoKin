# Session checkpoint: C271-P29-R07 local publication

Follows current main's [session template](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/docs/workflow/templates/SESSION.md).
Detailed evidence is linked, not repeated. Machine paths are left out; places beside the clone
are named relative to it. Times are UTC. This is the outcome checkpoint of the phase, corrected
after the fresh-context resumability check and its re-read. The declaration version is
retrievable from commit `80fecf97b785544e8044a60df849cc5918929599`, the first outcome version
from `12d7e55472f8b1d2b67414857ec310b288025244`, and the first correction from
`bb75b1c5f83da34e8cc653b536e635d2e89a62d2`.

## Identity

- Checkpoint time and author identity: 2026-11-26T02:19Z (UTC), the second correction after the
  resumability check's re-read, by Director `c271-p29-r07-e586f7497142`. The first outcome version stated
  02:00Z, later than its own commit time (01:54:49Z); its commit time is the correct one.
- Task, session, and agent or tool identity: C271, phase C271-P29-R07-local-publication; one
  Claude Code session (model Claude Opus 5.5) started in the main checkout.
- Execution mode, and the entry document or record that declared it: `local`, declared by
  current main's [LOCAL-START-HERE](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/LOCAL-START-HERE.md)
  on the owner's direction of 2026-11-25, America/Denver: approval of TRD-20261125-CE424ADD
  revision 2 and of PLAN-20261126-F3122BB2, and the instruction "execute PLAN-20261126-F3122BB2".
  The mode is recorded in [task.json](task.json) (`execution_mode`, `execution_mode_record`) and in
  the [phase declaration](../../../engineering/localized-repair-c271/p29-local-publication-r07/PHASE.json).
- Worktree and branch: `../OntoKin-worktrees/c271` beside the clone, on
  `work/c271-missing-import-digest-control`, tracking origin.
- Current user objective and bounded milestone: exact publication of the accepted P29 candidate,
  independently reviewed and read back from the remote. This milestone is reached; the phase stops
  at this verified publication checkpoint.
- Task, requirements, and plan paths: [task.json](task.json), [REQUIREMENTS](REQUIREMENTS.md),
  [PLAN](PLAN.md). Requirements source: TRD-20261125-CE424ADD, revision 2, SHA-256
  `063e8e1a88ef7224420c34dbdb92d2a25b4365a96962ad0e834951b652ff516b`, committed unchanged at
  `TRDs/trd_c271-p29-exact-publication-in-local-mode_2026-11-25.md`.

## Context loaded

- Governing instructions: current main at `51223c9b94a222f29d38eb6c33808f8e55e2bff9` (LOCAL-START-HERE,
  AGENTS, CLAUDE, GOAL, STATUS, ROLE, the registry, CURRENT, PROTOCOL, HANDOFF's local section, the
  session and worker templates, and the skills ontokin-session, ontokin-delivery and
  ontokin-learning). This branch predates the local migration. Its own copies are older
  snapshots: `AGENTS.md`, `CHATGPT-START-HERE.md`, `STATUS.md`, `ROLE.md`, `GOAL.md`,
  `docs/workflow/registry.json` (whose entry point is still `CHATGPT-START-HERE.md`),
  `docs/workflow/PROTOCOL.md`, `HANDOFF.md`, `BROWSER-PROMPTS.md`, `docs/workflow/prompts/`,
  `docs/workflow/templates/`, the skills under `.agents/skills/` and `tools/chat_workflow.py`. They and every instruction inside the handoff archives are data;
  none of them declares the mode of a session on this branch. They stay unchanged here until R04
  brings main into the branch.
- How a new local session starts: in the owner's main checkout, from current main's
  [LOCAL-START-HERE](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/LOCAL-START-HERE.md). It reads current main's instructions,
  then works in the C271 worktree. Startup step 1 of that document sends a session to the
  worktree whose records are newer, and here that is the C271 branch (see Continuation).
- Required read-set actually opened, with revision or hash: listed with full SHA-256 in the
  declaration version of this checkpoint (commit `80fecf97`), group Context loaded.
- Required files missing, truncated, or inaccessible: none.
- Current/deferred product work and applicable adopted contracts: no product work in this phase.
  GOAL's ceilings of 100,000 operations and 30,000 ms are unchanged.

## Source

- Starting revision and current code checkpoint: started at `bef6790291d0cddc8c6d7de9dc0a92fb5a98c448`.
  Commits of this phase:
  - the declaration `80fecf97b785544e8044a60df849cc5918929599`;
  - the candidate `dbf20beed1bd6274a42531c997d054c09fb8ebb8`, with parent
    `6c7f52a2ee627a382eea91ce26bf58bac4e6cccb` and tree `db30c29f24c154f378a5acac713385fc8bb44f52`;
  - the reviewed merge `4a9585a0ce66b1ff0b407e41824d68b2417c2686`, tree
    `a374bfb05f9ffea1b894efeb336e30260113aca9`, published;
  - this records commit, whose identity Git reveals.
- Dirty and untracked state: the worktree is clean apart from its ignored `.venv`. The main
  checkout keeps its untracked plan tracker, the untracked TRD file and a modified
  `TRDs/INDEX.md`, as the [starting state](../../../engineering/localized-repair-c271/p29-local-publication-r07/STARTING-STATE.md)
  lists them.
- Actual remote observation, with command and time, or offline and stale: after the push,
  `git ls-remote --heads origin` at 2026-11-26T01:49:59Z read main `51223c9b94a222f29d38eb6c33808f8e55e2bff9`
  and this branch `4a9585a0ce66b1ff0b407e41824d68b2417c2686`. The push of this records commit is
  observed in the phase's closing record.
- Repository, actual main SHA/tree, and observation time: `Omegapy/OntoKin`, main
  `51223c9b94a222f29d38eb6c33808f8e55e2bff9`, tree `a92e46b353d0697483fd5154814c00946be73e8b`,
  unchanged throughout the phase.
- Active branch/head, open PR, and scope issue: `work/c271-missing-import-digest-control`;
  [PR274](https://github.com/Omegapy/OntoKin/pull/274) open, draft, unmerged and conflicting with
  main; [issue273](https://github.com/Omegapy/OntoKin/issues/273) open.
- Local checkout identity and unpublished changes, if a workspace exists: the C271 worktree. The
  candidate commit is also kept by the local ref `refs/ontokin/c271-p29-r07/candidate`; it is
  published as the merge's second parent.

## Work

- Requirements completed, incomplete, blocked, and excluded: R01 and R02 done; R03, R04 and R05
  not_done. P01 done, P02 in_progress. The publication gate is complete. The other open gates are
  listed under Continuation. Excluded: the TRD's out-of-scope list.
- Completed acceptance items and last completed gate: the exact publication of the accepted P29
  candidate (TRD acceptance A1 to A6), and the records of A7.
  [Publication record](../../../engineering/localized-repair-c271/p29-local-publication-r07/PUBLICATION.json).
  P29-PUBLICATION-SIZE-001 is resolved **as a transfer gate only**: only the transfer route
  changed, the evidence is unchanged, and no host is qualified.
- Changed artifact paths and exact code/input identities:
  - 240 added accepted files under `docs/engineering/localized-repair-c271/required-images-p29/`
    and `tests/test_current_host_required_images_v01.py`;
  - the accepted `prototypes/static_tray_v01/current_host_inspection_v01.py`;
  - the four reconciled workflow records ([reconciliation](../../../engineering/localized-repair-c271/p29-local-publication-r07/RECORD-RECONCILIATION.md));
  - this phase's records under `docs/engineering/localized-repair-c271/p29-local-publication-r07/`;
  - this checkpoint and the TRD file.

  The evidence archive is the ordinary blob `9facb186ec11523163520323d83dc58fd68e829c`: 25,817,783
  bytes, SHA-256 `bae1b62fd3cc78e8cb886e08c4c2f7d76eaaf765e7f6374a394d5f0aa980d038`.
- Decisions made: those of the approved plan, DEC-002 to DEC-013; no deviation from them.
- Remaining items in this phase: the closing record, the checkpoint comments on PR274 and
  issue273, and the final report.
- Learning checkpoint result and capture preference: assessed under ontokin-learning. One
  supported lesson: an error from a text-only reader does not establish that an object is absent.
  All 43 candidate blobs recorded as "existence unknown" after UTF-8-only read errors were present
  when read through the binary-capable Git database endpoint
  ([destination inspection](../../../engineering/localized-repair-c271/p29-local-publication-r07/DESTINATION-INSPECTION.json)).
  It is not captured in `docs/workflow/memory.json` in this phase, because that file is one of the
  six in conflict with main (see below) and this phase's plan changes no memory record. The lesson
  is left for capture at or after the R04 integration.

## Environment

- Profile and its readiness: in the main checkout, `core` and `python-verification` ready and
  `visual-verification` mismatched (Node.js 25.9.0; the target is 22). The C271 worktree has no
  environment specification, so the doctor cannot diagnose it.
- Interpreter, operating system and architecture: CPython 3.12.13 (Homebrew), macOS 26.6.2,
  arm64.
- Manifest and lock identities: current main's `tools/local-environment.json`, SHA-256
  `c70b9d43634f9a35170e4ac633a6e352e7a986a6fb8ab10639fa60a9c776f9b4`. The worktree's `.venv` was
  created with `venv --without-pip` and holds no package.
- Relevant tool versions: Git 2.50.1 and Git LFS 3.7.1 (no LFS rule matches the candidate); the
  GitHub CLI is authenticated with repository scope.
- Terminal and executed interpreter/platform: zsh. The worktree's `.venv/bin/python` ran this
  branch's checks; the main checkout's `.venv/bin/python` ran the doctor and main's workflow check.
- Available read/write/conditional-update/merge operations: Git reads and non-forced pushes over
  the owner's SSH remote (observed twice), GitHub API reads, and local commits. No merge into main.
- Missing capabilities and their effect on this milestone: none. The owner's downloads-folder copy
  of the R06 archive could not be read (macOS folder access was not granted). The copy beside the
  clone, with the recorded identities, was used.
- Test and environment facts that stay visible and unchanged (REQ-032), recorded on main in
  [STATUS](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/STATUS.md#verification-and-remaining-limits)
  and in the migration's [RESULTS](https://github.com/Omegapy/OntoKin/blob/51223c9b94a222f29d38eb6c33808f8e55e2bff9/docs/engineering/local-migration-20261124/RESULTS.md):
  - local readiness on macOS arm64 with CPython 3.12.13 is separate from the historical Linux
    x86-64 CPython 3.12.14 qualification contract;
  - the routine run on the resulting main is still recorded as failed (4,989 unit tests: one not
    passing and three skipped with a resolved temporary directory; 307 distinct tests not passing
    with the default one);
  - 16 external cases are pending, and the visual profile is not prepared;
  - `--full`, `--force-agent`, Linux validation and hosted CI were not run.

  This phase neither changes nor qualifies any of them.

## Verification

- Commands actually executed and observed outcomes:
  - the [baseline](../../../engineering/localized-repair-c271/p29-local-publication-r07/CHECKS-BASELINE.json)
    and the [checks of the reconciled merge](../../../engineering/localized-repair-c271/p29-local-publication-r07/CHECKS.json):
    this branch's workflow check, documentation verifier and scoped whitespace check passed twice
    at `4a9585a0`;
  - the [archive verification](../../../engineering/localized-repair-c271/p29-local-publication-r07/ARCHIVE-VERIFICATION.json):
    16 of 16 checks passed;
  - the [staging verification](../../../engineering/localized-repair-c271/p29-local-publication-r07/STAGING-VERIFICATION.json):
    245 of 245 files passed;
  - the [candidate commit](../../../engineering/localized-repair-c271/p29-local-publication-r07/CANDIDATE-COMMIT.json)
    reproduced tree `db30c29f`;
  - the [independent review](../../../engineering/localized-repair-c271/p29-local-publication-r07/REVIEW.md)
    accepted `4a9585a0`, with no mandatory finding;
  - the readback in a separate repository without alternates verified the published head, both
    boundaries and the evidence blob ([publication record](../../../engineering/localized-repair-c271/p29-local-publication-r07/PUBLICATION.json)).
- Failures: none in a required check. The informational full whitespace pass reports 37 findings
  inside accepted candidate files; they are identical to the candidate's own recorded check, and
  the accepted bytes are not changed. One inaccurate statement in the declaration records about the
  reachability of four present blobs is corrected in the publication record (review finding O-01).
- Pending and not-run checks: the routine driver, the unit suite, the candidate's inherited tests,
  H0, H1, behavioural reruns and native loader execution are excluded from this phase and belong to
  later gates. No hosted run was started.
- Durable logs, review findings, and evidence links: the phase records above. Raw logs, scripts,
  the staging directory and the readback repository are kept in `../OntoKin-local/c271-p29-r07/`
  beside the clone.
- Evidence locations and hashes: in the phase records.
- Relevant validation/CI results and source revisions: workflows are manual-only; none ran.
- Current review eligibility and any changes since review: the published head is the reviewed
  head `4a9585a0`. Later commits change records only.

## Recovery

- Unpublished commits: none after the push of this records commit, which the closing record
  observes.
- Unique uncommitted files: none in the worktree. The main checkout's items stay in place.
- Outstanding operations and owned processes: none.
- Unknown operation and its intended parent/tree/commit or request identity: none in this phase.
  The historical unknown operations stay as the R02 phase record lists them; none was replayed.
- Remote readback needed before retrying that operation: not applicable.
- Current blockers with concrete evidence: none for C271's next step.
- Unpublished work that must be recovered and its known location: none.
- Actual unpublished recovery payloads and declared external dependencies: none. The R06 handoff
  stays in the owner's Library and beside the clone. This local phase produces no handoff ZIP.
- Superseded values kept where they stand: they are listed in the field
  `p29_r07_superseded_fields_index` of [task.json](task.json) and of the branch `CURRENT.json`.
  - `delivery`, `pending_phase_delivery` and `latest_handoff` are R02's source-time delivery
    records, resolved by its terminal comment. The R03 to R06 handoffs are named in
    `p29_recovery_records_r03_r06`.
  - `authorization` is P01's browser-era authorization.
  - `PHASE.json` of this phase is the declaration record; the outcome is in `PUBLICATION.json`.
  - R02's `PUBLICATION-BLOCKER.json` keeps its source-time status `blocked`; the blocker is
    resolved in `blocked_reason_history`.
  - `remaining_h0_constraint` is P26's record, discussed under Continuation.

  None of these values is rewritten. The index names the fields that hold the current state and
  the rule for the rest: a field named for an earlier phase (`p25_`, `p26_`, `p27_`, `p28_`,
  `p29_r02_`, `p29_publication_recovery_r02`, `prior_`, `previous_`, `older_`) or ending in
  `_history` is that phase's source-time record.

## Coordination

- Active workers and reserved files: none.
- Actual subagents, assigned scopes, and unresolved worker activity: the independent reviewer
  (fresh-context subagent, finished) and the resumability worker of the closing record. Neither
  wrote to the repository.
- Integration owner, expiry, and latest verified ownership record: none. Main's lease is released
  and was not used by this phase.
- Lease status: released (main STATUS).
- Ownership released, renewed, transferred, or still uncertain: owner `c271-p29-r07-e586f7497142`
  is released once the phase's closing record is on the remote and the matching checkpoint
  comments are on PR274 and issue273. It makes no write after them.

## Continuation

- One exact next action, inputs, acceptance gate, and stopping condition: the review of the
  `/0.1.5` operational plan against the published P29 candidate and current host facts, as a
  separate phase in its own session. It has not begun.
  - It requires a concrete reason for any further preparation work.
  - It assesses whether an existing executor meets the adopted contract before more host tooling
    is built.
  - It makes any executor substitution explicit and keeps the original test meaning.
  - It reads the original qualification plan and its later adopted supplements before any
    execution.
- Inputs of that review, all in this commit:
  - the published candidate under `docs/engineering/localized-repair-c271/required-images-p29/`:
    [SUMMARY](../../../engineering/localized-repair-c271/required-images-p29/SUMMARY.md), which defines `/0.1.5`,
    [VERIFICATION](../../../engineering/localized-repair-c271/required-images-p29/VERIFICATION.json) and
    [RECONSTRUCTION-DECISION](../../../engineering/localized-repair-c271/required-images-p29/RECONSTRUCTION-DECISION.md);
  - the staged qualification plan of P07:
    [QUALIFICATION-PLAN](../../../engineering/localized-repair-c271/host-inspection-p07/QUALIFICATION-PLAN.md), with its JSON,
    stages H0 to H3;
  - the later adopted designs that refine that plan, which the review reads as its adopted
    supplements and checks where they differ from it: the P05
    [current-host design](../../../engineering/localized-repair-c271/current-host-p05/ADOPTION.json), the P11
    [loader-path decision](../../../engineering/localized-repair-c271/loader-path-p11/ADOPTION.json), the P13
    [review boundary](../../../engineering/localized-repair-c271/review-boundary-p13/ADOPTION.json), which makes actual-loader
    suffix completeness (N34) an external independent-review prerequisite for adopting or executing
    an operational plan, the P16
    [tag decision](../../../engineering/localized-repair-c271/libc-tags-p16/ADOPTION.json), the P17
    [flags decision](../../../engineering/localized-repair-c271/libc-flags-p17/ADOPTION.json), the P24
    [path design](../../../engineering/localized-repair-c271/path-design-p24/ADOPTION.json) and the P27
    [required-image design](../../../engineering/localized-repair-c271/required-image-design-p27/ADOPTION.json);
  - the unchanged C260 [contract](../../../engineering/localized-repair-c260/CONTRACT.md) and
    [control plan](../../../engineering/localized-repair-c260/CONTROL-PLAN.md);
  - the H0 plan records `h0-plan-p21/`, `h0-plan-p23/` and `h0-plan-p26/`.
- Wording: the next action stated in task.json and CURRENT.json is current. The candidate's
  earlier wording of the same step, in `p29_reconstruction.next_technical_action` and in the P29
  summary ("prepare and independently review the executable /0.1.5 inspection plan ... stopping at
  any new blocker before H0/H1 execution"), stays as its source-time text. Whether preparing an
  executable plan is in scope is for that review to decide, and it needs a concrete reason for any
  further preparation.
- Questions the review has to settle, which this phase did not decide:
  - `remaining_h0_constraint` in task.json is P26's record. Its `selected_implementation` is the
    P25 inspector (233,502 bytes, SHA-256 `eea3e634...`), while the published P29 inspector is
    249,393 bytes, SHA-256 `71e837c31df06df7ce10262683c5d28a72bdb3c039f09b97eec58839f4121758`
    (`p29_implementation_candidate`). Its `next_phase_action` predates P27 and P29, and its
    `source_inventory` path lies on a disposable host.
  - No local executor meets the historical Linux x86-64 CPython 3.12.14 contract: the local host
    is macOS arm64 with CPython 3.12.13, and the container profile is unsupported. Whether an
    existing executor meets the adopted contract is the review's first question.
- Open gates after it, each a separate phase:
  - H0, with its open items as `remaining_h0_constraint.remaining_gates` lists them: complete
    author, runtime, metadata, alias, guard and loader closure; N34 actual loader and script source
    completeness; the historical N57 obligation; and independent acceptance and execution of the
    H0 plan;
  - H1 and the later qualification stages;
  - the required regression with independent integration review (R03);
  - reviewed integration with actual-main verification (R04);
  - parent completion with final delivery (R05). The files that
  main and this branch both changed are documented for R04 in
  [MAIN-CONFLICTS](../../../engineering/localized-repair-c271/p29-local-publication-r07/MAIN-CONFLICTS.md).
- The condition that makes that action safe and useful to execute: an explicit owner selection of
  that phase; the branch head read from the remote equal to, or descended from, the commit that
  adds this phase's closing record
  `docs/engineering/localized-repair-c271/p29-local-publication-r07/RESUMABILITY.md` (Git reveals
  it, and the checkpoint comments on PR274 and issue273 name it); no other writer on this branch.
- Where a session that starts from main finds C271: main's `STATUS.md` and `CURRENT.json` still
  describe C271 as observed on 2026-11-25 (browser mode, head `bef67902`, publication gate open).
  This phase does not write main, so those entries stay dated observations until R04 or a
  separately authorized update of main. The current state is on this branch.
- The decisions of the approved plan that governed this phase are copied unchanged in
  [PLAN-DECISIONS](../../../engineering/localized-repair-c271/p29-local-publication-r07/PLAN-DECISIONS.md).
- This phase's closing record (`PUSH-OBSERVATION.json`, `RESUMABILITY.md`, `AUDIT.md`) and the
  checkpoint comments on PR274 and issue273 follow this commit.

## Delivery

- Local checkpoint status: the records commit that carries this checkpoint, followed by one small
  closing record.
- Verified push state, or unconfirmed: the reviewed merge was read back from the remote. The push
  of this commit is observed by the closing record, and the push of the closing record by the final
  report.
- Actual merge/resulting-main checks, or remaining integration gate: R04, a later phase. Main is
  unchanged.
- Branch retention/deletion evidence, or exact pending cleanup instruction: the branch is retained
  for unfinished C271. The worktree, the staging directory and the readback repository stay in
  place.
- Durable evidence references: the phase records named above.
- Integration state separate from saved-delivery state: not integrated. In local mode no Library
  save is required for this phase ([delivery reconciliation](../../../engineering/localized-repair-c271/p29-local-publication-r07/DELIVERY-RECONCILIATION.md)).
- Published checkpoint revision and readback result: `4a9585a0ce66b1ff0b407e41824d68b2417c2686`,
  read back from a separate repository on 2026-11-26T01:50Z (UTC); result passed.

No receipt of the receipt: Git reveals the commit that carries this record.
