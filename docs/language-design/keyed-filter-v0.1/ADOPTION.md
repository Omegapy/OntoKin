# C083 bounded pure keyed filtering

**Decision identity:** `OK-DEC-KEYED-FILTER/0.1.0`  
**State:** Adopted for experimental implementation after independent exact-content review and input freeze; runtime implementation starts only after that reviewed freeze is published.  
**Date:** October 31, 2026  
**Baseline:** C082 main `753bed5ff53c5a11bffe1913b9ceddb9b9624011`, tree `4577451cde3552da35d163d9278cbce9eba12339`.

This decision addresses the [C082 next task](../../engineering/keyed-reduction-2026-10-31-c082/NEXT-TASK.md). The owner's autonomous development mandate permits the bounded increment after reviewed adoption and an independent published input freeze. Adoption, implementation, executed validation, integration and complete release acceptance are separate facts.

## 1. Purpose and bindings

A pure Boolean predicate selects entries from a finite immutable keyed construction value. Every surviving entry keeps its original key and typed value. This supports parameterized panels, vents and other reusable part configurations, and composition with adopted map and reduction expressions. Filtering creates no body, mass, force, event, connection, mutable collection, runtime spawning or motion authority. Existing keyed generation can construct the selected entries in a new source revision under its established identity rules.

The explicit bindings are source `ontokin "0.16";`, profile `keyed-filter-0.1`, `ontokin.agent/0.16` and recorded `ontokin.glb/0.16`. Immutable bundle/files stay `ontokin.bundle/0.2` and `ontokin.files/0.2`. Source .16 inherits .15 reduction, .14 map and the adopted geometry, appearance, execution-budget and physical semantics. No glTF geometry or motion encoding changes are introduced.

Older bindings and defaults retain their meanings. CLI Agent/0.1, Python ProgramAgentService/0.2 and GLB/0.1 remain the defaults. Older bindings reject a .16 entry. Complete feature release and full-product acceptance remain false.

## 2. Syntax, types and names

```ontokin
filter_keyed<Length>(widths, (key, value) -> value >= self.minimum_width)
```

The exact form is `filter_keyed<T>(input, (key, value) -> predicate)`. One explicit generic type `T` names the input and surviving leaf type. The input must have type `Keyed<T>` and the result has type `Keyed<T>`. Compare semantic types through inherited type/alias resolution: `Length` and its existing equivalent quantity alias are the same type. Filtering introduces no Int/Real widening, coercion, common-type inference or value conversion at its boundary. Existing literal/constructor conversions that formed the input remain unchanged.

`T` admits exactly the 24 C081/C082 immutable leaf families: Int, Real, Bool, String, Quantity and existing unit aliases; valid Vec3, Vector3 and Range instantiations; FrameRef, Point3, Rotation, Pose, Color; LoftSection, SurfaceMaterial, PlanarPoint, PolygonVertex, PolygonRing, PolygonSection, FramedPolygonSection, PolygonPocket; TextureImage, PlanarUV and TextureBinding. All inherited leaf and constructor bounds apply. Geometry, BodyModel, Action, reference leaves, generated-reference views and nested Keyed types remain unsupported, including empty inputs. A nominal PolygonRing containing its established bounded vertices does not admit arbitrary nested Keyed types.

The predicate must return strict Bool. Numeric truthiness, String truthiness, a keyed result, a reference and any other non-Bool result fail. A false result cannot excuse an inadmissible input, required static failure or constructor-domain error encountered while creating the input.

The two distinct read-only binders exist only inside the predicate. The key has type String and the value has type T. Input evaluation cannot see the new binders. Binders cannot shadow enclosing locals, predefined names, module definitions, import aliases, visible class/member/scene names or `self`. Nested map/filter/reduce binders must remain distinct. Inherited lexical `self`, nominal identity and private-access rules apply.

`filter_keyed` is a contextual expression form and reserved predefined spelling only in .16 declaring units. It is not a first-class function, general lambda or dynamically selected callable. An older user function named `filter_keyed` retains its ordinary meaning; a qualified call from .16 to that pinned older definition is an ordinary call. A .16 unit can import compatible .2 through .16 units under exact-pin rules. Older declaring units cannot import .16 or acquire .16 semantics through a newer caller.

## 3. Admission, static checking and traversal

Retain global pure-definition static checks, dependency cycles, names, visibility and types. After syntax/type/binder checks, evaluate the input once and complete its leaf-type and entry-bound admission before any actual predicate traversal. Keep the 256-entry input bound. Output cardinality is at most the admitted input cardinality. Over-bound input fails even when the predicate would drop everything.

Always check the predicate statically with unknown typed key/value locals, including empty input. Mask enclosing local payloads to unknown values while retaining their types and available frame metadata. Do not invent a sample key or execute a first concrete entry for static inference. A type-correct empty predicate that refers to a captured zero divisor executes no dynamic division. Invalid names, units, private access, constructor signatures and pure-call cycles still fail, including in unselected static branches.

