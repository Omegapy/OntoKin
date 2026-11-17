# C257 ownership field origins

The source observer tokenizes the two supplied UTF-8 byte strings directly.
Every source span uses an inclusive `startByte` and exclusive
`endByteExclusive` in the named original file. Comments and multibyte text do
not turn byte offsets into character offsets. Artifact origins are JSON
pointers into the JSON chunk of the artifact identified by `artifactSha256`.

| Observation | Source or artifact origin | Interpretation |
| --- | --- | --- |
| Source occurrence `id` | `origin.identityKeys`: module key, scene key, root key, each part/collection key, and each literal keyed-entry token | Full ordered key array. A dotted key remains one component. |
| Source `definitionId` | Actual import package, defining module key and class declaration key within `origin.definition` | Reused definition identity, distinct from the occurrence identity. |
| Source `path` | Lexical root/member names and quoted literal entry keys | Human display path; never a replacement for full identity. |
| Root `ownerId` / `ownerPath` | Scene containment and actual root declaration; `origin.ownerDeclaration` is the scene span | Explicit null: no containing object. |
| Part `ownerId` / `ownerPath` | Actual containing object's declaration, child declaration, recursive class resolution | Immediate lexical object owner. No transform/follow/hinge lookup. |
| Generated part owner | Collection declaration, generator input, selected default/override, helper return and literal-key spans in `origin.expansion` | The containing object owns each generated part directly. The collection adds no object. |
| Source program identity | Complete canonical manifest built from actual file hashes, fixed package/version and filenames | Adopted bundle identity rule; no sidecar supplies the answer. |
| Repeated source authority claims | Program `sources` for both units, program/top-level entry source IDs, top-level entry revision, module, scene and profile | All must agree with actual source bytes and parsed module/scene headers. `sourceAuthorityOrigins` gives their JSON pointers. |
| Node occurrence identity | `/nodes/<index>/extras/ontokin/element_id` | Must match the full source-derived identity array. |
| Definition association | Both mappings' `definition_id` and `class_id`, plus node `class_name` | Must match the independently resolved source definition. |
| Node owner claim | `/nodes/<index>/extras/ontokin/owner` | Explicit path string or null; a missing field refuses. |
| Source mapping owner claim | `/nodes/<index>/extras/ontokin/source_mapping/owner_path` | Independently read, then compared with the source owner. |
| Program occurrence owner claim | `/extras/ontokin/program/occurrences/<escaped path>/owner_path` | Independently read; JSON-pointer escaping preserves `/` and `~`. |
| Exact declaration/definition association | Each mapping's `source_id`, `filename`, `source_revision`, `start_byte` and `end_byte` | Must match the measured original file, SHA-256 and integer source span. Booleans and equal-valued floats are not byte offsets. |
| Historical admission | Actual bytes read from the existing proof paths | Exact size and SHA-256 before the same raw comparison. |

`observe_glb_ownership` exposes the three owner claims without calling them
verified. `compare_ownership` requires every claim to agree with the source
graph, including explicit null root owners. It checks all occurrences with no
duplicate identities or extra/missing program occurrences. The output's
`ownerId` comes from the independently derived source graph joined by full ID;
the artifact itself stores owner paths.

`sourceAssociationVerified` covers the complete source manifest and source-unit
table, program and repeated entry source identities, each node's program
revision, occurrence/definition/path fields, source module/scene/profile names
and the two measured declaration/definition source spans. It does not qualify
other producer metadata, such as generated-value provenance, `path_steps`,
relationship records, geometry, actions or animation. Those fields are not
substituted for independent observations. A complete semantic producer and a
general source-validity checker remain absent.
