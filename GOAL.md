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
5. Relevant tests, numerical/visual checks, and CI pass for the identified implementation; evidence and known limits remain reviewable in GitHub.

Full-product acceptance additionally requires evidence across **every area above** and the adopted full-product requirements. Proposed PRD numerical gates must be calibrated into versioned fixtures before use. The language's claimed authoring benefit must be evaluated against a documented direct-tool baseline, including unseen variants, repair effort, cost, quality, and reusable versus task-specific preparation. Do not invent a percentage improvement.

Completing a finite milestone does not complete the whole project. Deferred domains remain visible in STATUS. The longer-term world ambition remains an ongoing direction beyond any finite release's tested scale.

## Next release gate: OK-AGENT-001

Provide a working **AI Agent Authoring and Inspection Interface** over the existing language and visual exporter. Its acceptance gate is:

- Publish the concrete `ontokin.agent/0.1` operation/result contract and executable interface for discovery, create/edit, validation, bounded inspection, evaluation/reset, status, and cancellation.
- Demonstrate all **A01–A10** in the [language contract](docs/language-design/OK-LANG-001-core-language-specification.md#134-agent-operation-cases), including stale revisions, atomic patches, idempotent retries, changed-payload rejection, cursor consistency, cancellation after acceptance, unknown-outcome reconciliation, and correct velocity meaning.
- Preserve immutable candidate/accepted revisions, UTF-8 patch preconditions, run context, requested output levels, result limits, and explicit budget failures. Never substitute lower-level success.
- Connect source, numerical inspection, GLB output, and visual evidence by matching revision/artifact identities. Any destination operation must name its actual contract.
- Run a documented agent-style create → inspect → diagnose → repair → evaluate → export cycle, including an invalid candidate, a scoped instance edit, and an unchanged sibling. Preserve the existing source/export regression gates and publish actual results.

After that gate, select finite milestones for versioned reuse and procedural construction, richer exterior modeling, physical interactions and mechanisms, supplied controllers, and the remaining domain/delivery capabilities. Each milestone must name representative tasks, limits, expected failures, and evidence before implementation. Production compiler, physics-engine, and editor choices follow relevant requirements and experiments; the present prototype does not settle them permanently.
