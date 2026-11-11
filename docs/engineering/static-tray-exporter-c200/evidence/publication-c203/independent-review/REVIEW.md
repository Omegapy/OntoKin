# C203 independent review of the C200 integration candidate

**Decision: APPROVE the exact candidate for experimental development integration.** No code or evidence blocker was found against the observed main below. This review does not claim that publication, merge, or resulting-main verification has occurred. It does not authorize another C199 or C200 execution or claim a complete release.

## Exact identity and scope

| Item | Reviewed identity |
| --- | --- |
| Candidate commit | `125353836119e50215287c27d80e99cef6d85e8f` |
| Candidate tree | `b0e62bdefcb9afd1ea0708ba2b5ab459f457fbcd` |
| Candidate parent / fresh CPU-check source commit | `16c736c522c1f3684b5baabe6e72e56536ef08ce` |
| Observed main used for cumulative comparison | `2cad7ecfece83295a3534d8afc97ab127a665ded` |
| Previously executed C200 source commit | `62b2316cc3f88db187f69fbd7fdb2cf0997a97de` |
| C200 immutable input-lock SHA-256 | `e22d12703926740c2c4cb8596781192b9f0412836e3fba7c6f353bedfc60e0e0` |
| Candidate state | Clean at the start and end of the independent audit, and at final readback |

The review covers the cumulative candidate changes, including inherited implementation and protocol tools, rather than only the latest documentation commit. The reviewer did not author the implementation or historical qualification. The reviewer did author the new missing-log recovery manifest and preliminary C201 admission design. Verification of those particular artifacts is a self-check; it is not independent approval of their authorship. The design remains preliminary and is not part of the executed C200 protocol.

## Implementation and containment

The existing product-source delta is limited to three files in the explicit `prototypes/static_tray_v01` entry path:

- `export-settings.json` selects exporter log level `-1` in place of the incompatible positive value.
- `worker.py` verifies the pinned Blender exporter source, exact operator properties and actual INFO logging policy; initializes the pinned exporter's empty action-filter properties; records startup before export; uses the explicit execution path; and requires the expected cleanup and successful export receipt. It rejects unexpected debug settings, action state, preexisting filter properties, source changes and logger behavior.
- `qualification.py` changes the scope wording to identify the exact cohort through its input lock. It does not change geometry, limits, budgets, slot counts, or qualification behavior.

The qualified worker, exporter settings and all other executable inputs are byte-identical to the executed C200 source. The new exporter tests exercise positive, rejection and failure-receipt paths, including five tests against the exact pinned upstream source. Native geometry construction, canonical frontends, the artifact reader, receiving checks, and existing limits are unchanged.

The separate C200 coordinator, preparation and inventory tools were reviewed. They bind the new revision, consumed C199 evidence, source lock and independent approval; refuse an already-used invocation; retain failures; and do not convert an incomplete result into qualification. Handoff import code is unchanged from C199; its other tool differences are the C200 namespace and paths. Preserved capture and review scripts are historical evidence, not fresh executions.

The cumulative diff contains 465 paths. Outside the C200 directory and new C200 test, modifications are the three prototype files above plus README, documentation navigation and STATUS. Main runtime, schemas, grammar, fixtures, conformance tools, dependency configuration and workflows have exact unchanged identities. Main runtime and workflow entry points do not import or route through this experimental tray path. This establishes an actual entry boundary and avoids silently changing previously released behavior. Workflow execution policy is unchanged.

## Preserved qualification evidence

The independent mechanical audit in `CONTENT-AUDIT.json` passed all of these checks:

| Evidence | Verified result |
| --- | --- |
| Locked inputs | All 301 sizes and SHA-256 hashes match the immutable C200 lock and the fresh tested-source manifest |
| Original C202 overlay | All 303 files, 51,356,757 bytes, and recorded modes are preserved |
| Captured execution archive | Hash, size, all 2,565 member identities, modes and kinds match; 1,704 regular files total 60,009,373 bytes |
| Direct receipt copies | All 329 copies match their archived bytes |
| Final-review evidence references | All 26 explicit path, size and hash bindings resolve to preserved candidate bytes or archive members |
| Actual ledger | 60 events, with 12 each of RESERVED, STARTED, BUILT_PENDING_RECEIVING, RECEIVING and ACCEPTED |
| Actual C200 result | 12 accepted native transactions, 12 receiving starts, 12 actual delivered-artifact Node checks, 9 delivered controls, 12 reviewed images, and zero retries |
| Prior failure | One failed C199 native start remains recorded; the combined historical native count is 13 |
| Result-state history | The original raw `qualified=false` and later independently reviewed `qualified=true` are both preserved |

The original distinction between execution and later review is essential: the raw coordinator was not rewritten to look qualified. Historical result and numeric reviews remain bound to the exact artifacts. No new native, receiving, Node, lifecycle or author run was made by this reviewer.

### Nine recovered preparation logs

All nine files were found at their recorded original workspace paths and recovered unchanged, totaling 2,707 bytes. The synthetic `tests.log` has a matching historical individual hash and size. The other eight streams have newly recorded recovery-time hashes. Six streams are corroborated by retained process receipts, original jobs, probe results and observed byte counts; the driver's two streams have weaker correlation to exact retained driver receipts and do not have a historical standalone hash or byte count.

