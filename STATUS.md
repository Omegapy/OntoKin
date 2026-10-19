# OntoKin status

Checkpoint: **2026-10-19T12:18:00Z**. The complete [GOAL](GOAL.md) remains **in progress**. Native surface M01–M12, source impulse I01–I12 and the force source kernel are integrated. The implemented and tested Agent/0.5 checkpoint is now consolidated in [PR #14](https://github.com/Omegapy/OntoKin/pull/14) at `2f08ff2858a5fca3aac7cff95b3aa1ebdd823f1c`. **Its main integration is pending actual execution of the required CI checks. GLB/0.5 and complete F01–F12 are unfinished.** Repository publishing works; new Actions jobs fail before any step starts.

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

## CI execution issue and exact next actions

At current PR head `2f08ff28`, dedicated Agent run **39250099200**, job **118051507054**, failed with **steps=null**. The reference run **39250099192** likewise reports failure. Earlier evidence-retention run **39248717422**, job **118046935787**, never started a step and has no available log (BlobNotFound). The cause is not established through available connector reads. The archive helper made no source writes. Do not describe these jobs as passed, executed tests or a known billing failure. Do not bypass checks or change account settings.

When job execution becomes available, inspect the current refs and rerun the exact required PR reference and dedicated Agent checks. Retain the identified evidence archive in GitHub after reconciling the helper's expected branch head. Merge PR #14 only after required checks actually pass, then confirm resulting-main CI. No routine owner permission is missing.

Continue independent implementation of the acceleration-aware native GLB/0.5 adapter on a declared dependent branch from the identified Agent implementation: actual source geometry/PBR, requested-prefix simulation, exact force completions, complete source-bound force histories, conservative translation/angular sampling, output budgets/cancellation, independent decoded intermediate-motion checks and reviewed browser captures. Passing an export component is not completing F01–F12.

## Remaining full-product scope

GOAL still requires richer typed algorithms/libraries and compatible replacement; textures, mapping and skin deformation; continuous torques, contacts/collisions, general rigid dynamics and dynamic/closed mechanisms; vehicles; articulated creatures and purposeful locomotion/manipulation; flight/swimming and medium forces; vegetation/flexibility/wind; terrain/buildings; liquids and deformable solids; animation transitions, live engines, measured scale/performance and a documented direct-tool authoring comparison. Blender delivery and a generic delivered-level check are not established. Recorded playback is not live physics. Visual lofts add no physical matter or motion authority.

## Integration and recovery

**Main integration lease held:** `interactive-local-validation-20261019-1610Z-7of9`. Acquired **2026-10-19T16:10:23Z**; expires **2026-10-19T16:40:23Z**. Scope: integrate [PR #15](https://github.com/Omegapy/OntoKin/pull/15), its local-validation evidence and this status record. Observed main is `4737ede6967e27a42960cfaa1d46272377980a9d`; candidate code is `04622489c269695bb8c4942090935020293f590e`. The 689-test local regression passed with zero skips; the complete local visual workflow is still executing and is not yet claimed passed. Main implementation will be updated only after verification, using an expected-head nonforce update. Independent nonoverlapping branch work may continue; PR #14 and the dependent GLB/0.5 branch are outside this integration.

[Preceding detailed checkpoint](https://github.com/Omegapy/OntoKin/blob/1bc87c5e78ca736913e9a5f8bc47845ce902e7b3/STATUS.md), [issue #12](https://github.com/Omegapy/OntoKin/issues/12) and PR #14 retain scopes and handoffs. No other worker is claimed active. **Advance OntoKin remains intentionally disabled.** No automation changed. Attachment and stream errors do not change repository state.
