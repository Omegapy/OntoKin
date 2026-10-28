# C053 independent evidence and next-scope review

Date: October 27, 2026 UTC. Reviewer: `/root/recovery`. Source: C052 commit `853c01589af790bc83bf52ed70b18dc87673873b`, tree `cadf049f90b45dbcf234199acb2e25a3f4c0eec8`. Scope: [Issue 26 ownership record](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6451681679), owner `interactive-reach06-child-pi-publication-20261027-c053-4d2b`.

**The C053 structural publication schedule is a source-level NO-GO. Retained observations cannot repair its missing child-value authority. A useful C054 question is an exact native128 endpoint certificate with a narrow, non-evicting publication gate, subject first to a complete charged feasibility bound.** No endpoint constants, runtime candidate or collector are produced by this review.

This reviewer previously recovered immutable published source. It did not author the coordinator's S1 schedule or the separate authority/cost reviews. It developed the C054 tag-only key nomination below; that nomination is a proposal for independent review, not an independently accepted implementation. [input-binding.json](input-binding.json) binds inspected original inputs, the reviewed coordinator drafts and external kernel source. Source files and selected JSON fields/functions were read as text; no product module, numerical routine, request, archived driver or test was executed.

## 1. C053 decision and the remaining evidence gap

The [frozen S1 schedule](../../checkpoint-053-schedule.json) keeps the original successful128 child and target calculation, then screens current native structure, scans parent keys, retains the child Interval alias and attempts publication through a final post-tick admission. It deliberately contains no historical receipt or exact endpoint certificate.

The [authority review](../authority/review.md) identifies a source counterexample: a preinstalled nested `ConstructionBudget.check` can wait until the second child `round64` tick, replace the child's cached pi with native `Interval(F(25,8), F(25,8))`, and retire itself before the optional gate. The already-computed shoulder/elbow intervals remain the original rounding inputs. The later current-state screen sees a clean callback graph and a structurally acceptable positive dyadic value. A final post-publication-tick recheck still cannot distinguish that history from an authentic computation. The original path discards the child cache and computes parent pi independently at a later cold use; S1 can instead return the false transferred value.

This is a conditional source mechanism, not observed corruption or an executed request. It requires an original successful128 path with child pi and a later parent cold use. Its scope is sufficient to reject S1's proposed authority rule, without disproving protected pre-mint admission or a genuinely independent value certificate.

The retained evidence has different boundaries:

| Record | Established historical scope | Missing publication fact |
| --- | --- | --- |
| [C047 capture](../../checkpoint-047-l03-capture.md) | Original/captured L03 failed with matching work at shared operation 100,001; 154 reader key calls, 153 provisional returns and the final exception. | Canonical setup chronology, successful child precision, child pi contents/origin and parent pi absence at the new boundary. |
| [C047 lifetime census](../../checkpoint-047-lifetime-review/census-001/result.json) | 311 ordered reader-cache snapshots; the source-bound no-capacity-eviction interval runs from key 0 entry through key 153's exception, with occupancy 112 to 165. | Setup before key 0, publication occupancy, child caches, outer cleanup, a future tail and changed candidate lifetime. |
| [C044 P23 report](../../checkpoint-044-angular-census.md) | The observed original P23 request failed in the producer before the reader boundary. | Any eligible independent-reader publication opportunity. This reader-only change cannot affect that observed producer failure. |
| [Original L03 source](../../../../../docs/language-design/planar-reach-v0.1/draft2-supplements/sources/l03-completed-action-new-owner.ok) | Two authored starts, at 0 and 2 seconds, with different target/branch pairs. | Two successful128 publications or two saved parent misses. Authored actions are not a cache-incidence census. |

These claims are attributed to the published reports. No C047 archive member was newly audited here. The C047 reader dictionary is also distinct from the shared work cache that reached 256 entries.

The relevant source route is `validate_reach_export -> build_reference -> ReachReference._build -> _event -> _canonical_targets`, followed by `_base_tip -> sincos -> pi`. Reference construction precedes the observed `_key_comparisons` interval. Target-key deduplication, later successful precision, warm parent pi, a cached base tip/sine-cosine result and zero trigonometric arguments all change incidence. [reach_conformance.py](../../../../../ontokin/reach_conformance.py) and [reach_reference.py](../../../../../ontokin/reach_reference.py) establish these source relationships; they do not measure a whole request.

## 2. A different authority premise: exact values

C054 should ask one bounded question: **Can an independently derived certificate authenticate the exact current native128 child-pi endpoints, and can fresh copies enter a genuinely absent parent slot through a fully charged, currently native, non-evicting route?**

