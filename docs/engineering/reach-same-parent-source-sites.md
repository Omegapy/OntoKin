# Equal site placements in one full source traversal

## Scope and current evidence

This candidate applies only to the ordinary, complete source-pose traversal
in `reach_runtime.py`. It does not apply to selected-frame, pose-only or
recording-only traversal, independent source verification, release cells,
final certificates or phase bounds. It adds a private, normally unset
post-charge observer to `ReachExecutionWork` so optional source admission can
observe existing callback boundaries without changing the callback owner.

Development started from
`9329a144e29364e88002171453b6adc63db8fd81` on the isolated branch
`work/reach06-source-sites-20261023-3be6`. No acceptance limits, source fixtures,
sampling rules or cache maxima change. This note describes the candidate and
its proposed checks; it does not claim those checks have executed.

The earlier neutral P23 planning observation at source
`0cd8400e2b31b14203a45497f934f90b8a3a28fe`, retained in
`evidence/p23-planning-observer-001`, measured three ordinary full source
graphs at 5,363, 3,343 and 3,650 request operations. Their translated-node
helper accounted for 1,251 calls, 1,205 reuse hits and 6,587 self operations.
That helper already reuses complete arithmetic across different translated
mounts. This change addresses the remaining repeated composition for equal
sites of the **same actual parent pose**.

P23's unchanged source contains 32 arms. Each arm has three authored identity
sites equal to its three system origin sites, and two authored link tips equal
to their corresponding hinge-tip sites. This predicts 160 duplicate site
recipes per complete graph, or 480 over the three ordinary source graphs.
The dedicated test checks that prediction and compares every retained object
and site value, current reach output, claim and coordinate with the old path.
Actual operation savings and the full original P23 outcome remain to be
measured on the committed candidate.

## The equation being reused

For parent private pose `P` and fixed source local pose `L`, the original
source site is exactly

```
S = pose_ops.compose(P, simulator._constant_pose(L))
```

Its result includes three exact position components, four projective
quaternion components, three exact linear-velocity components, three exact
angular-velocity components, a position error allowance and a rotation error
allowance. A frozen quaternion projection, if present, also belongs to the
rotation's value.

The original composition rounds the translated position and spatial rates,
propagates the offset derivative, multiplies rotations and adds the original
numeric allowances. An identity local pose is therefore **not** permission to
return the parent pose. Equal site recipes reuse the result of that complete
original computation, including its accumulated allowances.

Two site occurrences can use the same result only if they have the same
actual required parent object, the same owner path, and identical native
local frame, position and quaternion values. Position/quaternion keys use
binary64 hexadecimal values, preserving signed-zero distinctions. Equal
quaternions, instantaneous orientation, site names, nominal identities or
approximately equal coordinates alone do not admit reuse.

## Required frames remain the only result source

The optional index exists for one invocation of the full resolver. It stores
at most the current `max_cache_entries` number of frame paths and source/result
admission seals. That capacity remains at most 256. It stores no translated
offsets, completed pose copies or alternative cross-traversal result table.
The ordinary numeric LRU keeps its existing capacity and behavior.

A seal retains the source/operand owners and detached, bounded integer pairs
needed to detect mutation. Those pairs are comparison evidence only. A hit
must find the original representative in the current required `frames` map,
with its original object identity and all sealed numeric values unchanged.
Removal, replacement by an equal object, or mutation of that frame rejects
the optional read. A seal cannot recover a missing computed value. Numeric
LRU eviction is harmless only while the actual required frame is still
present and unchanged.

After the last callback and complete admission, the code reads the **live
required representative** and constructs the new required site's value from
those live fields. Its Fraction and rotation wrappers, projection dictionary
and projection-domain dictionary are fresh. No later mutation of a borrowed
private wrapper or projection memo can alter the new site's value. Existing
or subsequently populated representative projection dictionaries are never
used as the source of a new site's public components. All actual finiteness
and public projection checks retain their original call sites.

## Source, arithmetic and mutation admission

Only native `SceneModel`, `_ReachRunState`, `ReachExecutionWork`, `ReachPoseOps`,
`SiteModel`, `Pose`, `PoseValue`, `RotationValue`, tuple, Fraction and binary64
storage is eligible. The graph must exceed 256 source nodes; smaller graphs
retain their existing path cache. The optional arithmetic domain requires
the unchanged 32,768-bit operand cap and native Fraction inputs/results of
at most 512 numerator/denominator bits. Wider valid operands, custom dispatch,
malformed optional inputs and unsupported source shapes use the original
builder and its ordinary admission.

