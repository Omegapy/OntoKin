# Local sufficient centered endpoint claim comparisons

This candidate starts from source `21c1368176117076f0bfebeb33fec9fd7f0d5f66`,
tree `58956f83039632a2f19f67a137930032128a7adf`, on branch
`work/reach06-centered-claim-thresholds-20261023-3be6`. The first committed
production cut was explicitly unexecuted. The later execution record below
identifies the tested candidate, which is **not yet integrated** at this worker
handoff. It changes only the local
comparison of a fresh independent centered endpoint bound with its actual
supplied claim. The original recording inputs, tolerances, 100,000-operation
allowance and all operand/cache limits remain unchanged.

## Independent result and actual claim

The centered reader still evaluates the independent source center and honest
radius, admits the complete actual stored vector, derives every fresh L1
distance, includes its radius and forms the factor-two quaternion bound.
Position magnitude is still evaluated or reused under its existing exact
receipt. The separate quaternion bound of one half is still checked whenever
the actual claim does not itself establish that range. The returned numerical
proof fields are unchanged.

Previously each fresh local claim comparison decoded the actual raw quantity
to a fraction and compared it with that independent result. The optional
helper can omit those two operations only when a strict sufficient inequality
already proves the same result from admitted native field metadata. The claim
is a threshold; it is not an independently derived error or a source truth.

The helper holds no result cache or per-row history. Its result is used
immediately. Unlike the separate certificate-group optimization, it does not
discard a possible running maximum or alter a later comparison operand.
There is no continuation-width envelope or new reader replay.

## Exact bit-exponent proof

Let the newly calculated nonnegative bound be the native fraction `m=n/d`,
where `d>0`. For positive `n`, write `B=bit_length(n)` and `D=bit_length(d)`.
The defining integer inequalities imply

\[
  0 < m < 2^{B-D+1}.
\]

The actual claim must be a native finite positive binary64 value. Its packed
encoding has exponent field `E` and fraction field `M`. If `E>0`, its exact
value is at least `2^(E-1023)`. For a positive subnormal, `E=0`, `M>0`, and
the exact value is `M*2^-1074`, which is at least
`2^(bit_length(M)-1075)`. Let `e` denote that lower exponent.

Thus `B-D+1 <= e` proves `m < claim`. An admitted zero numerator also proves
the strict inequality because the claim is positive. The proof constructs no
power, rational float decode, product, subtraction or normalization. Exact
equality and any insufficient exponent gap retain the original comparison.
Both normal and subnormal encodings are covered, including their transition.

The fraction must have native integer fields of at most 2,048 bits and a
positive denominator. Every finite binary64 reduced ratio has at most 1,024
numerator bits and 1,075 denominator bits. Consequently the original claim
decode, both scalar admissions and both prospective comparison cross products
fit within 3,123 bits. The helper admits that complete bound through the
original native arithmetic guards before omitting either operation. It is
available only at the exact native integer 32,768-bit limit; narrower and
unsupported domains retain the existing path. No finite limit is enlarged.

## Callbacks, dispatch and source receipts

At the actual omission point, after all preceding surviving callbacks, the
helper requires the original native arithmetic `compare`, `value`, `bits`
and `tick` methods, the original module tick dispatcher, and the original work
`charge` and `guard_bits` methods. It uses their existing frozen identities.
Initial custom dispatch or a dispatch replaced by a preceding callback declines
the optional proof. The existing local decode and comparison then execute,
preserving their callback and exception identities. No callback is replaced.

The complete centered proof's live source, radius, owner and external-callback
receipts are checked before and after a successful sufficient comparison.
Every surviving arithmetic callback retains its existing immediate receipt
check and latched cap departure. The helper snapshots native numerator and
denominator fields and operates only on those integers. Its admitted guards
have no callbacks; it checks the live fields again afterward. It neither
recaptures a changed source nor boxes a center without its radius.

Zero, negative, nonfinite, Boolean, integer, Fraction or foreign claims keep
the original path, as do wider or nonnative fractions and tight inequalities.
An ordinary exact comparison may still establish a tight centered claim. If
that complete centered proof is insufficient, its existing caller obtains
ordinary independent enclosures on the same remaining work. Source-batch
admission and supplied-byte certificate validation remain unchanged.

## Required execution and limits of the estimate

Dedicated tests must cover positive normal/subnormal boundaries, the largest
finite encoding, exact equality and strict exponent boundaries, zero and
non-dyadic independent results, 2,048/2,049-bit fields, malformed native fields,
unsupported claims, narrow caps and complete prospective comparison failures.
They must also exercise dispatch replaced at a preceding surviving callback,
original callback exception identity, live source/radius/owner rejection,
the independent quaternion one-half guard, exact fallback and actual source
prefix byte/report differentials for P09, P11 and L03.

