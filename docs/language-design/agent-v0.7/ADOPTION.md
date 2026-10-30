# Configurable execution budgets in the Agent lifecycle

**Identity:** `OK-AGENT-007/0.1.0`

**Decision date:** October 30, 2026

**State:** Selected experimental development contract for C074. Executed results and integration are recorded separately; this decision alone establishes no runtime or release pass.

## 1. Scope and explicit selection

This decision extends the [C073 source-budget contract](../execution-budgets-v0.1/ADOPTION-C073.md) to the durable local Agent workflow. The explicit binding is `ontokin.agent/0.7`, entry language `0.7`, profile `planar-reach-budget-0.1`, and recorded destination `ontokin.glb/0.7`. It serves the [OntoKin goal](../../../GOAL.md): editable source for increasingly capable 3D objects, animation and simulation.

The public Python entry is `ontokin.budget_agent.BudgetAgentService`. A trusted host supplies `HostPolicy` through its constructor; source text and JSON requests cannot supply that authority. The CLI selects this service only with `agent --protocol ontokin.agent/0.7`. Existing Agent defaults, registries, stores, source/CLI discovery fields and schemas retain their previous meanings. Budget Agent discovery has its own binding and reports experimental availability.

The service uses a separate versioned database. It retains the established request digest, immutable source snapshots, accepted-revision checks, run version fencing, cancellation and artifact transactions. No earlier store is migrated or interpreted as a budget Agent store.

## 2. Source request, host authority and caller caps

The entry source's exact bytes determine both its revision and its execution request. Omitted execution fields independently retain **100,000 operations and 30,000 ms**. A larger host ceiling does not increase those defaults.

For a new worker admission, the service snapshots the current immutable host policy and creates one fresh provisional ledger. The provisional limits are the minimum of the defaults, current host ceilings and explicit caller reductions. Header admission promotes that same ledger after checking the candidate source. Promotion retains all consumed work and the original monotonic start. A queued request therefore uses the policy current when its worker starts; it does not reserve the policy present when it entered the queue.

`budgets.max_operations` and `budgets.max_elapsed_ms` are optional caller caps. Each must be a positive integer no greater than `2^53 - 1`. They may reduce the source request. A cap larger than the source request is rejected even if the host could authorize it. The resulting request must fit the host's ceilings. There is no silent clamping, automatic larger-budget retry, unlimited value or authorization inferred from a previous result.

Other request budgets retain their fixed maxima: 1,000 objects, 1,000 result items and 100,000 logical value entries. The existing source, JSON, mesh, numerical operand, cache, reference-cursor, sample, certificate, artifact and chunk limits remain in force. Computation time is separate from scene duration, evaluation endpoints and playback sampling.

## 3. One allowance for one request

Source header admission, linking, construction, evaluation, inspection, recording, export, in-request supplied-byte verification and complete success-envelope checks consume one request ledger. Helpers and internal stages cannot create a second execution allowance. Recompiling or replaying a source within the request consumes its remaining work.

Each request owns its mutable counter, clock, cancellation state and temporary compiler. Concurrent requests cannot share these objects. A host policy change applies to later worker admissions; it does not mutate an already admitted request's ceiling. Explicit cancellation can stop active work at its next cooperative checkpoint.

Aggregate service scheduling, process memory, store retention and any required hard process deadline are separate host responsibilities. The local service independently defaults to four running requests and 256 pending requests, counting queued and running requests in its shared database. The trusted host can configure these finite limits; a source declaration cannot change them. Existing receipt retries and status/cancel requests remain available when the pending-work limit is full. A program declaration grants no concurrency, persistence or memory quota. Cooperative elapsed-time checks cannot preempt an arbitrary blocking host callback. The service reports its supported aggregate constraints without presenting a source budget as a service-wide reservation.

## 4. Atomic creation and edits

Create first retains the immutable candidate source, then admits and checks it at the requested output level. It accepts the candidate only after all required work and publication checks succeed. A failed candidate does not advance the accepted revision or publish an artifact.

C074's new binding accepts source patches only under the complete-file writable identity `['sources', source_id]`. A patch may replace a small byte span within that file; it need not replace the entire file. This is an explicit initial scope limitation of Agent/0.7. Earlier interfaces retain their finer occurrence and definition scopes. Clients discover source-unit identities before editing and supply the source revision, UTF-8 byte offsets, exact expected text and replacement text. Unknown source IDs, stale hashes, split UTF-8 characters, overlapping spans and inconsistent module changes fail atomically.

Patch preparation uses the provisional ledger and exact source bytes. It does not execute the old program merely to discover the candidate's budget. The candidate's own header then determines its request. A host that no longer authorizes the old allowance can therefore accept a valid edit that reduces that allowance.

Successful acceptance retains a complete source-derived map from object occurrence identity to nominal definition identity. The map is bound to the immutable program revision and implementation. A later successful edit compares the candidate's complete map with that retained map; an existing occurrence cannot silently acquire a different nominal definition. This descriptor supports identity comparison only. It grants no execution budget, cannot replace current-source admission and is not reused as evaluated state. Publication of the accepted source and its comparison descriptor is atomic. Missing or incompatible comparison evidence requires explicit reconstruction under current authority, not an unchecked acceptance.

On rejection, exhaustion, cancellation, output-limit failure or competing acceptance, the earlier accepted revision remains authoritative. Existing artifacts and run descriptors remain available by their original identities. A returned candidate or prefix must be identified as such and cannot be reported as accepted or delivered.

## 5. Operation contract

The strict operation shapes are in [request.schema.json](request.schema.json). All requests identify their schema, project, request ID and operation; unknown fields are rejected.

