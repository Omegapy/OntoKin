# Proposed C064: select a viable runtime reduction from integrated evidence

**Status: proposed, not started or scheduled.** C063 completes archive recovery and diagnostic integration. Continue from live main after reconciling the C063 release, current source identities and ownership.

## Product objective

Resolve the remaining original P11/P16/P23/L03 recording failures under the adopted semantics and unchanged complete-request budgets. The closest established evidence for P11/L03 is now integrated: C060's disjoint request ledger, C061's reader-setup attribution and C062's finite source-only ancestry rejection.

## Bounded next deliverable

Select **one concrete larger algorithmic change** in independent source/reference evaluation with a source-bound authority and complete-cost proof. Start by reviewing the integrated reader construction, source geometry/admission and per-key evaluation paths together with the retained C060/C061 evidence. Identify which original operations the proposed change removes, which operations it adds, and exactly which immutable or freshly admitted source facts authorize reuse.

The design must preserve actual setup outputs, independent validation, callback/cancellation and first-exception behavior, mutation authority, numerical results, cache accounting and all original limits. If it intentionally changes downstream work or cache behavior, specify and prove that change; C062's unchanged-downstream bound cannot be reused as an estimate for a different algorithm.

Require a positive complete-request premise before implementing instrumentation or running new requests. State what remains unknown and the smallest experiment that would resolve it. If the candidate fails its authority, error-order or cost proof, close that candidate with the specific counterexample rather than repeating the same measurement.

## Completed candidates that must stay closed

- C060: isolated producer `atan(1/239)` shortening cannot alone clear L03 under the reviewed unchanged-output/path conditions; P11 performed no such cold work.
- C061: isolated axial reader-setup reuse is insufficient in the examined original requests.
- C062: identity-only descriptors lack authority; the examined fresh per-node admission scheme has no positive warm saving; even free whole-ancestry removal remains insufficient when setup outputs and downstream charge/cache effects stay unchanged.

The measured whole-phase totals are not removable ancestry costs. Another ancestry-only attribution round does not advance these completed decisions.

## Implementation and acceptance boundary

A surviving design may proceed in its own explicitly scoped implementation task, with dedicated positive, negative, mutation/callback and operation-accounting controls, then complete original-request verification. Preserve actual failures and demonstrate complete-request savings without shortening the original workload or skipping independent checks. New shared runtime changes require the applicable regression cohort under OK-ENG-009. Release acceptance still requires the full adopted reach gate.

Do not bundle LFS migration, hosted execution, limit changes or branch-history cleanup into this runtime task. The complete recovered checkout and passing documentation gate are now available prerequisites, not further research objectives.
