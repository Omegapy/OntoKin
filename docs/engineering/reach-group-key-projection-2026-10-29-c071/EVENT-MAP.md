# C071 key, event order and authority obligations

The source identities and definition ranges are recorded in [source-binding](source-binding.json) and [derived evidence](derived-evidence.json). All statements here concern the unchanged baseline; proposed routes are not runtime implementation.

## Existing complete-group route

1. `interval_certificates` admits each interval, identifies its source phase, computes enclosing phases and accumulates endpoint/width/shift maxima by `(source_index, selected)`.
2. For each group/carrier visit, it charges `recording_certificate_group`, reads `phase.carriers[frame]`, and constructs the complete enclosing bound from componentwise maxima over `selected`.
3. It computes source allowances, final after-state allowances where applicable, endpoint excess and the original exact additions. Source acceleration/angular speed determine `proof_width`; enclosing speed/angular speed determine `proof_shift`.
4. It constructs the original full key, including the complete source and enclosing `MotionBound` objects. `_reuse` follows its current cache-capability checks and adds `reach_recording_arithmetic_v1`.
5. Cache `lookup` charges lookup, synchronizes operand limits, hashes/compares the actual key and, on hits, charges promotion and rechecks domain/key presence after callbacks. A miss executes the existing `_certificate_quantities` closure.
6. A successful miss may publish through `remember`. Insertion and eviction remain charged; operand-domain and generation changes can refuse publication. Errors do not publish a successful result.
7. Per-output identities, clocks, interval membership and final metadata remain fresh. The supplied-byte reader independently establishes its claims.

## Original miss order inside `_certificate_quantities`

| Ordered stage | Relevant behavior |
| --- | --- |
| Positional addition | Original exact charge, input guards, prospective width guard, operation and result guard |
| Angular region | Nine exact calls with the original endpoint, chord and arc range checks |
| Primitive field collection | Source acceleration/angular speed and complete enclosing fields read in their actual order |
| Primitive outward rounding | Original `upper_binary64` domain, cache and rounding behavior |
| Destination bounds | Original charged destination calculation and outward rounding |
| Temporary source bound | **Late `bound.speed` read** plus rounded acceleration/angular speed |
| Complete interval bounds | Original decode, domain/range and exact arithmetic schedule |
| Final fields | Primitive totals rounded outward; complete displayed totals recomputed from rounded primitives |

Numerical nonuse of the temporary source-speed field does not erase its original late read. A projected hit would also suppress all the original miss's guards, callbacks and first errors. Native passive execution therefore needs authenticated current inputs, formula and dispatch before such a hit can replace the miss.

## Concrete candidate and fallback

The studied candidate uses `certificate_group_source_speed_projection_v1`, source acceleration/angular speed, the complete enclosing bound and every other original field. It remains inside the existing request cache, with no second store or capacity increase. A distinct tag prevents collisions with the original full-key foreign route or another cache family.

Any unsupported/custom work, bound, numerical value, descriptor, hash/equality or callback route must retain the original full key and `_reuse` behavior. Do not read projected fields first and only then decide to fall back. Earlier reads can themselves change the first observable event.

An exact dataclass type does not authenticate field types or class/function lifetime. `MotionBound` annotations are not runtime validation. A conditional foreign-speed hash witness can distinguish full-key hashing from projected hashing for a mixed enclosing input. It remains unexecuted and does not claim stock production accepts that hostile input.

Native authority must cover the current field domains, generated comparison/hash methods, descriptors, numerical functions, global bindings, work instance, cache methods, callback provenance and live operand domain. A saved function alias is insufficient. The reader's `_certificate_term_native` illustrates substantial existing checks, but it is reader-specific and cannot be transplanted as proof. C057 remains open.

## Existing protections and their limits

`ReachExecutionWork.charge` captures the source observer, invokes the external check, checks request work/time, increments counters and then invokes the captured observer. `ConstructionBudget.tick` can invoke its check before shared construction accounting. These callbacks can raise or alter relevant state; speculative reordered checks must preserve actual first-error behavior.

`lookup` already resets a changed operand domain and checks the key again after charged promotion. `remember` already detects changed generation/domain before publication. This investigation does not describe a narrowed cap as an automatically stale hit. Those mechanisms still do not prove authority for suppressing an additional calculation on newly equivalent inputs.

Replaying every original charged seam on a proposed generic hit leaves no omitted arithmetic charges to finance new checks. This is a statement about that replay route, not a ban on separately proved native finite reuse.

## Finite result and cost boundary

For P11/L03 every enclosing set is the singleton source phase. The projected key reconstructs the complete source bound through retained `enclosing.speed`. It therefore preserves exact equality classes across all visits. Under passive native unchanged surrounding work, the same bounded cache sequence follows under key renaming, including nested calculations and downstream relative order. The direct saving is zero even with free new overhead.

This proof needs neither exact full tuples nor an observed ordered LRU trace. It does require the source-bound native structure and matched cache semantics stated above. Generic mutation/callback behavior is not included in that claim. Mixed-phase opportunities, hashing latency and other optimization targets remain outside it.
