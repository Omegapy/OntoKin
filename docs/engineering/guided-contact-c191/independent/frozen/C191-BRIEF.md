# C191 proposal: source-owned guided contact through Blender/Bullet

**Status: proposed next scope, not an adopted language contract or completed capability.** Define and adopt one bounded experimental contract, then qualify a small adapter and independent fixtures. Do this before another authoring comparison.

## Why this step

C190's OntoKin recovery replication retained geometry and following but passed through both stops: 250 mm travel and final signed gaps of −50/−75 mm. Native inspection reported contact unavailable; a physical follower was rejected. This establishes a capability limit, not comparative authoring performance.[1]

GOAL keeps design intent in `.ok`, delegates simulation to specialists and requires a qualified common backend before isolating the language's contribution.[2] Reuse the exact C190-qualified Blender/Bullet build through a thin adapter; defer a general engine, importer and production backend.

## Start the next discussion

Read GOAL, AGENTS, STATUS and the actual GitHub head/lease. **Spawn exactly two fresh subagents in this shared execution environment:** a contract/adapter author and an independent fixture/conformance reviewer. The coordinator reconciles their work and integrates. No separate host or isolation preflight is required; this is not a blind study. Routine development is authorized without another user confirmation.

## Contract to settle before implementation

Adopt explicit experimental source/profile and backend/output bindings, with frozen grammar, schemas, examples, diagnostics and compatibility rules. **This brief assigns no syntax or version.** Keep source `0.22`, `torque-0.1`, Agent/0.22 and GLB/0.22 unchanged; do not relabel new results as old-profile executions.[3]

| Required concept | Finite promise |
| --- | --- |
| Source authority | One immutable `.ok` revision and dependency closure own geometry, mass, collider dimensions/offsets, initial state, guide, collision enablement and stop position. Python performs the declared mapping. No manual scene preparation or task-specific hidden constants. |
| Identity | Stable, distinct body and collider keys, bound to their source occurrence and revision. Record body → native rigid body → collider → visible-part mappings. Renaming/reordering siblings must not remap a collider. |
| Mass and attachment | Each carriage owns exactly one 1 kg moving body. Its shoe collider contributes no additional mass and has exactly one owner. Visible shoes remain rigid followers. Do not reinterpret `follow` as a force-bearing joint or reinterpret inherited `sphere_body` as a box. |
| Motion authority | At modeled t = 0 each lane has one solver-controlled X coordinate, with a native linear velocity motor requesting the source-declared feed of 125 or 150 mm/s. The feed may remain active against contact; the solver alone determines pose. Lock Y/Z and rotation and leave X unbounded. Prohibit transform-position drivers, timed stops, contact-time tables, competing motion authorities and post-solve changes to X travel. |
| Collision geometry | The source owns four shoe/stop contact boxes. Enumerate the C190 native construction separately: two compound carriage bodies, their shoe and hidden carriage box children, two fixed stop boxes and a passive base anchor. Derive every helper dimension/frame from source, document its ownership and filtering, and introduce no independent moving mass authority. An exact four-native-shape design or exclusive matching-pair filter is a new qualification, not a C190 result. |
| Backend boundary | Pin executable/build hashes, Bullet provenance, platform, source-to-Blender axis/unit transform, body-frame transform, timestep/substeps, iterations, margins, filters, friction/restitution and initialization procedure. Zero gravity, friction and restitution. No general inertia or arbitrary contact claim. |

Hidden native proxies require an explicit, verified frame transform; only seven solids remain visible. Declare the initial pose, active feed, maximum native motor impulse and initialization. The measured binding maps the requested positive feed to `-speed_mm_s / 1000` for the native base/carriage ordering, with maximum motor impulse 100000. Verify feed from the first recorded interval. No kinematic handoff or pre-roll is required. This is feed-controlled contact, not a calibrated actuator-force model. Preserve frame/ownership meanings and count moving mass once: 2 kg.[4]

Reject unsupported shapes, rotations, guides, contact laws, multiple owners, duplicate IDs, conflicting motion authorities, initial overlap and unqualified backend settings. Freeze exact diagnostic codes, phases, source spans and blocked result levels at adoption. A missing backend, exhausted budget or failed solve cannot produce a successful later state. A failed edit or publication retains the accepted revision and previous artifacts.

## Freeze the qualification cases

The independent reviewer derives expectations from dimensions and pre-contact feed speeds, before inspecting prototype output. Use the unchanged seven-part C190 assembly, a 30 mm left stop, right stop at 495 mm and duration 2 s. Positive source variants differ only in left-stop X. The disabled control changes only the left shoe collider's enabled setting.

| Case | Left stop near face | Expected physical response | Left travel at 2 s |
| --- | ---: | --- | ---: |
| A | 380 mm | First contact at 1.600 s; halt | 200 mm |
| B | 355 mm | First contact at 1.400 s; halt | 175 mm |
| C, independent interpolation edit | 367.5 mm | First contact at 1.500 s; halt | 187.5 mm |
| D, collider disabled | 380 mm | No contact response; pass through | 250 mm; signed gap −50 mm |

In every case the right lane travels 300 mm and retains 15 mm clearance. The expected left contact time is `(stop_x − 180 mm) / (125 mm/s)`, not an input supplied to the solver. Add independent rejection fixtures for the contract errors above, a source edit rollback case, and a renamed/reordered identity control. Preserve the old .22 rejection and pass-through fixtures unchanged.

