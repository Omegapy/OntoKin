# C271 P07 — host inspection authoring design

**State:** design candidate for independent review; no implementation or host qualification.

**Source boundary:** retained branch `work/c271-missing-import-digest-control` at `3d9d5eacaff25244916f99912ef92947e1582592`, supplied by the Director. The author read and hashed the local source. `SOURCE-BINDINGS.json` binds the inspected bytes and source anchors; the Director owns live Git reconciliation. Substantive authoring started only after the Director confirmed the early recovery save at `2026-11-21T06:14:04.963212+00:00`.

This design supplies the missing way to **create** the host and inspection records that P06 already consumes. It keeps the adopted P05 contract and every existing source byte unchanged. It does not select an operational host, approve a runtime configuration, run Node or `ldd`, or close C271 R03–R05. [S01–S07]

## 1. The approval boundary

The existing `validate_selection` is unsuitable as the first inspection gate: it requires a completed `HOST.json`, which itself requires successful version and `ldd` receipts. Calling it before creating those receipts would be circular. The authoring entry point instead takes a **separate, independently reviewed static inspection plan**. [S08: `_selection`, `_verify_host`]

The sequence is fixed:

1. Implement and independently review the bounded authoring module and its focused controls in a later phase. Freeze its actual clean source commit/tree and inventory.
2. In a separately selected preparation phase, statically inspect the actual host files and exact retained archives. Prepare the runtime/dependency destinations through the existing non-replacing preparer. Author an inspection-plan candidate with exact commands, interpreter/inspector inputs, loader inputs, source identities and output paths. This work starts no Node or `ldd`.
3. An independent reviewer accepts those exact static plan bytes and records their digest outside the plan. The actual execution invocation supplies that expected digest. Computing the observed digest is not approval.
4. Execute only the plan's two bounded preparation commands, once each and in the frozen order. Fresh observations either produce compatible success records or retained failure/unknown evidence.
5. Independently review the complete observation package. Only then create and approve a separate qualification execution plan that binds the resulting `HOST.json`, receipts, real source/dependency/method records and an exact P06 configuration digest.
6. Execute the later qualification commands only under that second plan. Gate R, integration and closure remain later gates.

A static plan authorizes a small future observation. An observation does not approve its own command, source, host lock or subsequent checker configuration. The final host/config approval is external to every P06 schema. Neither stage edits a signed-off input in place. A changed host/input requires a new plan, independent review and fresh attempt paths; earlier records remain intact. [S01 §§3–8; S05; S08]

`QUALIFICATION-PLAN.json` is a **design freeze**, with `executable: false` and explicit unavailable future bindings. It is deliberately a different schema from both the proposed executable inspection plan and P06 configuration. No authoring or execution entry point may accept it as an executable plan.

## 2. Bounded implementation surface

Add one future module:

`prototypes/static_tray_v01/current_host_inspection_v01.py`

Add focused tests in one future file:

`tests/test_current_host_inspection_v01.py`

Both paths fall under the existing Python and JavaScript `SOURCE_TREES`; the new executable cannot be an untracked external harness or an unlisted tool. The future source lock must include these actual files and all existing source members, and must pass the same clean-commit/tree checks. No new `tools/` wrapper, automatic installer, generic host profiler, loader replacement, source exclusion, platform abstraction or consumer-schema change is required. [S08: `SOURCE_TREES`, `_source_paths`, `_verify_source`; S09: `SOURCE_TREES`, `verifySource`]

Proposed CLI, expressed as argument templates rather than executable commands:

`APPROVED_PYTHON -I -S -B ABSOLUTE_SOURCE/prototypes/static_tray_v01/current_host_inspection_v01.py --plan ABSOLUTE_PLAN --plan-sha256 EXTERNALLY_APPROVED_SHA256`

