# Independent C244 design review

**Decision: APPROVE the proposed design boundary.** This is approval of the two narrowly defined contract amendments and their source-level rationale. It is not approval of an observer implementation, a native start, installed callback behavior, destination fidelity, or R07 completion. Independent review of the inert controls and the applicable integration checks remain separate requirements.

Reviewer: `/root/design_review`, an actual subagent operating in the same Linux workspace as the integrator. The reviewer made no repository changes and did not publish or merge anything.

## Exact reviewed source and evidence

| Item | Identity |
| --- | --- |
| Draft commit | `8264db6e36b0c6118cf5b7ab2e41724569f72d90` |
| Draft tree | `c62c61d0287d5d006d53f653a3df8267289d547c` |
| Main baseline | `6bf7b9b1d53a4d8181679bf7bd8f7b5147023c01` |
| Changed repository files | `docs/engineering/second-target-c244/DECISION.md` and `test_decision.py` only |
| Engine source examined | Godot `35e80b3a8822a9df9be390814b62f44c0a9c69e8`; all nine retained source files rehashed |
| Original fixture | 185,236-byte GLB; SHA-256 `05ebe856d3fdb96dce4b6aa55906be5ae67501bcaede9112abc30b703905b5d8` |

[BINDINGS.json](BINDINGS.json) records exact reviewed file hashes, all nine source SHA-256/Git-blob bindings, all six unchanged authority-document hashes, the original fixture and the actual interpreter/platform. [verify_bindings.py](verify_bindings.py) reproduced these checks; [bindings.log](bindings.log) records success. The repository was clean before and after inspection. The two C244 files match the exact copies in the supplied handoff.

The review used `AGENTS.md`, the current goal/status, C210's scope decision, the development-integration contract, C220's plan, C241's contract and C243's design/source inventory. The current goal is checked transport of authoritative source meaning; its next unmet gate is a bounded second-target/source-traceability proof. A source-level capture decision is a legitimate incremental step toward that gate. It does not remove the later native or comparison requirements.

## Findings

### 1. Both conflicting contract boundaries are explicitly resolved

