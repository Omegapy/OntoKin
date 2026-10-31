# Agent/0.15 keyed reduction

The [C082 decision](../keyed-reduction-v0.1/ADOPTION.md) adds one sequential pure construction expression through explicit source `0.15`, profile `keyed-reduction-0.1`, Agent/0.15 and recorded GLB/0.15. The independently frozen decision and examples define its finite scope. Implementation and actual validation are separate from complete release acceptance.

```ontokin
reduce_keyed<Length>(dimensions, 0[m], (total, key, value) -> total + value)
```

Input admission completes before the seed is evaluated. Both are evaluated once. The body receives a typed accumulator, a String key and the input leaf. It runs in canonical ASCII key order with every intermediate type, unit, frame, domain and resource check preserved. An empty collection still receives static body checking and returns a detached seed. The admitted input and accumulator types are C081's 24 immutable leaf families, with the unchanged 256-entry bound. There is no reassociation or fold cache.

## Use the explicit binding

```bash
python -m ontokin agent --protocol ontokin.agent/0.15 --store /tmp/ontokin-keyed-reduction-store
python -m ontokin export --bundle examples/keyed-reduction/panel-task.files.json --target ontokin.glb/0.15 --output /tmp/ontokin-keyed-panels.glb
```

Storage is separate: `keyed-reduction-program-agent.sqlite3`, schema `ontokin.keyed-reduction-program-agent-store/0.1`. The twelve Agent operations, immutable bundle/files `0.2`, source/asset edit preconditions, transaction rollback, stale cursors, cancellation, durable retries and bounded retrieval retain their meanings. Each request uses current host authority. Defaults remain 100,000 operations and 30,000 ms; caller caps only reduce the admitted work.

The [panel task](../../../examples/keyed-reduction/panel-task.files.json) uses a pinned reusable construction twice. Its library maps supplied coefficients to segment lengths, reduces them to one total length and uses that result to construct keyed panels. Repairing the first occurrence's `scale` through the existing source patch operation changes its aggregate and dimensions while preserving the sibling, library, PNG bytes and unrelated recorded motion.

## Inspect derivations and repair source

Property values may include `derived_reductions`. Each record contains detached `expression`, `input`, `seed` and `body` locations, `input_element_type` and `accumulator_type`. Earlier actual derivations precede the current reduction. Generated occurrences may expose these as `input_reductions`. Existing map fields `derived_transforms` and `input_transforms` remain separate.

All actual input, seed and selected-body reads remain dependencies, including earlier values overwritten by later iterations. Empty reduction, helper calls and guarded caches cannot remove forbidden generated-view dependencies. The aggregate has no invented editable key or iteration identity. Repair uses existing source/member keys, exact UTF-8 spans, file preconditions and current program revision.

The [request](request.schema.json), [response](response.schema.json) and [diagnostic](diagnostic.schema.json) schemas describe this explicit binding. Earlier defaults and declaring units retain their prior behavior. Qualified calls to an older function named `reduce_keyed` remain ordinary calls.

GLB/0.15 retains inherited geometry, materials, PNGs, UVs, samplers and recorded motion. Equivalent separately authored .14 controls support complete-stream verification, with only enumerated source/version/revision/provenance differences. Native/browser captures establish their finite observed views. Unreal import, live destination physics, full feature release and full-product acceptance require separate evidence.
