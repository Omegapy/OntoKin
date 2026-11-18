# C266 comparison design audit

## Recommendation

Implement a source/program/object association component as one bounded prerequisite to `compare_hinges(source_files, raw)`, unless the Director explicitly selects and tests the complete comparator. The raw C261 reader deliberately accepts sparse or contradictory nested provenance. C265 supplies correct independent source hinge facts, but its public object projection does not itself reconstruct every repeated artifact mapping claim. Matching numeric hinge fields and calling C257's ownership comparator would leave material C260 binding obligations unmet.

A prerequisite should be named accordingly (for example `bind_hinge_inputs`) and never return a qualified hinge set or claim complete source/artifact hinge agreement. A complete comparator can use the same association layer and then add the simple exact field/set comparison. Historical `read_bound_endpoint` stays separate in either choice. Do not weaken C260 or mutate its pinned dependencies to fit the implementation.

## Read set and actual APIs

Inspected package root AGENTS/GOAL, C260 CONTRACT/INPUTS/FIELD-ORIGINS/CONTROL-PLAN, complete C265 `source_hinges.py`, C265 README/RESULTS, complete C261 `hinge_glb.py` and CONTROL-COVERAGE, and relevant C257 lexical/module/occurrence/manifest/comparison utilities. C252 DECISION and C261 README/RESULTS were absent from the selected ZIP read-set; they were read from the surviving `/workspace/scratch/b4cbf4ea8454/OntoKin` checkout instead. The Director should bind those reads to current main separately.

- `docs/engineering/localized-repair-c265/source_hinges.py`: `observe_source_hinges(source_files)`, source-only facts under `ontokin.c265.source-hinge-observation/0.1`. Frozen source SHA-256 `04bea0f7c5f82a3e3e74610d3ee98755f44ed0905566c00eb063647e31abbf9e`.
- `docs/engineering/localized-repair-c261/hinge_glb.py`: `observe_glb_hinges(raw)`, untrusted raw claims under `ontokin.c261.glb-hinge-observation/0.1`. Frozen SHA-256 `6167b3a56a2b1a600812340d85ee02eaa3b6399801d585a758333aabcfaa5e08`.
- `docs/engineering/localized-repair-c257/ownership.py`: permitted pinned lexical/module/occurrence utilities. Frozen bytes 35,942, SHA-256 `c28b6a52e0d3575204e138986e5b1dfa57081943b8e194be0613fc33a28210f1`. `manifest_for` builds the canonical bundle manifest and revision. `parse_module` provides names/keys. The source identity expansion supplies declaration/definition spans and generation witnesses. Its ownership/follow comparison must not supply hinge truth.

The package source snapshot is `070d18b7a5f663f51a22ecc147ce8be5290c3e0c`; live closure main supplied by the Director is `7818de1f17e379df50680cb94347ce86bcabb8a5`.

## Mandatory association obligations

1. Observe the supplied source bytes through the pinned C265 observer before promoting any artifact claim. Preserve its unsupported bare-CR comment form, numeric subset, two-file import closure and refusal bounds. Calling its `Source` internals directly without public validation/error wrapping loses boundary guarantees.
2. Independently bind complete canonical manifest and program revision, exact import digest, source unit identities, filenames, package/version, module names/keys and entry revision. Both `/extras/ontokin/source` and `/extras/ontokin/program` repeat claims. `source.uri` is only a caller locator; it is not source truth. C261 does not expose top-level module/scene or program collections in its returned excerpt, so do not silently advertise those fields as verified.
3. Join the complete source object set to actual nodes and the complete program occurrence table by full identity and exact source-rendered path. Check one-to-one sets and uniqueness. Node order is immaterial. Require actual class IDs, both declaration and definition source spans, source IDs/revisions and filenames in both node `source_mapping` and repeated program occurrence records.
4. Generated metadata needs deliberate treatment. The actual mappings also contain `root_path`, `path_steps`, `declaration_definition_id`, `generated` and `generated_ancestor`. Generated rows repeat collection path/ID/definition ID, literal key, generator input span and input-entry span. Validate all identity/span claims the chosen profile retains; merely checking that node and program maps equal each other lets both copies lie identically. C257's existing comparator does not check these additional fields.
5. Do not split dotted display paths. Legal opaque keys can contain dots, underscores and hyphens. Render paths from parsed source member/key steps, using exact JSON quoting. Derive object owner/root relationships from occurrence structure; do not derive them from an artifact path string.
6. For full hinge comparison, match exact complete joint identity and path sets, then bind each joint to the already mapped owning object/class. Use C265's explicit `ownerId` and `ownerDefinitionId`. Compare ordered parent/child path claims against complete source site records on their mapped owning objects. Match kind and exact canonical numeric values without tolerance, sign normalization, sorting or clamping.
7. Keep absent direct provenance absent. GLB has no direct joint definition/span, site table, site ID/definition/span, site pose or interface/size. These remain source-derived associations or source-only compatibility facts. Retain source byte witnesses and actual artifact JSON pointers separately in the output.

