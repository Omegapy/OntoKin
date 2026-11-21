# C271-P08 author implementation and results

**Author work is complete. Independent post-run acceptance remains pending.** This phase implements the accepted host-inspection record authoring module and its focused controls. It does not qualify a real host or close C271.

## Files and APIs

The only production/test files changed are:

- `prototypes/static_tray_v01/current_host_inspection_v01.py`: strict static plan admission, bounded host/loader closure checks, evidence record authoring, exact process-receipt accounting, pinned P06 projection and read-only recovery.
- `tests/test_current_host_inspection_v01.py`: isolated filesystem, synthetic ELF/runtime and mocked supervisor controls, with retained per-method fixture manifests.

The public entry points are `validate_inspection_plan`, `inspect_host`, `parse_ldd_output`, `reconcile_attempt` and the command-line `main`. Static admission is the default. Operational observation is explicit and remains unperformed in this phase. Reconciliation describes retained graph/content evidence; it preserves unknown durability and does not confer approval or permission to relaunch.

Concrete nested record shapes, outer-log append handling and correspondence to unchanged P06/preparer requirements are documented in `CONCRETE-SHAPES-AND-CORRESPONDENCE.md`. `candidate-004/CONTROL-MAP.json` binds every control to exact fixture recipes, live predicates, mock boundaries and frozen expectations. `candidate-004/REVIEW-DISPOSITIONS.json` records all mandatory static and test-review corrections. No protected consumer, supervisor, preparer, original method, specification, historical evidence or dependency bytes were edited.

## Exact source identity

Root published and verified the clean source checkpoint `cf16a0facebdce2fadf69e5c7fae6f2ca31cbd2e`, tree `5fcd7efc9037ed4f63fc39aa2b92f527256147b5`, before the successful run.

| File | SHA-256 |
| --- | --- |
| Module | `b2f4c869fd03919047db797bd3a80616cbe16f6b17689fe61d40754b27f97a39` |
| Tests | `797eb208670f6f74f14c9b5849485bd6cf3522a265d4129618c4b50ddc0a739a` |
| Candidate004 control map | `9f9adb0979c228b6eede5f75db8a0649ddd3cebd73f239d29020e1c53a6c35b0` |
| Unchanged guarded runner | `27489064a600ea3cfba73381fa1f75cc781cdc72303bd97ee200c6ebdb4aafdd` |

All four hashes matched after execution. Complete file bindings and evidence hashes are in `AUTHOR-FINAL-REPORT.json`.

## Focused execution and retained failure

Run002 executed all **135 methods** once: 109 frozen negative variants, five frozen positives, 16 review-supplement groups and five scoped regressions. It finished with **zero failures, errors or skips** in 8.288 seconds (8.593 seconds for the outer harness), within the 180-second bound. All 16 project-process guards reported zero calls. The sole outer Python test-runner launch is recorded separately from those counters.

Run001 is retained as failed history. It completed the same 135-method selection and produced 64 error records across 39 methods because the observation fixture used a dotted class-method string as a module attribute in `patch.object`. The affected observation routes did not execute. The independently reviewed correction changes one test line to patch the actual `_EvidenceStore` class and its `write` attribute. Production bytes, expected outcomes and control scope were unchanged. The first failure was preserved before any correction or second run.

Both `runs/run-001` and `runs/run-002` retain exact source/runner/map/oracle snapshots, command/environment records, complete stdout/stderr, outcomes, all generated fixture trees and 135 per-method manifests. The initial failure-inventory report is also retained; `FAILURE-INVENTORY-002.json` corrects its early arithmetic inference because unittest counts failing subtests separately.

## Scope of the evidence

The controls exercise real isolated file reads, path guards, bounded parsers, record writes and recovery graph checks. Host facts and process receipts are synthetic; supervisor delegation is an in-memory mock. Helper-only cases establish their named predicates and are distinguished from integrated static admission and observation routes. HI16-C, for example, proves serialization bounds with zero new mocked starts and one supplied synthetic process PID; other controls cover counted state-machine behavior.

The successful run supports this bounded implementation. It supplies no real-host observation or qualification. H0, runtime preparation, actual Node/ldd execution, the original seven methods, `check_local` and the full routine, integration and parent closure remain **NOT RUN or deferred**. C271 and R03–R05 remain open. No source edit or further execution occurred after run002. Root owns final independent acceptance, durable evidence packaging and canonical workflow/publication records.
