# C042 independent P23 constructor and consumer review

Reviewer: `/root/constructor_contract`. Inspected publication: C041 `b0ebdc318444ca97c729c11e0b29b19646096b34`, tree `a798a4c3f52f80e123fb54b65b3ac344bd8ea42b`. This is source inspection and retained-source analysis only. No OntoKin module was imported or executed. No product request, runtime test, numerical replay, benchmark, archive processing, remote write, implementation change or release claim belongs to this review.

The current goal remains the full OntoKin language and product in `GOAL.md`; the immediate unmet finite gate remains all 28 original recordings followed by the remaining Agent, independent destination, compatibility and release roles. This review follows `AGENTS.md`, the adopted reach `ADOPTION.md`/`release-contract.md`, and budget-counting section 3. It does not promote C035 or reopen C041's rejected replacements.

## Findings

The ordinary source-constant cache must return a full `PoseValue`. Three direct graph call sites serve both source and recording traversals. An outer cache miss does not mean a new `PoseValue` was allocated: the constructor can hit the stationary cache, and an inverse call has a further inverse-result cache. The two default-zero vector admissions and stationarity charge occur before a stationary-cache hit, so the proposed three-charge saving attaches to eligible `make` entries, not solely to new object allocations.

Under the unchanged native P23 source model, the three graph call sites have a vocabulary of 34 possible outer key values: 33 noninverse values and one inverse value. This is not a visit count, cold-miss count or upper bound on misses over a whole request. The same key can be evicted and reconstructed repeatedly; conversely, upstream reuse and native recording paths can avoid this helper altogether. Current eligible `make` entries and their cache-outcome sequence remain unestablished by this source review.

## Exact inspected source

The first six files below were independently hashed from the local review subset and matched the C041 Git tree. The remaining files were read from exact-commit GitHub URLs; their listed blobs are the C041 tree identities. Line numbers below name this source revision only.

| File | Git blob |
| --- | --- |
| `ontokin/reach_runtime.py` | `e7ccbb35c4f5aab7ff6431692bed80089fbf0cf0` |
| `ontokin/reach_pose.py` | `d58dd633c052c53a201eb6bdb16dac68625b3961` |
| `ontokin/reach_numeric.py` | `c552b085106a02b612a24a4884d8096f9733ee40` |
| `ontokin/reach_recording_fast.py` | `c58d76692a79c1a1507a1185d1dfd15959de11cc` |
| `ontokin/reach_recording_capture.py` | `13a205b5382b4417295d693cd603c166e4f25d5a` |
| `docs/language-design/planar-reach-v0.1/sources/p23-maximum-chain-count.ok` | `3300ab61b9ce901f517dab18ee57f3079baaaaa5` |
| `ontokin/model.py` | `b265a8eb691dbd5f6c159784956d15f36871a78e` |
| `ontokin/evaluator.py` | `04ba6331aa6f693a7a887c5597dbfb668f0b68ed` |
| `ontokin/force_runtime.py` | `36de39587f94fcc5c2b6fa037f0fe1c4b46cd5b0` |
| `docs/language-design/planar-reach-v0.1/libraries/reach-assets.ok` | `a9ff85b48649fd9997f6387dfa6fddab438d8841` |
| `docs/language-design/planar-reach-v0.1/libraries/reach-parts.ok` | `a139d1d7eef8d97e5190528f4a0e6e891411ba7e` |
| `docs/language-design/planar-reach-v0.1/libraries/reach-exterior.ok` | `9545c1cdbb4ae260bff56190d5ab37f026ec347b` |

GitHub code search returned a default-main result, not C041; that search was not used as branch-source evidence. Enumeration below comes from the inspected reach modules and their inherited evaluator consumers. Python permits additional dynamic callers, so this finite static enumeration does not prove an externally callable private method has no other possible caller.

## 1. Caller and result contract

`ReachSimulator._constant_pose` is `reach_runtime.py:534-540`. Its key is:

`("reach_source_constant_pose", inverse, value.position, value.rotation)`.

