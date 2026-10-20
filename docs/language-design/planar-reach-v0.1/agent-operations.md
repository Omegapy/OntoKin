# Proposed Agent/0.6 operations and complete reach projections

This document belongs to **OK-LANG-006 0.1.0-draft.2** and remains **unadopted
and unimplemented**. It is newly reconstructed proposal work identified as
`agent-contract-reconstruction-2026-10-20-14`, based on published draft
`e5ffcf98f2532a2cf8e7a15a7446dac7be7d6f9d`, the actual inherited Agent/0.5
contracts and the retained final review decisions. It does not claim byte
equivalence with the unavailable earlier Agent document, schemas or reports.
The new checks in [agent-review](agent-review/README.md) are schema and contract
preparation, not execution of the proposed language or service.

[OK-LANG-006](../OK-LANG-006-reusable-planar-reach-actions.md), the effective
Draft 2 amendments, [budget counting](budget-counting.md) and the
[release contract](release-contract.md) govern the finite proposed capability.
The adopted [Agent/0.5 interface](../../engineering/OK-AGENT-005-finite-force-program-workflows.md)
and its inherited operations remain the baseline. A separately published
adoption record must identify the complete reviewed bytes before implementation.

## 1. Explicit binding and schema authority

| Contract | Proposed binding |
| --- | --- |
| Source entry | `ontokin "0.6"; profile "planar-reach-0.1";` |
| Request and response | `ontokin.agent/0.6` |
| Discovery | `ontokin.agent-catalog/0.6`, profile `planar-reach-0.1` |
| Recorded destination | `ontokin.glb/0.6` |
| Durable filename | `planar-reach-program-agent.sqlite3` |
| Store schema | `ontokin.planar-reach-program-agent-store/0.1` |
| Source closure | Unchanged `ontokin.bundle/0.1` |
| Diagnostics | Unchanged envelope `ontokin.diagnostic/0.2`, with the reach specialization below |

Selection is explicit. A request cannot change an existing service's binding,
database or runtime profile. The new store must coexist with the inherited
stores in one directory without interpreting their rows, cursor secrets, request
identities or artifacts as its own. Earlier Python/CLI defaults, catalogs and
profile meanings remain unchanged. A schema-valid proposed request does not
mean the current service implements it.

The seven [schema drafts](schema-drafts/schema-drafts-manifest.json) use IDs under
`https://omegapy.github.io/OntoKin/proposals/planar-reach-v0.1/`. These are proposal
identifiers, distinct from the adopted schema namespace. The
[generator](author_schema_drafts.py) derives the request and response envelopes
from the actual Agent/0.5 schema bytes, records every inherited schema input and
the unchanged original corpus inventory hash, and writes deterministic JSON.
It does not parse, construct or evaluate a reach program.

The request schema preserves strict unknown-field rejection, operation names,
source bundle shape, UTF-8 patch preconditions, source/module authority,
destination/options dependencies, finite request budgets and existing response
levels. The only request-binding changes are Agent/GLB0.6, the new discovery
profile and the reach maximum `time_tolerance_s=1e-6`. Integer wire fields still
require integer JSON tokens; JSON Schema's mathematical integer test alone is
insufficient. Byte lengths, Unicode scalar strings, finite numbers, duplicate
JSON keys and all cross-field identities also require semantic validation.

## 2. The twelve inherited operations

Every request contains `schema_version`, `project_id`, `request_id` and
`operation`. This table lists the remaining required fields; optional fields
and exact limits are fixed by the [request schema](schema-drafts/agent-request.schema.json).

