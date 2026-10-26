# C045 cost review: conditional angular-prefix reuse

Date: October 26, 2026, America/Denver. Reviewer: `/root/cost_review`.
Reviewed source parent: `91e8899ad90f04292dd4aee5aaec8b730b397d45`, tree
`11d1ce9acc2cb4fa93be44c4772a9e8e3b3270ff`.

**Decision: the defined `B-Angular/full-entry-audit/0.1` schedule cannot provide
a positive charged bound for the observed 32-call group. Its structural cost
filter must decline that group. No runtime implementation is selected.**

This is a source and retained-data review. It includes independent AST counting
and JSON metadata inspection, with no product import or execution, candidate
numerical replay, candidate-cache simulation, benchmark or test. The reviewer
contributed the full-entry audit cost argument during design discussion; this
is not independent authorship of that candidate. The separate authority review
provides the independently assigned authority assessment.

## Evidence used

- [C044 exact census](../checkpoint-044-census.json) supplies 32 completed cold
  calls, one exact angular signature, 32 distinct whole keys, and a cache size
  of 256 at every envelope entry. Its SHA-256 is
  `5f1f66af9999cad3f0e46d3e249d0cb57c9920f5c18044ff9d962bed9aa4563f`.
- [C044 archive manifest](../checkpoint-044-evidence-manifest.json) identifies
  `c044-analysis/cache-review/attempt-001/ordered-cache-checkpoints.json`.
  The restored file has SHA-256
  `5db65f2ba84e711e97a29c818f699e37cfb4ac9fb2cc5da87dfb335fbe331e13`.
  Its `envelope_1_entry` order contains 256 original entries.
- [Current recording arithmetic](../../../../ontokin/reach_recording_fast.py)
  has SHA-256
  `bbe0a389f633dd4e6974538b17d2f92d8ed6658b8078ca0ae666fa3df6a4391e`.
  Independent AST inspection of `recording_float_excess` confirms one
  `source_leaves` site, four `e` sites, four `g` sites and four `q` sites.
