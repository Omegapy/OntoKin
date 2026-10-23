# Captured native forward translations

This isolated continuation starts from published implementation
`5224a84eb87f288b364f1dd9592a0fb088090e0c` (tree
`74ecd86efaa01f6d120039623f7c2cf32c49a6f3`). The candidate has passed its focused
and related tests but remains **unintegrated**; the unchanged original P16
recording still exhausts its operation budget. Its scope is the captured source
graph, one private native placement helper, and dedicated tests. It changes no source fixture, sample
clock, error allowance, independent reader, operation maximum, operand
maximum, cache capacity or numerical cache key.

## Repeated work being removed

For an ordinary captured site or follow, the existing builder constructs a
native local pose, then composes it with the freshly evaluated parent. A
literal binary64 translation with quaternion `(1, 0, 0, 0)` already takes the
existing direct source-leaf path. That path canonicalizes positional zeros and
constructs the identity quaternion without a numerical projection. The later
quaternion product also returns one of its operands without arithmetic.

The new private helper admits precisely that source shape and performs the
remaining translation calculation directly. It retains one actual native
domain checkpoint, the existing `_rotated_offset` calculation, and every
required world-component addition. It removes the two other generic domain
entries whose local-pose/product work is no longer executed. It does not
remove charges from operations that still execute.

The neutral P16 source analysis found 716 such forward placements before the
current reader cutoff, initially predicting a saving of 1,432 operations.
The subsequent unchanged original P16 run confirms exactly 1,432 fewer native
domain entries with unchanged native multiplication, subtraction and addition
counts. This is a measured reduction in producer work, not a recording pass.
The dedicated complete-prefix and phase comparisons also pass their positive
measured-saving gates, as recorded below.

## Exact native calculation

For each native local component, both paths use the same finite binary64
value. Both signs of literal zero become positive zero, exactly as in
`_direct_identity_source_leaf`. No rational, integer, float subclass,
nonidentity quaternion or nonzero inverse translation is admitted by this
new path.

For a nonzero local translation, the original parent identity shortcut stays
in place. Otherwise the existing `_rotated_offset` method executes unchanged:
the same Cartesian permutation, coefficient products and subtraction, unit
component shortcuts, sign handling, remaining component products and sums.
Each world component uses the same ordered expression: the offset when the
parent component is structurally zero, the parent component when the offset
is structurally zero, or the original native addition. The zero flags and
final canonical-zero selection are unchanged. No offset is combined with
another source placement, and no rounded world position is subtracted.

The original quaternion product tests its left identity before its right
identity. Consequently an exact identity parent, including one with X/Y axis
metadata, returns the canonical right identity with Z axis metadata. The new
helper preserves this case explicitly. Every other admitted parent retains
its original quaternion and flags. The resulting depth is the original
parent depth plus one, bounded by the unchanged 64-composition ceiling.

## Source and finite admission

The captured graph now detaches every native site/follow Pose before a parent
or cursor callback. Eligible and nonidentity leaves are both copied, so a
temporary live-source change cannot promote a previously ineligible local
rotation. These copies contain only immutable native source values and do
not store a computed pose.

At each placement the optional helper requires a complete native source
record of kind `site` or `follow`. Its typed literal position and rotation
must match the copied local values, including all original binary64 zero
signs. The existing complete graph publication still admits the actual live
model/state/proof, all source records and owners, active grips and otherwise
unused global edges after the output callbacks.

The native parent must have three finite binary64 position components bounded
by `2^500`, three boolean structural-zero flags, a native Cartesian rotation
inside its existing component bound, and an integer depth from zero through
63. The local position has the same `2^500` bound. The full 32,768-bit operand
domain proves every omitted finite-float decode guard, whose maximum width is
1,075 bits. Every remaining native intermediate retains its original finite
check. Unsupported shapes or an initially narrowed domain return to the
ordinary builder before any optional arithmetic runs.

The broad shared-arithmetic path remains ordinary. This preserves its
existing local-result LRU behavior and avoids adding two probes for a
one-off small-graph placement. The new helper itself neither reads nor writes
the numeric cache. Existing cache contents and the 256-entry maximum are
tested directly.

## Callback and owner boundaries

Before the first callback, the helper takes native field snapshots of the
actual parent, local leaf and source witness. Rotation arithmetic uses a
detached private rotation wrapper; all remaining numerical leaves are
immutable floats. Live parent and source owners still have to match those
snapshots before return.

The helper scopes the already existing work post-charge observer around its
remaining operations. It does not replace the external callback or add a
work operation. After each original callback and the original resource
checks, the observer verifies the same arithmetic/work owners, source/parent
receipts, cap, native helper dispatch and Cartesian selectors. A temporary
departure cannot wait for a later callback to restore admission. An occupied
observer causes initial ordinary fallback; cleanup removes only the helper's
own observer and preserves a foreign replacement.

