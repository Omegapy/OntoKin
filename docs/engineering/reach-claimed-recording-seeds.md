# Exact seeds for repeated claimed recording bodies

## Scope and motivation

The unchanged original P23 recording has 32 simultaneous two-coordinate
reaches. Its first exact recording graph requests 64 complete carrier seeds
at one clock. Each carrier still needs its own source admission and ordinary
bounded cursor. Its direct source orientation, however, repeats the same
ordered calculation for translated copies of the same arm.

The existing captured-seed cache already recognizes equal complete source
calculations, but each lookup reconstructs the full ancestry recipe and
rechecks its frozen witnesses. This change builds those structural recipes
once in the existing traversal index. When a later body's **ordinary cursor
actually requests a cold seed**, it may copy an earlier required direct-seeded
rotation with the same complete recipe. This removes repeated source decoding
and seed-key construction, without replacing the target cursor's history.

The implementation is confined to `ontokin/reach_runtime.py`. The prior
[static rotation optimization](reach-static-recording-rotations.md) retains
its static-only whole-cursor path. Native approximate sampling, source
evolution, release transfer, certificate bounds, fixture bytes, requested
times and keyframe limits are unchanged. No acceptance gate is established
by this implementation or its focused tests alone.

## Exact equivalence of a direct seed

Let `D(P, f, t)` be the original captured private orientation calculation for
frame `f`, phase proof `P`, and exact clock `t`. The ordered orientation recipe
retains all operands consumed by that calculation:

- A fixed root contributes its source mode, public fallback quaternion,
  private quaternion and error, and full orientation claim. Claimed root
  motion is excluded from this optional path.
- A site or follow contributes its parent's complete recipe and its local
  quaternion, preserving composition order.
- A joint contributes its parent's recipe, joint kind, axis and limits,
  inverse child-site quaternion, and complete selected coordinate law.
- A claimed coordinate retains the action kind, duration, vector or goal,
  active status, actual and ideal initial coordinates, selected solution,
  elapsed clock, running-since clock and rotation metadata. A reach additionally
  retains whether the shoulder or elbow coordinate is selected. The exact
  complete body axis, rate and trigonometric count remain in the recipe.

Only names identifying equivalent occurrences and translations absent from
the ordered orientation calculation are omitted. Each occurrence independently
proves its full current named source witness before sharing. Phase boundaries
and the sample clock are fixed native numerator/denominator pairs for the
traversal. Therefore equal admitted recipes imply the same ordered scalar,
axis and quaternion operations, and hence the same private rotation components,
private error bound and optional frozen binary64 projection.

A root spin also consumes a separately selected source spin plan with its
own precision and horizon. That plan is not part of the orientation recipe.
Consequently roots with orientation claims cannot participate, even when a
pair of exposed quaternions happens to be equal.

## Why the cursor remains in control

An instantaneous law or quaternion does not identify a cursor's numerical
history. A target could already have a warm cursor, a different last clock,
an out-of-order sample, or a different recurrence count. The implementation
always calls its original `recording_body_orientation` method. That method
continues performing its own phase checks, typed domain checks, bounded cache
lookup, warm recurrence, step counting, source guards, final source admission
and cache publication.

The shortcut is inside the method's supplied direct-seed builder. It cannot
run on the warm branch. A required earlier frame may become a representative
only when this traversal observed its actual direct seed and the returned
rotation still matches that seed's full fingerprint. A warm result cannot
become a representative. If the first occurrence is warm and a later one is
cold, the later occurrence performs the original exact source calculation;
only subsequent equal cold seeds can borrow it.

The target receives fresh `Fraction` wrappers for all four components and its
error. This is a value-preserving copy of an already required result, not a
new numerical approximation. Its position continues through the original
parent-origin/grid calculation. Its source token and cursor entry remain its
own. No target lookup, update, recurrence, source guard or cache admission is
replaced by the structural index.

## Admission and mutation receipts

The optional claimed path requires all of the following:

1. An exact native recording traversal, original `ReachPoseOps` class and
   method/storage dispatch, plain context object, native run state, plain
   claims/dynamics dictionaries, no dynamics, and 16–256 native coordinate
   claims. The lower threshold avoids extra recipe work on small graphs; it
   is an amortization choice, not a source identity or acceptance condition.
2. The unchanged 32,768-bit operand cap, an unchanged cache capacity between
   one and 256, exact phase/sample clocks, and at most 4,096 proof frames.
3. The same model, root/staged state, pose operations, shared work budget,
   cancellation check, external callback, source revision and proof map.
4. Each proof record's identity, parent, immutable typed source witness,
   exact rate object/value, rate axis, trigonometric count and token. Each
   recipe is compared with the fresh source witness. Native integer/string/
   tuple typing prevents boolean/integer equality from admitting malformed
   frozen values.
5. The actual representative frame/pose/rotation identities and a bounded
   fingerprint of all rational components, error, and optional frozen float
   hex values, including signed zero. The fresh target ancestry must still
   match its original admitted named witnesses.

The existing witness bounds remain 512 nodes, eight levels and 32 entries per
tuple; ancestry receipt walks stop at 64. Rational receipt components have at
most 512 bits, so unsupported larger values use the original direct path.
The traversal retains at most the original cache capacity of representative
references and fingerprints. It stores no extra computed rotation, no
cross-clock history and no second cache.