Input-leaf construction retains its inherited authored evaluation order. Traverse admitted entries in canonical ASCII key order, preserving exact spelling and case. For each entry, create fresh bounded key/value bindings and execute the selected predicate exactly once. Check the actual result as Bool. A true result retains a detached copy of that entry's original value; a false result retains no entry. A predicate failure terminates the whole operation before publishing an accepted result. Dropping one entry does not skip a later predicate. No predicate is run for an empty input.

The final result is a detached immutable keyed value. Its membership is an exact subset of the input; no renaming, new key, iteration-ordinal identity or writable occurrence identity is introduced. Source literal reordering preserves mathematical membership and surviving identities while exact source/program revision hashes continue to follow authored bytes. Apply inherited absent-key override/reference failures after final shape resolution. Old runs and artifacts remain pinned to their original revisions.

Nested/chained map/filter/reduce expressions remain subject to the inherited parser/type/expression/call/constructor bounds, including the 128-level expression-parser and expression/call bounds and 64-level type bound where applicable. Host recursion is diagnosed as a resource refusal. No recursion, mutation, I/O, randomness or file discovery is added.

## 4. Cumulative work and authority

Use the current complete-request work ledger. Charge ordinary expression/type work, one input evaluation, input admission, static predicate work and each enclosing local masked for that check. For each entry charge traversal selection, fresh String-key and input-leaf bindings, the actual predicate and any retained-value copy. Charge final keyed materialization, bounded copying and each provenance merge/projection record. Compound copies retain inherited logical-value costs even when their immutable internal payload can be shared.

Use the named `keyed_filter_iteration` stage at the real per-entry checkpoint. Preserve cooperative cancellation and precharges before bounded loops, copies and serialization. Callback exceptions retain their true identity and are not converted into predicate/type failures. A failed predicate, exhausted budget, cancelled request or interrupted publication cannot publish a partial accepted source, collection, run or artifact. Existing Agent transaction rollback, request identity, unknown-outcome reconciliation and idempotent retry remain authoritative.

Filter nodes are not constant/parameter memoized and no persistent membership cache is added. Eligible inherited pure-helper caches retain guarded actual-read replay and current accounting. Empty output, dropped values, caches and reopened stores do not reset work or authority.

Ordinary defaults remain 100,000 operations and 30,000 ms. Higher source requests need separately authorized current host ceilings; caller caps only reduce authority. Modeled animation duration is separate from computation time. Preserve the 32,768-bit operand, 256-entry numerical cache and 64-step cursor bounds. New demanding workloads never change an original gate's settings.

## 5. Dependency and provenance retention

The result retains actual dependency reads and forbidden generated-view taints from the input and every executed predicate, including entries ultimately dropped and entirely empty output. Input reads persist even for an initially empty value. Imported helpers, nested operations and guarded-cache replay preserve the same actual-read semantics. An unselected dynamic branch adds no invented dynamic read; global static checks still apply. Filtering cannot launder a forbidden construction dependency by dropping its value.

Fresh wrappers preserve origins and taints without modifying shared immutable payloads or allowing recycled host object IDs to contaminate later values. A surviving entry retains its original input-entry source provenance and inherited derivations. The detached aggregate also keeps the accumulated actual input/predicate derivations, including derivations produced by dropped entries. Downstream consumers of the aggregate must retain those dependencies and taints even if they discard every original entry.

Expose distinct read-only `derived_filters` records on derived property values and `input_filters` on generated occurrence provenance. Each filter record contains detached `expression`, `input` and `predicate` source locations plus canonical resolved `element_type` (for example Length for Quantity[m], and Point3<Length> for Point3). Locations use original source IDs, source revisions and UTF-8 byte spans. Keep unique actual source derivations in evaluation order, with inner/input/predicate derivations before the current filter. Inherited `derived_transforms`, `derived_reductions`, `input_transforms` and `input_reductions` remain independent and retain their meanings. Surviving entry provenance includes the current filter record without granting it a writable identity.

Source/member keys, exact UTF-8 byte preconditions and current program revisions remain the repair route. Inspector results are detached bounded copies. Generated `input_filters` merges aggregate and surviving-leaf derivations. This includes filters used only in a condition selecting an original plain keyed value; downstream maps and reductions keep filter origins even when their bodies ignore the input values. Earlier profile projections retain their exact field shapes. Exact boundary T mismatches use `OKL-E-TYPE` at the input expression token, including quantity-dimension mismatches; a non-Bool predicate uses `OKL-E-TYPE` at the predicate expression token. Internal predicate arithmetic keeps its inherited unit/domain diagnostics. Other diagnostics use existing syntax, name, access, capability, dependency, domain and resource families at their relevant original source locations; resource failures use `OKL-E-RESOURCE` with the real exhausted bound.

