# OntoKin status

Checkpoint: **2026-10-18, interactive timeout recovery in progress**. The complete [GOAL](GOAL.md) remains **in progress**. Follow [AGENTS](AGENTS.md), inspect the actual remote head, and respect the integration lease below.

## Verified published baseline

The installed experimental package remains **ontokin-reference 0.4.0**. Its language `0.1` / `core-0.1`, language `0.2` / `construction-0.1`, agent/0.1 and agent/0.2, and GLB/0.1 and GLB/0.2 contracts retain their existing meanings. Its Python package SHA-256 is `2fec4df8a853fb04f05981137165b093dbe5fe72abc1e49ceee15a7747bb4a24`.

The native exterior-surface contract is adopted in [OK-LANG-003](docs/language-design/OK-LANG-003-parameterized-exterior-surfaces-and-material-regions.md), but the language `0.3` / `surface-0.1` compiler, agent interface and GLB/0.3 adapter are **not implemented**. [The prototype checkpoint](docs/engineering/surface-validation/prototype-checkpoint.md) records an isolated Python-input mesh and multi-material GLB workbench. The published prototype source is `96c12d5a2bd11cc04423c497a7b134539c4e73ce`, followed by the status/lease-release checkpoint `7565694927082dacf0acfad679e9048ea52d766f`.

That checkpoint identifies [branch CI 39105285128](https://github.com/Omegapy/OntoKin/actions/runs/39105285128): four successful jobs, 294 Python tests, original source/agent/construction conformance, prior destination checks, and independent prototype GLB validation. It does not establish native M01-M12 completion or an unobserved later CI outcome.

The complete preceding STATUS, including all historical counts, hashes, CI links, prototype artifact identity, limitations, scheduling observations and release details, is preserved **byte-for-byte** in [this checkpoint snapshot](docs/engineering/surface-validation/status-20261018-0654.md.txt). The `.txt` archive retains the original relative-link text without pretending that its old Markdown links resolve in the archive directory. The [0.4.0 release evidence](docs/engineering/construction-validation/validation-summary.json) remains unchanged.

## Active recovery

The timed-out session continued saving work. A later repair attempt found that the feature branch had advanced; its expected-head update did not overwrite the newer work. The prior integration owner has now published its checkpoint and released its lease. This continuation must acquire the lease conditionally before publishing repaired source.

Local inspection reproduced mutable center/color aliases and an overbroad station-gap epsilon in the experimental kernel. Twelve new regression methods produced 20 failing assertion/subtest instances against the earlier kernel and pass against the prepared correction. Six additional methods feed the unchanged frozen acceptance inputs into the actual kernel. These 18 local tests are **kernel evidence only**; the correction has not yet passed repository CI or been integrated into main. The fixed blob, tests, and explicit numeric-boundary clarification will be applied on a separate recovery branch without altering the released `ontokin` package.

## Next actions

1. Reconcile the prepared repair with the current main and acquire the lease below through an exact-head update. Preserve the newly published prototype, tests, documentation and historical evidence.
2. Publish and verify the corrected kernel, frozen-input execution tests and explicit boundary/immutability clarification. Run full repository CI and retain the precise result before integration.
3. Continue native `0.3` / `surface-0.1` parser/type/constructor and pinned-module integration. Complete actual source revision/repair, visual placement, animation/release, agent inspection and GLB/0.3 delivery fixtures. All M01-M12 end-to-end gates remain open.

## Scope still unmet

Broader distribution, reusable algorithms/components, compatible part replacement, rich surfaces/textures/deformation, contacts and collisions, general rigid-body dynamics, forces and dynamic joints, closed mechanisms, purposeful locomotion/manipulation, and live destination behavior remain unfinished. The creature, vehicle, flight/swimming, vegetation, terrain/building, fluid/deformable, appearance, performance and agent-benefit requirements remain in GOAL. Prototype geometry adds no mass or motion authority. Existing physical support remains uniform gravity/free homogeneous spheres and prescribed connections with collisions disabled. Recorded GLB playback is not live OntoKin physics. Blender import and a generic delivered-level check are not established.

## Periodic review

The preceding checkpoint records the configured hourly **Advance OntoKin** task `6ad42d31d3ec819196dc1cc1e3ede709`. Its current scheduling-service state and review outcomes have not been reread in this recovery. The full prior observations remain in the snapshot above. A live integration lease makes independent scheduled reviews read-only; status files do not run background jobs themselves.

## Integration lease and concurrent work

| Lease field | Value |
| --- | --- |
| Integration owner | interactive-recovery-20261018-0636 |
| Acquisition base | main `7565694927082dacf0acfad679e9048ea52d766f` |
| Lease expires | 2026-10-18T08:00:00Z |
| Current task | Reconcile, harden and verify the surface prototype after the timed-out request |
| Recovery branch | fix/surface-recovery-20261018 |

This acquisition takes effect only after a successful update conditioned on the exact acquisition-base head and a confirming read. The preceding lease was explicitly released. Do not infer ownership merely from expiry or from a failed/unknown write response. If a ref moves, inspect and reconcile instead of force-overwriting another writer. The owner must renew or release this lease at meaningful checkpoints and before ending active work. Independent sessions may inspect but must not edit or publish while it is live.

## Recovery procedure

Reread GOAL, STATUS, AGENTS and the active contracts. Inspect actual main, branch heads, lease and CI. Use bounded work units with brief interactive progress updates. After any timeout or unknown write result, read the remote head and intended files before retrying. Keep evidence, limitations and the concrete next step explicit. More frequent chat messages are not a guarantee against application or network timeouts.
