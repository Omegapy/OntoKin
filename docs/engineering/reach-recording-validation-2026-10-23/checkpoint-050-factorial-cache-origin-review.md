# C050 factorial-cache origin closure review

Date: October 27, 2026, America/Denver. Owner: `interactive-reach06-factorial-cache-origin-20261027-c050-7a91`. Branch: `work/reach06-factorial-cache-origin-20261027-c050-7a91`. Base C049: `e828ee2d54b3c2a5a82bb332327fdce982a0f7f2`, tree `574c75e870d50aed5e5e96b34b454389074350fe`. [Owned scope](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6447560284).

**Decision: NO-GO for the bounded C050 raw-tuple authority hypothesis. No runtime implementation is selected.** The native writer invariant can be proved conditionally, but relying on a fresh arithmetic owner and the existing observers does not enforce its callback and dispatch premises. A specified repair that adds a charged authority check at every affine construction callback costs more than the arithmetic it would remove. A complete positive request ledger and prospective degree-14 eligibility remain unproved. This does not establish that every raw-tuple design is impossible.

The next task is **C051 source feasibility of adjacent arctangent-term reuse in `_Arithmetic._atan_small`**. It concerns a repeated division within one call and requires no factorial-origin receipt. [Next scope](checkpoint-050-next-scope.json), [independent nomination](checkpoint-050-reviews/alternative/review.md).

## Scope and evidence

This checkpoint examines source and identified predecessor evidence. It does not import OntoKin, implement or replay a candidate, rerun an original request, execute runtime tests, continue the failed tail, benchmark, dispatch hosted CI or merge `main`. Original28 remains **24/28**, with **P11/P16/P23/L03** unresolved. C035 remains held, including adverse timing. The finite reach release and the full product goal remain open.

Fresh startup confirmed the final C049 head, its explicit ownership release, 95 existing branches and 25 open draft PRs, main `2bb4588e121fcfe99b4d42c734b15b38362f3642`, and zero queued/in-progress Actions runs. Main's older STATUS and the continuation's newer STATUS were read as distinct records; neither was edited. The new C050 branch was created from the exact C049 commit. All changes are new checkpoint files.

The local source is a **partial 959-file snapshot**, containing **128,738,871 bytes** from the **2,748-file** C049 tree. Every copied file matches the freshly retrieved Git blob. All 65 runtime modules also match the held C035 tree. The 12 historical archives recovered by C049 are present as exact bytes; C050 does not claim a new archive-member or CRC audit. C047's original pair and its 311 snapshots were not re-executed or independently re-censused here. [Validation and source inventory](checkpoint-050-validation.json).

Independent [numerical/authority](checkpoint-050-reviews/authority/review.md) and [cost/lifetime](checkpoint-050-reviews/cost/review.md) reviewers inspected and hash-bound their own selected inputs. The third reviewer nominated C051; its later completeness audit discloses that earlier role. [Review index](checkpoint-050-reviews.json).

## 1. Exact arithmetic opportunity

For genuine factorials, degree `D >= 1`, exponent `e >= 0`, `F=(2D+1)!`, `Q=F*2^(2eD)` and `L=2^bit_length(Q)`, C048 proves the affine schedule:

```text
N_0 = F*(L+1)
N_i = N_(i-1)+2F
C_i = (N_i/(2i+1)!)*2^(2e(D-i)), i < D
C_D = L+2D+1
```

The original floor divisions are exact in that genuine-factorial domain. The fixed native-width proof bounds the new prospective operations by `2q+2`, where `q=bit_length(Q)`, within the original caller admission. Neither this theorem nor tuple immutability proves the tuple's origin or permits a callback to narrow the cap without preserving the original refusal. [C048 proof](checkpoint-048-series-coefficient-feasibility.md), [C049 limitations](checkpoint-049-factorial-origin-feasibility.md).

