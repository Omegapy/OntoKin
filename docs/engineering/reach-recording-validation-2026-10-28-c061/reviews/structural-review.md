# C061 static measurement and structural-reuse review

Date: 2026-10-28. Reviewer: `/root/c060_review`.

## Disposition and scope

**Proceed with one bounded attribution round. No runtime optimization is approved by this review.** The source contains a plausible repeated-work target in independent-reader axial derivatives, but C060 has not measured its eligible cost. The complete source/callback admission and cache-displacement costs remain unknown.

This is a static review of the C060 source at commit `00533b953ed345cbf5fa13eaa56aafa3a2f052a8`, the starting point for declared branch `work/reach-reader-setup-20261028-c061` and Issue #26 comment `6482986855`. No OntoKin module was imported or executed by this reviewer. No product request, numerical replay, test, archive operation, repository edit or remote mutation was performed. The only local write is this review. Plain file reads and standard-library hashing checked the materialized source identities after the root reported local source readiness.

The review does not certify a future collector implementation. Its final code, passive-observation behavior and emitted evidence require separate review and the prescribed control/capture comparison.

## Source binding

The following local files under `/workspace/scratch/16cb56e5d545/ontokin-c061` matched their immutable GitHub blob identities:

| Path | Bytes | Git blob SHA |
| --- | ---: | --- |
| `AGENTS.md` | 12,169 | `dc8f3433ef3563ab2d2b4af550da807946f98bac` |
| `ontokin/reach_reference.py` | 259,473 | `d751b2a49d6da41f61d1a92e2d32eadf507e5c7e` |
| `ontokin/reach_conformance.py` | 206,759 | `f91cdbc43fe7134c4b11c73bd43cd033bf9d16ea` |
| `ontokin/reach_numeric.py` | 38,427 | `c552b085106a02b612a24a4884d8096f9733ee40` |
| `tools/capture_reach_recording_work.py` | 30,860 | `4ca1c94d5c1959c9c7a55426dced2f49ac73a996` |

Their SHA-256 identities, in the same order, are:

```text
54fda7f5d98ffa60dac2ecbde1becac2d0101c2a814fea6b64f23b55634ff473
e17fb50c54f41e13b42ce5bc2c6464544c26992299b474032ad2b19e0485949f
b4c657eac72186203960b18738f65f08e700f52dffa11c1364c6b4609c59a81a
1bd7da1d6721369d8662ba314e08c8704abfd24a4d9707113da4ac296d92ea0a
916718f2056b076b94ae9c1423a3bc19718f2425bccd6196537044b4657c996a
```

The native-dispatch assessment also read `reach_reference_plan.py` and `reach_reference_center.py` from the same immutable GitHub commit. The four named existing axial/callback/operand/reuse test modules were inspected as source only. Root recovery of their local bytes is a separate prerequisite to claiming execution.

## Exact reader setup sequence and measurement boundaries

The controlling function is `reach_conformance.validate_reach_export` at line 3507 in this source. It performs the following sequence before the first `_key_comparisons` call:

| Boundary | Measurement scope and qualification |
| --- | --- |
| `gltf.read_glb` | Supplied-byte parsing, bounded JSON/accessor checks. Local import at reader entry makes the module function a suitable candidate observation boundary. |
| `reach_conformance.verify_numeric_bases` | Actual numeric-basis admission before source metadata/reference construction. |
| `scene.program_metadata` | Source metadata materialization. This function also serves producer paths; scope its observation to the reader. |
| `reach_reference.build_reference` | Entire independent state construction, including model capture, `_initialize`, history preflight, geometry capture and `_build`. |
| `ReachReference.boundary_states` | Complete both-sided history materialization, including incoming release records. |
| `reach_conformance._verify_metadata` | Supplied metadata against independent source expectations. |
| `reach_conformance.verify_retained_clocks` | Exact authored/stored clock admission and retained-axis work. |
| `reach_conformance._geometry_bounds` | Independent source geometry and mesh construction. |
| `gltf._validate_geometry` | Actual supplied-buffer/source geometry comparison. |
| `reach_conformance._phase_tables` | Distinct-carrier positive-width phase requests. Each call to `reference.phases` may invoke `_phase`. |
| `ReachReference.point_phase` | Separate inclusive final endpoint work for every table frame. Do not fold this silently into positive-width phases. |
| `reach_conformance._boundary_allowances` | Derived source-numeric allowances. |
| `reach_conformance._assert_projection` | Full independent boundary projection comparison; recursive calls require nesting-aware accounting. |
| Certificate admission and `_tracks` | `_verify_certificates` begins here, but continues through all key comparisons. Preserve uninstrumented admission as a named residual. |
| First `_key_comparisons` entry | Exact end of the reader-setup interval. |

