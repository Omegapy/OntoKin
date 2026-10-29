# C062 final candidate cost review

## Disposition

**PASS for the reviewed cost decision, calculator changes, and finite continuation scope.** This was a static review. No calculator, product module, request, test, or workflow was executed during this final review. No candidate source file was edited.

The candidate directory reviewed was `/workspace/scratch/f5868448bf9b/c062-candidate/docs/engineering/reach-recording-validation-2026-10-28-c062`.

## Findings

The selected whole-ancestry ceilings remain P11 `171 + 60 + 24 * 20 = 711` and L03 `68 + 24 + 24 * 6 = 236`. The P11 miss bound correctly uses at least 256 distinct later charged LRU updates, including promotions and insertions, after each incoming access; it does not require 256 new insertions or claim to measure misses. Its 6,084-operation enclosing interval is deliberately an oversized update pool. The L03 result allows every incoming call to miss.

The mandatory future-work floors remain P11 `15 * 20 + 320 * 3 = 1260` and L03 `24 * 6 + 150 * 3 = 594`. The key term includes only wholly unvisited keys. The interval term includes the interval ending at the partial key and later intervals, and its three charges are distinct from the key comparison charges. The resulting conditional necessary totals are `100000 - 711 + 1260 = 100549` and `100000 - 236 + 594 = 100358`.

The documents consistently distinguish source-derived visit counts and conditional upper/lower bounds from newly measured ancestry spans, observed cache misses, elapsed-time results, and complete request costs. They retain the exact setup-output and unchanged downstream control, charges, admission, and cache-effect conditions. The 6,006/3,300 whole-phase observations are expressly excluded as removable ancestry totals.

The authority/cost conclusion is properly narrower than a general impossibility claim. A descriptor design retaining incoming work and paying one fresh receipt per replaced node has at least `n + g + 2` warm charges against `n + g + 1`; insertion, eviction, invalidation, displacement, and fallback are additional costs. This rejects that concrete design. It does not impose that admission lower bound on every possible representation. Separately, the whole-helper ceiling rejects an isolated complete remedy under the stated conditions, without rejecting combined changes or smaller beneficial increments.

The candidate calculator differs from the earlier reviewed calculator only by (1) refusing execution with Python assertions disabled and (2) checking chronological non-overlap of retained phase spans. Neither change alters the cost algorithm. The `not __debug__` guard prevents Python `-O`/`-OO` from silently disabling the verifier's assertions. The added span assertion strengthens the enclosing-window premise.

The handoff and next task preserve the finite source-only NO-GO and do not automatically start another attribution or tuning round. The proposed continuation identifies exact historical-byte recovery, the unchanged documentation gate, dependency review, and fresh integration ownership as prerequisites. It preserves unresolved recording failures and does not equate an evidence-only increment with runtime or release acceptance.

## Receipt boundary

The prose source identities are consistently named: reviewed C061 baseline `e5e99b92e4efa541b434abcdda5c2ec31dda6a39`, with original executed C061 tooling/source `bd5a09618c123a0b1d3339df3a944cfd6ed63b56`. The linked `source-binding.json` did not yet exist in the candidate directory at review time, so this review does not verify that pending receipt or final publication/validation receipts. Root finalization must materialize and verify them. This is a receipt-completeness boundary, not a cost-proof objection.

## Exact reviewed hashes

| File | SHA-256 |
| --- | --- |
| CHECKPOINT-062.md | `1643397dd26407cf93a9af80c4faed715e3f34f49e99bb1c555dda59acb3d0b6` |
| README.md | `b24b0826a8467e4da778a60e146739f943b2b77e8ef30419fc58d6ea4fd2c0cc` |
| c062_ancestry_cost_screen.py | `e604534210f78144f730c4b2eeb7d089de000b08e95177220c6e75f5da5e7235` |
| HANDOFF-062.md | `513bfb04d522f00422aad7bcda4e097932fa62ee55e4441a5fd81e340e46dbb4` |
| NEXT-TASK.md | `48fa433f95c3214118207a92b9400d80c68b35e6825c2d1c64ba7fcb19960718` |

The displayed result section of the existing calculated ledger was also checked against the decision; its full-file identity was `b746295e6e731d44a6b0bf6309c159a07f15f9518f065fc38ea0916c088d4599` for `c062-cost-screen.json`. No new execution was performed to produce this review.

## Finalization pause

All review operations are paused after saving this file. No further reads, writes, execution, or external activity will be initiated during the upcoming exclusive root finalization window unless root explicitly resumes this reviewer.
