# Same-key independent offset products: proof investigation

Date: October 25, 2026. Checkpoint: 034.
Source: `336fd0c1b1ec094797328800ac623dfea7717e07`, tree
`a791352c48f324097f533bb802eadad57f840198`.
Accepted runtime: `d2f0088c4f3c1f570630334804a5a8f78e0105ac`, unchanged.

## Decision and scope

The bounded investigation selected in [HANDOFF-033](HANDOFF-033.md) is complete.
A separately stored two-product receipt is not profitable for the selected
two-consumer case. A more specific design can have a **conditional one-operation
saving**: replace the existing coefficient entry once, then obtain its two
completed products through the recipient's already required coefficient lookup.

That positive trace is a derivation, not an executed optimization. The fused
design remains **held before runtime implementation** until its source recipe,
native-dispatch latch and receipt lifecycle are bound to a complete reviewed
design and every added operation is accounted for. This checkpoint changes no
runtime, fixture, oracle, limit, shared overview or prior evidence. No product
request, regression test or recording gate was rerun.

The [cost ledger](checkpoint-034-cost-ledger.json) distinguishes the rejected
ordinary forms from the conditional fused form. The
[next scope](checkpoint-034-next-scope.json) makes the remaining work concrete.
L03 reseeding, P16 retained clocks, P23 producer sampling and other held
candidates remain separate.

## Source facts used by the derivation

The inspected source is the exact published checkpoint033 tree. In
[the centered reader](../../../ontokin/reach_reference_center.py),
`_offset` uses a cyclic coordinate order determined by its active Cartesian
axis. For Y rotation, that order is local z, local x, local y. It obtains
coefficients from `_coefficients`, then evaluates the original two expressions
at lines 681–682. The local `product` helper already skips multiplication for
zero operands and a last operand of +1; a last operand of -1 uses negation.

[The source library](../../language-design/planar-reach-v0.1/libraries/reach-assets.ok)
defines two sibling offsets with original local coordinates
(-0.1, 0.05, 0.23) and (+0.1, 0.05, 0.23). Its brow has a different common
operand. The decimal literals are decoded source values: 0.23 is the exact
binary64 rational 8286623314361713/36028797018963968. Their relation motivates
the investigation; a runtime rule must never select fixture names.

[Independent exact arithmetic](../../../ontokin/reach_reference.py) charges
one tick before each scalar operation and checks the input and prospective
unreduced numerator/denominator widths before multiplication. Centered
`_Guard.lookup` and `_Guard.remember` each charge one tick before their normal
bounded bookkeeping. Changed operand-domain synchronization can add work.

The existing [coefficient derivation](../reach-centered-coefficients.md)
shares five completed scalar operations. Its two-use cost is 10 to 8. That
margin does not transfer to the newly selected two products.

There are two distinct numerical caches. `ReachExecutionWork._cache` has its
own reported occupancy. The independent reader's `_Arithmetic.cache` is a
different dictionary bounded by `MAX_CACHE = 256`. Centered coefficients live
in the latter. Checkpoint033's reported work-cache occupancy does not measure
the independent cache's occupied or available slots.

## Conditional exact identity

Fix one admitted source group, orientation, arithmetic owner and evaluation
key. Let w and s be its native exact quaternion center components, and write

```
d = w*w - s*s
c = 2*(w*s)
p = d*b
q = c*b
```

For either signed second plane coordinate y, the original projection is

```
first = floor128(d*b - c*y)
last  = floor128(c*b + d*y)
```

Substituting already completed exact p and q at only those two product
positions gives the same two rational expressions and the same final grid
floors. The products involving signed y remain ordinary calls. No
normalization, sign factoring, reassociation or moved floor is used. Each
node retains its parent-position additions, uncertainty/radius decision and
final source admission. The substitution introduces no new approximation.

This identity is conditional on identical native Fraction numerator and
denominator fields, exact source/axis/product position, live owner and domain,
and a receipt that still represents the actual completed original operations.
It does not justify a value copied from output tracks or certificate claims.

### Prospective guard proof

The accepted coefficient record allows at most 535 numerator bits and 516
denominator bits for either retained coefficient. A native source vector
component allows at most 138 numerator bits and 129 denominator bits. Thus
both selected original multiplications have conservative prospective bounds:

| Bound | Maximum extent |
| --- | ---: |
| Numerator | 535 + 138 = 673 bits |
| Denominator | 516 + 129 = 645 bits |

