# C071 decision: source-speed projection has no new reuse in retained P11/L03

## Decision and scope

Do not implement or instrument the proposed omission of source `bound.speed` from the existing whole `certificate_group` cache key for the retained P11 and L03 requests. Exact source structure and retained clock bytes establish that this projection creates **zero new key equalities** on their passive native producer paths. With other cache behavior matched, it therefore avoids zero additional complete-group calculations and saves zero direct metered operations before added admission work.

This closes C070's nominated source task. It is stronger than an unresolved-incidence result: an exact numerical tuple census is unnecessary to reject this particular new-hit mechanism for these requests. It does not prove that arbitrary mixed-phase requests cannot benefit, establish elapsed-time performance, or claim a universal impossibility. No P16/P23 rescue conclusion follows.

Baseline is actual main `ff71faa05503245b553621ba390cad080276e732`, tree `a124d1acfa4e7c5f6c140e592d594036a2eed2ca`. The original C070 packet and ZIP were freshly verified, including all 3,749 source files / 622,661,283 bytes and all six uploaded metadata files. [Preparation](PREPARATION.md) preserves recovery boundaries. C070's explicit closure is [Issue #26 comment 6512520085](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6512520085); C071's isolated source scope is [comment 6512705757](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6512705757).

## Exact proposed change

The current key in [interval_certificates](../../../ontokin/reach_export.py) is:

```python
("certificate_group", bound, enclosing, radius, vertex_error, nsp, nsr,
 proof_width, proof_shift, ep, eq, magnitude)
```

`MotionBound` contains source speed, acceleration and angular speed. The candidate for this analysis replaces that complete source bound with its two numerically used fields and a distinct group tag:

```python
("certificate_group_source_speed_projection_v1",
 bound.acceleration, bound.angular_speed, enclosing,
 radius, vertex_error, nsp, nsr, proof_width, proof_shift, ep, eq, magnitude)
```

It uses the same complete-group result and the same bounded request cache, with the unchanged 256-entry maximum. `_reuse` retains its outer `reach_recording_arithmetic_v1` namespace. This is a proposed key representation, not changed runtime code. All remaining inputs stay in the key. In particular, the complete enclosing bound stays: `enclosing.speed` contributes to the position calculation.

The source-speed numerical-dependency observation is correct. `_certificate_quantities` reads `bound.speed` late while constructing `rounded_bound`. `complete_interval_bounds` reads that temporary bound's acceleration and angular speed, but not its source speed. The returned numerical fields do not expose source speed. However, the actual late read, original full-key hashing/equality and callback/error schedule remain observable obligations. Removing a numerical dependency does not by itself authorize suppressing those events.

## Why no new equality is possible here

Write an original native key as `(B, E, X)`, where `B = (v, a, w)` is the source bound, `E` is the enclosing bound, and `X` contains every remaining input. The candidate retains `(a, w, E, X)`.

For each group, the current producer obtains `B` from `phase.carriers[frame]`. It builds each component of `E` as the maximum over `selected`. When `selected == (source_index,)`, every enclosing component equals the source component. In particular, `v == E.speed`.

Consequently the projected key has a left inverse on this cohort: reconstruct `B` as `(E.speed, a, w)`. Equal projected keys must have equal original keys. Equal original keys also have equal projected keys. The exact key-equivalence relation is unchanged **across all visits**, including visits in different groups. This is not merely a within-group statement.

The producer also forms `numeric_selected` to cover adjacent after-state numerical allowances, and includes a separate final after-state. Those allowances affect `nsp` and `nsr`; they do not change `selected`, which supplies `enclosing`. Confusing these sets would invalidate the argument.

## Retained-byte evidence

The [derivation](derive_evidence.py) verifies C060's nine ordered archive parts, the assembled archive identity and the two selected GLB member identities. It reads the actual binary32 animation-clock accessor, checks the retained exact authored clocks and boundary flags, independently recomputes the positive-width enclosing selections, and checks every interval/carrier certificate identity and `source_phase_indices` value.

| Retained fact | P11 | L03 |
| --- | ---: | ---: |
| Exact source boundaries | 0, 2, 3 | 0, 2, 3, 4 |
| Retained keys | 52 | 178 |
| Intervals by source phase | 50, 1 | 87, 89, 1 |
| Carriers | 20 | 6 |
| Certificate rows checked | 1,020 | 1,062 |
| Complete groups | 2 | 3 |
| Existing group visits | 40 | 18 |
| Existing complete calculations | 23 | 12 |
| Existing full-group hits | 17 | 6 |
| Additional full-key equalities from projection | **0** | **0** |

All 51 P11 intervals and all 177 L03 intervals have `selected == (source_index,)`. Every source boundary is exactly representable in binary32 and appears unchanged in the stored clock accessor. The retained `source_phase_indices` agree with independent exact-clock recomputation; they are not accepted as authority by themselves.

