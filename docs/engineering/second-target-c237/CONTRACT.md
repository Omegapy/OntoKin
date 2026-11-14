# C237 CPU semantic treatment and retained-source contract

Version: `ontokin.second-target.c237/0.1`. Scope: opt-in finite C210 18-part observation comparison. This contract is predeclared before controls and implementation. It adds no exporter, evaluator, importer, native capture, replay or release acceptance.

## Authority and public path

`check_semantics(package_root, observation_path)` freshly executes `tools.second_target_c221.check_bindings.check_package` on every public invocation. A failed C221 admission refuses the observation. The unchanged C220 authority admits all eight original files. C237 then safely reads the exact original semantic sidecar, program bundle and independent source oracle using their original C220 byte/length/mode pins. It parses the bytes read through stable descriptors; no unchecked reopening or caller-supplied authority is accepted. Original sidecar and parsed oracle `semantic_canonical` must match recursively by exact JSON type and value.

CLI: `python3 tools/second_target_c237/check_semantics.py --package-root ROOT --observations FILE`. Standard output contains exactly one JSON report; there is no report-file option or report-file write side effect. Exit codes are 0 for finite equality, 1 for admissible measured loss, 2 for structural refusal. No native tool, source evaluator, compiler, export/import, render, scene write or aggregate runner is imported or started.

## Observation schema

The complete root has exactly `schema`, `producer`, `programRevision`, `parts`, `semantics`, `features`, `retainedFiles`, `capabilities`.

- `schema`: `ontokin.second-target.c237.observations/0.1`.
- `producer`: exactly `kind` (`synthetic` or `declared_destination`) and nonempty `name`. Both are provenance claims. A consistent claimed destination observation is permitted without acquiring native attestation.
- `programRevision`: exact admitted program revision.
- `parts`: exactly 18 unique records, keyed by `sourceNode`; order is immaterial. Each record has exactly `sourceNode`, `sourceMesh`, `elementId`, `definitionId`, `sourcePath`, `destinationLabel`. Node/mesh are exact nonnegative integers, never Boolean; identities are nonempty string arrays, source path is the exact admitted string, and destination label is a nonempty descriptive string. Every identity field must match the admitted part, with no missing, duplicate, extra or swapped identity. Duplicate cosmetic destination labels are allowed. Labels cannot repair identity mismatches, and exact unique source bindings do not attest actual destination-node mapping.
- `semantics`: the complete original sidecar-shaped JSON record. Dictionaries have exactly the original keys; lists retain original order and length. Every primitive has the original JSON type, including the distinction between Boolean, integer and float. Missing/extra fields, changed list lengths or types are structural refusals. Structurally valid changed primitive values are measured semantic losses. This covers all original object/provenance/owner/placement/geometry/typed-property/motion/site/follow/hinge/action/event/collection/coordinate/scene/feature fields without an implementation-maintained subset. Primitive comparison uses exact typed canonical JSON representations. In this new semantic-retention profile, float `-0.0` and `0.0` therefore differ and produce measured semantic loss; this does not change any geometry, normal, material or pose arithmetic rule or gate. Source order is meaningful; parts/features/retained-file outer lists alone are keyed sets.
- `features`: exactly 14 unique records keyed by `feature`; order is immaterial. Each has exactly the original `feature`, `treatment`, `reason`, `required` plus `provenance` and `capability`. Original fields have original types; changed source treatment, reason or required Boolean is a measured loss, except unsupported-to-supported contradictions which are refused. No feature may be omitted or invented.
- `retainedFiles`: exactly four unique records, each with `kind` and `base64`. Kinds are `program_bundle`, `glb`, `semantic_sidecar`, `source_normal_payload`. Base64 is canonical ASCII with standard alphabet, exact padding and no whitespace; re-encoding decoded bytes must equal the supplied string. Actual decoded lengths and SHA-256 hashes are compared to original pins. A valid representation of changed or empty bytes is measured retention loss. Omitted rows/fields or malformed encoding are structural refusals. Claimed hash strings are not part of the schema.
- `capabilities`: exactly `liveFollowing`, `liveHinges`, `actionExecution`, `livePhysics`, `sourceReconstruction`, `rigidBodyCount`, `controllerCount`, `representedBodyMassKg`, `motionAuthority`. Five Boolean flags must be false; both counts are integer zero; mass is float 0.0; motion authority is the original `OntoKin reference evaluator; destination receives baked playback only`. Contradictory capability claims are structural refusals. The zero mass is derived from this no_body fixture, not a native mass measurement.