- [Original numerical work/cache code](../../../../ontokin/reach_numeric.py),
  [captured-phase code](../../../../ontokin/reach_recording_capture.py), and
  [budget-counting section 3](../../../language-design/planar-reach-v0.1/budget-counting.md#3-preflight-exact-accounting-and-finite-reuse)
  establish the relevant charge, callback, storage and fallback obligations.
- [C043 cost ledger](../checkpoint-043-cost-ledger.json) remains the source for
  its rejected unconditional cold-domain examples. C045 does not relabel them
  as current P23 observations.

The selected prefix has 13 original arithmetic sites. Ten ordinary position
sites remain. The original comparisons and the late rotation multiplication
also remain in this candidate. These are source-site counts, not a measured
candidate result.

## Defined schedule and its accounting unit

The proposed batch rule is structural. It considers repeated exact angular
inputs in one bounded captured-phase envelope group, under the same method,
live operand domain and required native authority. It does not identify a
fixture, frame name, request option or particular integer values as eligibility.
Original whole-result lookups remain first, and an ordinary warm whole-result
return remains on its original path.

The proposed reusable prefix would belong to an existing whole-result entry.
No separate LRU entry or free private numerical cache is assumed. That storage
idea still needs a complete proof of payload integrity, bounded copied fields,
entry survival, non-retention after retirement and unchanged return behavior.
Those obligations are not established by the original whole-entry survival.

For a prospective admitted batch, this particular schedule performs a full
entry audit of the existing numerical cache. It charges at least one unit for
each key admission and one separate unit for each value/lifetime admission.
The key admission is intended to rule out foreign hashing/equality behavior;
the value/lifetime admission addresses value access and release when original
evictions occur. Further nested checks, snapshots and callbacks can add work.
The two-unit floor is therefore a property of the chosen schedule. It is not a
theorem that every possible cache-authority design must use two units per entry.

The full audit is granted once per batch, not once per call. This is favorable
to the candidate. Existing captured-phase source receipts do not establish that
such a once-per-batch work/cache certificate is already available at no cost.

## Closed charged bound for this group

Let `N` be the number of calls in the proposed common-signature group and `C`
the number of cache entries at the prospective batch admission. Grant the
candidate a successful first original calculation and all `N-1` later prefix
substitutions. Grant every other unresolved admission, key, copy, guard,
fallback, storage, lifetime and induced-work obligation zero cost solely to
obtain an optimistic upper bound.

The bound is:

```text
prefix gross saving <= 13 * (N - 1)
defined full-entry audit cost >= 2 * C
forced admitted-route net saving <= 13 * (N - 1) - 2 * C
```

The observed values are `N = 32` and `C = 256`:

| Term | Bound |
| --- | ---: |
| Repeated original prefix sites | 403 |
| Defined key admissions | at least 256 |
| Defined value/lifetime admissions | at least 256 |
| Full-entry audit alone | at least 512 |
| Forced admitted-route net saving | at most -109 |

Thus the proposed profitability prefilter `13 * (N - 1) > 2 * C` is false for
the actual group. A correct conditional implementation would decline before
performing the full audit. It would obtain zero prefix substitutions for this
group, and any screening cost would still be real work. **The 512 figure is
not a measurement of that declined path.** It is the lower bound on the
hypothetical admitted route that makes admission untenable here.

At a full 256-entry cache, `N >= 41` is a necessary condition for this prefix
schedule to survive even that optimistic filter. It is not a sufficient
condition for positive saving or safety: all omitted positive costs and all
authority and lifetime requirements still apply.

For sensitivity only, granting reuse of the late rotation site would raise the
gross ceiling to `14 * 31 = 434`, leaving a forced-route saving upper bound of
`434 - 512 = -78`. Late reuse is not selected. Its different callback and
failure boundary would require a separate proof.

## What this bound does and does not establish

The rejection does not need the number of diagnostic categories at batch
entry. C044 records 222 categories at final failure, but does not retain an
entry category map. This review does not move that final count backward in
time. Category authentication is an additional unresolved cost, not part of
the 512 floor.

The recorded entry keys have nested content and the cache contains numerical
payloads that C044 did not fully traverse. Those facts motivate the authority
work; they are not fabricated successful audits. The original cache timeline
is evidence about the original program only. It does not prove a candidate
entry's survival, a candidate payload's safety or a favorable change to other
request work.

Giving the same-slot design zero induced cache cost is deliberately optimistic
and conditional on preserving original cache behavior. It does not establish
that preservation. A different design that adds entries, promotes a previous
entry, changes retention or displaces useful work needs its own complete
ledger; the sign of its other-work difference cannot be assumed favorable.

The C043 singleton and distinct-signature witnesses remain rejected under
their own unconditional schedule. A duplicate-group predicate can exclude
them from an admitted reuse domain, but it cannot erase the work spent
discovering or rejecting them. Their exclusions do not overturn the current
32-call cost rejection.

This result does not prove that conditional angular reuse is universally
impossible. Selective victim audits, fixed-block checks, previously established
provenance or a different arithmetic algorithm would be different designs.
None receives an implementation approval here. No complete-request cost,
unseen-tail deficit, new recording pass, elapsed improvement or release
acceptance follows from this analysis.

## Supported next investigation

The retained L03 retirement/direct-seed path is a separate, evidenced target.
[HANDOFF-033](../HANDOFF-033.md) identifies key 153 at exact clock `244/89`,
where the prior cursor has 64 updates and the existing predicate requires a
direct seed. The refusal occurs while building series coefficients at
exponent 129 and degree 14. It also retains earlier successful reseeding at
key 66 and the later phase beginning at key 88.

The current source still has the retirement predicate in
`reach_reference_center._orientation` and the existing bounded-cache key
`("series_coefficients", operand_limit, exponent, degree)` in
`reach_reference._Arithmetic._series_coefficients`. This provides a concrete
source/retained-data question: which required direct-seed calculations or
coefficient entries are repeated, and why are their existing entries missing
or ineligible at a later use?

C046 should first bind the relevant current and historical source functions,
recover the retained L03 evidence and audit the actual retirement/direct-seed
and coefficient-cache sequence. It should preserve the 64-update ceiling,
original direct seed, rounding/radii, independent-reader ownership, original
request and all resource limits. Missing current observations should be named
before any separately reviewed neutral capture is scheduled. A final refusal
alone does not establish a global hotspot or a positive saving.

The latest complete original recording gate remains 24/28, and C035 remains
held, including its adverse L03 timing evidence.
