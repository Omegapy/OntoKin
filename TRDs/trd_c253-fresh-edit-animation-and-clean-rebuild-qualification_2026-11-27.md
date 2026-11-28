---
schema_version: 2
trd_id: "TRD-20261127-7B80B30A"
title: "C253 fresh edit, animation and clean-rebuild qualification"
slug: "c253-fresh-edit-animation-and-clean-rebuild-qualification"
created_at: "2026-11-27T20:49:56-07:00"
updated_at: "2026-11-27T21:02:18-07:00"
status: "trd_done"
revision: 3
last_action_id: "TO-TRD-006"
status_reason: "Owner explicitly approved the presented revision 2 (sha256 5f206f70...053b134) in conversation on 2026-11-27."
---

# Task Requirement Document: C253 fresh edit, animation and clean-rebuild qualification

## Destination

OntoKin's existing route for changing an animated assembly through its agent interface is qualified end to end on the three frozen C253 cases of the keyed-rack assembly. The cases are V1 (lengthen one finger from 0.65 m to 0.75 m), V2 (restore it to 0.65 m) and N1 (refuse 0.75 kg given as a length). One documented command starts each case from a fresh store, drives the real Agent/0.2 service with a scripted client, and lets independent checks judge the actual source and GLB bytes. The run must show that the accepted source changes as asked, that unrelated parts stay unchanged, that the invalid edit is refused without touching the accepted state, that the recorded animation is regenerated, and that the delivered source rebuilds to the same result in an empty workspace. The scope delivers the command, the editable sources, the regenerated GLBs, structured results, retained failures, an inspected playback and a short report that names what is still missing before a real-agent pilot.

This document states what must be true and how that is recognized. It is a requirements baseline, not a plan. It selects no scope and authorizes no implementation, installation, test execution, Git activity, publication or merge.

## Captured user intent

U01 — On 2026-11-27 (America/Denver) the project owner invoked the to-trd skill with one document as its only argument and no further instruction. The document is titled "OntoKin review and next development recommendations". It gives its review date as November 27, 2026 (America/Denver), the main revision it reviewed as `38ee8d18a6cd67245acf8b21d755e979b84153c1`, and the owner and "the local development agent" as its audience. It says of itself: "This is a review and proposed local-agent assignment. It does not report a new runtime test, model trial, release qualification or repository change."

This document calls that review RV. RV is not a file of the repository; it reached this document as the text of the invocation. The parts of RV that carry requirements are therefore reproduced below in RV's words, and the rest is cited by section number.

RV's decision:

> Make the next development scope **an independently checked, fresh edit and rebuild workflow for one existing animated assembly**. Use the current agent interface and the frozen C253 keyed-rack qualification cases. Deliver an executable path that changes accepted source, preserves unrelated parts, rejects an invalid edit, regenerates the animation and verifies the actual output.

RV's objective for this scope (section 4) is: "**Qualify OntoKin's fresh source-edit, recorded-animation and clean-rebuild path for C253 V1, V2 and N1.**" RV adds: "This first scope uses scripted clients to qualify that machinery. It does not run a model comparison. The actual-model stage comes after its prerequisites pass."

RV's acceptance criteria (section 4):

| ID | Required evidence |
| --- | --- |
| R01 | A fresh store accepts each case's exact starting source and pinned dependency closure through the real Agent/0.2 service. Generate and retain the accepted baseline artifact before each edit, including N1, so preservation checks are not vacuous. Record source, program and accepted revision identities. |
| R02 | V1 and V2 apply the intended occurrence edit. Actual source inspection proves that the shared library and unrelated parameters remain unchanged. |
| R03 | N1 returns the required incompatible-dimension rejection before acceptance. Accepted revision, source/dependencies and existing artifact bytes remain unchanged; no temporary accepted invalid state is permitted. |
| R04 | Freshly exported and retrieved GLB bytes are bound to the accepted source. Reject stale source, stale artifacts and self-asserted acceptance. A recorded digest alone cannot prove the acceptance history. |
| R05 | Independent checks cover all properties required by C253: identities, dimensions, relationships, site values, actions/events, permitted physical declarations, appearances and unrelated content. Missing coverage remains explicitly incomplete. |
| R06 | Independently decode the actual geometry and motion. Check all 126 required object/time poses at 0, 0.25, 0.5, 0.75, 1, 1.5 and 2 seconds, using the unchanged source and delivery tolerances. |
| R07 | Rebuild from the delivered accepted source in an empty workspace containing only declared inputs and pinned tools. Meet the frozen route's semantic, measurement and byte-identity requirements. No undeclared checkout file or retained artifact may supply the result. |
| R08 | Deliberate faults demonstrate that the checks reject wrong-part edits, changed siblings, incorrect motion, stale provenance, accepted invalid candidates, missing output and inconsistent rebuilds. Reuse qualified controls; implement only necessary gaps. |
| R09 | An external record retains every case outcome, actual request/response sequence, diagnostics and artifact identities. Failure and retry handling are exercised. Do not present inert classification examples as executed attempts. |
| R10 | A fresh replay produces the expected results. Complete applicable GLB validation and visual inspection using the prepared tools; retain the actual playback observation and disclosed losses. |
| R11 | Independent review checks the exact candidate and acceptance evidence. Applicable main integration checks pass or are classified against the recorded same-host baseline under current policy. |
| R12 | Deliver one documented command, editable sources, regenerated GLBs, structured results, retained failures and a short human-readable report. State remaining A1 dependencies without claiming full A1, C260 or product acceptance prematurely. |

RV's assignment for the local agent (section 8):

> Read LOCAL-START-HERE.md and reconcile current main, local state and task records. Treat this review as the proposed selection of one new scope: qualify the existing OntoKin Agent/0.2 fresh edit, recorded-animation and clean-rebuild workflow on the frozen C253 V1/V2/N1 cases. Reuse the implemented service and independent observers. Retain C270/C271's completed evidence and current historical boundaries. Implement only the missing components needed for the stated acceptance criteria, including trustworthy accepted-state provenance, complete applicable scoring, invalid-edit preservation and clean rebuild. Produce actual regenerated source/artifact evidence and an inspected playback. Follow the current same-host baseline policy, independent review and local integration workflow. Report completed criteria, failures and precise remaining A1/pilot prerequisites. Do not automatically launch the model comparison or expand the language, physics, transports or backends.

How this document reads U01:

- The owner made RV the subject of this document. RV's recommendations for the first scope are captured as requirements. Each checkable statement of RV was compared with the repository at the reviewed revision and with live GitHub (D02 and the table "RV's statements checked at capture").
- RV describes one scope to do now and several stages to do later. Only the first is captured as requirements. The later stages are listed under "Out of scope" with RV's conditions, so that the report can name them (REQ-029).
- RV proposes the selection of the scope. The invocation does not say that the owner has selected it, and this document records no selection (REQ-002, D03).
- RV keeps two roles apart. The development agent changes OntoKin's implementation, tests and documentation. The authoring agent uses OntoKin's public interface to solve a 3D task. In this scope the development agent does the work, and a scripted client, not a model, plays the authoring role.

Five principles follow from RV and govern everything below:

- Reuse before building. The agent service and the independent observers already exist. They are reused within the limits that their own contracts record, and only what the acceptance criteria still lack is built.
- Independent checks judge actual bytes. Expected results come from the task's source facts and equations. A producer's own statement, a recorded digest or a sidecar file never proves correctness by itself.
- What is frozen stays frozen. The cases, the source closures, the historical outputs, the tolerances and the adopted contracts are used as they are.
- A claim stops where its evidence stops. A missing check is reported as missing. Passing this scope is not the roadmap's A1 gate, not C260's qualification, not product acceptance and not evidence of an authoring advantage.
- The work stays in proportion. The deliverable is one correct, inspectable workflow. It is neither a large test count nor a chain of documentation milestones.

## Context and sources

### Source labels

Repository files were read at RV's reviewed revision `38ee8d18a6cd67245acf8b21d755e979b84153c1` from Git objects, because the clone's working tree was six commits behind that revision at capture (see "State observed at capture").

| Label | Source | What it supports |
| --- | --- | --- |
| U01 | The owner's to-trd invocation of 2026-11-27 | That RV is the subject of this document |
| RV | The review, cited by its "Decision" section, its sections 1 to 8 and its criteria R01 to R12 | The scope, the criteria, the reuse rules, the local procedure, the deliverables, the later stages and the deferrals |
| G | Live observation at capture, 2026-11-28 03:29Z to 03:40Z (2026-11-27 20:29 to 20:40 America/Denver): `git ls-remote --heads origin`, the clone's refs, status and worktrees, `gh pr list`, `gh pr view 274`, `gh issue list` and `tools/doctor_local.py` | The heads, the pull-request state, the clone's state and the readiness of the environment |
| CUR | `docs/workflow/CURRENT.json` | No active task; the next scope is the owner's choice |
| ST | `STATUS.md` | Completed scopes, what remains unqualified, the baseline results, the lease |
| AG | `AGENTS.md`, with its rule of 2026-11-28 on main's known failures and the matching amendment in OK-ENG-009 | The check table, the baseline rule, the preservation rules, proportion |
| GL | `GOAL.md` | The mission, the unmet gates, the deferred domains, the invariants and budgets |
| RM | `docs/engineering/review-integration-c252/ROADMAP.md` | The ordered gates, among them A1 and A2 |
| PR253 | `PROTOCOL.md` and `README.md` in `docs/engineering/localized-repair-c253/` | The frozen cases, the routes, exposure and the execution boundary |
| SC | `SCORING.md` in the same directory | Oracle independence, invariants, equations, tolerances, rebuild and revision rules, N1's boundary, the oracle controls |
| RP | `RUN-PLAN.json` in the same directory | Repetitions, budgets, the unfilled admission fields and the blocking requirements |
| CO | `corpus.json` in the same directory | The exact files, hashes, patches, invariants and tolerances of the three cases |
| C210 | `docs/engineering/semantic-export-c210/CONTRACT.md` | The deterministic-comparison rule of the frozen OntoKin proof |
| C255 | `docs/engineering/localized-repair-c255/CONTRACT.md` | The inert observation checker, its authority and observation records, and its limits |
| OBS | The README files of C256, C257, C258, C260, C267 and C268 in their directories under `docs/engineering/` | What each observer establishes and what it leaves unqualified |
| AUD | `docs/engineering/localized-repair-c269/AUDIT.md`; ST's paragraph on C270; `docs/engineering/localized-repair-c271/OWNER-DECISION-20261128.md` | The four partial groups, C270's correction, C271's result and its excluded phases |
| WF | `LOCAL-START-HERE.md`, `docs/workflow/PROTOCOL.md`, the local section of `docs/workflow/HANDOFF.md` and `ROLE.md` | Startup, task records, conduct, verification, review, integration, the lease and the closing state in local mode |
| ENV | `docs/development/LOCAL-SETUP.md`; `docs/engineering/local-migration-20261124/RESULTS.md` | Profiles, the doctor, the resolved temporary directory, output outside the checkout, the visual profile |
| E2 | `docs/engineering/OK-ENG-002-3d-scene-animation-export-and-visual-validation.md` | What actual playback and visual inspection each establish |

