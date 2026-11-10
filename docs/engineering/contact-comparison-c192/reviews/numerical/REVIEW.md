# C192 numerical evidence review — .ok route

## Decision

**APPROVE evidence integration. No unresolved blocking or nonblocking issue remains in this review's scope.** This approves retention and publication of the experiment's evidence. It does **not** approve the rejected outputs or qualify either target as a successful delivery.

The reviewed `.ok` first edit and reuse target both satisfy the source-localization and final-playback checks. Both exceed the unchanged 0.2 mm native/raw-to-final mapping gate and remain failed. Their native scene replays and fresh rebuilds reproduce those results.

## Independence and exact scope

This reviewer previously authored the Python route. That participant phase and its time accounting were closed before this separate review began. The independent artifact review covers **only the other, `.ok`, route**, together with the coordinator's scoring/rebuild/reopen harnesses and shared frozen numerical inputs. The Python artifact records and cross-route aggregate assertions are not independently endorsed here; those require the complementary review.

Review started at `2026-11-10T15:04:30Z`; the report was finished at `2026-11-10T15:13:03.207210+00:00`. No native build or Blender process was started during this review. All review files were written under `/workspace/scratch/d52b43d02a92/c192-reviews/numerical`; existing source, artifacts, frozen files, and remote refs were not edited by this reviewer.

The primary examined records were coordinator `results.json`, the frozen brief and input manifest, `tools/score_submission.py`, `tools/verify_builds.py`, the unchanged C191 independent mapping/native inspectors, the `.ok` participant source copies, and the first/reuse reproduction directories. Five retained `.ok` builds were examined: three participant builds and two coordinator fresh rebuilds. Five existing saved-scene replays were checked directly.

## Findings established from bytes and data

### Source localization and frozen implementation

The frozen `INPUT-FREEZE.json` matches the file in local freeze commit `9d1118f63195c8458aa804f2a99922cc780365aa`, whose tree is `5a5b22ddc1763d876c6f10339f20112977ee699d`. Every one of its **116 files** matches its pinned size and SHA-256 in both the coordinator checkout and the `.ok` participant checkout.

The participant's `00-starter.ok` is byte-identical to the frozen `.ok` starter. `01-edit.ok` changes exactly one literal in that starter, from `at = [380, 130, -220][mm];` to `at = [362.5, 130, -220][mm];`. `02-reuse.ok` changes that same literal to 372.5 mm. The reuse source also equals the first submitted source with only 362.5 replaced by 372.5. Source snapshots retained in each build match the corresponding editable source and recorder hash.

| Editable `.ok` source | SHA-256 |
| --- | --- |
| `sources/01-edit.ok` | `d399117bde6bd6bdd1d224f7794494f03938e1dcb21a7a7d1ff3c71aca0fd782` |
| `sources/02-reuse.ok` | `9e12b46d44c33a7a8701b8947ffc3d060e033a4564bae5f489dbd00aef009f5d` |

All **11 retained implementation files in each of five builds** match the original frozen implementation hashes. Embedded backend bytes also match the freeze. The actual pinned Blender executable matches SHA-256 `5e15447670804c855fef6033ac9b8fd82696b762095becf0df79b1c2f8034397`. Recorded requests preserve 1,000,000 operations and 80,000 ms.

### Rejection remains correct

I re-ran the coordinator scorer against each of the five retained `.ok` builds, with new output directories inside this review directory. These five read-only rescoring runs reproduced the coordinator's source checks, hashes, playback outcomes, mapping failures, and numerical measurements exactly.

| Target | Left travel | Native-sample to final maximum | Continuous raw-to-final bound | Overall |
| --- | ---: | ---: | ---: | --- |
| 362.5 mm stop | 182.500004768 mm | 0.244637657 mm | 0.271961075 mm | **Fail** |
| 372.5 mm stop | 192.499995232 mm | 0.292416239 mm | 0.322647313 mm | **Fail** |

Both mapping quantities are above the frozen 0.2 mm limit. Final playback passes, including 300.000011921 mm right travel, 14.999982901 mm right clearance, 481 common keys, and continuous clearance certification for all 20 unrelated pairs.

The `.ok` transaction records preserve `successful: false`, `committed: false`, `accepted_revision: null`, `exported: false`, and `destination_validated: false`, with diagnostic `C191_E_MAPPING`. The scorer computes overall acceptance as the conjunction of successful build, playback pass, and mapping pass. The verification harness keeps `verification_completed` separate from `experimental_delivery_pass`. Thus successful execution of an audit or successful scene replay does not promote rejected GLBs to accepted delivery.

