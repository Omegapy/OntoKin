# Sharing a completed independent interval update in a broad recording graph

The [fused rotation derivation](reach-reference-fused-recording-proof.md)
establishes the exact interval function

```
R(S, C, s, c) = (outward_grid(S*c + C*s), outward_grid(C*c - S*s)).
```

Its result depends on the four actual immutable input cells and the
independent grid precision. Source carrier identity, translation, elapsed
clock, action identity, and cursor ownership are not operands of this
function. An independently completed result can therefore serve another
calculation with identical cells in the same proved operand domain.

`_recording_rotate_sincos(..., shared=True)` retains this result in the
existing independent arithmetic LRU, keyed by the exact four cells, grid
precision, operand cap, and a separate `recording_interval_rotation`
namespace. It adds no cache, capacity, allowance, producer value, or broader
precision policy. The original type, lattice, width, ordering, zero/unit,
and full-domain eligibility checks precede reuse. Every hit still has a
fresh admission callback and input guards, a charged existing cache lookup,
and current-domain/output guards. A changed cap returns to the original
interval expression. Exact callback exceptions propagate, and the original
fallback remains outside the added proof handler.

The existing complete-domain derivation also covers every operation omitted
on a hit. The independently proved function is recomputed after eviction.
Only completed immutable results enter this namespace. A callback changing
the cap during publication cannot make an old-domain entry eligible under
the new cap; the existing synchronization and full key retain that domain
separation, and the current call takes its original fallback.

Each source path still owns and advances its own recording cursor. Its
phase/context identity, exact old/current coordinates and clocks, step
count, rewind behavior, and 64-step reseed rule are unchanged. Sharing the
interval arithmetic does not transfer a clock, a phase, or an accumulated
history between paths. Cursor publication still occurs only after that
path's complete successful update and final live-domain checks.

The automatic policy enables this optional proof reuse only for an explicit
recording batch selecting more than sixteen carriers. This is a bounded
performance policy for broad graphs, where repeated arm laws can share
identical arithmetic. Small selections retain their previous direct-update
cost. Selection size is not an acceptance criterion or part of the proof;
using or declining sharing preserves the same interval function.

The focused tests compare exact cold/warm results, every input's key
contribution, default and ineligible paths, original oversized-operand
failures, live-cap changes at lookup/publication, callback identity,
separate cursor clocks/steps, and existing-cache eviction. Actual recording
costs and corpus outcomes will be reported from separately identified
executions. This note does not claim completion of the remaining recordings
or release gates.
