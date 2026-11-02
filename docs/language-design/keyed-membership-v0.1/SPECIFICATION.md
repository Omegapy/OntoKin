# C088 bounded keyed membership

**Review draft v02 — not adopted and not implemented.**

Source basis: C087 main `a969a668f9fdf021793366ac5f5b9a8f9cd0fa56`, tree `2000393ec35ebc50d1517e71c7c1e630227b3a47`. A separate decision must identify the reviewed specification and independently authored input manifest. Publication and exact remote readback of both precede runtime edits.

## 1. Purpose and scope

Add one pure predicate, `has_key(collection, query) -> Bool`, for an existing finite immutable keyed collection. A reusable component library can select a supplied per-key dimension or its catalog default without repeating an accumulator and callback. Two independently configured instances share the same library, catalog, materials and texture while one instance's sparse overrides change.

Ordinary leaf membership is already expressible with `reduce_keyed<Bool>` and a conditional. This increment does not claim new expressive power for those collections, faster execution, or a measured authoring improvement. It also permits read-only membership on existing generated `Keyed<Ref<C>>` views, which the current reduction helper cannot accept. This uses the same access and generated-dependency restrictions as existing `len` and indexing; it grants no new part access or construction authority.

Explicit bindings are source `0.21` / `keyed-membership-0.1`, Agent/0.21 and recorded GLB/0.21. They are experimental development. Earlier meanings, ordinary CLI Agent/0.1, Python ProgramAgentService/0.2, GLB/0.1 and bundle/files 0.2 remain unchanged. Source .21 inherits .20 String concatenation, including its exact limits, work accounting, cache exclusion and original String diagnostic profile.

There is no optional-value type, fallback-returning lookup, exception handling, collection mutation, generic user-function system, new String operation, new container family, runtime spawning or physical/motion authority. Missing-key indexing remains an error. Membership does not validate application-specific relationships between an override map and its catalog or discard unexpected override keys.

## 2. Grammar, names and declaring versions

The existing ordinary call grammar applies; there is no new token or precedence level and no type argument. Exactly two positional arguments are required. In a .21 declaring unit, the bare name `has_key` resolves to the builtin and is predefined at the declaration, parameter, local and import-alias positions already checked against the compiler's predefined set. Existing call grammar continues to reject unsupported keyword/type-argument forms.

The declaring unit owns semantics. Older units do not acquire the builtin from a .21 entry program; an older legally declared function, parameter, member or import alias named `has_key` keeps its inherited meaning. A .21 unit may call an older exported function through its qualified module name. An older unit may not import a .21 dependency. The .20 dependency boundary must admit .21 importers while retaining the same refusal for earlier importers. No version is inferred solely from a numeric ordering.

The callee evaluates first, then every supplied argument once from left to right, as for inherited ordinary calls. A child error stops before later children or builtin admission. Even an incorrect-arity call evaluates its supplied children before the builtin's arity check, subject to inherited static validation. The predicate is not a special lazy form.

## 3. Types and static behavior

The first argument must be an existing valid immutable `Keyed<T>`. `T` is inferred from that argument. All authored leaf families already admitted by .20 are admitted unchanged, including their exact units, frames and nominal identity. No coercion or payload conversion occurs. Nested Keyed collections and authored Keyed reference annotations/literals retain their existing refusals.

Existing generated `Keyed<Ref<C>>` member views are also accepted directly. Their elements remain references with the exact original nominal type, and their original generated-collection dependency and access checks remain mandatory. This decision does not make `Keyed<Ref<C>>` a legal authored function parameter or return annotation, literal, transformation result family or new public type constructor.

The second argument must have exactly String type. Integers, Bool, references and other values are not converted. The result has exactly Bool type.

After eager arguments, signature admission checks arity, collection kind and admitted element family, then query type, in that order. Under abstract evaluation, or when either argument is unknown, a well-typed call returns unknown Bool. It does not inspect collection payloads, validate a literal query's key domain, scan keys, or perform any dynamic membership stage. This matches inherited indexing's type-only abstract behavior. Existing static expression/type work is still charged.