| Path, under fixed native limits | Original charges | Affine charges before new authority |
| --- | ---: | ---: |
| Factorial hit | 1 | 1 plus maintenance, if any |
| Factorial cold miss, `last >= 1` | `last+1` | Original construction plus additions |
| Native128 factory, `last=73` | 74 | 74 plus additions |
| Coefficient full-key hit | 1 | 1 if all new coefficient checks follow its miss |
| Complete positive-degree coefficient miss | `4D+5` | `3D+6` |
| Complete D14 miss | 61 | 48 |
| Corresponding D14 index-7 pre-division prefix, including lookup | 30 | 26 |

Thus D14 has **13 gross complete-helper operations** and **4 gross operations at the corresponding observed prefix**. No candidate saving was measured. The five completed degrees 7, 8, 13, 17 and 16 offer 56 combined gross operations in C047's bounded interval. Seven initially resident coefficient keys belong to earlier setup; their construction chronology and internal factorial-hit counts are not observed by that census. [C047 lifetime review](checkpoint-047-lifetime-review/review.md).

## 2. Native cache-writer and identity closure

The following table covers the actual reader dictionary, `ReachReference.a.cache`. The separate `ReachExecutionWork._cache` and source phase/basis caches are different structures. Source locations refer to the immutable C049 files named in the independent reviews.

| Path | Native effect on reader cache | Factorial-origin consequence |
| --- | --- | --- |
| `_Arithmetic.__init__`, reference 72–87 | Creates an empty native dictionary. | No factorial payload is initially trusted or retained. |
| `_series_factorials`, reference 461–469 | Lookup; `[1,1]`; defining multiplications; `tuple(values)`; `remember`. | Only explicit native factory for the `series_factorials` namespace. |
| `_Arithmetic.lookup`, reference 358–368 | Tick, domain synchronization, read, delete/reinsert hit. | Promotion returns the same payload under native dictionary semantics. |
| `_Arithmetic.remember`, reference 346–356 | Tick, synchronization, optional admission, replacement/oldest eviction/insertion. | Generic key/value API; it does not authenticate a factorial payload. |
| `_sync_cache_operand_limit`, reference 102–108 | Additional tick, clear, update recorded domain. | Removes authority-bearing entries; a later miss must construct again. |
| Cartesian lookup/publication, reference 1342–1354 and 1390–1398 | Native promotion/replacement/bounded insertion. | Disjoint native Cartesian keys; may evict a factorial key at capacity. |
| `_Guard.lookup/remember`, center 318–351 | Similar native operations; pending entries may be staged. | Disjoint native centered uses; generic parameters remain broader. |
| `_ProductSession.publish`, center 1084–1105 | Replaces an existing exact previous centered coefficient value. | Does not create a factorial key or revive an evicted entry. |
| `_PendingCursors.publish`, plan 341–354 | Checks pending ownership; replaces or inserts cursor entries, evicting at 256. | Native cursor keys are disjoint; eviction does not fabricate factorials. |
| `_SourceBatch` cache readers and `discard_cursors`, plan 139–170 | Reads owned cursor entries; deletes only its retained matching entries. | Native cursor deletion does not create factorial payloads. |
| External aliases, generic `remember`, mapping replacement, class/instance override | Can write or change lookup/return behavior outside those native call sites. | Must be excluded by actual admission or retain the original generic path. |

Under a genuinely closed native graph, an induction is straightforward: the empty cache satisfies the invariant; successful factory construction creates exactly `0!=1`, `1!=1` and the multiplication recurrence; promotions preserve object identity; unrelated writes use disjoint keys; deletion/clear/eviction removes entries; and later cold misses reconstruct them. The sole explicit runtime factory caller is `_series_dyadic` at reference line 518. Its existing `factorials` local is passed directly to `_series_coefficients` at line 560.

Successful construction is required before minting any future origin claim. If construction or the leading publication callback fails, the factory does not reach its final native publication. Earlier callback effects need not disappear: unrelated or factorial entries may already have been changed by a callback. Neither speculative trust nor rollback of completed generic effects is justified.

The existing local `factorials` reference lasts through the active `_series_dyadic` call. It can survive eviction during that call; this is original temporary storage. A new cross-call strong reference would retain evicted numerical data and would require its own 256-entry capacity/lifetime treatment. C050 selects no such reference, wrapper, second slot, copied table or recycled-object-ID authority.

## 3. H1: fresh-owner admission plus existing observers