### Terms

- `.ok` source: OntoKin's editable text description of an object. The accepted `.ok` source is authoritative (GL).
- GLB: the portable binary 3D scene and animation file. Here it is a checked output of the source and holds sampled, recorded motion (RV section 1, E2).
- Store, program revision, accepted revision: the agent service keeps source in a store. A program revision identifies one exact pinned source closure. The accepted revision is the one that the store currently holds as accepted.
- Agent/0.2 service: the existing program-bundle agent interface with protocol `ontokin.agent/0.2`. `ProgramAgentService` implements it, and `python -m ontokin agent --protocol ontokin.agent/0.2` offers it as a JSONL service.
- C253: the frozen qualification protocol "Localized assembly repair", with its corpus, scoring specification and run plan. Its three cases come from one public keyed-rack assembly family.
- Runner: "the small program that starts each case, invokes the real service, retains requests and output, and asks independent checks whether it succeeded" (RV section 4). SC calls the part that receives, validates and records submissions the external harness.
- Independent evaluator: the part that "determines expected results from the task's source facts and equations rather than accepting the producer's own claims" (RV section 4). SC also calls it the oracle.
- A1 and A2: gates of the C252 roadmap. A1 is "Build and validate only the minimal runner/oracles required by the approved protocol." A2 is the predeclared pilot that follows it (RM).

### State observed at capture

| Item | Observed |
| --- | --- |
| Remote | Only `main` exists, at `38ee8d18a6cd67245acf8b21d755e979b84153c1`, which is RV's reviewed revision. No pull request is open |
| Pull request #274 | Closed on 2026-11-28 at 03:01:23Z, draft, not merged, head `71b092326d4b54da87d33c6533bd13c0609cf9df`. Its branch `work/c271-missing-import-digest-control` is absent from the remote. GitHub keeps the head as `refs/pull/274/head`, and the clone holds that commit |
| Open issues | #154 (C211, Blender normal fidelity) and #134 (C199, static-tray mapping). Neither belongs to this scope |
| Clone | On `main` at `51223c9b94a222f29d38eb6c33808f8e55e2bff9`, six commits behind its tracking ref and none ahead; one worktree, no work branch, no stash |
| The six commits | They change `AGENTS.md`, `STATUS.md`, OK-ENG-009, CURRENT, C271's evidence directory and C271's task records: 65 files, none under `ontokin/`, `tools/`, `tests/` or `examples/` |
| Working tree | `TRDs/INDEX.md` modified; two approved requirements documents (TRD-20261125-CE424ADD and TRD-20261125-09FE8692) and `Implementation_Plans/` untracked. None of it is committed |
| CURRENT | `latest_task` C271, `active_task` null, `execution_mode` null, next action `awaiting_user_direction`: "No scope is selected; the owner chooses the next one." Its `observed_main` field holds `8e847c15e41c7e5970581993c465690526cd43d2`, the merge of pull request #278, which is an earlier head |
| STATUS | The lease is released. The text still says that C271's phases P02 to P38 stay unmerged on branch `work/c271-missing-import-digest-control` and in draft pull request #274 |
| Environment | CPython 3.12.13 on macOS 26.6.2, arm64. The doctor reports `core` and `python-verification` ready and `visual-verification` as mismatch: Node.js v25.9.0 is installed and the target is Node.js 22, the npm dependencies are not installed, and the Chromium shell is not checked |

These are observations of one moment. They are context, not instructions: the work reads the live state again before it acts (REQ-001).

### RV's statements checked at capture

| RV says | Observed |
| --- | --- |
| Main is at `38ee8d18`; CURRENT has no active task and awaits the selection of a new scope | Confirmed (G, CUR) |
| C271 closed through its documentation-only H22.02 result, and its phases P02 to P38 were excluded | Confirmed (AUD): "Phases P02 to P38 do not merge." |
| Only `main` exists, no pull request is open, and pull request #274 is closed and unmerged at `71b09232` | Confirmed (G) |
| The status text still describes a historical branch and draft pull request #274 | Confirmed (ST). The owner's decision record of 2026-11-28 says the same; it is a historical record and stays as it is (REQ-004) |
| CURRENT's `observed_main` field is not a live observation | Confirmed: it holds an earlier head |
| Known failures of main do not block when the branch and main show the same test ID and reason on the same host | Confirmed (AG and the OK-ENG-009 amendment of 2026-11-28) |
| The keyed-rack family has 18 objects, 34 sites, eight hinges, eight follows, two actions and two seconds of motion | Confirmed (PR253, CO) |
| V1, V2 and N1 as stated; 16 unrelated objects, among them all 11 of the second rack; seven times and 126 poses | Confirmed (PR253, SC, CO) |
| Six repetitions for each case and route; 36 attempts for two routes, 24 valid and 12 invalid; unfilled model and route fields; no advantage claim possible on this corpus | Confirmed (RP): the model pins and the route inputs are null, `qualifiedRoutes` is empty, and `advantageClaimEligible` is false |
| The agent service, the transaction tests, the demonstration tool, the observers and the tests that RV's reuse table names exist | Confirmed: each named file exists at the reviewed revision |
| Each observer's limit as RV states it | Confirmed against C255 and OBS (table "Existing components and their recorded limits") |
| C269 found H20 independence gaps and an H24 excessive-site gap; C270 and C271 added evidence for H16 and H22 | Confirmed (AUD, ST) |
| C099 recorded three fresh agent sessions with 32 successful requests | Confirmed (`docs/engineering/agent-first-use-c099/README.md`: 9, 13 and 10 requests) |
| Semantic export marks live physics and the execution of actions in a destination as unsupported | Confirmed (`ontokin/semantic_export.py`) |
| The migration recorded `core` and `python-verification` ready and the visual profile unprepared because of the Node.js version | Confirmed (ENV), and still so at capture (G) |
| "Three independent review workers examined agent use, geometry/animation and delivery readiness." | This is RV's account of how it was made. It cannot be checked from the repository |
| RV reviewed the remote main | The clone is six commits behind it. RV does not mention this; REQ-001 covers it |

No statement of RV was contradicted.

### The frozen C253 basis

C253 fixes the following, and this scope changes none of it (REQ-006).

| Case | Starting state | Requested outcome | Corpus binding |
| --- | --- | --- | --- |
| V1 | The first rack's middle finger is 0.65 m long | Change that occurrence to 0.75 m | Start `before.main.ok` (`start_065`); frozen endpoint `after.main.ok` (`target_075`) |
| V2 | The same occurrence is 0.75 m long | Restore it to 0.65 m | Start `after.main.ok`; frozen endpoint `before.main.ok` |
| N1 | The accepted starting state of V1 | Attempt the existing 0.75 kg candidate for the length, refuse it and keep the accepted state | Start `before.main.ok`; candidate `rejected-candidate.ok` (`invalid_mass`) |

- The files are in `docs/engineering/semantic-export-c210/evidence/proof/`. Their SHA-256 values in the corpus are `73c95c6509363e492084d7b6959356fe1955f4e78086a72b507167a271a33123` for `before.main.ok`, `443328e2a2e3f2e68245fa1e725b518187aa446ecd7ee3de4675e006cf4e666a` for `after.main.ok`, `3d65ef15bbf92b557b960f9bb186b6483cf76dca68737d62ba3761fe7a7be499` for `rejected-candidate.ok` and `1516e53179a7b9deecf593ab48afdcd72fba8124ea77868327c25a28a654681a` for the pinned library `hinges.ok` (`example.hinges` 1.0.0).
- The edited parameter is `first.fingers["middle"].length`. The library stays byte-identical in every case.
- The whole assembly stays in scope: 18 object identities, 34 sites, eight hinges, eight follows, two actions and the original two-second motion. Of the 18 objects, 16 are unrelated to the edit, among them all 11 of the second rack.
- SC gives independent equations for every center and rotation at time `t` in [0, 2] seconds and selected length `L`, for example `theta(t) = (pi / 4) * min(t, 1)` and the selected blade's center `(-1 + L*cos(theta)/2, 0.2*t + L*sin(theta)/2, 0)`.
- The observation times are 0, 0.25, 0.5, 0.75, 1, 1.5 and 2 seconds: 18 objects at seven times are 126 poses for each valid submission.
- Tolerances: 1e-12 m for source-level dimensions; 1e-9 m and 1e-9 rad where the reference evaluator is inspected; 0.001 m for each position component, 0.001 rad of rotation angle and 1e-6 s for delivered geometry and motion. Identities, units and relationship membership compare exactly.
- N1's boundary is "the acceptance decision on staged candidate source, before replacing any accepted revision, source file or artifact" (SC).
- The rebuild takes place "in a fresh empty workspace with only the declared dependency closure and pinned tools" (SC). For the frozen OntoKin proof: "Same exact source bundle, implementation, GLB export settings and environment must produce identical GLB bytes for this proof." (C210)
- PR253 says of the OntoKin route: "Requires a fresh qualified runner and independent oracle. Historical success is not a new trial."
- The three cases belong to one public, previously used family: "They can qualify a future test harness. They cannot constitute an unseen comparative corpus or establish general authoring advantage." (PR253)

