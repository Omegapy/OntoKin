# OntoKin goal

Reaffirmed by the project owner on October 28, 2026, including authority to reconcile and integrate the repository while preserving this mission. This record preserves the goal across sessions and implementation milestones. [STATUS.md](STATUS.md) records current evidence and work; [AGENTS.md](AGENTS.md) defines the working procedure.

## Mission

Build OntoKin into a programming language designed primarily for AI agents to create, inspect, revise, and reuse meaningful 3D objects and their behavior. An agent should express form, parts, appearance, physical properties, connections, and intended actions in editable, human-readable `.ok` source. OntoKin should supply the supported construction, routine setup, evaluation, and delivery needed to turn that source into usable models and animations.

Game-engine delivery, including Unreal Engine and other suitable engines, remains a product target. Each claimed destination must have a named format/version and actual import and animation-playback evidence; a valid exported file alone does not establish support in a particular engine.

The language must offer actual programmable abstractions: types, classes, instances, functions, operations, composition, and progressively richer reusable libraries and algorithms. Its purpose includes independent local actions within coherent assemblies, understandable physical and mechanical behavior, and precise inspection and repair. Human direction and review remain possible through the same source and evidence. Ordinary execution must continue without a language-model call per frame.

Start with complete exterior models, characters, props, mechanisms, and short animations. Preserve their reuse in larger scenes, games, connected virtual worlds, and the longer-term planetary and universe-scale settings described in the founding vision. That growth requires explicit models, precision, detail, and resource limits; it does not promise exact simulation of every physical phenomenon. Detailed biological interiors are outside the current modeling focus.

The [capability definition](docs/product/OK-CAP-001-modeling-motion-and-object-structure.md) supplies this modeling emphasis. The [PRD](docs/product/OK-PRD-001-product-requirements.md) retains the broader product ambition. Their historical review statuses remain visible; adopted language rules and measured implementation claims have separate records.

## Development priority: flexible execution budgets

The owner's October 29, 2026 direction prioritizes developing the language's capabilities and enabling increasingly complex 3D objects, animations and simulations. Keep the ordinary execution defaults of 100,000 operations and 30,000 ms, while adding an explicit language feature through which an entry program requests higher limits within resource ceilings authorized by its execution environment. Examples include 200,000 or 400,000 operations and 60, 75 or 80 seconds of computation time. Modeled animation duration remains a separate source value.

[C072](docs/engineering/language-execution-budgets-2026-10-29-c072/README.md) records the source evaluation and [OK-LANG-007 proposal](docs/language-design/OK-LANG-007-configurable-execution-budgets.md). [C073](docs/engineering/source-execution-budgets-2026-10-29-c073/README.md) implements the explicit source/CLI-to-GLB path under its [experimental adoption](docs/language-design/execution-budgets-v0.1/ADOPTION-C073.md), with actual verification and integration recorded separately. The [next increment](docs/engineering/source-execution-budgets-2026-10-29-c073/NEXT-TASK.md) is the separately versioned Agent/0.7 lifecycle. Keep that interface unavailable until its actual discovery, edit rollback, authorization, evaluation, export, cancellation and retry cases pass.

Original tests, fixtures and acceptance gates retain their current limits. New demanding workloads use separately identified, explicitly authorized higher-budget settings; their results cannot retroactively pass an old fixed-budget gate. Preserve bounded work, cancellation, failure atomicity, independent validation and all unrelated resource caps. Efficiency improvements remain part of development, but extensive optimization investigations must not become a prerequisite for extending the language.

## Preserve the full product scope

PRD section 9.2 identifies the following required areas. A limited release may defer them, but they remain part of the goal.

| Area | Required direction |
| --- | --- |
| Language and agent workflow | Reusable typed programs; discovery, scoped editing, inspection, repair, preview, and export. |
| Modular rigid assets | Composite geometry, physical materials, forces, contacts, and reusable parts. |
| Machines and vehicles | Joints, coupled and closed mechanisms, wheels, suspension, steering, propulsion, and braking. |
| Creature bodies | Custom body plans, unusual limbs, reusable parts, articulation, skin binding, and physical properties. |
| Purposeful creature movement | Supplied supported locomotion and manipulation, with declared body/load ranges and measurable outcomes. |
| Flight and swimming | Meaningful wings/fins, surrounding-medium forces, and compatible supported control. |
| Vegetation | Branches, foliage, anchoring, wind, and flexible response. |
| Terrain and structures | Parameterized landscapes, rocks, modular buildings, appearance, and interaction surfaces. |
| Liquids and deformable solids | Flow, containment, buoyancy/drag, supported solid interaction, and visible deformation. |
| Appearance | Regional materials, patterns, textures, mapping, and deformation-aware surfaces. |
| Animation and delivery | Reusable clips, timing, transitions, recorded/live distinctions, independent target validation, and live game behavior. |

