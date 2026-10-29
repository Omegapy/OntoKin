# C067: actual-point lower bounds for cold geometry extrema

## Decision

**The conditional mathematical screen is valid. A runtime implementation is not approved because stable native traversal and positive complete-request costs remain unproved.** C067 closes the feasibility question proposed by C066 with a narrower result: a previously visited seed cannot help, a future seed can help only before it is reached, and the current ordinary accessor path needs an additional authority proof. This is not a rejection of every actual-point optimization.

The baseline is actual C066 main `1aefbc24c38805cdd75add056421fcd0856e1f93`, tree `233cd6ae287bdcd4a77e0ea674dc1774f6923010`. The [source binding](source-binding.json) names thirteen exact inputs. [Recovery](RECOVERY.md) records the complete source reconstruction and its limitations. The [scope declaration](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6510695412) follows the explicit C066 closure.

No OntoKin runtime, test, fixture, contract, numerical limit, default or workflow changes. No product import, product request, runtime suite, native trigonometric evaluation, mesh generation or hosted job is executed. The standalone derivation evaluates abstract binary64/rational witnesses and reads source syntax; those calculations are not executions of the reader or original recordings.

## The quantity being preserved

The reader computes the largest exact rational `abs(x)+abs(y)+abs(z)` over the actual source vertices that it traverses. This L1 radius is used in later motion-error bounds. Each original vertex still has its geometry charge, source-to-binary32 comparison and component-error update. An existing upward float bound and repeated-maximum witness already avoid many exact sums. Every completed float candidate that remains incurs three decode and three addition charge calls. The final error norm, source construction, site-radius work, cache publication and warm validation remain baseline obligations.

The nominated proposal chooses the actual source row at zero-based index 133. This is a bounded experimental choice carried forward from the earlier sphere investigation, not a claim that the row is a sphere maximum. An actual-coordinate bound does not need a sphere recipe, ideal symmetry or a native-trigonometry enclosure. Any sufficiently long source sequence could supply the row; its usefulness must be established separately.

## One frozen arithmetic schedule

Let `RN` denote binary64 round-to-nearest, ties-to-even addition. For finite nonnegative native floats define:

`D(a,b) = nextafter(RN(a+b), 0.0)`

For the actual immutable native float triple `q`, select:

`L = D(D(abs(q.x), abs(q.y)), abs(q.z))`.

For a positive finite rounded sum, its predecessor is no greater than the exact sum. A zero rounded sum stays zero. If the sum overflows to positive infinity, `nextafter(inf, 0.0)` returns the largest finite binary64 number, which is below the exact overflowing sum. Thus `D` is finite and nonnegative and satisfies `D(a,b) <= a+b`. Applying the argument twice gives:

`0 <= L <= abs(q.x)+abs(q.y)+abs(q.z)` exactly.

This schedule handles signed zeros, finite subnormals and positive overflow without an artificial error. It uses two additions and two `nextafter` operations. It is the selected schedule throughout this record; the distinct clamped or finite-intermediate-rejection variants considered in review are not charged as though they were this one. Native dispatch and suitable seed-value checks are conditions, not facts established by the mathematical formula. An unsuitable seed must reject the optimization without converting a future value to a Fraction or producing a new earlier semantic exception.

At an original cold candidate seam, while the bound is pending, the proposed extra test is strictly `U < L`, where `U` is the unchanged existing upward bound. If it succeeds, omit only that point's exact radius fold. After each original component-error update while pending, perform one charged identity comparison `point is q`; a match retires the screen. Retaining `q` avoids an added ordinal counter. An earlier alias of the same immutable row can retire it safely after that occurrence. The seed never substitutes for the returned radius. Every original conversion and error update remains in order. Seed retention, pending-state setup and retirement are still identified setup/state work, not hidden within the identity comparison.

## What the proof establishes

### A seed must belong to the actual traversal

If the seed is eventually traversed and the scan returns successfully, let `M` be the true maximum of that traversal. Then `L <= L1(q) <= M`. Every maximizing point has `U >= M >= L` and cannot satisfy `U < L`. The original incumbent and repeated-component screens remain valid. Consequently at least one maximum receives its original exact fold unless the incumbent already proves it. The exact final radius is preserved under the stated native and coverage conditions.

