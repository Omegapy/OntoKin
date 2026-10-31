# Independent C082 decision and input review

**Reviewer:** `c082_design_review`, assigned separately from runtime and
Agent/destination implementation workers.  
**Date:** October 31, 2026.  
**Disposition:** Accept the exact reviewed decision and independently authored
inputs for experimental implementation after publication of this freeze.
Runtime, destination, integration and complete release results remain later
gates.

## Exact decision

The reviewed decision is `OK-DEC-KEYED-REDUCTION/0.1.0`.
`ADOPTION.md` has SHA256
`7531d6ef1c8036f9ea0a5911b02785a56ba2c55e6f9d580917dcd68751bf51f9`.
The grammar has SHA256
`2e8b22c838660c2b26ce775f705ff0a649e0875d396d18fc26ddaef6124781ca`.

I reviewed the complete exact decision and grammar, C081's current adoption
and implementation structure, and the proposed examples. The decision fixes
the explicit accumulator type, inherited typed input, three body-only binders,
input admission before seed evaluation, a single evaluation of both, and
sequential ASCII traversal. Every intermediate value receives the inherited
type, dimension, frame, domain and resource checks. Empty inputs return the
typed seed after static body checking. No arithmetic associativity is assumed.

The static rule masks known local payloads while retaining type/frame metadata.
It neither invents a sample value nor dynamically executes an empty body.
The concrete accumulator retains its actual frame at every step. The decision
keeps all 24 inherited immutable leaf families and their bounds, with no new
conversion or reference authority. Source, Agent and recorded destination .15
are separate bindings; older declaring units, user functions and defaults keep
their existing meanings.

The work model includes initial/final copies, per-entry selection, three fresh
bindings, selected body work, next-accumulator copies and provenance work on
the current cumulative ledger. Reduction nodes do not acquire memoization.
Actual cancellation remains observable at the real iteration checkpoint and
must preserve its exception/request identity and atomic failure semantics.

The most significant new implementation obligation is accumulated provenance.
All actual input/seed/body reads remain dependencies even when later iterations
overwrite their values. Forbidden generated-view taints cannot be removed by
empty input, a helper, a cache, a copied wrapper or a constant final body.
Detached `derived_reductions` and `input_reductions` records describe source
derivations and grant no writable identity. Existing map provenance remains
separate. The exact decision resolves these points; no blocking semantic
ambiguity remains in the reviewed text.

## Independent inputs

`examples/keyed-reduction/expected.json` fixes **128 cases**: **62 intended
successes** and **66 intended refusals**. These are requirements, not candidate
execution results. The case inventory covers empty/singleton/256/257 inputs,
key order and reordered literals, all 24 input/seed/result leaf families,
types/units/frames, exact and inexact conversions, nonassociative binary64
arithmetic, intermediate numeric/domain failures, constructor domains, parser
arity, body-only scope, imported helpers/private access/cycles, older declaring
semantics, source/image closure and retained resource bounds.

The nonassociative case calculates `(10000000000000000.0 +
-10000000000000000.0) + 1.0`, yielding 1.0 in the specified order. The maximum
input sums 0 through 255 to 32640. The decimal-order case constructs 12345
through the sorted keys `0`, `A`, `a`, `left.eye`, `z`. Intermediate overflow
and division-by-zero cases remain failures despite later cancelling or
overwriting expressions. All answers follow the prescribed arithmetic,
independently of a C082 implementation.

Each valid probe includes an explicit reduction-provenance requirement and
exact required source-expression locations. A plain qualified call to the
older user function `reduce_keyed` explicitly requires no intrinsic reduction
provenance. Nested input/seed/body and overwritten-derivation examples require
the earlier actual map/reduction expressions to remain present. Dependency
include/exclude records distinguish selected reads from unselected branches.
Locations and source revisions were calculated directly from authored UTF-8
text without importing a candidate parser.

All 62 valid cases have separately authored explicit `.14` controls. Compound
controls use existing immutable constructors; scalar controls use independently
calculated literals or explicit inherited operations. The representative panel
keeps the corrected C081 geometry, materials, PNG, placement and recorded
motion. Its new map-to-reduce-to-map construction computes the same dimensions:
`(0 + 0.25 * scale) + 0.75 * scale`, then multiplies the aggregate by the two
panel coefficients. These fractions and dimensions are exactly representable.
The explicit `.14` library spells out the two terms.

The pinned construction has two independently inspectable occurrences. Repair
changes only `first.scale` from 1 m to 1.5 m. Its aggregate changes from 1 m to
1.5 m, and its panel widths change from 1/2 m to 1.5/3 m. The sibling remains
1/2 m. Expected corners, volume, surface area, UVs, material graphs, identities
and five recorded poses retain independently authored mathematical values.
Library and PNG bytes and unrelated marker motion remain unchanged. The
expected source locations identify the segment map, reduction and width map.

Ten Agent workflow contracts require actual repair, invalid-edit rollback,
stale revision/cursor refusal, durable reopen/retry and changed-payload refusal,
current host authority, caller reductions/output exhaustion, cancellation
during a real reduction, interrupted artifact publication, exact PNG retrieval,
and complete comparison with the separately authored predecessor control.
Independent readers, supplied-byte adversaries and real pinned destination
checks remain mandatory.

## C081 control preflight and preparation history

All control execution used unchanged C081 commit
`838581854b9a7f6a3260cedff6fd00914be544b8`, tree
`705436e470b8aae058bf1a58fd8580eed8ba1cd8`, with a clean source checkout.
No C082 candidate runtime was imported or executed.

The first draft had 114 cases and all 58 explicit controls passed. The second
draft added explicit older-name and overwritten-derivation requirements; all
62 controls passed. Later preparation added parser/flat-input/empty-view/domain
refusals and the deterministic input-before-seed refusal. The final control
preflight again passed all 62 controls. No authoring failure was observed in
these control preflights. Original draft snapshots, generator versions and all
four receipts remain external preparation evidence; no earlier result is
relabeled as execution of the final C082 corpus.

The final preflight checks canonical manifests and exact program revisions,
including final scalar values and represented types. It does not establish
C082 execution, destination support, visual quality, performance, or release
acceptance. The freeze binds its exact receipt and the equality of every
current control revision.

## Remaining obligations

Implement only the frozen contract. Execute focused checks, all frozen source
and actual Agent requirements, independent supplied-byte readers, complete
immediate-predecessor .14 workflows, applicable complete inherited checks and
pinned native/browser validation. Review the actual captures, retain failures
and source cuts, and independently review the implementation before expected-
head integration and resulting-main checks.

The complete GOAL remains in force. Original28 stays failed overall at 24/28;
P11/P16/P23/L03, the 16 external cases and all retained compatibility, timing,
authority, complete-reach, LFS, Unreal/live-physics and measured-authoring gates
remain open. The three original missing C080 artifacts and incomplete earlier
history remain disclosed. This review does not close a feature release or the
whole product.