## 6. Appearance and public interfaces

Keep exact reachable-source PNG declaration closure across .13 through .16 declaring units, including unused definitions and dropped entries. Only literal builtin `png_asset` calls declare attachments. Admit all declared images once per compilation under current cumulative authority. Filtering cannot discard a declared image, admit changed bytes, fetch files or obtain free repeated admission. Image, encoded/decoded byte, UV, sampler, material, geometry and output bounds remain unchanged.

Agent/0.16 retains twelve operations and request shapes: discover, create, edit, validate, inspect, surface.mesh_page, evaluate, reset, export, artifact, status and cancel. Discovery identifies the experimental profile, strict predicate, stable membership, admitted types and current host view through detached data. The new inspection fields only add read-only filter provenance. Use `keyed-filter-program-agent.sqlite3` with store schema `ontokin.keyed-filter-program-agent-store/0.1`. Keep the 8,388,608-byte request envelope, exact source/asset identities, stale cursors, bounded complete retrieval, atomic edits, cancellation, rollback, reopen/retry, changed-payload refusal and interrupted-publication behavior.

GLB/0.16 records its actual source/profile and complete source/asset revision. Every complete delivered artifact must match an independently authored equivalent .15 control for complete BIN bytes and raw JSON/framing, except explicitly enumerated version/profile, source/revision/provenance and independently recomputed implementation-fingerprint fields. Geometry, accessor layout/data, PNG bytes, material/image/sampler graph, surviving stable identities and unrelated recorded motion must agree. Arbitrary JSON suppression and selected-coordinate-only comparison are insufficient.

Independent readers consume actual supplied bytes and reject targeted corruptions. Named pinned Khronos, Three.js and Chromium roles and direct retained-capture review remain required. Finite views establish only the inspected geometry and recorded poses; Unreal import, hidden geometry and live destination physics remain separate claims.

## 7. Independent inputs and representative repair

Publish this reviewed decision, the grammar, acceptance inventory, independently authored expected results/refusal codes/source spans and exact input hash manifest before runtime edits. Explicit .15 controls must preflight on unchanged C082. Expected membership and values come from authored predicates and source mathematics, never candidate outputs. Preserve authoring failures. A defective frozen input requires a separately named correction, retained original failure and fresh execution.

The freeze covers empty/singleton/256/257 input, keep-all/drop-all/mixed membership, reordered/boundary keys, every leaf family, invalid predicate type/name/unit/access/cycles, static masking and selected domain failures, input admission before traversal, dropped-entry dependencies/taints, map/filter/reduce composition, invalid resulting geometry, absent-key overrides/references, current host authority and caller reductions, actual cancellation, stale revisions/cursors, rollback, reopen/retry, changed payload and interrupted publication.

A pinned reusable PanelGroup has two independent occurrences and exact PNG bytes. Source repair changes only the first occurrence's selection-driving parameter, removes only its intended panel, preserves surviving identities and widths, leaves its sibling/library/assets unchanged and preserves unrelated recorded motion. Keep exact source/asset/artifact slices, raw requests/responses and durable stores. Independent .15 controls express the same selected geometry without filtering. Complete delivered-byte comparison and native observations establish this finite workflow.

After adoption and freeze, implement only this scope, execute frozen source/Agent/adversarial cases, complete immediate-predecessor .15 workflows/readers, applicable inherited local checks and direct visual review. Preserve source/input/tool identities and failures. Review independently before expected-head integration under a fresh bounded lease; verify actual merge/tree and relevant resulting-main checks. Hosted execution remains manual-only and default-false. Deliver one coherent ZIP preserving the exact C082 predecessor, its disclosed lineage, source cuts, failures and restoration records.

## 8. Retained gates

Original28 remains failed overall at 24/28 with P11/P16/P23/L03 unresolved. The 16 external cases, missing interpreter/compatibility roles, comparison/passive authority, held C035 including adverse timing, C057 and complete reach including R01–R12/Q01–Q22, C068–C071 dispositions, C059's unestablished storage cause and unfinished historical Git LFS migration remain unchanged. Complete earlier Git history and the three original missing C080 artifacts remain unavailable; C080-R2 remains separately identified replacement evidence.

Preserve every [GOAL](../../../GOAL.md) domain: typed algorithms/libraries; appearance and skin deformation; forces, contacts and general dynamics; mechanisms/vehicles; articulated creatures and purposeful movement; flight/swimming; vegetation/wind; terrain/buildings; liquids/deformable solids; animation transitions/live engines; measured scale/performance and direct-tool authoring comparison. Complete feature release and full-product acceptance remain false. This decision starts no hosted job or continuation schedule.
