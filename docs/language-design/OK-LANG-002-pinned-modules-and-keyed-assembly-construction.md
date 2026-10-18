---
project: OntoKin
document_id: OK-LANG-002
title: Pinned Modules and Keyed Assembly Construction
version: 0.1.1
date: 2026-10-18
status: adopted-for-experimental-implementation
document_type: language-extension-contract
repository: https://github.com/Omegapy/OntoKin
reviewed_source_commit: c4152509533f77ba54fac78268ba425df9b1a177
language_version: "0.2"
profile: construction-0.1
agent_contract: ontokin.agent/0.2
delivery_contract: ontokin.glb/0.2
implementation_status: experimental-reference-0.4.0-release-gate-tracked-separately
---

# Pinned modules and keyed assembly construction

## 1. Purpose, authority, and version boundary

Make reusable OntoKin components usable across source files and allow one declarative construction to create a bounded family of independently identified parts. An agent should supply typed, explicitly keyed inputs, reuse a pinned component definition, inspect one generated occurrence, and repair that occurrence without rewriting its siblings or changing the shared library by accident.

This contract was **adopted for experimental implementation on October 18, 2026** under the project owner’s delegated technical authority. Adoption fixed the syntax, semantic choices, source-bundle identity, companion grammar/schemas, limits, and predetermined acceptance requirements before production implementation. The resulting experimental 0.4.0 implementation has a separate [measured evidence record](../engineering/construction-validation/README.md); [STATUS](../../STATUS.md) records whether its complete release and publication gate has passed. Adoption itself is not an execution result. The earlier 0.3.0 implementation and its evidence belong to [OK-AGENT-001](../engineering/OK-AGENT-001-ai-agent-authoring-and-inspection-interface.md).

The extension advances [GOAL.md](../../GOAL.md): OntoKin is a programming language for agents to create, inspect, revise, and reuse meaningful 3D objects and behavior. Cross-file definitions and finite keyed construction address a specific missing programming capability. They do not complete procedural modeling, the required product domains, purposeful control, or the authoring-benefit benchmark.

[OK-LANG-001](OK-LANG-001-core-language-specification.md) remains authoritative for language `0.1` and `core-0.1`. Existing single-file programs, source revisions, diagnostics, agent requests, fixtures, and expected motion retain their meanings. This extension names language **`0.2`**, semantic profile **`construction-0.1`**, and a separately versioned **`ontokin.agent/0.2`** binding. A `0.1` program cannot silently acquire import or generation semantics. A `0.2` result must disclose its authored profile instead of calling itself `core-0.1` because it uses the same mechanical evaluator.

The extension changes definition resolution and construction. The baseline rules for dimensions, frames, immutable descriptions, nominal references, independent instances, ownership versus following/connections, single motion authority, mass accounting, event ordering, and release/state transfer remain applicable unless a specific rule below explicitly extends their construction-time meaning. [OK-SEM-001](OK-SEM-001-core-object-motion-and-physics-semantics.md) supplies the underlying distinctions; no new contact solver or physical capability is implied.

## 2. Bounded milestone requirements

The following adopted requirements define this release's finite obligations. They are narrower than the complete product requirements mapped in section 10.

| ID | Required outcome |
| --- | --- |
| CON-001 | Interpret `0.2` / `construction-0.1` explicitly while preserving all existing `0.1` behavior and rejecting unsupported version/profile combinations. |
| CON-002 | Resolve an entry source and all imported definition modules from an explicit source bundle, with exact content pins and no implicit network, host-code execution, or ambient search path. |
| CON-003 | Bind imported names through explicit aliases while retaining the imported definition's nominal identity and original source location. An alias is not a new type. |
| CON-004 | Reject absent/mismatched pins, ambiguous definitions, import cycles, executable imported scenes, and undeclared dependencies before successful construction. |
| CON-005 | Give the complete immutable program a distinct content identity while preserving each file's exact UTF-8 source identity. Changes to dependencies invalidate the program's derived products as products of the new revision. |
| CON-006 | Provide a finite immutable `Keyed<T>` construction input with explicit stable keys, homogeneous typed values, duplicate-key rejection, and deterministic lookup/iteration. |
| CON-007 | Construct one independent part occurrence per selected key after final input overrides resolve. Generation is definition-time elaboration and never runtime allocation or mutation. |
| CON-008 | Derive each generated occurrence identity from its owning occurrence, collection declaration key, and input key. Insertion, removal, or reordering cannot rename surviving entries or give them another entry's state. |
| CON-009 | Preserve source encapsulation and initializer precedence through typed member/key paths. A public per-key parameter override affects only its selected occurrence and applies before that child's own nested generation. |
| CON-010 | Validate generated parts and ordinary parts by the same geometry, relationship, matter, motion, and capability rules. A collection contributes no extra physical object, frame, mass, or transform. |
| CON-011 | Return bounded inspection and source provenance for collection definitions, inputs, generated occurrences, imported defaults, and public repair targets. Shared declarations do not become writable occurrence-local bytes. |
| CON-012 | Bound dependency resolution, keyed values, elaboration, and serialization; report exhaustion separately from invalid input, logical cycles, and unsupported behavior. Preserve accepted state on failure. |
| CON-013 | Extend revision-checked agent operations atomically across the program bundle without changing the meaning of `ontokin.agent/0.1` fields or weakening retry/run/cursor isolation. |
| CON-014 | Trace generated output to the whole program and its source files. Named GLB delivery preserves generated identities and the evaluator's motion within the established tolerances, with explicit loss reporting. |
| CON-015 | Publish executable positive, boundary, negative, composition, scoped-edit, version, and delivery cases with independently stated expectations and exact local/CI evidence. |

