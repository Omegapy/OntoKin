# C271 P07 — staged qualification plan

**Freeze type:** reviewed design of later work, not an executable plan. The companion JSON has `executable: false`. No actual host path, executable destination, inspected loader closure, future implementation revision, operational configuration digest or runtime fixture identity is invented here.

This schedule preserves the adopted Gate H and Gate R requirements. It decomposes the first unmet prerequisite so the next implementation is bounded and reviewable. Each numbered stage is a separately selectable future phase/checkpoint; this document does not start them. P06-H01/H02/H03 remain unexecuted, as do the original seven outcomes and complete routine. C271 R01/R02 stay done; R03–R05 stay not_done. [S01–S07; S23]

## 1. Gate schedule and stop points

| Stage | Entry evidence | Authorized work in a future selected phase | Acceptance and stop |
| --- | --- | --- | --- |
| `HI` — authoring implementation | Independently accepted P07 design, reconciled source, new confirmed early recovery | Add the one inspection module and focused tests; implement strict plan/read/path/ELF-map/ldd-parser/evidence contracts; static and filesystem controls; labelled mocks for process outcomes. No Node/ldd or original methods. | Exact implementation source and focused evidence independently accepted; all mandatory findings resolved; publish and save partial handoff. Stop before runtime installation or observation. |
| `H0` — static preparation and review | Accepted clean HI candidate; authenticated P05 Node archive and unchanged C195 dependency archive; actual host files available | Prepare exact install plans with independently frozen archive/member inventories; use existing preparer dry-run/apply as selected; inspect actual source/Python/ldd/loader input files without running Node/ldd; freeze the exact executable inspection plan and separate review digest. | All paths/identities/absence guards and expected commands concrete; independent static review accepts complete closure and fresh evidence paths. Stop before observation. Missing or unexplained closure is a specific blocker. |
| `H1` — host observation | Exact H0 inspection-plan descriptor/digest, unchanged admitted inputs, no unresolved previous attempt | Run the two plan commands once, in order, using the new module and bounded original supervisor. Retain every actual attempt and cleanup record. | Both compatible success inspections plus candidate HOST and complete immutable failure/success ledger; independent review accepts observations only. Stop before any probe/checker. |
| `H2` — operational freeze | H1 evidence, same boot/runtime/source, all unchanged scientific/dependency inputs | Author real source/dependency/method/discovery records and a P06 configuration; freeze all qualification controls/fixtures/commands and a separate expected-config digest. Recheck static consumer compatibility. | Independent author/reviewer accepts exact positive and negative inputs, expected stage/code/start counts, source/script/loader identities and paths. No unfilled fields. Stop before qualification. |
| `H3` — actual Gate H | Exact H2 qualification execution plan and approved config; all H1 bindings fresh and unchanged | Perform the frozen syntax check, direct-probe controls and original seven-method cohort; execute any separately frozen boundary controls; independent numerical/process/outcome audit. | All selected controls and original seven outcomes pass their own predicates with complete cleanup/evidence. Independently decide Gate H only. Stop before full routine. |
| `R` — complete routine / R03 | Accepted actual Gate H; separately reviewed whole discovery/stage plan and justified outer timeout | Capture actual complete discovery without running methods; reconcile against baseline plus approved additions; run every unchanged required default driver stage on its isolated source; perform documentation/workflow checks; independently audit all outcomes. | Every required original/additional method and stage complete with no missing/skip/expected-failure obligation, source preserved, no unresolved process/evidence. Independent R03 acceptance. Stop before integration. |
| `R04` / `R05` | All own preceding gates | Director's later leased integration, actual-main verification, branch disposition and final saved delivery/closure | Separate obligations; outside this P07 plan's execution authorization. |

Each future execution phase uses one fresh attempt ID and fresh no-replace paths. A failed or unknown command stops that stage; it is retained, never silently repeated. New attempts require reconciled state, unchanged or separately reviewed inputs and a new approved plan/path. A planned pause is not itself a blocker. [S01 §8; repository PROTOCOL/HANDOFF]

## 2. Real fields required before H0/H1

