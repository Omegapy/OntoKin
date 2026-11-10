# C192 Python participant — first edit submission

## Outcome

**Failed first formal submission.** One exact localized source edit reached the native Blender build, but the unchanged raw/native-to-final mapping gate rejected the outputs. The self-check passed final playback and failed mapping. The failed source, native scene, raw and final GLBs, native records, command logs, and delivery receipt are retained. This result is not delivery acceptance.

## Scope and provenance

The participant used local branch `work/c192-python-author`, starting at local freeze commit `9d1118f63195c8458aa804f2a99922cc780365aa`, tree `5a5b22ddc1763d876c6f10339f20112977ee699d`. The coordinator identified the same frozen tree at remote commit `25c5efb9a8d9b3cae2f4eebb6dc33c1dc7db5742`; this participant did not publish or move remote refs. Local writes are confined to this participant directory and `/workspace/scratch/d52b43d02a92/c192-runs/python`.

The participant read AGENTS, GOAL, STATUS, the frozen brief and targets, the input-freeze manifest, and the Python starter. The common verifier confirmed all 116 frozen files unchanged. The frozen direct runner and C191 Blender constructor, solver setup, validation, and recorded-output utilities are disclosed reusable preparation. This route supplies Python `DESIGN` data and does not parse `.ok`.

## Source edit and preserved candidates

The preserved initial copy is [source-00-starter.py](source-00-starter.py). The submitted editable source is [design-edit.py](design-edit.py), SHA-256 `03e0955c421541f144074bda5983a9363a9cccf32d5cf226c8a8f288f17bc798`.

Only `DESIGN['parts']['left_stop']['at_mm'][0]` changed, from 380 to 362.5 mm. A recursive comparison of the parsed dictionaries verified this as the sole changed scalar. All other values, identities, dimensions, colors, relationships, feeds, and physics settings are unchanged. Source bytes match the common recorder's submitted snapshot and the artifact's retained `source.py`.

## Commands and receipts

The native build command was:

```bash
python -B docs/engineering/contact-comparison-c192/shared/build.py --repo /workspace/scratch/d52b43d02a92/participants/python --route python --source /workspace/scratch/d52b43d02a92/participants/python/docs/engineering/contact-comparison-c192/participants/python/design-edit.py --out /workspace/scratch/d52b43d02a92/c192-runs/python/edit-build-01 --blender /workspace/scratch/d52b43d02a92/deps/blender-4.5.3-linux-x64/blender
```

The build exited 1. Its common recorder reported `successful: false` and `artifact_directory: null`; the partial artifact files remain at `/workspace/scratch/d52b43d02a92/c192-runs/python/edit-build-01/artifact`. [The delivery receipt](receipts/build-delivery.json) and [native build receipt](receipts/native-build-receipt.json) preserve the actual failure and timing. The outer recorded build elapsed time was 1.720239878 seconds. This is build duration, not participant wall time.

The self-check command was:

```bash
python -B docs/engineering/contact-comparison-c192/shared/check_delivery.py --repo /workspace/scratch/d52b43d02a92/participants/python --artifact /workspace/scratch/d52b43d02a92/c192-runs/python/edit-build-01/artifact --case edit --out /workspace/scratch/d52b43d02a92/c192-runs/python/edit-check-01
```

It exited 1 with `playback_pass: true`, `mapping_pass: false`, and overall `pass: false`. [The command receipt](receipts/self-check-command.json), [playback report](receipts/self-check-playback.json), and [mapping report](receipts/self-check-mapping.json) retain that distinction.

The frozen-input verifier passed. The documentation preservation/link checker also passed. Their exact commands, exit statuses, stdout, and stderr are in [input-verification.json](receipts/input-verification.json) and [documentation-check.json](receipts/documentation-check.json).

One earlier read-only search returned exit 1 because no C191/C192 entry matched in the documentation index. The chained identity reads did not run; a separate identity query then succeeded. [inspection-failure-01.json](receipts/inspection-failure-01.json) preserves the failed command and empty output. It was not a source or native-build attempt.

## Measured result

| Measurement | Observed | Required / interpretation |
| --- | ---: | --- |
| Left final travel | 182.500004768372 mm | 182.5 mm target; playback pass |
| Right final travel | 300.000011920929 mm | 300 mm target; playback pass |
| Right final signed gap | 14.999982900918 mm | 15 mm target; playback pass |
| Left contact-band entry | 1.455999985993 s | Within 0.005 s of 1.460 s |
| Final-playback maximum penetration | 0.052801333368 mm | Below 0.5 mm |
| Final-playback maximum rebound | 0.052794814110 mm | Below 0.1 mm |
| Common recorded samples | 481 | 240 Hz, 0–2 s |
| Continuously certified unrelated pairs | 20 | 20 required |
| Native-sample to final maximum vertex distance | 0.244637656707 mm | **Above 0.2 mm; failed** |
| Continuous raw-to-final full-clip bound | 0.271961073336 mm | **Above 0.2 mm; failed** |

The largest sampled mapping discrepancy is on the left shoe. [mapping-failure.json](receipts/mapping-failure.json) contains the per-part and per-lane details. These are measurements of retained outputs; no geometry, trajectory, tolerances, or shared code was changed to obtain a pass. One build does not establish repeatability of this failure. Independent coordinator scoring, native reopening, Khronos/Three.js readback, and receiving-application playback were not performed by this participant.

## Accounting and limits

Observed phase start: `2026-11-10T14:54:15+00:00`. Report finalized: `2026-11-10T14:58:15.156873+00:00`. Observed elapsed wall time through report preparation: **240.157 seconds**, within the 20-minute phase limit. Administrative commit and handoff completion are timestamped in the external submission receipt.

There was one source edit turn, one candidate after the retained starter, one native build attempt, one failed native build, one self-check, one first formal submission, and zero formal repair turns. No extra agent was spawned. One coordinator follow-up instructed preservation and submission of the unchanged-gate rejection; no design repair was supplied. No human intervention was observed. Provider token counts, provider cost, exact provider snapshot, and hidden internal model turns are unavailable and are not estimated.

The participant did not begin reuse. The first source and artifact are sealed for independent scoring before any reuse follow-up. This is a public shared-environment workflow result and supports no isolation, comparative advantage, or broad qualification claim.

## Artifact identities

[artifact-identities.json](receipts/artifact-identities.json) records exact paths, sizes, and SHA-256 values. The [artifact manifest](receipts/artifact-manifest.json) inventories all retained native and exported files. The principal hashes are:

| Artifact | SHA-256 |
| --- | --- |
| Native scene | `6469ee74cb5762496eac70fd263e4142c4a1c29a3c8e5200879c5c222e3731f3` |
| Raw GLB | `e29bf3d15092aed5f9535367d586e9970cdc62a7a9af13c227b5e32120ff9d06` |
| Final GLB | `9eea3d5931a26bff7ec8d4a98b1ba3f1963c0e89802a70e5e8284ae9d10828c1` |
| Canonical input | `1358dde89cb28862f827ddad9b56a1479f44677270b2d1ce77f6c2091db2f86c` |
