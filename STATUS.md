# OntoKin status

Checkpoint: **2026-10-18T02:04:12Z**. Goal: [GOAL.md](GOAL.md). Project goal remains **in progress**.

## Verified published baseline

| Item | Recorded state |
| --- | --- |
| Published `main` observed at this checkpoint | [edde3f0366bc3bf3fd3a8fe9d08de7e37e69d9f5](https://github.com/Omegapy/OntoKin/commit/edde3f0366bc3bf3fd3a8fe9d08de7e37e69d9f5) |
| Tree | `fe43bda2f226a9b57dd487626280b8885e6b14da` |
| Implementation | `ontokin-reference` **0.2.0**, experimental |
| Language / export contracts | Adopted `core-0.1`; bounded `ontokin.glb/0.1` |
| Latest verified CI for the published baseline | [Run 39087747956](https://github.com/Omegapy/OntoKin/actions/runs/39087747956), completed successfully; all four jobs passed |
| Current milestone | **OK-AGENT-001: AI Agent Authoring and Inspection Interface**; contract/implementation work is next, not yet claimed complete |

The working checkout may use a synthetic connector snapshot commit with the same tree. Verify the actual remote head before publishing; a local commit identity is not automatically the published GitHub identity.

## What exists

The parser, typed validator, and semantic evaluator support the bounded core programs. Primitive sphere/box meshes and sampled world transforms export to GLB, including correct gravity/release motion. An offline Three.js viewer plays the actual files. The source remains editable and authoritative.

[OK-ENG-001](docs/engineering/OK-ENG-001-core-reference-implementation-and-conformance-plan.md) records the headless milestone. [OK-ENG-002](docs/engineering/OK-ENG-002-3d-scene-animation-export-and-visual-validation.md) records scene/export contracts and evidence: 103 local tests, 43 source cases with 694 assertions, six independently validated GLBs, 347 Three.js pose comparisons, and ten browser checks. CI also passed Python 3.11–3.13 and the visual job. The retained CI JSON records the earlier implementation run; the latest run above additionally checked the subsequent documentation commit.

These are bounded demonstrations. The existing agent-operation specification is not a working revision-safe service. Generic `check --level delivered` remains unsupported; GLB export has its own named contract. Blender import has not been tested.

## Scope still unmet

- Agent request/run lifecycle, atomic revision-safe edits, retry/cancellation/recovery behavior, and complete A01–A10 interface evidence.
- Broader modules/packages, procedural generators and algorithms, compatible part replacement, rich geometry, deformation mappings, textures, and reusable standard components.
- Contacts/collisions, general rigid-body dynamics, forces/actuation, dynamic joints/closed mechanisms, capture/multiple grips, and purposeful locomotion/manipulation.
- Complete creature, vehicle, flight/swimming, vegetation, terrain/building, fluid/deformable, appearance, and live destination contracts from GOAL.
- Calibrated scale/performance guarantees, agent-benefit benchmarks, distribution/license decisions, and production architecture choices.

The current physical subset is uniform gravity and free homogeneous spheres, with externally prescribed connections and disabled collisions. GLB playback contains recorded poses, not live OntoKin physics. Historical coverage manifests remain design records; they must not be relabeled as current implementation completion.

## Next actions

1. Publish these stewardship records, then configure the periodic review and record its real task identity, cadence, and last result here. **No automation identity or completed scheduled review is recorded yet.**
2. Specify OK-AGENT-001 against LANG-025–028 and A01–A10, selecting concrete transport, storage/lifetime, budgets, and revision/run behavior without changing core semantics silently.
3. Implement and verify that finite contract, connect it to the source-to-visible-output workflow, publish evidence and CI results, then select the next unmet goal milestone.

## Integration lease and concurrent work

| Lease field | Value |
| --- | --- |
| Integration owner | `root` in the owner's active stewardship chat |
| Checkpoint / renewal | `2026-10-18T02:04:12Z` |
| Lease expires | `2026-10-18T08:04:12Z` |
| Current integration task | Stewardship records, followed by OK-AGENT-001 |

Renew this UTC lease at each integration checkpoint. While it is live, scheduled reviews and other independent sessions may inspect and report but **must not edit or publish**. The owner may delegate bounded file work; publication remains coordinated by the integration owner.

An expired lease permits an acquisition attempt, not automatic ownership. Fetch the current GitHub head and lease, acquire through a commit/update conditioned on that exact head, and confirm success before editing. Use an isolated branch for implementation. If the head or lease changed, reconcile instead of overwriting another writer. The lease coordinates work; it does not grant platform permissions.

## Recovery checkpoint

At session start or after compaction, read GOAL, this file, AGENTS, and the current engineering contract. Inspect the real repository tree, local changes, remote head, live lease, and relevant CI. Preserve others' work. Identify the next unmet acceptance gate and continue it. Update this record at every meaningful checkpoint with actual commits, checks, decisions, blockers, next actions, and lease renewal. Do not infer completion from a previous chat summary alone.
