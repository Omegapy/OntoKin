# C085 bounded pure keyed pair transformation

**Decision identity:** `OK-DEC-KEYED-ZIP/0.1.0`  
**State:** Adopted for the bounded experimental C085 increment, subject to publication of these exact reviewed inputs before runtime implementation. Independent contract and fixture review and unchanged-C084 control preflight are recorded in `ADOPTION-DECISION.json`. Adoption establishes no implemented or released behavior.  
**Date:** November 1, 2026  
**Baseline:** C084 main `21b014a4fbaab1245f7bae27e454d9307b9cc5ab`, tree `0da928527ab7ff72a58604b5929007e694fa85af`.

This decision addresses the [C084 next task](../../engineering/keyed-merge-2026-11-01-c084/NEXT-TASK.md). The owner's autonomous development mandate permits the bounded increment after its independent review and published freeze. Adoption, frozen inputs, implementation, actual validation, integration and complete release acceptance remain separate facts.

## 1. Purpose and explicit bindings

An agent can combine corresponding values from two finite immutable keyed collections. Separate libraries can provide panel dimensions and per-panel material choices. Their complete key sets must agree, so a missing dimension or material is an explicit failure. A pure expression computes one output value per matched key. Existing merge, filter, map and reduction operations can prepare either input or consume the result.

The selected bounded operation is exact-key pairing. This decision adds no intersection or outer join, conflict resolver, implicit default, inferred correspondence, nested collection or mutable reference. Key names identify correspondence; authored position does not. The usefulness claim is the expressible composition itself, not a measured authoring benefit.

The explicit bindings are source `ontokin "0.18";`, profile `keyed-zip-0.1`, `ontokin.agent/0.18` and recorded `ontokin.glb/0.18`. Immutable bundle/files remain `ontokin.bundle/0.2` and `ontokin.files/0.2`. Source .18 inherits .17 merge, .16 filter, .15 reduction, .14 map and the adopted geometry, appearance, execution-budget and physical semantics. This increment does not change glTF geometry or recorded-motion encoding.

Pairing creates no body, represented mass, force, event, physical connection, runtime spawn or motion authority. Earlier bindings retain their meanings and reject a .18 entry. CLI Agent/0.1, Python ProgramAgentService/0.2 and GLB/0.1 remain the defaults. Complete experimental feature release and full-product acceptance remain false.

## 2. Syntax, exact types and lexical scope

```ontokin
zip_keyed<Length, Real, Length>(widths, factors,
    (key, width, factor) -> width * factor)
```

The exact expression is `zip_keyed<T, U, V>(left, right, (key, left_value, right_value) -> body)`. It has exactly three explicit type arguments, two operand expressions and one scoped body. The left type must resolve to `Keyed<T>`, the right to `Keyed<U>`, and every statically checked or selected body result to `V`. The result is `Keyed<V>`, including when empty. Each boundary uses exact inherited semantic type/alias equality. An established quantity alias and its equivalent quantity dimension are the same type.

No implicit boundary widening, Int-to-Real conversion, common-type inference or type inference from a nonempty operand is introduced. The exact output boundary is a deliberate part of this new .18 operation; it does not alter the inherited map or reduction conversion rules. Existing conversions that take place inside a literal, constructor or called helper keep their own meanings before the boundary check. Unit, frame and imported nominal identity checks remain in force.

Each of `T`, `U` and `V` admits exactly these 24 immutable leaf families:

| Family | Admitted leaves |
| --- | --- |
| Scalars and quantities | `Int`, `Real`, `Bool`, `String`, `Quantity` and existing unit aliases |
| Numeric compounds | Existing valid `Vec3<Q>`, `Vector3<Q>` and `Range<Q>` instantiations |
| Frames and placement | `FrameRef`, `Point3`, `Rotation`, `Pose`, `Color` |
| Surface construction | `LoftSection`, `SurfaceMaterial`, `PlanarPoint`, `PolygonVertex`, `PolygonRing`, `PolygonSection`, `FramedPolygonSection`, `PolygonPocket` |
| Texture construction | `TextureImage`, `PlanarUV`, `TextureBinding` |