## 3. Source units and pinned resolution

### 3.1 Entry program and definition modules

One entry source declares the scene. Imported modules supply reusable class and pure function definitions; loading a module does not create scene objects, advance a clock, run an event, perform I/O, call a model, or execute host-language code. A definition's pure parameter/derived expression is evaluated in the occurrence and dependency context where the language requires it, not as a mutable module initialization side effect.

Every source unit declares the adopted language version, semantic profile, and stable module identity. The entry and its transitive dependencies must use the same construction contract. Similar lexical class names in different modules are permitted through explicit qualification. Accidental unqualified import, implicit re-export, fallback to a different version, or resolution from a previous editor session is not permitted.

The source-unit order is:

1. `ontokin "0.2";`
2. `module Name @ "module-key";`
3. `profile "construction-0.1";`
4. Zero or more baseline `requires` declarations.
5. Zero or more explicitly keyed imports.
6. Zero or more class/function definitions, optionally marked `public` or `private`; module-scope visibility defaults to public.
7. Exactly one scene in the entry source; no scene in an imported module.

The complete adopted grammar is [ontokin-construction.ebnf](construction-v0.1/ontokin-construction.ebnf), with unchanged lexical/numeric rules inherited from OK-LANG-001. New keywords `import`, `from`, `version`, `digest`, `parts`, `for`, `in`, and `keyed`, and the predefined `len` callable apply only to `0.2`. A spelling newly reserved here retains its old treatment in a `0.1` program. The grammar accepts broad expression forms whose type, access, effect, and domain restrictions remain mandatory.

An import has this form, where the all-zero digest illustrates the token shape only and must be replaced by the actual dependency source hash:

```ontokin
import mech @ "mechanics" from "example.mechanics" version "1.0.0"
    digest "sha256:0000000000000000000000000000000000000000000000000000000000000000";
```

The alias `mech` provides qualified references such as `mech.Finger`, `mech.offset(...)`, and `Ref<mech.Finger>`. Only the imported module's public definitions are accessible through that alias. Internal references in an imported class/function bind in its original declaring module; they do not capture the importing module's names or the caller's scope. Class-member visibility retains the baseline public/private rules.

An import's key is a declaration identity in its source namespace. It does not become the imported class's nominal identity. Import aliases, ordinary definitions, and predefined names must not collide in the same lookup scope. Imports are not wildcard namespace merges, and aliases do not implicitly re-export another module's interface.

### 3.2 Exact closure and content identity

An import identifies one package ID, exact version, and source digest. Package IDs match `[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*` and contain at most 128 ASCII characters. A version contains exactly three nonnegative decimal components separated by periods, with no leading zero except the value zero itself and each component at most 2,147,483,647. Ranges, prerelease labels, implicit latest selection, and multiple versions of one package ID in a valid closure are outside this slice. The version label selects declared content; its numbering does not certify API compatibility or substitute for the exact digest and validation.

The explicit bundle payload is `ontokin.bundle/0.1`:

```json
{
  "schema_version": "ontokin.bundle/0.1",
  "entry": {"filename": "main.ok", "source": "<exact entry source text>"},
  "modules": [
    {
      "package_id": "example.mechanics",
      "version": "1.0.0",
      "filename": "mechanics.ok",
      "source": "<exact definition-module source text>"
    }
  ]
}
```

The angle-bracket text above describes a JSON string value to replace; it is not valid complete OntoKin source. One package supplies one source module. Resolution is by package ID/version/digest from the supplied bundle, not by a source filename used as an ambient filesystem path.

The [bundle schema](construction-v0.1/bundle.schema.json) fixes the JSON shape. Cross-unit uniqueness, actual byte caps/hashes, import closure, and semantic validity require the additional checks here; JSON Schema alone does not establish them.

For every structurally valid supplied bundle, compute its program identity **before source parsing or import resolution**. A malformed source module, missing import, or mismatched content pin must still have a retained candidate identity and exact inspectable source bytes. Successful resolution is not a prerequisite for naming a rejected candidate.

Each unit has a `source_id`: `entry` for the entry, or `package:<package_id>@<version>` for a package. Its `source_revision` is `sha256:` followed by the lowercase SHA-256 of the exact UTF-8 source bytes. There is no line-ending or Unicode normalization. Build this manifest from all supplied units, sorting the `units` array by ASCII `source_id`:

```json
{
  "schema_version": "ontokin.bundle/0.1",
  "entry_source_id": "entry",
  "units": [
    {
      "source_id": "entry",
      "package_id": null,
      "version": null,
      "filename": "main.ok",
      "source_revision": "sha256:<exact source hash>"
    },
    {
      "source_id": "package:example.mechanics@1.0.0",
      "package_id": "example.mechanics",
      "version": "1.0.0",
      "filename": "mechanics.ok",
      "source_revision": "sha256:<exact source hash>"
    }
  ]
}
```

Canonical JSON uses recursively sorted object keys, unescaped Unicode scalar characters, no insignificant spaces, comma/colon separators, and no non-finite values. The identity is:

```python
canonical = json.dumps(manifest, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":"), allow_nan=False).encode("utf-8")
program_revision = "sha256:" + hashlib.sha256(
    b"ontokin.bundle/0.1\0" + canonical
).hexdigest()
```

Every manifest leaf is a string or null, so there is no numeric JSON canonicalization ambiguity. Filenames are included exactly for diagnostic context. Reordering the supplied module list or JSON object members leaves the identity unchanged; changing a filename, source bytes, package ID, or version changes its manifest and identity. Entry import pins are included through the entry's source bytes, and transitive pins through their declaring source bytes. Exact byte identity is deliberately distinct from semantic equivalence.