These bounds are below the unchanged 32,768-bit limit. They justify omitting
the prospective multiplication check only while the full native domain
remains admitted. A reduced stored result fitting a smaller domain would not
prove the omitted unreduced multiplication admissible. Initially narrowed
domains use the original path; a live narrowing must preserve the existing
latched-domain and original-refusal behavior.

Two multiplication charges exist only when d and c are both nonzero and
b is outside {0, +1, -1}. A zero or identity shortcut must not be counted as
a saved multiplication or published as an original multiplication receipt.

## Ordinary cache forms are held

The baseline computes two products for each of two consumers: four
multiplication charges.

| Design | First consumer | Second consumer | Total | Saving |
| --- | ---: | ---: | ---: | ---: |
| Original products | 2 | 2 | 4 | 0 |
| Separate bundled receipt: miss, compute, insert, hit | 4 | 1 | 5 | -1 |
| Source-known donor: compute, insert, hit | 3 | 1 | 4 | 0 |
| Two separate scalar receipts | 6 | 2 | 8 | -4 |

These favorable totals exclude any additional admission, changed-domain or
receipt work. Therefore the ordinary forms cannot satisfy the required
positive saving for this pair. Their rejection is not an impossibility
theorem about every fused design.

For r actual consumers, a separate bundled miss/insert/hit design has at most
r - 3 saved charges; omitting its first lookup has at most r - 2. The selected
task has two consumers and does not authorize expanding the source scope
to obtain a larger amortization count.

## The conditional fused design

Keep the existing coefficient insertion before the donor's offset
arithmetic. Execute all four original donor vector products, combinations
and final floors in their original order. If both selected multiplications
actually completed under the required native conditions, replace that exact
coefficient slot once with an immutable expanded receipt. Do not move the
original insertion callback.

The recipient obtains the expanded receipt during the coefficient lookup
it already performs. It substitutes p and q only at the two corresponding
product positions.

| Change relative to the unchanged runtime | Charge delta |
| --- | ---: |
| Existing coefficient computation, insertion and recipient lookup | 0 |
| One conditional replacement of the existing slot | +1 |
| Omit recipient d*b | -1 |
| Omit recipient c*b | -1 |
| Conditional eligible-pair total | **-1** |

The donor's two original products and the new replacement cost three
charges. The recipient reuses its two selected products, compared with four
multiplication charges in the original pair. This is a local static trace. It includes
one new publication charge but assumes no separately charged new scan,
lookup, admission, cleanup or receipt operation. Any such added charge must
be entered explicitly; one additional charge would consume the entire
margin.

### Required generic source selection

A sufficient conservative design selects at most one donor/recipient pair
per coefficient-source segment. Its sealed source recipe must establish all
of the following before numerical reuse:

1. Both nodes are nonstationary actual offset projections. A recipient that
   returns from a stationary-pose cache would not execute the offset, so a
   donor update could otherwise cost one operation without any saving.
2. Both are sibling relations with the same admitted parent/orientation
   source, active axis and no-intervening-seed segment.
3. Their exact prepared plane-first operand b is identical and nontrivial.
   Their second plane coordinates are opposite signed source values, and
   their axial coordinates agree. The signed products stay ordinary.
4. The selected donor precedes the selected recipient. Their identities,
   source segment and product positions are retained in the sealed recipe.
5. Only that donor may publish and only that recipient may consume. A later
   consumer does not refresh or republish the receipt. Nonselected coefficient
   hits preserve the expanded payload while reading its ordinary coefficients.

Disjoint endpoints alone are insufficient. Interleaved pairs D1,D2,R1,R2
can replace the same coefficient slot before its intended recipient.
Selecting one pair per coefficient-source segment avoids this collision.
A wider nonoverlapping-interval rule would need its own complete derivation.

Use the existing bounded plan traversal, exact native integer-field
identities and admitted source relations. Do not add an unaccounted second
scan, numerical pose computation or comparison against supplied GLB tracks.
If expanded preparation needs a new semantic charge, include it in the
complete ledger rather than assuming it is free.

The current source does not implement this recipe. It retains only
`coefficient_source`; its preparation-local segment number is not retained
in `_CenteredNode`. The current coefficient key also has no evaluation
nonce or clock identity. Those facts are explicit source-binding gaps.

### Finite receipt ownership and lifetime

A proposed receipt has a fixed shape: the existing four coefficient Fraction
leaves, one shared source operand, two completed products, an exact bounded
key-clock snapshot, bounded integer seals, one strong opaque evaluation token,
and bounded source segment/pair identities. No list may grow with clocks, consumers or callback history.

