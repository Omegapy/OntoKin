# Bounded reuse of exposed quaternion projections

## Scope and predecessor evidence

Owner `interactive-reach06-pose-budget-20261020-2223-7of9` prepared this
continuation on `work/reach06-pose-budget-20261020-2223-7of9` from published
candidate `767a1d7e88a946d4936122fe21d5abf769488f81`.
[PR #21's scope declaration](https://github.com/Omegapy/OntoKin/pull/21#issuecomment-6303096745)
reserves only `ontokin/reach_pose.py`, the new projection regression module,
and this note.

The root worker's retained run on that predecessor passed all 32 selected
cache, numeric, kinematics and pose tests. The [source cohort](SOURCE-CORPUS.md)
again passed 44 of 45 cases: P23 failed 11 of its 12 requests at the unchanged
shared 100,000-operation limit. Each failed P23 request had completed all 32
admissions with 147 series recurrence steps, then failed during quaternion
projection in the staged full graph. Its `0/before` request consumed 91,159
shared operations, down from 95,504 before the cache replacement. All 1,157
inputs remained stable. These are predecessor results, not results for the
projection change.

Separate poses can contain equal private quaternion components. Previously,
each pose's first public orientation read repeated the exact squared norm,
four component divisions and four correctly rounded square-root projections.
Pose-local memoization did not reuse that work across different poses.

## Reuse and work accounting

An ordinary projection now uses the existing request-local work cache, keyed
by the pose method identity, the projection operation and the actual immutable
quaternion component tuple. Positions, pose identities and angular error
allowances cannot affect these output bits and are absent from that key.
The cached value is the immutable four-float result of the unchanged exact
projection. No public-to-private quaternion round trip is introduced.

The frozen materialized-anchor branch remains before cache access. It retains
its existing charge and returns its actual saved projection directly. A normal
projection cached under equal components cannot replace a frozen anchor.

The existing `lookup` and `remember` helpers charge lookup, insertion and any
promotion or eviction through the same request's work and cancellation
callback. The fixed maximum remains 256 shared cache entries, with the same
supported lower limits and deterministic least-recently-used replacement.
Only a completed projection can be inserted or published to a pose. An
interrupted cache operation propagates its original failure. Operation counts
describe actual arithmetic and cache work; no limit or counter is enlarged,
reset or transferred to a fresh context.

## Prepared regressions and pending execution

`tests/test_reach_pose_budget.py` adds four named methods:

| Method | Concrete regression |
| --- | --- |
| `test_distinct_poses_reuse_exact_components_with_identical_binary64_bits` | Separate pose dictionaries and different error allowances; exact bits for unit, nonunit, negative and subnormal components, including canonical positive zero after negative underflow; a cache hit cannot call the square-root helper and still invokes the request callback. |
| `test_materialized_projection_bypasses_normal_component_cache` | An actual materialized anchor retains the identical saved tuple even when ordinary projection entries exist for its exact imported components. |
| `test_eviction_recomputes_identical_projection_with_bounded_storage` | Under a one-entry limit, an evicted projection recomputes with identical bits and storage stays bounded. |
| `test_cancelled_shared_projection_keeps_new_pose_unpublished` | Cancellation during a cache-hit promotion preserves cache order, leaves the new pose's projection dictionary empty and propagates the original callback exception. |

The explicit expectations use the identity, exact 3–4–5 normalization and
binary64 subnormal rounding boundaries. Cold-versus-cached comparisons test
optimization equivalence; they do not replace the existing independent
numeric/pose enclosures or adopted source expectations.

These files were prepared without executing runtime imports, tests, compiler,
exporter or probes. Publication and exclusive execution on an identified
candidate remain pending. The root worker will run the targeted cohort and
all 45 source cases, retaining any failed attempt separately.

This change has not established that every P23 request fits its allowance.
Source/Agent delivery, derived world-rate acceptance bounds, compatibility,
the remaining finite release roles and the full product goal remain open.
