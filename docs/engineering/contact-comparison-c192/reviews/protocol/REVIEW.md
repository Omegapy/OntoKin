# C192 direct-Python route and protocol review

## Verdict

**APPROVE integration of the experiment records. No delivery is approved.** The direct-Python first edit, reuse variant and regenerated first source all remain rejected by the frozen 0.2 mm mapping gate. The records preserve that outcome and distinguish passing playback, file-format and receiving-application checks from delivery acceptance.

This review began after the participant phases closed and is excluded from participant time and effort. The reviewer previously authored the `.ok` route. This review independently covers the **other direct-Python route**, common protocol records and receiving evidence; it does not supply independent approval of the reviewer's own `.ok` authoring or physics results. No new native trial was run.

All **23 recorded audit checks pass**, with no open integration blocker. [Machine-readable findings](findings.json) and [detailed checks](evidence-checks.json) identify the reviewed files, hashes and comparisons.

## Resolved reporting finding

`C192-PROTOCOL-01` identified a low-severity ambiguity: the two `edit-regenerated` result entries originally had `rebuild_exact: false`. No additional coordinator rebuild had been performed for those entries; the participant's regeneration had already reproduced the earlier rejected output. A false value could therefore be read as a failed reproducibility check.

The coordinator corrected the entries to `fresh_rebuild_performed: false` and `rebuild_exact: null`. The original generated arrays remain in `c192-audit/first-reproduction/results-before-review.json` and `c192-audit/reuse-reproduction/results-before-review.json`. I compared the original and corrected arrays: only the two reporting fields changed. Source hashes, native measurements, artifact hashes, replay results and rejection outcomes are unchanged. The correction is verified and resolved.

## Direct source and common backend

The starter, first edit and reuse files are editable Python modules containing a docstring and one literal `DESIGN` dictionary assignment. An abstract-syntax-tree inspection found no source-level calls or hidden generation code. Both the parsed values and exact byte substitutions show one edit per phase:

| Phase | Only changed field | Before | After |
| --- | --- | ---: | ---: |
| First edit | `DESIGN['parts']['left_stop']['at_mm'][0]` | 380 mm | 362.5 mm |
| Reuse | Same field | 362.5 mm | 372.5 mm |

The first source remains identical to commit `375f0df7bb63e8d7b72c7f0cf41643db3000da22`. All 39 files in the original first-build directory match the inventory captured before reuse.

The prepared direct runner loads Python `DESIGN` with `runpy.run_path`. It validates and serializes that data, then executes the retained, unchanged C191 `native_worker.py` with canonical JSON. It does not invoke the `.ok` parser. The canonical `source_binding` field is explicitly documented as an interchange-profile label, not evidence that `.ok` was parsed.

For each of the three participant builds I checked the retained runner and all 11 retained implementation files against the frozen shared implementation. All match. The pinned Blender command, empty trusted-test-hook list, 1,000,000-operation request and 80,000 ms request are retained. The source snapshot in the common recorder and the artifact both match the editable Python source. The canonical solver JSON equals the serialized dictionary.

The native subprocess completes, and the shared output binding rejects the projection at `C191_E_MAPPING`. All three common receipts return status 1, `successful: false` and `artifact_directory: null`. Their intermediate native and GLB files remain retained diagnostic evidence. No unrelated source or trajectory modification was found.

## Reproducibility and rejection

The first-source regeneration reproduces `source.py`, `canonical-input.json`, `native-transforms.json`, `native-trace.csv`, `raw.glb` and `final.glb` byte for byte. The coordinator's two fresh Python builds likewise reproduce canonical inputs, native transform records and raw/final GLBs. Different `.blend` hashes are disclosed; the frozen brief does not require `.blend` byte identity.

I inspected all **five** coordinator native-reopen records for the direct route: submitted and rebuilt first edit, submitted and rebuilt reuse, and regenerated first edit. Each reopen returns status 0, retains persisted configuration without reconstruction or repair, and reproduces all 481 native samples. Scene hashes in the reopen receipts match the actual saved scenes. These replay checks reproduce the physical result; they do not waive the separate mapping gate.

