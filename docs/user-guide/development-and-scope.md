# Development checks, scope and references

[User guides](README.md) · [Project overview](../../README.md) · [Current status](../../STATUS.md)

Run command examples from the repository root with Python 3.11 or later. Each named profile keeps its own contract and evidence; the examples do not select a new default or establish a comparative authoring advantage.

## Verification

Run the existing Python test and conformance checks locally:

```bash
python3 tools/check_local.py
```

The [local setup guide](../development/LOCAL-SETUP.md) prepares the environment for the complete run and says where a local session writes its output. Each run saves a source inventory, environment, per-step logs and JSON results in a new `build/local-checks/` directory unless `--output-dir` names another. Use `python3 tools/check_local.py --list` to inspect the commands. After the one-time setup in [the local validation guide](../../docs/engineering/OK-ENG-006-local-validation-and-hosted-ci-policy.md), `python3 tools/check_local.py --full` also rebuilds the 3D examples and runs the independent format and browser checks in an isolated copy. The original source and recorded historical evidence stay intact.

The tests check source-to-state behavior, independent numerical expectations, diagnostics, event boundaries, release from moving joint chains, parameter scope, and command-line failures. Export tests also decode the GLB independently, check triangle geometry and several complete turns of rotation, and reject precision loss or unsupported output. The [GitHub Actions workflow](../../.github/workflows/reference.yml) is now manual-only with an explicit hosted-job input that defaults to false. Pushes and pull requests no longer start this workflow. Manually opting in still consumes the applicable GitHub allowance or paid budget; it is not needed for local checks. Existing older branches keep their previous workflow definitions until synchronized.

