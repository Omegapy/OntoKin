# C090 independent torque inputs and expected results

This is the finite input packet for the proposed source `0.22` / `torque-0.1`, Agent `ontokin.agent/0.22` and recorded `ontokin.glb/0.22` contracts. It freezes source bytes, library/image dependencies, exact identities, independently calculated expectations, refusals, repairs and complete future execution procedures **before torque implementation**. It is not a claim that torque runtime, Agent, export, native playback or a feature release has passed.

The root [source specification](../SPECIFICATION.md), [Agent contract](../AGENT.md), [recording contract](../RECORDING.md) and their schemas define the proposed behavior. The separate C090 adoption/readback decision binds this packet with those files. Existing default bindings and all original predecessor regression obligations remain unchanged.

## What is included

| Input set | Count and scope | Authority |
| --- | --- | --- |
| `physics-cases.json` | 31 small source-positive cases with their exact `.21` torque-free controls | Literal analytic phase/speed table and exact canonical own inertia |
| `state-expectations.json` | 204 before/after observations across those 31 cases | Complete interval identities; canonical net, acceleration, route, anchor, phase and speed; exact counts/history; independent error inequalities |
| `numerical-cases.json` | 7 mathematical cases | Canonical rounding, inertia, underflow, exact aggregate cancellation, exact clocks, translation anchor tie, offset chord, and nonpublic zero crossing |
| `evaluation-domain-cases.json` | 4 additional source inputs | Exact phase-cap equality; long neutral-underflow shadow; reference-origin transfer; reference-only acceleration change |
| `refusal-cases.json` | 30 source/evaluation/clock refusals | Frozen code, phase, selected message/details and exact primary/repair coordinates; inherited constructors remain inherited |
| `language-cases.json` | 5 source cases and 2 `.21` construction controls | Imported pure Torque/Time inputs, contextual ordinary names, fixed local rotation, and forbidden function/initializer/library-scene contexts |
| `delivery-cases.json` | 31 separately authorized delivery inputs | Exact source/options/host policy, actual predecessor availability, geometry/landmark invariants and continuous-proof obligations |
| `delivery-refusals.json` | 2 source-valid articulated-path inputs | Exact unsupported-composition public envelope and offending joint span |
| `hostile-delivery-cases.json` | 40 precise mutations | Original accepted-byte control, exact mutation selection, adapter identity and public diagnostic mapping |
| `agent/repairs.json`, `agent/workflow-repairs.json` | 6 literal repairs in each separate authority cohort | Exact byte preconditions, resulting source/program identities, sibling and asset invariants |
| `agent/request-workflows.json` | 16 scenarios covering all 12 operations | Real create/edit/inspect/evaluate/resume/reset/reopen/retry, status/cancel, stores, publication, meshes, asset/artifact chunks and EOF |
| `agent/resource-cases.json` | 17 actual stages | 14 source/runtime stages and 3 recording stages; cancellation, cap, deadline and original-callback variants |
| `schema-cases.json`, `agent/transport-cases.json` | 52 schema/semantic mutations and 12 wire refusals | Closed new fields, source/provenance/chronology, native types, rational guards and unchanged transport authority |

All `.files.json` manifests explicitly enumerate the entry, dependency modules and PNG; there is no ambient import. `modules/carriers.ok` is a pinned `.21` definition module. Its two free spheres each have a massless textured label and a nested fixed arm/tip. `modules/torque_values.ok` supplies independently authored pure functions in the declaring `.21` profile. The 89-byte PNG is an unchanged C088 immutable image. Every source/program/asset revision is computed from complete exact bytes by the documented bundle/0.2 identity algorithm. File modes are `100644` and are included in `INPUTS.json`.

## Reading the physics expectations

The three-column literal sample rows are exact clock, global unwrapped phase, and signed angular speed. They describe the reference used for the finite mathematical assertions. The published `phase_since_anchor_rad` is a different field: it resets only at a genuine canonical rotation reanchor. `state-expectations.json` supplies the exact binary64 values and retained anchor for every frozen observation. A source-history boundary, a sample request, an unchanged canonical net, or an independent reference-origin update must not manufacture a canonical rotation anchor.

The independent arithmetic uses the actual canonical source values and inherited canonical sphere inertia. It sums all individual torque values as exact rationals, rounds the net once, divides by that inertia and rounds acceleration once. Phase and speed use their whole exact polynomials followed by one binary64 rounding. The exact pre-net-rounding reference acceleration is separately retained. Ideal work/energy and canonical rounding residuals are distinguished; the impulse cases measure torque work from their after-zero impulse state and do not pretend the impulse did no work.

