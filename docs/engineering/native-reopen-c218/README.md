# C218: one saved-scene reopen observation

This separately versioned experiment observes whether the exact C217 saved Blender scene preserves source authority, object meaning and measured native geometry after one reopen. It does not import a GLB or repair missing persistence. Read the [contract](CONTRACT.md), [observer](capture.py), [host coordinator](run.py) and [fixed installation bindings](build_bindings.json).

The source scene is C217's `agent-results/namespace-repair/run-01/received.blend`: 3,864,164 bytes, SHA-256 `dd8a6f32e96e45ec92207ee3417af0b3c88a6f9d898cff6d07e4366ab79993c4`. C217's executed source is `6af212204d58fbac2a98f3cded44facd67c52528`; its one-start import plan is consumed and closed. This observer gets at most one separately reviewed start.

## Scope and limits

The native process opens that scene with automatic scripts disabled. It reads the existing four authority texts, scene/object mappings, native identity extras, all 18 product objects, 7,800 triangles and 23,400 corners, materials and the same seven-time/126-pose samples. It verifies the saved camera/light/render recipe without reconfiguring it, then renders at most two predeclared views using the existing cameras. It never saves the scene, creates source texts or mappings, rebuilds product geometry or replaces normals.

Exact import/reopen persistence and fidelity to authoritative source are different checks. The original C211 `2e-6` normal-fidelity failure remains failed. C215's unchanged reporter supplies non-accepting loss data; it does not establish receiving acceptance. An independent review must account for every passed, failed and unrun gate before any separate finite receiving decision.

## CPU-only preparation and checks

Prepare only from a clean committed checkout and the verified C217 run directory. `prepare`, `check` and `report` never start Blender. The exact source, prepared inputs, plan and independent prelaunch review must be saved durably before root invokes `launch`.

```bash
python3 -IB -m unittest discover -s docs/engineering/native-reopen-c218 -p 'test_*.py' -v
python3 -IB docs/engineering/native-reopen-c218/run.py prepare --run /absolute/new/run-01 --prior-run /absolute/verified/c217/agent-results/namespace-repair/run-01
python3 -IB docs/engineering/native-reopen-c218/run.py check --run /absolute/new/run-01
```

Root alone creates the independent-review/root approval record for the exact committed source and plan. The only native route is `launch --phase reopen --approval /absolute/approval.json`. Any reservation consumes the single allowance, including launch failures and unknown outcomes. There is no retry, reimport, second destination or unplanned rerender route. Existing C211, C216 and C217 schedules remain closed.

The scene is bound at its existing location to avoid another large scene payload; `sceneArchivePath` names its preserved handoff location. Absolute execution paths record this host, not portable replay authorization. The final handoff must contain the exact source, inputs, prior scene and full observations with a verified restore path. Stop after the observed result or a concrete preparation blocker.

## Source lineage

[origin_guard.py](origin_guard.py) and [build_bindings.json](build_bindings.json) are byte-for-byte copies from C217's exact executed source. Read-only observation and authority functions retain its data shapes. New code replaces import/save/mapping/setup with a single strict reopen and verifies the persisted review setup. The coordinator adds cleanup of its owned process group if an exception occurs after process creation. [Origin controls](test_origin_guard.py) and [reopen controls](test_reopen.py) exercise these boundaries without native execution.
