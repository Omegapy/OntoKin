# OntoKin goal

Reaffirmed by the project owner on October 18, 2026. This record preserves the goal across sessions and implementation milestones. [STATUS.md](STATUS.md) records current evidence and work; [AGENTS.md](AGENTS.md) defines the working procedure.

## Mission

Build OntoKin into a programming language designed primarily for AI agents to create, inspect, revise, and reuse meaningful 3D objects and their behavior. An agent should express form, parts, appearance, physical properties, connections, and intended actions in editable, human-readable `.ok` source. OntoKin should supply the supported construction, routine setup, evaluation, and delivery needed to turn that source into usable models and animations.

The language must offer actual programmable abstractions: types, classes, instances, functions, operations, composition, and progressively richer reusable libraries and algorithms. Its purpose includes independent local actions within coherent assemblies, understandable physical and mechanical behavior, and precise inspection and repair. Human direction and review remain possible through the same source and evidence. Ordinary execution must continue without a language-model call per frame.

Start with complete exterior models, characters, props, mechanisms, and short animations. Preserve their reuse in larger scenes, games, connected virtual worlds, and the longer-term planetary and universe-scale settings described in the founding vision. That growth requires explicit models, precision, detail, and resource limits; it does not promise exact simulation of every physical phenomenon. Detailed biological interiors are outside the current modeling focus.

The [capability definition](docs/product/OK-CAP-001-modeling-motion-and-object-structure.md) supplies this modeling emphasis. The [PRD](docs/product/OK-PRD-001-product-requirements.md) retains the broader product ambition. Their historical review statuses remain visible; adopted language rules and measured implementation claims have separate records.

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

## Next development direction: finite physical influences

Specify, freeze and adopt a separately versioned finite center-of-mass force-interval contract before implementation. The next scope is a constant world force acting on an actually free homogeneous sphere over explicit activation and completion times, with additive overlaps, inherited gravity and impulse/release behavior, complete source identities, atomic failure handling, bounded agent inspection and physical-parameter repair, and independently validated recorded delivery. Positive, boundary, negative, composition and targeted-repair fixtures must fix the expected numerical and temporal behavior in advance. Exact endpoints, unchanged trajectory anchors for unchanged canonical acceleration, and validity of requested short prefixes need explicit rules. Existing profiles retain their meanings; this direction is not a claim that force intervals are already implemented.

Subsequent finite milestones must address richer exterior modeling, physical interactions and mechanisms, supplied controllers, and the remaining domain/delivery capabilities. Each must name representative tasks, limits, expected failures, and evidence before implementation. Production compiler, physics-engine, and editor choices follow relevant requirements and experiments; the present prototype does not settle them permanently.