The static inspection-plan template cannot be executed. Before approving H1, fill and independently verify:

- Clean implementation commit/tree and canonical source root; complete immutable source inventory including the authoring entry point and all tests; exact governing P05/P06 descriptors.
- Actual resolved Python executable, version, startup/runtime input inventory, exact seven package metadata/pin records and later qualification interpreter compatibility.
- Exact recovered Node archive and its static install plan/receipt; absolute task-specific installed executable; unchanged candidate digest/size/mode. The prior shared-runtime path is source provenance, not an approved destination.
- Exact C195 dependency archive/member inventory and install plan/receipt; destination containing precisely the retained 24 files and necessary directory modes; unchanged versions and loader source/layout.
- Actual boot/platform/libc/kernel/architecture; complete inspector/shebang/ELF/loader/alias/file closure and static resolution-map rationale; relevant search/config/cache files and required absences; all finite unsupported-case decisions.
- The two literal argv arrays, exact cwd/labels/environment, fixed limits, expected one direct start each, output predicates and no retry rule.
- Existing external evidence parent; all ancestor identities; absent per-command/attempt output paths; separately approved outer failure capture and reconciliation procedure.
- Separate independent review identity/decision and plan descriptor; the exact expected digest supplied by the selected invocation, outside the plan.

No `TODO`, null, wildcard, shell expansion, generated approval token, guessed hash, generic candidate path or unresolved host field is admissible in the executable inspection plan. The selected interpreter/inspector closure must be bound before its observation commands are used. H1 cannot authorize a new executable after observing it. [S01 §§3–6; S06; S08–S11]

## 3. Real fields required before H2/H3

The executable **qualification** plan is separate from the inspection plan. It must bind:

1. H1 plan/review, raw logs, actual process receipts, successful inspection documents and HOST descriptor, with all failed or unknown earlier attempts still enumerated.
2. Exact P06 configuration path/bytes/mode/digest, whose `parent` is null; exact source/contract, host, runtime, dependency and method/discovery descriptors; existing external evidence parent. Its externally selected digest must be preserved when tests or probe-negative fixtures mutate other documents.
3. Every actual command and its own expected direct process counts, route, bounded cwd, argv, environment, outer timeout and result/failure paths. Node flags, loader and final `--job` layout match current source.
4. Independently constructed positive and mutated fixture bytes and their SHA-256/size/mode inventory. The independent author records each mutation against the corresponding positive input, all unchanged companion bytes, and the exact expected rejection stage/message/code from the inspected source. The executor must not choose the oracle after seeing a result.
5. Which prior P06 controls are reused, with exact implementation, fixture, environment, command and dependency identity comparison. Reuse is decided per control. A prior mock/static result is never reused as actual H1/H3 behavior.
6. Runtime-discovery collector, unittest outcome collector and independent numerical-audit harness source identities. These tools must be reviewed and source-inventoried before use; no untracked harness or unbound result synthesizer is admitted.
7. A frozen control subcase table. Every row has a stable ID, route, input descriptors/mutation, expected rejection/acceptance stage, exact error selector, expected start counts, artifact requirements and cleanup/evidence predicate. Design rows that still list variants are not executable rows.

The next implementation scope is HI only. Adding a general execution-plan runner, redesigning the existing test result protocol, changing tests to accommodate a host or expanding the supported platform is outside HI. If exact H2 requirements need further tooling beyond the already identified observational harnesses, freeze that smaller implementation scope in a later phase before H3. [S01; S07; S12]

## 4. Process denominators

For a **single successful minimal H1 + H3 path**, before any extra separately frozen fault-control attempts:

| Kind | Direct Node launches | Direct ldd launches | Meaning |
| --- | ---: | ---: | --- |
| H1 Node version | 1 | 0 | Bounded preparation only. |
| H1 shared libraries | 0 | 1 | One direct ldd launcher; its reviewed descendants are supervised, not counted as another checker. |
| H3 probe syntax check | 1 | 0 | Syntax only, no job/library/scientific pass. |
| P06-H01 direct negative | 1 | 0 | External-digest refusal before reader imports. |
| P06-H02 direct negative | 1 | 0 | One independently frozen JS binding refusal before reader imports. |
| P06-H03 original CPU trio | 3 | 0 | One real checker for each original CPU method. |
| Original coordinator quartet | 0 | 0 | Four explicitly mocked seams; counts in their mock records are not actual OS starts. |
| **Total for these selected rows** | **7** | **1** | Does not count Python launchers/Git reads or claim eight total OS processes. |

