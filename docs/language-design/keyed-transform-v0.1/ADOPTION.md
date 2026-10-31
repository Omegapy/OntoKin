# C081 pure keyed-value transformation

**Decision identity:** `OK-DEC-KEYED-TRANSFORM/0.1.0`  
**State:** Adopted for experimental implementation after independent design review; runtime implementation has not started.  
**Date:** October 31, 2026  
**Baseline:** C080-R2 commit `2e51fc170a9db17e90cd7d97fd4c028b9afaefe9`, tree `21c6124fb6deb46ef8205fd2ae3d46c07eb04331`.

This decision follows the [C080 next task](../../engineering/textured-surfaces-2026-10-31-c080/NEXT-TASK.md) and its [verified recovery disposition](../../engineering/c080-recovery-evidence-2026-10-31-r2/RECOVERY-DISPOSITION.md). The actual C080 delivery and finite completion are recorded in [Issue #26 comment 6547208739](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6547208739). The owner's autonomous development mandate authorizes this bounded language increment. Adoption, frozen inputs, implementation, measured checks, integration and complete release acceptance remain separate facts.

## 1. Purpose and explicit bindings

An agent can write one pure expression that transforms every value in an existing immutable keyed collection. The result retains the same keys and count. This supports reusable construction algorithms for dimensions, outlines, mounting parameters and material recipes without requiring one expression per supplied key. The operation performs construction work; it does not allocate simulation objects during a timeline.

Select source `ontokin "0.14";` and profile `keyed-transform-0.1`, explicit `ontokin.agent/0.14`, and recorded `ontokin.glb/0.14`. Immutable bundle and file transport remain `ontokin.bundle/0.2` and `ontokin.files/0.2`: their source and asset identity definitions need no change. Profile .14 inherits the adopted .13 geometry, appearance, execution-budget and supported physical semantics.

Agent/GLB .14 are separate bindings because their source admission and inspectable source/profile metadata differ. Their underlying glTF geometry, animation, UV and PNG representation stays the same. Earlier source, Agent and destination bindings retain their meanings and reject a .14 entry. Existing defaults remain unchanged. A valid .14 file is experimental development evidence, not full feature or product release acceptance.

## 2. Grammar and lexical scope

The new expression is:

```ontokin
map_keyed<Length>(dimensions, (key, value) -> value * 2)
```

The output element type is explicit. The input is one expression returning an admitted flat `Keyed<T>`. The two binder identifiers name the current key and value within the body expression only. The key binder has type `String`; the value binder has the input element type. They are not declarations outside the body and are not writable.

The [grammar supplement](ontokin-keyed-transform.ebnf) inherits existing expression precedence and uses the existing `->` token. `map_keyed` is a contextual expression form and reserved predefined spelling only in .14 declaring units. It is not a first-class function, a general lambda, or a dynamically selected callable. Older declaring units retain user-defined names, including a function called `map_keyed`; qualified calls to an older imported user function keep that function's meaning.

Binders must be distinct. They cannot shadow existing local names, predefined names, module definitions, import aliases, or visible class/scene names. `self` retains its existing lexical meaning and cannot be a binder. The input expression is outside the new binders' scope. Nested transforms may use distinct names under the same restrictions. No binder grants access to a private member or to a caller's private scope.

Pure imported definitions bind in their declaring module and retain its declared language/profile, visibility and nominal identity. A .14 unit may import compatible .2 through .13 definitions and .14 definitions under existing exact-pin rules. Older units cannot import .14 definitions or acquire its reserved names, syntax, types or capabilities through a newer caller.

## 3. Types, units and bounded values

Input and output are flat immutable keyed values with at most 256 entries each. The result is `Keyed<Out>` even when empty. Every selected body result must satisfy the explicit `Out` type using existing conversions, dimensional checks, frame rules and constructor-domain checks. The operation adds no new conversion, widening rule or leaf type.

The complete admitted element-kind set for .14 is:

| Existing type family | Admitted leaves |
| --- | --- |
| Scalars and quantities | `Int`, `Real`, `Bool`, `String`, `Quantity` and its existing unit aliases |
| Numeric compound values | Existing valid `Vec3<Q>`, `Vector3<Q>` and `Range<Q>` instantiations |
| Frames and placement | `FrameRef`, `Point3`, `Rotation`, `Pose`, `Color` |
| Surface construction | `LoftSection`, `SurfaceMaterial`, `PlanarPoint`, `PolygonVertex`, `PolygonRing`, `PolygonSection`, `FramedPolygonSection`, `PolygonPocket` |
| Texture construction | `TextureImage`, `PlanarUV`, `TextureBinding` |

Each leaf keeps all inherited bounds. For example, a `PolygonRing` is still subject to its adopted vertex limit; its admission as one existing nominal leaf does not admit nested `Keyed` types. `Geometry`, `BodyModel`, `Action`, authored object-reference collections and nested `Keyed` remain unsupported input/output elements. An intrinsic generated `Keyed<Ref<C>>` view is read-only and cannot be admitted by coercion, emptiness, a helper or an alias.

Before constructing output, check the admitted input type and entry bound. An oversized source literal is rejected by its existing bound before map allocation. A successful transform copies exactly the input keys, including their case, without inserting, dropping, renaming, sorting by value, filtering or reducing entries. Selected body evaluation follows canonical ASCII key order. Literal reordering may change exact source revision while leaving the keys and mathematical results of unaffected entries unchanged.

## 4. Static checks and evaluation

Evaluate the input expression once per map evaluation. Check the body statically with unknown, typed key/value binders even when the input is empty. Abstract checking also replaces enclosing value locals with unknown values of their existing types and frame metadata. It must check names, types, units, access, constructor signatures and pure-call dependency cycles without inventing sample values or executing value-dependent domain operations. Thus an empty `Real` map whose body divides by a zero-valued enclosing `Real` local has no dynamic division; an empty map with invalid units or private access still fails.

The existing global static pass remains authoritative for all pure definitions and dependency cycles. In .14 declaring expressions, abstract checks of lazy branches also mask enclosing local payloads to unknown values of their existing types and frames. Earlier declaring expressions retain their prior rules. At dynamic evaluation, only selected lazy branches execute; selected value-dependent domain failures remain failures. An empty map invokes no dynamic body. A nonempty map evaluates one body for each key and completes the entire result before that result can be accepted by construction or an Agent edit.

The first increment adds no filtering, new keys, reductions, mutable collection, unbounded loop, recursion, effects, generated events/relations, I/O, random source, file discovery or physical authority. Nested/chained transforms are allowed only within existing pure-expression/call depth and complete-request limits. Retain the explicit 128-level expression/call bound and diagnosed resource refusal for host recursion. This maximum does not promise that every 128-deep input is admitted: source, parser, type or cumulative work bounds can reject it earlier. Existing construction, geometry, material-region and output bounds remain in effect.

## 5. Dependency provenance, locations and repair

Every map evaluation retains dependency provenance from its actual input and selected body reads, including imported helpers, nested dependencies, reused values and existing guarded caches. A transform result cannot hide a generated-collection dependency that is forbidden for a construction input. Fresh value wrappers retain the inherited dependency/taint route; no new persistent or authority-bearing cache is introduced. Map nodes are excluded from constant/parameter memoization in this increment. Existing eligible helper caching must preserve its prior actual-read replay and accounting rules.

Keys retain their source declaration origins. The map expression and body have their own original source ID and UTF-8 spans. Inspection must distinguish the original key declaration from the expression that derived a value; neither iteration ordinals nor derived mesh triangles become editable source identities. A repair uses existing source/member keys and exact source spans, with the current program revision and file preconditions.

For transformed .14 values, `derived_transforms` is an ordered sequence of records containing `expression`, `body` and `input` source locations plus `input_element_type` and `output_element_type`. Chained maps retain earlier input-transform records before the current record. An indexed/output leaf also identifies its original stable `key` and `input_entry` location when known. Generated occurrence provenance exposes these input derivations as `input_transforms` alongside its existing input-entry record. These fields describe derivation and add no writable identity. Untouched earlier profile projections keep their existing shape.

Use existing diagnostic families: malformed syntax at the relevant token; invalid/shadowing names at the binder/name; invalid input or output type at its expression/type; unit and private-access failures at the offending body expression; dynamic body failure at its original source span. Preserve bounded details and imported source identity. Resource failure uses `OKL-E-RESOURCE` with the actual named exhausted bound, including `keyed_entries` or expression depth. Cancellation and callback exceptions retain their identities and must not be recast as type failures. No partial output may become accepted state.

## 6. Execution authority and inherited appearance

Charge ordinary expression/type/input/static-body work and one operation for each enclosing local masked during an abstract check. For each dynamic entry, charge one selection operation, the existing logical-value charges for fresh String-key and input-leaf bindings, actual selected body work, and a fresh output-leaf copy before appending it. Charge the completed immutable collection's logical materialization under the existing value-entry rules as well. These charges describe distinct selection, binding, evaluation, copying and result work. Subsequent construction, inspection, export, verification and byte delivery remain on the same admitted request ledger. Repeated references, an empty map, cached helper results or a reopened store do not reset work or create authority. Existing precharges and cooperative cancellation checkpoints apply before bounded loops, copies and serialization.

Ordinary defaults remain 100,000 operations and 30,000 ms. A larger source request requires separately granted current host ceilings. Caller caps only reduce available work. Computation time remains separate from modeled animation duration. Preserve the 32,768-bit operand, 256-entry numerical cache and 64-step reference cursor bounds. A higher-budget new workload cannot pass an old fixed-budget gate retroactively.

C080's exact reachable-source PNG declaration closure remains authoritative across .13 and .14 declaring units, including unused definitions and empty transform bodies. Only literal builtin `png_asset` calls declare attachments. Dynamic strings, aliases to arbitrary older user functions, comments and text do not. All declared images remain admitted once per compilation under current cumulative authority; a transform cannot drop an unused attachment, repeat admission for free, fetch a file, or change original image bytes. Existing four-image, encoded/decoded byte, UV, sampler, opacity, material and geometry bounds are unchanged.

## 7. Agent and recorded destination

Agent/0.14 retains all twelve operations and existing request shapes: discover, create, edit, validate, inspect, surface.mesh_page, evaluate, reset, export, artifact, status and cancel. Existing result fields retain their meanings; the .14 inspection extension adds only the bounded, read-only provenance records in section 5. Use a distinct `keyed-transform-program-agent.sqlite3` store and `ontokin.keyed-transform-program-agent-store/0.1` schema. Discovery names the experimental profile, transform semantics and current host view through detached copies. Keep the existing 8,388,608-byte request envelope, asset-edit transaction rules, source/revision identity, stale cursor handling, bounded retrieval, cancellation, failure rollback and reopen/retry behavior. Changed-payload retries remain errors; interrupted export cannot expose a successful artifact.

GLB/0.14 records the actual .14 source/profile and complete source/asset revision while retaining .13 mesh, material, sampler, image, UV, placement and recorded-motion rules. Identity-map output must have the same complete BIN chunk, accessor layout/data, material/image/sampler graph, stable occurrence identities and recorded motion as the independently authored equivalent .13 control. Whole GLB bytes and program revisions need not match: JSON contract, source/profile, source-derived provenance, program revisions and independently recomputed implementation fingerprints identify different source programs. Readers must enumerate and validate those permitted metadata differences, not discard arbitrary JSON differences.

Independent readers check actual supplied bytes. Destination validation must use the pinned Khronos/Three.js/Chromium roles, and actual captures must receive visual review. Still images establish their finite visible views; they do not establish hidden geometry, exact image identity, all motion, Unreal import or live destination physics.

## 8. Independent input freeze and evidence

Publish this reviewed decision and an independently authored exact input manifest before changing runtime. The [acceptance inventory](acceptance.json) and [freeze](INPUT-FREEZE.json) bind source, pinned dependencies, image bytes, independent expected values and finite workflow requirements. Expected answers are derived from source mathematics and declared motion, not from the candidate's output. Any defective frozen input requires a separately named correction, preserved original failure and fresh execution; never overwrite the original expectation to obtain a pass.

Required input groups cover empty/singleton/256 and over-bound input; ASCII key stability; every admitted leaf family; valid and invalid quantities/types/frames; static empty-body name/unit/access/cycle checks; imported pure helpers and older declaring semantics; nested dependencies and generated-view provenance; caller reductions/current host budgets/cancellation; output exhaustion; stale revisions/cursors; invalid-edit rollback; reopen/retry/changed payload; and interrupted publication.

The representative pinned reusable construction has at least two separately inspectable occurrences. An actual Agent transaction changes only one occurrence's transform parameter. Verify independently expected changed values and geometry while preserving the sibling, exact library and PNG bytes, stable surviving identities and unrelated recorded motion. A separate .14 identity-map source has a frozen explicit .13 control for independent complete-stream comparison.

Execute changed-behavior source/Agent/supplied-byte adversaries, the full corrected immediate-predecessor .13 workflow and independent audits, the applicable complete inherited local driver, and pinned destination checks with actual image review. Record exact source and input hashes, interpreter/tools, commands, logs, failures and results. Preserve the unchanged C080 original and corrected input lineages, all prior failed attempts and the complete C080-R2 packet with its embedded predecessors. Integration uses an independently reviewed candidate, a fresh bounded expected-head main lease, verified merge and resulting-main input equality/checks. Hosted workflows remain manual-only with default-false opt-in.

## 9. Retained gates and complete mission

Original28 remains failed overall with 24 of 28 passing; P11, P16, P23 and L03 remain unresolved. The 16 inherited external cases, missing interpreter roles, comparison/passive authority, held C035 and adverse timing, C057 and complete reach including every R01–R12/Q01–Q22 obligation, C068–C071 dispositions, C059's unestablished storage cause and unfinished historical Git LFS migration retain their recorded states. The three missing original C080 files stay missing; verified C080-R2 is separately named replacement evidence. Complete feature release and full-product acceptance remain false.

The complete [GOAL](../../../GOAL.md) remains in force: richer typed algorithms/libraries; appearance and skin deformation; forces, contacts and general dynamics; mechanisms/vehicles; articulated creatures and purposeful movement; flight/swimming; vegetation/wind; terrain/buildings; liquids/deformable solids; animation transitions/live engines; measured scale/performance and direct-tool authoring comparison. This increment advances reusable construction programming without asserting a measured productivity gain or any untested destination.