## Feature provenance and capability matrix

Allowed provenance labels are `imported_native`, `independently_derived`, `observer_copied`, `retained_external`, `unsupported`. They describe declared origin. Equality and byte retention do not establish the truth of a native or independently derived claim.

| Features | Allowed provenance | Required capability |
| --- | --- | --- |
| source_closure | retained_external | retained_source |
| stable_identities, dimensions_units_frames | imported_native, independently_derived, observer_copied, retained_external | descriptive_metadata |
| ownership, following, hinge_constraints, physical_declarations | observer_copied, retained_external | descriptive_metadata |
| materials | imported_native, independently_derived, observer_copied, retained_external | descriptive_metadata |
| primitive_geometry, numeric_precision | imported_native, independently_derived, observer_copied, retained_external | approximated_representation |
| world_motion | imported_native, independently_derived, observer_copied, retained_external | baked_playback |
| action_execution, live_physics, source_reconstruction | unsupported | unsupported |

A feature/provenance/capability combination outside this matrix is structurally refused. This profile cannot express live following, destination joints, executable actions, rigid bodies, source reconstruction or controllers. Descriptions and original source may remain available without those capabilities.

## Retention and source-unit inspection

The exact original raw byte pins come from C220. Reformatting JSON changes raw retention even if parsed values are equal. Inspect the actual decoded program bundle with strict JSON rules; report both embedded source units, their UTF-8 lengths and source-revision hashes, filenames, entry identity, dependency package identity/version and equality to the original exact bundle. Units are embedded strings; no duplicate standalone source files are required. Invalid retained bundle content yields a measured retention/source-inspection loss. Preserve raw-file bindings separately from canonical semantic JSON hashes and source/program revisions.

A retained bundle establishes availability of original source. It does not establish reconstruction from a native scene, successful source execution, import lineage or compiler invocation. Retained sidecar/GLB/payload bytes similarly establish their availability, not received geometry, normals, materials or pose accuracy; those prior numerical checks remain independent.

## Safe admission and refusal

Use strict UTF-8 JSON with duplicate keys, nonfinite numbers, invalid scalar types, missing/unknown fields and unsafe paths refused. Observation limits are 4 MiB raw bytes, 64 levels of nesting, 100,000 JSON values, and 1 MiB UTF-8 bytes per string. Strings containing unpaired surrogates are refused. The full observation path and every component must resolve without symlinks; inputs must be regular files, not directories/FIFOs/devices. Use descriptor no-follow/nonblocking checks and revalidate inode/device/size/mtime before and after read; record observed raw SHA-256 and length. Read pinned original files under the same protocol with explicit expected size/hash/mode. Invalid parser/path/authority conditions are structural refusals.

## Report and result meaning

Reports bind exact observation bytes and admitted authority. Admitted reports retain full per-part identities, all 14 original and observed feature rows, complete expected/observed semantic records, primitive mismatch paths/values, actual retained-file byte bindings and source-unit inspection. No aggregate Boolean hides missing or unsupported treatments. Refusals contain an explicit stable refusal code and reason; measured losses remain a separate result class. All results set native attestation, source execution, native execution and aggregate execution false. A finite pass is only equality under this declared observation/retention contract. It does not pass the complete R07 gate, native qualification or OntoKin release acceptance.

## Required controls

Before acceptance exercise complete 18/14 positive observations; every provenance category and contradiction; missing/duplicate/extra/swapped identities; wrong revisions/spans/owners; all source treatments/reasons/required flags; metadata relationships, actions/events and invented physical capability; exact versus missing/changed/reserialized/forged-claim retained bytes; both source units and dependency identity/version; parser depth/size/duplicates/nonfinite/type confusion/symlink/nonregular/read-race refusals; API and CLI exit behavior and absence of source/native starts. Author and independent review must use independent expected data and inspect complete reports. Run the unchanged prerequisite cohort required by actual imports. Preserve failed development attempts separately from accepted run evidence and exact code identity.