The default checks static bindings and returns a static result to the independently captured stdout; it does not create the planned observation attempt root. Adding `--observe` permits only the two plan commands and their predeclared evidence writes. Unknown options, relative paths, missing digests, another schema, template fields or partial input records fail visibly. There is no `--force`, runtime discovery, fallback executable, arbitrary command list, retry, repair or approval-writing option.

The bootstrap uses the existing, independently identified Python executable. `-I -S -B` disables environment-based Python selection, site initialization and bytecode creation. The script derives its source root from its own canonical file path; after authenticating that local file against the selected plan, it adds only that root for imports of the bound provider/supervisor. Its launcher and relevant Python executable, standard-library, extension/interpreter and loader inputs are part of the independently reviewed plan. This is an explicit trust boundary for the already-running host and kernel, not a claim to authenticate an entire operating system. The module does not launch another Python interpreter to discover these identities.

P06 later compares `host.python.executable` with resolved `sys.executable`, its version with `platform.python_version()`, and all seven package versions through `importlib.metadata`. Therefore the authoring executable must be the same resolved interpreter selected for later qualification. With site initialization disabled, authoring reads the exact seven approved distribution metadata records through explicit plan-bound paths; it must not add a site directory or execute its `.pth`/startup hooks. The later provider's ordinary metadata lookup must independently agree. An incompatible metadata layout is a concrete refusal, not a reason to fabricate a package version. Package-version agreement is the unchanged seven-pin predicate, not authentication of every package byte. Bind any package code actually imported by the authoring tool as an executable input; this design does not add a whole-environment package audit. [S08: `_python_pins`, `_verify_host`; S09: `verifyHost`; S14]

Proposed API, all in that single module:

| API | Contract |
| --- | --- |
| `validate_inspection_plan(plan_path, expected_plan_sha256)` | Bounded strict decode, external digest comparison, closed shape and full static binding checks; no Node/ldd/checker and no host success record. The existing source guard may make only its five bounded, separately bound Git identity reads. Returns an immutable validated-plan value. |
| `inspect_host(plan_path, expected_plan_sha256, *, observe=False)` | Revalidates at entry. With `observe=False`, returns `STATIC_READY` to the outer capture without consuming the fresh observation paths; with `observe=True`, creates the independently authorized attempt evidence, runs the two fixed commands and returns `OBSERVED_UNAPPROVED` only after durable evidence and consumer compatibility checks. |
| `parse_ldd_output(stdout, stderr, expected_resolution)` | Pure bounded parser. Requires the frozen grammar and exact expected closure; never uses output to expand execution authority. |
| `reconcile_attempt(plan_path, expected_plan_sha256, attempt_path)` | Read-only evidence/path/process reconciliation. Never relaunches, deletes a destination or promotes an uncertain attempt to a fresh success. Any supplemental reconciliation is a new immutable record. |

Errors use `HostInspectionError(RuntimeError)`, never `supervisor.Stop`, with stable `CHI-*` categories in `CONTROL-MATRIX.json`. Original supervisor exceptions and any actual `process_record` remain attached unchanged. The provider's `CurrentHostBindingError` remains unchanged too.

## 3. Proposed executable inspection-plan contract

Schema identifier: `ontokin.current-host-readback-inspection-plan/0.1.0`. This schema is new and bounded to the first Linux/glibc host and the already selected Node build. All object keys below are required and closed. Missing, duplicate or unknown keys, nonfinite numbers, noncanonical paths, unexpected types or unresolved values fail. JSON is sorted ASCII with comma/colon separators and no nonfinite values, as in P06. The maximum plan is 16 MiB. Ordinary file descriptors use the unchanged P06 `{path, sha256, size_bytes, mode}` shape; file bindings use `{sha256, size_bytes, mode}`. [S06; S08: `_canonical`, `_read`, `_binding_shape`]