Resolution then checks each import against the supplied version and actual source hash, traverses the dependency DAG, and requires the supplied package set to equal the reachable closure. Extra modules, missing modules, mixed pins for one package, incompatible declarations, and import cycles fail explicitly. It never silently fetches a replacement, uses an ambient source search path, or substitutes cached content with another hash. The program revision is not a Git commit, an evaluator run, an artifact hash, or a renamed `0.1 source_revision`.

### 3.3 Nominal definitions and source provenance

An imported definition keeps a nominal identity derived from its **package ID, module key, and definition key**. Module keys are unique in their package namespace, not globally across unrelated packages. Entry definitions occupy a distinct entry namespace. Changing a local alias or lexical display name does not create another nominal class. The program's definition-revision metadata additionally identifies the exact package version and defining source revision. Updating a library pin can change a definition's implementation while leaving its declared stable key; clients must therefore compare the recorded revision as well as the name/key. One exact pin per package ID in a valid closure prevents two simultaneously resolved versions from ambiguously claiming that nominal identity.

The `0.2` nominal identity tuples are explicit:

| Element | Identity |
| --- | --- |
| Entry module | `["entry", module_key]` |
| Package module | `["package", package_id, module_key]` |
| Class/function definition | Its module identity followed by `["definitions", declaration_key]` |
| Definition member | Its enclosing definition identity followed by the existing member declaration-key steps |
| Object occurrence | `[entry_module_key, scene_key, root_object_key, ...ordinary_part_keys]` |
| Generated occurrence | Its owner's occurrence identity followed by `[collection_key, input_entry_key]` |

Version, source digest, filename, and alias are separate provenance fields. They are not inserted into nominal identity. These are new `0.2` definition identities; existing `0.1` definition tuples remain unchanged. The object occurrence rule continues to identify objects in the sole entry scene, even when their classes were defined in a dependency.

The implementation must not flatten all files into fabricated concatenated source locations. Every source span refers to its actual file and original UTF-8 byte offsets. Diagnostics involving an import and its target may need related locations from two files. The containing program revision supplies their common context, while each location retains its own source identity.

### 3.4 Editable file transport and exact diagnostic names

An optional `ontokin.files/0.1` manifest follows the [file-manifest schema](construction-v0.1/file-manifest.schema.json) and provides the same entry/module descriptors but replaces each `source` string with a `path`. The loader reads those files and seals their exact bytes into the bundle above. `path` is a relative POSIX path with no absolute prefix, backslash, empty segment, `.` segment, or `..` segment. Its resolved target, including symlink resolution, must remain within the manifest directory. A rejected transport path cannot trigger an unrelated file read.

Paths locate the editable inputs; they are excluded from the sealed program hash. Each explicit `filename` remains a separate nonempty diagnostic label of at most 1,024 UTF-8 bytes, containing no NUL or control characters. It is retained and hashed exactly without Unicode normalization. Moving an unchanged manifest/file tree while preserving descriptor filenames therefore need not change program identity. Changing the diagnostic filename does change identity, even if the source bytes stay equal. Source IDs, rather than filename spelling alone, distinguish the units in edits and diagnostics.

A sealed inline bundle is an immutable snapshot of those sources, not a second editor state that silently tracks later filesystem changes. Loading a file manifest reads and verifies a new snapshot. If both editable files and an earlier sealed bundle are retained, their identities must be compared; an older sealed copy cannot be presented as the revised files' current program.

## 4. Immutable keyed construction inputs

`Keyed<T>` is a finite immutable association of explicitly authored stable keys to values of one declared element type. Copying the value does not create objects or share mutable simulation state. Keys establish identity; a numeric ordinal or current iteration position does not substitute for an authored key.

Keys use the baseline stable-key domain `[A-Za-z0-9][A-Za-z0-9._-]{0,63}`. A duplicate key is invalid even when both values compare equal. Looking up an absent key fails explicitly; there is no automatic null, default member, or placeholder part. Values must satisfy their declared type and quantity dimensions. The typed literal `keyed<T>{"key": expression, ...}` retains the element type even when empty: `keyed<Length>{}` is a valid typed empty form. `len(value)` returns its entry count as `Int`; this overload does not introduce other collection or string operations. Expression lookup `value[string_expression]` reads an existing value without mutation.

Keys iterate in **canonical ASCII order**, independent of source literal ordering. A changed literal order may change exact source bytes and hence revision identity; it must not rename objects or alter the mathematical result of unaffected entries. No seeded randomness is added by this milestone, and stable keys alone do not establish a random-stream contract.

Authored inputs are **flat** `Keyed<T>` values. Permitted leaf types are `Int`, `Real`, `Bool`, `String`, quantity types/aliases, the baseline numeric `Vec3<Q>`, `Vector3<Q>`, and `Range<Q>` forms, and `FrameRef`, `Point3`, `Rotation`, `Pose`, and `Color`. Existing component-type and frame rules still apply; the whitelist does not create a new valid baseline generic instantiation.

Nested `Keyed`, `Geometry`, `BodyModel`, `Action`, and authored object-reference collections are unsupported. A generated collection has the intrinsic, derived, read-only type `Keyed<Ref<C>>`. That type identifies its lookup results; it is not available as an authored literal, parameter, return, or `let` annotation for constructing/storing arbitrary reference collections. Ordinary individual references retain their baseline meanings. Bounded input must also yield bounded inspection output under section 8.

