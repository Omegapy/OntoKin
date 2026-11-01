# C084 bounded pure keyed merge

**Decision identity:** `OK-DEC-KEYED-MERGE/0.1.0`  
**State:** Adopted for experimental implementation after independent exact-content review and input freeze; runtime implementation starts only after that reviewed freeze is published.  
**Date:** November 1, 2026  
**Baseline:** C083 main `c4451efe1f4d869b9644375f3a4ed52467304af0`, tree `1eed73f5f2a2af48cc5137ea14586e88e85bcc7e`.

This decision addresses the [C083 next task](../../engineering/keyed-filter-2026-10-31-c083/NEXT-TASK.md). The owner's autonomous development mandate permits this bounded increment after its independent review and published input freeze. Adoption, implementation, executed validation, integration and complete release acceptance remain separate facts.

## 1. Purpose and explicit bindings

Pure keyed merge combines two finite immutable keyed construction values that have the same resolved leaf type. Independently named groups can supply a standard panel set and an optional vent or bracket set. Existing mapping, reduction and filtering can prepare either operand. Existing keyed generation then constructs the combined set in a new source revision.

The explicit bindings are source `ontokin "0.17";`, profile `keyed-merge-0.1`, `ontokin.agent/0.17` and recorded `ontokin.glb/0.17`. Immutable bundle/files remain `ontokin.bundle/0.2` and `ontokin.files/0.2`. Source .17 inherits .16 filtering, .15 reduction, .14 mapping and the adopted geometry, appearance, execution-budget and physical semantics. This increment changes no glTF geometry or motion encoding.

Merge adds no body, represented mass, force, event, physical connection, mutable collection, runtime spawning or motion authority. It does not select a winner when two inputs use the same key.

Earlier bindings and defaults retain their meanings. CLI Agent/0.1, Python ProgramAgentService/0.2 and GLB/0.1 remain the defaults. Earlier bindings reject a .17 entry. Complete experimental feature release and full-product acceptance remain false.

## 2. Syntax, types and declaring units

```ontokin
merge_keyed<Length>(standard_widths, optional_widths)
```

The exact expression form is `merge_keyed<T>(left, right)`. It has one explicit type argument and two positional operands. Both operands must have resolved type `Keyed<T>`; the result has that same type. An empty operand retains its declared type and cannot infer or widen the other operand's type.

Use inherited semantic type and alias resolution. For example, an established quantity alias and its equivalent `Quantity` dimension are the same type. Merge introduces no Int/Real widening, common-type inference, conversion or coercion at either boundary. Literal and constructor conversions that formed an admitted input retain their existing meanings. Units, frames and imported nominal identity remain subject to their inherited rules.

`T` admits exactly these 24 immutable leaf families: Int, Real, Bool, String, Quantity with existing unit aliases, valid Vec3, Vector3 and Range instantiations, FrameRef, Point3, Rotation, Pose, Color, LoftSection, SurfaceMaterial, PlanarPoint, PolygonVertex, PolygonRing, PolygonSection, FramedPolygonSection, PolygonPocket, TextureImage, PlanarUV and TextureBinding. Every leaf and constructor bound still applies. Geometry, BodyModel, Action, general reference leaves, generated-reference views, mutable values and nested Keyed types remain unsupported, including when both inputs are empty. A nominal PolygonRing with its established bounded vertices does not admit arbitrary nested Keyed values.

The expression introduces no local binder or callable value. `merge_keyed` is a contextual expression form and reserved predefined spelling only in .17 declaring units. It is not a first-class function, general lambda, method or dynamically selected callable. An older user function named `merge_keyed` retains its ordinary meaning. A qualified call from .17 to that pinned older definition remains an ordinary call.

A .17 unit may import compatible .2 through .17 units under existing exact-pin rules. An older declaring unit cannot import .17 or acquire .17 semantics through a newer caller. All source-wide pure-definition checks, private access, visible names, constructor signatures and pure-call-cycle refusals remain in force, including statically checked unselected branches and unused definitions. Merge does not add recursion, mutation, I/O, randomness or file discovery.

## 3. Evaluation, admission and failure order

