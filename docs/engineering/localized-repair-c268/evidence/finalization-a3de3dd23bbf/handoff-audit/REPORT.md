# C268 handoff and accepted-evidence audit

## Verdict and first unmet gate

The four supplied handoffs are internally consistent and recover the same outstanding C268 acceptance checkpoint. All root manifests, ZIP inventories, CRC checks, extracted byte counts/hashes, and 374 snapshot bindings pass. Each snapshot also matches its declared `commit:path` in the retained Git checkout. This is local object verification, not a fresh remote-state observation.

The first unmet gate in all three C268 checkpoints is publication of accepted-evidence commit `ffb912cce59ccfe7d0d82ab4349de9b12271cc03` after identity/eligibility audit. This audit confirms its retained evidence and prerequisites. The Director must reconcile live publication status and ownership before writing; integration, fresh actual-main checks, branch disposition, final saved delivery, external receipt, and closure remain separate gates. No new implementation milestone is indicated.

## Exact identities

| Role | Commit or identity |
| --- | --- |
| Reviewed published implementation | `e6f55b73fa71953aa648bcd34711a6796a7346b6` |
| Reviewed implementation tree | `d94436a22552db903b8016f9d035985a7d8b6752` |
| Accepted evidence commit | `ffb912cce59ccfe7d0d82ab4349de9b12271cc03` |
| Accepted evidence tree | `10bcebf566d001a850f8e5c5c77eb96857de7e3b` |
| Ordered first parent | `e6f55b73fa71953aa648bcd34711a6796a7346b6` |
| Ordered second parent | `4370e54b93f65f01d1b5f3176562e3eb49f79b75` |
| Earlier equivalent local candidate | `52af987fd5705c034bf264e2fe3fbc9fa1f146ae`, same reviewed tree |
| Existing scope | `work/c268-historical-endpoint`, PR 266, issue 265 |

The bundle `recovery-payloads/C268_Accepted_Evidence_ffb912.bundle` is 2,152,869 bytes, SHA-256 `9f0c98776f5971e9f7c474f95a9244d6846c4f37be97726568ba54f2e7c55990`. `git bundle verify` passed in `/workspace/scratch/014048e883e4/OntoKin`; the two required commits are exactly the ordered parents above. The bundle advertises `refs/heads/work/c268-historical-endpoint` at the accepted commit.

## Acceptance and evidence reuse

`docs/engineering/localized-repair-c268/REVIEW.json` and its full finalization review record identify the separate reviewer `/root/review_c268_final`. The verdict accepts R01–R05 on the implementation commit/tree above, with no unresolved mandatory finding. The selector-length finding is resolved. Optional suggestion O01 about native `Path` preprocessing explicitly requires no change in this finalization phase. R06/R07 were not assessed by that review.

The published-candidate receipt records 12 groups, 282 methods, 14 C253 bindings, and zero failed/error/skipped controls. The C268 group has 35 methods and 131 calls: 12 historical admissions, nine raw successes, and 110 typed refusals. This audit verified all 157 candidate input files against the candidate commit, all 30 receipt-listed outputs, all 31 review artifacts, and all 18 reviewer code/dependency identities. No mismatch occurred. Tests were not rerun.

At the accepted-evidence commit, 153 of those input files remain identical. Four documented records changed: `STATUS.md`, C268 `RESULTS.md`, `docs/workflow/CURRENT.json`, and C268 `task.json`. Their before/after hashes match `EVIDENCE-CONTINUITY.json`; both retained preintegration documentation/workflow logs match their passing receipt. The current auditor interpreter bytes and platform match the historical CPython 3.12.14/Linux environment, including executable SHA-256 `fa67443527ed9647f760d807e2a38f26340757123e643c4639cf273ed15d5ea7`.

Reuse applies to those exact implementation, dependencies, fixtures, tests, runner, commands/settings, and applicable environment identities. Later material changes require affected checks/review. Actual resulting main still requires a fresh complete affected cohort. Full product aggregate, source conformance/export, other Python compatibility, native/visual/model trials, and hosted workflows remain unrun.