| Operation | Required operation fields | Meaning for planar reaches |
| --- | --- | --- |
| `discover` | `profile`, `limit` | Discover typed `ReachBranch`, its two enum values, the builder signature, reusable public methods, supported ranges, schemas, levels and unavailable domains. Optional `bundle` and `program_revision` are mutually exclusive. |
| `create` | `bundle`, `expected_program_revision`, `requested_level` | Snapshot and validate exact `.ok` closure. Acceptance occurs only when the requested level succeeds and the expected accepted head still matches at publication. |
| `edit` | `expected_program_revision`, `patches`, `requested_level` | Apply one atomic source transaction with exact per-unit hashes, UTF-8 spans, expected text and authorized occurrence scope; preserve inherited optional `module_changes`. |
| `validate` | `program_revision`, `requested_level` | Validate an immutable accepted, historical or candidate snapshot without silently accepting it. A candidate diagnostic run retains its own identity and provenance. |
| `inspect` | `program_revision`, `selector`, `fields`, `limit` | Inspect bounded source-derived records. Optional `run_id` and `time` select actual available state. Reach records are complete members of the existing `actions` group. |
| `evaluate` | `program_revision`, `run_id`, `until_seconds` | Start a fresh run when `run_id` is null, or extend the specified compatible accepted run. It performs no source edit. |
| `reset` | `program_revision` | Create a fresh accepted-source run at `0`, side `before`, with pending named actions; preserve old runs and source bytes. |
| `status` | `target_request_id` | Reconcile the retained operation receipt, including unknown outcome, terminal failure and cancellation. |
| `cancel` | `target_request_id` | Request cooperative cancellation of an accepted operation; observe its eventual terminal state before claiming cancellation succeeded. |
| `export` | `program_revision`, `destination` | Deliver the exact accepted-once source snapshot through GLB/0.6; optional `options.end` authorizes only the requested prefix. |
| `artifact` | `artifact_id` | Retrieve the committed artifact's exact bytes using inherited `offset` and `max_bytes` chunks and immutable provenance. |
| `surface.mesh_page` | `program_revision`, `element_id`, `count` | Retrieve complete native triangles for an accepted-once occurrence with the inherited region/query/geometry identity and signed cursor. |

There is no host-only reach, target, branch, joint-angle or velocity mutation.
Agents request a goal by writing the reusable `.ok` call and its source events.
Ordinary surface inspection and mesh pages retain `surface-0.1` geometry/PBR
shape, local coordinates and triangle ordering. The new entry profile does not
rename those inherited geometry contracts.

`destination` is explicitly `ontokin.glb/0.6`. On create/edit/validate, supplying
destination or options requires `requested_level="delivered"`; options also
require destination. Older destinations are rejected. A missing adapter must
produce the inherited explicit unsupported result without an artifact or
delivered-level success. Discovery advertises only actually implemented support.

## 3. Immutable source, acceptance and run identities

| Identity or field | Required interpretation |
| --- | --- |
| `program_revision` | The exact requested complete immutable source closure, including rejected candidates and accepted historical programs. It is never replaced with the accepted head merely to make an inspection appear current. |
| `accepted_program_revision` | The actual accepted project head observed for this response's publication; null before first acceptance. A retained/retried receipt preserves the head recorded at its original publication. |
| Projection `candidate_only` | In Agent context, whether this inspected source has never been accepted at that publication. An accepted historical revision is false even when its hash differs from the current head. |
| Run `candidate_only` and `origin` | Retained provenance of the specific run. A run created only for candidate diagnosis cannot be reused as an ordinary accepted run merely by replacing request fields. |
| `source_location` | Actual source unit ID/revision and UTF-8 start/end bytes within that requested program. The span is not a substitute for writable source authority. |
| `element_id` / `description_identity` | The named lifecycle occurrence and the source description identity. Sharing a description never merges two named lifecycles or their coordinate claims. |
| `run_id` | The service-issued identity of an actual retained run with its own immutable program and implementation binding. It cannot be fabricated by a shape fixture or copied onto another revision. |

Failed source edits preserve the accepted head. A stale expected head, wrong
source hash, invalid UTF-8 boundary, expected-text mismatch or unauthorized scope
must fail atomically. A candidate may remain available for diagnosis; its
existence and valid JSON shape are not acceptance. Export and mesh-page requests
require a source that was actually accepted at least once. Retained historical
accepted programs, runs and artifacts keep their original complete closure.

Cursor context includes the selected Agent binding, entry profile, implementation,
project, requested program revision, query, fields, frame, run and time as
applicable. Mesh pages additionally bind occurrence, geometry and region. Preserve
the inherited 65,536-byte cursor limit. Cross-profile, cross-project, altered
query, stale run and incorrect-signature substitutions fail without changing
accepted source or runs. Repeated request IDs with identical canonical payloads
return the retained receipt; changed payloads are rejected rather than reexecuted.

## 4. Complete action projection