### Existing components and their recorded limits

| Component | Reuse that RV intends | Limit that the component or RV records |
| --- | --- | --- |
| `ontokin/program_agent.py` and `ontokin/agent_cli.py` | `ProgramAgentService` or the existing explicit Agent/0.2 JSONL service | "Keep earlier protocol defaults intact." (RV) |
| `tools/build_construction_demo.py` | An example of real pinned-program creation, edit, evaluation and GLB retrieval | "Predetermined demonstrations are not model-trial outcomes." (RV) |
| C255, `oracle.py` | Independent expected-state and scoring rules | It checks inert records: "`realTrialSuccess` is always null, `executionAllowed` and `artifactReaderQualified` are always false." Its `classify_attempt` helper is an accounting control and records no execution (C255) |
| C256, `reader.py` | Measurement of actual GLB bytes: 18 meshes and 126 poses | It is a "partial observation producer". Its source association is limited to the two frozen closures; its `associate_glb` entry point accepts a GLB that is not a historical endpoint (OBS) |
| C257, `ownership.py` | Finite ownership observation and comparison | Ownership is not transform parenting. It authenticates no accepted revision, edit atomicity or rebuild (OBS) |
| C258, `follows.py` | Finite comparison of follow declarations | It does not establish site or world behavior (OBS) |
| C267, `hinge_compare.py` | Finite comparison of hinge declarations after source and artifact binding | Agreement establishes no world alignment, accepted revision, edit atomicity or rebuild equivalence (OBS) |
| C268, `endpoint_reader.py` | Historical exact-byte controls | It admits only the original bytes: "Preserve its admission boundary; do not route new arbitrary outputs through it by weakening the contract." (RV) |
| `tests/test_construction_export.py` and `tests/test_semantic_export.py` | Regression coverage and examples of artifact checks | "Unit-test assertions do not replace qualification of the independent trial evaluator." (RV) |

ST lists what is still unqualified on main: "complete C260 H groups, site/world behavior, authentic revisions, invalid-edit atomicity qualification, clean rebuilds, native routes, comparative trials." The criteria of this scope address authentic revisions, invalid-edit atomicity, clean rebuilds, complete semantic scoring and world poses for the three cases. Native routes and comparative trials stay outside it.

### The C269 audit and what came after

C269 audited the coverage of C260's 28 control groups without running anything new. At its baseline `23c044775ad77e7c1ab2f27eb1c9dd4a67c004bb` it found 24 complete and four partial groups, and 94 complete and five partial material subcases.

| Group | Missing demonstration according to C269 | Later evidence |
| --- | --- | --- |
| H16, unsupported endpoint and joint forms | A source-valid declared or computed `SiteRef`, exercised with an exact unsupported-form assertion | C270: the observer refuses an accessible, explicitly declared `SiteRef` parameter as `UNSUPPORTED_SOURCE_FORM`. ST adds: "No successful SiteRef support or broader H16/C260/product qualification follows." |
| H20, unrelated-field independence | Independently authored expected fields, and isolated changes of each actual ownership, follow and motion field | None recorded |
| H22, source and program provenance | An isolated removal of the actual source import digest, with its retained outcome | C271: the H22.02 isolated missing source import-digest control, merged as documentation only |
| H24, structural and resource bounds | A supplied excessive-site input with its actual typed outcome: "The remaining obligation needs an explicit decision or a bounded additional control." | None recorded |

ST still records: "Full C260 qualification remains unestablished."

### What A1 and trial admission ask

For gate A1 the roadmap requires "Positive and negative oracle controls, complete attempt accounting, source/artifact identity and a reproducible fresh-checkout path. No broad framework." (RM). The frozen run plan lists what blocks any trial (RP): a qualified offline oracle with its controls; qualified native artifact readers and a minimal trial runner; an exact model snapshot with its settings and usage semantics; a qualified Blender starting seed with its runtime dependency bindings; a frozen route roster with equivalent task and reference-pack bindings and starting-state checks; and, for any advantage study, a clean unseen multi-assembly corpus with a prospective precision justification. RV says: "The broader A1 roadmap gate includes more than this OntoKin-only path. Qualifying it is useful progress, while a direct-tool baseline and other pilot-admission requirements remain separate."

## In scope

- One executable qualification of the OntoKin route on C253's V1, V2 and N1: the runner with its scripted client, the independent evaluator, the accepted-state record, the clean rebuild, the fault controls and the fresh replay.
- The missing components that this needs, and the residual C260 controls that the workflow depends on.
- Validation of the regenerated GLBs and a visual inspection of an actual playback, with the `visual-verification` profile as their dependency.
- The frame of the work in local mode: reconciliation of the starting state, the task record after selection, a small correction of current-status text if it is still needed, the checks for the changed scope, the comparison with main's baseline, independent review, integration, branch disposition and the local closing state.
- The deliverables: one documented command with usage instructions, source bundles, regenerated GLBs, structured results, retained failures, the visual observation, a short report and a readiness table.

Affected at capture, by name: `ontokin/program_agent.py` and `ontokin/agent_cli.py` as the service under test; the observers of C255 to C258, C267 and C268 as reused components; new code and evidence for the runner, the evaluator's missing parts and the controls, at places that the plan chooses; `STATUS.md` and `docs/workflow/CURRENT.json` for the correction and the closing state; a new task directory under `docs/workflow/tasks/`; the `visual-verification` profile of the owner's environment.

## Out of scope

- Selecting this scope, creating its task record before selection, and every other decision that belongs to the owner. This document records none.
- A plan for this work and its execution. Each needs its own instruction from the owner.
- Any model session, model comparison or trial attempt. The 36 attempts of the frozen run plan are not started, and its unfilled model and route fields are not filled in this scope.
- The next stage that RV names in section 6: qualifying an equivalent direct Blender/Python starting state and output reader, preparing matched task information and route reference packs, assessing whether an OpenUSD-native route applies, pinning the model with its settings, tools and accounting, and running the predeclared pilot. RV's condition is a trustworthy scorer and runner and complete model and route admission.
- The stage after that: separately reserved, unseen creation and animation-editing tasks, for example a hinged lid or a sliding carriage, with a newly qualified evaluator. RV's condition is a new task population, frozen scoring and useful pilot feasibility.
- Later work that depends on evidence: improving one receiving route or a finite OpenUSD mapping, and an externally generated, content-identified asset with supported semantic bindings.
- Work that RV defers until a measured need and a separately bounded decision exist: custom model training, MCP transport, general collision or gameplay systems, many production backends, broad syntax and general refactors.
- New language features, new shape syntax, new physics, new transports, new destinations or backends, and any change to language semantics or to an adopted contract.
- Changes to C253's protocol, scoring, run plan or corpus, to the C210 proof files, to historical outputs, to any tolerance, or to the admission boundary of C268.
- Resuming C271's phases P02 to P38, restoring its old branch, and repairing main's known baseline failures.
- Claims of full A1, of C260 qualification, of product or release acceptance, of an authoring advantage, of live physics or collision behavior in a destination, of lossless Blender support, or of Unreal or Godot support.
- Redoing the local migration, adding a container, reconstructing an earlier disposable host, hosted CI and any paid execution.
- Committing or publishing this document.

## Task requirements

### REQ-001 — Work starts in local mode from the reconciled actual state
- Requirement: Work on this scope starts from `LOCAL-START-HERE.md` in the owner's persistent clone, after the independently observed remote main, the local changes, the existing task records, the worktrees and the ownership have been reconciled, with unpublished local work preserved.
- Source: RV section 5, step 1 — "Reconcile the independently observed remote main, local changes, existing task, worktrees and ownership. Preserve unpublished work."
- Source: RV section 8 — "Read LOCAL-START-HERE.md and reconcile current main, local state and task records."
- Source: WF, LOCAL-START-HERE's startup steps and PROTOCOL section 2 — "Preserve local changes before updating anything."
- Source: G — at capture the clone's main is six commits behind the remote main, and its working tree holds uncommitted requirements documents and plan files.
- Acceptance: The session's startup report, given to the owner before the first change, names the branch, the local head, the remote head read with `git ls-remote --heads origin`, the tracked changes, the untracked work, the worktrees, the work branches and the state of the lease.
- Acceptance: Every local change that exists at that moment is preserved before the checkout is updated; none is overwritten, reset or discarded.
- Acceptance: The session checkpoint records the execution mode as `local`.
- Depends on: None.

### REQ-002 — The scope gets its own task record only after the owner selects it
- Requirement: A new bounded task record for this scope is created only after the owner has selected the scope, inside the existing repository workflow, and it records the base revision of the reviewed recommendation and every newer decision that bears on the scope.
- Source: RV section 5, step 2 — "Create a new bounded task record for this scope only after it is selected. Record the reviewed recommendation's base and any newer decisions."
- Source: RV section 5 — "Follow the existing repository requirements, plan, worker and integration workflow. This handoff does not introduce a competing task system."
- Source: CUR — `active_task` is null and the suggested task is "Await owner direction; no next scope selected."
- Source: WF, LOCAL-START-HERE — "With no selected scope, report the state and ask."; PROTOCOL section 3 — the task directory with `REQUIREMENTS.md`, `PLAN.md` and `task.json`.
- Acceptance: No task record for this scope is created before the owner's explicit selection, and the approval of this document is not that selection.
- Acceptance: After selection the task record exists under `docs/workflow/tasks/`, names the execution mode `local`, names `38ee8d18a6cd67245acf8b21d755e979b84153c1` as the base of the reviewed recommendation, and lists the decisions made after that revision on which it relies.
- Acceptance: CURRENT stays the only owner of the task pointer and STATUS the only owner of the lease; no other ledger of status is created for this scope.
- Depends on: REQ-001

