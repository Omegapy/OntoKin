# OntoKin

**An AI-native, object-oriented language for physical 3D models and animation.**

OntoKin (pronounced **ON-toh-kin**) is a programming language under development, designed primarily for AI agents to create reusable objects, characters, and animations. An agent describes an object's form, parts, appearance, physical properties, mechanical connections, and intended actions. The language system supplies supported construction and behavior. People can inspect the definitions, review the results, and direct changes.

The current direction begins with exterior 3D models and short animations. Those objects should remain reusable in larger scenes, video games, and eventually more complex virtual worlds. Physics and mechanics are central to the design; mathematics gives those descriptions precise meaning.

> **Project status:** Experimental headless reference prototype. The repository includes a working parser, typed validator, and semantic evaluator for the bounded `core-0.1` demonstrations. The twelve core language decisions are adopted as an engineering baseline. Broader product and semantic requirements retain their draft status. Rendering, external delivery, and a production compiler are future work.

## Run the prototype

Use **Python 3.11 or later** from this repository's root. No external runtime dependency or installation is required.

```bash
python3 -m ontokin check docs/language-design/core-v0.1/01-independent-parts.ok
python3 -m ontokin evaluate docs/language-design/core-v0.1/01-independent-parts.ok --times 0 1 2 3
python3 -m ontokin evaluate docs/language-design/core-v0.1/02-gravity-and-release.ok --times 1 1.5 2
```

`check` reads the source, validates its static definitions, and checks the complete authored timeline. `evaluate` returns JSON samples containing object positions, orientations, velocities, ownership, physical assumptions, joint coordinates, and action status. The source file is unchanged. A SHA-256 source revision ties the results and diagnostic byte spans to the exact input.

The independently moving parts example produces these world positions:

| Time | Head position, m | Hand position, m |
| --- | --- | --- |
| 1 s | (1, 1, 0) | (1.5, 0.5, 0) |
| 2 s | (2, 1, 0) | (2.75, 0.5, 0) |
| 3 s | (2, 1, 0) | (2.75, 0.5, 0) |

The head retains its 90-degree local yaw when that action completes. The hand continues its independent slider motion while the root moves. The [executed conformance report](docs/engineering/conformance-results.json) checks these values and the other published expectations.

### Commands and failure results

| Command | Purpose |
| --- | --- |
| `python3 -m ontokin capabilities` | Inspect implemented operations, output levels, physical assumptions, and numerical limits. |
| `python3 -m ontokin check FILE.ok` | Validate and preflight the declared timeline. |
| `python3 -m ontokin check FILE.ok --level represented` | Check source representation while disclosing unresolved support requests. |
| `python3 -m ontokin check FILE.ok --level constructed` | Derive the initial world state before time-zero actions, without requiring later actions to be admissible. |
| `python3 -m ontokin evaluate FILE.ok --times 1 1.5 2 --side before` | Sample the incoming side of an event or natural completion. The default side is `after`. |
| `python3 -m ontokin evaluate FILE.ok --times 0.5 --object first.ball --frame first.frame` | Inspect one object in another frame. Velocity remains measured relative to world and is expressed in the requested axes. |
| `python3 -m ontokin conformance --output docs/engineering/conformance-results.json` | Execute all 43 published source cases and write their measured results. |

JSON diagnostics contain the stable error code, failure phase, source revision, original UTF-8 byte span, governing rules, and repair guidance. Admission and transition failures found during preflight retain the time and phase of the authored failure. Receiving a suggested repair does not apply it.

Exit status is `0` for success, `1` for I/O or conformance-run failure, `2` for an invalid/conflicting source, unavailable sample, numerical failure, or resource limit, and `3` for an unsupported requested capability/level. `--level delivered` returns unsupported; no lower-level success substitutes for delivery.

Sample times written on the command line are exact decimal seconds. Source time quantities first become canonical binary64 values, and event scheduling preserves those values exactly. A decimal sample of `0.1` is therefore slightly earlier than an event authored as `0.1[s]`. Returned `boundary_times_seconds` gives the exact event and completion times; use those strings for exact boundary inspection.

