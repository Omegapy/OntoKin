# Repeated independent planar coefficients

Date: 2026-10-24. Status: scoped implementation candidate; its 22-method
focused cohort passes, while integrated and original-recording acceptance
remain pending. The starting development
checkpoint is `571ea01001643da91acf001ff64fec32b83dea30`. This record describes
the candidate in [reach_reference_center.py](../../ontokin/reach_reference_center.py)
and the new [focused tests](../../tests/test_reach_centered_coefficients.py).
It does not replace the identified recording evidence or close a release gate.

## Exact calculation being shared

The [private centered proof](reach-reference-centered-recording.md) projects
an independently obtained quaternion center onto its true rotating plane.
For active scalar components `w` and `s`, it computes

```
d = w*w - s*s
c = 2*(w*s)
x' = d*x - c*y
y' = c*x + d*y
```

The first two coefficients require five exact scalar operations. The source
may attach several nonaxial offsets to the same orientation. Those offsets
previously repeated the same five operations even when their frozen `w` and
`s` were identical. The candidate reuses only the completed exact `d` and `c`.
All vector products, signs, sums, final 128-bit-grid floors, parent-position
additions and uncertainty decisions retain their original formulas.

An approximate center is still not a unit quaternion. Reusing the exact raw
Hamilton coefficients performs no normalization and adds no rounding or
approximation. Consequently the existing center and radius proof applies
without another allowance. An axial offset remains exact under the true
source rotation; zero offsets and exact positive-identity parents retain
their existing earlier exits.

## Source-only admission

Plan preparation associates each nonidentity hinge with its source path and
Cartesian axis. Identity descendants inherit that source association. The
plan marks only groups with at least two offsets having a nonzero component
outside that axis. The marker is a source path in the sealed centered recipe;
it stores no sampled orientation or numerical answer.

A new nonidentity hinge begins a separate group, including when its own
offset is zero or axial. Such a node can execute an independent orientation
seed that populates the existing arithmetic cache. This partition prevents
an admission count from combining two isolated projections separated by
another source seed. Unique groups keep the original five operations without
a coefficient lookup or insertion. Source preparation adds no arithmetic
operation or numerical cache.

Between eligible projections in one group, ordinary node evaluation can
insert only a coefficient entry and a stationary-pose entry per intervening
node. The existing 128-node plan limit is below the existing 256-entry cache
capacity even at two writes per intervening node. Orientation cursor
publication remains deferred until the end of evaluation. Thus normal
evaluation does not evict a fresh coefficient before its admitted second
use. Explicit nested callback work can still evict it; a subsequent lookup
then performs the original calculation and pays its actual miss cost.

The P11 source library has three head attachments, including its brow, and
also independently moving arm branches. The tests exercise that mixed source
selection and a reordered selection that separates two head attachments with
an arm seed. They do not change the adopted recording fixtures.

## Storage, finite operands and identity

The key combines the existing numerical domain, the opaque source-plan
identity and the source path. One value for that source holds the last frozen
`w`, `s`, `d` and `c`, plus an immutable integer-field seal. A changed operand
pair replaces the same entry. There is no per-clock table, pose table,
additional numerical cache or recovery of evicted values. Every insertion
uses the existing 256-entry independent arithmetic LRU and its normal
eviction policy.

Reuse requires native Fraction operands on the existing 128-bit dyadic grid,
component magnitude at most two, and the full existing 32,768-bit operand
domain. The native input predicate permits at most 138 numerator bits and
129 denominator bits. The following conservative prospective bounds cover
all five omitted operations using the unchanged exact-arithmetic rules:

| Calculation | Numerator extent | Denominator extent |
| --- | ---: | ---: |
| `w*w` or `s*s` | 276 bits | 258 bits |
| Difference of those products | 535 bits | 516 bits |
| `w*s` | 276 bits | 258 bits |
| Multiplication of that product by two | 278 bits | 259 bits |

Every bound is below 32,768. The cache hit still validates the exact record
type, native operand fields, bounded result fields and complete seal before
copying the result through the unchanged operand guard. A narrowed initial
domain uses the original five operations, so their first actual prospective
failure retains its original position and exception. A narrowing during a
remaining callback continues to latch the existing optional-domain failure.
No precision, source range or public resource allowance is expanded.

The active guard watches the cache owner, original Fraction leaves and the
hit record's field identities. Detached result copies are used by the
remaining offset operations. A live record or Fraction-field mutation is
therefore rejected at the next checked boundary rather than changing a
completed multiplication silently. Malformed cached records are rejected
before reuse.

## Dispatch, callbacks and publication

Native arithmetic and guard dispatch is an admission premise. Both class
definitions and instance-bound methods are checked, including `_Guard.exact`
and `_Guard.checked`, whose original calls are omitted on a hit. Foreign
class descriptors are detected before invoking them during admission.
Custom dispatch at entry keeps the original formula and its exception
positions.

