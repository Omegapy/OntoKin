# OntoKin development status

OntoKin is an AI-native semantic language and intermediate representation for constructing, inspecting, validating, repairing and transporting physically meaningful 3D objects. Accepted `.ok` source owns named parts, dimensions/units, relationships, physical declarations and source identity. Engines and specialist tools own rendering, general simulation and gameplay. The [revised GOAL](GOAL.md), [C210 decision](docs/engineering/semantic-export-c210/DECISION.md) and [coordination rules](AGENTS.md) govern current work.

## C223 R01: validation input and bytecode repair passed focused checks

[C223](docs/engineering/local-validation-c223/RESULTS.md) repairs the local driver's two recorded defects: the isolated input closure now includes all top-level fixtures, every planned Python command receives `-B`, and ordinary descendants inherit `PYTHONDONTWRITEBYTECODE=1`. Existing source-stability and frozen-reader cache guards, budgets, fixture bytes and expected outcomes remain intact.

Author `7a72d489235a6bc880ffd6c9732591a94a0ae383` passes all 30 focused methods; the same controls produce 11 original assertion/subtest failures against the unchanged driver. Independent review passes 12 groups covering all 42 real fixture files, 18 Python launch prefixes, grandchildren and six retained cache refusals. [Review](docs/engineering/local-validation-c223/REVIEW.md). [PR #179](https://github.com/Omegapy/OntoKin/pull/179) merged at `dfff965666771df5c850ac5d4f4954044da21bb1`, exactly matching the independently reviewed tree. Fresh actual-main checks pass all 30 methods and 29 preserved sources / 4,651 local links; the worktree is clean. [Integration receipt](docs/engineering/local-validation-c223/evidence/INTEGRATION.json).

R00 is completed after fresh verification of C222's exact saved archive, complete offline restore and closed scope #176. The [nine-task tracker](docs/engineering/review-integration-c221/RECOMMENDATIONS.json) preserves all 41 criteria. R01 is completed within its focused scope; after the verified C223 saved handoff, [R02 aggregate regression](docs/engineering/local-validation-c223/NEXT-TASK.md) is next. Historical aggregate failures remain failed. No native starts, product-source evaluations, exports, imports, renders or scene writes ran. Stop after C223 delivery.

## C222 current result: CPU observation schema and exact correspondence passed

[C222/0.1.0](docs/engineering/second-target-c222/RESULTS.md) supplies the finite observation format and geometry checker for the same 18-part fixture. C221 authority admission stays fixed. Exact positions and C220's predeclared winding conversion map all 7,800 triangles and 23,400 corners, with signed-zero canonicalization only. Names and normals cannot choose matches; malformed, missing, ambiguous, duplicate or extra geometry fails.

All 23 author controls and 49 independent public controls pass, plus ten ambiguity/winding controls and six static conditions. Nine accepted synthetic variants received complete 23,400-row correspondence checks. [Contract](docs/engineering/second-target-c222/CONTRACT.md), [independent review](docs/engineering/second-target-c222/REVIEW.md). Native labels remain untrusted. No Godot behavior, numerical normal/material/pose fidelity, native persistence or full release is established; all native/version/source/export/import/render starts and scene writes remain zero.

[PR #177](https://github.com/Omegapy/OntoKin/pull/177) merged at `5db3643a1b881af1e8adfa2437d303458bcf449b`, with the exact independently reviewed tree. Fresh actual-main checks pass all 43 selected C221/C222 CPU methods, the complete independent corner map and 29 preserved sources / 4,621 links. [Verified integration record](docs/engineering/second-target-c222/evidence/INTEGRATION.json). The merged work branch is absent and the four held PRs remain unchanged.

The [owner's review tracker](docs/engineering/review-integration-c221/README.md) retains all nine task records and criteria. C223 freshly verified the exact final C222 ZIP and closed scope #176 delivery; R00 is completed. The separately selected R01 repair is recorded above. R02 aggregate verification and R03-R08 remain pending, including the R07 second-target chain. C222's original seal-time wording and delivery evidence remain in its preserved handoff.

## C221 current result: CPU authority binding passed

[C221/0.1.0](docs/engineering/second-target-c221/RESULTS.md) supplies an isolated standard-library checker for the eight fixed C220 input files and complete source mapping. Actual input admission passes two source units, 18 parts, 52 span occurrences over 16 distinct ranges, 54 accessor bindings, 7,800 triangle instances and 23,400 corner instances. The [contract](docs/engineering/second-target-c221/CONTRACT.md) separates immutable file admission, structural source joins and unimplemented numerical/destination claims.

[Independent review](docs/engineering/second-target-c221/REVIEW.md) passed 39 controls and 337 static assertions; all 20 author methods pass without failures, errors or skips. Original worker source is `d16dde5b6017df2c37b2537ba4fa0a30ba46be09`, tree `998e4db5e3307849783acbd8f2b259c43a311af1`. [PR #175](https://github.com/Omegapy/OntoKin/pull/175) merged at `315e9a915c8681bb13b0fe0e5f84ffeb3c2b8a0f`, tree `dd4456259c27c8d526fd59c5a93a8aec4b410757`, exactly matching the reviewed candidate. Fresh actual-main checks pass authority admission, all 20 author methods, and 29 preserved sources / 4,595 local links. All 15,597 existing non-navigation entries remain exact. [Verified integration record](docs/engineering/second-target-c221/evidence/INTEGRATION.json). No product runtime, exporter, fixture, workflow or dependency changes. Historical failures and held PRs #155/#165/#167/#169 retain their meanings.

All native/target/version/source/export/import/render starts and native scene writes remain zero. Godot build lineage, runtime/API behavior and a useful rendering route remain unresolved. This step completes source-input preparation only. The next bounded task is [CPU-only observation schema and corner correspondence](docs/engineering/second-target-c221/NEXT-TASK.md); the rest of C220 preparation and the second-target proof remain pending. Finish the verified saved C221 handoff, then stop.

## C220 preserved result: second-target plan; execution held

[C220/0.1.0](docs/engineering/second-target-c220/PLAN.md) selects the installed Godot 4.6.3 candidate by exact executable digest and binds the same accepted C210 GLB/source/semantic inputs plus C214 authority. The planned mapping enumerates all 18 parts and their source spans, definitions, keyed occurrences and geometry references. Numeric, material, semantic, cross-target, persistence, visual and resource/stop requirements are predeclared.

The executable exists; its upstream build lineage is unresolved because its embedded commit-like value differs from the observed official tag. This shell has no confirmed rendering surface. Runtime/API behavior and useful images remain unverified. C220 is planning and read-only availability inspection only: zero target/native/source/export/import/render starts or scene writes. The original strict normal failure and all historical failed/unrun gates remain unchanged. [Planning status and limitations](docs/engineering/second-target-c220/evidence/PLANNING-STATUS.json).

[Independent review](docs/engineering/second-target-c220/REVIEW.md) passed 9,499 static source assertions, 14 contract conditions, 25 target conditions and seven final delta checks. The missing raw Blender observation binding was corrected and preserved. [PR #173](https://github.com/Omegapy/OntoKin/pull/173) merged at `0c5f4510672d6ff61a5865bb4be8ed52880154f1`, tree `d9be713ddf17ffc9081bf43be624973a09ceb721`, exactly matching the reviewed candidate. Fresh resulting-main documentation checks passed 29 preserved sources / 4,559 local links. Integration review passed 24 checks; all 15,584 existing non-navigation entries remained exact. [Verified integration record](docs/engineering/second-target-c220/evidence/INTEGRATION.json). **Current closure:** deliver the verified saved C220 handoff and stop. The next thread may perform only [CPU-only Godot observer/checker and protocol preparation](docs/engineering/second-target-c220/NEXT-TASK.md), with no target start. Full second-target execution remains blocked on reviewed source and evidenced capabilities; Unreal support and the matched direct-authoring comparison remain unrun.

## C219 preserved result: precise finite Blender receiving promise accepted

[C219/0.1.0](docs/engineering/receiving-decision-c219/DECISION.md) accepts the one-fixture, one-build promise from C217/C218: exact retained source authority, independently checked native geometry and measured shading loss, useful inspected views, and exact persistence of observed native values through the specified save/reopen. Its requirement table binds all 18 objects, 7,800 triangles, 23,400 corners and 126 poses. This is an experimental feasibility decision; it does not establish a general or production importer.

The original strict source-normal gate remains **FAILED** at maximum component difference `0.0001531541347503662` versus unchanged `2e-6`. No new normal, correspondence or shading tolerance is adopted. C215's automatic acceptance/provenance flags remain false. Retained source and mapped semantic metadata do not establish live native physics or actions. Held PRs #155/#165/#167/#169 remain unchanged; no prototype or runtime source is integrated. [Exact evidence bindings](docs/engineering/receiving-decision-c219/evidence/BINDINGS.json).

C218's completed delivery is reconciled from the exact saved input ZIP, current package verification, documented offline restore and closed issue #168. C219 uses preserved observations and starts no native process, source program, import/export or renderer. Original failed regressions and every broader failed, unknown or unrun claim remain visible in the [decision](docs/engineering/receiving-decision-c219/DECISION.md).

[PR #171](https://github.com/Omegapy/OntoKin/pull/171) merged the documentation-only decision at `e886f2d6575034fd0c521eda5e21327c2aa5f70d`, tree `00bfe5cacb3c0568e162da3ecce8a314101c1dda`, exactly matching the reviewed candidate. Fresh actual-main documentation checks pass 29 preserved sources / 4,533 local links. Independent review passed 22 decision conditions and 18 integration checks; all 15,575 existing non-navigation entries remain unchanged. [Integration record](docs/engineering/receiving-decision-c219/evidence/publication/INTEGRATION.json).

C219 delivery is confirmed by the exact saved ZIP, fresh input verification/offline restore and closed [scope issue #170](https://github.com/Omegapy/OntoKin/issues/170). Its queued planning step is the current C220 scope above; consumed native schedules remain closed.

## C218 preserved result: saved-scene reopen persistence passed

[C218](docs/engineering/native-reopen-c218/RESULTS.md) completed one independently reviewed reopening of C217's exact saved Blender scene with automatic scripts disabled. The process exited 0 after 9.911 seconds, with no timeout or remaining process group. All 18 objects, 7,800 triangles, 23,400 corner observations and 126 poses were retained. Complete numerical comparison with C217 found zero changed normal, position or pose values; two useful planned images were reviewed. The original scene bytes remain unchanged. The one-start schedule is consumed and closed.

The original strict normal gate remains **FAILED**: maximum source-normal component difference `0.0001531541347503662` exceeds unchanged `2e-6`. Exact saved-scene persistence preserves native values that already contain measured loss. No new tolerance, broader receiving acceptance or full release is claimed. [Measured summary and independent evidence](docs/engineering/native-reopen-c218/evidence/MEASURED-SUMMARY.json).

Executed local observer `efd5002a8dd955a4fb59c96920b0263e35e01a25` and held published source `15c369134cf8ae42d092823aeab9348c9861adfd` have the same tree, but remain distinct Git identities. The nine prototype files stay outside main in [draft PR #169](https://github.com/Omegapy/OntoKin/pull/169). Earlier held PRs #155/#165/#167 remain unchanged. The documentation/evidence result is published at `4a8fea791840e3cf18010c0c9ee12ffc24f3a1ef`, tree `9f8267deb4ddcda4eae6d4c2082aa82b4fec5dc9`, exactly equal to the independently reviewed candidate. Fresh actual-main checks passed 29 preserved sources / 4,518 local links; all 15,561 non-navigation baseline entries remain exact. [Integration record](docs/engineering/native-reopen-c218/evidence/publication/INTEGRATION.json).

**Successor disposition:** C218 final delivery is confirmed in closed [issue #168](https://github.com/Omegapy/OntoKin/issues/168) and independently reverified by C219. C219 above completes the separately versioned finite decision from those observations. C218 historical findings and its closed one-start schedule remain unchanged.

## C217 preserved result: namespace repair and native import/capture passed

[C217](docs/engineering/native-receiving-c217/RESULTS.md) completed one independently reviewed Blender 4.3.2 import/save/capture attempt in 14.217 seconds, exit 0, with no timeout or observed process-group residue. The corrected guard records raw module metadata before classification and accepts only pinned namespace directories while retaining exact concrete-source/cache checks. Actual C217 metadata confirms the selected package is a contained namespace; C216's unrecorded attributes remain unknown.

Independent audits cover all 18 objects, 7,800 triangles, 23,400 corners and 126 poses, with zero missing/ambiguous/invalid correspondence. One native scene and both useful images were produced and reviewed. The maximum normal component difference remains `0.0001531541347503662`; the original `2e-6` gate stays **FAILED**. Saved-scene reopen remains **UNRUN**, and complete receiving acceptance is not established. [Independent result](docs/engineering/native-receiving-c217/evidence/FINAL-IMPORT-REVIEW.md)

Actually executed local source `6af212204d58fbac2a98f3cded44facd67c52528` and published held source `55ce9f34a14cbf3d954332244c9e9a6800ed93fb` share tree `50cd8c97290130fc97945e74c51332bd507e91eb` but retain distinct identities. Prototype source is held in [draft PR #167](https://github.com/Omegapy/OntoKin/pull/167); main receives result documentation/evidence only. Original held PRs #155/#165 and all historical failures remain unchanged.

The documentation/evidence result is published at `7ddb286bb39b3f6d093e03f3f7a306dbc5d539cb`, tree `acacf5aa2b3a208f486453099acd4c9eba1ba109`, exactly equal to the independently reviewed candidate. Fresh actual-main checks pass 29 preserved sources / 4,505 local links, with all 15,539 non-navigation baseline entries unchanged and all eight prototype files absent. [Integration receipt](docs/engineering/native-receiving-c217/evidence/publication/INTEGRATION.json).

**Successor disposition:** C218 completed the separately reviewed one-start reopen above. C217's original source, saved scene, normal failure and consumed schedule remain unchanged.

## C216 preserved result: native start failed before product import

[C216](docs/engineering/native-receiving-c216/RESULTS.md) reviewed one finite Blender capture/save/reopen plan. Its first actual start failed in the initial loaded-importer origin guard for `io_scene_gltf2.blender.com`, exiting with code 19 after 2.325 seconds; the process group was absent. No product GLB import, save, native corner/pose/material capture, render or reopen occurred. One start was consumed and no retry was attempted.

Prelaunch source review passed 12 static findings, 385 input-binding assertions and 14 CPU controls. The installed module directory has no `__init__.py`, supporting a namespace-package explanation, but actual runtime file/loader/spec/search paths were not recorded before the guard raised. The exact executed source is local `2cb197ffe6047b13c9099f2987049ab0d1a29b2d`; identical tree `499fac8f4b51fff9a936d907715ac8427cb273db` is published as held `53a6e3169edf944180120a14b10ae09fc471cfc8` in [draft PR #165](https://github.com/Omegapy/OntoKin/pull/165). Main receives documentation/evidence only. C211's strict normal failure and held PR #155 remain unchanged; C214/C215 grant no new native acceptance.

The documentation/evidence result is published at `5c0dda90cd01ce5e45b12dcfc6615614fe1f64eb`, tree `de22d4ef35b128b955298300df0232f5ad089457`, exactly equal to the independently reviewed candidate. Fresh actual-main checks pass 29 preserved sources / 4,485 local links; all 1,244 protected files and all 15,523 non-navigation baseline tracked files remain exact. [Integration record](docs/engineering/native-receiving-c216/evidence/publication/INTEGRATION.json). No prototype source was merged.

**Successor disposition:** C217 completed the namespace repair and one separately reviewed import/save/capture step below its own finite plan. C216's failed start and missing raw attributes remain unchanged. Its consumed plan must not be replayed. Saved-scene reopen, second-target traceability and the matched authoring comparison remain later gates.

## C215 preserved result: CPU receiving observation adapter and proposed contract

The [C215 CPU adapter](docs/engineering/receiving-adapter-c215/README.md) maps Blender-format triangle corners to C214's exact source normals using source identity, positions and winding. Independent byte locks bind receiver and importer source, build record, settings and scene. The [proposed profile](docs/engineering/receiving-adapter-c215/CONTRACT.md) distinguishes observed, missing, ambiguous and invalid corners and reports component/angular loss. It establishes no native provenance, shading fidelity, receiving acceptance or new tolerance.

Five proof checks pass across all 18 synthetic objects / 7,800 triangles / 23,400 corners, with actual CLI/API output equality and safe existing-output refusal. Independent review checks 35 executable groups / 234,467 successful assertions and five source requirements. [Results and limits](docs/engineering/receiving-adapter-c215/RESULTS.md). Original harness/setup failures and their narrow corrections remain preserved. C214's synthetic-only behavior and C211's original strict `2e-6` failure remain unchanged; PR #155 stays held. No Blender, source program or exporter ran.

[PR #163](https://github.com/Omegapy/OntoKin/pull/163) merged at `d9361ba6c5b05ccdb30ca4dd440eec343c2d0aa5`, tree `bb5a2527d31986dded69eccbf129bf5dcb16e70c`, exactly equal to the reviewed candidate. Fresh actual-main checks pass 29 preserved sources / 4,465 links and all 1,244 protected hashes. [Integration receipt](docs/engineering/receiving-adapter-c215/evidence/publication/INTEGRATION.json).

C215's verified handoff was saved and scope issue #162 closed. C216 attempted the separately reviewed native step above and stopped before import. C215's CPU-only result and all unmet native save/reopen/visual gates retain their meaning.

## C214 preserved result: exact source-normal payload and synthetic loss report

The [C214 CPU prototype](docs/engineering/source-normals-c214/README.md) preserves all 3,024 source-corner float32 normal triples from the exact accepted C210 source/artifact/sidecar. Explicit instance mapping covers 18 objects and 23,400 observation corners. Its separately versioned [proposed profile](docs/engineering/source-normals-c214/CONTRACT.md) strictly validates source, mesh/primitive/corner, winding and direction identities. Synthetic loss reports retain missing/invalid observations and component/angular differences; native observation labels are refused.

All eleven CPU proof checks and 31 predeclared independent controls / 52,957 assertions pass. Exact synthetic copies still report native fidelity and receiving evidence as false; no approximation tolerance is adopted. [Results and limits](docs/engineering/source-normals-c214/RESULTS.md). The original one-link documentation failure and corrected result remain preserved in the C214 handoff. Production/runtime/exporter/receiver/workflow files and original evidence remain unchanged. This finite CPU result is not a full regression or receiving pass.

[PR #161](https://github.com/Omegapy/OntoKin/pull/161) merged at `c4f9c4b97f5a599e5e4708ca69c8d8d1a68470c5`, tree `b2d0ade1102312f4bdf2679548ff08e9124f4b42`, exactly equal to the reviewed candidate. Fresh actual-main documentation checks passed 29 preserved sources / 4,443 local links; all 1,053 protected input hashes remain exact. [Integration receipt](docs/engineering/source-normals-c214/evidence/publication/INTEGRATION.json).

C214's handoff was saved and its scope issue closed. Its [successor instructions](docs/engineering/source-normals-c214/NEXT-TASK.md) are implemented by the bounded C215 CPU adapter above. C214/0.1 remains synthetic-only. C211's original `2e-6` gate remains failed, PR #155 stays held, and save/reopen/visual gates remain unrun.

## C213 preserved result: finite codec loss characterized

The [C213 CPU characterization](docs/engineering/normal-codec-c213/README.md) implements the complete selected pinned Blender normal encoder/decoder with explicit independent frames and source-bound scalar float32 evaluation. Independent review approves 212 predeclared cases / 934 numerical assertions after one explicitly preserved decoder-domain oracle correction, 11 supplemental input refusals and 731 source/execution assertions. A separate 13-check source-fidelity audit passes. The original failed assertion remains retained.

Explicit-frame shortcut cases lose up to `0.014142955653369427` in a normal component in this selected corpus. That observation is not a universal bound or a replay of C211. No replacement tolerance is adopted. C211's original `2e-6` gate remains failed, the receiver in draft PR #155 remains held, and no native process ran. Runtime, exporter, prior receiver and historical evidence are unchanged. [Results and limits](docs/engineering/normal-codec-c213/RESULTS.md)

[PR #159](https://github.com/Omegapy/OntoKin/pull/159) merged at `4e45172c97e22e03c1f04dca1a740fdcd43751ed`, tree `565a2f807872ac6a68fac1875adab426b1f706e7`, exactly equal to the reviewed candidate. Fresh actual-main documentation checks passed 29 preserved sources / 4,416 local links; exact implementation/input equality retains the independent numerical evidence. [Integration receipt](docs/engineering/normal-codec-c213/evidence/publication/INTEGRATION.json). This finite experiment is not a full product regression or receiving pass.

**Successor disposition:** C214 completes the nominated CPU source-normal payload/loss-report prototype above. This does not change C213's finite results, the original C211 strict failure or the need for a separately reviewed receiving contract and execution plan.

## C212 preserved result: strict normal contract retained

The bounded [C212 investigation and decision](docs/engineering/normal-fidelity-c212/README.md) rejects an unsupported tolerance increase and keeps the receiver held. A fresh GLB decoder reproduces C211's exact normal failure; thirteen synthetic CPU controls pass. Eight failing sphere instances reuse one source mesh, so their maximum is not an independent error bound. All 118 installed executable/importer file bindings match C211. Pinned upstream source supports a lossy native encoding/calculation mechanism; exact executable source provenance and causal replay remain unresolved.

[Decision C212/0.1.0](docs/engineering/normal-fidelity-c212/DECISION.md) adopts no replacement numeric budget and changes no receiver, runtime, exporter, original contract or historical evidence. No Blender process ran. The original `2e-6` gate remains failed, draft PR #155 remains held, and issue #154 remains blocked. C212's documentation/evidence increment and its own checks do not establish a complete receiving proof or full regression pass.

[PR #157](https://github.com/Omegapy/OntoKin/pull/157) merged at `e3bb16c21371c7472d6a8eb1e649ed356210db24`, tree `384d3e39d273d69f748064095f80d73e3754af9c`, equal to the reviewed candidate. Fresh actual-main documentation checks passed 29 preserved sources / 4,377 local links; exact analysis-input equality retains the thirteen-control results. The [integration record](docs/engineering/normal-fidelity-c212/evidence/publication/INTEGRATION.json) distinguishes this published decision from the still-failed receiving gate.

**Successor disposition:** C213 completes the nominated CPU codec characterization above. Its finite counterexamples adopt no replacement budget and do not reconstruct missing native frames. C212 and its verified saved handoff remain complete; current work follows the C213 next-task boundary.

## C211 preserved result: Blender receiving proof failed/partial

The selected one-build receiving proof reached a concrete blocker and stopped. [C211 results](docs/engineering/semantic-receiving-c211/RESULTS.md) preserve one actual Blender 4.3.2 import. All 18 objects, 7,800 triangle positions/winding, 126 sampled poses, actual materials and native GLB object extras passed independent comparisons. Split normals failed on 7,088 triangle instances across eight sphere objects: maximum component error `0.0001531541347503662` exceeds the unchanged `0.000002` limit. Rendering separately failed because OpenImageDenoise is unavailable. Native save/reopen and visual inspection were not reached; no second import occurred.

The prototype remains held in [draft PR #155](https://github.com/Omegapy/OntoKin/pull/155) at `cdae8b582a37e37f76f142f07039ba74cedc08ad`, tree `2b2254ae2787a183fda0883fac39b91d2934f9f2`. That head includes an unexecuted denoising correction; it cannot resolve normal fidelity. Actual execution used local `66f1940c4c99f52dfdea835445cdc380498815f7`. Main receives documentation/evidence only, with no receiver product merge. [Scope issue #154](https://github.com/Omegapy/OntoKin/issues/154) remains blocked and open for explicit continuation.

All 302 affected methods (275 existing + 27 new), the fresh 54-check source proof, exact after-artifact reproduction, two Khronos validations and 252 Three.js pose checks passed. The broader mandatory driver was interrupted at the stopping point: 1,476 observed passing methods and 3,205 real methods without outcomes; no full-suite pass. Historical failed regressions remain failed. [Independent failed review](docs/engineering/semantic-receiving-c211/evidence/review/FINAL-REVIEW.json)

**Successor disposition:** C212 completed the normal-fidelity decision, and C213 completed the nominated CPU characterization, while preserving this failure and tolerance. A separately reviewed source-preserving profile or justified approximation policy remains required before another receiving attempt. The second destination and matched authoring comparison remain later stages. C211 itself is closed at its saved handoff.

## C210 current milestone: semantic export and one constrained edit

**Integrated experimental proof; actual-main checks passed.** Starting published main was `94dee707c148b7a545e43d4de0d601642c5fa3e8`; its complete C209 package and offline restore passed. [Scope ownership](https://github.com/Omegapy/OntoKin/issues/152), [results](docs/engineering/semantic-export-c210/RESULTS.md) and [integration state](docs/engineering/semantic-export-c210/evidence/INTEGRATION.json) bind the exact source and evidence. The explicit semantic sidecar reuses existing normalized construction, Agent/0.2 and GLB/0.2; no prior runtime module changed.

The actual edit passed 54 workflow checks, all 275 affected tests (262 existing and 13 new), 68 independent controls, both Khronos validations, 252 Three.js and 252 browser pose comparisons, and four inspected captures. All 18 IDs, 16 unrelated object records and the full eleven-object sibling are preserved. The invalid edit preserves accepted source and artifacts; the same accepted revision regenerates identical finite output.

[PR #153](https://github.com/Omegapy/OntoKin/pull/153) merged at `adfb43c5ab1d7750abfa5e5c74ab62e18a6879e7`, tree `918e398081a70e199e3ae0e29cdea559363397ce`, exactly matching the reviewed publication. Fresh checks on that actual main passed all **275 affected methods**, **43 core cases / 694 assertions**, and **29 preserved sources / 4,318 local links**. The complete checkout remained clean. Exact executable-input equality preserves eligibility of the independent artifact/browser evidence. The work branch was observed absent after merge, with its history retained in merge ancestry. This is integrated development, not a full release.

The broad local attempt remains **FAILED**: 4,342 passing methods, 91 method errors, seven failed-import placeholders and 221 real methods without outcomes, followed by the 900-second termination. Baseline reproductions identify unchanged fixture-copy and bytecode/cache incompatibilities. Root lease/evidence changes also tripped the wrapper's source-stability guard; the isolated immutable inputs match the candidate. The complete affected cohort passed. [Exact accounting and scoped integration rationale](docs/engineering/semantic-export-c210/REGRESSION.md) preserve the failed run without claiming a full regression pass.

**C210 successor disposition:** C211 executed the selected one-build receiving proof and reached the failed/partial result above. C212 records that decision and C213 completes the bounded CPU-only codec characterization; the current next action is the separately versioned source-normal payload/loss-report prototype. The second target/source-traceability proof and matched direct-authoring comparison remain later stages. Unreal support and authoring advantage remain unestablished.

**Explicit deferral:** C209 job/0.2 retained-result compatibility, C201 wrapper/probe/coordinator/host sealing/readiness/admission, broad new syntax, general gameplay, a replacement real-time physics engine, new creature/vehicle/fluid systems, model training, MCP transport and simultaneous backends. Existing reference physics, geometry, materials and validated exports remain current within their profiles. The older universal world/simulation product requirement is superseded as a current completion criterion, not marked complete. Historical domains and exact prior goals remain linked in the decision.

## Main integration lease

No active integration lease. Owner `c223-root-532e737a9a84` releases ownership after independently reviewed PR #179 merged and fresh actual-main focused/documentation checks passed. Author, code reviewer and integration reviewer have finished their bounded work; root completes only final handoff verification, offline restoration and confirmed save, then closes [scope issue #178](https://github.com/Omegapy/OntoKin/issues/178). The merged source is retained in actual main ancestry and the C223 handoff. Held PRs #155/#165/#167/#169 and all consumed schedules remain unchanged. R00 and R01 are completed within their recorded scopes; R02 aggregate regression is the next separately selected task after delivery. No additional feature starts in this thread.

## C209 entry bindings integrated; job/0.2 result compatibility pending

The separate [C209 job/0.2 component](docs/engineering/static-tray-admission-c201/READBACK-ENTRIES-C209.md) binds exact Validator, Three.js, GLTFLoader and package metadata files, versions, roles and declared dependency relationships. Its CPU import mapping rejects ambient lookup. Existing C208 job/0.1 behavior remains unchanged. All process, readiness and admission flags stay false; actual Node resolution and installed-package compatibility remain unverified.

Independent review approved exact component `d5d02cfadfcd549d527e7699224ff07aa389d4be` after 42 controls. Candidate `39ab1d752eab1e00f95a75dade818831e9c6e7cf` passed all 284 C201 methods, 78 source/compiler methods and 43 core cases / 694 assertions. All 605 reviewed hashes, 301 historical input bindings and four frozen protocol documents remain exact. [Source-bound evidence and limits](docs/engineering/static-tray-admission-c201/evidence/entries-c209/README.md)

[PR #151](https://github.com/Omegapy/OntoKin/pull/151) merged at `dcb1ac9b0a579b09294968a27fdd68a22762f620` with the exact reviewed publication tree. Fresh actual-main checks passed all 284 C201 methods in one clean batch, 43 core cases / 694 assertions, 605 reviewed input bindings and 29 preserved sources / 4,282 local links. [Integration receipt](docs/engineering/static-tray-admission-c201/evidence/entries-c209/INTEGRATION.json). C209 originally nominated CPU-only job/0.2 result compatibility; C210 now defers it together with executable wrapper/probe, coordinator, real host/dependency sealing, native readiness and admission. C208's original main timeout and separate pass remain unchanged with cause unproven. The inherited failed full regression remains visible below. No Node, native, receiving, lifecycle or timed-author starts occurred.

## C200 integrated; finite qualification retained

C200 merged through [PR #137](https://github.com/Omegapy/OntoKin/pull/137) at
`2b2f3e7de7595099ad5f9e0176c5596220c0c2dc`, tree
`7e1ab341160cf5b86807e8ffec2cc3bb7b47db92`, equal to the independently reviewed
publication. Its historical executed source remains
`62b2316cc3f88db187f69fbd7fdb2cf0997a97de`. All twelve C200 transactions were
accepted, with twelve receiving and actual-delivery checks, nine controls and
twelve reviewed images. Historical final review passed 16,645 checks and the
separate numeric review passed 497,809 assertions.
[Measured result](docs/engineering/static-tray-exporter-c200/RESULTS.md)

Fresh actual-main checks passed 107 focused methods, ten protocol controls,
43 core cases with 694 assertions and documentation preservation of 29 sources
and 4,106 local links. All 301 locked inputs remained exact. The earlier
47-method compiler pass was reused after input equality checks. These are
separate counts, with no new native, receiving, Node, lifecycle or author run.
[Integration receipt](docs/engineering/static-tray-exporter-c200/evidence/publication-c203/INTEGRATION.json)

C199's failed first construction remains preserved; the combined historical
construction count is thirteen. Both C199 and C200 schedules are closed. The
original coordinator's pending-review `qualified=false` and later independent
`qualified=true` remain separate unchanged receipts. All nine preparation-log
candidates missing from the supplied handoff were subsequently recovered from
original paths; eight stream hashes remain new recovery bindings.

GitGuardian returned neutral because the publication PR was too large to scan;
no security pass is claimed. The former C200 branch was observed absent after
merge, with history retained in merge ancestry and no explicit deletion by
this session. Earlier checkpoints remain in the
[verbatim historical status archive](docs/engineering/static-tray-exporter-c200/evidence/publication-c203/STATUS-before-C203.md.txt).
Its relative links originally resolved from the repository root.

## C204 ledger component integrated; C201 coordinator pending

The [C201 schedule and reservation ledger](docs/engineering/static-tray-admission-c201/LEDGER-C204.md)
is implemented as an isolated control component. Independent review approved exact local
commit `7861e2d0d7ed940cdf2be4b4fe98dbde3e8c373d` for this boundary only.
Its fixed A01/D01/D03/A02/A03/A04 order, persistent one-use receipt, stage reservations,
failed/unknown stopping and interruption handling passed 36 focused methods and six
independent CPU controls. Source/compiler checks passed 78 methods; core conformance
passed 43 cases / 694 assertions. All 301 historical locked inputs and four approved
C201 protocol documents remain unchanged. [Review and evidence](docs/engineering/static-tray-admission-c201/evidence/ledger-c204/REVIEW.md)

[PR #141](https://github.com/Omegapy/OntoKin/pull/141) merged the component at
`ac0c9b5b9135d33bb4b6b27d75ae1dc1897ea4da`. Fresh resulting-main checks passed
36 ledger methods, 43 core cases / 694 assertions and documentation preservation
of 29 original sources and 4,141 local links. The 78 source/compiler methods and
six independent controls remain eligible through exact input equality.
[Integration receipt](docs/engineering/static-tray-admission-c201/evidence/ledger-c204/INTEGRATION.json)

The component starts no children and grants no execution approval. Its recorded
cleanup, promotion and delivery results are caller observations, not validation of
actual outputs. A fixed trusted authority root must be bound by the future executable
lock. Complete coordinator implementation, transaction/readback compatibility,
current-host sealing, independent readiness and native admission remain pending.
[Remaining implementation](docs/engineering/static-tray-admission-c201/IMPLEMENTATION-NEXT.md)

C205 adds the separate input-binding validator described below. Transaction/readback
integration and actual process orchestration remain pending. C201 still has zero
native, receiver and actual-delivery Node starts. Its eventual sole invocation permits at most four of each, counting
failed or unknown starts, with zero timed authors and retries. The C199/C200
schedules stay closed. Protocol-document approval and this component review do not
constitute native readiness or family admission.

## C205 input-binding validator integrated; orchestration pending

The separate [C201 executable input-binding validator](docs/engineering/static-tray-admission-c201/INPUT-LOCK-C205.md)
rejects mismatched protocol, schedule, source/dependency bytes, roles, commands,
clean environments, writable paths, durable reservation authority and independent
approval bindings. It reads actual files and starts no children. Trusted facts must
come from independently retained sealing/review infrastructure; this component does
not authenticate a reviewer, discover the complete host closure or grant readiness.

Independent review approved exact local commit
`28bf6d74f651b22acc0ee5a4154dcd21b861c81b` for this boundary only. All 72 dedicated
methods and 23 independent controls passed. Review corrected dependency traversal,
alternate-path ancestry, clean-launch compatibility and host namespace handling.
Existing checks passed 36 ledger and 78 source/compiler methods, 43 core cases /
694 assertions, and all 301 historical inputs plus four frozen protocol documents.
[Review and evidence](docs/engineering/static-tray-admission-c201/evidence/input-lock-c205/README.md)

[PR #143](https://github.com/Omegapy/OntoKin/pull/143) merged at
`759a91f65331e69491524db06c86ae411ecd3f80`, with the exact local publication tree.
Fresh actual-main checks passed all 108 component/ledger methods, 43 core cases /
694 assertions and documentation preservation of 29 sources and 4,166 local links.
The 78 source/compiler methods and 23 independent controls remain eligible through
exact input equality. [Integration receipt](docs/engineering/static-tray-admission-c201/evidence/input-lock-c205/INTEGRATION.json)

C206 adds the separate transaction/accepted-source component below. Full
readback and coordinator integration,
real host/dependency and alias sealing, durable trusted bootstrap, independent
native readiness and the sole four/four/four invocation remain pending. No native,
receiving, Node, lifecycle or timed-author start occurred in this increment.

## C206 transaction component integrated; original cwd block resolved by C207

The separate [C201 transaction and accepted-source component](docs/engineering/static-tray-admission-c201/TRANSACTION-C206.md) resolves actual retained baseline source and dependencies, validates complete construction/receiving/receipt closures, and conditionally promotes an accepted pointer. Pre-commit rejection preserves the prior pointer; post-replacement interruption reports UNKNOWN. It starts no children and does not advance the coordinator ledger.

Independent review approved local commit `afa0a9d40ab0ffbf88e6540bbb685d889a67d391` for fixture-only preparation. All 47 new methods, 108 existing C201 methods, 22 independent controls and 78 source/compiler methods passed. Core conformance passed 43 cases / 694 assertions; all 301 historical inputs and four protocol documents remained exact. [Review and evidence](docs/engineering/static-tray-admission-c201/evidence/transaction-c206/README.md)

C206 originally rejected production bindings with `C201-NATIVE-CWD` because the C205 launch plan required repository cwd while the qualified supervisor and worker required the stage output directory. C207 below resolves that mismatch in the C201 bindings. The historical worker/supervisor remain unchanged. Readback, actual process provenance/deadlines, full coordinator, trusted bootstrap/host sealing, native readiness and admission remain pending. This increment has zero native, receiving, Node, lifecycle or timed-author starts.

The exact original C205 `final-tests.log`, already present in the previous handoff, is restored as tracked evidence to repair its existing documentation link. The original failed documentation check and byte-binding record are retained. Repaired documentation verification passed 29 preserved sources and 4,199 local links. [PR #145](https://github.com/Omegapy/OntoKin/pull/145) merged at `6573597a699ed90920a9cea3e17250bce5babbdc` with the exact local publication tree. Fresh actual-main checks passed all 155 C201 methods, 43 core cases / 694 assertions and 29 preserved documentation sources / 4,199 local links. All 56 independent bindings and complete product/test prefixes matched. [Integration receipt](docs/engineering/static-tray-admission-c201/evidence/transaction-c206/INTEGRATION.json)

## C207 working-directory alignment integrated; readback remains pending

The [C207 contract](docs/engineering/static-tray-admission-c201/WORKING-DIRECTORIES-C207.md) binds every planned command cwd to its own stage output directory. Construction/receiving jobs and supervisor receipts must agree with that same path. Wrong or changed paths/commands reject before acceptance. The former blanket `C201-NATIVE-CWD` purpose block is removed; validated production-shaped fixture records still confer no native authorization, current-host approval or admission.

Independent review approved exact local candidate `bd9fbf1487e557b9c21baf1d39e7b9cb818d4773` for this component only. All 171 C201 methods, 29 independent controls, 78 source/compiler methods and 43 core cases / 694 assertions passed. All 36 reviewed bindings, 301 historical inputs and four frozen protocol documents remain exact. [Review and evidence](docs/engineering/static-tray-admission-c201/evidence/cwd-c207/README.md)

C208 below adds the separate readback job/result binding component. The Node cwd is consistently planned, while executable dependency-entry mapping and the C201 probe/wrapper roles remain unimplemented. Complete coordinator/process provenance/deadlines, trusted bootstrap, real host/dependency/alias sealing, independent native readiness and actual admission remain pending. No C201 native, receiving, Node, lifecycle or timed-author process started. [PR #147](https://github.com/Omegapy/OntoKin/pull/147) merged at `d952254d5e63602e6d11c696e62ae8965d57c78e` with the exact reviewed publication tree. Fresh actual-main checks passed all 171 C201 methods, 43 core cases / 694 assertions and documentation preservation of 29 sources / 4,233 links. [Integration receipt](docs/engineering/static-tray-admission-c201/evidence/cwd-c207/INTEGRATION.json)

## C208 readback binding integrated; executable job remains pending

The separate [C208 component](docs/engineering/static-tray-admission-c201/READBACK-BINDING-C208.md) binds actual accepted source/transaction closures, GLB and audit bytes to exact jobs, output inventories, check options and process observations. It checks Khronos issue consistency and all 2,060 required Q01 numeric rows from supplied Three.js observations. Failed or unknown checks preserve the accepted pointer and stop that binding session. Returned evidence grants no execution, next-slot, readiness or admission authority.

Independent review approved local candidate `a645731147e4ce95ddaab8132c5a261cc3a9f44a` for this boundary only. All 223 C201 methods, 63 independent controls, 78 source/compiler methods and 43 core cases / 694 assertions passed. All 66 reviewed input bindings, 301 historical locked inputs and four frozen protocol documents remain exact. [Review and evidence](docs/engineering/static-tray-admission-c201/evidence/readback-c208/README.md)

[PR #149](https://github.com/Omegapy/OntoKin/pull/149) merged at `f8e397405b432d7a63464b136431d15a009c38df` with the exact publication tree. The first actual-main C201 batch remains FAILED: 222 methods passed and one synthetic four-slot setup hit the unchanged three-second promotion limit. The affected method passed separately with identical source/limits; all 223 methods have successful observations across two runs, not one clean batch. The cause is unproven. Independent review retained component approval with this timing limitation. Core passed 43 cases / 694 assertions; documentation preserved 29 sources and 4,258 links. [Integration and original failure](docs/engineering/static-tray-admission-c201/evidence/readback-c208/INTEGRATION.json)

The former C208 next step was the versioned job extension completed by C209 for exact lock-bound validator, Three.js and GLTFLoader entry points; further C201 preparation is now deferred. The current job is preparation data, not an executable probe contract. Actual wrapper/probe, complete coordinator/process provenance, real host sealing, native readiness and admission remain pending. No C201 native, receiving, Node, lifecycle or timed-author process started.

## Verification and remaining limits

The inherited full regression remains **FAILED**: **4,239 distinct passing
methods and thirteen torque-read methods NOT RUN** after the unchanged
30,000 ms setup timeout. A newly introduced or worsened legacy failure blocks
integration. Local checks follow [OK-ENG-006](docs/engineering/OK-ENG-006-local-validation-and-hosted-ci-policy.md);
no hosted pass or full regression pass is inferred from a focused check.

The fixed N05/N06 views cannot resolve the minimum-size tray. N07/N08 hide the
right interior/proxy. Numerical receiving checks passed, but hidden or
unresolvable surfaces are not visually certified. C200 establishes its finite
static mapping and recorded deliveries. General contact, live destination
physics, actual-Blender cancellation behavior, external compatibility and
sixteen external roles, comparative authoring advantage and full release remain
unestablished. [Evidence preservation](docs/engineering/static-tray-exporter-c200/evidence/publication-c203/PRESERVATION.md)

The earlier broader product ambitions remain uncompleted and classified by C210: typed algorithms and reusable
libraries; composite rigid assets, materials, forces and contacts; mechanisms
and vehicles; articulated creature bodies, skin deformation and purposeful
movement; flight and swimming; vegetation and wind; terrain and buildings;
liquids and deformable solids; appearance and textures; animation transitions,
live engines, scale and performance. Each expansion needs its named contract,
bounded tests and destination evidence. Finite tray qualification does not
complete those domains or the planned direct-tool comparison. The revised goal prioritizes semantic authoring and checked transport; new domain expansion requires a demonstrated need.

Keep stable source revisions and part identities, declared units/frames,
separate ownership/following/connections, one motion authority, represented
mass and honest state transfer. Ordinary execution defaults remain 100,000
operations and 30,000 ms; explicit larger requests require current host
authority. Original fixtures, tolerances, budgets, gates and prior releases
retain their meanings. Historical checkpoints and complete release records
remain available through the archive and [GOAL](GOAL.md).

