# C272 report: C253 edit, animation and clean-rebuild qualification

## In short

On the owner's Mac (macOS 26.6.2 arm64, CPython 3.12.13), one command ran OntoKin's existing
route on the three frozen C253 cases of the keyed-rack family:
- the route: construction-0.1 source, Agent/0.2 accepted edits, GLB/0.2 and the semantic sidecar;
- V1: 0.65 m to 0.75 m;
- V2: 0.75 m to 0.65 m;
- N1: 0.75 kg given as a length.

At the reviewed candidate's code revision `3c206ac7`, the command passed all three cases and all 24 controls. A fresh replay at the same revision produced identical results and bytes.

A scripted client made the edits; **no model took part**. The three cases come from one public,
previously used assembly family. The result qualifies this machinery on that family only. It is
not an unseen test and says nothing about authoring advantage.

## What the run showed

- **V1 and V2.** Each case started from a new store and the exact corpus source closure, with
  the corpus's program revisions. The service accepted an edit of only the selected
  occurrence's length literal, and the accepted source read back through the service equals
  the frozen endpoint byte for byte. `hinges.ok` and its digest pin were unchanged.
- **Locality, observed directly between the start and final deliveries.** Only these
  changed: the selected finger's length parameter, the selected blade's length and size, and
  its base site. Only the selected blade moved. All 16 unrelated objects, including all 11 of
  the second rack, stayed unchanged.
- **N1.** The service itself refused the candidate with `OKL-E-UNIT` (expected Length,
  received Mass) in its type phase; the record names that mechanism `compiler`. The accepted
  revision, the source and library bytes, and the baseline GLB and sidecar bytes stayed
  identical. The baseline GLB was retrieved again after the refusal. No accepted revision
  other than the start was observed after any request.
- **Scoring.**
  - The unchanged C255 checker accepted each case's observation of the actual bytes:
    `componentPass` true, no fault. Each per-property table has 100 rows, all passing.
  - All 126 delivered poses agree with the independent equations; the largest errors are
    4.8e-8 m and 3.6e-8 rad, against limits of 0.001 m and 0.001 rad.
  - That is agreement at seven sampled times, not proof of continuous motion or dynamics.
- **Provenance.** The accepted-state record of each case was derived from the service's
  responses and the bytes retrieved. The controls show that it rejects a stale source, a stale
  artifact and self-asserted acceptance.
- **Clean rebuild.** Each delivered source was rebuilt twice. The rebuild used a wheel built
  from the committed revision and installed alone, and ran with `-I` in a new workspace that
  held only `main.ok`, `hinges.ok` and the rebuild entry. Every rebuilt GLB and sidecar is
  byte-identical to the delivered one, and nothing was imported from a checkout.
- **Faults and positives.** 13 fault controls were each rejected while their clean twins were
  accepted. They cover all seven kinds that R08 names, plus stale and self-asserted provenance
  and a changed dependency pin. 4 positive controls and 7 residual controls (H20, H24) passed. P03 negates every stored rotation keyframe in the GLB bytes and is judged end to end
  ([CONTROLS.md](CONTROLS.md)).
- **Replay.** A second execution of the command from empty stores gave equal case outcomes,
  per-property and pose tables, and control results. All 34 retained source and artifact files
  are byte-equal ([REPLAY.json](evidence/REPLAY.json)).
- **Format and playback.**
  - All six delivered GLB files, which are two distinct byte sequences (`d009…` for 0.65 m and `05eb…` for 0.75 m), pass the Khronos validator 2.0.0-dev.3.10 with no errors or
    warnings, and Three.js r180 playback matches C255's poses for all 126 samples. A truncated
    copy was refused ([gltf-validation](evidence/gltf-validation/SUMMARY.json)).
  - V1's 0.75 m animation was played in the project's offline viewer and looked at
    ([PLAYBACK.md](evidence/PLAYBACK.md)).
- **Determinism beyond this host.** The fresh GLBs equal the historical C210 proof GLBs byte
  for byte. Those were generated at `bb7e831a` with CPython 3.12.14 on Linux x86-64. This
  equality is a comparison with that historical result, not a result of this scope run on Linux.

## Requirements

States are at the candidate given for independent review. The rows still open are completed or updated at integration and closing.

