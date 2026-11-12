# C218: saved-scene reopen and persistence result

**The independently reviewed finite saved-scene reopen passed.** A fresh Blender 4.3.2 process opened C217's exact saved scene with automatic scripts disabled, captured all required observations and rendered the two existing planned views. It exited with code 0 after `9.911221667000063` seconds. No timeout or remaining process group was observed. The one-start schedule is consumed and closed.

Independent reviews passed the complete numerical persistence comparison, authoritative-source geometry/loss checks, material/semantic/pose checks, input/process checks and both fixed views. All 32 requirements have explicit dispositions, retaining the strict source-normal failure and root-owned publication/archive/save closure as separate matters. This review establishes the finite reopen observation; it does not establish broader receiving acceptance.

All captured native normal and position values and all 126 captured pose matrices compare exactly with C217's import observations. This is exact numerical persistence for the captured data. Native normals still differ from authoritative source normals: the original maximum component difference is `0.0001531541347503662`, exceeding the unchanged `2e-6` limit. The original strict gate remains **FAILED**. No new correspondence, normal or shading tolerance was introduced, and broader receiving acceptance remains **NOT ESTABLISHED**.

## What executed and what stayed fixed

C218 opens an existing saved `.blend`; it performs no GLB import, scene save, source-text creation, identity remapping, geometry rebuild or normal replacement. The exact original scene remains 3,864,164 bytes, SHA-256 `dd8a6f32e96e45ec92207ee3417af0b3c88a6f9d898cff6d07e4366ab79993c4`, at archive path `agent-results/namespace-repair/run-01/received.blend`. Its bytes were checked before and after observation. The original C217 scene and consumed import schedule are unchanged.

The observer checked the saved source texts and mappings, actual source identities and geometry, original native extras, materials, supported semantic records and the same seven sample times. It verified the existing saved camera/light/world recipe without reconfiguration. Only in-memory playback time, selected existing camera and PNG output path changed for observation; those changes were not saved.

The overview and sphere-detail PNGs use the saved C217 recipe: Cycles CPU, 960×720, 16 samples, seed 216 and scene/view-layer denoising disabled. Root and the independent reviewer found both useful. Low-sample grain, polygonal silhouettes and hidden-surface limitations remain visible. Image usefulness cannot establish numerical normal accuracy, and identical PNG bytes are not claimed.

## Exact source and publication identities

