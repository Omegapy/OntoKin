# C251: held controlled scene-tree attachment

**Held source only. Neither GDScript parsing nor native execution has run.**
C251 adds one controlled attachment of the original imported root to the
actual Godot scene tree. Scene-tree membership is needed for a later native
world-transform read. This component performs no seek, playback, advancement,
world-pose read, rendering or persistence operation. R07 remains pending.

[attachment.gd](attachment.gd) owns one fresh C250 preparation after actual
generation-return acknowledgement. The complete result, including any partial
refusal, remains under `playback_preparation`. No caller supplies an accepted
receipt, and the consumed C246 registry is never read a second time for capture.
An entry thread check refuses a known non-main-thread caller before starting
C250; the receipt records that preparation was not attempted. Each component
instance is single use, including refused calls and reentry.

## Supported host and transition

The source obtains `Engine.get_main_loop()` and its actual root `Window`.
It accepts only a ready, script-free root Window in that same SceneTree, with
no parent, owner, existing child or current scene. The host must already be
paused, its root processing disabled, and physics interpolation disabled both
globally and on the root. Main-thread inheritance is explicit. No tween may
be registered. The component never changes these host settings.

The SceneTree's own script identity and metadata are recorded and must remain
unchanged. This permits a later frozen external launcher that extends
SceneTree; its script/project bytes still need independent admission binding.
An empty ready Window is an observed precondition, not evidence that timers,
native extensions, diagnostics or every external actor have been isolated.

The original fixture contains exactly 20 nodes: one Node3D root, 18 mapped
MeshInstance3D children and one AnimationPlayer. Product nodes retain inherited
processing/thread/interpolation modes, no enabled processing/input flags,
no groups, no scripts and no queued deletion. Their complete outgoing signal
inventory must have zero receivers. The selected host signals are
`SceneTree.node_added`, `SceneTree.tree_changed`, `Window.child_entered_tree`
and `Window.child_order_changed`. Unrelated native Window connections are not
silently erased. Any selected receiver produces a count and explicit refusal;
arbitrary Callable payloads are not read.

The sole transition is `parent.add_child(root, false, Node.INTERNAL_MODE_DISABLED)`.
The mutation ledger records ATTEMPTED before calling it and RETURNED after it
returns. Its partial actual readback remains visible after failure. The source
never rolls back, renames, changes ownership, rebuilds children, repairs
resources, repeats the attachment or recaptures a consumed session.

The host Window has no Node3D transform, so this introduces no additional 3D
parent frame. The root and 18 part nodes retain their actual raw local
Transform3D basis columns and origin. Top-level and scale-disable flags must be
false. Those local values are preservation evidence; they are not substituted
for any of the still-missing 126 native world poses.

## Explicit after-attachment predicate

[attached_inventory.gd](attached_inventory.gd) keeps the original C249 validator
unchanged. Detached reads call its original method. Attached reads use a
separate copy whose only scene-policy differences are the declared root parent
and membership of every original node in the exact host tree. The source/API
checker compares that copy against the pinned original with those explicit
changes. C250's unchanged read-only inventory then rechecks the player, library,
animation, all 36 tracks and targets, and every mesh/material selector.

Additional fresh controls capture all 20 nodes' metadata, names, parents,
owners, readiness, processing, interpolation and signals, plus the 19 raw
local transforms. Only these observed lifecycle differences are allowed:

| Field | Declared transition |
| --- | --- |
| Root parent / host children | null → exact Window; empty → exact original root |
| Host node count | 1 → 21 |
| All product nodes | detached/not-ready → same-tree/ready |
| Effective interpolation | retained detached value → false under inherited OFF host |
| `can_process` observation | explicitly not observed while detached → observed false |

`Node.can_process()` itself has a native error fallback outside the tree. The
detached receipt therefore records `NOT_OBSERVED`, without calling it or
pretending that its fallback is an observation. No product property is set to
make the after-state agree. The expected transition changes only receipt data.

Entry/ready notifications and signals still run under disabled ordinary
processing. In particular, the pinned AnimationMixer clears caches and emits
`caches_cleared` on entry; AnimationPlayer may autoplay at READY. Fresh checks
therefore retain MANUAL mode, active status, the same stopped assignment,
empty autoplay/current name, position zero, length two, and disabled internal
processing. Host, node, inventory and player controls receive repeated reads.
[BINDINGS.json](BINDINGS.json) identifies the exact inspected primary sources.

## Evidence and limits

The [Python model](inert_model.py) composes unchanged C250/C249/C248/C247 models.
Its host, IDs, NodePaths, signal counts, transforms and lifecycle effects are
fabricated test inputs. [Tests](test_inert_model.py) exercise persistent drift,
partial mutations and single-use behavior. The model does not execute C246
callbacks, parse GDScript or prove native signal ordering. Receipt shapes and
enumeration order are model abstractions, not a native serializer.

The complete earlier raw mesh arrays/material parameters remain retained; the
repeated inventory checks reread their bindings and selected controls, not
those raw values. A same-identity value change remains an explicit limitation
witness. Repeated comparisons use Variant-style value equality, including its
limitations around signed zero; they do not prove byte identity, atomicity,
absence of transient mutation, native lifetime or complete diagnostic coverage.

Every permitted-thread finish retains a fresh complete registry receipt, even
when another post-attachment check has already refused. Any latched registry
fault makes the component incomplete while preserving the original error.
Unsupported-thread exits explicitly omit shared registry inspection; an earlier
retained registry receipt is preserved if present. This omission cannot pass.
Registry faults are only registry faults. Complete engine/extension diagnostic
interception, build lineage, frozen launcher and project isolation, hard
process/output limits and execution admission remain unresolved. This source
cannot turn a synthetic pass or empty registry fault list into native admission.
Useful images, serialization/raw sealing and save/reopen remain later gates.

## Offline checks

With `PACKAGE` naming the extracted successor handoff:

```sh
python3 -B docs/engineering/second-target-c251/test_inert_model.py
python3 -B docs/engineering/second-target-c251/verify_bindings.py --package-root "$PACKAGE" --output /tmp/c251-bindings.json
```

The binding checker runs the unchanged C250 and C249 binding/fixture checks too.
For author preparation only, `--new-source-root` can select the directory of
new C251 upstream files while the original C250 package supplies inherited pins.
This is the same byte binding; it does not change native settings or source.

[RESULTS.md](RESULTS.md) records author outcomes and limitations. Independent
review and actual published/saved identities belong to root's review and
handoff records. After this source is reviewed and handed off, stop.
[NEXT-TASK.md](NEXT-TASK.md) describes the next separate scope.