| Top-level field | Exact contract |
| --- | --- |
| `schema` | The identifier above; never the P07 design-plan identifier. |
| `contract` | Exactly `ontokin.current-host-readback/0.1.0`. |
| `source` | P06 source binding: normalized absolute `root`, actual clean `commit` and `tree`, and exact complete inventory descriptor. |
| `author` | `{entry_point, source_descriptor, python_descriptor, python_version, runtime_inventory, metadata_inventory, git_descriptor, source_commands}`. Entry point is the new module under `source.root`; descriptors bind actual files, not claims of version equivalence. `runtime_inventory` and `metadata_inventory` are immutable file descriptors to the closed records below. `git_descriptor` binds the actual Git executable selected by the fixed PATH, and `source_commands` freezes the five existing source-guard read operations and sanitized Git environment. |
| `runtime` | `{executable, version, candidate, source_archive, install_receipt}`. Exact task-specific absolute destination; version `v24.22.1`; `candidate` is the P05 digest/size/mode; source archive is the exact saved P05 archive; install receipt identifies successful exact installation or independently verified already-exact content. |
| `dependencies` | `{root, inventory, install_receipt}`. External exact 24-file tree, unchanged C199 pins/layout; descriptors bind the existing preparer's outcome. |
| `host_static` | `{platform, files, aliases, roles, resolution, path_guards}`. `platform` has the P06 system/release/machine/libc/boot fields observed statically. `files`, `aliases` and `roles` have exactly the P06 shapes and complete set relations. `resolution` and `path_guards` are described below. |
| `environment` | Exactly `PATH=/usr/bin:/bin`, `LANG=C.UTF-8`, `LC_ALL=C.UTF-8`, `TZ=UTC`, `UV_THREADPOOL_SIZE=2`. No inherited child variables. |
| `commands` | Exactly two ordered records, `node_version` then `shared_libraries`; each is `{id, argv, cwd, label, timeout_ms, active_work_ms, cleanup_ms, expected_direct_starts, stdout_predicate, stderr_predicate}`. Values are fixed below. |
| `evidence` | `{parent, attempt_root, ancestor_identities, outputs, outer_capture}`. The parent exists outside source/runtime/dependencies. The attempt root and every output path are absent, normalized and private; ancestor device/inode/mode identities are bound. `outer_capture` identifies the independently approved invoking harness/log authority, not a path trusted from an unauthenticated plan. |
| `limits` | Exact finite values below; no caller override. |

The plan contains no `approved`, signature, expected-plan-digest or self-approval member. Review identity, reviewed plan descriptor, decision and supplied expected digest live in a separate retained review/authorization record. The CLI cannot infer authority from that record merely appearing beside the plan; the Director's separately selected execution invocation supplies its recorded digest.

The five source-read operations are the existing `_verify_source` calls: `rev-parse --show-toplevel`, `rev-parse --verify HEAD^{commit}`, `rev-parse --verify COMMIT^{tree}`, `status --porcelain=v1 --untracked-files=no`, and `ls-files --others --exclude-standard -z`, with the existing fixed `git -c core.fsmonitor=false -C ROOT` prefix. Each has at most five seconds and consumes the static-validation allowance; the actual selected Git executable and its relevant loader inputs are bound. Their counts/outputs belong to source-validation evidence, separate from the two preparation launches. No command may fetch, install, mutate the index or invoke hooks. [S08: `_verify_source`; S12: `git_environment`, `git_read`]

`author.runtime_inventory` is a closed `{schema, executable, interpreter, files, aliases, startup_files, extension_files, loader_inputs, environment}` record. It binds the executing Python binary and any ELF interpreter, startup/standard-library modules needed by this tool, admitted native extension modules and their shared inputs, and the clean launcher environment. An interpreter with unreviewed startup code or an unbounded additional executable path is refused. This finite inventory does not require a claim about unrelated installed software.