The reader entry, these spans and the first-key marker must reconcile to C060's measured interval, subject to a fresh neutral run: 23,171 shared/Reach charges for P11 and 17,185 for L03. These historical values are not expectations that permit adjusting new observations to fit them.

**The complete `_verify_certificates` call is not a setup span.** It includes all subsequent key work and the eventual exception. If it is wrapped, close or clip its setup contribution at first-key entry; retain later work in a separate scope. Do not subtract a full enclosing certificate span from setup totals.

`_phase` is also called while reference `_build` handles releases and impulses. A `_phase` or `_axial_derivatives` record therefore needs its parent setup segment. Grouping every `_phase` call as `_phase_tables` work would misattribute construction work.

For the selected hypothesis, nested `_phase` and `_axial_derivatives` spans are useful. Within an active axial span, `_source_basis`, `_joint_path`, `_l1` and `_axis_transport` can distinguish existing reuse from repeated attachment work. The nested local functions `attached`, `joint_motion` and `visit` cannot be replaced through ordinary module/class attributes. Do not rewrite their code or introduce tracing to obtain their individual costs. Retain an explicit axial residual for their work.

## Native-dispatch and observation hazards

The following functions must remain untouched by the collector: `_Arithmetic.tick`, `exact`, `guard`, `lookup`, `remember`, `_sync_cache_operand_limit`; `ReachExecutionWork.charge`, `tick` and related arithmetic/cache methods; `ConstructionBudget.tick` and `exceeded`; `_Bounds` arithmetic; `Fraction` methods; and trace/profile hooks.

This is a concrete neutrality issue. `reach_reference_plan._PartitionedPlan.evaluate_remaining` compares the bound arithmetic tick with `_PARTITION_TICK` and requires the expected observer state. `reach_reference_center._coefficient_domain` checks both class attributes and actual bound functions for `_Arithmetic` and `_Guard`. Certificate admission in `reach_conformance` pins class fields, functions, code objects, selected globals, callbacks and absence of tracing/profiling. A wrapper that forwards every call can still disable an optimization and change product counts.

The proposed high-level setup functions and the named `ReachReference` structural methods were not found in these reviewed pinned dispatch sets. That is a source-review observation, not proof that arbitrary instrumentation is neutral. The final collector must retain explicit native-dispatch checks and paired evidence.

Recommended installation discipline:

1. Import the involved modules before replacing observation boundaries, so native snapshots are not initialized from wrappers.
2. Install setup wrappers inside the already admitted `gltf.validate_export` observation window. Broad helpers such as `program_metadata` must not change producer execution.
3. Restore every wrapper in `finally`, including on product error and observation failure. Use saved originals once, forwarding original positional and keyword values unchanged.
4. Read counters and bounded primitive descriptors through actual native objects. Never call `lookup`, `remember`, `guard`, source admission helpers, `geometry_expectations`, or other product methods merely to observe state.
5. A `build_reference` entry is not an initialized `ReachReference` instance. Full cache/reference snapshots are safe only after construction returns; nested constructor methods need only fields already created at their actual entry.
6. Bound event count, nesting depth and descriptor size. An observation failure invalidates the diagnostic; it must not replace or hide the original product exception.

Frozen dataclasses do not authorize free arbitrary introspection. Native detached serialization should retain exact type distinctions, rational numerator/denominator pairs, floating-point bit identity, and explicit unsupported-type failures. A state object's `id` can label a within-run group, but cannot establish cross-run or runtime-cache source equivalence.

## Accounting requirements

Use parent-linked spans and compute exclusive deltas offline by subtracting only direct child intervals. Nested inclusive totals must not be summed as total work. Preserve setup work not covered by named spans as a named residual. All category deltas and all exclusive interval totals must reconcile to actual detached counters.

The generic `checkpoint` category combines reference arithmetic, byte/materialization callbacks, geometry callbacks and graph work. It does not identify `_phase`, axial work or removable work by itself. Report both shared-counter and Reach-category deltas. The final refused shared tick at 100,001 is not an admitted Reach category; retain that distinction when examining the later failure frontier.

Cache snapshots should contain occupancy and bounded category counts, with full detached keys only for the hypothesis under review. Reading cache entries must not promote them. Capture each reference's existing arithmetic cache separately from `ReachExecutionWork._cache`; each has its own identity and capacity. New retained entries can displace existing source-bound, root-pair, coordinate-law or trigonometric entries, so isolated hit savings cannot establish complete-request savings.

The fresh control/capture pairs must agree on complete work maps, original settings, retained reader bytes, source manifests, exception graph and product traceback after removing only exact named collector frames. A different failure frontier or generic count is an observation defect until explained and repaired. No elapsed-time neutrality is inferred from equal operation counts.

## Structural opportunity and current limits

