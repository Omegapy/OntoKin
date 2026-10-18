# OntoKin status

Checkpoint: **2026-10-18T03:01:09Z**. Goal: [GOAL.md](GOAL.md). Project goal remains **in progress**.

## Verified published baseline

| Item | Recorded state |
| --- | --- |
| Published `main` observed at this checkpoint | [7a7d82b785de5968eb14b9527ea8d182d87eba8f](https://github.com/Omegapy/OntoKin/commit/7a7d82b785de5968eb14b9527ea8d182d87eba8f) |
| Tree | `52abf70e9fd547b01babea6dbf6e9cf55462b80a` |
| Implementation | `ontokin-reference` **0.2.0**, experimental |
| Language / export contracts | Adopted `core-0.1`; bounded `ontokin.glb/0.1` |
| Latest verified CI for the published baseline | [Run 39089671015](https://github.com/Omegapy/OntoKin/actions/runs/39089671015), completed successfully after publishing the stewardship records |
| Current milestone | **OK-AGENT-001: AI Agent Authoring and Inspection Interface**; implementation 0.3.0 exists in the working checkout and local gates pass; local numerical/visual evidence is complete; GitHub publication/CI remains in progress |

The working checkout may use a synthetic connector snapshot commit with the same tree. Verify the actual remote head before publishing; a local commit identity is not automatically the published GitHub identity.

## What exists

The parser, typed validator, and semantic evaluator support the bounded core programs. Primitive sphere/box meshes and sampled world transforms export to GLB, including correct gravity/release motion. An offline Three.js viewer plays the actual files. The source remains editable and authoritative.

[OK-ENG-001](docs/engineering/OK-ENG-001-core-reference-implementation-and-conformance-plan.md) records the headless milestone. [OK-ENG-002](docs/engineering/OK-ENG-002-3d-scene-animation-export-and-visual-validation.md) records scene/export contracts and evidence: 103 local tests, 43 source cases with 694 assertions, six independently validated GLBs, 347 Three.js pose comparisons, and ten browser checks. CI also passed Python 3.11–3.13 and the visual job. The retained CI JSON records the earlier implementation run; the latest run above additionally checked the subsequent documentation commit.

These are bounded demonstrations. The current working checkout additionally implements a durable local Python/JSONL agent service. Its first full regression run passed **150 tests**, including **47 new agent, catalog, CLI, and transaction tests**. A01–A10 pass through actual requests. The separate agent-style demonstration passes **18 checks across 41 operations**, including an invalid candidate, a scoped instance repair, an unchanged sibling, prefix evaluation, and retrieved GLB bytes. Independent Khronos validation reports zero errors/warnings; Three.js matches 200 object poses for that artifact. The actual agent GLB also passed eight browser checks and 16 world-pose comparisons; its capture was inspected. Fresh export regression passed all six legacy GLBs and 347 pose comparisons. The [identified evidence](docs/engineering/agent-validation/validation-summary.json) still needs publication and remote CI before the release gate closes.

Generic `check --level delivered` remains unsupported; explicit GLB delivery has its own named contract. Blender import has not been tested.

## Scope still unmet

- Final OK-AGENT-001 evidence/publication/CI gate; broader multi-file packages, production/distributed agent infrastructure, and an independently calibrated authoring-benefit benchmark.
- Broader modules/packages, procedural generators and algorithms, compatible part replacement, rich geometry, deformation mappings, textures, and reusable standard components.
- Contacts/collisions, general rigid-body dynamics, forces/actuation, dynamic joints/closed mechanisms, capture/multiple grips, and purposeful locomotion/manipulation.
- Complete creature, vehicle, flight/swimming, vegetation, terrain/building, fluid/deformable, appearance, and live destination contracts from GOAL.
- Calibrated scale/performance guarantees, agent-benefit benchmarks, distribution/license decisions, and production architecture choices.

The current physical subset is uniform gravity and free homogeneous spheres, with externally prescribed connections and disabled collisions. GLB playback contains recorded poses, not live OntoKin physics. Historical coverage manifests remain design records; they must not be relabeled as current implementation completion.

## Next actions

1. Local checks and final documentation preservation/navigation verification passed; the release tree is frozen for publication.
2. Publish the verified 0.3.0 implementation and documentation against the observed GitHub head, inspect its CI, and record actual outcomes here.
3. Select the next finite expressive-language milestone against the full GOAL. The next direction is version-pinned reusable modules and bounded keyed assembly construction, as an explicit new language/profile. Its precise contract and acceptance fixtures are being designed before implementation; current core semantics remain unchanged.

## Periodic review

The **Advance OntoKin** recovery review is configured and enabled with `RRULE:FREQ=HOURLY`, using `America/Denver`. Its task identity is `6ad42d31d3ec819196dc1cc1e3ede709`, created at `2026-10-18T02:21:37.977291Z`. It rereads GOAL/STATUS/AGENTS, the current contract, actual main and CI, then follows the integration lease. A live worker makes independent scheduled reviews read-only. An expired lease permits a conditional acquisition attempt and one bounded verified continuation iteration.

Creation and enablement are verified. The scheduling service reports a last-run timestamp of `2026-10-18T02:22:40.519041Z`; its review outcome has not been independently inspected, so this file does not claim a completed scheduled review. This task and the recovery records do not promise an indefinitely running browser thread or unlimited background execution.

## Integration lease and concurrent work

| Lease field | Value |
| --- | --- |
| Integration owner | `root` in the owner's active stewardship chat |
| Checkpoint / renewal | `2026-10-18T03:01:09Z` |
| Lease expires | `2026-10-18T09:01:09Z` |
| Current integration task | OK-AGENT-001 release evidence and publication |

Renew this UTC lease at each integration checkpoint. While it is live, scheduled reviews and other independent sessions may inspect and report but **must not edit or publish**. The owner may delegate bounded file work; publication remains coordinated by the integration owner.

An expired lease permits an acquisition attempt, not automatic ownership. Fetch the current GitHub head and lease, acquire through a commit/update conditioned on that exact head, and confirm success before editing. Use an isolated branch for implementation. If the head or lease changed, reconcile instead of overwriting another writer. The lease coordinates work; it does not grant platform permissions.

## Recovery checkpoint

At session start or after compaction, read GOAL, this file, AGENTS, and the current engineering contract. Inspect the real repository tree, local changes, remote head, live lease, and relevant CI. Preserve others' work. Identify the next unmet acceptance gate and continue it. Update this record at every meaningful checkpoint with actual commits, checks, decisions, blockers, next actions, and lease renewal. Do not infer completion from a previous chat summary alone.