| Direct target | Native-to-final sample deviation | Continuous raw-to-final bound | Mapping result |
| --- | ---: | ---: | --- |
| 362.5 mm | 0.2446376567070452 mm | 0.2719610745598733 mm | Rejected at 0.2 mm |
| 372.5 mm | 0.2924162394357902 mm | 0.3226473129779241 mm | Rejected at 0.2 mm |

The direct outputs match the coordinator's sealed canonical/native/raw/final identities. Cross-route equality is reported as common-backend output equality, with no comparative authoring or cost advantage inferred. This review does not independently requalify the `.ok` route.

## Receiving evidence

The receiving tools operate on the actual retained GLBs. All **29 receiving dependency/tool files** match their corresponding bytes in the C191 `qualification-evidence.tar.xz` archive. Tool receipts identify actual input hashes and versions. Inherited `C191` and `corrected-low-light` labels belong to the reused render script; they are not evidence of a hidden C192 repair or render retry.

For the direct route, Khronos validator `2.0.0-dev.3.10` checked both raw and final files at both stop positions. All four file hashes match the retained outputs. There are no errors or warnings. Each final file has one preserved informational `UNUSED_OBJECT` message for the unused rotation sampler.

Three.js revision 186 loads those same four files through `GLTFLoader` and evaluates `AnimationMixer` at zero, the declared contact-reference time and two seconds. It finds seven mesh identities, two-second clips and the expected final gaps. The manifest and reports label every output `REJECTED_MAPPING`. The evidence makes no browser or GPU-rendering claim.

Blender 4.5.3 imports the two direct final GLBs, checks imported bounds against an independent decode, and renders three poses per target through CPU Cycles. All six image hashes and input hashes match their receipts. The largest direct-route import-bound error is approximately **2.52e-8 m**, within the script's 5e-5 m comparison limit. I visually inspected all six direct-route images. The complete gauge remains visible; the left shoe reaches its stop and the right lane advances while retaining its final gap. Those images cannot resolve or negate the submillimetre raw/final mapping violation.

This evidence supports file readability, recorded animation readback and sampled imported-frame inspection. It does not establish live destination collision physics or accepted deliveries.

## Protocol, preservation and accounting

All **116 frozen file hashes** match independently in both the coordinator and direct-Python worktrees. Git comparisons find no changed historical implementation outside the experiment and authorized navigation/status scope. The frozen constructor, checkers, tolerances, resource limits and earlier release gates remain intact.

The protocol requests two fresh default agents, separate scopes and branches, equal phase limits and common tools. The exercise is explicitly public and uses a shared environment. It makes no isolation or blind-evaluation claim.

The direct participant used one native build in the first phase and two in reuse, with one formal submission per phase and no repair round. The accounting receipt matches the direct participant's submission times and commits: **283.171448 s** through first submission readiness and **218.203328 s** through reuse submission readiness. Read-only search and transport failures are separately disclosed and not counted as native builds.

Reusable preparation is explicit: inherited C191 constructor/output/validation utilities, the new Python starter and runner, the common recorder and target wrappers, analytical controls, two setup builds and two setup reopens. Full setup wall time is disclosed as incompletely instrumented. Provider snapshot, token totals, provider cost and hidden model turns are null/unavailable rather than estimated. The report explains that differing inspection/report work prevents a comparative speed or cost inference.

## Scope of this approval

Approval applies to the experiment records at the hashes in `findings.json`, including corrected reporting metadata. It does not approve the rejected deliveries, a general contact backend, general source-program reuse, a larger comparative study, release completion or OntoKin GOAL completion. The coordinator was still preparing the final narrative and archive; later packaging must preserve these reviewed identities and this rejection classification.

Review completed: `2026-11-10T15:14:09.472391+00:00`. No source, artifact, frozen input or remote ref was edited by the reviewer.