`author.metadata_inventory` is a closed `{schema, lock, packages}` record. `lock` binds the unchanged seven-pin requirements file. Each package row has `{name, version, distribution_root, metadata_files}`; names/versions must equal the unchanged lock, and the actual metadata files must be canonical and bound. This reads the installed pin evidence without adding a new package-installation or package-byte requirement. No package import is needed to inspect these records.

`host_static.resolution` is a closed `{profile, images, needed_edges, loader_inputs, search_directories, inspector_commands, ignored_kernel_rows, rationale}` record. Profile is `linux-glibc-declared-closure-v1`. Every `images` row binds a predeclared ELF path, bounded static interpreter/dynamic metadata and its admitted resolution; `needed_edges` records the complete finite transitive `DT_NEEDED` relations. `loader_inputs` binds exact files or explicit absence. `search_directories` binds relevant directory identities and complete relevant entry inventories. `inspector_commands` binds the exact `ldd` script/interpreter and all external commands/loaders its reviewed branches can invoke, including candidates checked for existence. `ignored_kernel_rows` permits only the exact kernel-vDSO grammar described below. `rationale` points to the independent source-backed review of this one declared resolution, not a tool-generated declaration that the whole host is trusted.

`host_static.path_guards` contains every significant ancestor and alias hop: `{path, kind, device, inode, mode, target}` rows for existing paths, and `{path, parent, parent_device, parent_inode}` rows for required absence. Presence/absence is rechecked. P06's host alias record describes only the named link and final target, so this separate record is needed to protect intervening path components and directory/configuration absence without adding fields to `HOST.json`.

`evidence.outputs` is a closed map of planned fresh paths: `reserved`, `preflight`, per-command `intent`, `started`, `supervisor_outcome`, `stdout`, `stderr`, `inspection`, `postflight`, `failure`, plus `host`, `result`, `completion`. Paths are derived from the exact declared attempt root and command IDs, and compared with the explicit map. No unlisted success/evidence path is accepted. The external harness preopens its own bounded log under its own approval, allowing an unauthenticated-plan refusal to be captured without trusting the refused plan's output paths.

Plan limits: two direct preparation starts maximum, one per command; 5,000 ms per command including cleanup; 3,000 ms active work maximum and the existing 2,000 ms cleanup reserve; combined stdout/stderr at most 4 MiB per command; inspection document at most 8 MiB; HOST at most 8 MiB; other single evidence documents at most 16 MiB. Retain the existing supervisor's 64 MiB stage and 2,048-entry bounds. Static validation has an explicit 60-second outer ceiling and final publication a separate 30-second outer ceiling; neither extends a child deadline or permits a retry. A larger static plan that cannot finish within those bounds is unsupported pending a separately reviewed design revision.

## 4. Static closure before execution

The new tool validates a **predeclared finite resolution map**; it does not discover an executable by running it and does not become a general dynamic-loader emulator. The independent static review supplies the map before commands are authorized. The tool reads ELF metadata and the exact inspected script bytes, checks that every declared dependency edge and relevant path exists with the bound identity, and refuses unsupported semantics.

Mandatory static checks include:

