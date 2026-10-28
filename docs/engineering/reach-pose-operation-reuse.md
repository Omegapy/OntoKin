# Reuse of identical private rotation operations

Owner `interactive-reach06-release-review-20261020-2320-7of9` continues
[issue #24](https://github.com/Omegapy/OntoKin/issues/24) on an isolated child
of PR #23. The original branches and unpublished checkout remain unchanged.
The starting candidate `b8192e761c5ae32d27734f14aee26aca8d7898ff` combines
published pose projection and source assertion corrections. It passed 36
numeric/cache/pose methods but still failed P23 in the 45-case source run.
Both executions retained all 1,159 inputs unchanged. Detailed raw results are
retained with the later publication checkpoint; these are predecessor results.

## Mechanism and invariants

P23 contains 32 distinct chains. Their source identities and world positions
differ while many private quaternion products and rotated local vectors are
identical. Whole-pose caching therefore does not remove all repeated arithmetic.

`ReachPoseOps.multiply` now reuses a completed private quaternion product under
the existing request-local cache. Its key contains the method identity, the
ordered exact component tuples and both input angular error bounds. A reversed
product or changed error bound is a different key. The cached result is the
same immutable `RotationValue` produced by the unchanged Hamilton product,
rescaling and rounding operations. Materialized public quaternion projections
are absent from the key because multiplication does not read them; the result
remains unfrozen.

`ReachPoseOps.rotate` also reuses a completed rotated vector. The key contains
the method identity, exact private quaternion components and exact vector.
The original input guards and sparse cases still execute. Angular error bounds
and saved public projections do not affect this pure vector calculation. Every
pose composition still computes its own error bound from its own inputs.

A second bounded entry reuses the translation-independent part of a composition.
Its key contains both complete private rotations, both derivative pairs and the
local position. The parent position and both position errors are absent because
they do not enter this common arithmetic. The cached fixed tuple contains the
offset, rotation, derivatives and common positional-error contribution. Every hit
guards its numerical operands, computes and rounds the actual parent position
plus that offset, and computes its own position error with the original formula.
It constructs a fresh pose with its own projection dictionary. Cold evaluation
retains position-before-derivatives order. The common error contribution is the
offset-angle term plus both original `VECTOR_ERROR` allowances. Every call adds
its own parent and local position errors to that contribution. Exact rational
associativity preserves the complete mathematical bound; only the performed
additions change. The operand-bit guard applies to those actual intermediates,
so this is not a claim of identical resource rejection at artificial extreme
intermediate widths. No positive allowance is dropped. The existing stationary
whole-pose cache remains an earlier fast path; a miss may use this relative cache.

Public vector projections also share a completed binary64 tuple under its exact
private vector key. Position, velocity and angular velocity use the same rounding
operation. Each miss in the per-pose projection dictionary still checks operand
bounds and uses the charged request cache; a distinct exact tuple cannot borrow a
rounded result merely because the final floats would coincide. Already materialized
public values retain their saved bits. Failed or cancelled projections are not cached.
An exact-zero vector takes a guarded, charged fast path to canonical positive
zero components; tiny nonzero values still pass through actual binary64 rounding.

Hinge-pose reuse is keyed by the canonical exact axis, coordinate and exact slope.
All three operands are checked before lookup. The cached tuple contains only the
private rotation and angular velocity; each hit constructs a fresh private pose
bound to the current arithmetic helpers. A stopped hinge cannot reuse a running
hinge's rate. No source identity, joint claim or frame traversal is stored here.

The actual P23 cost probe also found no successful path-slot cache reuse: its
0/after request executed 900 path-slot lookups, 900 insertions and 822 evictions.
For a constructed object/site inventory larger than the request cache capacity,
the runtime therefore bypasses optional derived path-specific slots, with an
explicit charged cancellation/deadline checkpoint before the original builder.
Root slots remain eligible: their complete signature has no ancestor, and a
constant root would otherwise repeatedly decode the same canonical operands.
The capacity stays unchanged. The one complete graph cache for an exact state
and time remains, as do all graph traversal, motion-authority, projection and
output checks. This structural policy uses no fixture name or special source ID.

## Terminal dependency paths

Completion and explicit stop previously invalidated the graph cache and rebuilt
every object/site for each individual terminal tip. With 32 simultaneous completions,
that repeats a complete scene traversal up to 32 times before final validation.
The terminal measurement now uses the existing selected-frame resolver for the
action's base and tip, with every required ancestor and the actual position and
orientation. Terminal records expose no velocity fields, so this private path
does not construct unused derivative vectors. The relative tip calculation and
actual terminal residual test are unchanged. Its separate path-cache namespace
cannot replace full-kinematics values. Incidental failure precedence for unused
intermediate derivatives can change; complete incoming/final derivatives and
all explicitly exposed impulse intermediates remain checked. This use follows
the boundary transaction and does not claim recording's validated-prefix
precondition.

During natural reach completion without incoming dynamic bodies, a temporary context can retain the already
computed incoming frames and up to 256 relative terminal tip values. Each reach
stores the same canonical endpoint coordinates, so these p/q values remain
unchanged through other natural reach completions, including nested chains.
An ordinary latch, any written event, or a dynamic force-anchor update disables
this reuse. Time and staged-state identity must match. Eligibility is charged,
and the temporary context is always cleared in boundary cleanup.

This context never replaces the final complete graph. Moving reaches retain
nonzero incoming slopes at the exact endpoint; final staged evaluation must
compute their newly held zero outgoing rates. Only the relative tip values,
which have zero private derivatives by construction, can seed the bounded
derived-tip cache for final reach projection. Source actions, claims, ideal
anchors, histories and every published output occurrence remain fresh.

Whole stationary composition results are retained only when the parent's exact
translation is zero. Other translated instances still reuse the complete common
relative calculation and compute their own rounded position and error sum.
This limits one-use translation-specific entries in the existing 256-entry
cache; it changes cache admission, not arithmetic, identities or allowances.

This follows the adopted transaction: the complete incoming graph is computed
before ordered automatic completions, and the complete staged graph and full
reach/output projections are validated before publication. Explicit impulse
intermediate checks, incoming release state, completion order and whole-boundary
rollback remain in the inherited transaction. No partial map is stored as the
complete graph cache. Ordinary full source observations still resolve every
object/site. This removes unrelated intermediate traversals rather than a
required incoming, terminal-dependency or final-state check.

The single complete graph cache may also survive a changed sample clock when
the exact current state has no dynamic body and no motion claim. Its positions
and orientations then have no time-dependent input. Running or paused claims
and every dynamic body conservatively keep the clock in the key; event and
force transitions retain their existing invalidation. Every cache-key decision
is charged, and source observation times remain distinct in published records.

This does not identify translated assemblies as the same source object. Source
paths, topology, claims and output records still pass through the original
runtime. A changed derivative, rotation, local transform or error allowance is
a different numerical key when it affects those results. Position error changes
always enter their own fresh calculation. The cache cannot remove the final position's operand
bound or reuse another instance's world position.

This is finite reuse permitted by the adopted
[counting contract](../language-design/planar-reach-v0.1/budget-counting.md).
All lookups, insertions, promotions and evictions use the existing charged,
cancellable helpers. The cache retains its maximum of 256 entries; lowered
limits remain effective. No source graph, identity, claim, lifecycle, output
occurrence or independent-reader check is cached by these operations. No
operation maximum or numeric tolerance changes. Earlier source profiles do
not use these helpers.

The fixed-size composition guard includes the parent position and the private
rotated offset. After that check, position addition uses a private exact-vector
helper, removing the two redundant generic vector-decoding/helper calls. Its
sparse check, every executed exact addition, grid rounding and result bit guard
remain charged. Noncanonical parent position tuples still take the original
vector conversion/domain path. The immutable module `ZERO` vector also has a
charged canonical-zero projection path; equality with arbitrary caller values
does not qualify. Materialized saved projections retain precedence.

## Validation scope

`tests/test_reach_pose_reuse.py` uses exact noncommuting quarter-turn products,
exact vector rotation, changed error bounds, distinct frozen projections,
eviction and cancellation. Warm/cold equality is supplementary to these explicit
mathematical expectations. Existing numeric, lifecycle and source cohorts must
also execute against the identified candidate before any successful correction
claim. Passing these checks alone cannot close the full reach release.
