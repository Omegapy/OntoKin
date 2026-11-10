# C192 Python participant — reuse submission

## Outcome

**Both requested builds remain rejected by the unchanged 0.2 mm mapping gate.** The new 372.5 mm variant and the regenerated 362.5 mm source each pass final playback. Their native/raw-to-final mapping checks fail. The earlier first submission remains rejected and is not treated as an accepted baseline.

The coordinator independently scored the first submission before assigning this phase. Its first-score receipt identifies correct source localization, passing final playback, failed mapping, and matching canonical/native/raw/final bytes across routes. That score authorized the frozen reuse task; it did not accept the first delivery.

## Sources and preservation

First-phase commit: `375f0df7bb63e8d7b72c7f0cf41643db3000da22` on local branch `work/c192-python-author`.

The first editable source, [design-edit.py](design-edit.py), remains SHA-256 `03e0955c421541f144074bda5983a9363a9cccf32d5cf226c8a8f288f17bc798`. Its bytes still match the source in the first-phase commit. All **39 files** in the original first-build directory remain identical to the inventory captured before reuse. The first report and first-phase receipts are retained unchanged.

The new editable variant, [design-reuse.py](design-reuse.py), is a copy of that exact source with only `DESIGN['parts']['left_stop']['at_mm'][0]` changed from **362.5 to 372.5 mm**. Its SHA-256 is `c7f5e6755250b31dd7daed1af36320c279c69c417770a22d13af9ec248181c5e`. A parsed-dictionary comparison verified that this is the only changed scalar. [The edit receipt](receipts/reuse/source-edit.json) records both source hashes and the exact path changed.

This demonstrates retention and reuse of literal source variants. It does not establish reusable classes, parameters, libraries, or programmatic composition.

## Builds, checks, and retained failures

The participant executed the frozen commands below from `/workspace/scratch/d52b43d02a92/participants/python`, with the pinned Blender executable and unchanged shared implementation.

```bash
python -B docs/engineering/contact-comparison-c192/shared/build.py --repo /workspace/scratch/d52b43d02a92/participants/python --route python --source /workspace/scratch/d52b43d02a92/participants/python/docs/engineering/contact-comparison-c192/participants/python/design-reuse.py --out /workspace/scratch/d52b43d02a92/c192-runs/python/reuse-build-01 --blender /workspace/scratch/d52b43d02a92/deps/blender-4.5.3-linux-x64/blender
python -B docs/engineering/contact-comparison-c192/shared/build.py --repo /workspace/scratch/d52b43d02a92/participants/python --route python --source /workspace/scratch/d52b43d02a92/participants/python/docs/engineering/contact-comparison-c192/participants/python/design-edit.py --out /workspace/scratch/d52b43d02a92/c192-runs/python/reuse-edit-regeneration-01 --blender /workspace/scratch/d52b43d02a92/deps/blender-4.5.3-linux-x64/blender
python -B docs/engineering/contact-comparison-c192/shared/check_delivery.py --repo /workspace/scratch/d52b43d02a92/participants/python --artifact /workspace/scratch/d52b43d02a92/c192-runs/python/reuse-build-01/artifact --case reuse --out /workspace/scratch/d52b43d02a92/c192-runs/python/reuse-check-01
python -B docs/engineering/contact-comparison-c192/shared/check_delivery.py --repo /workspace/scratch/d52b43d02a92/participants/python --artifact /workspace/scratch/d52b43d02a92/c192-runs/python/reuse-edit-regeneration-01/artifact --case edit --out /workspace/scratch/d52b43d02a92/c192-runs/python/reuse-edit-check-01
```

Each build and each checker exited 1. Both common delivery receipts report `successful: false`, `source_unchanged_during_build: true`, and `artifact_directory: null`. Partial output is retained in the two artifact directories identified above; each contains its native scene, raw/final GLBs, canonical input, native records, source snapshot, and manifests.

