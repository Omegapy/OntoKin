# Proposed Draft 2 budget counting

This clarification belongs to **OK-LANG-006 0.1.0-draft.2** and remains
unadopted. It makes the inherited counting units and the added reach histories
explicit. It raises no inherited maximum. Different budgets measure different
work or output; the same numeric value does not make them interchangeable.

## 1. Four distinct counting regimes

| Regime | Maximum and counting unit | Application |
| --- | --- | --- |
| Source construction/execution work | 100,000 semantic operations and 100,000 materialized logical source-value entries, with inherited elapsed/object/item limits and lowered request budgets | Charge actual compilation, numerical admission, evaluation, projection, bounded planning and other defined work. The numerical admission cap is not an additional program allowance. |
| Agent JSON | 100,000 recursive JSON values/containers, 4 MiB compact UTF-8 bytes and depth 128 | The full successful response and every intermediate value to which the inherited budget applies. `budgets.max_value_entries` may lower the entry bound. |
| Retained source samples/boundaries | 100,000 weighted state records | Inherited ordinary object/joint/action/frame rows plus their already defined nested impulse/force weights; extend with full reach projection and incoming-release weights below. |
| Whole GLB JSON and binary | 64 MiB total GLB bytes; at most 67,108,864 recursive JSON values/containers and inherited depth 128 | The inherited writer/reader use the GLB byte maximum as their metadata-entry guard. Every repeated certificate/history value counts; this is distinct from the Agent envelope and source-history budget. |

The actual inherited implementation on main
`59b937d16ec0c82c9bc1395bd0c9bcc63e597261` makes these distinctions in
[construction.py](../../../ontokin/construction.py),
[program_runtime.py](../../../ontokin/program_runtime.py),
[json_limits.py](../../../ontokin/json_limits.py),
[evaluator.py](../../../ontokin/evaluator.py),
[scene.py](../../../ontokin/scene.py) and
[gltf.py](../../../ontokin/gltf.py). The JSON counter charges one entry for each
value or container; object keys contribute encoded bytes, but are not separate
logical entries. Repeated references are traversed and charged at every output
occurrence. Cycles are invalid. Exact encoded bytes use compact
`ensure_ascii=False` JSON with finite numbers and Unicode scalar strings.

GLB/0.6 additionally caps interval certificates at 100,000, while retaining
10,000 keys, 250,000 baked poses, 1,000,000 validation poses and 250,000 native
occurrence vertices. These maxima are simultaneous constraints, not independently
guaranteed successful combinations. The whole GLB metadata check cannot be
replaced by counting unique backing objects or only its binary chunk.

## 2. Added reach sample and boundary records

Let `O`, `S`, `J` and `A` be the actual constructed object, site, joint and named
action counts. `A` includes each named reach once, as an inherited action row.
Let `F05(t,side)` be the inherited force-profile `_records_per_sample` bound,
with its real prefix horizon and side. For the new profile, extend the inherited
profile dispatch to include its force/impulse obligations; do not omit them
because the profile name changed. The old profile's formula is unchanged.

For a full reach map on one sampled side, define

```text
R(t,side) = 1 + sum(logical_json_entries(full_reach_projection))
```

over every named reach retained on that side. The `1` counts the map container.
Count all identities, chain/target data, exact clocks, current physical state,
per-action rates and the latched terminal result. A repeated immutable source
description or a shared resolved target does not exempt a copied projection.
The full sampled-output weight is

```text
F06(t,side) = F05(t,side) + R(t,side).
```

For recorded boundary metadata, the inherited side weight omits frame output
and the duplicate object row which the boundary projection does not contain:

```text
H05(t,side) = F05(t,side) - (O + S + 1).
I(t) = logical_json_entries(complete incoming_releases array)

H06(t) = 2 + H05(t,before) + H05(t,after)
           + R(t,before) + R(t,after) + I(t).
```

The extra `2` counts the new boundary wrapper and source clock. `I(t)` includes
the array even when empty, every complete release record, every contributor's
identity/coordinates/rates, complete incoming world pose/linear/angular velocity,
and source span. Both sides are charged because both are materialized, including
natural completion followed by source events at the same exact clock. The
inherited impulse/force components already use their defined conservative
nested-history weights; they are not reduced to one record per event.

Require the sum of the full retained boundary weights to be at most 100,000.
For requested source samples, apply the inherited sample-count/output limit with
a conservative maximum `F06` for each requested sample (or their independently
bounded sum). A failed boundary publishes only its valid incoming prefix; do
not materialize an invalid after-side in order to count it. Failed-request
diagnostics remain bounded separately.

## 3. Preflight, exact accounting and finite reuse

Preflight before allocating all output maps or decoded copies. Immutable source
identities, bounded shapes, named-action counts and fixed vector dimensions allow
a conservative reach weight to be computed without first constructing a large
JSON value. Use the maximum applicable lifecycle shape: admitted target/start
pairs, claimed identities, current pose and terminal snapshot must not be
undercounted as their pending nulls. Include all source release contributors
permitted by the real finite topology and requested prefix. Refine the bound only
from independently established valid prefix information.

After preflight, the actual complete output must still pass its JSON/record/byte
guards. A conservative forecast is not permission to exceed a measured limit.
Inputs cannot raise profile maxima. Smaller request budgets retain their original
meaning, and every failure must identify the exhausted unit and bound.

Pure numerical results may be cached within a bounded operation when their exact
canonical inputs, branch and proof method match. Real work avoided by such reuse
need not be invented as executed work. Each new lookup, type/limit/claim check,
output occurrence and copied logical value is still charged; cache keys and
storage are bounded. A cache must not reuse stale source/run state, omit a
different action's authority checks or remove cancellation checkpoints. The
supplied-byte reader independently establishes results rather than accepting
the writer's cache or certificate as authority.

## 4. Fixed complete-response probe

Q03 and supplementary LP04 use original **P24**, `time_seconds="1.5"`,
`side="after"`, `selector.kind="action"`, `fields=["actions"]`, and `limit=128`.
The query returns all 128 named action items, each with its complete action group.
It uses the actual sampled run established by the preceding source/Agent steps.
No adaptive smaller query or within-group pagination is permitted.

First execute with the default limits and measure the full published successful
envelope using the inherited exact counter. Let its logical entry count be `N`.
Record the actual required intermediate peak/cumulative counts under their
respective inherited accounting rules. With fresh request identities and the
same source/run/query conditions, require successful publication at
`budgets.max_value_entries=N`, then require `N-1` to reach and fail the final
complete-response guard. A prior intermediate failure, missing result item,
different source revision, changed query or idempotency conflict does not satisfy
that final-publication probe. The implementation must preserve all intermediate
accounting rather than exempting work to force this result.

The Agent worker's synthetic shape measurements test that the proposed JSON
can fit the default bounds. They are preparation only: the actual protocol must
establish the real full envelope, intermediate feasibility, cursor integrity and
globally bounded failure receipt. Failure receipts retain the inherited rule
that a tiny successful-output budget must not prevent delivery of a bounded
diagnostic. All other global envelope limits still apply.
