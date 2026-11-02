# Finite torque: Agent, source, state and durable delivery

**Identity:** `OK-AGENT-022/0.1.0`  
**State:** review draft; subject to the separate exact C090 adoption  
**Basis:** unchanged Agent/0.21 on C088, as captured in C089

## 1. Binding and unchanged operations

Explicit `ontokin.agent/0.22` selects source `0.22` / `torque-0.1` and `ontokin.glb/0.22`. Its separate database is `torque-program-agent.sqlite3`, with store identity `ontokin.torque-program-agent-store/0.1`. A new TorqueAgentService and explicit CLI protocol selection must choose this binding without changing ProgramAgentService/0.2 or CLI Agent/0.1 defaults. Older services never open the torque database as an earlier schema. Existing databases, implementation identity and reopen rules retain their original meanings.

The twelve operations are unchanged: discover, create, edit, validate, inspect, evaluate, reset, status, cancel, export, artifact and surface.mesh_page. [Agent/0.22 request/response schemas](../agent-v0.22/README.md) retain the complete .21 operation shapes, exact source/asset bundle transport, output-level semantics and inherited error envelope. No apply-torque RPC, state patch, force mutation or auxiliary hidden model exists. All changes originate from accepted `.ok` source and immutable assets.

The source unit, accepted program revision and complete dependency/asset closure identify every observation. Native JSON schema validation is necessary but insufficient: independent readers must also recompute source identities, pins, exact clocks, canonical aggregates, stable record membership, run side/prefix, host authority and artifact byte identities. Passing a shape check cannot certify a physical state or source-authorized edit.

## 2. Discovery and source projections

The complete discovery catalog adds a bounded `torque_interface` matching [catalog.schema.json](catalog.schema.json). It states the exact statement grammar, three positive axes, explicit binding, phase limit, supported body/marker scope, every structural work stage and unsupported domains. The inherited keyed, String, texture, force, reach and resource interfaces remain present with unchanged semantics. Where a capability is inherited by .22, discovery explicitly adds that declaring-unit/profile membership; it must not advertise a .21-only membership builtin as unavailable in .22. Linked discovery identifies declarations and supplied closure, never claims evaluated output.

Catalog revision hashing retains the inherited canonical JSON procedure and includes the actual torque interface and current policy fields. Cursor context includes project, operation, filter, profile, complete program revision, catalog revision and implementation. A source, policy, filter or implementation change invalidates its inherited context instead of resuming at a coincident numeric offset. Pure discovery still checks the current original request budget and deadline; it does not acquire authority from a saved catalog.

When occurrence inspection requests `source`, add `torque_intervals`: every complete interval record authored for that occurrence, ordered by exact activation then source sequence index. Resolved occurrences with no intervals expose an empty array. Definitions, imports or unresolved sources cannot acquire occurrence histories; retain their inherited unavailable/source-only projections. Partial requested fields do not fabricate unrequested state. Scalar operand origin and duration origin remain actual UTF-8 source spans, including retained construction/provenance relationships when an expression comes from a component parameter. The original span remains repair authority; a derived value or detached contributor is never itself writable source.

Each record is the closed `record` in [torques.schema.json](torques.schema.json). It contains exactly:

- `torque_key`, four-part `torque_element_id=[module_id,scene_id,"torque",key]`, `target_path`, `target_element_id` and `program_revision`.
- `source_location`, `operand_location` and `duration_location`, each with exact source ID/revision and half-open UTF-8 start/end byte offsets.
- `sequence_index`, `axis`, signed canonical `torque_n_m`, and exact decimal `activation_time_seconds`, `duration_seconds`, `completion_time_seconds`.

Every pin and location must match the actual accepted closure. End equals exact start plus exact positive duration, regardless of binary64 end representability. Source identity does not change merely because an interval moves from active to completed. A successful change record adds exactly `kind="started"` or `kind="completed"`; no additional unbounded annotation or user-supplied field is accepted.

## 3. Complete closed torque state

Every available object state under .22 contains a `torques` object. This includes initial state, last valid run state, available object inspection and after-side recorded boundary state. Its new fields are closed; unsupported extra fields, missing fields or a sparse projection masquerading as a complete state are refused by the independent reader. Existing non-torque fields retain their original definitions.

