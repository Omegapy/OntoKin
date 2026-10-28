# Captured identity placements

The neutral original P16 diagnostic at implementation `e293d27f` identifies
38,041 producer sampling operations. Two constructions in the captured graph
perform work whose pose values are unused or provably identical.

The constant-hinge builder first constructs an identity pose, then immediately
replaces it with the actual hinge rotation pose. Constructing only the used
variant removes that discarded projection in both captured graph builders.
The actual hinge rotation, child inverse and ordered placement are unchanged.

A captured rigid or active grip joint with an exact zero child origin and
positive identity child rotation performs two identity compositions. The
existing `recording_parent_origin(parent, parent.rotation)` helper returns the
same native position, rotation and zero proofs, while adding both composition
depths. Its full parent, finite-domain and depth checks remain active. Each
performed operation and callback keeps its original charge.

The selector is computed once from the complete immutable, typed source
witness, immediately after its original current-source comparison and before
the next callback. It accepts only native binary64 zero translations and the
literal positive unit quaternion; either zero sign has the existing canonical
positive-zero projection. A hinge, nonzero child offset, negative unit lift,
foreign scalar representation or unsupported witness retains ordinary
placement. Native fixed child poses are detached before further callbacks,
including children that remain on the ordinary path. A later mutation of a
live Pose can change neither eligibility nor those captured source operands.

The selector stores a source fact in the already bounded captured graph. It
stores no numerical result and adds no cache. The original final publication
receipt still verifies complete source owners, actual joint/child operands,
active topology and phase bounds after all callbacks. Cancellation, changed
caps and failed final admission cannot publish a partial cursor group.

The preserved diagnostic suggests roughly 686 operations of discarded hinge
identity construction and roughly 1,144 operations of zero-child grip
placement in original P16. These are estimates from the prior trace, not an
executed saving. Focused tests compare every native pose bit and allowance,
verify source mutation and cancellation behavior, and retain the unchanged
100,000-operation and 256-entry cache limits. Full original results are pending.

## Executed checkpoint

[Checkpoint019](reach-recording-validation-2026-10-23/checkpoint-019.json) records41/41 worker and107/107 integration methods, followed by the complete original suite at23/28. Its neutral original P16 observer measures producer sampling36,211 operations versus38,041 previously, exactly1,830 fewer. The full P16 request still exceeds the unchanged operation budget.
