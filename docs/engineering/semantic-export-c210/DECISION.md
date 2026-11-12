# C210 scope decision: semantic authoring and checked transport

**Adopted direction: November 11, 2026, America/Denver.** The owner's attached C210 instruction supersedes conflicting queued priorities. This decision changes investment and sequencing; it does not change adopted language semantics or pass an unmet gate. See [current status](../../../STATUS.md), [goal](../../../GOAL.md), [contract](CONTRACT.md) and [scope ownership](https://github.com/Omegapy/OntoKin/issues/152).

## Mission and authority

OntoKin is an AI-native semantic language and intermediate representation for constructing, inspecting, validating, repairing and transporting physically meaningful 3D objects. Semantic information states what named parts are, how they relate, their dimensions and units, declared physical properties, constraints and source identity. An intermediate representation is the structured object description used between accepted source and destination tools.

Accepted `.ok` source remains authoritative. The existing normalized `SceneModel` is the representation to reuse. Preserve reusable definitions, stable occurrence identities, pinned dependencies, source provenance, bounded evaluation, atomic revision-safe edits, geometry, materials and validated delivery. No new syntax, Agent protocol or parallel intermediate representation is needed for this increment.

Rendering, general simulation and gameplay belong to engines and specialist tools. Unreal Scene Graph and Verse are intended integration targets; OntoKin supplies object meaning and checked mappings while the destination owns runtime behavior. Engine neutrality and existing GLB/Blender work remain current. The [Unreal boundary](UNREAL-INTEROP.md) distinguishes documented conceptual mappings from implemented support.

## Disposition of earlier ambitions and work

| Earlier direction or obligation | Current disposition | Reason and retained evidence |
| --- | --- | --- |
| Source language, reusable construction, inspection and localized repair | Current | These provide the stable authored meaning and revision control the new direction needs. Existing released profiles retain their contracts. |
| Geometry, materials, recorded GLB and existing Blender experiments | Current within their proved profiles | Reuse them for checked object transport; preserve their format, numerical and visual gates. |
| Bounded reference physics and existing motion profiles | Current as reference checks | Existing semantics and failures remain intact; metadata or playback does not establish destination physics. |
| Earlier requirement to complete every world, gameplay and simulation domain as OntoKin's product | Superseded as a current completion criterion | The current product boundary is semantic object authoring and checked transport. The [pre-C210 goal](https://github.com/Omegapy/OntoKin/blob/94dee707c148b7a545e43d4de0d601642c5fa3e8/GOAL.md) and historical PRD/capability records preserve the earlier ambition; no unmet domain is reported completed. |
| General gameplay programming and a replacement real-time physics engine | Deferred; destination-owned in this direction | Later work requires a demonstrated authoring or interoperability need, not the old world-building roadmap alone. |
| Broad new syntax; new creature, vehicle, fluid or deformable systems; model training; MCP transport | Deferred | They are outside the missing contract established by this inventory. Existing finite implementations remain preserved. |
| Further terrain/building systems, appearance/texture extensions, animation transitions, live-engine behavior and scale/performance expansion | Deferred unless a demonstrated authoring or interoperability need selects them | Existing geometry, materials, textures and recordings retain their implemented profiles; unfinished extensions are not reported completed. |
| C209 CPU-only job/0.2 retained-result compatibility | Explicitly deferred | It is not a dependency of the existing Agent/0.2 and GLB/0.2 path. C209's accepted component and exact evidence remain unchanged. |
| C201 native wrapper/probe, coordinator, host sealing, readiness and admission | Deferred, uncompleted | No C201 execution is authorized here. The four frozen protocol files remain byte-for-byte unchanged. |
| C199 failed construction and C200 twelve-transaction qualification | Historical, closed schedules | Preserve every outcome, consumed start, image limitation and hash. A new semantic proof does not reopen either schedule. |
| Controlled comparison against direct tools | Current gate before broad investment, sequenced after bounded interoperability proofs | Preserve matched conditions, unseen variants and predefined measures. The finite experiment below is not an author study or a benefit claim. |

The former GOAL deferred a general importer, capture pipeline or new production backend until the comparison justified its expense. That restriction is **clarified and revised explicitly** to permit one small, version-pinned receiving-application experiment after this semantic proof, then one second-target/source-traceability proof before the comparison. The bounded exception establishes feasibility and identifies loss; it does not authorize general importers, capture pipelines, simultaneous backends, production integration or broad language investment. Those still require demonstrated need and measured benefit. Existing C180 comparison principles and closed trial schedules remain unchanged.

## Existing architecture and the exact gap