- The selected Node is a regular nonlinked private task file, exactly 126,951,512 bytes, mode `0o755`, SHA-256 `acbe4b8d9153b841ed0697cbfc4f93e767386620edb745ab9358306c0a6f31aa`. Its source archive is 45,186,132 bytes with SHA-256 `100ae976555b388472c3e875aeda67bd7d8c9229a968a11661fb852624adaeb5`. `SOURCE.json` and the install receipt preserve source/destination provenance. No version execution is used to forgive a mismatch. [S01 §4; S08 constants; S10]
- Bounded ELF parsing checks header class/endian, file/table bounds, exactly one `PT_INTERP`, finite dynamic tables and strings, all `DT_NEEDED` edges, and declared `RPATH`/`RUNPATH` interpretation. Node and each relevant inspector/interpreter/external command have their actual interpreter and transitive relevant shared inputs bound. Reject malformed tables, unresolved/duplicate/conflicting edges, unreviewed token expansion, audit/filter/auxiliary loader features or architecture mismatch.
- The exact `/usr/bin/ldd` bytes, mode, private regular-file status and direct shebang are inspected before execution. The shebang must equal `#!` plus the declared `inspector_interpreter`, without arguments or `/usr/bin/env` selection. Independently inspect its actual script branches, including shell builtins, command substitution, pipelines, `RTLDLIST` candidates, testable absence and each possible external command. Bind their interpreter/runtime inputs before launch. The fixed top-level command remains `/usr/bin/ldd NODE`; invoking a loader or shell directly would not produce a P06-compatible receipt. [S08: `_verify_host`; S09: `verifyHost`]
- Bind the actual glibc loader, cache, configuration files, recursively included configuration and relevant search-directory entries. A cache may be treated as exact opaque bytes only when the independent reviewed resolution map explains the entries relevant to these particular images; otherwise refuse it. The tool checks the frozen map, not arbitrary cache formats. Every loader path that can select executable code must already be covered. Bind `/etc/ld.so.preload` as absent or exact empty content; a nonempty preload file is unsupported. No inherited `LD_*`, `NODE_OPTIONS`, `NODE_PATH`, Python hooks, shell startup variables or other injection variables enter the child.
- Relevant architecture/hwcaps search alternatives must be finite, statically identified and reviewed. Freeze their directory entries and required absences; reject unreviewed alternatives or a loader-selection rule the finite map cannot justify. Alias targets may occur in the system closure, but both named paths and all traversed components must be bound. Resolved file bindings are regular canonical files, with system hardlinks allowed only where P06 allows `private=False`.
- Freeze actual kernel/architecture/libc/boot identity, Python executable/version/packages, source and dependency inventories, executable destination and evidence ancestors. Recheck the complete bindings immediately before each command and after each outcome, including a failed outcome. Host reboot, changed loader inputs, new candidate directory entries, or any source/runtime drift invalidates the attempt.

Unsupported hosts include non-Linux, non-glibc, an unrecognized or unexplained loader/cache rule, static or malformed selected executable, incompatible shebang, symlinked `/usr/bin/ldd`, missing required roles, unresolved closure, whitespace-containing library paths that cannot satisfy both current consumers, and any safe path/evidence guarantee unavailable on the selected filesystem. Stop with the exact reason. Do not broaden accepted formats, normalize away an ambiguity or rewrite P05/P06 to make a host fit.

This model binds the declared execution inputs and verifies the observed resolution. It does not prove the internals of the kernel, every possible behavior of a native binary, or the absence of all hostile concurrent mutation. Path and inode checks detect observed drift; they do not provide a kernel-enforced immutable namespace. The selected build remains an identified supplied runtime, without a new vendor-provenance assertion. [S01 §4; S07]

## 5. The two commands and their records

| Order / ID | Exact child argv | Expected direct starts | Output predicate |
| --- | --- | --- | --- |
| 1 / `node_version` | `[runtime.executable, "--version"]` | 1 | Strict UTF-8 stdout is exactly `v24.22.1\n`; stderr is empty. |
| 2 / `shared_libraries` | `["/usr/bin/ldd", runtime.executable]` | 1 | Strict UTF-8 stdout matches the frozen parser grammar and exact declared path set; stderr is empty. |

Each command uses its own fresh stage/cwd and fixed label (`host-node-version` or `host-shared-libraries`), exact five-variable environment, `stdin=DEVNULL`, one process group, no shell wrapper and no retry. Reuse the unchanged `supervisor.run_process` with `Clock(total_ms=5000)`, `stage_end=clock.started + 3`, `cancel_after_ms=None` and a single start callback. This preserves its 2,000-ms cleanup reserve inside five seconds. It does not mean five seconds of active work plus cleanup. Preparation counts are separate from direct-probe negatives and the three original CPU checkers. `ldd` can start its reviewed descendants; one direct launcher receipt is not a claim to have counted every internal exec. Group cleanup is still mandatory. [S11]

