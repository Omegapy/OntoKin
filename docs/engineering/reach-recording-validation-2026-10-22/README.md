# Reach recording continuation, October 22, 2026

This is a development checkpoint, not release acceptance. The immediate gate
remains all 28 source recordings under the unchanged shared 100,000-operation
budget. The latest complete run passes **20/28**; the remaining cases
still fail on the attempted 100,001st operation. No result is inferred for an
unexecuted release role.

## Reconciled source and work

The owner's supplied checkpoint `9a4857ec6d4825416f8cc816da2310d33b50ddab`
was already superseded by actual draft PR #27 head
`215efd6c99d2e42ca54ddbd9d898dd99fa678418`, tree
`54e0d9e51db55fe006772bf1130a23d3ea9d62d5`. All 1,309 published files were
recovered and verified against their Git blob identities; the exact original
commit and tree were reconstructed locally. Publication `ad6169f65b4aef6569d5237351ab0f28722075b0`
then preserved checkpoint 001.

A later filesystem reconciliation located **21 clean older Git checkouts**
containing additional unpublished work. This corrects checkpoint 001's earlier
statement that no such checkout was available. Their exact heads, trees,
changed source/tool/test/document bytes and raw commit objects are retained in
checkpoint 002's static recovery inventory, deduplicated to **183** source
blobs. The originals were left unchanged; their old test results are not
current acceptance. Selected interval and source-observation changes were
reviewed, ported and freshly tested with the current implementation.

All **six exact release-auditor files** previously tested at the unavailable
commit `6119dd293ef1174e182f9a8b8077a92b40054931` were located at recovery commit
`d5c918312c68e7755c96eb818a8bfc409e9568cd`. Their sizes and SHA-256 hashes match
the preserved original input inventory. The recovery archive retains those
exact bytes separately from later auditor revisions. Current review,
integration and execution remain pending; the older 49-test result is not a
pass for this checkpoint.

Coordinator `interactive-reach06-complete-20261022-0410-7of9` works on
`work/reach06-complete-20261022-0410-7of9`. Planning, sampling and independent
reader workers use separate observed-head branches. Runtime, test, live-store
and archive execution is serialized. Main is unchanged at
`2bb4588e121fcfe99b4d42c734b15b38362f3642`; no main integration lease is held.
PR #27 remains draft and stacked on PR #25. Both workflows remain manual-only
with default-false hosted opt-in; no hosted job was requested, and the observed
baseline head has no workflow run.

The integrated implementation:

- Advances boundary-history preflight incrementally while retaining exact
  logical weights and all existing output limits.
- Reuses guarded measured residuals and exact recording spin increments.
- Factors endpoint position and quaternion conversion proofs, and visits
  carriers at each common key so the shared 256-entry cache can reuse equal
  quaternion operands before eviction. Each actual endpoint still contributes
  to its own carrier's maxima.
- Omits redundant independent grid rounding for already aligned exact sums,
  zero products and zero radicals. Changed cache domains re-admit retained
  operands before an equality shortcut can return zero.
- Reuses the complete incoming position/orientation graph only across a
  proved natural static reach completion. Fresh outgoing poses have zero
  derivatives; all source allowances, identities, finiteness checks, live
  limits and transactional rollback remain checked. General events, ongoing
  claims, dynamics or a narrowed operand cap use the ordinary resolver.

Frozen source/expected inputs, adopted quarter-allocation inequalities,
tolerances, actual trajectories and all public work/output/cache limits are
unchanged. Differential tests compare exact private values and complete GLB
bytes. Three stale independent-reader test doubles were updated to accept the
already existing `recording_context` argument; their assertions are unchanged.

## Latest checkpoint 008: 159 focused tests; 20/28 source recordings

The recovered local checkpoint `e4f51dbdb9ac9447a453e1a79f36e363108bd9af`
was published and read back at `b1d102a5391721b3e420277526696aca65b11ea5`. Its entire tree is exactly
`037849976437848c40b7cbbdf7e73ba60f4ada0d`; this also preserves the original
686-method and 20/28 historical evidence without relabeling it as current.

