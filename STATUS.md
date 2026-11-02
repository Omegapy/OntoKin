# OntoKin status

## Current development checkpoint

OntoKin's [GOAL](GOAL.md) is an AI-agent programming language for editable, reusable 3D objects, animation and physical behavior through authoritative `.ok` source. Finite increments do not complete that mission.

**C089 finite-torque utility and contract review is integrated through [PR #88](https://github.com/Omegapy/OntoKin/pull/88).** The [decision](docs/engineering/finite-torque-review-2026-11-02-c089/DECISION.md) is GO to a complete versioned contract and independent input freeze for Cartesian fixed-axis signed-scalar torque on free homogeneous spherical carriers with asymmetric massless markers. Torque syntax, a new source/Agent/GLB profile, runtime implementation and a torque release remain **unadopted/unimplemented**.

The review establishes concrete design obligations: persistent axis admission through zero and reversal; legacy motion until the first committed boundary with nonzero canonical angular acceleration, including completion of a cancelling interval; separate rotation state with preserved translation; ordered atomic boundaries; acceleration-aware and radius-aware bounds in the actual reach recorder and independent reader. The [independent addendum](docs/engineering/finite-torque-review-2026-11-02-c089/utility-review-addendum-01.md) defines exact comparison classes and offset-marker delivery requirements. The next unit writes the specified adoption artifacts; it does not repeat the utility review.

## Last implemented capability: C088

[C088 bounded keyed membership](docs/engineering/keyed-membership-2026-11-02-c088/README.md) remains the latest implemented increment, integrated through [PR #87](https://github.com/Omegapy/OntoKin/pull/87) at final source `7b6900baa0357ab96c4639ac5c2ebe4e1791833e`, tree `1a31d387795b0b794935b81d9f77803054e82699`. Explicit bindings are source `0.21` / `keyed-membership-0.1`, Agent/0.21 and recorded GLB/0.21; immutable bundle/files remain `0.2`. `has_key(collection, query) -> Bool` supports bounded read-only membership and sparse component overrides. Earlier meanings and defaults remain unchanged.

C088's [validation record](docs/engineering/keyed-membership-2026-11-02-c088/VALIDATION-SUMMARY.json) retains its 3,988 unit tests, 106 force-Agent tests, complete 34-role inherited invocation, independent source/Agent/native checks and directly reviewed captures. Its earlier 900-second unit timeout remains failed. C087's original 33-role pass plus separate documentation recovery remains distinct from a single passing full invocation. C089 did not rerun or relabel those runtime cohorts.

## Actual C089 evidence and integration

The [C089 engineering record](docs/engineering/finite-torque-review-2026-11-02-c089/README.md), [validation summary](docs/engineering/finite-torque-review-2026-11-02-c089/VALIDATION-SUMMARY.json) and [integration record](docs/engineering/finite-torque-review-2026-11-02-c089/integration.json) bind the review and actual commands. Independent mathematical scripts reproduce **663 ideal-model arithmetic assertions** and a separate **16-assertion canonical-input correction** on CPython 3.12.14. These are design witnesses, not production torque tests or an adopted release corpus. The original nondyadic diagnostic remains unchanged; the current review explicitly uses dyadic clocks for source-representable rounding witnesses.

Independent review verified all 10,839 files in the first candidate tree and found no integration blockers. The only changed predecessor path was the additive `docs/README.md` entry; runtime, tests, schemas, tools, workflows and existing contracts/gates remained exact. Published candidate `47050d893728ae86e5241be3f758afd3b0c0945d`, tree `539e247e81ded3f1cedf2fdb23c0d8b930f15f93`, adds only the subsequent review/check records and their summaries.

The actual merge is `cb0bc0dee8b473db20d379f2d78670e3267b3968`, tree `174d50f40a440f38156328c09516e5a81e3d9fc4`, with ordered parents lease `66f0f5928860c221e04c78f50fe95def14d5fdd5` and the exact candidate. Its only difference from that candidate is the lease STATUS. Fresh resulting-main documentation validation passed **29 preserved sources / 233 sections, zero failures**. All 10,842 tracked files matched their native tree and remained unchanged during the check. Documentation-only validation follows the adopted local policy; no new runtime or destination evidence is claimed.

The first native merge-import attempt remains failed. A separately identified reconstruction retained the original signed payload's trailing signature newline and reproduced the already observed GitHub commit hash exactly. This correction changed no remote merge, source file or expected result.

## Ownership and handoff

This expected-head closing publication releases owner `interactive-c089-torque-review-20261102-813f`'s main integration lease only after actual main and exact STATUS readback. Its recorded interval was 2026-11-02T20:10:16Z through 2026-11-02T20:40:16Z. The standalone closing receipt identifies the final head/tree and effective release; a saved status is not proof of current remote ownership. Reconcile actual refs, branches, PRs and CI before new work.

No hosted execution or continuation schedule was started. Hosted workflows remain manual-only with default-false opt-in. Historical October 19 Actions failures are not current-source validation, and no repository-wide Actions setting is inferred. The broader [Issue #26](https://github.com/Omegapy/OntoKin/issues/26) remains open.

The original C088 archive passed its exact member verifier, but its original full recovery in this session failed an inherited directory-inventory check. The separate source/native recovery passed every one of 10,792 source files and all 10,255 native objects/205 commits, including exact refs and both shallow boundaries. See the [recovery disposition](docs/engineering/finite-torque-review-2026-11-02-c089/RECOVERY-DISPOSITION.md). The new single-ZIP checkpoint carries complete current source, captured native history and C089 evidence once; it does not reproduce every old transient validation workspace. Final sealing, fresh ZIP recovery and durable delivery are separately recorded closing observations.

## Preserved gates and full goal

The [inherited gate record](docs/engineering/finite-torque-review-2026-11-02-c089/RETAINED-GATES.md) is carried by identity; its older checkpoint wording is historical. Accepted finite core, construction, surface, impulse and center-of-mass force releases retain their meanings. Explicit reach through `.21` membership remain experimental capabilities separate from complete release acceptance.

Original28 remains **24/28 passed; overall failed**, with **P11/P16/P23/L03 unresolved**. Sixteen external cases remain construction C20; surface M01–M09/M11/M12; impulse I07/I09/I11/I12. New Python 3.11/3.13 coverage remains unexecuted. M1 is rejected; comparison accounting/passive authority are open; C035 remains held, including adverse timing. C057 and complete reach remain open, including all 28 recordings, ten Agent artifacts, interpreter coverage, independent roles and R01–R12/Q01–Q22.

C068 is unadopted, C069 rejected, C070 unselected and C071 rejected. C059/C084/C085 storage causes remain unestablished; historical Git LFS migration remains unfinished. Three original C080 artifacts and complete earlier history remain unavailable; C080-R2 is separate replacement evidence. All earlier failures, separate recoveries, unavailable transient bytes and both disclosed shallow boundaries retain their recorded meanings.

Preserve `.ok` authority, immutable revisions, stable identities, units/frames, ownership/following/connections, one motion authority per coordinate, represented mass and honest state transfer. Defaults remain **100,000 operations / 30,000 ms**, CLI Agent/0.1, Python ProgramAgentService/0.2 and GLB/0.1. Larger requests need current host authority; caller caps only reduce work. All original fixtures, horizons, rates, equations, helpers, oracles and tolerances remain fixed, including 32,768-bit operands, the 256-entry numerical cache and 64-step cursor.

Retain every GOAL domain: typed algorithms and reusable libraries; appearance and skin deformation; forces, contacts and general dynamics; mechanisms and vehicles; articulated creatures and purposeful movement; flight/swimming; vegetation/wind; terrain/buildings; liquids/deformable solids; animation transitions and live engines; scale/performance and direct-tool authoring comparisons. Unreal import, live destination physics, hidden geometry and measured authoring benefit remain unverified. Complete experimental releases and full-product acceptance remain open.

## Next unmet task

[C090](docs/engineering/finite-torque-review-2026-11-02-c089/NEXT-TASK.md) must complete the versioned language/grammar, canonical numerical/transaction rules, source/Agent/delivery bindings, actual reach-recording proof, independently authored exact input freeze, and untouched predecessor preflight. Publish and read back reviewed adoption and every frozen byte/mode before torque runtime work. Include neutral COM-force controls, cancellation ending at a nonzero-acceleration boundary, fixed offset markers, source repair, current authority, cancellation, store recovery and exact artifact delivery. Earlier meanings and the full GOAL remain unchanged.
