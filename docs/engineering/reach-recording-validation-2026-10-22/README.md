# Reach recording continuation, October 22, 2026

This is a development checkpoint, not release acceptance. The immediate gate
remains all 28 source recordings under the unchanged shared 100,000-operation
budget. The latest complete run passes **14/28**; all fourteen remaining cases
still fail on the attempted 100,001st operation. No result is inferred for an
unexecuted release role.

## Reconciled source and work

The owner's supplied checkpoint `9a4857ec6d4825416f8cc816da2310d33b50ddab`
was already superseded by actual draft PR #27 head
`215efd6c99d2e42ca54ddbd9d898dd99fa678418`, tree
`54e0d9e51db55fe006772bf1130a23d3ea9d62d5`. All 1,309 published files were
recovered and verified against their Git blob identities; the exact original
commit and tree were reconstructed locally. No newer unpublished checkout was
available in this environment. The six release-auditor files previously tested
at `6119dd293ef1174e182f9a8b8077a92b40054931` were not recovered from GitHub
or the retained evidence archives; those archives retain results and input
hashes, not their missing implementation bytes. That recovery remains open.

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

## Executed results

| Execution | Identified source | Observed result |
| --- | --- | --- |
| Combined focused 001 | `e48186e6e84c991d47f8e95fedb5a057999b7931` | 246 methods: 245 passed, one existing L02 0.75-second export budget error, no failures or skips; stable inputs. |
| Complete source 001 | Same `e48186e` | 14/28 passed, finished 04:29:00 UTC; stable inputs. |
| Combined focused 002 | `b325986cf363648e4c5643424584ac2eb32097d9` | 39 actual methods passed; two nonexistent module names caused loader errors. The failed invocation is retained. |
| Combined focused 003 | Same `b325986` | Corrected module inventory: 47/47 passed, no failures/errors/skips; stable inputs. |
| Complete source 002 | Same `b325986`, tree `e8cbd75f0f8c17e998cc4c3d8482fc0aaf0505ef` | 14/28 passed, finished 04:34:53 UTC; stable inputs. P01 68,458; P13 92,266; P14 77,666; P17 64,989 shared operations. |

The fourteen remaining cases are **P02, P05, P07, P08, P09, P11, P16, P18,
P19, P20, P23, L01, L02 and L03**. Producer receipts preserve every failure and
all passing artifacts. Focused counts overlap and are not added together or
substituted for a complete regression. The previously reported complete
1,374/1,374 regression belongs to an earlier code revision and does not verify
these changes.

Worker evidence is also retained: the initial planning cohort; the sampling
67-method run with its existing L02 budget error; the independent-reader
141/141 run at `05d3f2c`; its reproduced baseline callback-domain defect and
three baseline test-double errors; the terminal-graph worker's 29/29 run;
filtered source failures; and unchanged-budget observational profiles. The
subsequent independent guard change at `578d8bc` is covered by combined
focused 001, not retroactively by the earlier 141-method result.

## Evidence and reproduction

[checkpoint-001.zip](checkpoint-001.zip) retains **217** raw members, including
both complete source runs, all combined attempts, worker logs and profiles,
before/after tracked-file inventories, exact driver files, the integrated
source patch and raw local commit records. The
[manifest](checkpoint-001.manifest.json) records every member's size and
SHA-256; all members and ZIP CRCs were verified. The archive is 4,155,074 bytes,
SHA-256 `87e0d55adbc993d800cff8282dc68c9d94116a7ca6cc817d0a553cfd38cf0b95`.
[checkpoint-001.json](checkpoint-001.json) gives the machine-readable summary.

The actual complete-source command was:

```bash
/tmp/ontokin-verify312/bin/python tools/build_reach_source_artifacts.py --output-dir /tmp/ontokin-combined-source-002
```

The interpreter was CPython 3.12.14 on Linux. The six exact verification
packages were installed in a dedicated environment; installation is a
prerequisite, not a compatibility result. The archived focused driver and
reports identify each executed module and command. Fresh output directories
are required for every repetition.

Profiles are diagnostic, not acceptance. Earlier stage profiles label the
`ReachExecutionWork.operations` counter, which excludes work already charged
by construction. P23 construction alone consumes 31,952 shared operations;
the corresponding P09/P16/P07/L02 construction costs are 4,106/4,324/4,173/4,215.
`ontokin-planning-functions-002` explicitly profiles the complete inherited
compiler counter. Final producer receipts always report the actual shared
budget, including construction; no fresh allowance is created for exporting.

## Next work and unmet release gates

Complete the fourteen recordings before running the ten Agent artifacts and
full release roles. Continue sampling and independent certificate savings,
P23 construction/planning costs, and a separately derived coaxial phase-bound
proof where source topology establishes cancellation of signed angular rates.
Any tighter bound must satisfy the unchanged inequalities and be independently
verified; its implementation and results are not claimed by this checkpoint.

After 28/28, execute the complete Agent delivery/protocol corpus, current-cut
Python regression and CPython 3.11/3.12/3.13 compatibility, independent rate
inventory, actual native/browser checks, review every required fresh capture,
hostile inputs, inherited workflows and independent R01–R12/Q01–Q22 audit.
Recover or reconstruct the missing release-auditor implementation explicitly.
Do not merge before all mandatory acceptance requirements pass. The complete
OntoKin language and the remaining domains in GOAL are still in progress.
