# OntoKin status

Checkpoint: **2026-10-18T07:11:03Z**. The timeout-recovery correction is integrated and verified. The complete [GOAL](GOAL.md) remains **in progress**. Read [AGENTS](AGENTS.md), the actual remote head and the integration lease before continuing.

## Verified implementation and correction

| Item | Recorded state |
| --- | --- |
| Installed experimental package | `ontokin-reference` **0.4.0**, unchanged by this repair |
| Preserved source profiles | Language `0.1` / `core-0.1`; language `0.2` / `construction-0.1` |
| Preserved service and delivery contracts | Agent/0.1 and Agent/0.2; GLB/0.1 and GLB/0.2 |
| Published surface repair | [9a9ca2dea3220f67cf10a3923a794141bab03413](https://github.com/Omegapy/OntoKin/commit/9a9ca2dea3220f67cf10a3923a794141bab03413) |
| Tested repair tree | `e700fef42de62b49a0d1623e184ea5a9ecea9301` |
| Observed branch CI | [39106141202](https://github.com/Omegapy/OntoKin/actions/runs/39106141202), all four jobs passed |
| Observed main CI | [39106452741](https://github.com/Omegapy/OntoKin/actions/runs/39106452741), all four jobs passed |
| Repository test suite | 312 tests; includes 18 added recovery tests, not a new package release |
| Native surface-language gate | `0.3` / `surface-0.1` source compilation, Agent/0.3, GLB/0.3 and full M01-M12 remain unimplemented or unpassed |

The correction passed branch CI before an exact-head update integrated it into main. Main CI passed independently. This evidence/status checkpoint adds documentation only; it preserves the tested code bytes. Its own later CI run is distinct from the identified implementation runs above and must be inspected rather than inferred.

## What the recovery completed

The timed-out earlier session continued saving work. The recovery inspected actual branch state instead of replaying the interrupted batch, preserved its completed surface/export prototype, waited for an explicit lease release, and conditionally acquired a distinct worker lease.

The experimental loft kernel now snapshots validated centers and colors, applies the explicit [C1 station-boundary rule](docs/language-design/surface-v0.1/clarification-c1.md), reports malformed inputs without invoking unsafe caller conversions, and checks cancellation during final grouping. Twelve new regression methods reproduce the earlier defects and pass after correction. Six more methods exercise actual frozen acceptance inputs through the kernel. The frozen manifest and installed runtime bytes are unchanged.

[The recovery checkpoint](docs/engineering/surface-validation/recovery-2026-10-18.md) and [identified evidence](docs/engineering/surface-validation/recovery-evidence.json) record the exact work and observed checks. Branch and main CI passed Python 3.11-3.13, all original source/agent/construction conformance, independent prototype and legacy GLB validation, browser regressions and documentation preservation. The fresh 96-triangle, three-material prototype export is byte-identical to the prior demonstration, with zero reported format errors/warnings. This remains Python-input prototype evidence, not native OntoKin surface-source delivery.

AGENTS now retains the user's requested interactive procedure: brief meaningful progress updates, bounded tool calls and verified checkpoints. After a timeout or unknown write result, inspect remote heads, files and the lease before retrying. These practices do not guarantee that the application or network will maintain the response stream.

## Preserved baseline and full scope

The [0.4.0 construction evidence](docs/engineering/construction-validation/validation-summary.json) and [preceding prototype checkpoint](docs/engineering/surface-validation/prototype-checkpoint.md) remain unchanged. The complete prior STATUS at the earlier handoff is preserved byte-for-byte in [the 06:54 snapshot](docs/engineering/surface-validation/status-20261018-0654.md.txt), including historical counts, hashes, CI links, limitations and scheduling observations.

The installed Python package identity remains `2fec4df8a853fb04f05981137165b093dbe5fe72abc1e49ceee15a7747bb4a24`. No `ontokin` runtime file was changed by the recovery. The [adopted surface contract](docs/language-design/OK-LANG-003-parameterized-exterior-surfaces-and-material-regions.md) does not itself register source support.

Still unmet: broader distribution, reusable algorithms/components, compatible part replacement, rich surfaces/textures/deformation, contacts and collisions, general rigid-body dynamics, forces and dynamic joints, closed mechanisms, purposeful locomotion/manipulation, and live destination behavior. Creature, vehicle, flight/swimming, vegetation, terrain/building, fluid/deformable, appearance, scale/performance and measured agent-benefit requirements remain in GOAL. Prototype geometry adds no physical mass or motion authority. Existing physics remains uniform gravity/free homogeneous spheres and prescribed connections with collisions disabled. Recorded GLB playback is not live physics. Blender import and a generic delivered-level check are not established.

## Next actions

1. Recenter on GOAL, STATUS and AGENTS; inspect current main, CI and the lease. Acquire a new lease through a confirmed exact-head update before further edits.
2. Implement the adopted `0.3` / `surface-0.1` parser, types, pure constructors and pinned-module rules. Compile the frozen `.ok` source rather than substituting host-language geometry preparation. Preserve old profiles and exact source identity.
3. Integrate the corrected surface generator with rigid local visual placement, source-driven motion, request-wide resource/cancellation accounting and GLB/0.3 material primitives.
4. Complete revision-safe source repair, independent compositions and variants, unchanged sibling/library checks, mesh-page inspection, animation/release and destination evidence. M01-M12 remain open as full end-to-end gates.

## Periodic review

The preceding checkpoint records the configured hourly **Advance OntoKin** task `6ad42d31d3ec819196dc1cc1e3ede709`. Its scheduling-service state and review outcomes were not reread in this recovery. Historical observations remain in the snapshot above. Independent scheduled reviews are read-only while a live integration lease exists; these Markdown files do not themselves run background work.

## Integration lease and concurrent work

| Lease field | Value |
| --- | --- |
| Integration owner | None; `interactive-recovery-20261018-0636` releases its completed correction |
| Release checkpoint | 2026-10-18T07:11:03Z |
| Lease expires | 2026-10-18T07:11:03Z |
| Completed task | Reconcile, harden, integrate and verify the experimental surface prototype after the timed-out request |
| Retained recovery branch | `fix/surface-recovery-20261018` |
| Next acquisition task | Native `.ok` surface-profile compiler integration and M01-M12 acceptance |

The release takes effect when this checkpoint is published to main. Until then the preceding published recovery lease governs writers. Subsequent work requires a fresh conditional acquisition; an old owner name or an expired timestamp does not itself confer ownership. If a head changes or a write has an unknown result, inspect and reconcile instead of force-overwriting another writer. The closing worker may inspect final CI read-only after publication.