The key has no recording/source discriminator, graph occurrence, frame name, phase token or output-type tag. The current helper uses `self.work.lookup`, calls `self.pose_ops.constant_pose(value)` or `self.pose_ops.inverse_pose(value)` only on a returned `None`, attempts `self.work.remember`, and returns the result. It does not do a separate result-type check before returning a hit.

The local `constant_pose` wrapper at `reach_runtime.py:1029-1032` is shared by these direct graph sites:

| Call site | Original operand and operation | Inverse? | Complete-source use |
| --- | --- | --- | --- |
| Site `frame`, lines 1426-1434 | Retained `site.pose`, then `compose(owner, constant_pose(local_pose))` | No | Ordinary source sites and source target/tip frames |
| Follow `instance`, lines 1447-1452 | Retained `follow.offset`, then `compose(parent, constant_pose(local_pose))` | No | Ordinary object following |
| Joint `connected`, lines 1487-1502 | Retained joint child site's `pose`, following the relative hinge/slider transform | Yes | Full connected-object position, rotation and spatial rates |

When no alternate recording operations object is present, the wrapper directly calls the outer helper. When an alternate object is present, it supplies `build=self._constant_pose` to `Binary64RecordingOps.recording_constant_pose`; that method can call it after its own native-domain and source-leaf-cache stages. This dispatch is important: all recording visits are not visits to `_constant_pose`.

`_resolve_kinematics` selects `ops.compose` for full source kinematics, `ops.compose_recording` for ordinary recording, and `ops.compose_recording_fast` when a recording context is active (`reach_runtime.py:1025-1028`). The source constant cache does not use that distinction. The upstream `_pose_slot`, translated-source reuse and `_SourceSiteIndex` may return a completed result without executing the builder; counting graph nodes therefore does not count constructor calls.

`PoseValue` (`reach_pose.py:103-139`) contains exact position, a `RotationValue`, exact velocity, exact angular velocity, a position-error allowance, and the owning operations object. It also owns mutable private projection/domain maps and optional finiteness-proof state. Public `position`, `orientation`, `velocity` and `omega` properties invoke the owning operations object's guarded projection path. Angular error comes from `rotation.error_rad`. Frozen dataclass syntax does not make those dictionaries immutable or prove hostile mutation impossible.

`RecordedTransform` (`reach_pose.py:142-160`) contains only exact position, rotation, the owner and position/orientation projection state. Its own docstring expressly excludes source composition, release anchors and point-error certification. A value of this class cannot occupy the existing full-pose key:

- `ReachPoseOps.compose` first requires both operands to be `PoseValue` (`1348-1350`), then uses both derivative vectors and both position-error fields (`1351-1436`). A short replacement can fail at the type check even before a missing-field access.
- Full `_kinematics` calls `_resolve_kinematics` without recording flags (`reach_runtime.py:702-707`). Every full object checks all four public fields at `713-715` and `1670-1672`. Inherited snapshots expose source velocity and angular velocity (`evaluator.py:701-767`); boundary execution also asks the overridden full `_kinematics` for incoming and staged graphs.
- `_tip_base` uses full `PoseValue` operands, source-relative geometry and an explicit pose owner (`reach_runtime.py:1688-1775`). A pose-only terminal traversal is still distinct from a derivative-free recording traversal and cannot silently change the constant key's contract.
- `inverse_pose` reads `position_error_m`, while full composition propagates it. `materialize` explicitly projects all four fields and returns a complete release anchor (`reach_pose.py:1742-1752`). `source_bounds` includes position and rotation error allowances (`1754-1767`). The runtime's source-site index also seals and copies derivative/error fields (`reach_runtime.py:2673-2712`).

A full-source caller after a recording call can use the identical key. A callback can likewise enter a full-source path on the same simulator/work object while a recording traversal is active. Native generation checks prevent an outer cache insertion from undoing nested completed cache work; they do not turn an already cached short result into a full pose. The result-type conflict is sufficient to reject the unchanged-key replacement without claiming that every possible reentrant callback necessarily takes that exact path.