An authored `Keyed<T>` can be copied, passed, or returned at the same element type. Individual literal entries use the baseline permitted conversion into declared `T`; the language does not add implicit whole-collection covariance or element conversion. Alias-resolved equal nominal/dimensional types retain their baseline equivalence. Keyed equality, ordering, arithmetic, mutation, concatenation, and general collection methods are unavailable. The supplied operations are typed literals, immutable use, `len`, read lookup, and the declarative generated-part form.

## 5. Declarative generated parts

### 5.1 Expansion and identity

A collection declaration specifies an owning class, its own stable declaration key, a keyed input expression, immutable key/value bindings, and a homogeneous part class with a reusable initializer. The form is:

```ontokin
public parts fingers @ "fingers": mech.Finger
    for (key, offset) in self.mounts {
    parent_frame = self.frame;
    mount_offset = offset;
    length = self.length;
}
```

This is a class-member fragment: `mech.Finger` and its public parameters must be defined, and `self.mounts`/`self.length` must have compatible declared types. The grammar does not infer those definitions from the fragment. `key` has type `String`; `offset` has the input's element type. It creates one independent occurrence for each input key. Generated children may themselves contain ordinary or generated parts within the same finite construction limits.

The two binder names must be distinct and follow the baseline lexical/predefined-shadowing rules. They are immutable locals for that initializer, not new object members or derived stable keys. The literal input key, rather than the spelling of either binder or an iteration ordinal, identifies the child.

The generated identity path is the owner's occurrence identity followed by the collection declaration key and then the input key. A generated descendant appends its ordinary part or further collection/key steps. The collection is an inspectable declaration/grouping, **not an Object**, frame, body, attachment, or intermediate physical owner. Generated parts belong physically and structurally to the owning object.

Display paths must distinguish member steps from literal key steps. For example, the conceptual path `rig.parts["left.eye"].tip` contains the single key `left.eye`, not two nested fields. The final source grammar and the inspection path representation must preserve that distinction. Dotted-string splitting must not reinterpret legal key content.

Adding one input key adds that occurrence and its owned descendants. Removing one key removes those occurrences in the new definition revision and requires surviving references to remain valid. Reordering keys leaves surviving identities unchanged. Old runs remain pinned to the older program; generation never inserts or removes bodies from a running evaluation.

### 5.2 Input resolution and override order

Collection shape resolves **after** the owning occurrence's final input overrides and inherited defaults, and **before** the collection's children are constructed. A public outer initializer can change a descendant's keyed input using the baseline outermost-explicit-override precedence. Per-key child overrides must bind before that child's own generated collections resolve.

Generation cannot first expand a default collection and then mutate/re-expand it when an outer override arrives. That would make source order influence shape, duplicate identities or mass, or leave references to removed children. An implementation may use lazy tasks or another architecture, but it must produce the same single resolved definition and detect dependency cycles explicitly.

The reusable collection initializer evaluates in the owner's lexical scope plus the immutable key/value bindings. The child retains its own class defaults and independent state. As in the baseline part initializer, assignment targets name the child being initialized; right-hand `self` continues to name the enclosing owner. The child's own class defaults and methods subsequently use the child's `self` and their original declaring module/class. The generated body does not gain a mutable child `self` or capture a caller's scene scope.

Precedence follows the existing outermost-explicit rule: child defaults are overridden by reusable ordinary/generated part initializer assignments, which are overridden by enclosing occurrence initializers and their per-key assignments. More distant explicit occurrence overrides take priority over inner reusable defaults, independent of declaration order. An override for a key absent after final shape resolution is an error; it never creates a new child or silently drops the write.

### 5.3 Purity, dependency validity, and empty collections

Collection shape must be computable from permitted immutable definition inputs and pure expressions without reading a current physical state or requiring the generated collection's own children to exist. Circular shape/value dependencies fail explicitly. Resource exhaustion is not evidence that a logical cycle exists.

Shape may not depend on **any generated collection or occurrence** in its actually evaluated pure dependency closure. This includes obtaining a generated collection view, `len(view)`, membership/index/reference lookup, reading an occurrence's properties, and consuming a cached scalar/leaf derived from those reads. The rule applies even if the collection is empty or already expanded. Generation inputs must be permitted flat keyed leaf values, not another generated reference view.

For a generated owner’s nested collections, direct use of that owner’s own final immutable `self` parameters/derivations, body-bound inputs, and `self.frame` identity is permitted. It does not itself obtain or traverse a generated occurrence. This permitted lexical `self` origin also survives passage through a pure helper parameter and valid nominal `Ref` coercion: a helper may read an enclosing owner’s immutable inputs supplied directly as `self` while initializing its child. The permission belongs to that reference origin, not every reference to the same object. A reference obtained by traversing a generated collection or occurrence does not gain it by passing through the same helper. Any prohibited collection/occurrence lookup in the evaluated dependency closure of those values remains prohibited, including through an outer initializer, cached scalar, or copied parameter. This distinction permits C07 without allowing assignment, coercion, a helper call, or memoization to erase dependency provenance.

This preserves the baseline's lazy `if` and short-circuit Boolean semantics: an unused branch is not evaluated, while both branches remain type/access checked. A pure helper call or memoization cannot hide a prohibited dependency. Cached values must retain the actual selected-branch dependency provenance, and shape validation checks that closure even when it performs no fresh generated lookup. Static checking of an empty collection body uses types and access rules, not fabricated concrete children or numeric sample values.

An empty collection creates no parts, but the declaration, part class, body expression types, visibility, and allowed assignments must still be valid. Empty input does not make an invalid body valid. Static recursive class composition through ordinary or generated parts is rejected, including when a particular input is empty; this milestone does not supply a separate finite-recursion language feature.

