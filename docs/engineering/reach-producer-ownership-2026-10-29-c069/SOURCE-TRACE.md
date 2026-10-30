# C069 actual producer-to-reader trace

All locations refer to baseline `7c0bf98e48a641e30627b7fd261b6713d79e223c`. Exact file hashes and definition ranges are generated in [derived-evidence.json](derived-evidence.json). This table records the native path's relevant retained storage and callout sites. It does not claim to enumerate arbitrary aliases that external Python code could manufacture.

| Stage | Bound source | Retained identities, aliases and transition |
| --- | --- | --- |
| Original request | [source driver](../../../tools/build_reach_source_artifacts.py), `build` | The driver retains bundle and compiler; passes compiler model and reach work to export. `compile_construction` has no supplied `check`. |
| Shared budget | [construction](../../../ontokin/construction.py), `ConstructionBudget`, `ConstructionCompiler.__init__`, `compile_construction` | The budget retains limits, time/counters and `check=None`; compiler retains the budget and `ReachExecutionWork(check=budget.tick)`. The reach external callback is non-null. |
| Export | [GLB adapter](../../../ontokin/gltf.py), `export_glb`, `_export_glb`, `validate_export` | The existing work is reused; bound `work.tick`/guarded checks cross scene building, encoding and validation. Source scene, encoded bytes and model remain live. |
| Decoder setup | GLB adapter, `read_glb` | Retains source bytes, chunk bytes, JSON document, binary chunk and `DecodedGLB`. JSON/layout preflight can call the existing check. |
| Eager data production | GLB adapter, `DecodedGLB.accessor`, `read_glb` | On miss, constructs native `result` list, appends unpacked row tuples, stores that same list in `_cache[index]`. The decode check runs every 256 rows. `read_glb` decodes every accessor, then finite-checks and verifies declared bounds. Local `values` and the cache reference the same list. |
| Structural geometry | GLB adapter, `read_glb` | `positions` and `normals` alias cached accessor lists. `indices` is a separate projection. Mesh/triangle checks call the existing callback while decoded lists remain retained. Triangle local rows are additional temporary aliases. |
| Structural animation | GLB adapter, `read_glb` | Time and output accessors remain cached. Local `times` is a separate projection; it supplies no refresh or ownership of POSITION. |
| Independent pregeometry work | [reach reader](../../../ontokin/reach_conformance.py), `validate_reach_export` | Retains decoded object, node/metadata/animation aliases and authored time records. Rational clock, numeric-basis, program metadata, reference/boundary construction, metadata validation and retained-clock validation precede geometry. Their work checkpoints retain the original callback chain. |
| Clock storage | GLB adapter, `DecodedGLB.clock`; reach reader, `verify_retained_clocks` | `_clocks[index]` is another mutable list projected from an accessor. Clock creation/cache use is independent of POSITION storage. |
| Independent mesh producer | [scene](../../../ontokin/scene.py), `_source_primitive_mesh`, `_source_surface_mesh`; [geometry](../../../ontokin/geometry.py), `Mesh`, `sphere_mesh` | Uses `reach_independent_source` namespace. Native sphere cold construction returns tuple positions and normals inside a frozen `Mesh`; a producer hit returns the existing cached object. Cache recipe checks do not authenticate externally replaced values. Source aliases include work-cache value, `mesh`, `meshes[index]` and `source_positions`. |
| Source/cache transitions | Scene helpers; [reach work](../../../ontokin/reach_numeric.py), `lookup`, `remember`, `remember_batch`, `_sync_cache_operand_limit` | Key construction, cache miss/hit, promotion, insertion, eviction and operand-limit resets have their own charged occurrences and callback/reentrancy rules. Numerical generation tracks these cache changes. It does not cover decoder storage. |
| Current POSITION/topology | Reach reader, `_geometry_bounds` | `stored_positions` aliases the previously decoded cached list. A length comparison precedes NORMAL/index cache access and normal comparisons. Source geometry metadata, primitive records and topology aliases remain separate subjects. |
| Wrapper entry | Reach reader, `_vertex_extrema` | The `direct` closure captures both sequences. Eligibility and cap/key creation precede a charged `work.lookup`; that lookup can run the callback, synchronize domain and promote a hit. Only a miss/decline reaches the cold helper. |
| Cold loop | Reach reader, `_vertex_extrema_uncached` | `zip` retains iterators; `point`/`stored` retain current rows. Point charge precedes row shape and source-to-binary32 comparison, exact source-float checks, optional radius fold and error update. Future-seed omission would require a stronger interval guarantee. |
| After the cold result | Reach reader, `_vertex_extrema` | Existing proof blocks reread source/stored rows after their charges, recheck conversions and create a new tuple snapshot. `remember` may call back before publication. This future completed proof cannot authenticate an earlier omitted fold. |

## Ownership facts and invalidation obligations

| Mutation or transition | Existing relevant owner | Effect on proposed receipt |
| --- | --- | --- |
| Item or equal-length slice replacement through stored-list alias | Native list write; no decoder/work method required | Same identity/count can name different rows. Neither candidate epoch necessarily changes. |
| Slice deletion, clear, pop, append, extend, insert, reverse or sort | Native list mutator; no decoder/work method required | Coverage, ordering or seed reachability may change without a decoder or numerical-cache transition. |
| Replace `_cache[index]` or entire decoder `_cache` | Mutable decoder dictionary/field | A retained old list and current lookup can diverge. A new mapping is not proof of original input association. |
| Replace decoder `document`, `binary` or `check` | Public dataclass fields | Accessor interpretation, provenance or future callouts can change. A retained byte object remains immutable but does not freeze the field binding. |
| Replace source-cache value or change source recipe | Work cache/model storage | Independent namespace and unchanged recipe do not establish cached value provenance. Actual producer completion must be retained across hits. |
| Work promotion/insertion/reset | Work cache methods | Numerical generation changes for its legitimate purpose. Those changes must not falsely imply POSITION mutation or freshness. |
| Change work callback, observer, caps or category dictionary | Mutable work fields | Router, charge/failure order and arithmetic authority may change. A native category dictionary's outer type does not certify its entries. |
| Modify dispatch, descriptors, module globals or introduce hooks/reentrancy | Host execution environment | A finite authentic root and explicit supported boundary would be needed; a copied identity or process label is insufficient. |

These rows are source conditions and hypothetical transitions. No mutation was injected or observed during C069.

## Original source versus Agent/custom paths

The source driver omits a custom construction callback. [Program runtime](../../../ontokin/program_runtime.py) passes its service budget's `tick` into `compile_construction`; [ProgramAgentService](../../../ontokin/program_agent.py), `_export`, retains that service callback and supplies its delivery check. Cancellation, nested budgets and legacy profile behavior remain separate obligations. No source-only eligibility conclusion transfers automatically to Agent or arbitrary direct callers.

## The missing root

The current graph contains no object whose established authority both authenticates the first optional router operation and controls every relevant list/dispatch mutation until seed retirement. The list's decoder reference is not exclusive ownership. The numerical cache's generation is not a list version. Retaining immutable source objects is useful provenance only after actual producer authentication. This is why the existing-list receipt fails before a total funding claim is available.
