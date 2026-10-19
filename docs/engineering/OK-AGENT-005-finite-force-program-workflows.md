---
project: OntoKin
document_id: OK-AGENT-005
title: Finite Force Program Workflows
version: 0.1
date: 2026-10-19
status: adopted-interface-contract
implementation_status: tracked-separately-in-STATUS
language_contract: OK-LANG-005
agent_contract: ontokin.agent/0.5
---

# Finite force program workflows

## Authority and explicit selection

[OK-LANG-005](../language-design/OK-LANG-005-finite-center-of-mass-force-intervals.md), its [source adoption](../language-design/force-v0.1/ADOPTION.md) and additive source errata govern force physics and exact clocks. This interface extends [OK-AGENT-004](OK-AGENT-004-source-impulse-program-workflows.md), not its earlier bindings. It is adopted before the new service implementation; execution evidence and F01–F12 acceptance remain separate.

Select `ProgramAgentService(path, protocol="ontokin.agent/0.5")` or `python3 -m ontokin agent --protocol ontokin.agent/0.5`. The selected binding accepts only source `0.5` / `force-0.1` entries and compatible pinned dependencies. The Python default remains Agent/0.2; the CLI default remains Agent/0.1. Source units retain their authored profiles and revisions.

| Contract | Explicit value |
| --- | --- |
| Request and response | `ontokin.agent/0.5` |
| Discovery | `ontokin.agent-catalog/0.5` |
| Database | `force-program-agent.sqlite3` |
| Store schema | `ontokin.force-program-agent-store/0.1` |
| Source bundle | Unchanged `ontokin.bundle/0.1` |
| Diagnostics | Unchanged `ontokin.diagnostic/0.2` |
| Required eventual delivery | `ontokin.glb/0.5`, unavailable until its adapter is implemented and verified |

## Operations, revisions and repair

Keep the inherited operations and strict request fields: discovery, create/edit/validate, inspect, surface.mesh_page, evaluate/reset, status/cancel, export/artifact. No operation applies a host-only force, rewrites velocities, or changes accepted run state. Forces originate in immutable `.ok` statements. The request envelope cannot change the service's selected protocol or store.

Source-authorized edits require the accepted program revision, exact source-unit revision, writable element identity, UTF-8 byte offsets, expected text and replacement. A force identity in a derived record is not a writable event scope. A scene or source-unit scope can authorize a force operand or duration edit; the correct public initializer scope can authorize a generated occurrence's mass edit. An occurrence must not grant write access to sibling initializers, scene events or imported library declarations. Failed and stale candidates preserve the accepted head. Retained earlier runs still refer to their original immutable source closure.

Request-ID retries, changed-payload rejection, unknown-outcome reconciliation, queue ownership, cancellation, failed-prefix retention and reset retain the inherited lifecycle. A force completion beyond the requested horizon is metadata, not permission to preflight future physics. An extended run that fails preserves its certified prefix and cannot be reused as a valid later state.

## Complete world-force inspection

Every evaluated object in this profile includes `state.forces` with exactly the fields adopted by OK-LANG-005: active records, net world force, nullable world acceleration, cumulative start/completion counts, latest change clock and complete latest change list. Active records are sorted by force key. A latest change entry adds its started/completed kind to the complete source-bound record. Exact time strings, occurrence identities, source-unit revisions, statement spans and sequence indices come from the source evaluator, not a second service simulation.

Normal self-frame inspection re-expresses top-level pose and velocity under the inherited rules. The explicitly named world-force and world-acceleration quantities remain world-expressed. Impulse records remain unchanged. Dynamic origin and trajectory-anchor time remain distinct; unchanged canonical acceleration alone must not reanchor a body.

The response schema constrains force projections in object inspections, constructed snapshots and retained run snapshots. Shape validation does not prove source-span authority, numerical correctness, exact temporal ordering or complete budgeting. Tests must exercise those relationships using the actual service and fixed source cases.

## Geometry, cursors and discovery

Nested `geometry.surface` and `surface.mesh_page` keep the surface-0.1 schemas, local geometry coordinates, region identities and triangle ordering. Force entry profiles do not redefine geometry. The signed cursor binds Agent/0.5, force-0.1 entry profile, implementation, project, accepted program revision, occurrence, geometry fingerprint and query context. It must reject cross-profile, cross-project and stale query substitutions without mutating runs.

Discovery must distinguish implemented source forces and agent workflows from unsupported delivery. Until GLB/0.5 exists, advertise an empty supported delivery-target list, an explicitly unavailable planned destination, and no delivered-level success. Old catalogs and defaults remain byte-identical. Unsupported contacts, continuous torque, general dynamics, controllers and other GOAL domains stay visible.

## Delivery failure and bounded publication

A request naming an older export contract is rejected, not coerced. A structurally valid request for the new but unavailable GLB/0.5 adapter returns `OKL-E-CAPABILITY-UNSUPPORTED`, blocks delivered output and creates no artifact or accepted source revision. The inherited lifecycle may retain an already completed isolated evaluation for diagnosis; that is not delivery success. Ordinary evaluated/constructed requests must not invoke the unavailable adapter.

All inherited work, time, source, nested-value, result and byte limits remain. Count complete active and latest force records before materialization and check the final successful response inside the publication transaction. Lowered limits cannot truncate a successful history or commit a partial head/run/artifact. Check cancellation during evaluation, active-set scans, geometry paging and result construction, and again before commit. A bounded failure receipt remains available even when the requested success budget is too small.

## Checkpoint acceptance

Before integrating the agent checkpoint, execute actual create, before/after inspection, same-directory store isolation, exact mass/force/duration repairs, unchanged sibling and pinned-library checks, stale and invalid candidates, retry collisions, cursor substitutions, prefix failure/reset, cancellation and final-envelope budget rejection. Verify the published schemas against actual responses and reject deliberate malformed force records. Run the complete inherited regression suite and exact-head CI.

This checkpoint can complete the agent-side implementation without claiming GLB/0.5 or F01–F12 complete. Source-built export, independent geometry/PBR/intermediate-motion validation, reviewed browser captures, retained evidence and all remaining GOAL requirements still require their own implementation and acceptance.