Static validation remains separate from dynamic operand evaluation. Resolve and admit `T`, then statically check the left and right operand types using inherited unknown-value semantics. Do not execute a selected constructor or helper merely to invent a static sample. A static error in the right operand is not hidden by an empty or dynamically failing left operand.

After required static checks, use this dynamic order:

1. Evaluate the left operand exactly once and complete its exact-type, leaf and entry-bound admission.
2. Evaluate the right operand exactly once and complete the same admission.
3. Check cross-input key collisions in canonical ASCII order as defined below.
4. If no key collides, enforce the result entry bound.
5. Copy the admitted entries into a detached canonical result and complete provenance/materialization work before publishing that result.

Each input is bounded to 256 entries. A left evaluation or admission failure prevents dynamic right evaluation. An empty left operand still requires full right evaluation and admission; an empty right operand does not bypass left admission. Within each input, literal entries and constructors retain their inherited authored evaluation order. Admission does not reorder that dynamic source evaluation.

A selected right constructor or helper failure precedes cross-input collision checking because the right input must first be fully admitted. A 257-entry input fails its input bound even if a hypothetical collision would reduce mathematical union size. A static or constructor failure retains its original diagnostic and source location; merge does not relabel it as a collision.

Cancellation or an exhausted current budget may interrupt any actual admission, collision check, copy or materialization stage. Diagnostic priority below describes semantic execution with sufficient authority; it does not promise that a later collision is diagnosed after the request has already exhausted its budget.

## 4. Canonical union and explicit collision refusal

Keep each admitted key's exact spelling and case. Compare keys by the existing ASCII ordering, independent of locale and authored insertion order. For collision detection, traverse the right input's keys in canonical ASCII order and test each against the admitted left input. The first shared key is therefore the smallest shared ASCII key. Stop at that collision; do not compare its values or traverse later collision candidates.

Any shared key is invalid, including keys whose values are equal. No overwrite, first-wins, last-wins, value-equality exception, implicit rename or merge-by-value rule exists.

The collision diagnostic is `OKL-E-ID`, category `invalid`, phase `elaboration`, with rule `LANG-007`. Its primary location is the first lexical token of the original right operand expression at this `merge_keyed` call. Its single related location is the first lexical token of the original left operand expression at that call. An opening `(` is the first token of a grouped operand; its one-byte span is retained even when the parser's semantic expression node describes the enclosed expression. These new .17 diagnostics use separate original-token coordinates, not a shortened or modified legacy expression node. The exact diagnostic details are:

```json
{"operation": "merge_keyed", "key": "<the smallest shared ASCII key>"}
```

The message identifies the operation and that same key. Frozen cases bind its actual UTF-8 primary and related byte spans, including grouped/nested operands and non-ASCII text before the call. Full operand-expression spans remain separately recorded in provenance. An operand may be a reference to an imported or computed input; the diagnostic still points to the authored operands at the merge call. Original entry provenance remains available independently for source repair.

Collision checking precedes result-size refusal after both inputs have passed admission. A colliding pair is therefore refused for its first canonical collision even when its total input count exceeds 256. If there is no collision, the result contains exactly `left_count + right_count` entries. A sum above 256 is refused with `OKL-E-RESOURCE`, category `resource_limit`, phase `support`, rule `LANG-009`. Its primary location is the original `merge_keyed` keyword token, including when the complete merge expression is grouped. It has no related location. Its exact details are:

```json
{"bound": "keyed_merge_result_entries", "limit": 256, "actual": 257}
```

Here `actual` is the admitted disjoint total, which may range from 257 through 512. This new result-bound `bound/limit/actual` detail shape is deliberate; inherited constructor and input-bound refusals retain their existing `budget/limit/consumed` shapes. The collision diagnostic does not publish a partial union or a synthetic collection with overwritten members. The resource diagnostic does not admit the first 256 entries.

An admitted result contains the exact disjoint union of both inputs in canonical ASCII order. Each result entry has a detached copy of its contributor's original typed value. Left-empty, right-empty and both-empty results obey the same type, authority and provenance rules. Reordering source entries preserves union membership, values and surviving construction identities while exact source/program revision hashes continue to follow authored bytes.

Retain inherited missing-key override and reference refusals after final construction shape resolution. Old runs and artifacts stay pinned to their original revisions and memberships. Adding or removing an optional group creates no writable identity for the merge expression itself.

