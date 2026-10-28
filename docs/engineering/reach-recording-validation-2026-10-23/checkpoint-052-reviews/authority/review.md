# C052 independent numerical and authority review

Reviewer: `/root/c052_authority`. Date: October 27, 2026, America/Denver. Source: C051 commit `9aeab3e1b4e05e47a0284da55925f41cccc23964`, tree `c661e9b40d5ba8390d4ed96725e41198f67655f9`.

**Decision: no implementation is selected.** Reusing the parent arithmetic at the first 128-bit canonical-target precision preserves the numerical calculation only when its pi entry has the exact original independent value, its current dispatch/domain is proved, and the changed callback and cache history is separately admitted. R1's current structural screen does not prove the pi entry's origin. A native, well-formed, positive, dyadic false entry gives a concrete wrong target. R2's full resident-entry scan remains insufficient to prove that origin and has an occupancy-dependent cost barrier. R3's empty-parent restriction avoids reading old numerical authority, but cannot trigger during the ordinary native fixed-domain reference-construction path.

This is source analysis. No OntoKin module, numerical candidate, request, archived driver, runtime test or benchmark was executed. The only commands were source reads and file metadata/hashes. The [input binding](input-binding.json) identifies the selected bytes and its read/hash timing limits. The coordinator's snapshot is partial. Publication, documentation validation, remote ownership and complete-request input closure are separate coordinator responsibilities.

## 1. Exact transformation and native numerical theorem

`ontokin/reach_reference.py:674–735` first computes exact source algebra with the supplied parent arithmetic. It checks the annulus, singular origin and selected branch; derives cosine, radical, shoulder coefficients and their exact signs; then iterates `PRECISIONS = (128, 256, 512, 1024, 2048)`.

The original line 710 constructs a fresh `_Arithmetic(arithmetic.work, arithmetic.check, bits=precision)` on every precision. The reviewed substitution is confined to that line at the first 128-bit precision: use the existing parent after admission; otherwise construct the original child. The common exact prefix, every other precision, the entire precision body, `_atan_small`, `_Uncertain` retry and final failure remain unchanged.

The constructor creates a new empty numerical cache, derives `scale = 2**bits` with the live operand-limit check, and initializes both arithmetic observer slots to `None`. Construction itself performs no charged tick. If `work` is present it selects the current `work.tick`, rather than the supplied `check` argument. Consequently matching a parent's saved check requires the same native bound function and owner, with no instance shadow; comparing the identities of two freshly obtained bound-method wrapper objects is not the relevant proof.

Under an unchanged fully native graph, the first precision has identical mathematical behavior if all of the following are established:

- The parent has exact native `bits=128`, `scale=2**128`, work/check ownership and live operand domain. The original child-constructor guard would pass at the same boundary.
- Both arithmetic observer slots are absent, as they are in the fresh child. All reachable work and nested construction observers/callbacks are either excluded or admitted by a separate complete proof.
- A parent pi hit supplies exactly the enclosure produced by the unchanged independent pi algorithm at this precision and operand domain. Its native Fraction fields and Interval endpoints remain unchanged.
- No admitted callback or other supported mutation changes these premises during the calculation. All remaining original operand/prospective guards and exception propagation retain their meaning.

The precision body reaches the arithmetic cache only through `pi`. It does not invoke `sincos`, the factorial table, or the pose cache families. On an original child the first reached pi lookup misses; later pi calls at that precision hit the completed entry. On a parent with the authentic same entry, the first lookup hits instead. The exact Machin-series construction, dyadic grid and native arithmetic make those pi endpoints equal under the stated premises. Every subsequent primitive receives the same inputs. Induction through the unchanged body therefore gives the same shoulder and elbow intervals, the same first `_Uncertain` point or success, the same binary64 rounding, the same positive-half-turn shoulder normalization, and the same selected-branch limit check.

This is equality with the original enclosure, not merely an enclosure that contains mathematical pi. A different but valid enclosure can change refinement or rounding decisions. A previously completed value also does not replace the proof that the original fresh calculation would satisfy its prospective operand checks under the current domain. A genuine completion under the identical native algorithm, precision and unchanged limit can supply that fact; a cache key alone cannot.

## 2. R1: current structural admission does not establish pi origin

R1 admits an exact native parent, native work/check ownership, matching 128-bit precision and scale, the current domain and empty arithmetic observer slots. Grant even that the current methods, native mappings and scalar types are all unchanged. These present-tense facts do not prove how an existing numerical entry was obtained.

The independent cache is an ordinary mutable dictionary. `pi` forms `("pi", self.bits, self.operand_limit)` and returns any non-`None` lookup result without recomputing or validating the pi enclosure (`reach_reference.py:389–395`). `lookup` ticks and synchronizes the domain, then promotes the resident object by deletion and reinsertion (`358–368`). A structurally valid Interval is not evidence of its mathematical origin.

### Concrete source counterexample

