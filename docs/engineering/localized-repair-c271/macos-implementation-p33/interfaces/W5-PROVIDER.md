# W5: the 0.2.0 provider, the 0.2.0 probe and the version dispatch (S7, S8, S10)

Worker W5 of gate MI, C271-P33. The assignment named base `2fcf5505`. During the work the
checkout's head moved to `bb15ddda`: the amendment's adoption and the follow-ups of W1 to W4. This
note follows the shapes committed at `bb15ddda`. It covers development work only. It is not
frozen and not reviewed, and nothing here ran on a prepared runtime: no Node, `ldd` or `codesign`
start, and the probe never ran.

It implements [plan sections 4.3 to 4.8](../IMPLEMENTATION-PLAN.md#4-shared-interfaces) and the
provider and probe parts of [contract sections 1, 7, 8 and 10](../../macos-contract-design-p31/CONTRACT.md#7-host-observation-in-place-of-h0-and-h1-s3-s7-s9),
under design revision 4 ([ADOPTION-AMENDMENT-001](../ADOPTION-AMENDMENT-001.json)) and the
[Director's decisions](../DIRECTOR-DECISIONS.md) D-03, D-04, D-08 and D-12 to D-14.

| File | Content |
| --- | --- |
| [`current_host_readback_v02.py`](../../../../../prototypes/static_tray_v01/current_host_readback_v02.py) | the 0.2.0 provider, a copy of the 0.1.0 provider with the contract's changes only |
| [`current_host_readback_v02.mjs`](../../../../../prototypes/static_tray_v01/current_host_readback_v02.mjs) | the 0.2.0 probe; its scientific body is byte-identical to the 0.1.0 probe's |
| [`current_host_readback_v01.py`](../../../../../prototypes/static_tray_v01/current_host_readback_v01.py) | the version dispatch and `git_binding_from_selection`, appended after the unchanged 0.1.0 code |
| [`test_current_host_readback_provider_v02.py`](../../../../../tests/test_current_host_readback_provider_v02.py) | 45 development tests (section 8) |
| [`W5-PROBE-MAP.json`](W5-PROBE-MAP.json) | the probe's segment map and the MC11 development scan (section 7) |

## 1. What 0.2.0 keeps and changes

The provider keeps every 0.1.0 rule that the contract keeps: the bounded, exclusive and
canonical file reads; the digest-checked selection; the source inventory and clean Git state;
the workspace derivation and parent check; the 24-file reader tree; the original method bodies;
the manifest with the twelve structural slots; the job checks; the clock; one delegated start;
preflight, postflight, `CurrentHostBindingError` and the unchanged re-raise of a genuine
supervisor `Stop`; the ledgers, setup self-finalization and the cohort accounting.

| Change | Rule |
| --- | --- |
| every document schema at `/0.2.0`; each entry point refuses 0.1.0 documents | contract section 1 |
| constants: contract `ontokin.current-host-readback/0.2.0`; the v02 provider and probe; the macOS contract; Node `v24.22.1` and the archive pin `89c68259…bc0a7`; the macOS lock | S1, S2, S7 |
| `DESIGN_REVISION = 4` and `AMENDMENTS = ("P33-AMENDMENT-001",)`, written beside `contract` in every document | D-03, D-12, D-13 |
| the configuration binds the amendment's adoption record (`amendment_adoption`) | design revision 4 |
| `_verify_host` consumes HOST/0.2.0 through the observer's helpers; no ELF, `ldd` or alias logic | S2, S7, S10 |
| the selection's Git is bound through `tools.check_local.bind_git` before the source reads | S9 |
| the boot identity, OS build and cryptex version are read before the cohort, and before and after each start | MC09 |
| `guarded_run_process` delegates once to `supervisor_darwin_v01.run_process` | S4 |
| results and refusals carry the labels of contract section 10 | D-04 |
| an ordinary run fails setup visibly with the fixed reason | S8 |

The Node executable's own pin (SHA-256, size and mode) is frozen at preparation. The provider and
the probe take it from HOST, never from a constant.

## 2. Documents at `/0.2.0`

Every key set is closed. A descriptor is `{path, sha256, size_bytes, mode}` and a binding
`{sha256, size_bytes, mode}`, with the mode written `0o644`. Every path is canonical
(`/private/var/…`, not `/var/…`); a symbolic-link component refuses.

### 2.1 Read by the provider

| Schema | Keys |
| --- | --- |
| `config/0.2.0` | `schema, contract, contract_source, amendment_adoption, source, host, dependencies, runtime, methods, evidence_root, parent` |
| `source/0.2.0` | `schema, files` (`{relative path: binding}`) |
| `dependencies/0.2.0` | `schema, files, directories, archive` |
| `methods/0.2.0` | `schema, source_test, original_bodies, discovery` |
| `discovery/0.2.0` | `schema, method_ids, baseline_map` |
| `host/0.2.0` | `schema, contract, design_revision, amendments, profile, executor, observed_at_utc, plan, observer, platform, os, environment, python, runtime, git, dependencies, source, inspections, starts, labels, claims` (W3's shape) |
| `inspection/0.2.0` | `schema, contract, design_revision, amendments, argv, environment, timeout_ms, started_at_utc, finished_at_utc, process, stdout, stderr` (W3's shape) |
| `node-source/0.2.0` | checked through the observer's `check_runtime`, unchanged |

Configuration members:
- `contract_source`: the descriptor of `<root>/docs/engineering/localized-repair-c271/macos-contract-design-p31/CONTRACT.md`.
- `amendment_adoption`: the descriptor of `<root>/docs/engineering/localized-repair-c271/macos-implementation-p33/ADOPTION-AMENDMENT-001.json`.
- `source`: `{root, commit, tree, inventory}`.
- `host`: the descriptor of HOST/0.2.0.
- `dependencies`: `{root, inventory}`.
- `runtime`: `{executable: <runtime directory>/bin/node, version: "v24.22.1"}`.
- `methods`: a descriptor.
- `evidence_root`: an existing directory outside the source.
- `parent`: `null` for an original selection. A derived one has `{config, source_root, workspace_binding}`.

### 2.2 Written by the provider

| Schema | Keys |
| --- | --- |
| `lock/0.2.0` (the manifest) | `schema, contract, design_revision, amendments, labels, profile, schedule_root, cohort_root, dependencies_root, scope, limits, environment, files, runtime, validator_version, three_version, validator_entry, three_package, three_entry, gltf_loader_entry, module_loader, probe, validator_options, three_options, slots, selection, source, host, methods, dependencies` |
| `workspace/0.2.0` | `schema, contract, design_revision, amendments, identity, parent_config, source_root, workspace_root, commit, tree, source_inventory, source_before, workspace_inventory, immutable_inventory_sha256, provider, probe` |
| `attempt/0.2.0` (the ledger) | `schema, contract, design_revision, amendments, labels, expected_argv, expected_checker_starts, actual_checker_starts, preflight, postflight, boot_before, boot_after, process, supervisor_failure, provider_failure, state, elapsed_ms`, and when present `started_record` and `artifacts_after` |
| `setup/0.2.0` | `schema, contract, design_revision, amendments, labels, run_kind, passed, checker_starts, boot`; on success also `config_path, config_sha256, manifest_sha256, source_root`; on failure `error` |
| `cohort/0.2.0` | `schema, contract, design_revision, amendments, labels, passed, expected_cases`; on success also `attempts, actual_checker_starts`; on failure `error` |
| `refusal/0.2.0` | `schema, contract, design_revision, amendments, labels, passed, error, authorized_evidence_destination, evidence_finalized`, and the 0.1.0 additions: `actual_checker_starts, process, attempt` from an attempt; `actual_checker_starts, setup, run_kind` from setup |
| `preserved-cohort/0.2.0` | `schema, contract, design_revision, amendments, original_root, retained_root, files, reason` |

- The manifest's `runtime` is `{executable, version, binding}`, where `binding` is HOST's
  executable pin. The `profile` key keeps 0.1.0's value, `ontokin.static-tray/0.1.0`.
- `boot_before`, `boot_after` and setup's `boot` are
  `{stage, boot_session_uuid, os: {product_version, product_build_version, product_version_extra, cryptex}}`.
- The derived selection keeps the configuration's key set. It rewrites `source.root`,
  `contract_source.path`, `amendment_adoption.path` and `parent`.

### 2.3 The source inventory (W3's question Q9)

The provider's `/0.2.0` source path set is the observer's: `source_paths` over `SOURCE_TREES`,
`SOURCE_FILES` and the `SOURCE_OPTIONAL` files that are present. `SOURCE_FILES` is 0.1.0's set
plus the macOS lock and the three p31 contract files. One document therefore serves the
observation plan, HOST's `source.inventory` and the configuration's `source.inventory`. The
provider checks that all three descriptors are equal.

On this checkout, `v02.source_inventory(root)` produced the same canonical bytes as
`observation.source_inventory(root)`: 642 files. The two would differ only for a file mode below
`0o100`, because the provider spells modes with `oct()`.

## 3. What MH's execution plan must supply

- **Configuration:** as in section 2.1. MH's reviewed plan supplies its expected digest from
  outside the file. The driver passes the path and the digest as
  `ONTOKIN_CURRENT_HOST_READBACK_CONFIG` and `ONTOKIN_CURRENT_HOST_READBACK_CONFIG_SHA256`.
- **HOST:** written by M0 and M1 on the real boundary (`labels.boundary == "real"`), at design
  revision 4. Its `source.inventory` and `dependencies.inventory` descriptors equal the
  configuration's. Its source root is the original checkout, and its `observer` binding equals the
  source inventory's binding of `current_host_observation_v02.py`.
- **Interpreter:** the unit process runs as `<root>/.venv/bin/python`, spelled exactly as HOST's
  `python.launcher`. Its `sys.version`, version and `proc_pidpath` image must equal HOST's
  `python.interpreter`.
- **macOS lock:** the provider reads it from its own root. Its binding and seven pins must equal
  HOST's `python.lock` and `python.packages`.
- **Supplied by no one:** the lock (`lock/0.2.0`) is not supplied. The provider writes it at
  setup.

## 4. Version dispatch (plan sections 4.6 and 4.8)

The dispatch is appended after the 0.1.0 definitions, which are byte-identical: the first 65,533
bytes of the file equal the committed 0.1.0 provider. The 0.1.0 functions stay reachable as
`_V010_ENTRY_POINTS`, and the facade takes their module-level names.

| Entry point | Dispatched on |
| --- | --- |
| `validate_selection`, `derive_workspace_binding`, `prepare_case_manifest`, `verify_case_manifest` | the configuration given by path and digest |
| `guarded_run_process`, `setup_cpu_cohort`, `finish_cpu_cohort` | the selection in the two environment variables |
| `git_binding_from_selection` | the configuration given by path and digest (section 5) |

- **Rule:** a configuration whose bytes match the expected digest and whose schema is
  `ontokin.current-host-readback-config/0.2.0` goes to `current_host_readback_v02`. Every other
  call goes to the unchanged 0.1.0 code, whose own checks refuse anything that is not a 0.1.0
  selection, with the same codes and reasons as before.
- **Errors:** the dispatch read never raises and starts nothing.
- **Internal calls:** a call between 0.1.0 entry points (for example `_job` calling
  `verify_case_manifest`) passes through the same dispatch, so it reads the configuration once
  more.
- **Ordinary run (S8):** when neither selection variable is set (or both are empty), the facade's
  `setup_cpu_cohort` raises `CurrentHostBindingError` (`CH-SELECTION`). Its message is exactly
  `No approved current-host readback selection: ordinary run, not a qualification`. Its refusal
  record has `run_kind: "ordinary"`, zero starts and no evidence destination, and `cls.root` is
  `None`. It is never a skip. `current_host_readback_v02.setup_cpu_cohort` gives the same reason
  when it is invoked directly.
- **Partial selection:** an error, as now ("Set both …").
- **The 0.1.0 code paths keep their behaviour.** `tests/test_current_host_readback_provider.py`
  keeps its outcomes exactly: 22 of 25 pass, and the same three Linux-only publication tests fail.
  **No existing expectation changed** and the file was not edited. Its setup test expects
  `CH-SELECTION`, zero starts and no root, and those hold for the S8 refusal too.

## 5. `git_binding_from_selection(config_path, config_sha256)`

It reads the configuration with the bounded reader and checks it against the expected digest.
- **0.2.0 selection:** it reads HOST through its descriptor and checks HOST's schema, contract,
  design revision, amendments, profile and executor. It checks the Git bytes with the observer's
  `check_git_binding`, which refuses the `/usr/bin/git` dispatcher, a link, a non-canonical path,
  other bytes and the dispatcher's file or bytes, and it requires `labels.git` to equal the
  binding. It returns `{"path", "sha256"}`.
- **0.1.0 selection:** it checks the 0.1.0 configuration's keys and contract, and returns `None`.
- **Anything else** refuses: another schema, a mismatched digest, or an unreadable file.

It starts no Git and no other process. A test patches `subprocess.Popen` and `os.posix_spawn` to
fail.

The 0.2.0 provider binds the same Git in the unit process. `_verify_source` calls `bind_git` as its
first step, before any source read, and confirms that `git_executable()` returns that path.
Unbound, unbindable or changed Git refuses before any Git start. Every later Git start re-hashes
the executable (W4's `git_executable`), and a mismatch never falls back to `PATH`.

## 6. Labels (contract section 10, amendment row 13)

`{executor, contract, design_revision, amendments, profile, os, node, python_inventory_sha256,
git, run_kind, boundary}`:
- `os`, `node` and `git` are HOST's verified labels;
- `python_inventory_sha256` is HOST's;
- `run_kind` is `qualifying` (`ordinary` for the S8 refusal);
- `boundary` is `real` only while every boundary is the module's own object: the Darwin
  `run_process`, `os.uname`, the observer's readers, `python_inventory`, `check_runtime` and
  `check_git_binding`, and the provider's own `host_state`, `_selection` and `_verify_host`. Any
  substitute makes it `mocked`.

Where the labels appear:
- **Before a verified HOST:** a refusal raised before any HOST was verified in the process says
  `unavailable: no HOST document has been verified in this process` for the four HOST-derived
  labels.
- **Ledger, setup, cohort and refusal records** carry the labels.
- **The manifest** carries them too, and the probe verifies them against HOST before any reader
  import.
- **The probe's result** takes the manifest's labels at initialization.

## 7. The probe and its segment map

[`W5-PROBE-MAP.json`](W5-PROBE-MAP.json) lists 21 preserved and 20 adapted segments. Each has its
line ranges and SHA-256 in both files, and each adapted segment its reason.
- **The scientific body** is the 0.1.0 probe's lines 1–38, 679, 683–691 and 695–809, which are
  `readback.mjs` unchanged. It lies entirely inside preserved segments.
- **The adapted segments** are bootstrap only:
  - the 0.2.0 identifiers and constants;
  - the Darwin host check: `os.type()`, `os.machine()` and `os.release()`; `SystemVersion.plist`
    and the cryptex copy by bytes, with the copy's link hops followed again (D-10); and
    `process.execPath` and its bytes against HOST's pin. There is no boot check, which is the
    stated weakening of E19, and no ELF, alias or `ldd` check;
  - `environmentAdmitted`, the JavaScript twin of the observer's predicate, with HOST's recorded
    `__CF_USER_TEXT_ENCODING`;
  - the M0 and M1 inspection receipts;
  - the labels and design-revision checks;
  - two schema lines in the main block.
- **Parser:** none is available in this phase. Without Node or npm, neither `node --check` nor a
  JavaScript parser can run, so no token or AST comparison was executed. **Byte identity of each
  preserved segment is stronger than token equivalence**, because any tokenizer's output is a
  function of the bytes. It is not a syntax check of the adapted segments; the probe syntax start
  at MH (contract section 7) is the first execution.
- **Assembly:** the probe was assembled by a script that copies the unchanged 0.1.0 lines byte for
  byte. The script and the map generator are kept in the worker evidence.

**MC11, the probe part, development run.** The scan's 15 hits are each reviewed in the map. They
are the same `(pattern, text)` set as the 0.1.0 probe's:
- static imports of `node:fs`, `path`, `crypto`, `module`, `url` and `os`;
- `createRequire`;
- one computed `require` of the bound validator entry;
- two computed `import()` calls of the bound Three.js and GLTFLoader entries;
- two `RegExp.prototype.exec` calls;
- the substring `Function` in `externalResourceFunction`.

There is no `child_process`, `cluster`, `worker_threads`, `process.dlopen`, `eval`, `Function`
constructor or `Worker`. A scan of names cannot exclude every dynamic route. The module loader and
the 24 reader files are MH's.

## 8. Development tests

`TMPDIR="$(cd "$TMPDIR" && pwd -P)/" .venv/bin/python -B -m unittest tests.test_current_host_readback_provider_v02 -v`:
45 tests, all passed, in about 1.7 s. They use the standard library only, with synthetic HOST,
configuration, trees and receipts.
- **Mocked boundaries:** the Darwin supervisor, the host readers, the selection, the Python
  inventory and the runtime check are mocked where a test says so, and the provider then labels
  its results `mocked`.
- **Synthetic pins:** the archive and C199/C195 pins are patched to the synthetic digests in the
  tests that need them.
- **Mutation check:** 22 mutations of the provider and the facade, each detected by at least one
  test. The provider was restored and hash-checked after each one; the facade mutations ran
  in-process only.

| Class | Tests | Covers | Starts |
| --- | ---: | --- | --- |
| `VersionRefusalTests` | 3 | v02 entry points refuse 0.1.0 configurations (both key sets), including setup and the adapter with zero starts; the 0.1.0 code refuses a 0.2.0 configuration; every document kind at `/0.2.0` refuses `/0.1.0` | none |
| `DispatchTests` | 3 | each of the seven entry points by schema (0.2.0, 0.1.0, another), a digest mismatch kept in 0.1.0; `git_binding_from_selection` for 0.2.0, 0.1.0 and refusals, with process creation patched to fail | none |
| `SelectionRuleTests` | 2 | S8 exact message, not a skip, `run_kind`, zero starts; partial selection | none |
| `HostBindingTests` | 11 | a consistent HOST; MC33 before any read; another contract, revision, amendment set, profile or executor; MC09 boot, build, cryptex and hop changes since HOST; MC31 HOST record through the predicate; exact-set Python trees and the interpreter build; runtime, archive, Git, inspection and label drift; inspection receipts of another revision; the adoption-record and contract bindings; HOST's source, observer and reader-tree cross-binding; labels and boundary detection | none |
| `RuntimeLayoutTests` | 2 | MC35 through the observer's real `check_runtime`: `.DS_Store`, extra, partial, changed, linked and inaccessible trees refuse, and nothing is repaired; the unchanged tree passes layout and pin and reaches the Mach-O rules | none |
| `SourceGitTests` | 6 | MC19: clean source with every read through the bound executable; dirty or untracked source; another commit or checkout; a changed provider or probe before any Git start; unbound, dispatcher, mismatched or relative Git, or another binding, before any Git start; a changed bound Git never falls back | a `/bin/sh` stand-in Git, 5 starts per passing source check |
| `DependencyTreeTests` | 2 | MC18: the exact tree; missing, extra, changed, linked and `.DS_Store` | none |
| `AttemptTests` | 7 | the positive attempt through the facade with boot before and after and labels; the genuine `Stop` re-raised; MC09 before the start (zero starts) and across it (fails); MC29 input, selection and OS changes after preflight (zero starts); MC31 launch environment (zero starts); MC21 selections (zero starts) | none; the supervisor is mocked |
| `CohortAccountingTests` | 5 | D-08: a complete cohort passes, a missing method or an attempt without its start fails; setup records boot, labels and run kind, and refuses a boot change before the cohort | none |
| `ProbeSegmentTests` | 4 | the map binds both files; every preserved segment byte-identical with its SHA-256; segments partition both files and cover the scientific body; MC11 scan equals its reviewed hits | none |

These are development tests, not frozen controls. They add 45 methods to the default inventory,
which MH's execution plan must approve (MC28).

## 9. Checks and measurements

Evidence is in `../OntoKin-local/c271-p33/workers/W5/`, beside the clone.

| Check, at head `bb15ddda` plus W5's files | Outcome |
| --- | --- |
| `tests.test_current_host_readback_provider_v02` | 45 OK |
| `tests.test_current_host_readback_provider` | 22 of 25; the same three Linux-only failures as at the base |
| `tests.test_current_host_readback_driver` | 30 OK |
| `tests.test_static_tray_readback_v01` | 4 run; the one `setUpClass` error now carries the S8 reason |
| `tests.test_current_host_inspection_v01` | 64 failures and 8 errors, the same 72 test IDs as W2's recorded baseline |
| `tests.test_current_host_observation_v02`, `tests.test_supervisor_darwin_v01` | 109 OK; 17 OK |
| `tests.test_prepare_current_host_readback_v02` | 58 of 59; one error that W5's files do not cause (finding F1) |
| mutation check | 22 of 22 detected |
| whitespace and ASCII | clean |

**Measured on this host**, read-only:

| Measurement | Result |
| --- | --- |
| Python installation inventory (`observation.python_inventory`) | 518 ms cold, 152 ms warm (3 runs); compare and digest 4.6 ms |
| its size | 3,788 framework entries, 14 venv entries, 84 images, 5 external dependencies, 6 link hops; 696,871 canonical bytes |
| source inventory | provider 116 ms, observer 37 ms; 642 files |
| `host_state()` (sysctls and both plists) | 0.3 to 2.9 ms |

Each selection check reads HOST, the source, the Python trees, the runtime, the reader tree and
the methods. A cohort makes 12 such checks: 2 at setup, 3 per case and 1 at the end. Before each
start, the preflight and launch checks use part of the original 28-second stage allowance; the
Python inventory is about 0.15 s of each check.

## 10. Findings

- **F1.** `tests.test_prepare_current_host_readback_v02`'s
  `test_D11_result_keys_are_closed_by_state_without_publication` errors at `bb15ddda`. It reads
  `observation.INSTALL_RESULT_KEYS`, which W3's commit renamed to `INSTALL_RECEIPT_KEYS`. The error
  lies between W2's test and W3's module.
- **F2.** D-08 needs no new rule. The 0.1.0 cohort accounting requires exactly the three case
  ledgers, each with one start, no provider failure and the expected exit. A method that did not run
  leaves no ledger and fails `finish_cpu_cohort`. The 0.2.0 provider keeps this, and a test shows
  it.
- **F3.** HOST records the environment as `{declared, cf_user_text_encoding}`, not as M0's full
  observed map. The provider applies the observer's predicate to that record. It therefore checks
  HOST's declared map against the provider's declared environment, and the shape of the recorded
  value. The comparison of an actual environment with the recorded value happens in M0 and in the
  probe.
- **F4.** The amendment's adoption record is `ADOPTION-AMENDMENT-001.json`. It was adopted during
  this work (`3ffabb3f`): SHA-256 `872312ed80a63fbb196c17ace42e786b7fe757b710eff41139b125dfaa507937`,
  5,396 bytes, mode `0o644`. The assignment left the probe's digest constant to the Director, but
  the record now existed. W5 therefore set `AMENDMENT_ADOPTION_SHA` to that digest. Otherwise
  filling it later would have left the map's file digest stale.

## 11. Assumptions

- HOST, inspection receipts and labels have the shapes of W3's code at `bb15ddda`.
- Node's `process.execPath` is the canonical executable path. It is compared with the canonical
  `config.runtime.executable`.
- Node's `os.release()` and `os.machine()` equal `os.uname()`'s release and machine.

## 12. Open questions

- **Q1. MC36's premise.** The probe's predicate refuses an altered recorded value only if Node's
  `process.env` contains `__CF_USER_TEXT_ENCODING`. Without it, the observed environment equals
  the declared one and is admitted, as contract section 7 states. MC36's expected refusal therefore
  depends on what MH observes for the official `node`.
- **Q2. The adoption record and the source set.** The adoption record is not in the `/0.2.0`
  source set. W3's `SOURCE_FILES` does not list it, and the configuration and the probe bind it
  separately. Should `SOURCE_FILES` add it, or the amendment's files?
- **Q3. F4.** The Director should confirm the filled digest.
- **Q4. The ordinary-run setup record.** The facade's ordinary-run refusal record keeps the 0.1.0
  module's `setup/0.1.0` and `refusal/0.1.0` schemas, because no version is selected.
- **Q5. Labels of a refused probe result.** A refused probe result can carry manifest labels that
  `verifyBootstrap` has not yet verified. A passed result has verified labels.
- **Q6. Boundary detection.** The `mocked` label detects a substituted object among the listed
  boundaries. A substitute inside the observer's internals would not be seen.
- **Q7. Speed of the provider's source inventory.** It hashes the files once more after the
  observer's path walk. It could reuse the walk's bindings if the 116 ms matters.
