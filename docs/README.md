# OntoKin documentation guide

For current development checks, start with [OK-ENG-006: Local validation and hosted CI policy](engineering/OK-ENG-006-local-validation-and-hosted-ci-policy.md). Local execution is the default; historical CI records and complete release contracts retain their identified scope.

Start with the capability definition, then use the PRD for detailed product requirements, the semantic model for proposed meanings, and OK-LANG-001 for the formal `core-0.1` source-language contract. OK-ENG-001 explains the first headless reference prototype; OK-ENG-002 adds viewable GLB animation; OK-AGENT-001 adds the durable single-source agent interface. The 0.4.0 milestone implements OK-LANG-002 and OK-AGENT-002 for pinned reusable modules, keyed assembly construction, and atomic program-bundle editing. Its [identified local and CI gate passed](engineering/construction-validation/validation-summary.json). OK-LANG-003 fixes the adopted surface-0.1 source contract. Native parsing, construction and GLB/0.3 export are implemented; OK-AGENT-003 supplies source-authoritative native surface workflows. [STATUS](../STATUS.md) separates implemented components from complete release evidence and unmet product requirements. The product, capability, and semantic records retain their review status. The original vision and architecture records remain available in full for their rationale, examples, alternatives, and open questions.

## Current definition and reading order

| Read | Document | Role | Recorded status |
| --- | --- | --- | --- |
| 1 | [OK-CAP-001 v0.1: Modeling, motion, and object structure](product/OK-CAP-001-modeling-motion-and-object-structure.md) | The current modeling emphasis: reusable exterior objects, nested parts, physical meaning, and short animations, with larger worlds as the longer-term direction. | Draft for concept review |
| 2 | [OK-PRD-001 v0.2: Product requirements](product/OK-PRD-001-product-requirements.md) | Broad product outcomes, support contracts, required behavior, acceptance evidence, research, and unresolved choices. | Draft for product review |
| 3 | [OK-SEM-001 v0.1: Core object, motion, and physics semantics](language-design/OK-SEM-001-core-object-motion-and-physics-semantics.md) | Proposed rules connecting objects, ownership, spatial frames, mechanical relationships, physical behavior, and actions. | Conceptual language design; proposed for semantic review |
| 4 | [OK-LANG-001 v0.1: Core language specification](language-design/OK-LANG-001-core-language-specification.md) | Review of all 28 SEM rules; complete grammar, types, object and motion rules, agent contracts, source examples, and validation cases for `core-0.1`. | Adopted core engineering baseline, October 17, 2026; measured support remains separate |
| 5 | [OK-ENG-001 v0.1: Core reference implementation and conformance plan](engineering/OK-ENG-001-core-reference-implementation-and-conformance-plan.md) | Prototype boundaries, adopted decisions, parser/validator/evaluator, reproducible commands, executed evidence, and production architecture assessment. | Experimental reference implementation; no full-core or full-product certification |
| 6 | [OK-ENG-002 v0.1: 3D scene representation, animation export, and visual validation](engineering/OK-ENG-002-3d-scene-animation-export-and-visual-validation.md) | Primitive meshes, evaluated world transforms, recorded GLB animation, conversion reporting, numerical checks, and visible demonstrations. | Experimental `ontokin.glb/0.1` export; live destination physics and broader delivery remain separate |
| 7 | [OK-AGENT-001 v0.1: AI agent authoring and inspection interface](engineering/OK-AGENT-001-ai-agent-authoring-and-inspection-interface.md) | Durable source/revision editing, bounded inspection, runs, retries, cancellation, recovery, and source-to-GLB agent workflow. | Experimental local `ontokin.agent/0.1` service; full product acceptance remains separate |
| 8 | [OK-LANG-002 v0.1.1: Pinned modules and keyed assembly construction](language-design/OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md) | Exact offline dependencies, program identity, reusable keyed parts, scoped repair, finite limits, and independent expected results. | Adopted October 18, 2026; experimental 0.4.0 implementation with measured local and CI gate passed |
| 9 | [OK-AGENT-002 v0.1: Program bundles and atomic source edits](engineering/OK-AGENT-002-program-bundles-and-atomic-source-edits.md) | Separate `ontokin.agent/0.2` protocol, per-file source authority, complete-program acceptance, scoped generated-instance edits, and `ontokin.glb/0.2` delivery. | Experimental 0.4.0 implementation; local and CI gate passed, with expected contracts and measured evidence kept separate |
| 10 | [OK-LANG-003 v0.2: Parameterized exterior surfaces and material regions](language-design/OK-LANG-003-parameterized-exterior-surfaces-and-material-regions.md) | Adopted `surface-0.1` source types, keyed loft sections, material-region rules, fixed limits and M01–M12 fixtures. | Native source compiler and GLB/0.3 adapter implemented; complete release evidence remains tracked in STATUS |
| 11 | [OK-AGENT-003 v0.1: Native surface program workflows](engineering/OK-AGENT-003-native-surface-program-workflows.md) | Explicit Agent/0.3 service, separate durable store, source repair, bounded surface summaries, triangle pages and native artifact retrieval. | Versioned interface and implementation; composed-source, destination and complete M01–M12 acceptance remain separate identified gates |
| 12 | [OK-ENG-004 v0.1: Native surface release conformance](engineering/OK-ENG-004-native-surface-release-conformance.md) | Executable M01–M12 mapping, complete source workflow, independent destination/browser checks, full regressions and current CI identity. | Reproduction and evidence contract; actual complete release results remain separately identified |
| 13 | [OK-LANG-004 v0.1: Source impulses and free-sphere dynamics](language-design/OK-LANG-004-source-impulses-and-free-sphere-dynamics.md) | Explicit source 0.4 units and frames, off-center sphere momentum, ordered atomic boundaries, complete source influence records and frozen I01–I12 expectations. | Adopted before implementation; implementation and final release evidence tracked separately |
| 14 | [OK-AGENT-004 v0.1: Source impulse program workflows](engineering/OK-AGENT-004-source-impulse-program-workflows.md) | Explicit Agent/0.4 discovery, bounded inspection, physical-parameter source repair, separate store and native GLB/0.4 retrieval. | Versioned implementation and actual request/retrieval workflow; finite release gate remains separately identified |
| 15 | [OK-ENG-005 v0.1: Source impulse release conformance](engineering/OK-ENG-005-source-impulse-release-conformance.md) | Executable fixed physics oracles, exact workflow/artifact evidence, independent destination/browser checks and all current inherited gates. | Reproduction and strict evidence contract for the complete finite I01–I12 release |
| 16 | [OK-LANG-005 v0.1: Finite center-of-mass force intervals](language-design/OK-LANG-005-finite-center-of-mass-force-intervals.md) | Exact finite-force clocks, additive overlaps, unchanged-acceleration anchors, rollback, source identities and frozen F01–F12 expectations. | Adopted source contract and identified supplements; full release evidence is separate |
| 17 | [OK-AGENT-005 v0.1: Finite-force program workflows](engineering/OK-AGENT-005-finite-force-program-workflows.md) | Explicit Agent/0.5 force discovery, complete bounded source inspection, atomic physical repairs and durable operation lifecycle. | Source workflow integrated; complete release and delivery evidence remain separately identified |
| 18 | [OK-ENG-006 v0.1: Local validation and hosted CI policy](engineering/OK-ENG-006-local-validation-and-hosted-ci-policy.md) | Fresh local checks, identified execution evidence and manual-only hosted execution under the owner's no-payment direction. | Adopted execution-provider policy; historical records retain their meaning |
| 19 | [OK-ENG-007 v0.1: Native force GLB export](engineering/OK-ENG-007-native-force-glb-export.md) | Bounded prefix recording, acceleration/angular subdivision, decoded binary32 validation and actual Agent artifact delivery. | Component implemented; complete release acceptance is a separate gate |
| 20 | [OK-ENG-008 v0.1: Provider-neutral finite force release conformance](engineering/OK-ENG-008-force-release-conformance.md) | Executable F01–F12 mapping, complete source and artifact corpora, Python compatibility, current inherited roles and hash-bound visual evidence. | Adopted evidence contract; actual release results remain separately identified |
| 21 | [OK-LANG-006/0.1.0: Reusable planar reach actions](language-design/planar-reach-v0.1/ADOPTION.md) | Frozen two-hinge reach semantics, exact numerical admission, atomic lifecycle, Agent/0.6 and recorded GLB/0.6 contracts with all finite release obligations. | Adopted for implementation; actual runtime and release acceptance pending |

