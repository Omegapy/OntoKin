# OntoKin status

Checkpoint: **2026-10-18T05:45:16Z**. Goal: [GOAL.md](GOAL.md). Project goal remains **in progress**.

## Verified published implementation

| Item | Recorded state |
| --- | --- |
| Implementation integrated into `main` | [7f25e1d88e3734fe515134b045da5bc2388f01a7](https://github.com/Omegapy/OntoKin/commit/7f25e1d88e3734fe515134b045da5bc2388f01a7) |
| Implementation tree | `f75884a8b4bcc8384182cc4f54399d7ff4c772ab` |
| Package | `ontokin-reference` **0.4.0**, experimental |
| Python package SHA-256 | `2fec4df8a853fb04f05981137165b093dbe5fe72abc1e49ceee15a7747bb4a24` |
| Preserved contracts | Language `0.1` / `core-0.1`; `ontokin.agent/0.1`; `ontokin.glb/0.1` |
| Added contracts | Language `0.2` / `construction-0.1`; `ontokin.bundle/0.1`; `ontokin.agent/0.2`; `ontokin.glb/0.2` |
| Verified implementation CI | [Branch run 39100888186](https://github.com/Omegapy/OntoKin/actions/runs/39100888186) and [main run 39101105169](https://github.com/Omegapy/OntoKin/actions/runs/39101105169): all four jobs passed in each run |
| Completed gate | **OK-LANG-002 / OK-AGENT-002:** pinned modules, keyed construction and atomic program authoring |
| Next gate | **OK-LANG-003:** adopt native exterior-surface/material-region contracts and independent fixtures, then implement |

The implementation passed branch CI before an expected-head update integrated it from `3043e3a671662568e6e6e1a80417eaff7d55533d` into `main`. Main CI also passed. This later documentation/evidence checkpoint preserves those implementation bytes and may have its own commit and CI run. Inspect the actual remote head and relevant CI before publishing. A local connector snapshot may have a different commit identity with the same tree.

## What exists and what passed

The parser, typed validator and semantic evaluator support the adopted bounded profiles. Sphere/box geometry and sampled world transforms export to actual GLBs, including correct gravity/release motion. The offline Three.js viewer plays the files. The source remains editable and authoritative.

The agent service provides discovery, inspection, revision-checked editing, validation, evaluation, cancellation, reconciliation and artifact retrieval. The new program service adds exact offline dependency bundles, nominal imported definitions, keyed generated parts, final occurrence overrides, and atomic program/source edits. Generated occurrences identify their declarations and overrides; inspecting an occurrence does not silently grant authority to edit a shared library.

The [identified 0.4.0 local evidence](docs/engineering/construction-validation/validation-summary.json) and [observed CI jobs](docs/engineering/construction-validation/ci-results.json) establish:

- **276 Python tests** passed against the fixed implementation. Original source conformance passed **43 cases / 694 authored assertions**; original agent conformance passed **A01–A10**.
- **C01–C20** passed through **128 distinct required executable test methods** and the separately identified retained destination evidence. Tests, source cases, assertions and pose comparisons are different counts.
- The actual program-agent workflow passed **35 checks across 22 operations**: discover a pinned library, construct two differently sized assemblies, reject an invalid candidate, repair one occurrence, preserve sibling/library bytes, evaluate and retrieve the GLB.
- The construction scene has **18 objects**. Khronos reported **zero glTF errors and warnings**. Independent decoding checked **18 mesh dimensions and 126 world poses**. The browser passed **eight checks and 126 pose comparisons**, and the actual [capture](docs/engineering/construction-validation/keyed-rack.png) was inspected.
- Fresh export regressions passed all **six legacy GLBs / 347 poses** and the original agent demonstration's **200 poses**. Legacy browser checks passed ten checks; the fresh agent browser run passed eight checks and 16 poses. Historical reports remain intact; byte-identical fresh outputs are retained separately.
- Independent schema validation checked all **five schemas**, the source bundle/file manifest, and all 22 actual requests and responses. Documentation preservation verified **29 historical sources and 233 sections**.
- GitHub CI passed Python **3.11, 3.12 and 3.13**, plus the GLB format/visual job. The latter rebuilt and independently checked the actual exports and browser workflows.

Earlier finite gates remain recorded in [OK-ENG-001](docs/engineering/OK-ENG-001-core-reference-implementation-and-conformance-plan.md), [OK-ENG-002](docs/engineering/OK-ENG-002-3d-scene-animation-export-and-visual-validation.md), and [OK-AGENT-001](docs/engineering/OK-AGENT-001-ai-agent-authoring-and-inspection-interface.md). The new adopted contracts are [OK-LANG-002](docs/language-design/OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md) and [OK-AGENT-002](docs/engineering/OK-AGENT-002-program-bundles-and-atomic-source-edits.md).

Generic `check --level delivered` remains unsupported; explicit GLB delivery has its own named contract. Blender import has not been tested.

## Scope still unmet

- Broader package distribution, procedural generators and algorithms, compatible part replacement, reusable standard components, rich exterior surfaces, regional materials, textures and deformation mappings.
- Contacts/collisions, general rigid-body dynamics, forces/actuation, dynamic joints and closed mechanisms, capture/multiple grips, and purposeful locomotion/manipulation.
- The complete creature, vehicle, flight/swimming, vegetation, terrain/building, fluid/deformable, appearance and live-destination contracts retained in GOAL.
- Calibrated scale/performance guarantees, an independently measured agent-authoring benefit, production/distributed agent infrastructure, distribution/license decisions and production architecture choices.

The physical subset remains uniform gravity and free homogeneous spheres, with externally prescribed connections and disabled collisions. GLB playback contains recorded poses; it does not execute live OntoKin physics. Historical coverage manifests remain design records and must not be relabeled as current implementation completion.

## Next actions

1. Recenter on GOAL, this file, AGENTS, the actual remote head and relevant CI. Acquire the expired integration lease conditionally before editing.
2. Refine [OK-LANG-003](docs/language-design/OK-LANG-003-parameterized-exterior-surfaces-and-material-regions.md) into an adopted versioned native surface/material contract. Fix grammar, types/profile, section identity and geometric order, caps/normals/topology, regional appearance, visual bindings, approximation bounds, resource limits and source/inspection behavior before implementation.
3. Adopt independent positive, boundary, negative, composition, unseen-variant and targeted-repair fixtures. Then implement on an isolated branch and verify actual authored surfaces/material assignments, reusable composition, unchanged siblings/library bytes, motion and destination output while preserving existing gates.

OK-LANG-003 is a proposal, with no implementation or measured acceptance claim. The full product remains unfinished.

## Periodic review

**Advance OntoKin** is configured and enabled with `RRULE:FREQ=HOURLY`, using `America/Denver`. Task identity: `6ad42d31d3ec819196dc1cc1e3ede709`; created at `2026-10-18T02:21:37.977291Z`. It rereads GOAL/STATUS/AGENTS, the current contract, actual main and CI, then follows the integration lease. A live worker makes independent scheduled reviews read-only. An expired lease permits a conditional acquisition attempt and one bounded verified continuation iteration.

Creation and enablement are verified. The last independently observed scheduling-service timestamp was `2026-10-18T03:07:05.478440Z`; the review outcome was not independently inspected. This record does not claim a completed scheduled review or promise an indefinitely running browser thread or unlimited background execution.

## Integration lease and concurrent work

| Lease field | Value |
| --- | --- |
| Integration owner | None; `root` releases the lease with this completed 0.4.0 checkpoint |
| Release checkpoint | `2026-10-18T05:45:16Z` |
| Lease expires | `2026-10-18T05:45:16Z` |
| Completed integration task | OK-LANG-002 / OK-AGENT-002 implementation, verification and publication |
| Next acquisition task | OK-LANG-003 contract and fixture adoption |

This release takes effect when the checkpoint is published. Until then, the previously published live lease governs concurrent writers. After publication the closing worker may observe CI read-only; any further edit requires conditional reacquisition.

Expiry permits an acquisition attempt, not automatic ownership. Fetch the current GitHub head and lease, acquire through a commit/update conditioned on that exact head, and confirm success before editing. Use an isolated branch for implementation. If the head or lease changed, reconcile instead of overwriting another writer. The integration owner may delegate bounded work and must renew this UTC lease at meaningful checkpoints. While a lease is live, independent sessions may inspect but must not edit or publish. The lease coordinates work; it does not grant platform permissions.

## Recovery checkpoint

At session start or after compaction, read GOAL, this file, AGENTS and the active contract. Inspect the repository tree, local changes, actual remote head, lease and relevant CI. Preserve others' work. Identify the next unmet acceptance gate and continue it. Update this record with actual commits, checks, decisions, blockers, next actions and lease state. Do not infer completion from a previous chat summary alone.
