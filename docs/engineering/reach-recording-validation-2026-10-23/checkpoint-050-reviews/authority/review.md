# C050 independent factorial-origin and authority review

Reviewer: `/root/origin_authority`. Date: October 27, 2026 (America/Denver).
Source: C049 `e828ee2d54b3c2a5a82bb332327fdce982a0f7f2`, tree `574c75e870d50aed5e5e96b34b454389074350fe`.

**Decision: NO-GO for H1, the specified fresh-owner screen relying on existing guards to preserve factorial-cache origin.** The native writer induction is valid under a closed, effect-free execution graph. H1 does not establish that graph. The source supplies a synchronous nested-callback counterexample to its admission, without assuming spontaneous or asynchronous mutation. A complete transitive native admission would be a different design; this review does not prove it impossible. No implementation or numerical execution is approved.

This is an independent source review, authored before the root C050 synthesis. The accompanying `result.json` binds inspected inputs by exact Git blob, size and SHA-256. Runtime modules and one existing callback-mutation test were read as text. No OntoKin import, product request, candidate arithmetic replay, archived driver, runtime test, benchmark or documentation checker was executed by this reviewer. C047 observations remain historical evidence read from their published review.

## 1. Exact hypothesis and mathematical premises

H1 preserves the raw tuple representation and existing native dictionary. It establishes that a new owner is an exact `_Arithmetic`, its cache starts as an empty native dictionary, precision/domain are native, its work is the native `ReachExecutionWork`, and its external callback is the native bound `ConstructionBudget.tick`. It may pin the current series helper definitions at that entry. It then treats factorial-key entries as factory-origin values across the request, relying on existing `_Guard.current`, `_Guard.original` and C035 observers for continued authority. It adds no maintained factorial receipt, no cross-call tuple reference, no wrapper on hits and no fresh series-helper screen at every miss.

This definition deliberately does **not** include a complete admission of the bound construction owner's nested `check`, all accounting maps/scalars, all transitive source records, or all subsequently used method/global/default/closure state. Checking that an outer method is native is not equivalent to checking those objects. That exact gap is tested below. A variant that adds only an initial `budget.check is None` screen is considered separately.

For genuine factorials and unchanged admitted native operands, the C048 identity is sound. With `F=(2D+1)!`, `Q=F*2^(2eD)`, `q=bit_length(Q)` and `L=2^q`, starting at `N_0=F*(L+1)` and adding `2F` gives `N_i=F*(L+2i+1)`. Dividing by `(2i+1)!` is exact, so the affine schedule produces the same coefficient and the direct last term is `L+2D+1`.

If `b=bit_length(F)`, the numerator multiplication is bounded prospectively by `b+q+1` bits, numerator advancement by `b+q+2`, and coefficient shifting by `2q+1`. Thus `2q+2` bounds the new operations and is dominated by the existing `_series_dyadic` width admission. This theorem requires the current fixed native cap. It does not certify operation reordering after a callback narrows that cap. The original first strict stopping degree, alternating tail, packed Horner polynomial and outward rounding remain separate preserved obligations. No candidate numerical calculation was run to reach these conclusions.

## 2. Native writer, reader and deletion closure