Zero-start parent/static refusal rows retain their own denominator. Additional actual supervisor/fault controls need separate exact starts and fresh paths; no unspecified `null` count can be executed. Any separately rerun full routine owns a new three-checker cohort; H3's three starts are not relabelled as those later outcomes.

A `subprocess.Popen` audit event shows an attempted launch. A callback/process receipt with actual positive PID establishes the direct start. A known PID without a complete final receipt is a started but unresolved attempt. If interruption occurs between launch and durable callback, the exact actual count is null/UNKNOWN and the observed count is only a lower bound; a missing callback is never a zero-start proof. Such an attempt blocks success and automatic retry. Cleanup must establish reaping, group absence and closed handles; absence of a log message does not establish cleanup. [S11; S17]

## 5. Direct-probe controls remain distinct

The original P06 rows remain exact historical obligations:

| ID | Current state | Later requirement |
| --- | --- | --- |
| `P06-H01` | `NOT_RUN_GATE_H` | One actual direct Node start; `CH-SELECTION`; no self-approval; failure before dynamic reader imports. |
| `P06-H02` | `NOT_RUN_GATE_H` | One actual direct Node start; source-derived `DECLARED_JS_REFUSAL`; failure in the declared argument/binding boundary before dynamic reader imports. |
| `P06-H03` | `NOT_RUN_GATE_H` | All original method outcomes; exactly three real CPU starts; intended negative `matrix_0_3` discrepancy; no inference from mocks. |

For **H01**, the planned principal variant is coherent unapproved input: preserve the external approved comparator `D0`; alter only an isolated configuration field; recompute that mutated configuration's observed digest `D1`, manifest selection and job-manifest hash coherently; keep argv's expected digest `D0`. Freeze all bytes independently. Expected source boundary is `approvedEnvelope`, specifically `CH-SELECTION: manifest digest is not external approval`. No successful result may appear. It is not enough to mutate only a hash field into malformed JSON or observe a parent-side zero-start refusal. [S09: `approvedEnvelope`]

For **H02**, P07 selects a concrete design variant for independent fixture construction: an otherwise coherent isolated configuration with an unsupported `schema`, using an explicitly approved **negative-control-only** comparator for those malformed bytes. Manifest/job digests agree so the process reaches the schema guard. Expected source boundary is `approvedEnvelope`, with `Current-host binding: wrong configuration contract/schema`; this is the actual selector represented by P06's abstract `DECLARED_JS_REFUSAL`. It is not an approval for positive qualification. Exactly one direct Node start is required. Additional variants such as malformed arguments, changed source or dependencies are separate rows, each independently frozen; they cannot silently share H02's one-start count.

`approvedEnvelope` runs outside the later report-writing `try` block. Therefore these variants are expected to leave no successful `probe.json`; Node stderr and the original supervisor's actual nonzero-exit receipt are the required negative evidence. The direct harness captures and audits them without passing through the provider's parent guard. It does not manufacture a normal failed scientific report. [S09: `approvedEnvelope`, module entry/report initialization]

The no-reader-import conclusion combines actual early refusal with the independently bound source/loader control flow. In the inspected probe, retained-reader imports occur only after successful `verifyBootstrap`; the original module loader's exact bound source does not preload them. This is a source-backed execution-path inference, not an OS-wide module-tracing claim. The reviewer must inspect those exact bytes and raw refusal evidence; if the new implementation cannot support that inference, the gate stays unmet pending a separately reviewed observation method. [S09; S16 dependency-loader member]

## 6. Original seven-method acceptance

Default discovery uses prefix `test_static_tray_readback_v01.`. Explicit package invocation uses `tests.test_static_tray_readback_v01.`. Retain the actual raw IDs and join only this declared prefix alias using source/class/method/body identity. Never merge execution attempts or silently normalize other IDs. [S01 §2; S08 `ORIGINAL_BODIES`; S13; S16]