The [reuse delivery receipt](receipts/reuse/reuse/build-delivery.json) and [regenerated-first delivery receipt](receipts/reuse/regenerated-edit/build-delivery.json) preserve exact commands, native runner arguments, return codes, build timings, and costs reported by the bounded runner. The [reuse native receipt](receipts/reuse/reuse/native-build-receipt.json) and [regenerated-first native receipt](receipts/reuse/regenerated-edit/native-build-receipt.json) retain the mapping errors. All stdout/stderr files, checker receipts, playback reports, and mapping failures are copied into the corresponding receipt directories.

At phase start, two read-only command launches failed before process creation because the exec-server transport disconnected. A following `pwd` command succeeded, and the original reads then succeeded. [transport-failures.json](receipts/reuse/transport-failures.json) preserves both failed launches. Neither was a native-build attempt and neither changed source.

## Measured outcomes

| Measurement | 372.5 mm variant | Regenerated 362.5 mm source |
| --- | ---: | ---: |
| Left final travel | 192.499995231628 mm | 182.500004768372 mm |
| Right final travel | 300.000011920929 mm | 300.000011920929 mm |
| Right final signed gap | 14.999982900918 mm | 14.999982900918 mm |
| Ideal contact | 1.540 s | 1.460 s |
| Contact-band entry | 1.535999866780 s | 1.455999985993 s |
| Native-sample to final maximum vertex distance | **0.292416239436 mm** | **0.244637656707 mm** |
| Continuous raw-to-final full-clip bound | **0.322647311932 mm** | **0.271961073336 mm** |
| Final playback | Pass | Pass |
| Mapping at unchanged 0.2 mm limit | **Fail** | **Fail** |
| Overall acceptance | **Fail** | **Fail** |

Both playback checks verify 481 common 240 Hz samples and all 20 unrelated pairs. The final-playback motion and clearance measurements do not erase the failed mapping gates. [measurements.json](receipts/reuse/measurements.json) and the per-build checker reports preserve the detailed observations.

## Regeneration comparison

The regenerated 362.5 mm source reproduces the original rejected submission's source bytes, canonical input, native transforms, native trace CSV, raw GLB, and final GLB **byte for byte**. The saved `.blend` file has a different hash; the frozen brief does not require `.blend` byte identity. No independent reopen was performed by this participant, so byte comparisons alone do not claim receiving-application acceptance.

| Compared output | Byte identity with first submission |
| --- | --- |
| `source.py` | Exact |
| `canonical-input.json` | Exact |
| `native-transforms.json` | Exact |
| `native-trace.csv` | Exact |
| `raw.glb` | Exact |
| `final.glb` | Exact |
| `scene.blend` | Different; byte identity not required |

[The preservation and regeneration receipt](receipts/reuse/preservation-and-regeneration.json) records every compared hash and the check that all original build files remain unchanged. [artifact-identities.json](receipts/reuse/artifact-identities.json) records the new paths, sizes, and hashes. Both artifact manifests retain their complete output inventories.

## Phase accounting and interpretation

Observed phase start: `2026-11-10T14:59:42+00:00`. Report finalized: `2026-11-10T15:02:43.032604+00:00`. Observed elapsed time through report preparation: **181.033 seconds**, within the 20-minute phase limit. Administrative validation, commit, and handoff completion are timestamped in the external submission receipt.

This phase used **one source edit turn, one new variant, two native build attempts, two failed native builds, two checker calls, one formal submission containing both required targets, and zero repair turns**. There were no additional native retries, extra agents, observed human interventions, scene repairs, trajectory edits, tolerance changes, or shared implementation changes. Provider token usage, provider cost, exact provider snapshot, and hidden internal model turns are unavailable.

The unchanged prepared direct runner sends Python design data to the qualified C191 constructor and recorded-output utilities. These remain disclosed reusable setup. The results establish a localized source change, literal-source reuse, and reproducible rejection of the retained first target in this public shared environment. They do not establish successful delivery, isolation, comparative authoring advantage, a production backend, or broader GOAL completion. Independent coordinator scoring, rebuild/reopen, Khronos/Three.js readback, and receiving-application playback remain separate work.