The new tested source is `4d5cae370aff239e632f05f94f7bbeb99aa145ff`, tree
`b042008cfd0911348b1665de6d49bea2a769b2ee`. Its full source run finished **2026-10-23T01:59:33.979602+00:00**,
passing **20/28** at the unchanged **100,000-operation** limit, with stable
tracked inputs. Remaining failures: **P05, P09, P11, P16, P20, P23, L01, L03**. L02 uses **94,169 operations**.

The same integrated source passes **159/159 focused methods**,
with no failures, errors or skips, in **42.455 seconds**.
Complete logs, method inventories, execution environment and before/after inputs
are retained. This selected cohort does not replace full regression or compatibility.

Changes include the recovered captured-graph sampler and independent phase-root
reuse, completed residual/square-root reuse, immutable source snapshot correctness
and original seed-failure propagation, exact repeated independent angular increments,
and complete orientation-claim inequality reuse. The existing numeric cache stays
bounded at 256; current source, callback and operand checks remain mandatory.

[checkpoint-008.zip](checkpoint-008.zip) contains **233 raw members**,
**4,036,914 bytes**, SHA-256 `5f885b5ad669079ab8d0e97c82b6149c712c804c68d18c5a52b53fdae22f4308`.
The [manifest](checkpoint-008.manifest.json) and [checkpoint](checkpoint-008.json)
identify every execution and its source. All **80 artifact/report hashes**,
every member and ZIP CRC were verified. Earlier archives are unchanged.
The earlier two test-assertion failures and clean-checkout preflight rejections
remain visible with their precise limitations.

Coordinator `interactive-reach06-continue-20261022-7fb5bc` works on
`work/reach06-continue-20261022-7fb5bc`; child scopes are recorded in issue #26.
The next work is complete-phase captured sampling, unchanged boundary-graph
finiteness admission and further independent arithmetic reductions, then another
complete 28-recording run. These pending candidates are not part of the current result.
Runtime, tests and archive creation remain serialized.

**Do not merge.** PR #27 remains draft; main stays
`2bb4588e121fcfe99b4d42c734b15b38362f3642`. Agent delivery, full current
regression/compatibility, independent rate verification, destination/browser and
visual checks, inherited/hostile roles and complete release audits remain pending.
No main lease or hosted job is claimed. Full GOAL remains open.

## Preserved checkpoint 007: 686 focused tests; source gate remains 20/28

The tested source is `63113dffd06ee879c3beeaaa52e22a74c813c6f5`, tree
`6f9df822639746327c101ea12da15e959a184eea`. Its complete source run finished
**2026-10-23T00:16:23.915776+00:00**, with stable tracked inputs and the original
**100,000-operation** request budget. It still passes **20/28**: P05, P09,
P11, P16, P20, P23, L01 and L03 each stop at operation 100,001. **L02 uses
93,980 operations**, down from checkpoint 006's 99,102. This is progress in
work cost, not a completed source gate.

The same source passes **686/686 focused methods**, zero failures, errors or
skips, in **92.287 seconds**. The complete raw log,
started/passed method IDs, interpreter/platform and before/after tracked
inventories are preserved. The preceding 682-method run had one ordinary
composition-interface error; the original test remains unchanged, and the
corrected run includes it. Earlier axis and geometry failures remain visible.

Changes since the verified published checkpoint `db745fbd5744624103da1d8c6cf076a719d456a4`:

- Reuse complete immutable spin operands and constant native relative transforms
  in the existing bounded numerical cache; atomic cursor batches retain final
  current-source admission and each actual cache-operation charge.
- Reuse independently constructed native primitives and immutable placed surfaces
  while checking every actual occurrence and retaining the role separation.
- Omit proved exact-zero endpoint/total work, reuse independently proved preceding
  arc envelopes, and fuse scalar/Z recording offset arithmetic before outward
  rounding. Ordinary source observations, cold seeds and unsupported graphs keep
  their original cells and interface.

