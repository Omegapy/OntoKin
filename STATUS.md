# OntoKin status

Checkpoint: **2026-10-18T03:04:38Z**. Goal: [GOAL.md](GOAL.md). Project goal remains **in progress**.

## Verified published baseline

| Item | Recorded state |
| --- | --- |
| Published `main` observed at this checkpoint | [c4152509533f77ba54fac78268ba425df9b1a177](https://github.com/Omegapy/OntoKin/commit/c4152509533f77ba54fac78268ba425df9b1a177) |
| Tree | `147d89c4905ab33520064c3f97aee7c192d990c4` |
| Implementation | `ontokin-reference` **0.3.0**, experimental |
| Language / export contracts | Adopted `core-0.1`; `ontokin.agent/0.1`; bounded `ontokin.glb/0.1` |
| Latest verified CI for the published baseline | [Run 39092228352](https://github.com/Omegapy/OntoKin/actions/runs/39092228352), all four jobs completed successfully for the identified 0.3.0 implementation |
| Current milestone | **OK-LANG-002: Pinned Modules and Keyed Assembly Construction**; precise grammar, program-bundle identity, and acceptance fixtures are being designed before implementation |

The working checkout may use a synthetic connector snapshot commit with the same tree. Verify the actual remote head before publishing; a local commit identity is not automatically the published GitHub identity.

## What exists

The parser, typed validator, and semantic evaluator support the bounded core programs. Primitive sphere/box meshes and sampled world transforms export to GLB, including correct gravity/release motion. An offline Three.js viewer plays the actual files. The source remains editable and authoritative.

[OK-ENG-001](docs/engineering/OK-ENG-001-core-reference-implementation-and-conformance-plan.md) records the headless milestone. [OK-ENG-002](docs/engineering/OK-ENG-002-3d-scene-animation-export-and-visual-validation.md) records scene/export contracts and evidence: 103 local tests, 43 source cases with 694 assertions, six independently validated GLBs, 347 Three.js pose comparisons, and ten browser checks. CI also passed Python 3.11–3.13 and the visual job. These retained reports are historical; fresh 0.3.0 regression and CI evidence is recorded separately.

The published 0.3.0 release additionally implements a durable local Python/JSONL agent service. Its final local regression run passed **150 tests**, including **47 new agent, catalog, CLI, and transaction tests**. A01–A10 pass through actual requests. The separate agent-style demonstration passes **18 checks across 41 operations**, including an invalid candidate, a scoped instance repair, an unchanged sibling, prefix evaluation, and retrieved GLB bytes. Independent Khronos validation reports zero errors/warnings; Three.js matches 200 object poses for that artifact. The actual agent GLB also passed eight browser checks and 16 world-pose comparisons; its capture was inspected. Fresh export regression passed all six legacy GLBs and 347 pose comparisons. The [identified evidence](docs/engineering/agent-validation/validation-summary.json) and [observed CI results](docs/engineering/agent-validation/ci-results.json) close the finite OK-AGENT-001 gate. The full product remains unfinished.

Generic `check --level delivered` remains unsupported; explicit GLB delivery has its own named contract. Blender import has not been tested.

## Scope still unmet

- The next language/profile for pinned modules and keyed generated parts, together with program-wide source/revision/agent contracts. Broader production/distributed agent infrastructure and an independently calibrated authoring-benefit benchmark remain future work.
- Broader modules/packages, procedural generators and algorithms, compatible part replacement, rich geometry, deformation mappings, textures, and reusable standard components.
- Contacts/collisions, general rigid-body dynamics, forces/actuation, dynamic joints/closed mechanisms, capture/multiple grips, and purposeful locomotion/manipulation.
- Complete creature, vehicle, flight/swimming, vegetation, terrain/building, fluid/deformable, appearance, and live destination contracts from GOAL.
- Calibrated scale/performance guarantees, agent-benefit benchmarks, distribution/license decisions, and production architecture choices.

The current physical subset is uniform gravity and free homogeneous spheres, with externally prescribed connections and disabled collisions. GLB playback contains recorded poses, not live OntoKin physics. Historical coverage manifests remain design records; they must not be relabeled as current implementation completion.

## Next actions

1. Publish this verified CI checkpoint and retain the completed 0.3.0 evidence.
2. Review and adopt OK-LANG-002 with finite reuse, boundaries, failures, composition, targeted edits, and delivery cases. The proposed profile is `ontokin "0.2"` / `construction-0.1`; existing source meanings remain unchanged.
3. Implement on a coordinated isolated branch: parser/bundle linker, construction/runtime, then durable agent 0.2 and complete source-to-animation verification. No new language behavior is implemented at this checkpoint.

## Periodic review

The **Advance OntoKin** recovery review is configured and enabled with `RRULE:FREQ=HOURLY`, using `America/Denver`. Its task identity is `6ad42d31d3ec819196dc1cc1e3ede709`, created at `2026-10-18T02:21:37.977291Z`. It rereads GOAL/STATUS/AGENTS, the current contract, actual main and CI, then follows the integration lease. A live worker makes independent scheduled reviews read-only. An expired lease permits a conditional acquisition attempt and one bounded verified continuation iteration.

Creation and enablement are verified. The scheduling service reports a last-run timestamp of `2026-10-18T02:22:40.519041Z`; its review outcome has not been independently inspected, so this file does not claim a completed scheduled review. This task and the recovery records do not promise an indefinitely running browser thread or unlimited background execution.

## Integration lease and concurrent work

| Lease field | Value |
| --- | --- |
| Integration owner | `root` in the owner's active stewardship chat |
| Checkpoint / renewal | `2026-10-18T03:04:38Z` |
| Lease expires | `2026-10-18T09:04:38Z` |
| Current integration task | OK-LANG-002 contract and implementation preparation |

Renew this UTC lease at each integration checkpoint. While it is live, scheduled reviews and other independent sessions may inspect and report but **must not edit or publish**. The owner may delegate bounded file work; publication remains coordinated by the integration owner.

An expired lease permits an acquisition attempt, not automatic ownership. Fetch the current GitHub head and lease, acquire through a commit/update conditioned on that exact head, and confirm success before editing. Use an isolated branch for implementation. If the head or lease changed, reconcile instead of overwriting another writer. The lease coordinates work; it does not grant platform permissions.

## Recovery checkpoint

At session start or after compaction, read GOAL, this file, AGENTS, and the current engineering contract. Inspect the real repository tree, local changes, remote head, live lease, and relevant CI. Preserve others' work. Identify the next unmet acceptance gate and continue it. Update this record at every meaningful checkpoint with actual commits, checks, decisions, blockers, next actions, and lease renewal. Do not infer completion from a previous chat summary alone.
