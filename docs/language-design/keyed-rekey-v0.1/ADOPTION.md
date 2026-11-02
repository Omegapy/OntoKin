# C086 bounded pure keyed renaming

**Decision identity:** `OK-DEC-KEYED-REKEY/0.1.0`  
**State:** Selected experimental contract after independent review and unchanged-C085 control preflight. Exact publication of this packet establishes adoption; runtime work remains gated on successful publication and readback.  
**Baseline:** C085 `f4c90c04b9b381de73d46715d52e68f588e49e4f`, tree `7c716b717d92027eecfa911a8ec8df16d851ae47`  
**Date:** November 1, 2026

This decision addresses C085's `NEXT-TASK.md`. The independent design, input reviews and unchanged-.18 control preflight are bound in [ADOPTION-DECISION.json](ADOPTION-DECISION.json). Runtime implementation must wait until this exact decision and [input freeze](INPUT-FREEZE.json) are published and read back. Preparation, adoption, implementation, actual validation, integration and full release acceptance remain separate facts.

## 1. Utility and selected scope

An agent can place a reusable collection's components into an explicit namespace before combining them with independently authored components. Existing map, filter, reduce, disjoint merge and exact-key zip operations do not change the surviving keys. This operation fills that specific gap while preserving each payload exactly. Its usefulness is expressible composition; no measured reduction in authoring time is claimed.

The selected expression is `rekey_keyed<T>(input, (old_key, value) -> new_key)`. It computes one new stable key for each entry of one finite immutable collection. The payload is unchanged. The operation adds no container kind, mutable reference, implicit suffix, overwrite policy, join mode, conflict resolver, runtime spawn or physical/motion authority. Existing String equality, conditional literals and `Keyed<String>` lookups can select explicit namespace keys. The predecessor has no String concatenation operator; this increment adds none. Generic prefix synthesis is outside this scope. The utility claim therefore concerns finite explicitly authored renaming, including namespaced component libraries with a supplied key map.

The selected explicit bindings are source `ontokin "0.19";`, profile `keyed-rekey-0.1`, `ontokin.agent/0.19` and recorded `ontokin.glb/0.19`. Immutable files/bundles remain `ontokin.files/0.2` / `ontokin.bundle/0.2`. The profile inherits .18 zip and all earlier adopted geometry, appearance, execution-budget and physical semantics. CLI Agent/0.1, Python ProgramAgentService/0.2 and GLB/0.1 remain ordinary defaults. Geometry and motion binary encoding remain unchanged.

## 2. Exact types, static scope and declaring versions

There is exactly one explicit type argument, one input expression and a two-binder body. The input and output types must be exactly resolved `Keyed<T>`. The callback result is exactly `String`. The binders have types `String` and `T`, are read-only, and exist only inside the body. The operation does not convert values, widen Int to Real or infer an element type from nonempty input. Equivalent inherited quantity aliases remain equivalent; units, frames and imported nominal identities keep their original rules.

`T` admits exactly the predecessor's 24 immutable leaf families: Int, Real, Bool, String, Quantity and existing aliases, valid Vec3/Vector3/Range instantiations, FrameRef, Point3, Rotation, Pose, Color, LoftSection, SurfaceMaterial, PlanarPoint, PolygonVertex, PolygonRing, PolygonSection, FramedPolygonSection, PolygonPocket, TextureImage, PlanarUV and TextureBinding. Every inherited constructor/leaf bound remains in force. Geometry, BodyModel, Action, references, generated-reference views, mutable values and nested Keyed types remain unsupported, even when the input is empty. A bounded nominal PolygonRing does not admit arbitrary nested collections.

Both binders must be distinct and cannot shadow any enclosing local, predefined name, module definition, import alias, visible class/member/scene name or `self`. The input is outside the new binder scope. Nested operation binders obey the same rules. Existing lexical self, access checks and declaring-module resolution remain authoritative.