| Requirement | State | Evidence |
| --- | --- | --- |
| REQ-001 local start, reconciled state | met | [START-STATE.json](START-STATE.json), task [SESSION.md](../../workflow/tasks/C272/SESSION.md) |
| REQ-002 task record after selection | met | [task record](../../workflow/tasks/C272/REQUIREMENTS.md) |
| REQ-003 C271's P02–P38 not resumed | met | task [PLAN.md](../../workflow/tasks/C272/PLAN.md); the requirements audit at review |
| REQ-004 current-status correction | met | STATUS.md, [START-STATE.json](START-STATE.json) |
| REQ-005 environment inspected and reused | met | [START-STATE.json](START-STATE.json), [VISUAL-PROFILE.json](evidence/VISUAL-PROFILE.json) |
| REQ-006 frozen cases and tolerances | met | runner's corpus check; C255 unchanged; preservation audit |
| REQ-007 reuse within limits | met | [COVERAGE.md](COVERAGE.md), table below |
| REQ-008 only missing components | met | [GAPS.md](GAPS.md) |
| REQ-009 C269 reconciliation and residual controls | met | [RECONCILIATION.md](RECONCILIATION.md), R01–R07 in [CONTROLS.md](CONTROLS.md) |
| REQ-010 scripted client, independent evaluator | met | [runner.py](runner.py); import tests in `test_observe.py`, `test_semantic_observe.py`, `test_score.py` |
| REQ-011 one documented command | met | [qualify.py](qualify.py), [README.md](README.md) |
| REQ-012 fresh store, exact start, baseline artifact | met | `evidence/runs/delivered-3c206ac7/cases/*/record/` |
| REQ-013 V1/V2 edit only the occurrence | met | the same records; locality in `RESULTS.json` |
| REQ-014 N1 refused, state untouched | met | N1 record and `accepted-state.json` |
| REQ-015 accepted-state record, stale and self-asserted rejected | met | `authority.json` (run output), E04a–E04d |
| REQ-016 every C253 property checked | met within option A's limit | per-property tables in `cases/*/score.json`: each row holds the observation, its origin pointers in the actual bytes, the expected value with its derivation, and the outcome; [GAPS.md](GAPS.md) |
| REQ-017 126 poses decoded and checked | met | `cases/*/score.json` pose rows |
| REQ-018 clean rebuild, byte-identical | met | `cases/*/rebuild.json` |
| REQ-019 deliberate faults rejected | met; the open items are named | [CONTROLS.md](CONTROLS.md) |
| REQ-020 external record, failure and retry exercised | met | `exchanges.jsonl`, protocol cases in `outcome.json` |
| REQ-021 fresh replay | met at the code revision `3c206ac7` | [REPLAY.json](evidence/REPLAY.json) |
| REQ-022 GLB validation and inspected playback | met | [gltf-validation](evidence/gltf-validation/SUMMARY.json), [PLAYBACK.md](evidence/PLAYBACK.md) |
| REQ-023 visual profile prepared | met, with a side effect reported to the owner | [VISUAL-PROFILE.json](evidence/VISUAL-PROFILE.json) |
| REQ-024 checks for the changed scope | met for the driver at `d10c9f62`; the observer regression and record checks on the review candidate are in its check record | [CHECKS.json](evidence/CHECKS.json) |
| REQ-025 failing check compared with main | met: one known baseline failure, none new or worsened | [CHECKS.json](evidence/CHECKS.json) |
| REQ-026 independent review | met: the first review (`d275baa4`) required changes M1 to M3; the second review accepted `48d35db9`; later changes are the record-only edits for its optional findings | `evidence/review-1/REVIEW.md`, `evidence/review-2/REVIEW.md` |
| REQ-027 integration and resulting main | open | the integration record |
| REQ-028 deliverables | met | this directory and `evidence/` |
| REQ-029 readiness table | met | below |
| REQ-030 local closing state | open | at closing |
| REQ-031 results within their limits | met | this report, README, PLAYBACK |
| REQ-032 no model, no expansion | met | no model call; no change under `ontokin/`; RUN-PLAN unchanged |
| REQ-033 failures visible | met | `evidence/runs/failed-4aff6024/`, `evidence/runs/earlier-f0e4148f/`, the driver's known failure |
| REQ-034 proportion | met | the G3 choice put to the owner; driver cost stated before running |

## Reused components and their limits

| Component | Interface used | Limit its contract records |
| --- | --- | --- |
| Agent/0.2 service | `ProgramAgentService.handle`, `accepted_revision`, `read_program` | The service under test; its success field is recorded, never the case result |
| C255 checker | `load_corpus`, `expected_state`, `evaluate` | Checks records; caller records are authenticated by this scope's harness, not by C255 |
| C256 reader | `associate_glb` | Finite GLB profile, two frozen source closures; geometry and poses only |
| C257, C258, C267 | `compare_ownership`, `compare_follows`, `compare_hinges` | Agreement between source and GLB declarations only; no world behavior, revision or rebuild |
| C268 endpoint reader | not used | Admits historical bytes only; its boundary is kept |

`tools/build_construction_demo.py`, `tools/build_semantic_export_demo.py` and the unit tests
are examples and regression coverage. They are not qualification of this evaluator.