### 5.4 Existing relationships and dynamics

Reusable generated component classes can contain the baseline's supported sites, following, prescribed joints, and actions, with explicit references and typed parameters. Generated ownership itself supplies no following or attachment. Each expanded assembly must satisfy the same incoming authority, connection compatibility, cycle, mass, and physical-support rules as an explicitly written assembly.

The milestone does not require a separate generator for arbitrary joint/event declarations. A homogeneous generated part can encapsulate its supported internal mechanics. General dynamic joints, closed mechanisms, contacts, force actuation, and new controllers remain unsupported unless a separate profile adopts them.

## 6. Public per-key overrides, inspection, and repair

A source initializer may traverse public ordinary parts and public keyed collections to reach a public parameter of a particular generated occurrence. For example, `fingers["middle"].length = 0.75[m];` changes one public parameter through an existing public collection. Left-hand key steps use string literals; arbitrary computed lvalue keys are outside the profile. Expression lookup may use a string-valued expression. Each member and key step must resolve and satisfy access rules. Private traversal, missing keys, duplicate writes at the same precedence, writes to derived properties, and nested writes to prohibited built-in motion/relationship fields fail as in the baseline.

An occurrence generated from a shared collection body does not own private writable bytes in that body's definition. Inspection must separately identify the collection declaration span, imported class/default span, keyed input provenance, and an available public initializer target in the selected enclosing occurrence. A repair that changes only one occurrence inserts or edits that public override. A change to the shared generator or library explicitly targets its defining source and reports the dependent scope.

The bounded inspection result must identify the program revision, defining and authored source revisions, stable element identity, owning object, collection key/input key, resolved nominal class, effective values and origins, and valid source edit target. A generated record with no distinct declaration span says so; it does not fabricate unique source offsets. Schema-valid metadata is not sufficient unless its identity, location, and values agree with actual source and constructed state.

Changing a dependency or keyed input produces a new program revision. Existing cursors, ordinary runs, diagnostic runs, and artifacts retain their old context and cannot be relabeled as current. A rejected candidate bundle remains available for diagnosis without replacing the accepted bundle.

## 7. Program-level agent and delivery boundary

### 7.1 Agent version separation

`ontokin.agent/0.2` must explicitly distinguish a **program revision** from a **source revision**. A multi-file patch identifies its source ID/hash, UTF-8 byte span, exact expected text, replacement, and target element within the expected accepted program. All patches and any manifest/pin changes form one candidate. Acceptance must recheck the whole expected program head at commit, not merely the edited file.

The binding is a separate Python `ProgramAgentService` and:

```bash
python3 -m ontokin agent --protocol ontokin.agent/0.2 --store DIR
```

It uses an independent `program-agent.sqlite3` store/schema in the chosen directory and may share the tested lifecycle machinery with the existing service. It does not silently migrate or reinterpret `0.1` projects. The existing `AgentService` and `ontokin.agent/0.1` remain supported under their original contract.

The revision fields are `program_revision`, `accepted_program_revision`, and `expected_program_revision`. `create` accepts an inline bundle. Each source edit patch adds `source_id` and that unit's `source_revision` to the existing `element_id`, `start_byte`, `end_byte`, `expected_text`, and `replacement` preconditions. Explicit module addition/removal records are part of the same atomic candidate. Replacing an existing module's source uses keyed source patches or an explicit replacement conditioned on its old `source_revision`; an add cannot silently overwrite it. A library change and all affected exact import pins must validate together.

The existing durable local lifecycle remains applicable: canonical request identity, no duplicate effects on retry, no changed payload under one request identity, truthful unknown outcomes/tombstones, cooperative cancellation and budgets, immutable candidate/accepted distinction, matching run/implementation context, bounded cursor pinning, and explicit requested stages. Full-stage validation still covers the authored horizon; prefix evaluation remains a separate operation.

Runs, cursors, artifacts, and their result pages bind to the whole program and loaded implementation identity. Diagnostics and per-source edits additionally identify the exact member source. Discovery exposes the construction built-ins and can inspect a supplied or retained library's public interface in program context; a public definition's existence does not claim that every use is supported. The complete `0.2` operation schemas and storage implementation remain an engineering gate. Interpreting an old `0.1 source_revision` as a whole-program revision is prohibited.

### 7.2 Named GLB delivery

The new named destination is **`ontokin.glb/0.2`**, extending the [OK-ENG-002](../engineering/OK-ENG-002-3d-scene-animation-export-and-visual-validation.md) geometry, world-pose baking, and numerical-validation contract with bundle/source-map provenance. The existing `ontokin.glb/0.1` retains its prior single-source behavior. A bundle delivery request must name `ontokin.glb/0.2`; it cannot silently pass through an old target with incomplete provenance.

Construction feeds the same world-pose and mechanical semantics into the exporter; the report and artifact still identify the authored `construction-0.1` profile and complete pinned program. Delivery metadata retains the entry, program identity, exact dependency/source identities, generated occurrence identities, and source mappings under the new contract. Neither a manifest nor a glTF metadata label establishes that the actual bytes contain the required objects or motion; acceptance compares decoded/loaded geometry and world poses with independently specified expectations.

The editable source bundle remains authoritative. A GLB contains generated geometry and recorded motion with the declared metadata, not a reconstructable library/generator implementation or live OntoKin solver. Loss reporting must say which recipe, comments, types, parameter relationships, dependency source, and mechanical behavior are not reconstructable from the artifact. Generic unnamed `delivered` remains unsupported.