**H1 is the concrete hypothesis rejected here:** establish an initially empty, exact `_Arithmetic` owner and native dictionary; recognize native work and the outer bound `ConstructionBudget.tick`; then treat factorial entries as factory-origin values while relying on the existing guards to maintain authority. H1 does not include a complete transitive admission of the budget owner's nested callback, maps/scalars, every series helper, descriptors, globals, builtins, defaults or closures. A private Boolean marking the owner native does not add that missing proof.

The real callback sequence is:

1. `_Arithmetic.tick` captures both source/product observers and calls its check.
2. `ReachExecutionWork.tick/charge` captures its source observer and invokes `external_check`.
3. The invoked native `ConstructionBudget.tick` calls its mutable `check` if present, then reads/writes its own counters, limits map and elapsed state.
4. After that callback returns normally, `ReachExecutionWork.charge` checks work/time, updates its counters/map, then invokes the captured work observer.
5. `_Arithmetic.tick` then invokes the captured product observer, followed by the source observer.

The actual reseeding route is `_Guard.original`, which installs a non-null source observer. Its `current()` checks owners, selected operands/records, precision and limits. It detects replacement of its own observer. It does **not** authenticate factorial payloads, all four series helpers or the nested `ConstructionBudget.check`. C035 product authority covers a different set of methods and values; it does not close these missing relationships. A `hooks is None` gate excludes the intended route. [Callback source](https://github.com/Omegapy/OntoKin/blob/e828ee2d54b3c2a5a82bb332327fdce982a0f7f2/ontokin/reach_reference_center.py#L233-L306), [work callback](https://github.com/Omegapy/OntoKin/blob/e828ee2d54b3c2a5a82bb332327fdce982a0f7f2/ontokin/reach_numeric.py#L38-L99), [construction callback](https://github.com/Omegapy/OntoKin/blob/e828ee2d54b3c2a5a82bb332327fdce982a0f7f2/ontokin/construction.py#L55-L89).

### A concrete admitted-gap sequence

Use a nested construction-budget callback that is already installed, remains inert through the genuine initial factory construction, and replaces the factorial cache entry on a later factorial-hit tick. The outer bound method, arithmetic/work owners, native cache type and operand cap remain unchanged. This requires no spontaneous or asynchronous mutation. The lookup invokes its tick **before** reading the cache; the existing observers do not reject the altered factorial payload. The caller then passes the returned replacement tuple.

For the D14 source case, let `F=29!` and change only odd entry 15 of an otherwise genuine length-74 tuple to `F+1`. Preserve every even factorial entry and entry 29. The degree search uses even entries, so this isolated replacement need not change the selected degree. At index 7:

```text
original factor: floor(F/(F+1)) = 0
affine factor:   floor(F*(L+15)/(F+1)) > 0
```

The original packed coefficient is zero and the rewritten one is positive. All values can be native integers within the original cap. Native types, owner identity and a plausible tuple length therefore do not justify the affine rewrite. This is a symbolic source counterexample, not an executed hostile probe or an allegation about C047's observed tuple.

Screening only `budget.check is None` does not constitute a complete transitive closure either: an unscreened effectful limits mapping can install a nested callback during a native budget lookup. Exact scalar/map types and class/code/instance/descriptor authority must be addressed, along with the callbacks invoked by each new charged check. A complete, transitively native and non-effectful graph could support the conditional writer theorem; C050 does not disprove such a future design. It has not specified or costed one that admits the complete target request.

### Live limits and failure identity

The original source observer deliberately latches a narrowed cap while allowing the original operation's prospective guard to refuse. After the common denominator/lane construction, a temporary cap of `q` admits the original repeated shift, whereas the affine `L+1` addition needs `q+2` prospective bits. Removing or reordering that boundary can therefore change the first refusal. An early optional fallback cannot suppress an original error, and a late invalidation cannot undo completed candidate arithmetic or cache effects. Preserve the original exception object, its callback identity, observer restoration and pending-publication behavior. C048's unchanged-cap theorem does not settle this case.

## 4. H2: a charged check at every construction callback

H2 is an explicit conservative repair policy: add at least one newly charged origin/authority check at **each affine construction-operation callback**. It is not the prior 14-check per-miss screen, and it is not a universal minimum cost for all authority designs.

The affine constructor has `3D+4` such operations before lookup/publication costs. Even if every other new cost is omitted from this optimistic upper bound:

```text
complete saving <= (D-1) - (3D+4) = -2D-5
D14 complete saving <= -33
corresponding prefix saving <= 4-25 = -21
```

Monitoring its own newly charged callbacks, avoiding recursive monitoring, startup, rejection, invalidation, output and cleanup require further treatment. No safe executable monitor was selected. These lower-cost floors alone reject this specified policy for a positive operation saving. [Full charged ledger](checkpoint-050-cost-ledger.json).

## 5. Full-request ledger and target eligibility

The raw-tuple design has no approved complete added-cost ledger. The ledger retains separate unknowns for owner/graph admission, factory minting, every factorial hit, coefficient misses and low-degree filters, rejected paths, callback checks, lifetime/invalidation, copies/output and changed later recomputation. No unknown term is set to zero.

The original cold `last=73` construction costs 74 and remains baseline work. Only its new maintenance belongs in the incremental difference, once at the actual construction point. `_series_dyadic` asks for factorials before it selects/refines the degree and before the coefficient lookup. Any new factory-side work therefore also affects later coefficient hits, low-degree cases, the later degree-bound rejection at lines 535–537, and subsequent interruption. It is not incurred on the pre-factory rejection or zero-return paths at lines 504–517. D1 offers zero complete-helper gross room; D2 offers one. D0 is outside the native selected-degree route and keeps its generic behavior.

For a hypothetical completed matched request, saving is the sum of eligible `D_i-1` differences minus **all** actual added request work. For actual L03, the complete baseline and candidate tail are unavailable. The interval's 56 completed plus 4 corresponding-prefix gross operations cannot establish a successful whole-request total, and `100001-60` is not an optimized request result.

Prospective D14 eligibility must start at a new complete request's required first genuine `last=73` construction and survive every intervening admitted callback, cache event and local dispatch. C047's existing table cannot be retroactively receipted. C050 establishes no such protected mint-to-D14 chain and does not resume the failed tail.

| Required exit condition | C050 result |
| --- | --- |
| Conditional native writer/origin induction | Established under explicitly closed native premises. |
| Enforced H1 admission and continuous callback/dispatch authority | Failed; concrete unscreened nested-callback replacement. |
| Actual observer, current-limit and failure preservation for affine route | Unproved; fixed-cap mathematics alone is insufficient. |
| Raw tuple capacity without extra persistent retention | Conditionally compatible; no extra slot selected. |
| H2 positive complete-helper saving | Rejected by bounds −33 complete / −21 prefix at D14. |
| Positive whole-request net and mint-to-D14 eligibility | Unknown; no implementation GO. |

## 6. Distinct next task

In `_atan_small`, iteration `k` computes `following = exact(power, 2*k+3, "div")` after updating `power`. If it continues, iteration `k+1` recomputes that same quotient as its `term`. Under unchanged native arithmetic, retaining the already computed local value preserves the exact series. For `N >= 1` completed iterations, the original positive path costs `4N+3`; retaining the first division and carrying subsequent terms costs `3N+4` before new admission. The gross opportunity is **`N-1`**.

This is a source-derived opportunity within one invocation. It adds no persistent numerical cache and depends on no factorial receipt. It still requires a finite authority/limit/callback proof, preservation of the first strict stop, alternating-tail enclosure and outward grid, all-path costs, and actual complete-request eligibility. A charged checkpoint at every omitted division consumes the entire gross opportunity. [Exact nomination and limits](checkpoint-050-reviews/alternative/review.md).

C051 should decide that single hypothesis before choosing code. If source evidence cannot establish request incidence, prepare a separately reviewed passive observation plan instead of inferring events. Preserve all original fixtures, equations, independent source authority, error/cancellation identity, pending publication and **100,000 operations / 30,000 ms / 32,768 operand bits / 256 cache entries / 64 cursor updates**. C050 authorizes no runtime implementation or release acceptance.