### REQ-003 — C271's excluded phases are not resumed and completed evidence stays as recorded
- Requirement: This scope neither resumes C271's phases P02 to P38 nor restores C271's old branch, treats neither as a prerequisite, and leaves the completed evidence of C270 and C271 as it is recorded.
- Source: RV section 3 — "C271 closed through its documentation-only H22.02 missing-import-digest result; its later P02–P38 work was excluded from that completion. Do not resume those phases as an automatic prerequisite."
- Source: RV section 3 — "The new scope does not require restoring that old branch."; RV section 8 — "Retain C270/C271's completed evidence and current historical boundaries."
- Source: AUD, the owner's decision of 2026-11-28 — "Phases P02 to P38 do not merge." and "None of their claims becomes a claim of main."
- Acceptance: The task's requirements and plan contain no step that carries out, completes or depends on the current-host readback contracts, their preparation, their host qualification or gate MR.
- Acceptance: The scope's branch starts from the main head observed at that time, and no step of the plan needs the commits that only the closed pull request #274 holds.
- Acceptance: The records of C270 and C271 keep their bytes; this scope cites them and neither reruns nor rewrites them.
- Depends on: None.

### REQ-004 — Current-status text agrees with the live branch and pull-request state
- Requirement: When the work begins, the live branch and pull-request state is read again, and if `STATUS.md` or another current-state record still describes C271's branch and draft pull request #274 as existing, a small correction brings that record in line with the observed state, while historical evidence stays unchanged.
- Source: RV section 3 — "The status text still describes a historical branch and draft PR274. Recheck live state when work begins; make a small current-status correction if still needed, while preserving historical evidence."
- Source: RV section 3 — "Do not treat the older observed_main field in CURRENT as a live GitHub observation."
- Source: G — only `main` exists on the remote, no pull request is open, and pull request #274 is closed and unmerged at head `71b092326d4b54da87d33c6533bd13c0609cf9df`, while ST still describes the branch and the draft pull request.
- Acceptance: The correction, if it is still needed, changes only statements of current state, says what was observed and when, and is checked with the documentation verifier and the workflow check.
- Acceptance: The owner's decision record of 2026-11-28, C271's records and every other historical record keep their bytes.
- Acceptance: No record of this scope gives CURRENT's `observed_main` field as the live head of main; the live head is read from the remote.
- Acceptance: If the records already agree with the live state when the work begins, no correction is made, and the task record notes that.
- Depends on: REQ-001

### REQ-005 — The prepared environment is inspected and reused
- Requirement: The scope's commands run through the checkout's own `.venv/bin/python`, after the existing doctor has shown the actual readiness of the profiles that they need; valid resources are reused, and only missing or incompatible inputs are prepared.
- Source: RV section 5, step 3 — "Inspect the current .venv with the existing doctor and reuse valid resources." and "Recheck actual readiness."
- Source: RV section 5, step 4 — "Use the checkout's .venv/bin/python. Follow LOCAL-SETUP's resolved TMPDIR guidance on macOS. Keep validation output outside the checkout."
- Source: RV section 5 — the visual profile "does not justify redoing the completed migration, adding Docker or reconstructing a past disposable host."
- Source: ENV — the profiles, the resolved temporary directory on macOS, and "Write driver output **outside the checkout**."
- Acceptance: A doctor report made in the checkout that runs a check shows each profile that the check uses as ready before the check's result is used.
- Acceptance: Checks that are sensitive to the symlinked macOS temporary directory are run with the resolved one, as LOCAL-SETUP shows.
- Acceptance: Driver and validation output is written to new directories outside every checkout.
- Acceptance: The environment is not rebuilt without a diagnosed reason, no container is added, and no earlier disposable host is reconstructed; each editing worktree has its own environment, created in place.
- Depends on: REQ-001

### REQ-006 — The frozen C253 cases, closures, historical outputs and tolerances stay frozen
- Requirement: The three cases V1, V2 and N1, their exact source closures, the historical outputs and every original tolerance are used unchanged; no new `.ok` fixture is created for them and no historical expectation is adjusted.
- Source: RV section 4 — "Keep these exact cases, source closures, historical outputs and tolerances frozen."
- Source: PR253 — "No new `.ok` fixture or adjusted historical expectation is created." and "The shared `example.hinges` 1.0.0 library remains byte-identical and pinned."
- Source: CO — the 14 file bindings with their SHA-256 values and the three task definitions; AG — "Never change expectations to pass tests."
- Acceptance: Before each run, the starting entry, the candidate and the library of each case are verified against the SHA-256 values of the C253 corpus, and a mismatch stops the run.
- Acceptance: The files of C253 (protocol, scoring, run plan and corpus), the C210 proof files and the construction fixture's `expected.json` keep their bytes on the scope's branch.
- Acceptance: Every comparison uses the tolerances that C253 fixes (REQ-016, REQ-017); none is widened, and none is supplied by a caller.
- Depends on: None.

### REQ-007 — Existing components are reused within their recorded limits
- Requirement: The workflow is built from the implemented agent service and the existing independent observers, each used only for what its contract says it establishes and after the applicable contracts have been read; no existing contract or admission boundary is weakened to make a new output pass.
- Source: RV section 4, "Reuse the existing components" — the table of components with their intended reuse and limits, and "Read the applicable contracts before connecting these modules."
- Source: RV section 4 — "Concatenating partial reports is insufficient unless every required field has a trustworthy observation and comparison. Producer metadata can be inspected, but cannot certify its own correctness."
- Source: RV section 2 — "Reuse the existing interface. Missing independent benchmark qualification does not mean these runtime features need to be built again."
- Source: C255 and OBS — each component's own statement of what it does not establish (table "Existing components and their recorded limits").
- Acceptance: The service under test is the existing `ProgramAgentService` or the existing explicit Agent/0.2 JSONL service, and the defaults and behavior of every earlier protocol version are unchanged.
- Acceptance: Freshly generated outputs are not passed through C268's historical exact-byte reader, and that reader still admits the original bytes only.
- Acceptance: The report names, for each reused component, the interface used and the limit that its contract records; `tools/build_construction_demo.py` and the unit tests are cited as an example and as regression coverage, not as qualification of the evaluator.
- Acceptance: A statement that a property was checked rests on an observation and a comparison of that property; partial reports placed side by side are not presented as a complete check.
- Acceptance: Metadata written by the producer may be inspected and never certifies its own correctness.
- Depends on: None.

### REQ-008 — Only the missing components are implemented
- Requirement: New code is limited to the components that the acceptance criteria of this document need and that do not exist yet, including trustworthy accepted-state provenance, complete applicable scoring, invalid-edit preservation and the clean rebuild.
- Source: RV section 8 — "Implement only the missing components needed for the stated acceptance criteria, including trustworthy accepted-state provenance, complete applicable scoring, invalid-edit preservation and clean rebuild."
- Source: RV section 4 — "If a required check needs a substantial new evaluator, record the exact missing property, implementation boundary and effort before expanding. Preserve the frozen contract. A prospectively reviewed narrower study could be proposed, but it must not be reported as completion of the existing one."
- Source: RM, gate A1 — "Build and validate only the minimal runner/oracles required by the approved protocol." and "No broad framework."
- Acceptance: The task's plan traces each new component to the requirement of this document that needs it.
- Acceptance: Before a substantial new evaluator is started, a record states the exact missing property, the boundary of the implementation and the estimated effort.
- Acceptance: A narrower study, if one is proposed, is reviewed before it is carried out and is reported under its own name, never as completion of the frozen C253 qualification.
- Depends on: REQ-007

### REQ-009 — The C269 audit is reconciled, and the residual controls that this workflow depends on are added
- Requirement: The coverage audit of C269 is reconciled with C270's SiteRef refusal correction and C271's isolated missing-digest control, and each residual control that this workflow depends on, among them the H20 independence gaps and the H24 excessive-site gap where they apply, is addressed inside this task.
- Source: RV section 4, "Resolve necessary gaps within this task" — "Reconcile the old C269 coverage audit with C270's SiteRef refusal correction and C271's isolated missing-digest evidence. Do not publish the old partial counts as a fresh audit or infer that an entire group passed from one new control."
- Source: RV section 4 — "Address applicable residual controls as dependencies of this executable workflow. Do not turn each into another unbounded chain of standalone documentation milestones."
- Source: RV section 4 — "Hinge-reader controls alone cannot prove accepted revision authority, atomic edit preservation, complete semantic scoring or clean rebuilds."
- Source: AUD — C269's table of remaining gaps for H16, H20, H22 and H24; ST — the results of C270 and C271 with their stated limits.
- Acceptance: A reconciliation record gives, for each of H16, H20, H22 and H24, the audit's finding, the later evidence that bears on it and the present state, and it keeps inherited results apart from results that this task newly produces.
- Acceptance: C269's counts are cited only as the audit's result at its baseline, never as a fresh audit, and no group is reported as passed by inference from one new control.
- Acceptance: For each residual gap the record states, with the reason, whether a check of this workflow depends on the property concerned; where it does, the control is implemented and executed in this task, and where it does not, the gap stays reported as open.
- Acceptance: No residual control becomes a separate documentation-only milestone.
- Depends on: REQ-007

### REQ-010 — A scripted client drives the real service, and an independent evaluator judges the result
- Requirement: The qualification is carried out by a runner that starts each case with a scripted client, invokes the real service and retains requests and output, and the judgment is made by an evaluator that derives the expected results from the task's source facts and equations instead of accepting the producer's own statements.
- Source: RV section 4 — "A runner is the small program that starts each case, invokes the real service, retains requests and output, and asks independent checks whether it succeeded. An independent evaluator determines expected results from the task's source facts and equations rather than accepting the producer's own claims."
- Source: RV section 4 — "This first scope uses scripted clients to qualify that machinery. It does not run a model comparison."
- Source: SC, "Oracle authority and independence" — the evaluator "must not import the OntoKin parser, normalized model, evaluator, exporter, sidecar producer or a route's scaffold to calculate expected answers. Route code and submitted metadata are observations to check, not oracle authority."
- Acceptance: The client's requests are fixed in the runner's source or inputs, and no language model takes part in any run of this scope.
- Acceptance: The code that computes expected values imports none of the OntoKin parser, normalized model, evaluator, exporter or sidecar producer, which an inspection of its imports shows.
- Acceptance: The runner's success statement for a case is the evaluator's result on the actual bytes; a success field in a response of the service is recorded and is not used as that result.
- Depends on: REQ-006, REQ-007

