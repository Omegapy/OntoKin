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

At commit `f7706acc369b1ad2df151a2d1e803f8c6d8e50ba`, a fresh focused run
passed all 46 methods in 2.324 seconds on CPython 3.12.14 with a complete `OK`
footer and no failures, errors or skips. Its log is
`reference-bounds-tail-002/tests.log`. Attempt 001 again returned process exit
zero with an incomplete log and no footer; it is retained separately and is not
counted as a successful execution.

The corresponding P23-only probe 003 established six of twelve requests, with
stable complete tracked inputs. Initial before/after requests used 67,036 and
89,070 outer operations. Previously blocked samples 002, 004, 006 and 008 proved
at 99,879, 99,889, 99,900 and 99,630 operations respectively. Requests 003, 005
and 007 still exhausted the shared budget during requested point-basis
construction; terminal requests 009–011 still exhausted during independent
reference initialization after source observation. Every result and failure is
retained in `reference-inventory-probe-003/`. The small successful margins are
measurements of this exact tree, not a new guaranteed resource margin or a
completed rate-acceptance gate.

## Repeated independent derivative-bound algebra

Constant source-basis values depend only on the exact local position, the
constant/inverse role and the arithmetic precision. Bound composition depends
only on the complete two immutable `_SourceBound` values and that precision.
Those pure calculations now use the same bounded 256-entry arithmetic cache;
they allocate no additional allowance or unbounded secondary table. Every
lookup and new entry charges the existing work callback. A composition key
contains every source-bound field, including derivative errors, source/ideal
speed bounds, acceleration, angular acceleration, coordinate discrepancy and
all operation counts. An altered rate or error therefore cannot borrow an
unrelated bound.

The independent graph walk, state/side selection and coordinate-path derivation
still run for each requested phase. No source identity or lifecycle conclusion
is cached by numeric coincidence. Authored tests compare full point-phase
records with the same evaluator forced to recompute every bound expression,
including incoming/completed reach motion and attached/released force-driven
payloads. They also require the distinct physical rate bounds to remain distinct
and the shared cache to retain its original entry limit. Execution follows in a
separate identified checkpoint.

Independent pose composition also omits derivative-only expressions when all
four complete three-component input velocity/omega intervals are exactly zero.
Then both rotated rate vectors and the cross product are exactly zero under the
raw Hamilton algebra; no quaternion-unit assumption is required. Position and
orientation arithmetic still execute, the full composition key still includes
all rates, and an interval merely containing zero takes the full derivative
path. This particularly avoids calculating unused zero derivatives in recording
pose queries. An analytic cyclic-axis rotation, a nonzero uncertain rate and
cancellation on a repeated zero-rate composition cover the shortcut.

At clean merge `bc7263213e85e68b173ef6afbc9b8d4ca4290bbb` (integrated
`bb0cfba` plus independent zero-rate composition `8bd0c53`), all 48 focused
methods passed on CPython 3.12.14 in 2.569 seconds with a complete `OK` footer.
`reference-bound-reuse-001/tests.log` retains the result. The P23-only probe 004
retained stable inputs and still proved six of twelve requests. Initial
before/after costs were 66,867/88,913; samples 002/004/006/008 used
99,616/99,626/99,637/99,367 operations. The other six remain resource failures.

A separate diagnostic on that same commit measured all six P01 object carriers
through the independent recording-pose API at `1/8`, `1/4` and `3/4` seconds.
The respective costs were 440, 297 and 318 shared reach operations, with 6,622
total outer operations including compilation and reference construction. The
last two queries reused established constants. Their sine/cosine calculations
cost 104 and 125 operations, including Taylor sums of 89 and 110; composition
cost 74, including rotation cost 47. These are **nested inclusive counts**, not
additive totals. `reference-pose-profile-001.json` records every carrier and
method count. This diagnostic measured independent p/q construction alone; it
does not establish the cost or correctness of a complete supplied GLB proof.

The exact fixed zero vector and world identity pose now reuse immutable values
in the same bounded arithmetic cache. This replaces repeated conversion and
allocation of those fixed constants at every graph clock. The zero-vector path
requires object identity with the module's immutable `ZERO` constant; arbitrary
supplied tuples retain ordinary numeric admission. A cache miss executes the
existing guarded construction, every lookup charges the original callback,
and eviction can only cause that same construction to run again. No new cache
or persistent capacity is added. The regression covers exact values, charged
reuse, eviction/reconstruction, invalid nonconstant operands and cancellation.

