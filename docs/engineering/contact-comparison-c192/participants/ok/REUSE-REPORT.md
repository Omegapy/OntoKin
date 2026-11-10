# C192 `.ok` participant: reuse phase

## Outcome

This phase preserves the rejected first submission and creates its requested **372.5 mm** source variant. Both required native builds ran once. Both final playbacks pass the shared checker, but **both builds fail the fixed 0.2 mm mapping gate**. Neither output is an accepted delivery.

The earlier 362.5 mm source, first-phase report, receipts and artifacts remain byte-for-byte unchanged. Its new regeneration reproduces the original source, canonical solver input, all native transform-record bytes and raw/final GLB bytes. The separately saved `.blend` has different bytes; the frozen protocol does not require `.blend` byte identity. No native scene was reconstructed or repaired after generation, no tolerance changed and no retry followed either rejection.

The coordinator's sealed first-phase score was read before beginning this work. It confirmed correct source localization and playback, rejected the mapping, and authorized proceeding to the frozen second target. The first design remains a rejected submission, rather than an accepted baseline.

## Source edit and preservation

The first-phase commit is `721f3691935cadf0d11cead973db11358071d33b` on `work/c192-ok-author`. This phase adds `sources/02-reuse.ok` by copying the submitted `sources/01-edit.ok` and replacing exactly one literal:

`at = [362.5, 130, -220][mm];` → `at = [372.5, 130, -220][mm];`

Reversing that substitution reproduces the earlier source bytes. Canonical input comparison independently finds exactly one changed field, `$.parts.left_stop.at_mm[0]`, from 362.5 to 372.5. Dimensions, identities, colors, following, ownership, collider enablement, feeds, guides and physics settings remain unchanged. [Edit receipt](reuse-edit-receipt.json) · [Canonical difference](evidence/reuse/canonical-difference.json)

| Source | SHA-256 |
| --- | --- |
| [Retained first source](sources/01-edit.ok) | `d399117bde6bd6bdd1d224f7794494f03938e1dcb21a7a7d1ff3c71aca0fd782` |
| [Reuse variant](sources/02-reuse.ok) | `9e12b46d44c33a7a8701b8947ffc3d060e033a4564bae5f489dbd00aef009f5d` |

All **37 original participant files** and **62 original external output files** matched their recorded hashes after the builds and checks. All **116 frozen input hashes** also passed before and after. [Prior-byte preservation](evidence/reuse/prior-byte-preservation.json)

## Measured results

| Gate or observation | Reuse: 372.5 mm | Regenerated first: 362.5 mm |
| --- | ---: | ---: |
| Build acceptance | FAIL: `C191_E_MAPPING` | FAIL: `C191_E_MAPPING` |
| Final playback | PASS | PASS |
| Independent mapping | FAIL | FAIL |
| Native-to-final sample deviation | 0.29241623943579215 mm | 0.24463765670705492 mm |
| Continuous raw-to-final bound | 0.32264731193203877 mm | 0.2719610733359383 mm |
| Mapping limit | 0.2 mm | 0.2 mm |
| Final left travel | 192.49999523162842 mm | 182.50000476837158 mm |
| Final left signed gap | -6.51925802230835e-06 mm | -6.51925802230835e-06 mm |
| Contact-band entry | 1.5359998667796984 s | 1.4559999859929085 s |
| Ideal contact | 1.540 s | 1.460 s |
| Final right travel | 300.00001192092896 mm | 300.00001192092896 mm |
| Final right clearance | 14.99998290091753 mm | 14.99998290091753 mm |
| Maximum final playback penetration | 0.05193706601858139 mm | 0.052801333367824554 mm |
| Maximum final playback rebound | 0.05193054676055908 mm | 0.052794814109802246 mm |
| Continuous unrelated-pair clearance | 20 pairs pass | 20 pairs pass |

The final recorded playback checks do not override the native-to-output mapping requirement. Both builds stopped after evaluation and retained failed export stages. Independent native reopen and receiving-application validation for these new scenes are coordinator work that has not been claimed here.

[Reuse build result](evidence/reuse/reuse/build-result.json) · [Reuse playback](evidence/reuse/reuse/self-check-playback.json) · [Reuse mapping check](evidence/reuse/reuse/self-check-mapping.json)

[Regeneration build result](evidence/reuse/edit-regeneration/build-result.json) · [Regeneration playback](evidence/reuse/edit-regeneration/self-check-playback.json) · [Regeneration mapping check](evidence/reuse/edit-regeneration/self-check-mapping.json)

## Regeneration comparison

