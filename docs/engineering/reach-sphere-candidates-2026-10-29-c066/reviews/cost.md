# C066 independent cost review

## Decision and scope

**The eight-point schedule has no established positive complete-request cost premise yet. Its arithmetic opportunity is real but conditional. This review does not prove all finite sphere shortlists unprofitable.** In particular, a blanket one-charge-per-vertex membership policy is not the only possible implementation and is not a sufficient basis for a universal NO-GO.

This is source inspection and symbolic accounting. No OntoKin imports, product requests, numerical geometry replay, runtime suites, instrumentation or hosted jobs were executed. Runtime source was read from the recovered C064 repository, which the parent reports as the unchanged C065 runtime. The parent must bind exact source identities in the final record.

Sources inspected: `ontokin/geometry.py` (`sphere_mesh`), `ontokin/scene.py` (`_source_primitive_snapshot`, `_source_primitive_mesh`), `ontokin/reach_conformance.py` (`_Bounds`, `_vertex_extrema`, `_vertex_extrema_uncached`, `_geometry_bounds`), and `ontokin/reach_numeric.py` (`ReachExecutionWork`). The inherited numerical and budget-counting documents were read as context; their own proposed/adopted status must remain intact.

## Existing work that can actually be omitted

The fixed constructor has 32 longitude segments and 16 latitude bands: one top pole, 15 rings of 32 points, and one bottom pole, for **482 source positions**. It creates binary64 coordinates by evaluating its trigonometric expressions and multiplying each resulting normal component by the actual radius.

For an ordinary native-float point, `_vertex_extrema_uncached` first charges `independent_geometry_point`, checks all three actual source-to-binary32 coordinates, computes the upward binary64 L1 screen and checks its existing repeated-maximum witness. Only a point that passes both existing screens reaches the exact candidate calculation.

Every completed existing float candidate calculation uses:

- Three `independent_bound_decode` charges, one for each absolute float coordinate.
- Three `independent_exact_add` charges, because `arithmetic.total` receives a generator and therefore takes its complete direct fold, including the initial addition to exact zero.

This is **six numerical operation charges per completed candidate event**, including candidates that prove smaller than the current maximum. The tuple-only sparse-total optimization does not apply to this generator. The native `guard_bits` method does not add a work charge, but its failure behavior remains an obligation. The baseline `candidate > radius` and equality tests are currently ordinary rational comparisons, not `_Bounds.compare` charge calls; this proposal cannot invent their removal as an additional measured operation saving. The separate C057 accounting concern remains open.

Let B be the number of those six-charge events in one complete baseline cold scan. The correct gross opportunity is at most 6B, not 6 times 482 by assumption. `0 <= B <= 482` is only a structural envelope; no B for an original recording or any concrete radius has been established by this review.

All other existing work remains: the 482 geometry-point charges, per-point binary32 checks, float component-error maxima, three final error decodes and the error norm, source mesh creation/cache work, source provenance/topology/normals, site-radius calculations, extrema-proof publication and warm validation. Existing float upper screening, repeated-max witnesses, error-max decoding and repeated-mesh reuse earn no new credit.

## The selected eight-point schedule

The proposed mathematical indices are latitude 5 or 11 and longitude 4, 12, 20 or 28. In the actual source position order their zero-based indices are:

`133, 141, 149, 157, 325, 333, 341, 349`.

For this review, the cheaper schedule considered is an in-order scan that keeps the original geometry/error work, performs membership selection only after its own existing upper/witness screen passes, and computes exact candidates only for admitted shortlist points. No ahead-of-order exact candidate precomputation is assumed.

For one successfully completed eligible cold scan, let:

- B = existing baseline exact-candidate events on that same input under the same admissible stable authority.
- K = exact-candidate events performed by the proposed scan, with `0 <= K <= 8`.
- L = all new selection-operation charges actually executed by the proposed scan.
- A = all other new admission, setup, retained-occurrence, construction, copying, dispatch and publication charges attributable to that scan.
- F = all additional fallback or repeated-scan work caused by the proposal, expressed in the same charged-operation units.

Then a necessary net accounting equation is:

`net saving = 6(B - K) - L - A - F`.

It is an equality only if every unchanged event really remains unchanged and no other new work is omitted. Otherwise its right-hand side is an optimistic upper bound. A useful premise requires a justified positive lower bound for this net quantity over the admitted successful domain, together with the applicable first-exception obligations.

### Selection count is not baseline candidate count

The baseline incumbent radius increases at omitted early candidates. A shortlist-only scan does not compute those incumbents. Consequently the proposed scan's screen passes need not equal the baseline's B events.

Until the first shortlisted point, index 133, the proposed radius and radius floor remain zero and there is no repeated-maximum witness. On a successful native-float prefix, even zero absolute components give a strictly positive upward `nextafter` screen. Therefore **at least 134 screen passes and membership decisions occur through index 133**. This conclusion uses source order and the proposed zero incumbent; it does not replay any product geometry.

With exactly one charged membership operation per proposed screen pass E and no additional per-point selection work, `L = E` and `E >= 134` for a completed eligible scan. The optimistic necessity is then:

`6(B - K) > 134 + A + F`.

Actual E may be larger than 134. It is not valid to substitute B for E in `6(B-K)-E`. Maintaining the baseline incumbent merely to preserve its old screen decisions would require computing its omitted candidates or supplying a separately funded, mathematically valid replacement screen.

This lower bound on E does not alone reject the schedule. B might be large enough on an admitted domain; that has to be proved from actual generated binary64 vertices and the baseline predicates. No such B lower bound or complete A upper bound has been established here.