For an optional installed `ontokin` command, install the checkout in a Python environment with `python3 -m pip install -e .`. The conformance command expects this repository's fixture directory; a packaged installation can specify it with `--fixtures PATH`.

### Verification

```bash
python3 -m unittest discover -s tests -v
python3 -m ontokin conformance --output /tmp/ontokin-conformance.json
python3 docs/maintenance/reorganization-2026-10-17/verify_reorganization.py
```

The tests check source-to-state behavior, independent numerical expectations, diagnostics, event boundaries, release from moving joint chains, parameter scope, and command-line failures. The [GitHub Actions workflow](.github/workflows/reference.yml) is configured to run these commands on Python 3.11, 3.12, and 3.13. Actual execution evidence and its limitations are recorded in [OK-ENG-001](docs/engineering/OK-ENG-001-core-reference-implementation-and-conformance-plan.md#6-measured-evidence).

## Start reading

Use the [documentation guide](docs/README.md) for the full reading order, document status, diagrams, and earlier design records.

| Question | Document |
| --- | --- |
| What should OntoKin create, and what is the initial focus? | [OK-CAP-001: Modeling, motion, and object structure](docs/product/OK-CAP-001-modeling-motion-and-object-structure.md) |
| What must the intended product support? | [OK-PRD-001: Product requirements](docs/product/OK-PRD-001-product-requirements.md) |
| What do objects, movement, mechanics, and physics mean? | [OK-SEM-001: Core object, motion, and physics semantics](docs/language-design/OK-SEM-001-core-object-motion-and-physics-semantics.md) |
| How does an agent express those meanings in valid code? | [OK-LANG-001: Core language specification](docs/language-design/OK-LANG-001-core-language-specification.md) |
| What does the first prototype implement, and how is it checked? | [OK-ENG-001: Core reference implementation and conformance plan](docs/engineering/OK-ENG-001-core-reference-implementation-and-conformance-plan.md) |

The documents are organized into **Product**, **Language design**, and **Engineering**. The [founding records](docs/README.md#founding-design-records) retain the original vision, language exploration, and architecture options. Their dates and proposal status remain visible. The guide explains how that earlier work relates to the current modeling direction.

## Language and implementation scope

The [core language specification](docs/language-design/OK-LANG-001-core-language-specification.md) reviews all 28 proposed semantic rules and defines `core-0.1`: typed classes and pure methods, independently instantiated parts, explicit frames and units, prescribed joints, concurrent action channels, exact event ordering, and a limited gravity/release contract.

Start with [independently moving parts](docs/language-design/core-v0.1/01-independent-parts.ok), then [gravity and release](docs/language-design/core-v0.1/02-gravity-and-release.ok). Two further programs check rotational velocity transfer and the distinction between ownership and following. The [validation manifest](docs/language-design/core-v0.1/validation-cases.json) preserves the original 43 source cases and ten agent-operation cases with their expected outcomes and historical design status. The separate [measured report](docs/engineering/conformance-results.json) records current source execution. No persistent agent editing/retry service or A01–A10 protocol certification is supplied.

The reference uses Python's standard library and analytic motion equations. Production compiler, runtime, physics-engine, and renderer choices remain open. Contact, dynamic articulated mechanisms, general body dynamics, deformation, and delivery remain visible future requirements.

The physical subset is explicit: uniform gravity, free homogeneous solid spheres, and externally prescribed connections without a load solution. Collision response is disabled and there is no ground plane. A sphere can pass below zero height without a collision. Passing the bounded fixtures does not certify correctly rounded transcendental functions for every input, exact internal rotations, rigorous interval bounds for all rotating mechanisms, long-duration accuracy, or the broader product. [OK-ENG-001](docs/engineering/OK-ENG-001-core-reference-implementation-and-conformance-plan.md) records these limits and the production decisions that still need evidence.

## About the name

**OntoKin** combines **onto-**, referring to ontology, or what exists and how entities relate, with **kin-**, referring to kinematics, or motion. Earlier drafts used the working name *OntoKine*; **OntoKin** is the current project name.

The [documentation reorganization record](docs/maintenance/reorganization-2026-10-17/reorganization-record.md) contains the requirements, implementation plan, source mapping, and preservation checks for the October 17, 2026 organization change.
