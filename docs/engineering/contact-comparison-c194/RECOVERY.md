# C194 interrupted-session recovery

## Reconciled starting state

The C193 handoff was recovered from its saved copy after its attachment failed
to mount. All 704 manifest entries passed exact size and SHA-256 verification.
The complete source restored offline at
`3c9fcaa4daff7b32e7b813ba05041212c1a5bc2f`, matching observed GitHub main.
C193 PR #126 was already merged. No open PR, active integration lease, queued
workflow or published C194 branch was observed at recovery start.

The previous local workspace remained available. Its original coordinator head
`fae25ca94d882a67f9fd5d352e1923035b96fe6b` retained fifteen C194 commits,
including both authors' first and reuse submissions. The authors' original heads
are `9031edddc48db12891a3504e31894da5770d75e7` and
`ae7b4f2da85873afbc154449b97f8231a698ef51`. Both author worktrees were clean.
The coordinator had only an untracked reuse-input manifest and proposed next
task. Both were copied without modification into the resumed checkout.

No process using the old workspace or Git write lock was observed. The old
workspace was left unchanged. Its branches and raw Git objects were copied to
a separate checkout, and the same integration scope was resumed. These process
checks are bounded observations, not proof about every possible external agent.
[Remote and local recovery evidence](evidence/recovery/LOCAL-RECOVERY.json)

## What had completed before the interruption

The fixed preparation matrix qualified both 365 and 375 mm targets with the
reserved four builds. The public comparison was frozen after qualification.
Exactly two fresh default authors then submitted their first edits, which were
independently accepted before reuse was dispatched. The same authors completed
their later variants and exact first-result regenerations. Automated reuse
validation finished successfully at 22:29:26 UTC on November 10, 2026.

The original reuse result still said `visual_review: PENDING`. It did not yet
have a visual receipt or explicit phase acceptance. Final result documentation,
integration and a complete C194 handoff were also unfinished. The original
records retain those historical states.

## Work completed during recovery

Independent reviewers checked frozen input identities, original source deltas,
artifact bytes, all sixteen retained constructions, ten saved-scene replay
receipts, receiver identities and source/accounting evidence. The coordinator
directly inspected all twelve original reuse render images and accepted both
375 mm deliveries and both first-result regenerations in a separately dated
receipt. No original receipt, participant source, test or numerical gate was
changed. No new author, native solve or receiving run was used for recovery.

[Source review](evidence/recovery/SOURCE-REVIEW.json) ·
[Numerical and evidence audit](evidence/recovery/EVIDENCE-AUDIT.json) ·
[Source and accounting review](evidence/recovery/REUSE-SOURCE-ACCOUNTING-REVIEW.json) ·
[Visual review](evidence/recovery/REUSE-VISUAL-REVIEW.json) ·
[Reuse acceptance](evidence/recovery/REUSE-ACCEPTANCE.json)

One interim provenance error is preserved: `ORCHESTRATOR-REVIEW.json` names
commit `4677188` while recording verifier SHA-256 `5be2048…`; that commit's
actual verifier has SHA-256 `de24a8a…`. The later `ORCHESTRATOR-REVIEW2.json`
correctly binds commit `883c004` and `5be2048…`, matching both actual validation
executions. The final bound review supports those executions. The interim
record remains unchanged rather than being silently corrected.

## Second interruption and final publication recovery

On November 10, 2026, a later continuation reconciled the repository again.
GitHub main was `ee7dc2b71710dc8963b01ab6db68a1c75e22c27a`; that commit
changed only the previous integration lease. C194 had no published branch,
pull request or evidence directory. The earlier completion claims therefore
described local acceptance, not a completed repository integration or ZIP delivery.

The original workspace and the first recovery checkout were still available.
A separate checkout preserved local head `67a35c2d9b1c2df2f5c8a982a37b3c9ec56e68d0`,
all original author histories, 22 inherited checkpoint refs and 31 uncommitted
recovery files. The previous workspace remained unchanged. Independent direct
byte review passed 3,925 integrity and consistency assertions across 1,038
archived files. These are evidence assertions, not new unit-test methods.

A fresh relocated extraction exposed a delivery-helper defect: the file-only
manifest did not list three harmless empty `.staging` directories retained in
the preparation and first-validation archives. The extractor wrongly refused
them. The narrow correction validates their mapped paths, rejects file/ancestor
collisions and skips safe directory entries. All archive bytes and manifest
hashes are unchanged. The original helper, failed invocation and dated review
remain in [the second recovery record](evidence/recovery-r2/).

After that correction, extraction verified all 1,038 files and the independent
recorded replay passed 1,755 assertions over sixteen artifact audits and ten
retained saved-scene receipts. No new author trial, native build, scene
resimulation or receiving execution was used. Current source/tests/backend/
contracts/workflows remain unchanged outside the bounded C194 preparation,
comparison and portable recovery tools.

The expired lease was reconciled and replaced through an expected-head update
at `5326fe7dc601cfd32cae76874f9204d4028ce5ff` by owner `c194-recovery-91d3`.
The actual candidate, PR, merge and resulting-main checks are identified in the
separate integration record when publication completes.

## Publication and history boundary

The ordinary Git client had read access but no write credential in this
environment. Authorized publication uses the connected GitHub Git-data API.
Its commit interface cannot reproduce original author/date metadata. Therefore
the remote publication commit is a new identity over the exact reviewed tree;
it is not a claim that the original worker commits were pushed as remote
commits. Their complete raw objects are retained in the incremental
[history bundle](evidence/original-worker-history.bundle). The complete handoff
also retains them as explicit source checkpoint refs.

The incremental bundle requires the real C193 base
`3c9fcaa4daff7b32e7b813ba05041212c1a5bc2f`. The final self-contained source
bundle includes that prerequisite and the complete delivered source, preserving
the declared C190 ancestry boundary. Earlier absent ancestry and unavailable
original C193 worker histories retain their inherited disposition.

Before merging, reconcile actual main and acquire its bounded integration lease
through an expected-head conditional update. Publish and review the exact tree,
merge with the expected PR head, fetch the actual result, run relevant recorded
checks on that result, then record verification and release the lease. Exact
publication and resulting-main receipts are added as those actions complete.

The unchanged failed legacy regression is not retested or relabeled by this
evidence-only continuation. See [the current result](README.md) and
[the inherited disposition](../guide-repair-c193/evidence/recovery/legacy/REGRESSION.md).
