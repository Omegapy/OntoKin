# C045 independent authority review

Reviewer: `/root/authority_review`. Date: October 26, 2026, America/Denver.
Reviewed source parent: `91e8899ad90f04292dd4aee5aaec8b730b397d45`, tree
`11d1ce9acc2cb4fa93be44c4772a9e8e3b3270ff`.

**Decision: no implementation approval for `B-Angular/full-entry-audit/0.1`.**
The defined batch audit cannot produce a positive charged bound for the observed
32-call group. Its numerical width prerequisite is independently supportable,
but its callback, storage and return-authority obligations remain incomplete.
The cost rejection does not establish that every possible conditional angular
reuse design is impossible.

## Scope and evidence

This review reads source and retained JSON. It executes no product import,
request, candidate numerical replay, runtime test or archive restoration. The
root's retained-data audit, `analysis-002.json`, reports the original cache
timeline and the concrete cost arithmetic. I inspected that record and the
[C044 census](../checkpoint-044-census.json); I do not claim independent execution
of the root's complete cache replay.

The principal source locations are:

| Source | Relevant locations and role |
| --- | --- |
| [reach_recording_fast.py](../../../../ontokin/reach_recording_fast.py) | `RecordingFloatExcess`, line 50; `recording_float_excess`, lines 527-598; `_require_domain`, lines 713-724. |
| [reach_numeric.py](../../../../ontokin/reach_numeric.py) | `charge`, lines 71-94; `lookup`, lines 120-137; `remember`, lines 139-176; cache-domain synchronization, lines 248-260; `exact`, lines 321-341. |
| [reach_recording_capture.py](../../../../ontokin/reach_recording_capture.py) | `_PhasePublication`, lines 1351-1410; `_CapturedPhase.sample`, lines 1446-1492; first-phase bound capture, lines 1603-1615. |
| [construction.py](../../../../ontokin/construction.py) | `ConstructionBudget.tick`, lines 75-87; compiler-owned reach work, lines 202-208. |
| [reach_phase.py](../../../../ontokin/reach_phase.py) | Shallowly frozen `PhaseBound`, lines 39-57. |
| [budget-counting section 3](../../../language-design/planar-reach-v0.1/budget-counting.md#3-preflight-exact-accounting-and-finite-reuse) | New checks, lookups and copied logical values remain charged; reuse does not remove current authority or cancellation requirements. |

Line numbers identify this source parent. Earlier C043 cold-domain rejections
and C044's execution-window qualification remain unchanged.

## The concrete schedule under review

The candidate concerns a structurally eligible first-excess batch within a
captured phase. It keeps every original whole-result cache operation and its
ordering. An optional seed payload would belong to an existing whole-result
entry; a bounded reference would last for the current batch. It would create no
additional numerical-cache entry.

Only the thirteen prefix operations producing `source_leaves`, `e`, `g` and `q`
are considered for reuse. The first computation remains original. The candidate
retains the ten ordinary position operations, the four additional position
operations when `dynamic=True`, both original short-circuit comparisons, the
late `16*q` multiplication, optional cell radii, and the distinct warm and cold
return paths.

The stated native-interval policy audits each current cache entry with one
charged key admission and one charged value/lifetime admission before relying
on a batch-wide certificate. This **two-charge policy is part of this candidate's
definition**. It is not a lower bound proved for every possible representation,
fixed-block audit, or independently authenticated provenance design.

## Existing phase state does not establish the required authority

`ReachExecutionWork.charge` first invokes `external_check` when present and later
invokes its captured `_source_after_charge` observer. Its category update uses
the mutable `counts` dictionary. A native work type does not establish native
instance dispatch, ordinary category keys/values, an unchanged observer, or the
full external callback chain. The compiler ordinarily binds `external_check`
to `ConstructionBudget.tick`; that budget has a further mutable `check` callback,
limits and dispatch of its own.

The unchanged cache operations also matter to a batch-wide interval.
`lookup` performs dictionary membership and retrieval, and `remember` performs
membership, insertion and possible eviction. A native `OrderedDict` can contain
foreign keys or values. Key hashing/equality can execute foreign behavior;
removing the final references to an entry can invoke finalization. Container
identity, size and `_cache_generation` alone do not authenticate those contents.
Direct mutation of the dictionary need not advance the work object's generation.

For the stated complete-audit schedule, examining keys and value/lifetime
contents is therefore a relevant obligation. Passing only the two outer checks
would not finish it: nested operands, dispatch, callback behavior, and actual
reference-release boundaries still need proof. The cost lower bound deliberately
grants all that further work for free.

The existing captured-phase objects do not supply this proof. `_require_domain`
checks the operand cap and Cartesian selector/dispatch. `_PhasePublication.admit`
checks source and bound identities near phase completion. Neither authenticates
a native work/counter/cache interval across the whole excess batch.

There is also no immutable integer seal in the existing bound-input tuple.
`begin_captured_phase` obtains `inputs` directly from bound fields and retains
those Fraction objects. The final comparison uses the retained aliases. It
cannot be treated as independent evidence that a Fraction's backing integers
have remained unchanged. This observation identifies a missing premise for the
new reuse route; it is not a new execution finding about the original request.

A different design could limit admission to the short interval after each
original whole lookup and before position arithmetic. Such an interval would
not include another cache operation. It would require a separate fresh
work/callback/counter/operand proof at every use. The current source contains no
reusable certificate that makes those checks free. An added observer or changed
counter representation would be a separate design with its own charges and
lifetime obligations.

## Independent numerical-width check

Assume native nonnegative integer `t` and `c`, canonical native Fraction `sq`
with positive denominator, and at most 2,048 bits in each integer input field.
Also assume the exact source constants and arithmetic dispatch are authenticated
and the current operand cap remains 32,768 throughout the omission interval.

The original `exact` helper precharges, guards its actual operands, guards the
unreduced prospective numerator/denominator widths, calculates, then guards the
result. Propagating its conservative addition and multiplication bounds without
taking credit for rational reduction gives:

| Completed prefix value | Numerator-bit upper bound | Denominator-bit upper bound |
| --- | ---: | ---: |
| `source_leaves` | 2,050 | 2 |
| `e` | 2,102 | 94 |
| `g` | 2,157 | 170 |
| `q` | 4,327 | 2,314 |

I independently derived these bounds from the source expressions. They use
`MAX_RECORDING_ROTATION_STEPS - 1 = 9999`, `AXIS_ERROR = 1/2^74`, and
`PRODUCT_ERROR = 1/2^91`. Every intermediate operand, prospective width and
result is bounded by 4,327 bits under these premises. Reduction cannot enlarge
the bounds for these positive-denominator rational operations.

The retained current `sq` has numerator/denominator widths 1,025/1,075, so a
1,024-bit gate would incorrectly exclude the observed numerical input. A
2,048-bit gate contains it. This is a numerical prerequisite only. It supplies
no callback or cache authority, no proof that any candidate hit is eligible,
and no permission to skip the original range comparisons.

## Cost decision and its limits

The retained census has 32 completed cold calls with one exact angular
signature. The original entry cache contains 256 entries. Keeping the first
prefix computation gives at most `13 * 31 = 403` omitted prefix charges. The
defined audit requires at least `2 * 256 = 512` charges.

Even if all other admissions, snapshots, copies, storage checks, lifetime work
and fallback costs were zero, an admitted traversal of that schedule has saving
at most `403 - 512 = -109` charges for this batch. Its proper optimistic cost
filter, `13*(N-1) > 2*C`, therefore rejects the observed `N=32, C=256` before the
full audit. It selects zero prefix reuses here. At a full 256-entry cache, 41
same-signature calls would be necessary to clear this optimistic filter; that
count would still be insufficient to prove complete eligibility or net saving.

The `-109` is a bound for the hypothetical admitted route, not the cost of the
properly rejected route. The latter still has its own charged prefilter and
fallback work. No candidate cost was measured, no actual candidate batch ran,
and neither form establishes the remaining full-request cost. The final
222-category map is not a map measured at batch entry and is not used in this
bound.

## Unfinished obligations remain explicit

Before any different candidate could be implemented, its review would need to
close the following obligations:

- Authenticate native helpers, class and instance dispatch, constants, work,
  category-map contents, the complete callback chain, and the relevant
  observation hooks at the actual omission points.
- Preserve the original domain errors and every intermediate guard, using
  current native fields rather than alias equality or a past successful call.
- Define a typed immutable seed payload, exact method/input/cap binding, a
  bounded batch reference, and charges for every new logical copy and lookup.
  A payload in an existing slot is still additional retained numerical state.
- Prove cache-entry ownership, replacement/eviction behavior, reference lifetime,
  retirement and cleanup. A local reference must not keep a seed alive past its
  authorized original entry merely because the C044 entry happened to survive.
- Close authority after seed attachment and every surviving callback. Original
  `remember` protects its pending insertion; it is not a general certificate
  that new payload fields and the final returned result stayed unchanged.
- Preserve original warm-return behavior, cold final guards, dynamic/radii
  branches, short-circuit comparison order, late multiplication timing, original
  exceptions and complete fallback. Include declined and partial admission work
  in the charged bound.
- Bound any effect outside the selected prefix, including shared-cache behavior
  and work newly reached after the original operation-cap refusal.

Those obligations are not silently marked proved because this candidate is
rejected. The appropriate next supported source-only investigation is the
separately scoped L03 retirement/direct-reseed census. The latest complete
original gate remains 24/28, C035 remains held, and no merge or release
acceptance follows from this review.
