# OntoKin

**An AI-native, object-oriented language for physical 3D models and animation.**

OntoKin (pronounced **ON-toh-kin**) is a proposed programming language designed primarily for AI agents to create reusable objects, characters, and animations. An agent describes an object's form, parts, appearance, physical properties, mechanical connections, and intended actions. The language system supplies supported construction and behavior. People can inspect the definitions, review the results, and direct changes.

The current direction begins with exterior 3D models and short animations. Those objects should remain reusable in larger scenes, video games, and eventually more complex virtual worlds. Physics and mechanics are central to the design; mathematics gives those descriptions precise meaning.

> **Project status:** Formal language design. OK-LANG-001 now defines a proposed core language, complete source grammar, agent contracts, and validation fixtures. The product, capability, semantic, and language documents remain review drafts. This repository does not yet provide a working OntoKin compiler, runtime, or renderer.

## Start reading

Use the [documentation guide](docs/README.md) for the full reading order, document status, diagrams, and earlier design records.

| Question | Document |
| --- | --- |
| What should OntoKin create, and what is the initial focus? | [OK-CAP-001: Modeling, motion, and object structure](docs/product/OK-CAP-001-modeling-motion-and-object-structure.md) |
| What must the intended product support? | [OK-PRD-001: Product requirements](docs/product/OK-PRD-001-product-requirements.md) |
| What do objects, movement, mechanics, and physics mean? | [OK-SEM-001: Core object, motion, and physics semantics](docs/language-design/OK-SEM-001-core-object-motion-and-physics-semantics.md) |
| How does an agent express those meanings in valid code? | [OK-LANG-001: Core language specification](docs/language-design/OK-LANG-001-core-language-specification.md) |

The documents are organized into **Product** and **Language design**. The [founding records](docs/README.md#founding-design-records) retain the original vision, language exploration, and architecture options. Their dates and proposal status remain visible. The guide explains how that earlier work relates to the current modeling direction.

## Current design work

The [core language specification](docs/language-design/OK-LANG-001-core-language-specification.md) reviews all 28 proposed semantic rules and defines `core-0.1`: typed classes and pure methods, independently instantiated parts, explicit frames and units, prescribed joints, concurrent action channels, exact event ordering, and a limited gravity/release contract.

Start with [independently moving parts](docs/language-design/core-v0.1/01-independent-parts.ok), then [gravity and release](docs/language-design/core-v0.1/02-gravity-and-release.ok). Two further programs check rotational velocity transfer and the distinction between ownership and following. The [validation manifest](docs/language-design/core-v0.1/validation-cases.json) supplies 43 source cases and ten agent-operation cases with expected outcomes. They are design fixtures, not executed OntoKin conformance tests.

Compiler, runtime, physics-engine, and renderer choices remain later work. The next engineering step can assess those choices against the language's written behavior and diagnostics. Contact, dynamic articulated mechanisms, general body dynamics, deformation, and delivery remain visible future requirements.

## About the name

**OntoKin** combines **onto-**, referring to ontology, or what exists and how entities relate, with **kin-**, referring to kinematics, or motion. Earlier drafts used the working name *OntoKine*; **OntoKin** is the current project name.

The [documentation reorganization record](docs/maintenance/reorganization-2026-10-17/reorganization-record.md) contains the requirements, implementation plan, source mapping, and preservation checks for the October 17, 2026 organization change.