Before a first representative is calculated, its required source ancestry is
copied into a private proof from already typed immutable witnesses. The copy
preserves the original record tokens, clocks and source revision. A callback
cannot temporarily replace live proof records, feed different operands to the
source decoder, then restore them before a final comparison. Ordinary source
admission still checks the actual model/state before publication.

A borrowed rotation is detached before the new charged sharing checkpoint.
Its representative and target receipts are checked again after that callback.
The original body cursor then performs all its ordinary charged source guards
and final source admission. After origin construction and exposure callbacks,
the borrowed representative and target receipts are checked once more before
the frame enters the graph. A changed receipt permanently declines sharing
for the rest of that traversal; restoration cannot revive it. Fallback uses
the original cursor/source calculation. A body-cursor cap retry clears any
receipt from an earlier builder invocation.

The new borrowed target also retains its own exact numerical fingerprint
across origin callbacks. Its ordinary cursor has already published that
private rotation, so a callback could reach it through the existing cache
without touching the earlier representative. A changed target component,
error or frozen projection raises the existing admission error before the
graph pose is returned; it cannot be replayed as a corrupted warm cursor.
Ordinary lazy projection changes a pose's separate projection dictionary or
the existing projection-factor cache. It does not modify a `RotationValue`'s
components, error or frozen projection, so those legitimate cache writes do
not invalidate the numerical receipt.

The ordinary failure and cancellation paths stay authoritative. Exceptions
from external checks are not caught or translated. A changed target source
must fail its original final source admission before its cursor is published.
On a late representative-only mutation, the already detached target value
remains correct; the fallback repeats the original cursor checks instead of
treating restoration as proof. Nested requests have separate local indices.

## Work accounting and expected benefit

No charged work is relabeled or refunded. The actual per-node structural
witness/recipe construction and each attempted shared seed are charged.
All target body-cursor operations, source-record guards, origin calculations
and fallback arithmetic remain charged by their original methods. The saved
work is the source decoder/seed-key construction and its cache access that
are no longer executed for an equal cold seed.

The operation cap remains 100,000 and the shared numerical cache remains at
most 256 entries. Removing redundant cache lookups may change ordinary LRU
retention and later misses; any resulting original work must still execute
and be charged. There is no promise that this isolated optimization clears
the entire recording. P23 still has later static sampling, certification and
independent validation work after its initial graph.

## Verification contract

`tests/test_reach_claimed_recording_seeds.py` compares exact private and public
values with only this optional claimed admission disabled. It covers the
complete original initial P23 graph and logs actual graph operation counts;
nonzero cold clocks; frozen/signed components; distinct world origins; warm,
repeated and out-of-order cursor histories; mixed warm/cold occurrences;
different durations and elapsed source laws; small/root/dynamic/native-owner
exclusions; strict and full-source paths; narrowed/restored caps; early and
late representative mutation; target source mutation before publication;
phase-clock and proof-record mutation; boolean-aliased frozen clocks;
borrowed-target mutation through its newly published cursor; ordinary lazy
projection;
transient live-proof replacement with the original live decoder as a negative
control; cancellation; and nested sampling.

The static, body-cursor, captured-seed, captured-graph and recording-sampler
cohorts must also pass. An original complete P23 recording must be attempted
under the unchanged operation cap and retain its actual stage, counters,
diagnostic and source identity even if it still fails. All original 28
recordings and the remaining mandatory release gates belong to integration
verification. The integrator serializes executor windows.

## Executed development checkpoint, October 23, 2026

The candidate implementation and tests at commit
`52548f3adfc01f4ea1424f2262a7976308e4f4e9`, tree
`4bddba19a6d85cf63eaf32c702f1980d4b0e650b`, were executed under an exclusive
window on CPython 3.12.14. All materialized tracked inputs matched their Git
index before and after each run. The driver separately discloses missing
historical binary archives; this is not the complete release input-closure
role or a compatibility result for other Python versions.

| Actual execution | Result |
| --- | --- |
| `p23-claimed-focused-001` | All 17 dedicated methods passed, with no failures, errors or skips. |
| `p23-claimed-cohort-001` | All 55 static/body-cursor/captured-seed/captured-graph/recording-sampler methods passed, with no failures, errors or skips. |
| Initial complete P23 graph and public projections in the focused comparison | 6,766 ordinary operations versus 6,118 with the optional index: 648 operations saved, exact private/public values unchanged, 64 target body cursors retained, captured direct-seed calls reduced from 64 to two. |
| `p23-claimed-original-001` | The unchanged full original recording still failed at the 100,001st request operation while sampling key 53 in the first static graph. Certification and independent delivered-byte validation had not begun. |

The original full-request attempt executed 62 claimed-seed shares. Against
the unchanged-source baseline, captured-seed domain calls decreased from
67 to five and seed witness blocks from 969 to 70. The same fixed budget
then reached 38 static shared-body completions instead of 26 before failing
at the child-origin cache promotion. All 66 target direct-seed cursor calls
still executed. These counters report progress within a failing request;
they do not establish an accepted recording or a total full-request saving.

The three named raw evidence directories retain the exact driver, environment,
commands, all materialized input hashes, complete test logs and individual
results or the original request diagnostic/traceback and every work counter.
Their publication is owned by the integration checkpoint. The candidate
does not change the 23/28 recording checkpoint or close any mandatory release
gate. Its measured improvement is limited to the repeated initial seed work.
