# OntoKin goal

Owner adopted semantic authoring: **November 11, 2026**. [November 16 C252 decision](docs/engineering/review-integration-c252/DECISION.md): retains [C210 boundary](docs/engineering/semantic-export-c210/DECISION.md); comparative evidence before receiver expansion. [STATUS](STATUS.md) owns actual results/next gates; [AGENTS](AGENTS.md) governs coordination/preservation.

## Mission

Build AI-native semantic language + intermediate representation: construct, inspect, validate, repair, transport physically meaningful 3D objects. Preserve named parts, relationships, dimensions/units, physical declarations, constraints, source identity; reuse existing normalized records between accepted source/destinations.

Authority: accepted `.ok`. Preserve language/classes/libraries, stable identities, pinned dependencies, provenance, bounded evaluation, revision-safe editing, geometry/materials, validated exports. Agents must inspect named parts, edit supported parameters, reject invalid candidates without losing accepted designs, regenerate checked artifacts. Ordinary playback: no model call/frame needed.

Engines/specialist tools own rendering/general simulation/gameplay; OntoKin supplies object meaning/checked mappings; destinations own runtime behavior. Preserve engine neutrality, GLB/Blender capabilities. Intended Unreal Scene Graph/Verse targets: distinguish conceptual/implemented support per [interoperability boundary](docs/engineering/semantic-export-c210/UNREAL-INTEROP.md).

## Current priorities and non-goals

Required:

- Semantic assemblies: stable object/part identities, reusable definitions, distinct occurrence provenance.
- Dimensions/units/frames: explicit quantities/placement; check supported constraints against source and delivered geometry.
- Relationships/physical declarations: separate ownership/placement/following/connection/motion authority; count matter once.
- Localized repair: atomic failure preserves accepted revision; success preserves unrelated parts.
- Checked transport: exact source/dependency/artifact references, machine-readable preservation/loss, measured destination evidence.

Finite physics: useful reference checks. Defer unless selected by demonstrated authoring/interoperability need: general gameplay, replacement real-time physics engine, broad syntax, creature/vehicle/flight/swimming/vegetation/fluid/deformable systems, model training, MCP transport, simultaneous backends, further terrain/buildings, appearance/textures, animation transitions, live-engine behavior, scale/performance expansion. Existing geometry/materials/textures/recordings retain named profiles/unresolved obligations.

