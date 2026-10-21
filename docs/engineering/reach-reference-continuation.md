# Independent reach reference continuation

This work continues the independent reader/reference gate described in the
[reach review checkpoint](reach-release-review/README.md). The complete
[release contract](../language-design/planar-reach-v0.1/release-contract.md)
still governs acceptance. The original 100,000-operation request budget and
frozen source/expected bytes are unchanged.

## Bounded reuse

The independent arithmetic context now retains pure normalization, rotation,
Hamilton product, constant-pose, composition and inverse results in its existing
256-entry cache. Exact immutable interval operands and precision identify each
result. Cache lookup and insertion call the original shared work callback;
hits can be cancelled and do not replenish the request allowance. Least-recent
replacement avoids leaving the cache permanently full of early source values.
The pi helper returns its calculated enclosure safely after saturation.

Exact zero vectors, zero scaling, unit scaling and either scalar unit-quaternion
representative have explicit algebraic paths. They omit arithmetic whose exact
answer is known. General interval operations and prospective operand guards
remain in the independent implementation. No production solver, controlled
pose evaluator, recording planner or certificate generator supplies an expected
answer. Source graph traversal, ownership, lifecycle, boundary history weights
and complete outgoing records retain their separate checks.

Full pose cache keys contain derivative operands. Equal positions with changed
angular or linear rates therefore do not share a full kinematic result.
Independent uniform-basis lookups avoid reconstructing an already captured
immutable state's relation graph when the requested carrier is cached.

The later P23 rate probe measured exhaustion while independently recalculating
the same local target pose and residual for repeated arms. The bounded cache
therefore also retains exact-operand norm, hinge, base-tip and residual results.
Hinge keys include coordinate, rate and the ideal/source axis convention;
base-tip keys include both source lengths and both coordinates. Each lookup and
insertion remains charged and interruptible.

For the common scalar/Z quaternion case, the independent evaluator expands
the Hamilton product algebra directly and omits terms proved exactly zero.
The vector transform retains `(w*w + z*z)*v_z`, so even a supplied nonunit
representative preserves the raw Hamilton-product meaning. An interval merely
containing zero does not qualify for the shortcut. This remains independent
of the production homogeneous matrix implementation and its normalisation.

The event ledger retains its immutable prior state as the next incoming state
and deep-copies it once for the outgoing transaction. The earlier second copy
of the incoming state performed an identical traversal and allocation. Every
transition still writes only to the staged copy, and H06 still counts repeated
before/after source rows independently. Returned snapshots remain fresh
projections, so consumer mutation does not mutate those retained states.

## Recording-only expectations

`ReachReference.recording_pose_enclosure(carrier, time, side="after", ideal=True)`
returns only independent position and orientation intervals. It uses exactly
the full resolver's position and orientation expressions, which do not depend
on spatial derivative output. Only the selected carrier's ancestry is resolved.
The internal derivative-free graph has a distinct cache namespace, and its
public return type has no velocity or angular-velocity fields. Full snapshots,
incoming releases, impulse histories and point/phase bounds continue to use
the full derivative path.

The returned intervals concern one exact clock and side. They do not establish
continuous interpolation accuracy or supply a missing whole-phase bound.
Independent certificate inequalities, actual stored key checks, all boundary
histories, destination/native/browser execution and visual review remain
separate required evidence.

The full `pose_enclosure` API also resolves only the selected carrier ancestry;
later full snapshots extend that same full-derivative cache to the remaining
carriers. An explicit `build_reference(..., end_side="before")` stops at the
incoming side of the exact final clock. It never stages that clock's natural
completions or authored transaction. The final after-side is an unavailable
sentinel, and the complete recording-history API refuses such a reference.
Default recording construction continues through the final after-side. The
rate-audit wrapper uses the requested side so that a valid incoming rate at an
otherwise failing boundary has an independent expectation.

## Complete frozen-rate inventory collector

`tools/reach_rate_inventory.py` maps the existing source cohort's 724 derived
world-rate measurements to 362 fresh, individually bounded requests. This is
the 359 original and lifecycle sample sides, the separately checked P16
incoming release, and its payload states at 3 and 4 seconds. Each request
checks both velocity fields for every required carrier, so it may establish
additional rate vectors beyond the 724 explicitly mapped frozen fields.

The collector verifies frozen input and bundle identities, retains every
per-request proof/unresolved/error report, and hashes all tracked checkout
inputs before and after the run. No request receives a replacement budget.
Frozen vectors identify the required field coverage; they do not supply an
unproved tolerance or determine the independent actual-versus-ideal verdict.
Every resulting report continues to label the comparison as a proposal and
the release role as pending. A `--cases` subset is explicitly partial.