These documents answer related questions at different levels. A product requirement says what OntoKin should accomplish. A capability definition explains the intended objects and tasks. A semantic rule defines what an operation or relationship means. The language specification defines how source expresses a bounded subset of those meanings, how validity is decided, and which state a program should produce. The engineering documents record how that subset is processed, exported, and tested. Expected behavior remains separate from measured implementation results.

### Core language companion files

The [core-v0.1 folder](language-design/core-v0.1/) contains the [complete EBNF](language-design/core-v0.1/ontokin-core.ebnf), four complete `.ok` programs, a [43-case validation manifest](language-design/core-v0.1/validation-cases.json) with ten agent-operation cases, a [diagnostic schema](language-design/core-v0.1/diagnostic.schema.json) and [synthetic example](language-design/core-v0.1/diagnostic-example.json), and a [coverage register](language-design/core-v0.1/requirement-coverage.json) for every PRD/CAP requirement. These are the original design artifacts; their pre-implementation status fields are historical. The specification explains expected behavior. The [original engineering conformance report](engineering/conformance-results.json) preserves the headless milestone's results; the [visual milestone run](engineering/visual-validation/core-conformance.json) and [0.3.0 agent milestone run](engineering/agent-validation/core-conformance.json) retain subsequent execution of those same expectations.