| Field | Meaning |
| --- | --- |
| `active` | Complete active interval records, ascending stable torque key |
| `net_torque_n_m` | Canonical signed exact-sum-then-round result; zero when no active torque |
| `angular_acceleration_rad_per_s2` | Canonical acceleration for a latched free carrier; otherwise null |
| `axis` | Sticky world_x/world_y/world_z, or null before first committed activation |
| `rotation_route` | `legacy` until first committed nonzero final canonical alpha; `split` thereafter |
| `rotation_anchor_seconds` | Actual canonical split rotation anchor time; null for legacy |
| `signed_angular_speed_rad_per_s` | Selected canonical world component when latched, otherwise null |
| `phase_since_anchor_rad` | Canonical phase at this observation's exact clock relative to split anchor; otherwise null |
| `angular_acceleration_reference_rad_per_s2` | Exact pre-rounding reference acceleration as a reduced rational, or null before latch |
| `angular_error_bound_rad` | Conservative complete angular discrepancy at this observation as a nonnegative rational, or null before latch |
| `angular_speed_error_bound_rad_per_s` | Conservative complete angular-speed discrepancy as a nonnegative rational, or null before latch |
| `started_count`, `completed_count` | Complete successful counts for this accepted run, including zero/cancelling intervals |
| `last_change_time_seconds` | Most recent committed torque-changing boundary, or null initially |
| `last_changes` | Every completion in key order followed by every activation in actual source order at that boundary |

Rationals are closed `{numerator,denominator}` objects containing canonical base-ten integer strings, positive denominator, gcd 1, no negative zero and at most 32,768 bits per actual integer. String-length guards precede parse; the schema's conservative decimal-length bounds do not replace the exact bit guards. Scalars are native finite JSON numbers, not Bool, infinity, NaN or custom numeric wrappers. Shared JSON and work accounting apply before allocation and after complete serialization. No partial success truncates active/recent histories to fit a limit.

Before a first activation, active/history are empty, both counts and net are zero, axis is null, route is legacy and all angular scalar/error fields above are null. After a zero activation, axis is latched and counts/history are real even though canonical alpha is zero. Underflow can give canonical alpha zero with nonzero reference acceleration and angular error; that separate error history cannot be discarded. A completion can switch from legacy to split when cancellation ends. Reset returns the inherited before-zero initial state and clears locks/history; prior accepted run/artifact identities remain immutable.

An unrelated boundary leaves `last_change_time_seconds` and `last_changes` untouched. A torque-changing boundary replaces the recent list only after complete commit. When a callback, late sequence event, final sum, record budget or commit check fails, all torque and inherited state fields remain at the previously accepted prefix. Presenting tentative axis/count/anchor values as accepted is an independent-reader failure. World scalar axis/history fields do not rotate in a self-frame query. Existing transformed position/velocity fields retain their established frame semantics.

## 4. Source edits and immutable provenance

Use the inherited expected program revision, per-source revision and exact UTF-8 byte-patch preconditions. The literal frozen repairs change one occurrence's torque magnitude, duration, mass or radius while preserving unrelated entry bytes, sibling configuration, pinned library and PNG. Invalid source, stale revisions, wrong source scope, mismatched old text, overlap, split UTF-8 code points, wrong digest and invalid image changes leave the accepted revision and every old run/artifact unchanged. A module edit requires its exact dependency-pin changes in the same candidate. An entry edit cannot silently rewrite a pinned module or asset.

Creation and edit may retain a never-accepted diagnostic source snapshot under the inherited rules. That snapshot has no accepted revision, valid run, executed torque history or artifact. Source inspection must label its actual acceptance state. Candidate and accepted program revisions must never be conflated. Failed editing and later repair are distinct request identities with the exact actual response and source bytes retained.

A new accepted revision initializes new run state. It does not alter an existing run's interval clocks, material/geometry streams or torque history. A successful duration patch changes completion only for newly evaluated source. A sibling's physical/visual invariants are checked against the independently frozen common clocks and actual source/library/image bytes; a schema label alone is insufficient.

## 5. Current authorization and request lifecycle

Every new effectful execution, evaluation, materialization, export, artifact retrieval requiring bounded work, and resumed request checks the current host policy and caller reductions through the inherited admitted execution context. Saved source budget requests, prior success, cached geometry, reopened state and an existing artifact are not grants. Effective operations/elapsed time derive from the authoritative entry request and current host ceilings; caller budgets can only lower them. Imported modules cannot raise entry authority. Ordinary defaults remain 100,000 operations and 30,000 ms, independent of modeled animation duration.

