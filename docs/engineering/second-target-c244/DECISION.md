# C244/0.2.0: proposed observation-chain identity boundary

**Recommendation: permit the narrow design below. Status: draft, not adopted.**
Independent review and integration are pending. C220 and C241 remain authoritative
until that review and integration occur. This document replaces the ambiguous
C244/0.1.0 draft, not an adopted contract. It authorizes no native process and
implements no observer, emitter, launcher or production receiver.

## Decision and exact proposed amendments

Original baseline: `6bf7b9b1d53a4d8181679bf7bd8f7b5147023c01`.
The [C243 investigation](../second-target-c243/DESIGN.md) establishes a source-level
capture gap, not an installed-runtime defect. The proposed resolution is one
observer-only `GLTFDocumentExtension._import_node` override with direct,
nonpersistent `Node.replacing_by` subscriptions and an external session-owned
registry. The built-in converter and original fixture remain mandatory.

If independently approved and integrated, **both** boundaries change together:

* C220 section 3 and C241 section 3 permit this single observer extension in the
  future reviewed experiment. Other virtual methods keep their pinned defaults.
  No generation override, editor import, converter replacement, product script,
  source label injection, geometry/resource mutation or setting change is allowed.
* C241 section 4 uses a live bidirectional loader-map check **before conversion**,
  followed by a complete observed replacement chain and final live membership.
  This explicitly replaces reliance on postconversion loader-map equality for
  these 18 objects. It neither repairs `GLTFState` nor claims that its old inverse
  lookup works on replacement nodes. Postconversion calls into that stale map are
  prohibited. Reopen identity remains a separate persistence contract, not a
  reuse of process-local instance IDs.

This is the design choice submitted for review now, not a request to postpone the
choice to implementation. Actual installed-build binding and execution admission
are later gates. Rejection of this proposal leaves the original boundary in force
and requires a separate, pinned engine-side map-repair decision.

## Evidence and scope of the source argument

All implementation references are pinned to Godot
`35e80b3a8822a9df9be390814b62f44c0a9c69e8`. The unchanged
[C243 source inventory](../second-target-c243/evidence/PRIMARY-SOURCES.json)
binds nine complete source files, their Git blob hashes and handoff locations.

| Inspected source | Relevant fact |
| --- | --- |
| [generate_scene](https://github.com/godotengine/godot/blob/35e80b3a8822a9df9be390814b62f44c0a9c69e8/modules/gltf/gltf_document.cpp#L7038-L7086) | All import-node callbacks precede root conversion and extension post callbacks. Callback errors use ERR_CONTINUE. Callback iteration order is not an identity rule. |
| [Converter](https://github.com/godotengine/godot/blob/35e80b3a8822a9df9be390814b62f44c0a9c69e8/modules/gltf/extensions/gltf_document_extension_convert_importer_mesh.cpp#L37-L95) | Replacement precedes metadata and mesh assignment; old nodes are later deleted. No state-map repair appears in this file. |
| [replace_by](https://github.com/godotengine/godot/blob/35e80b3a8822a9df9be390814b62f44c0a9c69e8/scene/main/node.cpp#L3222-L3287) | The direct signal occurs with the old object alive, before children and ownership finish transferring. Signal-time values are not final scene observations. |
| [State lookup](https://github.com/godotengine/godot/blob/35e80b3a8822a9df9be390814b62f44c0a9c69e8/modules/gltf/gltf_state.cpp#L375-L389) | Forward and inverse functions read the stored pointer map, not the external observer registry. |

The retained candidate's embedded revision differs from that source. Moreover,
its pinned executable path is absent in this rerun environment. Neither source
inspection nor the inert tests below establishes installed extension selection,
callback execution, pointer safety or native fidelity. No binary is substituted.

## Required observation sequence

Before generation, freeze the exact build/project/extension inventory and order,
keep extension instances stateless, and own mutable observation state in an
external session keyed by the exact GLTFState. A supported-extension-name list
alone is not an inventory of callbacks. Unexpected overrides or an unbound session
block the experiment. All original source/GLB/sidecar bytes remain separate.

For each live preconversion callback, derive the index from the loader, verify
both map directions and its exact GLTFNode/mesh association, and capture original
native metadata, scripts, signal connections, resources, parent/owner and instance
identity. Snapshot native values before installing that node's observer connection.
The snapshots are phase-local, not a claim of one simultaneous whole-scene state.
Only then connect with flags zero: direct, nondeferred and nonpersistent. Never
attach an observer script or source identity tag to a product node.

Require exactly 18 distinct original nodes with the locked node-to-mesh pairs.
Every capture and subscription must precede conversion. Each signal records one
index-bound old-to-new native identity edge while the old node is live. Reject
unknown old identities, duplicate indices, duplicate old/new IDs, old/new set
intersection, cross-index swaps, cycles, repeated or missing edges. Do not require
ascending index callback order. Never dereference a retired node.

The fixture requires a synthetic nonmesh root, zero product-root replacements
and exactly 18 descendant replacements. The source has a separate mesh-root
replacement path before import_post; that path is understood but **refused for
this fixture**, not silently generalized. At the signal record only the identity
transition. After generate_scene returns, require 18 distinct valid live
MeshInstance3D objects in the returned scene and capture their completed native
metadata, arrays, materials and evaluated poses. Traversal proves membership,
not source identity. Final observations are mandatory, never inferred from the
absence of an error or a returned root.

An external fatal latch and complete event accounting must veto successful
observation emission, packing, save, reopen and acceptance on any error. Returning
an error from a callback is insufficient. The future implementation must also
account for engine/other-extension diagnostics that do not reach its own latch;
unknown error coverage blocks admission. Failure receipts, partial raw capture,
diagnostics and bounded cleanup remain permitted and required. No retry follows.

Only after raw native observations are sealed may a separately declared stage
retain source metadata. Keep imported, observer-derived and source-retained facts
separate. All C221-C239 schemas, numeric tolerances, strict Blender-normal failure,
useful-image requirement, process budgets and two-start ceiling remain unchanged.

## Inert controls and stopping point

[test_decision.py](test_decision.py) checks synthetic records for the finite
identity/phase predicates. It does not call Godot, install signals, implement a
runtime registry or attest native metadata. Its fixed mesh tuple matches the
unchanged 185,236-byte GLB, SHA-256
`05ebe856d3fdb96dce4b6aa55906be5ae67501bcaede9112abc30b703905b5d8`.
The prior 12 controls pass but admit six reproduced invalid cases. The new suite
adds strict types, mandatory final observations, exact associations, disjoint
identity sets and explicit phase ordering. Passing it proves only those modeled
predicates, not every requirement above.

**Stop:** deliver this corrected draft and its checked, offline-restorable handoff.
The next action is independent review of this exact decision and its controls,
followed by coordinated integration or a recorded rejection. Do not start an
observer implementation until that review closes. No actual subagent execution
tool was exposed during this rerun; the author's re-audit is not independent review.
