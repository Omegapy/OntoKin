# Adjacent independent clock operands

This bounded candidate starts from checkpoint 023 at
`571ea01001643da91acf001ff64fec32b83dea30`, tree
`78e95fd5900112d9d763cd7a6a676e21416dc109`, on
`work/reach06-adjacent-clock-20261023-1bda`. It changes only interval clock setup
inside the independent supplied-byte certificate reader, its dedicated tests,
and this derivation. The source fixtures, horizons, sampling, tolerances,
100,000-operation request allowance, 32,768-bit operand maximum and all cache
capacities remain unchanged. Checkpoint 023 records 23/28 original recordings;
P09, P11, P16, P23 and L03 remain failed gates until their own new execution.

## Repeated calculation

For adjacent retained keys, interval `i` ends at the exact same authored clock
and stored binary32 value where interval `i+1` begins. The original independent
reader decodes both stored floats and calculates both signed endpoint shifts
again for each interval. Its preceding interval has already completed the next
left stored-clock decode and the exact difference between that stored value
and its authored clock.

The helper retains only these two completed native operands for one endpoint.
It does not keep another request cache, an array of shifts, certificate minima,
or previously accepted claims. The original source and stored widths, new right
decode, new right difference, and ordinary absolute values and maximum remain.
The original cold interval still performs six charged operations. An eligible
later interval may omit one decode and one exact subtraction, performing four.
These are eliminated calculations, not changes to any work charge.

## Provenance and local finite-domain proof

The receipt identifies the exact preceding interval index, authored Fraction
object and copied native integer fields, typed raw binary64 bits, stored ratio
and its fields, and completed signed difference and its fields. Matching raw
bits distinguishes signed zero. The arithmetic object and original work and
external-callback owners must still agree. Only immediately adjacent indices
within the existing key bound can use the receipt.

At each actual omission point, the helper requires the original native
`_Bounds.value/sub/op/bits/tick`, module `_tick`, and work `charge/guard_bits`
dispatch. The work must have the exact native integer 32,768-bit domain. A
finite native binary64 decode has at most 1,024 numerator bits and 1,075
denominator bits. The authored clock is admitted only with native numerator
and denominator fields of at most 2,048 bits.

The original subtraction checks its input fields, both prospective cross
products, their sum, the denominator product, and the reduced result. With
these input bounds, its largest prospective numerator size is at most
`max(2048+1075, 1024+2048)+1 = 3124` bits. Its denominator product uses at most
3,123 bits. The helper executes the original native, callback-free width guards
for these actual saved fields before the omission. Every such guard fits the
unchanged full domain. Wider, nonnative, nonfinite, custom-dispatch and narrower
inputs take the original operations at their original positions.

No result is reconstructed from copied fields. The stored value and signed
difference are the actual completed native results. The ordinary `abs()` still
runs before the next callback and supplies this interval's fresh absolute
shift, so a returned maximum does not expose the borrowed signed result.

## Callback and fallback ordering

The first operation sequence remains stored-left decode, stored-right decode,
authored width, stored width, left difference/absolute value, and right
difference/absolute value. Later eligible intervals omit only the two proved
operations in that sequence. No callback or observer is replaced or added.

A stale receipt before entry declines reuse and runs the original calculation.
After a stored ratio has actually been borrowed, every surviving operation
returns through a callback-free field and owner check. A changed borrowed
ratio or owner is an explicit independent-validation failure. An exception
from the original operation, cancellation callback or resource guard escapes
unchanged before that check. A changed prior signed difference before its
actual reuse point takes the original left subtraction instead.

The helper does not eagerly guard a borrowed ratio under a temporarily smaller
domain. The original arithmetic can narrow and later broaden the domain across
different callbacks; its exact prospective guards must retain their order.
The optional proof checks the domain only where an operation would be omitted.
If that domain is narrower, the original operation and its own callback execute
there. Receipt capture is conservatively disabled when a surviving callback
changes the admitted domain, native dispatch, or relevant source/result fields.
It cannot turn a tainted new result into the following interval's proof.