P16 now completes certification and reaches GLB exact-clock encoding. P20
completes all endpoint rows and stops in the final independent certificate-group
checks. P11 reaches independent phase tables. P23 still exhausts its request
during sampling after about 80,872 operations of preparation on the preceding
profiled cut; its repeated source preparation and sampling need further work.
P05, P09, L01 and L03 remain independent-verification failures.

[checkpoint-007.zip](checkpoint-007.zip) preserves **473 members**,
**9,941,379 bytes**, SHA-256
`b59d52dcdb2e3eda5f52c58e9403fcddc93b5ea652ef142467a65b3a02be5483`. The
[manifest](checkpoint-007.manifest.json) identifies three complete source runs,
the focused passes and failures, diagnostic profiles, reproduction drivers,
exact source patches and raw commit objects. All **120 GLB/report
identities**, every archive member and ZIP CRC were checked. Earlier archives
are unchanged. The [machine-readable checkpoint](checkpoint-007.json) retains
the precise scope and limitations.

The first spin run reported 261 passes but its raw log was truncated. That
report/log remains unchanged and is explicitly limited. A fresh 261-method
run on the same source has a complete atomically written log and method IDs.
An earlier geometry preflight rejected an unidentified untracked temporary ZIP
before executing tests; its path, size and hash are preserved. No responsible
environment component is established for either observation.

The immediate target remains **28/28**, followed by all ten Agent artifacts,
full current regression and compatibility, independent rates, native/browser
checks, fresh capture review, inherited/hostile gates and release audits.
PR #27 remains draft and **must not merge** before every mandatory acceptance
gate passes. Main stays `2bb4588e121fcfe99b4d42c734b15b38362f3642`.
No main integration lease is claimed and no hosted job was dispatched.

## Preserved checkpoint 006: freshly verified 20/28 and 597 focused tests

The reported newer unpublished 20/28 checkout was not available in this workspace
or the inspected GitHub branches. The actual starting PR #27 head was
`afe4a40cd990e2262ffd634fcd550a952db0ffc2`. All 1,397 files and the complete Git tree were
reconstructed and checked against their published identities. A fresh unchanged
baseline reproduced **19/28**. This checkpoint establishes its own fresh result;
it does not relabel the unavailable earlier 463-test run.

The integrated source is `52a1e6c10f22074c51e96d3289a0b10c10bc1b21`, tree
`a5ae8aeef10094d10699373df656fbf4c97974da`. The complete source run finished
**2026-10-22T23:21:11.378310+00:00**, with **20/28** passes and stable
tracked inputs under the unchanged **100,000** shared operation limit. **L02 now
passes at 99,102 operations**. P05, P09, P11, P16, P20, P23, L01 and L03 still
stop at the attempted 100,001st operation.

The same source passed **597/597 focused correctness tests**, zero failures,
errors or skips, in **93.854 seconds**, with stable inputs.
These are the selected recording, phase, independent-reader, reference,
orientation-proof, export and certificate tests. This is not a complete regression.

The changes share complete immutable exact orientation seeds in the existing
bounded cache, omit repeated equal actual/ideal phase calculations, reuse
freshly admitted constant independent parent poses and position comparisons,
omit exact zero-slope coordinate arithmetic, and compute destination certificate
bounds once from their actual reported operands. Source identities, source and
callback checks, narrowed-cap fallbacks, original cancellation errors, independent
proof authority, frozen fixtures, tolerances and public budgets remain mandatory.

[checkpoint-006.zip](checkpoint-006.zip) retains **193 raw members**,
**5,829,537 bytes**, SHA-256
`884a4abd98e4d5357c906d039c5ac877d6e8660d79c9b84ed711b468fbad3da7`. Its
[manifest](checkpoint-006.manifest.json) identifies both complete source runs,
all scoped results including the still-failing isolated P23 probes, baseline
profiles, reproduction drivers, exact source patch and raw commit objects.
All **78 GLB/report members** match their producer hashes; archive
CRC and all member identities were checked. The
[machine-readable checkpoint](checkpoint-006.json) records the exact scope.
Earlier archives retain their original bytes and outcomes.

