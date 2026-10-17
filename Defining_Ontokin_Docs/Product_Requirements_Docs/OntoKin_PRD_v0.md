---
project: OntoKin
document_id: OK-PRD-001
title: OntoKin product requirements document
version: 0.2
status: draft-for-product-review
date: 2026-10-16
repository: https://github.com/Omegapy/OntoKin
repository_snapshot: cfadf988e627112e9cf24ad9787d9b861e97d32d
audience: [product owner, language designers, AI coding agents, technical artists, future implementers]
document_scope: product definition and requirements
implementation_status: concept-stage
review_basis: attached OK-PRD-001 version 0.1, current owner brief, repository review, and independently checked primary sources
---

# OntoKin product requirements document

**An AI-native programming language for physical 3D assets, animation, and interactive scenes**

| Document control | Value |
| --- | --- |
| Product | OntoKin, pronounced ON-toh-kin |
| Document | OK-PRD-001, version 0.2 |
| Date | October 16, 2026 |
| Status | Product requirements draft for review |
| Primary use | AI agents creating 3D assets and animation for video games |
| Basis | The product owner's October 16 clarification, the supplied version 0.1 PRD, all repository documentation at the snapshot above, and an independent primary-source review |
| Revision | Existing requirement IDs retained; omissions and conflicting rules corrected. Appendix D records the material changes. |
| Decision boundary | Defines required product behavior. Grammar, implementation language, compiler strategy, engines, and development schedule remain separate decisions. |

## Reading this document

Sections 1–5 define the product and the responsibility it takes away from an AI coding agent. Section 6 evaluates existing work. Sections 7–10 contain the requirements, capability coverage, and acceptance scenarios. The final sections record risks, unresolved decisions, traceability, the repository review, and sources.

The document contains **226 numbered requirements: 213 MUST and 13 SHOULD**, together with **22 acceptance scenarios** and a mapping of **16 owner intentions**. Version 0.2 adds 20 requirements and strengthens existing requirements without renumbering them. MUST describes the complete intended product; it does not imply that every feature belongs in the first prototype.