Static source/full-inventory work occurs before this command clock starts. The final launch-binding check, start callback and process capture consume its allowance. After the supervisor returns or raises, preserve the actual result before later checks. A success receipt requires a monotonic process interval in `[0, 5]` seconds, return code zero, positive PID equal to process-group ID, closed handles, successful reaping and absent group, exact environment/argv/cwd/label, nonnegative actual stream counts and `error: null`. Wall timestamps must be zoned, ordered and not in the future. Raw log lengths must equal observed and retained counts for success. No missing receipt field is synthesized from an expected value.

The unchanged supervisor writes its own `.process.json` without a durable atomic-publication guarantee. The new wrapper retains that raw file as evidence but does not mistake it for its own committed record. If the supervisor loses its final write and raises without `process_record`, retain the earlier actual start receipt and logs, record final status as unknown, and refuse a compatible success inspection. Never reconstruct a purported successful process record from an exit code or from the expected template. [S11: `run_process` finalizer]

### Strict `ldd` parsing

Accept only a blank-free sequence of admitted glibc output lines, with leading/trailing horizontal whitespace allowed. Each nonempty line must be exactly one of:

1. `SONAME => ABSOLUTE_PATH (0xHEX_ADDRESS)`;
2. `ABSOLUTE_INTERPRETER_PATH (0xHEX_ADDRESS)`;
3. the predeclared kernel-only vDSO name followed by `(0xHEX_ADDRESS)`.

SONAME is a nonempty single token without `/`; every address is explicitly parsed as hexadecimal, and every path is absolute, normalized, nonempty and has no whitespace/NUL. Require one interpreter row, the expected unique SONAME-to-path mapping, no duplicate/conflicting file rows, and at most one exact vDSO row. The vDSO is kernel-provided and is retained as a non-file observation; it is not fabricated into `host.files`. Reject `not found` in either stream, `statically linked`, `not a dynamic executable`, arbitrary warnings, relative/bare unresolved names, empty output, malformed parentheses, unknown rows or unexpected stderr. Raw bytes remain unchanged in logs; parsing does not sanitize them into a success.

The final absolute path set must equal `roles.shared_libraries ∪ {roles.elf_interpreter}` exactly, matching both existing consumers. `roles.shared_libraries` excludes the separate interpreter and vDSO and must be nonempty. Every returned path must have been authorized in the static plan, resolve through the predeclared aliases, and match its file identity. A newly observed library cannot be added to the accepted plan after it has executed. Stop; a later separately reviewed plan can address the difference. [S08: `_verify_host` regex/set comparison; S09: `verifyHost`]

## 6. P06-compatible output, without schema changes

The tool emits a P06 inspection document only for a fully successful bounded command. Its exact keys are:

`schema, argv, environment, timeout_ms, started_at_utc, finished_at_utc, process, stdout, stderr`.

`schema` is `ontokin.current-host-readback-inspection/0.1.0`; timeout is 5,000. `process` has exactly the fourteen keys required by P06: `argv, cwd, environment, label, start_monotonic, pid, process_group, returncode, observed_log_bytes, retained_log_bytes, cleanup, handles_closed, error, end_monotonic`. `cleanup` has exactly `passed, process_group_absent, reaped, elapsed_ms`, with true success booleans and elapsed at most 2,000 ms. There are no approval, count, plan-hash or failure additions inside these closed objects. [S06 `$defs/inspection`, `$defs/cleanup`]

The host document has exactly:

`schema, observed_at_utc, platform, python, runtime, files, aliases, roles, environment, inspections`.