Coordinator `interactive-reach06-finish-20261022-1900-7of9` uses
`work/reach06-finish-20261022-1900-7of9`, with branch ownership recorded in issue
#26. Execution and archive windows remain serialized. Publication is authorized
to the existing draft PR #27 using an expected-head, nonforce update. Main remains
`2bb4588e121fcfe99b4d42c734b15b38362f3642`. No main lease or hosted job is claimed.

P23 still repeats native relative-pose work for its 32 identical chains. P16
now progresses farther through certificate construction. P11 reaches independent
geometry, and the other five failures reach independent certificate/reference
verification. Continue those reductions, then rerun all 28. Agent delivery,
full current regression and compatibility, independent verification, native and
browser roles and final release audits remain pending. **Do not merge.**

## Preserved checkpoint 005: complete source admission and repeated calculations

The latest tested source is `c011531992998d634ea9e2cf44e8eed8e9bddd40`, tree
`ef25230c3d2f64afa52d4911cd887fca9ce710e5`. Full source011 finished **2026-10-22
14:55:48 UTC**, with stable inputs and **19/28** passes under the unchanged
shared 100,000-operation budget. P05, P09, P11, P16, P20, P23, L01, L02 and L03
all stop at the attempted 100,001st operation. Source010 on `4351c07` had
passed **20/28**, with L02 at 99,572, before stronger source admission and
subsequent changes put L02 over the cap again. The current result is 19/28.

This checkpoint adds complete canonical inverse-kinematics receipts with all
four actual limits and current-call work, typed world-target decode reuse,
complete finite-pose proofs, and native identity/zero-origin projections.
Exact root translation retains the original rational equation and binary64
projection while omitting one-use cache entries. Native graph sharing binds
the complete ordered numeric orientation law at the same clock; every receiver
still admits its entire actual source ancestry. Direct carrier seeds consume
captured immutable source operands. Final cache publication rechecks the
complete current source after every cache callback and before any value or
order mutation. Original source/admission errors retain their identity.

Independent verification now has immutable world-orientation recipes,
root-spin recurrence, exact identity-carrier enclosure reuse, exact repeated
vertex witnesses and integer binary32 clock-cell checks. The producer's
numerical implementation/proof basis and the independent execution-input
closure retain their separate identities. Frozen fixtures, trajectories,
tolerances, every public limit and mandatory source/callback checks remain.

| Executed cohort | Exact source | Result |
| --- | --- | --- |
| Combined 014 | `e0d601848eeeba7012d30528b6d445a4ecd4c7ca` | **112/112**, stable inputs. |
| Combined 015 | `8eaef97df68c2a27df2bb8105ea0727ddc24d4c8` | **243 tests, 8 failures, 9 errors**, stable; retained. |
| Combined 016 | `4351c07c82f7df227bd3a4d820633c17e38ac22e` | **243/243**, stable inputs. |
| Native 017 | `1711a0a7574725952acdf60fcbc6947b536177e7` | **159 tests, 4 failures**, stable; retained. |
| Combined 018 | `c011531992998d634ea9e2cf44e8eed8e9bddd40` | **268/268**, zero failures/errors/skips; stable, 40.404 seconds. |
| Complete source010 | `4351c07` | **20/28**, stable inputs. |
| Complete source011 | `c011531` | **19/28**, stable inputs; current result. |

The 017 failures included a real native-body cost regression and three test
fixture mismatches. The final 268-method run retains the original strict
cost assertion and now passes it. The two old cached-leaf cases use a
nonidentity leaf to exercise their intended retained cache path; new identity
leaf tests separately cover current source, budget, cap and cancellation.
Other legacy spies explicitly exercise their original fallback paths, while
new tests cover the replacement paths. No expected physical result, adopted
acceptance threshold or operation limit was weakened.

