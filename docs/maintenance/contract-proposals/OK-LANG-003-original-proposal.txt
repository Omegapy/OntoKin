---
project: OntoKin
document_id: OK-LANG-003
title: Parameterized Exterior Surfaces and Material Regions
version: 0.1
date: 2026-10-18
status: proposal-requires-contract-and-fixture-adoption
document_type: next-milestone-design
implementation_status: not-implemented
---

# Parameterized exterior surfaces and material regions

## 1. Next capability and purpose

The next proposed modeling gate is a native, bounded surface family that lets an agent describe useful exterior shapes beyond spheres and boxes. An agent should import reusable component definitions, choose proportions and part counts, construct an exterior model, edit one section or material region of one occurrence, and inspect the resulting geometry and animation.

This proposal follows [GOAL](../../GOAL.md), the exterior-modeling emphasis in [OK-CAP-001](../product/OK-CAP-001-modeling-motion-and-object-structure.md), and the geometry, appearance, and delivery requirements in [OK-PRD-001](../product/OK-PRD-001-product-requirements.md). [OK-LANG-002](OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md) provides pinned component reuse and finite keyed construction. It does not itself supply a richer surface vocabulary.

**This document selects a design direction for the next iteration. It does not adopt grammar, a new language/profile number, numeric limits, or implemented support.** The next worker must resolve the decisions below into a complete versioned contract, grammar, schemas, and independent positive/boundary/negative/composition/repair fixtures before measuring implementation results. Keep the construction release and its evidence intact while doing that work.

## 2. Proposed first surface family

A capped loft connects explicitly positioned cross-sections to form a surface. A bounded family of sections on parallel planes along a strictly advancing longitudinal axis would support tapered limbs, shaped shells, handles, bottles, and branch-like forms. Each section could specify its axial position, lateral offset, width, and depth. Positive elliptical cross-sections are a candidate starting point; the exact family and cap treatment need adoption.

The family should permit meaningful changes through typed `.ok` parameters and pure constructors. An asset-specific Python generator or a prebuilt mesh imported by a demonstration would not establish the promised native language capability.

Source keys identify sections. Explicit dimensional coordinates order their geometry. Lexicographic key order must not silently become geometric ordering. Stable region and section identities belong to source recipes; triangle indices remain derived output and may change when tessellation changes. Inserting a section must preserve surviving source identities without pretending that the old mesh topology remains identical.

### Decisions required before implementation

| Decision | Required contract |
| --- | --- |
| Cross-section family | Supported outlines, positive dimensions, offset meaning, longitudinal axis, and unit/frame rules. |
| Geometric ordering | Strict station ordering, treatment of input order, and exact duplicate-position rejection. |
| Caps and topology | Supported end caps, closed/open distinction, winding, zero-area/zero-radius policy, and intersection guarantees or explicit exclusions. |
| Surface approximation | Angular and longitudinal tessellation, ideal-surface versus mesh approximation, finite precision, and independently measured error. |
| Normals | Smoothing and crease behavior, cap normals, finite normalization, and deterministic generation. |
| Appearance | Stable named regions, actual triangle assignments, supported material parameters, defaults, and unsupported texture/deformation behavior. |
| Visual binding | Logical carrier, explicit fixed local placement, geometry/physical-body distinction, and motion/release composition. |
| Resource bounds | Maximum sections, regions, vertices, triangles, aggregate generated data and output bytes; maximum and one-over fixtures. |
| Source API | Versioned immutable section/material values, pure constructors, generated identity rules, discovery, inspection, and scoped overrides. |
| Delivery | Named GLB contract, multiple material primitives, source/recipe provenance, losses, and independent destination checks. |

The existing `construction-0.1` flat `Keyed` value whitelist is fixed. New section or material values must be introduced through an explicit new language/profile contract. They cannot be inserted into the current profile while retaining its old name and claims.

## 3. Geometry, appearance, and mechanics

Keep the surface recipe, regional appearance, and visual binding explicit. A surface or region must not automatically add an object, physical body, ownership edge, joint, mass contribution, or motion authority. Existing prescribed object/joint motion can carry a rigid surface under a declared binding. Existing sphere-body gravity/release remains available only under its actual physical contract.

