---
project: OntoKin
document_id: OK-AGENT-004
title: Source Impulse Program Workflows
version: 0.1
date: 2026-10-18
status: adopted-interface-contract-release-evidence-pending
language_contract: OK-LANG-004
agent_contract: ontokin.agent/0.4
diagnostic_contract: ontokin.diagnostic/0.2
---

# Source impulse program workflows

## 1. Authority and explicit selection

[OK-LANG-004](../language-design/OK-LANG-004-source-impulses-and-free-sphere-dynamics.md), adopted before implementation in [issue #10](https://github.com/Omegapy/OntoKin/issues/10), defines the source and physical semantics. Its [adoption record](../language-design/impulse-v0.1/adoption.json) identifies the fixed acceptance corpus. This document specifies the inherited program-service interface; it does not replace those numerical, source, or release requirements. [OK-AGENT-003](OK-AGENT-003-native-surface-program-workflows.md) and [OK-AGENT-002](OK-AGENT-002-program-bundles-and-atomic-source-edits.md) remain mandatory unless explicitly extended below.

```python
from pathlib import Path
from ontokin.program_agent import ProgramAgentService

with ProgramAgentService(Path(".ontokin-state"), protocol="ontokin.agent/0.4") as service:
    response = service.handle(request)
```

| Binding | Agent/0.4 |
| --- | --- |
| Request and response schema | `ontokin.agent/0.4` |
| Source entry | `ontokin "0.4"` / `impulse-0.1` |
| Catalog schema | `ontokin.agent-catalog/0.4` |
| Explicit delivery target | `ontokin.glb/0.4` |
| Database | `impulse-program-agent.sqlite3` |
| Store schema | `ontokin.impulse-program-agent-store/0.1` |
| Source bundle | Existing `ontokin.bundle/0.1` |
| Diagnostic payload | Existing `ontokin.diagnostic/0.2` |

The program-service Python default remains Agent/0.2. CLI agent selection remains explicit, with Agent/0.1 as its default:

```bash
python3 -m ontokin agent --protocol ontokin.agent/0.4 --store .ontokin-state --request request.json --wait
```

The selected service determines the protocol, response envelope and database before reading a request. A request cannot switch these by changing its schema field. All four databases can share one directory with independent project/request IDs, accepted heads, runs, artifacts and cursor secrets. An explicitly wrong store schema rejects before journal mode, DDL or migration changes its bytes. Old schemas, source snapshots and defaults are not migrated.

## 2. Source operations and immutable revisions

The complete operation set is inherited unchanged from Agent/0.3: `discover`, `create`, `edit`, `validate`, `inspect`, `surface.mesh_page`, `evaluate`, `reset`, `status`, `cancel`, `export`, and `artifact`. There is **no host impulse RPC** or mutable state replacement operation. An impulse is an authored event:

```ontokin
at 1[s] sequence {
    impulse ball using vector(world, 0[N*s], 2[N*s], 0[N*s])
        at point(ball.frame, 0.5[m], 0[m], 0[m]);
}
```

Create or patch exact `.ok` bytes, evaluate the accepted revision, and inspect the resulting run. The [request schema](../language-design/agent-v0.4/request.schema.json) keeps the inherited required/optional fields and selects only GLB/0.4 as a destination. It adds no impulse argument to `evaluate` or another existing operation. Request-ID retries, changed-payload rejection, queued work, cancellation, result expiry and worker fencing retain their established meanings.

An impulse entry may import compatible pinned 0.2/0.3/0.4 definitions. Each source declaration retains its own language/profile, module identity and exact source revision. Ordinary evaluation, export and geometry paging require a previously accepted snapshot. Invalid or never-accepted candidates remain available for source diagnosis without gaining those permissions. A later accepted revision does not erase an older accepted snapshot or relabel its run/cursor.

Source edits use exact program/source revision, UTF-8 byte offsets, expected text and existing writable source identities. Public occurrence initializers can repair body mass, radius or other authored parameters. The scene's existing source scope can repair an impulse statement. Derived application records, vectors, mesh indices and generated event ordinals are read-only observations; they are not new writable event identities. Targeting an occurrence does not grant permission to edit its imported definition.

## 3. Bounded impulse state

The existing `state` inspection field includes `state.impulses` for every evaluated object under the impulse profile. Its exact shape is defined by the frozen [impulse state schema](../language-design/impulse-v0.1/impulses.schema.json). Initially it contains `applied_count: 0`, `last_application_time_seconds: null`, and `last_applications: []`.

The count covers the evaluated prefix. The list contains every application to that object at its latest impulse-bearing boundary, in written order. Unrelated boundaries retain the list; a later impulse boundary replaces only the touched object's list. Earlier history remains observable through existing exact-time before/after inspection within the run's valid interval. A failed atomic sequence retains its before-state count and list.

Every application records its zero-based index among **all** sequence statements, exact source-unit revision and statement span, resolved target path/identity, and the nine explicitly named impulse/point/lever/angular-impulse/before-and-after velocity vectors. All vector values are finite. A nonworld inspection re-expresses the ordinary top-level pose and velocity under inherited rules; these expressly world/self application records remain unchanged.

A free sphere's `pose_authority.since_seconds` retains its dynamic origin, zero or release time. `trajectory_anchor_seconds` identifies the latest release/nonzero-impulse anchor. A valid zero impulse still counts and records but preserves the old trajectory anchor exactly. The service obtains these values from source evaluation and does not independently apply momentum updates.

The [response schema](../language-design/agent-v0.4/response.schema.json) constrains available object state, constructed state and run snapshots using this projection. Shape validation is separate from the required numeric, boundary, revision and atomicity checks. [The diagnostic alias](../language-design/agent-v0.4/diagnostic.schema.json) retains Diagnostic/0.2; there is no new diagnostic payload version.

## 4. Geometry and discovery

Native geometry remains the inherited `surface-0.1` capability. `geometry.surface` and `surface.mesh_page` retain their exact nested schemas and `profile: "surface-0.1"`, local coordinates, triangle units, region semantics and geometry fingerprint meaning. The Agent/0.4 envelope and complete source closure identify the impulse entry. The service compiles the selected program under `impulse-0.1` while preserving the nested geometry contract.

An Agent/0.4 cursor additionally binds private `entry_profile: "impulse-0.1"`, along with protocol, implementation, project, revision, occurrence, region, geometry digest, ordering and coordinates. The public page does not acquire an `entry_profile` field. Page count can change from 1 through 256 on continuation; changing immutable cursor context rejects. Paging does not evaluate or advance a run.

The catalog advertises `impulse` as a source **event**, its units and exact frame requirements, free-sphere admission and atomic behavior. It exposes `state.impulses` and the origin/anchor distinction. Finite forces, continuous torques, actuators, contact, connected loads and general rigid-body dynamics remain unsupported. Mixed-module declarations preserve their actual declared profiles; a catalog record does not establish successful construction or evaluation.

## 5. Resource limits and publication

All inherited source, object, work, deadline, output, byte and value-entry limits apply. Nested influence records count before repeated snapshot materialization. The adopted conservative sampling weight is the legacy record count plus four entries per object's empty impulse projection and the maximum complete retained latest-boundary group weight. Each application contributes `45 + len(target_element_id)` logical entries. Before-time-zero construction excludes unexposed future groups. The service must never satisfy a lower budget by silently shortening a successful application list.

The runtime materializes run/inspection projections under `max_value_entries`, and the service checks the **complete final successful envelope** under that same requested limit after source, implementation, progress and cursor metadata are present. This final check runs inside the publication transaction. Failure rolls back new accepted-head, run and artifact effects together, retaining an explicit bounded failure receipt. A user's smaller success budget does not suppress the failure receipt itself. Request-wide cancellation likewise cannot publish a successful partial impulse result.

Source diagnostics preserve the exact program, original source unit and UTF-8 span. Application-time failures retain their actual event boundary, `side: "after"`, target occurrence and `details.sequence_index`; the earlier valid prefix is distinguishable from the failed after-state. Existing category, run, repair and blocking-stage semantics remain intact.

## 6. Recorded delivery and acceptance evidence

Explicit GLB/0.4 delivery inherits native geometry/PBR/provenance and source-driven world animation. It additionally retains complete per-object `impulse_states_after` at every boundary, with conservative spin sampling and independent source comparison. It records animation; it does not execute impulses in the destination. An evaluated binary64 program can still exceed float32, sampling or output limits and fail delivery without acceptance/artifact publication.

The frozen [operational procedures](../language-design/impulse-v0.1/acceptance.json) require actual interface execution: P08→P09/P10 scoped repairs, rejected candidates/retries, separate stores, mixed-profile discovery and geometry pages, frame-preserving state, complete-response budget boundaries, cancellation and rollback. Delivery must retrieve the same accepted artifact later checked by the independent decoder/browser. Existing source, agent, construction, surface, destination, regression and CI gates remain mandatory.

This interface document does not mark I01–I12 or the complete language finished. Current implementation/evidence status belongs in [STATUS](../../STATUS.md); [GOAL](../../GOAL.md) remains authoritative.
