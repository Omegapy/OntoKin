# C271 P08 implementation worker plan

Status: read and planning only. No implementation edit, project import, test, runtime preparation, Node/ldd process or Git mutation has been performed by this worker. Implementation is gated on the Director's explicit confirmation of the early recovery save and write authorization.

## Identity and ownership

- Worker: `/root/host_implementation`, implementer; inherited model configuration, no child workers.
- Director: `/root`; owns Git/index, canonical workflow/task/status records, evidence publication, commits and delivery. This worker has no main lease or integration authority.
- Shared checkout: `/workspace/scratch/8838dfc6e876/OntoKin`.
- Observed local branch/head: `work/c271-missing-import-digest-control`, `c99f44aaec10445b96deb2b451b1a860a1027401`, initially clean.
- Director-supplied observed main: `e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d`.
- Exclusive proposed source writes: `prototypes/static_tray_v01/current_host_inspection_v01.py` and `tests/test_current_host_inspection_v01.py`.
- Worker planning, checks and failure logs: `/workspace/scratch/8838dfc6e876/implementation_work/`.
- All P05/P06 production files, original seven methods and shared helper bodies, frozen specifications/evidence, dependency/runtime bytes and canonical task files are protected.

## Read basis

Read in full: `AGENTS.md`, `ROLE.md`, `docs/workflow/PROTOCOL.md`, `docs/workflow/HANDOFF.md`, `.agents/skills/ontokin-delivery/SKILL.md`, `docs/workflow/templates/WORKER.md`, adopted P07 `HOST-INSPECTION-DESIGN.md`, `QUALIFICATION-PLAN.md`, `ADOPTION.json`, `COMPATIBILITY-REPORT.md`; adopted P05 `CONTRACT.md`, `ADOPTION.json`, `IMPLEMENTATION-PLAN.md`; P06 `OPERATIONS.md`, `PROVIDER-IMPLEMENTATION.md`; and `docs/engineering/OK-ENG-006-local-validation-and-hosted-ci-policy.md`.

Read the machine-readable P07 qualification plan and all twenty HI control definitions; inspected preserved P05 control definitions and P06 deferred controls. Inspected P06 schema definitions for source, host, aliases, roles, inspection, process, cleanup and dependency bindings. Source inspection covers provider bootstrap/read/source/host/inspection/dependency guards, JavaScript host/inspection consumers, full original supervisor, preparer source/bootstrap/no-replace/publication/report behavior and the driver's Git environment/read seam. These were read as source, not executed.

## Public interface and bootstrap

Implement the four accepted APIs in the new module:

1. `validate_inspection_plan(plan_path, expected_plan_sha256)` returns a recursively immutable validated value after strict canonical input, external digest and full static checks. It creates no attempt directory and starts no Node/ldd/checker.
2. `inspect_host(plan_path, expected_plan_sha256, *, observe=False)` validates anew. Static mode returns `STATIC_READY` without consuming planned paths. Observe mode can delegate only the two fixed commands, once each, and can return `OBSERVED_UNAPPROVED` only after successful final publication.
3. `parse_ldd_output(stdout, stderr, expected_resolution)` is a pure strict parser: complete line grammar, exact SONAME/path map, one interpreter, optional exact vDSO, no unexplained output.
4. `reconcile_attempt(plan_path, expected_plan_sha256, attempt_path)` is read-only. It reports retained file/start/process evidence and uncertainty; it neither relaunches nor promotes incomplete evidence to success.

`HostInspectionError` is a distinct `RuntimeError` with stable `CHI-*` code, original cause and unmodified process receipt. CLI accepts only absolute `--plan`, externally supplied `--plan-sha256`, and optional `--observe`; no fallback, approval or retry option. The standard-library bootstrap authenticates its own canonical source file and the complete source inventory before adding the bound root for imports. Only then reuse bound provider/supervisor and `tools.prepare_current_host_readback.rename_without_replacement`.

## Static validation implementation

- Closed object contracts, exact types (booleans are not integers), duplicate-key/nonfinite/invalid-UTF8 rejection, canonical JSON, 16 MiB plan maximum, private regular nonlinked plan and mutation-during-read checks.
- Derive source root from the module file; require complete provider source-set equality and unchanged candidate identity. Freeze and account the five permitted Git identity reads through the existing bounded guard. In focused tests every process operation, including Git, is mocked.
- Require the unchanged Node/archive constants, external runtime/dependency roots, exact installation provenance receipts and exact retained 24-file dependency inventory. Do not install inputs.
- Verify actual Python identity, seven lock pins through explicitly bound distribution metadata, clean launcher environment, runtime/startup/extension/loader inventories and the selected Git executable. Do not add site paths or import packages to learn versions.
- Give the accepted nested inventory and resolution records concrete closed row shapes in this module. Reject unresolved fields and unsupported formats. Implement bounded static ELF header/program/dynamic/string-table parsing and exact declared `DT_NEEDED`, interpreter, RPATH/RUNPATH and architecture checks; refuse unsupported loader features/token expansion.
- Bind ldd direct shebang/script, inspector commands and candidate absences, cache/config/preload/search entries, ancestor/alias identities and complete finite resolution rationale. Independent static review supplies resolution authority; observed output cannot expand it.
- Freeze plan-owned output topology and absent paths; evidence parent must be outside source/runtime/dependencies, with all existing ancestors authenticated. No unchecked parent creation.
- Apply 60-second static and 30-second publication ceilings, bounded per-file reads and 64 MiB/2,048-entry stage caps.

