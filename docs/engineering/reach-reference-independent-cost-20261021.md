# Independent reference continuation, October 21, 2026

## Scope and source

Worker: `reference_cost_review`, coordinated by
`interactive-reach06-resume-20261021-2045-astra`.
Isolated branch: `work/reach06-independent-cost-20261021-2055`.
Starting integrated source: `79fb7b1`.

The previous private worker checkout and all its evidence remain unchanged.
Pending live-domain correction `d80a6dddd2a5933fc58abad7466765e3fe200800`
is cherry-picked as `7f80304`. Subsequent changes are:

| Commit | Scope |
| --- | --- |
| `a2a3474` | Recheck independent interval/pose shortcut operands after callbacks. |
| `6c639e0` | Guard native integer lane extraction and quadrant rounding after callbacks. |
| `bece5f3` | Reuse complete exact numerical coordinate-phase laws, with fresh occurrence identities. |

The implementation and all 16 added test methods have received independent
static review by the separate `planar_arithmetic_review` worker. No blocking
issue was found in that final static review. AST parsing and whitespace checks
pass. **No runtime, source request, test, profile or archive execution has run
for these changes at this checkpoint.** The coordinator reserves the exclusive
execution window. This record establishes no passed release role.

## Live-domain corrections

The inherited correction admits a work object's narrower operand cap and
invalidates numerical reuse when that cap changes. Several exact zero/identity
shortcuts checked their operands before their charged callback, then inspected
or returned them after it. A callback could narrow the cap between those steps.
The new uncharged checks admit the complete relevant endpoints immediately
after that existing callback, before shortcut evaluation. Public binary64
conversion likewise rechecks both endpoints. A radical rechecks its endpoint
denominators as well as the preallocated grid before its native allocation.

The packed independent series now performs lane extraction through the same
single charged guarded integer primitive, with `divmod` as its operation.
The quadrant operation retains its existing single charged checkpoint and
checks the quotient plus the prospective doubled numerator and division
remainder before native rounding. No charged operation is removed or added
on the unchanged-domain paths.

Review initially questioned returning a proof after the insertion callback
changes the cap. The prior explicit test contract permits an already completed
numerical proof to return; it prevents its reuse in the narrower domain by
retaining the original cap in the key and clearing prior cached results.
Review reconciled that distinction and withdrew publication alone as a
blocker. This continuation preserves that contract. An actual numerical
allocation after a callback must still satisfy its current domain.

The nine new callback tests exercise scalar and vector shortcuts, scalar
quaternion normalization, radical denominators, public conversion, native lane
division, quadrant allocation, valid smaller-domain results, and unchanged
cancellation exception identity. Their execution remains pending.

## Exact coordinate-phase law reuse

`_joint_path` repeatedly reconstructs the same exact scalar expressions for
carrier ancestries and independently derived uniform bounds. Translated cloned
arms can have the same numerical law while retaining distinct joint/action
identities. Its new bounded reuse key contains:

- effective operand cap;
- actual initial coordinate, canonical target and continuous ideal initial;
- duration, or explicit absence for an unclaimed coordinate;
- both actual elapsed endpoint values;
- claimed/unclaimed and running/nonrunning distinctions.

These values completely determine the unchanged exact expressions for actual
and ideal slopes, both actual and ideal endpoint coordinates, and the source
coordinate error. Every current scalar is guarded before lookup. A miss
executes the original rational expressions, and only the completed immutable
numerical tuple is retained. A hit constructs a new frozen `CoordinatePath`
with the current joint and action identities. No source state, action record,
clock object or numerical allowance supplied by production is stored.

The result uses the existing 256-entry independent pure cache. A changed cap
cannot obtain a proof under the earlier domain. All callbacks and actual
arithmetic retain their charges. The 100,000-operation ceiling, 32,768-bit
maximum, cache capacity, recorded tolerances and frozen source inputs remain
unchanged. The independent implementation imports no production solver,
sampler, planner or certificate generator.

Seven new methods compare every field against the previous exact expression,
check fresh occurrence identity, change every key operand, exercise lower
domains and cancellation, fill and evict the bounded cache, and compare actual
source phase records for P01, P13, L02 and P16. The source comparisons also
measure whether the new path uses less actual shared work; no saving is
claimed before those tests execute.

## Next execution

Run the two new test modules with the existing reference operand-cap, reuse,
extrema, integer-series, coordinate-law, source-reference and derivation
cohorts in an exclusive window, recording a clean commit and stable input
hashes. Retain any failed first attempt. Then repeat selected complete source
recordings and the complete 28-artifact gate on the reviewed integrated cut.

Earlier profile `ontokin-reader-profile-004` belongs to `99febf1`, not this
candidate. It reports 38,831 independent-reader operations for the passing
P01 recording and partial costs of 42,600 for failing P07 and 48,557 for failing
P13. Those observations motivate the work; they are neither new measurements
nor acceptance of the changed implementation. Main integration and the full
product goal remain open.
