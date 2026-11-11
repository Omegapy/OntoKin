# C200 pinned-exporter compatibility decision

This bounded repair addresses the two observed C199 exporter failures. The
[stopped C199 result](../static-tray-qualification-c199/RESULTS.md) remains
unchanged. Its N01 construction start is consumed, N02–N12 are unstarted, and
its coordinator and ledger must not be resumed or reset.

The selected implementation remains Blender **4.5.3**, build **67807e1800cc**.
No installed Blender file is changed. The two source frontends, canonical
record, box constructor, independent expected geometry, tolerances and ordinary
100,000-operation / 30,000-ms source limits retain their meaning and bytes.
This decision changes the invocation of the pinned exporter and adds an actual
startup receipt. It does not qualify a native export or authorize a new run.

## Exact source inspected

The installed distribution was read without launching Blender. Its exporter
sources are bound by these SHA-256 identities:

| Distribution-relative path | SHA-256 |
| --- | --- |
| `4.5/scripts/addons_core/io_scene_gltf2/__init__.py` | `82428a0415e11c27a285fd950f63e874add5ba2f8bacc6806ed762614560fa2e` |
| `4.5/scripts/addons_core/io_scene_gltf2/io/com/debug.py` | `a0112a1488ce1520f6554f1c337494845ab0aea9b683a73b0b747505d6a2fa94` |

The first identity equals the source hash recorded in
[C199's failure diagnosis](../static-tray-qualification-c199/FAILURE-DIAGNOSIS.json).
It also matches the complete UTF-8 bytes retrieved from the official
[Blender v4.5.3 source](https://github.com/blender/blender/blob/v4.5.3/scripts/addons_core/io_scene_gltf2/__init__.py).
The current branch of an upstream exporter is not substituted for the installed
distribution. The new execution lock must still bind the complete distribution
and dependency closure.

## Logging initialization and actual behavior

The pinned `export_loglevel` RNA property defaults to **-1**. The complete
`ExportGLTF2_Base.execute` method stores that value in `gltf_loglevel`, but
initializes its separate `loglevel` key only when the requested value is
negative. It later calls `Log(export_settings['loglevel'])` unconditionally.
The previous explicit **20** therefore bypassed initialization and produced the
recorded `KeyError`. The error was unrelated to geometry or elapsed budgets.

The new settings request **-1** and the worker requires the actual Blender
state `debug=False`, `debug_python=False`, `debug_value=0`. In the pinned
`set_debug_log`, zero resolves to Python `logging.INFO`, numeric **20**. Values
1–4 select other logging levels, while 102 would enable the exporter's profiling
branch even though its log level also resolves to INFO. Requiring zero binds both
decisions explicitly. The worker checks the pinned source hash and the actual
resolver result before export. After export it checks the logger's actual INFO
level and the separate error logger's ERROR level, numeric **40**.

The source-level CPU control executes the entire pinned Python `execute` method
with the reviewed 108 properties, substituting in-process observations for its
downstream native save and extension hooks. It exercises both compression-library
availability branches with compression disabled. Positive 20 reproduces the
original missing-key failure; -1 reaches the real pinned `Log` implementation,
the save boundary and both extension-hook boundaries. This is evidence for the
compatibility decision, not evidence that the native exporter completed.

## Inactive action-filter lifecycle

All **108** operator property/value pairs remain in the settings and in the
explicit `EXEC_DEFAULT` call. No argument is omitted. In particular,
`export_action_filter=False`, `export_animations=False` and
`will_save_settings=False` remain fixed. The worker still compares the entire
runtime property-name inventory with the complete frozen settings inventory.

In this pinned exporter, assigning False invokes an update callback that clears
`bpy.data.scenes[0].gltf_action_filter` and deletes that Scene property and
`gltf_action_filter_active`. Factory background startup has not initialized those
properties. The callback therefore needs valid empty state even though filtering
is inactive.

After saving the native scene, and immediately before invoking the exporter, the
worker initializes precisely those two transient properties. It uses the pinned
add-on's registered `GLTF2_filter_action` type for the empty collection and the
same `IntProperty` factory as the original callback. Before initialization it
requires one scene, that scene to be the current scene, no actions and no existing
filter properties. Unexpected existing state is rejected without clearing it.
It verifies an empty collection and zero active index, then passes False
explicitly. The pinned callback clears and removes the transient state; the
worker verifies that both properties are absent afterward and no action was
created. A completed operator that leaves this state behind is rejected.

The filter is never enabled. Initialization occurs after `scene.blend` is saved,
so these temporary properties are not included in the saved scene. Construction,
semantic metadata and delivered geometry are unchanged. This policy avoids
depending on omitted-argument defaults or remembered operator properties.

## Receipt retained on a later export failure

`native-startup.json` is written after compatibility checks and empty filter
initialization, before the exporter is called. It records the actual embedded
Python startup flags, Blender version/build, all effective operator arguments,
observed debug state, resolved logging level, empty filter observations and the
locked source/settings hashes. Its phase is `BEFORE_EXPORT` and its delivery
state is `NOT_EXPORTED`; it contains no success assertion.

An export exception leaves this receipt in the failed stage. A successful worker
additionally binds its hash and the post-export logger/filter observations in
`native-result.json`. Existing transaction promotion and failure retention remain
unchanged. C199 had no such startup receipt; this repair does not manufacture one
for its historical failed start.

## Focused child-free controls

[The new tests](../../../tests/test_static_tray_exporter_c200.py) inspect the real
worker helper bodies using Python's abstract syntax tree. They cover complete
argument coverage, the positive-level refusal, debug/profiling refusal, changed
source or resolver refusal, preexisting state preservation, scene/action limits,
callback cleanup, actual logger levels, nonfinished operator results and retained
startup evidence on an injected export failure. They create no subprocess.

The explicit pinned-source mode first checks both complete source hashes and
then executes the unchanged installed callback, logging resolver and complete
exporter method under controlled Python objects. Normal repository test discovery
does not depend on an installed Blender distribution and does not silently skip
these explicit source checks; the separately invoked mode records them as its own
five-method cohort.

```bash
python3 -B tests/test_static_tray_exporter_c200.py --pinned-exporter /absolute/pinned/blender/4.5/scripts/addons_core/io_scene_gltf2/__init__.py
```

The measured command and final results belong to C200's preparation evidence.
No native construction, receiving, rendering or author process is permitted by
these tests. A newly identified, independently approved schedule must bind the
changed worker/settings, preserved readers and sources, complete dependencies and
all commands before the next native start. That schedule must count the consumed
C199 start separately, retain the original 65,000-ms transaction structure, run
once, and stop at the first unexpected result.