Its schema is `ontokin.current-host-readback-host/0.1.0`. The host timestamp follows both inspection finishes. `runtime` has exactly `executable, version, candidate_sha256, candidate_size_bytes, candidate_mode, source_archive`. `roles` has exactly `node, python, ldd, inspector_interpreter, elf_interpreter, loader_configuration, shared_libraries, inspector_runtime`; the last three are nonempty duplicate-free lists. `aliases` keys equal the union of all named roles, and `files` keys equal their unique resolved paths. `inspections` has exactly `node_version` and `shared_libraries`, each an actual finalized file descriptor. `files` includes all admitted author/inspector/interpreter and loader inputs representable as files; role lists are not filled with unrelated dummy paths just to satisfy the schema. Additional non-file/absence/ancestor guards remain in the externally bound plan and sidecars. [S06 `$defs/host`, `$defs/roles`; S08; S09]

Run static compatibility validation against the actual bound P06 schema and consumer predicates before marking the observation package complete. Do not invoke `validate_selection` with a fabricated HOST during bootstrap. After real HOST and companion inputs exist, a future static-only consumer check may call `validate_selection` using an **independently approved provisional configuration descriptor**, with zero Node/`ldd` starts; it is not a CPU qualification. JavaScript consumer compatibility remains a later real execution gate.

`HOST.json` is an observed candidate. The sidecar explicitly labels it `OBSERVED_UNAPPROVED`. Its existence or digest alone cannot select it for the provider. The independently reviewed final P06 configuration later contains only the existing required keys, with `parent: null`. Its expected digest is recorded only in the separate qualification execution plan. The driver creates its own later derived workspace binding and preserves that parent configuration. [S08: `_selection`, `derive_workspace_binding`; S12]

## 7. Durable failure and no-replace publication

All writes happen inside the authenticated, externally predeclared evidence parent. An untrusted/mismatched plan cannot authorize an output path: return structured stderr with `evidence_finalized: false`; the independently approved outer harness captures it.

After authenticating the plan and evidence ancestors, create the attempt root exclusively with mode `0o700` and retain its device/inode. Before any child, atomically publish `reserved.json`, `preflight.json` and each command's intent. The intent records command identity, expected start count, zero observed starts and the pending/unknown completion state. It is not proof that no child started: once the launch boundary may have been crossed, a missing callback leaves the exact actual count unknown. The start callback immediately records the actual PID/group and increments the direct-start count once. A callback failure still counts the actual start and causes failure/cleanup; it never becomes a zero-start refusal.

Use one local atomic evidence writer: create a fresh same-parent temporary file with `O_EXCL|O_NOFOLLOW`, write the complete canonical bytes, fsync it, publish with Linux `renameat2(RENAME_NOREPLACE)`, then fsync the parent. The reachable reuse path is explicit: after the new script has authenticated its own canonical source root and the complete source inventory, with that root as the only added import path, use `from tools.prepare_current_host_readback import rename_without_replacement`. Both existing source inventories explicitly include that preparer and its provider dependency. Its guarded `main` does not run on import; call only this bound syscall wrapper. This adds no new wrapper module or untracked executable helper. Do not use overwrite rename, in-place JSON updates, hardlink publication, cleanup of another writer's path or implicit `mkdir(parents=True)` across unreviewed ancestors. Bind/check ancestor and owned staging identities before and after publication. [S10: `rename_without_replacement`, installation intent/readback; S08: `_write_new`]

No-replace conflict or lost/uncertain rename reply triggers readback of that exact source/destination pair. Preserve the intended bytes/hash, observed state and exception; do not retry. Only the proven owned temporary staging inode can be cleaned. A final success marker is published last, after each referenced file and directory fsync has been checked. Reserved/intent records are immutable history, not removed markers. A missing final marker, `failure.json`, unknown outcome or incomplete referenced file set blocks success even if a `HOST.json` file exists.

