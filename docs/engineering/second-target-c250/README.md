# C250: held detached playback preparation

**Held source only. GDScript parsing and native execution have not run.**
This bounded precursor prepares the already inventoried animation for a later,
separately reviewed pose-observation stage. It keeps the imported scene detached
and its player stopped, selects MANUAL automatic-processing mode while retaining
`active = true`, and assigns the actual inventoried animation without playback.
No seek, advance, tree attachment, world-transform reading or pose comparison
belongs to this component.

[playback_preparation.gd](playback_preparation.gd) owns exactly one fresh C249
capture after actual generation-return acknowledgement. The complete C249
receipt, including any partial refusal, remains under `animation_inventory`.
It never accepts a caller-supplied receipt or consumes the registry a second
time. Prior material, mesh-array and observed identity-chain receipts remain.

Before and after each setter, a policy-aware read-only inventory checks the
live player, library, animation, all 36 track paths and 18 targets, scene
membership and mesh/material selectors against the retained observations.
Only the two explicitly declared settings may differ. The baseline C249
inventory is not rerun on intentionally changed player state. This source
reuses its pinned read-only scene/fact helpers without editing inherited code.

Both internal idle and physics flags must be false at every boundary. Active
reads true at every boundary; the native mode setter temporarily toggles it
while changing the callback. Every receiver of `current_animation_changed` refuses; the receipt
retains the connection count and explicitly omits arbitrary Callable payloads.
A script-free player is not itself proof of receiver absence. After assignment,
`is_animation_active()` guards position/length reads; actual assigned key,
position 0, length 2 and stopped/empty-current state remain distinct observations.

Each mutation ledger records ATTEMPTED before the setter, RETURNED after the
call returns and its actual readback. A failed readback retains prior receipts
and partial observed changes. No rollback, corrective setter, retry or registry
reconsumption is attempted. Reentry and repeated use latch refusal. These
observations detect lasting drift; they do not prove atomicity or exclude a
transient receiver, concurrent mutation or native lifetime hazard.

The pinned `Node3D.get_global_transform()` requires SceneTree membership. A
detached call can return a default transform with an error, which cannot count
as an observation. A controlled tree-attachment lifecycle needs a separate
design and admission; this increment does not implement it. All 126 world poses
therefore remain pending. Future sampling also retains C241's diagnostic,
build-lineage, reservation/resource, raw-sealing and serialization gates.

The [synthetic model](inert_model.py) composes unchanged C249/C248/C247 models.
Its identities, NodePaths, getters and setter effects are fabricated inputs;
its mutation hook exists solely for adversarial controls. Passing Python checks
cannot establish GDScript validity, signal behavior or installed-engine truth.
[BINDINGS.json](BINDINGS.json) pins inherited primary evidence and the separate
API review sources without duplicating their payloads.

## Offline checks and review

The [author controls](test_inert_model.py) exercise complete preparation and
adversarial identity, lifetime, signal, partial-mutation and reentry cases.
The [binding checker](verify_bindings.py) verifies pinned upstream bytes, public
API names, unchanged inherited authority, original fixture bindings and lexical
scope restrictions. It does not parse GDScript.

With `PACKAGE` naming the extracted successor handoff:

```sh
python3 -B docs/engineering/second-target-c250/test_inert_model.py
python3 -B docs/engineering/second-target-c250/verify_bindings.py --package-root "$PACKAGE" --output /tmp/c250-bindings.json
```

Before packaging, `--supplement-root` may identify the current handoff directory
that holds the new C250 API-review source pins. The inherited package supplies
all unchanged earlier pins. Both routes verify the same declared bytes.

Author controls and binding checks have executed. [RESULTS.md](RESULTS.md) and
[REVIEW.md](REVIEW.md), added by the root coordinator, record exact checked
revisions, independent findings and publication outcomes. Independent approval
and saved delivery must be established from those records and their receipts. R07 and the original strict Blender-normal failure retain
their previous states. No native, parser, source/product or aggregate start was
introduced.
