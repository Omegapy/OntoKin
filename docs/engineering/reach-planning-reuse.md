# Reusing completed recording planning work

This implementation note covers only repeated structural work and completed
boundary projections in `reach_prefix_plan`. It changes no source equations,
source or destination error bound, acceptance criterion, or budget. The existing
100,000-operation request limit, 32,768-bit operand limit and 256-entry numerical
cache remain in force. It is development work until the applicable identified
verification evidence and complete release gates pass.

This port recovers the separately preserved work in `fc43d95`, `77c2a73`,
`c7be638` and `7eea7bb`. Their historical execution results do not establish
current verification. The current port retains the optional recording angular
proof argument and the existing incremental boundary-history preflight.

## One carrier selector per prefix

Each recorded phase needs every object frame and every possible joint-parent
frame, including parents retained after release. Their ordered structural list
depends on the same model throughout an ordinary prefix. `_PrefixFrameSelection`
constructs and deduplicates that list once. Later phases compare the actual
ordered object paths and joint-parent names, along with the current model/work
owner, before reusing the tuple. A changed topology or owner rebuilds it.
Cold construction also checks the complete ordered inputs after its callbacks;
changing an earlier parent during a later visit cannot publish a mixed list.

Only construction of this list is shared. Every phase still runs the complete
existing source dependency traversal, with its own exact clocks, claims, roots,
joint coordinates and error bounds. Standalone `recording_phase_bounds` calls
have no retained selector and construct a fresh list. There is one structural
selector per prefix, independent of the numerical LRU.

## Exact measurement of empty force histories

Within a single `_bounded_projection` call, the first complete empty force
history supplies an exact JSON entry/byte measurement. Another actual fresh
projection may share those two integer counts only if it has the exact plain
empty shape: positive binary64 zero net force, no acceleration, strict integer
zero counters, no active/latest records and no last-change time. Negative zero,
integer-valued vector components, booleans, other types, nonempty histories and
malformed data all use the original complete walker.

Every object still executes its occurrence checkpoint and constructs its own
history. Every occurrence adds the full logical entry and byte counts. Reuse
requires those complete counts to fit both remaining limits; on any possible
overflow, the original walker determines the first failing entry/byte and
preserves its diagnostic ordering and consumed count. This retains only one
measurement within the call, never a public output object or a numerical result.

## The unchanged final endpoint

A requested prefix can end strictly before the next semantic boundary, or
after the final semantic boundary. Its `before` and `after` observations are at
the same exact clock and may have the same complete state. The planner still
calls ordinary `advance` for both sides. Time zero and actual transition times
always use ordinary projection. Dynamic states currently use ordinary
projection as well.

For an eligible endpoint, an ephemeral receipt is captured before the ordinary
`before` projection. It contains an exact structural description of the actual
state, including action/force/impulse histories and numerical operands, and a
separate description of the source operands consumed by retained projections.
The latter binds actual source/occurrence identities and provenance, joint
fields, action clocks, bound reach payloads, site poses and follow dependencies.
It does not infer equality from state or model identity. Each description
supports only known dataclasses and exact built-in containers/scalars, with at
most 16,384 visited values, depth 32, bounded scalar widths and finite floats.
The model description additionally bounds the total structural record count at
4,096; construction ASTs, geometry and unrelated inspection provenance are not
read by these projections. Unsupported
objects, cycles or larger shapes make the optimization ineligible. No new
numerical result is retained and the receipt exists only for this endpoint.

Structural checks yield every 128 visited values. A subsequent bounded
callback-free comparison detects a callback that changed an already visited
field. Each structural checkpoint immediately leaves reuse if its callback
narrows the operand domain; it cannot wait for a later callback to restore that
domain. The receipt also binds the actual model, work, pose operations, callback,
state identity, context, exact transaction clocks, pending-output state and live
operand/force-output limits. A mismatch leaves the ordinary projection in
charge, including a callback that mutates fields of the same model object.

The ordinary after-side `recording_boundary` still resolves the complete graph,
checks every selected and unselected frame, constructs/checks each force and
impulse history, and verifies every aggregate mass. After those checks, unchanged
joint/action/reach projection work may be reused from the already bounded
before output at the same exact requested clock. A mismatched clock or input
side falls back to ordinary projection. A private shallow replacement changes only the top-level side
and each current reach observation's side. The ordinary complete output
materializer then creates fresh containers and checks the full actual after
entry/byte counts. A final live-state/domain check precedes publication. A
callback mutation during copying discards that candidate and rebuilds the
ordinary after projection under the actual current state.

Thus both complete H06 sides, source identities, histories, limits and private
output graphs remain present. Cancellation propagates the original callback
exception. Existing boundary transactions, future-event admission, invalid
prefix recovery and Agent delivery transactions are unchanged.

## Focused verification

`test_reach_planning_reuse` compares complete prefixes, retained phase states and
actual GLB bytes against ordinary projection/list construction. It covers the
32-arm P23 source, a valid L04 prefix, dynamic fallback, fresh before/after
objects, in-place state/model callback changes, mutation of an earlier receipt field,
mutation during output copying, narrowed domains, unsupported/cyclic state,
after-only unselected-frame failure, cancellation identity and topology/owner
changes during both cold construction and reuse. The force-projection cohort also compares exact cumulative JSON limits
and distinct zero/count encodings against the inherited walker.

No test or recording execution is claimed by this note alone. Exact revision,
commands, input receipts, logs, observed failures and successful results belong
in the accompanying execution evidence before integration.
