# C234 independent material-checker review

## Decision

**Accept the bounded CPU material step. No blocking implementation finding remains.** The final author commit is `67b01548056ec5caf7bc5cd0c41fde8434c0ab0e`, tree `a66739b07cef506a080ec3061b1aaafec8b10ef2`. The cumulative change from C233 main adds only the C234 checker, its package-dependent controls, contract and entry README. Existing C220 authority, C221 admission, C222 correspondence, runtime, exporter, tests, workflows and product limits are unchanged.

The independent execution used an isolated clean sparse checkout at `8c231cc01cb768e4e88c9ac05821594ec7f1ecc4`, tree `a796e13e0aa75ec514851ca9f2f8879a16035d63`. All **151 public/API/CLI controls passed** in 63.956 seconds on Linux x86-64 / CPython 3.12.14; its checked source remained unchanged. Exact checker, contract and README bytes match the final author commit. Only the additive author test file changed afterward. That full test source was separately inspected, and its final execution is recorded by the author. These commit identities remain distinct; no unchanged controls were replayed merely to rename their source.

## Independent oracle and observed results

The review decoded the retained 185,236-byte GLB directly using its own standard-library little-endian parser. GLB node extras supplied source identities, which were joined with the separately hash-checked frozen part map. The geometry fixture reverses vertex storage and cyclically rotates reversed triangle order. The independently derived complete 23,400-row correspondence digest matches C222, covering all 18 parts, 7,800 triangles and 23,400 corners. No author fixture, color converter or comparison helper was imported.

A 64-digit Decimal calculation constructs raw sRGB values from the two admitted source PBR materials. A separate Decimal calculation checks the report's normalized values. The baseline result accounts for all 18 material associations, 108 numerical components and 36 exact culling/transparency checks. Every raw observation remains equal to its input, every reported source material matches direct GLB decoding, and every normalized component agrees with the independent oracle. The material observation and geometry reports identify the exact consumed sizes and SHA-256 hashes.

The public controls establish:

- Missing, duplicate, swapped and incorrectly typed part/node/mesh/primitive/material associations are refused. Node labels must match the exact checked geometry. Both source material indices remain represented.
- Distinct resource copies are allowed. A shared resource label cannot refer to conflicting material indices or different raw values, even when the numeric difference alone is within tolerance.
- Missing/extra fields, malformed JSON/UTF-8, duplicate keys, non-finite or overflow values, boolean substitutions, invalid ranges and unknown storage semantics are refused.
- Unconverted linear RGB, double conversion, swapped material values, wrong alpha/metallic/roughness, and wrong culling/transparency modes fail their respective checks.
- Alpha near 1 remains linear and passes when its error is within the original limit. Applying an RGB transfer to that alpha would fail this control. Both retained source materials are fully opaque; these are synthetic controls, not native opacity observations.
- The represented value `0.000002` and its immediately smaller float pass for source-zero metallic. The immediately larger float fails. The contract explicitly compares exact rational representations against `1/500000` with no added epsilon or subtraction-rounding allowance. This retains the original numerical limit.
- A modified admitted GLB or a missing locked comparison input fails fresh authority admission. Invalid geometry blocks materials. Geometry that still passes correspondence but has different bytes cannot reuse the stale material digest. A copied prior pass report cannot replace either observation document.
- Producer labels such as `unattested-native` never enable native receiving evidence, mapping attestation or target execution. All such flags remain false, and all native/source/export/import/render/scene-write counts remain zero.

Failures distinguish authority admission, geometry correspondence, material structure and parameter comparison. The saved case results confirm those stage boundaries; the implementation retains complete comparison rows and individual outcomes when a numeric comparison fails. The full passing and untrusted-label reports are retained for inspection.

## Source and author controls

Static review checked the public admission chain, safe bounded material reads, exact geometry reread binding, independently decoded finite source parameters, complete association joins, raw-resource consistency, fixed color transfer, exact numerical rule, failure reports and CLI. It found no path that accepts a supplied authority/pass report or promotes a native label into evidence. The implementation has no native launcher, runtime import, source evaluator or exporter.

The author's final affected cohort passed **24 C234 + 20 C221 + 23 C222 methods = 67**, with no final failures, errors or skips. Its documentation preservation check passed 29 sources. Its earlier zero-method fixture error and the missing `--report` C221 caller error remain preserved. They are not relabeled as passing executions. This review inspected those logs and the complete author test source.

The reviewer initially encountered two Git clone ref-creation failures while capacity was constrained. A premature first control command then failed before importing the missing source; zero controls ran. These orchestration logs are retained. The precise clone failure mechanism was not independently diagnosed. A sparse single-branch clone succeeded, and the complete independently checked run subsequently passed. No product failure or skipped obligation is inferred from those startup attempts.

## Evidence and scope limits

- `REVIEW.json`: exact decision, source eligibility, hashes, checked stages and counts.
- `run-02/RESULTS.json` and `run-02.log`: all 151 independent observed control outcomes.
- `run-02/baseline-report.json` and `run-02/unattested-label-report.json`: complete material results.
- `c222-oracle-validation.json`: complete 23,400-row correspondence report; its summary confirms the independent map digest.
- `independent_oracle.py`, `run_independent_controls.py`, `fixtures/` and `run-02/oracle.json`: restorable independent evidence construction.
- `candidate.diff`: exact additive final-author change.
- `CLONE-FAILURE.json`, clone logs and `run-01.log`: preserved reviewer startup failures.

This acceptance covers CPU checks on untrusted synthetic observations only. It does not establish Godot behavior, native capture provenance, material appearance, normal fidelity, poses, persistence, a second-target receiving promise or a release. The original strict Blender normal failure, held prototypes and consumed schedules remain unchanged. The remaining R07 normal/pose/semantic/cross-target/observer/persistence/process/settings/rendering/build-lineage gates remain separate. Root still owns coordinated publication, resulting-main checks, successor archive verification and confirmed delivery.