[checkpoint-005.zip](checkpoint-005.zip) retains **272** raw members,
**5,190,924** bytes, SHA-256
`6ecc3544abf7f4e8a35c0ef69e2470f48073448a08703699913a9d1ef95c2f7c`.
The [manifest](checkpoint-005.manifest.json) identifies both full runs,
focused successes and failures, budget-limited profiles, reproduction drivers,
publication004 receipt, source patch from `cb93a45` and raw commit objects.
Assembly and two complete CRC/member-hash verifications used paused worker
filesystem windows. All **78** GLB/report files from the two full runs match
their producer receipts. The documentation preservation/navigation check
passed; its [raw log](checkpoint-005-docs.txt) is retained.
[checkpoint-005.json](checkpoint-005.json) records the
individual outcomes and current gate status. Earlier archives are unchanged.

P23 begins sampling at **80,984** shared operations and then exhausts its
budget on repeated exact boundary seeds. P16 reaches certification at
**92,841**; P11 reaches independent geometry; the other six failures reach
independent certificate checks. Subsequent seed and independent interval
reductions are work in progress. All ten Agent artifacts, complete current
regression/compatibility, independent rates, native/browser checks, visual
review, inherited roles and R01–R12/Q01–Q22 acceptance remain unexecuted for
this cut. PR #27 remains draft; main is unchanged; do not merge.

## Preserved checkpoint 004: planning, finite-pose receipts and endpoint reductions

The complete source run identifies `d1d947aedc4dfded55cd983b12063d0a29e65719`,
tree `70d5fea2d451620187f2eb731e5bc7fd62d7c8aa`. It passes **19/28**, with
stable inputs, and finished **2026-10-22 06:30:51 UTC**. P07 now uses **87,996**,
P08 **88,008**, and P18 **89,400** shared operations. The same nine cases remain
incomplete: **P05, P09, P11, P16, P20, P23, L01, L02 and L03**, each stopped at
the attempted shared operation **100,001**. No allowance was raised.

The implementation adds exact deferred phase locations, guarded prefix-frame
selection and unchanged-final-boundary projection reuse, complete immutable
finite-pose receipts and translated pose families, exact repeated interval
clock digits, native spin/vector/ballistic proof reuse, and a separately
derived uniform stored-lift sign test. Complete phase/planning derivations
are part of the source numerical identity.

The latest endpoint reduction freshly checks every actual seven-component
pose and its stored binary32 representation, then forms exact L1 sums from
component maxima once per group and carrier. This preserves all stored pose,
geometry and clock bytes; its conservative numerical certificate fields can
be larger. The original tolerances, quarter-allocation checks and independent
supplied-byte checks remain mandatory. Unsupported quaternion shapes and
changed or narrowed domains replay the original complete group. Cancellation,
rollback, changed operands and the existing 256-entry cache remain checked.

| Executed cohort | Exact source | Result |
| --- | --- | --- |
| Combined planning/sampling/reader 012 | `89dbe6e2100a08e919e3f52715d09b796fd7a4d4` | **212/212**, zero failures/errors/skips; stable inputs. |
| Endpoint/cursor/claim/basis 013 | `d1d947aedc4dfded55cd983b12063d0a29e65719` | **31/31**, zero failures/errors/skips; stable inputs. |
| Complete source 008 | `89dbe6e` | **19/28**, stable inputs. |
| Complete source 009 | `d1d947a` | **19/28**, stable inputs. |

The cohorts overlap and do not replace a complete regression. All **76**
GLB/report files from source008/009 match their producer receipts. The earlier
1,374-test complete regression still does not verify current code.

[checkpoint-004.zip](checkpoint-004.zip) retains **180** members,
**2,865,970** bytes, SHA-256
`7ae4274e8d26d5733789500e5c283a7e384cdf520647c80943786bb8c1db33ae`.
Its [manifest](checkpoint-004.manifest.json) identifies raw runs, profiles,
before/after inputs, drivers, publication003 receipt, exact source patch from
local checkpoint003 and raw commits. Every persisted member hash and ZIP CRC
was verified again in a separate call with worker filesystem activity paused.
The [machine-readable checkpoint](checkpoint-004.json) retains complete case
and cohort identities. All prior archives remain unchanged.