`rekey_keyed` is a contextual expression form and reserved predefined spelling in .19 declaring units only. It is not a first-class function, method or general lambda. Older units may retain an ordinary function of that name. A qualified call to such a pinned older definition remains an ordinary call. A .19 unit may import compatible .2 through .19 units under existing exact pins. Older units cannot import .19 or acquire its semantics from a newer caller.

Global syntax, pure-definition, access, name, type and call-cycle checks remain authoritative, including unused definitions and statically checked unselected branches. Locally, check the explicit type, binder declarations, exact input boundary and body in that order. Check the body with unknown typed binder payloads, including for empty input. Mask enclosing known local values to unknown while retaining type and available frame metadata. The expression's own unknown-payload check remains necessary during each dynamic evaluation; a global abstract declaration pass does not replace it. Do not use an arbitrary sample key or execute value-dependent domain work as static checking.

These static checks precede dynamic input evaluation. A type-correct empty callback that would divide by captured zero executes no division. An invalid name, private access, unit mismatch, constructor signature or pure-call cycle still fails. A statically invalid callback therefore precedes a dynamically invalid input.

## 3. Dynamic order, output domain and refusal precedence

Evaluate the complete input dynamically once. Admit its exact type, immutable leaf values, canonical unique stable keys and at-most-256 entry count before any callback runs. Literal entry evaluation retains its inherited authored order. Canonical callback traversal does not reorder input evaluation. An input-admission error prevents every callback.

Traverse admitted entries in canonical ASCII order of **old keys**, regardless of authored order or eventual output order. For each entry:

1. Use the actual `keyed_rekey_iteration` checkpoint before selecting the entry or constructing its fresh binders.
2. Bind a detached String old key and detached immutable original payload; evaluate the pure callback once.
3. Enforce exact String and an actual known immutable String result. Preserve any callback exception and its original diagnostic identity.
4. Use the actual `keyed_rekey_key_validation` checkpoint. Validate the computed String against `[A-Za-z0-9][A-Za-z0-9._-]{0,63}` in full. Keys contain 1–64 ASCII characters, begin with a letter or digit, and otherwise contain only letters, digits, period, underscore or hyphen. Spelling and case are exact. No Unicode normalization, trimming or escaping changes the key.
5. Use the actual `keyed_rekey_collision` checkpoint immediately before checking whether that new key was produced by an earlier old key. The first collision in original canonical traversal fails immediately. Equal payloads do not permit a duplicate. Do not run later callbacks, and do not copy the colliding payload into an accepted result.
6. Retain a detached copy of the **original** payload with this key's independently specified provenance.

After all callbacks succeed, precharge bounded sorting before allocating the sorted output, sort entries by their **new** canonical ASCII keys, then use the actual `keyed_rekey_publication` checkpoint immediately before final immutable collection and aggregate-provenance materialization. This internal checkpoint is not an Agent commit and grants no publication authority. Complete the immutable result and all provenance before any accepted publication. Output cardinality equals input cardinality and remains at most 256. Empty input has no per-entry checkpoints or callback evaluations, but reaches this one final checkpoint after static/admission work; its input dependencies remain observable.

This deliberately selects streaming collision refusal. An earlier collision wins over a later callback error or invalid output key. A callback error or invalid key at the current entry wins before collision testing at that entry. A valid earlier callback completes before a later callback's error. Static checking still precedes all these dynamic priorities. Actual cancellation or exhaustion can interrupt any stage and does not promise a later semantic error after authority is gone. No implicit all-callbacks-first phase is permitted.

The original collection and all aliases remain unchanged. Identity renaming creates the same key/payload mapping, but still performs its specified callback, work and provenance. It is not an optimization exemption.

## 4. Exact new boundary diagnostics

New input and callback exact-type mismatches use `OKL-E-TYPE`, category `invalid`, phase `type`, rule `LANG-003`. Primary location is the first original lexical token of the offending input/body expression, with no related locations. Details contain exactly `expected` and `actual`, using inherited canonical type spellings. Input expects `Keyed<T>`; body expects `String`. Their messages are exactly `rekey_keyed input requires exactly <expected>, received <actual>.` and `rekey_keyed body requires exactly String, received <actual>.`. Constructor internals keep their inherited unit/frame/domain/type diagnostics.