| Existing component | Reused responsibility | Missing finite contract |
| --- | --- | --- |
| `ontokin/model.py` | Normalized objects, sites, joints, following, placements, physical declarations and source/occurrence provenance | No separate model is introduced. |
| `ontokin/bundle.py` and `ontokin/construction.py` | Exact source closure, program revision, original definition and keyed occurrence identities | Bind the semantic delivery to the same complete source closure. |
| `ontokin/program_agent.py` | Accepted revisions, scoped atomic edits, rejected candidates, retries and artifact retrieval | Demonstrate the existing path; do not add a protocol. |
| `ontokin/scene.py` and `ontokin/gltf.py` | Recorded world transforms, source and ownership metadata, actual geometry/material serialization and decoded checks | Expose a portable, versioned sidecar with checked node/mesh/accessor references and explicit feature treatment. |
| Existing keyed-rack fixture and `tools/build_construction_demo.py` | Pinned reusable components, two sibling assemblies, generated keyed parts and a targeted repair | Derive a separate proof harness without changing frozen source or expected results. |

The selected proof changes `first.fingers["middle"].length` from 0.65 m to 0.75 m. It compares unchanged semantic values and stable identities separately from revision-bound source locations, hashes and artifact offsets that can legitimately change. Ownership is not transform parenting; following, physical connections, declared placement and motion authority remain distinct.

## Bounded implementation and completion conditions

New files implement an explicitly selected semantic sidecar, a proof driver, focused tests and the finite contract. Existing compiler, Agent and GLB writer behavior remains unchanged. The root documentation and active navigation adopt this decision. The main integrator owns those shared files and publication; the implementation worker owns only the sidecar/driver/tests/contract on its isolated branch.

The proof must execute the actual source/compiler/Agent/export path and establish:

1. One accepted object's complete supported semantic records are bound to its source revision, dependency pins and exact delivered GLB.
2. A valid targeted parameter edit changes the intended geometry while preserving unaffected identities, semantic values and sibling geometry.
3. An invalid edit preserves the last accepted source and accepted artifacts; retry and stale-revision cases use the actual protocol.
4. The same accepted revision reproduces the result under the contract's declared deterministic comparison rule.
5. Required unsupported features are rejected, and all declared/exported feature treatment is machine-readable with reasons.
6. Independent controls detect stale source/artifact pairings and broken geometry references. Applicable regressions, source-to-artifact checks, Khronos/Three.js checks and visual inspection are recorded for exact inputs.

Passing this gate establishes one experimental finite proof. It establishes neither Unreal support nor a general authoring advantage. A missing required check or a need for broader syntax/refactoring blocks integration; preserve a partial implementation and name the next concrete action instead of calling prose complete.

## Staged roadmap

| Order | Bounded stage | Evidence needed to advance |
| --- | --- | --- |
| 1 | This engine-neutral semantic export and constrained edit | Accepted-source/artifact binding, preservation, failure handling, deterministic regeneration, explicit loss and independent delivered-geometry checks. |
| 2 | One version-pinned receiving application | Execute import in the chosen installed application/build; measure identity, units/frames, geometry and supported semantics after import; record loss. Select the application based on actual availability and task needs. |
| 3 | Second target and source traceability | Reuse the accepted semantic source through one other target; trace received parts back to source and prove which facts survive both mappings. |
| 4 | Controlled comparison with direct authoring | Matched direct-tool baselines, unseen variants and comparable model, tool and resource settings, with measures declared before execution. |

This is an order of work, not a 90-day commitment. Only stage 1 is in this thread. Later comparison must measure edit correctness, unaffected-part preservation, recovery, reproducibility, elapsed time/tokens and cross-target reuse. Separate setup cost from task work, retain failures in the denominator, and compare costs at matched success levels. Broader language investment requires demonstrated benefit. Comparable direct-tool results trigger a documented scope reassessment, including whether a semantic schema and validation toolkit is sufficient.

## Preserved limits and evidence

Ordinary source budgets remain 100,000 operations and 30,000 ms. Original fixtures, tolerances and frozen trial budgets do not change. C208's original main timing failure and its separate isolated pass remain distinct; the cause is unproven. The inherited full regression remains failed with 4,239 distinct passes and thirteen torque-read methods not run after its unchanged 30,000 ms setup timeout. New checks report their own outcomes and cannot rewrite those records.

The complete C209 source handoff was verified at SHA-256 `d5e746235cfdc357a29fc078354fdd128806b39b93dc841cb4cd20a2251ff24d` and restored offline to published main `94dee707c148b7a545e43d4de0d601642c5fa3e8`. C210 uses fresh live reconciliation and serialized integration. Exact input links, historical preservation, publication, local-only histories and save receipts belong in the C210 handoff.