## Unpublished payload and restoration

Relative to the published first parent, the accepted commit contains 88 changed paths: 84 added evidence/review files and four modified state/result records. The exact path inventory is `published_delta_paths` in `ACCEPTED-EVIDENCE-AUDIT.json`. The added files include C268 `REVIEW.json`/`REVIEW.md`, the complete candidate-published receipt/output set, independent review/probe artifacts, recovery audit, verification summary/output audit, continuity, coordination, and preintegration receipts. No implementation file changes in this delta.

For recovery in an isolated checkout with both prerequisites, verify the bundle, fetch its advertised head into a dedicated recovery ref, and verify the commit/tree/ordered parents before adopting it. Preserve the exact commit and evidence history. Do not replay its historical `STATUS.md` lease over current main. Publish on the existing branch using observed-head protection; merge current unrelated changes under the governing integration protocol.

`C268_Local52_Verification_And_Commit.zip` preserves the earlier same-tree local run; it must not substitute for the published-candidate run. `FINAL-CARRY-FORWARD.zip` preserves 39 unique historical files, all hashes verified. Its base is `734789521f82248d39b623c33aae9d3284ab4bce`, published candidate `b799b7462bdc6a04464a2f903cec8dcabd659fa1`; do not execute historical scripts or apply patches automatically. `previous-confirmed-early.zip` has 159 verified manifest payload entries. All three nested ZIP CRC checks pass, and all 16 entries in the recovery-payload manifest match.

## Meaningful checkpoint changes

| Handoff | Observed main | Meaning |
| --- | --- | --- |
| Startup compression | `46485a6019648045d5a41d8a9254c7e84eab3128` | Separate startup scope; no unpublished payload; C268 explicitly outside scope. |
| C268 Recovery Early | `4370e54b93f65f01d1b5f3176562e3eb49f79b75` | Preserves accepted but unpublished evidence; recovery audits active. |
| Finalization Resume Recovery | `528f4258123ce891c862d13cf18d31f5af8d7dcc` | Prior lease acquisition already occurred and expired; remote audit/phase observations added. |
| Recovery 014048e883e4 | `452c88b8485e6d6fcf5557fa07ea6cb8f63e4b92` | Another historical lease/state observation; adds worker template and session phase/read-set. |

Early→Resume retains 125 files unchanged, changes eight metadata/state files, and adds four observations. Resume→newest retains 131 files unchanged, changes six metadata/state files, and adds three instruction/session files. No preserved recovery payload was removed or changed. The newest task snapshot is the historical main task record with stale `not_done` requirements; use the accepted commit's evidence to reconcile task state rather than restart implementation.

## Operations and delivery limits

The earliest recovery snapshot reports no surviving prior process but active new read-only audit/review workers. Resume reports `recovery_evidence` active and `remote_reconcile` finished. The newest snapshot reports `/root/recovery_audit` and `/root/github_reconcile` active, no unknown remote write, and prior owner `c268-finalize-539812f26573` lease expired at `2026-11-19T23:38:11.952Z`. These are observations at freeze, not proof of current termination. Current readbacks and worker reconciliation remain Director-owned. Do not replay prior successful lease acquisitions.

All checkpoints freeze with save/receipt pending; later receipts are intentionally external. Source archive identities and exact checkpoint metadata are in `ARCHIVE-AUDIT.json`. C262 remains unchanged and external: 532,260,846 bytes, SHA-256 `b8af544f730a4d1f741d47b56eb3fcf76147ed392a9ebb020f3d966f2f305c90`. Ordinary online continuation does not require reconstructing it. No full offline restoration is asserted.

An initial audit attempt unnecessarily compared candidate paths against unintegrated main and stopped on the expected absent `CONTROL-COVERAGE.md`; no files/Git state changed. The corrected audit compares the candidate and accepted-evidence identities. This failure and correction are preserved in `ACCEPTED-EVIDENCE-AUDIT.json`.