An invalid computed output key uses `OKL-E-ID`, category `invalid`, phase `elaboration`, rule `LANG-007`. Primary is the first original lexical token of the callback body. Related locations contain the current original input entry's full retained source span, when known, otherwise an empty list. Details are exactly `{"operation":"rekey_keyed","key":<actual String>,"old_key":<original key>}`. The exact message is `rekey_keyed produced invalid stable key <JSON(new_key)> from old key <JSON(old_key)>.`, where JSON(String) is a quoted JSON string using ASCII Unicode escapes. Input-key validation remains inherited and is not relabeled as a computed-key error.

A duplicate computed key uses `OKL-E-ID`, category `invalid`, phase `elaboration`, rule `LANG-007`. Primary is the first original lexical token of the callback body. Related locations contain the first producer's original full entry span and then the colliding producer's original full entry span, omitting only an unavailable span. Do not deduplicate the two contributor roles when their retained spans happen to coincide. Details are exactly `{"operation":"rekey_keyed","key":<duplicate new key>,"first_old_key":<first old key>,"duplicate_old_key":<colliding old key>}`. The exact message is `rekey_keyed output key <JSON(new_key)> duplicates old keys <JSON(first_old_key)> and <JSON(duplicate_old_key)>.`, with the same JSON(String) convention. The first producer is the earliest old key that produced the selected new key. The colliding producer is the first collision encountered in old-key traversal; the error does not select the smallest duplicate **new** key among hypothetical future work.

For grouped input/body expressions, the original opening parenthesis is the primary first token, with its one-byte span. Complete expression provenance is a separate full span. All coordinates are original UTF-8 byte offsets. For an original keyed literal, an input-entry span begins at the opening key quote and ends with the complete value expression, excluding its comma. Unavailable source-entry mappings remain unavailable; the callback body remains a valid primary location. Imported entries keep their original source/revision and filename.

Unsupported leaf families, syntax, access, cycles and input cardinality/resource failures retain their inherited diagnostic families and settings. No partial first-256 result is permitted. Inherited absent-key initializer/reference refusals follow final generated shape resolution.

## 5. Work, cancellation, caches and publication

Use the actual current complete-request ledger for type/expression work, each masked enclosing local, complete input admission, callback binding and execution, key validation, collision lookup, detached payload copies, bounded sorting, all origin merges/copies and final materialization/serialization. Charge bounded allocations and sorting before they occur. Compound immutable payloads retain inherited logical copy costs even when internal bytes can be shared. Identity rekeying, ignored payload binders and cached inputs do not make any of this work free.

The three named per-entry checkpoints run at the exact stages above. An invalid computed key reaches key_validation but not collision; a duplicate reaches both. A callback exception reaches only that entry's iteration checkpoint. The final publication checkpoint runs once after successful complete traversal and bounded sorting, including for empty input. Existing cancellation before other bounded work/copies/serialization remains in force. Checkpoint wrappers must preserve the actual callback exception, not replace it with a generic rekey error.

No rekey-node constant cache, parameter cache or persistent key-renaming cache is introduced. Existing eligible helper caches retain guarded actual-read replay, exact current accounting, taints, current source scope and live-owner safeguards against recycled host object IDs. Reopened stores, retries, repeated references and empty results do not reset the request ledger or grant authority.

Any failure, resource exhaustion, cancellation or interrupted publication publishes no partial accepted collection, source revision, run or artifact. Complete temporary local construction is not accepted publication. Existing Agent transactions, rollback, request identity, unknown-outcome reconciliation and idempotent retry keep their meanings.

