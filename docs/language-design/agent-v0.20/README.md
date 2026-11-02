# Experimental String concatenation Agent/0.20

This explicit interface implements the adopted [C087 decision](../string-concat-v0.1/ADOPTION.md) and [exact specification](../string-concat-v0.1/SPECIFICATION.md). The [frozen original inputs](../string-concat-v0.1/freeze/INPUTS-MANIFEST.json) were independently authored and preflighted before runtime implementation. Implementation, executed validation, integration and full release acceptance remain separate facts.

The binding is `ontokin.agent/0.20`, for source `0.20`, profile `string-concat-0.1` and recorded `ontokin.glb/0.20`. Immutable transport remains `ontokin.bundle/0.2` and `ontokin.files/0.2`. Explicit storage is `string-concat-program-agent.sqlite3`, schema `ontokin.string-concat-program-agent-store/0.1`. Ordinary CLI Agent/0.1, Python ProgramAgentService/0.2 and GLB/0.1 defaults remain unchanged.

## Source operation and authority

`String + String -> String` returns the exact ordered Unicode scalar sequence of the left operand followed by the right. The expression's declaring source unit owns this overload. An older imported helper retains its older semantics. Both operands are evaluated once, left then right, including empty operands. No implicit conversion, normalization, trimming, interpolation, slicing or new String length operation is added. Every other operator/type pair retains its complete inherited dispatch.

Each computed result is limited to **65,536 UTF-8 bytes**. The actual complete-request ledger permits at most **4,194,304 cumulative logical result bytes**. The scalar scan precedes encoding or concatenation allocation. Reservation precedes allocation and is not refunded within a request. Empty results retain the three non-scan stage charges.

Successful dynamic concatenation adds `3 + ceil(left_bytes/64) + ceil(right_bytes/64) + ceil(result_bytes/64)` operations to the inherited expression/operand/provenance work. Four stages use the original admitted ledger: `string_concat_admission`, `string_concat_scan`, `string_concat_allocation` and `string_concat_publication`. Abstract type checking returns unknown String without dynamic String allocation or stages. The specification fixes exact ordering, diagnostics and cancellation semantics.

The ordinary defaults remain 100,000 operations and 30,000 ms. Larger source requests require independently current host ceilings; caller caps only reduce that authority. Operation/time requests do not enlarge either fixed String byte cap. Modeled animation duration remains separate.

## Agent workflow and discovery

`StringConcatAgentService` inherits the twelve operations: discover, create, edit, validate, inspect, surface.mesh_page, evaluate, reset, export, artifact, status and cancel. The operation envelopes, current-revision checks, atomic rollback, idempotent request rules, cancellation, durable reopen and historical artifact retrieval retain their earlier meanings. Requests remain bounded by 8,388,608 bytes. Source inspection uses bounded source-unit pages; existing asset/artifact slices remain unchanged.

Discovery adds `string_concat_interface`, whose `source_expressions.string_concat` describes the exact overload, both UTF-8 caps, charge schedule, cancellation stages, declaring semantics and current host/caller authority. Its inherited `rekey_keyed` entry reports that concatenation is available in this explicit profile. Original Agent/0.19 discovery continues to report its original absence.

The new request, response and diagnostic schemas retain every inherited operation and provenance shape. [SCHEMA-DERIVATION.json](SCHEMA-DERIVATION.json) identifies exact source hashes and every structural change from the unchanged .19 schemas. No new public concatenation-lineage family is introduced. Original transform/reduction/filter/merge/zip/rekey records retain their contributors, source revisions and locations.

## Computed namespaces and repair

Concatenation allows `prefix + old_key` inside `rekey_keyed`. Ordinary String validity does not make a valid stable key: rekey still requires 1–64 ASCII characters with an initial alphanumeric character and retains its original collision order. A 65-byte ASCII result can therefore concatenate successfully and then fail as a computed key.

Changing a prefix changes the affected generated occurrence keys. Original payload entries, earlier contributor keys and immutable source/member spans remain authoritative. The [frozen Agent scenarios](../../../examples/string-concat/agent/workflows.json) specify two library occurrences, scoped prefix and membership changes, unchanged sibling/source/PNG/payload/motion checks, invalid-prefix rollback, restoration, retry, reopen and historical artifact retrieval.

## Acceptance boundary

Recorded GLB/0.20 inherits geometry, material, image and motion representation. Complete comparison against independently authored .19 literal controls permits only the individually frozen source/version/provenance differences. Native validation and directly reviewed views are separate required observations. This interface does not establish Unreal import, live engine physics, measured authoring benefit, complete experimental-feature release or full-product acceptance. All [retained C086 gates](../../engineering/keyed-rekey-2026-11-01-c086/RETAINED-GATES.md) and the complete [project goal](../../../GOAL.md) remain in force.