Reuse the original admitted shared ledger, start/deadline, cooperative callback and staged publication context. Cancellation polls occur during torque compilation, active enumeration, exact summation, interval planning, numeric operations, history/JSON serialization, independent byte validation and final commit. A callback exception preserves object identity through private helpers and retains the inherited public mapping. New torque code cannot replace callbacks, catch a foreign exception as a harmless numeric refusal or acquire a fresh elapsed allowance for the independent reader.

The same request ID and canonical payload returns/reconciles its recorded historical outcome without replaying effects. A changed payload with that ID receives the inherited request-identity refusal. A terminal historical retry is identified as the old outcome; it is not evidence of a fresh current-policy execution. A new ID is a new request and needs current policy. Status/cancel/reopen retain the original lifecycle, tombstones and unknown-outcome rules. `status` must identify the actual target operation and committed revision/run/artifact if known. An interrupted response is not proof of failure; reconcile actual durable state before retrying. Reset and revision replacement never erase old immutable requests or artifacts.

Agent store verification independently opens the actual database read-only, verifies protocol/store identity, complete request-to-response-to-source/run/artifact relationships and transaction atomicity, and compares stored byte lengths and digests. Producer JSON is not store evidence. Required failures include reopen during active or unknown work, cancellation before/after acceptance, response-limit failure after an artifact was staged, artifact write/publication interruption, and same-ID reconciliation. Database recovery must not require editing a history row to label an incomplete transaction successful.

## 6. Exact artifact publication and retrieval

Export selects recorded `ontokin.glb/0.22` explicitly. Its complete source closure, immutable asset pins, implementation/numerical/destination basis, options, exact timeline and after-side torque state must pass the source, recorder and independent supplied-byte checks before publication. A failed independent reader, cancellation, work/byte cap, stale authority or failed final response check publishes no successful artifact/result. Preserve any retained partial bytes as failed diagnostic evidence with their actual identities; they cannot be retrieved as accepted output by inventing a normal artifact row.

Successful artifact retrieval uses the existing immutable artifact ID and exact stored bytes. Offsets are native nonnegative integers; `max_bytes` is 1 through 65,536 and defaults to 65,536. A slice is the exact half-open byte interval from offset to the smaller of offset+max_bytes and total length. `next_offset` is offset+slice length while bytes remain, otherwise null. At offset equal to total length, return an empty base64 string, null next offset and nontruncated success. Offset greater than length receives `OKA-E-ARTIFACT` with the inherited exact message. Unknown ID/project and tampered digest/length retain their original errors.

Every chunk repeats the actual artifact identity, total length, media type and inherited digest/closure fields. Reassemble all slices without decoding/re-encoding GLB JSON, normalizing padding or deduplicating equal streams. Verify the complete SHA-256, length, framing and native bytes. Changing a request chunk size does not create another artifact; retrying a historical request must obey its exact identity rules. Smaller current caller caps can refuse fresh retrieval without destroying the stored artifact. Revision-bound surface/asset pages retain their existing independent 256-triangle/asset-slice limits and stale-cursor behavior.

The new controlled torque destination is a separately implemented future `.22` adapter, with the exact contract in [RECORDING.md](RECORDING.md). Preserve the old .6-only player. Fresh Khronos/native checks, actual controlled Three.js playback and individual captures must refer to the same accepted artifact bytes. Default animation-mixer playback alone cannot establish the new controlled interpolation guarantee. Unreal import, live physics and broader destination support remain unverified.

## 7. Frozen workflow obligations and limits

The independent packet provides concrete request sequences and source/repair identities for discovery, create/inspect, invalid/stale edits, successful scoped repairs, repeated/resumed evaluation, full before/after boundaries, reduced host/caller limits, every cancellation stage, reset, reopen/retry, interrupted publication and chunk/EOF retrieval. Requests and responses must validate against these schemas and independently reconcile actual source, state, SQLite and native artifacts. Hostile mutations require an unchanged accepted original control and exact expected refusal; merely changing schema-valid text is not an executed adversarial result.

All retained predecessor fixtures, failed attempts, original28 failures, missing attestations/interpreter coverage and full GOAL domains remain visible. C090's schema/model examples are proposed validation inputs, not observed service responses. Contract adoption, input publication, runtime implementation, development integration, complete feature release and full-product acceptance remain separate states.
