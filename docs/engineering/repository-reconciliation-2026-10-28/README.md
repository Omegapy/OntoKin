# C059 repository reconciliation

Date: October 28, 2026. Scope: [Issue #26](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6478260243). The owner authorized technical decisions, branch cleanup and more frequent main integration while preserving the AI-agent language mission.

## Selected integration

[PR #56](https://github.com/Omegapy/OntoKin/pull/56) combines the C058 evidence/history with C032's reviewed development runtime. Tested candidate `4155acfd1b01e1b72aac23be5e28b054d2e10440` has tree `6afc9960c5551115c87aafdcbc1d9d002172d5f6` and implementation SHA-256 `c87bf41b1219a0ab281af26dcc666a864d75c944c57f23b398dea4ea55c5b39c`.

It restores `ontokin/reach_reference.py` and `ontokin/reach_reference_center.py` to their exact C032 blobs, excluding held C035 product-observer and offset-product changes. [Source selection](source-selection.json), [the initial risk review](source-selection-review.json) and [the independent runtime review](evidence/reviews/reviews/runtime-selection-review.json) identify the exact bytes and containment.

The exact C035 test module remains in [held source](held-source/test_reach_centered_offset_products.py). Its 29 methods are excluded from the active suite with the held implementation. The original test path contains only a documentation pointer, preserving frozen links. No tests are skipped or silently changed. Historical results and adverse timing remain.

Six existing capabilities/discovery strings mark explicit source/Agent/GLB 0.6 as experimental and release-incomplete. Earlier defaults, schemas and numerical behavior are unchanged by those metadata edits. [OK-DEC-COMPARE-M1](../OK-DEC-COMPARE-M1-0.1.0.md) rejects exact M1 for comparison-only operation saving; it does not validate the existing accounting gate. [OK-ENG-009](../OK-ENG-009-development-integration-and-branch-lifecycle.md) distinguishes verified development integration from full release acceptance.

## History preservation and completed cleanup

[Original refs](remote-refs-before.json) record 104 branches and 95 distinct heads; [original PR metadata](pull-requests-before.json) records 47 PRs, including 34 open drafts. Archive branch `archive/pre-consolidation-20261028` at `e6917dae0be3a786c22e76be3de62e3c97784cf5` has 95 parents and an index-only tree. It retains every original head and must never be merged into main or used as a product development base.

The [retention review](archive-retention-review.json) and [publication readback](archive-publication-verification.json) preceded removal. [Final deletion receipts](evidence/reviews/branch-audit/cleanup-receipts-final.json) cover all 103 original non-main branch names, each with fresh-head verification and postdeletion absence. [PR closure receipts](evidence/reviews/branch-audit/pr-closure-receipts-final.json) retain the exact heads, dispositions and successor of all 34 original drafts; closure does not imply each proposal was merged or accepted.

The [independent cleanup review](evidence/reviews/branch-audit/branch-cleanup-final-review.json) and [live readback](evidence/reviews/branch-audit/branch-cleanup-final-live-readback.json) observed main, the archive and PR #56's branch, with only PR #56 open. [Repository settings](evidence/reviews/github-repository-settings.jpg) were reloaded and confirmed: automatic deletion of merged head branches, and inclusion of Git LFS objects in archives. Retaining the archive preserves historical Git objects; deleting branch names does not remove their storage.

## Actual candidate verification

The complete C058 snapshot was recovered: 3,174 files and 558,686,958 bytes, with file blobs, tree objects and actual commit bytes verified. [The recovery record](source-recovery.json) identifies the exact shallow checkout. Refreshed metadata recovered all 396 initially failed signed-file downloads; acquisition failures are separate from product checks.

All runtime executions below used the exact candidate above with unchanged source/Git identity. The original driver, frozen fixtures, expectations, independent oracles, workflows and resource limits were unchanged.

| Execution | Actual result |
| --- | --- |
| `c059-validation-full-001` | 3,064 tests passed with no skips. The separate 106-test Agent/0.5 cohort passed and overlaps that suite. The driver attempt failed: 25 roles passed, two failed, seven blocked. |
| `c059-validation-recovery-001` | All nine failed/blocked driver roles passed, including browser readiness, the 22-fixture / 492-exchange surface Agent workflow, and six browser roles. |
| `c059-force-regression-001` | Four roles passed: 56-case source conformance, 23 source GLBs plus five required artifact-free failures, native validation and nine browser fixtures. The fifth role, Agent build, failed with a malformed SQLite database. |
| `c059-force-delivery-recovery-002` | In an exclusive execution window, all four remaining force roles passed: Agent delivery, independent audit, native validation and browser validation. Seven GLBs were reconstructed from 11 retrieved chunks across 412 exchanges. |
| Actual visual review | All 83 PNGs inspected: 35 inherited/recovery, 27 force source and 21 force Agent. No blocking rendering concern was found. |

The selected union is exactly 34 planned local-driver roles and eight supplemental force roles. Neither original failed attempt is relabeled as passed, and the entire suite was not rerun after evidence publication. The [aggregate review](evidence/reviews/reviews/c059-validation-review.json), [member ledger](evidence/reviews/reviews/c059-validation-review-members.json) and [independent crosscheck](evidence/reviews/reviews/final-claim-crosscheck.json) bind commands, reports, roles and inputs. Crosscheck counts are evidence checks, not additional product tests.

Actual tools included CPython 3.12.14, Node 24.22.1, Playwright 1.56.1, Chromium 141.0.7390.37, Three.js 0.180.0 and Khronos glTF Validator 2.0.0-dev.3.10. No fresh CPython 3.11/3.13, Node 22, macOS, Blender or live-engine execution is claimed. No hosted job was dispatched.

## Retained failures and limits

The initial browser preflight failed on sandbox process permissions; the selected recovery passed after the required process permission was supplied. An initial truncated browser download was separately recovered from another official distribution endpoint.

The first surface Agent run lost durable request state: two successful responses were absent from the final database, and a following request failed while committing. The first force Agent build later reported a malformed SQLite database. [The failure analysis](evidence/reviews/branch-audit/surface-agent-failure-readonly-review.json) preserves exact requests and database identities. The physical cause remains unknown; no runtime guard was added to hide these failures.

[Surface recovery verification](evidence/reviews/branch-audit/surface-agent-recovery-readonly-verification.json) reconciles all 492 durable rows. [Force recovery verification](evidence/reviews/branch-audit/force-delivery-recovery-readonly-verification.json) checks database integrity, 824 request/response hashes, 409 durable request identities, seven retrieved payloads and expected retry/cancellation transitions. Passive filesystem events do not identify a responsible actor or establish a general storage guarantee.

[Inherited visual review](evidence/reviews/visual-review/actual-visual-review-recovery.json) and [force visual review](evidence/reviews/visual-review/actual-visual-review-force.json) retain every inspected capture. Broad cameras make some objects small; side views can occlude paired objects or arrays. Images and playback do not prove live physics or Unreal acceptance.

Historical original28 remains **24/28, failed**. P11/P16/P23/L03 remain unresolved; C035 remains held. Complete reach acceptance still requires all R01–R12/Q01–Q22 and mandatory roles, 28 source and ten Agent artifacts, compatibility, rates/native/browser/visual verification and formal input closure. No new numerical, performance or live-engine claim follows from consolidation.

## Evidence transport and resulting-main verification

[Archive parts](evidence/archive-parts.json) identify the ordered split ZIP and hashes. [Archive members](evidence/archive-members.json) identify every extracted member and payload hash. Raw evidence includes all four attempts, commands/logs/reports/databases/artifacts, generated example inputs and reproduction scripts. Duplicate copied source, dependency installations and Git metadata from the original full-run workspace are excluded; the exact tested commit/tree and original inventories identify its source inputs. Reassemble parts in manifest order, verify the whole archive hash and CRCs, and verify all members.

Existing preparation JSON and historical reviews remain immutable, including their original pending states and reviewed input hashes. This narrative and new records describe later outcomes. [The reviewed reuse method](evidence/reviews/reuse-method/FINAL-EVIDENCE-REUSE-METHOD.md) requires complete Git-tree and actual source-inventory equality outside a closed exact-path list for new evidence and these two governance narratives. The unchanged preservation/link checker and independent evidence/claim review apply to those additions. Runtime results remain attributed to the tested candidate.

PR #56 merged as `1e2e7fff7bfb7ed638aa01db84c23fdf30bd35a3`. Its observed tree equals the published evidence tree `86a83027cb6761bd0ed3c8f1f59b9177066a597f`, with parents `a5199cd419ab071981cfcba02d8c64d0fed5127b` and `e7f2516ac60e7b4ca5bd95026bbd746ca6e4529f`. [Actual resulting-main verification](evidence/resulting-main-verification.json) confirms all 3,184 unchanged original inputs and the exact 101-path evidence/narrative difference from the tested candidate. [Its fresh preservation/navigation check](evidence/resulting-main-documentation.log) passed. [The integration receipt](evidence/integration.json) records actual merge, branch cleanup and subsequent evidence-only closure. The work branch was automatically deleted; main and the archive remain.

## Git LFS boundary

The owner authorized Git LFS use and funding. GitHub's archive-inclusion setting is enabled; that setting alone does not establish uploaded objects or completed migration. Strict storage-identity support and migration preparation are isolated from this tested candidate. The executor has no authenticated Git transport, and the connector has no LFS object-transfer operation. Payloads remain ordinary Git blobs until authenticated upload and clean download verification; no unuploaded pointer is introduced.
