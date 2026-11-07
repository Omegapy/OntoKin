# OntoKin development status — C164

## Current checkpoint

Given two independently named elbows of the same class, Agent/0.11 connected the straight duct to the requested outlet in one editable source change. Its inlet started 0.375 m from the bypass and 4.018 m from the requested elbow. The repaired rims match within 0.56 µm and share 0.99999970 m² of clear opening. A flush fit to the bypass failed the requested joint by 4 m. An unknown or ambiguous selection preserved the accepted revision. [Run the example and compare the three exports](examples/connected-duct/README.md#c164--select-one-of-two-identical-elbow-outlets)

[PR #101](https://github.com/Omegapy/OntoKin/pull/101) merged at [00ef2e3ee7e9](https://github.com/Omegapy/OntoKin/commit/00ef2e3ee7e977538f2199dabeb18e72addd34d3). The clean merge reproduced the earlier duct controls and passed 36 duct tests, 27 C164 selection probes, 137 framed-loft tests and all 69 stock acceptance cases. The next authoring task is to fit both ends of one editable straight to two named stationary ports and reject a span the straight cannot bridge. The [C160 torque release obligations](docs/engineering/torque-verification-c160/README.md) remain open.

Owner `c164-selection-91b3` releases the main integration lease on verified publication of this record.

## Previous checkpoint at C163

Agent/0.11 placed a mispositioned straight duct against the named elbow outlet from the delivered GLB. It measured the two mating frames and changed one placement declaration. The initial gap was 0.375 m and the axis was tilted 12°. Both complete rims now agree within 0.56 μm, and the shared opening measures 0.99999970 m². The elbow declaration and imported parts module retain their source identities. [Run the example and view the before and after close-ups](examples/connected-duct/README.md#place-the-straight-duct-from-its-exported-geometry)

[PR #100](https://github.com/Omegapy/OntoKin/pull/100) merged at [118fa7803fa8](https://github.com/Omegapy/OntoKin/commit/118fa7803fa8447d28ea6cb1d66d5fc1b409789c). On the clean merge the fixed and oblique examples reproduced their reference artifacts. All 25 duct tests, 17 independent placement probes, 137 framed-loft tests and 69 stock acceptance cases passed. The next task is to select a named outlet among repeated part instances and reject a flush connection to a decoy. The separate torque A08 release obligations remain open.

Owner `c163-port-fit-87b67246` releases the main integration lease on verified publication of this record.

## Previous checkpoint at C162

An Agent can now verify and repair the stationary duct joint at either of two authored placements. In the translated and rotated assembly, a 0.25 m local bore shift reduced the measured shared opening from 0.99999948 to 0.74999978 m². Reversing that one source edit restored all 49,736 bytes of the nominal model. The checker measures the exported triangle winding and complete inner and outer boundaries in the chosen port frame. [Run the example and inspect both views](examples/connected-duct/README.md#move-the-assembly-and-repair-the-same-opening).

[PR #99](https://github.com/Omegapy/OntoKin/pull/99) integrated at [3e8168e006df](https://github.com/Omegapy/OntoKin/commit/3e8168e006df61db167367426d9b11e9276d30bf). On the merge, the six C161 controls reproduced their original artifacts and outcomes, all 35 example exchanges passed schema validation, and all 12 joint and 137 existing framed-loft unit tests passed. The stock 0.11 acceptance suite passed 69 cases and 1,036 assertions. Both transformed views passed Khronos validation. The next authoring task is to place a mispositioned straight duct against a named outlet using frames recovered from exported geometry. The separate finite-torque A08 release gates remain open.

Owner `c162-placement-140b63d6` releases the C162 main integration lease on verified publication of this record.

## Previous checkpoint at C161

C161 adds a stationary hollow elbow and straight duct with a shared editable bore. A 0.25 m shift kept their 2 m exteriors aligned but reduced the common opening from 1.00 to 0.75 m². Agent/0.11 repaired the shift and reproduced the original 49,504-byte GLB. An out-of-bounds 2 m edit preserved the prior accepted source and artifact. Six direct exports and three Agent exports produced the expected joint checks. The wider pair measured 1.5625 m². Rolling the straight part 90° passed. Shrinking its bore or tilting its axis failed. [Source, replay and measured views](examples/connected-duct/README.md)

[PR #98](https://github.com/Omegapy/OntoKin/pull/98) integrated the example, checker and tests at [990561c31a45](https://github.com/Omegapy/OntoKin/commit/990561c31a4514c4639cd3b4e42afb702479f008). The seven new regression tests follow the original A08 prelude in discovery order. The next authoring task is to verify and repair the joint after translating and rotating the entire assembly. The separate A08 release gates below remain open. Owner `c161-duct-5e6eedd3` releases the integration lease on verified publication of this record.

## Previous checkpoint at C160

C160 retained the reference class-attribute guard. In a real simulator tick the faster membership expression missed the caller’s exception and charged one operation. A fallback that inspected monitoring introduced a different observable call. The original A08 Agent export timed out at 30.001 s. Its 80-second control published at 35.588 s and passed all 13 reads. Chromium and VTK sampled the rebuilt original clip. A separately tested Agent/0.11 duct example gives C161 a starting point for joining and repairing two editable 3D parts. [C160 probes, measurements and authoring pilot](docs/engineering/torque-verification-c160/README.md)

Owner `c160-guard-1aaa4982` releases the integration lease on verified publication of this record. [Previous simulator investigation](docs/engineering/torque-verification-c159/README.md)

## Integrated development baseline at C156

[The C156 product merge](https://github.com/Omegapy/OntoKin/commit/900f271db4cc0fb057971b2456deb14ac46fedc4) integrates the service-entrance checker and the opt-in finite-torque implementation. The reference package version is 0.4.0. Earlier default source, Agent and GLB behavior passed direct comparison with the previous main. The existing release gates remain open as recorded below.

[Service-entrance PRs #94](https://github.com/Omegapy/OntoKin/pull/94), [#96](https://github.com/Omegapy/OntoKin/pull/96) and [#97](https://github.com/Omegapy/OntoKin/pull/97) are integrated. All seven steps of the original PR #97 worker passed on Linux x86-64 with CPython 3.12.14. An independent checkout verified all 3,988 baseline methods in order and the same 16 pending external cases. The worker ran under observation on a temporary host. On the product merge, all seven focused tests passed, all 22 CLI cases matched, the checker rejected all 13 corrupted exports, and both renamed scenes passed.

[Finite-torque PR #90](https://github.com/Omegapy/OntoKin/pull/90) adds explicit source, Agent and recorded GLB 0.22 for development. The combined preview passed all 3,988 legacy methods and produced 52 legacy GLBs byte for byte. Its expanded unit run exercised 4,163 methods and reported zero failures, errors or skips. All 13 original A08 read methods passed in this suite, which requires the preceding export to complete within 30 seconds. Three standalone attempts on the identical fixture exceeded that deadline before any read method could start. A separate standalone invocation produced the original 2,447,148-byte GLB (SHA-256 `6911a4921133841df9b12e308c59b89b9ef4b5219f604751c6de2861410564aa`) and passed all 13 methods. The separately configured 80-second export produced the expected 2,447,148 bytes and the 13 read checks passed with a 30-second caller cap. Full one-byte transfer, independent playback, external destination checks and release qualification remain open. [Prior measurements](docs/engineering/torque-verification-c104/README.md)

The C133 [index](https://github.com/Omegapy/OntoKin/blob/cf95177318f174053b16d5e4f51d8f2fbacd7542/RETAINED-HEADS.json) preserves older branch tips. At the owner's request to reconcile every branch, C156 records that index commit as historical ancestry and keeps its one-file tree out of the product checkout. Owner `interactive-c156-branch-integration` releases the integration lease on verified publication of this record.

## Branch integration at C133

[PR #91](https://github.com/Omegapy/OntoKin/pull/91) added the first agent edit to the [README](README.md#try-an-agent-edit). At the [main merge](https://github.com/Omegapy/OntoKin/commit/18854eb7d7a0a615596920cff2444906b5b1f39e), the documentation checker passed and the scripted edit passed all 18 checks across 41 operations on Linux x86-64, CPython 3.12.14. Its 125,892-byte animation matched the reviewed candidate byte for byte. The independent newcomer playback trial remains open.

[PR #92](https://github.com/Omegapy/OntoKin/pull/92) integrated the native-reader verification setup into the [torque development branch](https://github.com/Omegapy/OntoKin/commit/70bd425b53ab01fd65ab7e19cc52198c60b9d4ab). The merged setup passed the decoder preflight, 11 test methods, 47 subtests and the documentation checker. [PR #90](https://github.com/Omegapy/OntoKin/pull/90) remains draft. The [retention index](https://github.com/Omegapy/OntoKin/blob/cf95177318f174053b16d5e4f51d8f2fbacd7542/RETAINED-HEADS.json) preserves the original work heads for #91 and #92.

[PR #94](https://github.com/Omegapy/OntoKin/pull/94) remains draft at `fe6a9dd23511916f49dc52fc9c5854a8108b95e0`. Its next gate is one complete seven-step run on a persistent Linux x86-64 runner. The two interrupted attempts together cover 2,611 distinct methods out of 3,988. Neither has a complete stock step or worker exit. After a passing audit, reconcile the README, first-use documentation and STATUS changes on current main before integrating the service checker.

## Service-entrance checkpoint — C127

[PR #93](https://github.com/Omegapy/OntoKin/pull/93) integrated the [editable service entrance](examples/service-entrance/README.md) at [`9ce0df0e5de0`](https://github.com/Omegapy/OntoKin/commit/9ce0df0e5de0fa84afa93ab78f17f62dbd951275). Both the visual and agent guides lead to its source. On Linux x86-64 with CPython 3.12.14, both fresh builds reproduced the accepted source bundles and animated GLBs from C126 byte for byte. The 0.58 m cart cleared the gate and post by 0.46 m per side. The 0.90 m edit left 0.30 m per side. Both used the pinned [simulation runtime](https://github.com/Omegapy/OntoKin/commit/3a1cd5785a9dd0c64d9b74ef97cdc5e6b609b117). Mesh measurements, independent playback and the documentation check passed at the merge.

On reviewed candidate `88c2fd9fada027c8090f671af1bc381fcc301f9b`, one complete stock core run passed all 3,988 original methods with zero skips, plus source, agent, construction, surface, impulse and documentation checks. Sixteen external conformance cases remain pending. The C127 handoff preserves the two failed C126 runs and the fresh logs. This example is integrated development. The human first-use study, native-platform coverage and finite release gates remain open. The next proposed agent trial adds a second independently parked cart from the repository entry point.

## Earlier contract checkpoint — C090

[C090](docs/engineering/finite-torque-contract-2026-11-02-c090/README.md) completes the finite-torque contract and independent input freeze selected by C089. The reviewed [adoption](docs/language-design/torque-v0.1/ADOPTION.md) fixes explicit source `0.22` / `torque-0.1`, Agent/0.22 and recorded GLB/0.22 bindings. **Torque runtime implementation and release remain unfinished.** The [C091 task](docs/engineering/finite-torque-contract-2026-11-02-c090/NEXT-TASK.md) implements and executes the complete frozen obligations; it does not repeat the utility review or silently alter the frozen expectations.

The global input manifest binds **399 files / 12,256,793 bytes**, SHA-256 `98df30158c0cd77c542d89652f5dec6b585d03451a06bf7b1baffee0fc2f02eb`. It fixes signed Cartesian world-axis couples on a free homogeneous sphere, canonical rounding and reference/error transport, sticky axis and split-rotation transactions, current authority and real work charges, source repair and all twelve Agent transports, actual reach-recording error allocation and a separate controlled .22 destination. Earlier source, Agent, recording and default meanings remain unchanged.

## Implementation at C088

[C088 bounded keyed membership](docs/engineering/keyed-membership-2026-11-02-c088/README.md) was the implemented increment at source `7b6900baa0357ab96c4639ac5c2ebe4e1791833e`, tree `1a31d387795b0b794935b81d9f77803054e82699`. Source `0.21` / `keyed-membership-0.1`, Agent/0.21 and recorded GLB/0.21 provide bounded read-only `has_key(collection, query) -> Bool` and sparse component overrides. Immutable bundle/files remain `0.2`.

C088's identified evidence retains 3,988 unit tests, 106 force-Agent tests, its complete 34-role inherited invocation and directly reviewed captures. Its earlier 900-second unit timeout remains failed. C087's original 33-role pass and separate documentation recovery remain distinct from a single passing full invocation. C089 supplied the separate utility/contract review; C090 does not relabel any older runtime cohort as fresh torque validation.

## Actual C090 evidence and integration

The [validation summary](docs/engineering/finite-torque-contract-2026-11-02-c090/VALIDATION-SUMMARY.json), [independent reviews](docs/engineering/finite-torque-contract-2026-11-02-c090/REVIEW-MATRIX.json), [publication](docs/engineering/finite-torque-contract-2026-11-02-c090/PUBLICATION.json) and [integration](docs/engineering/finite-torque-contract-2026-11-02-c090/integration.json) distinguish design proofs, synthetic schema probes, actual predecessor execution and future .22 acceptance. Independent mathematical/source review, actual-reach recording derivation, Agent/state/recording schemas, corpus/native/quaternion checks and the exact adoption binding passed their identified final attempts. Initial defects, failed harnesses, their original inputs and subsequent corrections remain separately retained.

The untouched C088 preflight passed **15 selected roles**. Its independent native reader passed 1,229,089 checks and Agent reader 31,006, including actual closed SQLite observations. All 10,792 predecessor source files / 669,367,315 bytes and native modes remained unchanged. This selected CPython 3.12.14 check does not replace the full inherited release cohort or missing interpreter/destination roles.

All 31 newly authored torque-free .21 physical controls passed construction and both-side common-clock state evaluation. Their default-budget artifact batch remains **failed**: 27 GLBs passed; p03/p19/p20 exhausted the unchanged 100,000-operation cap and p28 reached the inherited independent-spin refusal. Four supplemental language/marker constructions passed in their final identified attempts; earlier invalid articulated drafts remain failed. Separately named future delivery/workflow inputs fix source and validation-host settings at 1,000,000 operations / 30,000 ms. This predetermined allocation is not observed .22 success and does not raise an old gate.

Published adoption/input candidate `754f72106279abc6c867ab180300f2ba382a3f2d`, tree `693ad3ad6cf176b6b645d2edda3468673d5cae52`, passed actual remote byte/mode readback for all 1,255 changed paths: 533 unique blobs / 19,062,747 bytes. Failed raw HTTP attempts and unsupported large/binary file-response probes remain failed; successful separately identified responses supplied the actual bytes. The evidence-only follow-up `133cff003287ccda44760b95871ed76a5b39b646` preserved every adopted input.

[PR #89](https://github.com/Omegapy/OntoKin/pull/89) merged at `b193828ba7e08439f04344405e732c57b3ff75a4`, tree `72116c83bc5ac3b2c17886384030ab3e52a10978`, with ordered parents the actual integration lease and reviewed evidence candidate. Resulting-main source preservation, independent frozen-input/runtime preservation and the focused documentation checker passed their recorded exact revisions. This closing publication changes only coordination/evidence and preserves all adopted bytes. Runtime, tests, inherited schemas/tools/workflows, prior contracts and gates remain unchanged.

## Ownership and handoff

**C133 integration lease release.** Owner `interactive-c133-first-use-20261106` releases the lease after verified publication and readback of this STATUS-only commit. The lease at `e40cfc2935a9c42402b9771b24c7476eb968b720` covered PR #91 from 2026-11-06T03:11:07Z to 2026-11-06T03:41:07Z. The actual merge and its verification are recorded above.

**C127 integration lease release.** This closing update releases `interactive-c127-service-entrance-20261105T185655Z` on verified publication and readback of its STATUS-only commit. The lease began at `2026-11-05T18:56:55Z` with expiry `2026-11-05T19:26:55Z`. PR #93 is merged and both builds were verified at `9ce0df0e5de0fa84afa93ab78f17f62dbd951275`. Consult actual main, open PRs and current ownership before further integration.

This expected-head closing publication releases owner `interactive-c090-torque-contract-20261102-7of9`'s main integration lease only after actual main and exact STATUS readback. Its recorded interval is `2026-11-02T21:45:28Z` through `2026-11-02T22:15:28Z`. The standalone closing receipt identifies final head/tree and effective release. A saved status is not proof of current remote ownership; reconcile actual refs, branches, PRs and CI before C091.

No hosted job or continuation schedule was started. Workflows remain manual-only with default-false opt-in. Historical October 19 Actions failures are not current-source evidence; no repository-wide Actions setting is inferred. [Issue #26](https://github.com/Omegapy/OntoKin/issues/26) remains the broader open handoff.

The [recovery disposition](docs/engineering/finite-torque-contract-2026-11-02-c090/RECOVERY-DISPOSITION.md) retains the passing C089 v2 archive recovery and all earlier failures. The standalone C090 ZIP carries complete current source, every captured native object, exact refs and both disclosed shallow boundaries, current contract/preflight/review evidence, and unchanged recovery tools. It does not recursively reproduce every older transient workspace or claim complete earlier history. Final sealing and fresh archive recovery are separately recorded closing observations.

## Preserved gates and full goal

The [retained gate record](docs/engineering/finite-torque-contract-2026-11-02-c090/RETAINED-GATES.md) remains exact. Original28 is **24/28 passed, overall failed**, with **P11/P16/P23/L03 unresolved**. Sixteen external cases remain construction C20; surface M01–M09/M11/M12; impulse I07/I09/I11/I12. New Python 3.11/3.13 coverage remains unexecuted. M1 is rejected; comparison accounting/passive authority are open; C035 remains held, including adverse timing. C057 and complete reach remain open, including all 28 recordings, ten Agent artifacts, interpreter coverage, independent roles and R01–R12/Q01–Q22.

C068 is unadopted, C069 rejected, C070 unselected and C071 rejected. C059/C084/C085 storage causes remain unestablished; historical Git LFS migration remains unfinished. Three original C080 artifacts and complete earlier history remain unavailable; C080-R2 is separate replacement evidence. All original failures and separate recoveries retain their meanings.

Preserve `.ok` authority, immutable revisions, stable identities, units/frames, ownership/following/connections, one motion authority, represented mass and honest state transfer. Ordinary defaults remain **100,000 operations / 30,000 ms**, CLI Agent/0.1, Python ProgramAgentService/0.2 and GLB/0.1. Larger requests need current host authority; caller caps only reduce work. Original fixtures, horizons, rates, equations, helpers, oracles and tolerances remain fixed, including 32,768-bit operands, the 256-entry numerical cache and 64-step cursor.

Retain every GOAL domain: typed algorithms and reusable libraries; appearance and skin deformation; forces, contacts and general dynamics; mechanisms and vehicles; articulated creatures and purposeful movement; flight/swimming; vegetation/wind; terrain/buildings; liquids/deformable solids; animation transitions and live engines; scale/performance and direct-tool authoring comparisons. Unreal import, live destination physics, hidden geometry and measured authoring benefit remain unverified. Complete experimental releases and full-product acceptance remain open.
