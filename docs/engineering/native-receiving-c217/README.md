# C217 namespace-aware import and capture

This isolated experiment repairs C216's module-origin guard, then permits at most one freshly reviewed Blender import, save and capture. A Python namespace package is a package directory without its own `__init__.py`; it must still resolve to the pinned importer inventory. [CONTRACT.md](CONTRACT.md) defines the source-authority promise, strict provenance checks, finite plan and retained limitations.

C216 failed before product import and did not record the rejected module's raw attributes. Its failed source and consumed plan remain unchanged. C217 preserves raw module metadata before validation, accepts only explicitly pinned namespace directories, and retains exact concrete-source and cache-origin checks. It does not change the accepted GLB, production compiler/exporter, held C211/C216 source, C214 source authority, C215 reporter or the failed C211 `2e-6` normal limit.

## Preparation and controls

Run the targeted CPU-only controls with `python3 -IB docs/engineering/native-receiving-c217/test_origin_guard.py`. They cover ordinary packages/modules, legitimate namespaces, missing/contradictory metadata, external/mixed/escaped locations, source drift, cache mismatches, retained raw rejection diagnostics and the actual static installed importer layout. These controls launch neither Blender nor the installed importer and do not establish native compatibility.

From a clean committed checkout, `python3 -IB docs/engineering/native-receiving-c217/run.py prepare --run /absolute/new/c217-run` verifies the installed build, copies accepted inputs, creates the exact C214 source-normal payload, preserves importer source bytes and binds all eight C217 source/contract/control files plus unchanged C214/C215 helpers. `check --run ...` verifies the same inputs without native execution.

The independent reviewer and root must approve that exact committed source and freshly prepared plan. Approval schema `ontokin.c217.native-approval/0.1` requires `decision: APPROVE_NATIVE_START`, `phase: import`, exact `sourceRevision`, canonical `planSha256`, `maxNativeStarts: 1`, a nonempty `integrator`, and `independentReview: {path, file: {bytes, sha256}}`. This record is retained review evidence, not cryptographic authentication.

## Sole native start

Only root runs the independently approved import:

```bash
python3 -IB docs/engineering/native-receiving-c217/run.py launch --run /absolute/c217-run --phase import --approval /absolute/import-approval.json
```

The exclusive reservation is consumed before process creation, including failed or unknown outcomes. There is no reopen route or automatic retry. Maximum wall time is 240 seconds with two Blender threads. The driver retains the exact command, environment settings, PID, exit status, deadline, process-group observation and logs.

Capture writes and fsyncs complete raw metadata before classifying any module. It verifies actual runtime/build labels, imports once, retains accepted source and semantics, saves once, captures all native corners/poses/materials, then renders the unchanged overview and sphere detail. Captured measurements precede renders so a rendering failure cannot erase them. Exact normal values are observed without replacing normals, meshes or materials.

## Independent review and stopping point

After a known completed import, root may generate the unchanged C215 loss report with `report --run ... --phase import`. Independent review checks the complete 23,400-corner denominator, positions/winding, normals/loss, all 126 poses, material values, native extras and retained source authority. It also reviews both images and exact source/build/settings/scene bindings. The saved scene hash completes the lock only after actual saving; no scene hash is pretended known before launch.

C215's fidelity/provenance/receiving flags remain false. Complete receiving acceptance remains unproved because saved-scene reopen is outside this task. Any failed or unknown process or unusable evidence is a preserved blocker. Historical C211 normal failure, unrun old corrections, C214 synthetic-only meaning, build lineage `Unknown` and unpinned system-library closure retain their meanings.

After this one observed result or a concrete preparation blocker, preserve source/evidence, finish the verified saved handoff and stop. A later task may review reopening the exact saved scene if the import result supports it. No second destination, general importer, runtime feature or authoring comparison belongs here.