| Earlier output compared with regeneration | Exact bytes preserved |
| --- | --- |
| `source.ok` | Yes |
| `canonical-input.json` | Yes |
| `native-transforms.json` | Yes, all 481 samples |
| `raw.glb` | Yes |
| `final.glb` | Yes |
| `scene.blend` | No; byte identity is not required |

The complete old/new hashes are in the [regeneration comparison](evidence/reuse/regeneration-comparison.json). This comparison establishes reproducibility of the rejected first output on this runtime. It does not turn that failure into acceptance.

## Commands, failures and retained outputs

The two outer commands used the unchanged common recorder:

```sh
python -B docs/engineering/contact-comparison-c192/shared/build.py --repo /workspace/scratch/d52b43d02a92/participants/ok --route ok --source /workspace/scratch/d52b43d02a92/participants/ok/docs/engineering/contact-comparison-c192/participants/ok/sources/02-reuse.ok --out /workspace/scratch/d52b43d02a92/c192-runs/ok/reuse-build-01 --blender /workspace/scratch/d52b43d02a92/deps/blender-4.5.3-linux-x64/blender
python -B docs/engineering/contact-comparison-c192/shared/build.py --repo /workspace/scratch/d52b43d02a92/participants/ok --route ok --source /workspace/scratch/d52b43d02a92/participants/ok/docs/engineering/contact-comparison-c192/participants/ok/sources/01-edit.ok --out /workspace/scratch/d52b43d02a92/c192-runs/ok/edit-regeneration-01 --blender /workspace/scratch/d52b43d02a92/deps/blender-4.5.3-linux-x64/blender
```

Both commands returned status 1. Their exact native invocations, source snapshots, stdout, stderr, costs and elapsed times are retained in the [reuse delivery receipt](evidence/reuse/reuse/build-delivery.json) and [regeneration delivery receipt](evidence/reuse/edit-regeneration/build-delivery.json). Both receipts contain `artifact_directory: null` because neither transaction accepted an export.

Retained reuse failed stage:

`/workspace/scratch/d52b43d02a92/c192-runs/ok/reuse-build-01/store/attempts/ca5af75b3b5c426faa1db0ce3bca769d/failed-stage`

Retained regenerated-first failed stage:

`/workspace/scratch/d52b43d02a92/c192-runs/ok/edit-regeneration-01/store/attempts/a1a958b383664c64aca5db144454f015/failed-stage`

Original first failed stage, retained unchanged:

`/workspace/scratch/d52b43d02a92/c192-runs/ok/edit-build-01/store/attempts/88e214ce617f4f609190ecf9a710ef66/failed-stage`

The [reuse manifest](evidence/reuse/reuse/artifact-manifest.json) and [regeneration manifest](evidence/reuse/edit-regeneration/artifact-manifest.json) identify every retained artifact byte.

The shared checker ran once per output using `--case reuse` and `--case edit`, with new output directories. Both checker commands returned status 1, reporting playback success and mapping failure. Their capturing Python wrappers returned status 0 after preserving those nonzero statuses. Exact check commands and output are linked from the [reuse command receipt](evidence/reuse/reuse/self-check-command.json) and [regeneration command receipt](evidence/reuse/edit-regeneration/self-check-command.json). There were no additional failed read-only commands or invalid source candidates in this phase.

## Timing and observed work

First observed reuse wall time: **2026-11-10T14:59:55.533894407Z**. Report preparation completed at **2026-11-10T15:03:45.045669+00:00**. The observed work interval is **229.512 seconds**. This starts at the first shell clock observation after the reuse dispatch and ends before final local commit and handoff. Exact dispatch and submission timing belongs to the coordinator.

| Count in this phase | Observed |
| --- | ---: |
| Participant invocations | 1 |
| Source-edit actions | 1 |
| Formal submissions | 1, containing both requested outputs |
| Repair rounds | 0 |
| Native build attempts | 2 |
| Failed native builds | 2 |
| Independent checker calls | 2 |
| Participant native reopens | 0 |
| Coordinator follow-ups after phase dispatch | 0 |
| Human interventions | 0 |

The participant used the assigned default settings. Provider token totals, provider cost and hidden model turns remain unavailable. Reusable setup and the coordinator's independent scoring, rebuilding, reopening and receiving validation remain outside these participant counts.

## Interpretation

The participant retained and reused literal source correctly, and regenerated the first rejected output exactly in the required data. Both positions nevertheless fail the unchanged mapping gate. This phase does not qualify accepted reuse, general classes, parameters, imports, libraries or composition. It remains public shared-environment workflow evidence, with no claim of isolation, comparative advantage, cost superiority, general dynamics, production readiness or full OntoKin completion.
