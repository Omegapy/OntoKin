# Exact deferred source-phase locations

This implementation note describes an arithmetic work-avoidance change in
`reach_phase.py`. It changes no source coordinates, phase boundary, subdivision
formula, tolerance, operation cap, logical output limit or independent reader.
The returned values remain the ordinary complete immutable `PhaseBound` records.
Current implementation and validation identities must be recorded separately;
this derivation does not claim that tests or release gates have run.

The port recovers the idea in historical commits
`4e801bb725499067be55b130fbd4a23b107e8563` and
`14dbf1bec3de337f8539e8105a4f6b7747e19bc0`, adapting it to the current signed
coaxial derivative proof and immutable recording angular witnesses. Historical
test results do not validate this port.

## Exact location invariant

Write a complete source bound's private position extent as `M`, accumulated
offset extent as `L`, position error as `P`, and rotation error including
exposure as `R`. The existing uniform equation is affine in the first two:

```
P = P_anchor + L*(R - EXPOSED_ROTATION_ERROR)
    + N_vector*VECTOR_ERROR + M*2^-53 + 3*2^-1075.
```

A phase-local `_PhaseLocation(relative, extent, offset)` represents the complete
bound obtained from `relative` by exactly these replacements:

```
M = relative.M + extent
L = relative.L + offset
P = relative.P + extent*2^-53
    + offset*(relative.R - EXPOSED_ROTATION_ERROR).
```

All other fifteen fields are unchanged. The implementation uses guarded exact
fractions for each product and sum. There is no approximate materialization,
sampled error estimate or replacement source trajectory.

The ordinary composition equations do not read the parent's `M`, `L` or `P`
when calculating ideal derivatives, actual derivatives, derivative errors,
counts, angular errors or anchor errors. Consequently, the same outer extent
and offset can pass through successive relative compositions. At materialization
the formula uses that descendant's complete `R`, so the offset receives every
rotation error accumulated along the descendant path.

The existing local-translation factorization has a narrower prerequisite: the
parent's ideal angular speed and acceleration, actual angular speed and angular
velocity error must all be exactly zero. Under that prerequisite a local
translation affects no derivative equation. Its contributions can be added once
to the outer location:

```
extent' = extent + 2*local.M
offset' = offset + local.L + local.M.
```

The relative local bound then has zero `M`, `L` and `P`, with every other field
unchanged. Other local translations retain their complete original operands in
the ordinary relative recurrence.

## Coaxial laws and recording witnesses

The fresh topology-derived `axial_rate` still enters every relative composition.
The existing derivative tightening runs at the same source node after the
ordinary recurrence. Location materialization changes no ideal or actual rate,
acceleration, derivative allowance, count or angle allowance.

An optional `RecordingAngularFrame` takes its `trig_count` from the complete
relative bound because that field is invariant under materialization. Its rate,
parent identity, complete typed source witness and fresh opaque token use the
unchanged proof path. The complete returned frame bound has that identical
count. No deferred location record escapes through either a frame map or a
recording proof.

## Operand limits, cancellation and storage

Deferral is considered only in the unchanged full 32,768-bit operand domain and
when the source graph exceeds the existing numeric-cache capacity. It is useful
for repeated paths whose different outer translations would otherwise replace
the same cached affine result repeatedly.

The proof admits only exact spatial constituents at most 2,048 bits wide in
numerator and denominator. The final equations contain at most five rational
products or sums; the 1/16 width margin admits the original prospective spatial
intermediates before reduction. The eligibility check includes both bounds'
`M`, `L`, `P` and `R`, together with both outer offsets. Unrelated derivative
fields retain their original full operand and arithmetic guards. Wider spatial
values and narrower live caps take the original eager path.

All complete relative fields and location offsets are guarded on each use.
Each real arithmetic operation remains charged. Cache lookup, publication and
final result callbacks remain cooperative cancellation points. If a callback
narrows the domain during a relative recurrence, its complete original parent
is materialized before the eager recurrence is reconsidered. A cached relative
result is never treated as a completed proof for a larger position under the
new domain. A callback exception retains its original identity, including one
whose type happens to equal the private internal fallback exception.

The existing bounded numeric cache and its capacity are unchanged. Location
records live only in the existing traversal's object/frame maps. Each returned
node is materialized once; an object and its corresponding frame retain the
same ordinary immutable record. Whole source identities, claims, state and
returned coverage remain unchanged.

## Required verification

`tests/test_reach_phase_locations.py` compares complete eager/deferred results
for translated mounts, both P23 phases, moving/released paths, and a translated
coaxial chain. It checks all eighteen returned fields, recording witnesses and
trigonometric counts, object/frame identity, changed inputs, cache eviction,
wide operands, cap changes during recurrence and materialization, and original
cancellation with a fresh retry. Relevant phase, lifecycle and numeric-domain
cohorts and a fresh unchanged-budget P23 recording are still required before
claiming current execution results.
