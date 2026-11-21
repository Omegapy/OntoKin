# Current-host provider: operational boundary

P06 adds the implementation for the adopted [P05 contract](../current-host-p05/CONTRACT.md). It does not qualify this host or authorize a full routine. The parent C271 task stays open. The current phase and its explicit limits are in [PHASE.json](PHASE.json).

## Selection and isolation

Normal `tools/check_local.py` execution includes the original unittest discovery stage. It now requires both `--readback-config ABSOLUTE_FILE` and `--readback-config-sha256 EXPECTED_DIGEST`. The digest must come from the separately reviewed execution plan. Computing a new digest from arbitrary configuration is not approval.

The configuration must describe the exact clean candidate commit/tree, complete execution-source inventory, actual host lock and inspection receipts, retained dependency inventory, original methods, and an external evidence parent. The driver's `--output-dir` must be a new directory within that evidence parent. P06 does not supply a qualified operational configuration.

The driver verifies the original configuration before copying source. It then binds the isolated workspace through a separate derived configuration and a recorded full-inventory equality proof. It preserves the approved parent file. Before the unit-test child starts, it rechecks the derived digest and passes the selected path and digest through `ONTOKIN_CURRENT_HOST_READBACK_CONFIG` and `ONTOKIN_CURRENT_HOST_READBACK_CONFIG_SHA256`. Ambient values for these variables cannot select a provider. The child environment excludes declared Python, Node and dynamic-loader injection variables.

The new JavaScript probe receives the externally selected digest in `--expected-config-sha256 DIGEST` before the terminal `--job FILE` pair. The manifest cannot approve itself. The original fixed Node environment, original CPU jobs and scientific assertions remain required.

## Listing and direct invocation

`python3 -B tools/check_local.py --list` prints the unchanged command plan without reading a configuration, preparing a runtime or creating evidence files. It is suitable for inspection before host qualification.

Direct invocation of `tests/test_static_tray_readback_v01.py` uses the same two environment variables as its selection interface. Missing or invalid selection produces a visible setup error. It does not skip the three CPU tests. The four coordinator methods remain independently selectable; their results alone do not replace the full original seven-method obligation.

The provider retains setup and per-attempt evidence. When setup cannot authenticate an evidence destination, it returns a structured refusal that the calling harness must capture; it must not claim a durable provider ledger exists. Temporary cohort cleanup first preserves and verifies the cohort outside the temporary directory. An explicit `STATIC_TRAY_READBACK_CPU_OUTPUT` destination remains retained.

## Static preparation

`tools/prepare_current_host_readback.py` requires `--plan ABSOLUTE_FILE` and `--plan-sha256 EXPECTED_DIGEST`. It defaults to a dry run. `--apply` permits only the exact independently frozen plan: a destination must be absent or already complete and exact. The tool validates every archive member, stages privately, publishes without replacing an existing destination, and records uncertain publication or cleanup outcomes for reconciliation. It never starts Node or `ldd`.

The `isolated-control` purpose exists only for finite filesystem tests and is refused by the operational CLI. Fixture installation is not runtime installation or host qualification.

## First remaining gate

Gate H must first provide a reviewed, reproducible way to observe the actual host and author fresh host/inspection records. That authoring entry point is not implemented in P06. Before any qualifying command, freeze the actual executable destination, candidate/source/dependency identities, complete positive/refusal controls, expected process counts and externally approved configuration digest. Actual bounded preparation, JavaScript syntax/runtime validation, direct-probe refusal controls and the original CPU outcomes remain unrun.

Gate R then requires the full original discovery inventory and every required routine stage, with zero missing or skipped obligations and independent R03 acceptance. R04 integration and R05 parent closure remain separate. No P06 mock, source comparison or focused Python test may be reported as passing those gates.