This directly addresses S1's counterexample. If the admitted pair equals the exact result that the unchanged native parent pi factory would produce in the same domain, unknown prior child mutation history does not by itself make that transferred pair numerically different. The original target result remains untouched. A certificate is not a repair for a target previously affected by an original callback, nor does it excuse current callbacks, changed arithmetic dispatch or omitted cancellation behavior.

The certificate must identify the exact original outward endpoints, including rational normalization. Merely enclosing mathematical pi, using `PI64`/`math.pi`, reading a producer result, accepting a nearby interval or checking positive dyadic shape would not establish the required equality.

### Symbolic certificate target

Let `q = 2^128`, and define exact rational expressions

```text
S(d,N) = sum(k=0..N-1) [(-1)^k / ((2k+1) * d^(2k+1))]
T(d,N) = 1 / ((2N+1) * d^(2N+1))
L_d = floor(q * S(d,N))
U_d = ceil(q * (S(d,N) + T(d,N)))
```

The pinned `_atan_small` loop first stops at `N=28` for `d=5` and `N=8` for `d=239`, using the strict stopping inequalities already recorded in the [C051 cost ledger](../../checkpoint-051-cost-ledger.json):

```text
55 * 5^55 < 2^136 < 57 * 5^57
15 * 239^15 < 2^136 < 17 * 239^17
```

Both iteration counts are even, so the final zero-based index is odd and the alternate endpoint is `S+T`. The first rounded seed endpoints are therefore `[L_d/q,U_d/q]`. The original positive multiplication by 16 and 4 preserves this grid exactly. Native cross-endpoint subtraction then targets

```text
L = 16 * L_5 - 4 * U_239
U = 16 * U_5 - 4 * L_239
native128 endpoint pair = [L/q, U/q], with each Fraction normalized
```

This is a symbolic target derived from `_atan_small`, `grid`, `mul`, `sub` and `_sum_enclosure`; no integer endpoint was computed here. C054 must independently prove the first strict stops, interval sign/order and selected arithmetic branches, exact grid rounding, normalization and every original operand/prospective guard at the fixed 32,768-bit domain. The certificate must reproduce the pinned factory, rather than substitute a different approximation procedure. Certificate generation and numerical evaluation are not selected by this record.

## 3. A bounded safe-key lemma

A specific stricter parent gate avoids S1's recursive inspection of every key payload:

1. Require an exact native parent dictionary.
2. At the final admission after `remember`'s tick and domain synchronization, require occupancy `m < 256`.
3. Traverse resident keys without hashing them. Require each key to be an exact nonempty tuple, its first element to be an exact native string, and that string to differ from `"pi"`.
4. Reject any pi-tagged key, including one for another precision/domain. Publish only the native key `("pi",128,32768)`.