## First complete pointwise rate inventory

At clean merge `da073f398c5890b2ee710e9a8adedf6b0ce1b1be`, whose tree
`c013127f92fb1c30e6a038548cd1cfd36822ba48` is identical to integrated root
`a5d93c23cb4e498a37a119ddaea59a215ec2a287`, all **84 focused methods passed**
on CPython 3.12.14 in 3.063 seconds with a complete `OK` footer and no failures,
errors or skips. The cohort comprised 29 production pose methods, 49 independent
reference/rate methods and six destination-inventory methods.
`reference-common-focused-001/tests.log` preserves the complete command and result.

The first complete inventory then executed all **362 requests / 724 frozen
coverage fields**, with stable tracked inputs before and after the run. It
proved **351 requests / 702 coverage fields**. No completed comparison reported
`contradicted` or `unresolved`; eleven requests failed their existing resource
guards and are not counted as proved. The complete reports, request identities,
input hashes and failure stacks are retained in
`reference-inventory-complete-001/`, with the external execution log in
`reference-inventory-complete-001.log`. Execution began at
`2026-10-21T06:10:36.136448+00:00` and finished at
`2026-10-21T06:11:22.467237+00:00`.

The remaining failures are distinct:

- Nine P23 requests (`002`–`007` and `009`–`011`) exhausted the original shared
  operation budget. Requests `002`, `004` and `006` reached the fresh wrapper's
  final input-fingerprint check; completing earlier comparisons does not turn
  those incomplete end-to-end requests into accepted results. Requests `003`,
  `005` and `007` failed during point-basis construction. Requests `009`–`011`
  failed while initializing the independent reference after source observation.
- P24 requests `010` and `011` reached the independent **complete H06 history
  capacity** guard, reporting more than 100,000 weighted boundary records. This
  is a recording-history resource rejection, not an operation-budget exhaustion
  or a numerical contradiction. The rate request asks for a single observed
  time and side; the current reference also insists on complete recording
  capacity. That API-scope mismatch requires a separately explicit observation
  mode, without changing the default recording cap or allowing that mode to
  provide complete `boundary_states` evidence.

The comparison criterion remains **proposed and not adopted**. These measured
results do not close the source-execution role, independent rate acceptance,
recording delivery, the reach release or the full product goal. Every request
retains one compiler/source/reference/comparison budget; no frozen expectation,
source allowance or resource limit was changed for this inventory.

## Repeated physical values in complete independent observations

Each independent `sample` now owns a temporary table of at most 256 physical
joint observations. A value contains the independently computed exact
coordinate/rate and their public binary64 projections. The joint rows and every
reach action referring to the same joint in that unchanged sample reuse those
immutable values. The table never survives the particular state, time and side;
if full, another joint is evaluated normally. Every lookup and insertion charges
the existing callback.

World-target construction also reuses a pure result in the existing bounded
arithmetic cache, keyed by the complete immutable base pose, exact target and
precision. A changed base pose or target cannot borrow a previous answer.
Action identities, provenance, lifecycle, admission, claims, elapsed clocks,
own commanded rates, residuals and terminal records are still constructed for
every action. All public containers are fresh, and H06 continues to count every
repeated occurrence. This reduces repeated arithmetic in the 128-action P24
boundary observations without removing any identity or history record.

Authored regressions compare the entire P24 projection against forced fresh
coordinate/target computation, require the active and pending records to keep
their distinct action state, test public mutation isolation and earlier-side
queries, and exercise capacity, changed operands and cancellation. Execution
of this change is recorded separately from the 84-test checkpoint above.

## Independent recording pose batches

`recording_pose_enclosures(carriers, time, side, ideal=True)` accepts a finite
list or tuple bounded by the captured source's total carrier inventory. It
validates each requested identity and resolves their ancestry union through one
independent `_pose_map` call. The returned fresh map uses canonical names and
exposes only the requested immutable position/orientation enclosures. The
single-carrier API delegates to this method and retains its return type.

This removes repeated construction of the same incoming relation map when a
reader compares several carriers at one actual key. It neither computes
unrequested carrier subtrees nor exposes private zero derivatives as rate
evidence. State, exact time, side, ideal/actual convention and pose-only cache
namespaces remain separate. Selection admission, work callbacks, unknown
identities, incoming-only prefixes and normal source capacity remain enforced.
Focused authored tests compare batch and full individual enclosures, require a
single graph construction, and check selected ancestry, fresh output, count and
type bounds, invalid sides and cancellation. Execution is pending separately.

