# C082 bounded pure keyed reduction

**Decision identity:** `OK-DEC-KEYED-REDUCTION/0.1.0`  
**State:** Adopted for experimental implementation after independent exact-content review and input freeze; runtime implementation starts only after that reviewed freeze is published.  
**Date:** October 31, 2026  
**Baseline:** C081 commit `838581854b9a7f6a3260cedff6fd00914be544b8`, tree `705436e470b8aae058bf1a58fd8580eed8ba1cd8`.

This decision follows the [C081 next task](../../engineering/keyed-transform-2026-10-31-c081/NEXT-TASK.md) and its [finite delivery completion](https://github.com/Omegapy/OntoKin/issues/26#issuecomment-6548405914). The owner's autonomous development mandate authorizes the bounded increment. Exact adoption, independent input freeze, implementation, executed checks, integration and complete release acceptance remain separate facts.

## 1. Purpose and version bindings

An agent can combine a finite immutable keyed construction value into one typed result. Examples include a total length, total area, accumulated offset or a selected construction recipe. The author supplies a typed starting value and a pure expression that produces the next accumulator. This is construction computation and creates no body, mass, force, event, connection or motion authority.

Select source `ontokin "0.15";` with profile `keyed-reduction-0.1`, explicit `ontokin.agent/0.15`, and recorded `ontokin.glb/0.15`. Immutable bundle/files remain `ontokin.bundle/0.2` and `ontokin.files/0.2`. Profile .15 inherits the adopted .14 map, geometry, appearance, execution-budget and supported physical semantics. The new bindings expose distinct admission, discovery and provenance; glTF geometry, UV, PNG, material and recorded motion representations retain their prior rules.

Earlier source/Agent/destination bindings retain their meanings and reject a .15 entry. CLI Agent/0.1, Python ProgramAgentService/0.2 and GLB/0.1 defaults remain unchanged. Explicit .15 is experimental development; complete feature release and full-product acceptance remain false.

## 2. Syntax, names and lexical scope

```ontokin
reduce_keyed<Length>(dimensions, 0[m], (total, key, value) -> total + value)
```

The exact form is `reduce_keyed<Acc>(input, seed, (accumulator, key, value) -> body)`. `Acc` is the explicit accumulator and result type. The input expression has an existing explicit flat `Keyed<T>` type, which fixes the input leaf type `T`; a second generic argument is not added. The seed is checked against `Acc`. The accumulator binder has type `Acc`, the key binder is `String`, and the value binder has type `T`.

The three distinct, read-only binders exist only inside the body expression. Input and seed expressions cannot refer to these new bindings. Binders cannot shadow an enclosing local, predefined name, module definition, import alias, visible class/member/scene name or `self`. Nested map/reduce expressions require distinct unshadowed names. Existing lexical `self`, nominal identity and private-access rules remain authoritative.

`reduce_keyed` is a contextual expression form and reserved predefined spelling only in .15 declaring units. It is not a first-class function, general lambda, mutable loop or dynamically selected callable. A .14 or older user function named `reduce_keyed` retains its ordinary meaning; a qualified .15 call to that older function remains an ordinary call. Existing `map_keyed` remains available in .14 and .15 under its original contract. A .15 unit may import compatible .2 through .15 definitions under exact-pin rules. Older declaring units cannot import .15 or acquire its capabilities through a newer caller.

The [grammar supplement](ontokin-keyed-reduction.ebnf) inherits .14 precedence, expression nesting checks and type syntax.

## 3. Types and bounded immutable values

Input must be a flat immutable keyed value with no more than 256 entries. Both `T` and `Acc` use exactly the same admitted immutable leaf families as C081:

| Family | Admitted leaves |
| --- | --- |
| Scalars and quantities | `Int`, `Real`, `Bool`, `String`, `Quantity` and existing unit aliases |
| Numeric compound values | Existing valid `Vec3<Q>`, `Vector3<Q>` and `Range<Q>` instantiations |
| Frames and placement | `FrameRef`, `Point3`, `Rotation`, `Pose`, `Color` |
| Surface construction | `LoftSection`, `SurfaceMaterial`, `PlanarPoint`, `PolygonVertex`, `PolygonRing`, `PolygonSection`, `FramedPolygonSection`, `PolygonPocket` |
| Texture construction | `TextureImage`, `PlanarUV`, `TextureBinding` |

All inherited leaf bounds remain. A nominal leaf such as `PolygonRing` does not admit a nested `Keyed` type. `Geometry`, `BodyModel`, `Action`, object-reference collections and nested `Keyed` remain unsupported. Empty values, aliases, helper functions and coercion cannot admit a generated `Keyed<Ref<C>>` view.

The seed and each selected body result must satisfy `Acc` through the existing type, numeric conversion, dimension, frame and constructor-domain rules used for map output. No new widening, unit conversion or common-type inference is introduced. Exact implicit Int-to-Real conversion is admitted only where the inherited rules admit it. A seed mismatch fails even for an empty input; a body mismatch fails under static checking even for an empty input.

The abstract accumulator retains the seed's type and available frame/hint metadata, while its payload is unknown. Each concrete iteration binds the actual current accumulator and its frame. Operations and constructors keep their inherited frame compatibility checks. Returning a value of an admitted type does not grant new frame or physical authority.

## 4. Sequential evaluation and static checking

Ordinary global static checks of all pure definitions, dependency cycles, names, visibility and types remain authoritative. During a concrete reduction expression, after the required syntax/type/binder checks, evaluate the input once and complete its type and entry-bound admission before evaluating the seed once. Then check seed compatibility. This input-then-seed order preserves the first actual failure: an inadmissible input cannot be masked by a later seed-domain failure. Do not duplicate either evaluation for iteration or provenance.

Always check the body statically with unknown typed accumulator/key/value binders, including when the input is empty. Mask enclosing local payloads to unknown values while retaining their existing types and frame metadata. Static checking must not invent sample keys, evaluate a first entry as a sample, or execute value-dependent domains. Thus a type-correct empty reduction whose body divides by a captured zero-valued Real has no dynamic division. Invalid names, units, private access, constructor signatures and pure-call cycles still fail.

Create a fresh charged initial accumulator from the checked seed. Traverse input entries in canonical ASCII key order, preserving case and exact stable keys. For each entry, bind a fresh key, input value and current accumulator, execute the selected pure body exactly once, check it against `Acc`, and create a fresh next accumulator. The final result is a detached materialization of the last accumulator. An empty input executes zero dynamic bodies and returns a detached seed result with reduction provenance.

This is a sequential left fold. No associativity or commutativity is assumed. Do not regroup, sort by value, parallelize the fold, skip intermediate checks or replace it with a closed-form formula. Floating rounding, exact arithmetic, dynamic diagnostics, intermediate overflow/domain failures and resource consumption follow the authored sequential operations. An earlier failure remains a failure even if later mathematical terms would cancel it.

Nested/chained map and reduce expressions are permitted only within existing source, pure-call, expression, type, construction and complete-request limits. Retain the 128-level expression/call bound, 64-level type/parser bound where applicable, and diagnosed resource refusal for host recursion. A bound is a maximum, not a promise that every input at that depth is admitted. No recursion, mutation, filtering, new keys, generated events/relations, I/O, randomness or file discovery is added.

## 5. Work accounting and execution authority

All work remains on the current cumulative request ledger. Charge ordinary expression/type checks, input and seed evaluation, static body checking and each enclosing local masked for that check. Charge the initial accumulator copy. For every entry charge selection, fresh String-key/input-leaf/accumulator bindings, actual selected body work and the fresh next-accumulator copy. Charge final aggregate materialization and the existing per-record work for provenance merges and detached projections. Compound values consume the inherited logical-value charges on each required copy even when their immutable internal payload can be shared.

Use the named `keyed_reduction_iteration` stage at the real per-entry checkpoint. Keep precharges and cooperative cancellation before bounded loops, copying and serialization. Cancellation and callback exceptions retain their actual identities; do not convert them into type failures. A failed reduction cannot publish a partial accepted value, program revision, run or artifact. Agent transaction rollback, durable outcome reconciliation and idempotent retry remain inherited obligations.

Reduction nodes are not constant/parameter memoized and no persistent fold cache is added. Existing eligible pure-helper caches retain actual-read replay, guards and current accounting. Repeated references, empty folds, cached helpers and reopened stores do not reset cost or grant authority.

Ordinary defaults remain 100,000 operations and 30,000 ms. A higher source request needs separately granted current host ceilings; caller caps only reduce authority. Computation duration remains separate from modeled animation time. Preserve the 32,768-bit operand, 256-entry numerical cache and 64-step cursor bounds. New higher-budget workloads cannot retroactively pass an original fixed-budget gate.

## 6. Dependencies, provenance and repair authority

The aggregate retains actual dependency reads and forbidden generated-view taints from input evaluation, seed evaluation and every selected body execution, including imported helpers, nested map/reduce expressions and guarded-cache replay. Dependencies from an earlier iteration remain even when a later body returns a constant and discards the previous accumulator. Empty input still retains input/seed reads and taints. Unselected dynamic branches add no invented dynamic reads; inherited global static dependency checks still apply.

Fresh wrappers preserve provenance and taints without modifying shared immutable payloads. Retained wrapper identities must not alias later values through reused host-language object IDs. A reduction cannot make an otherwise forbidden construction dependency acceptable.

Expose a distinct read-only `derived_reductions` ordered sequence on derived property values. Each record contains detached `expression`, `input`, `seed` and `body` source locations plus `input_element_type` and `accumulator_type`. Keep unique actual source derivations in evaluation order, with earlier nested/input/seed/body derivations before the current reduction. Retain inherited `derived_transforms` independently. Generated occurrence provenance may expose the same reduction records as `input_reductions`, alongside existing input-entry and map derivation fields.

These locations refer to original source IDs and UTF-8 spans. The aggregate has no invented key, iteration ordinal, writable identity or generated-reference authority. Source/member keys, exact file preconditions and current program revisions remain the only existing repair route. Inspectors return detached bounded copies. Older profile projections retain their exact shapes.

Use existing diagnostic families at the relevant source token/span: syntax; invalid/shadowing binder name; inadmissible input or accumulator type; seed/body type, unit or private access failure; and the actual selected dynamic failure. Resource refusals use `OKL-E-RESOURCE` and identify the real exhausted bound, including `keyed_entries` or expression depth. Preserve imported source IDs and bounded details.

## 7. Inherited appearance and Agent/destination bindings

Exact reachable-source PNG declaration closure remains authoritative across .13, .14 and .15 declaring units, including unused definitions and empty bodies. Only literal builtin `png_asset` calls declare attachments. All declared images remain admitted once per compilation under current cumulative authority. Reduction cannot drop an unused attachment, fetch a file, alter PNG bytes or grant free repeated admission. Existing image, encoded/decoded byte, UV, sampler, opacity, material, geometry and output bounds stay unchanged.

Agent/0.15 retains twelve operations and their request shapes: discover, create, edit, validate, inspect, surface.mesh_page, evaluate, reset, export, artifact, status and cancel. Discovery identifies the experimental profile, seed/order semantics, admitted leaves and current host view through detached data. The inspection extension adds only the read-only reduction provenance above. Use `keyed-reduction-program-agent.sqlite3` and store schema `ontokin.keyed-reduction-program-agent-store/0.1`. Keep the 8,388,608-byte request envelope, exact source/asset revision identities, atomic edits, stale cursors, bounded full retrieval, cancellation, failure rollback, reopen/retry and changed-payload rejection. Interrupted publication cannot expose a successful artifact.

GLB/0.15 records its actual source/profile and complete source/asset revision. Geometry, accessor layout/data, material/image/sampler graph, PNG bytes, stable occurrence identities and unrelated recorded motion must match independently authored equivalent .14 controls. Compare complete delivered BIN and raw JSON/framing, enumerating permitted source/version/provenance/revision and independently recomputed implementation-fingerprint differences. Do not ignore arbitrary JSON or compare only selected coordinates.

Independent readers consume actual supplied bytes and reject targeted corruptions. Destination checks use pinned Khronos, Three.js and Chromium roles and actual capture review. Finite views do not prove hidden geometry, all motion, exact image identity, Unreal support or live destination physics.

## 8. Independent freeze, implementation and verification

Publish the exact reviewed decision, grammar, independent acceptance inventory and hash manifest before runtime edits. Expected results come from source mathematics and declared motion, never the candidate output. Preflight separately authored explicit .14 controls on unchanged C081. Preserve authoring failures. A defective frozen input needs a separately named correction, original failure and fresh execution; do not rewrite frozen expectations to obtain a pass.

The freeze covers empty/singleton/256/257 inputs; canonical order and reordered literals; admitted input/accumulator families; seed/body types, quantities and frames; nonassociative and intermediate-domain cases; static empty-body behavior; imported helper/access/cycles and older declaring semantics; nested map-to-reduce composition; accumulated provenance and overwritten dependency/taint cases; caller reductions, host ceilings and cancellation; stale cursors/revisions; rollback; reopen/retry; changed-payload retry; and interrupted publication.

Include a pinned reusable construction with two independent occurrences. Actual Agent operations repair one aggregate-driving parameter while preserving the sibling, exact library and PNG bytes, surviving identities and unrelated recorded motion. Supply independently authored explicit predecessor controls and complete-stream comparison expectations.

After freeze, implement only this contract; execute focused tests, the frozen source/Agent/supplied-byte cases, complete immediate-predecessor .14 workflows and readers, applicable complete inherited local checks, pinned native/browser checks and direct capture review. Record exact source/input identities, tools, commands, logs, failed attempts and observed outcomes. Runtime dependencies remain Python's standard library; pinned verification dependencies remain separately identified.

Review the candidate independently. Integrate through a fresh bounded expected-head main lease, verify the real merge/tree, check resulting-main inputs and run relevant resulting-main checks. Hosted workflows remain manual-only with default-false opt-in. Deliver a complete portable handoff preserving the unchanged C081 ZIP and its C080-R2/R1/C079 predecessors, all new source cuts and failures, source/evidence restoration, exact inventory, durable save and whole-file readback. Close only the finite performed scope in Issue #26.

## 9. Retained gates and full mission

Original28 remains failed overall at 24/28, with P11/P16/P23/L03 unresolved. The 16 external cases, current-scope Python 3.11/3.13 gaps, comparison/passive authority, held C035 including adverse timing, C057 and complete reach including R01–R12/Q01–Q22, C068–C071 dispositions, C059's unestablished storage cause and unfinished historical Git LFS migration remain as recorded. The three original missing C080 artifacts remain missing. Complete earlier Git history has not been recovered. C080-R2 is separately identified replacement evidence.

Retain every [GOAL](../../../GOAL.md) domain: typed algorithms/libraries; appearance and skin deformation; forces, contacts and general dynamics; mechanisms/vehicles; articulated creatures and purposeful movement; flight/swimming; vegetation/wind; terrain/buildings; liquids/deformable solids; animation transitions/live engines; measured scale/performance and direct-tool authoring comparison. Unreal import, live destination physics and measured authoring benefit remain unverified. This decision starts no hosted job, background worker or continuation schedule.
