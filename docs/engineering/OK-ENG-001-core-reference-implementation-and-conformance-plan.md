---
project: OntoKin
document_id: OK-ENG-001
title: OntoKin Core Reference Implementation and Conformance Plan
version: 0.1
date: 2026-10-17
status: experimental-reference-implementation
document_type: engineering-plan-and-evidence
repository: https://github.com/Omegapy/OntoKin
reviewed_source_commit: 1a9a52a7eedf4170d864c0d37d0f32ae69bf9a69
language_profile: core-0.1
language_baseline: OK-LANG-001 engineering_baseline 2026-10-17
implementation_language: Python 3.11 or later
runtime_dependencies: Python standard library
production_architecture: not-selected
---

# OntoKin core reference implementation and conformance plan

## 1. Objective and authority

Build a small program that reads OntoKin source, checks its meaning, and calculates the state it specifies. The first demonstration is independently moving parts; the second is a carried sphere released into gravity. A valid program produces inspectable state at requested times. An invalid or unsupported request produces a structured diagnostic with its source location and repair guidance.

The project owner's October 17, 2026 instruction authorizes the engineering work and adoption of the twelve decisions in [OK-LANG-001 section 2.2](../language-design/OK-LANG-001-core-language-specification.md#22-material-decisions-and-remaining-approval-scope). The [language baseline addendum](../language-design/OK-LANG-001-core-language-specification.md#16-engineering-baseline-adoption-and-clarifications) records that adoption. The broader [PRD](../product/OK-PRD-001-product-requirements.md), [capability definition](../product/OK-CAP-001-modeling-motion-and-object-structure.md), and [semantic model](../language-design/OK-SEM-001-core-object-motion-and-physics-semantics.md) retain their draft status and requirements.

This is an experimental reference implementation: readable software used to test the language's meaning. Python is a convenient implementation language for this experiment. OntoKin source remains its own language; it is never treated as Python source. The prototype does not commit the production system to Python, a compiler backend, a physics engine, or a renderer.

## 2. Baseline decisions and resolved issues

All D-01 through D-12 are retained. The implementation uses the existing `.ok` grammar, explicit units and frames, stable occurrence identities, nominal classes, pure methods, independently controlled channels, prescribed joints, and the uniform-sphere release contract. The first prototype evaluates these declarations without rendering them.

| Clarification | Decision and rationale | Governing evidence |
| --- | --- | --- |
| Tween limit phase | Type, frame, numeric, and duration checks occur during elaboration. A target outside its joint's mandatory range is an admission failure, even when timeline preflight detects it early. | LANG section 10.3; C-01; N14 |
| Design fixtures and measured results | Keep the existing fixture sources, replacements, expected outcomes, and original design-status metadata. Record actual execution in a separate report. | LANG C-02; [validation manifest](../language-design/core-v0.1/validation-cases.json) |
| Agent contract versus local commands | Implement the requested file-based parser, validator, and evaluator. Track service editing, accepted-revision transactions, retry, cancellation, and pagination separately. | LANG C-03; A01–A10 |
| Numerical support | Preserve the language's exact numeric requirements. Report finite test evidence and unproved arithmetic guarantees explicitly. | LANG C-04; sections 5.2, 5.4, and 13.5 |

No fixture expectation may be changed merely to make a failing implementation pass. A newly discovered specification defect needs a recorded clarification or semantic revision, a rationale, and a regression case. A semantic revision must identify the affected programs and profiles.

## 3. Implementation boundaries

| Component | Responsibility | Boundary |
| --- | --- | --- |
| Lexer and parser | Read UTF-8 `.ok` files and produce an abstract syntax tree, which records the source's declarations and expression structure. Preserve original byte spans. | Syntax acceptance makes no claim about valid types, relationships, or behavior. |
| Validator and elaborator | Bind names and stable keys; check types, units, frames, inheritance, access, overrides, dependencies, finite parts, body descriptions, sites, and relationships. Produce an inspectable resolved model. | Ownership, spatial following, and joints remain distinct records. Initialization must not apply an owner's transform automatically. |
| Reference evaluator | Evaluate root translation and spin, hinge/slider coordinates, fixed/grip transforms, action lifecycle, uniform gravity, and release. | Prescribed joints provide no dynamic load solution. Only a homogeneous sphere has a dynamic body contract. |
| Diagnostics and command-line interface | Expose validation results, resolved data, numerical samples, source identity, and support limits as JSON. | The CLI is not the `ontokin.agent/0.1` service. It supplies no external delivery contract. |
| Conformance runner | Materialize the existing candidates and compare actual diagnostics and sampled state against independent expectations. | The runner may know fixture IDs; the parser, validator, and evaluator must process their source without consulting expected answers. |