Support profiles define finite promises within this scope. They must not redefine the whole project as a moving sphere, a mesh exporter, or a collection of prepared demonstrations.

## Invariants and completion gates

Preserve stable identities and source revisions; distinguish ownership, frames, following, physical connections, and visual bindings. Resolve one motion authority per coordinate and count represented matter once. Keep defaults, assumptions, approximations, unsupported requests, and information loss inspectable. A failed edit preserves the accepted revision; a failed evaluation cannot label later state valid. The adopted [language baseline](docs/language-design/OK-LANG-001-core-language-specification.md) governs these meanings until an explicit versioned change replaces it.

Reviewed development increments can be integrated into main under [OK-ENG-009](docs/engineering/OK-ENG-009-development-integration-and-branch-lifecycle.md) before the complete feature release. Explicitly selected incomplete capabilities remain experimental; existing meanings and defaults are preserved.

A release is complete only for its named scope when:

1. Its supported features, ranges, dependencies, output contracts, and unmet requirements are published by requirement/profile identity.
2. Versioned positive, boundary, negative, composition, and targeted-edit fixtures pass predetermined acceptance limits. Changed limits are recorded as requirement changes.
3. Actual source, geometry, physical state, action outcomes, and destination output establish the claims made. Metadata, a running solver, or a convincing image alone is insufficient.
4. Agents complete the promised workflow through documented operations, with source/revision integrity, useful diagnostics, bounded work, and no hidden manual preparation.
5. Relevant tests, numerical and visual checks, and the required integration-validation roles pass for the identified implementation under the [current validation policy](docs/engineering/OK-ENG-006-local-validation-and-hosted-ci-policy.md). Evidence, execution environments, and known limits remain reviewable in GitHub. Historical release evidence retains its original meaning; future complete release audits need a versioned local-evidence contract before accepting a different execution provider.

Full-product acceptance additionally requires evidence across **every area above** and the adopted full-product requirements. Proposed PRD numerical gates must be calibrated into versioned fixtures before use. The language's claimed authoring benefit must be evaluated against a documented direct-tool baseline, including unseen variants, repair effort, cost, quality, and reusable versus task-specific preparation. Do not invent a percentage improvement.

Completing a finite milestone does not complete the whole project. Deferred domains remain visible in STATUS. The longer-term world ambition remains an ongoing direction beyond any finite release's tested scale.

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

## Continuing capability work: reusable purposeful actions

Continue implementing and validating the adopted [OK-LANG-006/0.1.0 contract](docs/language-design/planar-reach-v0.1/ADOPTION.md) alongside the execution-budget priority above. [PR #19](https://github.com/Omegapy/OntoKin/pull/19) integrated its separate adoption and exact reviewed inputs as main merge `349ac15ce92502673aff05ecd2c7aabc4912d17b`. The original 41-case source/expected corpus remains unchanged; the adopted supplements define both-moving lifecycle, bounded numerical admission, simultaneous claims, complete Agent projections, failed-prefix recovery, scoped repair and bounded recorded delivery. Draft labels in frozen preparation files retain their historical identities; the separate adoption record establishes current authority.

The finite runtime and release gate remain open. Source `0.6` / `planar-reach-0.1`, explicit Agent/0.6 and recorded GLB/0.6 must satisfy all adopted source, protocol, numerical, destination, browser, compatibility and inherited obligations. The [integration record](docs/language-design/planar-reach-v0.1/contract-review/integration18.json) reports only contract preparation, adoption and resulting-main checks; it does not establish runtime support, an authoring improvement or full-product completion.

Subsequent finite milestones must address richer exterior modeling, physical interactions and mechanisms, supplied controllers, and the remaining domain/delivery capabilities. Each must name representative tasks, limits, expected failures, and evidence before implementation. Production compiler, physics-engine, and editor choices follow relevant requirements and experiments; the present prototype does not settle them permanently.