P23 now finishes planning and reaches sampling. Construction is still **26,373**
shared operations; its prefix plan costs **64,626** more. The next useful targets
are phase bounds, graph construction and boundary processing. P16 completes
sampling and fails during certification; the remaining seven failures are in
independent verification. A profile attempt collided with an existing output
directory and executed no source request; its failure log is preserved. The
subsequent uniquely named P23 profile completed with stable inputs and retains
the original budget failure. Full release roles remain pending until 28/28.

## Preserved checkpoint 003: certified native recording and independent verification

The complete source run identifies `5f7f503ab3727c4b78bc4b01ceb6472dc8c02473`,
tree `f6479c0f1da00b787eeed0fbb6667de2df7574d1`. It passes **19/28** and finished
**2026-10-22 05:52:52 UTC** with stable tracked inputs. P07 **94,833**, P08
**94,845** and P18 **95,782** now pass. The remaining **P05, P09, P11, P16,
P20, P23, L01, L02 and L03** stop at the attempted shared operation **100,001**.

Additional implementation work:

- Bounded native planar interior sampling retains exact first/boundary samples
  and supplies explicit conservative position/quaternion endpoint allowances.
  Production stored float32 values may differ from the exact sampler; they
  must satisfy the unchanged independent supplied-byte checks and tolerances.
  The separate strict-cell path proves byte equality when requested.
- Exact private affine hinge laws, bounded dynamic Horner motion and strict
  finite quaternion guards admit only the derived domain. Unsupported domains
  replay the whole phase with the original sampler and retain attempted work.
  Lowered limits, changed operands, cancellation and rollback remain checked.
- Complete native implementation and derivation hashes are bound into the
  source numerical identity and independent rate input inventory.
- Exact native phase operand keys and constant error templates reduce repeated
  decoding. Independently derived fused interval rotations round only their
  combined extrema; bounded shared proofs preserve each clock/context seed.
- Stationary endpoints retain a completed limit comparison only for freshly
  admitted identical values, typed equal limits and the current operand cap.

| Executed cohort | Exact source | Result |
| --- | --- | --- |
| Native sampling 005 | `5f7f503` | **67/67**, zero failures/errors/skips; stable inputs. |
| Combined sampling/source/reader 004 | `5f7f503` | **241/241**, zero failures/errors/skips; stable inputs. |
| Independent reader 011 | `763b0804af794d6ea79f812302eccaaf3f8ee698` | **232/232**, zero failures/errors/skips; stable inputs. |
| Phase/lifecycle 006 | Worker `68adba26352e87f8cbcbc26bacff7005efa7d6bf` | **72/72**, zero failures/errors/skips; stable inputs. |

Only `tests/test_reach_recurring_endpoint_claims.py` changed between the full
source run and reader 011. The original exact recurrence test is retained and
an additional native test proves both samplers reject independently measured
understatements of position and quaternion endpoint errors. The old exact
recurrence/body-cursor tests explicitly select their intended exact path.
Initial native cache invalidation, two exact-path harness assertions and reader
010's stale exact-path counter all remain visible with their subsequent fixes.
The source-artifact integrity script initially mishandled the `sha256:` prefix;
its corrected receipt confirms all **38** GLB/report files match. Both receipts
are retained; this was a comparison-script error, not artifact corruption.

[checkpoint-003.zip](checkpoint-003.zip) retains **136** members, **2,729,636**
bytes, SHA-256 `fc00cf5b71a1cee191bfe6ddc2610ac82eafc2ceab3e00dd596ed29669e18c02`.
Its [manifest](checkpoint-003.manifest.json) identifies all raw runs, failures,
profiles, before/after inputs, drivers, publication-002 receipt, exact patch
from local checkpoint 002 and raw commits. Every persisted member hash and ZIP
CRC was rechecked in a separate call while all worker filesystem activity was
paused. The [machine-readable checkpoint](checkpoint-003.json) records complete
case counts and exact cohort identities. Earlier archives remain unchanged.

P23 now completes both phase bounds but fails in its final boundary observation.
P16 uses the native path without a phase restart; repeated vector, root rotation,
enclosure and dynamic extent work still dominates sampling. P09 and L03 reach
independent verification. These profiles guide the next work without changing
any work allowance or acceptance threshold.