Older ambitions: [pre-C210 goal](https://github.com/Omegapy/OntoKin/blob/94dee707c148b7a545e43d4de0d601642c5fa3e8/GOAL.md), [PRD](docs/product/OK-PRD-001-product-requirements.md), [capability definition](docs/product/OK-CAP-001-modeling-motion-and-object-structure.md). Unimplemented domains: deferred, not completed. Superseded for today's completion: requiring OntoKin itself to implement every historical world-engine domain.

## Staged roadmap and one current action

[STATUS](STATUS.md#current-workflow-and-next-action)/[CURRENT](docs/workflow/CURRENT.json) own current scope/exact component states/next action; stop after its verified saved handoff. C253 [protocol/corpus](docs/engineering/localized-repair-c253/README.md): binds three cases from one public keyed-rack family for evaluator qualification, not unseen comparison/general advantage. [C260](docs/engineering/localized-repair-c260/README.md) unchanged; historical input admission: separate queued interface. Unmet: complete semantics, site/world behavior, authentic revisions, invalid-edit atomicity, clean rebuilds, native routes, comparative trials.

Follow [C252 roadmap](docs/engineering/review-integration-c252/ROADMAP.md):

1. Freeze protocol/fixture bindings → qualify minimal runner → execute separately approved pilot.
2. From evidence, select one bounded receiving/OpenUSD mapping objective; assess OpenUSD-native authoring baseline; no OntoKin exporter implied.
3. Test control/traceability around an externally generated asset only if earlier evidence justifies it.
4. Publish narrowly supported claim or reduce scope to useful parts.

C210's second-target-first ordering superseded; cross-target claims still require receiver evidence. C221 R08 pending; localized-authoring preparation before more R07 source work. Retain R00–R02 completed scopes, R03–R07 unmet obligations, all nine recommendations/41 criteria. C210/[C219 Blender promise](docs/engineering/receiving-decision-c219/DECISION.md): finite existing evidence. STATUS retains strict-normal failure, C251 stale-authority failures, deferred native work, C233 historical input-specific aggregate pass. Older next-task text cannot override C252.

## Evidence before expansion

Comparative advantage: unproven. Test **same agent** versus matched direct tools for better localized-edit correctness, preservation of unrelated meaning, invalid-edit recovery, provenance retention. One repair/valid GLB/large test count cannot establish advantage.

Follow [C180](docs/engineering/semantic-physical-scope-c180/README.md)/C252: same supported task; compare direct Blender/Python; assess OpenUSD-native authoring. Pin model/settings, information, tools, outputs, comparable budgets. Trials: unseen variants, repetitions, failures in denominator; distinguish related assembly edits; separate reusable setup/maintenance from per-task cost; disclose backend/exporter differences before attributing language benefits.

Predeclare success, unintended-change rate, invalid-edit handling, identity/provenance correctness, transport loss, one primary efficiency measure. Suggested provisional investment thresholds: **20 percentage-point success gain or 30% effort reduction at non-inferior success**; not adopted standards/release criteria/results. Before trials choose endpoint, noninferiority margin, sample/repetition policy, uncertainty rule.

Broader investment requires demonstrated benefit or explicitly selected bounded experiment dependency. Mature comparison without useful advantage → documented scope reduction; consider semantic schema + provenance/validation toolkit. Inconclusive pilot establishes neither general success nor failure. Fund evidence-supported families/semantics. Physical claims require independent physical references; destination claims require actual destination observations.

## Invariants, budgets and completion

Preserve stable identities/revisions, units/frames, separate ownership/following/connections, one motion authority, represented mass, honest release/state transfer. Expose defaults/approximations/unsupported features/loss. Failed edits preserve accepted source/artifacts; failed evaluation cannot validate later state. [Adopted language rules](docs/language-design/OK-LANG-001-core-language-specification.md) govern until explicit versioned decision changes them.

Ordinary source execution ceilings: **100,000 operations and 30,000 ms**. Explicit larger requests require current host authority; animation duration separate. Unchanged: original fixture limits, cancellation, failure atomicity, other ceilings. [Budget decision](docs/engineering/source-execution-budgets-2026-10-29-c073/README.md).

[OK-ENG-009](docs/engineering/OK-ENG-009-development-integration-and-branch-lifecycle.md): reviewed experimental increments permitted without releasing whole features. Each finite release requires its named profile, predetermined positive/boundary/negative/composition/edit fixtures, source-to-artifact evidence, protocol failure/retry checks, applicable numerical/visual/compatibility roles under [OK-ENG-006](docs/engineering/OK-ENG-006-local-validation-and-hosted-ci-policy.md). New/worsened failures block integration; historical failed/unrun checks remain visible.

Product acceptance requires adopted semantic-authoring/checked-transport evidence + documented investment decision. Demonstrations/metadata/untested destinations/running solvers cannot establish acceptance. Releases below: exact scope; incomplete profiles remain incomplete. **Before changing/claiming an affected profile, read its full section in [preserved original GOAL](docs/engineering/startup-reading-20261118/before/GOAL.md.txt) and linked contracts/evidence.** Conditional reading retains all detailed requirements/revisions/counts/nonclaims.

## Completed release gate: OK-AGENT-001

0.3.0 passed finite `ontokin.agent/0.1` interface gate **A01–A10**: revision-safe discovery/editing/inspection/evaluation/cancellation/source-to-export repair workflows. [Evidence](docs/engineering/agent-validation/validation-summary.json) retains exact protocol/identity/budget/failure/retry/unchanged-sibling obligations.

## Completed release gate: pinned modules and keyed assembly construction

Experimental **0.4.0**, [OK-LANG-002](docs/language-design/OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md)/[OK-AGENT-002](docs/engineering/OK-AGENT-002-program-bundles-and-atomic-source-edits.md), passed **C01–C20**: pinned reusable definitions, bounded identifiable parts. Earlier `0.1`/`core-0.1` meaning intact. [Evidence](docs/engineering/construction-validation/validation-summary.json): finite construction, not whole-product completion.

## Completed release gate: native exterior surfaces and material regions

[OK-LANG-003 v0.2](docs/language-design/OK-LANG-003-parameterized-exterior-surfaces-and-material-regions.md), `0.3`/`surface-0.1`, passed **M01–M12**: bounded lofts, keyed sections, PBR regions, rigid visual placement, native Agent workflows. [Evidence](docs/engineering/surface-release-validation/README.md). Visual geometry adds no matter/motion authority. Unproved: deformation/locomotion/contacts/wind/general dynamics/live physics/authoring benefit.

## Completed release gate: explicit source impulses

[OK-LANG-004](docs/language-design/OK-LANG-004-source-impulses-and-free-sphere-dynamics.md), source/Agent/GLB **0.4**, passed **I01–I12**: instantaneous world-momentum impulses on free homogeneous spheres, ordered release events, atomic repair/rollback. [Evidence](docs/engineering/impulse-release-validation/README.md). Closed: instantaneous PHY-008 only. Open: continuous forces/torques, contacts, general dynamics, product completion.

## Completed release gate: finite center-of-mass force intervals

[OK-LANG-005](docs/language-design/OK-LANG-005-finite-center-of-mass-force-intervals.md), explicit Agent/GLB **0.5**, passed **F01–F12**: finite additive world forces at free homogeneous spheres' centers of mass; exact clocks/order/anchors, rollback, valid prefixes. [Evidence](docs/engineering/force-release-validation/README.md). Open: torque/contacts/general dynamics/deformables/live physics/authoring benefit/remaining product domains.

## Deferred incomplete release: reusable purposeful actions

[OK-LANG-006/0.1.0](docs/language-design/planar-reach-v0.1/ADOPTION.md): adopted; incomplete/deferred pending demonstrated authoring/interoperability need. Source `0.6`/`planar-reach-0.1`, Agent/GLB 0.6: retain unchanged 41-case corpus and all adopted supplements/source/protocol/numerical/destination/browser/compatibility/inherited obligations. [Integration](docs/language-design/planar-reach-v0.1/contract-review/integration18.json) proves contract preparation/adoption/checks, not runtime/authoring benefit/product completion. Frozen draft labels: historical; authority: separate adoption.

Before later exterior-model/mechanism/controller implementation/backend selection: select representative investment-priority task; predeclare limits/failures/evidence.