The standalone `evaluator._constant_pose` is a different inherited helper returning `_Kinematics`; it is not this method or this cache. Captured native graph samplers also define `source_constant` builders which call `ops.source_ops.constant_pose`/`inverse_pose` directly (`reach_recording_capture.py:1139-1140,1241-1242`). Such calls can reach `make` without the simulator's outer cache, so a direct constructor optimization would require a separately defined census and scope.

## 2. Relevant cache layers and warm terminology

All of the following numerical entries share the native `ReachExecutionWork._cache`; the table does not describe independent 256-entry allowances.

| Layer | Key prefix / complete additional inputs | When reached |
| --- | --- | --- |
| Outer source constant | `reach_source_constant_pose`, inverse selector, original position, original rotation | Every actual call of this helper |
| Raw constant rotation | `METHOD, constant_rotation`, decoded quaternion tuple, current operand cap | `_rotation` when the supplied orientation is not already a `RotationValue` |
| Stationary pose | `METHOD, stationary_pose`, admitted exact position, admitted complete `RotationValue` | `make` after derivative admission and stationarity check |
| Static inverse result | `METHOD, inverse_pose`, exact position, complete rotation, position error | `inverse_pose` after acquiring a complete input pose |
| Alternate native source leaf | native recording `METHOD, source_leaf`, cap, Cartesian-axis setting, original position/rotation, inverse selector | Native recorder after its direct identity shortcut declines |

The outer source key distinguishes inverse from noninverse requests. The stationary cache does not: a raw inverse call first creates or retrieves the same forward stationary input. It then looks up the distinct inverse-result key. Rotation and inverse caches must be included in any complete cache/first-failure account; referring only to an outer and an inner cache is incomplete for the inverse route.

Use the following distinctions in a census:

1. An outer hit returns without entering the selected constructor and offers none of the proposed three charges.
2. An outer noninverse miss enters `constant_pose` and `make`, unless an exception occurs before entry.
3. An outer inverse miss on an ordinary model `Pose` enters `inverse_pose`, then `constant_pose` and `make`, before the inverse-result lookup.
4. A stationary hit still incurred both default-zero vector admissions and stationarity testing. It avoids allocating/inserting a new stationary `PoseValue`, but it is an eligible constructor entry for that narrower three-charge target.
5. A warm inverse-result hit can follow a forward stationary hit or miss. It still incurred the preceding forward-constructor work for a raw `Pose`.
6. A direct `inverse_pose(PoseValue)` skips `constant_pose`/`make` entirely. It has no default-zero-constructor saving. Ordinary graph callers supply model `Pose` leaves; a generic design cannot erase this separate supported helper route.
7. A lookup can find an entry initially, charge promotion, then return `None` because a callback changed the operand domain or evicted the entry. A census must classify the returned result/control flow, not just initial membership.
8. A `remember` can decline publication after a domain or generation change. A constructor return does not prove a retained entry exists afterward.

In a stable native domain with no intervening callback changes, a missing lookup charges one `cache_lookup`; a hit additionally charges one `cache_promote`. Insertion charges `cache_insert`, then promotion for an existing key or eviction at capacity. These conditional facts do not supply a fixed total cost for an arbitrary call. The actual order and state of all shared-cache entries still matter.

## 3. Original noninverse sequence and first failure

For the ordinary model `Pose` route, the exact source order is:

1. `_constant_pose` reads `value.position` then `value.rotation` to form its outer key. Generic property/descriptor or key hashing/equality behavior remains observable; a new eligibility gate must not silently reorder it.
2. `work.lookup` charges `cache_lookup`, synchronizes a changed operand limit, tests presence and, for a prospective hit, charges `cache_promote`, resynchronizes/rechecks, then moves the entry and returns it. An actual outer hit ends this helper's constructor path.
3. On `None`, `constant_pose` reads `pose.position` and `pose.rotation` again to evaluate arguments to `make` (`1202-1203`). The original helper does not freeze those two reads with the earlier key reads. Any proposed change must preserve the generic fallback; native immutable-operand eligibility cannot be assumed from the old key alone.
4. `make` calls `_vector(position)` first, then `_rotation(orientation)` (`1189-1190`). Python evaluates these calls left to right. A position rejection precedes rotation processing.
5. `_vector` precharges `pose_vector_domain`, verifies a list/tuple of the required length, and either guards an exact native `Fraction` tuple or decodes every element in order with `rational`. `rational` precharges `exact_decode`, rejects booleans/unsupported scalar types, checks finite floats, then calls `bits_fraction` for float decoding. `bits_fraction` precharges `binary64_decode` and checks the prospective dyadic representation width before constructing the exact value (`reach_numeric.py:308-318,375-384`). Low operand caps and malformed or nonfinite values retain their original failure sites.
6. `_rotation` on a `RotationValue` precharges `pose_rotation_reference`, guards components/error and returns it. Otherwise it calls `_vector(orientation,4)`, looks up the constant-rotation key, and on a miss executes the original `_rescale`, including zero-quaternion rejection, prospective width guards, scale/grid arithmetic, sign canonicalization and error addition, then attempts insertion (`280-315`).
7. Only after position and rotation return does `make` call `_vector(velocity)` and then `_vector(omega)`. In the original unmodified default environment both are exact `ZERO` tuples. Each precharges one `pose_vector_domain` and guards its three zero fractions; it does not call `rational` on those native tuple elements.
8. `make` precharges `pose_stationary_check`, then computes `not any(velocity) and not any(omega)`, builds the stationary key, and looks it up. A stationary hit returns its complete saved `PoseValue` only after steps 4-8 have run.
9. On a stationary miss, it constructs `PoseValue(position, rotation, velocity, omega, Fraction(0), self)`, attempts inner insertion, and returns. The outer helper then attempts outer insertion and returns. The allocation itself is not an additional explicit scalar work charge in the original source; a proposed retained copy/storage operation must still follow budget-counting section 3.

Each charged operation first captures the current `_source_after_charge` observer, invokes `external_check` if present, then checks operation and elapsed limits, increments operation/category counters, and finally invokes the captured observer (`reach_numeric.py:71-94`). Callback exceptions are saved as `callback_error` and propagated by identity. An original callback/resource refusal prevents later steps. Category-dictionary operations are also observable Python operations. Removing three charges removes their three callback/check/observer opportunities; type equality alone does not prove equivalent execution.

Native `lookup` and `remember` already synchronize operand-limit changes. There is no claim that warmed native entries survive a changed cap. `remember` captures domain and generation before its insertion charge, rechecks after all insertion/promotion/eviction callbacks, and abandons stale publication (`139-176,248-261`). The static review must preserve this behavior, not add a hypothetical stale-cache defect.

## 4. Original inverse sequence

The outer key uses `inverse=True` and runs the same initial lookup. On a miss, `ReachPoseOps.inverse_pose` (`1442-1456`) proceeds as follows:

1. If the supplied object is already a `PoseValue`, use it directly. Otherwise call `constant_pose(pose)` and execute the complete forward constructor sequence above, including its stationary-cache opportunity.
2. Form the inverse key from the completed forward exact position, full rotation and position-error allowance. Look it up. A hit returns immediately, after the preceding raw-Pose constructor work.
3. On an inverse miss, call `inverse_rotation`. That first executes `_rotation(value.rotation)`, then charges `quaternion_conjugate` with amount 3 and constructs the conjugated rotation while retaining its error (`546-550`).
4. Charge `pose_position_negate` with amount 3, negate the position components, and call `rotate(rotation, negated_position)`. The rotate loop validates rotation before vector, checks a changed cap, and executes `_rotate_guarded`; zero-vector, scalar-rotation, axis and general paths retain their respective original guards, caches and rounding (`552-561` and following).
5. Compute the error in the original evaluation order: `_l1(value.exact_position)` precharges three `pose_norm_bound` occurrences and its exact sum; multiply that bound by `value.angular_error_rad`; then sum `value.position_error_m`, the product and `VECTOR_ERROR` using the original exact operations. Each exact operation precharges, guards operands and prospective widths, performs the operation and guards the result (`reach_numeric.py:321-341`).
6. Construct a full `PoseValue(position, inverse_rotation, ZERO, ZERO, error, self)`, attempt inverse-result insertion, return it to the outer helper, attempt outer insertion and return.