| Class.method after the prefix | Required outcome |
| --- | --- |
| `ReadbackCPUControls.test_q01_actual_synthetic_meshes_load_in_both_libraries` | Original Q01 GLB and passed independent audit; actual retained Khronos/Three import; exit 0; original shared assertions and independent numerical audit pass. |
| `ReadbackCPUControls.test_q03_actual_synthetic_rotations_load_in_both_libraries` | Original Q03 rotation/translation GLB and passed independent audit; same actual reader, exit, shared-assertion and numerical obligations. |
| `ReadbackCPUControls.test_three_rejects_changed_synthetic_reference` | Byte-identical Q01 GLB; only reference scope plus `equipment-tray/pair/left/base.world_matrix[0][3] += 0.001`; actual checker exit 1; genuine scientific rejection, not provider/config failure; exactly the intended discrepancy/finding. |
| `ReadbackCoordinatorSeams.test_result_write_failure_leaves_predecessor_gate_blocked` | Original mock seam returns false/UNKNOWN; pending marker retained; N02 predecessor refusal. |
| `ReadbackCoordinatorSeams.test_host_alarm_cannot_interrupt_supervisor_cleanup` | Original seam passes; outer alarm disabled during delegated supervisor seam. |
| `ReadbackCoordinatorSeams.test_success_finalization_uses_remaining_outer_alarm` | Original seam passes; positive finalization allowance at most 30 seconds. |
| `ReadbackCoordinatorSeams.test_uncertain_marker_removal_recreates_pending` | Original removal uncertainty yields false/UNKNOWN; pending marker recreated and successor blocked. |

Run the complete original module/cohort through the reviewed observational harness so setup and teardown see all three CPU cases. Do not invoke isolated CPU methods and reinterpret the expected missing-cohort teardown as acceptable. The four coordinator results remain labelled mocks. Missing selection is a visible setup failure, never a skip.

Independent audit must verify all actual artifact/reference/job/manifest/config/source hashes; start counts and receipts; actual imported versions; raw stdout/stderr counts; preserved input bytes; exact method outcomes; and every scientific predicate mapped in P05 that these cases execute. The original thresholds are 5×10⁻⁶ m for positions/translational matrix terms, and 10⁻⁶ for other matrix terms and normals. Preserve 14 nodes, 12 meshes, one scene, zero animation/cameras, semantic identities/names/relationships, material/index/attribute layouts, finite values, bounds, external-resource rejection and validator zero-error/zero-warning/nontruncation checks. [S01 §7; S09 scientific body; S13; S16–S19]

Historically each case had 2,060 scalar rows. Recompute the expected row inventory and each `difference`, `threshold`, `passed` decision from actual independent reference/report values; check completeness and uniqueness, not just count. Q01/Q03 positive require all rows pass. Negative requires exactly one failed scalar row and exactly one intended finding at the left/base `matrix_0_3` field, with the original 0.000005 threshold and approximately 0.001 difference from the exact retained values. Its other scalar rows and exact comparisons pass. Inspect source/fixture equality before using the historical count. The scientific methods retain their original assertions; the stricter independent outcome audit closes the intended-negative obligation. [S01 §7; S17]

Keep the CPU clock 30,000 ms, child deadline 28,000 ms and cleanup reserve 2,000 ms inside that allowance. Keep 8 MiB GLB, 4 MiB result/log/audit, 1 MiB manifest and 32 KiB job limits, original 64 MiB stage/2,048-entry supervisor caps, and source execution ceilings 100,000 operations/30,000 ms. No long outer test timeout extends these limits. The unused native-schedule directory must remain absent. [S01; S11; S13; S15]

## 7. Gate R — complete routine

Actual runtime discovery is collected without invoking test methods, after eligibility and before the routine. Bind collector source, interpreter, command/environment, complete raw IDs and import errors. Reconcile exactly with the P05 baseline inventory plus explicitly approved P06/HI additions and any later reviewed source changes. Preserve generated and inherited methods. The historical baseline has 4,741 static IDs in 372 modules; these figures are reference evidence, not today's discovery total. An import failure, unresolved dynamic inventory, missing ID, unexpected exclusion, duplicate execution or unapproved extra blocks qualification. [S16; S12]

