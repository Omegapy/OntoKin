# C268 one-phase plan

Implement, independently verify/review and integrate the finite historical endpoint reader; save verified delivery and stop.

Starting main: `b2ca38875bd7b43b85011bbc671ee9fee1682441`. Owner: `c268-root-c7dae94da130`. [Requirements](REQUIREMENTS.md).

## P01 — Scope and early recovery

Requirements: R01, R02, R03. Pinned startup, live reconciliation and confirmed early save.

Artifacts: `docs/workflow/tasks/C268/REQUIREMENTS.md`, `docs/workflow/tasks/C268/PLAN.md`, `docs/engineering/localized-repair-c268/EARLY-RECOVERY-RECEIPT.json`.

## P02 — Reader and independent controls

Requirements: R01, R02, R03, R04. Positive and adversarial independent controls.

Artifacts: `docs/engineering/localized-repair-c268/endpoint_reader.py`, `docs/engineering/localized-repair-c268/test_endpoint_reader.py`.

## P03 — Affected checks and exact review

Requirements: R04, R05. Complete affected cohort and independent review.

Artifacts: `docs/engineering/localized-repair-c268/RESULTS.md`, `docs/engineering/localized-repair-c268/REVIEW.json`.

## P04 — Integration and actual main

Requirements: R06. Conditional merge, fresh affected main checks, retained ancestry and branch disposition.

Artifacts: `docs/engineering/localized-repair-c268/INTEGRATION.json`.

## P05 — Verified saved handoff and closure

Requirements: R07. ZIP/extraction/source verification, confirmed save, external receipt and closure.

Artifacts: `docs/engineering/localized-repair-c268/DELIVERY.json`.

## Ownership and checks

Director owns tasks, shared state, evidence, Git index/commits, all remote writes, lease and delivery. Independent implementer owns endpoint_reader.py and an implementation report. Independent control author owns test_endpoint_reader.py, fixtures/control evidence and CONTROL-COVERAGE.md. A separate investigator reviews the exact candidate. Workers use fresh context and inherited model configuration, no nested fanout.

The complete affected cohort is the C253 corpus and C255/C256/C257/C258/C261/C265/C266/C267/C268 isolated observation components, plus workflow/documentation checks. No shared product code changes; complete product/Agent/export/native/visual/model/compatibility suites are not claimed. Unchanged historical failures remain visible. New/worsened affected failures block integration.

## Stop

Stop after confirmed final delivery, or first unplanned scope expansion with honest partial handoff; no next phase. Parent stays in_progress or review until every gate passes. A partial handoff is session delivery only.

Reviewer continuity: `/root/state_audit` launched with fresh context for startup, then retained that context for follow-up early-package and candidate review. Implementation/control workers launched separately with fresh contexts. No worker is represented as reset between follow-ups.

## Recovery phase — C268 P03, November 19

The interrupted implementation is already published at `734789521f82248d39b623c33aae9d3284ab4bce`. Its exact 12-group/281-method cohort was recovered from the previous workspace. A mandatory endpoint-length guard correction and independent 35-method controls were staged but unpublished. Preserve and resume these exact bytes.

Current owner: `c268-recovery-8bd47a4cbab7`. Starting main: `7ff41e071fb694dadf1ba256b13168e1a4083926`. Confirmed recovery and unpublished-work ZIP receipts are under `evidence/recovery-20261119/`. The previous main lease is honored until expiry; this phase has no integration authority without a new verified lease.

Acceptance: verify the fixed immutable candidate, independently review R01–R05, publish the P03 evidence checkpoint, and save a verified partial handoff with an external receipt. Stop before P04 integration and P05 parent closure. Retain the existing branch, draft PR266 and open issue265. Any remaining finding stays explicit; do not start another phase.

## Finalization phase — November 19, fresh continuation

Current user Prompt 1 resumes C268 and authorizes reviewed integration plus final saved delivery. The preceding P03-only stop bounded the interrupted prior session; it is retained above as history. This phase finishes the already-published correction, its full affected checks and independent acceptance, then P04/P05 if those gates pass. No next milestone or new implementation scope. Owner: `c268-final-ee457d84062e`; observed main `409ef18e0cb992ad1ab771c1258e989d5ef1c765`, branch `b799b7462bdc6a04464a2f903cec8dcabd659fa1`.

Early recovery is confirmed saved; see `evidence/finalization-20261119/EARLY-RECOVERY-RECEIPT.json`. Publish checkpoint before verification. Independent recovery audit and exact-candidate reviewer are separate workers; Director owns all commits, shared state and remote writes. Acquire a new conditional main lease only after acceptance. Stop after final saved C268 handoff, or preserve an incomplete handoff if a new material implementation requirement appears.

## Recovery finalization — November 19

Owner `c268-finalize-a3de3dd23bbf` resumes this same scope and branch. R01–R05 are accepted on the unchanged corrected candidate. Preserve the recovered original commit and exact evidence; finish P04 integration/main checks and P05 saved delivery/closure only. Reconcile the current main lease before any integration write. No implementation replay or next milestone is authorized by this phase.

## Delivery recovery — November 19, final bounded phase

Owner `c268-delivery-60da64efa55b` resumes after interruption. Live main is merge `5084dd69312e8da5a49aadd33cf83ba56db7c058`; PR266 is merged, its head is retained by main, the branch is absent, and issue265 remains open. Recovered post-merge evidence `ecce5f18fd4693e254bc6c797cd8b3f0a74d32a1` passes an independent 673-assertion continuity audit. Its full original tree is published at `71932558224d80794f76e52adf603b6308580326`. Do not repeat implementation, merge or eligible observer tests.

Confirmed early save: `docs/engineering/localized-repair-c268/evidence/delivery-60da64efa55b/EARLY-RECOVERY-RECEIPT.json`. Publish the recovered R06 verification record under verified lease `bb317b3bb84c484a4877b2a1a5e74393d94795f8`; run applicable fresh documentation/workflow checks for current records; verify and save final ZIP and prompts; publish separate receipt, close task/issue and release ownership. Stop immediately after this phase. R07 remains pending until its actual saved delivery and closure.