## 5. Cumulative work, cancellation and atomicity

Use the current complete-request ledger for both inputs and the result. Charge ordinary expression/type work, each operand's single evaluation and full admission, canonical traversal/key comparisons, every collision lookup, detached leaf copying, inherited and current provenance merges, and final keyed materialization. Sorting or bounded index preparation is charged before it runs. Compound leaf copies retain inherited logical-value costs even when immutable payload bytes can be shared internally.

Use `keyed_merge_collision` as a real checkpoint before each canonical right-key collision lookup. Use `keyed_merge_iteration` as a real checkpoint before selecting and copying each result entry during canonical materialization. Both stages use the current request's cancellation and work authority. Empty inputs still pass the ordinary expression/admission and final materialization checks; they do not invent a per-entry iteration. Before any bounded copying or public serialization, apply the inherited precharge and cancellation checks.

No merge-node constant/parameter memoization or persistent membership cache is added. Eligible inherited pure-helper caches retain guarded actual-read replay and current accounting. A reused cache, empty output, reopened store or retry does not reset the ledger or increase authority. Callback exceptions retain their original identity and are not converted into type, collision or constructor errors.

A collision, invalid leaf, excess result, exhausted budget, cancellation or interrupted publication cannot publish a partial accepted source, collection, run or artifact. Existing Agent transaction rollback, request identity, unknown-outcome reconciliation and idempotent retry remain authoritative.

Ordinary defaults remain 100,000 operations and 30,000 ms. Higher source requests need independent current host ceilings; caller caps only reduce authority. Modeled animation duration remains separate from computation time. Preserve inherited parser/type/expression/call/constructor bounds, including applicable 128-level expression/parser/call and 64-level type limits, the 32,768-bit operand bound, 256-entry numerical cache and 64-step cursor bound. Host recursion remains a resource refusal. A new demanding workload cannot change an original gate's budget, horizon, rate, helper, equation, oracle or tolerance.

## 6. Dependencies and detached source provenance

Retain actual dependency reads, forbidden generated-view taints and inherited map/reduction/filter/merge origins from both evaluated operands, including initially empty operands. All admitted result entries may come from one side, but that does not erase the other side's evaluation. An empty result must still retain both inputs' actual dependencies and derivations. Selected dynamic branches contribute their actual reads; an unselected dynamic branch adds no invented read. Global static checking remains independent of that rule.

Keep aggregate dependencies and derivations when downstream mapping, filtering, reduction or generation ignores original entry values. Merge cannot launder an inadmissible construction dependency by combining it with an empty or unused set. Guarded helper-cache replay preserves these same facts.

Fresh wrappers preserve origins and taints without mutating shared immutable payloads or allowing recycled host object identities to contaminate later values. Every result entry retains its contributor's original entry source provenance and inherited derivations.

The new read-only projections are `derived_merges` on derived property values and `input_merges` on generated occurrence provenance. A merge record has exactly five fields:

| Field | Meaning |
| --- | --- |
| `expression` | Original complete merge-expression source location. |
| `left` | Original complete left-operand source location at that call. |
| `right` | Original complete right-operand source location at that call. |
| `element_type` | Canonical resolved common leaf type, using inherited type spelling. |
| `input_side` | `"both"` for an aggregate derivation, `"left"` or `"right"` for the contributor of an individual result entry. |

Locations use the inherited detached location shape with original source IDs, revisions and UTF-8 byte spans. They describe original authored expressions, including calls whose input values originated in pinned libraries. Existing entry-source records separately identify the original contributing entry. No location grants a writable synthetic occurrence identity.

For aggregate provenance, preserve unique actual inherited records from the left evaluation, then from the right evaluation, in their existing evaluation order; append this operation's `input_side: "both"` record. For an individual copied entry, preserve its inherited entry records and append this operation's `"left"` or `"right"` record. Exact-record equality, including `input_side`, controls deduplication.

Generated `input_merges` combines aggregate records first, then the selected entry records, retaining the first occurrence of each exact record. It can therefore contain both the aggregate and contributing-side record for one merge expression. The aggregate record establishes that both operands were evaluated; the entry record identifies which supplied that generated member. Nested merges retain separate original expression locations. Consumers must not flatten these records into a guessed single side or discard records solely because their expressions match.

