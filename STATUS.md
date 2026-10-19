# OntoKin status

Checkpoint: **2026-10-19T18:17:00Z**. The complete [GOAL](GOAL.md) remains **in progress**. Native surface M01–M12, source impulse I01–I12 and the force source kernel are integrated. **Local validation is now the default under [OK-ENG-006](docs/engineering/OK-ENG-006-local-validation-and-hosted-ci-policy.md); automatic hosted CI has been removed from the current main workflow.** [PR #15](https://github.com/Omegapy/OntoKin/pull/15) merged at `caeb98577db275b3e913fbba4cf97f4fd661c1af`. Agent/0.5 remains consolidated in [PR #14](https://github.com/Omegapy/OntoKin/pull/14) at `2f08ff2858a5fca3aac7cff95b3aa1ebdd823f1c`, awaiting scoped validation and integration under the new policy. **GLB/0.5 and complete F01–F12 remain unfinished.**

## Integrated releases and preserved evidence

Native source 0.3 / surface-0.1, Agent/0.3 and GLB/0.3 supply parameterized loft geometry, regional PBR materials, rigid placement, source-driven animation, revision-bound triangle inspection and atomic source edits. PR #9 merged at `1a6dc3268c770d492b93e994b752c72eeb459cb0`; original [surface evidence](docs/engineering/surface-release-validation/README.md) is unchanged.

Source 0.4 / impulse-0.1, Agent/0.4 and GLB/0.4 supply authored off-center impulses on free homogeneous spheres, ordered release/impulse boundaries, whole-boundary rollback, bounded inspection, physical-parameter repair and recorded animation. PR #11 merged at `d25ab70a08fe5fb1e9f9a5be7a71fe6cbc99225e`. Original [impulse evidence](docs/engineering/impulse-release-validation/README.md) and [integration record](docs/engineering/impulse-release-validation/integration.json) retain their own identified implementation, 40 source cases, 124 mapped methods, both 588-test inventories and independent destination/browser results. They do not certify later changed runtime bytes.

Source 0.5 / force-0.1 adds finite constant world COM-force intervals, exact completion clocks, additive final active sets, unchanged anchors when acceleration is unchanged, inherited release/impulse ordering, atomic rollback, bounded histories and valid short prefixes. Its adopted source contract and original 44 fixtures remain unchanged; twelve supplements and explicit additive errata supply 56 effective source cases without widened tolerances. Kernel implementation `cd5a6f2131b1fe2c760ab851a11c2c5b3cf119b1` passed 677 tests. PR #13 merged at `74089239eb81b3c5a335b63145b3444eccfab148`. All four resulting-main jobs passed in [39198117569](https://github.com/Omegapy/OntoKin/actions/runs/39198117569). [Kernel checkpoint](docs/language-design/force-v0.1/KERNEL-CHECKPOINT.md) and [integration record](docs/engineering/force-kernel-validation/integration.json) retain exact source/tree comparisons. Do not merge these completed PRs again.

Latest successfully executed observed main CI: [39204919656](https://github.com/Omegapy/OntoKin/actions/runs/39204919656) at `0a8f1f6908571adbd7abc31613397524b46a3c8b`. Later main `1bc87c5e78ca736913e9a5f8bc47845ce902e7b3` changed STATUS only.

## Agent/0.5 implementation and verification

PR #14 preserves original service `f2785fff`, recovered schemas/recorder `db50d464`, corrected audit/tests `f0326561`, dedicated CI `f1746048`, and reconciled main records `45d213a`. Current head `2f08ff2858a5fca3aac7cff95b3aa1ebdd823f1c` additionally preserves the [exact checkpoint record](https://github.com/Omegapy/OntoKin/blob/2f08ff2858a5fca3aac7cff95b3aa1ebdd823f1c/docs/engineering/force-agent-validation/CHECKPOINT.json). Earlier branches remain intact.

Tested implementation **`f17460489d9c1bb55053a6de6d08a9fea45d5bb1`**, tree **`e4049fa291588597c56b2694c1bcdad4d20f9307`**, supplies explicit discovery, isolated stores/cursors, complete source-bound force state, atomic mass/force/duration repairs, cancellation and final-envelope budgets. Public schemas, actual source workflow, independent source/message audit, 29 adversarial/schema tests, nine transaction/CLI tests and guides are implemented. Unavailable GLB/0.5 requests still fail explicitly without an artifact. Older defaults, catalogs, schemas and stores retain their meaning.

| Executed evidence | Actual result |
| --- | --- |
| Local complete regression | 733/733 passed, zero failures/errors/skips, 267.381 s |
| Guarded publication regression | 733/733 passed, zero failures/errors/skips, 281.796 s |
| Original source and Agent | 43 cases / 694 assertions and A01–A10 passed |
| Actual Agent/0.5 workflow | 418 exchanges, 25 immutable source snapshots, 334 predetermined samples; independent audit passed; 411 complete force projections schema-checked |
| Documentation preservation | 29 historical sources, 233 sections, 673 links passed |
| Publication run | [39246541254](https://github.com/Omegapy/OntoKin/actions/runs/39246541254) passed all executed steps; code child `f0326561988ae1ff171bc620492059444874729c` |

Runtime is `ontokin-reference` 0.4.0, SHA-256 `ad1c473a595dc1147bfeef10330a39bbffb33cd68cc236ec70fc12b445e720ea`. Five rehashed corruptions accepted by the earlier audit are now rejected. They established evidence-verification defects, not a force-kernel defect. This audit continuation changed no runtime, adopted expectation, numerical tolerance, earlier schema or historical evidence. Verification-only dependencies remain separate from the standard-library runtime.

Artifact **12183769150**, run 39246541254, retains the successful source.bundle, messages and logs until **2026-11-02T11:47:27Z**. ZIP SHA-256 `3c783a352888b429d538d9665105cb8081f964af04e668bbe43a43e67fe93067`; downloaded ZIP, bundle, commit/tree and logs were checked. A separately retained conversation archive contains 873 regular source/message/evidence files, 138176 bytes, SHA-256 `51088ecf5462ad8c1dba800cf027932c62b9fcf7d6451d80062c3c69590a193f`. Its file ID and members are recorded with PR #14. **That archive is not yet published as a repository file.** Mutable service stores and staging payloads are excluded.

## Local validation and exact next actions

The owner requested no paid Actions execution. [OK-ENG-006](docs/engineering/OK-ENG-006-local-validation-and-hosted-ci-policy.md) adopts fresh, identified local checks for routine integration. Run `python3 tools/check_local.py`; use `--full` for the complete existing visual workflow after preparing its pinned tools. Do not wait for hosted execution, retry blocked jobs, or enable paid execution as a prerequisite for routine development.

[The migration evidence](docs/engineering/local-validation-2026-10-19/README.md) binds code `04622489c269695bb8c4942090935020293f590e`, tree `dcf4848e2abf8565ad4a7083fa308b0b430b9bab`, to an actual complete local run: **30/30 steps passed; 689 tests with no skips; 525.530 seconds**. Original source 43 cases / 694 assertions and A01–A10 passed; all visual build/format/browser commands passed. All 599 original inputs remained unchanged. Actual environment was Python 3.12.14, Node 24.19.0, Chromium 141.0.7390.37 and Linux x86_64. [The integration record](docs/engineering/local-validation-2026-10-19/integration.json) verifies unchanged source/tool/test trees on resulting main and another 12 focused tests plus preservation checks.

The durable bundle retains logs, reports, immutable exchanges/source snapshots, 52 GLB files and 35 PNG captures; six representative captures were reviewed. It preserves the raw final progress checkpoint and a separate observed-completion/evidence-audit record after a saved-summary persistence discrepancy. That cause remains unestablished. **Sixteen external attestations remain pending; this is not a full release, three-Python matrix, Node 22 or macOS certification.** Original historical releases retain their own identified evidence.

At PR #14 head `2f08ff28`, dedicated Agent run **39250099200**, job **118051507054**, failed with **steps=null**; reference run **39250099192** also failed. Earlier evidence-retention run **39248717422**, job **118046935787**, never started a step and had no available log (BlobNotFound). The owner supplied confirmation of exhausted included minutes and a blocked $0 Actions budget. Connector job reads established nonexecution; this migration did not independently read the private billing balance or alter account settings. These jobs are not passed checks or executed test failures.

The current main workflow uses only `workflow_dispatch`; every hosted job requires a boolean opt-in that defaults to false. No workflow run was observed for the candidate or resulting merge. **Repository-wide Actions disablement was not applied; older branches can retain automatic workflows until synchronized.** Before integrating PR #14 or another old branch, inspect every workflow it adds or changes, including its dedicated force-agent workflow, and apply the manual-only/default-false policy.

Next, reconcile current main and PR #14, execute its actual required Agent/0.5 protocol/schema/audit checks and relevant regression roles on the identified implementation, retain the evidence, then integrate through the lease procedure. Do not use this migration's legacy/reference run as Agent/0.5 evidence. Reconcile the previously retained Agent archive and its expected helper branch separately. A future complete release audit needs a separately versioned provider-neutral evidence contract; do not fabricate CI identities or rewrite old schemas to accept local results.

Continue the acceleration-aware native GLB/0.5 adapter in its declared scope. The last published dependent branch is `work/glb05-native-forces-20261019-1315-astra` at `18cea63ba45fd6bc9989531cb97a3c88d923c524`: source geometry/PBR, requested-prefix simulation, exact force completions, complete source-bound histories, conservative translation/angular sampling, budgets/cancellation, independent decoded intermediate-motion checks and reviewed captures. The branch is not proof of an active worker or a completed adapter. Passing an export component is not completing F01–F12.

## Remaining full-product scope

GOAL still requires richer typed algorithms/libraries and compatible replacement; textures, mapping and skin deformation; continuous torques, contacts/collisions, general rigid dynamics and dynamic/closed mechanisms; vehicles; articulated creatures and purposeful locomotion/manipulation; flight/swimming and medium forces; vegetation/flexibility/wind; terrain/buildings; liquids and deformable solids; animation transitions, live engines, measured scale/performance and a documented direct-tool authoring comparison. Blender delivery and a generic delivered-level check are not established. Recorded playback is not live physics. Visual lofts add no physical matter or motion authority.

## Integration and recovery

**Main integration lease held.** Owner `interactive-agent05-local-20261019-1658Z-7of9` acquired this bounded lease at **2026-10-19T18:17:00Z**; it expires at **2026-10-19T18:47:00Z**.

Task: integrate reviewed [PR #16](https://github.com/Omegapy/OntoKin/pull/16) at `ff5b77a0203fa188788b5a89736168aced36f5a7`, incorporating PR #14 without changing its branch, then verify resulting main and publish the Agent/0.5 checkpoint. Observed main before acquisition: `e605be2a3e165cee497dd81213c8c84f9ba610b9`. The exact code `0d56b255a9e813e92bacba0c4cf5891a2481bca3` passed all 11 local roles, 753 regression tests and 56 dedicated Agent tests; [retained evidence](https://github.com/Omegapy/OntoKin/blob/ff5b77a0203fa188788b5a89736168aced36f5a7/docs/engineering/force-agent-local-validation-2026-10-19/README.md) preserves all attempts and storage diagnostics.

Reserved integration scope: main merge, shared STATUS coordination, and the new Agent/0.5 integration evidence record. Original worker branches, adopted fixtures and historical evidence remain intact. Independent nonoverlapping branch development remains allowed. No hosted run, paid execution or automation change is requested.

Recovery: after any uncertain write, inspect the actual main ref, PR #16/#14 states and this lease before retrying. Verify the resulting-main code/input identities and actual protocol/audit checks; then publish the final checkpoint and explicitly release the lease. Do not interpret a timeout or this lease's eventual expiry as proof that a write failed or another worker stopped.

[Previous complete checkpoint](https://github.com/Omegapy/OntoKin/blob/e605be2a3e165cee497dd81213c8c84f9ba610b9/STATUS.md) and [issue #12](https://github.com/Omegapy/OntoKin/issues/12) retain earlier releases and handoffs. No other worker or automation is claimed active.
