# OntoKin documentation guide

Start with the capability definition, then use the PRD for detailed product requirements, the semantic model for proposed meanings, and OK-LANG-001 for the first formal source-language contract. All four are review drafts. The original vision and architecture records remain available in full for their rationale, examples, alternatives, and open questions.

## Current definition and reading order

| Read | Document | Role | Recorded status |
| --- | --- | --- | --- |
| 1 | [OK-CAP-001 v0.1: Modeling, motion, and object structure](product/OK-CAP-001-modeling-motion-and-object-structure.md) | The current modeling emphasis: reusable exterior objects, nested parts, physical meaning, and short animations, with larger worlds as the longer-term direction. | Draft for concept review |
| 2 | [OK-PRD-001 v0.2: Product requirements](product/OK-PRD-001-product-requirements.md) | Broad product outcomes, support contracts, required behavior, acceptance evidence, research, and unresolved choices. | Draft for product review |
| 3 | [OK-SEM-001 v0.1: Core object, motion, and physics semantics](language-design/OK-SEM-001-core-object-motion-and-physics-semantics.md) | Proposed rules connecting objects, ownership, spatial frames, mechanical relationships, physical behavior, and actions. | Conceptual language design; proposed for semantic review |
| 4 | [OK-LANG-001 v0.1: Core language specification](language-design/OK-LANG-001-core-language-specification.md) | Review of all 28 SEM rules; complete grammar, types, object and motion rules, agent contracts, source examples, and validation cases for `core-0.1`. | Formal language design; proposed normative draft; not implemented |

These documents answer related questions at different levels. A product requirement says what OntoKin should accomplish. A capability definition explains the intended objects and tasks. A semantic rule defines what an operation or relationship means. The language specification defines how source expresses a bounded subset of those meanings, how validity is decided, and which state a program should produce. Their behavior checks are expected outcomes for later work, not executed OntoKin tests.

### Core language companion files

The [core-v0.1 folder](language-design/core-v0.1/) contains the [complete EBNF](language-design/core-v0.1/ontokin-core.ebnf), four complete `.ok` programs, a [43-case validation manifest](language-design/core-v0.1/validation-cases.json) with ten agent-operation cases, a [diagnostic schema](language-design/core-v0.1/diagnostic.schema.json) and [synthetic example](language-design/core-v0.1/diagnostic-example.json), and a [coverage register](language-design/core-v0.1/requirement-coverage.json) for every PRD/CAP requirement. The specification explains the exact expected behavior and the limits of the editorial checks.

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
| Open design decisions | [CAP section 8](product/OK-CAP-001-modeling-motion-and-object-structure.md#8-efficiency-interoperability-and-the-next-definition), [PRD section 12](product/OK-PRD-001-product-requirements.md#12-decisions-deliberately-left-for-product-and-language-design), and [SEM: Decisions still open](language-design/OK-SEM-001-core-object-motion-and-physics-semantics.md#decisions-still-open) |

## Founding design records

The [foundations folder](language-design/foundations/) contains three distinct early records. Their content remains intact, including their dated proposals and decision registers. They are useful when tracing why the project took its current direction.

| Document | What it preserves | Recorded status |
| --- | --- | --- |
| [OK-001 v0.1.1: Project vision and initial architecture](language-design/foundations/OK-001-project-vision-and-architecture.md) | Origins, name, world-description goals, AI/human collaboration, initial architecture, phased roadmap, constraints, and open questions. | Initial concept record; vision and proposed architecture |
| [OK-002 v0.1.1: Language foundations and conceptual minimal specification](language-design/foundations/OK-002-language-foundations-and-minimal-specification.md) | Candidate vocabulary, mathematical descriptions, human and agent interfaces, examples, alternatives, and questions a future specification must answer. | Brainstorming draft; not a finalized specification |
| [OK-003 v0.1: Compilation and runtime architecture](language-design/foundations/OK-003-compilation-and-runtime-architecture.md) | Compiler and interpreter options, OntoKin intermediate representation, LLVM discussion, runtime responsibilities, renderer integration, and proposed experiments. | Brainstorming draft; architectural proposal |

Read older statements in their dated context. Their sphere-first experiments, physics-as-extension framing, proposed future document sequence, and earlier naming notes are preserved historical material. The later PRD and capability definition explicitly discuss how the direction evolved. OK-LANG-001 now proposes exact core syntax; earlier syntax remains illustrative history. No current draft selects an interpreter, LLVM, solver, renderer, or runtime storage design.

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

- Put product purpose, capabilities, and required outcomes in `product/`. Put proposed language meanings and formal language work in `language-design/`.
- Keep a stable document ID, version, date, purpose, and review state inside each document. Retain an existing ID when moving a file. An editorial move does not approve a proposal or advance implementation status.
- Keep founding records identifiable as historical sources. Record a changed decision and its relationship to earlier work explicitly, rather than silently rewriting its history.
- Link to the source responsible for a subject. Avoid copying full requirement tables or semantic rules into new summaries. A summary helps navigation; it cannot replace the detailed definition.
- Preserve references, diagrams, examples, and decision rationale when revising a document. When editing OK-003, review both its Markdown and HTML editions and their shared figures.
- Use relative links for current repository navigation and retain commit-pinned URLs where they support historical claims. Recheck links and anchors after renaming files or headings.
- Add a new guide entry when a substantive document is created. Keep the core grammar, examples, diagnostics, and expected outcomes synchronized with OK-LANG-001. Implementation architecture and prototype plans remain future work.

## Reorganization evidence and original navigation

The October 17, 2026 reorganization preserved the six substantive records that existed at that point. It combined package navigation here and retained the replaced navigation in full. It also accounted for the separate README texts on the existing semantics draft branch; the semantic document itself was already identical on `main`. OK-LANG-001 was subsequently added as the seventh substantive record; the earlier preservation evidence remains unchanged.

| Evidence | Purpose |
| --- | --- |
| [Requirements, implementation plan, and results](maintenance/reorganization-2026-10-17/reorganization-record.md) | Explains the task, decisions, completed steps, and verification. |
| [Source map](maintenance/reorganization-2026-10-17/source-map.json) | Maps every original file and Markdown section to its destination, with hashes and exact editorial transformations. |
| [Original navigation](maintenance/reorganization-2026-10-17/navigation-history.md) | Retains all four original main-branch READMEs and the two unique draft-branch READMEs verbatim. |
| [Preservation checker](maintenance/reorganization-2026-10-17/verify_reorganization.py) | Repeats the source-content and local-navigation checks offline. |

[Return to the project overview](../README.md).