## 8. Limits, diagnostics, and exclusions

The adopted maxima are:

| Resource | Maximum and scope |
| --- | --- |
| Source units | One entry plus 16 dependency modules. |
| Import depth | Eight dependency edges from the entry. |
| Exact source bytes | 2,000,000 UTF-8 bytes across all supplied sources; no individual source can exceed that total. |
| Tokens | 200,000 across the complete bundle. |
| Keyed entries | 256 entries per flat keyed value or generated collection. |
| Constructed objects | 1,000 total ordinary and generated object occurrences, counting roots and descendants once. |
| Ownership depth | 64 ownership edges; a collection grouping adds identity steps but zero ownership/frame/body depth. |
| Operations | 100,000 request-wide semantic/dependency/construction work operations. |
| Logical value materialization | 100,000 entries, including logically repeated immutable values when materialized/serialized; shared backing storage is not an exemption. |
| Encoded result envelope | 4 MiB of UTF-8 JSON, checked through bounded materialization rather than first allocating an unbounded string. |
| Active elapsed work | 30,000 ms, with the existing cooperative checkpoint semantics. |
| Agent element identity | 256 key segments in `0.2`, allowing generated collection/key steps plus module, scene, root, and member context. |
| Display/structured query path | 32,768 UTF-8 bytes in `0.2`. |

Smaller request budgets may be accepted where exposed by the agent contract; a request cannot raise the profile maxima silently. Existing `0.1` limits retain their previous meaning. The object/depth caps apply before host recursion or allocation failure; static recursive composition remains a distinct invalid-definition check. Parser/value nesting must also fail explicitly within the bounded operation/source contract rather than leak a host exception.

Capped source input does not on its own bound generated or serialized output. Work limits count the complete attempt, including imported units and repeated construction/inspection, not a newly reset budget for each module or child. Strings and repeated immutable leaves still consume logical/encoded output budget. A result truncated for pagination identifies its continuation; a budget failure cannot masquerade as a complete shorter result. Existing separate GLB byte/mesh/keyframe/probe limits remain applicable to binary delivery.

Elapsed limits and cancellation remain cooperative. Expensive kernels checked only before/after can overshoot a deadline; these maxima do not promise hard real-time preemption, an operating-system memory sandbox, or a universal latency result. Actual timings require identified measured fixtures.

Reuse the registered diagnostic distinctions where applicable: syntax/name/type/unit/access/identity errors, circular definitions, support unavailability, numerical failure, stale contexts, and resource exhaustion. Bundle context and cross-file related locations need a versioned extension rather than overwriting a diagnostic's source identity with another file's hash. A missing dependency cannot be reported as successfully constructed with missing children, and exhausted generation cannot be called an empty valid collection.

This milestone excludes network package installation or semver range selection; imported executable scene initialization; arbitrary host extensions; mutable collections; general loops/recursion; runtime allocation/removal; keyed generators for arbitrary relation/event declarations; random sampling; automatic compatible part replacement; new shapes, textures, skinning, or deformation; new physical solvers/controllers; multi-user permissions/distributed storage; hard real-time preemption; and a claimed agent productivity improvement. These exclusions bound the next release and do not remove the requirements from GOAL.

## 9. Acceptance cases and evidence gate

The following fixture cases are requirements for implementation, **not passed results**. The language implementer and integration owner must freeze complete source bundles, exact manifests/hashes, declared settings, expected IDs/values/poses, and diagnostics before evaluating the release. The `C01`–`C20` identifiers will be synchronized with the companion manifest.

| Case | Category | Required observation |
| --- | --- | --- |
| C01 | Positive module reuse | Two entry objects instantiate one pinned library class; internal parts, parameter overrides, references, and motion state remain independent. |
| C02 | Namespaces and composition | Two libraries expose the same lexical class/function names through distinct aliases. Qualification resolves each correctly; alias rename retains the imported nominal identity. |
| C03 | Transitive closure | An entry imports A, A imports B; a clean offline resolver uses exactly the supplied pinned bytes and reports the full dependency closure. |
| C04 | Positive keyed construction | One generator creates three explicitly keyed asymmetric parts. Expected identities, dimensions, poses, ownership, and own/aggregate mass match a separately authored reference assembly. |
| C05 | Key stability | Reorder inputs, insert one key, then remove another. Surviving occurrence/descendant identities and effective inputs remain unchanged; only intended membership changes. |
| C06 | Empty and singleton boundaries | Empty and one-entry inputs have declared types, exact counts and mass; valid empty generation produces no phantom object/frame/body. Invalid body types/access still fail when empty. |
| C07 | Nested final-input composition | An outer initializer changes a child's keyed input before nested construction. No default-only child survives, no child is duplicated, and final references/values resolve once. |
| C08 | Scoped per-key repair | Change one generated public parameter through an occurrence initializer. Siblings and shared library bytes remain unchanged; inspection identifies the override and its origin. |
| C09 | UTF-8 and candidate source | A rejected per-key unit edit reports the actual file/hash and candidate byte span, preserves accepted program bytes, and can be repaired against the accepted head. |
| C10 | Exact pin failure | Absent file, wrong hash, changed dependency bytes under one name, invalid path, and undeclared dependency each fail explicitly without ambient or network fallback. |
| C11 | Module validity failure | Import cycle, conflicting package pin/definition identity, incompatible version/profile, imported scene, or forbidden import-side effect fails before construction. Unrelated packages may reuse a module key without collision. |
| C12 | Key/type failure | Duplicate/invalid/missing keys, wrong element type/unit, and an unsupported keyed nesting/type form each return the specified error rather than silently coerce or omit an entry. |
| C13 | Access and identity failure | Private traversal, generated shared-span write, same-level duplicate override, and nominal replacement under an unchanged occurrence key fail without partial acceptance. |
| C14 | Shape dependency and cycle boundary | Valid lazy pure inputs preserve baseline branch semantics. Prohibited evaluated shape reads, cyclic derivation, and recursive composition—including an empty generated edge—fail distinctly from resource exhaustion. |
| C15 | Resource boundaries | The supported maximum and one-over limit are tested for files/bytes, keyed entries, generated objects/depth, dependency work, and serialized output. Failure preserves accepted source and does not claim a partial complete assembly. |
| C16 | Mechanical composition | Generated components with prescribed internal following/joints move independently within a moving owner; world transforms and mass match a written reference with no double motion. |
| C17 | Release composition | A generated sphere initially carried through an explicit supported grip releases with the existing world-state transfer and gravity trajectory; ownership alone does not keep it attached. |
| C18 | Program revision and lifecycle | Change a dependency pin through one atomic candidate; stale expected heads, old cursors/runs/artifacts, retries, cancellation, and independent-process recovery retain the specified program context. Existing `0.1` operations still pass their original cases. |
| C19 | Deterministic identity and invalidation | Equivalent source-map ordering follows the adopted canonical hash rule; changing any closure bytes/pins changes the required revision. Old results retain the old identities and are not presented as new output. |
| C20 | Actual versioned delivery | Export and retrieve the generated assembly, verify source/program/artifact hashes and authored profile, validate glTF, compare imported geometry and motion, and visually inspect the same artifact. Unsupported output and lost recipe information are reported. |

