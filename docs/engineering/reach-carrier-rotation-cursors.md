# Recording complete coaxial carrier orientations

This derivation accompanies the recording-only carrier cursor in
`ontokin/reach_pose.py` and its guarded graph use in `ontokin/reach_runtime.py`.
It uses the optional ideal body-angular-velocity proof in
[reach-coaxial-phase-bounds.md](reach-coaxial-phase-bounds.md). The adopted
recording limits, quarter allocation, canonical source coordinates, source
evaluation and anchors, geometry, histories, and all public tolerances remain
unchanged. The general numerical derivation remains
[reach-numeric-kernel.md](reach-numeric-kernel.md).

## Exact ideal law and private direct seed

An eligible immutable frame proof gives an exact constant ideal angular
velocity in its own body coordinates, `r e_a`, for Cartesian axis `a` and exact
rational coefficient `r`. A zero coefficient needs no preferred axis. For any
two clocks in this one continuous phase, the exact ideal complete orientation
therefore satisfies

\[
Q_*(t)=Q_*(s)R(e_a,r(t-s)).
\]

The increment acts on the right. An ordinary root spin, whose velocity is
specified in world coordinates, instead acts on the left. This distinction
matters for a noncommuting initial orientation or a mounting rotation that
reverses the Cartesian axis.

A new or evicted cursor evaluates the ordinary **private complete world
orientation** at its current clock. An orientation-only recipe reads the
already frozen typed witnesses, evaluates the unchanged canonical coordinate
kernels, and applies the ordinary root spin, quaternion normalization,
conjugation and ordered multiplication kernels. It omits only unused position
and derivative calculations. No preceding local hinge recurrence, parent
carrier recurrence, or exposed binary64 quaternion supplies a seed. The
ordinary bounded cache may reuse exactly identical direct source operands.
No event or source state is advanced.

The recipe does not reread mutable model/action records while arithmetic
callbacks run. Its initial orientations, actual affine endpoints, clocks,
axes and fixed quaternions are the same immutable values that passed the
current witness check. A temporary source mutation restored during a cold
seed therefore cannot publish another curve's quaternion under that proof
token. Later calls continue to verify the current complete witness chain.
Recipe decoding retains concrete numeric types, signed binary64 zero and
private rotation projections, and charges its actual scalar reconstruction.
It creates no second retained graph or numerical cache.

Let `S_R_private` denote the uniform source angular allowance before the final
public quaternion exposure. Its existing derivation covers canonical source
coordinate rounding, inherited anchor discrepancies, axis-kernel error, and
all direct composition projections on the path. That allowance applies to a
direct private seed at **every** clock of the phase, including a seed after
eviction or the cursor step ceiling. It is not restricted to the phase start.
The public exposure allowance must not be fed back into the position
recurrence; this is why an exposed quaternion is not an admissible seed.

## Existing finite endpoint allowance

Write `A=2^-74` for the existing axis-kernel angular allowance and `P=2^-91`
for the existing 96-bit quaternion product/grid allowance. Each exact
Cartesian body increment is evaluated by the ordinary axis kernel. Its error
is at most `A+P`; the subsequent exact Hamilton product and projective grid
projection add at most another `P`. Bi-invariance of rotation-angle distance
then gives, after `j` cursor advances,

\[
d(Q_j,Q_*(t_j))\le S_{R,\mathrm{private}}+j(A+2P).
\]

The clocks need not be monotone. Repeated clocks and a zero ideal coefficient
execute no increment or product and introduce no extra angular error. A
reseed replaces the old recurrence with an independently direct source seed;
errors from different seeds are not added. Every retained cursor contains at
most `K` samples, where `1<=K<=10000`, and reseeds before another advance.

The already adopted recording endpoint excess is

\[
\Delta_R=N_{\mathrm{trig}}(10000-1)(A+2P),\qquad
\Delta_P=L_{\mathrm{total}}\Delta_R.
\]

The runtime admits a nonzero carrier coefficient only when its already
derived source phase bound has `N_trig>=1`. Thus one complete carrier cursor's
extra angular error is bounded by the unchanged `Delta_R`; it replaces
several local increments and composition products without increasing their
conservative path allowance. A zero coefficient introduces zero recurrence
excess, including when opposite ideal hinge rates cancel. The ordinary source
allowance still covers any canonical-coordinate rounding wobble around that
constant ideal orientation.

## Position propagation and narrow topology

The first implementation uses a carrier cursor only at a hinge whose child
site has exactly zero local translation. The complete child origin is then
the parent-site origin, independent of the hinge and child-site rotations.
The original final 96-bit position grid remains; two consecutive identical
grid projections are idempotent. A nonzero child-site translation uses the
existing sampler. Sliders, fixed/grip relations, sites, follows, roots and
free dynamic trajectories also retain their existing sampling equations.