Those eight current hashes establish identity from recovery onward. They do not establish that historical per-stream hashes ever existed. In particular, the two previously inferred driver filenames are now observed files, while their weaker historical provenance remains explicit. Original C202 package missingness is unchanged. This residual uncertainty concerns preparation stream preservation; the decisive native qualification archive, approval, ledger and final reviews already have retained historical bindings. It is therefore a documented limitation rather than a blocker to this exact integration.

## Applicable fresh checks and legacy failure accounting

Fresh reports under `docs/engineering/static-tray-exporter-c200/evidence/publication-c203/checks/` record CPython 3.12.14 on Linux x86-64:

| Cohort | Observed result |
| --- | --- |
| Focused prototype/exporter controls | 107 passed; zero skips; includes all five exact pinned-exporter source tests |
| Compiler controls | 47 passed; zero skips |
| C200 protocol controls | 10 passed |
| Core conformance | 43 cases, 694 assertions, zero failures |
| Documentation preservation and links | 29 sources, 233 sections, 4,106 local links; zero failures |

The CPU checks ran at parent commit `16c736c522c1f3684b5baabe6e72e56536ef08ce`, with additional evidence files present in the worktree. The final candidate adds documentation and evidence. All 301 actual tested locked inputs match the final committed candidate; executable code also matches the previously executed C200 source. Reuse is based on those exact input identities, not a branch label.

The observed fresh focused/compiler/protocol child-process audit records eight ordinary Python reader CLI children and six Git metadata reads, with zero protocol children and zero unexpected blocked children. The unchanged runner's statement that focused tests start no subprocess is imprecise; the published check report explicitly corrects it. Core conformance ran directly and was not covered by that subprocess instrumentation. No blanket claim of zero subprocesses is made. No Blender, Node, receiving, lifecycle, timed-author or new qualification execution occurred in these fresh checks.

The historical full legacy suite remains **FAILED**: 4,239 distinct passing methods, with 13 torque-read methods NOT RUN after the unchanged 30,000 ms setup timeout. It was not rerun and is not represented as passing.

Under `OK-ENG-009/0.1.0` section 3 and `OK-ENG-006`, the required regression scope follows the actual shared behavior affected by integration. Exact comparison shows no change to shared language, numerical, Agent, delivery, core runtime or workflow machinery. The changed behavior is the explicit experimental tray exporter, covered by preserved source-built native evidence, independent artifact reviews, fresh exporter failure controls, compiler controls, protocol controls and core conformance. The legacy timeout therefore remains an unchanged incomplete-feature failure with no identified path into this increment. Repeating the complete failed cohort is not required for this contained change. This rationale would not apply to a subsequent change in shared machinery or to an unresolved effect on released behavior.

## Blockers, limitations and remaining integration steps

**Candidate blockers found: none.** The exact candidate is suitable for experimental development integration against the observed main. Approval does not extend automatically to additional implementation changes or to an unreviewed new base.

Material limitations remain:

- The full historical legacy suite is FAILED, and its 13 unexecuted torque-read methods stay unexecuted.
- Visual limits remain for N05/N06 minimum-tray subpixel detail and N07/N08 occluded right interior detail.
- Actual-Blender cancellation, general contact/live physics, external compatibility, comparative benefit and full release evidence are not established.
- Fresh CPU compatibility evidence covers the recorded Python 3.12.14/Linux environment only.
- Eight recovered streams lack historical individual hashes; the driver pair also lacks historical standalone byte counts.
- C201 admission has not executed. Its separate four-export protocol, source closure, independent review and fresh execution authority remain future work. C199/C200 schedules stay closed.

The integrator must still verify current main and lease ownership, publish through the expected-head procedure, and verify the actual resulting commit/tree and applicable resulting-main checks. Any later evidence-only review commit should preserve the reviewed executable and locked inputs exactly. A changed base or source requires a new scope assessment. This approval is not a claim that those external integration steps have already succeeded.

## Audit artifacts

- `REVIEW.json` provides the machine-readable decision and material limits.
- `CONTENT-AUDIT.json` contains per-file and per-reference identity results.
- `audit_candidate.py` records the read-only mechanical audit procedure.
- `FIRST-ATTEMPT.json` preserves an initial reviewer query failure: an overly broad Git pathspec matched newly added historical evidence scripts. The query was narrowed to top-level execution tools; no candidate file changed as a result.

Repository evidence anchors are `EXECUTABLE-INPUTS.json`, `evidence/result-review/RESULT-REVIEW.json`, `evidence/native-execution/MANIFEST.json`, `evidence/publication-c203/FRESH-LOG-RECOVERY.json`, `evidence/publication-c203/checks/CHECKS-SUMMARY.json`, `evidence/publication-c203/checks/TESTED-SOURCE-MANIFEST.json`, `evidence/publication-c203/checks/SOURCE-COVERAGE.json`, and `evidence/publication-c203/DOCUMENTATION-CHECK.json`, all under `docs/engineering/static-tray-exporter-c200/`.