Equality is retained. Replacing the strict comparison with `U <= L` is outside this nomination.

### A visited seed cannot improve the existing screen

Let the current exact incumbent be `R`. After a point has been processed, its valid finite float lower bound satisfies `L <= R`. The existing screen uses `radius_floor = prev(RN(R))`. Binary64 discreteness implies that a float `U > radius_floor` is at least `RN(R)`. Every float `L <= R` is at most `RN(R)`. Therefore an original candidate cannot also satisfy `U < L`.

The initial zero-radius state is harmless: its existing floor is zero and a visited zero point supplies no positive lower bound. This proof rules out a first-point seed and any plan that waits until the seed is already included before starting the new screen. It is a dominance theorem, not an empirical cost estimate.

### The future-seed effect ends at the seed

Every skipped earlier point has `L1(p) <= U(p) < L <= L1(q)`. Once `q` completes its original position, the baseline and proposed prefix radii agree. Their downward floors and repeated-maximum components also agree: a larger or equal establishing maximum cannot have been removed by a strict bound below the seed, while a seed attaining the maximum establishes the same component witness. Error accumulation was never omitted.

The screen can therefore stop permanently after the seed. An optional earlier stopping condition is `RN(R) >= L`; float discreteness then makes the new screen redundant. This condition does not assert `R >= L`, because rounding may be upward. A new conversion or stopping comparison still has a cost. The frozen ledger uses inclusive candidate comparisons through index 133 and charges seed recognition separately.

### Extra candidate decisions do not imply extra exact folds

In a stable all-native successful trace with one fixed valid `L`, skipping early folds may leave a smaller incumbent and expose additional candidate seams. However, it cannot introduce an exact fold absent from the baseline. Before the two states synchronize, the baseline-only larger incumbent came from a skipped point and is below `L`. Any point that baseline rejects using that incumbent, but the proposed scan exposes, has an upper bound below `L` and is rejected by the new test. A baseline-only repeated-component witness has the same property. A component tuple with upper bound at least `L` was not removed when it established its witness.

When a retained fold restores the same incumbent, or at the seed at the latest, both states synchronize. Thus proposed exact-fold count `K <= B`, where `B` is the baseline count. New seam decisions must still be counted independently. This stronger result depends on a fixed valid lower bound and stable native behavior; it does not apply to arbitrary shortlists, failed prefixes, changed callbacks or changing bounds.

## Traversal and authority remain unresolved on the ordinary path

The cold helper iterates `zip(source_positions, stored_positions)`. It has no independent stable-coverage check. Its caller checks equal lengths earlier, but subsequent work charges can invoke callbacks. Equal entry lengths alone do not establish that a future seed will be reached.

The [authority review](reviews/authority.md) gives a conditional helper-entry witness. Start with matching rows and a low first point, with a larger seed at index 133. A callback at the first point charge shortens the stored list to one row. The first pair was already yielded by `zip`; the helper can finish without visiting the seed. An unchecked future bound could skip the first fold and return zero instead of the baseline radius one. The abstract derivation reproduces the arithmetic consequence of that truncated traversal. It does not execute the callback or establish a complete-export failure. The wrapper can detect some later coverage changes and rescan; that possibility requires its own fallback accounting and does not prove the direct helper safe.

Equal immutable outer tuples provide a sufficient structural coverage condition for a successful traversal. But `DecodedGLB.accessor` creates, caches and returns a mutable list of native unpacked tuples. The ordinary POSITION path passes that list to the extrema helper. A stored-tuple-only gate has zero new coverage on this ordinary path. Copying the list adds work and freezes bytes that the baseline reads live, so a copy needs its own passive-execution proof.

A useful restricted list path would need an interval in which the actual rows, work object, callbacks, operand cap and relevant dispatch cannot invalidate coverage or omission. It must include `scene.float32`, `math.nextafter`, arithmetic and work/guard behavior; foreign row methods and equality must not execute unexpectedly. It must preserve the original path for foreign callbacks, observers, narrowed domains and unsupported values. Native budget checkpoints may change when real work is removed; identical native callback counts are not imposed.

