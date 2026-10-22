# Reach recording continuation, October 22, 2026

This is a development checkpoint, not release acceptance. The immediate gate
remains all 28 source recordings under the unchanged shared 100,000-operation
budget. The latest complete run passes **19/28**; all nine remaining cases
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

## Latest checkpoint 003: certified native recording and independent verification

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
