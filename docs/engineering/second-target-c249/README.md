# C249: held animation selection and track inventory

**Held source only. GDScript parsing and native execution have not run.** This
component identifies the imported animation resource and inventories its tracks
for the original 18-part fixture. A track is the native animation's record of
which object and transform property it changes. This prepares a later pose
observation; it does not assign, play, seek or evaluate that animation.

The [native source](animation_inventory.gd), [synthetic model](inert_model.py),
[author controls](test_inert_model.py), [binding checker](verify_bindings.py) and
[pinned inventory](BINDINGS.json) are isolated here. Existing C246–C248 sources,
fixtures, contracts and numerical limits are unchanged. [RESULTS.md](RESULTS.md)
separates executed Python controls from native behavior that remains untested.

## Capture ownership and retained evidence

A future admitted caller must report actual synchronous generation return to
C246 before calling `capture_after_generation_return(state, root)` on one fresh
C249 reader. C249 creates its own fresh C248 reader and invokes it once. C248
owns C247, and C247 alone consumes the C246 registry. C249 never closes that
registry, retries its consumed state or accepts a caller-supplied receipt.
Running an earlier capture separately first makes this fresh chain refuse.

The complete actual C248 result stays under `materials`, including a partial
refusal. On success it retains the earlier material, mesh-array and observed
replacement-chain receipts. C249 then verifies final node/mesh/material resource
identities, surface selectors and scene membership against those receipts.
It does not reread the earlier material parameter payload or claim that the
entire multiphase observation is atomic. It never calls the stale GLTFState
source-node map after conversion.

## What the selected animation association means

The unchanged source GLB contains one animation, `KeyedRack: Demo`, with 36
LINEAR channels: translation and rotation for each of the 18 source nodes.
Each source input accessor contains 121 times from zero to two seconds. The
[pinned importer](https://github.com/godotengine/godot/blob/35e80b3a8822a9df9be390814b62f44c0a9c69e8/modules/gltf/gltf_document.cpp#L7038-L7057)
creates one AnimationPlayer under the returned root, then imports each source
animation into that player's default library. Its
[resource insertion](https://github.com/godotengine/godot/blob/35e80b3a8822a9df9be390814b62f44c0a9c69e8/modules/gltf/gltf_document.cpp#L5753-L5763)
provides the source-supported finite association used here.

C249 requires exactly one direct, script-free AnimationPlayer child, one default
library and one animation key. It obtains the actual resource independently
through the library and the player and requires those references to agree.
Player/library/animation instance IDs, classes, actual keys, names, paths and
typed metadata remain in the receipt. Native names, resource names and scene
traversal order do not supply source identity. A `RESET` animation key is
refused because the mixer gives it special behavior.

This is a conditional association under the pinned importer route and unchanged
inputs, **not a public source-animation/native-resource pointer attestation**.
The public GLTFState animation-player getters are export-only and are not used.
The selected resource is an inspected candidate; no active playback selection
has been made. Installed-build lineage and actual importer behavior remain
unproved.

## Track target identity and supported metadata

The reader records the player's actual root NodePath, checks its shape before
lookup and requires it to resolve to the owned returned root. Each track's own
relative, nonempty NodePath must have zero property/bone subnames. The pinned
[mixer](https://github.com/godotengine/godot/blob/35e80b3a8822a9df9be390814b62f44c0a9c69e8/scene/animation/animation_mixer.cpp#L661-L714)
uses `get_node_and_resource`; for these node-only paths that delegates to the
same `get_node_or_null` lookup used here. The returned live instance identity
must match a preserved final replacement-chain endpoint. A path serves as the
native track's lookup instruction; an expected name or matching pose never
stands in for the returned object's identity.

All 36 native track indices remain explicit. Each row retains the actual
track type, path, enabled/imported flags, interpolation, loop wrapping,
compression flag, resolved native node identity, associated source node/mesh
and actual key count. Exactly one position and one rotation role must resolve
to each part. Track order can vary. Duplicate roles, missing or extra tracks,
scale/value/method/audio/animation/blend-shape tracks, disabled/nonimported
tracks, non-LINEAR interpolation and compressed tracks refuse. Compression
is checked before any key-count access. No key time or key value is read.

Native key counts must be positive and at most 4,096. This is a finite inventory
bound, not an assertion that the native keys equal the 121 source samples.
The raw count stays visible, even when it differs from 121. Payload fidelity,
interpolation behavior and the 126 world-pose comparisons remain later work.
The native duration must equal the source's exact two seconds; nonpositive or
nonfinite step, loop mode, capture mode and unexpected markers refuse.

The imported player must remain detached, unassigned and not playing, with no
autoplay, queue, section, next animation, root motion or nondefault speed/blend.
Its native active/idle defaults and other relevant callback modes are recorded
and checked. **C249 does not disable automatic advancement.** The detached-tree
requirement makes that an explicit prerequisite for the later assignment and
sampling component. No position/length getter that requires an assigned player
is called.

## Refusals, rechecks and limits

Every result retains prior receipts and partial current observations. Unsupported
metadata uses the unchanged C246 fact helper, retaining typed facts and refusal
markers. Each pass shares its finite 100,000-value/depth-32 budget across the
player and both resources. All scene members must be live, script-free, unqueued
and detached; other mixers, unexpected classes and hierarchy changes refuse.
The scene is capped at 64 nodes. Collection counts are checked before enumerating
unsupported library, animation or track payloads, with explicit omissions.

Two complete inventories must agree. Each pass rechecks scene membership,
source/resource selectors and actual player/library/animation lookups after the
track reads. A final registry-fault check also remains required. These reads
detect observed lasting drift; they do not establish atomicity, exclude
transient changes or prove native lifetime safety under concurrent mutation.
Native list/getter allocations happen before returned counts can be checked.
Hard memory, time, process and output limits remain later admission work.

The returned Dictionary is detached observation data, not serialized C238
output or a persisted scene. Raw sealing, exact serialization, full diagnostics,
pose evaluation, rendering, native persistence, installed lineage and the
launcher/reservation remain separate gates. R07 stays pending. The original
strict Blender-normal failure remains unchanged.

## Offline recheck

With `PACKAGE` denoting the extracted handoff:

```sh
python3 -B docs/engineering/second-target-c249/test_inert_model.py
python3 -B docs/engineering/second-target-c249/verify_bindings.py --package-root "$PACKAGE" --output /tmp/c249-bindings.json
```

The Python model composes the unchanged C248 and C247 models. C247's registry is
a synthetic completed-receipt provider; these controls do not run C246 callbacks.
NodePath parsing/resolution, lifetime, metadata and native getters are fabricated
model inputs. Passing controls prove none of their installed-engine behavior.
There is no runnable native project or launch command. After independent review
and confirmed saved handoff, stop. [NEXT-TASK.md](NEXT-TASK.md) names a separate
future component.