### Construction language and program companions

The [construction-v0.1 folder](language-design/construction-v0.1/) contains the [0.2 EBNF](language-design/construction-v0.1/ontokin-construction.ebnf), [inline bundle schema](language-design/construction-v0.1/bundle.schema.json), [local file-manifest schema](language-design/construction-v0.1/file-manifest.schema.json), and [C01–C20 acceptance manifest](language-design/construction-v0.1/validation-cases.json). The [module subset](language-design/construction-v0.1/module-cases.json) fixes concrete source bundles, exact hashes, and failure origins for reuse, namespaces, transitive imports, pin failures, module validity, and revision identity. These files state expectations; their contents are not an execution report.

Begin with the [two-source Rack program](language-design/construction-v0.1/01-keyed-rack/program.files.json), its editable [entry](language-design/construction-v0.1/01-keyed-rack/main.ok) and [component library](language-design/construction-v0.1/01-keyed-rack/hinges.ok), and its [independent expected geometry and poses](language-design/construction-v0.1/01-keyed-rack/expected.json). The [namespace](language-design/construction-v0.1/02-namespaces/program.files.json) and [transitive import](language-design/construction-v0.1/03-transitive/program.files.json) examples exercise distinct module composition rules. The [construction example guide](../examples/construction/README.md) explains how to run the complete authoring workflow and play its GLB.

The separate agent contract has [request](language-design/agent-v0.2/request.schema.json), [response](language-design/agent-v0.2/response.schema.json), and [diagnostic](language-design/agent-v0.2/diagnostic.schema.json) schemas. A `program_revision` identifies the complete supplied closure; a `source_revision` continues to identify one exact source file. The original 0.1 schemas and operation meanings remain in place.

### Surface-0.1 companion files

