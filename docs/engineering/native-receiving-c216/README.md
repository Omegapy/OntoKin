# C216 finite native receiving proof

This isolated experiment receives the unchanged accepted C210 assembly in one installed Blender build. [CONTRACT.md](CONTRACT.md) defines exact source authority, measured native loss and the two-start ceiling. Surface normals are the per-corner directions used for shading; native values are observed, never replaced with source values.

The source is additive. It does not modify the compiler, GLB writer, C211 held receiver, C214 authority or C215 loss adapter. The first native start imports once, preserves accepted source and semantics in the scene, captures measurements, saves the actual `.blend`, and renders one overview and one curved-surface detail. A separately approved second start reopens that exact scene, captures again, and renders the same views without reimporting.

## Before any launch

Read the contract and current repository coordination instructions. Commit this source and inspect the exact live state. In a clean checkout, create a new external run directory with:

```bash
python3 -IB docs/engineering/native-receiving-c216/run.py prepare --run /absolute/new/c216-run
```

Preparation reads and hashes files only. It copies the accepted source triple/reference, creates the C214 source-normal payload, preserves actual importer source bytes, binds this exact committed source and writes `plan.json`. It starts no Blender, source program or exporter. Use `check --run ...` to verify these inputs without native execution.

An independent reviewer and the root integrator must review the exact committed capture/helper/driver/contract, prepared plan and their byte hashes. An approval JSON for one phase has schema `ontokin.c216.native-approval/0.1`, decision `APPROVE_NATIVE_START`, `phase` (`import` or `reopen`), exact `sourceRevision`, canonical `planSha256`, `maxNativeStarts: 2`, nonempty `integrator`, and `independentReview: {path, file: {bytes, sha256}}`. Root creates this record only after actual review. It is retained review evidence, not cryptographic authentication.

Importer source checks also require an empty installed bytecode-cache inventory. Native receipts identify every actually loaded `io_scene_gltf2` module, its source hash, loader/origin and cache path before and after import and at phase closure. The capture records actual Python flags, refuses an initial external cache prefix, explicitly disables bytecode writing and selects a fresh empty private cache prefix. Requested environment variables alone do not establish which Python flags Blender actually used.

Only root runs an approved phase:

```bash
python3 -IB docs/engineering/native-receiving-c216/run.py launch --run /absolute/c216-run --phase import --approval /absolute/import-approval.json
```

Each phase consumes an exclusive reservation before process creation. Repeating an attempted or unknown phase is refused. The host retains command, selected environment settings, PID, exit status, deadline, process-group observation, logs, and native completion/failure files. The two phases each have a 240-second deadline and two Blender threads.

## Import review and reopen

After import is known complete, root may generate the unchanged C215 loss report with `report --run ... --phase import`. The independent reviewer must separately check actual raw positions/winding/normals, complete denominator, source/build/settings/scene bindings, all seven pose samples, material values, raw extras and mapped semantics. Review both rendered images. Any failed, unknown or missing gate stops this task.

A reopen approval additionally contains `priorImportEvidence`, mapping each reviewed run basename to its exact `{bytes, sha256}` descriptor. Required entries are `received.blend`, `input-lock.json`, `import-process.json`, `import-native-complete.json`, `import-observations.json`, `import-details.json`, `import-overview.png` and `import-sphere-detail.png`. Extra reviewed run files may also be bound. Only then may root invoke `launch --phase reopen` with that approval. Reopen never imports or saves another scene.

## Interpretation and evidence

`input-lock.json` is completed after native save because the scene hash does not exist beforehand. Independent review must compare every prelaunch input identity with that final lock. Both phases bind the same scene bytes. Raw C215 observations and auxiliary details precede rendering so failure cannot erase captured measurements. The host `report` command keeps all C215 fidelity/provenance/receiving flags false.

No result is declared by source existence, successful launch, metadata retention or small normal error. The independent final review decides whether this finite exact-authority/disclosed-loss receiving promise was met. C211’s original `2e-6` failure remains a separate failed historical gate. Build lineage `Unknown` remains explicitly unresolved; exact executable and importer bytes identify this finite experiment only.

The root handoff retains prepared inputs, actual outputs, independent reviews, failure history, process receipts, saved scene, renders and the complete restorable source. Stop after the verified saved C216 handoff. No second destination or authoring comparison belongs here.