The small cohort covers positive/negative acceleration, braking/reversal, overlap, zero/cancellation, same-net replacement, staggered completion, first splitting caused solely by completion, all three world axes, different masses/radii/inertias, large and small marker offsets, nested markers, translation and COM-force boundaries, both same-boundary torque/impulse orders, generated occurrences, ordered release and exact canonical clock addition.

Several witnesses guard easy-to-miss differences:

- **Translation tie:** p15 starts at `x=1` with `vx=2^-52`. Its final canonical x is `0x1.0000000000001p+0`. An extra translation anchor at the torque boundary produces the wrong `0x1.0000000000000p+0`.
- **Completion starts rotation:** p09 has cancelling active intervals until one completes at one second. That completion must create the first split rotation anchor even though no new source statement runs there.
- **Noncommuting orientation:** p31 begins with the exact X half-turn `(0,1,0,0)`. A world-Z torque left product has quaternion `(0, cos(theta/2), sin(theta/2), 0)`, modulo publication sign. Right multiplication gives the wrong Y sign. The independent report contains all four component enclosures, not merely the increment quaternion.
- **Exact clocks:** p29 uses canonical source `0.1` plus canonical duration `0.2`. Its exact completion is `10808639105689191/36028797018963968`, distinct from separately authored canonical `0.3`. A query at that latter clock cannot complete the interval early. n25 additionally makes both clocks mandatory, provoking the inherited binary32 clock-collapse refusal.
- **Neutral underflow is not zero ideal torque:** p24 and p30 have torque `2^-1074`, inertia 2 and canonical acceleration zero. Canonical motion stays on the legacy route; reference acceleration is `2^-1075`. At one second the shadow speed and phase contributions are `2^-1075` and `2^-1076`.
- **Large shadow, unchanged canonical route:** domain02 runs that neutral law to exact `2^537` seconds, giving a quarter-radian independent phase discrepancy while the canonical pose remains stationary. Domain03 ends the pulse halfway and carries the reference origin forward, giving `3/16` rad at the same final clock. No split-only phase cap may be imposed on this legacy route.
- **Whole-segment phase domain:** domain01 admits exactly `2^20` radians. n26 has zero endpoint phases but an interior maximum `2^20+1`, which must refuse. Its short earlier prefix remains valid, and incoming-segment diagnostics retain the actual requested before/after side.

`reference/verify_inputs.py` uses standard-library exact rationals and an independent degree-180 sine/cosine polynomial with the Lagrange remainder `|x|^181/181!`, for `|x| <= 16`. It emits outward decimal intervals and applies the full saved-orientation Hamilton product. It does not import OntoKin, copy its trigonometric kernel, call its sampler, read candidate output, or generate an accepted GLB. The literal scalar/work integrator is not an alternate anchor specification; separate preserved-anchor expectations and common-clock scalar checks are mandatory.

For the small cohort, canonical quaternion comparisons use the predetermined absolute `2^-40` tolerance, with the declared radius-dependent position allowance for markers/landmarks. These are fixed input-derived test allowances, not a global promise over all phase magnitudes. Long-prefix/phase-cap domain cases are explicitly excluded. Reported source errors must additionally enclose the independent shadow and stay within the preselected small-case ceiling. Recorded output has its own complete interval proof at the fixed requested tolerances; dense samples do not replace that proof.

## Delivery, native bytes and the six comparisons

`comparisons.json` distinguishes six obligations: unchanged predecessor complete bytes; same-program repeated/resumed results; new-profile neutral canonical physics; torque-independent carrier COM translation; equivalent nonzero schedules with distinct preserved histories; and changed-source delivery with exact source-derived metadata differences. Never strip all new metadata or replace complete-stream predecessor equality with a geometry-only comparison.

Markers are tested as actual asymmetric textured geometry. The panel has exact local dimensions `1/4 × 1/2 × 1/8` m and local maximum radius squared `21/64`. The nested tip origin is `(3/4,3/8,0)`, with radius squared `45/64`. p14 uses a 100 m offset and equal rotation endpoints through a reversal: angular-only endpoint agreement does not certify its translation. The frozen certificate tests include both angular-acceleration fields, actual neighboring phases crossed by rounded clocks, full nested offsets, local landmark/vertex errors, exact coverage, stored clock bits, quaternion lift, source histories and numerical basis identities.