Unselected branches, empty callback bodies and never-invoked helpers retain complete inherited syntax, name, access, type, purity and cycle checking. A type-correct unselected query may be outside the dynamic stable-key domain without executing that domain check. A wrong-typed query still fails statically. Static absence is never folded to false.

## 4. Key meaning and dynamic order

Queries use the unchanged stable-key grammar `[A-Za-z0-9][A-Za-z0-9._-]{0,63}`: one through 64 ASCII characters, beginning with an ASCII letter or digit. Case, punctuation and complete spelling matter. Empty, overlong, Unicode, whitespace or punctuation-leading queries fail explicitly; they do not return false. The implementation checks length before regex/content validation and does not copy, encode or echo an oversized query.

After signature admission and the known-value check, reapply every existing generated-value taint through the compiler's generated-dependency guard. An illegal collection-shape dependency remains `CON-007` and fails before membership can publish a value. Ordinary argument evaluation may encounter that restriction earlier, when the generated view is read.

The bounded operation then validates the complete canonical input, validates the query, scans canonical keys in order, and returns true at the first exact match or false after the final key. Empty collections return false for a valid query. Reordering valid authored entries does not change the result or canonical scan order. Constructing the collection remains eager: an invalid payload fails during its ordinary construction, even if the queried key would be absent or would match an earlier entry.

Membership never evaluates a leaf payload again, compares leaf payloads, constructs a set/dictionary, sorts keys, or creates an intermediate collection. It reads only the existing entry container, key and resolved type/known-value metadata. Complete input admission precedes the query/scan so a malformed tail cannot be concealed by an early match.

## 5. Exact bounded work and authority

Use the actual `SharedExecutionBudget` already admitted for the complete request, with its original deadline, current host authority and caller caps. A missing, unresolved or unadmitted ledger has the unchanged `execution_context_required` refusal. No fallback construction ledger, new clock, reset, synthetic authority, independent allowance or persisted permission is created. Source requests remain subject to current host ceilings, and caller caps can only reduce allowed work.

Every dynamic tick polls the original cancellation callback before incrementing operations and checking its limit, then checks the original elapsed-time limit in the inherited order. Preserve thrown callback object identity and the established Agent mapping. A wrapper restores the previous `ledger.stage` in `finally`, including on failure. Membership does not reserve or consume C087 computed String bytes.

The following stages are normative. All work described after a stage's tick happens only if that tick succeeds.

| Stage | Operations | Bounded work |
| --- | ---: | --- |
| `keyed_membership_admission` | 1 | Require an exact native KeyedValue containing an exact tuple of entries, an admitted exact resolved element Type, and at most 256 entries. Read the tuple length before traversal. Capture that immutable tuple and the bounded type descriptor described below; do not copy its entries. |
| `keyed_membership_input` | 1 for each of n entries | Require an exact two-element entry tuple; an exact String key of length 1–64 satisfying the stable-key grammar; strict ascending order after the prior key; and an exact Value wrapper with a valid bounded type descriptor equal to the collection descriptor and a known payload. Never inspect or compare that leaf payload. |
| `keyed_membership_query` | 1 | Require an exact native String query, check its constant-time length, then validate at most 64 characters against the stable-key grammar. |
| `keyed_membership_scan` | 1 for each of k comparisons | Compare only the admitted key with the admitted query. Stop at the first exact match, otherwise finish all n entries. |
| `keyed_membership_publication` | 1 | Recheck authority before returning the Bool to the evaluator and its inherited provenance handling. |