### Index membership itself needs a bounded mechanism

The existing loop iterates `zip(source_positions, stored_positions)` without an explicit ordinal. A proposal that adds `enumerate` or a manually maintained ordinal must account for the new selection/index-tracking work under its stated charging unit. It cannot call the membership operation free because a geometry-point tick already exists, and it cannot simply relabel an omitted decode as a successful decode while doing unrelated work.

One alternative avoids an added ordinal during the full scan: select and retain the identities of the eight native point tuples once, then perform bounded identity-set membership only when the proposed screen passes. The immutable outer source tuple retains all point objects, preventing identity reuse while it remains retained. This option still needs:

- Charges for each actual shortlist index access, identity extraction, container insertion and copied logical occurrence under the selected representation.
- A bounded eight-entry representation and any setup/lookup charges.
- A proof that these are the actual current constructor-produced points, not merely some native tuple with 482 rows.
- Complete native/type/domain and producer-to-consumer authority, including changes at callbacks.
- No setup work performed for a warm hit that would otherwise return unchanged.

The source-only review has not selected a final charge schedule for these actions. Thus the one-charge-per-screen-pass formula is a favorable conditional schedule, not a claim that a real implementation has A equal to zero.

For comparison only, a naive added membership charge on all 482 vertices gives the stricter requirement `6(B-K) > 482 + A + F`. That finite schedule can be rejected if its own B bound proves insufficient. Its failure would not reject the cheaper schedule above.

## Copying, admission and fallback ledger

A completed implementation ledger must enumerate the actual representation rather than hide work in a constant label. At minimum it must account for each of the following when present:

| New work | Required accounting treatment |
| --- | --- |
| Constructor identity, dimensions and radius-domain admission | Count checks and any proof construction; numerical equality or a `sphere` name is insufficient authority. |
| Type/domain checks on actual selected points or complete source shape | Count every new check under a declared bounded charging schedule; baseline conversion/type work can only be credited if it is actually reused at the same authorized point. |
| Selection/index tracking | Count the chosen mechanism; distinguish all-vertex ordinal work from selection only at proposed screen passes. |
| Retained point identities or copied values | Count actual created occurrences and container operations; native references may avoid detached numeric copies but do not establish authority for free. |
| New exact candidate evaluations | Six original-style charges each unless a separately justified arithmetic schedule changes them. Such a change is another proof obligation. |
| New comparisons used in admission/proof | Charge their actual selection/claim work; do not treat ordinary baseline uncharged comparisons as removable budget headroom. |
| Cache lookup, insertion, promotion or eviction introduced by the new design | Retain native `ReachExecutionWork` charges; do not allocate a second free cache. |
| Rejected admission or failed proof | Charge all work already executed, even if no later candidate is saved. |
| Restart/fallback | Count the entire extra executed prefix and any repeated scan/error/cache work, not only the final successful continuation. |
| Producer setup with no consumer | Count it, including work in a writer role if a generic constructor is changed. Independent-reader and writer proof namespaces remain separate. |

Reusing the timing slot of a baseline charge is not itself a cost saving. If one formerly executed decode is replaced by one properly charged selection operation, the selection consumes one of the six possible omitted charges. For a retained exact candidate the selection is additional to its six charges. The category and source record must describe the actual operation performed.

## Complete request and replay

A request can encounter the same numerical sphere more than once without repeating a cold extrema calculation. `_source_primitive_mesh` already caches native geometry under role-specific exact recipe keys, and `_vertex_extrema` already caches extrema by retained source-position identity and operand cap. A clean warm sphere proof uses its existing lookup/promotion, four reuse-block charges for 482 rows, comparisons of actual stored rows, and final operand guards. It performs no cold exact-candidate calculation to fund new shortlist work.

New eligibility or shortlist setup should therefore be reached only on an actual direct/uncached path if warm behavior is to remain unchanged. Preparing metadata at the caller before discovering a warm hit is real overhead even if the cold helper later ignores it.

A cache miss is not necessarily the only direct scan. The existing wrapper can call the direct path again after domain changes, failed proof-row validation, changed stored conversion results, or publication-time domain changes. Warm validation can also fall back to a direct scan. Cache eviction or reconstructed mesh identities can create later cold work. The ledger must follow actual attempts, not count one saving per distinct authored radius, sphere object or animation frame.

For a whole successful request, partition each affected complete direct attempt i and write:

`request saving = sum_i 6(B_i - K_i) - sum_i (L_i + A_i + F_i) - W - U`.

W includes new warm-hit overhead. U includes new setup on paths that never execute a benefiting scan. Do not count common mesh construction or previously existing reuse as new savings.

For a failed/partial attempt, the six-charge event abstraction is insufficient: a callback or operand guard can interrupt between a decode and its addition. Use the actual completed baseline and candidate charge events in the prefix, preserving the first exception, and subtract every executed new event. No future omitted candidate may fund a prefix that never reaches it. A complete-request positive premise cannot be inferred from successful scans alone when rejected admissions or replay add unbounded or unaccounted work.

## Remaining gates

Cost approval requires a concrete admitted radius/constructor/authority domain, a proof that the eight actual binary64 points cover the exact L1 maximum in that domain, and an explicit schedule whose B/K/L/A/F bounds yield positive request-wide saving. Exact positive finite radius alone does not establish those items. Input-dependent baseline screens, subnormal/rounding behavior, native constructor provenance, mutable callback authority and first exceptions must be resolved before instrumentation.

The source supports the six-charge candidate opportunity and the symbolic accounting above. It does not support a measured saving, an original-recording improvement, a complete positive budget premise, or a universal impossibility claim.