Actual original callback and resource failures escape without translation.
The bounded-phase boundary captures its original work owner before entering
the sampler, so replacing `ops.work` while raising the private unsupported
exception cannot disguise a callback refusal as optional phase fallback.
It also retains the existing current-work check for an actual later callback
on a replacement native work object, without reading callback fields from an
arbitrary foreign replacement. The initial unexecuted review cut
`cb5ac0796a419660839448484cfb9822a48bcc15` checked only the entry work;
read-only review found that this could translate the later original callback
case. Its separate correction adds the native-current-work disjunction and
an actual P16 phase regression. The numerical helper and positive-saving
gates are unchanged. The initial cut remains unexecuted; only its corrected
child identified below was executed.
An ordinary optional decline retains the existing complete same-work phase
replay behavior. No private cursor is published before the unchanged final
source receipt.

## Required evidence and limits

The dedicated methods cover native bits, flags and depth on all Cartesian
axes, signed zeros, subnormal and large finite translations; exact remaining
operation sequence; literal and foreign source boundaries; initial dispatch,
cap and occupied-observer fallback; warm source/parent/owner/dispatch changes;
cap narrowing with attempted later restoration; original exception identity;
unchanged actual numeric cache contents; and final live source admission.

Actual P16 pre-release and released-phase samples must keep all native bits
and endpoint allowances while reducing work. A complete unmodified P16
prefix must produce identical GLB bytes and the complete same independent
validation report, with a positive operation saving. Those are focused gates,
not substitutes for the complete original P16 recording or all 28 original
recordings on the eventual integrated source.

## Executed branch evidence, October 23, 2026

All three executions used the clean corrected commit
`18fb795762755d16c60753fc45aeb9d7e009c4f8`, tree
`e375a91efa9f22cfca7227438228cc82ae3ff1d5`, with CPython 3.12.14 and the
preserved development driver SHA-256
`052518bda650883f83f24dd34bc1bda9144c27ee3ad6900f72242ca74f10ddf6`.
Each run has identical before/after tracked input receipts, its exact command,
environment and complete raw result. Evidence directories are outside the
checkout and are supplied to the coordinator for the next archive checkpoint.
The existing explicit historical-archive omissions remain disclosed; these
runs do not establish the release input-closure role.

| Evidence directory under `evidence/` | Observed result |
| --- | --- |
| `forward-translations-focused-001` | 19/19 methods pass; no failures, errors or skips; complete log |
| `forward-translations-combined-001` | 263/263 methods pass; no failures, errors or skips; complete log |
| `forward-translations-original-p16-001` | Original P16 fails with `OKL-E-RESOURCE`, limit 100,000 and consumed 100,001 |

The focused tests compare every native pose bit and endpoint allowance for
15 actual P16 samples in each of two phases. Work falls from 3,990 to 3,840
in phase 0..2 and from 3,576 to 3,456 in phase 2..3. The complete original
P16 prefix through 0.25 seconds produces identical GLB bytes and the same
complete independent validation report; its work falls from 44,677 to 44,547.
The numeric cache test preserves all 256 original keys and value identities.

The full original P16 run retains its original source identity, end time 4,
fps 1, helpers disabled and all original error tolerances. Against the
identified parent run `full-certificate-threshold-integrated-001`, native
domain entries fall from 4,879 to 3,447. Native multiplication, subtraction
and addition remain exactly 6,329, 1,420 and 2,075 respectively; both runs
retain 206 recording samples and 1,435 certificates. The independent retained
clock counter advances from 76 to 166 before the cap. The current failure is
a rational-clock cache eviction inside `verify_retained_clocks`; it still
occurs before independent key-pose comparison. No completed full P16 artifact
or acceptance advance is claimed.

The focused log SHA-256 is
`a3928587de618cf7a3e3f180d54e0afc1120b1cc0bd7cf19fe119e11be46e6d7`;
the related-cohort log SHA-256 is
`c8dd864202b97dcd09f02fc71c7d9633141507ba57a45483a6d8e44510f49014`.
The full P16 request-result SHA-256 is
`c80708124bb63fddf718fb6bd6a5a63ac3aa1062fb333a2528e94e3fa69aa534`.

This result record is a documentation-only child of the tested cut. Runtime
ownership was explicitly released after the full P16 attempt. The coordinator
must review integration onto the current continuation, execute the relevant
cohort and all unchanged 28 originals there, and preserve these raw attempts
before drawing an integrated-source conclusion.

## Continuation integration

The coordinator independently reviewed the source diff and preserved the
tested runtime/test bytes from `18fb7957`, together with the documentation-only
handoff `6b4fd9ab`. This integration follows checkpoint 022 and the prescribed
reference partition. It changes only the four declared files, with no fixture,
workflow, source horizon, tolerance or numeric/cache maximum changes. The
related cohort and all original 28 recordings must execute on the published
integration before any integrated result is claimed. Worker results and the
original full P16 failure retain their own exact source identities.
