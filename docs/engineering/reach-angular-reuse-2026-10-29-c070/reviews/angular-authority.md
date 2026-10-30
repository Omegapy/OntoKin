# C070 independent authority and event-order review

Reviewer: `/root/angular_authority`. Scope: source inspection at baseline commit `20977e92945d767bc8047b36e0e697f53d2a886e`. No product import, runtime request, test, instrumentation, numerical endpoint calculation, trigonometry or mesh generation was performed. This review is an independent analysis of the existing source; root supplied the proposed C071 dependency question after the first C070 findings.

## Decision boundary

The four-input tuple is a valid numerical dependency description under passive native execution. It is not a complete execution identity. A direct angular `_reuse` wrapper cannot be approved from that tuple alone: it changes the time of the `bound.angular_speed` read and may omit live guard, callback, observer or foreign behavior. Replaying the nine original charged seams can address those omitted events, subject to preserving their operands and continuation, but removes none of the nine metered units before added cache/admission work. That replay therefore has no positive operation-budget premise for this nine-call target.

A separately authenticated passive native route remains unproved, not disproved in general. Its fresh eligibility, lifetime and complete costs cannot be inferred from existing whole-group cache acceptance, C030's historical acceptance, C068's unadopted units or a nominal formula/version string. Do not report a universal impossibility, an executed hostile test or an observed stock recording defect.

## Exact source bindings

| Source | SHA-256 |
| --- | --- |
| `ontokin/reach_export.py` | `9ce63f55313175222a8ec539c1865c8ec15b4835e4cf1c96ec723337dd10c35e` |
| `ontokin/reach_numeric.py` | `1bd7da1d6721369d8662ba314e08c8704abfd24a4d9707113da4ac296d92ea0a` |
| `ontokin/construction.py` | `eae788d2e4c2a6c0cac76e578c3a1be683fca415e62b6e6e3b55f807d7f346c2` |
| `docs/language-design/planar-reach-v0.1/budget-counting.md` | `055b6167cbf67dc420c99dc24f3e08d449ae9d8d993250fbddfb48cabb4f4d04` |
| C057 comparison-admission audit | `bf6662bff92242e5e47b10fb9b7e49a643b584093aa5c288c9e46b4adf19271b` |
| C069 `NEXT-TASK.md` | `fef45d09e0fbfc13c8aa6f41b50694ec5d2c54c3885109d72cbc3d8dca96f574` |

AGENTS, GOAL, STATUS, C069 NEXT-TASK, the adopted budget, C057's audit and authority review, C068's proposal, C069's rejected receipt and relevant existing tests were read. Existing tests were inspected, not executed or changed.

## Original evaluation order

At `reach_export.py:1049–1069`, Python evaluates nested call operands before their enclosing call. Let `q` be incoming `eq`, `r` be `nsr`, `w` be `width`, and `omega` be the value read from `bound.angular_speed` at its actual source position.

| Event | Actual operation or check | Important order |
| --- | --- | --- |
| P | `_exact(ep, nsp, "add", work)` | Original positional addition at1052 precedes the angular region and any proposed angular cache work. |
| A1 | `e = _exact(q, r, "add", work)` | First angular charge at1053. |
| R1 | `e > Fraction(1, 2)` | Fails with current model's endpoint-range diagnostic before reading `bound.angular_speed`. |
| A2 | `p = _exact(bound.angular_speed, w, "mul", work)` | `bound.angular_speed` is read at1059 only after R1 passes. |
| A3 | `h = _exact(p, Fraction(2), "div", work)` | Left branch of the chord expression completes before its right branch. |
| A4 | `u = _exact(Fraction(4), e, "mul", work)` | Uses adjusted `e`. |
| A5 | `c = _exact(h, u, "add", work)` | Forms chord after both branches. |
| R2 | `c > Fraction(1, 2)` | Current model's short-arc diagnostic precedes arc arithmetic. |
| A6 | `s = _exact(c, c, "mul", work)` | First arc intermediate. |
| A7 | `t = _exact(s, Fraction(4), "div", work)` | Retain prospective division guard. |
| A8 | `d = _exact(Fraction(1), t, "sub", work)` | Denominator is formed before final division. |
| A9 | `a = _exact(c, d, "div", work)` | Retain actual zero-divisor behavior before prospective guard. |
| R3 | `a > ANGULAR_STEP` | Current model's arc-range diagnostic at1068–1069. |

The angular arithmetic count is exactly nine explicit `_exact` calls: two additions, three multiplications, three divisions and one subtraction. The two numeric outputs of this region are adjusted `e` and `a`. The rest of `_certificate_quantities` still constructs quantities, rounds exposed primitives and computes destination and complete-interval bounds.

Each `_exact` at112–133 has this order: charge; operand guard; read numerator/denominator bit lengths; calculate prospective width and, for division, test the actual divisor; prospective-width guard; selected `Fraction` arithmetic; result guard. A successful old result does not, by itself, discharge all current obligations.

The range checks are existing raw comparisons, not calls to `_compare`; no fresh explicit comparison charge is inferred. Guards likewise are existing bodies within `_exact`, not independent extra charged units in this source. Any additional candidate checks need their own supported accounting, without inventing per-bytecode costs.