Downstream fixed/site/follow offsets continue to be rotated and composed by
those ordinary recording helpers. An ancestor carrier cursor contributes at
most `(10000-1)(A+2P)` of additional angular error at each such offset.
Every descendant's existing path trig count dominates the relevant ancestor
count. Summing the offset contributions therefore gives at most
`L_total*Delta_R`. The unchanged uniform source position allowance already
includes the direct seed's source rotation error and the original vector/grid
operations along the same path. Direct seed clocks may differ between
ancestors; their uniform error bound and the sum of path offsets still apply.

Arbitrary constant child-site rotations are eligible only when the phase's
exact axis-transport proof admits them. No sampled near-zero threshold,
approximate coaxial test, changed source coordinate, or reassociation of a
nonzero child translation is used.

## Current source witnesses, work and cancellation

The phase proof stores immutable local source witnesses and parent-frame
identities. During the existing current sample traversal, each node compares
its freshly typed witness and requires an already validated parent witness.
The witness includes static root orientation, active claimant/status,
canonical and ideal affine inputs, clocks and duration, axes, topology, and
fixed poses. Concrete numeric types, tuple shapes and binary64 signs are
preserved; a boolean equal to integer zero is not an interchangeable operand.
A changed or absent witness uses the existing sampler. The proof also checks
program revision and closed phase clocks. The final after-state is sampled
under a fresh context without the preceding phase proof.

A cold seed consumes the captured recipe, and a warm increment consumes its
captured rate. Both must still belong to the current source when the completed
cursor is published. The traversal therefore links its already admitted local
records to their admitted parents. Before publication, it charges one existing
witness guard for each record in that ancestry. After every final cache
insertion, promotion, eviction and operand-scope callback, one callback-free
admission reads and compares the whole current chain. It also checks the model
and root-state identities and the source revision. Identity alone never
substitutes for these actual law and fixed-pose comparisons.

There is no callback between the first final ancestor comparison and the
cache's value/order update. A persistent source change rejects publication;
the old completed cursor and cache order survive. A callback that reenters the
cache or changes its operand cap cannot let the outer pending insertion
overwrite the completed nested work. If publication is declined solely by
that cache generation change, the returned value still passes the same
precharged current-source admission. These linked records are one traversal's
structural receipts, not a second retained table of numerical results.

Each frame proof has a fresh opaque token. The numerical cursor key includes
that token, phase context, path, phase bounds, Cartesian rate, operand cap and
step ceiling. It retains only the latest complete private rotation, clock,
count and one exact repeated increment in the existing shared 256-entry LRU.
There is no per-frame unbounded numerical memo table. The traversal's set of
valid frame names is structural state for that one already bounded graph.

Every actual scalar operation, fixed-size current-domain check, lookup and
publication retains the shared work/cancellation charges. A narrowed operand
cap disables recurrence and evaluates the direct source seed with its ordinary
preflights. A cap change during optional cursor work restarts at those source
preflights; an original seed-kernel refusal is propagated with its original identity and
is never retried by the optional cursor merely because its cap changed. The
same holds for a current-source admission refusal and the callback's own
exception. Cursor publication happens
only after the complete result passes under an unchanged live cap. A failed
or cancelled call cannot publish a partial cursor or mutate source state.

## Verification and scope of results

`tests/test_reach_recording_body_cursor.py` compares noncommuting body
increments on all Cartesian axes against independently computed interval
sine/cosine rotation matrices. It checks zero rates, reverse/repeated clocks,
direct private ancestry, fresh phase/proof tokens, step ceilings, eviction,
narrowed caps, cancellation, stale source witnesses, the zero-child-offset
restriction, and source-state preservation. Complete generated GLBs are
checked again by the independent analytic supplied-byte reader with the
production pose sampler and rotation helpers disabled. Every stored endpoint
and interval certificate remains covered.

`tests/test_reach_recording_captured_seed.py` checks the private recipe against
the direct source graph through completion, changed axes and fixed rotations,
paused and tween coordinate laws, transient callback mutations, and cancelled
cold seeds. `tests/test_reach_recording_source_admission.py` checks persistent
source changes at final insertion, promotion and eviction, identical-valued
root-state replacement, callback-free final comparison, cache order and
generation preservation, and unchanged original seed/admission failure
identity across cap changes.

The recording algorithm can change endpoint bits while preserving the same
independently established inequalities. Universal equality to an earlier GLB
is not claimed. These test descriptions are verification obligations; actual
execution evidence must identify the tested implementation and settings.
Neither this proof nor a short prefix test closes the 28-recording gate or
the remaining native, browser, Agent, compatibility and release requirements.