Ordinary defaults remain 100,000 operations / 30,000 ms. Higher source requests need independently current host ceilings; reducing caller caps cannot grant authority. Modeled duration remains separate. Preserve the 32,768-bit operand, 256-entry numerical cache, 64-step cursor, 8,388,608-byte request envelope and every inherited parser/type/expression/call/constructor bound. New fixtures cannot change an old fixture, horizon, rate, equation, helper, oracle, budget or tolerance.

## 6. Detached lineage, dependencies and occurrence identity

The new read-only projections are `derived_rekeys` on derived values and `input_rekeys` on generated occurrence provenance. Each record has exactly seven fields:

| Field | Meaning |
| --- | --- |
| `expression` | Full original rekey-expression location. |
| `input` | Full original input-expression location at the call. |
| `body` | Full original callback-body location. |
| `element_type` | Canonical resolved `T` spelling. |
| `old_key` | Original input key for a selected entry, otherwise null. |
| `new_key` | Result key for a selected entry, otherwise null. |
| `input_entry` | Retained original payload entry location when known, otherwise null. |

Non-null locations contain exactly `source_id`, `source_revision`, `filename`, `start_byte` and `end_byte` in the inherited detached shape. Aggregate records set old_key, new_key and input_entry to null while keeping original expression/input/body/type fields. Normalize only this origin family on every Keyed aggregate and deduplicate complete records in actual evaluation order. Do not normalize selected stored leaf records or scalar/indexed public projections.

Aggregate order is normalized input-evaluation records, selected callback records in old-key traversal order, then the current aggregate record. Each stored output leaf retains its matching original input leaf's records, then the actual callback result's records, then the current old-to-new entry record. Public selected/indexed/generated projections concatenate aggregate records before that stored leaf's records and deduplicate by entire detached-record equality, retaining the first. Never infer contribution from a coincident key or relabel unrelated aggregate records as selected contributions.

Preserve every actual dependency and forbidden generated-view taint from complete input admission, including empty input or ignored payload binders. Preserve actual selected callback reads, condition-only reads and earlier iterations whose keys/payloads are later ignored. Unselected dynamic branches add no invented reads; their static checks remain separate. Downstream map/filter/reduce/merge/zip, indexing, generation and guarded cache replay retain these facts. Fresh wrappers prevent mutation, shared-payload contamination and recycled-ID contamination.

Inherited map/reduction/filter/merge/zip records keep their original shapes, original keys and contributor meanings. A prior zip record for old key `a` remains a zip record for `a` after rekey produces `ns.a`; the new record supplies the `a` to `ns.a` step. A second rekey preserves both actual steps. For plain A and inner rekey a→b followed by outer rekey b→c, the outer aggregate list is `[inner/aggregate, outer/aggregate]`; stored c has `[inner/a→b, outer/b→c]`; its public projection is those aggregates followed by both stored steps.

The singular generated `input_entry` remains the retained original **payload** entry, mapped under the new key. It must not be described as a literal declaration of the computed new key. The current rekey body and explicit lineage explain the key computation; neither is a writable occurrence identity. Generated element IDs and paths use the actual new key. Changing a key therefore removes the old occurrence identity and introduces the new identity; identity renaming preserves the occurrence key. Unchanged siblings, unchanged remaining keys, pinned libraries/assets and independent motion keep their original identities and meanings. Repair authority remains current original source/member spans, immutable revisions and exact UTF-8 preconditions.

## 7. Representative Agent workflow and output comparisons

Retain all twelve operations: discover, create, edit, validate, inspect, surface.mesh_page, evaluate, reset, export, artifact, status and cancel. Selected .19 storage is `keyed-rekey-program-agent.sqlite3`, schema `ontokin.keyed-rekey-program-agent-store/0.1`. Discovery must describe exact types, the key domain, old-key callback order, immediate collision refusal, new-key output sorting, 256-entry bound, identity consequences and current host view through detached data.