The source also explains the result: `reach_timeline` retains semantic boundaries, and monotone rounding cannot carry an interior endpoint across an exactly represented boundary. The selected retained-byte census directly checks these requests. It does not replace actual bytes with a general floating-point assertion.

The source-bound C060 producer category records establish 23 and 12 calculations from 40 and 18 group visits. All current runtime files match that historical source. The missing exact full-key tuple sequence is not reconstructed; no ordered LRU trace is reconstructed. Neither is necessary for the injectivity proof.

| Identified retained payload | Bytes | SHA-256 |
| --- | ---: | --- |
| Complete C060 evidence archive | 6,962,230 | `0865d06b6aee8290ebcd9372218f5c2b784a1b97bfcffc249b2fced3bdc81df5` |
| P11 unvalidated reader input | 1,799,228 | `4ea1d4d90fd1942aa8a793892dfe1a72f7ae047b5725f9750ab5c7b330477c3d` |
| L03 unvalidated reader input | 1,657,840 | `12f78939fd6fb5e8a6dace1ed4469c4da90ae3e56a8f0e21dd2e73947ae567e5` |

These are retained inputs from failed requests, not accepted delivered artifacts. Reading their clocks and metadata does not certify their numerical inequalities, rerun the historical auditor or alter their failed status.

## Complete-cost implication

Under passive native execution, unchanged surrounding dispatch and a projected group tag disjoint from other cache families, an injective key rename preserves hits, misses, promotions, insertions, evictions and relative LRU order. Nested calculations execute in the same places. The same number of distinct complete-group entries occupies the same bounded cache. There is no positive downstream occupancy benefit to infer here.

Even if new projection and authority work were free, the new-hit mechanism saves zero operations. Added paid checks cannot be funded by absent new group hits. The [funding record](funding.json) separates complete skipped calculations, outer-cache charge differences, added admission, refused/replayed work and signed other-work differences. It does not import C070's separate-angular-cache overhead formula, because this proposal replaces an existing key rather than adding another lookup layer.

The earlier matched-path mandatory reader-tail floors of 620 and 294 remain historical bounded screens. A zero direct saving cannot remove either deficit. No full tail cost or measured candidate request is claimed. A shorter Python hash representation might affect unmetered elapsed time, but this investigation has not measured that effect, and it does not supply operation-budget rescue.

## General route and authority remain unresolved

For a mixed enclosing set, another phase can determine `enclosing.speed`, while the source speed varies. The left inverse need not then exist. Abstract bounds `(1,a,w)` and `(2,a,w)` under the same enclosing bound `(3,A,W)` illustrate a possible projected collision if every other input matches. They are a mathematical example, not an observed native request or measured duplicate.

Any broader proposal must establish exact native incidence, current field domains, original first errors, live arithmetic and cache dispatch, callbacks, lowering of operand limits, and provenance throughout the skipped work. Exact `MotionBound` type alone is insufficient: the frozen dataclass has no field-type validation. A foreign speed object with a raising hash is an unexecuted helper-level witness that full and projected keys can have different observable behavior when the enclosing field does not duplicate it. It is not an observed stock-source failure. The singleton cohort retains that same speed through `enclosing`, so this particular hash-omission witness does not apply there.

The original foreign route must keep the full key without eager projection reads. Existing cache domain resets, charged promotion and generation checks are real safeguards; they do not automatically authenticate a new writer route. Replaying the original omitted arithmetic schedule for arbitrary callbacks would remove the intended operation saving. [The event analysis](EVENT-MAP.md) records these boundaries. No general authority-safe funded schedule or positive complete-request premise is established.

## Validation, preserved status and next action

[Validation](validation.json) binds the actual static derivation runs and their output. [Reviews](reviews.json) identify exact reviewed inputs and disclose which reviewers contributed evidence or tooling. Documentation checks on actual published candidate, resulting merge and final main are separate roles; they establish source/documentation integrity only.

All 65 runtime files and all existing tests, fixtures, contracts, defaults, limits and workflows remain unchanged. C071 runs no product imports, requests, runtime suites, native trigonometry, mesh generation or hosted jobs. Historical recordings remain **24/28, failed**, with **P11/P16/P23/L03 unresolved**. M1 remains rejected; C035 remains held including adverse timing; C057, complete reach acceptance and historical LFS migration remain open. C068's proposal remains unadopted and C069's existing-list receipt remains rejected.

Preserve 100,000 shared operations, 30,000 ms, 32,768 operand bits, 256 cache entries, 64 cursor updates and every original acceptance input. The full language, modeling, dynamics and engine-delivery [GOAL](../../../GOAL.md) remains in progress. [NEXT-TASK](NEXT-TASK.md) names a different bounded investigation. It does not reopen an exact-tuple census for this disproved P11/L03 opportunity.
