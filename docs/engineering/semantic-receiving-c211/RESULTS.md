# C211 measured receiving result

**Result: FAILED/PARTIAL. Product integration is held.** This record describes one actual import in Blender 4.3.2 on Linux x86-64. It does not establish general Blender compatibility, a released receiver or authoring benefit. [Scope issue #154](https://github.com/Omegapy/OntoKin/issues/154) and [draft PR #155](https://github.com/Omegapy/OntoKin/pull/155) retain the blocked work.

## Exact source and receiving build

Starting published main was `4f7a62cf965066ee7f27540c3c5f2554732c6950`. Actual execution used local candidate `66f1940c4c99f52dfdea835445cdc380498815f7`, tree `efab26f1833f91747bd98f7ba8aacd26277d18ef`. Its nine implementation files exactly match independently reviewed worker `fda92dab2fc184b7d90f27b6ca292217efcd07a8`; the differing ancestry records integration ownership.

The input is C210's exact accepted after-artifact, not regenerated receiving geometry. Accepted revision is `sha256:c77d102a4b201d3c3cce6cbdc73c38eedf0bb1dfca7c9843a92d697cc0c7e082`; GLB SHA-256 is `05ebe856d3fdb96dce4b6aa55906be5ae67501bcaede9112abc30b703905b5d8`; sidecar SHA-256 is `1077eff813807c0b2058d35e2007c234b4d8c157f6dc0177f5a548924edd2c34`. Eight selected input files retain source, pinned dependency, reference poses and prior actual Agent acceptance evidence.

`/usr/bin/blender` reports version 4.3.2 and executable SHA-256 `0dfe9af0f3e67643ecf15327fa5e14e7315f61d1a81afdcafe76a71b1918e2b4`. Its upstream build label is `Unknown`; no label is invented. The executable and all 117 installed glTF importer Python files are pinned. This is an exact finite build binding, not a hermetic host or cross-version claim. [Executed input bindings](evidence/native/execution-inputs.json) and [independent input audit](evidence/review/ACTUAL-INPUT-AUDIT.json)

## Actual import and independent measurements

One metadata preflight and one actual import process ran. The stock importer completed the GLB import, then the observer recorded raw Blender-basis triangles, split normals, material inputs, matrices and native extras before rendering. The independent reviewer decoded GLB accessors and animation separately, checked the frozen source oracle and applied its own coordinate conversion. It did not use a receiver success label as evidence.

| Check | Actual observation | Disposition |
| --- | --- | --- |
| Object inventory and stable mapping | All 18 expected objects, identities and revision-bound metadata observed | Passed for the actual imported scene |
| Full triangle positions and winding | All 7,800 triangle instances match exactly | Passed |
| Split-normal component precision | 7,088 triangles fail across eight sphere objects; maximum error `0.0001531541347503662`, versus frozen `0.000002` | **Failed** |
| Normal direction | Maximum measured direction difference `0.00015615850038545062` rad | Diagnostic observation; does not replace the failed component gate |
| World poses at seven frozen times | All 126 poses pass; maximum position error approximately `4.77e-8` m and rotation error approximately `1.98e-7` rad | Passed |
| Actual material inputs | Maximum component difference approximately `2.38e-8` | Passed |
| Stock-imported GLB object extras | All 18 observed dictionaries recursively match the actual GLB extras | Passed; an earlier string-conversion concern did not occur here |
| Complete semantic sidecar | Exact canonical JSON deliberately attached by the adapter | Metadata mapping verified; this is separate from stock importer behavior |
| Rendering | Process failed because this Blender build has no OpenImageDenoise support | **Failed** |
| Native save, separate reopen and visual inspection | Not reached; no `.blend` and no rendered review images | **Not run** |

The diagnostic inventory contains 15,876 checks: 8,788 pass and 7,088 fail. It preserves the original failed overall gate. All original numeric limits remain unchanged. The exact mechanism causing the imported normal differences is not established by this attempt; it is the next investigation, not a claimed Blender defect. [Diagnosis summary](evidence/review/attempt1-diagnosis-summary.json), [first counterexample](evidence/review/attempt1-first-mesh-failure.json), [lossless detailed measurements](evidence/review/attempt1-diagnosis-detail.json.gz) and [raw native observations](evidence/native/import-observations.json.gz)

Ownership, following, hinge declarations and physical properties remain distinct metadata. Native objects have no parents, modifiers, constraints or rigid bodies, and the scene has no rigid-body world. Preserved metadata does not execute those source semantics. The imported animation is baked playback.

## Failure handling and held work

The import process returned exit 1 after the rendering failure; raw measurements had already been written. The [original summary](evidence/native/SUMMARY.json), [process receipt](evidence/native/import-process.json), [stderr](evidence/native/import-stderr.log) and [stdout](evidence/native/import-stdout.log) remain unchanged. Independent review then identified the normal failure. Zero second imports and zero reopens occurred.

Worker correction `61eb6e9ad425047f73a48c7e3861752768e3ae4a` explicitly disables scene/view-layer denoising and records the setting. It was syntax/whitespace checked but **not executed**. It cannot resolve the separate normal gate. [Correction record](evidence/worker/CORRECTION-01.json)

The held branch is published at `cdae8b582a37e37f76f142f07039ba74cedc08ad`, tree `2b2254ae2787a183fda0883fac39b91d2934f9f2`, exactly matching local held candidate `b876741f8aea702b046740481f449dc44123f445`. Draft PR #155 remains unmerged. Main receives only documentation/evidence and current-status changes. Exact local worker, executed, corrective and publication histories remain separately restorable in the handoff. [Publication readback](evidence/HELD-PUBLICATION.json)

## Validation that passed, and its limits

All **302 affected methods** passed without failure/error/skip: the complete 275-method C210 affected inventory plus all 27 new receiver CPU controls. The immutable candidate remained clean. Independent preparation also passed 29 synthetic comparator controls and eight input mutation controls. Synthetic observations test rejection and accounting; they do not prove receiving compatibility. [Affected result](evidence/affected/SUMMARY.json), [independent controls](evidence/review/synthetic-control-results.json) and [input mutation controls](evidence/review/input-mutation-controls.json)

Fresh C210 source regeneration passed all 54 proof checks. The accepted after GLB, semantic sidecar, entry source, complete program bundle and pinned library were byte-identical to the retained inputs. Fresh Khronos validation reported zero errors/warnings for two GLBs, and Three.js passed 252 pose comparisons. Core conformance passed 43 cases / 694 assertions; documentation preservation passed its current candidate check. These results establish their own source/artifact checks and cannot override Blender's failed normal or rendering gates. [Exact reproduction](evidence/validation/SOURCE-COMPARISON.json), [format/Three.js checks](evidence/validation/FORMAT-AND-THREE.json) and [core/documentation boundary](evidence/validation/CORE-DOCS-AND-BOUNDARY.json)

The mandatory broad local driver was started once with a 900-second command limit and bytecode writes disabled, then interrupted after the concrete receiving blocker ended this scope. The retained accounting records **1,476 distinct passing methods, zero completed errors and 3,205 real methods without outcomes**, from 4,681 collected methods. There is no terminal unittest summary and no complete regression pass. Earlier running labels remain verbatim; a separate reconciliation records the tool session's exit 130. The interface cannot independently attest the old subprocess PID/group cleanup, and no PID-level cleanup is claimed. [Interrupted accounting](evidence/validation/GLOBAL-ACCOUNTING.json.gz), [later interruption reconciliation](evidence/validation/INTERRUPTION-RECONCILIATION.json), [complete validation disposition](evidence/validation/FINAL-VALIDATION.md.txt) and [liveness observation limit](evidence/validation/LIVENESS.json)

C210's failed broad result (4,342 passes, 91 method errors, seven failed-import placeholders and 221 methods without outcomes) and the earlier failed full regression remain unchanged. Frozen C199/C200 schedules stay closed; C201 admission and C209 job/0.2 work remain deferred. No historical result is relabeled by this experiment.

## Next bounded action

Investigate the imported normal representation against the retained GLB and raw Blender measurements, then adopt or reject a separately versioned normal-fidelity/loss contract decision. Any revised promise must state its rationale, expected failure cases and acceptance checks before another native attempt; it must preserve this failed 2e-6 result. Reconcile the held branch and ownership, include the unexecuted rendering correction, checkpoint the chosen source and exact build, and only then consider one new bounded attempt. Do not begin the second destination or authoring comparison while this receiving gate remains unresolved.