The [surface-v0.1 folder](language-design/surface-v0.1/) fixes the M01–M12 analytical, boundary, negative, held-out and source-repair expectations. Its [pinned two-file sample](language-design/surface-v0.1/README.md) compiles as native `0.3` source and exports through the explicit `ontokin.glb/0.3` adapter. The [native export guide](engineering/OK-ENG-003-native-surface-glb-export.md) supplies the executable file-manifest command, limits and independent validation procedure. The [complete native release evidence](engineering/surface-release-validation/README.md) records all M01–M12 passed, including actual Agent/0.3 source workflows, 22 source-built GLBs and reviewed browser views. [STATUS](../STATUS.md) identifies integration revisions and the next unfinished requirement. The [standalone mesh/GLB workbench](../prototypes/surface_v01/README.md) remains independent prototype evidence.

The [fixed conformance mapping](language-design/surface-v0.1/conformance.json) names concrete executable tests, 22 source artifacts, required repaired/composed/released browser views, and a frozen inherited regression floor. [OK-ENG-004](engineering/OK-ENG-004-native-surface-release-conformance.md) documents the runner and current-implementation evidence needed to close those requirements. A passing subset, a CI pre-attestation run, and a complete M01–M12 result have distinct recorded meanings.

### Run the reference prototype

The [root quick start](../README.md) gives the commands. The Python package reads `.ok` files, returns structured validation results, and samples headless state. Start with [independent parts](language-design/core-v0.1/01-independent-parts.ok), then [gravity and release](language-design/core-v0.1/02-gravity-and-release.ok). Use the [engineering reproduction steps](engineering/OK-ENG-001-core-reference-implementation-and-conformance-plan.md#5-reproduce-the-prototype) to run the complete source corpus.

### Export and view an animation

[OK-ENG-002](engineering/OK-ENG-002-3d-scene-animation-export-and-visual-validation.md#7-reproduce-and-inspect-the-demonstrations) explains the `.ok` to `.glb` workflow and the local visual demonstrations. The older exporter generates spheres and boxes; [GLB/0.3](engineering/OK-ENG-003-native-surface-glb-export.md) adds native lofts and regional PBR materials. Both record the evaluator's world transforms and report conversions and numerical limits. The released sphere follows its calculated free trajectory in playback. Source ownership remains metadata and does not apply carrier movement a second time.

The GLB contains recorded animation. Contact, dynamic articulated mechanisms, and live destination physics remain future work. The generic `check --level delivered` command is still unsupported; export success belongs to the named `ontokin.glb/0.1` output contract. File validation, numerical agreement, and actual destination inspection have separate evidence in [the export engineering record](engineering/OK-ENG-002-3d-scene-animation-export-and-visual-validation.md#8-measured-evidence).

### Author and inspect through the agent service

[OK-AGENT-001](engineering/OK-AGENT-001-ai-agent-authoring-and-inspection-interface.md) implements the language's agent-operation contracts through a durable local Python/JSONL interface. The [workflow example](../examples/agent/README.md) performs creation, exact-span diagnosis, a scoped occurrence repair, prefix evaluation, and GLB retrieval. The [request](language-design/agent-v0.1/request.schema.json) and [response](language-design/agent-v0.1/response.schema.json) schemas define its transport shapes; the [evidence index](engineering/agent-validation/README.md) separates executed tests from remaining limits. The root [goal](../GOAL.md), [status](../STATUS.md), and [working procedure](../AGENTS.md) preserve continuity across sessions.

[OK-AGENT-002](engineering/OK-AGENT-002-program-bundles-and-atomic-source-edits.md) extends that workflow to an explicitly supplied program bundle through `ProgramAgentService` and `python3 -m ontokin agent --protocol ontokin.agent/0.2 --store DIR`. The new service uses its own database and response fields. It preserves every source unit's original bytes and locations, atomically validates library edits with their changed import pins, and exposes public initializer targets for generated occurrences. The [construction guide](../examples/construction/README.md#use-local-source-files-or-an-inline-bundle) shows the actual APIs for local file manifests and inline source snapshots. The [construction evidence](engineering/construction-validation/README.md) records independently checked `ontokin.glb/0.2` output and the preserved baseline regression gates.

[OK-AGENT-003](engineering/OK-AGENT-003-native-surface-program-workflows.md) binds the same source-authoritative workflow to native surfaces through `ProgramAgentService(store, protocol="ontokin.agent/0.3")` and `python3 -m ontokin agent --protocol ontokin.agent/0.3 --store DIR`. Its [request](language-design/agent-v0.3/request.schema.json) and [response](language-design/agent-v0.3/response.schema.json) schemas define revision-bound `surface.mesh_page` reads of at most 256 complete triangles, with carrier-local positions, normals, source ordinals and regional identities. Summaries stay bounded; edits target actual `.ok` spans. The [additional composition fixtures](language-design/surface-v0.1/compositions/README.md) fix ordinary/generated parts and rotated-release expectations using the unchanged pinned surface library. CLI defaults and earlier stores remain unchanged; current implementation and complete release evidence are identified in [STATUS](../STATUS.md).

### How the scope statements relate

The PRD records the broader intended product, including game assets, complex object families, physical behavior, and delivery. Its MUST requirements do not place every capability in the first prototype. The later capability definition records the owner's modeling-first clarification: exterior models and short animations take priority, games are one possible use, and larger worlds remain a growth direction. It also places detailed biological interiors outside the current focus. See [CAP section 1](product/OK-CAP-001-modeling-motion-and-object-structure.md#1-language-purpose-and-current-direction), [CAP section 9](product/OK-CAP-001-modeling-motion-and-object-structure.md#9-relationship-to-earlier-work), and [SEM section 1.1](language-design/OK-SEM-001-core-object-motion-and-physics-semantics.md#11-how-to-read-the-proposed-rules).

The reorganization preserves both the broader requirements and the recorded clarification. It does not approve all draft requirements or settle their remaining design questions. A document's role and explicit statements determine how it is used; a newer filename alone does not give it authority over every subject.

## Find a specific topic

| Need | Start here |
| --- | --- |
| The agent's responsibilities and the setup OntoKin should supply | [PRD section 4: Responsibility contract](product/OK-PRD-001-product-requirements.md#4-the-responsibility-contract) |
| Detailed functional requirements | [PRD section 7](product/OK-PRD-001-product-requirements.md#7-functional-requirements) |
| Product acceptance scenarios and proposed measurements | [PRD section 10](product/OK-PRD-001-product-requirements.md#10-acceptance-scenarios-and-evaluation) |
| Requirement traceability to the owner's intent | [PRD section 13](product/OK-PRD-001-product-requirements.md#13-traceability-to-the-owners-intent) |
| The 18 high-level capabilities | [CAP section 6](product/OK-CAP-001-modeling-motion-and-object-structure.md#6-high-level-capability-requirements) |
| Classes, parts, ownership, and related representations | [SEM section 3](language-design/OK-SEM-001-core-object-motion-and-physics-semantics.md#3-object-oriented-structure) and [section 4](language-design/OK-SEM-001-core-object-motion-and-physics-semantics.md#4-object-hierarchy-and-related-representations) |
| Combining whole-object movement, local movement, and physical behavior | [SEM section 5](language-design/OK-SEM-001-core-object-motion-and-physics-semantics.md#5-position-and-movement) and [section 8](language-design/OK-SEM-001-core-object-motion-and-physics-semantics.md#8-animation-and-control) |
| Carrying and releasing a prop | [SEM section 9](language-design/OK-SEM-001-core-object-motion-and-physics-semantics.md#9-attachment-release-and-other-state-transitions) |
| A complete character sequence and its conceptual checks | [SEM section 11](language-design/OK-SEM-001-core-object-motion-and-physics-semantics.md#11-worked-example-a-modular-human-character) and [section 12](language-design/OK-SEM-001-core-object-motion-and-physics-semantics.md#12-semantic-behavior-checks) |
| Write valid core source, diagnose errors, and perform local agent edits | [OK-LANG-001](language-design/OK-LANG-001-core-language-specification.md) and its [grammar](language-design/core-v0.1/ontokin-core.ebnf) |
| Read the first formal programs | [Independent parts](language-design/core-v0.1/01-independent-parts.ok), [gravity/release](language-design/core-v0.1/02-gravity-and-release.ok), [rotating release](language-design/core-v0.1/03-rotating-release.ok), and [ownership/reuse/following](language-design/core-v0.1/04-ownership-reuse-and-follow.ok) |
| Determine which requirements the core addresses or defers | [Requirement coverage](language-design/core-v0.1/requirement-coverage.json) and [validation cases](language-design/core-v0.1/validation-cases.json) |
| Review the adopted baseline and prototype execution results | [LANG baseline addendum](language-design/OK-LANG-001-core-language-specification.md#16-engineering-baseline-adoption-and-clarifications), [engineering plan](engineering/OK-ENG-001-core-reference-implementation-and-conformance-plan.md), and [measured conformance](engineering/conformance-results.json) |
| Generate a visible 3D animation and understand its retained meaning | [Scene and GLB contract](engineering/OK-ENG-002-3d-scene-animation-export-and-visual-validation.md), [conversion/loss reporting](engineering/OK-ENG-002-3d-scene-animation-export-and-visual-validation.md#5-conversion-contract-and-loss-reporting), and [demonstration commands](engineering/OK-ENG-002-3d-scene-animation-export-and-visual-validation.md#7-reproduce-and-inspect-the-demonstrations) |
| Import exact reusable modules and generate a keyed assembly | [OK-LANG-002](language-design/OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md), [construction grammar](language-design/construction-v0.1/ontokin-construction.ebnf), and [Rack source bundle](language-design/construction-v0.1/01-keyed-rack/program.files.json) |
| Repair one generated occurrence or update a library and its pins atomically | [OK-AGENT-002](engineering/OK-AGENT-002-program-bundles-and-atomic-source-edits.md), [program request schema](language-design/agent-v0.2/request.schema.json), and [construction workflow](../examples/construction/README.md) |
| Check construction requirements and release evidence | [C01–C20 manifest](language-design/construction-v0.1/validation-cases.json), [module source scenarios](language-design/construction-v0.1/module-cases.json), and [current release status](../STATUS.md) |
| Open design decisions | [CAP section 8](product/OK-CAP-001-modeling-motion-and-object-structure.md#8-efficiency-interoperability-and-the-next-definition), [PRD section 12](product/OK-PRD-001-product-requirements.md#12-decisions-deliberately-left-for-product-and-language-design), and [SEM: Decisions still open](language-design/OK-SEM-001-core-object-motion-and-physics-semantics.md#decisions-still-open) |

## Founding design records

The [foundations folder](language-design/foundations/) contains three distinct early records. Their content remains intact, including their dated proposals and decision registers. They are useful when tracing why the project took its current direction.

| Document | What it preserves | Recorded status |
| --- | --- | --- |
| [OK-001 v0.1.1: Project vision and initial architecture](language-design/foundations/OK-001-project-vision-and-architecture.md) | Origins, name, world-description goals, AI/human collaboration, initial architecture, phased roadmap, constraints, and open questions. | Initial concept record; vision and proposed architecture |
| [OK-002 v0.1.1: Language foundations and conceptual minimal specification](language-design/foundations/OK-002-language-foundations-and-minimal-specification.md) | Candidate vocabulary, mathematical descriptions, human and agent interfaces, examples, alternatives, and questions a future specification must answer. | Brainstorming draft; not a finalized specification |
| [OK-003 v0.1: Compilation and runtime architecture](language-design/foundations/OK-003-compilation-and-runtime-architecture.md) | Compiler and interpreter options, OntoKin intermediate representation, LLVM discussion, runtime responsibilities, renderer integration, and proposed experiments. | Brainstorming draft; architectural proposal |

Read older statements in their dated context. Their sphere-first experiments, physics-as-extension framing, proposed future document sequence, and earlier naming notes are preserved historical material. The later PRD and capability definition explicitly discuss how the direction evolved. OK-LANG-001 defines the adopted core syntax; earlier syntax remains illustrative history. OK-ENG-001 selects direct evaluation in Python for the reference prototype. OK-ENG-002 adds the experimental GLB adapter and visible recorded playback. Production compilation, LLVM, physics-engine, renderer, and storage choices remain open.

The historical roadmap reserves **OK-004** for renderer integration. Existing document identifiers are retained. The new filenames remove package-name clutter; version information remains inside each document. In particular, `OntoKin_PRD_v0.md` is now `OK-PRD-001-product-requirements.md`, and its content remains version 0.2.

### Alternate edition and diagram files

OK-003 also has an [HTML edition](language-design/foundations/OK-003-compilation-and-runtime-architecture.html). It is another reading format of the same record. The Markdown edition includes its document metadata; the HTML includes screen and print styling. For offline reading, download the repository, then open the HTML file in a browser while keeping the adjacent `diagrams` folder in place.

Every original diagram file is retained. PNG files are raster images; SVG files are vector images. DOT files are the editable Graphviz sources supplied for OK-003. The alternatives below are formats of six figures, not separate specifications.

| Parent document and figure | PNG | SVG | DOT source |
| --- | --- | --- | --- |
| OK-001: Founding architecture | [PNG](language-design/foundations/diagrams/OntoKin_001_Architecture_Diagram.png) | [SVG](language-design/foundations/diagrams/OntoKin_001_Architecture_Diagram.svg) | Not supplied |
| OK-002: Authoring to execution | [PNG](language-design/foundations/diagrams/OK-002-Figure-01-Authoring-to-Execution.png) | [SVG](language-design/foundations/diagrams/OK-002-Figure-01-Authoring-to-Execution.svg) | Not supplied |
| OK-002: Conceptual language core | [PNG](language-design/foundations/diagrams/OK-002-Figure-02-Conceptual-Language-Core.png) | [SVG](language-design/foundations/diagrams/OK-002-Figure-02-Conceptual-Language-Core.svg) | Not supplied |
| OK-003: Compiler and package | [PNG](language-design/foundations/diagrams/OK-003-Figure-01-Compiler-and-Package.png) | [SVG](language-design/foundations/diagrams/OK-003-Figure-01-Compiler-and-Package.svg) | [DOT](language-design/foundations/diagrams/OK-003-Figure-01-Compiler-and-Package.dot) |
| OK-003: Runtime and renderer | [PNG](language-design/foundations/diagrams/OK-003-Figure-02-Runtime-and-Renderer.png) | [SVG](language-design/foundations/diagrams/OK-003-Figure-02-Runtime-and-Renderer.svg) | [DOT](language-design/foundations/diagrams/OK-003-Figure-02-Runtime-and-Renderer.dot) |
| OK-003: Backend choices | [PNG](language-design/foundations/diagrams/OK-003-Figure-03-Backend-Choices.png) | [SVG](language-design/foundations/diagrams/OK-003-Figure-03-Backend-Choices.svg) | [DOT](language-design/foundations/diagrams/OK-003-Figure-03-Backend-Choices.dot) |

## Keep the collection organized

- Put product purpose, capabilities, and required outcomes in `product/`. Put proposed language meanings and formal language work in `language-design/`. Put implementation decisions, conformance plans, and measured results in `engineering/`.
- Keep a stable document ID, version, date, purpose, and review state inside each document. Retain an existing ID when moving a file. An editorial move does not approve a proposal or advance implementation status.
- Keep founding records identifiable as historical sources. Record a changed decision and its relationship to earlier work explicitly, rather than silently rewriting its history.
- Link to the source responsible for a subject. Avoid copying full requirement tables or semantic rules into new summaries. A summary helps navigation; it cannot replace the detailed definition.
- Preserve references, diagrams, examples, and decision rationale when revising a document. When editing OK-003, review both its Markdown and HTML editions and their shared figures.
- Use relative links for current repository navigation and retain commit-pinned URLs where they support historical claims. Recheck links and anchors after renaming files or headings.
- Add a new guide entry when a substantive document is created. Keep the core grammar, examples, diagnostics, and expected outcomes synchronized with OK-LANG-001. Record language clarifications explicitly and keep measured implementation evidence separate from expected results and historical design coverage.

## Reorganization evidence and original navigation

The October 17, 2026 reorganization preserved the six substantive records that existed at that point. It combined package navigation here and retained the replaced navigation in full. It also accounted for the separate README texts on the existing semantics draft branch; the semantic document itself was already identical on `main`. OK-LANG-001 was subsequently added as the seventh substantive record, followed by OK-ENG-001 as the eighth and OK-ENG-002 as the ninth. The earlier preservation evidence remains unchanged; later engineering work has its own decision and verification record.

| Evidence | Purpose |
| --- | --- |
| [Requirements, implementation plan, and results](maintenance/reorganization-2026-10-17/reorganization-record.md) | Explains the task, decisions, completed steps, and verification. |
| [Source map](maintenance/reorganization-2026-10-17/source-map.json) | Maps every original file and Markdown section to its destination, with hashes and exact editorial transformations. |
| [Original navigation](maintenance/reorganization-2026-10-17/navigation-history.md) | Retains all four original main-branch READMEs and the two unique draft-branch READMEs verbatim. |
| [Preservation checker](maintenance/reorganization-2026-10-17/verify_reorganization.py) | Repeats the source-content and local-navigation checks offline. |

[Return to the project overview](../README.md).

## Reach delivery implementation work

The [recorded delivery checkpoints](engineering/reach-delivery-implementation.md)
and [independent reader implementation](engineering/reach-independent-validation.md)
describe branch work and its remaining execution obligations. Implementation
notes do not establish complete reach or product acceptance.

## Force workflows and recorded delivery

The [Agent/0.5 verification guide](engineering/force-agent-validation/README.md) and [source workflow example](../examples/force-agent/README.md) document finite-force inspection and repair. [OK-ENG-007](engineering/OK-ENG-007-native-force-glb-export.md) defines bounded GLB/0.5 recording, and the [delivery guide](../examples/force/README.md) documents actual export, artifact retrieval, independent native decoding and browser validation. Implementation and component results do not close complete F01–F12 acceptance; [STATUS](../STATUS.md) identifies the integrated evidence and next unmet gate.

The [Agent/0.5 local integration record](engineering/force-agent-local-validation-2026-10-19/README.md) retains the identified complete local run, unsuccessful attempts and resulting-main verification.

[OK-ENG-008](engineering/OK-ENG-008-force-release-conformance.md) defines the separately versioned complete local force-release audit. Its [literal test/source mapping](language-design/force-v0.1/conformance-local-v0.1.json) preserves the adopted expectations and earlier regression identities. The [runner](../tools/run_force_conformance.py) records actual named executions and independently audits retained artifacts; the [collector](../tools/build_force_release_evidence.py) only assembles exact immutable files and reference manifests. Missing or stale roles remain pending, and every required browser image needs its own identified visual review.


## Reusable reach action development

The [separate OK-LANG-006 adoption](language-design/planar-reach-v0.1/ADOPTION.md) establishes authority for the exact reviewed [language contract](language-design/OK-LANG-006-reusable-planar-reach-actions.md) and its original and supplementary corpora. Frozen draft labels remain historical. The [contract integration record](language-design/planar-reach-v0.1/contract-review/integration18.json) identifies the actual merge and fresh pure checks. Runtime implementation, all R01–R12/Q01–Q22 obligations and the complete [finite release gate](language-design/planar-reach-v0.1/release-contract.md) remain pending.

The [source acceptance development record](engineering/reach-source-acceptance-validation/README.md)
retains fresh integration and regression runs, failed source-export probes,
legacy protocol-test corrections and the exact checkout recovery. Its source
corpus mapping and execution outcomes are distinct from complete release acceptance.