| Find | Section |
| --- | --- |
| Product meaning and purpose | [1. Product definition](#1-product-definition) |
| Changes from the earlier concept | [2. Repository reconciliation](#2-reconciliation-with-the-existing-repository) |
| What the agent defines and the language supplies | [4. Responsibility contract](#4-the-responsibility-contract) |
| Existing work and possible reuse | [6. Research](#6-research-existing-work-and-its-relevance) |
| Detailed required behavior | [7. Functional requirements](#7-functional-requirements) |
| Performance, reliability, and documentation | [8. Quality requirements](#8-quality-operability-and-documentation-requirements) |
| Full-product scope and supported ranges | [9. Capability coverage](#9-required-capability-coverage-and-product-boundaries) |
| How the product proves its promises | [10. Acceptance scenarios](#10-acceptance-scenarios-and-evaluation) |
| Risks and unresolved choices | [11. Risks](#11-product-risks-and-tradeoffs) and [12. Open decisions](#12-decisions-deliberately-left-for-product-and-language-design) |
| Connection to the original brief | [13. Traceability](#13-traceability-to-the-owners-intent) |
| Repository inventory, terminology, and references | [Appendix A](#appendix-a-repository-documentation-examined), [Appendix B](#appendix-b-working-glossary), [Appendix C](#appendix-c-source-catalog) |
| Review findings and changes from version 0.1 | [Appendix D](#appendix-d-review-findings-and-revision-record) |

**Evidence and authority:** The owner's current description controls the intended product. Repository documents provide prior context; they describe proposals, not implemented features. External sources establish what other systems document or demonstrate. Requirements, capability profiles, and numerical acceptance targets in this PRD are proposed product decisions unless identified as direct owner requirements. They are not measurements of an existing OntoKin implementation.

Source labels beginning with **R** refer to repository documents. Labels beginning with **S** refer to external primary sources. **U** labels in the traceability section identify requirements expressed in the current owner brief. Research was checked on October 16, 2026. Reuse candidates are evaluated as possible foundations; this document does not select dependencies.

## 1. Product definition

### 1.1 What OntoKin is

**OntoKin is an AI-native, physics-based domain-specific programming language for defining, generating, animating, and exchanging modular 3D assets and interactive scenes, primarily for video games.**

An AI coding agent describes what an object is, its dimensions and parts, where and how those parts should attach, its appearance, and what it should do. OntoKin provides reusable physical, mechanical, anatomical, and animation abstractions that turn supported declarations into geometry, articulated structures, movement, and interactions. The resulting assets and scenes can be inspected, simulated, rendered through existing systems, and delivered to game or animation tools.

For example, an agent should be able to define a three-legged creature with a particular body size, skin pattern, limb arrangement, and walking goal. It should not need to derive rigid-body equations, implement contact detection, write a joint solver, paint routine skinning weights, or independently construct a balance controller for every supported creature. OntoKin must supply those capabilities through tested models and reusable behavior systems, within a declared range of support.

The product includes the language's meaning, its standard domain libraries, and the execution and inspection contracts needed to honor that meaning. A syntax alone cannot make a wheel roll or a creature walk. The user-facing promise belongs to the complete OntoKin language system, even when an existing physics engine or renderer performs part of the computation.

At the product level, the language combines declarative object and relationship definitions with reusable functions, classes/types, methods/operations, procedural generation, constraints, and behavior over time. The formal specification must define how these parts interact; this PRD establishes the required capabilities without choosing their grammar or execution strategy.

### 1.2 What the language is for

The primary outputs are reusable 3D assets and animations: creatures, people, machines, vehicles, vegetation, buildings, terrain, and objects made from different materials. Assets must remain meaningful objects with editable parts and behavior. They must be usable individually or as members of a larger scene.

Interactive scenes are part of the product because the same car, animal, or tree must respond to forces, collisions, changing conditions, and game input. A recorded animation is also a valid delivery, provided the product clearly distinguishes recorded motion from behavior that remains active in a destination engine.

Secondary applications include animated film content, simulation demonstrations, procedural environments, and synthetic visual data. These uses can benefit from the same capabilities. They must not displace the main goal of reliable AI authoring for game assets and animation.

### 1.3 What "a renderer for AI agents" means here

From an agent's perspective, OntoKin should be an executable medium for turning a structured description into a visible, moving result. It therefore needs a complete authoring-to-preview experience.

The responsibilities remain distinct:

| Responsibility | Meaning |
| --- | --- |
| Definition | Describe entities, dimensions, materials, parts, connections, physical properties, and intended actions. |
| Generation | Construct geometry, appearance, collision representations, rigs, and other derived content from those declarations. |
| Simulation and control | Calculate physical responses and generate supported purposeful motion over time. |
| Rendering | Turn the current scene into images using cameras, lights, materials, and a rendering system. |
| Delivery | Package editable assets, recorded animation, or supported live behavior for a destination tool or engine. |

OntoKin must own the consistency of this experience. A dedicated graphics renderer is not required to define the product. The existing repository already separates language, runtime, and renderer, and that boundary remains useful. [R01] [R02] [R03]

### 1.4 What "understanding physics and anatomy" must mean

The language must associate a declared concept with inspectable structure and behavior. A leg is a reusable arrangement of segments, connections, contact surfaces, optional actuators, and appearance. A wheel has a radius, axle relationship, rolling contact, and an optional drive or brake. A leaf has shape, attachment, material, and a supported response to wind.

These concepts must carry defaults, constraints, derived properties, and a description of the conditions in which they work. Their names alone cannot establish physical capability. An object with wings might glide, flap, use an engine, or have decorative wings. The author chooses that intent; OntoKin supplies a supported model and exposes its assumptions.

The required abstraction is **declaration of meaningful objects with accountable automatic behavior**. Defaults must be discoverable and replaceable. Unsupported behavior must produce an actionable result rather than silently generating unrelated motion.

## 2. Reconciliation with the existing repository

The reviewed repository is a concept-stage documentation collection. At commit `cfadf988e627112e9cf24ad9787d9b861e97d32d`, it contains the root README, three numbered concept documents, three package READMEs, an HTML edition of OK-003, six diagrams in SVG and PNG form, and three Graphviz diagram sources. The inventory and review details appear in Appendix A.

| Earlier direction | Treatment in this PRD | Reason |
| --- | --- | --- |
| AI-native authoring with human-readable source | Retained and made testable | Agent use is a primary design constraint; people still need to inspect and direct the work. |
| Mathematical descriptions of virtual worlds | Expanded to physical objects and behavior | Mathematics supports the product, while physics, mechanics, anatomy, and reusable animation define its practical purpose. |
| Physics and richer relationships as later extensions | Promoted to central product requirements | These are essential to the owner's current explanation. A language that leaves routine physics setup to the agent would miss the intended abstraction. |
| Interactive sphere as an initial experiment | Retained only as a limited pipeline check | It cannot establish the main value of modular bodies, mechanisms, passive motion, or materials. |
| Separation of language, runtime, and renderer | Retained as a product responsibility boundary | The product must support simulation and output without permanently depending on one drawing system. |
| Typed, inspectable world representation and structured errors | Required as observable capabilities | Agents must inspect and repair individual objects predictably. The internal representation is still an implementation decision. |
| Interpreter first, possible LLVM later | Remains an implementation option | Compiler technology does not define the product or supply its physical meaning. |
| Primitives first, other geometry later | No permanent geometry restriction | Game assets require meshes, imported content, procedural shapes, textures, and deformable surfaces. |
| Human approval and controlled changes | Retained as configurable project policy | Authorized routine agent work should proceed within its declared scope. |
| Exact grammar, extension, engines, and execution machinery | Unresolved | This PRD specifies outcomes and semantics needed from those choices. |

This PRD refines the product definition for future work. It does not rewrite the historical documents or treat their tentative implementation proposals as approved architecture. The spelling **OntoKin** is used consistently. [R01] [R02] [R03] [R04]

## 3. Users, goals, and the importance of AI-native design

### 3.1 Primary and supporting users

| User | Main goal | Product support required |
| --- | --- | --- |
| AI coding agent | Create and revise valid assets from a human brief | Discoverable concepts, precise declarations, bounded edits, inspectable results, useful diagnostics, and predictable defaults |
| Human creator or game developer | Direct the design and decide whether it meets the creative goal | Readable source, previews, clear change summaries, and direct control over important properties |
| Technical artist | Refine shape, rig, materials, and animation; connect existing assets | Detailed overrides, reusable components, import/export, and visibility into generated content |
| Language and domain-library contributor | Add a new object family or behavior without breaking existing content | Stable contracts, versioning, compatibility tests, and documented support limits |
| Game or rendering integration developer | Receive assets and behavior with explicit meaning | Capability declarations, units, identity mappings, playback rules, and a report of conversion losses |

An **authoring agent** is the AI system writing OntoKin. A **simulated character** is an object inside the resulting scene. A character controller may use algorithms or learned policies, but an AI language model does not have to run during every animation frame.

### 3.2 Why targeting agents changes the product

An agent needs to determine what it may create, which inputs are required, what will be derived, and whether the result is correct. Requiring it to reconstruct these rules from long prose or a graphics editor's hidden state would retain much of the original authoring burden.

OntoKin must therefore provide:

1. **A discoverable vocabulary.** An agent can inspect a component such as a leg, wheel, wing, or liquid volume and obtain its parameters, units, attachment rules, defaults, and supported actions.
2. **A reliable editing unit.** The agent can change one limb, material region, or motion goal while preserving other objects and their identity.
3. **Explicit responsibility for derivation.** The system generates routine physical and animation setup from supported declarations and records what it generated.
4. **Feedback about the actual scene.** An agent can inspect joints, contacts, motion sources, materials, and physical state, alongside rendered views.
5. **Predictable failure.** Invalid units, failed physical preconditions, unsupported requested behaviors or physical models for a body plan, and missing dependencies return structured diagnostics.
6. **Repeatable work.** The same source, dependency versions, random seeds, and declared execution configuration can be rebuilt within stated guarantees.

These are product hypotheses to verify against direct scripting of established tools. No reduction in authoring cost or error rate is assumed until comparative tests establish it.

### 3.3 Product goals

| Goal | Observable outcome |
| --- | --- |
| Reduce routine physical authoring | Representative tasks succeed without author-supplied solver code, collision routines, per-joint movement equations, or manual construction of standard controllers. |
| Preserve creative freedom | Nonstandard limb counts, asymmetric parts, hybrid bodies, and unusual appearances remain expressible. |
| Produce useful animation | Purposeful motion, passive motion, collision response, and authored timing can coexist under explicit rules. |
| Keep assets editable | Components, materials, attachments, controllers, and generated content retain identity and provenance. |
| Make results portable | Supported outputs open correctly in named target tools, with explicit records of preserved and lost capabilities. |
| Support accountable agent work | A failed declaration can be diagnosed and repaired through structured feedback; edits can be scoped and reversed. |

## 4. The responsibility contract

### 4.1 What the agent defines and what OntoKin supplies

| Topic | AI coding agent or human author defines | OntoKin must supply for a supported case |
| --- | --- | --- |
| Object meaning | Creature, machine, vehicle, plant, rock, structure, liquid, or a custom combination | A typed object and applicable component contracts |
| Shape | Dimensions, proportions, part counts, attachment intent, imported shapes, or procedural parameters | Generated or adapted geometry and checks for invalid construction |
| Assembly | Which parts belong together and how a part should connect | Resolved attachments, local frames, appropriate joints or flexible connections, and connection validation |
| Physical character | A material or body preset; optional mass, stiffness, friction, or other overrides | Documented physical defaults and valid derivation of omitted properties |
| Appearance | Colors, patterns, surface materials, textures, skin, fur, bark, paint, and region assignments | Supported surface construction, mapping, deformation bindings, and export conversion |
| Active behavior | Walk, turn, reach, grasp, drive, steer, flap, or another supported goal | Compatible movement/control behavior, contact handling, and failure reporting |
| Passive behavior | Which environmental effects apply and the intended realism or stylization | Gravity, wind response, collision response, bending, buoyancy, or other supported reactions |
| External influence | A force, impulse, wind field, current, input command, or environmental change | Application of that influence with consistent units, scope, time, and physical effect |
| Delivery | Target engine/tool, real-time or recorded output, and quality budgets | Validated output, conversion report, dependencies, and the required playback contract |

The agent may override detailed physics or provide custom algorithms. Those are advanced capabilities; they must not become prerequisites for routine use of standard components.

### 4.2 Defaults must be explicit facts about a model

A density preset and valid volume may allow the system to derive mass. A color does not determine density. Dimensions may support an inertia calculation, but a hollow object and a filled object can have the same outside shape and different mass distributions.

Every important value must therefore be identifiable as **authored**, **inherited**, **derived**, **estimated**, or **unresolved**. A documented preset can make ordinary cases simple. It must not conceal ambiguity that changes behavior. Geometry changes must update dependent values or explain why they cannot be updated.

Derivation must also have a consistency rule. If an author supplies volume, density, and mass that disagree under a filled-solid model, provenance alone does not resolve the conflict. OntoKin must apply an explicit mass-override or alternative material-distribution policy, or report the conflicting inputs. It must not silently change the authored shape, material, or number of parts to obtain a solvable model. A hollow shell, a filled solid, and a composite need distinct mass-distribution assumptions where those differences affect the result.

### 4.3 Hierarchy and physical connections are different relationships

An arm belongs to a body and a hand belongs to the arm. That ownership hierarchy is useful for editing and reuse. Physical connections describe another relationship: the elbow permits motion, a hand can contact a separate object, and a mechanical linkage can close a loop.

The product must preserve these distinctions:

| Relationship | Example | Required meaning |
| --- | --- | --- |
| Ownership | Vehicle contains a wheel assembly | Defines composition and lifecycle responsibility |
| Transform relationship | A light is positioned relative to the vehicle | Defines how coordinate frames relate |
| Physical connection | Wheel rotates about an axle | Defines allowed motion and transmitted forces |
| Temporary interaction | Foot touches ground; hand grasps a tool | Defines contact or a changing constraint between independent objects |
| Deformation binding | Skin follows several bones | Connects a visible surface to an articulated or deforming structure |

An ownership hierarchy alone cannot express every physical connection. Closed mechanisms and contacts require relationships beyond the ownership hierarchy. This is a product modeling requirement; it does not prescribe an internal data structure.

The physical articulation and the visible deformation skeleton also need not match one for one. An arm may use extra twist bones to keep its skin from collapsing while still containing only the intended physical segments. Animation controls, deformation bones, and physical bodies must have explicit mappings; adding a visual control must not automatically add mass or a physical joint.

### 4.4 Physical validity and creative control

OntoKin must distinguish three selectable behavior policies:

| Policy | Meaning | Required disclosure |
| --- | --- | --- |
| Physical | Movement follows the supported physical model and its limits. | Model, defaults, numerical tolerance, active forces, and failed constraints |
| Game approximation | Simplified physical behavior is used to meet interaction or cost goals. | Which effects are approximated and where the approximation applies |
| Art-directed | Authored motion or explicit fictional rules can override physical behavior. | Which rules are overridden and how those objects interact with physical ones |

These are proposed product policies, not reserved language keywords. No policy implies exact simulation of reality. Changes between policies must be explicit and inspectable.

### 4.5 Passive motion and purposeful motion

A tree can bend in wind without choosing a goal. A walking creature must coordinate its support, balance, and movement. A car's wheels can rotate under torque, but following a path also requires control decisions.

OntoKin must cover both physical response and supported behavior generation. It must also define how physical simulation combines with keyframes, animation clips, inverse kinematics, and game commands. Inverse kinematics means finding joint poses that place an end part, such as a hand, at a requested location; it does not by itself prove that the full body can balance or generate the necessary forces.

A behavior such as walking must have an input and outcome contract: the target, reference frame, speed or timing intent, supported conditions, completion criteria, and failure response. OntoKin supplies the compatible controller and its connections to body state and actuators. The author can request a destination or a different gait style through supported parameters without constructing the controller's observation vectors or per-joint commands.

### 4.6 Automatic setup has a declared scope

The ordinary authoring path must resolve a complete assembly, not merely recognize the names of its parts. A supported leg, wing, liquid model, and controller can still be incompatible when combined. Before expensive execution, OntoKin must explain which requested capabilities the assembled object can provide in the selected environment and target, what it will generate automatically, and which assumptions or adaptation steps remain unresolved.

Within that scope, the language system owns routine model selection, parameter derivation, attachment and rig construction, controller wiring, initialization, and validation. A failure report is necessary when the request exceeds support, but it does not count as successful automatic construction or movement. An implementation must demonstrate working standard cases as well as understandable failures.

## 5. Representative authoring experiences

The examples below describe required user experiences. They are not finalized syntax or claims of current implementation.

### 5.1 A creature with three legs

The author specifies a torso, three legs with dimensions and attachment locations, two arms, three eyes, a skin material, and a supported walking goal. OntoKin builds an inspectable body structure, resolves the joints, creates a surface that follows the body, applies documented physical defaults, selects a compatible movement system, and tests the requested movement.

Changing the third leg's length must update its shape, affected attachments, collision representation, and relevant movement parameters. If the resulting proportions exceed a controller's supported range, the system must preserve the requested creature and report the movement limitation. It must not silently remove the leg or substitute an ordinary human skeleton.

### 5.2 A modular vehicle

The author selects a vehicle concept, defines a chassis and four wheel assemblies, chooses dimensions, paint, tire appearance, suspension intent, and a driving goal. OntoKin supplies the applicable axle, steering, suspension, contact, and drive behavior.

The author can replace a wheel assembly, add a trailer, or create a six-wheeled variant. Supported combinations must resolve through component contracts. A closed linkage must retain its mechanical meaning instead of being represented only as visually overlapping parts.

### 5.3 A hybrid creature

The author combines an elephant-like body, insect-like legs, wings, and a custom face. Biological category labels must not prevent this construction. Each functional part declares its role and supported mechanics.

Appearance does not establish flight capability. The author can request physical flight using a supported model, a simplified game flight model, or deliberate fictional flight. The system must identify the chosen interpretation and report failed physical preconditions, unsupported capabilities, or unsuccessful motion generation. It must distinguish these outcomes from demonstrated physical infeasibility.

### 5.4 A tree in changing wind

The author defines a rooted tree, branching pattern, leaf shape and distribution, bark, leaf appearance, and a wind environment. OntoKin provides supported flexible behavior for branches and leaves. Wind changes must affect motion according to the declared material and attachment model. The author should not need to animate each leaf separately.

Leaves remain parts of the tree until an explicit detachment rule applies. A decorative motion approximation is acceptable only under a policy that identifies it as such.

### 5.5 A mountain, a building, and water

The author defines a terrain region, a mountain form, a building assembled from reusable components, and water with its material and physical behavior. Rocks and buildings can be static colliders or contain dynamic parts. Water must have the behavior of a supported liquid model, not merely a reflective blue surface.

The same scene must distinguish appearance from interaction: a transparent solid remains solid, and an opaque liquid remains liquid. A floating object must respond to the configured liquid interaction, within the fidelity promised by that profile.

### 5.6 A targeted revision and delivery

An agent changes only the creature's skin pattern, previews the result, and exports an animation. The edit must preserve the body, motion, and physical properties unless the author also changed them. The export must report whether it contains an editable rig, sampled motion, physics data, live behavior, or some combination supported by the destination.

## 6. Research: existing work and its relevance

### 6.1 Findings that affect the product definition

**Reusable physical components are an established language idea.** Modelica connects equation-defined physical components and supports reusable object-oriented models. OntoKin can adopt that principle while serving a different authoring task: creative 3D assets and animation. Its Standard Library is also a source of component interfaces and reference models. [S01] [S02]

**Simulation languages already hide some routine setup.** MuJoCo's MJCF supports nested bodies, defaults, and derived model properties. Its documentation illustrates why domain meaning is still needed above these mechanisms: a solver handles a joint's mathematical configuration without recognizing the anatomical meaning of an elbow. OntoKin's domain components must supply that meaning and its associated constraints. [S04] [S05]

**High-level procedural interfaces can help model-driven authoring, but the benefit depends on the task.** ProcFunc supplies explicit functions and composition for Blender procedural generation. Its material-creation experiments show fewer coding errors, while its parameter-editing error results are mixed. This supports testing the interface idea; it does not establish a general reduction in errors or cost for OntoKin. [S21] [S22]

**Generating a body and making it move purposefully are separate problems.** DeepMimic, MimicKit, and morphology-conditioned control research provide methods for physical character control. Their results support reuse and further investigation; they do not establish a controller that works for every conceivable arrangement of limbs. [S12] [S13] [S14]

**A visible result is insufficient evidence of correct construction.** SimWorlds studies agent-generated dynamic scenes with explicit mechanism checks and runtime-state inspection. This supports evaluating both the visible result and the underlying physical/animation setup. Its reported experiments do not establish OntoKin's performance. [S32]

**An engine accepting a field does not establish that it enforces the field.** Newton's solver matrix documents different supported joint/material properties across backends, including a stored joint-velocity-limit field that its listed built-in solvers do not enforce. OntoKin therefore needs an execution-level meaning and enforcement check, in addition to an export capability matrix. [S36]

**A reusable walking controller needs more than a policy file.** Genesis's locomotion example depends on joint mappings, body-frame observations, scaled actions, update timing, and reset state. These are parts of a controller's contract that OntoKin must resolve for standard bodies. The tutorial itself describes a minimal example, not a production locomotion system. [S38]

**Material behavior depends on its numerical model.** XPBD addresses the dependence of effective stiffness on timestep and solver iterations in traditional position-based dynamics. This supports requiring calibrated material response across supported numerical/detail settings; it does not justify a promise of exact, resolution-independent physics. [S37]

### 6.2 Reuse and precedent matrix

"Integrate" means evaluate existing software as a component. "Adapt" means use a documented modeling or interface pattern. "Reproduce" means implement an algorithm or experimental method with its own validation. None means copying every linked asset, dataset, or trained model without examining its separate terms.

| Existing work | What the source establishes | Potential contribution to OntoKin | Boundary or gap |
| --- | --- | --- | --- |
| Modelica and its Standard Library | Reusable physical components and a formal language specification covering scope, types, functions, connections, events, and initialization. [S01] [S02] [S34] | Adapt component and semantic-contract design; evaluate reference models. | Does not supply the complete creative asset and agent-authoring experience. Adopting its principles does not require selecting its syntax or equation-solving architecture. |
| Scenic | A language for constrained scene distributions and dynamic behaviors, with simulator interfaces. [S03] | Adapt declarative spatial constraints, reusable scenarios, and behavior conditions. | Its scenario-modeling role differs from constructing detailed body anatomy and game assets. |
| MuJoCo / MJCF | Articulated dynamics, model defaults, body/joint structure, actuators, and programmatic modeling. [S04] [S05] | Integrate or use as a reference for physical execution and resolved-model inspection. | Domain-specific anatomy and purposeful control remain responsibilities above the solver. |
| MuJoCo fluid-force models | Approximate forces for moving bodies in a fluid medium without simulating the surrounding fluid state. [S06] | Adapt or use suitable aerodynamic and hydrodynamic approximations. | Drag and lift support does not satisfy flowing-liquid requirements. |
| Jolt Physics | Game-oriented collision, constraints, vehicles, ragdolls, soft bodies, and other physical features. [S07] | Evaluate a reusable game physics implementation for bodies and mechanisms. | Numerical approximations and supported combinations still require explicit product contracts. |
| PhysX Vehicle SDK | Vehicle components encapsulate calculations using parameters, state, and command inputs. [S08] | Adapt the assembly of reusable wheel, tire, suspension, and drive behavior. | A vehicle's external geometry alone does not define its full mechanics. |
| Project Chrono / Chrono::Vehicle | Vehicle subsystem templates define bodies, joints, force elements, topology, and hierarchical parameter files. [S35] | Evaluate integration and adapt wheel/track, steering, suspension, and drivetrain component contracts. | Concrete hardpoints, inertial/contact data, and subsystem choices are still required; OntoKin must supply suitable defaults. Tire/terrain combinations have compatibility limits. [S46] |
| Genesis | Multiple solver families and explicitly documented coupling configurations. [S09] [S45] | Evaluate solid/liquid/deformable execution and supported interactions. | Coupling is specific to model pairs and configuration; listing two material families does not prove they interact. Asset construction, controller compatibility, and game delivery remain separate. |
| Newton / NVIDIA Warp | Newton provides physics models and multiple solver backends; Warp provides lower-level computation. [S36] [S42] | Evaluate integration and adapt explicit feature/enforcement matrices. | Joint/material support differs by backend, and some paths are experimental. The API vocabulary is broader than any one backend's effective support. |
| XPBD | A published method for compliant constraint dynamics with reduced stiffness dependence on numerical settings. [S37] | Reproduce a validated numerical method or integrate a suitable implementation. | A paper is not a complete runtime or a license to copy unrelated implementations; model/contact accuracy still requires testing. |
| OpenSim | Bodies, biomechanical joints, muscles, passive forces, and controlled actuators. [S10] | Adapt anatomy-informed part models and optional detailed biological mechanics. | Ordinary game animation should also support simpler representations; active motion requires control. |
| Drake contact modeling | Inspectable contact models, mass properties, and separate visual/collision geometry. [S11] | Adapt physical validation and documentation of contact approximations. | Compliant contact need not mean the visible body actually deforms. |
| DeepMimic and MimicKit | Physical motion imitation and controller training methods. [S12] [S13] | Reproduce suitable behavior methods or evaluate current implementations and policies. | Training data, computational cost, and supported bodies remain separate dependencies. |
| Morphology-conditioned control research | Control can account for changing body structure and improve transfer within evaluated settings. [S14] | Investigate controllers that use limb roles and body parameters. | Universal behavior for arbitrary fictional anatomy remains unproven. |
| Blender Geometry Nodes and armatures | Reusable procedural geometry and bone-driven surface deformation. [S15] [S16] | Integrate existing authoring/output capabilities and adapt parameterized construction. | The language must avoid dependence on hidden editor selection or fragile tool state. |
| Houdini KineFX/APEX | Procedural character construction, rig components, and retargeting workflows. [S18] | Adapt the separation of body definition, rig construction, and evaluation; consider optional licensed integration. | A proprietary product precedent is not freely reusable source code. |
| Infinigen | Procedural assets and scenes, with a broad generator collection. [S19] | Evaluate reusable nature, architecture, material, and scene-generation components. | Generator coverage does not imply valid behavior for every invented object. |
| Infinigen Articulated | The revised paper describes 18 object categories, reusable articulation utilities, physical properties, and simulator export. [S20] | Particularly close candidate for automated articulated asset construction and export. | The paper leaves coupling between joints as future work. Its demonstrated object generators do not establish support for arbitrary creature anatomy. |
| ProcFunc | Explicit procedural functions, composition, and tracing. The repository contains the primitives API, transpiler, and tracer; its procedural generators are distributed separately in Infinigen2. [S21] [S22] | Adapt inspectable authoring interfaces or evaluate tooling. | Pre-1.0 interfaces and pinned Blender/Python dependencies require version-specific screening. Authoring benefits are task-dependent; physics and movement remain separate. |
| L-systems / Algorithmic Botany | Formal models of plant structure and development. [S23] | Reproduce suitable branching and organ-generation methods. | Structural growth rules alone do not establish calibrated wind response; a declared mechanics or animation model is still needed. |
| GPU Gems procedural tree wind methods | Hierarchical vegetation motion, wind inputs, and simulation detail levels for graphics. [S41] | Adapt or reproduce an efficient vegetation approximation. | The cited method uses stochastic/periodic approximations in place of some force propagation. It supports a disclosed game-approximation profile, not a claim of complete mechanical tree simulation. |
| OpenUSD, UsdPhysics, and UsdSkel | Scene composition plus schemas for common physical and skeletal data. [S24] [S25] [S26] | Evaluate interchange, variants, reusable scene composition, physics metadata, and skeletal delivery. | A schema's representational capacity does not guarantee a target runs its behavior. |
| glTF | A delivery format for 3D content, animation, and declared extensions. [S27] [S28] | Provide explicitly scoped game and viewer delivery profiles. | Export capability depends on supported extensions and the actual importer. |
| MaterialX | Application-independent shading networks, patterns, textures, and assignments. [S29] | Evaluate portable appearance descriptions and material translation. | Appearance graphs do not replace physical material declarations. |
| OpenPBR Surface | A documented common surface-shading model and a MaterialX reference implementation. [S44] | Evaluate material parameters and reference appearance for supported rendering/export profiles. | Specialized shading and target approximations remain explicit; optical appearance does not define friction, mass, or liquid motion. |
| CadQuery / OpenSCAD | Programmatic parameterized solid construction; CadQuery also exposes reusable modeling operations. [S47] [S48] | Evaluate machine/building geometry tooling or adapt source-driven dimensional modeling. | Exact or parametric shape construction does not provide rigging, physical control, or complete game delivery. |
| Alembic / OpenVDB | Computed geometry/animation exchange and sparse volumetric data, respectively. [S30] [S31] | Evaluate recorded deformation and volume delivery. | A recorded result does not preserve the original live solver or authoring recipe. |
| SceneCraft / SimWorlds | Agents can construct editable scenes through executable graphics code; dynamic scenes benefit from structural verification. [S33] [S32] | Adapt authoring, inspection, and evaluation methods. | These systems are precedents for agent workflows, not evidence that the proposed OntoKin language already exists. |
| WorldAgent | A September 2026 preprint describes structured entity contracts and geometry/simulation-state checks for editable physical-world construction. [S43] | Adapt verification questions and evaluate its benchmark method. | Treat results as reported research, not independently reproduced production capability or proof of universal body/controller support. |
| Khronos glTF Validator / destination import tools | Structured format validation and documented target processing of skins, meshes, materials, and animation. [S39] [S40] | Evaluate reusable conformance checks and destination test procedures. | Validator extension coverage is bounded; file validity cannot replace actual importer/runtime verification. |

### 6.3 Reuse constraints that must inform later selection

The reviewed project sources identify Modelica Standard Library, Scenic, Infinigen, and ProcFunc as BSD-3-Clause; Jolt as MIT; Genesis and MimicKit as Apache-2.0. These are useful candidates for further technical screening. The current OpenUSD documentation identifies the TOST license, so a dependency record must use the actual version's license rather than an older generic description. Blender's application license and the terms for generated artwork or data must be considered separately. Houdini remains a licensed product integration or design precedent. [S02] [S03] [S07] [S09] [S13] [S17] [S19] [S22] [S24]

A later dependency decision must examine the selected version, subcomponents, redistribution method, target platform, and the separate terms for models, motion data, textures, and weights. This PRD does not establish license compatibility for a combination that has not been selected.

The added candidates also need version-specific review. The checked top-level license files identify [MuJoCo](https://raw.githubusercontent.com/google-deepmind/mujoco/main/LICENSE) and [Newton](https://github.com/newton-physics/newton/blob/main/LICENSE.md) as Apache-2.0 and [Project Chrono](https://github.com/projectchrono/chrono/blob/main/LICENSE) as BSD-3-Clause. These statements concern the cited code repositories, not every related asset or trained controller. Papers and commercial-tool documentation are algorithm/interface precedents unless an applicable implementation license has also been checked.

Evidence maturity must remain visible during later selection: a normative format describes a data contract; an implementation may provide only a subset; a tutorial proves an example within its configuration; and a research result reports evaluated experiments. Integration candidates must pass OntoKin's own fixtures before they are called supported dependencies. No component was installed or benchmarked as part of this requirements review.

### 6.4 Important interchange findings

OpenUSD supports modular composition and scene data, while UsdPhysics and UsdSkel describe different physical and skeletal concerns. Their existence does not guarantee portable controller execution or equivalent simulation. OntoKin must declare what each export preserves. [S24] [S25] [S26]

UsdSkel can carry skeletons, skin bindings, blend shapes, and skeletal animation, but it does not define a general rigging execution system. An exported animation can preserve completed movement without preserving the controller or constraints that generated it. [S26]

As checked on October 16, 2026, the glTF extension registry lists `KHR_interactivity` as ratified, while `KHR_collision_shapes` and `KHR_physics_rigid_bodies` remain Review Draft. This establishes specification status, not support in a specific engine. The product must negotiate **core format plus supported extensions plus target version**, rather than promise complete behavior from a file extension alone. [S28]

Skin retention also requires more than matching joint poses. glTF specifies linear blend skinning, bind transforms, and the order of morph and skeletal deformation; UsdSkel describes skeletal data rather than general rig execution. The source and target can therefore share joint motion while producing different surfaces. The PRD requires explicit deformation mappings and checks of the deformed mesh. [S26] [S27]

Godot's documented import options illustrate why final target inspection is necessary: options affect skin influences, modifier application, procedural materials, and animation sampling. OntoKin must record those settings and validate the imported artifact. Khronos's glTF Validator is useful for file checks within its stated coverage, but does not establish that a particular game target preserved the intended effect. [S39] [S40]

### 6.5 Research conclusion for product scope

The strongest approach is to reuse established numerical and content-processing capabilities while making OntoKin responsible for their consistent meaning at the object level. The product must add a dependable domain vocabulary, compositional semantics, automatic physical and animation setup, accountable defaults, targeted editing, validation, and delivery guarantees.

The reviewed sources do not demonstrate the entire contract proposed here as one universal solution. That is a finding about this research set, not a claim that no related product or research project exists elsewhere.

## 7. Functional requirements

### Requirement notation

**MUST** means required for the product defined by this PRD. **SHOULD** means a recommended capability whose omission needs an explicit product rationale. These priorities do not assign delivery dates. A requirement can be mandatory for a domain profile without implying that every profile must execute in the earliest prototype.

Every claimed supported capability must meet its requirements and acceptance checks. Releases must publish which profiles are supported, experimental, or unavailable. A roadmap entry is not working support. Section 9 states the required domain coverage; Section 10 defines representative evidence for accepting it.

The acceptance column states an observable check. Detailed test fixtures, tolerances, and resource profiles must be fixed before evaluating a release. Requirements must not be considered satisfied solely because source parses or a single attractive frame renders.

### 7.1 Language meaning and programmability

| ID | Priority | Requirement | Acceptance evidence |
| --- | --- | --- | --- |
| LNG-001 | MUST | Define a formal language for reusable assets and scenes with documented syntax and meaning independent of a particular editor. | A reader can predict a valid example's objects, relationships, and state changes from its specification. |
| LNG-002 | MUST | Provide declarative object, component, material, relationship, constraint, and behavior definitions. | The representative car and creature are declared without manually assembling every low-level engine operation. |
| LNG-003 | MUST | Provide reusable functions with parameters, return values, documented effects, and composition. | A parameterized function creates a limb family and can be used in more than one asset. |
| LNG-004 | MUST | Provide class/type definitions, instances, properties, and methods or equivalent named operations with the same author-facing capability. | Authors define a specialized vehicle and invoke an operation through a documented type contract. |
| LNG-005 | MUST | Support reuse by specialization and by component/capability composition. | A winged machine and a mixed creature can share functional parts without being forced into one exclusive biological taxonomy. |
| LNG-006 | MUST | Support expressions, conditions, iteration, collections, and algorithms needed for procedural generation and bounded behaviors. | One generator creates a chosen number of legs, wheels, or leaves with stable parameterized variation. |
| LNG-007 | MUST | Provide numeric, Boolean, enumeration, vector, rotation, transform, color, reference, and structured-record concepts. | Invalid assignments between unrelated concepts produce type errors. |
| LNG-008 | MUST | Treat physical quantities and their units as checkable language values, including length, time, mass, angle, velocity, force, torque, density, stiffness, and viscosity where applicable. | Valid unit conversions work; assigning length to mass or adding force to distance fails before execution. |
| LNG-009 | MUST | Define coordinate frames, handedness, axes, rotation conventions, and conversion rules. Spatial values and operations must identify their frame or resolve it unambiguously; incompatible frames require a documented conversion. | An asymmetric asset retains orientation and joint axes on import. A body-local force is converted correctly; an ambiguous frame combination is rejected. |
| LNG-010 | MUST | Distinguish definition-time generation, simulation-time behavior, and sampled output evaluation. | A query identifies when a procedural expression runs and whether an edit requires regeneration. |
| LNG-011 | MUST | Provide modules, namespaces, explicit imports, public interfaces, and versioned reusable packages. | Two libraries can expose similarly named parts without ambiguous resolution. |
| LNG-012 | MUST | Define default precedence, specialization rules, and explicit overrides without reliance on hidden mutable editor state. | The same declaration resolves to the same effective defaults in a clean environment. |
| LNG-013 | MUST | Support seeded procedural variation with stable scope and discoverable sampling parameters. Declare how generated element identities and random streams survive supported insertion, removal, or reordering. | Rebuilding one asset reproduces its variation. Inserting a new leaf does not rename or resample unrelated leaves when the generator claims stable keyed elements. |
| LNG-014 | MUST | Allow constraints and assertions over dimensions, assembly, capabilities, and behavior outcomes. | Contradictory dimensions, invalid attachments, and unmet behavioral conditions are identified by object and source location. |
| LNG-015 | MUST | Preserve human-readable source and comments alongside a versioned machine-inspectable representation. Define edit authority and semantic round-trip rules between them; neither may silently diverge from the accepted definition. | A structured edit produces a focused source change with relevant comments retained. Reading, editing, serializing, and rereading preserves meaning and stable object references. |
| LNG-016 | MUST | Separate supported custom extensions from ordinary source execution, and declare their dependencies and effects. | A custom force or generator identifies its interface, permissions, compatibility, and output contract. |
| LNG-017 | SHOULD | Provide formatting, documentation extraction, and a semantic comparison of revisions. | Reformatting does not change behavior, and a comparison can distinguish formatting changes from object changes. |
| LNG-018 | MUST | Specify name binding, scope, value versus object-reference behavior, copying, mutation, function/method calls, and applicable specialization and dispatch rules. These meanings must not depend on undocumented host-language behavior. | Conformance programs distinguish shared references from copies, verify instance-state isolation and method resolution, and report unresolved or ambiguous names. |
| LNG-019 | MUST | Define evaluation order, permitted effects, initialization, and dependency rules for generation, simulation, and output sampling. Cyclic derivations or conflicting state writes require a defined resolution mechanism or a diagnostic. | A generator cannot silently mutate a running scene; a cyclic derived dimension and simultaneous conflicting writes have specified outcomes. Repeated read-only inspection does not advance state. |
| LNG-020 | MUST | Specify numeric precision/ranges, conversion and comparison rules, angle conventions, and handling of division by zero, invalid function domains, overflow, and non-finite values. Invalid physical state must not propagate as a successful result. | Numeric conformance cases have documented outcomes; normalizing a zero vector or passing time directly to an angle-only function cannot silently create invalid scene state. |
| LNG-021 | MUST | Distinguish mandatory constraints, preferences, defaults, and behavior goals, including when each is checked. Satisfy mandatory constraints within declared numerical tolerances; intentional relaxation is permitted only for explicitly relaxable preferences. Report residuals, unmet goals, and unresolved or conflicting mandatory constraints. | A clearance requirement cannot be silently relaxed to fit an object. A permitted numerical residual is distinct from weakening that requirement. Exhausting a placement search is reported separately from proving that no placement exists. |

### 7.2 AI authoring and repair

| ID | Priority | Requirement | Acceptance evidence |
| --- | --- | --- | --- |
| AGT-001 | MUST | Support creation, inspection, validation, simulation, preview, and export without manual GUI operations. | An authorized agent completes the representative tasks through documented programmatic operations. |
| AGT-002 | MUST | Expose a discoverable catalog of types, components, behaviors, material profiles, required parameters, units, defaults, and examples. | An agent can inspect an unfamiliar wheel or limb component before using it. |
| AGT-003 | MUST | Return compact machine-readable diagnostics with stable codes, severity, object identity, source location, relevant dependencies, and a repair direction when known. | The agent localizes and repairs seeded unit, attachment, and capability errors without replacing the whole scene. |
| AGT-004 | MUST | Support scoped create, modify, replace, attach, detach, and remove operations on identified objects or properties. | A requested skin change modifies the intended material assignment while preserving the body and behavior. |
| AGT-005 | MUST | Validate edits against a known source revision and report conflicting concurrent edits. | An outdated patch cannot silently overwrite a newer limb definition. |
| AGT-006 | MUST | Apply a multi-part edit atomically against its declared validation/output level. An invalid edit retains the previously accepted revision. A valid represented or constructed body may be accepted at that level while unavailable animation is reported separately; a higher requested level cannot be silently downgraded. | An invalid wheel replacement leaves no partial accepted change. A valid extra limb can be saved as a body despite unavailable walking support; the old clip becomes stale and cannot pass as animation of the new body. |
| AGT-007 | MUST | Expose effective properties and their origin as authored, inherited, derived, estimated, or unresolved. | An agent can identify which template supplied a joint limit and which geometry produced a mass estimate. |
| AGT-008 | MUST | Describe the consequences of an edit for geometry, rig, collision, materials, controllers, and caches. | A limb-dimension change reports the affected derived products before or during regeneration. |
| AGT-009 | MUST | Provide scene queries by identity, type, role, component, and relationship without relying only on display names. | The agent selects the third supporting leg even after the asset is renamed. |
| AGT-010 | MUST | Return preview images or clips together with structural and numerical inspection results. | A visual preview and a report of joint/contact state refer to the same source revision and simulation interval. |
| AGT-011 | MUST | Support bounded agent work with explicit resource budgets, cancellation, resumable results where supported, and clear failure status. | An expensive generation or simulation stops within its configured budget and retains actionable diagnostics. |
| AGT-012 | MUST | Operate within delegated project permissions and retain reviewable change history. | Routine authorized edits proceed; operations outside the allowed project scope are rejected or routed through the configured approval policy. |
| AGT-013 | MUST | Allow different agent providers to use the same language and contracts. | Valid source and resulting behavior do not depend on one model vendor or conversational session. |
| AGT-014 | MUST | Execute supported ordinary scenes without requiring a language-model call for each frame or simulation step. | A packaged demonstration continues when the authoring agent is disconnected. |
| AGT-015 | SHOULD | Provide examples and conformance fixtures sized for retrieval by agents, with sufficient context for correct use. | An agent can obtain the contract and a complete minimal example for a component without retrieving an entire manual. |
| AGT-016 | MUST | Resolve the capabilities of the complete assembly, requested behavior, environment, physical policy, execution configuration, and target before claiming support. Expose required inputs, selected or eligible models, automatic products, adaptation needs, resource class, and incompatibilities. | Individually valid parts with an incompatible controller or coupling produce a localized preflight result. A compatible combination resolves through standard contracts without manual engine wiring. |
| AGT-017 | MUST | Publish versioned operation/result schemas with revision references, request/job identity, progress and terminal status, cancellation rules, and retry semantics. Retries using the same request identity must not silently duplicate edits, impulses, or expensive jobs; unknown or expired outcomes follow a declared policy. | An agent reconnects after a timed-out request, queries its outcome, and safely retries under the documented contract. A new request identity can intentionally repeat an action. Cancellation cannot be confused with successful completion. |
| AGT-018 | MUST | Support bounded queries and result retrieval by object, property, relationship, time interval, and selected fields, with explicit pagination or continuation when needed. Every result must identify the source revision and relevant run/sample. | An agent inspects one elbow and its dependencies in a large scene without retrieving the entire world; a truncated result is labeled and can be continued consistently. |

### 7.3 Objects, composition, and relationships

| ID | Priority | Requirement | Acceptance evidence |
| --- | --- | --- | --- |
| OBJ-001 | MUST | Give each asset, part, connection, and other independently editable element a stable identity distinct from its display name. | Renaming a forearm preserves references to its hand, joint, material regions, and animation controls. |
| OBJ-002 | MUST | Support nested parent-child ownership with explicit lifecycle and removal rules. | A body contains arms, arms contain segments and hands, and invalid ownership cycles are rejected. |
| OBJ-003 | MUST | Represent ownership, transform relationships, physical connections, deformation bindings, and behavior dependencies as distinguishable concepts. | Inspection can show which relationship makes a wheel belong to a car and which allows it to rotate. |
| OBJ-004 | MUST | Provide named attachment sites with role, orientation, dimensions, compatibility constraints, and connection intent. | A supported leg attaches through its declared body connection; incompatible interfaces return a useful diagnostic. |
| OBJ-005 | MUST | Define how composite transforms affect children and derived representations without unintentionally applying motion twice. Validate uniform/nonuniform scale, reflection, shear, and singular transforms for each affected representation. | Moving a vehicle preserves local articulation. A supported reflection updates geometry orientation, normals, joint frames, and colliders; unsupported shear or zero scale returns an explicit result. |
| OBJ-006 | MUST | Support reusable templates and separate instances with shared defaults and per-instance overrides. | Two creatures use one leg template but can have independent leg dimensions and physical state. |
| OBJ-007 | MUST | Allow arbitrary finite part counts, asymmetric layouts, repeated roles, and custom roles within resource limits. | One-, three-, four-, and six-legged body descriptions are representable without reserved biped-only fields. |
| OBJ-008 | MUST | Support custom composite types combining biological, mechanical, and environmental components. | A robotic limb on an organic body retains its chosen material, joint, and actuation semantics. |
| OBJ-009 | MUST | Express physical links across ownership branches and closed constraint loops. | A four-bar mechanism is represented without duplicating a physical body or introducing a false ownership cycle. |
| OBJ-010 | MUST | Keep semantic categories independent of mobility, actuation, collision, and physical material. | A living tree can be anchored, a nonliving robot can walk, and a human-shaped statue can remain rigid. |
| OBJ-011 | MUST | Define aggregate mass and bounds without counting shared references or visual-only geometry twice. | A composite's reported mass equals the configured physical parts under the documented aggregation rule. |
| OBJ-012 | MUST | Clone or instantiate assemblies while remapping internal references and preserving intentional external references. | Copying a car gives it independent wheels and controls without connecting them to the original car. |
| OBJ-013 | MUST | Link generated meshes, collision representations, skeletons, and material assignments back to their source objects. | Selecting an exported or previewed part can identify the originating declaration through its mapping record. |
| OBJ-014 | MUST | Distinguish authored definitions, initial conditions, current simulation state, and recorded output. | Resetting a simulation restores declared initial conditions without overwriting source parameters. |
| OBJ-015 | MUST | Define attachment and detachment as explicit operations where supported, including their effects on ownership, constraints, state, and caches. | A released object continues under the selected motion policy and no longer follows its former attachment. |
| OBJ-016 | SHOULD | Support instance variants and reversible overrides for collaborative asset refinement. | A visual variant can be removed to restore the base appearance without rebuilding unrelated source. |
| OBJ-017 | MUST | Distinguish changing units or coordinate representation from changing physical dimensions. Physical resizing must update dependent geometry, attachments, mass distribution, colliders, bindings, and control under the declared override policy, or identify unsupported changes. | Expressing one car in centimeters preserves physical mass and motion. Enlarging a wheel changes its physical dimensions and derived properties; explicitly authored mass follows its declared override rule. |
| OBJ-018 | MUST | Distinguish semantic parts, physical articulation, animation controls, and deformation structures, with explicit mappings between them. Auxiliary visual controls or deformation bones must not automatically become massive physical bodies. | A forearm uses extra twist bones while preserving its physical segments, joints, and total mass. Every structure remains traceable to its source parts. |

### 7.4 Geometry and asset construction

| ID | Priority | Requirement | Acceptance evidence |
| --- | --- | --- | --- |
| GEO-001 | MUST | Support parameterized basic solids and editable mesh assets as ordinary geometry sources. | A body can combine generated segments, imported hands, and primitive collision-friendly parts. |
| GEO-002 | MUST | Provide procedural operations needed for repeated parts, curves, sweeps, surfaces, deformation, and shape variation. | A generator constructs a curved tail or branch with attached repeated elements from parameters. |
| GEO-003 | MUST | Distinguish grouping, rigid compounding, surface joining, and geometric union. | Combining parts for visual continuity does not silently remove an intended mechanical joint. |
| GEO-004 | MUST | Support local dimensions, proportions, and attachment-aware shape changes. | Increasing forearm length updates its hand attachment and preserves the intended assembly. |
| GEO-005 | MUST | Import external geometry with explicit units, axes, material references, named regions, and available rig data. | A documented import profile reports missing information and preserves all supported named content. |
| GEO-006 | MUST | Validate geometry for its requested use, including finite coordinates, degenerate elements, orientation, and valid volume where volume-derived physics is requested. | A non-closed mesh cannot silently receive an unreliable volume-based mass calculation. |
| GEO-007 | MUST | Generate or select collision representations suitable for the intended interaction while retaining visible geometry. Validate required openings, cavities, support surfaces, thin features, and mechanical clearances, and expose approximation error. | A detailed creature uses inspectable simpler colliders. A container's collider preserves its intended opening and containment surfaces; a convex approximation that seals the opening fails that interaction profile. |
| GEO-008 | MUST | Support levels of detail and geometry budgets for target assets. | Export checks triangle/vertex counts and preserves designated silhouette, joint, and material requirements within the chosen profile. |
| GEO-009 | MUST | Preserve the generating recipe and its parameters alongside derived geometry when source delivery is requested. | A generated mountain can be regenerated and revised after its mesh has been exported. |
| GEO-010 | MUST | Automatically update dependent regions, rig bindings, colliders, and animation data for supported topology-changing edits; invalidate and report dependencies when regeneration cannot be completed. | Adding a leg within a supported profile produces updated bindings; an unsupported regeneration is reported without accepting stale bindings as valid. |
| GEO-011 | MUST | Allow manual or imported refinements with explicit source authority. Classify generated data as disposable output, an authored override, or an imported/refined source contribution; an unsupported reverse conversion must be marked as detached from regeneration. | Regeneration preserves a supported refinement or reports why it cannot be reapplied. Direct mesh or rig edits cannot be silently discarded or presented as unchanged output of the original recipe. |
| GEO-012 | SHOULD | Support parametric and implicit shape descriptions where they provide useful authoring control, with explicit conversion to supported output geometry. | A mathematical surface retains its source definition and reports approximation tolerance when converted to a mesh. |

### 7.5 Physics and interaction

These requirements apply through declared physical profiles. They require reliable behavior within tested bounds, not exact reproduction of every physical phenomenon.

| ID | Priority | Requirement | Acceptance evidence |
| --- | --- | --- | --- |
| PHY-001 | MUST | Represent motion modes such as static, kinematic, and dynamic separately from structural roles such as rigid, articulated, and deformable, with documented supported combinations and interaction rules. | An anchored wall, a pose-driven door, a falling rock, and a flexible branch behave according to their selected roles. |
| PHY-002 | MUST | Supply gravity, linear and angular motion, and rigid-body response from physical properties without author-supplied integration equations. | A free-fall and a rotating-body fixture meet their profile's reference checks. |
| PHY-003 | MUST | Automatically derive mass, center of mass, and inertia for supported geometry/material distributions. State derivation inputs, filled/shell/composite assumptions, valid ranges, override precedence, and consistency rules for authored values. | Resizing a supported solid updates derived properties. Conflicting mass, density, and volume require an explicit override or a diagnostic; the system does not silently change the authored shape. |
| PHY-004 | MUST | Provide reusable physical material presets, including density, friction, and restitution where relevant, with model-specific property meanings, units, ranges, and provenance. Distinguish volumetric from areal density, material stiffness from joint/contact stiffness, and thickness or section assumptions where relevant. | A material query explains its response model. A cloth refinement preserves total material mass instead of assigning the full mass to every new vertex. |
| PHY-005 | MUST | Detect and resolve supported collisions and contacts, including interaction with terrain and moving objects. | Collision fixtures remain within the declared penetration and response tolerances. |
| PHY-006 | MUST | Define self-collision, connected-part collision, contact filtering, and trigger-only interactions explicitly. | Adjacent body segments do not accidentally fight their own joints, while enabled contacts with the environment remain active. |
| PHY-007 | MUST | Support continuous-motion collision handling or an equivalent declared protection within supported speed/size ranges. | A fast moving object does not pass through a thin obstacle in the profile's required fixture. |
| PHY-008 | MUST | Provide forces, torques, impulses, and fields with units, reference frames, application locations, durations, and scope. | Applying an off-center impulse changes both translation and rotation according to the selected model. |
| PHY-009 | MUST | Provide springs, damping, limits, constraints, and the numerical setup required by standard parts. | A supported suspension or flexible attachment operates without hand-written stabilization equations. |
| PHY-010 | MUST | Define material-pair interaction rules and allow explicit pair overrides. | Contact between two materials resolves to a queryable friction/restitution policy, independent of declaration order. |
| PHY-011 | MUST | Expose meaningful quality settings while automatically supplying routine solver configuration for standard cases. | A standard car or creature can run using a named profile without an agent selecting solver-internal constants. |
| PHY-012 | MUST | Detect structurally invalid definitions and supported incompatible-constraint cases, and monitor invalid initial overlap and numerical instability. Report convergence or feasibility failures with the responsible objects and available context. | Deliberately incompatible or invalid fixtures produce a controlled diagnostic; failure to solve is distinguished from proof that no valid configuration exists. |
| PHY-013 | MUST | Keep physical energy and force sources identifiable and check passive reference systems for unexplained growth within declared tolerances. | A damped passive fixture settles; the report identifies motors, moving kinematic supports, or authored overrides responsible for driven motion. |
| PHY-014 | MUST | Define how explicit motion, forces, and controllers interact when they affect the same object. | A joint cannot receive conflicting authoritative poses and physical controls without a declared resolution policy. |
| PHY-015 | MUST | Report whether interactions between different physical models are supported, approximated, one-way, two-way, or unavailable. | A rigid object interacting with liquid or cloth has a documented coupling result before execution. |
| PHY-016 | MUST | Automatically regenerate affected physical data for supported edits to dimensions, materials, part connections, or motion roles; invalidate and report dependencies when regeneration cannot be completed. | A supported wheel resize updates contact radius and inertia; failed regeneration blocks acceptance of stale physical data. |
| PHY-017 | MUST | Permit explicit changes to world gravity and other supported environment parameters, including fictional settings. | A declared gravity change affects the selected objects and appears in the reproducibility record. |
| PHY-018 | MUST | Provide numerical inspection of pose, velocity, contacts, joint limits, forces where available, and model-specific failures. | A headless run can establish whether an intended physical mechanism was active. |
| PHY-019 | MUST | Verify that the selected execution configuration enforces every required physical property, joint/actuator feature, and interaction. Map it to an equivalent supported meaning, use an explicitly permitted approximation, or report it as unsupported. Storing or forwarding an ignored value does not satisfy the requirement. | A requested limit or coupling unsupported by the selected engine blocks claimed support. A resolved mapping record and a behavior check establish the property actually used. |
| PHY-020 | MUST | Calibrate effective physical behavior across the time steps, solver settings, and geometry/simulation detail levels that a profile claims to support. Preserve declared material meaning within its tolerance or disclose a changed approximation and require the applicable fallback policy. | A supported cloth/branch refinement or time-step change keeps mass, reference deflection, and settling within specified bounds. A setting that changes the model cannot masquerade as a purely visual quality change. |
| PHY-021 | MUST | Define and automatically perform bounded initialization or settling required by standard profiles. Distinguish rest configuration, authored initial conditions, and the state required to start a controller; record preparation and failed initialization. | A supported creature reaches its declared starting state without author-written stabilization. Temporary preparation supports are reported and removed as specified; source geometry and initial intent are not silently overwritten. |

### 7.6 Mechanics and machines

| ID | Priority | Requirement | Acceptance evidence |
| --- | --- | --- | --- |
| MEC-001 | MUST | Provide reusable machine and vehicle abstractions with inspectable part and capability contracts. | A specialized vehicle reuses standard mechanics while allowing a different body and wheel arrangement. |
| MEC-002 | MUST | Provide fixed, hinge, slider, ball-type, and configurable multi-axis connections with frames, limits, and valid defaults. | A door, telescoping segment, shoulder-like connection, and wheel can be expressed through supported contracts. |
| MEC-003 | MUST | Provide actuators/drives with meaningful goals, force/torque output limits, commanded speed limits, damping, and saturation behavior. Distinguish motor commands, physical joint constraints, and monitored operating envelopes; disclose any added forces or pose/velocity projection used to enforce them. | An undersized actuator saturates and reports unmet motion. Commands, applied output, and measured motion are separately inspectable; external loading is not resisted by an undeclared infinitely strong speed clamp. |
| MEC-004 | MUST | Provide wheel and axle components covering rotation, rolling contact, tire interaction, and driven or free-spinning roles. | Drive and brake commands apply torque only to configured wheels; a free wheel can rotate through contact or external forces without receiving drive torque. |
| MEC-005 | MUST | Provide reusable vehicle steering, braking, propulsion, and suspension behavior for declared vehicle families. | The representative car drives, turns, brakes, and traverses its test surface without custom tire or suspension equations. |
| MEC-006 | MUST | Support functional coupling between parts, including gears, rack-and-pinion, pulleys, and linkages in declared mechanism profiles, with ratios, direction, force/torque transmission, and ideal or lossy assumptions stated. | A coupled pair preserves its specified motion relationship and transmits load under the declared model. Matching angles alone cannot establish dynamic mechanical coupling. |
| MEC-007 | MUST | Support closed mechanisms, diagnose supported incompatible-constraint cases, and identify redundant constraints or solver limitations where relevant. | A four-bar fixture moves through its valid range and rejects a contradictory connection. |
| MEC-008 | MUST | Provide reusable rotational and linear mechanism goals independently of a particular appearance. | The same mechanism operates inside visually different machines. |
| MEC-009 | MUST | Treat detachable tools, trailers, and other machine attachments as reusable connected assemblies. | A supported attachment retains its identity, constraints, and state when connected and disconnected. |
| MEC-010 | MUST | Expose dimensions and physical ranges that determine whether a component remains supported after customization. | A modified suspension reports when its requested travel or mass exceeds the tested profile. |
| MEC-011 | MUST | Support alternative locomotion components, including tracked or other declared vehicle mechanisms, without redesigning the language's object model. | A published alternative vehicle profile replaces wheels while keeping the vehicle command contract where compatible. |
| MEC-012 | SHOULD | Provide optional breakage, wear, damage, and failure behaviors through explicit component rules. | A configured break threshold changes the connection state and records the event; unconfigured objects do not fail unpredictably. |

### 7.7 Anatomy, body plans, and creature construction

**Body plan** means the arrangement and functional roles of body parts. It does not require that a creature match an existing species. Biological simulation beyond the mechanics needed for animation is a separate level of detail.

| ID | Priority | Requirement | Acceptance evidence |
| --- | --- | --- | --- |
| BIO-001 | MUST | Provide reusable torso, limb, segment, joint, hand, foot, head, eye, tail, wing, and comparable body-part concepts with explicit roles. | An agent constructs the representative creatures using documented components. |
| BIO-002 | MUST | Allow body plans with nonstandard counts and placement of heads, eyes, limbs, joints, and other parts. | A three-legged, three-eyed creature retains all requested parts through construction, animation, and supported export. |
| BIO-003 | MUST | Allow mixtures of animal, insect, human-like, plant-like, and mechanical components without requiring a single species classification. | A hybrid asset combines distinct part families and remains queryable as one composite object. |
| BIO-004 | MUST | Keep appearance, anatomical role, physical structure, and behavior capability separate. | A decorative wing is valid without flight behavior, and a grasp-capable appendage need not be named a human hand. |
| BIO-005 | MUST | Generate an articulated structure and ordinary joint setup from supported body-part declarations. | The agent specifies limb dimensions and connection intent without authoring every low-level joint frame or constraint equation. |
| BIO-006 | MUST | Supply anatomy-informed default joint ranges, preferred bending directions, segment properties, and contact roles where a profile defines them. | A profile's assumptions are inspectable and can be deliberately overridden for fictional anatomy. |
| BIO-007 | MUST | Generate and validate surface bindings for supported body shapes so visible skin follows the articulated structure. | Representative poses across the declared range preserve surface continuity, regional materials, and the profile's deformation-quality limits. Unbound vertices, invalid references, unintended openings, collapsed regions, or excessive distortion fail the check. |
| BIO-008 | MUST | Support endoskeleton, segmented/exoskeleton, rigid-shell, and supported flexible-appendage representations. | A mammal-like body and an insect-like body can use different deformation models. |
| BIO-009 | MUST | Preserve functional roles when adapting dimensions, proportions, or limb arrangements. | Changing leg length updates attachments and gait-dependent data or identifies a specific adaptation limitation. |
| BIO-010 | MUST | Publish the supported combinations of body plan, dimensions, mass distribution, actuator limits, terrain, and behaviors. | Before requesting motion, an agent can determine whether its creature is supported, requires adaptation, or has no available controller. |
| BIO-011 | MUST | Supply supported locomotion and manipulation behavior without requiring the author to write routine joint torques, balance equations, or gait schedules. | The declared three-legged walking fixture and a reaching fixture execute from high-level goals. |
| BIO-012 | MUST | Allow the same part to participate in more than one declared role when compatible, such as support and grasping. | A creature can use a hand-like appendage at the end of a leg without violating a fixed naming convention. |
| BIO-013 | MUST | Support basic eye, head, and facial movement controls as appearance/animation features independently of full sensory or biological simulation. | A three-eyed creature can direct its gaze through supported controls without requiring a full vision system. |
| BIO-014 | MUST | Preserve a valid custom body when a requested behavior is unavailable, and distinguish unavailable support from a demonstrated physical impossibility. | An unsupported hybrid remains editable and exportable; the diagnostic does not falsely claim its anatomy can never work. |
| BIO-015 | SHOULD | Offer more detailed muscles, tendons, soft tissue, or biological mechanics through optional profiles. | Detailed and simplified bodies expose compatible high-level intent where possible and declare their different costs and assumptions. |

### 7.8 Animation, control, and interaction over time

| ID | Priority | Requirement | Acceptance evidence |
| --- | --- | --- | --- |
| ANM-001 | MUST | Provide animation clips, timelines, named actions, events, and reusable behavior definitions. | An asset can contain multiple named motions and respond to an input that changes the active action. |
| ANM-002 | MUST | Support motion from mathematical functions, keyframes, imported clips, procedural rules, physical simulation, and controllers, with explicit provenance. | Inspection identifies the source of motion for each controlled property or joint. |
| ANM-003 | MUST | Provide forward and inverse kinematic operations for supported articulated objects. | A hand reaches a reachable target; an unreachable target returns a residual or failure with the relevant limits. |
| ANM-004 | MUST | Provide high-level goals for supported behaviors such as move, walk, turn, reach, grasp, drive, and follow a path. | An author requests a destination or action without supplying a low-level control sequence. |
| ANM-005 | MUST | Select, parameterize, generate, or adapt a compatible controller using the declared body and capability profile. | The resolved result identifies its controller, inputs, supported range, and any adaptation performed. |
| ANM-006 | MUST | Coordinate balance, foot or support contacts, and locomotion timing for declared walking profiles. | The three-legged fixture makes progress with every declared support leg participating according to the selected gait, while meeting its support, fall, slip, and joint-limit checks. Physical-mode progress comes from controller actuation and simulated contacts. |
| ANM-007 | MUST | Define transitions and blending between motions, including how position, velocity, contact, and control authority are handled. | A walk-to-stop or animation-to-ragdoll transition has no unexplained pose jump outside its stated tolerance. |
| ANM-008 | MUST | Support retargeting by body roles, proportions, and compatible joint mappings, with a report of unsupported mappings. | A compatible motion transfers to a changed body without silently dropping the third leg or inventing a mapping. |
| ANM-009 | MUST | Provide passive secondary motion for supported tails, ears, cloth, hair, leaves, and similar parts. | The relevant profile responds to body or environment motion while preserving its attachments. |
| ANM-010 | MUST | Define simulation/animation clocks, controller updates, physics substeps, cross-model exchange times, event ordering, pause/resume/reset, and time scaling. Standard profiles supply scheduling, interpolation/holding, delayed-input rules, and bounded handling of repeated zero-time events. | Repeated inputs produce the specified order. A permitted substep change preserves controller timing; a pause causes no time jump and an event cycle cannot run without bound. |
| ANM-011 | MUST | Keep rendering cadence separate from the meaning of simulation and animation time. | Changing preview frame rate does not unintentionally change the declared physical scene speed. |
| ANM-012 | MUST | Support deterministic sampling and declared replay behavior for recorded animation, including random influences. | A clip can be regenerated from recorded settings within its declared reproducibility tolerance. |
| ANM-013 | MUST | Expose body-root movement, local joint animation, looping, and contact markers as distinct animation data where applicable. | A game integration can choose in-place playback or supported root motion without double movement. |
| ANM-014 | MUST | Support behavior interruption, completion, failure, and recovery outcomes. | A blocked reach or unreachable destination reports a state the agent or game can handle. |
| ANM-015 | MUST | Record and export animation over a requested interval, sampling rate, and interpolation policy. | Exported motion duration and sampled poses agree with the validated source within the output profile's tolerance. |
| ANM-016 | MUST | Identify learned-controller dependencies, training/adaptation needs, expected computation, and policy compatibility. | A task requiring new training cannot silently start unlimited work or be presented as immediately supported. |
| ANM-017 | SHOULD | Allow live editing with explicit state-transfer or restart rules. | A supported edit preserves the promised state; unsupported edits clearly restart or request re-evaluation. |
| ANM-018 | MUST | Define each standard action's required roles, input quantities/frames, preconditions, target or trajectory intent, timing, completion criteria, and interruption/failure outcomes. Compatible simultaneous actions require explicit control authority. | A reach request identifies its target frame and tolerance. A walking-and-looking action combination resolves correctly; two incompatible commands to the same joint are diagnosed or handled by the declared policy. |
| ANM-019 | MUST | Give reusable controllers a versioned observation/action contract covering body-role and actuator mappings, units/scales, reference frames, control rate/latency, required observations, internal state, initialization, and reset. Supply routine wiring automatically for standard supported bodies. | Renaming or reordering compatible joints does not redirect actions. A missing observation or incompatible policy produces a localized error; reset restores required controller history as well as body state. |
| ANM-020 | MUST | For a claimed replayable interactive run, retain initial state, timestamped external inputs, environmental changes, random-stream state or equivalent data, and relevant event/control configuration. State whether replay is from initialization or a supported checkpoint and identify missing replay information. | A steering/braking run with a moving obstacle and pause/resume is reproduced within its guarantee. Incomplete input history or incompatible controller state prevents a false replayability claim. |

### 7.9 Surface appearance, skin, and materials

The word **skin** has three relevant meanings: a visible surface, its material/pattern, and the binding that makes it follow an underlying body. OntoKin must expose these meanings separately. A physical material is another independent declaration that can share a convenient preset with appearance without becoming indistinguishable from it.

| ID | Priority | Requirement | Acceptance evidence |
| --- | --- | --- | --- |
| MAT-001 | MUST | Support colors, image textures, procedural patterns, material graphs or equivalent reusable descriptions, and named surface regions. | An agent assigns separate skin, eye, shell, bark, leaf, glass, and painted regions through explicit parameters. |
| MAT-002 | MUST | Provide meaningful appearance parameters for supported shading models, including roughness, metallic response, transparency/transmission, emission, and surface detail. | A preview and target export identify supported values and any material approximation. |
| MAT-003 | MUST | Keep visual material, physical material, visible geometry, and deformation binding independently inspectable and editable. | A color-only change leaves mass, friction, topology, joint limits, and skin weights unchanged. |
| MAT-004 | MUST | Provide reusable material presets with separate visual and physical subcontracts where both are included. | A rubber-like preset exposes which values affect appearance and which affect physical response. |
| MAT-005 | MUST | Support patterns over curved and deforming surfaces using declared mapping coordinates and scale. | A creature's spots and a tree's bark remain attached to their intended surface during supported motion. |
| MAT-006 | MUST | Provide routine texture-coordinate generation or equivalent mapping for standard generated assets. | A standard creature, building, and tree can receive textures without manual per-face authoring. |
| MAT-007 | MUST | Support layered appearance, masks, regional overrides, and reusable variation. | Changing a building's wall pattern does not change its window material or physical structure. |
| MAT-008 | MUST | Support valid skin influences and weights for generated or imported rigs, with repair or diagnostics for invalid bindings. | Every influenced vertex references existing joints and satisfies the binding profile's normalization rules. |
| MAT-009 | MUST | Preserve texture roles/references, color-space interpretation, normal/tangent conventions, mapping, alpha coverage, sidedness, and relevant transmission/thickness assumptions through supported delivery. | A normal-mapped curved surface, thin leaf, and transparent solid retain their intended appearance; flipped normal detail, missing leaf backs, or incorrect transparency are identified separately from allowed renderer differences. |
| MAT-010 | MUST | Identify procedural appearances that need baking or approximation for a selected target. | Export reports the source material, resulting textures or graph, resolution, and known loss of editability. |
| MAT-011 | MUST | Provide appropriate representations for hair/fur, feathers, scales, leaves, or comparable repeated surface elements within their declared profiles. | A profile distinguishes visual-only elements from elements participating in physical secondary motion. |
| MAT-012 | MUST | Permit stylized and non-photorealistic appearances without changing the object's underlying physical role. | A cartoon rock remains a solid collider and a stylized liquid remains a liquid under its selected physical model. |
| MAT-013 | SHOULD | Support appearance changes driven by declared state, such as wetness, wear, seasonal color, or damage. | A state transition changes only the linked appearance and any explicitly coupled physical properties. |
| MAT-014 | MUST | Define reference/rest poses, bind transforms, joint identity mappings, deformation methods, and the order of applicable deformations. Validate these independently of weight normalization; changing a deformation method during delivery requires a report and surface-quality checks. | The bind pose causes no unintended displacement. A twisting limb passes deformed-surface checks before and after export; identical joint motion alone cannot establish equivalent skin deformation. |
| MAT-015 | MUST | Support named morph targets or equivalent surface-deformation channels for declared facial and corrective-deformation profiles, including their combination with skeletal animation and recorded deformation. Preserve them or explicitly report conversion, baking, or lack of support. | A three-eyed character blinks while moving its head, and an elbow correction works during bending. Delivery cannot silently discard the visible expression while retaining the skeleton. |

### 7.10 Vegetation, terrain, buildings, and environment

| ID | Priority | Requirement | Acceptance evidence |
| --- | --- | --- | --- |
| ENV-001 | MUST | Provide reusable plant structures with roots or anchors, trunks/stems, branches, leaves, and optional additional organs. | A parameterized tree retains a meaningful hierarchy through generation and animation. |
| ENV-002 | MUST | Support procedural branching, organ distribution, shape variation, and reusable plant patterns. | A tree's parameters generate consistent branches and leaf attachments with a repeatable seed. |
| ENV-003 | MUST | Supply passive wind response for supported flexible plant components using their geometry, attachment, and material profile. | A standard tree moves under a wind change without per-leaf authored animation. |
| ENV-004 | MUST | Provide wind as an environment influence with direction, magnitude, time variation, and spatial scope. | Two selected plants can experience different declared wind regions and report their applied influences. |
| ENV-005 | MUST | Support anchoring and force propagation through supported plant structures. | The trunk remains attached to its anchor while branches and leaves move within the declared model. |
| ENV-006 | MUST | Define plant detail and motion fidelity separately, including instance-based visual detail and simpler physical representations. | A dense tree can retain detailed leaves while reporting which structures are individually simulated or approximated. |
| ENV-007 | MUST | Provide parameterized terrain, mountain, rock, and ground-surface construction with materials and collision behavior. | A mountain asset can be revised by shape parameters and used as the ground for other objects. |
| ENV-008 | MUST | Support modular buildings with repeated structural and decorative parts, openings, materials, and movable subassemblies. | A building combines floors, walls, windows, and a hinged door without treating all parts as one inseparable mesh. |
| ENV-009 | MUST | Provide placement and spatial constraints for assets, including support, clearance, containment, alignment, and surface attachment where supported. | A building stands on terrain and a tree's root anchor is placed on the declared surface. |
| ENV-010 | MUST | Preserve world scale, local coordinate precision, and stated size limits for environment assets. | A terrain-and-character fixture retains contact and attachment accuracy within the published scale profile. |
| ENV-011 | SHOULD | Support growth stages, seasonal variants, erosion-shaped terrain, or comparable environment evolution through explicit generators or behaviors. | A stage change preserves intended identity or reports the declared topology and cache changes. |

### 7.11 Liquids, deformable solids, and movement through media

| ID | Priority | Requirement | Acceptance evidence |
| --- | --- | --- | --- |
| FLD-001 | MUST | Distinguish physical solid, liquid, and other supported material behaviors from the way their surfaces look. | Transparent-solid and opaque-liquid fixtures retain their correct interaction behavior. |
| FLD-002 | MUST | Provide a liquid profile with a volume or equivalent physical domain, boundaries, initial state, and supported sources or sinks. | An author defines water in a container and can inspect its physical extent and boundary conditions. |
| FLD-003 | MUST | Supply actual liquid motion and containment behavior for the liquid-flow profile, including gravity-driven flow. | Water redistributes under gravity and interacts with a supported container without requiring user-written fluid equations. |
| FLD-004 | MUST | Expose meaningful density, viscosity, and other supported liquid properties with presets and units. | A declared viscosity change produces the profile's expected resistance to flow; the change is not merely a visual material edit. |
| FLD-005 | MUST | Provide supported buoyancy, drag, and current response for interacting objects. | Objects of different configured densities show the required floating or sinking behavior under the reference setup. |
| FLD-006 | MUST | Provide and identify supported liquid-solid coupling, including reaction on dynamic solids in the full liquid-interaction profile. | A moving object affects the liquid and receives the specified reaction; one-way approximations are explicitly labeled. |
| FLD-007 | MUST | Report volume/mass balance, numerical leakage, boundary failures, and invalid liquid states where relevant to the model. | A closed-container test stays within its declared conservation and leakage tolerances. |
| FLD-008 | MUST | Provide deformable-solid profiles with stiffness/compliance, damping, attachment, collision, and visible deformation. | A soft body or flexible sheet changes shape under load and returns or settles according to its material model. |
| FLD-009 | MUST | Support cloth-like surfaces and flexible membranes needed for clothing, wings, leaves, and similar assets. | A supported membrane remains attached and responds to the configured body motion or environment forces. |
| FLD-010 | MUST | Provide declared aerodynamic or hydrodynamic force models for supported flying and swimming assets. | A supported wing or fin produces model-dependent forces; the report distinguishes this from a full simulation of surrounding flow. |
| FLD-011 | MUST | Connect flight and swimming intent to supported actuation and control, including passive gliding and powered motion where offered. | A declared flight/swim fixture runs through a supplied controller and reports capability limits and failed preconditions. |
| FLD-012 | MUST | Offer explicit recorded-output options when the supported simulation exceeds a selected real-time budget. | A liquid or deformable simulation can be evaluated offline and delivered as a recorded result with playback metadata. |
| FLD-013 | SHOULD | Permit additional gas, smoke, granular, phase-change, or multi-liquid models through separately declared profiles. | An extension identifies supported phenomena and interactions; its absence does not silently reinterpret the requested effect. |

### 7.12 Rendering, game delivery, and interoperability

The deliverable must state whether it preserves an editable definition, a rig, a live physical model, an executable controller, sampled animation, or only rendered images. These are distinct outputs with different guarantees.

| ID | Priority | Requirement | Acceptance evidence |
| --- | --- | --- | --- |
| EXP-001 | MUST | Provide an integrated preview path through at least one rendering system while keeping source meaning independent of that renderer. | A valid asset can be previewed with its materials and animation without rewriting its source as editor-specific operations. |
| EXP-002 | MUST | Support cameras, lights, framing, background/environment lighting, and output settings needed to inspect and render assets. | The same source revision produces standard multi-view previews and a requested animation view. |
| EXP-003 | MUST | Deliver standalone assets and scene assemblies with geometry, materials, part identity, and dependencies. | A target can import the requested asset without requiring unrelated objects from its source scene. |
| EXP-004 | MUST | Support a documented skeletal-animation delivery profile for compatible meshes, joints, skin weights, clips, and root motion. | The three-legged fixture plays its animation in a named target while preserving the extra leg and correct skin binding. |
| EXP-005 | MUST | Support recorded deformation and simulation-result delivery where skeletal motion is insufficient. | A liquid or cloth result plays for the recorded interval, with units, sampling, and cache dependencies identified. |
| EXP-006 | MUST | Provide at least one documented game integration that preserves live behavior and physics for a declared profile, including state ownership, inputs, timing, and contact authority. | A delivered vehicle responds to previously unrecorded input and a new obstacle through its declared controller and physical model; one system owns its authoritative motion. |
| EXP-007 | MUST | Publish capability matrices for each format, extension set, exporter, importer/renderer, and version used for supported output, including relevant import/export settings. | Before export, an agent can determine whether the actual target configuration supports a required joint, material, controller, or deformation; specification status alone cannot establish support. |
| EXP-008 | MUST | Produce a conversion report classifying requested features as preserved, approximated, baked, omitted by authorization, or unsupported. | Required unsupported behavior blocks a successful export status unless an explicit permitted fallback is selected. |
| EXP-009 | MUST | Convert units, coordinate conventions, joint frames, material conventions, and timing consistently. | An asymmetric articulated fixture survives a supported round trip within declared tolerances. |
| EXP-010 | MUST | Retain an authoritative OntoKin source package and a mapping to derived output when source delivery is requested. | An exported mesh or clip can be traced to the source asset, parameters, dependency versions, and generation settings. |
| EXP-011 | MUST | Validate budgets on the delivered/imported result after target processing, including geometry counts, material/submesh counts, texture/decoded memory use, joints/influences, animation, instancing, and dependencies where relevant. | Vertex splitting, tessellation, influence reduction, texture baking, or LOD generation cannot conceal a final budget violation. A diagnostic identifies the property and permitted remediation. |
| EXP-012 | MUST | Preserve custom non-humanoid hierarchies unless an explicit target limitation or selected retargeting operation requires conversion. | An export never silently turns a three-legged creature into a two-legged skeleton. |
| EXP-013 | MUST | Demonstrate delivery to at least two independent destination applications or engines across the declared profiles. | The same representative source asset is inspected in an authoring/rendering target and used in a game target with documented retained features. |
| EXP-014 | MUST | Support rendered still images and animation sequences with recorded source revision, camera, lighting, exposure, material model/version, display/view transform, simulation interval, and rendering profile. | A comparison can recreate its viewing conditions and distinguish a changed object/material from changed lighting, exposure, or color interpretation. |
| EXP-015 | SHOULD | Prefer established interchange formats where they meet the required contract, while allowing documented extensions and sidecar metadata. | Each format choice maps to required retained capabilities and has a clear fallback for unsupported semantics. |
| EXP-016 | MUST | Validate file conformance separately from the imported result in the named destination. Record validator coverage, target processing/settings, actual retained semantics, deformed-surface quality, and calibrated appearance checks appropriate to the profile. | A format-valid file with a discarded controller, altered binding, or unsupported extension cannot pass target delivery. Swatches and stress poses expose material or deformation conversion errors. |

### 7.13 Validation and observability

| ID | Priority | Requirement | Acceptance evidence |
| --- | --- | --- | --- |
| VAL-001 | MUST | Validate syntax, references, types, units, defaults, attachment compatibility, and capabilities required for the requested output level before accepting that level. | A negative-test set returns stable diagnostic categories; missing control support blocks claimed movement without invalidating an otherwise valid custom body. |
| VAL-002 | MUST | Validate generated geometry, physical models, rigs, controllers, and dependencies as well as source declarations. | A successful parse cannot conceal an invalid collider or broken skin binding. |
| VAL-003 | MUST | Distinguish invalid input, unsupported capability, unresolved assumption, numerical failure, unsuccessful control, and proven constraint violation. | Each failure class produces a different actionable result rather than a generic build failure. |
| VAL-004 | MUST | Evaluate behavior through structured state checks and visible outputs. | An attractive animation cannot pass a physical fixture when its expected forces, contacts, or solver mechanism are absent. |
| VAL-005 | MUST | Support headless simulation and scripted inspection for conformance tests. | The required benchmark states can be checked without opening a graphics editor. |
| VAL-006 | MUST | Map reported numerical, contact, or controller failures to originating source objects, properties, models, and relevant dependencies. Distinguish directly identified violations from suspected causes or unresolved diagnoses. | A failed contact or controller identifies the involved leg or wheel and its profile; uncertain causal attribution is labeled explicitly. |
| VAL-007 | MUST | Distinguish warnings from blocking errors under a published policy. | A missing optional preview feature can be a warning; missing required physics cannot be silently downgraded. |
| VAL-008 | MUST | Expose the effective scene, its version, and relevant simulation interval consistently to all inspection operations. | Structural, numerical, and visual evidence can be matched without ambiguity. |
| VAL-009 | MUST | Track stale generated data and prevent it from being presented as the result of the current source. | Changing a joint limit marks the affected recorded animation stale until its required reevaluation completes. |
| VAL-010 | MUST | Provide conformance results for each supported component and profile, including known limits and regression history. | A release can show which representative cases passed and which remain unsupported or experimental. |
| VAL-011 | MUST | Establish acceptance from measured generated/runtime/target state and independently specified expected outcomes, not only self-reported metadata or the generator's own success flag. Include controlled perturbations for claimed physical responses. | Changing wind, load, contact, or actuator strength produces the declared effect or a reported limitation. A correctly labeled but inactive mechanism fails; visual review remains a separate check. |

## 8. Quality, operability, and documentation requirements

### 8.1 Nonfunctional requirements

| ID | Priority | Requirement | Acceptance evidence |
| --- | --- | --- | --- |
| NFR-001 | MUST | State reproducibility guarantees separately for source resolution, procedural generation, simulation, and rendering. | A release identifies what is exact, what uses tolerances, and which hardware/backend combinations are covered. |
| NFR-002 | MUST | Record source revision, resolved transitive dependency versions and content identities, assets/controller weights, seeds, profiles, execution settings, and relevant environment information. Pair this with the input/state record required for claimed interactive replay. | A result is rebuilt without an earlier chat session. A changed texture, package, or weights file under an unchanged filename is detected; missing dependencies do not silently resolve to unrelated content. |
| NFR-003 | MUST | Publish supported scene-size, object-scale, coordinate-range, duration, and numerical-precision limits. | Fixtures near declared limits pass or return explicit limit diagnostics. |
| NFR-004 | MUST | Define and measure separate budgets for authoring latency, regeneration, simulation, preview rendering, memory, and export. | A performance report includes the test scene, hardware, configuration, percentile timings, and failures. |
| NFR-005 | MUST | Provide a documented interactive preview profile and an offline profile for more expensive results. | The interactive fixture meets its declared budget; expensive simulations can complete as offline jobs without pretending to meet that budget. |
| NFR-006 | MUST | Bound CPU, GPU, memory, recursion/iteration, generated-object counts, and execution duration where those resources are used. | Resource exhaustion produces a controlled failure and preserves the accepted source revision. |
| NFR-007 | MUST | Isolate generated programs and extensions from unauthorized host resources and network access. | Conformance checks demonstrate that ordinary asset source cannot read unrelated files or execute undeclared host operations. |
| NFR-008 | MUST | Declare supported operating systems, CPU/GPU requirements, external applications, and optional accelerators for every profile. | An unsupported machine receives a capability explanation before a long build or simulation begins. |
| NFR-009 | MUST | Version language semantics, domain models, and delivery contracts, and make compatibility changes explicit. | An updated default or controller cannot silently change an existing pinned project's behavior. |
| NFR-010 | MUST | Preserve recoverable source and useful diagnostics after interrupted generation, simulation, or export. | Cancellation or a failed component does not destroy the last accepted asset definition. |
| NFR-011 | MUST | Track provenance and applicable terms separately for reused code, assets, textures, motion data, datasets, and trained weights. | A delivered package can list its dependencies and identify unresolved provenance rather than implying universal reuse permission. |
| NFR-012 | MUST | Keep source and declared outputs usable without permanent dependence on an authoring-agent vendor or online account. | A prepared ordinary project can be inspected and executed within its published offline capability profile. |
| NFR-013 | SHOULD | Support targeted regeneration and reuse of valid intermediate results. | A material-only change avoids unnecessary rerunning of unchanged physical simulation where the dependency contract permits it. |
| NFR-014 | MUST | Provide human-readable explanations of errors, units, relationships, state, and required decisions. | A human reviewer can understand the affected object and the required decision without reading raw engine logs. |

### 8.2 Product documentation and examples

| ID | Priority | Requirement | Acceptance evidence |
| --- | --- | --- | --- |
| DOC-001 | MUST | Maintain a normative language reference and distinguish it from brainstorming, proposals, and examples. | Every published language feature has a versioned meaning and an identifiable support status. |
| DOC-002 | MUST | Document the normal authoring path in which OntoKin supplies routine physics, mechanics, rigging, and supported control. | The main tutorials do not ask an agent to implement solver equations or manually repair standard joints. |
| DOC-003 | MUST | Publish component contracts with parameters, units, defaults, derivations, constraints, motion capabilities, and tested ranges. | A component's human documentation and machine-readable catalog agree. |
| DOC-004 | MUST | Provide complete examples for the mandatory acceptance scenarios in Section 10. | Each example contains source, dependencies, expected results, known limitations, and a repeatable validation procedure. |
| DOC-005 | MUST | Explain common distinctions: hierarchy versus joint connection, appearance versus physical material, rig versus controller, and recorded versus live behavior. | Tutorials demonstrate the distinctions through observable examples. |
| DOC-006 | MUST | Publish target-specific import/export capability and loss documentation. | A user can choose a delivery profile without assuming every target preserves the whole OntoKin program. |
| DOC-007 | MUST | Preserve requirement-to-example and requirement-to-conformance traceability across releases. | Each required capability has evidence or an explicit unimplemented status. |
| DOC-008 | SHOULD | Include compact diagrams where relationships or execution order are hard to explain in text, together with a text equivalent. | The documentation remains understandable without relying on color or images alone. |
| DOC-009 | MUST | Before marking a profile requirement complete, publish versioned fixtures with parameter ranges, exclusions, preparation, reference scale, duration, measurement methods, and explicit pass/fail criteria. Support-range evidence must include declared boundary and held-out combinations. | Terms such as fall, slip, distortion, settling, leakage, or excessive penetration have measurable fixture definitions. Two favorable demonstrations cannot establish an unrestricted operating range. |

## 9. Required capability coverage and product boundaries

### 9.1 A support profile is a contract

A **support profile** declares the objects, parameter ranges, behaviors, interactions, target outputs, and quality levels that a particular configuration can provide. It must include the component/model versions, required inputs, supplied defaults, supported edits, automatic rebuild behavior, limits, and associated conformance cases.

The following information must be available to an agent and a human reviewer. This specifies the content of the contract, without selecting its eventual serialization or internal architecture.

| Contract area | Required information |
| --- | --- |
| Identity and status | Profile identity/version, dependency identities, implementation and conformance status, supported execution environments, and evidence revision. |
| Inputs and physical meaning | Parameters, units, frames, ranges, defaults, derivations, shape/material assumptions, overrides, and resolution of conflicting authored values. |
| Assembly and changes | Allowed ownership and connection relationships; semantic, physical, control, and deformation mappings; supported edits and automatic dependent updates. |
| Effective physical behavior | Selected model/backend, enforced properties, tolerances, declared approximations, unsupported features, and observable force/state evidence. |
| Actions and controllers | Supplied goals, preconditions and outcomes, body-role requirements, observation/action mappings, authority, adaptation limits, and any initialization or preparation cost. |
| Time and repeatability | Simulation, control, event, and output clocks; scheduling rules; rest and initial states; reset/checkpoint support; logged external inputs; replay guarantees. |
| Combined interactions | Supported model pairs and full-assembly restrictions, coupling direction, contact/filter rules, environmental inputs, and ownership of shared state. |
| Quality and resources | Reference scales, physical and visible detail, material calibration across supported settings, resource budgets, and permitted quality changes. |
| Delivery | Exact target and exporter/importer versions/settings, retained semantics, required extensions or runtime integrations, accepted conversions, and validation coverage. |
| Conformance | Requirement IDs, versioned fixtures, preparation, parameter boundaries, held-out combinations, measurements, acceptance limits, and known failures. |

Profiles are needed because a rigid car, a flexible leaf, a skinned creature, and flowing water do not use identical models. They must not be used to redefine the core request down to a moving sphere or a collection of static meshes.

For all supported standard cases, OntoKin must automatically complete routine setup and supported dependent updates. Invalidating a cache or reporting a missing joint is a legitimate failure outcome; it is not successful completion of a requirement to build or animate the object.

### 9.2 Minimum breadth required by the defined product

| Required area | Required product capability | Minimum representative evidence |
| --- | --- | --- |
| Language and agent workflow | Typed reusable definitions, functions, classes/types, methods/operations, headless inspection, scoped edits, diagnostics, and versioned results | Agent creates, revises, validates, previews, and exports the fixtures without GUI work or hidden state. |
| Modular rigid assets | Composite shapes, physical materials, contacts, forces, and reusable parts | A compound object and a falling/colliding rock with independently editable appearance. |
| Machines and vehicles | Joints, coupled mechanisms, wheels, suspension, steering, propulsion, and braking | An articulated car plus a closed linkage; at least two supported parameter variants. |
| Creature bodies | Custom body plans, extra limbs/eyes, reusable anatomy, automatic articulation, skin binding, and physical properties | A three-legged creature and an insect/mammal hybrid retain their requested structure. |
| Purposeful creature movement | Supplied locomotion and manipulation for a stated range of body parameters | Dynamic three-legged walking using all declared support legs and a supported reach/grasp; no author-supplied gait or torque equations. |
| Flight and swimming | Wings/fins as meaningful components, medium forces, and compatible supported control | At least one physical or explicitly simplified flight case and one swimming case, with capability limits disclosed. |
| Passive vegetation | Branching structures, leaves, anchoring, wind, and flexible response | A tree responds to a wind change and settles under its stated profile. |
| Terrain and structures | Parameterized mountains/rocks, modular buildings, appearance, and interaction surfaces | A textured mountain and a building with a functional moving part. |
| Liquids and deformable solids | Flowing liquid, containment, buoyancy/drag, supported solid interaction, and deformation | A liquid/container/object scene plus a flexible sheet or soft-body scene. Offline evaluation is allowed when declared. |
| Appearance | Regional materials, patterns, textures, mapping, and deformation-aware skin | Material-only revisions preserve mechanics; patterns follow a moving supported surface. |
| Animation and delivery | Clips, timing, transitions, live/recorded distinctions, budgets, and conversion reports | A skeletal asset and recorded simulation work in documented independent targets; a game integration demonstrates live vehicle behavior in response to new input and interaction. |

This is the minimum breadth of the full product definition, not a claim that the earliest prototype can deliver every row. A limited release must say which rows remain unimplemented. A product claim covering the owner's complete vision requires evidence for all rows.

### 9.3 Levels of successful output

An operation must report the requested result and the results it achieved:

1. **Represented:** The requested object and intent are validly described.
2. **Constructed:** Geometry, assembly, and required derived structures were created and validated.
3. **Animated or simulated:** The requested behavior ran under a declared model and met the relevant checks.
4. **Delivered:** The selected target received an output meeting its stated retention contract.

These are capability results, not a mandatory linear pipeline. A static rock can be constructed and delivered without an animation step. A compound request must expose status for each requested behavior and output: a simulation that ran without completing a walking goal has not successfully produced the requested walk.

A represented body may have an unavailable controller. A valid clip may have no live physics in its destination. Valid source, generated geometry, animation, and delivery retain their separate revision/status records. In particular, a valid creative body edit can be accepted at its requested representation or construction level while unavailable control is reported and obsolete animation is marked stale. An operation requesting successful animation or delivery must not silently downgrade that request. An alternative result requires the author's explicit choice or an already-declared project policy. AGT-006 and BIO-014 govern these distinctions.

### 9.4 Scope boundaries

The following are not mandatory claims of this PRD:

- Exact simulation of all real-world physics, all scales, all materials, or every possible interaction.
- Guaranteed stable locomotion, flight, or biological realism for every imaginable body.
- Full cellular biology, cognition, metabolism, medical biomechanics, or material chemistry.
- General engineering certification or proof that a virtual machine can be manufactured or operated safely.
- A new rasterizer, ray tracer, GPU language, or compiler backend built from scratch.
- A complete replacement for a game engine's networking, gameplay systems, audio, user interface, or publishing tools.
- A natural-language-only authoring system, or a language model required during every execution step.
- Mandatory use of a single geometry representation, renderer, physics engine, operating system, or model provider.
- Cross-engine or cross-hardware bit-for-bit numerical identity without a specifically validated profile.

Detailed scientific models, procedural growth, damage, gases, and advanced materials can extend the language through declared profiles. They must not obscure the core game-asset and animation purpose.

## 10. Acceptance scenarios and evaluation

### 10.1 Evaluation principles

Acceptance must show that OntoKin removes the intended work from the author. A demonstration fails the abstraction test if the agent must implement a contact solver, derive routine inertia formulas, hand-configure every standard joint, paint routine rig weights, or invent a new per-joint walking controller merely to complete a supported scenario.

Each fixture must retain its source, dependency versions, parameters, seeds, selected profiles, actual configuration, and expected results. Evaluation must check both normal cases and targeted revisions. Negative cases must demonstrate understandable failure.

Before a fixture can establish conformance, it must define what its qualitative conditions mean in measurable terms: for example, a fall, slip, unacceptable surface distortion, settling, leakage, or excessive penetration. Measurements must use the resulting geometry, state, controller output, or imported artifact, with independent reference expectations; generated labels and success flags alone are insufficient. Declared support ranges require boundary cases and held-out parameter combinations, not only favorable demonstrations. DOC-009 and VAL-011 make these obligations normative.

The scenarios below are mandatory product evidence within the scope defined in Section 9. They are not a development sequence. Numerical gates in Section 10.3 are proposed acceptance targets for review, not measured capability or promises of universal precision.

### 10.2 Scenario catalog

| Scenario | Author input and action | Required system behavior | Evidence and failure conditions |
| --- | --- | --- | --- |
| AC-01: agent discovery and creation | An agent inspects the component catalog and creates a parameterized asset from a human brief. | Supplies defaults, validates source and generated data, previews the result, and records provenance. | Complete programmatic workflow; no required GUI selection, hidden state, or author-written low-level engine setup. Covers LNG, AGT, VAL, DOC. |
| AC-02: modular vehicle | Define a chassis and four wheels with dimensions, appearance, drive/steering intent, and suspension; then change wheel size. | Generates assembly, contact geometry, physical properties, suspension, and drive behavior; updates dependent data automatically. | Drives, turns, brakes, and traverses the fixed test surface within limits. Torque reaches only intended driven/braked wheels. No stale radius or inertia after revision. Covers OBJ, GEO, PHY, MEC, ANM. |
| AC-03: three-legged creature | Define three support legs, a torso, arms, three eyes, dimensions, skin, and a walking goal. | Generates the requested body, articulation, skin binding, physical model, and a compatible controller. | A dynamic fixture traverses the path through actuation and simulated contacts, without an undeclared prescribed root path or teleportation. Each support leg contributes as specified by the gait; contact/load evidence distinguishes support from decorative or dragging parts. No fixture-defined fall or unreported limit violation occurs. Two proportion variants and stress poses satisfy deformation-quality checks. Covers BIO, ANM, PHY, MAT. |
| AC-04: local leg revision | Increase one support leg's length by a fixture-defined amount within the supported range, then change only its visible pattern. | Automatically updates affected geometry, attachments, colliders, inertia, bindings, and controller parameters; preserves unrelated identities and properties. | Revision scope is inspectable; physical dependencies rebuild without manual repair. Pattern-only change leaves physical state definitions unchanged. Undo restores the original accepted definition. Covers AGT, OBJ, GEO, PHY, BIO, MAT. |
| AC-05: hybrid anatomy | Combine an elephant-like torso with insect-like limbs, a nonstandard face, and wings. | Preserves the custom body and supplies all declared supported structures. Reports controller/flight availability separately from representability. | A supported task exercises the hybrid's defining functional parts, such as locomotion using its insect-like limbs. No hidden conversion to a standard biped occurs. Unavailable flight or other movement is diagnosed separately. Covers OBJ, BIO, ANM, FLD. |
| AC-06: reach and grasp | Define a hand or grasp-capable appendage and a reachable tool; request reach, grasp, move, and release. | Supplies the supported pose/control behavior, contact/attachment handling, and release semantics. | The target is reached within tolerance, tool motion follows the declared grasp, and release restores the selected free-body behavior. An unreachable target fails usefully. Covers MEC, BIO, ANM, PHY. |
| AC-07: closed mechanical linkage | Declare a four-bar mechanism or equivalent closed fixture with one driven component. | Resolves ownership separately from the loop constraint and supplies the supported mechanical relationship. | Motion stays within closure and joint tolerances; a deliberately inconsistent variant returns a diagnostic. Redundancy alone is not misreported as physical impossibility. Covers OBJ, MEC, PHY. |
| AC-08: wind-driven tree | Define an anchored tree with branches and leaves; apply a repeatable gust and then remove it. | Generates attachments and passive response without per-leaf authoring. | Branches/leaves move according to the declared model, the root remains anchored, and the passive fixture settles within its defined envelope. Covers ENV, PHY, FLD, MAT. |
| AC-09: solids and liquids | Define a water container with impermeable sides/bottom and an accessible top opening. Choose fill level, freeboard, and disturbances that should not cause physical overflow; release supported objects with known closed geometry, mass, and density. | Supplies liquid flow/containment, task-suitable collision boundaries, and configured object-fluid interaction, including the declared coupling direction. | The generated collision representation preserves the opening and interior. The liquid redistributes after the disturbance, approaches its expected rest state, and shows the declared reaction to objects. Float/sink behavior, mass balance, density/volume deviation, and numerical leakage checks pass separately. Any physically permitted spill/splash is distinguished from penetration through containment barriers. A blue shader without liquid state fails. Covers GEO-007, FLD, PHY, MAT, VAL. |
| AC-10: flexible surface | Attach a supported cloth-like surface or membrane and apply gravity and a declared disturbance. | Generates deformation and attachment behavior under its physical profile. | The surface deforms, remains attached, and meets collision and settling checks. Moving only a rigid proxy while claiming deformable output fails. Covers GEO, PHY, FLD, ANM. |
| AC-11: mountain and building | Generate a mountain with a chosen surface pattern and a modular building with a hinged door. | Creates editable terrain and building components, materials, valid support/collision surfaces, and door motion. | Geometry and material revisions preserve component meaning; a supported moving object interacts with the ground and door. Covers ENV, GEO, MAT, MEC. |
| AC-12: flight and swimming | Select a supported winged body and swimming body; define medium, dimensions, actuator capability, and a movement goal. | Supplies compatible force/control profiles and identifies physical versus game-approximation behavior. | Each published fixture completes its motion under stated bounds. Decorative wings alone do not count as flight; failed motion generation is not labeled proof of impossibility. Covers BIO, FLD, ANM, PHY. |
| AC-13: skeletal game delivery | Export the three-legged creature, its clip, and reference stress poses to the named game target and an independent inspection/authoring target. | Preserves supported geometry, skin, joints, materials, timing, root-motion meaning, and declared deformation quality; reports losses. | All requested legs remain visible and animated. Imported surfaces meet bind-pose, bending, twisting, contact, and interpolated-pose quality checks; matching joint samples alone is insufficient. Unsupported controllers are explicitly identified; no implied live physics from clip playback. Covers EXP, MAT, ANM; AC-21 extends surface and material evidence. |
| AC-14: simulation-result delivery | Evaluate the liquid or flexible fixture offline and deliver its recorded result to the stated target. | Produces a replayable cache or equivalent output with time range, units, source, and dependencies. | Replay matches the accepted samples within output tolerance and is labeled as recorded simulation. Covers FLD, EXP, NFR. |
| AC-15: failure and repeatability | Introduce incompatible units, an unknown part, an invalid attachment, an excessive budget, and an unsupported target feature; repeat a valid case. | Returns correct failure classes, retains the accepted revision, and reproduces the valid result under its guarantee. | No partial accepted edit, silent downgrade, or stale-data success. Source and generation replay checks pass. Covers LNG, AGT, VAL, NFR. |
| AC-16: live game behavior | Deliver the supported vehicle to a named game target. After execution begins, send previously unrecorded steering/braking input and introduce a moving obstacle. | Executes the declared controller and physical model with explicit input, timing, and state ownership. | The vehicle responds to new commands and obstacle interaction within its profile. Recorded clip playback alone cannot pass. Only one system owns authoritative motion, and response latency is measured. Covers EXP-006, MEC, PHY, ANM, NFR. |
| AC-17: language and agent protocol | Exercise reference/copy behavior, scoped names, method dispatch, dependencies, units/frames, constraint residuals, and numeric failures. Reconnect after an operation times out and inspect a large asset through scoped queries. | Applies the published language semantics, preserves source/structured meaning, diagnoses forbidden cycles and invalid values, and returns revision-consistent query pages and job status. | No hidden simulation advancement during inspection, silent frame conversion, or unreported mandatory-constraint relaxation. A retry with the same request identity causes at most the declared single operation; a new identity can request another. Expired or unknown outcomes and cancellation follow the stated contract. Covers LNG-009, LNG-015, LNG-018–LNG-021, AGT-017–AGT-018. |
| AC-18: edit acceptance by requested result | Add a structurally valid limb outside the current controller's support range, first requesting a valid body definition and then successful walking. Separately submit a malformed attachment edit. | Preserves the valid requested anatomy at the appropriate accepted stage, reports unavailable control, invalidates affected animation, and rejects the malformed edit atomically. | A valid body is not discarded merely because walking is unavailable; an old clip is not attributed to the new body. The walking request does not succeed by silently returning only geometry. No partial invalid source is accepted. Covers AGT-006, BIO-014, GEO-010, VAL-009, and Section 9.3. |
| AC-19: physical and controller enforcement | Request a backend-unsupported physical property, overload a bounded actuator, reorder equivalent joint declarations, and request a supported action with valid and invalid preconditions. | Preflights the complete assembly, resolves actual property enforcement, supplies stable body/controller mappings, and exposes goal status, applied outputs, saturation, and any explicit approximation. | An accepted-but-ignored backend field cannot pass as implemented behavior. Required motion is measured against the goal; saturation or an unmet precondition is diagnosed. Reordering does not redirect actuation to another limb, and incompatible observation/action conventions fail before execution. Covers AGT-016, PHY-019, MEC-003, ANM-018–ANM-019, VAL-011. |
| AC-20: scaling, materials, and initialization | Convert the same asset between units; physically resize a separate copy; provide conflicting mass/density inputs; and vary a supported cloth fixture's resolution and time step. Generate its initial simulation state automatically. | Preserves physical identity during unit conversion, recomputes dependent properties during physical resizing, resolves or reports conflicting inputs, and supplies calibrated material response and bounded initialization. | Reference lengths, mass, inertia, and deformation agree with the declared assumptions/tolerances. Supported nonuniform transforms follow stated semantics; unsupported transforms produce diagnostics. Refinement does not multiply cloth mass or silently change calibrated stiffness. Rest, initial, and controller-ready states and initialization cost are recorded. Covers OBJ-005, OBJ-017, PHY-003–PHY-004, PHY-020–PHY-021, NFR-002. |
| AC-21: deformation and imported appearance | Create an asymmetric articulated arm with supported auxiliary deformation controls and a facial or corrective shape deformation; combine it with skeletal motion and deliver to the chosen targets. | Maintains distinct physical and deformation structures, supplies bind/rest data and the declared deformation order, and preserves or explicitly converts supported appearance and deformation features. | Auxiliary twist/facial controls do not add unintended physical mass or joints. Imported surfaces satisfy silhouette, volume, penetration, texture, normal/tangent, transparency, and morph checks in specified stress poses and between keys. Final imported geometry, skin influence, material, and animation budgets pass; validator results and untested features are reported separately. Covers OBJ-018, MAT-009, MAT-014–MAT-015, EXP-007, EXP-011, EXP-014, EXP-016. |
| AC-22: composed scene and interactive replay | Assemble independently generated vehicle, creature, tree, and terrain assets under a supported scene profile. Apply new commands and a timed wind change, revise one local part, then replay the recorded inputs. | Resolves units/frames, clocks, contacts, controller authority, environment effects, dependency updates, and input history for the combined scene. | Supported cross-object interactions work together; unrelated identities and properties survive the local revision. Replaying the same accepted revision, configuration, and input sequence reproduces behavior within the stated guarantee. Missing input history or an unsupported model pair is reported before claiming reproducibility or support. This fixture does not require every fluid/deformable model to run live together. Covers AGT-016, ANM-010, ANM-020, NFR-002, and the profile contract in Section 9.1. |

### 10.3 Proposed measurable gates

These values make the proposed contract concrete. They require product-owner review and fixture calibration before becoming release gates. They are intentionally attached to named controlled tests. Changing a target after seeing a result must be recorded as a requirement change.

| Area | Proposed gate | Measurement conditions |
| --- | --- | --- |
| Requirement coverage | Every MUST requirement has an identified conformance case or is explicitly listed as unimplemented for a limited release. | Coverage is by requirement ID and claimed profile, not by marketing category. |
| Scoped edit integrity | Zero unintended changes to protected source properties and stable IDs in the targeted-edit fixtures. | Compare accepted revisions semantically; derived changes are allowed only through declared dependencies. |
| Default traceability | 100% of physical and controller parameters required for the requested execution stage resolve to authored, inherited, derived, or documented estimated values before that stage succeeds. | Unresolved values required for simulation or control block successful execution of that stage; they do not invalidate an otherwise valid represented or constructed asset. |
| Source replay | Exact equivalence of resolved definitions and selected seeded parameters on the same pinned build and environment. | Simulation and rendered-image results have separate tolerances. |
| Basic rigid-body reference | Free-fall displacement error no greater than 1% of the analytic displacement over the defined pre-contact interval. | Uniform gravity, zero drag, known initial conditions, and fixed fixture duration; do not apply this threshold to all simulations. |
| Kinematic target accuracy | End-part position error no greater than 1% of specified limb reach for reachable reference targets; a separate angular tolerance applies when orientation is requested. | Publish the comparison frame, constrained degrees of freedom, and joint limits. Equivalent rotation representations compare as the same orientation. Force/balance validity is evaluated separately. |
| Mechanical closure | Loop-closure position residual no greater than 0.5% of the reference mechanism's characteristic length. | Publish a separate angular tolerance and test the full required operating interval. |
| Locomotion outcome | AC-03 completes a 10 m level-ground route within its declared duration without a fixture-defined fall or unreported limit violation. Each support leg contributes according to the gait profile. | Test at least two proportion variants and three controlled seeds/initial conditions. Require at least one dynamic physical fixture with controller actuation and simulated contacts; no undeclared root trajectory, teleportation, or pose override supplies progress. |
| Liquid balance and containment | For the constant-density liquid fixture, total mass-balance error is no greater than 2% of initial liquid mass over 10 s, after accounting for sources and sinks. Unintended passage through containment barriers must also meet a separately specified leakage limit. | Record mass outside the intended containment domain independently of total mass balance; distinguish numerical leakage from physically permitted spill/splash. Report volume/density deviation using a defined method; publish the leakage tolerance before testing. The gate applies only to this calibrated profile. |
| Export pose retention | Sampled joint orientations within 1 degree and root positions within 1 cm of the accepted meter-scale skeletal fixture. | Same sample times, known coordinate conversions, documented interpolation and root-motion policy. |
| Surface and target retention | All fixture-defined surface, material, morph, and final imported budget checks pass in the named target versions. | Publish stress poses, inter-key sample times, reference views/measurements, allowed conversions, and tolerances; a joint-pose match or format-validator pass alone is insufficient. |
| Effective physical and control behavior | Every requested field required by the fixture is enforced, explicitly mapped/approximated under the selected policy, or rejected as unsupported. Controller goals and applied outputs meet the fixture's separate success criteria. | Exercise unsupported-field and actuator-saturation variants; compare actual state and outputs against independent expectations. Merely storing a field or running a controller does not pass. |
| Material and initialization consistency | Unit conversion preserves physical meaning, and supported detail/time-step changes remain inside the profile's published material-response tolerance. Automatic setup reaches its declared valid initial state within the allowed cost. | Record characteristic scale, mass/inertia assumptions, resolution, time step, rest/initial state, preparation method, and tolerance before evaluation. Changes outside the calibrated range require a capability result. |
| Interactive replay | Recorded external commands and environment changes reproduce the fixture within its separately published replay tolerance on the pinned configuration. | Log input timestamps, ordering, scheduling, random state, revisions, and relevant configuration. State whether replay restarts from initial conditions or a supported checkpoint. |
| Interactive preview | Initial goal: 95th-percentile presented frame time no greater than 33.3 ms for a published reference scene and hardware configuration; 16.7 ms is desirable. The dynamic fixture must also maintain its declared simulation-to-wall-clock rate and maximum permitted lag. | Fix resolution, materials, scene size, simulation detail, warm-up, and measurement interval. Report command-to-visible-response latency and frames repeated because simulation updates were unavailable. Offline liquid evaluation is measured separately. |
| Invalid input handling | All cases in the required negative-test set return the expected diagnostic class without accepting a partially invalid revision. | Include unit/type errors, attachment conflicts, resource limits, stale edits, and export incompatibility. |

There is no general claim that all scenes will run at these rates or all physics will meet one universal accuracy figure. Before engineering evaluation begins, every incomplete fixture definition in this table must be resolved into a versioned test description.

### 10.4 Test whether the language helps agents

The central value proposition requires a comparison against direct scripting of a selected established tool. Use the same asset tasks, agent models, input briefs, resource limits, and evaluation criteria for both approaches. Document tool access and supplied resources for each route. Include unseen proportions, compositions, and local revisions so the result cannot be explained only by memorizing the demonstration assets.

Measure task-completion rate, invalid-program rate, repair attempts, human intervention, authoring time, model/tool cost, size of the authored change, unintended edits, and retained export functionality. Record visual review separately from structural and physical correctness.

Account separately for reusable platform preparation and task-specific preparation. Record any human-built template, rig, controller, trained policy, motion data, or manual asset repair that a route depends on, including its preparation cost and tested scope. Then measure the marginal work needed for new assets and revisions. An OntoKin wrapper around a hand-prepared answer to each evaluation task cannot establish the promised general authoring benefit.

A useful result must show improvement in authoring or repair without hiding lost capability, lower quality, or additional manual preparation. Any claimed percentage improvement must come from this evaluation; this PRD does not assume one.

## 11. Product risks and tradeoffs

These risks guide product decisions and evaluation. They are not reasons to transfer the normal authoring burden back to the agent.

| Risk or tradeoff | Consequence for the product | Required response and evidence |
| --- | --- | --- |
| Broad scope across creatures, vehicles, vegetation, and liquids | A visually impressive subset could be presented as if it fulfilled the whole product. | Publish coverage by domain and profile; retain the full-product definition in Section 9. Every limited release identifies unfinished requirements. |
| Confusing physical simulation with purposeful movement | A valid articulated body may fall, remain still, or fail a goal despite having correct joint physics. | Evaluate supplied control separately from articulation. AC-03, AC-06, and AC-12 require successful actions, not only simulated bodies. |
| Generalizing movement to unusual bodies | Reusable parts can represent a body beyond the tested range of an available controller. | Keep representability separate from behavioral support. Publish parameter ranges and adaptation limits; preserve valid creative definitions when a behavior is unavailable. BIO-010, BIO-014, ANM-005, ANM-016. |
| Excessive reliance on hidden defaults | The same word could produce surprising mass, joint limits, or movement after a library update. | Expose effective defaults and provenance, pin versions, and make overrides inspectable. LNG-012, NFR-002, NFR-009. |
| Appearance mistaken for physical behavior | A blue surface can be called water, or visible skin can conceal missing deformation and collision data. | Inspect the actual material model, geometry, bindings, forces, and state. MAT-003, FLD-001–FLD-007, VAL-002–VAL-004. |
| Independent components fail when combined | Individually working fluid, rigid-body, soft-body, and controller models may have incompatible time steps, mappings, or coupling assumptions. | Preflight and validate complete scenes; report supported pairs, coupling direction, timing, and authority. AGT-016, ANM-010, ANM-019, FLD-006, EXP-006, AC-09, AC-19, AC-22. |
| Declared behavior is present only as metadata | An engine can accept a parameter without enforcing it, or a controller can run without achieving its goal. | Inspect effective backend behavior and action outcomes using independent state measurements and negative variants. PHY-019, ANM-018, VAL-011, AC-19. |
| Local creative changes break derived content | Resizing or replacing a part can leave obsolete attachments, inertia, skin bindings, controllers, or exported clips. | Automatically rebuild supported dependencies and block stale success. GEO-010, PHY-016, VAL-009, AC-04. |
| Fidelity competes with interactive cost | Detailed geometry, contacts, deformation, and liquid flow may exceed the preview budget. | Separate visible detail, physical approximation, interactive preview, and offline output. Publish measured budgets and quality settings. NFR-003–NFR-005, FLD-012. |
| Artistic freedom competes with strict physical interpretation | A desired animation may need intentional forces, stylized proportions, or fictional behavior. | Allow explicit physical, game-approximation, and art-directed policies. Preserve the author's choice and expose overrides instead of silently altering the model. Section 4.4; PHY-014, PHY-015. |
| Interchange loses executable meaning or surface quality | A destination can retain joint samples while changing skin deformation, or preserve visible motion while discarding constraints and controllers. | Evaluate actual imported surfaces, behavior, and budgets in the target version. Keep source and conversion records; require explicit fallback choices. MAT-014–MAT-015, EXP-004–EXP-016, AC-13, AC-14, AC-21. |
| An agent optimizes only the preview image | A convincing render could mask broken topology, missing limbs, unsupported physics, or unstable animation. | Match visual evidence to structural and state checks for the same revision and interval. AGT, VAL, Section 10.4. |
| Reuse is mistaken for an approved dependency | A paper or open repository can have incompatible terms, separate asset rights, incomplete export, or untested assumptions. | Record exact versions and provenance; validate technical and distribution suitability before selection. NFR-011 and Section 6.3. |

The most important tradeoff is the range of automatic behavior that a release can support reliably. The product should expand that range through tested reusable models while keeping the declared object vocabulary and extension mechanisms open to new forms.

## 12. Decisions deliberately left for product and language design

The requirements above define the desired product. The following decisions remain open because the owner has asked to establish the language's purpose and requirements before deciding how to implement it. The suggested starting positions are proposals, not selected architecture or an implementation schedule.

| Decision | Constraint already established | Suggested starting position for later evaluation |
| --- | --- | --- |
| Source syntax and authoring notation | Formal, human-readable, agent-inspectable source must support reusable declarations and algorithms. | Evaluate concise typed declarations with explicit units and named operations against the representative agent tasks. Do not freeze a grammar from illustrative pseudocode. |
| Formal semantics and agent operations | Binding, identity, effects, evaluation order, numeric behavior, constraints, and versioned operation results must have unambiguous meaning. | Resolve the choices identified by LNG-018–LNG-021 and AGT-017–AGT-018 in a normative language/API specification. Do not assume that choosing a host language supplies these answers. |
| Class specialization and component composition | Functions, types/classes, instances, properties, methods/operations, and modular reuse are required. Hybrid objects must remain expressible. | Use composition for independent capabilities and allow specialization for useful shared defaults. The precise inheritance and dispatch rules need a separate language specification. |
| Standard object and behavior vocabulary | The primary author should request meaningful parts and actions. Their implementation details should be supplied. | Start vocabulary design from the acceptance assets: body, leg, joint, wheel, chassis, branch, leaf, solid, liquid, material, and supported movement goals. Names and signatures are not yet fixed. |
| Default physical interpretation | Every model must state assumptions and preserve explicit creative intent. | Use documented game-oriented physical defaults for ordinary assets, with separately selected stricter or art-directed profiles. Decide the exact default policy before normative examples are published. |
| Controller support and adaptation boundaries | Supported locomotion and manipulation must be supplied; unusual bodies must not be rejected solely because their anatomy is unfamiliar. | Define measurable parameter ranges for the required three-legged case and hybrid demonstrations. Decide how new-controller generation is exposed and costed without assuming an agent writes low-level control. |
| Physics and geometry engines | OntoKin owns the declared behavior even if external tools perform computation. | Evaluate candidates against requirements and combined interaction fixtures. Do not select a system merely because it can display an asset or simulate one class of objects. |
| Runtime and compilation approach | Source meaning, validation, execution timing, inspection, and delivery must have stable contracts. | Compare interpreter, compilation, intermediate representation, and host integration options later. Existing repository proposals remain inputs to that evaluation. |
| First supported destinations | The full product needs demonstrated delivery across independent authoring/rendering and game targets. | Name the initial target applications and exact versions, then define retention matrices and tests. A format specification alone cannot serve as an integration acceptance test. |
| Liquid and deformable fidelity | Actual liquid flow, a meaningful solid interaction profile, and visible deformation are required. | Choose finite, testable scale, material, boundary, and coupling ranges. Determine which cases require offline evaluation and what results can remain live in game targets. |
| Hardware, budgets, and acceptance fixtures | Performance, physical accuracy, deformation quality, and support claims must attach to versioned fixtures and environments. | Complete DOC-009 and calibrate Section 10.3 before release evaluation, including measurement methods, negative cases, support boundaries, and held-out combinations. Publish both successful results and tested limits. |
| Distribution, dependency policy, and project license | Reused code, generated assets, data, and trained policies need explicit provenance. | Select the project's distribution model and license before adopting dependencies for redistribution. The reviewed repository does not yet contain a license file. |
| Standard-library governance and compatibility | Domain assumptions and behavior can change the meaning of existing source. | Define package ownership, semantic versioning policy, conformance evidence, and migration expectations before third-party libraries are treated as stable. |

These choices may change the implementation strategy. They must not silently remove the owner-facing contract that OntoKin supplies routine physics, mechanics, rigging, and supported movement from meaningful declarations.

## 13. Traceability to the owner's intent

This table paraphrases the current brief. It separates the owner's requested outcomes from the supporting product requirements added to make those outcomes precise and testable. Requirement families refer to the tables in Sections 7 and 8; numbered scenarios refer to Section 10.

| Intent | Owner's requested outcome | Coverage in this PRD | Representative evidence |
| --- | --- | --- | --- |
| U01 | Define OntoKin as a programming language before discussing implementation. | Sections 1–4 and 12; LNG-001–LNG-021 | A coherent language and responsibility contract, including semantic conformance in AC-17; implementation choices remain explicitly open. |
| U02 | Make AI coding agents the primary users. | Section 3; AGT-001–AGT-018; VAL; DOC | AC-01, AC-15, AC-17, and AC-18; comparative authoring and repair evaluation. |
| U03 | Create reusable 3D game assets and animations that rendering programs can consume. | Sections 1.2–1.3; GEO; ANM; EXP | AC-13 and AC-14 in actual independent destinations; AC-16 verifies live game behavior. |
| U04 | Base the language heavily on physics, mechanics, and algorithms, while removing routine physical implementation from the agent. | Section 4; LNG-006, LNG-008; PHY; MEC; FLD; DOC-002 | AC-02, AC-03, AC-07, AC-08, AC-09; abstraction checks in Section 10.1. |
| U05 | Offer reusable functions, methods, and classes, such as machine and vehicle concepts. | LNG-003–LNG-006, LNG-011–LNG-012, LNG-018–LNG-019; OBJ-006; MEC | Parameterized reusable parts and a specialized vehicle in AC-01 and AC-02; language semantics in AC-17. |
| U06 | Make parts modular and preserve parent-child relationships: a hand belongs to an arm, an arm to a body, and wheels to a car. | Section 4.3; OBJ-001–OBJ-009, OBJ-012–OBJ-018 | AC-02, AC-04, AC-06, AC-07, and AC-21; ownership, physical connections, and deformation remain distinguishable. |
| U07 | Understand machines, moving parts, joints, wheels, and their interactions. | MEC-001–MEC-012; PHY; ANM-004–ANM-005 | A vehicle, grasping mechanism, and closed linkage in AC-02, AC-06, and AC-07. |
| U08 | Provide anatomy and mechanics for animals and people, including joints, legs, arms, hands, and skin. | BIO-001–BIO-014; GEO-010; OBJ-018; MAT-005–MAT-008, MAT-014–MAT-015; ANM | AC-03, AC-04, AC-06, AC-19, and AC-21; articulation, bindings, contact, and compatible control are supplied. |
| U09 | Permit creative anatomy: three legs, extra eyes, and insect/human/elephant hybrids. | OBJ-007–OBJ-008; BIO-002–BIO-004, BIO-010, BIO-012–BIO-014; EXP-012 | AC-03, AC-05, and AC-13; requested parts survive generation and export. |
| U10 | Let the agent choose dimensions, appearance, skin, textures, colors, and patterns. | GEO-001–GEO-004; MAT-001–MAT-015; AGT-004; BIO-007; OBJ-017 | AC-04, AC-11, AC-20, and AC-21; targeted visual changes preserve unrelated physical definitions and delivery retains the promised appearance. |
| U11 | Represent living and nonliving things without confusing that meaning with motion or physical substance. | OBJ-010; BIO-004; FLD-001; Sections 4.1 and 7.9 | An anchored living tree, active machine, rigid statue, and liquid retain their distinct roles. AC-02, AC-08, AC-09. |
| U12 | Animate trees and leaves through wind even when they have no active mechanical control. | Section 4.5; ENV-001–ENV-006; ANM-009; PHY; FLD-008–FLD-009 | AC-08 generates passive response and settling without per-leaf motion scripts. |
| U13 | Understand solids, liquids, forces, collisions, and how the environment affects an object. | PHY-001–PHY-021; FLD-001–FLD-012; ENV-004; ANM-020 | AC-02, AC-08–AC-10, AC-12, and AC-19–AC-22 inspect actual physical response, numerical assumptions, combined interactions, and replay. |
| U14 | Define wings, flying capability, and comparable meaningful features without requiring the author to implement underlying mechanics. | BIO-001, BIO-004, BIO-010–BIO-011; ANM-004–ANM-005; FLD-010–FLD-011 | AC-12; wing appearance, force model, actuation, and controller support have explicit meanings. |
| U15 | Create rocks, mountains, trees, and buildings with surface patterns and appropriate behavior. | ENV-001–ENV-010; GEO; MAT; PHY | AC-08 and AC-11 include semantic parts, collision/support surfaces, and editable appearance. |
| U16 | Examine the repository and deeply research what can be reused, reproduced, or adapted before writing the requirements. | Sections 2 and 6; Appendices A and C; NFR-011 | Complete repository inventory, primary-source reuse matrix, stated limitations, and no unsupported dependency selection. |

The principal product test joins these intentions: **an agent defines a novel supported object, OntoKin supplies its routine physical and animation machinery, a local revision preserves the rest of the asset, and a named destination receives the promised result.**

## Appendix A. Repository documentation examined

The review covered all documentation artifacts in repository snapshot `cfadf988e627112e9cf24ad9787d9b861e97d32d`. Text, diagram labels and source, and rendered diagram images were examined. The inventory consists of **7 Markdown files, 1 HTML file, 6 SVG files, 6 PNG files, and 3 Graphviz DOT files: 23 documentation artifacts in total**. The repository also contains a `.gitignore`, which is not a product specification.

The following package prefixes identify exact repository directories:

| Prefix | Directory |
| --- | --- |
| Root | Repository root |
| P1 | `Defining_Ontokin_Docs/OK-001/` |
| P2 | `Defining_Ontokin_Docs/OK-002/` |
| P3 | `Defining_Ontokin_Docs/OntoKin_003_Compilation_and_Runtime_Architecture_Package/` |

In the inventory, each listed format denotes a separate examined file with the shown base name and extension. Paths are relative to the stated package prefix.

| Package | Document or diagram base name | Formats examined | Files | Main contribution |
| --- | --- | --- | --- | --- |
| Root | `README` | `.md` | 1 | Product name, repository organization, concept-stage scope, and roadmap. [R01] |
| P1 | `README` | `.md` | 1 | OK-001 package contents and navigation. |
| P1 | `OntoKin_001_Project_Vision_and_Architecture` | `.md` | 1 | Vision, AI-first world authoring, responsibility boundaries, and initial experimentation. [R02] |
| P1 | `OntoKin_001_Architecture_Diagram` | `.svg`, `.png` | 2 | High-level authoring, language, runtime, rendering, and feedback relationships. |
| P2 | `README` | `.md` | 1 | OK-002 package contents and navigation. |
| P2 | `OntoKin_002_Language_Foundations_and_Minimal_Specification` | `.md` | 1 | Proposed language core, types, behavior, initial minimal world, and staged extensions. [R03] |
| P2 | `diagrams/OK-002-Figure-01-Authoring-to-Execution` | `.svg`, `.png` | 2 | Proposed authoring and execution flow. |
| P2 | `diagrams/OK-002-Figure-02-Conceptual-Language-Core` | `.svg`, `.png` | 2 | Proposed conceptual types, relationships, and language responsibilities. |
| P3 | `README` | `.md` | 1 | OK-003 package contents and renderer-integration follow-up. |
| P3 | `OntoKin_003_Compilation_and_Runtime_Architecture` | `.md`, `.html` | 2 | Proposed compiler/package model, runtime contracts, rendering boundary, and backend options. [R04] |
| P3 | `diagrams/OK-003-Figure-01-Compiler-and-Package` | `.svg`, `.png`, `.dot` | 3 | Proposed compilation stages and packaged representations. |
| P3 | `diagrams/OK-003-Figure-02-Runtime-and-Renderer` | `.svg`, `.png`, `.dot` | 3 | Proposed runtime/renderer interaction and state flow. |
| P3 | `diagrams/OK-003-Figure-03-Backend-Choices` | `.svg`, `.png`, `.dot` | 3 | Proposed execution/backend alternatives. |

### Review observations

The snapshot contains no implemented compiler, runtime, language test suite, dependency manifest, executable example, or project license file. Claims in these documents are therefore treated as design intent rather than demonstrated capability.

The OK-003 HTML edition repeats the Markdown edition's substantive content. Its presence does not establish an additional specification. The diagram formats provide alternate views of the same proposed architecture and were checked for consistency with the text.

Two editorial inconsistencies affect navigation and historical interpretation: the root README links to `Defining_OntoKin_Docs/`, while the actual directory is `Defining_Ontokin_Docs/`; OK-003 contains a naming-transition statement about older documents that is stale relative to the inspected versions. Neither changes the product definition. This PRD consistently uses OntoKin and the actual repository paths.

The existing roadmap reserves OK-004 for renderer integration. This requirements document uses the separate identifier **OK-PRD-001** so it does not imply completion of that planned architecture document.

## Appendix B. Working glossary

These definitions clarify product language. The eventual formal specification must define exact semantics.

| Term | Meaning in this PRD |
| --- | --- |
| Asset | A reusable object or assembly with geometry and associated meaning, appearance, physical data, and optional animation or behavior. |
| Entity/object | An identifiable thing in the authored world, such as a creature, arm, wheel, building, or liquid domain. |
| Component | A reusable contribution to an object: a part, capability, physical model, material, or behavior with an explicit contract. |
| Class/type | A reusable definition of properties and supported operations from which compatible objects can be created. Exact inheritance rules remain open. |
| Function and method | A reusable parameterized operation; a method is an operation associated with an object/type contract. Effects and timing must be documented. |
| Ownership hierarchy | The parent-child relationship describing which parts belong to which assemblies. It does not by itself define every physical constraint. |
| Attachment | A declared connection site and intent that relates parts and can generate supported transforms, joints, bindings, or other constraints. |
| Articulation | A system of connected parts with permitted relative movement, such as a limb or mechanical linkage. |
| Kinematics | The relationships between poses and motion without calculating the forces that cause them. |
| Dynamics | The evolution of physical state under forces, torques, mass, constraints, contacts, and the selected model. |
| Controller | A system that chooses actuation or motion commands to achieve a goal while operating within its declared model and limits. |
| Rig | The structures and controls used to pose or animate a body. A rig can include a skeleton and constraints; its existence does not guarantee a successful movement controller. |
| Skin binding | The mapping that makes visible geometry follow a skeleton or another deformation structure. It is separate from skin color and texture. |
| Physical material | Properties governing supported physical response, such as density, friction, compliance, and viscosity; distinct from visible shading. |
| Collider | The geometry or representation used to calculate contact and collision. It can differ from the detailed visible surface. |
| Morphology/body plan | The arrangement, proportions, and functional roles of parts, without requiring correspondence to a known species. |
| Support profile | A versioned contract specifying supported objects, parameter ranges, models, interactions, outputs, quality, and limitations. |
| Provenance | A record of where a value or result came from: authored input, library default, derivation, estimate, imported asset, or generated result. |
| Baking/recording | Converting procedural or simulated behavior into sampled output, such as animation curves, mesh samples, or texture images. |
| Live behavior | Behavior that remains executable in the target and can respond to new input or conditions. It has a different contract from recorded playback. |
| Level of detail | A selected complexity of geometry, appearance, or simulation; changing one does not automatically require changing all others. |

## Appendix C. Source catalog

All external sources below are official project documentation, project repositories, or original research papers. They were consulted to identify existing capabilities, limitations, and reuse candidates. They do not independently establish that the proposed OntoKin requirements have been implemented. Research and project status were checked on October 16, 2026; version-specific findings should be rechecked at dependency selection.

### Repository sources

All repository links are pinned to the reviewed commit.

| ID | Source |
| --- | --- |
| R01 | [OntoKin repository README][R01] |
| R02 | [OK-001 — Project Vision and Architecture][R02] |
| R03 | [OK-002 — Language Foundations and Minimal Specification][R03] |
| R04 | [OK-003 — Compilation and Runtime Architecture][R04] |

### External primary sources

| ID | Source | Main relevance |
| --- | --- | --- |
| S01 | [Modelica language project][S01] | Reusable declarative physical components and equation-based modeling. |
| S02 | [Modelica Standard Library repository][S02] | Domain-library breadth and reuse terms. |
| S03 | [Scenic language documentation, 3.x][S03] | Structured scene generation, spatial constraints, and dynamic scenarios. |
| S04 | [MuJoCo modeling documentation][S04] | Body hierarchy, joints, defaults, physical properties, and model construction. |
| S05 | [MuJoCo overview][S05] | Dynamics, actuation, and the boundary between physical primitives and anatomical meaning. |
| S06 | [MuJoCo fluid interaction documentation][S06] | Drag/lift approximations and the distinction from evolving fluid simulation. |
| S07 | [Jolt Physics repository][S07] | Game-oriented physical interactions and mechanisms. |
| S08 | [NVIDIA PhysX vehicle documentation][S08] | Reusable vehicle-dynamics components and configuration. |
| S09 | [Genesis project repository][S09] | Multiple physical material/solver families and coupled simulation. |
| S10 | [OpenSim documentation][S10] | Musculoskeletal components, actuation, and control. |
| S11 | [Drake hydroelastic contact tutorial][S11] | Separate visual, collision, and inertial representations; contact-model limitations. |
| S12 | [DeepMimic project and original research][S12] | Physically simulated motion through learned imitation control. |
| S13 | [MimicKit repository][S13] | Reusable motion-imitation tooling and dependency considerations. |
| S14 | [Universal Morphology Control via Contextual Modulation, ICML 2023][S14] | Research on control across changing morphologies. |
| S15 | [Blender Geometry Nodes modifier, manual 4.4][S15] | Reusable procedural geometry and exposed parameters. |
| S16 | [Blender Armature modifier documentation][S16] | Skeletal deformation and skin binding. |
| S17 | [Blender license information][S17] | Distinguishing application terms from created artwork/data. |
| S18 | [Houdini KineFX overview][S18] | Procedural rigging and animation design precedent. |
| S19 | [Infinigen repository][S19] | Procedural environment and asset generation. |
| S20 | [Procedural Generation of Articulated Simulation-Ready Assets, version 3][S20] | Infinigen Articulated: reusable articulated generators and simulator export. |
| S21 | [ProcFunc paper, version 2][S21] | Higher-level procedural functions for language-model authoring. |
| S22 | [ProcFunc repository][S22] | Implementation availability, maturity, and reuse terms. |
| S23 | [Algorithmic Botany: Modeling Plant Development with L-Systems][S23] | Recursive plant structure and growth-model precedent. |
| S24 | [OpenUSD introduction][S24] | Scene composition, typed relationships, and current project license statement. |
| S25 | [UsdPhysics documentation][S25] | Physics scene description and interoperability limits. |
| S26 | [UsdSkel introduction][S26] | Skeletons, skinning, blend shapes, and skeletal animation. |
| S27 | [glTF 2.0 specification][S27] | Runtime asset and animation exchange. |
| S28 | [Khronos glTF extension registry][S28] | Current status of interactivity and draft physics extensions. |
| S29 | [MaterialX project][S29] | Portable material and look descriptions. |
| S30 | [Alembic project][S30] | Recorded geometry and animation delivery. |
| S31 | [OpenVDB project][S31] | Sparse volumetric data representation. |
| S32 | [SimWorlds paper, version 1][S32] | Agent-generated dynamic scenes and verification beyond appearance. |
| S33 | [SceneCraft: An LLM Agent for Synthesizing 3D Scene as Blender Code][S33] | Agent-driven procedural scene authoring. |
| S34 | [Modelica Language Specification, version 3.7][S34] | Formal semantics for reusable physical modeling, types, functions, events, and initialization. |
| S35 | [Project Chrono vehicle overview][S35] | Vehicle subsystem templates, mechanical assemblies, and parameter contracts. |
| S36 | [Newton solver overview and feature matrix][S36] | Actual backend enforcement of joint/material properties and solver-specific support. |
| S37 | [XPBD: Position-Based Simulation of Compliant Constrained Dynamics][S37] | Physical material compliance and the effects of numerical solver settings. |
| S38 | [Genesis locomotion tutorial][S38] | Controller observation/action mappings, units/scaling, timing, state, and reset assumptions. |
| S39 | [Godot 3D import configuration documentation][S39] | Destination processing of geometry, skin weights, materials, and animation. |
| S40 | [Khronos glTF Validator repository][S40] | Structured file validation and its documented extension coverage. |
| S41 | [GPU Gems 3: GPU-Generated Procedural Wind Animations for Trees][S41] | Hierarchical tree motion and efficient, explicitly approximate vegetation response. |
| S42 | [Newton FAQ][S42] | Distinguishing Newton's physics models from Warp's computation facilities. |
| S43 | [WorldAgent paper, version 1][S43] | Recent agent-authored physical worlds using entity contracts and state verification. |
| S44 | [OpenPBR repository and linked specification][S44] | Common surface-shading parameters and a MaterialX reference implementation. |
| S45 | [Genesis coupling documentation][S45] | Model-pair and configuration-specific coupling boundaries. |
| S46 | [Project Chrono vehicle terrain documentation][S46] | Tire/terrain compatibility and supported interaction models. |
| S47 | [CadQuery introduction][S47] | Reusable programmatic parametric solid construction. |
| S48 | [OpenSCAD overview][S48] | Script-defined constructive solid geometry. |

## Appendix D. Review findings and revision record

### D.1 Review conclusion

The supplied version 0.1 already captured the owner's principal idea well. It required an AI-native object language, automatic routine physics and mechanics, modular ownership and physical connections, unusual anatomy, supplied movement, passive vegetation, liquids and deformable materials, inspectable defaults, and honest delivery contracts. Those requirements have been retained.

The material gaps were primarily in the contracts connecting those capabilities: exact language meaning, complete-assembly support, acceptance of valid creative edits, actual enforcement by an engine, controller compatibility, numerical material behavior, deformation quality, interactive replay, and evidence in destination tools. Version 0.2 closes those gaps at the product-requirements level and adds acceptance cases for them.

This review covered the supplied Markdown, the owner's current brief, all 23 repository documentation artifacts, and the primary sources cataloged above. It did not implement or benchmark OntoKin or its candidate dependencies. The revised document is a product baseline for review; a versioned formal language specification, calibrated support profiles, and executable conformance fixtures remain required outputs of later design and implementation. Future evidence can justify further changes through the same requirement IDs and revision process.

| Registry measure | Supplied version 0.1 | Revised version 0.2 |
| --- | --- | --- |
| Numbered requirements | 206 | 226 |
| MUST requirements | 193 | 213 |
| SHOULD requirements | 13 | 13 |
| Acceptance scenarios | 16 | 22 |
| Owner intentions traced | 16 | 16 |
| Original requirement IDs removed or renumbered | — | 0 |
| Existing priorities changed | — | 0 |

### D.2 Material changes and evidence

“Added” identifies new requirement IDs. “Strengthened” identifies existing requirements whose meaning or acceptance evidence was clarified. Existing requirements should continue to be cited under their original IDs.

| Finding | Revision and purpose | Requirement coverage | Acceptance evidence |
| --- | --- | --- | --- |
| Language constructs were named without a complete requirement for their semantics. | Require explicit binding, reference/copy behavior, dispatch, effects, evaluation order, cycles, numeric failures, and constraint priorities/tolerances. This makes the eventual language specification testable without choosing an implementation language. | Added LNG-018–LNG-021; strengthened LNG-009, LNG-013, LNG-015. | AC-17; DOC-001. |
| Atomic edits could conflict with preserving valid anatomy outside controller support. | Define acceptance by the requested result. Keep valid source/body construction while reporting unavailable control and stale derived output; do not silently downgrade a request for successful animation. | Strengthened AGT-006; aligned with BIO-014 and Section 9.3. | AC-18 and AC-04. |
| Individual feature support did not establish a supported assembly, and agent operations needed stronger lifecycle contracts. | Require complete-assembly preflight, versioned operation/job results, safe retry semantics, cancellation, and bounded queries tied to a revision/run. | Added AGT-016–AGT-018; expanded Section 9.1. | AC-17, AC-19, and AC-22. |
| Unit conversion, physical resizing, conflicting physical inputs, and numerical settings could change behavior unexpectedly. | Distinguish conversion from physical change; expose mass-distribution assumptions and input conflicts; require calibrated material behavior and bounded automatic initialization. | Added OBJ-017, PHY-020–PHY-021; strengthened OBJ-005, PHY-003–PHY-004. | AC-20; Section 10.3. |
| A stored parameter or motor command could be mistaken for enforced physics. | Require effective backend behavior, disclosed mappings/approximations, measurable actuation limits, and distinction between command limits and physically enforced constraints. | Added PHY-019; strengthened MEC-003 and MEC-006. | AC-19 and AC-07. |
| Physical articulation and visual skin deformation could be conflated. | Require mappings between semantic parts, physical bodies, controls, and deformation structures; bind/rest and deformation-order contracts; supported facial/corrective shape deformation; actual surface-quality evidence. | Added OBJ-018, MAT-014–MAT-015; expanded Section 4.3. | AC-13 and AC-21. |
| A behavior name or controller file did not fully specify the action and body interface. | Require goal/precondition/outcome contracts and supplied observation/action mappings, units/frames, timing, state, and reset behavior. | Added ANM-018–ANM-019; expanded Section 4.5. | AC-06, AC-12, and AC-19. |
| Repeatability needed external inputs and coordinated clocks, in addition to seeds. | Require declared scheduling across simulation, control, events, and output, plus input/environment histories and replay configuration. | Added ANM-020; strengthened ANM-010 and NFR-002. | AC-16 and AC-22. |
| Accepted local or imported refinements could lose authority during regeneration. | Clarify which definition governs generated content, how refinements are preserved or detached, and when structured/source forms must agree. | Strengthened GEO-011, LNG-013, and LNG-015. | AC-04 and AC-17. |
| Valid geometry or a valid export file could still fail the intended task. | Preserve necessary collision openings/clearances; specify appearance conventions; check final importer settings, deformed surfaces, and target budgets separately from format validation. | Added EXP-016; strengthened GEO-007, MAT-009, EXP-007, EXP-011, and EXP-014. | AC-09, AC-13, and AC-21. |
| Qualitative acceptance and self-reported success were insufficient to establish support. | Require independent measurements, versioned fixture definitions, boundary/held-out combinations, and transparent human/template/controller preparation in the agent comparison. | Added VAL-011 and DOC-009; expanded Sections 10.1, 10.3, and 10.4. | All scenario fixtures; particularly AC-19–AC-22. |

The 20 added IDs are **LNG-018–LNG-021; AGT-016–AGT-018; OBJ-017–OBJ-018; PHY-019–PHY-021; ANM-018–ANM-020; MAT-014–MAT-015; EXP-016; VAL-011; and DOC-009**. All are MUST requirements of the complete intended product. A limited release must disclose which are unfinished, together with any unfinished original requirements.

### D.3 Research corrections and additions

The ProcFunc finding has been narrowed to the task-dependent evidence in its paper. Its material-creation results support investigating higher-level functions; parameter-editing results do not support a blanket error-reduction claim. The revised document also distinguishes the repository's primitives/transpiler/tracer from separately distributed generators. [S21] [S22]

The review retained the original document's correct boundaries for glTF extension maturity, UsdSkel's scope, and the Infinigen Articulated paper's coupled-joint limitation. These findings continue to require actual target and interaction evidence. [S20] [S26] [S28]

Added research covers the current formal Modelica specification, modular Chrono vehicles and terrain, Newton's backend enforcement matrix, XPBD, Genesis controller/coupling contracts, destination import behavior, explicit procedural tree-wind approximations, OpenPBR, programmatic solid construction, and recent entity-contract research. Their specific contributions and limits are recorded in Section 6 and sources S34–S48. They are candidates and precedents, not selected dependencies or reproduced benchmarks.

### D.4 Deliberately unresolved choices

The review did not turn the PRD into a compiler or runtime design. Exact grammar, inheritance/dispatch rules, numeric representations, profile serialization, engines, controller methods, supported destination versions, hardware budgets, and calibrated numerical tolerances still require explicit decisions. Sections 7–10 now state the contracts those choices must satisfy, and Section 12 identifies the remaining decisions. Resolving them must preserve the principal promise: **the author defines the object and intended behavior; OntoKin supplies its routine physical and animation machinery within demonstrated support.**

[R01]: https://github.com/Omegapy/OntoKin/blob/cfadf988e627112e9cf24ad9787d9b861e97d32d/README.md
[R02]: https://github.com/Omegapy/OntoKin/blob/cfadf988e627112e9cf24ad9787d9b861e97d32d/Defining_Ontokin_Docs/OK-001/OntoKin_001_Project_Vision_and_Architecture.md
[R03]: https://github.com/Omegapy/OntoKin/blob/cfadf988e627112e9cf24ad9787d9b861e97d32d/Defining_Ontokin_Docs/OK-002/OntoKin_002_Language_Foundations_and_Minimal_Specification.md
[R04]: https://github.com/Omegapy/OntoKin/blob/cfadf988e627112e9cf24ad9787d9b861e97d32d/Defining_Ontokin_Docs/OntoKin_003_Compilation_and_Runtime_Architecture_Package/OntoKin_003_Compilation_and_Runtime_Architecture.md
[S01]: https://modelica.org/projects/language/
[S02]: https://github.com/modelica/ModelicaStandardLibrary
[S03]: https://docs.scenic-lang.org/en/3.x/
[S04]: https://mujoco.readthedocs.io/en/stable/modeling.html
[S05]: https://mujoco.readthedocs.io/en/stable/overview.html
[S06]: https://mujoco.readthedocs.io/en/stable/computation/fluid.html
[S07]: https://github.com/jrouwe/JoltPhysics
[S08]: https://nvidia-omniverse.github.io/PhysX/physx/latest/docs/Vehicles.html
[S09]: https://github.com/Genesis-Embodied-AI/genesis-world
[S10]: https://opensimconfluence.atlassian.net/wiki/spaces/OpenSim/pages/53088473
[S11]: https://drake.mit.edu/tutorials/hydroelastic_contact_basics.html
[S12]: https://xbpeng.github.io/projects/DeepMimic/index.html
[S13]: https://github.com/xbpeng/MimicKit/
[S14]: https://proceedings.mlr.press/v202/xiong23a.html
[S15]: https://docs.blender.org/manual/en/4.4/modeling/modifiers/generate/geometry_nodes.html
[S16]: https://docs.blender.org/manual/en/latest/modeling/modifiers/deform/armature.html
[S17]: https://www.blender.org/about/license/
[S18]: https://www.sidefx.com/docs/houdini/character/kinefx/overview.html
[S19]: https://github.com/princeton-vl/infinigen
[S20]: https://arxiv.org/html/2505.10755v3
[S21]: https://arxiv.org/html/2604.26943v2
[S22]: https://github.com/princeton-vl/procfunc
[S23]: https://algorithmicbotany.org/papers/modeling-plant-development-with-l-systems.html
[S24]: https://openusd.org/release/intro.html
[S25]: https://openusd.org/release/api/usd_physics_page_front.html
[S26]: https://openusd.org/release/api/_usd_skel__intro.html
[S27]: https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html
[S28]: https://raw.githubusercontent.com/KhronosGroup/glTF/main/extensions/README.md
[S29]: https://materialx.org/index.html
[S30]: https://www.alembic.io/
[S31]: https://www.openvdb.org/
[S32]: https://arxiv.org/html/2607.01766v1
[S33]: https://arxiv.org/abs/2403.01248
[S34]: https://specification.modelica.org/maint/3.7/MLS.html
[S35]: https://api.projectchrono.org/vehicle_overview.html
[S36]: https://newton-physics.github.io/newton/stable/solvers/index.html
[S37]: https://matthias-research.github.io/pages/publications/XPBD.pdf
[S38]: https://genesis-world.readthedocs.io/en/latest/user_guide/policy_training/examples/locomotion.html
[S39]: https://docs.godotengine.org/en/stable/tutorials/assets_pipeline/importing_3d_scenes/import_configuration.html
[S40]: https://github.com/KhronosGroup/glTF-Validator
[S41]: https://developer.nvidia.com/gpugems/gpugems3/part-i-geometry/chapter-6-gpu-generated-procedural-wind-animations-trees
[S42]: https://newton-physics.github.io/newton/stable/faq.html
[S43]: https://arxiv.org/html/2609.33208v1
[S44]: https://github.com/AcademySoftwareFoundation/OpenPBR
[S45]: https://genesis-world.readthedocs.io/en/latest/user_guide/theory/coupling/index.html
[S46]: https://api.projectchrono.org/vehicle_terrain.html
[S47]: https://cadquery.readthedocs.io/en/latest/intro.html
[S48]: https://openscad.org/about.html