### REQ-011 — One documented command runs the qualification
- Requirement: One documented command runs the qualification of all three cases with their checks, rebuilds and controls, and concise usage instructions say how to run it and where its output goes.
- Source: RV R12 — "Deliver one documented command"; RV section 5, deliverables — "A reproducible qualification command and concise usage instructions."
- Source: RM, gate A1 — "a reproducible fresh-checkout path".
- Acceptance: The command is run through the checkout's `.venv/bin/python` and writes to a new or empty output directory outside the checkout.
- Acceptance: Its structured result states, for each case and each check, whether it passed, failed or was not run.
- Acceptance: The usage instructions name the prerequisites, the exact invocation and the files that a run writes.
- Acceptance: A run needs no model and no step done by hand between its start and its results.
- Depends on: REQ-005, REQ-010

### REQ-012 — A fresh store accepts each case's exact starting state (RV R01)
- Requirement: For each of V1, V2 and N1, a fresh store accepts the case's exact starting source and pinned dependency closure through the real Agent/0.2 service, and the accepted baseline artifact is generated and retained before the edit, for N1 as well.
- Source: RV R01 — "A fresh store accepts each case's exact starting source and pinned dependency closure through the real Agent/0.2 service. Generate and retain the accepted baseline artifact before each edit, including N1, so preservation checks are not vacuous. Record source, program and accepted revision identities."
- Source: RV section 4 — "Each case starts independently."; PR253 — "Each case starts from its own clean accepted source. N1 is not an extra repair turn within V1."
- Acceptance: Each case begins with an empty store that no earlier case or run has used, and with the starting entry and library that the corpus binds to it: `start_065` for V1 and N1, `target_075` for V2, and `hinges.ok` for all three.
- Acceptance: The record of each case holds the SHA-256 of every accepted source file, the program revision and the accepted revision identity, all taken before the edit.
- Acceptance: The baseline GLB bytes of each case are generated through the service, retrieved and retained before the edit, so that the later preservation check for N1 compares real bytes.
- Depends on: REQ-005, REQ-006, REQ-010

### REQ-013 — V1 and V2 change the intended occurrence and nothing else (RV R02)
- Requirement: In V1 the length of the first rack's middle finger changes from 0.65 m to 0.75 m and in V2 from 0.75 m to 0.65 m, through an accepted edit of that occurrence only, and inspection of the actual source shows that the shared library and every unrelated parameter are unchanged.
- Source: RV R02 — "V1 and V2 apply the intended occurrence edit. Actual source inspection proves that the shared library and unrelated parameters remain unchanged."
- Source: PR253 — "The candidate source may change only the selected occurrence initializer in OntoKin."; CO — the target path `first.fingers["middle"].length` and the lists of allowed and forbidden changes.
- Source: SC — "Changing the shared library or global length to make one target correct is a locality failure, even if some siblings happen to look unchanged."
- Acceptance: After the accepted edit, the bytes of `hinges.ok` and its import version and digest are identical to the starting ones, shown by comparison of the actual accepted files.
- Acceptance: The accepted entry source differs from the starting one only in the numeric length of the selected occurrence's initializer and equals the frozen endpoint that the corpus binds to the case.
- Acceptance: The observation is made on the source that the service holds as accepted after the edit, not on the request that was sent.
- Depends on: REQ-012

### REQ-014 — N1 is refused before acceptance and the accepted state is untouched (RV R03)
- Requirement: In N1 the candidate that assigns 0.75 kg to the length is refused with the required incompatible-dimension rejection at the acceptance decision on the staged candidate, and the accepted revision, the source and dependencies and the existing artifact bytes stay unchanged, with no invalid state accepted even temporarily.
- Source: RV R03 — "N1 returns the required incompatible-dimension rejection before acceptance. Accepted revision, source/dependencies and existing artifact bytes remain unchanged; no temporary accepted invalid state is permitted."
- Source: SC — "**N1's exact boundary is the acceptance decision on staged candidate source, before replacing any accepted revision, source file or artifact.**"
- Source: SC — "A rejection produced only by the common harness records protected accepted state, but does not satisfy the route-rejection predicate." and "Producing the 0.75 m answer instead is not success."
- Source: C255 — the diagnostic's code `incompatible-dimension`, the dimensions `length` and `mass`, and the distinct mechanisms `compiler`, `script_unit_validator` and `author_refusal`.
- Acceptance: The service's actual response to the N1 candidate is a rejection, and its retained diagnostic identifies an incompatible dimension with length expected and mass received; the record names the mechanism that produced it.
- Acceptance: After the rejection, the accepted revision identity, every accepted source and dependency byte and the baseline artifact bytes of REQ-012 are identical to those recorded before the candidate was submitted.
- Acceptance: The record of the exchange shows no accepted revision between the starting one and the end of the case.
- Acceptance: A run in which the 0.75 m answer is produced, or in which only the runner and not the service refuses the candidate, is recorded as a failure of N1.
- Depends on: REQ-012

### REQ-015 — Delivered GLB bytes are bound to the accepted source by a record that the producer cannot assert (RV R04)
- Requirement: The freshly exported and retrieved GLB bytes of each valid case are bound to the accepted source by an accepted-state record that the runner creates from the bytes it actually received and validated, and the checks reject stale source, stale artifacts and self-asserted acceptance.
- Source: RV R04 — "Freshly exported and retrieved GLB bytes are bound to the accepted source. Reject stale source, stale artifacts and self-asserted acceptance. A recorded digest alone cannot prove the acceptance history."
- Source: SC, "Rebuild, revision and locality checks" — "The external harness creates the accepted-state record from bytes it actually received and validated. Source/dependency/artifact hashes, model/settings, tool versions, immutable starting revision, candidate IDs and parent revision are recorded outside the author's editable directory. A submitted claim of acceptance is not authority."
- Source: ST — "authentic revisions" are listed among what is unqualified.
- Acceptance: For V1 and V2 the record holds the starting accepted revision, the candidate's identity and parent revision, the new accepted revision, the tool versions, and the SHA-256 of every accepted source, dependency and artifact byte sequence, and it is written outside the directory that the client can edit.
- Acceptance: The record is derived from the service's actual responses and the retrieved bytes; a digest or a statement of acceptance that the client supplies or that the artifact contains is not used as proof.
- Acceptance: Fields of the frozen record that have no value in this scope, such as the model and its settings, are recorded as not applicable to a scripted client and are not invented.
- Acceptance: The fault controls of REQ-019 show that a stale source, a stale artifact and a self-asserted acceptance are each rejected.
- Depends on: REQ-012, REQ-013

### REQ-016 — Independent checks cover every property that C253 requires (RV R05)
- Requirement: Independent checks cover all properties that C253 requires for each case: identities, dimensions, relationships, site values, actions and events, the permitted physical declarations, appearances and the unrelated content; a property without a trustworthy observation and comparison is reported as incomplete.
- Source: RV R05 — "Independent checks cover all properties required by C253: identities, dimensions, relationships, site values, actions/events, permitted physical declarations, appearances and unrelated content. Missing coverage remains explicitly incomplete."
- Source: SC, "Exact semantic invariants" — the 18 admitted identities matched by full stable occurrence key; the pinned library, the other typed parameters, the ownership map, the separate follows and hinges with their axes, limits and initial angles, the appearances, zero matter, the source duration, the actions and the event values; the selected blade's base site at `(-L/2, 0, 0)` metres and its dimensions `(L, 0.08, 0.08)` metres; and "Every other site's semantic value stays unchanged."
- Source: PR253 — "18 object identities; 34 sites; eight hinges; eight follows; two actions; the original two-second motion."; C255 — the semantic record's keys `units`, `frame`, `scene`, `objects`, `sites`, `follows`, `hinges`, `actions` and `events`.
- Acceptance: A table of results for each case lists every required property with the observation used, its origin in the actual source or artifact bytes, the independent derivation of the expected value, and the outcome.
- Acceptance: Objects are matched by full stable occurrence key; exactly 18 identities are present, with none missing, extra or duplicated, and definition identity is checked apart from occurrence identity.
- Acceptance: For V1 and V2 only the selected finger's length and the selected blade's consequences differ from the starting state; all 16 unrelated objects, among them all 11 of the second rack, keep their semantic values.
- Acceptance: Symbolic values, units, identities and relationship membership compare exactly, and source-level dimensions compare within the original 1e-12 m limit.
- Acceptance: A property for which no trustworthy observation and comparison exists is listed as incomplete with the reason, and the workflow is not reported as covering it.
- Depends on: REQ-009, REQ-010, REQ-013, REQ-015

### REQ-017 — Geometry and motion are decoded independently at all 126 poses (RV R06)
- Requirement: The actual geometry and motion are decoded independently from the delivered GLB bytes, and all 126 required poses, 18 objects at 0, 0.25, 0.5, 0.75, 1, 1.5 and 2 seconds, are checked against the independent equations with the unchanged source and delivery tolerances.
- Source: RV R06 — "Independently decode the actual geometry and motion. Check all 126 required object/time poses at 0, 0.25, 0.5, 0.75, 1, 1.5 and 2 seconds, using the unchanged source and delivery tolerances."
- Source: RV section 4 — "A changed length affects the selected blade's geometry and trajectory; correct text alone cannot pass."
- Source: SC, "Independent motion and geometry equations" — the equations for the angle, the centers and the selected blade's rotation, and the limits of 0.001 m, 0.001 rad and 1e-6 s for delivered geometry and motion.
- Source: SC, "Evidence from actual artifacts" — "For a route using GLB, read the real geometry attributes, transforms and time tracks." and "Every extracted field carries the artifact hash and its concrete native path or buffer/node reference."
- Acceptance: For each valid case, 126 pose records, one for each object and required time, are measured from the delivered GLB's own geometry attributes, transforms and time tracks, and each carries the artifact's SHA-256 and the place in the artifact from which it was read.
- Acceptance: Every pose agrees with the independent equations within 0.001 m for each position component, 0.001 rad of rotation angle and 1e-6 s, with a quaternion comparison that is sign-invariant after a finite, nonzero norm check.
- Acceptance: Box dimensions are established from corner positions, and sphere geometry from the declared radius and the finite mesh envelope; a bounding box alone or a sidecar's statement establishes neither.
- Acceptance: Nonfinite values, zero quaternions, reflections, unintended scale or shear, and duplicate time or identity records make the artifact fail; an invalid artifact is not normalized into a passing one.
- Acceptance: The result is described as agreement at seven sampled times, not as proof of continuous motion or dynamics.
- Depends on: REQ-015