At the unchanged default operand cap, let the parent contain:

```text
key   = ("pi", 128, 32768)
value = Interval(F(25, 8), F(25, 8))
```

Use native source payload values `lengths_m=(2,1)`, `target_m=(1,0,0)`, branch `elbow_positive`, and closed limits that include zero and the original positive pi64 elbow, such as the ordinary symmetric pi64 joint limits. All unrelated operations and limits succeed. The false entry has native types, ordered endpoints, positive value, a dyadic denominator, exact grid alignment, and lies strictly between 3 and 4. It can survive all those shape and coarse range checks.

The common exact algebra gives radius 1, cosine -1, radical 0, `k=1`, shoulder Cartesian coordinates `(1,0)` and positive elbow sign. R1 therefore uses the false interval for the elbow, independently computes shoulder zero, and returns exactly `(0.0, 3.125)`. The parent cache is not read by the common exact prefix, so the unchanged original reaches the same algebra before making its fresh empty child.

The original cannot produce that elbow value. For the unchanged native series, the first atan enclosure's lower endpoint is above `1/5 - 1/(3*5**3) - 2**-128`; the second enclosure's upper endpoint is below `1/239 + 2**-128`. The intervening multiplications and subtraction preserve dyadic grid alignment. Thus the computed pi lower endpoint is above

```text
1184/375 - 4/239 - 20*2**-128.
```

Before the tiny grid allowance, its margin over `25/8` is exactly `11183/717000`, greater than 0.015. Native binary64 rounding cannot bridge that gap. If the original returns a target, its elbow differs from 3.125; if a subsequent original refinement or failure occurs, R1's already returned false target still does not preserve that behavior. This rejection does not rely on claiming an unexecuted original request or a separately computed exact pi64 rounding-cell audit.

This is a counterexample to R1's stated admission, not an allegation that a retained P11/P16/P23/L03 request had a corrupted cache. A protected fresh-factory history could rule out the counterexample, but R1 does not establish that history. A scan of current native classes, keys, types and endpoint shapes cannot retroactively establish it either. Native Fraction and frozen dataclass type names alone are not an immutable provenance mechanism.

## 3. Callback and failure identity remain separate obligations

The source callback order is `_Arithmetic.tick` → `ReachExecutionWork.tick/charge` → its `external_check`, commonly `ConstructionBudget.tick` → that budget's nested `check`. After normal returns and the resource/counter checks, the captured work observer runs; arithmetic then runs its captured product observer followed by its source observer. Both work and construction owners retain and rethrow the same callback exception object.

Empty arithmetic observer slots do not prove that the work observer or nested construction callback is absent. A native outer bound `ConstructionBudget.tick` is compatible with an arbitrary nested callback. Added admission charges invoke this same graph and therefore also need safe charging and current-state checks.

The source counts for the simple payload above, conditional on the first precision taking its successful native path, are independently reconciled with the cost reviewer: 26 common exact-prefix ticks; then 185 ticks with a fresh pi miss or 21 with a parent pi hit. The full call is therefore 211 versus 47 before new admission. The same 21-tick body applies to the false point entry. The gross difference is 164; avoiding construction contributes zero.

For a genuine pi entry and a successful native first precision, bare reuse with an admitted effectful nested callback can miss a preinstalled fixed sentinel on call-local callback 48: the original reaches it, whereas bare reuse returns after 47. A fixed successful admission of `G` additional ticks changes that example to callback `48+G`, for `0 <= G < 164`. These ordinals apply only to that specified schedule. They are not measurements, do not apply to an unspecified future gate, and do not disprove a gate that closes the entire callback graph.

The current `exact` operation ticks before its operand and prospective intermediate checks. Cache synchronization itself can tick and clear the cache if the live operand limit changes. A parent can have a stale synchronization marker that a fresh child would not have. That adds another event and possible exception before reuse. A valid admission must account for the original constructor guard, the synchronization marker, limit changes during callbacks, malformed domains and interrupted calculations; checking the initial integer cap once is insufficient.

The centered `_Guard.original` is an active observer with plan, batch, source-record and product-session obligations. Its explicit rule permits a narrowed cap to reach the original prospective arithmetic refusal. It cannot be silently removed or treated as a generic safe callback. In the ordinary native `build_reference` path, however, canonical targets are computed during reference construction before the later supplied-byte centered sampling/batch work. The original fresh child has no inherited arithmetic observers. This makes a distinct observer-free constructor domain plausible; it does not establish request eligibility or authenticate every reachable callback.

## 4. R2: a full current cache scan is neither a provenance proof nor a free gate

R2 adds a fresh current native-graph screen and a scan of every resident parent cache entry before the R1 substitution. Its declared optimistic charge floor is one combined entry inspection per resident, with all other class/function/global/instance/field/limit checks, copied values, origin work and rejection costs charged separately.