## Observation/evidence implementation

Create only the authenticated fresh mode-0700 attempt and command-stage paths. Publish immutable reservation/preflight/intent before entering the supervisor boundary. The command clock is `Clock(total_ms=5000)`, active deadline `clock.started + 3`, cleanup reserve 2,000 ms, no cancellation and no retry. Fixed ordered commands are `[NODE, "--version"]` and `["/usr/bin/ldd", NODE]`, with the accepted five-variable environment and fixed labels.

The start callback retains positive PID/group immediately. Entering the launch boundary without a durable start/final receipt leaves actual count null and observed lower bound zero. Only a proven prelaunch refusal gives zero; a retained positive start/final receipt gives one. Counts and failure state stay in separate sidecars, never the closed P06 success objects.

Preserve raw supervisor receipt/logs before postflight and success projection. Validate exact keys, actual argv/cwd/environment/label, duration, stream counts, exit, cleanup, handles and zoned timestamps. No synthesized receipt field. Any failure blocks the second command; source/host/runtime/dependency drift remains failure after preserving the actual process outcome.

Use same-parent exclusive temporary file, complete write/fsync, bound `renameat2(RENAME_NOREPLACE)`, directory fsync and inode/readback checks for every wrapper record. A race or uncertain rename retains the original intention and observed source/destination; never retry or replace. Do not delete paths belonging to another writer. Publish final completion marker last. Missing marker, missing references, retained failure or uncertain write cannot be reported as success.

Project exact P06 inspection and ten-key HOST structures only after both commands have compatible actual outcomes. Validate the unchanged P06 field contract plus stricter consumer predicates; host remains explicitly unapproved in the separate result. No bootstrap `validate_selection` call with fabricated HOST/config.

## Focused evidence and independent gate

Before execution, freeze candidate source/test identities and independently review the exact test/control plan. Tests use small isolated files, synthetic ELF/metadata records and clearly labelled mocked process receipts. Patch process creation and group operations globally for the focused suite; any unexpected process attempt fails visibly. Never launch Node/ldd, original methods, preparer apply or full routine.

Control coverage targets all `HI01`–`HI20`: external comparator/refused plan paths; strict file/JSON reads; source/runtime/inspector/closure mutation; unsupported ELF/host; output path/race protection; pre/postflight drift; version and ldd parser outputs; launch/callback/unknown-count cases; deadline/log/cleanup/receipt defects; write/fsync/rename/completion faults; interrupted read-only reconciliation; exact success-record shape. Split HI14/HI18/HI19 into concrete zero-start, observed-one and unknown subcases before execution. Mock starts are labelled separately from actual OS starts, which remain zero.

Proposed focused command after authorization and fixture freeze: `python3 -B -m unittest tests.test_current_host_inspection_v01 -v`, with full stdout/stderr and per-method outcomes retained under worker scratch. Use compile/AST checks without bytecode writing. The Director owns applicable documentation/workflow checks and the durable source/review evidence. Scope instructions explicitly defer `tools/check_local.py` and the original cohort to later gates.

Independent implementation reviewer must inspect exact source/test bytes and every mandatory control, resolve findings and re-review affected changes. Implementation failure or an unimplementable contract detail stops this phase with preserved evidence; it does not justify editing the adopted design or protected consumers.

## Decisions and limitations to make explicit

The accepted P07 design defines closed top-level contracts but leaves nested ELF-resolution, author-runtime and metadata-row layouts to HI. Concrete conservative layouts are an implementation decision subject to independent review, not grounds to broaden the supported host. The existing preparer result is not a self-contained approval record: its selected descriptor must remain bound by the externally approved plan, and runtime/dependency bytes must be independently rechecked. The existing provider's Git environment inherits non-Git variables; the inspector must verify the independently frozen clean launcher environment before using that guard.

No real host plan, completed install receipt, operational HOST or configuration will be authored in P08. The plan therefore cannot claim an end-to-end real host acceptance. Focused controls establish only the implemented boundaries they exercise. P06-H01/H02/H03, original seven outcomes, Gate H/R, R03–R05 and main integration remain open.

## Stop

After accepted module/tests, focused evidence, mandatory independent implementation review and the Director's publication/delivery checkpoint: stop. Do not begin H0 static host preparation, H1 Node/ldd observation, host qualification, full routine or integration. Before authorization, the next action is Director confirmation of the early saved recovery and exact worker write ownership.