A local run reports only the Python version and platform actually executed. Full compatibility still needs identified Python 3.11, 3.12 and 3.13 runs; complete release gates retain separate external-evidence and visual-review requirements. [OK-ENG-001](../../docs/engineering/OK-ENG-001-core-reference-implementation-and-conformance-plan.md#6-measured-evidence) preserves the original prototype evidence; [OK-ENG-002](../../docs/engineering/OK-ENG-002-3d-scene-animation-export-and-visual-validation.md#8-measured-evidence) records the export milestone.

The [C01–C20 construction manifest](../../docs/language-design/construction-v0.1/validation-cases.json) fixes the new module, construction, scoped-edit, lifecycle, and delivery requirements. Its [runner](../../ontokin/construction_conformance.py) executes the selected tests and separately verifies identified external evidence. A run without the required external delivery evidence leaves that gate pending. [STATUS.md](../../STATUS.md) records when the complete local and CI release gate has closed; the fixture expectations and demo driver alone do not establish that result.

## Git LFS for engineering archives

Git LFS tracking is configured for future ZIP, numeric ZIP-part, TAR.XZ and TAR.GZ payloads under `docs/engineering/lfs-archives/`. Existing archives remain ordinary Git files with their original bytes and history. [The storage guide](../../docs/engineering/OK-ENG-010-git-lfs-archive-storage.md) defines the exact profile, local Git LFS setup, storage verification and no-history-rewrite migration procedure. [The focused validation record](../../docs/engineering/lfs-storage-validation-2026-10-28/README.md) identifies the actual checks.

Authenticated object upload and independent retrieval are required before publishing new LFS pointers. Existing-archive migration is prepared but remains pending that authenticated transfer. Ordinary checkouts with no LFS payloads retain their existing local-validation requirements; checkouts containing tracked LFS payloads need Git LFS 3.8.1 or newer and hydrated files.

## Language and implementation scope

The [core language specification](../../docs/language-design/OK-LANG-001-core-language-specification.md) reviews all 28 proposed semantic rules and defines `core-0.1`: typed classes and pure methods, independently instantiated parts, explicit frames and units, prescribed joints, concurrent action channels, exact event ordering, and a limited gravity/release contract.

The `construction-0.1` extension adds side-effect-free source modules with exact version/content pins, qualified nominal types and pure functions, flat immutable `Keyed<T>` inputs, and bounded generated parts with stable per-key identities. Public per-key overrides apply before nested construction. This profile uses the same motion and physical subset. Imports are resolved from explicitly supplied bytes; supported limits include 16 dependency modules, 256 entries per keyed value, 1,000 objects, and 2,000,000 total source bytes. Nested authored keyed values, runtime topology changes, host-language execution, and network package resolution are outside this profile. The [language contract](../../docs/language-design/OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md) supplies the complete limits and version rules.

Start with [independently moving parts](../../docs/language-design/core-v0.1/01-independent-parts.ok), then [gravity and release](../../docs/language-design/core-v0.1/02-gravity-and-release.ok). Two further programs check rotational velocity transfer and the distinction between ownership and following. The [validation manifest](../../docs/language-design/core-v0.1/validation-cases.json) preserves the original 43 source cases and ten agent-operation cases with their expected outcomes and historical design status. The separate [source conformance report](../../docs/engineering/agent-validation/core-conformance.json) records execution under 0.3.0. The [agent conformance report](../../docs/engineering/agent-validation/conformance.json) executes A01–A10 against the durable service; both are finite test-corpus evidence, not full-product certification.

The core reference uses Python's standard library and analytic motion equations. Its GLB/0.1 adapter exports sphere/box meshes, linear RGBA appearance, optional display markers, and sampled world transforms. Source ownership, physical properties, joints, and release events remain inspectable metadata; a destination plays baked motion without executing those rules. That core profile does not establish contact, dynamic articulated mechanisms, general body dynamics, deformation or broader delivery contracts. The current goal defers broad engine/runtime investment; later named profiles retain their own scope and evidence.

The core physical subset is explicit: uniform gravity, free homogeneous solid spheres, and externally prescribed connections without a load solution. Collision response is disabled and there is no ground plane. A sphere can pass below zero height without a collision. Passing the bounded fixtures does not certify correctly rounded transcendental functions for every input, exact internal rotations, rigorous interval bounds for all rotating mechanisms, long-duration accuracy, or the broader product. [OK-ENG-001](../../docs/engineering/OK-ENG-001-core-reference-implementation-and-conformance-plan.md) records these limits and the production decisions that still need evidence.

## Start reading

The [current goal](../../GOAL.md) and [C252 review decision](../engineering/review-integration-c252/DECISION.md) govern present priorities. Older product ambitions remain historical or deferred where that decision says so.

Use the [documentation guide](../../docs/README.md) for the full reading order, document status, diagrams, and earlier design records.

| Question | Document |
| --- | --- |
| What did the original capability definition propose? | [OK-CAP-001: Modeling, motion, and object structure](../../docs/product/OK-CAP-001-modeling-motion-and-object-structure.md) |
| What did the original product requirements propose? | [OK-PRD-001: Product requirements](../../docs/product/OK-PRD-001-product-requirements.md) |
| What do objects, movement, mechanics, and physics mean? | [OK-SEM-001: Core object, motion, and physics semantics](../../docs/language-design/OK-SEM-001-core-object-motion-and-physics-semantics.md) |
| How does an agent express those meanings in valid code? | [OK-LANG-001: Core language specification](../../docs/language-design/OK-LANG-001-core-language-specification.md) |
| What does the first prototype implement, and how is it checked? | [OK-ENG-001: Core reference implementation and conformance plan](../../docs/engineering/OK-ENG-001-core-reference-implementation-and-conformance-plan.md) |
| How do calculated objects and motion become a visible animation? | [OK-ENG-002: 3D scene representation, animation export, and visual validation](../../docs/engineering/OK-ENG-002-3d-scene-animation-export-and-visual-validation.md) |
| How does an agent discover, inspect, edit, evaluate, and retrieve an animation? | [OK-AGENT-001: AI agent authoring and inspection interface](../../docs/engineering/OK-AGENT-001-ai-agent-authoring-and-inspection-interface.md) |
| How do exact-pinned modules and immutable inputs generate reusable assemblies? | [OK-LANG-002: Pinned modules and keyed assembly construction](../../docs/language-design/OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md) |
| How does an agent inspect and atomically edit a complete source bundle? | [OK-AGENT-002: Program bundles and atomic source edits](../../docs/engineering/OK-AGENT-002-program-bundles-and-atomic-source-edits.md) |
| How do native exterior surfaces and material regions reach GLB? | [OK-ENG-003: Native surface GLB export](../../docs/engineering/OK-ENG-003-native-surface-glb-export.md) |
| How do agents describe native exterior surfaces and material regions? | [OK-LANG-003: Parameterized exterior surfaces and material regions](../../docs/language-design/OK-LANG-003-parameterized-exterior-surfaces-and-material-regions.md) |
| How does source apply an off-center impulse and retain its physical meaning? | [OK-LANG-004: Source impulses and free-sphere dynamics](../../docs/language-design/OK-LANG-004-source-impulses-and-free-sphere-dynamics.md) |
| How do agents inspect impulse state, repair physical parameters and retrieve recorded motion? | [OK-AGENT-004: Source impulse program workflows](../../docs/engineering/OK-AGENT-004-source-impulse-program-workflows.md) |
| What establishes the complete finite impulse release gate? | [OK-ENG-005: Source impulse release conformance](../../docs/engineering/OK-ENG-005-source-impulse-release-conformance.md) |
| How are finite forces authored, inspected and repaired? | [OK-LANG-005: Finite center-of-mass force intervals](../../docs/language-design/OK-LANG-005-finite-center-of-mass-force-intervals.md) and [OK-AGENT-005: Finite-force program workflows](../../docs/engineering/OK-AGENT-005-finite-force-program-workflows.md) |
| How is force motion recorded and independently validated? | [OK-ENG-007: Native force GLB export](../../docs/engineering/OK-ENG-007-native-force-glb-export.md) and [the delivery guide](../../examples/force/README.md) |
| What establishes F01–F12 with actual local execution? | [OK-ENG-008: Provider-neutral finite force release conformance](../../docs/engineering/OK-ENG-008-force-release-conformance.md) |

The documents are organized into **Product**, **Language design**, and **Engineering**. The [founding records](../../docs/README.md#founding-design-records) retain the original vision, language exploration, and architecture options. Their dates and proposal status remain visible. The guide explains how that earlier work relates to the current modeling direction.
