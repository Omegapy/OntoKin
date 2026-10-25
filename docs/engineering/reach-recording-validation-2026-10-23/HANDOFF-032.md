# OntoKin continuation: HANDOFF-032

Checkpoint: **October 24, 2026, 20:51 America/Denver** (`2026-10-25T02:51:19Z`).
Coordination: [Issue #26](https://github.com/Omegapy/OntoKin/issues/26).
Owned publication branch: `work/reach06-regression-verify-20261024-05dd`.

**The bounded regression-fixture validation is complete on identified source `99d683741d5eea20910c319463871dec8cd9afce`.** The final default local run passes **7/7 checks**, including a complete **3,064/3,064** unittest execution on CPython **3.12.14**, with zero failures, errors, skips or expected failures and unchanged source inputs. The earlier complete default run remains **failed, 6/7**. Its construction-request elapsed-limit failure is preserved and its cause remains unestablished. No runtime optimization, new recording pass, release acceptance or main merge is claimed.

## 1. Resume and ownership

Read live `AGENTS.md`, `GOAL.md`, `STATUS.md`, `README.md`, `docs/README.md`, the adopted reach specification and release contract, [HANDOFF-030](HANDOFF-030.md), this handoff, Issue #26, and the relevant draft PRs. Re-observe every remote head, active scope and integration lease before editing. A timeout or missing workspace does not establish that another worker stopped.

The shared README/STATUS overview still contains the preceding coordinator's checkpoint. This worker supplies an applicable [proposed overview patch](checkpoint-032-overview-update.patch) for coordinated owner integration. It has passed `git apply --check`; it has **not** been applied. Shared timestamps, ownership and integration fields are unchanged. New evidence is published only on this worker's branch, for a new draft PR based on PR #28. Only the continuation owner may advance PR #28 through fresh observed-head, nonforce coordination.

| Identity | Observed state before this evidence publication |
| --- | --- |
| Main | `2bb4588e121fcfe99b4d42c734b15b38362f3642`, unchanged; no main lease acquired |
| PR #27 | Open draft, unmerged; `f8e0bb3e4a13bf9c83180d21e22e9a2c71e20153` |
| PR #28 | Open draft, unmerged; `450956c8706b3e6d9cb27dcc8f2935418f14853a` |
| Earlier regression branch | `work/reach06-regression-20261024-dd3c`, still `942ca5244f0b6633eb6cbd06c4fa90475c388ae9` |
| Tested final source | `99d683741d5eea20910c319463871dec8cd9afce` |
| Tested final tree | `8d75db307b98c56e587021e900d7c254926be348` |
| Accepted runtime implementation | Unchanged checkpoint-030 `d2f0088c4f3c1f570630334804a5a8f78e0105ac` |

The evidence commit containing this handoff is a later documentation/archive publication; it is not the source/test cut used for the executions. Consult its actual Git identity and the latest Issue #26 publication comment rather than substituting an earlier branch head. Both existing PRs remain draft. No hosted job, paid CI, forced ref update or main merge was performed. The tested source had zero GitHub workflow runs, check runs and status records at the recorded inspection.

## 2. Actual executions and coverage

The [checkpoint record](checkpoint-032.json), [final local summary](checkpoint-032-local-core.json), [independent execution review](checkpoint-032-execution-review.json) and [36-attempt audit](checkpoint-032-audit.json) bind the commands, source identities, raw outputs, input inventories and actual counts.

| Execution | Source | Actual result |
| --- | --- | --- |
| Four originally failing methods, each run individually and serially | `942ca524` | Four separate 1/1 passes |
| Added explicit stale-CellAnchor rejection method | `942ca524` | 1/1 passed |
| Three complete original affected modules | `942ca524` | 15/15 passed |
| Six later failure methods on candidate and untouched checkpoint 029 | `942ca524` and `6afa8439` | Twelve complete failed executions retained, one failure each |
| Six corrected later methods, individually | `99d6837` | Six separate 1/1 passes |
| Complete combined affected/related modules | `99d6837` | 325/325 passed, zero skips |
| First completed full unittest run, within `local-core-002` | `99d6837` | 3,064/3,064 passed; 1,440.281 seconds |
| Complete default driver `local-core-002` | `99d6837` | **Failed, exit 1; 6/7 checks passed** |
| Exact construction-method diagnostic retry | `99d6837` | 1/1 passed |
| Complete stock construction diagnostic retry | `99d6837` | 128/128 methods passed; separate diagnostic execution |
| Final complete unittest run, within `local-core-003` | `99d6837` | 3,064/3,064 passed; 1,148.901 seconds |
| Final complete default driver `local-core-003` | `99d6837` | **Passed, exit 0; 7/7 checks passed** |

Both complete unittest logs contain exactly the collected **3,064 distinct method IDs in order**, actual successful outcomes and complete `OK` footers. No count is inferred from a partial log or parser sentinel. The final raw log contains **604,009 bytes**, SHA-256 `ac4725b7e6d1b5dee43e2d5322598ee11b278ab45e12cc49e13f27620a260abc`. The earlier complete log has the same byte count and SHA-256 `0396398a02d9d994f79610250e434633c2dd94a4453fd4be3ee81f36f6ac2986`.

Coverage is **115 ⊆ 194 ⊆ 325 ⊆ 3,064**. The 115 focused methods are wholly included in the 194 related methods. The combined run comprises three disjoint selections: **194 related + 63 original affected/adjacent + 68 later affected = 325**. It includes all nine changed modules; the original three modules' 15 methods are exercised again on the final cut. These counts and the repeated full runs must not be added together as unique coverage. The archive includes the complete method inventory, collection driver and input receipt.

The five initially isolated controls are:

- `test_reach_endpoint_traversal.ReachEndpointTraversalTests.test_cancellation_preserves_input_tracks_and_propagates_original_exception`
- `test_reach_endpoint_traversal.ReachEndpointTraversalTests.test_complete_p01_bytes_equal_carrier_major_proofs`
- `test_reach_pending_output.ReachPendingOutputTests.test_every_observed_field_equals_fresh_boundary_reconstruction`
- `test_reach_phase_reuse.ReachPhaseReuseTests.test_translated_and_differently_anchored_paths_do_not_borrow_bounds`
- `test_reach_phase_reuse.ReachPhaseReuseTests.test_changed_dynamic_errors_reject_the_retained_cell_anchor`

The final source inventory contains **1,862 files / 409,312,173 bytes**. The complete before/after mappings agree with collection and both full runs. Source and isolated-workspace Git identities remain clean and stable. Exact interpreter, platform, dependency versions, pinned-requirements hash and executable receipt are preserved. This is current CPython **3.12.14 / Linux x86-64** evidence; the three-version matrix remains open.

## 3. What changed in the tests

The two source commits after PR #28's inspected evidence head change **only nine test files**. The [source and coverage review](checkpoint-032-source-review.json) and [publication review](checkpoint-032-publication-review.json) identify the exact assertions and selected paths.

| Test scope | Corrected control and preserved obligation |
| --- | --- |
| Endpoint traversal | Both arms explicitly select exact scalar endpoint traversal and disable separate component reduction. Positive/equal invocation counts, full GLB/report equality, callback ordinal 83, original exception identity, `callback_error` identity and unchanged input tracks remain asserted. Separate reduction tests retain dispatcher coverage. |
| Pending output | The control reconstructs the public snapshot without overriding native staged validation. Both arms retain equal native proof eligibility and actual P16 release capture/publication. Output, cost, alias, transfer, mismatch, budget and cancellation assertions remain. |
| Phase reuse | Valid synthetic changed-operand comparisons omit an inapplicable CellAnchor in both arms and retain exact increment/fresh-recomputation checks. A separate retained-proof test requires changed-source rejection before publication and preserves the original state/proof. |
| Unit offsets | Both arms disable separate forward-translation selection. Actual native/ordinary offset calls and exact nonmultiplication-charge equality bind the measured saving. |
| Reference axis, child origins, sequential and sparse Cartesian | Both comparison arms hold later centered-reader selection constant; axis also holds native composition constant. Actual kernel/cursor/composition/sparse use, complete bytes/validation equality and cost reconciliation remain asserted. |
| Source Cartesian products | Both arms disable later Cartesian producer capture while retaining ordinary Y-head participation, selected phase assertions, completed phases, actual rotation steps, complete output equality and original limits. |

Runtime source, original `.ok` fixtures, independent oracles, tolerances, proof authority, callbacks, report contracts and request limits are unchanged. No assertion was converted to an expected failure or skip. Positive path checks prevent a passing comparison from silently missing its intended implementation.

The [six-method comparison](checkpoint-032-regression-comparison.json) retains twelve fresh failures across candidate and untouched checkpoint 029. Four complete signatures agree after replacing only checkout-root prefixes. The axis-recording and source-Cartesian cases fail at the same respective assertions but have different real operation totals; those differences are retained. This scoped attribution does not certify the whole baseline repository.

## 4. Failures, retries and missing historical files

`local-core-001` refused before test planning because its isolated copy contained an extra temporary file. Six initial baseline-method attempts likewise refused their clean-source precondition before running any test. Original tracked bytes were unchanged. The extra files, inventories and failure receipts are preserved separately; the environmental component responsible is unknown. Unique output paths and exclusive writing/execution windows were used throughout the successful runs.

The first completed default batch, [local-core-002](checkpoint-032-failed-local-core.json), retains its failed **6/7** result. Its [construction report](checkpoint-032-construction-failure.json) executed 128 methods: 127 passed and one failed. `test_retrieved_old_artifact_keeps_its_original_program_after_edit` failed the export-success precondition when the request guard reported **48,103.099285 ms against 30,000 ms**. C18, C19 and C20 reference that single failure. It occurred before the edit and old-artifact retrieval assertions, so it does not establish an artifact-provenance defect. The report does not establish why elapsed time increased.

A protocol recorded before the follow-up permitted one exact-method retry, one complete stock construction retry, and—only if both passed—one further complete default-driver invocation. Both diagnostics passed, and `local-core-003` then passed the actual full default plan. This is a new identified pass; the earlier failed result is neither changed nor explained away. Construction's final case result remains **19 passed / 1 pending** because C20 needs independent visual-delivery evidence. The final default report retains **16 external pending cases** across construction, surface and impulse.

The supported **2,400-second per-subprocess allowance** and **3,600-second outer allowance** affect only the external validation harness. They do not change OntoKin's **30,000-ms product request cap**. Checkpoint 030's separate 900-second batch timeout, failed driver and partial-log recovery remain historical failures. The new complete runs supply actual counts that the old partial execution could not.

The preceding `dd3c` workspace was readable during initial inspection and became unavailable before its checkpoint-031 raw files could be copied. The responsible component is unknown. A clearly marked retrospective observation records what independent readers saw; no missing raw log was recreated. Current acceptance relies on fresh checkpoint-032 executions. The observed unpublished six-file patch for `66fc501` reproduced its complete observed tree, but its original raw commit object was not recovered. **`99d6837` is a distinct published commit with that verified tree**, not a relabeling of the missing commit.

All **20 failed attempts in the 36-command execution inventory** remain explicit: 13 executed failed product/driver runs and seven preflight refusals with no tests executed. A separate packaging preflight false positive is also preserved with its original script and captured tool output. It produced no archive; its corrected successor passed. Evidence integrity acceptance never means every retained attempt succeeded.

## 5. Archive and independent verification

The [manifest](checkpoint-032-manifest.json) binds **426 members / 41,216,989 uncompressed bytes**. The ordered archive has **18 parts / 15,613,930 bytes**, joined SHA-256:

`a3dbe22f2821159049ad2020cdf61fca3ffd0baec427f42866d5f9f2fec852f3`

Manifest SHA-256: `ebb28d0965c211ee2ef899cb6593b01825ff8c1f8a3d4654aadd04d0ed361a73`.

The [archive review](checkpoint-032-archive-review.json) records successful part/joined/manifest hashes, exact membership, ZIP CRCs, safe paths, conflict-free file layout and extracted-file hashes. Every recovered byte was independently compared with the frozen original evidence tree. The independently authored evidence auditor then passed again against the recovered archive, accounting for all 36 planned attempts, exact test IDs, source/input/driver identities, commands, outcomes, traceback records and preserved temporary files.

Raw command streams, complete test logs, reports, before/after inventories, collection and execution drivers, prior auditor versions, recovery metadata and failure comparisons are included. Duplicate validation workspaces, environments, operational locks, bytecode and ephemeral signed download URLs are excluded. New documentation, packaging receipts and archive/replay audit receipts sit outside the archive to avoid circular hashes. The already-published checkpoint-030 archive was separately rejoined and verified; its original members remain unchanged.

From this evidence checkout, use fresh output names:

```bash
python docs/engineering/reach-recording-validation-2026-10-23/checkpoint-032-recover.py \
  --checkpoint docs/engineering/reach-recording-validation-2026-10-23/checkpoint-032.json \
  --manifest docs/engineering/reach-recording-validation-2026-10-23/checkpoint-032-manifest.json \
  --output /tmp/ontokin-checkpoint032-replay \
  --receipt /tmp/ontokin-checkpoint032-replay-receipt.json

python /tmp/ontokin-checkpoint032-replay/drivers/audit_regression.py \
  --evidence /tmp/ontokin-checkpoint032-replay \
  --output /tmp/ontokin-checkpoint032-replay-audit.json \
  --allow-failures
```

`--allow-failures` accepts preserved failures as valid evidence. It does not waive missing execution, changed inputs, skips, invalid receipts or a failed current gate. Inspect the separately named `final_checkpoint.latest_default_driver_passed` and actual run records. Archive replay executes no product tests. A product rerun must use a clean checkout of the identified source cut, the pinned verification environment, a newly coordinated exclusive window and unique logs. Its stock command is `python tools/check_local.py --timeout 2400 --output-dir <new-directory>`.

## 6. Next bounded development investigation

The last verified unchanged original recording suite remains **24/28** from checkpoint 030. This test-only checkpoint did not rerun original28 and adds no recording pass or runtime-performance claim. P09's historical validated pass at 99,975 operations remains unchanged; P11/P16/P23/L03 still have their last verified 100,001-operation refusals.

Follow [checkpoint-030-next-scope.json](checkpoint-030-next-scope.json) exactly: **neutral original P11/L03 source-endpoint capture and an independent input census**. Pair each capture with an unchanged stock failed run on the same identified cut. Preserve callbacks, owners, arguments and exception flow; do not replace arithmetic or install trace/profile/work observers. Capture source/wrapper ledgers at the approved boundaries and reconcile complete category maps, shared/reach totals, cache occupancy, source/options, diagnostics and underlying failure frames. Equal operation counts do not establish elapsed neutrality.

Independently decode all **52 P11 keys** and **178 L03 keys**, their actual binary clocks, carrier tracks and certificate identities. Bind the visited prefix and partially attempted final key to original indices. Existing counter-based key positions are inferences until captured. L03's direct orientation seed does not establish why it occurred. Keep unvisited-tail estimates conditional; do not resume with a reset allowance. Select an optimization only after the observations and independent census exist.

| Recording | Last verified refusal area | Scope |
| --- | --- | --- |
| P11 | Independent centered source-pose evaluation | Joint neutral endpoint capture/census with L03 |
| L03 | Independent source-pose orientation seed | Same capture; establish why direct reseeding occurs |
| P16 | Authored-clock monotonicity verification | Separate clock-cost investigation |
| P23 | Producer sampling / constant-pose cache lookup | Separate producer investigation |

Preserve **100,000 shared operations / 30,000 ms / 32,768 operand bits / 256 numerical-cache entries** and the separate **512 metadata-category limit**, original horizons/fps/helpers, source fixtures, oracles, tolerances, ownership and report contracts. Held equal-triple/P23 candidates remain held. Any runtime change requires fresh original28 and all affected regression and release evidence.

Even 28/28 recordings is an intermediate gate. Actual Agent delivery and all ten retrieved artifacts, complete source/rate acceptance, the CPython 3.11/3.12/3.13 matrix, independent native/browser/visual checks, hostile/inherited roles, formal input closure, all R01–R12/Q01–Q22 audits and resulting-main verification remain open. `GOAL.md` retains the wider unfinished language and product scope. **Keep the existing PRs draft and main unchanged.**

## 7. Copyable continuation instruction

> Continue authorized development in `Omegapy/OntoKin`. Read live ownership, adopted contracts, Issue #26, draft PRs #27/#28 and the new regression-verification draft, HANDOFF-030 and HANDOFF-032. Re-observe all heads and preserve other workers' unpublished work. Checkpoint 032 validates test source `99d683741d5eea20910c319463871dec8cd9afce`, tree `8d75db307b98c56e587021e900d7c254926be348`: 325 distinct selected methods and two complete 3,064-method unittest runs pass; the final stock default run passes 7/7. The earlier 6/7 elapsed-limit failure and all available failed evidence remain immutable, with its cause unestablished. Use the actual evidence commit containing this handoff and verify its archive. The continuation owner must coordinate any PR #28 advance; the proposed README/STATUS patch is not applied. Runtime remains unchanged and the recording result remains 24/28. Next perform only the already scoped neutral original P11/L03 endpoint capture and independent key/clock/carrier census before selecting an optimization. Preserve all callbacks, proofs, oracles and original caps. No hosted job, force update, main merge or release-acceptance claim.