A successful known call adds exactly `n + k + 3` dynamic stage operations, excluding inherited argument evaluation, static checking and expression/provenance bookkeeping. `k=0` for an empty input; otherwise a present key uses its one-based canonical position, and an absent key uses n. Empty input costs 3, and last/absent in 256 entries costs 515. For 256 entries, an early first match costs 260. Length and type admission are bounded before traversal. Each key has at most 64 characters; a paid input step performs a fixed number of bounded validations and comparisons, including key syntax/order and the shallow type descriptor. It does not promise only one character pass. Native type admission and comparison follow the exact bounds below. No total process-memory or wall-clock performance claim follows from these finite work bounds.

### Native type metadata admission

An exact outer Type class alone does not establish safe metadata: a private caller can forge recursive fields or objects with custom equality. Before type comparison, validate native fields without invoking recursive dataclass equality, user-defined comparison/hash, string conversion or payload evaluation. Check `type(kind) is str` and `len(kind) <= 32` before dispatch. Produce a small flat descriptor from the admitted native fields and compare those bounded descriptors. No collection is copied.

The following shapes are exactly the current compiler-produced leaf metadata. `None` below means the actual singleton, not an object equal to it.

- Simple kinds are Int, Real, Bool, String, FrameRef, Rotation, Pose, Color, LoftSection, SurfaceMaterial, TextureImage, PlanarUV, TextureBinding, PolygonPocket, FramedPolygonSection, PolygonSection, PolygonRing, PlanarPoint and PolygonVertex. Their dimension, element and name fields are all None.
- Quantity has an exact four-element tuple of exact native ints (Bool excluded), each from -16 through 16, with at least one nonzero exponent; element and name are None. The all-zero dimension is represented by Real in the existing compiler.
- Vec3, Vector3 and Range have dimension/name None and one exact Type child of Int, Real or the Quantity shape above. The child has no child. Int children remain admitted even for empty collections whose constructors ordinarily produce Real values.
- Point3 has dimension/name None and one exact Quantity child with dimension `(1, 0, 0, 0)` and no further child or name.
- A generated Ref has dimension/element None and an exact native nominal String name of length 1 through 278. Existing source/linker resolution establishes its identity and access; membership adds no nominal resolution. The maximum derives from package ID 128, module key 64, definition key 64 and the fixed `package/` and `/definitions/` separators. Entry nominal names and Object fit within the same bound.

The complete allowed descriptor has depth at most two and no arbitrary linked walk. Check child native type/kind before reading its fields. Cyclic/deep/unrecognized native metadata is refused as the collection error when it belongs to the declared expected Type, or the leaf-type error when it belongs to an entry. A non-Value entry leaf, a non-Type leaf.type, a malformed/mismatched leaf descriptor, or an UNKNOWN leaf payload uses the leaf-type diagnostic. A wrong container/entry tuple shape or non-String native key uses the collection-shape diagnostic. Bounds are checked before comparison or hashing; exact native int range checks cannot call foreign methods.

After initial admission, use the captured exact immutable entry tuple for both the input and scan stages. Source keys and queries are exact immutable Strings. A callback cannot replace the tuple being scanned by replacing a wrapper field. Types are compared through the captured bounded descriptor, and no leaf payload is reread after its admission. The original callback remains responsible for cancellation and retains its exception identity; membership adds no callback or observable mutable data API.

Failure before publication produces no accepted partial result, collection, revision, run or artifact. An operation-cap failure preserves the actual consumed prefix, and no later key/query/publication stage executes. Cancellation or the original deadline can interrupt at any stage. Existing source-text, value-entry, expression-depth, keyed cardinality, numerical operand/cache and result/cursor limits remain independent.

## 6. Diagnostics and precedence

Membership-specific errors use the complete ordinary call span as primary and no invented related source locations. Inherited child errors keep their original locations, details and exception identities. Exact new messages and details are frozen below; other default diagnostic fields follow the inherited diagnostic constructor.

