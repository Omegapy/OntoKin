# OntoKin status

Checkpoint: **2026-10-19T18:27:57Z**. The complete [GOAL](GOAL.md) remains **in progress**. **Agent/0.5 is integrated** through [PR #16](https://github.com/Omegapy/OntoKin/pull/16), main merge `2a7cf5651de7ffe2737ad06478de3f53716b8c4f`, with fresh local acceptance and resulting-main checks. The original [PR #14](https://github.com/Omegapy/OntoKin/pull/14) is now also marked merged by GitHub; its original branch and head `2f08ff2858a5fca3aac7cff95b3aa1ebdd823f1c` are preserved. **GLB/0.5 and complete F01–F12 remain unfinished.**

## Integrated capability and evidence

Explicit `ontokin.agent/0.5` supplies source force discovery, complete revision-bound force state, atomic mass/force/duration repairs, isolated stores and cursors, retries, cancellation and final-response budgets. Its schemas, actual source workflow and independent source/message audit are implemented. Unsupported GLB/0.5 delivery fails explicitly without an artifact. Earlier profiles and defaults retain their meaning.

The [new validation record](docs/engineering/force-agent-local-validation-2026-10-19/README.md) identifies tested code `0d56b255a9e813e92bacba0c4cf5891a2481bca3`, tree `04f9f7029dcc85ab7e43fede69a572b45bfed232`. Runtime and frozen language fixtures are unchanged from the original Agent branch. Runtime remains `ontokin-reference` 0.4.0, SHA-256 `ad1c473a595dc1147bfeef10330a39bbffb33cd68cc236ec70fc12b445e720ea`.

| Executed check | Actual result |
| --- | --- |
| Complete selected local plan | 11/11 steps passed in 427.837 seconds; CPython 3.12.14 / Linux x86_64 |
| Full regression | 753 tests; zero failures, errors, skips or expected failures |
| Dedicated Agent/0.5 cohort | 56 tests, zero skips; also included in the full suite |
| Original source and Agent | 43 cases / 694 assertions and standalone A01–A10 passed |
| Fresh source workflow and independent audit | 418 exchanges, 25 source snapshots, 334 predetermined samples, 411 complete force projections passed |
| Source stability | All 623 original inputs and the source Git revision unchanged |
| Resulting main | All six checks passed: 20 runner tests, source conformance, A01–A10, another fresh workflow, independent audit, documentation preservation |

[Integration metadata](docs/engineering/force-agent-local-validation-2026-10-19/integration.json) binds the actual merge, matching implementation/test/tool/fixture trees, resulting-main logs and immutable source/message evidence. The isolated local driver now preserves actual source Git identity, including when evidence is outside the repository. Both failed attempts are retained: the first exposed the repaired Git-provenance defect; the second lost durable SQLite state after all regression/cohort tests passed. A minimal production-store probe observed a database inode replacement and regressing timestamp outside Agent evaluation. The replacing environment component remains unidentified. The complete passing run paused other executor/filesystem activity; runtime, WAL behavior and the suite's own concurrency tests were unchanged.

Earlier finite releases retain their identified evidence:

- Native surface M01–M12, Agent/0.3 and GLB/0.3: [PR #9](https://github.com/Omegapy/OntoKin/pull/9), merge `1a6dc3268c770d492b93e994b752c72eeb459cb0`, [surface evidence](docs/engineering/surface-release-validation/README.md).
- Source impulse I01–I12, Agent/0.4 and recorded GLB/0.4: [PR #11](https://github.com/Omegapy/OntoKin/pull/11), merge `d25ab70a08fe5fb1e9f9a5be7a71fe6cbc99225e`, [impulse evidence](docs/engineering/impulse-release-validation/README.md).
- Source 0.5 / force-0.1 kernel: [PR #13](https://github.com/Omegapy/OntoKin/pull/13), merge `74089239eb81b3c5a335b63145b3444eccfab148`, [kernel checkpoint](docs/language-design/force-v0.1/KERNEL-CHECKPOINT.md) and [integration record](docs/engineering/force-kernel-validation/integration.json). Exact clocks, additive overlaps, rollback, anchors and short-prefix rules remain adopted; 44 original fixtures plus twelve explicit supplements retain their expectations.

The [recovered historical Agent archive](docs/engineering/force-agent-validation/README.md#historical-archive-recovery) preserves hosted run 39246541254 separately from the new local runs. Its original `CHECKPOINT.json` is unchanged. The separately identified conversation archive remains unavailable and is not claimed to be the recovered archive. Historical results do not certify later changed bytes.

## Local validation and next unmet gate

[OK-ENG-006](docs/engineering/OK-ENG-006-local-validation-and-hosted-ci-policy.md) makes local checks the default under the owner's no-payment direction. Prepare the [pinned verification-only packages](docs/engineering/force-agent-validation/README.md), then run `python3 tools/check_local.py --force-agent` in a fresh output directory. Use `--full` for the existing visual roles after preparing their pinned tools. Runtime dependencies remain Python's standard library.

Both current workflows are manual-only with a boolean hosted-job opt-in that defaults to false. No hosted run was dispatched or retried; no run was observed for the tested candidate or resulting merge. Repository-wide Actions settings and automations were not changed; older branches can retain automatic workflows until reconciled. [The prior local-policy migration](docs/engineering/local-validation-2026-10-19/README.md) retains its own 30-step execution and visual evidence. Sixteen external attestations remain pending in the current inherited reports. This checkpoint supplies no new Python 3.11/3.13, macOS or browser/visual attestation and does not complete a release.

**Next: implement the bounded acceleration-aware recorded GLB/0.5 adapter.** The preserved dependent branch [`work/glb05-native-forces-20261019-1315-astra`](https://github.com/Omegapy/OntoKin/tree/work/glb05-native-forces-20261019-1315-astra), head `18cea63ba45fd6bc9989531cb97a3c88d923c524`, adds only one engineering contract; it contains no published adapter implementation, tests or captures. Continue on a new branch from current main. Reconcile its conflicting OK-ENG-006 identifier under a new unused ID and apply the adopted local-validation policy before integration.

The adapter must preserve source geometry/PBR, requested-prefix simulation, exact force completions, complete source histories, conservative acceleration/angular/float32 bounds and cancellation/budgets. Then execute actual source exports, independent decoded intermediate-motion checks and reviewed browser captures. Complete F01–F12 requires the remaining force-release gates and a separately versioned provider-neutral evidence contract; do not relabel historical CI schemas or a component pass as complete release evidence.

## Remaining full-product scope

GOAL still requires richer typed algorithms/libraries and compatible replacement; textures, mapping and skin deformation; continuous torques, contacts/collisions, general rigid dynamics and dynamic/closed mechanisms; vehicles; articulated creatures and purposeful locomotion/manipulation; flight/swimming and medium forces; vegetation/flexibility/wind; terrain/buildings; liquids and deformable solids; animation transitions, live engines, measured scale/performance and a documented direct-tool authoring comparison. Blender delivery and a generic delivered-level check are not established. Recorded playback is not live physics. Visual lofts add no physical matter or motion authority.

## Integration and recovery

**Main integration lease active.** Owner `interactive-force08-integration-20261020-0448Z-7of9`; acquired at **2026-10-20T04:48:14Z**; expires at **2026-10-20T05:18:14Z**. Scope: integrate [PR #17](https://github.com/Omegapy/OntoKin/pull/17), accepted force F01–F12 implementation/evidence head `34e33adce7eb07896c8f6f30ddbf6caa66545d2d`, then verify resulting main and publish measured STATUS/GOAL and the integration record. Acquisition uses a nonforce expected-head update from observed main `f901b1ac3b09fcb20842285f12d407dc919f9632`. This holder reserves main writes, STATUS/GOAL coordination and `docs/engineering/force-release-validation/`; independent nonoverlapping branches remain available. No hosted job is required or dispatched.

The earlier integrated capability checkpoint above remains historical until the merge and resulting-main verification finish. PR17 already retains the actual all-F01–F12 passing audit and all83 reviewed captures; full-product acceptance remains open.

**Prior lease release.** Owner `interactive-agent05-local-20261019-1658Z-7of9` acquired the lease at `2026-10-19T18:17:00Z` in commit `9400f3f18c2399b6c678ca845176daae42d718fd`, with expiry `2026-10-19T18:47:00Z`. Release recorded at **2026-10-19T18:27:57Z**, effective when this checkpoint is published to main through a nonforce expected-head update from verified merge `2a7cf5651de7ffe2737ad06478de3f53716b8c4f`. The merge and resulting-main verification completed before release; this final change contains only documentation and retained evidence.

After an uncertain write, inspect actual main, PR states and this record before retrying. Original worker and integration branches remain preserved; a branch or schedule does not establish that a worker is active. [Previous checkpoint](https://github.com/Omegapy/OntoKin/blob/e605be2a3e165cee497dd81213c8c84f9ba610b9/STATUS.md) and [issue #12](https://github.com/Omegapy/OntoKin/issues/12) retain earlier handoffs.