The [reach projection](schema-drafts/reach-projection.schema.json) appears as one
complete `inspect.result.items[].actions[]` member and as each
`snapshot.reaches[path]` value. The enclosing source and response identities must
agree with it. Existing joint/action summary rows remain independently present;
the rich map does not exempt them from history or output accounting.

Every projection includes `kind="reach_planar"`, lifecycle occurrence and
description identities, the requested program and acceptance context,
`source_location`, `channel="joint_coordinates"`, chain, typed target, branch,
canonical duration and `current`. The chain identifies the shoulder, elbow,
end site and exact base-site frame, actual effective lengths and both effective
closed limits. The target retains that exact frame identity and finite local
coordinates; a coincident different frame is not equivalent.

For Agent output, `context_origin="agent"` and `candidate_only` is a Boolean.
Recorded source projections use `context_origin="source_recording"` with null
acceptance and candidate fields. Recorded artifact metadata cannot invent an
Agent acceptance; the separately identified Agent receipt/artifact provenance
binds the service delivery.

Without an actual sample, `current` is exactly
`{"available":false,"reason":"run_required","value":null}`. Source-only
inspection, including candidate inspection, does not fabricate pending state.
An inspection time without a matching run remains an inherited sampling error.
With an actual sample, `available=true`, `reason=null` and `value` contains the
complete state described below.

An unresolved source or definition record retains the inherited unavailable
**actions group**, with reason `source_is_unresolved` or
`definition_has_no_occurrence_state`. That group is not a constructed reach
projection and cannot stand in for a complete requested occurrence group.

| Observation context | Required clock/run meaning |
| --- | --- |
| `constructed_initial` | A real construction result at `time_seconds="0"`, `side="before"`, with null run ID. It precedes all zero-time source events and every named reach is pending. |
| `run_sample` | An actual compatible retained run and available requested side/time, with a nonempty run ID. A reset run is still a run sample even at zero before. |
| `recorded_prefix` | An independently source-bound before/after sample represented in recorded metadata, with null service run ID. It is not an unrun Agent inspection. |

The response schema distinguishes `result.initial_state` from
`result.run_state.last_valid_state`. A constructed result does not acquire a run
just because its sample is valid. A run descriptor and each nested observation
must carry the same actual run identity and source; these equalities are semantic
checks beyond JSON Schema.

`current.value` contains observation; lifecycle and goal outcome; resolved target
and captured starting coordinate pairs; exact start, elapsed and applicable
completion clocks; actual joint coordinates/rates; this action's own rates;
claimed joint IDs; current residual; base/world tip poses; current equivalent
world target; and the nullable latched terminal result.

| Lifecycle | Goal outcome | Claims and completion | Terminal result |
| --- | --- | --- | --- |
| `pending` | `pending` | No claims. Resolved targets, captured starts, start/elapsed/completion clocks and current residual are null. | Null |
| `running` | `active` | Both distinct coordinate claims; original admitted targets/starts and current exact completion clock. | Null |
| `paused` | `active` | Both claims retained, physical and own rates zero, held elapsed/coordinates, completion clock null until resumed. | Null |
| `stopped` | `interrupted` | Claims released; completion clock null; admitted starts/targets and stopped elapsed retained. | `outcome="interrupted"` |
| `completed` | `satisfied` | Claims released; actual completion clock retained. | `outcome="satisfied"`, completion residual at most `1e-9 m` |

These four values are the complete current goal-outcome set. Failed admission
belongs to diagnostics on the failed request/boundary. It cannot overwrite the
valid incoming projection with a `failed` current goal or a partially admitted
target/claim pair. A stopped action is interrupted even when its current pose
happens to meet the goal.

`joint_coordinates_rad` and `joint_rates_rad_per_s` describe the actual physical
coordinates at observation. `action_joint_rates_rad_per_s` describes only this
action's contribution and is zero while pending, paused, stopped or completed.
A pending action can observe another owner; after stop/completion another action
can move the same joints. The old action's current residual and physical rates
then change normally. Its terminal outcome, terminal time, terminal coordinates,
base tip pose and measured terminal residual remain latched. The satisfied
residual bound applies to that terminal snapshot, not to every later physical
pose. Complete projections must not substitute old terminal coordinates for
current coordinates or suppress the new owner's physical rates.

## 5. Exact boundaries, failure and recovery

