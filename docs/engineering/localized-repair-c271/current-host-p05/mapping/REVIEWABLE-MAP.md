# C271 P05: original methods and readback predicate map

This map identifies the existing readback obligations and the precise boundary of the proposed current-host provider. **It reports static source inspection, not a test run or host qualification.** The seven original methods can retain their identities and bodies while their CPU setup and one explicitly imported process adapter select a separately versioned provider. The old preparer, manifest checker and JavaScript probe keep their historical meaning and bytes.

Source baseline: commit `743409619a8663682750b0ca29c50547a25dde41`, tree `8202185735f50aa91078a9206c351d917084ed16`. The Director supplied this reconciled Git identity. This worker read the actual local files, computed their hashes and parsed Python source without importing project modules, running tests, executing Node or ldd, installing dependencies, or changing any existing repository source. Governing instructions were read first; substantive mapping began only after the Director confirmed the early recovery save.

## Evidence package and scope

The complete machine-readable records are members of [MAP-EVIDENCE.zip](MAP-EVIDENCE.zip). `MAP-EVIDENCE-MANIFEST.json` binds every member's bytes and SHA-256. `MAP-SUMMARY.json` gives the compact counts, package identity and verification result. These files are analysis artifacts; they contain no operational implementation of the new provider.

| Archive member | What it establishes |
| --- | --- |
| `SOURCE-INVENTORY.json` | Exact bytes, SHA-256, line count, mode and computed Git blob identity for 402 source/data files. The source commit/tree are declared separately from local byte observations. |
| `DEFAULT-DISCOVERY-INVENTORY.json` | 372 default test modules and 4,741 static method IDs, including the 56 source-generated force cases. It records method source/body identities, decorators, inheritance, import aliases and analysis limits. |
| `PREDICATES.json` | 3,355 Python condition/control/assignment records and 3,260 call records, each with exact source and AST anchors. It also includes all 168 original JavaScript lines and 17 fully inspected source ranges. |
| `METHOD-PREDICATE-MAP.json` | The original seven method identities, direct/shared assertions, source-call graph, explicitly mocked edges, complete reachable predicate IDs, and a separate proposed operational graph. |
| `PRESERVATION-DISPOSITIONS.json` | 46 source groups and per-node dispositions: unchanged source, historical source with a new versioned equivalent, or an explicitly bounded future setup/driver adaptation. |
| `DEPENDENCY-INVENTORY.json` | The exact retained 24-file external dependency inventory, historical ten-file runtime/ten-alias inventory, role paths, fixed options, original slots and the inspected loader member. |
| `KNOWN-CALLBACKS.json` | Source-backed callback relations, including the real start callback invoked by the mocked coordinator child. |
| `SCOPED-EXCLUSIONS.json` | Boundaries that are retained but not claimed as executed or internally audited here. |
| `STATIC-VALIDATION.json` | Static consistency/source-preservation checks and the retained initial inspection error. It is not a behavioral validation result. |
| `SUPERSEDED-PACKAGES.json` | Identity and retained location of the first frozen package, superseded after the reviewer requested more precise external dependency disposition labels. |

The original-source graph has 253 function/module/JavaScript/dependency nodes and 578 labelled edges. The seven methods reach 129 distinct nodes when all preserved source branches are included. That closure is a set of possible source paths, not an assertion that all branches execute for Q01 or Q03. The graph retains raw call expressions and marks its limits instead of inferring arbitrary dynamic dispatch.

## One-to-one original method mapping

The actual default driver command is `python -B -m unittest discover -s tests -v`. With that discovery root, the source-derived module namespace is `test_static_tray_readback_v01`. Historical explicit module invocation uses `tests.test_static_tray_readback_v01`. Both names are retained in the machine map and joined by source path, class, method, exact function-line hash and body AST hash. They are not silently treated as the same raw runtime ID. The future runtime inventory must preserve its actual emitted IDs and perform this explicit reconciliation.

