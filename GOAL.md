# OntoKin goal

The owner adopted this revised direction on **November 11, 2026**. The [C210 scope decision](docs/engineering/semantic-export-c210/DECISION.md) records what remains current, what is deferred and which earlier priorities are superseded. [STATUS.md](STATUS.md) records actual results and the next unmet gate; [AGENTS.md](AGENTS.md) governs coordination and preservation.

## Mission

Build OntoKin as an AI-native semantic language and intermediate representation for constructing, inspecting, validating, repairing and transporting physically meaningful 3D objects. Semantic means preserving the meaning of named parts, their relationships, dimensions and units, declared physical properties, constraints and source identity. The intermediate representation is the structured description between accepted source and destination tools; OntoKin already has normalized records to reuse.

Accepted `.ok` source remains authoritative. Preserve the existing language, reusable classes and libraries, stable identities, pinned source dependencies, provenance, bounded evaluation, revision-safe agent editing, geometry, materials and validated export capabilities. An agent must be able to inspect a named part, change one supported parameter, reject an invalid candidate without losing the accepted design, and regenerate a checked artifact. Ordinary playback needs no model call per frame.

Engines and specialist tools provide rendering, general simulation and gameplay. Unreal Scene Graph and Verse are intended integration targets: OntoKin supplies object meaning and checked mappings; the destination owns runtime behavior. Preserve engine neutrality and existing GLB/Blender work. The [Unreal interoperability boundary](docs/engineering/semantic-export-c210/UNREAL-INTEROP.md) distinguishes conceptual mappings from implemented support.

## Current priorities and non-goals

| Current capability | Required meaning |
| --- | --- |
| Semantic assemblies | Stable object and part identities, reusable definitions and distinct occurrence provenance. |
| Dimensions, units and frames | Explicit quantities and placement, with supported constraints checked against source and delivered geometry. |
| Relationships and physical declarations | Ownership, transform placement, following, physical connection and motion authority stay distinct; declared matter is counted once. |
| Localized repair | Atomic edits preserve the accepted revision on failure and preserve unrelated parts on success. |
| Checked transport | Exact source/dependency/artifact references, machine-readable preservation or loss, and measured evidence for each claimed destination. |

Existing finite physics remains useful for reference checks. General gameplay programming, a replacement real-time physics engine, broad new syntax, new creature/vehicle/fluid systems, model training, MCP transport and simultaneous new backends are deferred. Later work must address a demonstrated authoring or interoperability need. Existing supported profiles and all their unresolved release obligations keep their meaning.