Two-coordinate admission is one staged transaction. Failed structural/domain,
claim, reachability, singularity, branch-limit, numerical or resource checks
cannot publish one successful claim or one changed coordinate. The inherited
whole exact-boundary transaction includes natural completions, source events and
force completions. A failure later in `stop old; start new;` rolls back the stop
as well. Before-side state remains the valid incoming state.

An ordinary evaluation may publish a failed run descriptor with its certified
incoming prefix and failed-boundary diagnostic. That is different from source
acceptance and from request-wide cancellation/publication failure. A failed run
can be inspected only within its certified interval; it cannot be extended as a
ready run. Preserve any stronger earlier certified prefix when a smaller-budget
replay fails sooner. Reset deliberately reconstructs a new before-zero run from
accepted source; it does not edit source or erase historical evidence.

Q22 must use **one project** and the actual accepted L04 source. Apply the
inherited atomic source-edit route with expected program revision L04, its
exact entry-source revision and the inspected `reach_b` scene-level action's
writable declaration scope. Use the exact expression's UTF-8 span and expected
text. The resulting bundle must equal exact L02: replace only
`reach_b`'s target/branch expression from `(8,8)` with positive branch to `(1,1)`
with negative branch. The unchanged libraries and every other source byte remain
exact. Only after that actual accepted edit request does the probe combine the
retained L04 run ID with the new L02 revision and require stale-sample rejection.
A second create or a cross-project lookup does not exercise this requirement.

LP01–LP05 retain their **42** fixed semantic steps. The additional L04 recovery
artifact is separately required: after reset and a fresh successful `t=0.25` run,
issue actual GLB/0.6 delivery with inherited `options.end="0.25"`; retrieve and
independently validate its exact bytes, fresh delivery-run identity and unchanged
L04 program revision. Export uses inherited fresh-prefix evaluation; it must not
claim that the earlier run ID became the delivery run. A full request crossing
L04's failure emits no success artifact. This separate artifact does not add an
unrecorded step to the original 42-step fixture inventory.

## 6. Scoped repair remains source-authorized

For P13/P20, inspect the effective property and follow its
`source.initializer_target` to the writable **rig root occurrence** and actual
entry-source span. Editing a generated arm occurrence or a property identity
does not confer authority over the containing root initializer. Execute the
otherwise identical forbidden-scope probes and require atomic rejection.

The accepted length repair reconstructs the actual sites and solves a new goal
for the new immutable source. Four sibling arm subtrees and all unchanged
pinned libraries remain exact. Old runs/artifacts cannot be attributed to the
repair. Limit repairs retain closed canonical limits and the specified branch;
there is no hidden branch fallback or rewritten target to make a failure pass.
Concrete class replacement retains the inherited new-key/rebinding rule.

## 7. Diagnostics and transport status

The [diagnostic specialization](schema-drafts/reach-diagnostic.schema.json)
retains every inherited `ontokin.diagnostic/0.2` field and adds a required
`details.reach_code`. `OKL-E-REACH` is the proposed umbrella source code for the
new semantic conditions; it does not create a new category or transport status.

| `reach_code` | Envelope code | Category | Phase | Validation/evaluation result |
| --- | --- | --- | --- | --- |
| `reach_type` | `OKL-E-TYPE` | `invalid` | `type` | `rejected` |
| `reach_frame` | `OKL-E-REACH` | `invalid` | `elaboration` | `rejected` |
| `reach_chain` | `OKL-E-REACH` | `unsupported` | `support` | `rejected` |
| `reach_domain` | `OKL-E-REACH` | `unsupported` | `support` | `rejected` |
| `reach_claim_conflict` | `OKL-E-REACH` | `invalid` | `admission` | `rejected` |
| `reach_unreachable` | `OKL-E-REACH` | `invalid` | `admission` | `rejected` |
| `reach_singular` | `OKL-E-REACH` | `invalid` | `admission` | `rejected` |
| `reach_limit` | `OKL-E-REACH` | `invalid` | `admission` | `rejected` |
| `reach_numeric` | `OKL-E-NUMERIC` | `numerical_failure` | `admission` or `evaluation` | `failed` |
| `reach_resource` | `OKL-E-RESOURCE` | `resource_limit` | `support` | `failed` |

Use the actual source unit/revision, relevant primary/related spans, rule IDs,
precise failed condition and resolvable chain/action/target/frame/branch context.
The unavailable portion of a malformed expression cannot be fabricated as a
resolved chain. Admission diagnostics include the actual exact failed boundary
and side. When no source span exists, retain the inherited explicit
`location_status="program_condition_without_source_span"` distinction.