The existing certificate-term gate is not a geometry receipt. It occurs in a different part of the reader, lacks complete geometry dispatch and coverage bindings, and carries [C057's unresolved funding and passive-storage concern](../reach-recording-validation-2026-10-23/checkpoint-057-comparison-admission-audit.md). Native dictionary type alone does not exclude a foreign key whose equality runs during lookup. Reusing that gate does not make these new checks free or safe.

## Cost result

For a completed admissible cold scan, use:

`saving = 6*(B-K) - S - I - A - F`.

Here `S` counts the new candidate comparisons and `I` the pending `point is q` identity comparisons, each under an explicitly one-unit comparison schedule. `A` contains every other added seed access, shape/type/finite/domain/coverage check, absolute value, bound operation, retained occurrence, pending-state/retirement operation and dispatch/passivity check. `F` contains extra fallback, restart, rescan and replay work. Any changed retained work also belongs in the ledger. This is a conditional equality only when the unchanged work is actually equal; otherwise it is an optimistic bound.

For seed index 133, only the preceding 133 points can have folds removed. The gross upper bound is therefore 798 charge calls. At most 134 new seam comparisons and 134 pending identity comparisons occur through the seed. **134 is not a general lower bound on seam comparisons:** existing screens can bypass many of those points. An earlier row alias can also shorten recognition. The actual baseline count cannot be replaced by 482 sphere vertices or an aggregate geometry counter.

The [standalone derivation](derive_evidence.py) gives both directions:

| Abstract coordinate sequence | Baseline folds | Proposed folds | New comparisons | Meaning |
| --- | ---: | ---: | ---: | --- |
| Increasing points `(1,0,0)` through `(133,0,0)`, then seed `(256,256,256)` | 134 | 1 | 134 | Gross 798, leaving an optimistic 664 before all setup, authority, recognition and fallback costs. |
| Repeated `(1024,0,0)` points, then seed `(1,0,0)` | 1 | 1 | 1 | No removed numerical work; the proposal adds work. |

The positive trace also has 134 charged identity recognitions, leaving **530** before all other setup, authority, retained-state and fallback work. The negative trace has 134 recognitions and therefore adds 135 comparison units before its other costs. These are synthetic arithmetic traces, not generated meshes, valid whole programs, original recordings or measured requests. A positive local example does not establish the necessary complete-request premise. Warm cache hits already avoid cold folding. Failed admission, repeated direct scans, cache eviction and request replay can add cost without providing a new saving. Interrupted folds must use their actual executed events, not a completed six-charge count.

An eager gate that separately funds all three source and all three stored leaf-type checks spends six new checks per vertex before its other costs. Under that explicit funding schedule, even its type checks consume the maximum six-charge-per-vertex gross opportunity; for a 482-point mesh they also exceed this nomination's 798-charge prefix ceiling. This rejects that particular duplicated full-scan admission schedule. It neither assigns a unit to every Python instruction nor excludes a cheaper properly justified authority mechanism.

No complete positive request bound is established. No product instrumentation follows from the 798-charge ceiling or the 664-unit synthetic residual.

## Validation and preservation

The source/arithmetic derivation checks thirteen exact source bindings, relevant AST structure, zero/subnormal/overflow bounds, illustrative float-order cases, a positive and negative abstract trace, seed synchronization and the conditional truncation consequence. It reproduced twice byte-identically on CPython 3.12.14 with empty stderr. [Validation](validation.json) and [reviews](reviews.json) separate executed calculations from general source proofs and unexecuted product claims.

The unchanged documentation preservation/link checker is the applicable integration gate. Published-candidate, actual-merge and final-main receipts each retain their own command, streams, complete before/after source inventories and actual Git identity. They do not establish a speedup or new recording success.

All 65 runtime files and every original fixture, helper, test, horizon, frame rate, equation, oracle, tolerance, limit, default and workflow remain unchanged. Preserve 100,000 shared operations, 30,000 ms, 32,768 operand bits, 256 numerical-cache entries and 64 cursor updates. Historical original recordings remain **24/28, failed**, with **P11/P16/P23/L03** unresolved. M1 remains rejected; C035 remains held including adverse timing. C057, full reach acceptance and historical LFS migration remain open. The full [GOAL](../../../GOAL.md) remains in progress.

The [next proposed task](NEXT-TASK.md) is a bounded authority-and-funding design for this actual cold-reader invocation. It must address the ordinary mutable accessor list and C057 explicitly before another numerical shortcut or runtime experiment is selected.