| Role | Revision or identity |
| --- | --- |
| Observed starting main | `d70513870537611cd423e0fadd2fbb1594beb297` |
| Actually executed C218 observer, local Git identity | `efd5002a8dd955a4fb59c96920b0263e35e01a25` |
| Published held observer, [draft PR #169](https://github.com/Omegapy/OntoKin/pull/169) | `15c369134cf8ae42d092823aeab9348c9861adfd` |
| Executed observer tree | `35ce5d109bb45d3a08930031fef5cbc98728854a` |
| Canonical C218 one-start plan hash | `f087d2ac64fdfa4aafc026151b15f4880459f2ce76ecc5ac547c05dbebdf808d` |
| Final prelaunch C215 input-lock hash | `2e23063ed197e5baf521c824232aa7a7b72fcd34eac45aafec43e014d2d3ad6c` |
| Actual earlier C217 source | `6af212204d58fbac2a98f3cded44facd67c52528` |
| Published held C217 source, [draft PR #167](https://github.com/Omegapy/OntoKin/pull/167) | `55ce9f34a14cbf3d954332244c9e9a6800ed93fb` |

A shared source tree does not make distinct Git commit identities interchangeable. The source snapshot in the handoff distinguishes local execution/authoring commits from published main and held-branch commits. Scope issue [#168](https://github.com/Omegapy/OntoKin/issues/168) records coordination. Root owns final documentation publication, exact resulting-main verification and lease release.

The nine prototype files remain held outside main: `README.md`, `CONTRACT.md`, `build_bindings.json`, `capture.py`, `common.py`, `origin_guard.py`, `run.py`, `test_origin_guard.py` and `test_reopen.py` under `docs/engineering/native-reopen-c218/`. Main receives only results, next-task instructions and selected evidence. Earlier held [PR #155](https://github.com/Omegapy/OntoKin/pull/155) and [PR #165](https://github.com/Omegapy/OntoKin/pull/165), their source identities and failed outcomes remain unchanged.

## Complete measured result

| Measure | Observed result |
| --- | --- |
| Product objects | 18 |
| Triangle instances | 7,800 |
| Expected / observed corners | 23,400 / 23,400 |
| Missing / ambiguous / invalid corners | 0 / 0 / 0 |
| Sample times / object poses | 7 / 126 |
| Native normal components changed from C217 | 0 differing corners; maximum component difference 0 |
| Native positions changed from C217 | 0 differing corners; maximum component difference 0 |
| Captured poses changed from C217 | 0 differing poses; maximum matrix-component difference 0 |
| Native-vs-source maximum normal component difference | `0.0001531541347503662` |
| Independently recomputed maximum normal angle | `0.008947222990085959` degrees |
| Corners / triangles / objects exceeding original `2e-6` limit | 14,880 / 7,088 / 8 |
| Original strict source-normal gate | **FAILED**, unchanged |
| Broader receiving acceptance | **NOT ESTABLISHED** |

The measured loss is the same as C217's. The eight affected objects share sphere geometry; they do not establish a universal error bound. The C215 reporter calculates a maximum angle of `0.008947222990085517` degrees; the tiny arithmetic difference from the independent result falls within the existing auditor comparison allowance. That allowance is not a shading tolerance.

Fresh comparison with authoritative source also passed supported material, semantic and pose checks. Maximum PBR component error was `2.384185793236071e-8`, maximum position error `4.768371586472142e-8 m`, and maximum rotation-angle error `1.976862424823881e-7 rad`, within their existing respective `2e-6`, `0.001 m` and `0.001 rad` limits. Those limits do not apply to or relax the failed source-normal gate.

The unchanged C215 reporter retains `nativeFidelityEstablished=false`, `receivingEvidence=false`, `provenanceAuthenticated=false` and `shadingAcceptance=NOT_EVALUATED`. Its generic settings artifact is explicitly labeled as a saved-scene reopen, with original import settings preserved separately. The observations therefore do not imply that C218 imported a GLB or that the reporter granted acceptance.

## Checks and evidence

| Check | Result |
| --- | --- |
| Observer CPU controls | 26 methods passed; includes changed-scene rejection, one-start/unknown-outcome refusal and postspawn exception cleanup |
| Independent static prior-scene/host audit | 255 assertions passed |
| Independent prepared-source/input audit | 232 assertions passed |
| Independent persistence corruption controls | 12 controls passed |
| Independent exact numerical persistence comparison | 55,197 assertions passed |
| Independent native corner/source-loss audit | 93,691 assertions passed while retaining the original normal failure |
| Independent material/semantic/pose audit against source | 2,695 assertions passed |
| Independent input/process/module/scene/render audit | 464 assertions passed after preserved reviewer-harness corrections |
| Independent visual review | Both actual PNGs useful, with visibility/grain limits |
| Requirement accounting | All 32 explicitly dispositioned; original normal failure and root closure remain distinct |
| Native starts / reimports / scene saves / retries | 1 / 0 / 0 / 0 |
| Full product regressions | Not repeated for this isolated observation; inherited failed/incomplete results retain their meaning |

Archive evidence paths are plain paths because the large native payload remains in the verified handoff:

- `agent-results/reopen-c218/run-01/`: immutable plan and inputs, approval/reservation, actual process logs, raw restored state, native measurements, loss report and PNGs.
- `agent-results/reopen-c218/IMPLEMENTATION-CHECKPOINT.json`: exact committed source, checks and prepared input identities.
- `agent-results/review-c218/EXACT-PERSISTENCE-AUDIT.json`: complete captured import/reopen comparison.
- `agent-results/review-c218/NATIVE-CORNER-LOSS-AUDIT.json`: independent source decoding, correspondence and loss measurements.
- `agent-results/review-c218/FINAL-REOPEN-REVIEW.json` and `.md`: final independent finite-result decision and exact evidence hashes.
- `agent-results/review-c218/REQUIREMENT-DISPOSITION.json`: all 32 requirements, including failed strict fidelity and pending root closure.
- `agent-results/review-c218/REVIEWER-HARNESS-CORRECTIONS.json`: original auditor failures, exact corrections and preserved source/result hashes.
- `evidence/c218/root-visual-review.json`: root's review of the two actual reopened-scene images.

The original provenance-auditor failure and material/pose invocation error remain preserved. Four narrow reviewer-harness corrections resolved their causes:

- The reservation hashes the original root approval file; its canonical run copy has equivalent parsed content but different serialized bytes. Both are now checked separately.
- Blender's recorded initial `dont_write_bytecode=False` matches C217. The observer then sets it to `True`; actual flags and absent caches remain checked.
- The complete scene-property oracle now includes the previously declared Cycles renderer group, derived from the preserved C217 settings. Unknown extra properties remain refused.
- The material/pose invocation now uses the unchanged C217-bound `source-expectations.json`; its first invocation incorrectly supplied a source-only corner oracle.

These corrections changed review parsing/input selection only. No executed observer source, native input/output, fidelity expectation or tolerance changed, and no native process reran. A harmless precommit edit-path error and its unchanged-source CPU run are also retained separately; the corrected source passed its checks before the executed commit was frozen.

## Remaining limits and exact next action

[C217](../native-receiving-c217/RESULTS.md) supplies the actual import/save/capture evidence; C218 supplies the separately observed reopening. [C215's proposed contract](../receiving-adapter-c215/CONTRACT.md) still requires an explicit finite receiving decision. The original strict normal contract and [C212 decision](../normal-fidelity-c212/DECISION.md) remain unchanged. Persistence preserves native values that already contain measured loss; it does not recover the original source normals as native normals or prove lossless transport.

Upstream executable source/build lineage remains `Unknown`, system shared-library closure and hostile-host authenticity remain unproved, and the historical C211 fan-frame/short and interrupted-driver observation gaps remain recorded. No live destination physics/actions, second target, universal normal bound, full release or comparative authoring advantage is established. Earlier failed/incomplete regressions and all consumed schedules retain their meaning.

Finish the verified saved C218 handoff and stop. The [next bounded task](NEXT-TASK.md) is an evidence-only finite receiving acceptance/scope decision using C217 and C218. It authorizes no native start or second-target execution.
