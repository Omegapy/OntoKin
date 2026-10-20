# Reach source and lifecycle implementation

This implementation note describes the explicit `planar-reach-0.1` source path.
It does not change the adopted contract, its frozen corpus, or any earlier
profile's numerical behavior. Runtime and release acceptance are separate from
the static implementation checkpoints recorded in Git.

## Source authority and the transaction

The builder produces an immutable description with source identities, two joint
references, the tip, framed target, duration and selected branch. Actual named
descriptions are structurally bound after the ordinary relation validation.
Construction performs no inverse-kinematics admission.

`ReachSimulator` extends the inherited force transaction. Both coordinate claims
and the selected target are admitted together. Natural completions and all
ordered source statements operate on one staged state. Complete reach maps and
incoming-release records pass their output guards before that state is committed.
An exception retains the incoming state, both original claims and the event index.
The released sphere receives the saved incoming pose and velocity, including
the reach's exact slopes and root motion even when the reach completes at that
same clock. Public goal outcomes are pending, active, interrupted and satisfied.

Each before/after side contains every named reach, including pending actions.
Stopped and completed terminal results remain latched while the current physical
coordinates can subsequently move under a different owner. Source-only inspection
cannot synthesize a run; it returns the adopted `run_required` availability.
Agent acceptance and issued run identities are bound by the Agent publication
layer, rather than inferred from a zero timestamp or modified in historical data.

## Work and output counting

The compiler owns a transient `ReachExecutionWork` whose external callback charges
the same `ConstructionBudget` that counted the preceding compilation. Evaluation
and delivery accept this object explicitly for the same request. A separate direct
evaluation creates a fresh bounded context. Neither the immutable model nor a
saved run stores the elapsed clock, proof cache or request counter.

Numerical helpers charge every actual arithmetic constituent through that shared
work context. The separately capped admission recurrence count never creates a
second 100,000-operation allowance. Callback exceptions keep their original identity.

JSON traversal has different units. `measure_reach_json` still counts every
recursive value/container occurrence and every compact UTF-8 byte, including
repeated identities and descriptions. It batches at most 128 traversal callbacks
into one cooperative work checkpoint, matching the inherited bounded-data
strategy. A remaining partial batch is flushed on completion. Traversals retain
the finite 100,000-entry, 4 MiB and depth limits, and numerical arithmetic never
uses this batching adapter. This does not waive any intermediate or final Agent
logical-entry budget, including the adopted exact `N`/`N−1` publication probe.

Complete source snapshots also pass through inherited `bounded_data` before
publication. This expands internal geometry dataclasses into their complete
JSON contents under the same recursive entry/byte/depth guards. It preserves
every geometry field and counts repeated occurrences; applying a JSON-only
counter directly to an internal `LoftSection` is not a valid materialization.

`reach_record_bound` uses the maximal complete lifecycle shape rather than pending
null fields. `boundary_history_bound` implements `H06`: both inherited side
weights, both complete reach maps, the wrapper and source clock, and the full
incoming-release array. Contributor bounds follow the actual finite topology and
include every potentially contributing named action. The prefix horizon prevents
later authored force/impulse histories from entering the bound. Actual output is
still measured after this conservative preflight.

## Controlled poses and remaining proof integration

Only source 0.6 dispatches to the controlled pose helpers. Private projective
rotations and exact derivative values remain private through parent/child
composition. Canonical tuples are exposed at samples and true event anchors;
older profiles retain their existing arithmetic. The separate numerical derivation
identifies each controlled helper and its error bound.

Continuous-phase certificates additionally require explicit ideal starts,
derivative bounds and propagated anchor discrepancies across stop, restart,
release and force/impulse anchors. Those phase inputs are a separate integration
obligation; a successful point sample is never a uniform phase certificate.