### 9.1 Complete representative source and independent expectations

The [Rack entry](construction-v0.1/01-keyed-rack/main.ok) and [hinge component module](construction-v0.1/01-keyed-rack/hinges.ok) supply a complete two-source fixture, retained both as an editable [file manifest](construction-v0.1/01-keyed-rack/program.files.json) and sealed [inline bundle](construction-v0.1/01-keyed-rack/program.bundle.json). The entry pins `example.hinges` version `1.0.0`. That public module provides `three_mounts` and `Finger`; `Finger` contains a private `Blade`, supported mounting follow, prescribed hinge, and pure `bend_to` action method.

The first Rack uses three mounts and overrides only `fingers["middle"].length` to 0.75 m. The second supplies five mounts and retains the 0.6 m default. The first Rack moves at 0.2 m/s along world +Y for two seconds while its selected middle hinge turns through 45 degrees during the first second. The second Rack remains fixed. These are primitive mechanical components, not a claim of a complete hand or controller.

The following values are **independently calculated fixture expectations**, not observed runtime results:

| Property | Exact expected value |
| --- | --- |
| Authored objects | 18: two Racks, eight Fingers, eight owned Blades. Generated collection groups add zero objects. |
| Relationships | Eight mounting follows and eight prescribed hinges; no implicit ownership-based following. |
| Rack box full dimensions | First `(0.1, 1.8, 0.1)` m; second `(0.1, 3, 0.1)` m. |
| Finger sphere radius | 0.06 m for every occurrence. |
| Blade box full dimensions | Selected first middle `(0.75, 0.08, 0.08)` m; every other Blade `(0.6, 0.08, 0.08)` m. |
| Own and aggregate mass | Zero: the fixture declares no body model. It tests prescribed construction/motion, not a nonzero mass model. |
| Selected Finger identity | `["keyed-rack", "demo", "first", "fingers", "middle"]`; its Blade appends `"blade"`. |
| First Rack / middle Finger at time t | World position `(-1, 0.2t, 0)` m for `0 ≤ t ≤ 2`; identity orientation. |
| Selected Blade angle | World +Z rotation `θ(t) = (π/4) min(t, 1)` rad over that interval. |
| Selected Blade center | `(-1 + 0.375 cos θ(t), 0.2t + 0.375 sin θ(t), 0)` m. |
| Unchanged second middle Finger / Blade | World positions `(1, 0, 0)` m and `(1.3, 0, 0)` m; identity orientations. |

At 1 s after the boundary, the selected Blade center is approximately `(-0.7348349570550448, 0.4651650429449553, 0)` m and its angle is π/4. At 2 s the X coordinate/angle are unchanged and Y has increased by 0.2 m. The machine-readable [expected.json](construction-v0.1/01-keyed-rack/expected.json) retains all 18 object identities, ownership, geometry, and closed-form poses at 0, 0.25, 0.5, 0.75, 1, 1.5, and 2 s. Its 126 world-pose expectations, including exact event/completion boundaries, check combined translation/articulation rather than only a favorable endpoint. It sets evaluator position/rotation tolerances of 10⁻⁹ m/rad, geometry dimension tolerance of 10⁻¹² m, exact zero mass, and the inherited named-delivery tolerances. The source's private Blade remains inspectable through authorized diagnostic inspection without exposing its definition as a public source type or granting a shared writable occurrence span.

Editorial byte/hash checks confirm that the two sealed `source` strings equal the companion `.ok` bytes exactly and that the authored import digest matches the library. The entry source revision is `sha256:443328e2a2e3f2e68245fa1e725b518187aa446ecd7ee3de4675e006cf4e666a`; the module source pin is `sha256:1516e53179a7b9deecf593ab48afdcd72fba8124ea77868327c25a28a654681a`. Their 3,619 total UTF-8 bytes produce program revision `sha256:c77d102a4b201d3c3cce6cbdc73c38eedf0bb1dfca7c9843a92d697cc0c7e082` by section 3.2. These are static source-identity checks; no parser, construction, evaluator, or destination pass is inferred from them.