The decision identifies the existing prohibition on a custom loader extension and the existing live forward/inverse map requirement, then proposes changing both together. It permits only one observer `_import_node` override, retains the built-in converter and defaults of the other virtual methods, and forbids generation overrides, product scripts, identity injection and geometry/resource mutation. It separately replaces postconversion map reliance with a live original association, observed replacement edge and final live membership. It expressly does not repair `GLTFState` or claim that its old inverse lookup applies to replacement nodes. This is a concrete design choice, not a deferred choice disguised as an implementation task. [C244 decision, lines 18–35](https://github.com/Omegapy/OntoKin/blob/8264db6e36b0c6118cf5b7ab2e41724569f72d90/docs/engineering/second-target-c244/DECISION.md#L18-L35); [C220 plan, lines 23–29](https://github.com/Omegapy/OntoKin/blob/6bf7b9b1d53a4d8181679bf7bd8f7b5147023c01/docs/engineering/second-target-c220/PLAN.md#L23-L29); [C241 contract, lines 79–113](https://github.com/Omegapy/OntoKin/blob/6bf7b9b1d53a4d8181679bf7bd8f7b5147023c01/docs/engineering/second-target-c241/CONTRACT.md#L79-L113).

The proposed exception changes only the finite capture route. Original authority, numerical tolerances, retained failure outcomes, useful-image requirements, process limits and the two-start ceiling remain binding. Process-local identities are explicitly excluded as a reopen identity substitute. The old C220/C241 documents need not be rewritten to conceal their earlier requirements; publication must make the adopted amendment and its exact scope easy to find.

### 2. The pinned source supports the proposed observation window

In `gltf_document.cpp` lines 7058–7085, all import-node callbacks execute before the mesh-root conversion and all extension post callbacks. The callback receives the state, exact GLTFNode and live scene-node pointer. `gltf_state.cpp` lines 375–389 confirms that both map directions use the stored pointer map. The proposal therefore checks this association at a phase where the selected conversion has not retired it, rather than attempting to validate a stale pointer later. Callback arrival order is explicitly excluded as an identity rule. [Retained loader source](https://github.com/godotengine/godot/blob/35e80b3a8822a9df9be390814b62f44c0a9c69e8/modules/gltf/gltf_document.cpp); [retained state source](https://github.com/godotengine/godot/blob/35e80b3a8822a9df9be390814b62f44c0a9c69e8/modules/gltf/gltf_state.cpp); C244 decision lines 64–77.

The additional pre-callback `_process_mesh_instances` path is restricted to skinned nodes in the inspected source, lines 5888–5922. Fresh parsing of the exact fixture found no skins or node skin entries. The review does not generalize this result to other fixtures.

### 3. Signal-time identity and final values are correctly separated

`Node::replace_by` emits `replacing_by` at line 3259 while the old object still exists, but before children and ownership finish transferring. The converter calls `replace_by` before copying metadata and assigning the generated mesh, and deletes old nodes later. A direct callback can therefore record the identity transition, while completed arrays, materials, metadata and poses must be observed after `generate_scene` returns. The proposal makes precisely this distinction and prohibits dereferencing retired nodes. [Retained node source](https://github.com/godotengine/godot/blob/35e80b3a8822a9df9be390814b62f44c0a9c69e8/scene/main/node.cpp), lines 3222–3287; [retained converter source](https://github.com/godotengine/godot/blob/35e80b3a8822a9df9be390814b62f44c0a9c69e8/modules/gltf/extensions/gltf_document_extension_convert_importer_mesh.cpp), lines 46–95; C244 decision lines 72–87.

Exactly 18 original nodes, 18 distinct descendant replacement events and 18 final live `MeshInstance3D` objects are required. Unknown old identities, reused or intersecting IDs, cross-index swaps and missing/repeated events refuse the finite run. For this selected fixture, a complete chain is one observed replacement per source node; the decision grants no permission for a general multi-stage replacement algorithm. Traversal establishes membership only, not source identity.

### 4. Original metadata and observer actions remain distinguishable

The proposal requires each node's native metadata, scripts, signal connections, resources, parent/owner and instance identity to be captured before installing its observer connection. It labels these as phase-local snapshots, not one simultaneous scene observation. Final native capture precedes retained source metadata. C241's unsupported-type refusal, explicit mutation ledger and separation of original values from retained source remain applicable. [C244 decision, lines 64–70 and 96–99](https://github.com/Omegapy/OntoKin/blob/8264db6e36b0c6118cf5b7ab2e41724569f72d90/docs/engineering/second-target-c244/DECISION.md#L64-L99); C241 contract lines 115–142.

Flags zero prohibit deferred or persistent observer subscriptions. The callback owner and mutable registry remain outside the imported scene, keyed to the exact state. The proposed extension remains stateless and may not install an observer script or source identity tag on product nodes. Actual lifetime management, typed serialization and absence of side effects still require independent implementation review.

### 5. Extension selection and root shape are finite prerequisites

The default extension preflight returns `OK` when there is no override; the inspected loader adds such extensions to its active list. The proposed sole `_import_node` override is therefore not contradicted by a requirement to override a second virtual method merely to be selected. Registration order, exact build/project/extension inventory and unexpected callbacks still must be bound before execution. A list of supported glTF extension names is not accepted as a callback inventory. [Retained extension source](https://github.com/godotengine/godot/blob/35e80b3a8822a9df9be390814b62f44c0a9c69e8/modules/gltf/extensions/gltf_document_extension.cpp), lines 62–72 and 134–149; retained loader source lines 6535–6541 and 6753–6762; C244 decision lines 58–62.

Fresh fixture parsing confirms exactly 18 node-to-mesh pairs matching the immutable C220 part map, five meshes, one primitive per mesh and no `GODOT_single_root` extension. The inspected loader creates a synthetic nonmesh root in this case. The proposal refuses a product mesh root or any root replacement; it does not silently extend the proof to the separately visible root conversion path. Retained loader source lines 6857–6905 and 7074–7077; C244 decision lines 79–82.

### 6. Fatal-error handling is a requirement, not an asserted implementation

The source uses `ERR_CONTINUE` for callback errors, so a callback error return alone does not establish that generation stopped. The proposed external fatal latch and complete event accounting must veto successful emission, packing, save, reopen and acceptance. It also explicitly requires coverage of engine and other-extension errors outside that latch and blocks admission when coverage is unknown. Failure evidence and bounded cleanup remain allowed. This closes the earlier logical gap without pretending that a complete diagnostic-capture mechanism already exists. Retained loader source lines 7070–7082; C244 decision lines 89–94.

An implementation cannot claim this requirement passed merely because all expected identity events arrived or the engine returned a root. Demonstrated error coverage remains an execution-entry blocker. That limitation does not invalidate selecting this design before implementation.

## Approval limits and integration conditions

No blocking defect was found in the design decision within this review's assigned scope. The corrected draft is suitable for adoption as a narrow, source-supported experiment design once its independent controls review and relevant documentation checks pass and the integrator follows the expected-head lease rules. This report does not independently approve the synthetic record validator's implementation or every control; another reviewer owns that scope.

The retained executable's embedded revision differs from the inspected upstream source, and the pinned executable is absent in this review environment. No installed-source equivalence, callback execution, pointer safety in that build, native fidelity, rendering route, hard resource enforcement, reservation, observer/emitter implementation or R07 acceptance is established. No native process, source export, product aggregate or new fixture generation occurred.

Publication should record the new independent approval/adoption separately and preserve the original draft and self-audit history. The historical decision's statements that it was draft and lacked an independent subagent refer to the earlier authoring stage; they must not be mistaken for this review's status. The next work after a reviewed integration is separately bounded implementation preparation under the unchanged zero-start and entry-gate constraints. If the independent controls reviewer finds a blocker, integration must remain held despite this design-only approval.
