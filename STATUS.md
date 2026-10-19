# OntoKin status

Checkpoint: **2026-10-19T11:54:34Z**. The complete [GOAL](GOAL.md) remains **in progress**. Native surface M01–M12, source impulse I01–I12 and the force source kernel are integrated. The Agent/0.5 checkpoint is implemented and tested on a published continuation branch; consolidation into [PR #14](https://github.com/Omegapy/OntoKin/pull/14), exact-head CI and integration are in progress. **GLB/0.5 and the complete F01–F12 force release are not complete.**

## Integrated finite releases

Native source 0.3 / surface-0.1, Agent/0.3 and GLB/0.3 supply parameterized loft geometry, regional PBR materials, rigid placement, source-driven animation, revision-bound triangle inspection and atomic source edits. PR #9 merged at `1a6dc3268c770d492b93e994b752c72eeb459cb0`. Original [surface evidence](docs/engineering/surface-release-validation/README.md) remains unchanged.

Source 0.4 / impulse-0.1, Agent/0.4 and GLB/0.4 supply authored off-center impulses on free homogeneous spheres, ordered release/impulse boundaries, whole-boundary rollback, bounded inspection, physical-parameter repair and recorded animation. PR #11 merged at `d25ab70a08fe5fb1e9f9a5be7a71fe6cbc99225e`. Original [impulse evidence](docs/engineering/impulse-release-validation/README.md) and [integration record](docs/engineering/impulse-release-validation/integration.json) retain their identified implementation, 40 source cases, 124 mapped methods, both 588-test inventories and independent destination/browser results. They do not certify later changed runtime bytes.

Source 0.5 / force-0.1 adds finite constant world COM-force intervals with exact completion clocks, additive final active sets, unchanged anchors when acceleration is unchanged, inherited release/impulse ordering, atomic rollback, bounded histories and valid short prefixes. Its adopted source contract and original 44 fixtures remain unchanged; twelve supplements and explicit additive errata supply 56 effective source cases without widened tolerances. Kernel implementation `cd5a6f2131b1fe2c760ab851a11c2c5b3cf119b1` passed 677 tests. PR #13 merged at `74089239eb81b3c5a335b63145b3444eccfab148`; all four resulting-main jobs passed in [39198117569](https://github.com/Omegapy/OntoKin/actions/runs/39198117569). [The kernel checkpoint](docs/language-design/force-v0.1/KERNEL-CHECKPOINT.md) and [integration record](docs/engineering/force-kernel-validation/integration.json) preserve exact source/tree comparisons and results. Do not merge PR #13 again.

Latest observed pre-lease main is `0a8f1f6908571adbd7abc31613397524b46a3c8b`; its [CI 39204919656](https://github.com/Omegapy/OntoKin/actions/runs/39204919656) passed. Its only changes after the kernel merge are STATUS and the additive kernel integration record.

## Published Agent/0.5 checkpoint

The initial implementation `f2785fff2c6655af88f596233400bf9182d3d269` remains the current PR #14 head on `work/force01-agent05-20261019-0435-astra`. It adds explicit source discovery, separate database/schema/cursor context, complete source-bound force state, atomic mass/force/duration repairs, cancellation and final-envelope budgets. Older defaults, catalogs and stores remain unchanged. The adopted OK-AGENT-005 contract makes unavailable GLB/0.5 requests fail explicitly without an artifact.

The six-file schema/workflow checkpoint was successfully published as `db50d4641264cdf69c01fbd7c73b2e39f15b3f45` on `work/force05-agent-finish-20261019-0545-astra`. Its exact source.bundle was recovered and checked against tree `283b73f701e439854a93a3614779eb0e73965230`. It is not an unavailable local-only draft.

The reviewed continuation is now published at **`f17460489d9c1bb55053a6de6d08a9fea45d5bb1`**, tree **`e4049fa291588597c56b2694c1bcdad4d20f9307`**, on `work/force05-verification-20261019-1118-astra`. This equals the complete locally tested tree. Runtime identity remains `ontokin-reference` 0.4.0, SHA-256 `ad1c473a595dc1147bfeef10330a39bbffb33cd68cc236ec70fc12b445e720ea`.

| Executed checkpoint evidence | Actual result |
| --- | --- |
| Full local regression | **733/733 passed**, zero failures/errors/skips, 267.381 s |
| Guarded publication regression | **733/733 passed**, zero failures/errors/skips, 281.796 s |
| Original source / agent cases | 43 cases / 694 assertions and A01–A10 passed |
| New adversarial and operational tests | 29 evidence/schema counterexamples plus nine transaction/CLI tests; all included in the passing full suites |
| Actual Agent workflow | 418 exchanges, 25 immutable source snapshots, 334 predetermined samples; independent audit passed with 411 force projections schema-checked |
| Documentation preservation | 29 historical sources, 233 sections, 673 local links passed |
| Guarded publication | [39246541254](https://github.com/Omegapy/OntoKin/actions/runs/39246541254), all steps passed; published code child `f0326561988ae1ff171bc620492059444874729c` |
| Retrieved publication artifact | ID 12183769150; ZIP SHA-256 `3c783a352888b429d538d9665105cb8081f964af04e668bbe43a43e67fe93067`; ZIP, source.bundle, commit/tree and logs checked |

The independent reader now binds initial/final snapshots, force histories, source manifests, frame requests, run identities and retry receipts. Five concrete rehashed corruptions were accepted by the earlier reader and are now rejected. These probes established verification defects, not a force-kernel defect. No runtime, adopted source expectation, earlier schema or historical evidence changed in this continuation. A dedicated read-only CI job installs pinned verification-only dependencies and requires actual schema/mutation tests with zero skips. The ordinary runtime remains standard-library-only.

## Exact next task

Retain the identified Agent checkpoint evidence, reconcile the published continuation with current main and PR #14, and run all required exact-head CI. Integrate the verified Agent/0.5 checkpoint using the bounded lease below, then confirm the resulting-main checks and update this record. Do not replay completed publication helpers or overwrite historical branches.

Then implement the separately specified acceleration-aware native GLB/0.5 adapter: actual source geometry/PBR, force completion boundaries, requested-prefix validity, complete source-bound force metadata, conservative translation/angular sampling, budget/cancellation parity, independent decoded intermediate-motion checks and reviewed browser captures. Run the complete retained F01–F12 release gate before declaring the finite force release complete.

Still required by GOAL: richer typed algorithms/libraries and compatible replacement; textures, mapping and skin deformation; continuous torques, contacts/collisions, general rigid dynamics and dynamic/closed mechanisms; vehicles; articulated creatures and purposeful locomotion/manipulation; flight/swimming and medium forces; vegetation/flexibility/wind; terrain/buildings; liquids and deformable solids; animation transitions, live engines, measured scale/performance and a documented direct-tool authoring comparison. Blender delivery and a generic delivered-level check are not established. Recorded GLB playback is not live physics. Visual lofts add no physical matter or motion authority.

## Integration and recovery

| Lease field | Value |
| --- | --- |
| Owner | `interactive-force05-integration-20261019-1154Z-astra` |
| Task | Retain verified Agent/0.5 evidence, consolidate PR #14 and safely integrate after exact-head checks. |
| Acquired UTC | 2026-10-19T11:54:34Z, after prior expiry and current ref/CI reconciliation. |
| Expires UTC | 2026-10-19T12:24:34Z |
| Observed main before acquisition | `0a8f1f6908571adbd7abc31613397524b46a3c8b` |
| Reserved scope | Main integration, STATUS and new Agent checkpoint evidence. |
| Recovery | Read actual main, PR #14, the f1746048 continuation, issue #12 and CI before retrying any write. Preserve completed commits. PR #13 and the earlier impulse/surface releases are already merged. |

[Previous main checkpoint](https://github.com/Omegapy/OntoKin/blob/0a8f1f6908571adbd7abc31613397524b46a3c8b/STATUS.md) retains earlier recovery details. [Issue #12](https://github.com/Omegapy/OntoKin/issues/12) and PR #14 retain work scopes and handoffs. No other worker is claimed active. The owner intentionally disabled **Advance OntoKin**; no automation was changed or reactivated. Attachment and stream errors do not change repository state.
