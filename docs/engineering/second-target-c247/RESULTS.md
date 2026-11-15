# C247 author result and limits

One held source component captures the original 18 parts' final native mesh
arrays using the C246 observed chain. It preserves source/native/surface keys,
raw buffers, exact native format and slot types/lengths, API positions/normals/
indices and auxiliary tangents. It refuses unsupported layouts and returns a
partial, non-accepting receipt on failure. No original source coordinate,
normal or index is substituted for an observation.

The Python model has **34 passing author methods**, including shared resources,
18 traversal permutations, no admission on success, exact-state and single-use
refusal, wrong chain/root/membership/resource failures, unsupported flags and
channels, missing buffers, count/slot limits, retained partial observations,
nonfinite/index failures and same-count buffer/API-value drift. Synthetic
readback intentionally uses values different from the real source fixture,
including non-unit normals and negative zero, to ensure no source-fill or
normalization rule is hidden in the model. This establishes the model's behavior
only. It does not prove GDScript compilation, Godot API behavior or native fidelity.

The static binding checker passes **147 checks** covering 23 source records
(22 distinct source basenames), seven unchanged authority/dependency documents,
exact original GLB bytes, all 18 node/mesh joins, five single indexed triangle
primitives and selected API/lexical boundaries. Full primary files and retrieval
metadata are preserved at their exact `packagePath` entries in BINDINGS.json.
Two initially wrong upstream paths returned 404 and were corrected using source
includes: `scene/resources/3d/importer_mesh.cpp` and
`servers/rendering/rendering_server.h`. The original failures remain evidence.

The first binding-checker attempt incorrectly assumed PART-MAP rows were ordered
by node index. The map preserves source order instead. The corrected checker
requires the exact complete node set and each actual node-to-mesh association;
it does not reorder or change the authority. The initial failure log remains
preserved separately from the passing corrected run.

An initial independent static review identified a partial-evidence gap: valid
bounded arrays were discarded if another slot's type/length was refused. The
corrected source records each inspected slot's actual type/length and supported
bounded copies before cross-slot validation. The model and controls cover that
refusal boundary. A suggested explicit `as ArrayMesh` cast was also adopted for
clarity; the reviewer's subsequent pinned-analyzer inspection did not establish
that the previous base-typed return was a parser failure. Neither version has
been parsed by Godot.

The strongest result is `MESH_ARRAYS_CAPTURED_OTHER_RAW_PENDING`. Even that
component state has only been executed in the synthetic CPU model.
`execution_admission` and `native_acceptance` remain false, and R07 remains
pending. Complete independent review and publication are recorded by the root
integrator against an exact commit/tree and preserved source hashes.

No Godot/version/parser/import/render/save/reopen, source export, fixture
regeneration, product run or aggregate was started. No full envelope, native
serialization, material/pose expansion, persistence, reservation or launcher
was implemented. Native source/build lineage, diagnostic coverage, process
limits and useful-image proof remain unresolved. The inspected storage codec
may change native values; no tolerance or historical result has been revised.
