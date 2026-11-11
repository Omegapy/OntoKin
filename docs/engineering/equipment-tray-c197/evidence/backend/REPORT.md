# C197 common backend feasibility review

## Decision

**FEASIBILITY_PROPOSAL_REQUIRED. Do not start baseline exports or dispatch authors.**

At the reviewed C196 main commit, the standard language has native tray geometry, classes, keyed instances and GLB delivery. That does not establish the common Blender construction path required by C197. The qualified C191/C193 adapter is confined to the seven-part carriage gauge. The earlier native Blender/Python and native OntoKin workflows use different construction/export implementations.

A separately versioned static assembly mapping is needed before a tray comparison can satisfy the same-backend condition. This is a new representation mapping under C197's definition of a substantial adapter change, even if the implementation is small. The permitted closing outcome is a feasibility proposal, not an in-place expansion of the C193 namespace.

## Reviewed identity and scope

Repository: Omegapy/OntoKin  
Commit: `6cbcf9c8c136659def1aac94829330cb81872511`  
Tree: `13eb2463217d3021c7783c6c6d8be749e8c2e145`  
Checkout: `/workspace/scratch/21331b7111cc/main_c196`

This review read GOAL, AGENTS, current STATUS, and the complete C197 next task. It inspected the current source, adopted mappings, independent readers, earlier experiment documentation, and selected original builders inside retained C185, C186, C187, C189 and C190 archives. It did not run native exports, Blender, simulations, product tests or authors. It made no repository or remote mutation. REPORT.json retains full-file SHA-256 identities, exact line ranges, source excerpts, archive/member identities, and the search scope.

The integrated and verified C196 state supplied by the coordinator is the starting dependency. This review makes no new C196 execution claim.

## Required common path and observed implementations

| Candidate path | Observed implementation | Admission implication |
| --- | --- | --- |
| Standard .ok classes and native GLB writer | `ontokin.scene` constructs meshes from resolved source objects; `ontokin.gltf._encode` writes them directly to GLB. Existing pockets can represent trays. | Supports source-owned geometry. It is the OntoKin exporter, not a qualified standard-language-to-Blender construction adapter. |
| C185/C186 rotary designs | Blender builds/edits its own scene and calls `bpy.ops.export_scene.gltf`; OntoKin calls `execute_torque_export`. | Shared evaluator and output format; different native construction paths. |
| C187/C189 two-carriage designs | Blender builds mesh objects/parents/drivers and exports through Blender; OntoKin compiles .ok and exports through its own runtime, then normalizes mesh names. | Prior evidence does not qualify a common constructor for standard .ok. |
| C190 shoe contact | Blender adds compound-body contact; the unchanged native .22 route has no contact response. | Explicitly different physical implementations. It motivated the finite adapter. |
| C191/C193 common constructor | Both experimental literal .ok and direct Python feed the same canonical gauge model into the same pinned Blender worker. | Common backend is established only for the fixed gauge schema and admitted edits. |
| GLB import in Blender | Existing receiving script imports already generated GLB, checks seven gauge IDs and bounds, and renders frames. | Receiving validation; not a qualified common source constructor or identity-preserving re-export mapping. |

### Native tray capability exists

The adopted polygon-pocket contract binds source `0.12`, profile `polygon-pockets-0.1`, and destination `ontokin.glb/0.12`. It supports an exterior outline with keyed blind pockets and retains earlier nominal classes, functions, parameters, pinned modules and keyed generation. Pockets are visual geometry and add no body, mass, contact or motion authority.

Evidence:

- `docs/language-design/polygon-pockets-v0.1/ADOPTION.md`, lines 9–24.
- `examples/polygon-pockets/heldout-stepped-tray.ok`, lines 1–40.
- `examples/textured-surfaces/sources/marked-tray.ok`, lines 1–32.
- `ontokin/scene.py`, lines 1120–1142 and 1250–1266.
- `ontokin/gltf.py`, lines 158–175.

A five-box tray and explicit payload proxy could be an even smaller static representation than a pocket mesh. Selecting that formulation does not resolve the backend gap by itself. The source semantics and common backend must both be supported.

### C193 cannot accept tray roles

