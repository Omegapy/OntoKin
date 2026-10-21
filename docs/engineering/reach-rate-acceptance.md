# Proposed pointwise acceptance for source rate inspections

## Status and owned scope

This is a **proposed comparison criterion**, not an adopted language tolerance,
a passed source-execution release role, or completion of the full product goal.
The adopted [planar reach contract](../language-design/planar-reach-v0.1/ADOPTION.md)
and [release contract](../language-design/planar-reach-v0.1/release-contract.md)
retain their authority. Existing frozen source and preparation expectations are
unchanged.

| Checkpoint field | Value |
| --- | --- |
| Owning branch | `work/reach06-rate-audit-20261020-2338-7of9` |
| Exact starting parent | `b8192e761c5ae32d27734f14aee26aca8d7898ff` |
| Coordination | [Issue #24](https://github.com/Omegapy/OntoKin/issues/24), independent branch work |
| New files owned | `tools/reach_source_rates.py`, `tests/test_reach_source_rates.py`, this document |
| Existing dependencies | `ReachReference`, shared construction/reach work, actual source snapshots, numerical derivations |
| Preparation status | Implemented for independent review; execution evidence must be recorded separately |
| Adoption status | Pending; no existing acceptance field or frozen limit is amended |

The active finite direction is the reusable planar reach release. Its source,
Agent, recording, destination, compatibility and inherited roles remain distinct
obligations. The broader [GOAL](../../GOAL.md) remains open.

## The question this checker answers

For one canonical carrier, exact source time, and `before` or `after` side, the
checker asks whether the **defined source inspection vector** is within the
independently derived arithmetic allowance of its ideal mathematical vector.
The two supported fields are `velocity_m_per_s` and
`angular_velocity_rad_per_s`, each with three world-frame components. They are
the velocity and omega inspection fields, not finite-difference derivatives of
rounded positions or quaternion components. Source interpolation, public
extraction and event-side semantics have their own rounding and state rules.

This is a pointwise numerical question. It does not establish the continuous
error over an interval, action outcome correctness, compiler correctness, full
source-closure conformance, Agent protocol correctness or destination motion.

There are three different inputs whose meanings must remain visible:

1. **Actual inspection:** finite binary64 values obtained from a source snapshot,
   or explicitly asserted as such by a caller of the lower-level interface.
2. **Independent ideal enclosure and source allowance:** exact rational bounds
   from the actual `ReachReference` implementation for that source, time and side.
3. **Optional frozen preparation values:** finite binary64 measurements whose
   preparation-oracle error has not been established by this checker.

The third input never determines the proposed verdict and never inherits the
actual implementation's arithmetic allowance.

## Exact rule and proof

Let the observed vector be `a = (a_1, a_2, a_3)`. Each binary64 component is
converted exactly to a `Fraction`, without decimal approximation. Let the
independent ideal vector `v` be enclosed by the Cartesian box

\[
B = [l_1,h_1] \times [l_2,h_2] \times [l_3,h_3], \qquad v \in B.
\]

Let `E >= 0` be the independent source arithmetic allowance, in the same vector
units. The source derivation defines the velocity and omega errors as Euclidean
norm bounds. Its use of conservative L1 bounds in intermediate rounding steps
does not change this public vector-norm interpretation; see the
[source numerical kernel](reach-source-kernel.md).

For each coordinate, define the distance to the interval and the farthest
endpoint distance:

\[
d_i = \max(l_i-a_i,\;0,\;a_i-h_i),
\qquad D_i = \max(|a_i-l_i|,\;|a_i-h_i|).
\]

Then compute exactly

\[
L^2 = \sum_{i=1}^{3} d_i^2,
\qquad U^2 = \sum_{i=1}^{3} D_i^2.
\]

For every `v` in the box, each coordinate's squared difference lies between
`d_i²` and `D_i²`. Adding yields

\[
L^2 \leq \|a-v\|_2^2 \leq U^2.
\]

The box admits independent coordinates, so both extrema are attained in the
box. The farthest point may use a different endpoint choice for each coordinate;
checking only the all-low and all-high corners is insufficient. Correlation
between the true ideal components may make the box conservative, which can
produce an unresolved result without invalidating either implication below.

| Exact relation | Proposed status | Meaning |
| --- | --- | --- |
| `U² <= E²` | `proved` | Every ideal vector in the supplied enclosure satisfies the allowance. |
| `L² > E²` | `contradicted` | Every ideal vector in the supplied enclosure exceeds the allowance. |
| Otherwise | `unresolved` | The enclosure permits both possibilities; no conclusion is asserted. |

Equality belongs to the allowed region. Thus `L² == E²` with `U² > E²` remains
unresolved. No square root, epsilon, midpoint substitution, componentwise
tolerance or host floating-point norm participates in this decision. Squaring
exact fractions also preserves subnormal differences that would underflow in a
binary64 squared norm.

The proof is conditional on the independent enclosure and source allowance
being correct for the identified implementation. This new document does not
replace review of that underlying derivation.

## Where the enclosure and allowance come from

The source-aware interface requires an actual `ReachReference` and invokes:

```python
pose = reference.pose_enclosure(carrier, time, side, ideal=True)
phase = reference.point_phase(carrier, time, side)
```

`pose.velocity` and `pose.omega` supply exact interval endpoints.
`phase.source_numeric_velocity_error` and
`phase.source_numeric_angular_velocity_error` supply `E_v` and `E_w`.
The returned phase must identify the requested canonical carrier and have
`phase.start == phase.end == time`.

The existing independent reference reconstructs source topology and state, ideal
and actual affine slopes, coordinate discrepancies, inherited transform errors,
public extraction rounding, and dynamic release/force/impulse anchors. The
[source kernel derivation](reach-source-kernel.md) explains these recurrences;
the [numeric kernel derivation](reach-numeric-kernel.md) fixes the implementation
and derivation hash scheme. This checker calls those actual independent methods
instead of copying a tolerance from a fixture or regenerating an expectation
with the production evaluator, pose kernel or inverse-kinematics solver.

The reference is built from the compiled source model. Independently checking
that model against the authored source remains a separate obligation. Identical
source hashes establish identity, not compiler correctness.

## Interfaces and observation provenance

`compare_rate_vector(actual, ideal_intervals, allowance, work=work, frozen=None)`
provides the exact mathematical comparison for one vector. It establishes no
source identity and must not be reported as a fresh source execution.

`audit_source_rates(reference, observation, work=work, frozen=None)` binds that
comparison to a source reference. The observation schema is
`ontokin.reach-rate-observation/0.1` with exactly these fields:

```text
schema_version
source: profile, program_revision, module_key, scene_key, sources
time_seconds
side
carriers: canonical carrier -> both supported rate vectors
```

`source.sources` contains the complete source-ID to source-revision map captured
by the compiled model. Program and source revisions must be complete lowercase
SHA-256 identities. The profile must be `planar-reach-0.1`. The source identity
must equal the reference's captured source identity. The exact time must be
inside its built prefix. Carriers use `world` or actual canonical object/site
`.frame` paths; a successful lookup by an unrelated alias is not sufficient.

Packet clocks must be JSON integers or exact decimal/fraction strings. Boolean,
floating-point and `Fraction` packet clocks are rejected. The high-level Python
interface separately accepts an exact `Fraction` time argument and obtains the
actual snapshot's JSON clock. Exponent strings are rejected before constructing
arbitrary-sized rational values.

The low-level report explicitly says
`observation_provenance: supplied_identity_assertion`. Matching identities does
not establish that a caller-supplied vector was produced by the named source.
`observation_from_snapshot` is only a bounded extraction helper and carries the
same limitation when called on supplied data.

`execute_source_rate_audit(bundle, time=..., side=..., carriers=..., ...)`
provides the fresh path. It compiles the supplied bundle, obtains an actual
`ReachSimulator` snapshot, builds the independent reference through the requested
time, and compares selected fields. It retains the exact compiler work object
through all those stages. Its report says
`observation_provenance: fresh_compile_and_source_snapshot_in_this_call`.
Optional construction `budgets` and cancellation `check` are passed to the
actual compiler; limits cannot be raised through this interface.

The optional frozen packet uses
`ontokin.reach-frozen-rate-observation/0.1`. It must match source, time and side,
and may supply either field for any subset of selected carriers. It records
binary64 bits, exact observed-minus-frozen differences and exact distances from
the frozen vector to the ideal box. Every such measurement says
`acceptance_status: not_established` and `used_for_verdict: false`. Exact bit
equality remains distinct from numeric equality, including signed zeros.

## Work limits and unavailable references

Every checked operand, rational operation, comparison, serialization chunk and
bounded file-hash chunk charges the caller's existing work context. The checker
requires an operation limit no greater than 100,000 and an operand limit no
greater than 32,768 bits. It guards intermediate cross-products before allocation
and respects any lower operand limit. Inputs are restricted to plain bounded
containers, three-component finite binary64 vectors, and exact finite rational
interval endpoints and allowances. Booleans, NaN, infinity and inexact integer
conversions are rejected.

The selected carrier limit is 4,096; source identities are limited to 256 entries;
individual text fields to 4,096 UTF-8 bytes; canonical observation hashing and
each identified file to 262,144 bytes. These are checker resource limits, not
additional language support promises. Hitting them does not establish a source
numeric contradiction.

No stage resets, replaces or extends the work budget. The outer construction
request counter includes earlier parsing/construction plus later checks invoked
through the reach work callback. The report records
`compilation_request_operations`, final `request_operations` and its limit, and
final `reach_work_operations` and its limit separately. The inner reach counter
alone is not the total request cost; these overlapping counters are not added.

A large valid source request can consume nearly all its allowance before the
additional independent audit. Such a request may exhaust the shared budget.
Resource and cancellation exceptions propagate unchanged, including an original
callback exception whose type is `ReferenceError`. They are not converted into
`proved` or `contradicted`, and no partial result is silently certified. A caller
may record the audit as unavailable, with the actual failure evidence. Separately
bounded analysis of recorded observations is useful, but remains an asserted
observation audit unless its execution provenance is independently established.

There is also a specific reference limitation: `build_reference(end=t)` stages
both sides of events through `t`. At a failed boundary, actual incoming source
state can be valid while that reference construction fails on the outgoing
transition. The fresh wrapper reports `unresolved` with
`reason: reference_unavailable` and the original reference diagnostic. It retains
the exact requested time/side and observed identity. It does not use an epsilon,
skip the sample or assume that a later state succeeded. Ordinary invalid source
execution and resource/cancellation failures still propagate as failures.

## Input identities and reproducibility

The report identifies the selected observation bytes and optional frozen packet
by canonical JSON SHA-256. Exact fractions in the report use hexadecimal signed
numerators and positive denominators, avoiding configurable decimal digit limits.
It also records individual file hashes and aggregates for four ordered groups:

| Group | Ordered inputs |
| --- | --- |
| Source numeric implementation | `ontokin/reach_numeric.py`, `ontokin/reach_kinematics.py`, `ontokin/reach_pose.py`, `ontokin/reach_phase.py`, `ontokin/reach_runtime.py` |
| Source numerical derivation | `docs/engineering/reach-numeric-kernel.md`, `docs/engineering/reach-source-kernel.md` |
| Independent source reference | `ontokin/reach_reference.py` |
| Proposed rate audit | `tools/reach_source_rates.py`, `docs/engineering/reach-rate-acceptance.md` |

For each group, the aggregate hashes the concatenated ASCII records
`path + NUL + lowercase_hex_sha256 + newline` in the listed order. Symlinked,
escaping, absent or oversized inputs are rejected. The imported reference must
come from this checkout. Hashes must remain equal before and after the
comparison; the fresh wrapper also checks them around source observation and
reference construction.

Compilation occurs before the fresh wrapper's hash window. The report explicitly
records `compilation_preceded_hash_window: true`. These numerical input groups
are not a complete compiler or release-input closure, and matching files do not
prove that arbitrary modified in-memory Python objects match their files. A
reviewable execution record must separately identify the actual Git revision,
clean/dirty state, complete eligible inputs, interpreter/platform, command,
environment and logs. This proposal creates no synthetic passing release record.

## Focused checks and remaining adoption work

`tests/test_reach_source_rates.py` contains independently calculable 3–4–5,
componentwise-versus-Euclidean, mixed-corner, equality, interval-ambiguity and
subnormal cases. It also covers frozen measurement separation, malformed input,
operand/work limits and callback identity. Source cases exercise actual source
snapshots, block production expectation generators during independent reference
comparison, detect a deliberately changed velocity, reject stale identities,
record fresh provenance, and preserve the failed-boundary incoming-side gap.

The authored tests are not execution evidence. Preparation and review must obey
the repository's exclusive executor procedure; no concurrent source edits may
invalidate a claimed run. The focused command, when an execution window is held,
is:

```bash
python3 -m unittest discover -s tests -p 'test_reach_source_rates.py' -v
```

Before any adoption, independently review the source derivative-error derivation
against the exact implementation; execute the focused tests and actual source
inventory; preserve all unresolved, unavailable and resource outcomes; and decide
the criterion's authority in a separate versioned acceptance change. Complete
source, native, protocol, recording, browser, compatibility and inherited roles
remain required by the existing release contract. Every current report keeps
`criterion_status: proposed_not_adopted`, `release_acceptance: false`,
`source_execution_role: pending` and `full_product_goal_completed: false`.