### 9.2 Implementation and release evidence gate

The release gate requires the old 43 source cases, A01–A10, Python suite, and identified GLB/viewer regression to retain their meanings and pass. New evidence must execute the `0.2` interface and construction cases; converting a new program manually to old `.ok` does not demonstrate module resolution, source mapping, keyed construction, or atomic bundle editing.

Numerical comparisons inherit the named evaluator/exporter tolerances where semantics are unchanged; exact keys, membership, revisions, hashes, source bytes, and ownership use exact comparison. Reference assemblies and expected values must be specified independently of the generator's reported success. Delivery requires real loaded geometry/pose evidence and a reviewed capture, with destination/tool versions disclosed.

Implementation reports must record package version/digest, source-bundle revision and all per-file hashes, fixture manifest, source/dependency settings, budgets, expected and observed outcomes, artifact identities, actual local/CI results, and unresolved limits. A proposal, schema, parser acceptance, or favorable screenshot cannot substitute for those checks.

## 10. Product mapping and remaining scope

| Source requirements | Contribution of this bounded contract | Remaining limitation |
| --- | --- | --- |
| PRD LNG-001, LNG-004–006, LNG-010–012, LNG-018–019 | Versioned modular definitions, typed keyed values, declarative finite construction, name/effect/default rules. | General algorithms, value records, unrestricted collections, richer component interfaces, and a stable third-party package ecosystem remain future work. |
| PRD LNG-013, OBJ-001, OBJ-006–007, OBJ-012; CAP-01–03 | Explicit key stability, independent repeated instances, scoped overrides, finite arbitrary part counts. | No random streams, runtime cloning, compatible replacement, or unrestricted recursive generators. |
| PRD LNG-015, AGT-003–009, AGT-017–018; CAP-14–15 | Exact source authority, per-file diagnostics, bounded generated inspection, atomic program edits, revision/run/cursor integrity. | This is a local service binding; permissions, collaboration policy, and general incremental regeneration are not certified. |
| PRD OBJ-002–003, OBJ-011, OBJ-013–015; CAP-05–08, CAP-10–12 | Generated parts preserve existing ownership, physical/following distinctions, mass, mappings, and release rules. | New mechanics, forces/contacts, rich deformation, and supported purposeful control remain outside the profile. |
| PRD EXP-008, EXP-010, EXP-016, VAL-002, VAL-008–011; CAP-16 | Bundle provenance, generated identity mapping, explicit loss, source/runtime/target consistency checks. | No complete recipe reconstruction from GLB, second destination certification, live engine behavior, or full appearance contract. |
| PRD NFR-001–002, NFR-006–007, NFR-010, NFR-012; DOC-001, DOC-003–004, DOC-009 | Exact resolution, bounded work and output, offline ordinary execution, durable source/evidence, finite acceptance fixtures. | No universal rendering determinism, hard real-time guarantee, distributed durability, package-license certification, or calibrated product-wide scale claim. |
| CAP-04, CAP-13, CAP-17–18; PRD section 9.2 | A reusable construction step toward richer assets and larger scenes. | Complete creatures, machines/vehicles, locomotion, flight/swimming, vegetation, terrain, fluids/deformables, appearance, and live delivery remain explicit GOAL obligations. |

The requirement sources are [OK-PRD-001](../product/OK-PRD-001-product-requirements.md) and [OK-CAP-001](../product/OK-CAP-001-modeling-motion-and-object-structure.md). The mapping describes intended progress, not completion of the cited full-product rows. It does not alter their historical review status or the original coverage register.

## 11. Adoption, clarifications, and present evidence

**Version 0.1.1 clarification, October 18, 2026:** section 5.3 makes the generated owner’s direct immutable input context explicit, including lexical `self` passed through pure helper parameters and valid nominal `Ref` coercion. The initial wording “any generated occurrence” was too broad when read as also forbidding a generated child’s own final inputs for C07. The clarification permits those inputs while retaining forbidden-lookup provenance; nested positive, helper/coercion positive, view-derived helper negative, and tainted-own-input negative cases must cover it. No prior implementation result is relabeled.

The adopted language choices are explicit above: pinned package-qualified modules; candidate identity before parse/link; canonical source manifest/hash; flat keyed leaf values; intrinsic generated reference views; typed literal-key lvalues; final-override-first expansion; generated dependency provenance through memoization; static recursive-composition rejection; and finite construction/output limits. The integration owner adopted this version with its complete EBNF, bundle/file-manifest schemas, representative source bundle, and predetermined C01–C20 expectations on October 18, 2026, before production implementation began. Complete executable negative/boundary/composition test bodies may be written during implementation; they must be fixed before measuring their release outcomes. Implementing the contract does not require pretending those unwritten tests already exist or pass.

The corresponding `ontokin.agent/0.2` request/response/diagnostic extension, storage/migration behavior, catalog, and exporter provenance contract must then be explicit before their implementation is claimed. Their version distinction and required effects are fixed by sections 6–7; this language document does not substitute a table for executable protocol schemas. Update current navigation and STATUS without editing historical core semantics into a false account of prior support.

**Current evidence: adopted contract, complete source/schema companions, independent numerical expectations, and the editorial byte/hash checks above.** No `construction-0.1` conformance count, performance claim, executed module import, generated animation result, `ontokin.agent/0.2` service result, or remote CI success is asserted here. Implementation proceeds on `work/construction-0.1`; the integration owner records later measured results separately. [STATUS.md](../../STATUS.md) remains the recovery record for the actual next unmet gate.
