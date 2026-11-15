# C248: held final native material-parameter snapshot

**Held source only. No GDScript parser or native process has run.** This
component reads the final material parameters used by the original 18 parts
and binds them to the two original source materials. It preserves actual
native values and refuses unsupported material routes. It grants no execution
admission, native acceptance, full raw-capture completion or R07 pass.

The [source](materials.gd), [inert model](inert_model.py),
[controls](test_inert_model.py) and [binding checker](verify_bindings.py) are
isolated here. The existing C246 observer, C247 reader, contracts, input bytes,
numerical checkers and tolerances remain unchanged. [RESULTS.md](RESULTS.md)
separates the executed Python checks from the unexecuted native implementation.

## One owner of the capture chain

A future independently admitted caller must report actual synchronous
generation return to C246, then call
`capture_after_generation_return(state, root)` on a fresh C248 reader once.
C248 creates its own fresh, unchanged C247 reader and invokes it exactly once.
C247 alone closes the C246 registry entry and returns the internally sourced
identity/mesh-array receipt. C248 accepts no caller-supplied receipt and never
calls `Registry.close_state` a second time. Running C247 beforehand consumes
that registry state; C248 then refuses without retrying or reconstructing it.

C248 retains the actual C247 result, including a partial refusal. If that
component completes, C248 rechecks final root/membership, source node and mesh
associations, and each current native node/ArrayMesh identity. It never reads
the stale GLTFState loader map. Names, traversal order and similar material
values are not identity fallbacks.

The original fixture has one primitive per source mesh. The pinned importer
assigns that primitive's source material to the corresponding native surface.
C247 supplies the already checked primitive-0/surface-0 association. The exact
source material association is:

| Original source meshes | Original source material |
| --- | --- |
| 0, 1 | 0 |
| 2, 3, 4 | 1 |

The [binding inventory](BINDINGS.json) pins and checks all 18 source node/mesh
joins, all five primitive/material joins and both source material definitions.
This is a source-supported association for the frozen import route, conditional
on still-unresolved installed build lineage and settings. C247 did not retain
material identities. C248 observes those identities itself and does not claim
to compare them with an earlier C247 material identity.

## What is observed and what is refused

Each part retains its source node/mesh/primitive/material indices, native node
and mesh identity, native surface, material-selection identities, actual
instance transparency, material identity/class and typed material values.
The values include native `Color`, separate red/green/blue/alpha components,
metallic, roughness, culling and transparency enums. No expected source factor
fills a missing observation. No value is normalized, rounded or converted.

Native material selection follows node override, then surface override, then
mesh-surface material. The source verifies this precedence in
[MeshInstance3D](https://github.com/godotengine/godot/blob/35e80b3a8822a9df9be390814b62f44c0a9c69e8/scene/3d/mesh_instance_3d.cpp#L384-L401).
The locked route requires no node/surface override or overlay, one surface,
and agreement between the observed active and mesh-surface materials. It also
records the separate GeometryInstance3D transparency multiplier and requires
its supported value of zero. An unexpected selector is preserved before refusal.

Only script-free `StandardMaterial3D` is supported. The reader records and
checks 13 feature flags, 25 general flags, 19 texture slots, the next-pass
identity and 15 finite route settings. Additional features, nonbaseline flags,
textures, extra passes, shader/ORM materials and unsupported settings refuse.
Texture and pass identities are retained; their payloads are not traversed.
Refusal records an omission marker for unsupported payloads. The texture-repeat
flag remains enabled because that is the inspected native default, even when
all texture slots are empty. The exact inventories/defaults and public getter
bindings are preserved in [BINDINGS.json](BINDINGS.json).

Native RGB/alpha and PBR factors must be finite floats in the finite contract's
unit interval. Known culling and transparency enums remain raw, including values
that would fail a later comparison with this source fixture. This reader does
not apply the C234 numerical or mode comparison and does not claim complete
rendered appearance. Inactive feature parameters and mode-specific appearance
outside this finite parameter observation are not a complete material export.

The storage label `srgb-rgb-linear-alpha` follows the pinned
[GLTF importer](https://github.com/godotengine/godot/blob/35e80b3a8822a9df9be390814b62f44c0a9c69e8/modules/gltf/gltf_document.cpp#L3006-L3019)
and [Color conversion](https://github.com/godotengine/godot/blob/35e80b3a8822a9df9be390814b62f44c0a9c69e8/core/math/color.h#L199-L204).
The importer converts source linear RGB for native storage while preserving
alpha. C248 reads that native storage without another conversion. The label
does not attest the installed build or establish source fidelity.

Shared native materials and separate copies are both allowed. One native
material identity cannot claim different source material indices or inconsistent
raw snapshots. Each part's row is retained before its getters run, so a refusal
preserves earlier complete parts and the current partial observation. A full
second surface/material read must equal the first, followed by final live
membership and registry-fault checks. Lasting changes are detected; transient
concurrent mutation and atomic capture remain unproved.

## Bounds, limitations and recheck

Traversal is capped at 64 scene nodes; material loops use the fixed inventories
above and at most 18 part rows per pass. Unknown inventory sizes refuse before
enumeration, with counts and an omission marker. The component does not read
texture bytes or recursively follow additional passes. These are finite reader
bounds, not hard memory/process/time/diagnostic enforcement. Native getters and
the included C247 readback can allocate before returning; detached receipts
can duplicate observations. The C247 limits and codec-readback limitations
continue to apply.

The returned detached Dictionary is not a serialized C238 member or saved
native scene. Build lineage, diagnostic coverage, animation/pose observations,
raw-capture sealing, exact serialization, useful rendering, persistence,
launcher, reservation and hard limits remain separate gates. The original
strict Blender-normal failure and all historical evidence remain unchanged.

From the restored repository, with `PACKAGE` denoting the extracted handoff:

```sh
python3 -B docs/engineering/second-target-c248/test_inert_model.py
python3 -B docs/engineering/second-target-c248/verify_bindings.py --package-root "$PACKAGE" --output /tmp/c248-bindings.json
```

The model composes the actual unchanged C247 Python reader. Its registry is
C247's synthetic completed-receipt provider, not C246's event model. Passing
these controls does not prove callbacks, GDScript parsing, native getter
behavior, precision or lifetime. There is no runnable native project or launch
command here. After independent review and confirmed saved handoff, stop.
[NEXT-TASK.md](NEXT-TASK.md) documents a separate bounded scope.