Every inherited leaf and constructor bound applies. `Geometry`, `BodyModel`, `Action`, reference leaves, generated-reference views, mutable values and nested `Keyed` types remain unsupported, including with two empty inputs. A nominal `PolygonRing` containing its established bounded vertices does not admit arbitrary nested collections. All three explicit leaf types are checked independently, including an otherwise unused input type and an empty result type.

The three distinct read-only binders exist only inside the body. Their types are `String`, `T` and `U`, in that order. Both operand expressions are outside the new binder scope. Binders cannot shadow enclosing locals, predefined names, module definitions, import aliases, visible class/member/scene names or `self`. Nested map/filter/reduce/zip binders must remain distinct under those rules. Existing lexical `self`, declaring-module visibility and private access remain authoritative.

`zip_keyed` is a contextual expression form and reserved predefined spelling only in .18 declaring units. It is not a first-class function, general lambda, method or dynamically selected callable. An older user-defined function named `zip_keyed` retains its ordinary meaning; a qualified .18 call to that pinned older definition remains an ordinary call. A .18 unit can import compatible .2 through .18 units under existing exact-pin rules. Older declaring units cannot import .18 or gain .18 semantics through a newer caller.

## 3. Static validation and dynamic admission order

Inherited global static checks of pure definitions, dependency cycles, names, visibility and types remain authoritative. They include unused definitions and statically checked unselected branches. Syntax and ordinary global checks precede execution. Within a zip expression, resolve and admit explicit types `T`, `U`, `V` in source order; check binder declarations; then statically check left, right and body in that order. The first local static failure wins. An invalid right operand or invalid body is not hidden by an empty or dynamically failing left input.

Check the body with unknown typed binder payloads even when both inputs are empty. The global abstract declaration pass does not replace the expression's own unknown-payload body check during each dynamic zip evaluation. Mask enclosing local payloads to unknown values while retaining their types and available frame metadata. Do not invent a sample key, use the first concrete pair as a sample, or execute a value-dependent domain operation during abstract checking. A type-correct empty body dividing by a captured zero-valued `Real` executes no dynamic division. Invalid names, units, private access, constructor signatures and pure-call cycles still fail. A statically invalid body therefore precedes any dynamic key-set mismatch.

After the required static checks, perform exactly this dynamic sequence:

1. Evaluate the left operand once and complete its exact type, leaf, key and entry-bound admission.
2. Evaluate the right operand once and complete the same admission.
3. Check complete key-set agreement in canonical ASCII order as section 4 specifies.
4. For each agreed key in canonical ASCII order, create fresh key/left/right bindings, execute the pure body once, check its exact output type, and copy its detached output leaf.
5. Complete the immutable keyed result and provenance before publication.

An input has at most 256 entries. A left evaluation/admission failure prevents dynamic right evaluation. An empty left still requires complete right evaluation/admission. An oversized input is refused before any key-set comparison even if a hypothetical intersection would be small. Literal entries and selected constructors within each input retain their inherited authored evaluation order. The canonical pairing traversal does not reorder operand evaluation.

A selected right-input constructor failure precedes a key-set mismatch. A mismatch precedes every dynamic body, including a body that would fail at a common key. After agreement, the first failing dynamic body in canonical key order ends the operation. Internal failures retain their original diagnostic and source location. Cancellation or exhausted current authority may interrupt any actual stage; these semantic priorities do not promise a later diagnostic after the request has already been cancelled or exhausted.

## 4. Complete key-set agreement and deterministic diagnostics

Retain exact key spelling and case and inherited ASCII key-domain rules. Compare the sorted union of admitted input keys in canonical ASCII order. Before each key's membership checks, use the real `keyed_zip_keyset` checkpoint. Test membership in both inputs. The first key present on only one side is the smallest ASCII element of their symmetric difference. Refuse it immediately without comparing values, executing any body or copying any output entry. Full key agreement must be established before beginning the pair loop.

The mismatch is `OKL-E-ID`, category `invalid`, phase `elaboration`, rule `LANG-007`. Its primary location is the first lexical token of the original operand expression on the **missing side** at this zip call. Its single related location is the first lexical token of the original operand on the **present side**. Its exact details are:

```json
{"operation": "zip_keyed", "key": "<lowest mismatched ASCII key>", "missing_side": "left"}
```

`missing_side` is exactly `"left"` or `"right"`. The message identifies the operation, the same key and the missing side. No cardinality-first alternative, all-missing-key list, guessed partner or common-prefix result is published. Equal counts with different key sets still fail. One empty side and one nonempty side fail at the nonempty side's lowest key. Both-empty is valid after all static and input checks.

For any new zip boundary diagnostic, grouped expressions retain their original opening `(` as the first lexical token, with its original one-byte UTF-8 span. A parser's shortened semantic expression node cannot replace these original coordinates. Non-ASCII preceding text is measured in UTF-8 bytes, not character positions. The first token and the full expression span are distinct records. Imported inputs keep their original entry provenance, but the new mismatch points to the actual operands authored at this call.

An exact left, right or body boundary mismatch uses `OKL-E-TYPE`, category `invalid`, phase `type`, rule `LANG-003`. Its primary location is the first original lexical token of the offending left/right/body expression. It has no related location. Details contain exactly `expected` and `actual`, using inherited canonical resolved type spelling: left expects `Keyed<T>`, right `Keyed<U>`, and body `V`. Quantity-dimension mismatch at a zip boundary uses this exact type diagnostic; arithmetic inside the body keeps its own inherited unit/frame/domain diagnostic. Check a left boundary failure before right, and right before body, in the local static sequence.

Unsupported leaf families retain `OKL-E-CAPABILITY-UNSUPPORTED`; invalid constructor internals, naming, access and cycles retain their inherited diagnostic families and original locations. Input-bound and other resource failures use the actual inherited exhausted bound. There is no separate zip result-size failure: admitted equal key sets have an output count equal to each input count, hence at most 256. No result with only the first 256 entries is possible.

For accepted inputs, every output key is the original agreed stable key; its value is the checked result of that pair's body. Different authored entry order preserves correspondence and surviving generated identities. Exact source/program revision hashes still follow the authored bytes. Inherited missing-key override/reference refusals occur after final construction shape resolution. Old accepted revisions, runs and artifacts remain pinned to their original membership and values.

## 5. Work, cancellation, caching and atomicity

Use the current complete-request ledger for all work. Charge ordinary type/expression work; static body checking and every masked enclosing local; both single input evaluations and full admissions; bounded sorting/index preparation before it runs; each key-set traversal and membership lookup; every pair selection; fresh String-key, left-leaf and right-leaf bindings; actual body work; detached output-leaf copying; provenance merge/copy records; and final keyed materialization. Compound values retain inherited logical-value copy costs even when immutable payload bytes may be shared internally.

Use `keyed_zip_keyset` immediately before each sorted union key's membership work. Use `keyed_zip_iteration` immediately before selecting and binding each agreed pair. Both are actual current-ledger cancellation/checkpoint stages. Empty input pairs execute no per-key or per-pair checkpoint, but retain ordinary admission, static-check and final materialization work. Keep inherited precharges and cooperative cancellation before bounded loops, copying and public serialization. Callback exceptions retain their original identity and must not be converted into type or key mismatch failures.

No zip-node constant/parameter memoization or persistent pairing cache is introduced. Existing eligible pure-helper caches retain guarded actual-read replay, exact current accounting and dependency/taint retention. Repeated references, cached helpers, empty results, reopened stores and retries do not reset the request ledger or grant authority.

A key mismatch, body/constructor failure, resource exhaustion, cancellation or interrupted publication cannot publish a partial accepted collection, source revision, run or artifact. Existing Agent transactions, rollback, request identity, unknown-outcome reconciliation and idempotent retry remain authoritative. A complete local temporary result is not an accepted public result until all required publication steps finish.

Ordinary defaults remain 100,000 operations and 30,000 ms. Higher source requests require independent current host ceilings; caller caps only reduce authority. Modeled animation duration remains separate from computation time. Preserve inherited parser/type/expression/call/constructor bounds, applicable 128-level expression/parser/call and 64-level type limits, the 32,768-bit operand bound, 256-entry numerical cache and 64-step cursor bound. Host recursion remains a resource refusal. New workloads cannot change old fixtures, horizons, rates, equations, helpers, oracles, budgets or tolerances.

