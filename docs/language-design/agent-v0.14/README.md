# Agent/0.14 keyed construction transforms

The [C081 decision](../keyed-transform-v0.1/ADOPTION.md) adds one pure source expression, `map_keyed<Out>(input, (key, value) -> body)`, through explicit source `0.14`, profile `keyed-transform-0.1`, Agent/0.14 and recorded GLB/0.14. It preserves the input's keys and cardinality while computing a typed value for each entry. Immutable bundle/files `0.2`, the twelve Agent operations and the existing source-edit authority remain in force.

This is experimental integrated-development scope. The [C081 engineering record](../../engineering/keyed-transform-2026-10-31-c081/README.md) identifies actual implementation and evidence; the independently frozen decision and inputs retain their original bytes. Complete feature release and full-product acceptance remain separate.

## Explicit entry points

Use `KeyedTransformAgentService` from `ontokin.keyed_transform_agent`, or select the JSONL service explicitly:

```bash
python -m ontokin agent --protocol ontokin.agent/0.14 --store /tmp/ontokin-keyed-transform-store
```

The separate database is `keyed-transform-program-agent.sqlite3`, with schema `ontokin.keyed-transform-program-agent-store/0.1`. Earlier protocol stores and default entry points retain their meanings. A retained accepted revision does not authorize later work: each new request uses the current host policy and caller caps.

Export a complete, pinned example from the repository root:

```bash
python -m ontokin export --bundle examples/keyed-transform/panel-task.files.json --target ontokin.glb/0.14 --output /tmp/ontokin-keyed-panels.glb
```

The manifest includes the entry source, exact reusable library and immutable PNG attachment. Source code cannot discover a PNG path or fetch a missing dependency. The [identity example](../../../examples/keyed-transform/panel-identity.files.json) has a separately authored [explicit .13 control](../../../examples/keyed-transform/control-panel-identity.files.json) for complete stream comparison.

## Source-level programming

The pinned [PanelGroup definition](../../../examples/keyed-transform/modules/panels.ok) converts dimensionless coefficients to lengths using an occurrence's public scale:

```ontokin
public param scale @ "scale": Length = 1[m];
public param coefficients @ "coefficients": Keyed<Real> = keyed<Real>{"right": 2, "left": 1};
public derive widths @ "widths": Keyed<Length> =
    map_keyed<Length>(self.coefficients, (k, v) -> v * self.scale);
```

The result contains the same `left` and `right` keys, in canonical ASCII order. At the default scale their values are 1 m and 2 m. Generated panels consume those derived widths through the existing `parts` construct. Editing one occurrence's scale changes its derived widths; the source key identities, reusable library and sibling occurrence remain separately inspectable.

The input is evaluated once. Every nonempty input entry evaluates the body under the same current request ledger. The two body-only binders are immutable and cannot shadow visible names. An empty input still checks the body with unknown typed binders and unknown enclosing value locals, preserving type/frame information. It performs no dynamic body iteration. Actual selected value-dependent failures remain failures.

All 24 adopted immutable leaf families keep their inherited limits. Input and output contain at most 256 entries. Nested keyed values, geometry, bodies, actions and generated object-reference collections remain outside the admitted element set. The expression introduces no filtering, new keys, reductions, mutation, unbounded loops, recursion, effects or physical authority. Older imported definitions retain their declaring semantics, including a qualified older function named `map_keyed`.

## Requests and read-only derivation records

- [request.schema.json](request.schema.json) defines the `.14` discriminator and the unchanged operation/request shapes.
- [response.schema.json](response.schema.json) includes the adopted read-only transform records.
- [diagnostic.schema.json](diagnostic.schema.json) retains source-bound diagnostic families.
- The [inherited texture interface](../agent-v0.13/README.md) documents immutable attachments, atomic source/module/asset edits, bounded byte retrieval and surface pages. Its behavior applies under the explicit `.14` binding.

The operations remain `discover`, `create`, `edit`, `validate`, `inspect`, `surface.mesh_page`, `evaluate`, `reset`, `export`, `artifact`, `status` and `cancel`. The complete JSON request ceiling remains 8,388,608 bytes. An edit uses the current program revision, the exact source-file identity and revision, UTF-8 byte offsets and expected text. Invalid edits preserve the prior accepted revision.

An inspected transformed value may include `derived_transforms`. Each ordered record contains `expression`, `body` and `input` source locations, plus `input_element_type` and `output_element_type`. Earlier input transformations precede the current transformation. An indexed leaf also carries its original stable `key` and actual `input_entry` location when known; an unknown original location remains null. Generated occurrences expose these derivations as `input_transforms` alongside their existing input-entry provenance.

These records are detached descriptions of source derivation. They grant no new editable identity. Repair the authoritative source member or parameter at its real span; iteration ordinals, generated triangles and derived results are not patch targets. Nested selected leaves keep their actual inner keys rather than adopting an unrelated outer key. Untouched earlier profile projections retain their original shape.

## Budgets, durable outcomes and delivery

Defaults remain 100,000 operations and 30,000 ms. A larger source request requires separate current host ceilings; caller caps only reduce work. Input evaluation, static checks, masked locals, entry selection, fresh bindings, selected body work, output copies and final collection materialization all consume existing cumulative limits. Construction, image admission, inspection, export, verification and retrieval continue on that same request ledger. The existing 32,768-bit operand, 256-entry numerical cache and 64-step reference cursor bounds remain unchanged.

Cancellation during a map iteration cannot accept a partial result. Stale revisions/cursors, identical retry identities, changed-payload refusal, reopening and interrupted publication retain the existing durable lifecycle. Reopen/retry results identify what happened; they do not grant execution authority from an earlier host receipt.

GLB/0.14 keeps the inherited geometry, PBR, PNG, UV, sampler, rigid placement and recorded-motion representations. A .14 identity transform must preserve the complete BIN chunk, accessor layout and data, material/image/sampler graph, stable occurrence identities and recorded motion of its explicit .13 control. The source/profile, exact program revisions, validated source spans and read-only derivation metadata identify the different programs. Independent readers enumerate those permitted differences and compare all remaining JSON.

Recorded playback has no live solver. Actual pinned destination checks and reviewed images establish only their identified finite artifacts and views. Unreal import, live destination physics, the retained release gates and the complete OntoKin mission remain open as recorded in [STATUS](../../../STATUS.md).
