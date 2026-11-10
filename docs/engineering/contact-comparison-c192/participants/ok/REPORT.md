# C192 `.ok` participant: first edit

## Outcome

Formal submission 1 **fails the fixed raw/final mapping gate**. The submitted source changes only the left stop near-face position from 380 to 362.5 mm. The source was represented, constructed and evaluated. The adapter refused export acceptance with `C191_E_MAPPING`; no accepted revision or accepted artifact directory was created.

The first native build is retained unchanged. Its final recorded playback passes the shared geometry, motion and clearance checker. The independent mapping check fails. The saved native scene reopens without reconstruction or repair, and all 481 independently resimulated native sample records equal the original records as parsed JSON. Native reopening success does not override the mapping failure.

## Source and scope

- Branch: `work/c192-ok-author`.
- Starting local commit: `9d1118f63195c8458aa804f2a99922cc780365aa`.
- Frozen tree: `5a5b22ddc1763d876c6f10339f20112977ee699d`.
- Exact submitted source: `docs/engineering/contact-comparison-c192/participants/ok/sources/01-edit.ok`.
- Source SHA-256: `d399117bde6bd6bdd1d224f7794494f03938e1dcb21a7a7d1ff3c71aca0fd782`.
- The retained baseline is [sources/00-starter.ok](sources/00-starter.ok). The editable submission is [sources/01-edit.ok](sources/01-edit.ok).
- The sole replacement is `at = [380, 130, -220][mm];` to `at = [362.5, 130, -220][mm];`. Reversing that replacement reproduces all original source bytes. [Edit receipt](edit-receipt.json)

No other source design, shared implementation, frozen inputs, checker, tolerances, trajectories, physics settings or submitted output was changed. All 116 frozen input hashes passed verification before the build and after inspection. Documentation preservation also passed. This branch contains only this participant's scoped source and evidence.

## Measurements and gates

| Observation | Measured result | Outcome |
| --- | ---: | --- |
| Maximum native-to-final sample mapping deviation | 0.24463765670705492 mm | Fails 0.2 mm limit |
| Maximum continuous raw-to-final bound | 0.2719610733359383 mm | Fails 0.2 mm limit |
| Final left travel | 182.50000476837158 mm | Playback gate passes |
| Final left signed gap | -6.51925802230835e-06 mm | Playback gate passes |
| Contact-band entry | 1.4559999859929085 s | Within 0.005 s of 1.460 s |
| Maximum final playback penetration | 0.052801333367824554 mm | Within 0.5 mm |
| Maximum final playback rebound | 0.052794814109802246 mm | Within 0.1 mm |
| Final right travel | 300.00001192092896 mm | Playback gate passes |
| Final right clearance | 14.99998290091753 mm | Playback gate passes |
| Continuous unrelated-pair clearance | 20 pairs, 480 intervals each | Passes |
| Native scene reopen | 481 samples; persisted configuration unchanged | Passes |

The 0.2 mm mapping gate limits how much removing transverse and rotational solver residuals can change the delivered geometry. This result exceeds that allowance even though the projected playback reaches the requested stop position. The frozen backend remains unchanged.

## Timing and observed work

The first observed wall timestamp was **2026-11-10T14:54:02+00:00**. Evidence preparation completed at **2026-11-10T14:58:43.373569+00:00**, an observed **281.374 seconds**. This interval starts at the first shell clock observation after dispatch and ends before the local commit and final handoff; the coordinator owns the precise dispatch/submission timestamps.

| Count | Observed |
| --- | ---: |
| Participant invocations | 1 |
| Source-edit actions | 1 |
| Formal submissions | 1 |
| Formal repair rounds | 0 |
| Native build attempts | 1 |
| Failed native builds | 1 |
| Shared playback/mapping checker calls | 1 |
| Independent native reopens | 1 |
| Coordinator follow-up messages | 1 |
| Human interventions | 0 |

The coordinator instructed the participant to retain the first failed build as formal submission 1 and conclude without an extra native retry. No further source edit followed. The participant has not started reuse. Provider token usage, provider cost and hidden internal model turns are unavailable; they are not estimated. Setup and independent coordinator scoring are outside participant effort.

## Retained commands and receipts

The common build invocation was:

```sh
python -B docs/engineering/contact-comparison-c192/shared/build.py --repo /workspace/scratch/d52b43d02a92/participants/ok --route ok --source /workspace/scratch/d52b43d02a92/participants/ok/docs/engineering/contact-comparison-c192/participants/ok/sources/01-edit.ok --out /workspace/scratch/d52b43d02a92/c192-runs/ok/edit-build-01 --blender /workspace/scratch/d52b43d02a92/deps/blender-4.5.3-linux-x64/blender
```

It returned status 1. The [delivery receipt](evidence/edit/build-delivery.json), [build result](evidence/edit/build-result.json), [stdout](evidence/edit/build-stdout.txt) and [stderr](evidence/edit/build-stderr.txt) preserve the first attempt. The delivery receipt records `artifact_directory: null`. Its unaccepted native scene, GLBs and intermediate data remain at:

`/workspace/scratch/d52b43d02a92/c192-runs/ok/edit-build-01/store/attempts/88e214ce617f4f609190ecf9a710ef66/failed-stage`

The [artifact manifest](evidence/edit/artifact-manifest.json) records every retained file hash. The full external output root is `/workspace/scratch/d52b43d02a92/c192-runs/ok`.

The [checker command receipt](evidence/edit/edit-check-01.command.json) records the unchanged `shared/check_delivery.py --case edit` invocation. The checker returned status 1, with [playback pass](evidence/edit/self-check-playback.json) and [mapping failure](evidence/edit/self-check-mapping.json). Its capturing Python wrapper returned status 0 because it preserved and printed that nonzero checker status.

The [native reopen command receipt](evidence/edit/edit-native-reopen-01.command.json), [native summary](evidence/edit/native-reopen-summary.json) and [sample comparison](evidence/edit/native-reopen-comparison.json) record the pinned Blender reopen, configuration inspection and exact parsed-sample equality. The original and reopened JSON byte hashes differ because their serialization differs; no byte-identical native JSON claim is made.

Read-only inspection covered `AGENTS.md`, `GOAL.md`, the current `STATUS.md` checkpoint, `docs/README.md`, the frozen brief/input manifest/targets, the `.ok` starter, the common recorder/checker/inspection wrappers, and the finite guided-contact specification/transaction code. One read-only compound command returned status 1 because `rg --files docs -g AGENTS.md` found no nested instruction file. That stopped chained git identity reads, which were rerun successfully. The [nonzero-command record](evidence/edit/read-only-command-nonzero.json) preserves this administrative failure separately from the native build and checker failures. No invalid source candidate was attempted.

The final scoped diff and local commit are identified in the coordinator handoff. No remote ref was changed.

## Interpretation

This is one public shared-environment workflow observation. The permitted localized source edit exposes an export-mapping failure in the fixed backend at this stop position. It establishes neither general authoring advantage nor comparative cost, isolation, a production backend, general contact support, a complete release or completion of the OntoKin goal.