## 6. Dependencies and detached provenance

Retain actual aggregate reads, forbidden generated-view taints and inherited map/reduction/filter/merge/zip derivations from both evaluated inputs. This includes initially empty inputs and an input whose binder the body never reads. Both complete operands are dependencies of the accepted pair result. Retain actual reads from every selected body, including an earlier iteration whose calculated value is later ignored by a downstream consumer. Unselected dynamic branches add no invented dynamic reads; global static checking is separate.

Downstream map, filter, reduction, indexing and generation preserve those aggregate reads even when they ignore every original entry value. Pairing cannot launder an inadmissible generated-view dependency. Guarded helper-cache replay preserves the same facts. Fresh wrappers retain origins and taints without mutating shared payloads or allowing recycled host object identities to contaminate later values.

The new read-only projections are `derived_zips` on derived property values and `input_zips` on generated occurrence provenance. Every zip record has exactly these ten fields:

| Field | Meaning |
| --- | --- |
| `expression` | Original complete zip-expression source location. |
| `left` | Original complete left-operand source location at the call. |
| `right` | Original complete right-operand source location at the call. |
| `body` | Original complete body-expression source location. |
| `left_element_type` | Canonical resolved `T` spelling. |
| `right_element_type` | Canonical resolved `U` spelling. |
| `output_element_type` | Canonical resolved `V` spelling. |
| `key` | `null` for an aggregate record; the exact stable key for a paired-entry record. |
| `left_entry` | `null` for an aggregate record; the original left matching entry location when known, otherwise `null`. |
| `right_entry` | `null` for an aggregate record; the original right matching entry location when known, otherwise `null`. |

All non-null locations use the inherited detached source ID, source revision, filename and UTF-8 byte-span shape. `left_entry` and `right_entry` identify actual matching source entries when known, independently of whether the body reads either binder. Use each admitted collection's retained original entry-source mapping. For an original keyed literal, this is the full inherited `keyed_entry` node: from the opening quote of its key through the end of its value expression, excluding the following comma. A missing original mapping remains `null`; do not invent a source span, synthesize an entry in an unrelated map or use an iteration ordinal. Key-set agreement guarantees that a per-entry record identifies a real pair even if one or both original locations are unavailable.

The existing singular key-origin/input-entry convention uses the left input's original key declaration when available. This identifies the preserved key's primary declaration, not the sole source of the output value. The new paired-entry record independently retains the right declaration and the full body expression. A generated part must preserve aggregate reads without assigning the part's key to an unrelated aggregate operation. Neither the zip expression nor its paired-entry record becomes a writable occurrence identity.

For every `Keyed` aggregate, normalize each new zip-family derivation to aggregate form by setting `key`, `left_entry` and `right_entry` to `null`, while preserving its original expression/operand/body locations and types. Deduplicate the normalized complete records in actual evaluation order. This rule applies to zip itself and to every downstream keyed producer or consumer, including maps, filters, merges and a condition that selects an otherwise plain keyed value. It applies only to the new zip origin family; inherited map/reduction/filter/merge origin rules and field shapes remain unchanged. It does not normalize scalar/indexed projections or stored leaf contributor records.

The current zip aggregate gathers normalized records from the left evaluation, then the right evaluation, then selected body evaluations in canonical key order; append the current zip's aggregate record. Direct nested zip calls or captured/indexed zip values read by a body contribute their normalized original records to this aggregate. Their actual pair-specific records remain available on the output leaf derived from that body.

The stored records for each output entry preserve that matching left entry's inherited records, then the matching right entry's inherited records, then actual derivations of the selected body result; append the current zip's paired-entry record. Preserve these records without key normalization or substitution. This entry sequence does not relabel unrelated aggregate records as contributors. A condition-only zip followed by a plain leaf retains its actual records; it does not acquire the current outer pair's key unless the current zip's separately appended record establishes that contribution.

