# C216: native receiving start stopped before import

**The receiving proof failed before the product GLB import call.** One approved Blender process started and exited with code 19 after 2.325 seconds. The initial importer-module origin check refused `io_scene_gltf2.blender.com`. The process group was absent after exit and on independent readback. No retry or reopen occurred.

The exact capture prototype is retained in [draft PR #165](https://github.com/Omegapy/OntoKin/pull/165), not merged into the product or main. This main record contains documentation and evidence only. [Scope issue #164](https://github.com/Omegapy/OntoKin/issues/164) and the [C216 recovery checkpoint](https://chatgpt.com/library?file_id=libfile_fde3_f-c2d4d4a41da48191aa40ec3a9ef904a9_2ab2a24d43748191957f9bcc356b59de&account_id=personal) preserve the current delivery state.

## Selected finite promise

C215 supplied a CPU adapter for associating recorded Blender corners with exact source normals. A normal is a direction used to shade a surface. C216 selected one actual receiving experiment: retain exact accepted source authority, observe native geometry and shading, disclose measured loss, save a native scene, then conditionally reopen and inspect it. This adopted no new normal tolerance and could not pass C211's original strict `2e-6` gate by retaining metadata or observing a small error.

The reviewed schedule allowed at most two starts, each limited to 240 seconds and two Blender threads. The first was import/save/capture/two planned renders; the second required complete independent numeric, provenance and visual review of the first. Any failed or unknown required gate stopped continuation. The first failure therefore closed this schedule. The unused second slot is not retry permission.

## Exact source and prepared inputs

| Identity | Revision or binding |
| --- | --- |
| Verified starting main | `ad2b90b5eb28c7ec806ef10f53c90c9281230953` |
| First capture checkpoint, unpublished | `cb0efc3f93b7da0f66368b5dd33315577516ea95` |
| First complete plan source, unpublished and unexecuted | `931fd78a2c1d592f4ee419a4d7a5123fec43025e` |
| Reviewed and actually executed source, unpublished Git identity | `2cb197ffe6047b13c9099f2987049ab0d1a29b2d` |
| Published held source | `53a6e3169edf944180120a14b10ae09fc471cfc8` |
| Identical executed/published source tree | `499fac8f4b51fff9a936d907715ac8427cb273db` |
| Executed prepared plan, canonical SHA-256 | `8899d0557a030c1ddf3ec6fba9f766295ce7004b93a77f8d18011d8e05e12bda` |

The commits remain distinct even though the held tree equals the executed tree. Six additive prototype files contain the capture, driver, shared binding helper, exact installed-build bindings, contract and instructions. Existing runtime, compiler, Agent, exporter, held C211 receiver, C214 authority and C215 reporter bytes were unchanged.

The executable `/usr/bin/blender` is 94,967,000 bytes, SHA-256 `0dfe9af0f3e67643ecf15327fa5e14e7315f61d1a81afdcafe76a71b1918e2b4`. All 117 installed importer Python files matched retained C211 bindings. Source review, preparation and byte checking used Linux x86-64 / CPython 3.12.14. The actual native stdout identifies Blender 4.3.2. The process failed before the capture's planned runtime-label/module receipt, so that unrun check is not reported passed. Upstream build hash `Unknown` and incomplete shared-library/source-build lineage remain limitations.

Both preparation records are preserved. `run-01` used the first complete source and never launched. Before execution, review added a narrow cache/module-origin record and prepared `run-02` from the final frozen source. The native failure belongs only to the latter. No preparation or CPU control is counted as a native start.

## What passed and what failed

Prelaunch review passed 12 static findings, 385 byte/Git/input-binding assertions and 14 CPU controls. The accepted source triple and exact C214 normal payload were retained; the importer source was preserved separately. Syntax checks, whitespace checking, preparation and exact readback passed. These results did not establish compatibility with every actual startup module. Prelaunch review missed the namespace-package shape encountered by the first native start.

The actual failure occurred in `importer_modules()` during the initial cache/module inventory, before the first raw importer receipt was written. The guard required every loaded importer entry to have a concrete source-file path contained in the pinned file inventory. The observed diagnostic is:

> Loaded importer module has unpinned origin: io_scene_gltf2.blender.com

The installed `io_scene_gltf2/blender/com` directory contains nine pinned Python files and has no `__init__.py`. That is consistent with a Python namespace package, whose identity can come from package search directories rather than one source file. This is a strong static explanation for the refusal, not a captured observation of the failing module's `__file__`, loader, spec origin or search locations. Those attributes remain unknown because validation raised before saving them. Some importer modules had already loaded during Blender startup; no explicit product GLB import occurred.

| Gate | Observed disposition |
| --- | --- |
| Exact prelaunch source/input/build review | Passed within its declared finite scope |
| First native start | Failed, exit 19, 2.3252033009994193 seconds; no timeout |
| Process outcome | Known; process group absent on repeated readback |
| Initial complete loaded-importer receipt | Not produced; guard failed while constructing it |
| Product GLB import | Not reached |
| Saved native scene and final scene lock | Not reached |
| Native corner/pose/material/semantic measurements | Not reached; no loss values or native denominator result |
| Planned overview and curved-surface render | Not reached |
| Reopen and persistence checks | Not reached; no second reservation |
| Receiving acceptance | Failed/incomplete |

The independent failure audit confirms the exact source/plan/receipt bindings, stage and absent outputs. Its audit success means that the failure was correctly accounted for; it is not a receiving pass. See [retained evidence](evidence/README.md).

The independent reviewer also preserved an earlier CPU-harness inventory assertion failure while adapting its reference checker. A narrow corrected assertion passed without changing capture or source input bytes. The original code, output and correction remain in the handoff. All prior failed/incomplete product regressions and C211's normal failure remain visible. No new full-suite pass is claimed.

## Stopping point and next action

No fix, retry, rendering fallback or second milestone was attempted after this blocker. Draft PR #165 retains the exact failed prototype. Draft PR #155 and C211's original failed strict-normal contract remain unchanged. C214 remains synthetic-only; C215's fidelity/provenance/receiving fields remain false.

The [next bounded task](NEXT-TASK.md) is a narrow namespace-aware module-origin repair with raw diagnostics preserved before classification, meaningful synthetic controls, exact source/plan review and at most one fresh import/save/capture/visual start. It must not replay this consumed plan. Save/reopen fidelity, useful native shading evidence, the second destination and the direct-authoring comparison remain unproved.

The final C216 handoff must retain all historical bytes, the exact local and published source identities, both prepared plans, raw process/failure records and independent evidence, then verify offline restoration and confirm the ZIP save. Delivery completes this stopped step only.