The inherited C191 contract explicitly says its separately invoked literal prototype does not inherit the standard parser, classes, functions or imports. It qualifies only the seven-part C190 assembly. Its visible IDs are fixed, its two mass-owning carriage bodies and two shoe relationships are fixed, and its dependency closure contains no external modules or assets.

C193 preserves these limits. Its specification states that the source owns exactly seven visible boxes, two 1 kg carriage bodies, four contact boxes and two follow relationships. Only the left stop X coordinate and left shoe collider enablement are admitted design edits. The same-canonical-model/same-constructor requirement applies inside that finite scope.

The implementation enforces the limit, not merely the prose:

- `source.schema.json` fixes the module to `gauge`, scene to `slide`, duration to two seconds, canonical role set, and numerous fixed dimensions.
- `source.py` compares every canonical declaration set to the schema, emits `E_SCOPE` on a different set, and requires exactly fifteen declarations.
- `native_worker.py` names the seven gauge parts, constructs fixed/moving roles from the backend mapping, accesses `left_stop`, `contact.left_shoe`, and lane-specific carriage/shoe bodies, and installs guides and motors.
- `backend.json` fixes the visible-part order and the two moving lanes.

Renaming tray parts to gauge roles, bypassing schema validation, or treating `mesh_box` as an already qualified general adapter would change the meaning and supported domain. None is an existing documented tray route.

Key evidence:

- `docs/language-design/guided-contact-v0.1/SPECIFICATION.md`, lines 18–24, 34–64, 105–132.
- `docs/language-design/guided-contact-v0.2/SPECIFICATION.md`, lines 20–50 and 71–80.
- `prototypes/guided_contact_v02/source.py`, lines 384–417.
- `prototypes/guided_contact_v02/native_worker.py`, lines 14–55, 120–140 and 175–205.
- `docs/language-design/guided-contact-v0.2/backend.json`, lines 449–475.

### Earlier Blender mappings were inspected

The review did not infer absence from C193 alone. It read earlier native-route records and original builders retained inside the following archives:

- C185 `deliveries.zip`: Blender `build_variants.py` opens its editable starter and calls Blender's glTF exporter. OntoKin `build.py` invokes the native torque exporter.
- C186 `deliveries.zip`: retained builders follow the same split native routes.
- C187 `deliveries.zip`: Blender `build.py` creates meshes with `bpy.data.meshes.new` and exports in Blender. The OntoKin builder calls `execute_torque_export` and copies stable node IDs into mesh names.
- C189 `trial-evidence.zip`: Blender and OntoKin remain separate native construction/export routes.
- C190 `trial-evidence.zip`: Blender construction/contact and export remain distinct from the standard .22 native route.

The documentation confirms the distinction. C187 README lines 10–14 describes separately regenerated native exports and mesh-name normalization. C189 README lines 17–21 distinguishes Blender parent/driver behavior from OntoKin following and native export. C190 README lines 21–27 distinguishes Blender contact from the unchanged source profile's lack of contact response. A common GLB reader, viewer or format does not make those construction implementations identical.

## Why GLB import does not close the gate

Blender's existing glTF importer can receive an OntoKin GLB. The repository does not establish the stronger tray claim needed here: a standard .ok source and a direct Python source entering the same qualified construction mapping with the same export settings while preserving stable instance/component identity.

The existing rendering workflow does the following:

1. Receives an already exported GLB.
2. Starts an empty Blender scene and imports the GLB.
3. Requires exactly the seven gauge mesh IDs.
4. Confirms there is no live rigid-body scene.
5. Compares imported bounds to the GLB reader and renders selected frames.

It does not construct trays from resolved typed source, regenerate source definitions, export the imported scene through a qualified round trip, or prove preservation of source-to-instance metadata. Its receipt explicitly labels the work as rendering imported delivered GLBs.

The native export contract warns that importers may discard application metadata and that a successful GLB write does not prove mapping retention after editing/re-export. The implementation also records that source classes and definitions are not embedded for reconstruction and that Blender re-export may discard OntoKin extras.

Evidence:

- `docs/engineering/guided-contact-c191/tools/render_frames.py`, lines 310–375.
- `docs/engineering/OK-ENG-002-3d-scene-animation-export-and-visual-validation.md`, lines 128–151.
- `ontokin/scene.py`, lines 1441–1449.