### REQ-018 — The delivered source rebuilds cleanly in an empty workspace (RV R07)
- Requirement: The delivered accepted source of each valid case is rebuilt in an empty workspace that contains only the declared inputs and the pinned tools, and the rebuild meets the frozen OntoKin route's semantic, measurement and byte-identity requirements, with no undeclared checkout file and no retained artifact supplying the result.
- Source: RV R07 — "Rebuild from the delivered accepted source in an empty workspace containing only declared inputs and pinned tools. Meet the frozen route's semantic, measurement and byte-identity requirements. No undeclared checkout file or retained artifact may supply the result."
- Source: SC — "Rebuild the final source in a fresh empty workspace with only the declared dependency closure and pinned tools. Require the same normalized semantic values and delivered measurements. Require byte identity for artifacts whose frozen route settings promise it; predeclare any native timestamp-only normalization before trials and retain raw bytes. Never whitelist a varying field after seeing a failed rebuild."
- Source: C210 — "Same exact source bundle, implementation, GLB export settings and environment must produce identical GLB bytes for this proof."
- Source: C255 — for the bound OntoKin source closure the declared inputs are exactly `hinges.ok` and `main.ok`, and the determinism is `byte-exact`; CO — `ambientResolutionAllowed` is false.
- Acceptance: The rebuild's workspace is new and empty before the declared inputs are placed in it, and a listing of its contents and of the tools' identities (interpreter, package revision or build, and their hashes) is retained.
- Acceptance: The rebuild uses no file of a checkout except through the pinned tools and no artifact retained from the delivery run, which the retained listing and the recorded working directory, environment and invocation show.
- Acceptance: The rebuilt artifact passes the same checks as the delivered one (REQ-016, REQ-017) and is byte-identical to it under the same source bundle, implementation, export settings and environment.
- Acceptance: A difference between the rebuilt and the delivered bytes is a failure of this requirement; no varying field is exempted after the difference has been seen.
- Depends on: REQ-015, REQ-016, REQ-017

### REQ-019 — Deliberate faults show that the checks reject wrong results (RV R08)
- Requirement: Deliberate faults demonstrate that the checks reject wrong-part edits, changed siblings, incorrect motion, stale provenance, accepted invalid candidates, missing output and inconsistent rebuilds; controls that are already qualified are reused, and only the necessary gaps are implemented.
- Source: RV R08 — "Deliberate faults demonstrate that the checks reject wrong-part edits, changed siblings, incorrect motion, stale provenance, accepted invalid candidates, missing output and inconsistent rebuilds. Reuse qualified controls; implement only necessary gaps."
- Source: SC, "Required oracle controls before runner admission" — the list of faults, the positive controls for quaternion sign equivalence and legitimate revision-bound provenance changes, the boundary controls, and "A large check count is not evidence that the chosen oracle is scientifically correct."
- Source: RM, gate A1 — "Positive and negative oracle controls".
- Acceptance: For each of the seven kinds of fault that RV names, at least one executed control presents the fault to the workflow's own checks, and the retained result shows the rejection with its reason.
- Acceptance: Positive controls show that independently correct 0.65 m and 0.75 m states are accepted, including an equivalent quaternion sign and a legitimate change of provenance after a valid edit.
- Acceptance: The report states, for each fault that SC lists beyond those seven, whether an existing qualified control covers it or whether it remains open; none is assumed covered without that statement.
- Acceptance: The controls are labelled as evaluator controls; none is counted as a case outcome, as a model attempt or as a new fixture of the frozen corpus.
- Depends on: REQ-014, REQ-015, REQ-016, REQ-017, REQ-018

### REQ-020 — An external record retains every outcome and exchange, with failure and retry exercised (RV R09)
- Requirement: A record kept outside the service and outside the client's editable directory retains every case outcome, the actual sequence of requests and responses, the diagnostics and the artifact identities, and the service's failure and retry handling is exercised by executed protocol cases.
- Source: RV R09 — "An external record retains every case outcome, actual request/response sequence, diagnostics and artifact identities. Failure and retry handling are exercised. Do not present inert classification examples as executed attempts."
- Source: AG, check table, row "Agent interface" — "Execute actual protocol cases, including failure/retry; schemas are insufficient."
- Source: RM, gate A1 — "complete attempt accounting, source/artifact identity"; PR253 — "Preserve all candidate, failed, missing and timed-out artifacts."
- Acceptance: For every started case of every run, the record holds the outcome, each request sent and each response received in order, every diagnostic, and the SHA-256 and size of each source and artifact byte sequence involved.
- Acceptance: A case that fails, times out, crashes or produces no output keeps its record; no started case is removed or replaced.
- Acceptance: The executed protocol cases include at least one failure and one retry, for example an identical retry of a request, a retry with a changed payload or an edit against a stale revision, and their actual responses are retained.
- Acceptance: Examples made with C255's `classify_attempt` helper or with other inert records are labelled as inert controls and appear in no count of executed cases.
- Depends on: REQ-010, REQ-012

### REQ-021 — A fresh replay reproduces the expected results (RV R10)
- Requirement: A fresh replay, that is a new execution of the documented command that starts from empty stores and uses no result of an earlier run, produces the expected results for V1, V2 and N1.
- Source: RV R10 — "A fresh replay produces the expected results."
- Source: RM, gate A1 — "a reproducible fresh-checkout path".
- Source: C210 — "Same exact source bundle, implementation, GLB export settings and environment must produce identical GLB bytes for this proof."
- Acceptance: The replay is run at the candidate's exact revision, after the candidate is final, with an output location that holds nothing from an earlier run.
- Acceptance: Its case outcomes and per-property results equal those of the run whose evidence is delivered, and its GLB bytes equal the delivered ones under the same source bundle, implementation, export settings and environment.
- Acceptance: The replay's own record is retained beside the first run's record, including any difference that was found.
- Depends on: REQ-011, REQ-018, REQ-019, REQ-020

### REQ-022 — The regenerated GLBs are validated and an actual playback is inspected (RV R10)
- Requirement: The applicable GLB validation is completed for the regenerated GLBs, and the actual playback of a regenerated animation is visually inspected with the prepared tools; the observation and the disclosed losses are retained.
- Source: RV R10 — "Complete applicable GLB validation and visual inspection using the prepared tools; retain the actual playback observation and disclosed losses."
- Source: RV section 5, deliverables — "Visual verification for the selected output and explicit transport limitations."; RV section 8 — "Produce actual regenerated source/artifact evidence and an inspected playback."
- Source: AG, check table, row "Exporter/viewer" — "Fresh source-to-GLB builds, independent Khronos/Three.js checks, visual inspection" under OK-ENG-002.
- Source: E2 section 6.2 — actual destination playback establishes that "The emitted GLB loads and its animation is usable in the named destination/configuration."; visual inspection does not establish "Numerical correctness by appearance alone."
- Acceptance: Each regenerated GLB that the scope delivers passes the independent Khronos validator and Three.js checks at the committed tool versions, and the reports are retained with the SHA-256 of each GLB.
- Acceptance: The regenerated animation of at least one edited case is loaded and played from its actual bytes in a named viewer configuration, and a retained observation states which file was played, at which times it was looked at, and what was seen.
- Acceptance: The observation is made by looking at the rendered playback; it is not derived from the numerical results and is not offered as proof of numerical correctness.
- Acceptance: The losses and limits of the transport are stated with the result: the GLB holds sampled motion, and live physics, collision response and the execution of actions in a destination are unsupported.
- Depends on: REQ-015, REQ-023

### REQ-023 — The visual-verification profile is prepared as a dependency of the playback check
- Requirement: The `visual-verification` profile of the owner's environment is prepared as LOCAL-SETUP describes, and only as far as the validation and the playback inspection of REQ-022 need it.
- Source: RV section 5 — "The remaining visual profile is a concrete dependency when fresh playback verification is selected. It does not justify redoing the completed migration, adding Docker or reconstructing a past disposable host."
- Source: ENV — the profile holds Node.js 22 and npm, the npm dependencies of `tools/package-lock.json` and Playwright's Chromium headless shell; "The setup tool does not install Node.js. Install Node.js 22 with the machine's existing mechanism"; "`npm ci` **replaces** an existing `tools/node_modules`."
- Source: G — at capture the doctor reports the profile as mismatch, because Node.js v25.9.0 is installed.
- Source: WF, PROTOCOL section 2 — "Tools: authorized only; no destructive probes/unnecessary installations."
- Acceptance: Before the checks of REQ-022 are run, the doctor reports `visual-verification` as ready for the checkout that runs them, and that report is retained.
- Acceptance: The preparation installs nothing beyond what the profile names, changes no committed lock, pin or npm file, and leaves `core` and `python-verification` ready.
- Acceptance: The record states what was installed on the owner's machine, by which mechanism and at which version.
- Acceptance: If the profile cannot be made ready, REQ-022 is recorded as not met with that reason, and no visual result is claimed.
- Depends on: REQ-005