Use two independent textured occurrences of a reusable pinned component library, a scoped namespace parameter and an unrelated moving marker. Through actual Agent edits, rename only a prescribed subset in the first occurrence. Compare every intended identity removal/addition and every unchanged sibling/remaining member. Preserve reusable source bytes, exact PNG bytes, geometry/material values and independent motion. Reject a duplicate-output-key candidate and prove rollback. Retain old accepted revisions, runs and artifacts, then reverse the edit and prove restoration against explicit .18 controls.

Exercise complete bounded source-unit pages and source/asset/artifact slices, every revision/cursor scope, stale read refusals, actual JSON response exhaustion, current host reductions, all four actual cancellation stages, callback-exception identity, durable reopen/retry, changed-payload refusal and interrupted publication. A schema or configured callback is not execution evidence.

The exact declared PNG closure remains required for reachable .13 through .19 units, including unused definitions, empty inputs and discarded payloads. Only literal builtin png_asset calls declare attachments. Images are admitted once per compilation on the same ledger. Rekey cannot discard a declared asset, fetch it, accept changed bytes or get free repeated admission.

Every complete .19 output must agree with its independently authored explicit .18 literal control in complete BIN bytes and raw JSON/framing, subject only to narrowly enumerated and independently validated metadata differences for version/profile, source/revision/provenance and implementation fingerprint. Freeze all permitted source-ID differences from authored controls before reading candidate output. Geometry, accessor layout/data, material/image/sampler graph, exact PNG bytes, actual expected identities and motion must agree. Arbitrary JSON suppression or selected-coordinate checks are insufficient.

Use supplied-byte corruption adversaries, pinned Khronos/Three.js/Chromium readers and direct review of retained captures. These prove only their named streams, views and recorded poses. They do not establish Unreal import, hidden geometry, live destination physics, general playback or measured authoring benefit.

## 8. Independent inputs, publication and retained gates

The independent freeze must include complete source cases, explicit .18 controls, exact key/value/order/lineage/diagnostic expectations, conservative work bounds, actual Agent workflows, complete delivery allowances and supplied-byte adversaries. Preflight every explicit .18 control on unchanged C085. Derive expectations from this decision, authored bytes and source mathematics; never record the candidate's output as the expected answer. Preserve defective inputs and their failures; any correction is separately reviewed and retains fresh execution lineage.

Cover empty, singleton, identity, reordered output, maximum input cardinality, 257-entry refusal, every key boundary, duplicates, all 24 families, aliases and exact-type failures, malformed syntax, access/cycles, declaring-version behavior, nested compositions, taints, condition-only and ignored reads, alias isolation, unknown-payload checking, guarded cache replay and multiple-error precedence. Bind first-token and full-expression spans independently, including grouped expressions and UTF-8 prefixes. Retain exact original entry mapping and unknown-map fallback cases.

After the exact reviewed adoption and freeze are published and read back, implement only this scope. Required completion evidence includes all frozen checks, complete immediate-predecessor .18 workflows/readers, applicable complete inherited local validation, independent candidate review, expected-head integration under a bounded lease, relevant resulting-main checks and a coherent recoverable ZIP containing the complete unchanged C085 predecessor chain. Hosted workflows remain manual-only/default-false; this decision dispatches no job or continuation schedule.

Complete experimental feature release and full-product acceptance remain false. Preserve every C085 RETAINED-GATES obligation: Original28 overall failure at 24/28; P11/P16/P23/L03; sixteen external cases; unexecuted compatibility roles; comparison/passive authority; C035 including adverse timing; C057 and complete reach R01–R12/Q01–Q22; C068–C071 dispositions; unestablished storage causes; three unavailable original C080 artifacts; incomplete earlier history and LFS migration. Original failed full invocations and separately scoped recoveries retain their distinct identities.

Every GOAL domain remains open unless separately established: typed algorithms/libraries, appearance/skin deformation, forces/contacts/general dynamics, mechanisms/vehicles, articulated creatures/purposeful movement, flight/swimming, vegetation/wind, terrain/buildings, liquids/deformable solids, animation transitions/live engines, measured scale/performance and direct-tool authoring comparison. A finite renaming operation cannot close the language or product.