The following table concerns the reader cache `reference.a.cache`, not the distinct production/work cache `ReachExecutionWork._cache`. Source references are to the exact commit above: [reference](https://github.com/Omegapy/OntoKin/blob/e828ee2d54b3c2a5a82bb332327fdce982a0f7f2/ontokin/reach_reference.py), [centered reader](https://github.com/Omegapy/OntoKin/blob/e828ee2d54b3c2a5a82bb332327fdce982a0f7f2/ontokin/reach_reference_center.py), and [source plan](https://github.com/Omegapy/OntoKin/blob/e828ee2d54b3c2a5a82bb332327fdce982a0f7f2/ontokin/reach_reference_plan.py).

| Native route | Source lines | Effect and origin condition |
| --- | --- | --- |
| `_Arithmetic.__init__` | reference 72–87 | Creates a fresh empty dictionary at line 79. This initializes storage; it is not a certificate for later payloads. |
| `_series_factorials` | reference 461–469 | Sole literal runtime `series_factorials` key constructor. A miss starts with exact integers 1,1, computes the defining multiplication recurrence, converts it to a tuple and delegates publication/return to `remember`. A hit returns the cached payload directly. |
| `_Arithmetic.remember` | reference 346–356 | Generic key/value writer. It charges, synchronizes the domain, may invoke an admission callback, replaces/promotes an existing key or evicts the oldest at 256, inserts and returns the supplied value. Native series origin depends on the actual caller and exact delegated method. |
| `_Arithmetic.lookup` | reference 358–368 | Charges and synchronizes before `cache.get`. A hit deletes/reinserts the same object for recency. Under native keys/storage, no callback intervenes inside that promotion. A callback before the read may have changed the entry. |
| `_sync_cache_operand_limit` | reference 102–108 | On a changed domain, performs an additional tick, clears the cache and updates the cached domain. It erases entries; it does not mint origin. |
| Inline Cartesian read/publication | reference 1342–1354, 1390–1398 | Native bounded lookup/promotion/publication for the Cartesian rotation namespace. It can evict an older factorial entry at capacity, but its native key construction does not write that namespace. |
| `_Guard.lookup` / `_Guard.remember` | center 318–351 | Equivalent guarded cache reads/writes. Pending cursor publication is staged rather than immediately inserted. Ordinary native centered keys are distinct from `series_factorials`. |
| `_PendingCursors.publish` | plan 341–354 | Checks current cursor identities, then replaces/inserts staged cursor keys and may evict the oldest entry. Native staged keys are cursor/pose keys, not factorial keys. |
| `_ProductSession.publish` | center 1084–1105 | Replaces an already present centered-coefficient slot only if it still contains the exact previous object. Native key comes from `reference_centered_coefficients` at center 668. It does not resurrect an evicted entry or create a factorial entry. |
| `_SourceBatch` cursor ledger | plan 139–170 | Reads cache entries to maintain its owned cursor ledger. `discard_cursors` deletes still-owned cursor values. Native ledger contents do not include factorial keys. |
| Caller aliases and dynamic paths | reference 346–368; ordinary instance/class attributes | Generic `remember`, direct dictionary writes, replacement of `.cache`, altered instance/class methods, foreign keys/mappings and callbacks are not constrained to those native namespaces. H1 must exclude or detect them before optimized reuse; the table alone does not do so. |

A text inventory of all runtime modules finds `_series_dyadic` as the sole explicit caller of `_series_factorials` (reference 518) and `_series_coefficients` (reference 560). Native values pass through the same local variable. This inventory establishes ordinary source call sites, not the absence of external callers, aliases or dynamically replaced dispatch.

Under the additional premises that every actual key/write/callback is the original native one, that all hash/equality/scalar operations are effect-free, and that dispatch/domain authority remains valid, induction gives a useful result. The empty dictionary has no counterfeit factorial entries. A genuine cold factory creates genuine integer factorials; promotions preserve the same object; disjoint native writers do not replace a factorial payload; eviction or clear removes it; a later native miss reconstructs it. Therefore every retained factorial entry is genuine in that closed execution. No separate persistent numerical reference is needed for this conditional theorem.

Those premises must hold for the execution being optimized. They cannot be inferred from a native dictionary type, an initially empty cache, a current native method name, or the observed C047 boundary states alone.

## 3. Cold minting, exact tuple passage and storage

The genuine construction proof starts with `0!=1` and `1!=1`. Each native `range` factor and previous exact integer passes the original `_series_integer` charge and prospective guard before multiplication. Only after the entire loop does the factory create and publish the tuple. Authenticity requires the actual executing helper, its globals/builtins and its integer operands to remain native. Entry method identity alone cannot prove that later loop calls or final `remember` dispatch remain unchanged.

A failed construction makes no native factory publication before line 469. It may nevertheless have executed callbacks that completed other cache effects. A receipt must neither certify the unfinished tuple nor clear/rewind those effects. The original exception and completed mutations must survive.

With genuine native return dispatch, `_series_dyadic` keeps exactly the returned tuple in `factorials` at line 518 and supplies that object at line 560. Its degree search reads even-indexed factorials. Several charged search, power and tail operations occur between those two lines. A replacement of the cache entry after line 518 does not mutate the already retained immutable local tuple. It can affect a later factory hit, and a replaced helper can affect the later dynamic call.

The existing local `factorials` reference lasts through the ordinary calculation, including line 570. It is **not new storage** and must not be charged as an added persistent receipt. A newly added reference kept across invocations is different: after an ordinary eviction it can retain a numerical result outside the 256-entry cache. An object ID without such a reference has no protection against object-ID reuse. Neither treatment is silently free.

For native `bits=128`, the caller has `limit=36` and `last=73`. A new complete request offers a real opportunity for the first required native construction to establish conditional origin before later hits. C050 has not proved that the proposed authority remains valid to the degree-14 miss. No provenance is retroactively attached to C047's existing table, no hit count is inferred, and no failed tail is resumed.

## 4. Actual callback graph and the failed H1 admission

The active target observer is non-null. `_Guard.original` installs its local `observed` closure at center 283–296; `_orientation` invokes the direct source reseed through that route at center 590. A `hooks is None` gate therefore excludes the target.

The normal callback order is explicit:

1. `_Arithmetic.tick` captures both source/product observers, then calls `self.check` (reference 110–117).
2. Native `ReachExecutionWork.tick` dispatches to `charge`; `charge` invokes `external_check`, checks work/time, updates `operations` and `counts`, then calls the captured work observer (numeric 71–97).
3. The actual native outer callback is `ConstructionBudget.tick`. It first invokes its own mutable `check` field, then uses its operations scalar, limits mapping and time fields (construction 75–87).
4. The captured product and source observers run after successful original work. `_Guard.current` checks owners, source records, precision and current cap (center 233–271).

Existing source-observer replacement is detected: `_Guard.current` compares the current hook to `oracle_guard`. The present gap is not a missing observer-capture mechanism. It is that `_Guard.current` does not authenticate the construction owner's nested `check`, factorial entry contents, or `_series_*` method dispatch. C035's `_PRODUCT_ARITHMETIC_METHODS` at center 1295–1296 likewise omits all four series helpers. The product checks do not turn a factorial payload into a factory receipt.

### Synchronous callback counterexample to H1

Construct a native `ConstructionBudget` with a nested `check` callback that remains inert until the first genuine factorial tuple is retained. This nested callback is a supported constructor argument. The work's external callback remains the same bound native `ConstructionBudget.tick` throughout; there is no asynchronous mutation. The callback can close over the newly created arithmetic owner after its constructor returns, and remain inert during the first cold factory.

On a later leading tick, it replaces only the existing factorial entry with a different native tuple. Keep its length and all even-indexed values unchanged; keep entry 29 unchanged; change entry 15 to `F+1`, where `F=29!`. Owners, dictionary identity, precision, limits, outer callback identity, source observer identity and method identities remain unchanged. The callback returns normally.

The native lookup reads after the callback and existing observers, so a subsequent factory hit returns the replacement tuple. The existing guard predicates do not authenticate the changed entry. H1's original fresh-owner classification is still true by its own rules, but the payload no longer has factorial origin.

For a later genuine coefficient-key miss selected at degree 14, unchanged even factorials leave the caller's degree-search inputs unchanged. At interior index 7 the original helper computes `floor(F/(F+1))=0`, and its shifted/packed coefficient is zero. The proposed affine helper instead computes `floor(F*(L+15)/(F+1))*2^(2e(14-7))`, which is positive for this domain. Thus the two source formulas differ on a tuple admitted by H1. This is a symbolic control-flow and arithmetic counterexample; it is not a candidate replay, a claim of C047 corruption or a continuation of its failed request. Sufficient remaining budget for the illustrative operation is a premise of the constructed generic case.

H1 could exclude that nested callback only by adding a sufficient callback-owner admission. An initial `budget.check is None` check alone is still not a complete transitive admission. For that narrower H1+None variant, let a caller supply the exact native budget with a preexisting effectful `limits` mapping before the fresh arithmetic owner is created. The initial check field is None. During an ordinary native `tick`, the mapping's `__getitem__` used for `max_operations` can install the nested check for a later tick. The outer native method remains unchanged. This counterexample applies specifically when that mapping is not admitted. A gate that proves native maps, scalar fields and the complete called graph excludes it and is a different, unproved design here.

No counterexample is claimed for a fully established effect-free native graph. Such a graph would support the induction in section 2. C047's recorded native request is evidence for its identified execution; it does not itself implement a general runtime admission for every new request.

## 5. Dispatch, limits and original failures

A nested callback can also install an instance shadow for `_series_integer`, replace a class slot, change a function's `__code__` while retaining its identity, or alter globals/defaults/closures used by a later call. Python's already bound current operation and later dynamic calls must be distinguished: replacing an instance method during its tick does not retroactively replace that already bound invocation, but a subsequent loop iteration can resolve the replacement. A correct origin proof must cover the whole construction and actual returned object. Existing guards do not pin the series dispatch graph.

The inherited live-limit counterexample remains relevant. After the denominator and lane shifts, the original duplicate shift has prospective width `q`; the affine next `L+1` addition needs `q+2`. A permitted nested callback that temporarily narrows the cap to `q` therefore distinguishes refusal positions. `_Guard.original` intentionally lets the inherited operation perform its own prospective check after such a narrowing. A stale fixed-cap theorem or an early optional retry cannot replace that behavior.

`ConstructionBudget.tick` and `ReachExecutionWork.charge` retain and re-raise callback failures. `_Guard.original` wraps an inherited `ReferenceError` as `_OriginalFailure`, and centered `evaluate` raises the identical contained error at center 1261–1262. Original cancellation and callback exceptions must not be converted into a failed optional admission. An added monitor must not bind new foreign descriptors during error cleanup or mint origin after an interrupted publication.

## 6. Cost boundary, decision and follow-on scope

This reviewer confirms only the arithmetic opportunity and the authority implications of the cost design. The original complete coefficient miss has `4D+5` charged operations; the affine schedule has `3D+6` before new admission, so the complete gross difference is `D-1`. Degree 14 offers 13 gross operations, while the corresponding captured index-7 division offers only four gross prefix operations. The five completed new degrees in the retained C047 interval offer 56 gross operations. None is net saving or a complete-request total.

Adding new per-callback origin checks is a distinct repair policy with new charged work under budget-counting section 3. If that policy adds at least one charged check for each of the `3D+4` affine construction operations, even granting every other new cost free, the complete-helper saving is at most `(D-1)-(3D+4)=-2D-5`, or -33 at degree 14. This rejects that explicit repair policy even if its correctness were separately established; it is not a universal minimum cost for every authority mechanism. The independent cost reviewer owns the complete ledger and all path/request qualifications.

H1 fails a required origin/authority obligation, and the full transitive native graph and positive whole-request cost are not established. The bounded C050 raw-tuple hypothesis therefore cannot select an implementation. Preserve the conditional mathematics and native-writer theorem, publish the precise gap, and choose a different source optimization target as directed by the handoff. Do not relabel the rejected four-helper screen, factorial recomputation or another unpriced receipt variant as new progress.

Original28 remains 24/28 on preceding evidence; P11/P16/P23/L03 and full release acceptance remain open. C035 remains held, including adverse timing. This review ran zero runtime or numerical tests and makes no performance, release or main-integration claim.
