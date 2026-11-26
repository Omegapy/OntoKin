# W3: M0 and M1 host observer (S3, S7, S10)

Worker W3 of gate MI, C271-P33, on base `f3a5acf8`. This note covers development work only. It
is not frozen and not reviewed, and the observer has not run on the real host as M0 or M1. It
implements [plan sections 4.2 to 4.4](../IMPLEMENTATION-PLAN.md#4-shared-interfaces) under
[contract sections 3, 4, 7 and 10](../../macos-contract-design-p31/CONTRACT.md#7-host-observation-in-place-of-h0-and-h1-s3-s7-s9).
It follows design revision 4: the contract as amended by P33-AMENDMENT-001
([adoption](../ADOPTION-AMENDMENT-001.json)). It applies the [Director's decisions](../DIRECTOR-DECISIONS.md)
D-02, D-04, D-05 and D-10 to D-13. Section 12 lists the corrections of the first follow-up.

- [`prototypes/static_tray_v01/current_host_observation_v02.py`](../../../../../prototypes/static_tray_v01/current_host_observation_v02.py):
  one standard-library file. Importing it imports no project module, starts nothing and writes
  nothing.
- [`tests/test_current_host_observation_v02.py`](../../../../../tests/test_current_host_observation_v02.py):
  109 development tests (section 8). They are not the frozen controls.

## 1. Launch and command line

Every command requires `-I -S -B` (`PYTHON-LAUNCHER`), so no bytecode is written into an
inventoried tree. The plan's digest is always an argument, never taken from the plan.

| Command | Starts | Writes |
| --- | --- | --- |
| `static --plan P --plan-sha256 H` | none | nothing; prints a `STATIC_READY` result |
| `observe --plan P --plan-sha256 H` | M0: one Git `--version`. M1: one Node `--version`. Both through the Darwin supervisor. | the plan's absent attempt directory only |
| `python-inventory --venv V --framework F --output O` | none | the absent path `O` |
| `source-inventory --root R --output O` | none | the absent path `O` |

- **M0's launch:** `<venv>/bin/python -I -S -B <root>/prototypes/static_tray_v01/current_host_observation_v02.py observe …`,
  from exactly the declared environment. `sys.executable` must be `<venv>/bin/python`.
- **Paths:** every path argument is canonical, for example `/private/tmp/…`, never `/tmp/…`.
- **Outcome:** exit 0 prints the result on stdout. Exit 1 prints
  `ontokin.current-host-readback-observation-refusal/0.2.0` on stderr:
  `{schema, contract, design_revision, amendments, passed: false, error: {code, reason, state, cause,
  details}, evidence_finalized, result}`.
- **Values:** refusals name environment variables, never their values.

## 2. Plan: `ontokin.current-host-readback-observation-plan/0.2.0`

Every object is closed. The plan is canonical JSON (sorted keys, compact separators, ASCII), and
its SHA-256 is compared with the supplied digest before it is decoded (`PLAN-DIGEST`).

**P07 section 2 rules:**
- anywhere in the plan, a `null`, a float, `TODO`, `TBD`, `FIXME`, `XXX`, any of `* ? [ ] { } ~ $`
  and a backtick refuse (`PLAN-UNRESOLVED`), and so does a digest of one repeated digit;
- every path equals its own `canonical_path`;
- a descriptor is `{path, sha256, size_bytes, mode}` and a binding `{sha256, size_bytes, mode}`,
  with the mode written `0o%03o`.

| Key | Content and rule |
| --- | --- |
| `schema`, `contract`, `profile`, `executor` | the plan schema, `ontokin.current-host-readback/0.2.0`, `darwin-arm64-v1`, `macos-arm64-local`. Another schema refuses (`PLAN-SCHEMA`). |
| `environment` | exactly `{PATH: /usr/bin:/bin, LANG: C.UTF-8, LC_ALL: C.UTF-8, TZ: UTC, UV_THREADPOOL_SIZE: 2}` (`PLAN-ENVIRONMENT`) |
| `platform` | `{system: Darwin, release, machine: arm64, proc_translated: 0, boot_session_uuid}`. The actual release and boot, as P07 section 2 requires, so a plan serves one boot. |
| `os` | `{system_version: descriptor, cryptex}`. `system_version.path` is `/System/Library/CoreServices/SystemVersion.plist`. `cryptex` is `{state: present, path, sha256, size_bytes, mode}`, whose `path` is the copy's canonical path (finding F1), or `{state: absent, path}` with the conventional path. |
| `source` | `{root, commit, tree, inventory: descriptor}`. The inventory is `ontokin.current-host-readback-source/0.2.0`, `{schema, files: {relative path: binding}}`. |
| `observer` | descriptor of `<root>/prototypes/static_tray_v01/current_host_observation_v02.py` |
| `python` | `{venv, framework, version, inventory: descriptor}`: `<root>/.venv`, the canonical `…/Python.framework/Versions/3.12`, its patch version, and the frozen inventory of section 5 |
| `runtime` | `{directory, version: v24.22.1, root_mode, bin_mode, executable: binding, node_source: binding, archive: descriptor, install: {plan, result}}`. `archive` is the retained official archive, whose SHA-256 must be the pin (`RUNTIME-ARCHIVE`). Another version refuses before any start (`RUNTIME-VERSION`, MC33). |
| `dependencies` | `{root, inventory: descriptor, install: {plan, result}}`. The inventory is `dependencies/0.2.0`, `{schema, files, directories, archive}`. |
| `git` | descriptor of the Git implementation. `/usr/bin/git` refuses (`GIT-DISPATCHER`), and so does a link (`GIT-SYMLINK`). |
| `commands` | exactly `expected_commands(plan)`, in order (`PLAN-COMMANDS`) |
| `evidence` | `{parent, ancestors, attempt, outputs}`. The parent exists, is canonical and lies outside every bound root. `ancestors` lists `{path, device, inode, mode}` for the parent and each ancestor, sorted by path. `attempt` is an absent direct child. `outputs` equals `output_paths(attempt)`. |
| `failure_capture` | `{procedure: descriptor}`: the separately approved failure-capture procedure, bound by its bytes and outside the attempt |
| `limits` | exactly `LIMITS` |

Each command record has exactly `{id, kind, argv, cwd, label, environment, timeout_ms,
active_work_ms, cleanup_ms, expected_direct_starts, stdout_predicate, stderr_predicate}`. Both
have `cwd` `<attempt>/<id>`, 5,000 ms in all with 3,000 ms of work and the 2,000 ms cleanup
reserve, one expected direct start and an empty `stderr_predicate`.

| `id` | `kind` | `argv` | `environment` | `label` | `stdout_predicate` |
| --- | --- | --- | --- | --- | --- |
| `git_version` | `other` | `[git.path, "--version"]` | declared, plus `GIT_CONFIG_NOSYSTEM=1`, `GIT_CONFIG_GLOBAL=/dev/null`, `GIT_TERMINAL_PROMPT=0`, `GIT_ATTR_NOSYSTEM=1`, `GIT_OPTIONAL_LOCKS=0`, `GIT_NO_REPLACE_OBJECTS=1` | `host-git-version` | `git-version-line-v1`: one line, `git version`, printable ASCII, `\n` |
| `node_version` | `node` | `[<directory>/bin/node, "--version"]` | declared | `host-node-version` | `v24.22.1\n` |

**Outputs:** `<attempt>/{reserved,preflight,result,completion,failure}.json` and
`<attempt>/HOST.json`. Each command adds `<attempt>/<id>/{intent,started,inspection,postflight,failure}.json`
and the supervisor's own `<label>.stdout.log`, `<label>.stderr.log` and `<label>.process.json`.

## 3. HOST: `ontokin.current-host-readback-host/0.2.0`

It is written only after both starts have succeeded and every binding has been checked again.
It is an observed candidate (`OBSERVED_UNAPPROVED`). W5 consumes this shape unchanged.

| Key | Content |
| --- | --- |
| `schema`, `contract`, `profile`, `executor` | the identifiers; `executor` is `macos-arm64-local` |
| `design_revision`, `amendments` | `4` and `["P33-AMENDMENT-001"]`, beside `contract` (decisions D-12 and D-13) |
| `observed_at_utc` | later than both inspection receipts |
| `plan`, `observer` | descriptors of the plan and of the observer file |
| `platform` | `{system, release, version, machine, proc_translated, boot_session_uuid}`, from `os.uname()` without the node name, and from `sysctlbyname` |
| `os` | `{system_version, cryptex}`. A present file is `{state, path, sha256, size_bytes, mode, product_name, product_version, product_build_version, product_version_extra}`; the cryptex adds `link_path` (the conventional name) and `hops`. An absent cryptex is `{state: absent, path, hops}`. `product_version_extra` is a string or `null`. |
| `environment` | `{declared, cf_user_text_encoding}`: the declared map, and the observed value, a string or `null` |
| `python` | `{launcher, venv, framework, interpreter, selection, inventory, inventory_sha256, packages, records, lock}` (below) |
| `runtime` | `{directory, executable, version, binding, archive, node_source, layout, macho, install}` (below) |
| `git` | `{path, sha256, size_bytes, mode, version}`; `version` is the `--version` line without its newline |
| `dependencies` | `{root, inventory, archive, files: 24, install}` |
| `source` | `{root, commit, tree, tree_check, inventory, head}`. `head` is `{gitdir, common_dir, ref, commit, files}`, read from the Git files without a start. |
| `inspections` | `{git_version, node_version}`: descriptors of the two `inspection/0.2.0` receipts |
| `starts` | `{node: 1, other: 1}` |
| `labels` | `{executor, contract, design_revision, amendments, profile, os, node, python_inventory_sha256, git, run_kind, boundary}` |
| `claims` | `{closure, python, boot, status}`: the contract's weaker claims, stated in every HOST |

- **`python.interpreter`:** `{implementation, version, build_string, flags, executable,
  base_executable, prefix, base_prefix, path, process_image}`. `build_string` is `sys.version`,
  `flags` is `sys.flags` as a map, and `process_image` comes from `proc_pidpath`.
- **`python.selection`:** the inventory's selection record (section 5).
- **`python.inventory`:** the plan's frozen descriptor. `inventory_sha256` is the digest of the
  observed inventory, which equals the descriptor's `sha256`.
- **`python.packages`:** the lock's seven `{name: version}` pins. `records` is
  `{name: {dist_info, record, hashed_rows, unhashed_rows}}`, and `lock` describes the macOS lock.
- **`runtime`:** `binding` is Node's binding and `archive` the retained archive's descriptor.
  `node_source` is `{path, sha256, size_bytes, mode, content}`, with the parsed `NODE-SOURCE.json`.
  `layout` is `{root_mode, bin_mode, entries}`. `macho` is `{magic, cputype, cpusubtype, filetype,
  flags, ncmds, sizeofcmds, commands}`, with each command as `{cmd, name, cmdsize, …decoded
  fields}`. `install` is `{plan, result, purpose, state}`, the outcome of the receipt rule below.
- **`labels`:**
  - `os`: `{product_version, product_build_version, product_version_extra, cryptex}`. The cryptex
    label is `{state: "present", product_version, product_build_version, product_version_extra}`,
    or `{state: "absent"}` (correction W3-C3). `check_os_label` tests this shape;
  - `node`: `{archive, archive_sha256, executable, signature_check}`, the last being the recorded
    status (decision D-02);
  - `git`: `{path, sha256}`, the input of W4's `bind_git(path, sha256)`;
  - `run_kind`: `host-observation`;
  - `boundary`: `real`, or `mocked` when any host reader, the supervisor or the publication
    function was substituted.
- **Inspection receipt:** the 0.1.0 shape at `/0.2.0` with the revision fields, `{schema,
  contract, design_revision, amendments, argv, environment, timeout_ms: 5000, started_at_utc,
  finished_at_utc, process, stdout, stderr}`. `process` is the supervisor's 14-field receipt,
  unchanged.

**Receipt rule (decisions D-05 and D-11).** M0 adapts the 0.1.0 rule of `_check_installation`
and compares its fields in the shapes that W2 confirmed (W2-PREPARER.md section 7, commit
`fb86cd63`), for the runtime and for the reader tree:
- **plan** `install/0.2.0`: the closed keys `{schema, contract, purpose, source_root, archive,
  destination, root_mode, files, directories, members, node_source, report}`. `purpose` is
  `selected-node` or `retained-dependencies`; `source_root` is the plan's source root; the
  destination, root mode, files and directories equal the observation plan's tree; `archive`
  equals the retained archive's descriptor; `report` is the result's path (`INSTALL-PLAN`).
- **result** `install-result/0.2.0` (`INSTALL-RESULT`):
  - **state:** only the receipts `INSTALLED_EXACT` and `ALREADY_PRESENT_EXACT`, with `passed:
    true`. `DRY_RUN_READY`, `REJECTED` and `UNKNOWN` refuse, so does a failed report write,
    which W2 records as `UNKNOWN` with `passed: false` and `report_error` (W2's correction C4);
  - **closed keys** of its outcome: `base` = `{schema, contract, design_revision, amendments,
    purpose, passed, state, apply_requested, execution_counts, operations, pins, labels,
    preparer_source}`, with `archive` and `before`, and `after` and `publication` for
    `INSTALLED_EXACT`;
  - **values:** the contract, `design_revision` 4 and `amendments` `["P33-AMENDMENT-001"]`; zero
    starts; `operations` rows `created_owned_stage` or `removed_owned_stage`; `pins` exactly
    `{origin: "adopted-contract", node_archive_sha256, dependency_archive_sha256}` with the
    contract's pins, so a receipt made through W2's synthetic seam refuses;
  - **labels:** exactly `{executor, contract, profile, design_revision, amendments, pins, os}`.
    `pins` is `{origin, node_archive_sha256, node_executable}` for `selected-node`, with Node's
    binding, and `{origin, dependency_archive_sha256}` for the reader tree. `os` has HOST's
    `labels.os` shape (`check_os_label`); M0 checks its shape, and binds the current OS itself;
  - **preparer_source:** `{root, files_at_start}`, naming this source root;
  - **readbacks:** `INSTALLED_EXACT` needs `apply_requested` true, `before` `{state: "absent"}`,
    `after` `{state: "complete_exact", files, directories}` and `publication` exactly
    `{call: "renamex_np", library: "/usr/lib/libSystem.B.dylib", flag: "RENAME_EXCL", flag_value:
    4}`. `ALREADY_PRESENT_EXACT` needs `before` `{state: "complete_exact", files, directories}`.
- **archive summary:** exactly `{sha256, size_bytes, members, expanded_bytes, symlinks,
  member_inventory_sha256, extracted_members}`, plus `executable` for `selected-node`. Digest,
  size, member count, expanded bytes and the members digest equal the plan's. `executable` is
  `{member, path, sha256, size_bytes, mode, macho: {magic, cputype, cpusubtype, filetype}}` with
  the Node member, `bin/node` and Node's binding. The retained archive's bytes are bound
  (`INSTALL-ARCHIVE`).
- **runtime only:** `NODE-SOURCE.json`'s signature check, member digest and archive size equal the
  plan's (`NODE-SOURCE`). A `failed` signature check is recorded, not refused (D-02).

The values of `symlinks`, `extracted_members`, `files_at_start`, the readbacks' trees and the
`macho` fields are not compared; their keys are.

**Design revision (decisions D-12 and D-13).** Every document the observer writes carries
`contract`, `design_revision: 4` and `amendments: ["P33-AMENDMENT-001"]` beside its schema:
HOST and its `labels`, both inspection receipts, the attempts (`intent.json`, `postflight.json`),
the start and failure records, `reserved.json`, `preflight.json`, the result, the completion, the
refusal, and the printed results of the two inventory commands. The attempt's `intent.json` is
the observer's publication intent record. These keep their content: the supervisor's own
`<label>.process.json`, `NODE-SOURCE.json` (D-13), and the Python and source inventories, which
are frozen inputs outside D-13's list.

**Rechecks by a consumer.** The helpers of section 4 give W5 the same predicates: `environment_admitted`
with HOST's `environment`; `read_boot_session_uuid`, `read_proc_translated` and `read_os_identity`
against `platform` and `os`; `python_inventory_digest(python_inventory(venv, framework))` against
`inventory_sha256`, with `compare_inventory` for the differences.

## 4. Exported helpers

`ObservationError` carries `code` (`CHO-<category>`), `reason`, `state`, `cause` and `details`,
with `details["rule"]` wherever a rule applies.

| Helper | Signature | Meaning |
| --- | --- | --- |
| `environment_admitted` | `(observed, declared, recorded_cf) -> bool` | plan section 4.4. `declared` must not contain `__CF_USER_TEXT_ENCODING`; malformed input is false. |
| `check_environment` | `(observed, declared) -> str or None` | M0's predicate for its own process; returns the observed value. Refusals list extra, forbidden, missing and differing names only. |
| `canonical_path` | `(value, *, allow_absent=False) -> str` | plan section 4.4. The value itself may not be a link. `allow_absent` admits a missing last component. |
| `resolve_link_chain` | `(path, *, category="PATH") -> {state, path, hops}` | component-by-component resolution, as the kernel does it, recording each link |
| `read_os_identity` | `(*, system_path, cryptex_path, check) -> {system_version, cryptex}` | the shapes of section 3 |
| `check_os_label` | `(value) -> bool` | HOST's `labels.os` shape, with the cryptex's `state` (W3-C3); the receipt rule uses it |
| `read_proc_translated`, `read_boot_session_uuid` | `() -> 0 or 1`, `() -> str` | `sysctlbyname` through ctypes and `/usr/lib/libSystem.B.dylib`; an unreadable value refuses (`CHO-PLATFORM`) |
| `read_process_image` | `() -> str` | `proc_pidpath(getpid())` |
| `check_platform` | `(observed, planned)` | MC08, then the planned release and boot |
| `python_inventory`, `python_inventory_digest`, `compare_inventory` | `(venv, framework, *, check)`, `(inventory)`, `(expected, actual) -> [rows]` | section 5 |
| `verify_packages`, `read_lock_pins`, `interpreter_selection` | `(venv, venv_entries, pins, version_directory)`, `(raw)`, `(venv, framework, framework_entries, venv_entries)` | section 5 |
| `macho_magic_kind`, `parse_macho`, `read_macho` | `(head)`, `(data, file_size)`, `(path, *, maximum, private, category, check, expected) -> (binding, summary)` | section 6.1 |
| `check_node_macho`, `check_python_macho` | `(summary)` | sections 6.2 and 6.3 |
| `check_git_binding` | `(git, *, dispatcher="/usr/bin/git", check) -> {path, sha256, size_bytes, mode}` | also refuses a hard link of the dispatcher and the dispatcher's bytes under another name |
| `check_node_source`, `check_runtime`, `check_dependencies`, `check_source` | `(raw, executable)`, `(plan)`, `(plan)`, `(plan, observer_path)` | sections 2 and 7 |
| `source_paths`, `source_inventory`, `git_head` | `(root)` | `SOURCE_TREES` and `SOURCE_FILES` (open question Q9) |
| `validate_plan`, `static_check`, `observe_host` | `(plan_path, plan_sha256, *, host=None)`, and for `observe_host` also `rename=rename_exclusive` | the commands of section 1 |
| `output_paths`, `expected_commands` | `(attempt)`, `(plan)` | the fixed outputs and commands |
| `rename_exclusive` | `(source, destination)` | `renamex_np` with `RENAME_EXCL` = `0x00000004`, bound from the macOS SDK's `<sys/stdio.h>`. A failure raises `OSError`; there is never a fallback. |
| `Host` | class | the real host boundary. A substitute must set `boundary = "mocked"`, and every record then says so. |

## 5. Python inventory

The document is `ontokin.current-host-readback-python-inventory/0.2.0`, `{schema, framework:
{root, entries}, venv: {root, entries}, selection, closure}`. Its digest is the SHA-256 of its
canonical bytes.

1. **Trees.** Both are listed exhaustively, and no link is followed. An entry is
   `{kind: file, sha256, size_bytes, mode}`, `{kind: symlink, target}` or `{kind: directory, mode}`.
   Bytecode files are ordinary entries. A special file refuses, and so does a directory that
   changes while it is listed.
2. **Images.** Every regular file that starts with a Mach-O magic is an image. Fat, 32-bit and
   big-endian images refuse.
3. **Selection.** `<venv>/bin/python` is resolved with every link hop and must end at
   `<framework>/bin/python3.12`. In `pyvenv.cfg`:
   - `include-system-site-packages` is `false`, and `version` is 3.12.x;
   - `home` is a directory whose `python3.12` resolves to the same launcher;
   - `executable`, if present, resolves to it too.

   The process image `<framework>/Resources/Python.app/Contents/MacOS/Python` must be an
   inventoried file.
4. **Closure.** Each image is checked by the Python rules, and its references are resolved by
   section 6.3. A target inside a tree must be an inventoried image. A target outside is bound as
   an external dependency, with its link hops, and processed in turn. The closure repeats until
   every image's set of spellings is stable, at most eight times.
5. **Comparison.** `compare_inventory` returns `{part, path, change}` rows: `added`, `missing`,
   `changed` or `root` for tree entries, external dependencies and images; `added` or `missing`
   for link hops, with the target; `changed` for each selection key and for the schema. M0 refuses
   any row (`PYTHON-INVENTORY`), and also requires identical canonical bytes.
6. **Packages.** Every `*.dist-info` directly in site-packages is read by explicit path: METADATA's
   `Name` and `Version`, and RECORD as CSV. `importlib.metadata` is never used.
   - The normalized names must be exactly the lock's seven pins, at their versions.
   - A RECORD row must name an inventoried file inside the venv. A hashed row must match its
     `sha256=` digest and size. An unhashed row is admitted only for RECORD itself and for `.pyc`
     under `__pycache__`.
   - Every file under site-packages must be owned by exactly one row (`PYTHON-UNOWNED`), so an
     added `.pth` file refuses.

**Measured on this host**, read-only, with the venv as MI leaves it (no packages). Evidence is in
`../OntoKin-local/c271-p33/workers/W3/dev-observations/`.
- **Framework:** 3,478 files, 414 of them bytecode, 5 links, 305 directories, 72,433,430 bytes.
  **Venv:** 5 files, 3 links, 6 directories.
- **Images:** 84. The framework holds 79: 2 `MH_EXECUTE`, 1 `MH_DYLIB` and 76 `MH_BUNDLE`. Five
  external dylibs lie under `<prefix>/Cellar`.
- **Links:** 6 closure hops, for example `<prefix>/opt/openssl@3 -> ../Cellar/openssl@3/<version>`,
  and a selection chain of 4 hops. No `@`-relative reference occurs. The rpaths are `<prefix>/lib`,
  a dependency's own `lib` directory and libmpdec's `@loader_path/../lib`, each resolved as a
  directory.
- **Size and time:** 696,871 canonical bytes; 0.53 s cold and 0.15 to 0.16 s warm. A second
  computation showed no difference.
- **Packages:** verification refuses, as expected before MP: none of the seven is installed.
- **Source inventory of this worktree:** 639 files, 13,033,943 bytes, 0.03 s.

## 6. Mach-O rules as implemented

### 6.1 Parser

- **Magic:** only `cf fa ed fe`, thin 64-bit little-endian. The four fat magics refuse
  (`MACHO-FAT`); 32-bit and big-endian magics refuse (`MACHO-MAGIC`).
- **Header:** `cputype` must be `CPU_TYPE_ARM64` (`0x0100000c`) and `cpusubtype` exactly 0
  (`CPU_SUBTYPE_ARM64_ALL`), or `MACHO-CPU`. `0 < ncmds ≤ 4096`, `0 < sizeofcmds ≤ 4 MiB` and
  `32 + sizeofcmds` within the file.
- **Commands:** each `cmdsize` is at least 8, a multiple of 8 and inside the table, and the sizes
  add up to `sizeofcmds`. The parser checks each known structure's size and keeps its data ranges
  inside the file: `LC_SEGMENT_64` (72 + 80 per section), `LC_SYMTAB`, `LC_DYSYMTAB`, `LC_UUID`,
  `LC_BUILD_VERSION`, `LC_SOURCE_VERSION`, `LC_MAIN`, every linkedit-data command and
  `LC_DYLD_INFO(_ONLY)`. Strings must be terminated inside their command, non-empty and printable
  ASCII. Anything else is `MACHO-MALFORMED`.
- **Unknown commands** are recorded with `name: null`, and both rule sets refuse them.
- **Binding:** `read_macho` hashes the file and parses its bytes, and refuses a change of identity
  during the read.

### 6.2 Node (contract section 7)

- File type `MH_EXECUTE` (`MACHO-FILETYPE`).
- `LC_RPATH`, `LC_DYLD_ENVIRONMENT`, `LC_LOAD_UPWARD_DYLIB` and `LC_REEXPORT_DYLIB` refuse
  (`MACHO-REFUSED-COMMAND`). Any other command outside the closed list of 16 refuses
  (`MACHO-COMMAND`).
- `LC_LOAD_DYLINKER` is `/usr/lib/dyld` (`MACHO-DYLINKER`).
- Each `LC_LOAD_DYLIB` and `LC_LOAD_WEAK_DYLIB` path: an `@` prefix refuses (`MACHO-AT-PATH`).
  Otherwise the path is normalized and absolute (no `.`, `..` or `//`) and starts with `/usr/lib/`
  or `/System/Library/` (`MACHO-DYLIB-PATH`).
- **Structure:** exactly one `LC_LOAD_DYLINKER` and one `LC_MAIN` (`MACHO-STRUCTURE`), and no
  second copy of a single-instance command (`MACHO-DUPLICATE`).

### 6.3 Python (contract section 4)

- File types `MH_EXECUTE`, `MH_DYLIB` and `MH_BUNDLE`; the allow-list is Node's plus `LC_ID_DYLIB`
  and `LC_RPATH`. `LC_DYLD_ENVIRONMENT` and `LC_LOAD_UPWARD_DYLIB` refuse. `LC_REEXPORT_DYLIB` and
  unknown commands are outside the list.
- `LC_LOAD_DYLINKER`, where present, is `/usr/lib/dyld`. An executable has one dylinker and one
  `LC_MAIN`, other files neither, and a dylib one `LC_ID_DYLIB`.
- **References:** `@rpath/`, `@loader_path/` or `@executable_path/` followed by a name; any other
  `@` form refuses (`MACHO-AT-PATH`). Every other path is normalized and absolute
  (`MACHO-DYLIB-PATH`).
- **`LC_RPATH`:** normalized absolute, or `@loader_path` or `@executable_path`, alone or followed by
  `/…` (`MACHO-RPATH`). Every entry is recorded.

**Resolution.** `resolve_link_chain` records each link `{path, target}`, at most 40.
- **System:** a `/usr/lib/…` or `/System/Library/…` reference is recorded as `system` and not
  resolved. It lies in the dyld shared cache, identified by the OS build.
- **Absolute:** resolved, and it must end at a regular file.
- **`@loader_path`:** from the image's canonical directory, and from the directory of each
  spelling by which another image refers to it. All must agree (`MACHO-AT-AMBIGUOUS`).
- **`@executable_path`:** an executable's own directory, or the process image's for any other file.
- **`@rpath`:** the image's own `LC_RPATH` entries in order, each resolved as a directory. The
  first candidate that exists is selected, and it must be a bound file; no candidate refuses
  (`MACHO-AT-UNRESOLVED`).
- **Failures:**
  - a non-system reference that resolves into `/usr/lib/` or `/System/Library/` refuses
    (`MACHO-AT-PATH`);
  - a missing target refuses, weak references included, so dyld's fallback paths never apply
    (`MACHO-AT-UNRESOLVED` for the `@` forms, `MACHO-DEPENDENCY-MISSING` otherwise);
  - a target that is not a thin arm64 Mach-O file refuses (`MACHO-DEPENDENCY-NOT-MACHO`).

## 7. Starts

| Step | Node | Other | Through |
| --- | ---: | ---: | --- |
| M0, static bindings | 0 | 0 | none |
| M0, Git `--version` | 0 | 1 | Darwin supervisor |
| M1, Node `--version` | 1 | 0 | Darwin supervisor |

**Order.** Plan digest, plan shape (MC33), environment (MC07, MC30, MC31), platform (MC08), OS
identity, source inventory and HEAD, launcher and Python inventory (MC32), packages, loaded
modules, runtime with Node's bytes and Mach-O (MC05, MC06), reader tree, Git binding, failure
capture, evidence ancestors and absent attempt. Then the supervisor import, the attempt
directories, Git, and Node last.

**Supervisor import.** `load_darwin_supervisor` runs only after the source inventory has bound
`prototypes/__init__.py`, `prototypes/static_tray_v01/__init__.py`, `supervisor.py` and
`supervisor_darwin_v01.py`. It puts the bound root on `sys.path` for the import only. Each loaded
module must be the bound file without bytecode, and `run_process`'s code must come from it.

**Each start:**
1. intent, then every binding again (zero new starts on a difference, `DRIFT`);
2. `Clock(total_ms=5000)` with the stage ending 3 s after its start, then the final check inside
   that clock: the executable's bytes, the platform and the boot;
3. `run_process(argv, stage, label, clock, stage_end, env, on_started, cancel_after_ms=None)`,
   whose `on_started` publishes `started.json`;
4. the logs and raw receipt are retained, every binding is checked again, then the receipt,
   counts and output predicate are checked, and the inspection and attempt are published.

**Failure.** `failure.json` and the attempt, whose count state is `PROVEN_ZERO`, `OBSERVED_ONE` or
`UNKNOWN`. There is no retry.

**Publication.** Every document is a same-directory temporary file, fsynced, then published with
`renamex_np(RENAME_EXCL)` and a directory fsync. `EEXIST` replaces nothing; `ENOTSUP` has no
fallback. Before HOST and again before the completion marker, the attempt must hold only its own
directories and planned files, so a `.DS_Store` (`TREE-DS-STORE`) or any other entry
(`EVIDENCE-TREE`) refuses.

## 8. Tests

`TMPDIR="$(cd "$TMPDIR" && pwd -P)/" .venv/bin/python -B -m unittest tests.test_current_host_observation_v02 -v`:
109 tests, all passed, in about 3.7 s. They start no Node, ldd, codesign or Git, and never import
or run the Darwin supervisor. Constants pinning real historical bytes (the C199 manifest and C195
archive digests) are patched to synthetic digests where needed.

| Class | Tests | Starts and boundaries |
| --- | ---: | --- |
| `MachOParserTests` | 19 | none. Builder bytes: MC05's Mach-O part, every MC06 refusal, malformed tables and the Python rules. |
| `CanonicalPathTests` | 5 | none. MC20, including the `/var` spelling of the temporary directory. |
| `EnvironmentTests` | 4 | none. The predicate truth table, each of 21 forbidden names with and without the variable (MC07), MC30's M0 side and MC31. |
| `PlatformTests` | 2 | none. MC08 on mocked values; one test reads this host's sysctl values and process image, asserting only their shapes. |
| `OSIdentityTests` | 5 | none. With, without and behind the conventional link of the cryptex copy, the label's `state` (W3-C3), and the refusals. |
| `GitBindingTests` | 5 | none; the fake Git is a shell script that is never executed. `/usr/bin/git`, a link, a non-canonical path, a digest or mode mismatch, and the dispatcher's hard link or bytes. |
| `PythonInventoryTests` | 19 | none. MC32: changed, added and missing files, added bytecode, a changed `pyvenv.cfg`, retargeted link and selection hops, unresolved `@` loads; resolving `@` loads; RECORD, ownership, package-set, lock, selection and launcher checks. |
| `RuntimeTests` | 10 | none. MC05's pin and Mach-O cases, layout, `NODE-SOURCE.json`, a recorded `failed` signature (D-02), the receipt rule's plan, result and archive cases (D-05), W2's confirmed shapes (D-11 to D-13, 22 cases) and the reader tree's own pins. |
| `PlanTests` | 9 | none. Digest before decoding, unresolved fields, MC33, other versions, fixed environment, limits and commands, canonical and separate paths. |
| `ObservationTests` | 18 | mocked supervisor and host, labelled `mocked`; `renamex_np` on temporary files. Complete HOST; the revision fields in all 13 observer documents and in the refusal documents (D-12, D-13); MC30 without the variable; MC10; Git output; a supervisor `Stop`; drift between the starts; an unplanned file in the evidence tree; static mode; fresh attempt; MC07 and MC08 before any start; an OS build change; a retargeted cryptex link; unlabelled substitutes; `ENOTSUP` and `EEXIST` publication. |
| `RenameTests` | 1 | `renamex_np` with `RENAME_EXCL` on temporary files, a real system call |
| `SupervisorImportTests` | 4 | imports synthetic stand-ins from a synthetic root only. Lazy import, a module claiming the bound path with other code, a supervisor outside the inventory, standard-library imports only. |
| `SourceTests` | 5 | none. Inventory, static HEAD, a worktree `.git` file with packed refs, bytecode, links and `.DS_Store`, and the exact reader tree. |
| `CommandLineTests` | 3 | each run starts one Python, five in all: the observer under `-I -S -B` (a missing plan; `python-inventory` twice, the second refused because its output exists; `source-inventory`), and once under `-I -B` without `-S` |

## 9. Findings

- **F1. The cryptex copy's path is not canonical on this host.** Decision D-10 adopts the reading
  below; the independent reviewer is asked to confirm it. `/System/Cryptexes/OS` is a link
  to `../../System/Volumes/Preboot/Cryptexes/OS`. Contract section 7 refuses any other linked
  ancestor in a bound path, so the conventional path cannot be bound as named. The observer
  resolves the conventional path, binds the copy by its canonical path, and records the
  conventional name and the hop beside it; a retargeted link refuses (`OS-CRYPTEX`). If the
  contract means the conventional path itself to be bound, that needs an amendment admitting this
  link. W5's probe reads the OS build file and should take the path from HOST's `os.cryptex.path`.
- **F2. The environment** under an exact clean launch of the venv interpreter holds the declared
  names plus `__CF_USER_TEXT_ENCODING` (its value was not recorded). `__PYVENV_LAUNCHER__` is
  absent: the interpreter removes it. Under `-I -S`, `sys.prefix` equals `sys.base_prefix`, the
  framework, so M0 checks `sys.executable`, the launcher behind it and the process image instead.
- **F3. Universal files.** System executables, the `/usr/bin/git` dispatcher and the developer
  tools' Git implementation are universal files, and the parser refuses them (`MACHO-FAT`). Git is
  bound by its bytes and never parsed, so this changes nothing; it shows the refusal on real bytes.
- **F4. Bytecode.** The framework holds 414 bytecode files, so the frozen inventory stays exact
  only if nothing runs this interpreter without `-B` between MP's freeze and M0. That is MC32's
  purpose; MP and MH operators should know it.
- **F5. Receipt shapes** come from W2's interface note, which W2 confirmed against its code under
  D-11 (W2's section 13). W3 did not read or run W2's code. The rule also binds the retained Node
  archive, which must therefore stay at its planned path until MH.
- **F6. Shared OS reader.** Under D-04 the preparer reads the OS identity through
  `read_os_identity`, so finding F1 shapes its labels too: the cryptex copy appears under its
  canonical path, with `link_path` and `hops`.

## 10. Assumptions

- The Darwin supervisor exposes `run_process`, `Clock` and `Stop` with the original semantics and
  the 14 receipt fields, and writes `<label>.process.json` equal to the record it returns. W1's
  note states the names; the tests do not import the module.
- The official `node` binary is thin arm64 with `cpusubtype` 0, and its load commands lie in the
  closed list. Nothing here observed it; MP and N34-M will.

## 11. Open questions

- **Q1. Universal files.** The contract does not mention them, and the observer refuses them by
  default, in Node and in both Python trees. A file that starts with `ca fe ba be`, such as a Java
  class file, is refused as a universal file too.
- **Q2. Cryptex path:** finding F1.
- **Q3. CPU subtype.** Only `CPU_SUBTYPE_ARM64_ALL` is admitted; `arm64e` and capability bits refuse.
- **Q4. `@rpath`.** dyld also searches the rpaths of the loading chain and skips candidates that
  fail to load. The observer does neither, which is stricter and fails closed.
- **Q5. `MH_OBJECT`.** The contract's Python file types exclude it. Some Python builds install
  `config-3.x-darwin/python.o`; this host has none, but such a tree would refuse.
- **Q6. Git version.** The contract states no expected version, so the plan freezes none: the line
  is checked against a grammar and recorded. An exact expected line would need a value known
  before M0.
- **Q7. Signature check.** Settled by D-02: a `failed` status is recorded in HOST and its label,
  and M0 does not refuse it.
- **Q14. The observation plan's revision.** The plan is an input that the Director writes, not a
  document the observer writes, so it carries no `design_revision`. If plans should name the
  revision they were written for, that is a new closed key.
- **Q15. The receipt's OS label.** M0 checks its shape only. Requiring it to equal the current OS
  would refuse every receipt after an OS update between MP and MH.
- **Q8. Source tree.** M0 reads HEAD's commit from the Git files, but cannot check the tree object
  or the absence of untracked files without a Git read. The provider's bound Git reads must do so
  (MC19). HOST says this in `source.tree_check`.
- **Q9. Source inventory.** `SOURCE_TREES` and `SOURCE_FILES` for 0.2.0 are defined here: the 0.1.0
  sets, plus the macOS lock and the 0.2.0 contract files. W5 should import them, or the Director
  should make the provider's source inventory the same document.
- **Q10. Boot.** P07 section 2 puts the actual boot in the plan, so a reboot needs a new plan and
  review.
- **Q11. Letter case.** `canonical_path` does not normalize letter case on a case-insensitive
  volume. A differently cased plan path refuses only where the strings are compared.
- **Q12. Process image.** The check through `proc_pidpath` is stronger than the contract asks. It
  can be dropped if the Director prefers.
- **Q13. Run kind.** HOST's `run_kind` is `host-observation`, a value of this note, not of the
  contract.

## 12. First follow-up: corrections

Requested by the Director after design revision 4's adoption. Code and note now agree.

| ID | Where | Correction | Basis |
| --- | --- | --- | --- |
| W3-C1 | code | Every observer document carries `contract`, `design_revision: 4` and `amendments: ["P33-AMENDMENT-001"]`, and so do HOST's `labels`. Documents that had no `contract` field (the inspection receipts, attempts, start and failure records, reservation, preflight, completion and the inventory commands' results) gain it beside the two new fields. | D-12, D-13 |
| W3-C2 | code | The receipt rule follows W2's confirmed shapes: the result's closed keys per outcome include `design_revision` and `amendments`; its labels are `{executor, contract, profile, design_revision, amendments, pins, os}` with the pins of its purpose; `pins`, `preparer_source`, `operations`, the readbacks, `publication` and the archive summary with its `executable` are checked as section 3 states. | D-05, D-11 |
| W3-C3 | note | The cryptex label's `state`. The note said a present cryptex label "holds the same three fields". The code, and so HOST, also writes `state: "present"`, and W2 follows the code. The note now says so. | W2's finding F8 |
| W3-C4 | code | `check_os_label(value)` is exported, and the receipt rule checks the receipt's OS label with it. | D-04 |

**Expectations changed because a new field is required:**
- HOST's top-level key set gains `design_revision` and `amendments`.
- The `ALREADY_PRESENT_EXACT` acceptance case: its `before` readback gains `files` and
  `directories`, W2's confirmed readback shape. It is still accepted.
- The synthetic receipts of the fixture take W2's confirmed result shape. Every earlier refusal
  case still refuses with its rule.

No other expectation changed.