| Condition | Code / phase | Message | Additional details |
| --- | --- | --- | --- |
| Arity differs from two | `OKL-E-TYPE` / `type` | `has_key requires exactly two positional arguments.` | `received`: actual count |
| First argument is not Keyed, expected Type metadata is malformed, or native collection/entry/key shape is invalid | `OKL-E-TYPE` / `type` | `has_key requires an immutable Keyed value.` | none |
| Query type or native payload is not exactly String | `OKL-E-TYPE` / `type` | `has_key query requires exactly String.` | none |
| A native leaf is not exact Value, has non-Type/malformed/mismatched Type metadata, or has an unknown payload | `OKL-E-TYPE` / `type` | `has_key input entry has a different resolved leaf type.` | none |
| Native input keys are duplicated or not strictly canonical | `OKL-E-ID` / `binding` | `has_key input keys must be unique canonical stable keys.` | none |
| Input or query key is outside the stable-key domain | `OKL-E-ID` / `binding` | `Stable keys must contain 1–64 ASCII letters, digits, '.', '_', or '-', and begin with a letter or digit.` | none |
| Native input exceeds 256 entries | `OKL-E-RESOURCE` / `support` | `Keyed membership input exceeds 256 entries.` | `budget`: `keyed_entries`; `limit`: 256; `consumed`: actual count |
| Missing admitted execution context | `OKL-E-RESOURCE` / `support` | `Construction requires one admitted execution context.` | `budget_reason`: `execution_context_required` |

Unsupported authored element families retain the existing `_keyed_leaf` refusal and its original diagnostic. Ordinary source construction already excludes malformed native inputs; their direct-operation checks establish bounded internal admission, not a new way to author malformed data.

Precedence is inherited static validation; callee and eager child errors; arity; collection kind/admitted element family; query type; abstract/unknown return; generated-taint guard; admitted-ledger precondition; admission-stage authority and native collection shape/cardinality/expected type descriptor; each input-stage authority followed by that entry's shape, key domain, canonical order and leaf wrapper/type-descriptor/knownness; query-stage authority and query native type/domain; each scan-stage authority and comparison; publication authority; then inherited value-flow and downstream consumers. Check key native String type as collection shape before a length or regex read. Runtime authority can prevent a later semantic refusal. Do not catch and relabel original callback, operation or deadline failures.

## 7. Dependencies, caches and repair

Keep `has_key` outside the existing constant and parameter-result call allowlists. A cache route may not skip a call that ordinary evaluation would execute, including within an enclosing expression or helper. Syntax-only classification caches remain allowed. Every actual invocation pays every applicable stage. Reading a previously computed immutable parameter/derived binding retains inherited binding reuse, fresh dependency/taint guards and current request checks; it is not a new invocation.

Both true and false results depend on the actual admitted collection and query. Preserve every actually read parameter/member/definition dependency and all detached map/reduction/filter/merge/zip/rekey origins and generated taints through the ordinary expression-flow machinery. Do not refine an aggregate origin to a fictitious selected payload key just because membership is true. Do not invent reads for dynamically unselected branches. No new public membership-lineage family, writable key, generated identity or patch authority is added.

Original .ok bytes, module/image pins, immutable revision identities and exact source spans remain repair authority. Insertion, update and removal of one occurrence's override must leave the other occurrence, unchanged catalog/library/texture bytes, materials, surviving generated identities and independent recorded motion unchanged. A selected invalid dimension fails the existing geometry rules atomically. An unguarded absent lookup retains its existing `OKL-E-NAME` refusal.

## 8. Agent, recorded delivery and independent observations

Agent/0.21 retains the inherited twelve operations, source/revision integrity, request identity, scoped byte patches, rollback, bounded inspection, cancellation/reset/status, reopen/retry and artifact semantics. Its explicit store is `keyed-membership-program-agent.sqlite3`, schema `ontokin.keyed-membership-program-agent-store/0.1`. Discovery must expose the exact signature, declaring-unit boundary, admitted collections including generated views, stable-key domain, eager/static behavior, all five dynamic stages and formula, preserved provenance and current host/caller authority.