The complete command, to be run only inside an exclusive executor window, is:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/reach_rate_inventory.py \
  --output-dir /absolute/path/to/new-evidence-directory
```

The evidence directory must be new and outside the checkout. Authoring the
collector does not establish that its inventory has executed successfully.

## Independent derivative and history corrections

The impulse ledger now encloses the actual source-output operations in the
units of each field. Its seven derived vector fields are lever length and world
application position (metres), angular impulse (N·m·s), two linear velocities
(m/s), and two angular velocities (rad/s). The old generic boundary projection
either had no applicable rule for the lever/application fields or treated an
angular impulse as an orientation error. Those dimensions cannot be exchanged.

Starting from the independent ideal pose and the old phase's source errors,
the reference bounds source position, orientation, velocity and omega before
applying the impulse. The lever enclosure adds the incoming rotation allowance
times the self-point L1 norm and one private vector-round allowance. Exact
interval cross products and division by the canonical mass/inertia propagate
the result into the corresponding momentum and rate units. Every public
binary64 vector projection rounds both interval endpoints monotonically.
The ledger's resulting source-output intervals already include this exposure;
the boundary checker adds no unrelated global pose or rate allowance to them.
A nonzero impulse carries the bounded source/ideal discrepancy forward, while
a zero impulse leaves the trajectory anchors in place.

Force changes capture the complete old point basis before replacing the active
acceleration. For the old phase's acceleration discrepancy `Ea` and elapsed
time `T`, this retains `Ea*T` in velocity and `Ea*T*T/2` in position. The old
implementation retained the old anchor errors alone and discarded these terms
at every force change. Canonical acceleration changes materialize the current
public source tuple. If canonical acceleration stays equal, the actual source
clock is retained while the independent proof clock moves; conversion from a
public-point error to that continuing private trajectory adds a conservative
binary64 publication bound. In either case, the exact ideal acceleration is
computed from the exact sum of the active canonical forces.

Materialized canonical quaternion tuples denote projective rotations. The
reference normalizes their independent interval enclosure when importing a
release, impulse or force anchor, rather than treating the exposed four-tuple
as exactly unit length in later Hamilton products.

An auxiliary hinge's ideal angular velocity now uses the same normalized axis
as its ideal orientation. Its actual source expectation retains the inherited
canonical raw-axis convention. This distinction is already included in the
documented derivative allowance through the canonical axis's norm defect; a
reference using the raw axis for both vectors concealed the intended physical
discrepancy. Exact +Z reach hinges are unaffected.

The additional focused tests include an analytic 3–4–5 hinge axis, a compiled
auxiliary hinge whose canonical axis norm differs from one, force completion
with canonical acceleration `binary64(1/3)` versus ideal `1/3`, and an active
force addition that changes the exact ideal sum without changing canonical
acceleration. A composed P16 variant adds two nonzero and one zero impulses
without altering frozen inputs. Each impulse field is also checked against a
one-ULP mutation while unrelated global allowances are deliberately large.
Execution of these new methods is recorded below.

## Executed checkpoints

On CPython 3.12.14, commit `0f20876cb7a09e18a4b19cd2a10a4864381d44f6`
passed all 29 methods in `test_reach_reference_reuse`, `test_reach_reference`
and `test_reach_source_rates`, with no failures, errors or skips. The first
attempt retained one failure in a newly added exact antipodal-identity test;
the subsequent algebraic shortcut corrected it without changing an allowance.
Raw logs are retained by the continuation's execution collector.

At commit `99595f5a83694ee17ed223f6a41d8c13d0889531`, the same three modules
passed all 31 methods on CPython 3.12.14 in 1.546 seconds, including the new
recording-only comparison and invalid-selection methods. There were no failures,
errors or skips. The recording-only and full paths returned identical position
and orientation intervals for both sides of the selected P01 and P16 clocks;
the full paths retained their spatial derivatives. The retained log is
`reference-recording-001/tests.log` in the continuation execution collection.

These focused results do not adopt the proposed
[rate criterion](reach-rate-acceptance.md) or close any full release role.

At commit `016ce5acc4a37e121e84e1dd04ac694a1cd36d12`, all 37 methods across
the preceding three modules plus `test_reach_reference_impulses` and
`test_reach_reference_derivations` passed on CPython 3.12.14 in 1.801 seconds,
with no failures, errors or skips. The complete footer and individual method
results are retained in `reference-derivations-003/tests.log`.

Two preceding attempts remain separate evidence. Attempt 001 passed 36 methods
and rejected the new auxiliary-hinge fixture's unnormalised `(3,4,0)` source axis
during construction. The analytic helper counterexample still uses that exact
3–4–5 axis, while the compiled-source fixture was corrected to the admitted
canonical `(0.6,0.8,0)` axis. Attempt 002 reported process exit zero but lacked
the final method result and unittest footer; it is incomplete and is not counted
as passing. The corrected single method completed independently, then attempt
003 completed the full focused cohort.

The new source-history and force-anchor intervals can be more conservative
than the previous unsound values. Actual impulse/force GLB certification still
needs to establish the complete supplied-byte inequalities within the original
resource and motion tolerances; these focused tests do not substitute for it.

At commit `a18a59a8eb7ad621adadc52ed1f64e43a2083767`, all 40 focused methods
passed on CPython 3.12.14 in 2.037 seconds, including the new incoming-only
reference and ancestry tests. The complete result is retained in
`reference-prefix-001/tests.log`.

The first collector probe on that same clean commit covered P01, P16, P23 and
L04: 46 requests mapping 92 frozen rate fields. Thirty-six requests proved all
their selected vectors, covering 72 mapped fields; ten P23 requests exhausted
the original shared outer request budget. Every P01, P16 and L04 request proved,
including the P16 free payload and valid L04 incoming failed-boundary state.
The initial P23 before/after requests proved at 69,031 and 94,094 total request
operations. Complete tracked input identities stayed equal. Per-request reports
and all ten failure tracebacks are in `reference-inventory-probe-001/`; this is
partial, unsuccessful inventory evidence and does not close the rate gate.

At commit `5c43962020caa93652df9dce0a95d947b22bf314`, whose complete tree is
identical to integrated source commit `744da7f`, all 43 focused methods passed
on CPython 3.12.14 in 2.533 seconds. This includes repeated local-solution reuse,
immutable incoming-state sharing, and exact planar Hamilton algebra without
changing the raw nonunit quaternion meaning. The full footer is retained in
`reference-reuse-final-001/tests.log`.

The second P23-only inventory probe retained all twelve requests and stable
tracked input identities. The initial before/after requests proved at 67,453
and 89,586 outer operations. The other ten still exhausted the original
100,000-operation request budget. Samples 002, 004 and 006 now reached the final
rate-vector comparisons; 003, 005 and 007 reached requested point-basis
construction; 008 reached the final numerical-input hash check. Samples 009–011
exhausted while initializing the independent reference after the full source
observation. `reference-inventory-probe-002/` retains every report and failure
stack. This is a measured remaining acceptance blocker, not a numeric
contradiction or a reason to replace the shared budget.

## Exact zero and identity terms in derivative bounds

The point/phase source-basis equations still include every documented error
term. Their scalar sum/product folds now omit arithmetic whose exact result is
known from zero or one operands. All supplied operands are converted and guarded
before any shortcut, including operands after a zero product. Each fold charges
the existing work callback; every nontrivial remaining operation retains the
original prospective cross-product guard and charge. No arithmetic result or
source-bound coefficient is approximated or removed: `x+0=x`, `1*x=x` and
`0*x=0` are exact identities over the already bounded fractions.

Focused authored checks compare complete moving-carrier and released dynamic
point-phase records with the original full exact folds. Separate cases exercise
zero-product operand guards, prospective multiplication overflow, empty folds,
cancelling sums and callback identity. Their execution is recorded separately
from the 43-test checkpoint above.

## Independent adaptive trigonometric tails

The interval reference continues to use exact midpoint Taylor sums, independently
of the production Horner evaluator. For a reduced interval contained in `[-1,1]`,
let its exact midpoint be `m` and half-width be `w`. Both sine and cosine are
globally 1-Lipschitz, so an enclosure of their value at `m`, enlarged by `w`,
contains their value at every point of the original interval.

At Taylor iteration `k >= 1`, the included sine and cosine terms have magnitudes
`|m|^(2k+1)/(2k+1)!` and `|m|^(2k)/(2k)!`. Each series alternates, and each next
term is no larger because `|m| <= 1`. The alternating-series remainder after
including iteration `k` is therefore bounded by the next term and hence by the
already computed current term. The reference uses the larger current magnitude
as a common conservative tail, stops only when it is below `2^-(bits+8)`, adds
`w` exactly, and rounds both result endpoints outward on the unchanged grid.
The bounded iteration count, operand guards and work callback remain in force.

Using the actual current term replaces the previous global `1/(2k)!` tail;
smaller reduced arguments need fewer exact terms. It changes no production
source error allowance or destination tolerance. The authored check independently
constructs direct power/factorial Taylor sums with next-term enclosures at 128
and 256 bits, including signed endpoints, intervals crossing zero and a small
argument, then verifies that small arguments consume less charged work.