When a public inspector indexes one output leaf or generates its occurrence, concatenate aggregate records first and that selected entry's records second. Deduplicate by equality of the **entire** detached record, retaining the first occurrence. The aggregate and paired-entry record for one expression are distinct and can both be present. Do not deduplicate solely by expression location or flatten the two input contributors into a single assumed source.

For plain keyed inputs `A`, `B`, `C` with the same key set and no earlier zip origins, define `inner = zip(A, B, body1)` and `outer = zip(inner, C, body2)` as shorthand for the fully typed syntax above. If both bodies simply compute from their binders, the outer aggregate zip list is `[inner/aggregate, outer/aggregate]`. The stored output entry for `k` has `[inner/k, outer/k]`. Its indexed or generated public projection is `[inner/aggregate, outer/aggregate, inner/k, outer/k]`. Inner aggregate records are deduplicated after the defined normalization; they must not gain a made-up `k` field. Frozen cases bind the complete order and original locations, including direct/captured body zips and a condition-only zip followed by a plain keyed result.

Inherited `derived_transforms`, `derived_reductions`, `derived_filters`, `derived_merges` and their generated `input_*` forms remain separate with their existing shapes and contributor rules. Earlier profile projections retain their exact prior fields. All nested provenance and result locations are bounded detached copies. Source/member keys, current program revisions and exact UTF-8 byte preconditions remain the repair authority.

## 7. Appearance, Agent operations and recorded output

Preserve exact reachable-source PNG declaration closure across .13 through .18 units, including unused definitions, empty inputs and discarded values. Only literal builtin `png_asset` calls declare attachments. Every declared image is admitted once per compilation under the current cumulative authority. Pairing cannot drop an attachment, accept changed bytes, fetch a file or obtain free repeated admission. Existing encoded/decoded image, UV, sampler, material, geometry and output bounds remain unchanged.

Agent/0.18 retains the twelve operations and existing request shapes: discover, create, edit, validate, inspect, surface.mesh_page, evaluate, reset, export, artifact, status and cancel. Discovery identifies the experimental profile, exact typed pair/body boundaries, complete key agreement, deterministic missing-side refusal, canonical traversal, 256-entry input/result bound and current host view through detached data. New inspection fields add only the read-only zip provenance above.

Use `keyed-zip-program-agent.sqlite3` with store schema `ontokin.keyed-zip-program-agent-store/0.1`. Preserve the 8,388,608-byte request envelope, exact source/asset identities, bounded source/asset/mesh/artifact reads, stale revisions/cursors, atomic rollback, cooperative cancellation, reopen/retry, changed-payload refusal and interrupted publication. Old accepted revisions, runs and artifacts remain inspectable after a scoped repair. Actual JSON response exhaustion must be exercised, not inferred from a declared bound.

GLB/0.18 records the actual source/profile and complete source/asset revision. Every complete output must match an independently authored explicit .17 control in complete BIN bytes and raw JSON/framing, except for a narrowly enumerated allowance for version/profile, source/revision/provenance and independently recomputed implementation-fingerprint fields. Geometry, accessor layout/data, complete material/image/sampler graph, exact PNG bytes, stable identities and unrelated recorded motion must agree. Arbitrary JSON suppression, reordered-member acceptance or selected-coordinate-only comparison is insufficient.

Independent readers consume actual supplied bytes and reject targeted corruptions. Use the pinned Khronos, Three.js and Chromium roles and directly review retained captures. Finite views and recorded poses support only their inspected scope. Unreal import, hidden geometry, live destination physics and general simulation require separate evidence.

## 8. Independent freeze and representative authoring workflow

Publish the reviewed decision, grammar, exact acceptance inventory, independently authored source/expected corpus, workflow requirements and exact hash manifest before runtime changes. Preflight separately authored explicit .17 controls on unchanged C084. Expected pairing, typed values, source locations, refusal precedence and finite budget outcomes come from this contract and source mathematics, never from candidate output. Preserve input-authoring failures. A defective frozen input requires a separately named correction, retained original failure and fresh execution lineage.