The implementation lives in [the `ontokin` package](../../ontokin/). Its in-memory syntax and resolved model are internal Python structures. No persistent intermediate representation or binary application interface is standardized by this milestone. This uses the responsibility separation explored in [OK-003](../language-design/foundations/OK-003-compilation-and-runtime-architecture.md), while recording the actual prototype choice here instead of changing that historical proposal.

### 3.1 Time and release

Schedule events using the exact rational values of canonical source timestamps. A decimal CLI time is an exact decimal request. For example, a request for `0.1` seconds is not the same instant as the binary64 value of source `0.1[s]`; boundary times must remain inspectable. There is no epsilon-based grouping of events.

At each boundary, save the incoming state, process natural action completions, then stage the authored event sequence. Expose an after-state only when the complete sequence succeeds. A failed sequence must not leave an accepted partial release or channel change. Before/after sampling includes natural completions as well as authored events. [LANG-020](../language-design/OK-LANG-001-core-language-specification.md#93-event-ordering-and-boundary-sampling--lang-020) defines the ordering.

Release transfers the center-of-mass position, orientation, linear velocity, and angular velocity from the complete incoming transform chain. Include the rotational offset term and any changing local joint coordinate. Retain identity, ownership, matter, and outgoing massless followers. The released body then follows the free-sphere equations without another carrier transform or added carrier velocity. These obligations come from [LANG-017](../language-design/OK-LANG-001-core-language-specification.md#83-release-transaction--lang-017), rather than a particular physics engine.

### 3.2 Explicit support limits

The prototype evaluates mathematical sphere/box geometry descriptions and physical sphere descriptions. It does not produce meshes, pictures, animation files, or a game-engine integration. Collision response is disabled; there is no implicit ground plane. A negative height in a free-fall example is therefore expected.

Contact, dynamic articulated joints, mechanical loops, actuators, general external forces or torque, deformation, liquids, locomotion, tracking, imports, and runtime object allocation remain outside `core-0.1`. A meaningful unsupported request receives the applicable support result. A misspelled name or incompatible unit remains invalid source.

The Python numeric implementation is experimental. Passing the bounded fixtures does not establish correctly rounded transcendental functions for every input, exact internal rotation representation, all finite-range interval properties, long-duration stability, or bit-identical results across hosts. These are preserved language obligations or future support claims requiring additional evidence. This distinction must be present in the implementation's support information.

### 3.3 Reference work budgets

The prototype has explicit work budgets so a large source token or recursively expanded description receives a structured result. These limits belong to this implementation; they do not change the language's types or prove that a stopped expansion is logically cyclic.

| Work item | Prototype limit |
| --- | --- |
| Source file | 2,000,000 UTF-8 bytes |
| Lexical tokens | 200,000 |
| Expanded object occurrences | 10,000 |
| Numeric literal conversion | 4,096 characters; absolute decimal exponent at most 4,096 |
| Unit expression processing | 4,096 tokens and 65,536 characters |
| Exact sample time processing | 4,096 decimal digits of the represented request |
| Requested samples | 1,000 |
| Returned state records | 100,000 combined object, frame, joint, and action records across samples |

Budget exhaustion returns `OKL-E-RESOURCE` with category `resource_limit`. Provable `Int` overflow remains `OKL-E-NUMERIC`, and a unit exponent outside the core's declared support remains `OKL-E-CAPABILITY-UNSUPPORTED`. Parser/evaluator nesting exhaustion likewise receives a structured resource result. No refusal from a work budget should be mislabeled as a completed validation or a language-dependency cycle.

## 4. Build sequence and conformance gates

| Gate | Work | Required evidence |
| --- | --- | --- |
| G1: Stable core baseline | Review all documents; adopt D-01–D-12; record execution clarifications. | LANG baseline addendum; unchanged grammar and original expected outcomes; preserved broader requirements. |
| G2: Source processing | Implement the parser, validator, and structured diagnostics. | The four complete source files are processed; lexical/syntax negatives fail at their specified phase; later negatives reach their relevant checks. |
| G3: Independent movement | Evaluate P01, including inheritance, pure calls, nested parts, fixed/hinge/slider relations, and disjoint channels. | Compare the root, head, and hand at specified times; check retained endpoints, identity, and parameter values. |
| G4: Gravity and release | Evaluate P02 and P03, then ownership/following in P04. | Position and velocity continuity; rotational offset velocity; continuing free motion after carrier stop; correct mass accounting and no duplicated ownership transform. |
| G5: Executed conformance | Run all 43 source candidates and the independent numerical/state assertions. Add regressions for discovered defects. | Measured report with actual outcomes, expected phases/codes, comparisons, and failures; meaningful tests pass. |
| G6: Architecture assessment | Review what the prototype establishes and what remains unproved. | Production decision table in section 7; explicit next evidence required before adopting a backend or integration. |

The existing corpus contains 12 expected-valid programs, 29 invalid or conflicting programs, and two unsupported requests. Of the 43 candidates, four should fail lexing or parsing; the other 39 must proceed to later checks. Exact replacement matching is part of the test input contract. Failing to materialize a candidate is a fixture error, not a language-validation result.

Diagnostic evidence must check the actual code and phase, source revision, original UTF-8 byte boundaries, identified elements where resolvable, rule IDs, and repair guidance. Merely returning a JSON object of the correct shape is insufficient. No diagnostic or suggested repair changes the source automatically.

Numerical checks use [LANG section 13.5](../language-design/OK-LANG-001-core-language-specification.md#135-numeric-comparison-and-actual-editorial-checks): maximum component error of `1e-9` for position, linear velocity, and angular velocity in their canonical units; orientation error of `1e-9` radians; other scalar error at most `max(1e-12, 1e-12 × abs(reference))`. Identity, authority, lifecycle, event ordering, and diagnostic code must match exactly. Tests must measure rotation angle rather than raw quaternion component differences.

Expected outcomes stated as prose in the manifest also need assertions. This includes independent instance overrides, retained stable keys after a rename, held local poses after stopping the root, active gravity while an unrelated action is paused, scene ownership after release, and the unavailable sample beyond P04's horizon. A source case does not fully pass because it parsed or returned a success flag.

## 5. Reproduce the prototype

Use Python 3.11 or later from the repository root. No external runtime package is needed. Editable installation is optional; running the module from the checkout is sufficient.

```bash
python3 -m ontokin check docs/language-design/core-v0.1/01-independent-parts.ok
python3 -m ontokin evaluate docs/language-design/core-v0.1/01-independent-parts.ok --times 0 0.5 1 1.5 2 3 --side after
python3 -m ontokin evaluate docs/language-design/core-v0.1/02-gravity-and-release.ok --times 1 --side before
python3 -m ontokin evaluate docs/language-design/core-v0.1/02-gravity-and-release.ok --times 1 1.5 2 --side after
python3 -m ontokin evaluate docs/language-design/core-v0.1/03-rotating-release.ok --times 1 1.5 2 --side after
python3 -m ontokin conformance --output docs/engineering/conformance-results.json
python3 -m unittest discover -s tests -v
```

`check` defaults to the `evaluated` level, including validation and timeline preflight through the scene horizon. `--level represented` requests source representation checks. `--level constructed` additionally resolves the initial world state at `0/before`, before starting authored actions. A higher requested result must not be reported as successful merely because a lower level succeeded. `evaluate` returns JSON state at the requested times; `--side before` and `--side after` select event-boundary observations.

The [root quick start](../../README.md) documents the public commands and current limits. The conformance command overwrites only its explicitly named report. Normal validation and sampling leave the source unchanged.

## 6. Measured evidence

The [conformance report](conformance-results.json) records actual source-case and state-check results for the checked implementation and environment. It is distinct from the [original expected-outcome manifest](../language-design/core-v0.1/validation-cases.json) and the [design coverage register](../language-design/core-v0.1/requirement-coverage.json). The original artifacts retain their pre-implementation status fields and do not report current execution status.

<!-- BEGIN MEASURED RESULTS -->
The October 17, 2026 local execution used **CPython 3.12.14 on Linux**. The report records the implementation source hash, original fixture-manifest hash, environment, actual diagnoses, and individual comparisons.

| Verification | Actual result |
| --- | --- |
| Four complete base programs | Parsed, semantically validated, and evaluated from their original `.ok` source |
| Published source corpus | **43/43 cases passed; 0 failed**: 12 valid, 29 invalid/conflicting, and two unsupported outcomes matched their expectations |
| Conformance comparisons | **694 assertions passed**, covering numerical state, discrete state, prose observations, diagnostics, and represented-level retention where required |
| Automated Python test suite | **69 tests passed**, including independent parser, validator, evaluator, diagnostic, resource-boundary, and CLI contracts |
| Package smoke check | A wheel built and installed offline without runtime dependencies; the installed command validated P01 from outside the checkout |
| Original documentation preservation | **29/29 source artifacts and 233 sections verified**; all original PRD/CAP/SEM registry rows preserved |
| Repository navigation | **198 local links and 59 anchors checked across 13 documents**; no failures |

The independent-parts demonstration checks simultaneous root movement, head rotation, and hand translation, including their retained endpoints. Gravity/release checks incoming-state continuity, the released sphere's continued motion after its carrier stops, and velocity transferred through rotating and changing joint chains. Regression checks also exercise invalid unused branches, lexical private access, nested parameter precedence, oversized numeric tokens, phase-correct failures, and construction before zero-time actions.

The [GitHub Actions workflow](../../.github/workflows/reference.yml) is configured for Python 3.11, 3.12, and 3.13. These are configured targets; this record does not claim remote workflow execution, other operating systems, or cross-host numerical certification. The measured support remains the bounded local evidence above.
<!-- END MEASURED RESULTS -->

A01–A10 remain the original agent-operation scenarios. Local equivalents can test repeated read-only sampling, requested support levels, or vector re-expression; they do not establish the full versioned service, cursor, accepted-revision, retry, or cancellation contracts. No agent-protocol conformance claim is made by a passing source report.

The 226 PRD requirements and 18 capability requirements keep their original design dispositions. Passing this milestone supplies narrower evidence toward selected requirements. It does not complete the broad product scenarios for characters, vehicles, contacts, deformation, rendering, or delivery, and it does not measure the claimed benefit to AI authoring against another tool.

## 7. Production architecture assessment

| Question | Decision for the prototype | Production decision and evidence still needed |
| --- | --- | --- |
| Front end | Keep original source spans, a syntax tree, and a resolved semantic model separate. | Retain this responsibility boundary. Before freezing a serialized representation, specify schema versioning, source mapping, and migration behavior. |
| Implementation language | Use Python and its standard library for readable reference behavior and an offline workflow. | Keep the reference available when evaluating another implementation. Select a production language using measured workload costs, packaging needs, diagnostics, platform coverage, and integration constraints. |
| Interpretation or compilation | Directly evaluate the limited typed model and analytic trajectories. | Native compilation or LLVM remains a candidate when a representative workload identifies a justified need. Re-run the same independent expectations against any backend. |
| Numerical machinery | Use the disclosed experimental arithmetic and exact event-time scheduling. | Prove the required rounding and range behavior or define an explicitly revised numerical contract; fixture agreement alone is insufficient. |
| Physics engine | Use the specified analytic gravity and uniform-sphere rotation equations; prescribed joints are direct transforms. | Evaluate an engine only after defining contact, dynamic-joint, general-inertia, force, and coupling requirements. Check actual property enforcement, state transfer, and failure reporting. |
| Rendering and delivery | Publish headless state with stable identity and explicit units. | Add one adapter that consumes that state without acquiring a competing motion authority. Measure geometry, timing, coordinate conversion, and destination retention under a named contract. |
| Agent service | Provide repeatable local file operations and structured diagnostics. | Implement revision-safe source edits, request identity, cancellation, bounded inspection, and A01–A10 before advertising the service contract. |

The next engineering work should be selected from measured failures and these remaining contracts. Broad compiler, physics-engine, or rendering claims require their own relevant evidence. The earlier architectural alternatives in OK-003 remain available; the prototype tests language behavior before those choices become commitments.

## 8. Repository review and preservation

The review began at commit `1a9a52a7eedf4170d864c0d37d0f32ae69bf9a69`. It covered all seven substantive records, both navigation documents, the alternate HTML edition, the six figures in every supplied format, the four maintenance files, and every language companion artifact.

| Material reviewed | Use in this engineering work |
| --- | --- |
| PRD and CAP, including all requirement and acceptance rows | Preserve the full product direction, exterior-modeling priority, agent responsibility, stage-specific success, and scope limits. |
| SEM-01–SEM-28 and SC-01–SC-24 | Check identity, independent ownership and pose relations, physical participation, control, and release against the formal core. |
| OK-LANG-001 and its nine companion files | Adopt D-01–D-12; check grammar, four complete source files, all 43 source cases, A01–A10, diagnostic schema/example, and all PRD/CAP coverage entries. |
| OK-001, OK-002, OK-003, HTML edition, six SVG/PNG figures and three DOT sources | Retain historical alternatives and their rationale; verify that the headless step follows the authorized current scope. All six PNG figures were visually inspected. |
| Navigation history, source map, reorganization record, and preservation checker | Preserve dated decisions and complete earlier content. The checker verifies original bytes/sections and active local links; it does not establish language conformance. |

The original preservation check recovered all 29 mapped sources and verified all 233 source sections before this engineering edit. The broader requirements, semantic record, foundations, diagrams, HTML edition, and maintenance evidence are not rewritten. Current navigation and the explicit LANG baseline change record identify the new engineering work.

Run the existing preservation check independently of the language tests:

```bash
python3 docs/maintenance/reorganization-2026-10-17/verify_reorganization.py
```

This document records the new implementation decisions and evidence. It does not modify the older reorganization hashes or imply that the original documentation work had already implemented OntoKin.