Radius-only Agent repair deliberately changes the selected sphere's independently reconstructed geometry. It preserves sibling, marker, material and image streams. Magnitude, duration and mass repairs preserve every mesh stream. A stable occurrence ID by itself does not promise unchanged geometry.

Recorded composition refusal inputs n31/n32 place a hinge under the prescribed massless `ball.arm`, which itself follows the free sphere. The source remains legal while the affected path contains an unsupported active joint. Both the static zero-torque latch and moving hinge must refuse recorded delivery. The independent `.21` construction attempts confirm this source arrangement. A historical grip already removed before the torque latch, as in p28, is not an active dependency path and does not by itself cause this new refusal.

Adapter `OKE-*` identities are carried in `details.export_code`. They are not top-level public diagnostics or a new exception class. The frozen rows include the actual inherited public wrapper: numerical reader failures use `OKL-E-NUMERIC` / `evaluation` / `numerical_failure`; unsupported structure/composition uses `OKL-E-CAPABILITY-UNSUPPORTED` / `support` / `unsupported`; both block delivered output. The new composition check must preserve the actual offending relation span instead of the inherited generic scene-span default.

## Authority and actual predecessor observations

Every original physics input and its `.21` control retains the default 100,000 operations / 30,000 ms source request. Their exact original observations are archived under `predecessor/`, including failed authoring attempts. The final 31 controls all constructed and evaluated at their common before/after clocks on untouched C088. **The artifact batch failed overall:** only 27 produced accepted GLBs. p03, p19 and p20 reached the unchanged 100,000-operation readback limit at operation 100,001. p28 refused inherited independent validation because its spin norm could not be resolved. These four have no accepted predecessor artifact to compare. Their source/pose evidence and actual failures remain available.

The separately named `delivery-*` and `workflow-agent-*` entries request exactly **1,000,000 operations and 30 seconds** in source, with the same explicitly identified validation-host ceilings. Root selected this fixed allocation before torque implementation. It is not a change to defaults or any old control, nor an assertion that future export will succeed. Failure under the frozen allocation remains failure; the corpus does not authorize increasing it after seeing candidate output. p28's future `.22` delivery is its own independent gate, without an invented old GLB pair. Current-host reductions, caller reductions, stale authority, warm caches and reopen behavior are all tested separately.

The original baseline archives contain full raw input snapshots, state projections, binary64 projections, actual export reports, accepted GLBs and stream identities. `predecessor/ARCHIVES.json` binds every uncompressed member's exact length, SHA-256 and mode, plus each complete ZIP. Supplemental construction archives retain the first direct-dynamic-parent joint failures and the subsequently accepted prescribed-parent revisions. No supplemental torque evaluation or export was executed.

## Reproduce the independent input checks

Run these from this directory, giving each execution a fresh report filename:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 reference/verify_inputs.py /tmp/c090-input-check-new.json
PYTHONDONTWRITEBYTECODE=1 python3 reference/verify_manifest.py
```

The schema-only checker additionally needs the pinned review dependencies `jsonschema==4.26.0` and `referencing==0.37.0` and the complete root contract checkout:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 reference/check_schema_inputs.py --contract-root /absolute/path/to/OntoKin /tmp/c090-schema-check-new.json
```

This checker validates design prototypes, closed-shape mutations and materialized request-template types. Symbolic response IDs are explicitly inert schema examples; it does not pretend a future run/artifact/cursor exists, and it does not execute semantic mutations or any Agent operation.

The preserved input check 04 passed 2,906 assertions and emitted 128 complete quaternion-reference samples. The schema check passed 222 assertions. Earlier input reports are retained as actual earlier attempts, not overwritten. Independent reviewer findings and amendments are listed in `review/AMENDMENTS.md`; root's separate final review binds the final file inventory. The final manifest does not call these design checks a torque runtime pass.

## Remaining release gates

Implementation must execute the exact frozen source/refusal/state/resource/Agent/store/publication/native-byte/destination procedures, with actual controls and preserved failures. It must retain all original predecessor gates, independent readers and resulting-main checks. The contract/input checkpoint neither closes a torque release nor changes Original28's retained 24/28 overall failure, missing external/interpreter attestations, unverified destination support or the wider GOAL domains.