**Proposed acceptance limits**, to freeze before implementation: geometry/initial world bounds within 0.2 mm; linear color channels within 0.005; fixed-part and shoe/carriage offset drift within 0.1 mm; positive final travel and signed gap within 0.5 mm; contact onset within 0.005 s of the analytic value; left sampled finite-difference residual speed at most 0.5 mm/s from 0.025 s after ideal contact through 2 s; pre-contact and right speed within 0.5 mm/s. No later rebound displacement above 0.1 mm. For positive contact cases A–C, maximum shoe-face penetration past the stop near face must remain at most 0.5 mm across every exported interpolation interval, not only at the final state. In all four cases, certify continuous nonoverlap for all twenty unrelated visible-part pairs throughout the clip; the intended left shoe/left stop pair is evaluated separately. The disabled-collider control retains its expected pass-through. Retain 240 Hz native capture and GLB recording, 481 common keys, 10 substeps per frame, nominal 1/2400-second solver step and 100 iterations. C190 had a short correction above 0.5 mm/s at 12.5 ms; a new 10 ms settling gate is not qualified by this evidence. If the existing backend cannot meet these proposed gates, retain that failure and review a contract change before freezing new expectations. Do not adjust limits after candidate results to claim a pass.

## Evidence required to qualify the adapter

1. **Build twice** in fresh processes and empty scenes. Retain source, canonical solver input, mappings, scripts, commands, versions, hashes and failures. Require identical canonical inputs and final GLB bytes on the pinned environment; do not assume `.blend` byte identity.
2. **Inspect the native solve:** bodies, masses, transforms, guides, flags and initialization. Bind native trajectories/velocities to body/collider IDs and disclose their actual cadence. Retain contact/impulse records where exposed; never derive purported solver records from overlap. Leave unobservable claims unqualified. Disabled-collider response and the 367.5 mm edit must rule out a baked stopping schedule.
3. **Reopen the generated `.blend`** in a new process. Verify persisted settings, clear caches and replay the declared initialization without rebuilding/repairing the scene. Reproduce contact and disabled pass-through; a cached trajectory is insufficient.
4. **Check raw/final GLBs independently:** seven IDs, dimensions/colors, fixed poses, offsets, trajectories, gaps and collider correspondence at every key and interpolation interval. Preserve every native carriage X sample and time. A disclosed final projection may remove numerical rotation/transverse guide residuals only if it lists every changed field and bounds native-sample and continuous raw-export playback vertex deviation within a proposed 0.2 mm mapping limit. It cannot qualify unobserved native substeps or contact impulses. Document adapter changes and preserved bytes. Run format/geometry checks and review receiving-application playback against the same hashes.[5]

A picture, metadata or source acceptance alone is not solver evidence.

## Bounds, deliverables and decision

Limit this experiment to seven visible solids, two moving masses, four source-owned shoe/stop contact boxes plus the explicitly enumerated native helper shapes, two independent world-X guides and one declared native linear feed motor per lane and two modeled seconds. No external asset import, network fetch, arbitrary Python from source, mesh collision, nonzero friction or restitution, arbitrary actuators, general articulation or dynamic/dynamic contact. Preserve ordinary execution defaults of 100,000 operations/30,000 ms. Freeze any explicit higher source request and host ceiling separately; C190's 1,000,000 operations/80,000 ms is a proposed starting allocation, not automatic authority. Supervise the backend with a finite wall-clock deadline; cap steps, native objects, trace/output bytes and cancellation latency in the adopted contract. Verify cancellation, malformed results and atomic publication failures.[2], [6]

Deliver the exact adopted contract/input manifest, compatibility decision, small adapter, independent oracle/checker, all four editable `.ok` cases, native `.blend` files, raw/final GLBs, native and reopened traces, diagnostics, two clean rebuild receipts and a capability/loss report. Apply relevant local regression, original conformance, delivery and preservation checks; do not modify frozen historical tests. Integration and experimental qualification remain separate from full release.[6]

**Advance only when these identified gates pass.** Then propose a later comparison using the same pinned backend and disclose adapter setup cost separately. C191 itself establishes no general contact capability, production adapter, comparative authoring benefit or completed GOAL.

### Basis

[1] C190 recovery replication: `../deliveries/ontokin/README.md`, `../deliveries/ontokin/build/*/native-state.json`, probe diagnostics and the delivery `SHA256SUMS` (manifest SHA-256 `ea2fc2bdc6e85001eed8eda4b84d4b4fd7786b21df14f1af738bab57cfedbe95`). This is new recovery evidence, not the missing original run.

[2] Repository `GOAL.md`, “Near-term investment”, “How to decide whether to expand” and “Execution budgets”; `docs/engineering/semantic-physical-scope-c180/README.md`.

[3] `docs/language-design/torque-v0.1/ADOPTION.md` and `SPECIFICATION.md`; `ontokin/torque_agent_catalog.py` (contacts unsupported).

[4] `docs/language-design/OK-LANG-001-core-language-specification.md`, LANG-012, LANG-014 and LANG-015; `AGENTS.md`, “Preserve meaning and evidence”.

[5] `docs/engineering/OK-ENG-002-3d-scene-animation-export-and-visual-validation.md`; the new output contract must state its own backend-specific evidence without weakening the historical contract.

[6] `AGENTS.md`; `docs/engineering/OK-ENG-006-local-validation-and-hosted-ci-policy.md`; `docs/engineering/OK-ENG-009-development-integration-and-branch-lifecycle.md`.