### REQ-024 — The checks that the changed scope requires are run
- Requirement: The checks that the actual changed scope requires are run fresh on the owner's prepared environment: the runtime gates for runtime work, executed failure and retry cases for agent-interface work, independent GLB checks and visual inspection for fresh exporter or viewer work, and the documentation and workflow checks for the records.
- Source: RV section 5, step 5 — "Run checks required by the actual changed scope. Runtime work follows runtime gates; agent-interface work includes failure/retry cases; fresh exporter/viewer work includes independent GLB checks and visual inspection."
- Source: AG, "Verify the actual change" — the check table and "Select checks for actual scope".
- Source: WF, PROTOCOL section 5 — durable evidence names the source revision, the input hashes, the environment, the command, the settings, the artifacts, the outcome and the logs, and distinguishes passed, failed and not run.
- Acceptance: The record lists the files that the scope changed and, for each row of the AGENTS check table under which those files fall, the command run, the revision, the executor and the outcome.
- Acceptance: Every check is run on the candidate's exact revision; a result from another revision is reused only after the identities of implementation, dependencies, fixtures, tests, command and environment are established as equal.
- Acceptance: A check that was not run is recorded as not run, with the reason.
- Depends on: REQ-005

### REQ-025 — A failing required check is compared with main on the same host
- Requirement: A required check that fails is compared with main's run of the same check on the same host; a failure, error or skip that main shows too, with the same test ID and reason, is recorded as a known baseline, and only a new or worsened failure blocks integration.
- Source: RV section 3 — "The latest integration rule allows known main failures when branch and current-main runs show the same test ID and reason on the same host. Only new or worsened failures block integration. Preserve both results. A failing endpoint required by this new task still prevents claiming that endpoint passed. Integration eligibility and product qualification are different decisions."
- Source: RV section 5, step 6 — "Compare any required failing check against current main on the same host. Do not add unrelated baseline repairs to this scope."; RV R11 — "Applicable main integration checks pass or are classified against the recorded same-host baseline under current policy."
- Source: AG — "Use main's recorded run, or run main once if none is recorded. Keep both results." and "Fixing main's known failures is separate work, never a precondition of another branch."
- Acceptance: Both runs, the branch's and main's, are retained with their revisions, the host, the temporary-directory setting and the outcome of each test.
- Acceptance: Each failure of the branch's run is classified as a known baseline, with the same test ID and reason on main, or as new or worsened; a new or worsened failure blocks integration until it is resolved.
- Acceptance: No repair of a known baseline failure is part of this scope's changes.
- Acceptance: A check that fails and that this document requires for one of its own results is not reported as passed for that result, whatever the baseline shows.
- Depends on: REQ-024

### REQ-026 — An independent reviewer checks the exact candidate and its evidence (RV R11)
- Requirement: An independent reviewer, that is a separate worker with fresh context, checks the exact candidate and the acceptance evidence against the requirements of this document, and mandatory findings are resolved and reviewed again before integration.
- Source: RV R11 — "Independent review checks the exact candidate and acceptance evidence."
- Source: WF, ROLE — "Independence requires an actual separate worker inspecting the candidate. Without subagents, work sequentially, label self-review and leave required independent review unmet."; PROTOCOL section 5 — "Resolve mandatory findings; re-review affected changes; self-review cannot close this gate."
- Source: SC — "Before scoring any trial, a separate reviewer must approve an oracle implementation and its fault controls against the raw source and equations." and "Review the formulas and controls independently from their implementation."
- Acceptance: The review record names the reviewer, the exact commit reviewed, the acceptance criteria applied and the findings.
- Acceptance: The review covers the evaluator's formulas and fault controls against the raw source and SC's equations, not only the behavior of the code.
- Acceptance: Every mandatory finding is resolved and the affected change is reviewed again; a self-review is labelled as such and does not meet this requirement.
- Depends on: REQ-021, REQ-022, REQ-024, REQ-025, REQ-028, REQ-029

### REQ-027 — The reviewed work is integrated, the resulting main is verified and the branch is resolved
- Requirement: The reviewed work is integrated into main under the current ownership rules, the resulting main is verified with the applicable checks, and the completed branch is resolved with its history retained.
- Source: RV section 5, step 7 — "Obtain independent review, integrate completed work under current ownership rules, verify resulting main and resolve the completed branch. Keep durable failures and explicit incomplete acceptance."
- Source: WF, PROTOCOL section 7 — one branch for each bounded scope; writes to main by the verified lease holder only; "conditional nonforce update or protected expected-head PR merge; read back actual merge commit/tree; applicable resulting-main checks"; deletion of a completed branch only after its retained history, its integration and its latest head are verified.
- Source: AG — OK-ENG-009 governs development integration "separately from finite release acceptance".
- Acceptance: The scope's work is on its own branch, and main receives it by a conditional, non-forced update or a protected expected-head pull-request merge, made by an agent that holds the main-integration lease, acquired against the observed head and released afterwards.
- Acceptance: The actual merge commit and tree are read back from the remote, and the checks that apply to the resulting main are run on it and recorded, with known baseline failures classified as in REQ-025.
- Acceptance: The disposition of the branch is observed and recorded, with its history retained.
- Acceptance: The integration record says that integration is neither release acceptance nor product qualification.
- Depends on: REQ-026

### REQ-028 — The stated deliverables are provided (RV R12)
- Requirement: The scope delivers the documented command with its usage instructions, the accepted before and after source bundles with exact dependency identities, the newly generated GLBs, the retained evidence of the invalid candidate, the actual service exchanges, the independent per-property results, the control outcomes, the clean-rebuild evidence, the visual verification, the retained failures and a short human-readable report.
- Source: RV R12 — "Deliver one documented command, editable sources, regenerated GLBs, structured results, retained failures and a short human-readable report."
- Source: RV section 5, deliverables — the six listed items, and "A large test count is not the deliverable. The deliverable is a correct, inspectable workflow and evidence for its stated limits."
- Source: WF, HANDOFF's local section — "Exact bytes, identities and a durable location; failures and not-run checks included."
- Acceptance: Each listed item exists at a durable location that the report names, with its SHA-256 where it is a file of evidence.
- Acceptance: The source bundles are editable `.ok` files with their pinned library, and each carries the program revision and the accepted revision to which it belongs.
- Acceptance: The structured results are machine-readable and hold, for each case, the outcome and the per-property results, and for each control its outcome.
- Acceptance: The report is short, is written for a reader who has not followed the work, and states for each requirement of this document whether it is met, partly met or not met, with a pointer to the evidence.
- Depends on: REQ-011, REQ-012, REQ-013, REQ-014, REQ-015, REQ-016, REQ-017, REQ-018, REQ-019, REQ-020, REQ-021, REQ-022

### REQ-029 — The report states the completed criteria and the remaining A1 and pilot prerequisites (RV R12)
- Requirement: The report includes a compact readiness table with this workflow's completed criteria, the actual remaining prerequisites of the pilot and one next action, and it states the remaining dependencies of the roadmap's A1 gate without claiming full A1, C260 qualification or product acceptance.
- Source: RV R12 — "State remaining A1 dependencies without claiming full A1, C260 or product acceptance prematurely."
- Source: RV section 5, deliverables — "A compact readiness table: this workflow's completed criteria, actual remaining pilot prerequisites and one next action."; RV section 8 — "Report completed criteria, failures and precise remaining A1/pilot prerequisites."
- Source: RV section 4 — "The broader A1 roadmap gate includes more than this OntoKin-only path. Qualifying it is useful progress, while a direct-tool baseline and other pilot-admission requirements remain separate."; RP — the blocking requirements of `executionAdmission`.
- Acceptance: The table lists RV's criteria R01 to R12 with their state, and each blocking requirement of the frozen run plan with its state after this scope.
- Acceptance: The table names exactly one next action, and the report presents it as a proposal to the owner, not as a selected scope.
- Acceptance: The report contains no statement that A1 is complete, that C260 is qualified, that the product or a release is accepted, or that an authoring advantage is shown.
- Depends on: REQ-028

### REQ-030 — The scope closes on the local closing state
- Requirement: The scope closes under the existing local workflow with a source checkpoint, truthful task and session records, a verified publication state, retained evidence and a concise closing report; no browser handoff ZIP is made for it.
- Source: RV section 5, step 8 — "Close under the existing local workflow with a source checkpoint, verified publication state, retained evidence and a concise closing report. Ordinary local development does not require recreating browser handoff ZIP cycles."
- Source: WF, HANDOFF's local section — the four closing items, and "**Local scope completion** needs all task acceptance, verified integration and resulting main, observed branch and worktree disposition, and a closing report."
- Acceptance: The task's `task.json` agrees with the actual acceptance of each requirement, the session checkpoint follows the session template, and CURRENT points to both.
- Acceptance: The push state is read from the remote and recorded; offline, it is recorded as unconfirmed.
- Acceptance: STATUS and CURRENT state the result and the next unmet gate concisely, and the lease is recorded as released.
- Acceptance: The task is recorded as done only when all its acceptance, the verified integration and resulting main, the observed disposition of branch and worktree, and the closing report exist; otherwise it stays `in_progress`, `blocked` or `review` with one exact next action.
- Depends on: REQ-027

