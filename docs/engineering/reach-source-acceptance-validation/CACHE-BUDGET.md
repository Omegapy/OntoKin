# Bounded reach cache replacement

## Scope and predecessor evidence

Owner `interactive-reach06-cache-budget-20261020-2217-7of9` prepared this
continuation on `work/reach06-cache-budget-20261020-2217-7of9` from published
source candidate `8aa120dfa3c5567704c52df29c51c8b7203eb0d6`.
[PR #21's scope declaration](https://github.com/Omegapy/OntoKin/pull/21#issuecomment-6303005082)
reserves only `ontokin/reach_numeric.py`, the new cache regression module, and
this note.

The retained `source-001` run on that predecessor executed all 45 methods in
the [source cohort](SOURCE-CORPUS.md): 44 passed, while P23 failed 11 of its
12 sample requests at the unchanged shared 100,000-operation limit. Its
`0/before` request consumed 95,504 shared operations. Each later request
reached five admissions before exhausting its allowance. All 1,155 inputs
remained stable. Those results describe the predecessor, not this correction.

The shared cache previously stopped accepting new entries at capacity. Source
pose entries could fill it before the first IK admission. The already keyed,
immutable IK solution was then discarded, so identical subsequent admissions
repeated its complete proof.

## Replacement and work accounting

`ReachExecutionWork` now uses deterministic least-recently-used replacement.
Every new entry is retained; when full, insertion evicts the least recently
used entry. A hit or an existing-key replacement promotes that entry. The
fixed maximum remains **256 entries**, with the same supported lower limits.
The cache remains local to the existing request work object.

The existing `cache_lookup` and `cache_insert` charges remain. A hit and an
existing-key replacement additionally precharge `cache_promote`; insertion
at capacity additionally precharges `cache_evict`. All required charges occur
before values or recency order change. Each unit invokes the inherited work
and cancellation callback. Cancellation or a resource failure at those new
checkpoints leaves the previous cache entries, values and order intact.

The exact arithmetic, interval proofs, rounding, precision schedule and
acceptance limits retain their existing definitions. An IK cache hit still
validates operands and their domain, rechecks the current closed joint limits,
and reports the current admission's actual work. Source topology, lifecycle,
modes and claims remain the evaluator's responsibility. Only successful
immutable mathematics is reused; the cache grants no action authority.

This replaces the optional stop-inserting policy described in the earlier
[numeric implementation derivation](../reach-numeric-kernel.md). Operation
counts reflect the executed arithmetic and newly charged cache bookkeeping.
No counter is reset or enlarged and no completed proof is charged again as
though it were recomputed.

## Prepared regressions and pending execution

`tests/test_reach_cache_budget.py` adds three named methods:

| Method | Concrete regression |
| --- | --- |
| `test_saturated_cache_retains_proof_and_revalidates_limits_and_domain` | Fill all 256 slots before actual P01 admission; compare with frozen expected bits; require reuse without another series proof, fresh work accounting, and rejection of changed closed limits or an invalid domain. |
| `test_hot_proof_survives_interleaved_pose_entries_at_lowered_capacity` | Keep an actual repeatedly used proof while distinct entries arrive under a two-entry limit. |
| `test_interrupted_bookkeeping_preserves_cache_values_and_order` | Interrupt promotion, replacement and eviction at their new checkpoint with both caller cancellation and a lowered work budget; retain the exact previous cache and original callback exception. |

These files were prepared without running the runtime, tests, compiler or
exporter. Publication and exclusive execution are pending. The root worker
will bind the actual candidate SHA to the new numeric cohort and a fresh
45-case source run. Results must be retained separately from `source-001`.

Cache replacement has not yet established that P23 fits every source request.
Repeated full-scene work during simultaneous completion, source/Agent delivery,
derived world-rate acceptance bounds, compatibility and the remaining release
roles retain their separate gates. This correction does not close
`source_execution`, the finite reach release or the full product goal.