## Limits that go with every result

- **The sidecar's origin.** No Agent/0.2 operation delivers the semantic sidecar. The harness
  builds it in process with the product's `build_semantic_manifest`, from the program it read
  back through `read_program` and the GLB bytes it retrieved. The rebuild does the same with
  the installed wheel. This is the C210 route's sidecar production, run by the harness.
- **Provenance fields.** The observation's accepted and program revisions are taken from the
  accepted-state record. C255's check of those two fields is therefore a consistency check.
  The GLB's own program revision is checked independently through C256, and the accepted
  revision is observed only in the service's responses and its accepted pointer.
- **More reader rules.** Besides the four source-only facts, G3 reads the tween's numeric value
  (45) and the event time (0 s) as source literals, cross-checking them against the delivered
  goal and time. A site's `kind` is derived from `@system` in its element ID, and a hinge's
  `axisFrame` from the sidecar key `axis_in_parent_site`. Each such rule is listed as derived
  in the semantic record.
- **Output inside the checkout.** The package-smoke setup tool writes its own report into the
  checkout's ignored `build/local-environment/`. All other run output is written outside the
  checkout.

- **Delivered semantics.** The semantic values (sites, actions, events, parameters, placement)
  are delivered producer metadata. They are checked against C255's independent expectations
  and cross-checked against decoded motion, under option A, which the owner chose. They are
  not an independent re-interpretation of the source expressions. Four values are source
  literals read by fixed pattern, and zero mass is derived from `no_body`
  ([GAPS.md](GAPS.md)).
- **Transport loss.** The GLB carries no sites, actions or events; only the sidecar does. The
  GLB holds sampled, recorded motion. Live physics, collision response and the execution of
  actions in a destination are unsupported.
- **Untested.** No destination other than the offline Three.js viewer was tested. Blender,
  Unreal, Godot and OpenUSD were not.
- **Not executed here.** Timeout and infrastructure-incident denominators, an end-to-end
  change of a global or shared default, and end-to-end tolerance-boundary controls. C255's
  record-level tests cover them ([CONTROLS.md](CONTROLS.md)).

## Readiness

Criteria R01 to R12 of the review that the requirements document captures (RV):

| RV | State after C272 |
| --- | --- |
| R01 fresh store, exact start, baseline artifact | met |
| R02 intended occurrence edit, library and unrelated parameters unchanged | met |
| R03 N1 refused before acceptance, state untouched | met |
| R04 delivered bytes bound to accepted source; stale and self-asserted rejected | met |
| R05 all C253 properties checked | met within option A's stated limit |
| R06 126 poses decoded and checked | met |
| R07 clean rebuild, byte identity | met |
| R08 deliberate faults rejected | met for the seven named kinds; the listed extras that stay open are named in CONTROLS.md |
| R09 external record, failure and retry | met |
| R10 fresh replay, GLB validation, inspected playback | met |
| R11 independent review; main checks classified | met: independent review accepted after one round of changes; main checks classified (one known baseline) |
| R12 command, sources, GLBs, results, failures, report | met |

Blocking requirements of the frozen run plan (`RUN-PLAN.json`, `executionAdmission`):

| Blocking requirement | State after C272 |
| --- | --- |
| Qualified offline oracle with positive, boundary and adversarial controls | **Partly addressed, for the OntoKin route only.** Positive and adversarial controls run end to end here. Boundary controls exist at record level in C255. An independent review of the oracle, its formulas and its controls accepted the candidate (REQ-026). |
| Qualified native artifact readers and minimal trial runner | **Partly addressed, for the OntoKin route only.** The GLB and sidecar readers and the scripted runner have been implemented and exercised on this family, and accepted by the independent review on this family. A Blender reader and a model-facing trial runner do not exist. |
| Exact model snapshot, settings and usage semantics | unmet; the run plan's model fields stay null |
| Qualified Blender starting seed and runtime dependency bindings | unmet |
| Frozen route roster, equivalent task and reference-pack bindings, starting-state checks | unmet |
| For any advantage study: clean unseen multi-assembly corpus | unmet; this family is one, previously exposed |

**Remaining A1 dependencies.** Gate A1 also needs the following:
- the direct Blender/Python baseline with an independently qualified output reader;
- matched task information and route reference packs;
- the OpenUSD-native assessment;
- complete attempt accounting under a pinned model.

This scope is useful progress toward A1. It does not complete A1, qualify C260 or accept the
product.

**One next action (a proposal to the owner, not a selected scope):** qualify the direct
Blender/Python route's equivalent starting state for V1, V2 and N1 with an independently
qualified reader of its output, so that the same evaluator can judge a second route.