### REQ-031 — Results are described within their limits
- Requirement: Every statement of a result describes the animation as source-defined with recorded playback, names the one previously exposed assembly family on which it was obtained, and claims no destination, physics, generality or advantage that was not tested.
- Source: RV section 2 — "Describe the result as source-defined animation with recorded playback. Metadata and playback do not prove live destination constraints or collision simulation." and "Reuse its lessons without claiming general lossless Blender support or completed Unreal/Godot support."
- Source: RV section 4 — "They qualify tools using one previously exposed assembly family. They are not an unseen test of general creative ability."; RV section 7 — "state exactly what an agent can create or edit, which profiles and destinations were tested, and what remains unsupported."
- Source: PR253 — "The independent assembly-family count is one."; SC — "Seven-time success establishes only this finite sample, not arbitrary continuous motion or dynamics."
- Source: AG — "Claim no untested destination, universal numerical accuracy, unrun benchmark/job or whole-product coverage from a small corpus."
- Acceptance: The report and the status text name what was exercised (construction-0.1 source, Agent/0.2 and GLB/0.2) and the executor (the owner's macOS arm64 environment).
- Acceptance: They say that the three cases belong to one public, previously used family and that a scripted client, not a model, made the edits.
- Acceptance: They contain no claim about live destination constraints, collision simulation, support in Blender, Unreal, Godot or OpenUSD, continuous-time accuracy, or an authoring advantage.
- Acceptance: A historical result that is cited keeps the revision and environment on which it was obtained and is not presented as a result of this scope.
- Depends on: REQ-028

### REQ-032 — No model comparison is launched and nothing is expanded
- Requirement: The scope launches no model comparison and no trial attempt, and it expands neither the language nor the physics, the transports or the backends.
- Source: RV section 8 — "Do not automatically launch the model comparison or expand the language, physics, transports or backends."
- Source: RV section 6 — "Do not start these runs simply because a schedule exists: the plan still contains unfilled model/route admission fields."; RP — "Null is a blocker, never a wildcard or instruction to guess."
- Source: RV section 7 — the deferrals; GL — the deferred domains, among them "model training, MCP transport, simultaneous backends".
- Acceptance: No run of this scope calls a language model, and no record of this scope is an attempt in the sense of the frozen run plan.
- Acceptance: The run plan's fields for the model, the route inputs and the qualified routes are unchanged after this scope, and no model pin, seed or token count is invented.
- Acceptance: The scope's changes add no language feature, shape syntax, physical behavior, protocol version, transport or export target; a change of that kind that the work finds necessary is recorded as a finding for the owner and is not made.
- Depends on: None.

### REQ-033 — Failures and unmet criteria stay visible
- Requirement: Failures, interruptions, checks that were not run and criteria that are not met are retained and reported as such; no criterion is recorded as met without its evidence, and no expectation is changed to make a check pass.
- Source: RV section 5, step 7 — "Keep durable failures and explicit incomplete acceptance."; RV R05 — "Missing coverage remains explicitly incomplete."
- Source: AG — "Never change expectations to pass tests." and "Expose unsupported behavior, loss, failure, stale results."
- Source: WF, ROLE — "Never silently reduce unmet requirements or claim unexecuted operations."
- Acceptance: The evidence holds every failed run, failed control and failed check of the scope with its output, beside the later passing one where there is one.
- Acceptance: Each requirement of this document is reported as met, partly met or not met, and a requirement without retained evidence is reported as not met.
- Acceptance: If the scope stops before all criteria are met, the task stays open with the unmet criteria listed and one exact next action, and the scope is not reported as complete.
- Depends on: None.

### REQ-034 — The effort stays in proportion to the change
- Requirement: The effort of each check and gate stays in proportion to what it checks: when checking would cost far more than the change it checks, the owner is told plainly before the work goes on, and necessary gap work is done inside this task and not as separate milestones.
- Source: AG, owner direction of 2026-11-28 — "When checking would cost far more than the change it checks, tell the owner plainly before going on."
- Source: RV section 4 — "Do not turn each into another unbounded chain of standalone documentation milestones."; RV section 5 — "A large test count is not the deliverable."
- Source: AUD, the owner's decision of 2026-11-28 — the owner judged C271's eight days of pre-merge work "out of proportion to the task"; WF, PROTOCOL section 4 — "no repeated capability-only phases".
- Acceptance: Before a verification or pre-merge step whose cost is far larger than the change it checks is continued, a plain statement to the owner names the step, its estimated cost and the ordinary alternative.
- Acceptance: The task's plan has no phase whose only result is a record of capability, readiness or audit that no requirement of this document needs.
- Acceptance: The report does not offer the number of tests or checks as evidence of correctness.
- Depends on: None.

## Decisions

- D01 — One document for one scope. RV asks to treat it "as the proposed selection of one new scope" and separates that scope from what follows it. This document therefore carries the first scope only. The later stages are listed under "Out of scope" with RV's conditions; they are not requirements here, and the report names them as remaining prerequisites (REQ-029).
- D02 — RV is a review that the owner supplied. Its statements about the first scope are captured as requirements because the owner made it the subject of this document. They are settled by the owner's approval of this document, not by this capture. Each checkable statement was compared with the repository at the reviewed revision and with live GitHub; the table "RV's statements checked at capture" gives the result. None was contradicted. One fact that RV does not mention was added: the clone is six commits behind the remote main and holds uncommitted files (REQ-001).
- D03 — No selection is recorded. RV calls itself a "proposed local-agent assignment", CURRENT says that the owner chooses the next scope, and LOCAL-START-HERE tells a session with no selected scope to report the state and ask. The invocation of to-trd asks for requirements. This document therefore treats the selection as a separate act of the owner (REQ-002), and its approval approves the requirements only.
- D04 — How RV's parts map to this document's requirements:

| RV | This document |
| --- | --- |
| R01 to R09 | REQ-012 to REQ-020, in the same order |
| R10 | REQ-021 (fresh replay), REQ-022 (validation and inspected playback), REQ-023 (the profile that they need) |
| R11 | REQ-026 (independent review), REQ-025 (classification against main's baseline) |
| R12 | REQ-011 (the command), REQ-028 (the deliverables), REQ-029 (remaining dependencies) |
| Section 3 | REQ-003, REQ-004, REQ-025 |
| Section 4, reuse and gaps | REQ-006 to REQ-010 |
| Section 5, steps 1 to 8 | REQ-001, REQ-002, REQ-005, REQ-024, REQ-025, REQ-026, REQ-027, REQ-030 |
| Sections 2, 6, 7 and 8, limits and deferrals | REQ-031 to REQ-034 |

- D05 — Where the frozen contract is more exact than RV's short wording, the frozen wording is used. RV says "Preserve the frozen contract" and "Read the applicable contracts before connecting these modules." This applies to N1's boundary and diagnostic (REQ-014), the accepted-state record (REQ-015), the tolerances and equations (REQ-016, REQ-017), the byte identity of the rebuild (REQ-018) and the list of faults (REQ-019). Acceptance lines that go beyond the words of a source only make a sourced requirement observable; they add no new outcome.
- D06 — "Fresh replay" in R10 is read as a new execution of the documented command from empty stores, with no result of an earlier run (REQ-021). The other possible reading, a replay of the retained request sequence against a fresh store, is the same act here, because the scripted client's requests are fixed. The playback of the animation is covered separately by REQ-022.
- D07 — "External record" in R09 is read with SC: a record that the runner keeps outside the service under test and outside the directory that the client can edit (REQ-020). Driver and validation output is first written outside every checkout (REQ-005). The evidence that the scope publishes is then committed at a durable location in the repository, as PROTOCOL section 5 and HANDOFF's local section require (REQ-028). The plan chooses the places.
- D08 — "Applicable residual controls" in RV section 4 is read as RV's own next words say: controls that are "dependencies of this executable workflow". A residual control applies when a check that this workflow uses for one of its requirements depends on the property that the control covers. REQ-009 requires the reason to be recorded in both directions. For H24, C269 allows "an explicit decision or a bounded additional control"; this document takes no such decision. If the workflow depends on that property, the bounded control is added; if it does not, the gap stays reported as open.
- D09 — What the one command covers. RV's deliverables name "A reproducible qualification command and concise usage instructions." REQ-011 requires it to run the cases with their checks, rebuilds and controls (REQ-012 to REQ-020). Whether it also starts the format validation of REQ-022 is left to planning, because that validation needs the tools of another profile. The visual inspection is an observation of rendered playback and cannot be the result of a command.
- D10 — Which output is inspected. RV asks for "an inspected playback", and its deliverables name "Visual verification for the selected output and explicit transport limitations." REQ-022 requires the playback of at least one edited case to be inspected and the report to say which file it was. The choice of that case is left to planning.
- D11 — Node.js 22. The visual profile needs Node.js 22, which is not on the owner's machine at capture, and LOCAL-SETUP's setup tool does not install it. This document records the dependency (REQ-023) and gives no authority to install anything. The installation changes the owner's machine; it is made only as part of the selected task, with the mechanism that the machine already uses, and it is recorded.
- D12 — No model takes part in this scope. The fields of SC's accepted-state record that describe a model are therefore recorded as not applicable (REQ-015). The outcomes of the scripted cases are recorded completely (REQ-020), and they are not attempts of the frozen run plan (REQ-032).
- D13 — The correction of current-status text (REQ-004) belongs to this scope, because RV places it at the start of the work. Whether it travels in its own small pull request or with the scope's branch is left to planning.
- D14 — Left to implementation planning, within the requirements: the task's ID, its branch name and its evidence directory; the names and places of the runner, the evaluator's new parts, the controls and the records; whether the runner drives the JSONL service or the Python class; how the empty workspace of REQ-018 is built (LOCAL-SETUP's package-smoke procedure is one existing way to run an installed package from an empty directory); which protocol failure and retry cases are executed beyond the minimum of REQ-020; the number of workers and reviewers, provided that the reviewer of REQ-026 is independent; the form of the retained visual observation; whether the short report of REQ-028 and the closing report of REQ-030 are one document; and whether one plan or several are made from this document. None of these changes what the owner receives or how success is recognized.
- D15 — This document is a requirements source, not a second ledger. The task's own `REQUIREMENTS.md`, `PLAN.md`, `task.json` and session checkpoints remain the record of progress (PROTOCOL section 3). They may carry these requirements with their IDs, as the local migration did, and they cite this document by its identifier, revision and SHA-256.

## Open questions

None.

## Not yet specified

None.

## Assumptions

- Accepted: "The local development agent" in RV is a session that works in local mode in the owner's persistent clone. Basis: RV section 5 starts "from LOCAL-START-HERE.md and the actual local checkout".
- Accepted: "The real Agent/0.2 service" in R01 is the existing program-bundle service of protocol `ontokin.agent/0.2`, as `ProgramAgentService` or as the explicit JSONL service. Basis: RV's reuse table names both.
- Accepted: "The frozen route" in R07 is the OntoKin route of the C253 protocol: construction-0.1 source, Agent/0.2 accepted edits, GLB/0.2 and the semantic sidecar. Basis: the route table of PR253.
- Accepted: "One finger occurrence" in RV's case table is the first rack's middle finger, `first.fingers["middle"]`. Basis: PR253 and the target path in CO.
- Accepted: "The recorded same-host baseline" in R11 is main's recorded run on the owner's Mac, or one run of main on that host when no applicable run is recorded. Basis: AG, the rule of 2026-11-28.