**Conditional proof.** With the relevant native kernel descriptors bound, a resident key cannot equal the incoming pi key: tuple equality reaches the unequal native strings at index zero and returns false before visiting deeper members. In CPython 3.12.14, generic dictionary probing compares the stored resident hash and invokes rich comparison with the resident key as its first operand. It does not rehash the resident key. Native tuple comparison supplies the early exit; deeper custom members therefore cannot run equality or hashing through this particular pi probe. Key iteration retrieves existing entries without hashing them, and table resize rebuilds indices from stored hashes. These are source facts in [tupleobject.c](https://github.com/python/cpython/blob/v3.12.14/Objects/tupleobject.c) (`tuplerichcompare`) and [dictobject.c](https://github.com/python/cpython/blob/v3.12.14/Objects/dictobject.c) (`dictkeys_generic_lookup`, `dictiter_iternextkey`, `build_indices_generic`).

The native `remember` source then finds no equal key and, with the fresh `m < 256` check, takes neither its replacement nor eviction deletion. No resident victim is retired by that insertion. A pre-tick absence/capacity observation alone does not prove this; every charged callback before final admission can change the cache. The final scan must occur after the last such callback, with the inspection-to-insertion interval independently closed.

This proves only the stated key-comparison/no-deletion property. It does not establish passive insertion in every interpreter state: the inspected CPython `insertdict` source includes a dictionary-watcher notification, and allocation/cleanup or other admitted observers still require analysis. Exact builtin tuple/string objects exclude ordinary Python overrides on those instances; the proof still needs authoritative builtin references/descriptors and the actual supported interpreter kernel. It must not assume arbitrary future monkeypatching, C-extension mutation or reentrant activity cannot occur merely because a present type check passed.

The externally inspected files are bound by Git blobs `918654fae898e7dd1cd2d1c705b49fbb2b9bf1ec` (tuple) and `7337e290e89c1027d286d493500c8016c726037b` (dict), with complete local copies and SHA-256 metadata recorded in [input-binding.json](input-binding.json). This is a CPython 3.12.14 source lemma; 3.11/3.13 kernel closure remains unreviewed. It is not a runtime compatibility result.

## 4. Concrete C054 schedule to freeze

Preserve the complete original child calculation and consider the optional path only after successful first128 target/rounding/closed-limit completion. Preserve original fallback for failed128, later success, empty child pi, unsupported current state and rejected admission. Never construct missing child pi or use parent numerical values as target authority.

Freeze these stages and their exact charged order:

1. Establish a safe new-charge/bootstrap path and the complete currently relevant native parent/child/work/budget/storage/function/descriptor graph. Bind bits, scale, operand limits and cache-domain records. Close nested `ConstructionBudget.check`, work/arithmetic observers, trace/profile and all other reachable effects over the actual interval.
2. Require the existing child pi entry. Inspect native endpoint fields and compare them to the independently proved normalized certificate. Price the certificate's provenance, constant storage, access and every type/value/limit check.
3. Prepare fresh endpoint Fractions and a fresh Interval, with every copy and retained logical occurrence charged. This avoids carrying the child Interval alias into the parent; it does not prove later identity/observer equivalence by itself.
4. Apply the non-evicting tag gate and prepay the exact final-admission work. Invoke original native `parent.remember(key, fresh_value, admission=final_check)`.
5. After its tick and domain synchronization, recheck the selected current authority, copied certificate fields, actual parent identity/domain, current occupancy and all resident tags. The final closure must be callback-free through insertion. A mismatch returns exactly False; original exceptions are not swallowed or relabeled.
6. Return the same original target tuple and use the original consumer. Prove the immediate cache-order/numerical convergence and price every changed later operation, retained lifetime and cleanup. Do not replace this proof with a blanket exclusion of future changes.

Existing centered-reader `_Guard` and product/source observation receipts do not supply free authority for this new route. Their source has different inputs and boundaries. The proposal still needs a current-native proof covering every omitted original parent-pi callback/prospective-error obligation and the new publication interval.

## 5. Cost-first stop gates

The [C053 ledger](../../checkpoint-053-cost-ledger.json) gives only a conditional opportunity: original successful native128 parent pi cold costs 165, an eligible hit costs 1, and one new native `remember` tick consumes another operation. **The room is 163 before every other new operation**, with zero original child work saved.

For matched completed native executions, retain

```text
saving = 164*H - Q - A_nonpublication - Delta_remaining
```

Here `H` counts actual original cold parent-pi calls replaced by authentic hits; `Q` counts newly reached publication ticks; `A_nonpublication` includes all other new work; and `Delta_remaining` is signed changed later work outside those terms. Failed/refused prefixes require their actual event identity, not an invented completed equation.

The tag gate still costs per key. Even counting only tuple type, nonemptiness, first-element string type and tag comparison gives a conservative floor of `4m` for one completed scan. Iteration, indexing, field access and retained occurrences add work. If both preliminary and final scans are selected, the floor is `4*(m_before+m_after)`; it becomes `8m` only under an independently established stable occupancy. The observed C047 reader occupancy cannot be substituted for either setup value.

Freeze the exact dependency graph and all new stages before obtaining new incidence. Count certificate access/storage, normalization/copies, key construction, every scan, every charge/precharge, synchronization, final rechecks, rejected/warm/empty/full/custom paths and cleanup. If the source-local lower bound on new work other than the already-counted publication tick is at least 163 for a single convergent publication, stop before generating endpoint constants or choosing a collector. A lower bound below 163 is only room for a proof, not positive whole-request saving. No fixed occupancy cutoff should be invented from the L03 fixture.

Other immediate stop reasons include an uncloseable native/precharge interval, a reachable observer or cancellation obligation that changes behavior, inability to reproduce all native prospective guards, failure of the tag-only kernel premise on a supported version, or later cache effects that eliminate the gain. The original first128 success and real first parent miss also remain unknown.

Only after a concrete authority schedule and complete charged bound survive should a separate bounded collector mechanism be selected for missing setup/precision/cache facts. [C052's next-scope record](../../checkpoint-052-next-scope.json) already explains why repeating a generic collector plan is insufficient. No collector or original request is selected here.

## 6. Outcome

C053 adds a precise rejection and a more concrete next proof target. It supplies no runtime saving, accepted recording or new release pass. The original28 state remains historical 24/28 with P11/P16/P23/L03 unresolved; C035 remains held, including adverse timing. The larger product goal and all remaining reach release gates remain open.

C054's value certificate and tag-only non-evicting gate are worth a bounded source review because they address specific authority and key-dispatch blockers. Feasibility remains conditional on exact current closure, supported-kernel proof and all-path cost. No implementation, numerical execution, collector, failed-tail continuation, hosted job or main integration is authorized by this review.