Allocate a fresh strong object token for each complete `evaluate()`
invocation and compare it by identity. An integer `id()` is insufficient
because object IDs can be reused after destruction. The recipe also binds
the source phase/segment and arithmetic owner. Repeated w,s at another clock
must never recover the product pair.

Publication is a conditional replacement, not a general insertion.
After its charged callback and normal domain synchronization, require
`cache[key] is observed_record` immediately before replacement. If nested
work replaces or evicts that entry, decline publication. Do not resurrect
an evicted value or overwrite a nested writer's newer record. A successful
replacement adds no LRU slot.

The expanded immutable value remains inside the existing 256-entry
independent arithmetic cache. Old fields may remain stored after an
invocation, but a different token makes them ineligible; later ordinary
replacement or eviction disposes of them. There is no recovery side table
or new persistent numerical cache. This avoids a separate cleanup charge,
subject to a complete implementation proof of inaccessible stale values.

The existing 128-node plan bound and bounded intervening writes motivate
retention of the selected slot through a native same-segment pair. The
implementation must bind that existing argument to its exact selected
interval and update behavior. A callback-induced eviction is a fallback
case, not a positive-saving case.

### Dispatch, mutation and original expression order

A hit-time native check alone is insufficient. The two omitted products are
separated by ordinary signed products, combination work and a floor, whose
callbacks may change dispatch or mutate an alias.

The design needs a product-specific native-domain latch observed at each
remaining checked boundary and consulted again at each proposed skip.
A departure remains latched if later callbacks restore the original methods.
If eligibility is lost, that product executes its ordinary branch; no
product receipt is refreshed after a departure.

The existing `_Guard.current` already runs after checked operations, but it
does not itself implement this new product-dispatch latch. The final design
must identify every participating native class/instance method and foreign
descriptor check, without invoking foreign dispatch merely to test
eligibility.

Freeze and watch the actual donor operands and completed result objects.
The recipient must validate exact record type, bounded shape, all integer
seals, token/segment/owner identities and fresh detached values. Existing
watching by a prior node's guard does not automatically protect the next
node, because each node creates a fresh guard.

Keep Python's original binding order. In
`guard.floor(combined(product(...), product(...), ...))`, the outer floor
method is bound before its argument expressions execute. Refactoring the
whole expression into sequential assignments can change which
callback-installed method runs. Replace only the selected product result
while preserving the original surrounding expression.

The donor's added replacement is a real cancellation/resource boundary.
An exception there must retain its identity and leave the old entry intact.
Final batch owner checks, pending cursor publication and rollback remain
unchanged. A rejected source batch must not allow an old token to authorize
a later invocation.

## Proof status and the implementation hold

The exact substitution and full-domain prospective bounds are established
conditionally. The ordinary separate-cache forms are nonpositive. The
specific one-slot replacement has a coherent positive local trace under the
conditions above; neither review found an inevitable second charge.

The complete operational proof is **not closed**. The exact source predicate,
per-boundary latch semantics, immutable field/clock bounds and coverage of
all added charges still need one source-bound operational design. The
conditional design above identifies what that binding must establish; the
absence of implementation is not itself a proof defect. Candidate execution
and hostile controls subsequently test whether code satisfies that design.
No candidate trace has been measured across actual planning, callback and
cache paths, and the audit's arithmetic examples do not establish those
implementation claims.

Accordingly, retain the HANDOFF-033 implementation hold. The next bounded
step is to close this specific fused recipe/lifecycle derivation and its
actual charge ledger, then implement only if those premises are established.
Otherwise publish the exact failed premise and hold the candidate. Do not
retry ordinary memoization or claim that the fused design is impossible.

Any later accepted runtime change needs exact differential and hostile
controls, unchanged complete P11/L03 requests, fresh original28 and all
relevant regression/local/release evidence on its actual changed source.
A local one-operation trace predicts neither a complete-request saving nor
a P11 pass. The original recording gate remains historical **24/28**.

## Evidence and reproducibility

The [checkpoint record](checkpoint-034.json) identifies exact source recovery,
checkpoint033 archive verification, the standard-library analysis audit,
independent reviews and documentation validation. The audit imports no
OntoKin runtime and executes no product request. It verifies source
assumptions, the explicit charge models and finite exact-arithmetic examples;
its assertions are not product test methods or a proof of the absent
implementation.

The existing checkpoint033 archive was freshly reconstructed and verified:
13 parts, 87 exact members, 10,968,753 joined bytes, SHA-256
`afa76b17523188400f462e90612e14d9e773056bc25763896bcaef9bd4faeb8e`.
All member hashes, safe paths and ZIP CRCs passed. That operation verifies
preserved bytes; it does not rerun historical product failures.
