# C035: binding the same-slot product receipt

This record binds the conditional design selected by
[checkpoint 034](checkpoint-034-offset-products.md) to a concrete isolated
candidate. It does not itself establish a measured saving, a recording pass,
runtime acceptance, or release acceptance. Actual execution and the final
disposition belong to the separate C035 checkpoint and handoff.

Starting publication: `f527649ef1cede84eb1d1c15b394ec45da975433`;
complete tree: `471dd49cbcd4f293a6bae9323f2424430fab8c7b`.
The previously accepted runtime remains
`d2f0088c4f3c1f570630334804a5a8f78e0105ac` until a separately identified
candidate satisfies its required gates. The last complete historical original
recording result is 24/28, with P11, P16, P23 and L03 blocked.

## Source selection

The existing bounded `prepare` traversal in
[reach_reference_center.py](../../../ontokin/reach_reference_center.py)
selects from source recipes, after their existing sign conversion. Eligible
nodes are nonstationary site, follow, fixed or grip projections. Hinges are
excluded. Both endpoints have the same parent, coefficient/orientation
source, axis and no-intervening-seed segment, with the donor before the
recipient. In the cyclic axis order `(axis+1, axis+2, axis)` modulo three,
their first and axial vector components are identical, and the nonzero
second components are exact opposites. The shared first component is neither
zero nor positive/negative one.

The candidate deliberately selects at most **one pair in the entire prepared
plan**, a stronger restriction than one per segment. That keeps the live
watcher fixed in size even when separate sources interleave. The bounded
candidate map and final metadata pass use the existing source traversal and
already charged source visits. They add no additional whole-plan traversal,
exact arithmetic, numerical cache, or charge. No fixture name, output track or expected pose
participates in selection. Prepared metadata seals bind the pair and each
endpoint's path/kind/parent to its actual source node.

## Arithmetic and the complete conditional charge ledger

Write the original plane coefficients as `d` and `c`, the shared component
as `b`, and the signed component as `y`. The candidate retains the original
donor calls for `d*b` and `c*b`; it never factors or reconstructs them. The
recipient uses those completed exact values in its unchanged expressions:

```text
floor128(d*b - c*y)
floor128(c*b + d*y)
```

Both outer `guard.floor` bindings still occur before evaluation of their
inner arguments. The signed products, combination order, parent-position
additions, radii and final floors are unchanged. The axis coordinate is
unchanged. The prospective bounds derived in checkpoint 034 are at most
673 numerator bits and 645 denominator bits for the retained products;
the shared operand is bounded by 138/129 bits. These bounds justify omitted
native multiplication guards only in the unchanged 32,768-bit domain.

| Selected work | Original | Eligible candidate | Binding |
| --- | ---: | ---: | --- |
| Donor `d*b` and `c*b` | 2 | 2 | Original exact calls complete normally. |
| Same-slot immutable replacement | 0 | 1 | One additional original `tick`; no new key. |
| Recipient `d*b` and `c*b` | 2 | 0 | Values arrive through its existing coefficient lookup. |
| Source preparation, bounded metadata admission and sealing | 0 added | 0 added | Existing visits; native field work only. |
| Existing coefficient insertion and recipient lookup | unchanged | unchanged | Neither is duplicated or removed. |
| Operand-limit synchronization at replacement | 0 added | 0 added | Both live cap and saved cache marker must remain native 32,768. |
| Selected total | **4** | **3** | **Conditional net saving: one operation.** |

This ledger includes preparation and publication rather than counting only
removed multiplications. A changed cache marker can make synchronization
charge even when the live cap is unchanged, so both values are admission
conditions and any observed departure disables reuse. A second added charge
would consume the entire margin and is not authorized by this derivation.

The result is conditional. Publication followed by no reuse costs one extra
operation; publication followed by one reuse breaks even. Callback churn,
dispatch changes, eviction and source/domain changes are not relabeled as
positive cases. Zero coefficients and zero/unit shared operands retain their
original shortcuts and do not publish a two-product receipt. Prefix controls
do not substitute for complete P11 or L03 requests.