## Preserved checkpoint 002 implementation and executed results

The latest complete recording run and combined cohort identify implementation
`1bd2e4e7f5fb21a18db3e09f8f1d9e05b443d9df`, tree `7f88f4862d2b3b6a7d6d919665ca8a4a86ab38e3`.
Further changes after checkpoint 001:

- Bounded constant-expression and resolved-member reuse reduces P23's actual
  construction counter from **31,952 to 26,373**, preserving logical weights,
  source provenance, shadowing, evaluation depth, cancellation and diagnostics.
- Exact signed coaxial derivative bounds and independently reconstructed
  reader bounds tighten only proved ideal speed/acceleration fields. A typed
  phase witness permits complete carrier-rotation cursors; every general
  fallback and source allowance remains active.
- Shared relative observations, position-only target resolution, large-graph
  translated-node reuse and guarded terminal projection receipts avoid repeated
  exact work. Narrowed domains, changed operands and failed callbacks retain
  normal admission and whole-boundary rollback.
- Independent sufficient endpoint and interior-path arc inequalities avoid
  unnecessary square roots only when the actual supplied claims are proved.
  Closing semantic-boundary arcs retain normalized endpoint verification;
  identical actual quaternion operands with completed current-domain endpoint
  proofs have a separately proved exact zero arc.
- Exact sign-selected interval corners compute the original outward result
  with fewer products/divisions. All complete original prospective-width
  guards, interval/series caps and constituent callback checks remain.

| Execution | Identified source | Observed result |
| --- | --- | --- |
| Complete source 003 | `6edaaba0aa31333ba48cf249a746406094210e40` | 16/28; stable inputs. P02 and P19 newly pass. |
| Complete source 004 | `ada37ac` | 16/28; stable inputs, finished 05:17:09 UTC. |
| Complete source 005 | `199f82ec3abe39df1bbccc051b974ddd56461a94` | 16/28; stable inputs, finished 05:25:21 UTC. |
| Complete source 006 | `1bd2e4e7f5fb21a18db3e09f8f1d9e05b443d9df` | **16/28**, stable inputs, finished **05:34:19 UTC**. P01 **65,176**; P02 **75,765**; P13 **92,240**; P14 **74,824**; P17 **61,507**; P19 **70,347** shared operations. |
| Combined focused 009 | Same `1bd2e4e` | **98/98**, no failures, errors or skips; stable inputs. Includes source observations, complete carrier cursor, basis identity, independent endpoint/arc checks, terminal paths/projections, cancellation, rollback, limits and construction reuse. |
| Interval/source focused 001 | `d6e3662` | **60/60**, including all **45 source cases**, no failures, errors or skips; stable inputs. |

The twelve remaining cases at checkpoint 002 were **P05, P07, P08, P09, P11, P16, P18,
P20, P23, L01, L02 and L03**. Every failure stops at the attempted **100,001st**
shared operation. Producer receipts retain all passing artifacts and failures.

Earlier new focused attempts remain visible: combined 004 passed 98/98;
005 passed 111/112 with one stale basis-file-count assertion; 006 passed
113/113 after correction; 007 passed 88/89 with a terminal-cost regression;
008 passed 94/95 with an independent short-recording cost regression. Both
performance assertions remain unchanged and pass in 009 after the actual work
was reduced. The reproduced constant-expression depth defect and its corrected
128/129 boundary check, all worker attempts, construction profiles and the
independent-reader forgery-oracle correction are retained. Worker cohorts
include 195/195 independent-reader methods, 205/205 sampling methods and 31/31
relative-observation methods on their own identified revisions.

Focused inventories overlap and are not added together. The previous complete
**1,374/1,374** regression belongs to an older code revision; no current-cut full
regression or compatibility result is claimed.

## Preserved checkpoint 001 results

