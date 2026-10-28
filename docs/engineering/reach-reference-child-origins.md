# Independent recording body cursors with nonzero child origins

## Scope

This optional independent-reader calculation applies only inside a complete
source-admission batch. Its existing body-axis recipe must already prove the
complete ideal orientation and its rate. The captured child pose must contain
native finite binary64 components and exactly identity rotation. The child
translation may be nonzero in any direction. The original P11 head has an
identity child rotation and position `(0,-0.25,0)`.

Direct source inspection, the ordinary independent walker, nonidentity child
rotations, malformed operands and changed numerical domains retain the previous
expressions. This candidate is implemented but has not yet executed or been
integrated. Checkpoint014 remains 23/28.

## Position and orientation proof

Write the parent pose as `(p,Q)`, the hinge quaternion as `H`, and the child
site as `(c,I)`. The original placement is

`compose(compose((p,Q),(0,H)),inverse((c,I)))`.

Its ideal orientation is `QH`; its position is `p - rotate(QH,c)`. The existing
independent complete-body recipe already includes the inverse child rotation.
For this exact identity child rotation its independently enclosed quaternion
therefore encloses `QH` without a second rotation factor.

The new path puts that complete orientation at the original parent position
and then executes the original independent `inverse(constant(child))` and pose
composition. Thus the original translated child origin remains in the position
proof. It never substitutes the parent position as the final body position.
No axis-parallel assumption is needed, because the actual inverse translation
is still rotated by the complete orientation. Descendant eye and site offsets
continue through the original per-edge composition with that positioned body.

The complete body cursor uses the existing independent Taylor/direct seed,
128-bit outward interval grid, exact affine clock/rate proof, charged recurrence,
64-step reseed ceiling and bounded cache. A warm recurrence can produce a
different conservative enclosure from the older per-hinge recipe. Correctness
is interval containment of an independently calculated finer source enclosure;
equality to the previous over-enclosure is not required. The producer's sampled
poses and numerical allowances do not establish this proof.

## Source receipts and publication

The source plan already contains the detached immutable native child tuple,
all actual ancestry records, source action recipes and owner identities. Each
frame still has its original charged visit, and every new numeric operation
uses the existing work object. The child inverse and complete body orientation
are independently calculated; no new pose table, numeric cache or history is
introduced.

The existing plan and source-batch owner checks remain before and after
callbacks. Complete current-source admission and owned-cursor checks precede
final publication. Persistent source or owner changes reject the batch and
discard its still-owned cursors; temporary source changes cannot enter the
copied child expression. Narrowed domains, cancellation, callback exception
identity and reentrant cursor ownership retain their original rules.

## Verification required

Dedicated tests must exercise the actual P11 head/eye origins, signed Cartesian
axes, non-axial translations, unsupported child rotations, repeated source
changes, cap/cancellation behavior, eviction/reseeding, and actual short supplied
bytes. The earlier source-batch cell-identity cohort explicitly disables this
new optional path so that its original fallback and angle-cursor obligations
remain executed. Relevant independent-reader cohorts and original P11 follow.
Every integration then requires the complete original28 suite. No public cap,
fixture, sampling setting, tolerance or release acceptance rule changes.