The accepted coarse observer on source `5224a84e` contains no scalar claim
values. Its completed centered-call and reuse counts bound the number of
fresh comparisons already reached before the cap: P09 has at most 956, P11
227 and L03 682. Even universal activation there would omit at most
1,912/454/1,364 operations, respectively. These are ceilings for those reached
regions, not measured savings or a complete-recording cost estimate. The newer
`21c13681` full original run has identical application counters, while its
separate neutral stage observer identifies the earlier producer/reader costs.

The writer forms quaternion claims with four times grouped conversion maxima
plus source/normalization allowances; the independent reader forms twice the
actual fresh L1 plus radius. That source-code distinction suggests useful
slack, but it is neither a premise of the proof nor evidence of activation in
an actual recording. Position claims may be tight. Actual activation, exact
operation changes, focused correctness and the complete original suite remain
unmeasured at the preparation checkpoint. All five original failures and every
remaining release gate stay open until their own identified executions pass.

## Executed worker handoff

Production and its derivation were independently reviewed at
`d4e5c9f8f26b7c1f7e0d00c65b72b08998fd0b05`. The dedicated test commit and all
executed source bytes are
`118ee1f11199f195146239d67db99664aa4ce378`, tree
`0c511ea308bf283d0532b61aa5e93c1a225a1a2e`. The working tree was clean before
and after each run, and every materialized tracked input retained its exact
hash. The existing 37 unmaterialized historical binary archives remain
explicitly disclosed by the development driver; this is not release input
closure.

Execution used CPython 3.12.14 on Linux with the canonical sparse development
driver SHA-256
`052518bda650883f83f24dd34bc1bda9144c27ee3ad6900f72242ca74f10ddf6`.
The driver, exact commands, input snapshots, complete logs and structured
results are retained in these separate raw evidence directories:

| Raw run | Actual result |
| --- | --- |
| `centered-claim-thresholds-focused-001` | 24/24 dedicated methods passed, no failures, errors or skips; complete log and stable inputs. |
| `centered-claim-thresholds-combined-001` | 249/249 related methods passed, no failures, errors or skips; complete log and stable inputs. |
| `centered-claim-thresholds-originals-001` | Original P09, P11 and L03 each failed at the unchanged 100,000-operation cap, recorded as the rejected attempt 100,001; complete raw failures and stable inputs. |

The combined cohort contains the same 15 modules and 206 methods as the prior
integrated certificate cohort, the 24 new local-claim methods and the current
19 independent partition methods. It retains the actual forged-byte endpoint
tests, source-batch admission, source/release bounds, ordinary interval fallback,
certificate continuation checks and callback/resource tests. No test selection
or source correction was required after execution began.

The quarter-second source-prefix differentials disable only the new local
helper for their exact control. They retain identical complete GLB bytes and
independent validation reports:

| Original source prefix | Exact local comparisons | Sufficient local comparisons | Operations saved |
| --- | ---: | ---: | ---: |
| P09 | 35,959 | 35,723 | 236 |
| P11 | 60,290 | 60,232 | 58 |
| L03 | 31,642 | 31,542 | 100 |

These are measured prefix savings, not complete-recording operation deltas.
The full worker recordings remain failures. Compared with the fresh original
run at the exact parent `21c13681`, their work reaches further:

| Original recording | Parent key/carrier inspections | Candidate inspections | Parent certificate-member visits | Candidate visits | Completed candidate key maps |
| --- | ---: | ---: | ---: | ---: | ---: |
| P09 | 1,158 | 1,212 | 1,146 | 1,200 | 201/205 |
| P11 | 680 | 700 | 640 | 660 | 34/52 |
| L03 | 830 | 876 | 822 | 864 | 145/178 |

The unchanged geometry has 6, 20 and 6 carriers, respectively. The candidate
tracebacks fail during the following key's independent centered source
evaluation, after the prior key map and interval loop returned. Those traces
and counters establish the completed-map figures, up from 192, 33 and 138 on
the parent. The counters themselves are charged inspections, and pending group
flush and final source admission prevent a certificate acceptance claim. The
recordings did not fail at an elapsed cap, and no allowance was reset or raised.

The coordinator's later continuation includes separately reviewed producer
forward-translation work that is absent from this worker parent. Its effects
must be measured on the actual integration; they cannot be added to these
partial counts. Current-source related checks and the complete original
28-recording suite remain the integration handoff. No PR merge, full regression,
Python compatibility, Agent, native, browser, visual or R/Q release gate is
closed by this worker checkpoint.

## Continuation integration

The coordinator independently reviewed the source and dedicated tests and
preserved the production/test bytes from executed `118ee1f1`, together with
documentation-only handoff `d0cbb795`. This integration follows the published
forward-translation integration `d5965a7b`. It changes only the three declared
files, without fixture, horizon, tolerance, operation-limit or numeric/cache
maximum changes. A fresh 268-method related cohort and all original 28
recordings must execute on the published integration before any combined
result is claimed. The worker's three original failures and its source
identity remain separately preserved.