The independent corpus covers both-empty, singleton, mixed, 256-entry maximum, 257-entry input refusals, reordered and boundary keys, each one-sided empty mismatch, same-count unequal key sets, multiple mismatches, case-sensitive keys, all 24 families at applicable input/output positions, alias equality and exact boundary mismatches. Include malformed syntax, duplicate/shadowed binders, invalid constructors, private access, cycles, older reserved-name and declaring-unit compatibility, nested compositions, selected dependencies, empty taints, ignored binders, shared-payload isolation and guarded-cache replay.

Multiple-error fixtures must establish static right/body failure before dynamic left failure; dynamic left before right; complete right admission before key mismatch; key mismatch before a failing common-key body; and first canonical failing body after agreement. Freeze exact first-token and full-expression spans, grouped/nested operands, a UTF-8 prefix, both missing-side directions and exact details. Distinguish actual aggregate origins from the two matched contributors in nested, indexed, generated and condition-only cases.

Authority cases include actual cumulative work across both operands and every pair; low-budget refusal and adequate-budget success with a written conservative basis; current host ceilings and reducing caller caps; genuine cancellation at both named stages; callback-exception identity; atomicity; source/asset/artifact bounds; actual JSON response exhaustion; stale revisions/cursors; rollback; reopen/retry; changed payload; and interrupted publication. The contract does not assert a universal exact consumed-operation count. Such a claim would require a separately specified counting model. Do not change old gate settings to fit candidate costs.

The representative construction has two independent textured occurrences using a pinned library, separate keyed dimension and material definitions, exact PNG bytes and an unrelated moving marker. Through real Agent operations, repair only the first occurrence's paired attributes. Preserve the sibling, pinned library/assets, surviving identities and unrelated recorded marker motion. Reject a missing-partner candidate and verify exact rollback of its accepted source/revision. Keep raw requests/responses, durable stores, old-run/artifact readback, complete bounded source-unit pages, asset/artifact byte slices and all failure/retry evidence. Independent .17 controls construct every complete expected state without zip.

After reviewed adoption and published freeze, implement only this scope. Execute frozen source, Agent and supplied-byte cases; the complete immediate-predecessor .17 workflows/readers; applicable complete inherited local validation; pinned native checks; and actual visual review. Retain source/input/tool identities and every failure. Independently review the actual candidate before expected-head integration under a fresh bounded lease; verify the actual merge/tree and relevant resulting-main checks. Hosted workflows remain manual-only with default-false opt-in. Deliver one coherent ZIP preserving the unchanged complete C084 predecessor, its disclosed recovery chain, all source cuts and failures, and exact restoration instructions.

## 9. Retained release obligations and full mission

Original28 remains failed overall at 24/28 with P11/P16/P23/L03 unresolved. The 16 external cases, current-scope Python 3.11/3.13 and other unexecuted compatibility roles, comparison/passive authority, held C035 including adverse timing, C057 and complete reach including R01–R12/Q01–Q22 remain open as recorded. M1 remains rejected. C068 is unadopted, C069 rejected, C070 unselected and C071 rejected. C059's storage cause remains unestablished; historical Git LFS migration remains unfinished.

Complete earlier Git history and three original C080 artifacts remain unavailable. Both disclosed shallow boundaries remain unchanged. C080-R2 remains separately identified replacement evidence. The C084 failed full inherited invocation, separate three-role recovery, both structurally corrupt stores, unchanged-C083 failed diagnostic comparison and unestablished causes remain distinct preserved evidence; no new design decision relabels them.

Earlier finite core, construction, surface, impulse and center-of-mass force releases retain their meanings. Preserve every [GOAL](../../../GOAL.md) domain: typed algorithms/libraries; appearance and skin deformation; forces, contacts and general dynamics; mechanisms/vehicles; articulated creatures and purposeful movement; flight/swimming; vegetation/wind; terrain/buildings; liquids/deformable solids; animation transitions/live engines; measured scale/performance; and comparison with direct authoring tools. Unreal import, live destination physics and measured authoring benefit require their own evidence.

Complete experimental feature release and full-product acceptance remain false. This adoption starts no hosted job or continuation schedule. Runtime implementation may begin only after the exact reviewed adoption and independent input freeze are published and read back.