All seven rows retain the same default method ID. The original full test file remains pinned at its historical Git object. Only an explicitly reviewed later operational revision can change its imports, availability decorator and class lifecycle wiring; the test bodies and shared scientific helpers below stay byte-identical.

| Original class and method | Source lines | Required operational outcome |
| --- | --- | --- |
| `ReadbackCPUControls.test_q01_actual_synthetic_meshes_load_in_both_libraries` | 169–170 | Same Q01 synthetic GLB and independent reference; actual Khronos and Three.js imports; every shared assertion passes. |
| `ReadbackCPUControls.test_q03_actual_synthetic_rotations_load_in_both_libraries` | 172–173 | Same Q03 rotations/translations and all shared assertions. |
| `ReadbackCPUControls.test_three_rejects_changed_synthetic_reference` | 175–176 | Same Q01 GLB, exact `+0.001` left/base matrix-reference mutation, rejected Three comparison and a `matrix_0_3` finding. A provider or binding failure cannot masquerade as this expected negative. |
| `ReadbackCoordinatorSeams.test_result_write_failure_leaves_predecessor_gate_blocked` | 76–82 | `passed=False`, `state=UNKNOWN`, pending marker retained; N02 predecessor check raises the unresolved-finalization `Stop`. |
| `ReadbackCoordinatorSeams.test_host_alarm_cannot_interrupt_supervisor_cleanup` | 84–87 | Successful seam; outer timer is off while the child/supervisor seam runs. |
| `ReadbackCoordinatorSeams.test_success_finalization_uses_remaining_outer_alarm` | 89–93 | Successful seam; finalization timer is positive and no more than 30 seconds, using the same remaining allowance. |
| `ReadbackCoordinatorSeams.test_uncertain_marker_removal_recreates_pending` | 95–101 | Lost reply after actual marker removal yields `UNKNOWN`; pending marker is recreated and blocks N02. |