## Concrete generated-span pitfall

For original `first.fingers["lower"]`, the source key token witness is `hinges.ok` bytes `[193,200)`. The artifact `generated.input_entry` is the full key-value entry `[193,228)`. Comparing it to the key-token span is incorrect. Derive the complete entry by bounded token grouping in the actual final keyed literal, including nested commas correctly. The generator `input` is independently `[670,681)` in main.ok. The function/default/override span is another distinct witness and cannot substitute for either.

Ordinary descendants of generated objects still carry `generated_ancestor`, even though their own `generated` value is null. For ordinary child `blade`, `declaration_definition_id` is the owning class definition plus the part key, not the child's class definition. Root declaration-definition IDs are null. These are useful adversarial cases.

## Output and refusal design

Use a new typed Fault with `code`, `detail`, source/artifact origin as relevant, bounded source hashes/byte counts and bounded artifact hash/size. Preserve dependency I/O failures and malformed/resource/unsupported categories; distinguish source/artifact binding contradiction from supported hinge-field disagreement. Fail atomically with no qualified partial set. For oversized bytes, retain size without an unbounded diagnostic hash.

Successful comparison must keep `historicalInputsBound`, `sitePosesEvaluated`, `sourceValidityQualified`, `acceptedRevisionQualified`, `completeC255Semantic` and `executionAllowed` false. No accepted revision, historical hash admission, physical validity, motion/rebuild/native/model trial or comparative benefit follows. A prerequisite also keeps hinge-agreement false.

## Independent test priorities

- Both original endpoint inputs produce eighteen bound objects; full comparison produces eight hinges, one shared joint definition and sixteen source-associated sites. No historical admission flag.
- Missing/extra/duplicate object or joint, wrong owner/class, span shifted by one byte, wrong filename/hash/revision, sparse mandatory mapping, boolean/fractional span endpoints and two mutually consistent but false repeated claims all refuse.
- Independently corrupt every repeated generated key/ID/class/span claim; mutate the program occurrence and node map separately and together. Check direct keyed literals, helper-returned literals and final owner overrides. Include Unicode comments before declarations so byte offsets cannot be confused with code points.
- Joint lexical-name rename while retaining its key; key rename while retaining its name; site-name/key rename; reordered nodes/joints/keyed inputs; added/deleted legal members; opaque keys containing dots/underscores/hyphens. Deliberately paired artifacts must update all required provenance and no product exporter may construct expected answers.
- Source-only numeric change with provenance rebound but old hinge retained must reach field disagreement, not fail earlier only on stale hashes. Keep a separate stale-binding control. Paired supported values pass. Include all signed basis axes, signed zero, exact adjacent binary64 mismatches, inclusive/zero-width limits and deg/rad one-round equivalence.
- Endpoint swaps and another object's same-named site refuse; unsupported endpoint forms remain explicit refusals. Nontrivial site pose or unrelated geometry/motion values never become agreement evidence.
- Malformed bytes, duplicate JSON keys, count/length/depth boundaries, dependency pin mismatch and unreadable dependency produce typed whole-call refusal. Existing C265/C261 controls establish their original scopes only; changed comparator dependencies still need equality receipts.

Map each executed case to C260 H-group portions. H26 and historical portions of H01/H03/H04/H27 remain open without the separate historical interface. A passing binding prerequisite does not close numeric/endpoint agreement portions.

## Integration scope

Own a new C266 engineering directory, dedicated controls/evidence and task records. Keep prior source, tests, fixtures, contracts, product runtime/defaults, budgets and hosted workflow configuration unchanged. Relevant inherited observer cohorts, C253 corpus bindings, workflow structure and documentation preservation are proportionate checks for this isolated standard-library component, alongside the new independent suite. Root alone publishes shared STATUS/CURRENT and main integration.