Earlier malformed syntax, missing references, unit errors and inherited mode or
lifecycle failures retain their own diagnostic codes and precedence. An unknown
reach subcode, made-up category, `failed` current projection or generic
unsupported result for a geometric rejection is not an acceptable substitute.
Resource exhaustion and cancellation do not prove a geometric outcome.

Final successful-envelope publication failure uses inherited protocol
`OKA-E-RESOURCE`, including `effects_committed=false`; it is not converted into
a fabricated source reach failure. Request statuses retain queued, running,
succeeded, rejected, failed, cancelled and unknown_outcome. They describe the
operation, not the goal outcome of any named action.

An inspection of an invalid candidate can itself succeed at returning source
and diagnostics under the inherited inspection contract. The classification
table does not turn that successful diagnostic inspection into an accepted
candidate or require every envelope carrying an error diagnostic to be rejected.

## 8. Recorded histories and incoming releases

The [GLB metadata schema](schema-drafts/glb-metadata.schema.json) applies at
`document.extras.ontokin`. Every retained source boundary includes its exact
`source_seconds`, complete before **and** after joint/action/pose-authority/
impulse/force/reach maps, and `incoming_releases` even when empty. Both sides
have their actual observation side and `recorded_prefix` context. A successful
prefix artifact contains no fabricated after-side for a failed boundary.

Each incoming release records program revision, complete source location,
sequence index, exact clock, grip and released-target occurrence references,
`reach_contributors`, incoming world pose, incoming world linear velocity and
incoming world angular velocity. Each contributor names its actual action,
shoulder and elbow occurrences and the two saved incoming coordinates and
rates. An empty contributor list is valid only when no reach contributes to
that actual release; it cannot conceal a contributor in P16.

At natural completion, retain the nonzero incoming rates and full root/base
transport even though after-side claims/rates are released/zero. Include root
translation, root angular velocity crossed with displacement, both joint rates
and every real local lever arm once. The independently released sphere's later
force/coast state must agree. Contributor IDs and source spans are checked
against the exact source and before-side state, not trusted metadata labels.

These schemas constrain new fields while the inherited independent validators
still check complete expected object sets, geometry/PBR, surface placement,
authority, impulse/force histories, source closure and active scenes. The schema
leaves inherited extension fields open only where their existing separate
schemas/validators already define them; this is not an exemption from validation.

## 9. Exact clocks and quantization evidence

The [quantization schema](schema-drafts/quantization.schema.json) binds
`clock_conversion="binary32_rne_ties_to_even_from_exact_rational"`. Convert an
exact rational source clock directly to binary32 using nearest/ties-to-even;
an intermediate binary64 conversion is not allowed to choose a different key.
Each retained key stores its exact `authored_seconds` numerator/denominator,
`stored_seconds`, `stored_binary32_bits` and semantic-boundary flag. The bit
field is a new explicit addition in this reconstruction. It must agree with
actual decoded accessor bytes and the independently recomputed conversion.
A label alone never certifies correct rounding.

The exact rational clock can differ from every binary64 scalar, including the
Q16 completion `3 + 2^-53`. Source boundary strings preserve the exact value.
Reduced rational form, monotonic keys, distinct noncollapsing semantic clocks,
and time error at most the requested tolerance (never above `1e-6 s`) require
independent checks. The actual Q16 variant records its nonbinary source clocks,
canonical source literals and positive overlap with the preceding moving phase;
deleting that required phase must fail when tested on an otherwise valid artifact.

Each interval certificate retains exact authored/stored gaps, all source phases
touched by their enclosure, actual carrier identity, landmark radius, speed,
carrier and enclosing-carrier acceleration bounds, endpoint errors, numerical
and local-vertex errors, the ideal and `carrier_position_bound_m` terms,
quaternion arc/difference bounds, and total position/rotation bounds. Neither a
midpoint-only phase choice nor a zero-rate paused phase can erase a positive
moving-phase overlap. Independently recompute every term from actual source,
stored accessors and the specified reader interpolation.

Derivative bounds use exact rational `(canonical_target-canonical_start)/duration`
slopes and outward enclosures. The separately exposed binary64 inspection rates
may round downward and therefore cannot be used as exact upper bounds for `W`,
acceleration or derivative-based proof terms.