Source: [the complete original test module](https://github.com/Omegapy/OntoKin/blob/743409619a8663682750b0ca29c50547a25dde41/tests/test_static_tray_readback_v01.py). The machine map binds the full original method-line bytes and body AST separately. Future hashes are `null` with an explicit unimplemented status; no proposed code identity has been invented.

### Shared CPU helper

The three CPU methods call the same unchanged `check_case` at lines 125–168. Its 13 assertion calls are retained individually in the machine map. They require a passed independent reference audit; exactly one observed checker start; successful process-group cleanup; closed handles; actual artifact digest; validator version `2.0.0-dev.3.10` and success; Three.js version `0.186.1`; 14 nodes and 12 meshes; the intended positive or negative outcome; input preservation; and, for the changed-reference case, the expected matrix finding. The last assertion is conditional, so 13 source assertions does not mean all 13 execute in each positive case.

The job still binds the manifest, GLB and audit hashes. The helper uses fresh labels and stage directories, the manifest's declared argv with only its final job path replaced, a 30,000 ms `Clock`, and a child deadline of `clock.started + 28`. The negative branch alone catches the original supervisor `Stop` and reads its genuine process record. The setup's output override remains exclusive; the temporary-root path retains cleanup. Its unused native schedule must remain absent.

### Shared coordinator harness and callbacks

The four coordinator methods call the unchanged `run_seam` at lines 32–74. It registers temporary-directory cleanup, constructs a synthetic accepted candidate and N01 manifest, records two alarm observations, and injects controlled write/removal failures. It patches `format_check.check_file`, `verify_manifest`, `run_process`, `transaction._prior_result` and `store.verify_candidate`. Those mocked boundaries are explicit graph edges; the seam results do not qualify their real implementations.

One easily missed transitive obligation is `format_check.run_check.started` at lines 164–166. The mock child invokes this **real** callback through `kw["on_started"](process)` at test line 50. It increments `checker_starts` and calls the real durable writer for `started.json`. The graph includes the callback's binder, mock invocation and writer dependency, and all four seam closures include its predicate IDs. `KNOWN-CALLBACKS.json` also records the CPU `started.append` lambda, alarm handler, patch callbacks, clock callbacks, strict-JSON hooks, temporary cleanup and source helper callbacks.

## Proposed operational route

The accepted implementation design must use distinct new paths:

| Role | Proposed path or interface |
| --- | --- |
| Python provider | `prototypes/static_tray_v01/current_host_readback_v01.py` |
| JavaScript probe | `prototypes/static_tray_v01/current_host_readback_v01.mjs` |
| Safe preparer | `tools/prepare_current_host_readback.py` |
| Class manifest preparation | `prepare_case_manifest(output, *, config_path, config_sha256, source_root, schedule_root)` |
| Class manifest verification | `verify_case_manifest(path, *, config_path, config_sha256, source_root, schedule_root)` |
| Per-case process adapter | Import `guarded_run_process` explicitly as the test module's `run_process`; preserve `check_case` unchanged. |
| Driver selection | `--readback-config ABSOLUTE_FILE --readback-config-sha256 EXPECTED_DIGEST`; the expected digest is frozen independently in the accepted execution plan. |
| Test-process selection | `ONTOKIN_CURRENT_HOST_READBACK_CONFIG` and `ONTOKIN_CURRENT_HOST_READBACK_CONFIG_SHA256`; these variables do not enter the Node child's fixed environment. |

The adapter validates the exact approved configuration, job, manifest, source/workspace, runtime and dependency bindings immediately before and after the checker. Both validations consume the existing `Clock`. It delegates **once** to the unchanged supervisor with the same argv, stage, label, clock, stage deadline, environment and callback. It cannot reset the clock, extend a limit, retry the child or replace the returned process evidence.

Every adapter-origin refusal, including a timeout raised by its own clock check, uses a distinct `CurrentHostBindingError(RuntimeError)` and retains the original failure/state/process evidence. The negative original helper catches `Stop`, so allowing adapter errors to use that type could conceal a binding or postflight failure behind a genuine negative probe. Only a genuine `Stop` from the delegated supervisor can be re-raised unchanged, and only after successful bounded postflight verification. This rule is part of the proposed graph, separate from the graph of original source.

The driver's isolated copy must execute its own bound provider and probe. A configuration cannot point the copied tests back to the original checkout. After its existing commit/tree and byte-inventory equality checks, the driver creates an explicit derived workspace binding with a new identity, both source roots and the parent configuration digest. The original source and selected configuration remain unchanged. All existing default stages and zero-skip/error accounting remain required. Source: [driver workspace construction and execution](https://github.com/Omegapy/OntoKin/blob/743409619a8663682750b0ca29c50547a25dde41/tools/check_local.py).

## Manifest, JavaScript and historical coupling

The historical Python checker hardcodes Node `v24.22.1` in both manifest construction and verification. The historical JavaScript probe independently checks that version and the old manifest schema. Changing Python hashes alone cannot make a new schema valid in that JavaScript. The new provider therefore has distinct manifest/result/host schemas and a separately named JavaScript entry point. The selected version remains **`v24.22.1`**; a different executable or host is separately identified and qualified rather than presumed equivalent.

The old files remain byte-identical:

| Original source | SHA-256 |
| --- | --- |
| `tests/test_static_tray_readback_v01.py` at the original Git object | `2f0abd812aa668b7abf9e249315acdb9c0fd175adb59672ab1c454679d494394` |
| `prototypes/static_tray_v01/format_check.py` | `e0d71482b9878fbdf9ca1287013756fc0f6b9df530864f5634b8863354a29447` |
| `prototypes/static_tray_v01/readback.mjs` | `156c988ffc478adafe59c495a07e0a48f5ac77c12829d85d147838578b523b4c` |

The C225 helper pins these three full files together with the original C199 manifest, HOST and C195 archive. All six pins matched during this analysis. A future setup edit changes the complete test-file digest even if its seven test bodies remain identical. The unchanged C225 helper must therefore continue to refuse that operational checkout. Historical exact replay uses the original checkout and original prerequisites; current-host results cannot satisfy or relabel it. Source: [C225 source guard and recovery controls](https://github.com/Omegapy/OntoKin/blob/743409619a8663682750b0ca29c50547a25dde41/docs/engineering/readback-prerequisites-c225/restore_readback_prerequisites.py).

The complete manifest obligations include new-path refusal, actual bounded version/closure inspections, exact file sets, forbidden dependency symlinks, file bytes/sizes/modes, aliases, executable membership in the runtime closure, host identity, source-probe ownership, exact reader versions/options/environment/limits, all executable roles, and the original twelve ordered slots with exact argv/stage/result fields. New source/config/runtime bindings replace only explicitly historical operational identities. Scientific thresholds and dependency bytes do not change. Sources: [manifest build/verify and coordinator](https://github.com/Omegapy/OntoKin/blob/743409619a8663682750b0ca29c50547a25dde41/prototypes/static_tray_v01/format_check.py), [bound-file reader and native source lock](https://github.com/Omegapy/OntoKin/blob/743409619a8663682750b0ca29c50547a25dde41/prototypes/static_tray_v01/lock.py).

The original native `lock.build_lock` seals all `test_static_tray*.py` files and all prototype Python/JSON/JavaScript files. `verify_lock` calls the old manifest verifier. The new CPU manifest must not be smuggled through those native entry points. Their source/host/approval/slot/Blender gates remain unchanged and outside current-host CPU authorization.

### Owned JavaScript predicates

All 168 original JavaScript lines are hashed, and the 17 source ranges cover every line. They retain these obligations:

| Range | Preserved conditions |
| --- | --- |
| 1–37 | Node standard imports; SHA-256; canonical object comparison; bounded regular-file reads; exclusive result creation, 4 MiB limit, fsync and descriptor cleanup; finite vectors and matrix layout conversion. |
| 39–59 | Exact `--job FILE` shape; 32 KiB job, 1 MiB manifest, 8 MiB GLB and 4 MiB audit; explicit report provenance; runtime/schema gates; exact manifest/input hashes; passed independent audit bound to artifact and case. |
| 60–81 | No external fetch or external reader resources; actual validator version and options; zero errors/warnings and no truncated report; actual Three and GLTFLoader import; package/revision checks; one scene, no animation or cameras. |
| 82–118 | Exact and finite threshold comparisons with retained measurements; unique semantic IDs and full node inventory; 14 nodes; no unsupported object types; original names, complete extras, children/parent relationships; all 16 matrix entries with the original separate tolerances. |
| 119–146 | Empty roots; one mesh/material per part; attribute/index layout and counts; finite actual vertices/normals; actual world transforms; per-coordinate comparisons; exact indices and materials; no texture maps. |
| 147–168 | World min/max/size comparisons; 12 meshes; stable findings/results; post-read input hashes; pass only if both readers and preservation pass; retained failure report, exclusive output and exit code. |

Source: [original probe](https://github.com/Omegapy/OntoKin/blob/743409619a8663682750b0ca29c50547a25dde41/prototypes/static_tray_v01/readback.mjs). The new probe must add explicit current-host/source/dependency authentication before dynamic imports and preserve the scientific body. Schema/report/bootstrap adaptations are separately identified; they are not permission to alter numerical comparisons or failure behavior.

No JavaScript AST parser was installed, and Node execution is prohibited in this phase. The JavaScript anchors are therefore exact line/segment hashes with manually inspected syntax ranges, **not** a claimed JavaScript AST or behavioral-equivalence proof. Python anchors are genuine `ast.parse` nodes. The separately implemented JavaScript will require a reviewed exact segment/token/AST comparison using an identified parser where available.

## Independent scientific reference and resource paths

The CPU helper imports `synthetic` and `audit` through `tests.test_static_tray_reader_v01`. The latter is the function from `tools/static_tray_reader_v01/reader.py`; it is not the `audit.py` CLI. The support module also imports `corrupt`, whose bytecode-cache refusal is an import-time condition even though the corruption function is never called by the target methods.

The synthetic GLB comes from hand-derived dimensions and face tables. It contains explicit float32 position/normal data, uint16 triangle indices, fixed materials, semantic relationships and Q01/Q03 translations/rotations. Its construction does not call the producer or native exporter. The independent reader uses exact rational reference dimensions, actual decoded buffers and exact semantic records. It checks container bounds, strict JSON, finite numbers, accessor offsets/strides, supported features, graph identity, rigid transforms, materials, outward box topology, corner welds, signed volume, cavity dimensions, clearances, headroom and overlaps. The method graph reaches all associated helper functions and records their rejection, numerical and resource branches. Sources: [synthetic construction](https://github.com/Omegapy/OntoKin/blob/743409619a8663682750b0ca29c50547a25dde41/tests/test_static_tray_reader_v01.py), [reference equations](https://github.com/Omegapy/OntoKin/blob/743409619a8663682750b0ca29c50547a25dde41/tools/static_tray_reader_v01/expected.py), [GLB decoder](https://github.com/Omegapy/OntoKin/blob/743409619a8663682750b0ca29c50547a25dde41/tools/static_tray_reader_v01/glb.py), [independent audit](https://github.com/Omegapy/OntoKin/blob/743409619a8663682750b0ca29c50547a25dde41/tools/static_tray_reader_v01/reader.py).

The target helper calls `audit(..., delivery_rules=None, baseline_right=None)`. It therefore uses the synthetic/measurement interface. Full-layout validation immediately returns when rules are absent; Q04/Q05 baseline obligations are outside these Q01/Q03 calls. Those bodies, fixtures and full-suite controls remain preserved and inventoried, but a passing CPU cohort cannot claim that every optional reader branch or native layout/receiving requirement executed.

The supervisor preserves one monotonic deadline and one direct process start, exact environment and working directory, Linux descendant reaping, capped nonblocking pipe capture, bounded staged inventory, cancellation/deadline checks, lingering-descendant refusal, nonzero exit handling, mandatory TERM/KILL/reap cleanup, closed descriptors and actual process receipts. The 2,000 ms cleanup reserve remains within the 30,000 ms CPU allowance; the supervisor's 65,000 ms maximum is a separate native-transaction ceiling, not permission to enlarge CPU readback. It also enforces a 64 MiB aggregate stage cap and 2,048 filesystem-entry limit. Source: [supervisor](https://github.com/Omegapy/OntoKin/blob/743409619a8663682750b0ca29c50547a25dde41/prototypes/static_tray_v01/supervisor.py).

The coordinator shares the original exclusive writer, alarm management and immutable-candidate checks. A success finalization uses only remaining outer time. Failed or uncertain finalization preserves or recreates its pending marker and blocks successors. Source: [transaction helpers](https://github.com/Omegapy/OntoKin/blob/743409619a8663682750b0ca29c50547a25dde41/prototypes/static_tray_v01/transaction.py), [candidate verifier](https://github.com/Omegapy/OntoKin/blob/743409619a8663682750b0ca29c50547a25dde41/prototypes/static_tray_v01/store.py). Native construction/promotion/receiving bodies were read as context and remain unchanged; the target CPU methods do not execute them.

The separate ordinary product-source limits remain **100,000 operations and 30,000 ms**. They are preserved by the adopted goal and native lock constants. No `.ok` source program was executed by this mapping work, so this is not new evidence that a particular program complied with those budgets.

## Dependency boundary

The retained external closure contains exactly 24 files: validator, Three.js modules and the custom module loader, with all paths, byte counts and digests from the immutable C199 manifest. Its internals are treated as bound external dependencies. The owned integration code checks their actual API results; the map does not claim to have authored or exhaustively audited every external algorithm.

The exact 564-byte module-loader member was read in memory from the authenticated archive, without extraction or execution. Its SHA-256 is `927190e6d34940b2c7f9586c72459c24dc5fad497268bded628acd459ec9235e`. It resolves `three`, `three/webgpu` and `three/tsl` relative to `../indexer-view/three` and delegates other resolution. Preserving the archive-relative layout permits relocation without altering its source. The complete loader text and archive/member identities are in `DEPENDENCY-INVENTORY.json`.

The historical ten runtime files and ten aliases remain historical records. They are not current-host evidence and do not impose an arbitrary ten-file limit on a newly declared closure. The current host must supply its own complete admitted executable/shared-library/loader/interpreter bindings and bounded preparation observations. Matching versions alone is insufficient. The preparer must preserve complete inventories, exact archive bytes, safe member kinds/paths, symlink refusal, absent-or-complete installation states, same-filesystem no-replace publication, race reconciliation, owned-only cleanup and explicit unknown outcomes.

## Whole default inventory and its limits

The static inventory found **372 top-level `test*.py` modules and 4,741 unique method IDs**: 4,685 declared/inherited methods plus 56 generated force cases. `tests/__init__.py` is absent. No `load_tests` hook or imported `TestCase` alias adding duplicate method IDs was found in the stated scan.

The generated cases are installed by `tests/test_force_source.py` lines 213–216. The inventory expands the exact names from `acceptance.json` and `reviewed-acceptance.json`, using the source's ID-keyed dictionaries and name transformation. It binds the generator, corpus hashes, source case and installation line for every generated ID. This is a static interpretation of a specific known generator, not arbitrary Python evaluation. Source: [force case generation](https://github.com/Omegapy/OntoKin/blob/743409619a8663682750b0ca29c50547a25dde41/tests/test_force_source.py).

The nontrivial inheritance paths use `ReachAgentFixture`, `NativeFieldTestCase` and `EntryFixtureCase`; those bases add helpers/lifecycle behavior and no `test*` methods. The inventory resolves their source definitions and inherited methods. The other top-level mutation found by the hazard scan updates reach-corpus data, not test method names.

The analysis does not import the tests. It cannot establish import success, evaluate host-dependent skip decorators, observe runtime `_FailedTest` cases or prove all possible imported decorator side effects absent. An actual eligible-environment discovery inventory must therefore be captured later and reconciled with these baseline source identities plus explicitly approved additions. Every original required method needs its own actual outcome; totals, filters, successful replacements or skipped originals cannot satisfy that gate. The other 4,734 methods are inventoried, not individually given a transitive semantic audit in this bounded readback phase.

## Static verification and remaining gates

The static checks passed: all selected Python/test files parsed; every graph endpoint exists; the seven-method mapping is bijective; the retained external inventory has 24 files; the historical runtime inventory has ten files and ten aliases; all six C225 source pins match; the inspected loader matches its manifest binding; and all inventoried source bytes remained unchanged during analysis. Source-copy identities, source-derived method names and graph counts do not establish runtime acceptance.

The initial size-only inspection attempted to stat an assumed `tests/__init__.py` and received `FileNotFoundError`. The analysis was corrected to record that file as absent. That failed inspection is retained in `STATIC-VALIDATION.json`; it executed no project code and altered no source. Independent review also found the missing real start-callback edge; the corrected graph and callback record preserve that finding and its resolution.

The reviewer subsequently requested more precise metadata for the three external dependency nodes. The corrected dispositions distinguish retained historical runtime records, a separately qualified new runtime/interpreter closure, and the exact 24 retained dependency files relocated to explicitly bound external paths. The previous frozen ZIP and its receipts remain byte-for-byte in `superseded-001`; the new package records that supersession. No original source predicate changed in this correction.

The next gate is independent acceptance of the exact contract and this map. Implementation, actual provider/refusal controls, eligible-host qualification, real default discovery and full routine, R03 acceptance, main integration and R04/R05 closure remain separate later gates. If an implementation cannot preserve a mapped predicate or reconcile an original method, that mismatch is a blocker to report, not an expectation to weaken.