## Explicit observation scope for independent rate requests

`build_reference(..., mode="observation")` now names the single-observation
scope separately from the unchanged default `mode="recording"`. Both modes
execute all required source boundaries, natural completions, authored events,
release/force/impulse effects and exact side semantics through the requested
prefix. Both retain the original caller's operation allowance, operand guards,
arithmetic cache limits and the 10,000-boundary retained-state cap. A requested
complete single reach projection retains its original capacity check.

Observation mode omits only the **aggregate projected H06 recording-history
capacity claim**. It does not allocate that projection, and its
`boundary_states()` always rejects. If a caller requests a full `sample`, its
actual output must pass the existing 100,000-entry/depth logical walker. The
default recording mode still preflights the entire conservative H06 sum before
retaining each state pair and checks actual complete histories against that sum.
No source language limit, recording limit or numerical acceptance value changes.

The fresh rate wrapper selects observation mode explicitly and records it in
every report. This addresses P24's measured mismatch between one source rate
observation and an unrequested complete-recording precondition. The pending
criterion's exact Euclidean comparison and proposed/not-adopted status remain
unchanged. Authored checks preserve the P24 default recording rejection while
requiring a bounded terminal observation, reject history delivery from that
mode, compare full release/force pose and derivative equations across modes,
and retain failed-boundary side, state-cap, invalid-mode and callback behavior.
Actual execution results follow in a separate checkpoint.

Observation mode also defers hypothetical maximal reach-map construction and
geometry expectation materialization until `sample` or `geometry_expectations`
is actually requested. Rate-only pose and point-basis equations use neither
projection. The same maximal reach-map check runs before sample allocation;
the same guarded geometry capture runs before geometry output. Each complete
result is published to its private slot only after successful construction.
Default recording mode still performs both preparations eagerly. A regression
keeps rate equations usable when these unrequested output guards are armed,
then requires the original exceptions on the corresponding actual requests,
no partial cache publication and independent fresh geometry output afterward.

## Integrated observation and batch verification

At clean merge `8d3a0baed2d28782a8a8830d2521f182be4edeb2`, tree
`fc0f106ded876425569a1a25ec24616aefc5a7d5` is identical to root
`dc5ae5cb655d86c4861e4cc6a7de5ea6aeb6bf62`. All **89 focused methods passed**
on CPython 3.12.14 in 4.066 seconds, with a complete `OK` footer and no failures,
errors or skips: 32 production pose methods and 57 independent reference/rate
methods. `reference-common-focused-002/tests.log` preserves the execution.
This includes all observation reuse, batch-query, explicit-mode and lazy-output
guards described above, together with the inherited numerical checks.

The corresponding P23/P24 probe 005 executed all 24 selected requests with
stable tracked inputs. **Twenty-one requests / 42 frozen coverage fields
proved**. Every P24 request now proves, including the two terminal observations
previously rejected by the unrequested complete-history precondition. Its outer
operation counts range from 23,745 to 38,136. P23 requests `000`–`008` prove
within 61,137–95,577 operations. Only P23 requests `009`–`011` still fail the
original shared budget, during independent reference initialization. All
reports and failures remain in `reference-inventory-probe-005/`; the external
log is `reference-inventory-probe-005.log`.

A focused stage diagnostic on that same clean cut identifies the terminal P23
cost before the independent proof:

| P23 request `sample-011` stage | Outer operation count |
| --- | ---: |
| Compilation completed | 35,913 |
| Fresh source snapshot entered | 37,186 |
| Fresh source snapshot completed | 99,105 |
| Selected rate observation extracted | 99,151 |
| Independent reference entered | 99,195 |
| Shared request exhausted during initialization | 100,001 |

The source snapshot itself costs 61,919 operations. Reference construction has
only 805 successful operations left in this request. Further independent
trigonometric tuning cannot supply the missing source-evaluation margin.
`reference-stage-profile-002.json` retains the full stage trace and charged
work-category counts.

The same diagnostic also completed default **recording-mode** P24 histories for
the quarter-second prefix. Compilation used 17,568 operations, independent
construction added 5,234, and complete boundary projection added **7,287**,
for 30,089 total. Both exact boundaries (`0`, `0.25`) retain all 128 actions on
both sides; the unchanged conservative H06 preflight is **84,954 weighted
records**. This measures independent history construction, not a complete GLB
export or supplied-byte acceptance.

