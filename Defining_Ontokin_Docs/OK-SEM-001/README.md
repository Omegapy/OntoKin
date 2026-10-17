# OntoKin OK-SEM-001

[Read **Core Object, Motion, and Physics Semantics**](OntoKin_Core_Object_Motion_and_Physics_Semantics.md).

**Status:** Conceptual language design, version 0.1. The semantic rules are proposed for review.

This document defines how objects contain parts, how local and whole-object motion relate, how mechanical connections and physical influences affect behavior, and how concurrent actions resolve their control. A modular character that walks, looks, reaches, and releases a prop provides the main example.

The document includes 28 proposed semantic rules, 24 conceptual behavior checks, and traceability to the existing requirements. The checks describe expected outcomes; no OntoKin implementation has been tested by this document.

## Context

- [OK-CAP-001: Modeling, motion, and object structure](../Product_Requirements_Docs/OntoKin_Modeling_Motion_and_Object_Structure.md) explains the current modeling focus.
- [OK-PRD-001 v0.2: Product requirements](../Product_Requirements_Docs/OntoKin_PRD_v0.md) records the broader intended product.
- [Project overview](../../README.md) links the current documents and founding design records.

Exact language syntax, compiler architecture, physics and rendering engines, internal data structures, and implementation plans remain later decisions. OK-SEM-001 establishes the meaning those choices must preserve.