## Concrete conditional first-error witness

Consider entry directly to `_certificate_quantities`, a helper already exercised by `tests/test_reach_certificate_single_pass.py`. Choose ordinary native positional inputs for which P completes, and ordinary exact `q`, `r` with `q+r > 1/2`, for example `q=3/4`, `r=0`. Keep sufficient original budgets and passive work. Let a foreign `bound` object expose an `angular_speed` property that raises an existing exception E when read.

The original source completes P and A1, then reaches R1 and raises its `OKE-E-NUMERIC-BOUND` diagnostic. It never reads the property. A wrapper constructing `(bound.angular_speed, width, eq, nsr)` immediately after P instead reads that property first and raises E. This changes the first failure. It is an unexecuted helper-entry source witness, not evidence that a stock source request creates such a `bound` or fails this way.

Placing the wrapper after A1 and R1 avoids this particular hoist, but leaves only eight candidate arithmetic calls and changes the dependency tuple to use adjusted `e`. It does not settle cache publication, foreign callbacks, live guards or admission costs. An exact-native eligibility check could reject a foreign bound before access only if its own placement, authority and costs are justified.

At a seam inside A1 after its original charge returns, its operand and prospective/result guards and arithmetic remain pending. An added check there does not reuse the already consumed charge as free payment. Rejecting an optional attempt must resume the pending original continuation correctly; calling a fresh `_exact` repeats the original charge. Any earlier side effects and added work remain real.

## Cache protection that already exists

`ReachExecutionWork.lookup` at120–137 charges lookup, synchronizes the live operand cap and, on a hit, charges promotion. It synchronizes again after that callback and checks both the cap and key's continued presence. A changed domain invalidates the old cache through `_sync_cache_operand_limit` at248–261. Do not claim that simply lowering the operand cap yields a stale warm hit through this ordinary implementation.

`remember` at139–176 charges insertion and any required promotion/eviction before publication. It compares the live domain and cache generation around those callouts. It refuses publication after a detected domain/cache change. `calculate()` must complete before `_reuse` calls `remember`, so exceptions during computation do not publish its incomplete return value.

These protections concern the shared cache and operand domain at their actual checkpoints. They do not authenticate the code, mutable field aliases, callback/observer behavior or source proof method for a new reuse unit. An added cache entry can also displace existing entries used later by the writer or supplied-byte reader. Those complete-request effects belong in the cost analysis even when the two angular values are identical.

## Callback and authority classification

`ReachExecutionWork.charge` at71–94 captures the observer, calls the current external check, checks operation/time limits, increments counters, then calls the captured observer. Callback exceptions retain their identity. Native construction requests supply `ConstructionBudget.tick` at construction205–208; that meter may itself hold a nested custom check and increments before its own operation-limit check. The actual source-artifact driver creates the native no-custom-check route, while direct and Agent paths need their own treatment.

A permitted custom work/callback or observer can raise or narrow the domain at any original A1–A9 event. A generic warm hit replacing those events with lookup/promotion does not preserve that behavior. For example, an event-aware custom work implementation can raise its existing marker on the first angular `recording_exact_mul`; an angular cache hit skips that event. This is a conditional source counterexample to an unrestricted hit, not a claim about native stock callbacks or executed tests.

For passive native execution, genuine omitted arithmetic may move native budget checkpoints under the adopted rules. Requiring all nine old ticks on every native hit would incorrectly deny that permission. Conversely, the native numerical theorem cannot justify omitting observable foreign events. The design must establish its admitted route before omitting work, preserve unsupported routes and price every added/repeated/refused eligibility operation. C057 documents why copying a broad introspection gate supplies neither automatic passive storage nor complete funding. C068's proposed unit catalogue remains unadopted.

## C071 source-feasibility candidate

The existing `certificate_group` key at1307–1308 contains the full `bound` MotionBound, whose fields are `speed`, `acceleration` and `angular_speed` at452–456. In the passive native calculation, `bound.speed` appears only at1095, where it is passed through into a new `MotionBound`. `complete_interval_bounds` at1370–1402 reads `bound.acceleration`, `bound.angular_speed`, `enclosing.speed` and `enclosing.angular_speed`; it never reads that passed-through source `bound.speed`. No field of the returned quantity tuple exposes source `bound.speed`. The complete expression therefore has a narrower numeric dependency than the existing native whole-group cache key.

This is a concrete different next question: can the existing whole-group key omit source `bound.speed` under a fully paid, authority-safe route, with actual distinct-speed repeated incidence and positive complete-request benefit? It potentially avoids adding a second angular namespace or an extra entry for each completed group. Those advantages are hypotheses until the actual proposed key, entry count/order and full request effects are derived.

This dependency fact does not license deleting the actual `bound.speed` read on a miss, changing foreign field/hash/equality behavior, ignoring native field validity or changing first exceptions. That read occurs late, after destination work; any new key projection would read other bound fields earlier than their original cold uses and must be reviewed at the existing key/lookup seam. Exact retained incidence, native route authority, fresh key/read/type costs and downstream occupancy effects remain unresolved. No C071 implementation or observation is approved by this review.