The two zero derivative vectors of the *inverse result* are directly supplied to `PoseValue`; they do not incur another pair of `_vector` calls or another stationarity check. The three-charge target, where applicable, belongs to step 1's forward `make`. It is not doubled for an inverse request.

Identity inputs do not authorize a zero-error replacement. For the ordinary P23 zero-position input, the existing inverse error includes `VECTOR_ERROR` even when the norm product is zero. The raw identity quaternion also passes through the existing projective canonicalization/error path on a cold rotation miss. Preserving only the represented identity rotation cannot justify altering those full-source fields or their failure order.

## 5. What unchanged P23 source establishes

The original P23 file defines 32 keyed mounts at `(0,j/4,0)` for `j=0..31`, 32 independent reach actions, and a three-second scene. `ArmRack` instantiates a `PlanarArm` for each mount. `PlanarArm` supplies one mounting follow, a zero-position pivot and two joints. Both segments have unit length in this fixture; the explicit first-arm forearm-length assignment is also one. `Segment` supplies a zero-position base and two coincident unit-x sites (`hinge_tip` and `tip`). All these local source poses use the identity quaternion. The segment's separate geometry placement rotates mesh geometry; it is not one of the three source-constant graph call sites.

For these immutable source leaves, the possible outer key values are therefore:

| Branch | Possible position values | Count |
| --- | --- | ---: |
| Noninverse mounting follows and zero sites | `(0,j/4,0)`, `j=0..31` | 32 |
| Noninverse unit-length tip sites | `(1,0,0)` | 1 |
| Inverse child bases | `(0,0,0)` | 1 |
| Total key vocabulary | Inverse selector distinguishes the last row | 34 |

This is a source-derived vocabulary for untouched P23 leaves, not a reconstructed run. It says neither that every key is reached before the original cap nor that a key is reached only once. The key deliberately excludes frame identity, so distinct source occurrences with equal numeric leaves can share a result. Conversely, the 256-entry shared cache also contains rotations, inverse poses, source topology, relative compositions, recording cursors and other numerical results. Its capacity being larger than 34 does not prove these 34 entries survive between visits.

Current source has several mechanisms which prevent node count from identifying actual constructor entries: whole-graph reuse; `_pose_slot` hits or translated-source reuse; source-site reuse; body cursors; alternate native identity leaves (`reach_recording_fast.py:1006-1022`); and captured graph paths. The native identity shortcut already handles finite native identity-quaternion leaves, including zero-position inverse leaves, in its own domain. Counting those visits as newly removable ordinary constructor work would double-count existing optimization.

## 6. Cost consequence and precise missing datum

Let `m` be the number of eligible entries to the original default-zero `make` reached through actual outer noninverse misses or raw-Pose inverse misses in the unchanged request. Include stationary hits in `m`; exclude outer hits, direct `inverse_pose(PoseValue)`, upstream builder bypasses, and native direct leaves. If a specialization preserves the existing full `PoseValue`, original position/rotation admission and all existing cache layers, its unconditional gross target is exactly `3*m`: two `pose_vector_domain` charges plus one `pose_stationary_check` per eligible entry. It may not claim all inclusive helper work, all inverse arithmetic, cache evictions or new allocations as removed work.

The net condition remains `A + sum(h_i) + L < 3*m`, with setup, per-invocation eligibility, new retained storage/copies, failure/fallback and retirement included. This review establishes neither `m` nor a complete affordable authority gate. It therefore does not select an implementation.