Deriving mass or inertia from loft geometry would require a separate physical-distribution rule and independent numerical checks. Producing a closed-looking mesh does not establish that rule. This preserves the distinctions in [OK-SEM-001](OK-SEM-001-core-object-motion-and-physics-semantics.md) and the adopted [core specification](OK-LANG-001-core-language-specification.md).

A material region must affect real triangle groups and serialized material assignments. Retaining a region name only in metadata would not satisfy this milestone. Similarly, a visual-binding record must affect the decoded placement, without introducing a second authority over the carrier's coordinates.

## 4. Implementation boundary

Reuse the existing evaluator and durable program service where their contracts apply. Introduce pure, bounded surface inputs and a generator that produces positions, normals, indices, region assignments, bounds, and recipe-to-output provenance. Count required output before allocation and observe cancellation during generation.

Extend the visual representation to support several region/material primitives for one logical carrier. Preserve source identities independently of mesh indices. Detailed geometry inspection must be bounded and paginated; ordinary object inspection should not return an unbounded full mesh.

Extend the named delivery adapter and its independent decoder checks to actual geometry, material groups, and promised attributes. Preserve world-transform baking, timing, source-bundle identity, and release semantics. Do not infer correct exported geometry from an in-memory recipe or metadata alone.

## 5. Acceptance work to adopt

The following groups define what the next contract must turn into concrete fixtures. They are **unmeasured requirements**, not passed cases or frozen tolerance values.

| Group | Evidence required |
| --- | --- |
| M01: Analytic shapes | Constant and tapered sections match independently derived bounds, cross-sections, orientation and, where promised, closed-surface volume. |
| M02: Nontrivial shape | An offset and tapered exterior has valid caps/winding, finite normals and no degenerate triangles within the supported family. |
| M03: Approximation | Separately measured ideal-surface approximation and float32 delivery error, with explicit tessellation settings and tolerances fixed in advance. |
| M04: Regional appearance | Independently decoded triangles and materials carry the expected regions; a region edit visibly changes the intended area. |
| M05: Reusable modeling | One pinned `.ok` library builds at least two different compositions through language parameters and constructors. |
| M06: Unseen variants | Predetermined held-out proportions, section counts and composition combinations work within the declared support range. |
| M07: Targeted repair | One section/region edit changes the chosen occurrence, preserving sibling/library bytes, unrelated identities and applicable mechanics. |
| M08: Topology changes | Insertion/removal preserves surviving source keys and reports changed mesh data without promising stable triangle indices. |
| M09: Motion composition | Independent actions, nonidentity local placement and release retain their expected world positions, rotations and timing. |
| M10: Failure and bounds | Duplicate stations, invalid dimensions, frame mismatch, missing regions, unsupported caps/intersections, resource limits and cancellation fail precisely. |
| M11: Destination evidence | Actual source, geometry/material decoding, numerical playback and inspected multi-view or animated captures identify the same program and artifact. |
| M12: Regression | Existing core, agent, construction and destination gates remain true for their named versions. |

Fix candidate limits and the independent oracle before implementing their tests. A convenient passing example must not determine the acceptance range after the fact. A render is useful evidence of appearance and usability; it does not replace topology, material, dimensional or motion checks.

## 6. Proposed demonstration

Use one library of shaped rigid components to build a complete segmented creature or articulated prop and a differently composed branch-like or ornamental object. Add another instance with different proportions and an occurrence-specific shape or region edit. The same native surface family should explain all of them without hidden host-language preparation.

Retain the complete agent workflow: discover the public contracts, author a new combination, receive an invalid section/region diagnostic, repair it through the authorized source scope, inspect the affected dependencies, and export the corrected scene. Retain task-specific inputs and preparation along with the measured result.

This gate would establish richer exterior construction and source-driven variation. Continuous skin deformation, purposeful locomotion, contacts, general rigid-body dynamics, wind response, textures and live engine behavior remain separate unmet goals. The later agent-benefit comparison still needs unseen tasks, repair effort, cost, quality and a documented direct-tool baseline; this milestone must not claim an unmeasured productivity gain.

## 7. Recovery instruction

After the construction gate closes, reread GOAL, STATUS and AGENTS, inspect the actual main head and CI, and follow the integration lease. Refine this proposal into one finite adoptable contract on an isolated branch. Do not change `0.1`/`0.2` semantics in place, start implementing an undecided surface contract, or mark the broader product complete because these shapes can be rendered.
