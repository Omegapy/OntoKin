# OntoKin

**A typed semantic language for AI agents to construct, inspect, repair and transport physically meaningful 3D objects.**

OntoKin (pronounced **ON-toh-kin**) gives an agent editable `.ok` source that names parts, records dimensions and units, declares physical properties and preserves source identity. Its intermediate representation is the structured object description between that source and specialist tools. The accepted source revision remains authoritative; a delivered mesh is one checked result of it.

For example, an agent can change one component in a reusable assembly, reject a value with the wrong unit, preserve an unchanged sibling and retrieve an artifact tied to the accepted source. Engines and specialist tools provide rendering, general simulation and gameplay.

## How the pieces fit

| Stage | Responsibility |
| --- | --- |
| Request and `.ok` source | Express named parts, supported dimensions, relationships and physical intent. |
| Checked edit and evaluation | Validate the requested change, retain accepted source on failure and inspect supported state. |
| Specialist tools and transport | Produce or consume geometry, recorded motion and destination-specific results under a named contract. |
| Artifact and provenance | Identify the source revision and artifact bytes; disclose measured preservation, loss and unsupported behavior. |

External generators are potential geometry suppliers. That integration is a planned experiment. Current exports use the implemented source geometry and named GLB profiles.

## Current status and research question

OntoKin is a research prototype with released finite capabilities and explicitly experimental development. The reference package is **0.4.0**. Named profiles cover reusable assemblies, native surfaces/materials, bounded motion, revision-safe agent edits and recorded GLB export. [Current status](STATUS.md) separates implemented behavior, complete finite release evidence and unresolved requirements.

The central question is whether the **same agent** achieves more correct localized repairs, better preservation or lower correction cost with OntoKin than with relevant direct Blender/Python or OpenUSD workflows. **A comparative advantage has not been established.** Existing scripted demonstrations and receiver checks establish only their documented scopes.

The [November 16 review decision](docs/engineering/review-integration-c252/DECISION.md) retains semantic authoring and checked transport, prioritizes a controlled benchmark and defers broad language/backend expansion. A finite Blender receiving result includes disclosed normal loss; the original strict normal failure remains. The Godot second-target proof is incomplete. Unreal/Verse mappings are [conceptual integration boundaries](docs/engineering/semantic-export-c210/UNREAL-INTEROP.md).

## Try an agent edit

Use **Python 3.11 or later**, from this repository's root. The reference uses the standard library; this checkout workflow needs no package installation.

```sh
python3 tools/build_agent_demo.py --output-dir /tmp/ontokin-first-model
```

Open the checkout's [offline viewer](examples/visual/viewer.html), choose **Open GLB**, and select `/tmp/ontokin-first-model/repaired.glb`. At **1.5 s**, the moving assembly's blue head is wider than the stationary assembly's head. The scripted client rejects an invalid units edit, repairs one occurrence and retrieves the recorded animation. It is a reproducible API example, not a model benchmark.

