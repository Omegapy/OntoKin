# Proposed exact source-normal payload and explicit loss report, C214/0.1.0

**Proposed experimental profile; CPU-only.** A surface normal is a direction used for shading a surface. This profile preserves the exact normal values delivered by the accepted C210 GLB. It separately reports differences in explicitly synthetic observations. It does not establish a receiving application's shading behavior.

The [C210 source proof](../semantic-export-c210/CONTRACT.md) remains the authority for the accepted program and artifact. [C211's receiving contract](../semantic-receiving-c211/evidence/CONTRACT-ATTEMPT-1.md.txt) and its failed `2e-6` normal gate remain unchanged. [C212's decision](../normal-fidelity-c212/DECISION.md) adopted no replacement tolerance; [C213](../normal-codec-c213/RESULTS.md) found finite lossy codec examples. This separately versioned proposal does not amend any of those contracts.

## 1. Claims and implementation boundary

| Claim | C214 treatment |
| --- | --- |
| Exact accepted source normal values | Decode original float32 bytes, retain their bits and unambiguous source-corner identity, and validate against the exact accepted inputs. |
| Destination shading directions | Report explicitly synthetic CPU observations in this profile. A native observation label is refused. |
| Normal differences | Report raw component differences and an angular difference for each valid observation. Missing and invalid observations have separate states. |
| Shading acceptance | Always `NOT_EVALUATED`; no acceptance tolerance exists. |
| Native fidelity or receiving evidence | Always false. A copied normal payload is not evidence of actual destination shading. |

The implementation is an isolated standard-library script in this directory. It changes no source language, compiler, Agent protocol, GLB writer, Blender receiver or existing default. `prototype.py` imports no OntoKin runtime module and launches no process. The proof driver launches only read-only Git identity queries; it never executes the source program or a native/destination application. A later native profile needs separate review, a destination reader, a demonstrated coordinate conversion/corner mapping, exact build/settings bindings, a bounded execution plan, native save/reopen checks and useful visual evidence. No such attempt is authorized here.

## 2. Accepted input authority

The public API accepts only the exact existing C210 `after.glb`, `after.program.bundle.json` and `after.semantic.json` bytes. Their byte sizes and SHA-256 values are pinned in `ACCEPTED_INPUTS` in [prototype.py](prototype.py). Raw input identity includes whitespace in JSON; semantic equivalence alone is insufficient for this finite profile. Replacing the whole triple with a different self-consistent revision is refused.

After checking those pins, the script recomputes source-unit hashes and the program revision using the existing `ontokin.bundle/0.1` manifest and domain separator. It verifies that the semantic sidecar and GLB program provenance identify that same manifest/revision. It checks the semantic artifact digest, exact geometry accessors and their data hashes, and object/node/source-identity coverage. This is a consistency check on retained accepted inputs. It does not compile a new program, independently re-prove C210's authoring acceptance, or grant acceptance to new source.

The low-level `decode_glb`, `accessor_bytes` and `source_corners` helpers support independent synthetic parser controls. These helpers return decoded data only; they cannot issue an accepted payload and do not bypass the public input pins.

## 3. Payload schema

The schema is `ontokin.source-normal-payload/0.1`; profile is `c210-accepted-after-source-normals-c214/0.1`. The source frame is the literal `gltf-object-local-right-handed-y-up`. A source normal remains in its GLB object's local frame. No normalization, frame transformation, vertex welding, triangle sorting or normal averaging changes its authoritative bytes.

Each source-corner record has these exact fields:

| Field | Meaning |
| --- | --- |
| `key` | Four nonnegative integer indices: mesh, primitive, triangle ordinal in the original index stream, and corner ordinal 0–2. |
| `vertex` | The original indexed vertex at this corner. |
| `winding` | The three original vertex indices in exact triangle order. |
| `normal_f32le` | Lowercase hexadecimal encoding of the exact twelve little-endian bytes of the three IEEE 754 binary32 normal components. |
| `position_f32le` | The corresponding exact twelve position bytes, used without merging coincident source positions. |