For example, let `inner = merge_keyed<T>(A, B)` and `outer = merge_keyed<T>(inner, C)`, where A, B and C are plain disjoint inputs with no earlier merge origins. The outer aggregate has `[inner/both, outer/both]`. An entry supplied by A has its own stored entry records `[inner/left, outer/left]`. Generating that entry produces `input_merges` in the exact order `[inner/both, outer/both, inner/left, outer/left]`. Indexing the same entry into a derived scalar property uses that aggregate-before-selected-entry order in `derived_merges` as well. Indexing observes both the collection and its chosen entry; it does not replace the aggregate record with the entry record.

Mapping, filtering or reduction must retain the actual aggregate merge origins even when its body ignores the entry value. A conditional that reads a merge-derived value only in its condition and selects an otherwise plain keyed input also retains the condition's actual merge origins. Frozen cases must distinguish these aggregate reads from the contributing entry's stored records.

Inherited `derived_transforms`, `derived_reductions`, `derived_filters`, `input_transforms`, `input_reductions` and `input_filters` remain separate with their existing field shapes. Earlier profile projections retain their exact prior fields. All inspector results and nested provenance locations are detached bounded copies. Repair continues through original source/member keys, current program revision and exact UTF-8 byte preconditions.

An exact `T` boundary mismatch uses `OKL-E-TYPE`, category `invalid`, phase `type`, rule `LANG-003`, at the first lexical token of the offending operand, including quantity-dimension mismatches. Apply the same opening-parenthesis convention defined for collision locations. The mismatch has no related location. Its exact details contain `expected` and `actual`: `expected` is the canonical resolved `Keyed<T>` spelling, and `actual` is the offending operand's canonical resolved type spelling. For an operand that is itself Keyed, both spellings therefore name resolved Keyed types; a non-Keyed operand retains its actual non-Keyed type. Diagnose the left mismatch before the right mismatch when both are statically invalid. Unsupported leaf families retain `OKL-E-CAPABILITY-UNSUPPORTED`; invalid constructor internals retain their established type, unit, frame or domain diagnostic. Access, naming and pure-call-cycle failures retain their inherited families and original locations. Resource failures name the actual exhausted bound.

## 7. Appearance, Agent operations and delivered bytes

Keep exact reachable-source PNG declaration closure across .13 through .17 declaring units, including unused definitions, empty selected groups and values subsequently discarded by filtering. Only literal builtin `png_asset` calls declare attachments. Admit all declared images once per compilation under current cumulative authority. Merge cannot remove a required declared image, admit changed bytes, fetch files or receive free repeated image admission. Encoded/decoded image, UV, sampler, material, geometry and output bounds remain unchanged.

Agent/0.17 retains the twelve .16 operations and request shapes: discover, create, edit, validate, inspect, surface.mesh_page, evaluate, reset, export, artifact, status and cancel. Discovery identifies the experimental profile, exact common leaf type, duplicate-key refusal, 256-entry input/result bounds, canonical ordering and current host view through detached data. The new inspection fields add only read-only merge provenance.

Use `keyed-merge-program-agent.sqlite3` with store schema `ontokin.keyed-merge-program-agent-store/0.1`. Preserve the 8,388,608-byte request envelope, exact source/asset identities, bounded source/asset/mesh/artifact retrieval, stale revisions/cursors, rollback, cancellation, reopen/retry, changed-payload refusal and interrupted publication. Old accepted revisions and runs remain inspectable after a scoped source repair.

GLB/0.17 records its actual source/profile and complete source/asset revision. Each complete artifact must match an independently authored equivalent .16 control for complete BIN bytes and raw JSON/framing, except for an explicitly enumerated allowance for version/profile, source/revision/provenance and independently recomputed implementation-fingerprint fields. The comparison must preserve geometry, accessor layout/data, PNG bytes, the complete material/image/sampler graph, surviving stable identities and unrelated recorded motion. Arbitrary JSON suppression and selected-coordinate-only comparison are insufficient.

Independent readers consume actual supplied bytes and reject targeted corruptions. Pinned Khronos, Three.js and Chromium observations and direct review of retained captures remain required. A valid file or finite capture does not establish Unreal import, hidden geometry, live destination physics or general simulation support.