| Execution | Identified source | Observed result |
| --- | --- | --- |
| Combined focused 001 | `e48186e6e84c991d47f8e95fedb5a057999b7931` | 246 methods: 245 passed and one L02 0.75-second export budget error; stable inputs. |
| Complete source 001 | Same `e48186e` | 14/28, finished 04:29:00 UTC; stable inputs. |
| Combined focused 002 | `b325986cf363648e4c5643424584ac2eb32097d9` | 39 actual methods passed; two nonexistent module names caused loader errors. |
| Combined focused 003 | Same `b325986` | 47/47, no failures/errors/skips; stable inputs. |
| Complete source 002 | Same `b325986`, tree `e8cbd75f0f8c17e998cc4c3d8482fc0aaf0505ef` | 14/28, finished 04:34:53 UTC; stable inputs. |

## Evidence and reproduction

[checkpoint-002-verified.zip](checkpoint-002-verified.zip) retains **688** raw members from 64
run/file roots plus the source-recovery inventory. It includes four additional
complete source runs, focused successes and failures, worker evidence,
profiles, before/after tracked inputs, exact drivers, the integrated patch
from local checkpoint 001 and raw local commit records. The archive is
**11,334,068 bytes**, SHA-256
`12d63887498dfde34aa9e9622197d272fbf9bbb79398d0083311bdf1ad7067cc`.
The [manifest](checkpoint-002-verified.manifest.json) identifies every member; all hashes
and ZIP CRCs were checked, with tracked source unchanged during assembly.
[checkpoint-002.json](checkpoint-002.json) gives the machine-readable summary.

Two archive attempts were verified when created but subsequently appeared
truncated before publication. Their [initial](checkpoint-002-initial.manifest.json)
and [second](checkpoint-002-second.manifest.json) inventories and
[failure/reconciliation receipt](checkpoint-002-archive-reconciliation.json)
retain both expected and observed sizes/hashes and the missing ZIP-directory
error. No cause or responsible process is asserted. All **128** artifact/report
files from source runs 003–006 matched their producer receipts, and every
tested runtime input matched the source-run snapshot. All workers paused
filesystem activity for the third assembly. Its **688** persisted member hashes
and ZIP CRCs were then rechecked successfully in a separate tool invocation.
The truncated containers are not presented as usable evidence.

[checkpoint-001.zip](checkpoint-001.zip), its
[manifest](checkpoint-001.manifest.json) and
[summary](checkpoint-001.json) remain unchanged: 217 members, 4,155,074 bytes,
SHA-256 `87e0d55adbc993d800cff8282dc68c9d94116a7ca6cc817d0a553cfd38cf0b95`.

The latest complete-source command was:

```bash
/tmp/ontokin-verify312/bin/python tools/build_reach_source_artifacts.py --output-dir /tmp/ontokin-native-5f7f503-source-007
```

All new execution used CPython 3.12.14 on Linux and the six exact verification
packages. This prerequisite is not a compatibility result. Archived focused
reports identify each executed module, interpreter and command. Every run uses
a fresh output directory. Runtime/test/live-store/archive execution is serial;
static work proceeds on isolated worker branches.

Profiles are diagnostic. `ReachExecutionWork.operations` excludes preceding
construction charges; the complete inherited compiler counter and final
producer receipt include them. P23 compilation now costs 26,373 shared
operations. Its final boundary observation and P16 sampling costs still require
optimization; most other remaining failures occur in independent verification. No new work
allowance is introduced by exporting.

## Next work and unmet release gates

Complete the nine recordings. Next isolate deferred exact phase-location work,
repeated native sampling proofs and independent stored-lift sign verification.
These further optimizations are outside the tested checkpoint.
Preserve exact source behavior, cache bounds, cancellation, rollback and every
original acceptance inequality while reducing performed work.

After 28/28, execute all ten Agent artifacts and the complete protocol corpus,
current-cut regression and CPython 3.11/3.12/3.13 compatibility, independent rate
inventory, actual native/browser checks, every required fresh visual capture,
hostile inputs, inherited workflows and independent R01–R12/Q01–Q22 audit.
Review and integrate the recovered release-auditor implementation, then publish
its literal mapping before final acceptance execution. Do not merge before all
mandatory requirements pass. The complete OntoKin language and remaining GOAL
domains remain in progress.