| Operation | Required work and authority |
| --- | --- |
| `discover` | Report this binding, current policy, defaults, finite caps, available operations and source-edit scope. A supplied bundle or saved program is admitted under the request's ledger. Source-free discovery has bounded provisional work and grants no source execution authority. |
| `create` | Admit the exact candidate bundle and satisfy its requested level before accepting it. |
| `edit` | Check exact source patches and module changes, admit the resulting candidate, check identity continuity and requested output, then publish atomically. |
| `validate` | Reauthorize the exact saved program under current policy and satisfy the explicit requested level. |
| `inspect` | Reauthorize the saved program and preserve revision, run, time, frame, cursor and result bounds. Saved run metadata is evidence, not authority. |
| `evaluate` | Reauthorize the accepted program; create or advance only the named compatible run. Internal replay does not replenish the ledger. |
| `reset` | Reauthorize the accepted program and construct a new initial run with a fresh request ledger. |
| `export` | Reauthorize the accepted program, evaluate the requested prefix, record and validate exact GLB/0.7 bytes. Never replace requested delivery with represented success. |
| `artifact` | Resolve the artifact's retained program, admit that exact source under current host policy, and return a bounded chunk. A historical producer receipt cannot authorize retrieval. Optional `budgets` supply current caller reductions. |
| `surface.mesh_page` | Reauthorize the program and produce a bounded, revision-bound geometry page with the same ledger. |
| `status` | Return durable request state, including its historical execution receipt. Do not execute or reauthorize the target. |
| `cancel` | Request cancellation through the existing ownership and transaction fences. Do not publish tentative source, run advancement or artifact bytes. |

A new saved-program, saved-run or artifact request receives a new ledger and current-policy admission. A lower host ceiling rejects an older larger request unless an explicit caller cap or source repair fits. Returning a stored request receipt through status or an identical retry is distinct from a new computation or artifact retrieval.

## 6. Retries, cancellation and publication

The same project/request ID and canonical payload return the original durable receipt. They never enqueue another execution or grant a new allowance, including after a policy change. Changing source, budgets, options or any other payload field under the same ID fails with a request-identity conflict. A deliberate new request ID undergoes current-policy admission. Expired results retain tombstones and cannot be silently replayed.

Cancellation is checked before charged work and before publication. Runtime adapters preserve the original caller exception and ordering; the durable service converts its own cancellation signal to the established cancelled response. No partial artifact is committed. A race with another source acceptance or run advancement is resolved in the same durable transaction as the result.

Complete success-envelope traversal remains charged through the final transaction check. If that check fails, all tentative acceptance, run and artifact writes roll back. The service can then retain a bounded failure receipt without more product work. A small requested result allowance cannot suppress this failure transport. Failure transport does not authorize construction, evaluation, export or a hidden retry.

## 7. Inspectable receipts

[response.schema.json](response.schema.json) adds `execution_budget` to the versioned envelope. Before worker admission, and for source-free protocol/control responses, it may be null. A terminal worker receipt identifies defaults, current policy identity and ceilings, source request, caller caps, effective limits, cumulative operations, elapsed time, original monotonic start/deadline, stage, outcome and implementation. Unresolved fields remain null when admission fails.

Monotonic timestamps are process-local timing evidence; they are not civil timestamps and cannot be compared across service processes. The deadline derives from the original start and admitted effective time allowance. A receipt is descriptive and cannot grant authority to another request or reader. Artifact producer evidence and retrieval-request evidence keep separate identities.

An export report records `execution_budget_at_export` with status `export_verified_pending_publication`. This is a historical snapshot taken after supplied-byte verification and before the complete Agent envelope and its transaction are checked. It is not the final consumed-work total. The top-level `execution_budget` receipt in the terminal Agent response contains the final count and outcome. `producer_request_id` links the retained artifact to that durable producer response. A later artifact request carries its own top-level receipt and verifies the retained bytes by their exact hash; the producer's numerical validation remains separately identified historical evidence.

The source/program revision, requested and achieved levels, run identity, artifact identity, diagnostics and explicit valid prefix remain available through the ordinary envelope and result. Prefix evidence covers only state already established as valid. Earlier source, numerical and output diagnostics retain their meanings; resource failures report the C073 budget reason where applicable.

## 8. Evidence and remaining obligations

The five deferred cases in the unchanged [29-case plan](../execution-budgets-v0.1/conformance-plan.json) are C074's required lifecycle checks:

| Case | Required evidence |
| --- | --- |
| EB15 | Candidate budget edits change exact revision; successful repair and failed-candidate rollback preserve accepted state. |
| EB16 | Saved programs, runs and artifacts receive current-policy authorization; historical receipts grant no allowance. |
| EB18 | Concurrent request counters and policy snapshots remain isolated; queued-policy changes and active cancellation execute. |
| EB24 | Identical retries, changed-payload rejection, new-request admission and cumulative internal accounting execute. |
| EB29 | Actual discovery, create/edit, inspect, evaluate, export/retrieve, status, cancel, hostile input and retry paths execute. |

Development integration additionally requires the full applicable inherited regression cohort, unchanged local-driver roles, protocol transcripts, source-to-delivery checks, independent destination checks, actual visual review and resulting-main verification. A reused C073 workload retains its exact source and expected hashes, with separately identified Agent evidence.

Original28 remains 24/28 failed, with P11/P16/P23/L03 unresolved at their original settings. Higher-budget Agent evidence cannot pass those fixed-budget gates retroactively. Complete reach release, missing external and compatibility roles, C035, C057, historical LFS migration and the remainder of GOAL remain open. Recorded GLB playback establishes no live destination physics or untested engine support.