Freeze a full default-driver command with the exact selected Python executable and approved selection:

`PYTHON -B tools/check_local.py --timeout 3600 --readback-config ABSOLUTE_CONFIG --readback-config-sha256 APPROVED_DIGEST --output-dir FRESH_APPROVED_OUTPUT`

This is a future command template; its unresolved operands cannot be executed. The proposed 3,600-second maximum applies **per driver command** and addresses the retained 900-second incomplete run. Before R, the independent plan must justify it using actual suite size/timing and an outer supervising allowance covering copying, all selected stages, final checks and bounded termination. A timeout preserves the incomplete attempt and stops qualification. It does not warrant automatic retries or a larger source budget. [S01 §3; S12; C271 requirements]

Current core stages, in order, are:

| Driver ID | Required command body |
| --- | --- |
| `unit-tests` | `PYTHON -B -m unittest discover -s tests -v` |
| `source` | `PYTHON -B -m ontokin conformance --output REPORTS/source.json` |
| `agent` | `PYTHON -B tools/run_agent_conformance.py --output REPORTS/agent.json` |
| `construction` | `PYTHON -B -m tools.verify_construction_ci --external-evidence docs/engineering/construction-validation/external-gate.json --output REPORTS/construction.json` |
| `surface` | `PYTHON -B tools/run_surface_conformance.py --allow-pending --output REPORTS/surface.json` |
| `impulse` | `PYTHON -B tools/run_impulse_conformance.py --allow-pending --output REPORTS/impulse.json` |
| `documents` | `PYTHON -B docs/maintenance/reorganization-2026-10-17/verify_reorganization.py` |

Freeze actual expanded report paths and cwd from `build_plan`; retain unchanged plan semantics. Existing `--allow-pending` preserves the historical distinction between completed local checks and pending external acceptance; it does not claim those external cases passed. Extra `--full` visual or `--force-agent` roles require separate applicability/source/dependency review. Do not silently omit a selected stage, switch to a replacement suite or infer complete routine from a focused cohort. [S12]

The driver already preserves original/copy Git identities and complete source inventories, passes an explicit derived configuration to its unittest child, and compares immutable source after execution. Verify those actual artifacts and the exact parent/derived config relation. Check unchanged source in both original and isolated workspaces. Preserve its existing generated-output exclusions without adding a new executable-source exception. [S08: `derive_workspace_binding`, `_verify_parent`; S12]

The driver's footer/count parsing is necessary but insufficient for P05's per-method obligation. The independent observational collector/auditor must retain every discovered, attempted, passed, failed, skipped, expected-failure, unexpected-success, error and interrupted raw method outcome, then reconcile the full list. Bind that collector and its exact hook to the unchanged unittest process before R; if it is unavailable, record the missing acceptance evidence and do not call the routine qualified. A successful footer or the presence of seven target names alone cannot close R03.

Fresh `tools/chat_workflow.py check` and the documentation/navigation check are still required for the applicable records. Independent review names the inspected candidate/source, every retained attempt and unmet gate. R03 acceptance follows only after this complete evidence; integration, resulting-main checks, branch disposition and final parent delivery remain R04/R05.

## 8. Failure policy and verification of this freeze

All current records report no Node, ldd, runtime installation, original-method, native/model/hosted or full-routine execution. `CONTROL-MATRIX.json` maps P05 control obligations, the three retained P06 direct-host IDs and the new authoring controls to exact boundaries. A design control with unresolved fixture descriptors is explicitly `requires_independent_fixture_freeze`; it is not a passing result or permission to execute.

P07 static acceptance checks cover source hashes/anchors, original body identities, schema field compatibility, exact control-ID coverage, gate separation, declared zero execution and unchanged existing files. They do not invoke the new module, tests or provider runtime. The independent reviewer decides whether this design is accepted for HI. Initial drafts, review findings and revisions remain retained.