## 8. Independent freeze and representative repair

Publish the reviewed decision, grammar, exact acceptance inventory, independently authored source/expected corpus, workflow requirements and hash manifest before runtime changes. Preflight separately authored explicit .16 controls on unchanged C083. Expected membership, typed values, source spans, diagnostic details and finite budget outcomes must come from this contract and source mathematics, never candidate outputs. Preserve authoring failures. A defective frozen case needs a separately named correction, retained original failure and new execution lineage.

The freeze includes both-empty, each one-sided empty, singleton, mixed and 256-entry disjoint unions; independently admitted pairs with totals of 257 and 512; 257-entry invalid operands; reordered entries and boundary keys; equal/unequal duplicate values; multiple collisions with deterministic ordering; collision before result bound; right-constructor failure before collision; each of the 24 leaf families; alias equivalence and exact mismatches; invalid constructor, access and cycle cases; older declaring-unit and reserved-name compatibility; nested filter/map/reduce/merge composition; selected dynamic dependencies; empty-input dependencies/taints; shared-payload isolation; guarded-cache replay; absent-key repairs; and invalid resulting geometry.

Authority cases include current host ceilings and reducing caller caps, unchanged ordinary defaults, cumulative work across both operands, genuine cancellation at both named stages, failure atomicity, stale revisions/cursors, source/asset/artifact bounds, rollback, reopen/retry, changed-payload refusal and interrupted publication. Freeze low-budget refusal and adequate-budget outcomes with a written conservative operation/value-entry basis independent of candidate measurements. The contract does not fix a universal exact consumed-operation count; such a claim would require a separately specified counting model. Do not adjust original gates to match a candidate's observed costs.

A pinned reusable construction has two independent textured occurrences and exact PNG bytes. The left group supplies its standard named panels; a separately defined optional group supplies a disjoint named part set. Change only the first occurrence's selection-driving parameter through actual Agent operations to add or remove its optional set. Preserve the unchanged sibling, pinned library/assets, surviving identities and widths, and unrelated recorded motion. Keep exact source/asset/artifact slices, raw requests/responses, durable stores and failure/retry evidence. Independent .16 controls construct each complete expected result without merge.

After published adoption and freeze, implement only this scope. Execute its frozen source/Agent/supplied-byte cases, complete immediate-predecessor .16 workflows/readers, applicable complete inherited local validation and direct visual review. Retain source/input/tool identities and all failed attempts. Review the actual candidate independently before expected-head integration under a fresh bounded lease. Verify the actual merge/tree and relevant resulting-main checks. Hosted execution remains manual-only with default-false opt-in. Deliver one coherent ZIP with the unchanged complete C083 predecessor, exact available source history, evidence, failures and restoration instructions.

## 9. Retained release and product obligations

Original28 remains failed overall at 24/28 with P11/P16/P23/L03 unresolved. The 16 external cases, current-scope Python 3.11/3.13 and other unexecuted compatibility roles, comparison/passive authority, held C035 including adverse timing, C057 and complete reach including R01–R12/Q01–Q22 retain their recorded dispositions. M1 remains rejected; C068 is unadopted, C069 rejected, C070 unselected and C071 rejected. C059's storage cause remains unestablished and historical Git LFS migration remains unfinished.

Complete earlier Git history and three original C080 artifacts remain unavailable. The two disclosed shallow boundaries remain unchanged; C080-R2 remains separately identified replacement evidence. Earlier finite core, construction, surface, impulse and force releases retain their original meanings. This decision cannot relabel their evidence or pass a previously failed fixed-budget gate.

Preserve every [GOAL](../../../GOAL.md) domain: typed algorithms/libraries; appearance and skin deformation; forces, contacts and general dynamics; mechanisms/vehicles; articulated creatures and purposeful movement; flight/swimming; vegetation/wind; terrain/buildings; liquids/deformable solids; animation transitions/live engines; measured scale/performance; and comparison with direct authoring tools. Unreal import, live destination physics and measured authoring benefit require their own evidence.

Complete experimental feature release and full-product acceptance remain false. This decision starts no hosted job or continuation schedule. Runtime work remains subject to the reviewed and published input freeze above.