For occupancy `m`, the immediate upper bound is `164 - m - A_other`. At `m=256` it is at most -92 before those other costs; at `m>=164` no strictly positive immediate room remains. These are bounds for this chosen per-entry scan, not a universal lower bound on safe admission. A separate design could restrict occupancy, avoid reading existing pi, or establish a protected lifetime earlier. Actual canonical-entry occupancy was not observed here.

Even a successful full structural scan does not authenticate the pi value in section 2. To close authority, a design must verify the exact numerical result against an independent defining proof, or enforce a trustworthy computation-to-use history across every supported writer and callback. Merely remembering that the owner started empty or that current methods are native is insufficient after a mutation-capable interval. A newly retained receipt, strong numerical reference or copied table also needs its own bounded lifetime and charging.

The relevant native graph includes the canonical helper and payload access, all used arithmetic and cache helpers, Interval construction/storage, Fraction construction/operators/comparisons/conversion and inherited storage dispatch, work/counter/map/clock behavior, the complete external and nested construction-budget graph, and any active observer. Existing product-native checks cover a different graph. This review does not claim that listing these dependencies implements an admission or proves its cost.

## 5. R3: empty-parent-only origin is sound locally but has no ordinary constructor incidence

If an exactly native empty parent is admitted together with a complete fixed-domain callback/dispatch proof, its first pi construction can establish new local origin without trusting an old cache entry. The canonical body performs the same cold computation as the original child. It has zero immediate pi saving; it only changes where the new entry survives afterward.

On the ordinary unchanged native reference-construction path, an empty-parent-only gate does not trigger. `ReachReference.__init__` calls `_initialize` before `_build` (`2253–2286`). `_initialize` calls `p.quaternion` for each object (`2316–2342`). Native quaternion either uses an existing cache entry or completes a `remember`, including the identity-quaternion route (`891–904`). Any successful valid reach chain requires three distinct object owners (`2344–2362`). Therefore the parent cache is nonempty before `_build` can start the first reach and call `_canonical_targets`.

Ordinary fixed-domain lookup promotion, replacement and bounded insertion/eviction preserve nonemptiness. The arithmetic cache clear is the operand-domain synchronization branch, which is not taken under the fixed-domain premise. Centered batch cursor retirement occurs in the later consumer; it is not a hidden native clear before this constructor's canonical setup. Interrupted operations do not establish a later successful setup path.

This excludes R3 only for the stated native, unchanged-domain constructor route. Direct helper use, an independently admitted domain reset, custom mutation or a different lifecycle is a separate domain. No such eligible complete-request incidence is demonstrated. Even there, later benefit would need the exact first future parent pi use, retention until that use and all added costs; the cold canonical call itself has no 164-operation gain.

## 6. Cache history, refinement and later work

On an admitted warm parent hit, lookup moves pi to the end of its insertion order. On a cold parent, a successful pi construction inserts it and can evict the oldest unrelated entry at the 256-entry cap. An original fresh child's pi operations do neither to the parent. Because the precision body has no other cache family, these differences can be stated precisely without inventing a broader cache trace.

A first-precision `_Uncertain` can leave a completed 128-bit pi in the reused parent even though the subsequent precision uses a fresh child and the original would have discarded its first child. A later selected-branch failure likewise differs in retained cache history if the shared owner survives for diagnostic or direct-helper use. Whether an entire failed reference constructor becomes unreachable does not justify silently importing a success-path saving into a failed call.

Cache effects need not imply wrong native mathematical values, but they change later hits, evictions and recomputations. Later centered consumers can also have source/product receipts and pending publication/retirement rules tied to the same owner. Complete request savings cannot be inferred from the local 164-operation opportunity. The existing `_targets` dictionary already deduplicates equal `(lengths,target,branch,limits)` keys at `3489–3499`; authored action count is not a canonical-call count.

## 7. Supported next direction and review limits

A distinct source question is to retain the original fresh canonical child and, only after the target calculation and its original checks succeed, consider publishing that child's freshly computed pi into the existing parent cache for a later native use. This avoids treating an existing parent value as authority and preserves the original canonical pi computation and refinement. It is a hypothesis, not an approved design.

Such a proposal still must freeze the publication boundary, prove the child's result/current fields and callback history, preserve original exceptions, price all new callbacks and value/reference copies, honor capacity and ordering, and establish actual later use before eviction. It must not publish a failed refinement or cancelled calculation as successful authority. Parent key access and mutation can themselves encounter custom entries or callbacks; the new proposal needs a concrete safe gate and complete cost review. No new numerical storage allowance or producer-derived oracle is implied.

R1 is rejected by the concrete false-pi entry. R2's structural scan does not repair origin and has the stated immediate occupancy barrier; a restricted or amortized fully closed design remains unresolved. R3 gives no ordinary native fixed-domain constructor eligibility. No implementation, collector or numerical execution is selected. Original28 remains 24/28; P11/P16/P23/L03 and all later release roles remain open; C035 remains held, including adverse timing. Those are inherited statuses, not newly executed results.