The complete original computation has already passed its prospective-width
checks at the same cap and the same exact operands. Reuse adds no arithmetic
whose width could exceed those checks: the new required record merely copies
the admitted live native integers into new Fraction wrappers. Native,
positive denominators and every source scalar type are checked, so Python
equality cannot turn a boolean or malformed rational into a valid receipt.
The optional bounds do not relax any original numerical constraint.

The receipt binds the current simulator/model/state/work/pose-operations
owners, program revision, exact clock, model table owners and sizes, callback
owner, native storage and relevant method dispatch. Each actual site read
binds its source-record owner, source path, occurrence identity, owning object,
local pose owner and all local placement fields. Each parent/result seal binds
its private component owners, exact numerator/denominator pairs, derivative
values, both error allowances and any frozen rotation projection.

An actual owner, source, parent or required-result change raises the existing
`reach_domain` admission error. It cannot be replayed through a corrupt warm
value. A matching retained receipt is admitted before deciding whether the
current parent is eligible for a fresh seal. A shared parent/result leaf that
becomes malformed must reject that warm receipt; it cannot turn into an
unsupported-input fallback. A fresh unsupported operand without a matching
receipt still uses the original builder. A live cap or arithmetic-dispatch
departure instead permanently
declines the optional index for that traversal. Restoring the cap or dispatch
at a later callback cannot revive that receipt. The original builder continues
under the live domain, preserving its own actual resource or dispatch failure
instead of manufacturing a successful optional fallback.

## Callback boundaries and accounting

`ReachExecutionWork.charge` captures its optional observer separately for
every member of an `amount` charge. It invokes the existing `external_check`
exactly as before, with the same owner. Original callback exceptions remain
the original objects and retain the existing `callback_error` behavior.
Original operation/time limits and counter updates run in their previous
order. Only a successfully completed charge then invokes the observer before
control returns to arithmetic.

The site scope installs this observer around its initial admission and the
original multi-operation builder or duplicate read. The observer sees a cap
or dispatch departure before a subsequent callback can restore it. It does
not catch or translate the original builder's exceptions. The default path
leaves the hook unset. A nested optional site scope declines an occupied hook;
ordinary reentrant work still invokes the original callback. Cleanup restores
only a hook still owned by the current scope, preserving a foreign replacement
instead of silently overwriting it.

Every eligible site pays one `source_site_admission` operation for its bounded
source/input admission and index lookup/publication. A duplicate pays one
additional `source_site_reuse` operation for its bounded complete
representative admission and required-record copy. Each original site visit,
owner resolution, complete graph observation, object finiteness check and
public output remains in place. Removed ordinary numeric-cache lookups,
promotions and repeated translations genuinely stop executing; no operation
counter is decremented or reset.

## Verification scope

`tests/test_reach_source_site_index.py` covers complete numeric/public equality,
identity-site allowances, changed local operands, signed zero, different
parent owners, malformed source values, wider and narrowed operands, bounded
index/numeric-cache storage, foreign hooks, required-frame removal/replacement,
numeric LRU eviction, private Fraction mutation, source-owner mutation,
independent projection ownership, temporary cap/dispatch changes, original
resource/callback/dispatch exceptions and reentrant ownership.

The actual unchanged P23 check compares the new and original full source
graphs at the started and terminal boundaries, retains all object/site values
and reach/claim/coordinate observations, and measures the request operation
difference. Partial and recording-only paths must not instantiate the index.
Relevant existing source-translation, source-node, source-pose, planning,
callback-domain and recording cohorts, followed by the unchanged original
P23 request, still need execution on the identified committed source.

The first focused execution at `c27f7f653d04ecc971ac9ad631504e3135c4fbb9`
passed 20 of 21 methods with stable inputs. Its complete raw evidence remains
in development run `p23-source-sites-focused-001`. The original P23 full-graph
comparison passed with all 480 expected duplicate uses and positive net
operation savings. The negative Boolean-backed Fraction case failed: its
identity quaternion leaf was shared with the parent, making the fresh parent
seal decline before the existing warm receipt was checked. The follow-up
admission ordering above retains that unchanged negative test and the
existing fresh wider-operand fallback test. It has not yet been executed.
No broader cohort or full original P23 recording ran after that failure.

## Corrected execution and integration

Corrected source `de2fab39952054a85de596c06ba01b20dc5907e0`, exact tree
`b18f2b9286843672b03f5d21a3bdb8678e122052`, passes **21/21** dedicated
methods and **110/110** existing related methods, with stable inputs and no
failures, errors or skips. The complete unchanged P23 request still exhausts
100,000 operations. Its counters confirm 480 actual `source_site_reuse` uses
and 963 admissions; translated relative-pose domain work falls from 1,251 to
771 calls. These are execution and activation observations, not a P23 pass.
The earlier failed test remains preserved in checkpoint020. Root integrates
these four owned files onto checkpoint020 before its separate focused and
complete-original-suite execution.
