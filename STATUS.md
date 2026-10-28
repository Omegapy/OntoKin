# OntoKin status

Checkpoint: October 28, 2026, C059 reconciliation and Git LFS configuration merged and verified. The full [GOAL](GOAL.md) remains in progress: an AI-agent programming language for editable 3D shapes, objects and animation, with validated delivery to game engines including Unreal Engine.

## Released capability

The finite force-0.1 / Agent/0.5 / recorded GLB/0.5 release remains complete at its identified implementation and [release evidence](docs/engineering/force-release-validation/README.md). Earlier core, construction, surface and impulse releases retain their meanings. Recorded GLB playback supplies no live destination physics. C059 makes no new release or engine-acceptance claim.

## Current development integration

[PR #56](https://github.com/Omegapy/OntoKin/pull/56) merged as `1e2e7fff7bfb7ed638aa01db84c23fdf30bd35a3` and consolidates the reviewed C032 runtime and later C058 evidence. It excludes the held C035 runtime changes and preserves their exact tests and historical results. Explicit source 0.6 / planar-reach-0.1, Agent/0.6 and GLB/0.6 remain experimental. Existing defaults remain CLI Agent/0.1, Python ProgramAgentService/0.2 and GLB/0.1.

Tested candidate `4155acfd1b01e1b72aac23be5e28b054d2e10440`, tree `6afc9960c5551115c87aafdcbc1d9d002172d5f6`, passed 3,064 tests on CPython 3.12.14 with no skips. The separate 106-test Agent/0.5 cohort passed and overlaps that suite. Selected executions cover all 34 local-driver roles and eight supplemental force roles; all 83 resulting PNGs were actually reviewed. [The reconciliation record](docs/engineering/repository-reconciliation-2026-10-28/README.md) preserves exact commands, inputs, failed attempts, successful recoveries and limits.

The original full run failed two roles and blocked seven; the recovery passed those nine. The first force run passed four roles and failed its Agent build; an exclusive recovery passed the remaining four. SQLite state loss/corruption occurred in the failed attempts; its physical cause remains unresolved. Neither failed run is relabeled as passed. The C059 merge tree was `86a83027cb6761bd0ed3c8f1f59b9177066a597f`. Its complete tree and actual source-inventory comparison preserved all 3,184 original inputs outside the two current-status narratives; the unchanged documentation checker passed. [The C059 integration record](docs/engineering/repository-reconciliation-2026-10-28/evidence/integration.json) binds those results. Runtime executions remain attributed to the tested candidate. The later LFS verification-tool increment has separate evidence below and changes none of the 65 product runtime files.

## Decisions and unresolved gates

[OK-DEC-COMPARE-M1/0.1.0](docs/engineering/OK-DEC-COMPARE-M1-0.1.0.md) rejects exact C058 M1 for comparison-only operation saving. No replacement accounting model is adopted. The C057 comparison accounting/passive-authority concern remains open.

Historical original recording evidence remains **24/28, failed**. **P11/P16/P23/L03** remain unresolved, and **C035 remains held, including adverse timing**. Preserve all original limits: 100,000 shared operations, 30,000 ms, 32,768 operand bits, 256 numerical-cache entries and 64 cursor updates; all fixtures, horizons/fps/helpers, equations, independent oracles and tolerances remain.

The next runtime objective is to resolve the remaining original recording failures under the adopted semantics and complete-request accounting, beginning with the identified P11/L03 source-evaluation bottleneck and its independent evidence. Every new runtime change requires relevant regression and original-input verification. The finite reach release still needs all 28 source recordings and ten Agent artifacts, CPython 3.11/3.12/3.13, independent rates/native/browser/visual and hostile/inherited roles, formal input closure, and every R01–R12/Q01–Q22 requirement.

## Repository lifecycle and ownership

[OK-ENG-009/0.1.0](docs/engineering/OK-ENG-009-development-integration-and-branch-lifecycle.md) makes main the current development baseline while keeping release acceptance separate. Use one branch per active bounded scope, normally at most three active work branches; checkpoints are commits. The historical archive `archive/pre-consolidation-20261028` at `e6917dae0be3a786c22e76be3de62e3c97784cf5` preserves all 104 original branch heads through 95 distinct parents. Never merge its index-only tree into main.

All 34 original open draft PRs were closed with exact provenance; all 103 original inactive non-main branch names were removed after fresh-head checks and verified retention. After the merge, automatic branch deletion removed PR #56's branch. Verified remaining branches are main and the archive. Automatic deletion of merged head branches is enabled.

C059 integration scope `interactive-main-reconciliation-20261028-c059-7of9` is complete and released. LFS scope `interactive-lfs-storage-20261028-root`, acquired `2026-10-28T20:23:37Z` with expiry `2026-10-28T20:53:37.000Z`, is also complete and released by this checkpoint. No main integration lease remains active. PR #57's branch was automatically deleted after its merge; main and the historical archive are the only remaining branches. Reconcile actual heads and acquire a fresh bounded lease before future integration. Both hosted workflows remain manual-only/default-false; no hosted execution was dispatched.

## Git LFS

The owner authorized Git LFS use and funding. [PR #57](https://github.com/Omegapy/OntoKin/pull/57) merged as `a8138a2605448675e1a9cd515d960b9b52a077c2`. GitHub's inclusion of LFS objects in repository archives is enabled. Four committed rules configure future archives under the currently unused `docs/engineering/lfs-archives/` directory, with zero existing payload matches. [OK-ENG-010](docs/engineering/OK-ENG-010-git-lfs-archive-storage.md) defines strict pointer/payload identities, isolated local hydration and exact no-history-rewrite migration. [Focused evidence](docs/engineering/lfs-storage-validation-2026-10-28/README.md) records 15 storage tests and 21 local-driver tests passing with zero skips, including a repeated check of the applied patch. The observed merge tree matches the reviewed candidate; all 65 runtime files and existing archive payloads are unchanged. [The storage integration record](docs/engineering/lfs-storage-validation-2026-10-28/integration.json) binds actual results.

No payload has been replaced with an unuploaded pointer. The [migration inventory](docs/engineering/lfs-storage-validation-2026-10-28/migration-plan-001/plan.json) identifies 357 existing archives totaling 459,206,837 bytes at the LFS merge. Authenticated upload and independent download verification remain pending because the available connector cannot transfer LFS objects and this executor has no authenticated Git transport. Future tracking configuration and archive inclusion do not establish completed migration or reduce historical Git storage. Regenerate the exact plan from clean current HEAD in an authenticated maintainer checkout before following the documented conversion procedure; the saved inventory remains bound to its original merge.

## Remaining product scope

Keep the complete GOAL scope: richer typed algorithms/libraries and replacement, textures/mapping/skin deformation, continuous torques and contacts/collisions, general rigid dynamics and mechanisms, vehicles, articulated creatures and purposeful movement, flight/swimming and medium forces, vegetation/flexibility/wind, terrain/buildings, liquids/deformable solids, animation transitions, live engines, measured scale/performance, and a documented direct-tool authoring comparison. Finishing reach will not complete those domains.

The prior [main status](https://github.com/Omegapy/OntoKin/blob/2bb4588e121fcfe99b4d42c734b15b38362f3642/STATUS.md) and [C058 continuation status](https://github.com/Omegapy/OntoKin/blob/8d17f369dadf4db038d72577112e8669e10ae55b/STATUS.md) preserve their historical evidence and limitations unchanged.