Start your own edit with the [scene](examples/agent/authoring-demo.ok), [Agent/0.1 request schema](docs/language-design/agent-v0.1/request.schema.json) and [agent workflow guide](docs/user-guide/agent-workflows.md). A [pinned-library example](docs/user-guide/agent-workflows.md#build-an-assembly-from-a-pinned-component-library) demonstrates multi-file assemblies through Agent/0.2.

<a id="run-the-core-prototype"></a><a id="commands-and-failure-results"></a>

To inspect the existing CLI or check a core source file:

```sh
python3 -m ontokin capabilities
python3 -m ontokin check docs/language-design/core-v0.1/01-independent-parts.ok
```

See [core commands and failure results](docs/user-guide/core-and-cli.md) for evaluation, exact time boundaries, exit codes and optional installation. Examples requiring later profiles name them explicitly; default Agent/0.1 and GLB/0.1 contracts remain unchanged.

<a id="continue-from-current-checkpoint"></a>

## Continue development in a browser chat

Use [CHATGPT-START-HERE.md](CHATGPT-START-HERE.md) and the [continuation/recovery prompts](docs/workflow/BROWSER-PROMPTS.md). The [workflow guide](docs/workflow/README.md) explains how requirements, plans, roles, skills, project memory and evidence stay in GitHub. Each bounded browser development or recovery scope also delivers a verified session ZIP under the [handoff contract](docs/workflow/HANDOFF.md). Read the supplied ZIP, [current checkpoint](docs/workflow/CURRENT.json) and [STATUS](STATUS.md) before selecting work; reconcile saved observations with live GitHub.

The workflow checks what the current session can actually do. Repository instructions do not install browser tools or guarantee automatic loading. Agents explicitly read the required files, use available subagents, verify the actual change, integrate completed work and resolve its branch.

C261's raw GLB hinge reader and C262's historical handoff are complete in their bounded scopes. [C265](docs/engineering/localized-repair-c265/README.md) adds the bounded independent source hinge observer under unchanged C260, including ordered endpoint identities, literal values and exact byte witnesses; site poses stay unevaluated. Its [task record](docs/workflow/tasks/C265/task.json) identifies actual verification, integration and saved-delivery state. Source/artifact comparison, historical admission, full semantics, native/model trials and comparative advantage remain unqualified. The [C252 roadmap](docs/engineering/review-integration-c252/ROADMAP.md) governs product priorities; the older C251 native-sampling task stays deferred. Current user direction selects the next scope.

## Start reading

The [user-guide index](docs/user-guide/README.md) holds the detailed workflows moved from this README. The [documentation guide](docs/README.md) indexes specifications, adoption records and engineering evidence.

<!-- Preserve links to sections moved into the user guides. -->

<a id="select-sparse-per-key-component-overrides"></a><a id="give-reusable-part-groups-computed-namespaces"></a><a id="pair-named-attributes-with-exact-key-agreement"></a><a id="combine-named-part-groups-with-explicit-collision-refusal"></a><a id="select-optional-keyed-parts-while-preserving-surviving-identities"></a><a id="compute-reusable-construction-parameters-from-keyed-values"></a>
<a id="add-opaque-image-labels-to-native-surfaces"></a><a id="author-recessed-trays-panels-and-housings"></a><a id="author-bent-ducts-and-handles-with-explicit-section-frames"></a><a id="author-tapered-polygon-forms-and-hollow-ducts"></a><a id="author-plates-slots-and-through-holes"></a><a id="author-polygon-plates-and-concave-brackets"></a><a id="export-native-exterior-surfaces"></a><a id="inspect-and-repair-a-native-surface-program"></a>
<a id="configurable-execution-budgets-source-cli-and-agent-workflows"></a><a id="current-development-experimental-planar-reach"></a><a id="apply-source-impulses-and-export-their-motion"></a><a id="apply-finite-force-intervals-and-retrieve-recorded-motion"></a>
<a id="build-an-assembly-from-a-pinned-component-library"></a><a id="author-and-repair-through-the-agent-interface"></a><a id="see-the-animations"></a><a id="export-an-ontokin-program"></a>

| Need | Guide |
| --- | --- |
| Atomic edits, reusable libraries and agent interfaces | [Agent workflows](docs/user-guide/agent-workflows.md) |
| Named groups, overrides, filtering, merging and reduction | [Keyed construction](docs/user-guide/keyed-construction.md) |
| Polygon parts, surfaces, materials and image labels | [Geometry and appearance](docs/user-guide/geometry-and-appearance.md) |
| Impulses, forces, execution budgets and deferred reach | [Motion and budgets](docs/user-guide/motion-and-budgets.md) |
| GLB export, playback and numerical limits | [Export and view](docs/user-guide/export-and-view.md) |
| CLI options, diagnostics and source checking | [Core and CLI](docs/user-guide/core-and-cli.md) |
| Local verification, archive storage and historical design | [Development and scope](docs/user-guide/development-and-scope.md) |

## Language and implementation scope

Source authority, stable identities, units/frames, distinct ownership/following/connections and explicit failure remain central invariants. Recorded animation is sampled output; it does not establish live destination physics. Each supported profile states its own limits and release evidence.

General gameplay, a replacement physics engine, broad syntax, creature/vehicle/fluid systems, model training and simultaneous production backends remain deferred. OpenUSD transport and generated-asset integration are bounded future candidates, subject to the [evidence-first roadmap](docs/engineering/review-integration-c252/ROADMAP.md). [GOAL.md](GOAL.md) owns the current scope; [detailed language limits](docs/user-guide/development-and-scope.md#language-and-implementation-scope) explain existing profiles.

## Verification

Read [AGENTS.md](AGENTS.md) for branch ownership and integration rules. For documentation/navigation changes, run:

```sh
python3 docs/maintenance/reorganization-2026-10-17/verify_reorganization.py
```

Workflow records additionally use `python3 tools/chat_workflow.py check`.

Runtime work uses [the local validation policy](docs/engineering/OK-ENG-006-local-validation-and-hosted-ci-policy.md) and the affected contracts. [Verification details](docs/user-guide/development-and-scope.md#verification) explain the existing local driver, optional visual checks and environment limits. A test result covers only its recorded inputs and executed roles.

<a id="git-lfs-for-engineering-archives"></a>

The [archive storage guide](docs/engineering/OK-ENG-010-git-lfs-archive-storage.md) covers Git LFS requirements and preservation. Historical evidence stays intact when documentation moves.

## About the name

**OntoKin** combines **onto-**, referring to ontology—what exists and how entities relate—with **kin-**, referring to kinematics, or motion. Earlier drafts used *OntoKine*. The [documentation reorganization record](docs/maintenance/reorganization-2026-10-17/reorganization-record.md) preserves the earlier organization and source mapping.
