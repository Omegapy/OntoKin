# OntoKin status

Checkpoint: **2026-10-18T06:54:12.963Z**. Goal: [GOAL.md](GOAL.md). Project goal remains **in progress**.

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
| Next gate | **OK-LANG-003:** implement adopted language `0.3` / `surface-0.1` in `.ok` parsing, semantic construction, agent revision/inspection and GLB/0.3 delivery; M01–M12 remain unpassed |

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

## Adopted surface contract and prototype checkpoint

On **2026-10-18**, [OK-LANG-003 v0.2](docs/language-design/OK-LANG-003-parameterized-exterior-surfaces-and-material-regions.md) adopted the new language `0.3` / `surface-0.1` **contract** and [prospective M01–M12 corpus](docs/language-design/surface-v0.1/acceptance.json). The original proposal is preserved verbatim as an archive. The [isolated workbench](prototypes/surface_v01/README.md) implements pure bounded section-sorted loft triangulation and a glTF 2.0 multi-material prototype, with 18 additional Python tests. It deliberately does **not** alter the published `ontokin` 0.4.0 package or claim any native `.ok` surface compilation.

[Identified branch CI](https://github.com/Omegapy/OntoKin/actions/runs/39105285128) for merged [commit `96c12d5`](https://github.com/Omegapy/OntoKin/commit/96c12d5a2bd11cc04423c497a7b134539c4e73ce) passed **all four jobs** on Python **3.11, 3.12 and 3.13**, including **294 Python tests**, original source conformance **43/43**, agent conformance **A01–A10**, construction conformance **C01–C20**, existing 0.4.0 destination validation, and documentation preservation. The prototype GLB is identified by SHA-256 **`b2034d95d2c1d856642be68b29ffee375b918654d3141197654fb6ac1dd5183b`**. Independently decoded Khronos/Three.js verification found **zero format errors/warnings**, **three actual PBR groups**, **96 triangles**, and **2.4439790857755384e-08 m** maximum local float32 vertex error. This is an experimental **Python-input** GLB, **not** GLB/0.3 from OntoKin source. The full source/agent/destination release gate **M01–M12 remains unpassed**. Detailed scope and reproduction steps are in [the checkpoint](docs/engineering/surface-validation/prototype-checkpoint.md).

Existing `0.4.0` source identity is unchanged; its separately identified construction visual evidence still applies only to that version. Branch CI covers the merge source revision. A new main CI run triggered by the later status checkpoint must be inspected separately; do not infer its outcome in advance.

## Scope still unmet

- Broader package distribution, procedural generators and algorithms, compatible part replacement, reusable standard components, rich exterior surfaces, regional materials, textures and deformation mappings.
- Contacts/collisions, general rigid-body dynamics, forces/actuation, dynamic joints and closed mechanisms, capture/multiple grips, and purposeful locomotion/manipulation.
- The complete creature, vehicle, flight/swimming, vegetation, terrain/building, fluid/deformable, appearance and live-destination contracts retained in GOAL.
- Calibrated scale/performance guarantees, an independently measured agent-authoring benefit, production/distributed agent infrastructure, distribution/license decisions and production architecture choices.

The physical subset remains uniform gravity and free homogeneous spheres, with externally prescribed connections and disabled collisions. GLB playback contains recorded poses; it does not execute live OntoKin physics. Historical coverage manifests remain design records and must not be relabeled as current implementation completion.

## Next actions

1. Recenter on GOAL, STATUS and AGENTS; verify current main, CI and the lease. Acquire a new integration lease conditionally before any further edits.
2. Implement the adopted `0.3` / `surface-0.1` parser, types, pure constructors and exact pinned-module resolution. Compile the frozen `.ok` examples and explicitly reject invalid section/material inputs without altering accepted revisions.
3. Bring the isolated loft generator and multi-material GLB serialization into a versioned renderer/visual-binding pipeline. Preserve rigid world motion, source identity, object mass/motion separation, resource accounting and cancellation; build actual source-to-GLB/0.3 results.
4. Complete independent executable M01–M12 fixtures: two different pinned compositions, unseen variants, section/material repair with unchanged siblings/library bytes, local visual placement and animation/release, source-page inspection and independently reviewed destination captures. Keep existing `0.4.0` gates valid for their identified implementation.

The contract and geometry prototype are real deliverables; the native surface-language release remains **in progress**, and the full product is unfinished.

## Periodic review

**Advance OntoKin** is configured and enabled with `RRULE:FREQ=HOURLY`, using `America/Denver`. Task identity: `6ad42d31d3ec819196dc1cc1e3ede709`; created at `2026-10-18T02:21:37.977291Z`. It rereads GOAL/STATUS/AGENTS, the current contract, actual main and CI, then follows the integration lease. A live worker makes independent scheduled reviews read-only. An expired lease permits a conditional acquisition attempt and one bounded verified continuation iteration.

Creation and enablement are verified. The last independently observed scheduling-service timestamp was `2026-10-18T03:07:05.478440Z`; the review outcome was not independently inspected. This record does not claim a completed scheduled review or promise an indefinitely running browser thread or unlimited background execution.

## Integration lease and concurrent work

| Lease field | Value |
| --- | --- |
| Integration owner | None; integration published and lease released |
| Release checkpoint | 2026-10-18T06:54:12.963Z |
| Lease expires | 2026-10-18T06:54:12.963Z |
| Completed task | Adopt OK-LANG-003 source contract, freeze prospective corpus, build and verify isolated surface/GLB prototype |
| Published implementation/documentation | Main `96c12d5a2bd1`; release checkpoint commit follows |
| Next acquisition task | Implement native `.ok` 0.3 / surface-0.1 compiler integration and M01–M12 acceptance |

The bounded integration task was published with expected-head safeguards. The active lease is released at this checkpoint; any new implementation session must reacquire it with an exact-head conditional update. Previously published checkpoints retain their historical meaning.

Expiry permits an acquisition attempt, not automatic ownership. Fetch the current GitHub head and lease, acquire through a commit/update conditioned on that exact head, and confirm success before editing. Use an isolated branch for implementation. If the head or lease changed, reconcile instead of overwriting another writer. The integration owner may delegate bounded work and must renew this UTC lease at meaningful checkpoints. While a lease is live, independent sessions may inspect but must not edit or publish. The lease coordinates work; it does not grant platform permissions.

## Recovery checkpoint

At session start or after compaction, read GOAL, this file, AGENTS and the active contract. Inspect the repository tree, local changes, actual remote head, lease and relevant CI. Preserve others' work. Identify the next unmet acceptance gate and continue it. Update this record with actual commits, checks, decisions, blockers, next actions and lease state. Do not infer completion from a previous chat summary alone.