New sidecar schema `ontokin.current-host-readback-inspection-attempt/0.1.0` is independent of P06. Required fields are `schema, plan, command_id, expected_argv, expected_direct_starts, actual_direct_starts, observed_direct_starts, start_count_state, state, preflight, start, supervisor_process, supervisor_failure, postflight, artifacts, evidence_finalized, failure`. Descriptor/null fields are typed explicitly. `actual_direct_starts` is 0, 1 or null; `observed_direct_starts` is the retained lower bound, 0 or 1; `start_count_state` is `PROVEN_ZERO`, `OBSERVED_ONE` or `UNKNOWN`. `PROVEN_ZERO` requires a completed pre-launch refusal proving the supervisor/launch boundary was not entered, and has exact count 0/lower bound 0. `OBSERVED_ONE` requires an actual retained PID/start or final process receipt, and has exact count 1/lower bound 1. An interrupted or lost launch-to-callback window is `UNKNOWN`, with exact count null/lower bound 0; missing evidence never supplies a zero. Counts above one violate the no-retry contract and fail with retained actual evidence. The sidecar states are `NO_START`, `STARTED`, `COMPLETED`, `REJECTED`, `TIMEOUT`, `CANCELLED`, `UNKNOWN`. `COMPLETED` still means only that preparation command completed, never that the host is qualified. Preserve exact raw process receipts and failures without mutating them to fit the success schema.

New overall result schema `ontokin.current-host-readback-inspection-result/0.1.0` has `schema, plan, mode, state, command_attempts, actual_counts, artifacts, host, evidence_finalized, failures`. Mode is `static` or `observe`; successful states are `STATIC_READY` or `OBSERVED_UNAPPROVED`. `host` is null unless both real commands and all finalization checks succeed. Actual counts distinguish attempted launches, observed direct starts, Node-version starts, `ldd` launches and zero checker starts. Each aggregate with an unresolved launch has `exact: null` and a retained `observed_lower_bound`; it must not sum unknown counts as zero. Expected counts remain exact plan inputs. An inspection success requires an observed exact count of one for each preparation command. Complete counts do not stand in for individual receipts.

Timeout, nonzero exit, log overflow, decode/parser error, pre/postflight drift, lost process receipt, cleanup failure, callback failure, evidence write error, publication race and interruption all retain an unsuccessful attempt and block the next command. A killed authoring process can leave only durable intent/start records; that is an unresolved attempt, not permission to repeat it. `reconcile_attempt` may inspect actual process groups and files under the bound boot identity, but it must not invent termination or successful completion from PID absence alone.

If the evidence filesystem itself cannot retain a failure, the tool cannot promise durability. It must return `evidence_finalized: false`/`UNKNOWN`, retain any already committed records, and let the outer harness capture the error. There is no successful outcome when failure evidence or cleanup is uncertain. This limitation is explicit rather than hidden behind a successful exit or a reconstructed receipt.

## 8. Preserved obligations and next checkpoint

The exact original seven methods and two shared helper bodies stay unchanged, as do the scientific JavaScript segments, independent synthetic/reference construction, original supervisor/coordinator logic, 24 dependency bytes, same selected Node build, source budgets and historical evidence. The twelve manifest slots remain structural only; `unused-native-schedule` must remain absent. No Blender/native/export/model/hosted operation is introduced. [S01; S08–S13; S15–S17]

The next bounded implementation phase can add the one module, focused tests and its documentation; bind exact source; pass static/filesystem and explicitly labelled mocked-boundary controls; obtain independent review; and deliver. It must stop before actual Node/`ldd` qualification. A later static preparation/review checkpoint freezes real host fields. The staged Gate H and Gate R schedule, original-method table and independent audit requirements are in `QUALIFICATION-PLAN.md` and its machine-readable companion. The control matrix states which inputs still need independent fixture freeze.

P07 acceptance means this design and plan are sufficiently concrete for that implementation. It establishes no host eligibility, JavaScript runtime/syntax pass, P06-H01/H02/H03 result, original seven-method outcome, full routine completion, R03 acceptance, integration or parent closure.