The missing current-request datum is an exact-source-bound classification of actual helper entries and exits: outer noninverse/inverse lookup result; whether raw `Pose` construction reaches `make`; stationary lookup result; inverse-result lookup result; completed or refused publication; original failure location; and enough surrounding cache/callback/domain context to attribute those results. Aggregate `pose_stationary_check` counts include other `make` callers. Aggregate cache counts mix namespaces. The historical 192 helper calls by themselves do not provide this partition; the additional historical attribution data reviewed below does establish a narrower old-source partition.

Any future diagnostic must be separately scoped and reviewed; this record does not authorize a new request or continuation of a failed tail. If a concrete three-charge design cannot pay for a complete gate, close that design and investigate a larger distinct P23 sampling operation with its own source, cost and consumer proof. Keep the held static-transfer candidate and its adverse timing separate. Original28 remains 24/28; no new pass is established here.

## 7. Independent check of the recovered historical partition

After the initial source review, `/root/retained_census` recovered C020's retained `execution/p23-sampling-observer-001/P23.json`, executed driver and report. This reviewer read those extracted text files as data; no archived code was executed and no archive extraction was performed by this reviewer. The retained-evidence review owns archive/member integrity and full provenance. The observations belong to old source `88473124cc058f7e2926a04d79ab38e340ab4407`, not C041.

The driver's profiler attributes each charge to its nearest selected function. `make`, `constant_pose`, `inverse_pose`, `_vector` and `_rotation` are not separately selected, so their ordinary charges remain attributed to `ReachSimulator._constant_pose`. Both inclusive and self totals are 1,934 for the sampling row; no selected-child subtraction is hidden in that number. The recorded charge amount and actual request/reach work also agree there. The original refusal occurs later in `recording_frames` position projection, not midway through the counted constructor work.

For the historical sampling scope the retained row has 192 calls, 316 lookups, 192 promotions, 248 vector-domain charges, 434 exact decodes, 434 binary64 decodes, 62 stationarity checks, 124 insertions and 124 evictions. It has no rotation-reference, rescale, conjugate or position-negation charge. Under the inspected unmodified native driver/source:

- The 62 stationarity charges identify 62 `make` entries. The 248 vector charges equal four per entry, and 434 scalar decodes equal seven per entry, consistently identifying raw three-position/four-quaternion admission plus the two exact default-zero vectors.
- Those entries require 62 raw-rotation and 62 stationary lookups. `316 - 192 - 62 - 62 = 0` leaves no inverse-result lookup. Therefore none of the historical sampling outer misses took the inverse constructor.
- Outer hits are `192 - 62 = 130`. All 62 raw-rotation lookups hit because no rescale ran. The remaining promotions are `192 - 130 - 62 = 0`, establishing zero stationary hits.
- The 124 insertions and 124 evictions reconcile as 62 outer publications and 62 new stationary-pose publications at cache capacity. The historical sampling gross three-charge target is therefore 186, not `3*192` and not 1,934.

The same record's `advance:0:before` planning row contains 40 calls, 109 lookups, 42 promotions, 34 stationarity checks and 67 insertions. Its single `quaternion_conjugate` amount 3 and `pose_position_negate` amount 3 identify one computed inverse. The analogous partition is 34 `make` entries, 6 outer hits, 34 rotation hits, 2 stationary hits, 32 new stationary-pose allocations and one inverse-result miss. Its lookup equation is `109 = 40 + 34 + 34 + 1`; insertion equation is `67 = 34 + 32 + 1`. The separate three-call `advance:0:after` and three-call `advance:2:before` rows are all outer hits.

This reviewer independently compared ASTs of old/current `_constant_pose`, `make`, `constant_pose`, `inverse_pose`, `lookup` and `remember`; they match. The old/current `charge` AST differs, and the old/current caller/sampler flow is not established identical. Those facts support explaining the historical counts through the common constructor source, but they do not transfer old hit rates or `m` to C041. Warm outer hits cannot be split further into inverse and noninverse from these aggregates alone. These are retrospective data/source deductions, not a new optimization result or measured current saving.