A new bounded import/re-export profile could be proposed separately, but it would require an explicit source/identity/frame mapping and its own qualification. It cannot be counted as an existing qualified common constructor merely because both output files are opened in Blender. It would also retain two initial geometry constructors, which must be disclosed if used to study language contribution.

## Independent geometry and identity checking

Existing independent GLB code is useful groundwork. The C191 reader decodes actual POSITION accessors and triangle indices, computes world transforms, and verifies exact node/mesh identities supplied by the evaluator. It does not trust dimensions declared in source annotations.

It is not already a qualified static tray checker. Its current profile requires exactly one animation spanning zero to two seconds, one mesh per stable ID, solid materials and other frozen restrictions. Tray cavity/wall/clearance and unchanged-sibling expectations would need their own independent calculation and controls. Preparing a new task checker is allowed by C197 after feasibility, so this is additional qualification work rather than an independent semantic blocker.

Evidence: `docs/engineering/guided-contact-c191/independent/checker/gltf.py`, lines 56–140, 161–180 and 198–215.

For a later static box mapping, derive extents from delivered vertices transformed through the full node hierarchy. Verify each part ID and owner/instance ID against the frozen expected set, measure base/wall thickness and interior clearances, prove nonoverlapping corner partitions, and compare the right tray's actual geometry/placement against its accepted baseline. Negative controls must change real geometry or remove/rename a right-side component. Correct annotations with incorrect vertices must fail.

## Bounded mapping proposal

A suitable later proposal is a separately named experimental **static box assembly to Blender mapping**, version 0.1. The name is provisional and does not select or implement a new contract.

Suggested scope:

- Reuse an existing standard .ok source/profile with classes, units, stable keyed instances, arithmetic and explicit box geometry. Do not add language syntax or reinterpret physical relationships.
- Add one explicit mapping from resolved, static, no-body box occurrences and their supported world poses to a bounded canonical schema. Preserve full stable occurrence IDs, instance ownership, source revision and dependency closure.
- Let direct Python produce that same canonical schema without invoking the .ok parser or a different mesh generator.
- Run both canonical inputs through one pinned Blender constructor starting from an empty scene and one fixed glTF export configuration.
- Bound the first case to two tray instances, each consisting of one base, four rectangular walls and one explicitly identified payload proxy: twelve visible boxes in total. Freeze the exact corner partition so no material is counted twice. Do not add dynamic contact, deformation, arbitrary import, animation or general scene conversion.
- Reuse the available Blender 4.5.3 Linux build pin only after confirming its actual bytes. The current C193 backend record identifies build `67807e1800cc` and executable SHA-256 `5e15447670804c855fef6033ac9b8fd82696b762095becf0df79b1c2f8034397`; this review did not launch or inspect an installed executable.
- Give the new mapping a separate version, schema, namespace and independent fixtures. Preserve all C191/C193 contracts, source bytes and receiving evidence.

The adapter must define primitive origin, units, axis transform, rotations, hierarchy flattening or retention, node and mesh naming, material defaults, supported roles, zero-motion interpretation, output provenance, loss reporting, budgets and rejection behavior. Those decisions are part of the missing mapping, not facts already guaranteed by the current API.

### Suggested validation and effort estimate

A later implementation should first qualify: supported box/pose mapping; stable identities under order changes; independent instance resize and unchanged sibling; exact dependency/source retention; rejection of unsupported geometry/motion; finite budgets and cleanup; deterministic regeneration; actual receiving import; and the two required delivered-content failure controls. Only then should the tray baseline admission freeze authorize exports.

Planning estimate: **3–7 engineer-days** for a narrow mapping and its independent qualification, assuming twelve static boxes, reuse of existing compilation and identity machinery, available pinned tools, and no newly discovered standard-language defect. This is an estimate, not measured effort. A general importer, surface-wide mapping, class reconstruction from GLB, live physics or production backend would exceed it. The coordinator may refine this estimate after the source-side feasibility review.

## Preserved limits

No baseline artifact has been admitted and no performance or authoring advantage is established. The inherited legacy driver and supplemental tail remain FAILED, with 4,239 distinct passing methods and thirteen torque-read methods NOT RUN. Ordinary defaults remain 100,000 operations and 30,000 ms. General contact, live destination physics, production backends, broader compatibility, and all unmet GOAL domains remain open.