The frozen mapping checker rejects at its numerical limit before some later byte checks can execute. I separately decoded the retained raw/final GLBs to verify all sampler time arrays and native/raw/final carriage-X samples. The raw translations match the native samples after the stated coordinate conversion and float32 representation; all final X values remain exact. This supplementary check does not change the mapping verdict.

### Native replay and clean regeneration

For each of five recorded `.ok` scene replays, I compared the full saved `native-transforms.json` structures to the originating artifact. All **481 rows × seven parts** agree exactly in each replay: **2,405 replayed sample rows** in total. Frames and times are exactly 0–480 and `frame / 240`.

The actual reopen command receipts use the pinned Blender executable, the identified saved `.blend`, factory startup, and the unchanged independent inspection wrapper. All five recorded commands exited zero. Their scene, source, and canonical-input hashes match the files now present. The inspector clears the point cache, checks unchanged configuration, and captures evaluated poses without reconstructing or repairing the scene.

The retained configuration data confirms 13 objects, seven visible meshes, two 1 kg active compound owners, solver motion authority, constant-feed motors, no transform actions, ten substeps per frame, 100 solver iterations, 240 Hz recording, and the requested stop coordinate. The independent inspector code itself is frozen and checks the wider geometry/driver/constraint contract.

The clean first-edit rebuild and clean reuse rebuild reproduce their submitted source, canonical input, native transforms, native trace CSV, raw GLB, and final GLB byte for byte. The participant's later first-target regeneration reproduces those same first-submission bytes. `.blend` hashes differ between builds, which the frozen brief explicitly permits; the saved scenes were separately reopened and matched their corresponding native traces.

## Resolved review issue

**N1 — ambiguous `rebuild_exact` field, low severity, resolved.** Originally, `verify_builds.py` copied the requested rebuild flag into `rebuild_exact`. This made `false` on a regeneration row mean that no additional coordinator rebuild was requested, although the field name could suggest a failed equality check.

The coordinator added `fresh_rebuild_performed` and now records `rebuild_exact: true` after a performed and verified rebuild, or `null` when no extra rebuild was run. I compared both audit result files to their retained `results-before-review.json` copies and verified that only those expected metadata fields changed. The consolidated verification rows exactly match the corrected audit rows. The script differs from its retained predecessor only in this result-field stanza.

All reviewed artifact hashes, the scorer, the freeze, and the original numerical checkers remain unchanged. No new native run was added. [metadata-fix-verification.json](metadata-fix-verification.json) records the correction and its hashes.

One review-only delta check initially assumed that the executable review snapshot preceded this correction. The snapshot already contained the correction, so applying the transformation again triggered an assertion. That failed reviewer assumption and its resolution are retained in [metadata-fix-first-check-failure.json](metadata-fix-first-check-failure.json). It was not a source, build, or numerical evidence failure.

## Reviewed identities and commands

| Record or harness | Reviewed SHA-256 |
| --- | --- |
| Coordinator `results.json` | `0a2cce4ef173938b573ba425fb80263fe69d925407f8278fcd36141eeabefa53` |
| Frozen `INPUT-FREEZE.json` | `ee0840f60497964c77d2c2ee2355ff369d807aa3b4d3b6fb648e2bd0a416e3d2` |
| `tools/score_submission.py` | `5a943f6cf166e0eee32d7a33b78a969f1d35f0c9e222d8b432771a5526c7617a` |
| Corrected `tools/verify_builds.py` | `f38912102d357af4ca955d8d15c66efb08774aa07ff7b8dd5168b038b112c41c` |

The principal executed review commands were:

```bash
python -B /workspace/scratch/d52b43d02a92/c192-reviews/numerical/review_checks.py
python -B /workspace/scratch/d52b43d02a92/c192-reviews/numerical/metadata_fix_check.py
```

The first script launched five scorer invocations, one for each recorded `.ok` build, with output only inside this review directory. [commands.json](commands.json) records their complete argument vectors, timestamps, stdout, stderr, and exit statuses. [review-execution.json](review-execution.json) retains the primary script result. [findings.json](findings.json) contains the machine-readable final decision, exact artifact paths/hashes, freeze checks, source checks, replay comparisons, rebuild comparisons, resolved issue, and limits.

This review covers numerical records and harness behavior. It does not replace Khronos/Three.js readback, actual receiving-application playback, independent review of the Python route, or broader qualification. Every reviewed target remains rejected at the unchanged mapping gate.