The current receipt is removed before a new interval starts. Failed partial
execution publishes no new receipt. A generation check prevents an outer
reentrant call from overwriting a nested completed receipt. Each complete
certificate replay creates a fresh helper on the same remaining work; it does
not import receipt state from an abandoned attempt or reset the allowance.

## Required execution

The dedicated cohort covers exact cold/warm results, non-dyadic and extreme
native operands, signed zero, nonadjacent and replaced source identities,
mutated completed fields, narrower/custom paths, original diagnostic and
callback order, callback exceptions, work/callback/dispatch replacement,
temporary domain narrowing and restoration, original prospective failures,
reentrancy, fresh replay state, observer ownership and unchanged resource caps.
Original quarter-second P09, P11 and L03 prefixes compare complete GLB bytes and
entire reports, including cold setup and every real callback, and require a
strict positive saving in their actual shared operation counts.

The initial code/test preparation was unexecuted. The executed worker handoff
below identifies the later dedicated result. Related callback and certificate
cohorts, integration review and the complete original 28-recording suite remain
required for the integrated source. The maximum
gross opportunity is two operations per eligible interval after the first;
there is no prediction that this alone resolves an original failure. P23 fails
in the producer before reaching this independent reader and cannot benefit
from this candidate. All release, compatibility, Agent, destination, visual,
R01–R12/Q01–Q22 and full-product gates retain their existing status.

## Executed worker handoff

The coordinator independently reviewed the production implementation and all
dedicated tests before granting an exclusive execution window. The exact
executed commit is `c3408060c3b1fa78060be20b3cf1250c63569521`, tree
`2890f6d534e0271dcc696ad09be0859022986b14`. The checkout was clean and all
tracked input bytes were stable before and after execution. No tracked
historical archives were omitted. This input check does not certify the full
release input-closure role or retroactively recover any unavailable older run.

Run `clock/adjacent-focused-001` passed **26/26 dedicated methods**, with zero
failures, errors or skips and a complete test log. Actual execution used
CPython **3.12.14** on Linux from **2026-10-24T00:27:49.242278+00:00** through
**2026-10-24T00:27:56.528344+00:00**. The unchanged development driver has
SHA-256 `052518bda650883f83f24dd34bc1bda9144c27ee3ad6900f72242ca74f10ddf6`.
The launch command selects only `--test test_reach_adjacent_clock_operands`
from the identified clean worktree; the raw launch receipt retains its exact
interpreter, command and working directory.

All three original quarter-second source prefixes preserve **complete GLB
bytes and entire export reports**. The comparison disables only this helper's
optional reuse for the control and includes the cold interval, receipt setup,
every actual callback, and the complete production and independent reader:

| Original prefix | Ordinary operations | Reuse operations | Operations saved |
| --- | ---: | ---: | ---: |
| P09 | 35,619 | 35,569 | 50 |
| P11 | 60,182 | 60,170 | 12 |
| L03 | 31,498 | 31,478 | 20 |

The dedicated controls also pass for callback-time mutation of both retained
operands, narrow-then-widen domains, original prospective guard/cancellation
ordering, changed owner/external callback/dispatch, reentrancy, observer
ownership and signed zero. No failed attempt or test repair preceded this
result.

The raw handoff is under `evidence024/clock/adjacent-focused-001/`, together
with sibling `adjacent-focused-001.stdout.txt`, `.stderr.txt` and `.launch.json`
files. It contains the exact executed driver, input snapshots, structured test
results, full text log and execution report. Report SHA-256 is
`2f629e6c463494497aef275655c5addd0358405e5018dfeb657283641e151687`;
`tests.log` SHA-256 is
`66abd4800fcd98d798815247662379831f5881e17b56406ec9091d83031909da`.
The coordinator owns durable archive publication and will bind those paths
to the next checkpoint's verified member manifest.

This handoff changes documentation only after the executed cut. Production and
tests remain identical. No related cohort or full original recording suite ran
in this worker checkout. The coordinator must publish the reviewed integration,
then run the established 18-module related cohort with the new adjacent-clock
and independent-clock-cell modules and all original 28 recordings on that exact
source. The prefix savings are not full-recording passes; both PRs remain draft,
main remains unchanged, and every unexecuted acceptance role remains open.
