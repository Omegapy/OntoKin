# OntoKin goal

The owner adopted semantic authoring on **November 11, 2026**. The [November 16 C252 decision](docs/engineering/review-integration-c252/DECISION.md) retains the [C210 boundary](docs/engineering/semantic-export-c210/DECISION.md) while moving comparative evidence ahead of receiver expansion. [STATUS](STATUS.md) owns actual results/next gates; [AGENTS](AGENTS.md) governs coordination and preservation.

## Mission

Build an AI-native semantic language and intermediate representation for constructing, inspecting, validating, repairing and transporting physically meaningful 3D objects. Preserve named parts, relationships, dimensions/units, physical declarations, constraints and source identity; reuse existing normalized records between accepted source and destinations.

Accepted `.ok` remains authoritative. Preserve language/classes/libraries, stable identities, pinned dependencies, provenance, bounded evaluation, revision-safe editing, geometry, materials and validated exports. Agents must inspect named parts, edit supported parameters, reject invalid candidates without losing accepted designs, and regenerate checked artifacts. Ordinary playback needs no model call per frame.

Engines/specialist tools own rendering, general simulation and gameplay. OntoKin supplies object meaning and checked mappings; destinations own runtime behavior. Keep engine neutrality and GLB/Blender capabilities. Unreal Scene Graph/Verse are intended targets, with conceptual versus implemented support distinguished in the [interoperability boundary](docs/engineering/semantic-export-c210/UNREAL-INTEROP.md).

## Current priorities and non-goals

| Capability | Required meaning |
| --- | --- |
| Semantic assemblies | Stable object/part identities, reusable definitions, distinct occurrence provenance. |
| Dimensions, units, frames | Explicit quantities/placement; supported constraints checked against source and delivered geometry. |
| Relationships/physical declarations | Separate ownership, placement, following, connection and motion authority; count matter once. |
| Localized repair | Atomic failure preserves accepted revision; success preserves unrelated parts. |
| Checked transport | Exact source/dependency/artifact references, machine-readable preservation/loss, measured destination evidence. |

Finite physics remains useful for reference checks. General gameplay, a replacement real-time physics engine, broad syntax, creature/vehicle/flight/swimming/vegetation/fluid/deformable systems, model training, MCP transport, simultaneous backends, further terrain/buildings, appearance/textures, animation transitions, live-engine behavior and scale/performance expansion are deferred unless a demonstrated authoring/interoperability need selects them. Existing geometry, materials, textures and recordings retain named profiles and unresolved obligations.