A lookup or insertion retains its normal charged callback. Admission is
checked immediately afterwards and again after any normal cache-domain
synchronization. A lookup callback that replaces arithmetic or guard methods
therefore returns to the five original operations on the same work context;
it cannot receive a warm value or invoke a newly installed synchronizer as
part of optional cache maintenance. During a miss, every completed original
operation checks the native premise. A departure stays latched even if a
later callback restores native dispatch. Such results are not published as
native coefficient receipts. Cancellation and original resource exceptions
are not translated.

These entries are completed pure arithmetic results. They contain neither
source poses nor deferred source-admission decisions. Like existing exact
arithmetic memoization, they do not enter the source-batch cursor ledger.
The existing pending body-cursor publication, nested-writer checks and
source-batch rejection still operate unchanged. On source rejection, owned
stationary and orientation cursors are discarded; retained exact
coefficients cannot supply a new source pose, bypass fresh source-plan
admission, or substitute for an independent orientation calculation. The
tests verify rejection followed by a fresh source batch after a source
translation change.

## Cost and verification obligations

The local operation model predicts seven operations for an eligible miss
(lookup, five original operations, insertion) and one for a hit. Two actual
uses therefore cost eight operations instead of ten, before the unchanged
offset work. The focused execution verifies these local costs and the
complete costs below, including source-plan setup, source-batch admission,
cache pressure and evictions. The 100,000-operation limit and both existing
cache limits remain unchanged.

The focused cohort covers full Hamilton comparisons on all three axes,
signed and boundary operands, first-use costs, operand replacement, actual
LRU eviction, narrowed prospective guards, native dispatch departures,
cancellation at every executed cold/warm offset boundary, malformed/live
receipt mutation, mixed source selection and source-batch rollback. It also
compares complete P11 centered evaluations under empty, partially churned and
fully churned independent caches. Original P09/P11/L03 quarter-second exports
must keep identical GLB bytes and complete validation results, with positive
measured P11 work savings and no extra work on the singleton controls.

### Identified focused execution

The first candidate attempt, `coefficients-focused-001`, passed **22/22**
methods with zero failures, errors or skips on implementation
`c13db8e8e5368ebaba361acc2fa9ac67a908eab3`, tree
`444f40736aa0928203cfd309016ad495cac1475f`. The exclusive run used CPython
3.12.14 on Linux x86-64, starting at `2026-10-24T00:45:23.385515+00:00` and
finishing at `2026-10-24T00:45:32.304709+00:00`. The launch exited zero after
8.919 seconds; the actual test runner reported 5.878 seconds. Complete tracked
input inventories matched before and after the run. The complete 5,489-byte
test log has SHA-256
`97f532fc7ecd9ab20612e53e32ddc3e6a6fad7607b0b838ad59646eb89bdc057`.

The unchanged `reach_development_probe_v2.py` driver, SHA-256
`052518bda650883f83f24dd34bc1bda9144c27ee3ad6900f72242ca74f10ddf6`, executed
`--test test_reach_centered_coefficients` against that clean checkout. Raw
reports, before/after inventories, complete test log, launcher receipt and
stdout/stderr are retained under
`evidence025/coefficients/coefficients-focused-001` and its sibling launch
files for the coordinator's next evidence checkpoint. No other candidate
test cohort or recording suite was executed in this window.

| Executed comparison | Original operations | Shared operations | Saved |
| --- | ---: | ---: | ---: |
| P11, eight complete mixed-source evaluations, no cache churn | 4,804 | 4,756 | 48 |
| P11, same evaluations, initially full LRU and 32 writes per later key | 5,543 | 5,495 | 48 |
| P11, same evaluations, 256 LRU writes before every key | 11,665 | 11,617 | 48 |
| Original P11 quarter-second export prefix | 60,182 | 60,140 | 42 |
| Original P09 quarter-second export prefix | 35,619 | 35,619 | 0 |
| Original L03 quarter-second export prefix | 31,498 | 31,498 | 0 |

The original controls disable only coefficient admission and execute the
original five operations. Both modes retain the same source preparation and
ordinary arithmetic. Every complete P11 pose map, including centers and
radii, matched under all three cache-pressure conditions. Each of the three
export-prefix comparisons retained identical GLB bytes and complete
validation results. The prefix settings remain the established test helper's
end `1/4`, four frames per second and helpers disabled; these are explicit
prefix checks, not replacements for the full adopted recordings.

This evidence establishes a small positive measured saving in the exercised
P11 paths. It does not establish a full-recording saving, a wall-clock speedup,
or acceptance of any previously failing recording. Integrated focused tests
and all original 28 recordings remain mandatory. Source-suite success alone
would still leave the Agent, complete regression, full Python 3.11/3.12/3.13
compatibility, independent, browser/visual and R01–R12/Q01–Q22 release
obligations open.