Source and destination numerical-bound bases each identify the actual algorithm
name/version, implementation hash, method and derivation hash. A favorable set
of samples, an unproved library accuracy assumption or unused tolerance cannot
establish a uniform error bound. Unknown terms require rejection. See the
separately reviewed quantization derivation for the complete inequalities.

## 10. Complete budgets and the fixed Q03 publication probe

Keep the distinct counting regimes in [budget-counting.md](budget-counting.md):
semantic work and cumulative materialized source values; recursively counted
Agent JSON; weighted retained samples/boundaries; and whole GLB JSON/binary.
Repeated immutable references count at every output occurrence. No storage
sharing or pure-solver cache removes identity checks, output occurrences,
coordinate claims, copied values or cancellation checkpoints.

The global Agent limits remain **4 MiB**, **100,000 recursive JSON entries** and
depth **128**, with complete finite values and Unicode scalar strings. Existing
`budgets.max_value_entries` may lower the entry bound. There is no new
`max_response_bytes` or inspect `max_bytes`. Artifact `max_bytes` retains its
separate inherited chunk meaning. Bound intermediate and cumulative work under
their actual inherited units; then measure the final successful envelope again
inside the publication transaction after identities, cursor, implementation and
progress metadata are present. Failure cannot commit a partial head, run or
artifact. A bounded failure receipt is exempt only from a caller's tiny success
entry budget, and still obeys every global envelope limit.

Q03/LP04 is fixed to original **P24**, an actual sampled run at
`time_seconds="1.5"`, `side="after"`, `selector.kind="action"`,
`fields=["actions"]`, `limit=128`. It returns all 128 named action items with
each complete action group, `truncated=false` and `next_cursor=null`. Pending
actions can observe the running action's nonzero physical rate while their own
rates and admission fields retain pending meaning.

Execute first under default limits and measure the **entire published envelope**
with the inherited exact counter; call that entry count `N`. Record actual
constructor cumulative counts, all other applicable intermediate peak/cumulative
counts and their units. Under otherwise identical source/run/query conditions
and fresh request IDs, `max_value_entries=N` must publish successfully. `N-1`
must reach and fail the final complete-response guard, with no partial committed
effects and a bounded failure receipt. A failure earlier in constructor or
intermediate accounting does not satisfy this probe. Preserve those accounting
rules while implementing a feasible complete projection. Do not adaptively shrink
the query, skip action fields, paginate within a group or exempt construction
work to manufacture a pass.

Synthetic schema/envelope measurements in this proposal establish only shape
feasibility under the default bound. They cannot establish the actual `N`,
constructor feasibility, final transaction guard, cursor integrity or service
effects. Those remain actual-protocol acceptance obligations.

## 11. Cancellation, acceptance and remaining execution gates

Check cancellation through construction, exact numerical admission, claim
preflight, histories, projection, recording planning, geometry, supplied-byte
decoding, serialization and immediately before commit. Q01/Q02 must observe
actual accepted work, request cancellation and reconcile terminal status. A
sleep-only race or cancellation of an operation that never began does not prove
the designated gate. Preserve prior artifacts and immutable source with their
original identities.

Before Agent/0.6 acceptance, execute actual discovery, whole bench and character
creation, goal authoring, complete source/joint/site/action inspection, diagnosis,
root-authority repair, unchanged siblings/libraries, before/after lifecycle
samples, historical/candidate distinctions, Q22, all 42 supplementary steps,
L04's extra prefix artifact, retries/collisions, unknown-outcome reconciliation,
store isolation, cursor substitutions, budgets and accepted-work cancellation.
Validate actual responses against these schemas as well as the independent
source/run/byte relationships. Complete the inherited Agent and source roles.

The release requires 28 source GLBs, nine ordinary Agent artifacts and the
separate tenth L04 recovery artifact. The 54 specified reach browser captures
cover the nine ordinary source and nine ordinary Agent selections; the extra
L04 artifact has independent native validation and does not silently change
that capture inventory. Actual source evaluation, Agent/SQLite workflows,
artifact decoding, browser review and compatibility/release audits remain
pending until implemented and executed in their coordinated windows. Schema
checks alone close none of those gates and do not complete the full GOAL.