The [pre-C210 goal](https://github.com/Omegapy/OntoKin/blob/94dee707c148b7a545e43d4de0d601642c5fa3e8/GOAL.md), [PRD](docs/product/OK-PRD-001-product-requirements.md) and [capability definition](docs/product/OK-CAP-001-modeling-motion-and-object-structure.md) retain older ambitions. Unimplemented domains are deferred, not completed; requiring OntoKin itself to implement every historical world-engine domain is superseded as today's completion criterion.

## Staged roadmap and one current action

[STATUS](STATUS.md#current-workflow-and-next-action) and [CURRENT](docs/workflow/CURRENT.json) own current scope, exact component states and next action. Stop after its verified saved handoff. C253's [protocol/corpus](docs/engineering/localized-repair-c253/README.md) binds three cases from one public keyed-rack family for evaluator qualification, not unseen comparison or general advantage. [C260](docs/engineering/localized-repair-c260/README.md) remains unchanged; historical input admission is a separate queued interface. Complete semantics, site/world behavior, authentic revisions, invalid-edit atomicity, clean rebuilds, native routes and comparative trials remain unmet.

Follow the [C252 roadmap](docs/engineering/review-integration-c252/ROADMAP.md):

1. Freeze protocol/fixture bindings, qualify a minimal runner, then execute a separately approved pilot.
2. Use evidence to select one bounded receiving/OpenUSD mapping objective. Assess OpenUSD-native authoring as a baseline; no OntoKin exporter is implied.
3. Test control/traceability around an externally generated asset only when earlier evidence justifies it.
4. Publish a narrowly supported claim or reduce scope to useful parts.

This supersedes C210's second-target-first ordering, not receiver evidence for cross-target claims. C221 R08 remains pending; localized-authoring preparation precedes more R07 source work. R00–R02 keep completed scopes; R03–R07 keep unmet obligations. Preserve all nine recommendations and 41 criteria. C210 and the [C219 Blender promise](docs/engineering/receiving-decision-c219/DECISION.md) remain finite existing evidence. STATUS retains strict-normal failure, C251 stale-authority failures, deferred native work and C233's historical, input-specific aggregate pass. Older next-task text cannot override C252.

## Evidence before expansion

Comparative advantage remains unproven. Test whether the **same agent** makes correct localized edits, preserves unrelated meaning, recovers from invalid edits and retains provenance better than matched direct tools. One repair, valid GLB or large test count cannot establish this.

Follow [C180](docs/engineering/semantic-physical-scope-c180/README.md) and C252: compare direct Blender/Python and assess OpenUSD-native authoring on the same supported task. Pin model/settings, information, tools, outputs and comparable budgets. Use unseen variants, repeated trials and failures in the denominator; distinguish related assembly edits, separate reusable setup/maintenance from per-task cost, and disclose backend/exporter differences before attributing benefits to the language.

Predeclare success, unintended-change rate, invalid-edit handling, identity/provenance correctness, transport loss and one primary efficiency measure. Suggested **20 percentage-point success gain or 30% effort reduction at non-inferior success** are provisional investment thresholds, not adopted standards, release criteria or results. Choose endpoint, noninferiority margin, sample/repetition policy and uncertainty rule before trials.

Broader investment needs demonstrated benefit or an explicitly selected bounded experiment dependency. A mature comparison without useful advantage requires documented scope reduction, considering a semantic schema plus provenance/validation toolkit. An inconclusive pilot proves neither general success nor failure. Fund evidence-supported families/semantics. Physical claims need independent physical references; destination claims need actual destination observations.

## Invariants, budgets and completion

Preserve stable identities/revisions, units/frames, separate ownership/following/connections, one motion authority, represented mass and honest release/state transfer. Expose defaults, approximations, unsupported features and loss. Failed edits preserve accepted source/artifacts; failed evaluation cannot validate later state. [Adopted language rules](docs/language-design/OK-LANG-001-core-language-specification.md) govern until an explicit versioned decision changes them.

Ordinary source execution stays bounded at **100,000 operations and 30,000 ms**. Explicit larger requests require current host authority; animation duration is separate. Original fixture limits, cancellation, failure atomicity and other ceilings remain unchanged. [Budget decision](docs/engineering/source-execution-budgets-2026-10-29-c073/README.md).

[OK-ENG-009](docs/engineering/OK-ENG-009-development-integration-and-branch-lifecycle.md) permits reviewed experimental increments without releasing whole features. Each finite release still needs its named profile, predetermined positive/boundary/negative/composition/edit fixtures, source-to-artifact evidence, protocol failure/retry checks and applicable numerical/visual/compatibility roles under [OK-ENG-006](docs/engineering/OK-ENG-006-local-validation-and-hosted-ci-policy.md). New/worsened failures block integration; historical failed/unrun checks remain visible.

Product acceptance needs adopted semantic-authoring/checked-transport evidence and a documented investment decision. Demonstrations, metadata, untested destinations or running solvers cannot establish it. The releases below retain exact scope; incomplete profiles remain incomplete. **Before changing or claiming an affected profile, read its full section in the [preserved original GOAL](docs/engineering/startup-reading-20261118/before/GOAL.md.txt) and its linked contracts/evidence.** That conditional reading retains all detailed requirements, revisions, counts and nonclaims.

## Completed release gate: OK-AGENT-001

The 0.3.0 release passed the finite `ontokin.agent/0.1` interface gate **A01–A10**, covering revision-safe discovery, editing, inspection, evaluation, cancellation and source-to-export repair workflows. [Evidence](docs/engineering/agent-validation/validation-summary.json) retains exact protocol, identity, budget, failure/retry and unchanged-sibling obligations.

## Completed release gate: pinned modules and keyed assembly construction

Experimental **0.4.0**, [OK-LANG-002](docs/language-design/OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md)/[OK-AGENT-002](docs/engineering/OK-AGENT-002-program-bundles-and-atomic-source-edits.md), passed **C01–C20** for pinned reusable definitions and bounded identifiable parts. Earlier `0.1`/`core-0.1` meaning remains intact. [Evidence](docs/engineering/construction-validation/validation-summary.json) establishes finite construction, not whole-product completion.

## Completed release gate: native exterior surfaces and material regions

[OK-LANG-003 v0.2](docs/language-design/OK-LANG-003-parameterized-exterior-surfaces-and-material-regions.md), `0.3`/`surface-0.1`, passed **M01–M12** for bounded lofts, keyed sections, PBR regions and rigid visual placement, with native Agent workflows. [Evidence](docs/engineering/surface-release-validation/README.md). Visual geometry adds no matter/motion authority; deformation, locomotion, contacts, wind, general dynamics, live physics and authoring benefit remain unproved.

## Completed release gate: explicit source impulses

[OK-LANG-004](docs/language-design/OK-LANG-004-source-impulses-and-free-sphere-dynamics.md), source/Agent/GLB **0.4**, passed **I01–I12** for instantaneous world-momentum impulses on free homogeneous spheres, ordered release events and atomic repair/rollback. [Evidence](docs/engineering/impulse-release-validation/README.md). Only instantaneous PHY-008 is closed; continuous forces/torques, contacts, general dynamics and product completion are not.

## Completed release gate: finite center-of-mass force intervals

[OK-LANG-005](docs/language-design/OK-LANG-005-finite-center-of-mass-force-intervals.md), explicit Agent/GLB **0.5**, passed **F01–F12** for finite additive world forces at free homogeneous spheres' centers of mass, exact clocks/order/anchors, rollback and valid prefixes. [Evidence](docs/engineering/force-release-validation/README.md). Torque, contacts, general dynamics, deformables, live physics, authoring benefit and remaining product domains remain open.

## Deferred incomplete release: reusable purposeful actions

[OK-LANG-006/0.1.0](docs/language-design/planar-reach-v0.1/ADOPTION.md) remains adopted but incomplete/deferred pending demonstrated authoring/interoperability need. Source `0.6`/`planar-reach-0.1`, Agent/GLB 0.6 retain the unchanged 41-case corpus and all adopted supplements/source/protocol/numerical/destination/browser/compatibility/inherited obligations. [Integration](docs/language-design/planar-reach-v0.1/contract-review/integration18.json) proves contract preparation/adoption/checks, not runtime, authoring benefit or product completion. Frozen draft labels remain historical; separate adoption supplies authority.

Later exterior-model/mechanism/controller work must select a representative investment-priority task and predeclare limits, failures and evidence before implementation/backend selection.
