# OntoKin

**An AI-native, object-oriented language for physical 3D models and animation.**

OntoKin (pronounced **ON-toh-kin**) is a proposed programming language designed primarily for AI agents to create reusable objects, characters, and animations. An agent describes an object's form, parts, appearance, physical properties, mechanical connections, and intended actions. The language system supplies supported construction and behavior. People can inspect the definitions, review the results, and direct changes.

The current direction begins with exterior 3D models and short animations. Those objects should remain reusable in larger scenes, video games, and eventually more complex virtual worlds. Physics and mechanics are central to the design; mathematics gives those descriptions precise meaning.

> **Project status:** Conceptual language design. The product requirements, capability definition, and semantic model are review drafts. This repository does not yet provide a working OntoKin compiler, runtime, or renderer.

## Start reading

Use the [documentation guide](docs/README.md) for the full reading order, document status, diagrams, and earlier design records.

| Question | Document |
| --- | --- |
| What should OntoKin create, and what is the initial focus? | [OK-CAP-001: Modeling, motion, and object structure](docs/product/OK-CAP-001-modeling-motion-and-object-structure.md) |
| What must the intended product support? | [OK-PRD-001: Product requirements](docs/product/OK-PRD-001-product-requirements.md) |
| What do objects, movement, mechanics, and physics mean? | [OK-SEM-001: Core object, motion, and physics semantics](docs/language-design/OK-SEM-001-core-object-motion-and-physics-semantics.md) |

The documents are organized into **Product** and **Language design**. The [founding records](docs/README.md#founding-design-records) retain the original vision, language exploration, and architecture options. Their dates and proposal status remain visible. The guide explains how that earlier work relates to the current modeling direction.

## Current design work

The semantic model proposes rules for classes, instances, nested parts, frames, joints, physical participation, and concurrent actions. Its main example follows a character walking, turning its head, using one hand, and carrying and releasing a prop. The rules and behavior checks are proposed meanings and expected outcomes, not implementation test results.

Language syntax and implementation choices remain later work. OntoKin describes objects and behavior; execution evaluates their state over time; rendering turns the evaluated scene into visible images. The existing documents explore how those responsibilities might be implemented without selecting a final compiler, physics engine, or renderer.

## About the name

**OntoKin** combines **onto-**, referring to ontology, or what exists and how entities relate, with **kin-**, referring to kinematics, or motion. Earlier drafts used the working name *OntoKine*; **OntoKin** is the current project name.

The [documentation reorganization record](docs/maintenance/reorganization-2026-10-17/reorganization-record.md) contains the requirements, implementation plan, source mapping, and preservation checks for the October 17, 2026 organization change.