The older world-building ambition is preserved in the [pre-C210 goal](https://github.com/Omegapy/OntoKin/blob/94dee707c148b7a545e43d4de0d601642c5fa3e8/GOAL.md), [PRD](docs/product/OK-PRD-001-product-requirements.md) and [capability definition](docs/product/OK-CAP-001-modeling-motion-and-object-structure.md). Their unimplemented creature movement, vehicles, flight/swimming, vegetation, fluids/deformables, gameplay and world-scale domains are deferred, not completed. Further terrain/building systems, appearance/texture extensions, animation transitions, live-engine behavior and scale/performance expansion are also deferred unless a demonstrated authoring or interoperability need selects them. Existing implemented geometry, materials, textures and recordings retain their named profiles. Requiring every historical domain as OntoKin's own engine is superseded as a current product completion criterion by the semantic-authoring boundary above.

## Staged roadmap and one current action

1. Complete one experimental engine-neutral semantic export and constrained edit on an existing object, using the existing representation and GLB path. [C210 contract and proof](docs/engineering/semantic-export-c210/README.md)
2. Select one actual receiving application and exact version, then execute and verify a small import with explicit loss reporting.
3. Prove a second target and trace received parts back to the same authoritative source.
4. Compare with matched direct authoring on unseen variants before broad language or backend investment.

This is an order of work, not a schedule commitment. The former goal deferred a general importer, capture pipeline or new production backend until the comparison justified its expense. That investment restriction is clarified and revised to permit the small interoperability experiments in stages 1–3 before the comparison. General importers, capture pipelines, production backends and broad investment still require demonstrated need and measured benefit. C209's CPU-only job/0.2 retained-result compatibility and C201 native admission are deferred; neither is needed by the selected Agent/0.2 and GLB/0.2 proof. Frozen C201 instructions and closed C199/C200 schedules remain unchanged.

The C210 finite semantic proof passed its affected and independent checks; its broad regression attempt remains failed. [C211's one-build receiving attempt](docs/engineering/semantic-receiving-c211/RESULTS.md) is failed/partial: actual geometry positions, poses, materials and native object metadata passed, while sphere split normals exceeded the unchanged precision limit and rendering failed. The prototype is held, with no product merge. [C212](docs/engineering/normal-fidelity-c212/DECISION.md) retains the strict contract and rejects an unsupported tolerance increase. [C213](docs/engineering/normal-codec-c213/RESULTS.md) completes the CPU-only characterization and establishes finite explicit-frame counterexamples without a new tolerance or native replay. The next action is one [CPU-only source-normal payload and explicit loss-report prototype](docs/engineering/normal-codec-c213/NEXT-TASK.md), with a separately versioned proposed contract that distinguishes exact source authority from approximate native shading observations. Any revised receiving promise or native attempt still requires separate review. Preserve C211's original failure, tolerance and unrun save/reopen/visual gates. The second destination and direct-authoring comparison remain later stages.

## Evidence before expansion

The research question remains whether OntoKin helps an agent make correct localized edits, preserve unrelated meaning and reuse the result more effectively than direct tools. One successful repair or a valid GLB cannot establish that advantage. Preserve the [C180 comparison principles](docs/engineering/semantic-physical-scope-c180/README.md) and all earlier trial results as historical evidence; do not reopen a closed schedule.

A later study must use matched direct-tool baselines and unseen variants, comparable model snapshots/settings, inspection tools, task information, execution resources and output requirements. Declare measures before execution: edit correctness, unaffected-part preservation, failure recovery, reproducibility, elapsed time/tokens and cross-target reuse. Separate reusable preparation from task cost, keep failures in the denominator and compare cost at matched success levels. A claim of physical behavior needs an independent physical reference; a destination claim needs execution in that destination.

Broader language investment depends on demonstrated benefit. If direct tooling produces comparable results, document a scope reassessment, including whether a semantic schema and validation toolkit is sufficient. A narrow result should fund only the task families and semantics that earned their cost. No percentage improvement is assumed.

## Invariants, budgets and completion

Stable identities and source revisions, declared units/frames, separate ownership/following/connections, one motion authority, represented mass and honest release/state transfer remain mandatory. Keep defaults, approximations, unsupported features and information loss inspectable. A failed edit preserves accepted source and artifacts; a failed evaluation cannot label later state valid. The adopted [language baseline](docs/language-design/OK-LANG-001-core-language-specification.md) governs meaning until an explicit versioned semantic decision changes it.

Ordinary source execution remains bounded by **100,000 operations and 30,000 ms**. Existing explicitly requested larger budgets need current host authority; modeled animation duration is separate. Original fixture limits, cancellation, failure atomicity and unrelated resource ceilings remain unchanged. [Execution-budget decision](docs/engineering/source-execution-budgets-2026-10-29-c073/README.md)

Reviewed experimental increments may integrate under [OK-ENG-009](docs/engineering/OK-ENG-009-development-integration-and-branch-lifecycle.md). Integration does not close a full feature release. Each finite release still needs its named supported profile, predetermined positive/boundary/negative/composition/edit fixtures, actual source-to-artifact evidence, protocol failure/retry checks and applicable numerical, visual and compatibility roles under the [local validation policy](docs/engineering/OK-ENG-006-local-validation-and-hosted-ci-policy.md). Newly introduced or worsened failures block integration; historical failed or unrun checks remain visible.

Product acceptance requires evidence for the semantic-authoring and checked-transport claims actually adopted, plus a documented investment decision. It cannot be inferred from a finite demonstration, metadata preservation, an untested destination or a running solver. Earlier releases below retain their exact scope and historical evidence; incomplete profiles remain incomplete.

## Completed release gate: OK-AGENT-001

The working **AI Agent Authoring and Inspection Interface** passed its finite release gate in 0.3.0. [Identified local and CI evidence](docs/engineering/agent-validation/validation-summary.json) records these satisfied acceptance requirements:

- Publish the concrete `ontokin.agent/0.1` operation/result contract and executable interface for discovery, create/edit, validation, bounded inspection, evaluation/reset, status, and cancellation.
- Demonstrate all **A01–A10** in the [language contract](docs/language-design/OK-LANG-001-core-language-specification.md#134-agent-operation-cases), including stale revisions, atomic patches, idempotent retries, changed-payload rejection, cursor consistency, cancellation after acceptance, unknown-outcome reconciliation, and correct velocity meaning.
- Preserve immutable candidate/accepted revisions, UTF-8 patch preconditions, run context, requested output levels, result limits, and explicit budget failures. Never substitute lower-level success.
- Connect source, numerical inspection, GLB output, and visual evidence by matching revision/artifact identities. Any destination operation must name its actual contract.
- Run a documented agent-style create → inspect → diagnose → repair → evaluate → export cycle, including an invalid candidate, a scoped instance edit, and an unchanged sibling. Preserve the existing source/export regression gates and publish actual results.

## Completed release gate: pinned modules and keyed assembly construction

The experimental **0.4.0** release implements reusable pinned component definitions and bounded declarative generation of independently identifiable parts. It preserves the meaning and conformance of existing `ontokin "0.1"` / `core-0.1` source. [OK-LANG-002](docs/language-design/OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md) fixes the grammar, source-bundle identities, dependency limits, patch authority and predetermined C01–C20 requirements; [OK-AGENT-002](docs/engineering/OK-AGENT-002-program-bundles-and-atomic-source-edits.md) binds the separate program service.

The [identified local and CI evidence](docs/engineering/construction-validation/validation-summary.json) establishes actual imported libraries, variable keyed part counts and dimensions, stable identities under insertion/reordering, targeted generated-instance repair with unchanged siblings/library bytes, and independently validated animation. All 276 tests, original source/agent cases, C01–C20, and the four remote CI jobs passed. Exact source files remain authoritative; accepted programs, runs, inspections and artifacts identify the complete pinned dependency closure. This finite construction release does not complete the full language or product.

## Completed release gate: native exterior surfaces and material regions

The adopted [OK-LANG-003 v0.2 contract](docs/language-design/OK-LANG-003-parameterized-exterior-surfaces-and-material-regions.md) is implemented for language `0.3` / `surface-0.1`: a bounded loft family with stable keyed sections, explicit geometric ordering, actual PBR material regions and rigid local visual placement. [OK-AGENT-003](docs/engineering/OK-AGENT-003-native-surface-program-workflows.md) supplies native source discovery, atomic scoped edits, bounded revision-bound mesh inspection, evaluation and GLB/0.3 retrieval. Earlier language, agent and export bindings retain their meanings.

The [identified release evidence](docs/engineering/surface-release-validation/README.md) closes **M01–M12** on implementation `80d59bb2b09a5a57cad8e1b477d89f23a3e5a5a1`: 22 actual source-built GLBs, 492 agent exchanges, repaired and composed programs using the unchanged pinned library, predetermined held-outs, independent geometry/PBR/motion checks, and 12 reviewed browser captures. All 464 regression tests, 43 original source cases / 694 assertions, A01–A10, fresh C01–C20 and four identified GitHub CI jobs passed. [OK-ENG-004](docs/engineering/OK-ENG-004-native-surface-release-conformance.md) defines the executable acceptance and evidence audit. STATUS records integration revisions and subsequent checks separately.

This finite gate demonstrates native source-to-export capability, including independently identifiable material regions and source-driven rigid animation. Visual geometry adds no physical matter or motion authority. It does not establish skin deformation, purposeful locomotion, contacts, wind response, general dynamics, live destination physics or a measured authoring benefit; those requirements remain open.

## Completed release gate: explicit source impulses

The adopted [OK-LANG-004 contract](docs/language-design/OK-LANG-004-source-impulses-and-free-sphere-dynamics.md) is implemented for source `0.4` / `impulse-0.1`, explicit Agent/0.4 and recorded GLB/0.4. A program can apply world momentum at a target-self point on a free homogeneous sphere, inspect its linear and angular response, compose ordered release/impulse events, and repair physical parameters through atomic source edits. Whole-boundary rollback, bounded inspection and conservative high-spin recording preserve earlier profile meanings.

[The durable evidence](docs/engineering/impulse-release-validation/README.md) closes **I01–I12** on implementation `da0eb32c789a6f631a0d39eb219cbb3a912c9dfa`: 40 frozen source cases, 124 mapped methods, both 588-test regression inventories, current core/Agent/C01–C20/M01–M12 gates, nine source-built impulse GLBs, 192 fixed and 7,628 dense destination poses, and reviewed browser captures. [The integration record](docs/engineering/impulse-release-validation/integration.json) identifies PR #11, actual main merge `d25ab70a08fe5fb1e9f9a5be7a71fe6cbc99225e`, all four passing resulting-main jobs and matching implementation inputs. This closes only the instantaneous impulse portion of PHY-008, not continuous forces, torques, contacts, general dynamics or the whole product.

## Completed release gate: finite center-of-mass force intervals

The adopted [OK-LANG-005 contract](docs/language-design/OK-LANG-005-finite-center-of-mass-force-intervals.md), explicit Agent/0.5 and recorded GLB/0.5 passed the finite **F01–F12** gate. Supported free homogeneous spheres respond to additive finite world forces at their centers of mass, with exact activation/completion clocks, unchanged-acceleration anchors, gravity/impulse/release ordering, whole-boundary rollback and valid requested prefixes. Agents inspect complete source histories, repair physical parameters and retrieve the exact recorded artifacts through the documented interface.

The [durable release evidence](docs/engineering/force-release-validation/README.md) identifies implementation `c7db6520e172b2b38591969a4bdf75f97a993dbb`: 56 adopted source cases, 242 mapped methods, all 878 tests on each of CPython 3.11/3.12/3.13, actual source and Agent workflows, 23 source GLBs, seven retrieved GLBs, independent geometry/PBR and fixed/dense motion checks, all 83 reviewed browser captures, and all mandatory inherited roles. The separately versioned [OK-ENG-008 audit](docs/engineering/OK-ENG-008-force-release-conformance.md) passed every gate without relabeling historical provider evidence. [The integration record](docs/engineering/force-release-validation/integration.json) binds PR #17, main merge `e74dd14bd90bfd0ef7b11d9a939292bb9e5dda4c`, unchanged eligible inputs and fresh resulting-main checks.

This closes the adopted finite center-of-mass force scope. Continuous torque, contacts, general rigid dynamics, deformable matter, live destination physics and all remaining product domains still need their own evidence. No measured authoring benefit or full-product completion is inferred from this release.

## Deferred incomplete release: reusable purposeful actions

Preserve the adopted [OK-LANG-006/0.1.0 contract](docs/language-design/planar-reach-v0.1/ADOPTION.md) as an incomplete reference profile; further work is deferred until a demonstrated semantic-authoring or interoperability need selects it. [PR #19](https://github.com/Omegapy/OntoKin/pull/19) integrated its separate adoption and exact reviewed inputs as main merge `349ac15ce92502673aff05ecd2c7aabc4912d17b`. The original 41-case source/expected corpus remains unchanged; the adopted supplements define both-moving lifecycle, bounded numerical admission, simultaneous claims, complete Agent projections, failed-prefix recovery, scoped repair and bounded recorded delivery. Draft labels in frozen preparation files retain their historical identities; the separate adoption record establishes current authority.

The finite runtime and release gate remain open. Source `0.6` / `planar-reach-0.1`, explicit Agent/0.6 and recorded GLB/0.6 must satisfy all adopted source, protocol, numerical, destination, browser, compatibility and inherited obligations. The [integration record](docs/language-design/planar-reach-v0.1/contract-review/integration18.json) reports only contract preparation, adoption and resulting-main checks; it does not establish runtime support, an authoring improvement or full-product completion.

For any later work on exterior models, mechanisms or controllers, select a representative task from the investment priorities above. Specify limits, expected failures and evidence before selecting an implementation or backend.