## Receipt, storage and lifetime

The existing `_CenteredCoefficients` record keeps its original four-value
seal and two-value return API, with one optional immutable product payload.
The fixed payload contains a fresh strong `object()` evaluation token, the
exact clock numerator/denominator, the selected pair, one detached operand,
two detached products and a seal. Clock fields are native integers bounded
by the existing 1,024-bit clock admission. There is no cross-clock table,
integer-address nonce, separate persistent cache or side table from which
evicted numerical values can be recovered.

The recipient must obtain the actual expanded record through its ordinary
coefficient lookup. Nonselected hits preserve that record. Publication checks
the expected slot identity after the added callback and synchronization, then
replaces that exact existing key. It never deletes/reinserts the key, revives
an evicted entry, or overwrites a nested writer. The numerical cache remains
bounded at 256 entries, independently of the work cache and the separate
512-category metadata limit.

For an uninterrupted native pair, the prepared plan has at most 128 nodes.
There are at most 126 intervening nodes, each capable of at most one
coefficient entry and one stationary-pose entry. Thus at most 252 newer
entries/accesses can intervene, below the 256-entry independent cache bound.
There is no intervening orientation seed in the selected segment, and neither
selected endpoint writes a stationary pose. This proves native retention;
arbitrary callback cache churn instead takes the guarded fallback.

One session belongs to one evaluation. Its source snapshot retains strong
identities for the plan/cache identity, context/phase, state, node tuple,
recipe tuple and both selected source nodes. Bounded raw-dictionary admission
prevents added source reads from invoking caller-installed descriptors.
Its watcher retires after the sole recipient's complete offset and cannot
rearm. Final cleanup clears only its own observer, preserves a nested owner,
and cannot replace an original in-flight exception by invoking a new property.

## Callback and native-dispatch binding

The existing `_recording_after_tick` observer affects nested-route admission;
reusing it for this optimization would change existing routes. The supporting
scope therefore adds a separate optional `_recording_product_after_tick` in
[the original arithmetic class](../../../ontokin/reach_reference.py). The
original tick captures both observers, performs the original check, then
calls the product observer and the original observer in that order. If the
original check raises, neither observer runs. This adds no tick.

The product observer only latches eligibility/integrity; it does not raise
ahead of an original prospective guard. Class and instance dispatch,
participating function code/default/closure/global identities, native
Fraction fields, arithmetic owners, live/cache caps, source/phase/clock,
and receipt/operand seals remain admitted at affected checked boundaries.
A self-restoring foreign guard cannot erase the recorded departure.

The same native conditions must be checked at each actual skip before
dispatching a replaceable session method. A foreign `reuse` method returning
true must not override an already false latch. Capture and publication also
cannot become foreign paths that create a receipt after native departure.
Existing original-error wrapping, callback exception identity, final source
batch admission and pending cursor publication/rollback remain in force.

## Required executable evidence

The new dedicated test module is
[test_reach_centered_offset_products.py](../../../tests/test_reach_centered_offset_products.py).
Its controls cover independent all-axis Hamilton arithmetic, complete pair
and preparation costs, actual P11 keys, bounded P11/L03 byte comparisons,
every actual paired cancellation boundary, shortcuts, full cache pressure,
stale tokens/clocks/phase/owners, mutation, foreign/restored dispatch,
conditional replacement, observer coexistence and cleanup.

Required subsequent execution retains unchanged complete P11 end 3 and L03
end 4, fps 1, helpers false; original28; relevant complete regression and
default local validation. All runs must identify actual source/tree, stable
inputs, raw streams, interpreter and status. The limits remain 100,000
shared operations, 30,000 ms, 32,768 operand bits and the existing caches.
Every failed attempt remains evidence. No hosted/paid CI or merge is part of
this isolated scope. Compatibility, Agent/native/browser/visual and the
complete release obligations remain separate pending gates.