Recorded GLB/0.21 carries the explicit binding and independently checkable source/revision identity. Complete geometry, accessors, material/PBR/UV facts, image bytes, node identities and animation data must agree with independently authored .20 literal/reduction controls. Permitted metadata differences are individually enumerated version/profile, source/revision/span/provenance and implementation-fingerprint paths. Never strip all metadata to obtain equality. New source expressions naturally change spans/dependencies; derive each expected difference from original source. Framing, padding, complete JSON and BIN data remain checked.

The representative source and Agent workflow has two instances of one pinned three-panel library and catalog, sparse per-instance width overrides, exact namespace keys, preserved appearance/image and independent animation. Frozen states include insertion, update, removal, malformed selected dimension, guarded/unguarded absence, unchanged sibling/library, stale revision/cursor, atomic rollback, reopened stores, idempotent retries, changed request payload and interrupted publication.

Independent readers check actual producer stores/artifacts and refuse predetermined coherent corruptions. Retained SQLite databases are inspected immutably or through private copies. Fresh native delivery uses the inherited pinned validator and actual browser/Three.js pipeline; each required capture receives direct review. A valid GLB or browser view establishes neither Unreal import nor live destination physics.

## 9. Freeze and execution gates

A different author determines expected Booleans, selected widths, final keys, refusals/locations, stage costs, interruption prefixes, generated-view restrictions, actual dependencies and workflow invariants before candidate execution. Publish and read back the reviewed adoption and complete exact input bytes/modes before runtime edits. Preflight immediate-predecessor literal and reduction controls on exact unchanged C087; those controls do not establish .21 stage charges. Preserve every draft and failed preflight. Any later correction requires a separate reviewed preconditioned overlay preserving originals and observed failures.

Coverage includes empty/singleton/first/middle/last/absent/reordered keys; case and punctuation; 1/64/65-character, empty and invalid keys; every admitted leaf family; wrong arguments/types/arity; eager invalid payload; unknown locals/empty callbacks/unselected branches; old names and declaring-version imports; every inherited keyed transformation and String concatenation; guarded/unguarded lookup; generated views/access/shape taints/cycles; true and false dependencies; current ceilings and caller caps; all operation/cancellation/deadline stage boundaries; repeated calls/bindings/caches/reopened stores. Direct fresh-ledger internal-operation checks are labeled separately from source and Agent workflows; they may not preload counters or substitute authority to manufacture success.

After implementation, run all frozen source/Agent/resource cases, independent readers and hostile mutations, complete immediate-predecessor workflows with exact retained-artifact comparisons, and the complete mandatory inherited local roles. Preserve original failures and missing roles. Run actual affected native delivery/capture checks, independent candidate review, observed-head serialized integration, and resulting-main verification. Bind each observation to actual source, input identities, environment, commands, logs and artifacts.

## 10. Retained obligations

Carry the C087 RETAINED-GATES.md unchanged by identity, including its failed original full invocation (33 passed roles plus one separately recovered documents role), all predecessor failed/recovered attempts and missing historical evidence. Original28 remains 24/28 and overall failed; sixteen external attestations and current Python 3.11/3.13 remain pending; comparison/passive authority, C035 adverse timing, C057/complete reach, C068–C071 dispositions, unknown storage causes, missing C080 artifacts/earlier history and historical LFS migration remain at their recorded states.

Defaults remain 100,000 operations and 30,000 ms. Do not change original horizons, rates, equations, helpers, oracles, numerical/cache/cursor limits or tolerances. Higher-budget new results cannot pass an original fixed-budget gate retroactively. Hosted workflows stay manual-only with default-false opt-in. No job or continuation schedule starts from this document.

Every GOAL domain remains required: typed reusable programs; exterior form, appearance and skin deformation; forces, contacts and general dynamics; mechanisms and vehicles; articulated creatures and purposeful movement; flight and swimming; vegetation/wind; terrain/buildings; liquids/deformable matter; richer animation and actual engine delivery; scale/performance and measured comparison with direct tools. Implementation, integrated development, complete feature release and full-product acceptance remain distinct.