The payload stores each mesh corner once. `instances` maps every GLB node to a mesh, source path and stable `element_id`. An observation uses the node plus the source-corner key, so two objects sharing a mesh cannot be confused. Sharp boundaries remain distinct even when corners occupy the same position. Float32 signed-zero bits remain distinct in the payload; no claim is made that the selected accepted fixture contains every possible float32 pattern.

The limited GLB decoder requires embedded two-chunk GLB 2.0, non-sparse float32 POSITION/NORMAL accessors, indexed triangles, complete bounds and supported alignment. It refuses unsupported required extensions, morph/skin geometry, nonfinite positions or normals, zero normals, incomplete triangles, repeated vertex indices within a triangle and out-of-range indices. This is a bounded decoder, not a general glTF importer or a source geometry quality certificate.

`validate_payload` rebuilds the expected payload from the pinned authoritative bytes and compares canonical encodings. Missing, duplicate, extra, reordered or modified records are refused, including changed winding, source normal sign, position, instance mapping and unknown fields. Integer booleans differ in canonical encoding and are refused. Canonical JSON uses UTF-8, sorted object keys, compact separators, unchanged array order and no NaN/infinity tokens. The file reader also refuses duplicate JSON object members.

## 4. Synthetic observation schema

`ontokin.normal-observations/0.1` contains exactly `schema_version`, `sourcePayloadSha256`, `sourceFrame`, `kind`, `producer` and `records`. `sourcePayloadSha256` hashes the canonical payload without a final newline. `kind` must be `synthetic-cpu`, and `producer` must be nonempty. The source frame must match exactly; frame conversion is unimplemented.

Each record contains `key` and `normal` only. The key is `[node, mesh, primitive, triangle, corner]`, with five nonnegative non-bool integers. Unknown, mismatched, ambiguous or duplicate keys are refused. Absence of an expected corner is reported as `missing`. A present direction must contain three finite numeric, non-bool components and have nonzero magnitude; otherwise the corner is `invalid`. An invalid observation does not erase valid observations or become a zero difference.

The Python API can report nonfinite in-memory values as invalid observations. Such an input is not canonical JSON: its input digest is null and `observationsCanonicalJson` is false. Standard JSON files must represent a failed observation with an invalid value such as null or a string; literal NaN/infinity JSON tokens are refused by the file reader. Valid fixture files and outputs have exact byte hashes in the retained run manifest.

## 5. Loss-report schema and measurements

The report schema is `ontokin.normal-loss-report/0.1`. It binds the canonical source payload and, when representable, the canonical observation input. Every expected object-corner has an `observed`, `missing` or `invalid` row. Summary counts add to the complete expected denominator. With no valid observations both numerical maxima are null, not zero.

For valid observations, `componentDelta` is observed minus source in the same frame, before normalization; `maximumComponentDifference` is the greatest absolute component delta. Angular difference is measured in degrees with `atan2` of the normalized cross-product length and dot product. Scale-first normalization avoids overflow and underflow for finite large or subnormal input magnitudes. Normalizing for the angle does not alter the source payload or hide magnitude differences from component measurements. Opposite directions measure 180 degrees. The report establishes no universal codec error bound and has no pass threshold.

`sourceAuthority` is `EXACT_SOURCE_PAYLOAD`; `nativeFidelityEstablished` and `receivingEvidence` are false; `acceptanceTolerance` is null; `shadingAcceptance` is `NOT_EVALUATED`. These fields are fixed by code, not taken from caller claims. A synthetic report remains synthetic even when all its directions equal the source exactly.

## 6. Checks and stopping condition

Independent controls are predeclared before execution. They cover exact round trip, signed-zero preservation through untrusted synthetic helpers, missing/duplicate/ambiguous corners, winding, signs, invalid/zero normals, sharp boundaries, stale bindings, missing/invalid observations, mismatched frames and numerical extremes. Implementation smoke checks exercise complete accepted-input construction and report production. Original failures and later corrections remain separate evidence.

Completion means a reviewed finite payload/validator/report implementation with applicable CPU/documentation checks and preserved source/evidence, or a precise blocker. It does not require or authorize another Blender process, a receiver merge, a new normal tolerance, a second destination, an author comparison or another feature.
