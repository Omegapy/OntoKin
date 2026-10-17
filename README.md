# OntoKin

**An AI-native, object-oriented language for physical 3D models and animation.**

OntoKin (pronounced **ON-toh-kin**) is a proposed programming language designed primarily for AI agents to create reusable 3D objects, characters, and animations. An agent describes an object's form, parts, appearance, physical properties, mechanical connections, and intended actions. The language system supplies supported construction and behavior, while people can inspect the definitions, review the results, and direct changes.

The [current capability definition](Defining_Ontokin_Docs/Product_Requirements_Docs/OntoKin_Modeling_Motion_and_Object_Structure.md) focuses first on exterior models and short animations. Those objects should remain reusable in larger scenes, video games, and eventually complex virtual worlds. Physics and mechanics are central to their meaning, supported by mathematics and explicit rules.

> **Project status:** Conceptual language design. Product requirements, capabilities, and the new core semantic model are review drafts. This repository does not yet provide a working OntoKin compiler, runtime, or renderer.

## Current design work

The new document is [**OK-SEM-001: Core Object, Motion, and Physics Semantics**](Defining_Ontokin_Docs/OK-SEM-001/OntoKin_Core_Object_Motion_and_Physics_Semantics.md).

It proposes how classes, instances, nested parts, coordinate frames, joints, physical laws, and concurrent actions relate. Its central example is a character that walks, turns its head, and controls one hand while maintaining coherent mechanical and physical behavior. Carrying and releasing a prop makes the transition between connected and independent motion explicit.

The document contains 28 proposed semantic rules, a worked character sequence, and 24 conceptual behavior checks. These are design rules and expected outcomes, not implementation test results. Exact syntax and implementation choices remain later work.

## Project documents

The [Defining OntoKin Docs](Defining_Ontokin_Docs/) directory contains the current design documents and the founding records.

### Current definition and semantics

For a concise introduction, start with OK-CAP-001. Use the PRD for the broader requirements and OK-SEM-001 for the proposed rules that make the core concepts precise.

| Document | Purpose | Status |
| --- | --- | --- |
| [**OK-CAP-001 v0.1 — Modeling, motion, and object structure**](Defining_Ontokin_Docs/Product_Requirements_Docs/OntoKin_Modeling_Motion_and_Object_Structure.md) | Explains the current modeling focus, modular objects, physical behavior, and scope progression. | Draft for concept review |
| [**OK-PRD-001 v0.2 — Product requirements**](Defining_Ontokin_Docs/Product_Requirements_Docs/OntoKin_PRD_v0.md) | Defines the intended product's capabilities, support contracts, and acceptance scenarios. | Draft for product review |
| [**OK-SEM-001 v0.1 — Core Object, Motion, and Physics Semantics**](Defining_Ontokin_Docs/OK-SEM-001/OntoKin_Core_Object_Motion_and_Physics_Semantics.md) | Defines object relationships, movement authority, physical participation, and transitions such as release. | Conceptual language design; proposed for semantic review |

### Founding design records

These documents explain the project's origins and earlier architecture exploration. The newer owner direction and capability definition govern the current modeling focus. Historical implementation proposals remain options for later evaluation.

| Document | Topic |
| --- | --- |
| [**OK-001 — Project Vision and Initial Architecture**](Defining_Ontokin_Docs/OK-001/OntoKin_001_Project_Vision_and_Architecture.md) | Origins, goals, intended uses, and initial system proposals |
| [**OK-002 — Language Foundations and Conceptual Minimal Specification**](Defining_Ontokin_Docs/OK-002/OntoKin_002_Language_Foundations_and_Minimal_Specification.md) | Early concepts for objects, state, behavior, and human/AI authoring |
| [**OK-003 — Compilation and Runtime Architecture**](Defining_Ontokin_Docs/OntoKin_003_Compilation_and_Runtime_Architecture_Package/OntoKin_003_Compilation_and_Runtime_Architecture.md) | Compiler, interpreter, runtime, and rendering-integration proposals |

The earlier roadmap reserved **OK-004** for renderer integration. **OK-SEM-001** identifies the semantic-design work without renumbering those records.

## What the core model distinguishes

A character can contain a hand without that containment alone specifying how the hand moves. Its frame relationship describes placement; a wrist joint permits and limits relative movement; an action supplies a goal; and the physical model determines the supported response.

The proposed semantics therefore distinguish:

- Classes and shared definitions from individual objects and their state.
- Object ownership from spatial following and mechanical connection.
- Logical parts, visible surfaces, animation controls, and physical bodies.
- Prescribed movement from dynamic response and physically driven actions.
- Independent action targets from the physical coupling between connected parts.
- Valid definitions, constructed models, successful behavior, and delivered output.

These distinctions let agents make focused changes and inspect why a part moved. They also keep the result understandable to the people reviewing it.

## Direction of development

| Stage | Question |
| --- | --- |
| Product requirements and capability definition | What should OntoKin create and accomplish? |
| Core semantic model | What do objects, movement, mechanics, and physics mean? |
| Language specification | How do agents express those meanings precisely? |
| Implementation architecture and prototype plan | How is that meaning executed, verified, and connected to external tools? |

The current stage is review of the core semantic model. The initial examples concern complete exterior models, nested parts, concurrent short actions, attachments, contact, gravity, and a simple environmental response.

The earlier moving-sphere proposal remains a possible small pipeline experiment. It does not establish the current goals for modular modeling, mechanics, or independently controlled parts. Broader environments and physical domains remain part of the longer-term direction described in the existing PRD and capability document.

## Language, execution, and rendering

OntoKin describes objects and behavior. Execution evaluates their state over time. Rendering turns the evaluated scene into visible images. These responsibilities remain distinct even when existing tools perform some of the work.

The founding documents explore interpreters, compilation, and rendering adapters. The semantic model does not select those mechanisms or require a dedicated graphics renderer.

## About the name

**OntoKin** combines **onto-**, referring to ontology, or what exists and how entities relate, with **kin-**, referring to kinematics, or motion. Earlier drafts used the working name *OntoKine*; **OntoKin** is the current project name.

---

*This README describes the intended language and its current design documents. Documented capabilities remain proposals until implemented and verified.*