The full 362-request inventory was not repeated on this cut because the scoped
probe still has three concrete resource failures. Results from different trees
are not combined into an unexecuted complete acceptance claim. The criterion
remains proposed/not adopted, and the source execution, delivery, release and
full-product gates remain open.

### Terminal P23 source breakdown

A second diagnostic at clean `fdc49f7a06cb6f02012aff1359616a70d4617bd0`
executed the original P23 `sample-011` source request directly, retaining the
original compiler budget. It completed at **98,993 outer operations**, returning
all 97 objects and 32 completed reach records. The 112-operation difference from
the preceding wrapper's 99,105 source-snapshot endpoint is the wrapper's input
identity work; this direct diagnostic is not a rate proof and does not include
reference construction or rate comparison.

`reference-p23-source-breakdown-001.json` preserves the exact source/program,
commit/tree, clean before/after state, category counts and nested method spans.
The source `advance` cost remains **61,919 operations**. Its principal stages
are the `t=0` boundary (31,197), `t=2` completion boundary (23,254), and final
`t=3` snapshot (7,174). Simulator initialization is a separate 1,161 operations.

| Measured method | Calls | Inclusive operations | Self operations |
| --- | ---: | ---: | ---: |
| Controlled pose composition | 1,988 | 19,035 | 13,353 |
| Source per-node pose slot | 1,800 | 31,004 | 5,171 |
| Public vector projection | 1,909 | 5,095 | 5,095 |
| Public pose-field exposure | 4,192 | 11,247 | 4,192 |
| Exact vector addition | 1,992 | 3,690 | 3,690 |
| Constant source-pose lookup/build | 1,668 | 4,140 | 3,354 |
| Terminal base-tip calculation | 32 | 1,003 | 128 |

Inclusive counts overlap nested calls. Self counts subtract only instrumented
child spans; they must not be mixed with inclusive counts in a sum. Full
kinematics calls at `t=0` and `t=2` account for 18,832 and 15,685 inclusive
operations. All 33 calls at `t=3` hit the complete graph cache and cost only 66
operations. The measured remaining source cost is therefore concentrated in
boundary graph composition and projection, not rebuilding the final graph or
independent trigonometric evaluation.

## Immutable source-location projection reuse

Repeated named actions can share the same frozen four-field source location.
The independent description path now caches only that scalar projection in the
existing 256-entry pure arithmetic cache. The key contains the complete source
ID, revision, start byte and end byte; exact scalar types and integer widths
are checked before lookup. Only the fixed frozen dataclass shape is eligible.
Other shapes, including a dataclass containing a mutable field, retain the
ordinary recursive source-record conversion.

The cached result is an immutable tuple of field/value pairs. Every occurrence
receives a new dictionary, while action identities, description identities,
chain records, target records and lifecycle observations are still constructed
for that occurrence. A cache hit polls the original shared work context. Cold
conversion and publication retain the original recursive work and cancellation
points, and no partial result is stored after interruption. Complete maximal
and actual H06 weights still count every repeated field and occurrence.

Two focused regressions compare all 128 P24 descriptions and their complete
maximal weight with ordinary conversion; check independent mutable output;
change every key field; reject an over-width byte offset; preserve mutable-shape
fallback; exhaust the original cache capacity; and retain warm-hit cancellation.
These new methods await the next exclusive execution window. This is pure
source-metadata reuse and introduces no numerical allowance or rate verdict.

### Terminal rate probe after the first derivative omission

The three remaining P23 terminal requests were executed on clean, detached
`21ebfca62d7be6f53f8375b7777c470a088adb33`, tree
`19a0e8db2099c9fe9f8d52392ce8f23c9b711ec9`, after the production composition
change that omits exact zero local derivative terms. All three (`sample-009`,
`sample-010`, `sample-011`) still exhausted the original shared request budget
during independent initialization of a placement position. No request proved;
the three errors retain `OKL-E-RESOURCE`, phase `support`, category
`resource_limit`, and their complete original tracebacks.

`reference-terminal-probe-001/` and its external `.log` preserve the complete
three-request selection, all tracked input hashes, exact collector hash,
interpreter/platform and unchanged before/after Git state. This is an explicitly
partial diagnostic with six frozen coverage fields, not a complete inventory.
The full 362-request inventory was not repeated because this prerequisite still
failed. No earlier partial or complete result is relabeled as success at these
changed bytes. Subsequent source arithmetic savings require a fresh probe.