`_axial_derivatives` creates `found = {}` and `visiting = set()` for every carrier request. Its `visit` recursively reconstructs source ancestry, and `attached` recomputes attachment L1 radii and axis transport. Different carriers can traverse common prefixes in the same independent state and phase. This is the proposed repeated-work opportunity.

Several nearby operations already reuse work:

- `_incoming` retains immutable relation maps in the bounded arithmetic cache, keyed by a model token and freshly captured grip set.
- `_joint_path` caches the pure coordinate law by its actual scalar operands and running-state meaning.
- `_source_basis` shares an already derived graph within a state/interval and retains a guarded bound-composition cache.
- `_phase_root_poses` captures typed source inputs and reuses complete actual/ideal root pairs with fresh admission.
- `_phase_root_distance` already handles its proved equal-point case.
- `phases` and `point_phase` retain completed phase results up to their existing cap.

The collector should show invocation count, exact charged work, input type/phase grouping and repeated arguments before choosing an optimization. Repeated carrier names or state IDs alone do not show repeated eligible arithmetic.

Whole axial-prefix reuse has a broad admission surface. It must bind independent topology, state/phase endpoints, live reference/arithmetic/work ownership, source records, active action status, root mode and rotation error, coordinate laws, axis/sign, fixed attachment position and rotation, precision and operand domain. A root or parent descriptor cannot be reused merely because its numerical output happened to match earlier output. Unsupported dynamic or noncoaxial paths must preserve their ordinary behavior.

Existing axial tests deliberately mutate child attachment rotation, action lifecycle and root rotation-error evidence between requests. Any new warm-cache path must still observe those changes. Cancellation/error identity, prospective intermediate-width checks, callback mutation, lowered/restored caps, failed publication and eviction require focused controls before accepting a candidate.

The narrower fallback is reuse of attachment L1 radii or axis-transport results within the axial walk. It has fewer numerical inputs, but requires a complete all-path argument too. As source-only gross path counts, `_l1` on an actual three-element native scalar vector executes six original ticks: three scalar-to-point conversions and three exact additions. `_axis_transport` on an actual four-element native scalar quaternion executes five: its entry tick and four scalar-to-point conversions. Interval inputs differ. These counts are not measured saving and exclude replacement admission, lookup, insertion, eviction, fallback, and any lost reuse elsewhere. They must not be presented as a positive candidate ledger.

## Acceptance and stop conditions for this task

Proceed only with the prescribed four sequential baseline/capture requests first. Stop if bounded observation or neutrality fails. Select at most one candidate after a positive full-cost argument and semantic review; the optional second paired round adds at most four product requests. Do not expand into producer arithmetic, JSON/geometry optimization or an automatic full-corpus tuning loop.

For an implemented candidate, recover the exact existing axial, callback-domain, operand-cap, reuse and conformance tests before claiming execution. Add the candidate-specific changed-source, warm-cache, phase/end-point, axis-reversal, cancellation, eviction and changed-domain controls. No Agent/SQLite work should run concurrently with the original-request window.

Report operation changes at matched first-key and original-failure milestones and all actually observed later work. A later failure can establish a prefix improvement but cannot establish completion cost, a passed recording or full-request savings. Complete-request acceptance requires actual complete independently validated requests under unchanged limits. C035 remains held; M1 remains rejected.

## Source links

- [C061 bounded proposal](https://github.com/Omegapy/OntoKin/blob/00533b953ed345cbf5fa13eaa56aafa3a2f052a8/docs/engineering/reach-recording-validation-2026-10-28-c060/NEXT-TASK.md)
- [Independent reference](https://github.com/Omegapy/OntoKin/blob/00533b953ed345cbf5fa13eaa56aafa3a2f052a8/ontokin/reach_reference.py)
- [Independent conformance reader](https://github.com/Omegapy/OntoKin/blob/00533b953ed345cbf5fa13eaa56aafa3a2f052a8/ontokin/reach_conformance.py)
- [Reference plan native admission](https://github.com/Omegapy/OntoKin/blob/00533b953ed345cbf5fa13eaa56aafa3a2f052a8/ontokin/reach_reference_plan.py)
- [Centered reference native admission](https://github.com/Omegapy/OntoKin/blob/00533b953ed345cbf5fa13eaa56aafa3a2f052a8/ontokin/reach_reference_center.py)
- [Original diagnostic collector](https://github.com/Omegapy/OntoKin/blob/00533b953ed345cbf5fa13eaa56aafa3a2f052a8/tools/capture_reach_recording_work.py)
- [Existing axial tests](https://github.com/Omegapy/OntoKin/blob/00533b953ed345cbf5fa13eaa56aafa3a2f052a8/tests/test_reach_reference_axial_derivatives.py)
