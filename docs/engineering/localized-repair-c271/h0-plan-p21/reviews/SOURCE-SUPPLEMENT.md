# C271 P21 source supplement for H0 authoring

This is a **nonexecutable field and import reference**, not an operational plan or permission to run a script. It is derived from the exact current inspection module (SHA-256 `e14542e45deb200bb97f2a591c94bdd19916a1d33dcb3ce9f631816b98e0c206`) and its selected helper source. The companion `H0-SCHEMA-AND-IMPORTS.json` lists every inspected closed object, fixed limits, source inventory members and import edges.

## Operational shape

Use only plan `ontokin.current-host-readback-inspection-plan/0.1.3` with resolution profile `linux-glibc-declared-python-origin-rpath-libc-plt-static-tls-v1`. Its top-level keys remain exactly:

`schema, contract, source, author, runtime, dependencies, host_static, environment, commands, evidence, limits`.

All ordinary descriptors have `path, sha256, size_bytes, mode`; map file bindings omit only `path`. Aliases have `resolved_path, symlink, link_target`. JSON must be canonical sorted ASCII without whitespace separators, duplicate keys or nonfinite numbers. No expected-digest or approval key is added to the operational plan.

| Object | Required keys |
| --- | --- |
| source | root, commit, tree, inventory |
| author | entry_point, source_descriptor, python_descriptor, python_version, runtime_inventory, metadata_inventory, git_descriptor, source_commands |
| runtime | executable, version, candidate, source_archive, install_receipt |
| dependencies | root, inventory, install_receipt |
| host_static | platform, files, aliases, roles, resolution, path_guards |
| resolution | profile, images, needed_edges, loader_inputs, search_directories, inspector_commands, ignored_kernel_rows, rationale, origin_rpath, libc_plt |
| evidence | parent, attempt_root, ancestor_identities, outputs, outer_capture |

`origin_rpath` retains P11's exact ten fields. `libc_plt` has exactly `schema, subject, loader` and keeps schema `ontokin.current-host-readback-libc-plt/0.1.0`. No new TLS, flags, completeness or review-status field exists. The canonical subject Python must remain the pinned direct-main image. A venv alias can select that image, but the origin is its resolved canonical parent, not the venv's bin directory.

The author runtime sidecar is `schema, executable, interpreter, files, aliases, startup_files, extension_files, loader_inputs, environment`. The metadata sidecar is `schema, lock, packages`; each of seven rows has `name, version, distribution_root, metadata_files`. Its complete metadata root must include exactly its actual necessary subdirectories, and may contain no executable `.py/.pyc/.pth/.so` file. Bind explicit metadata paths; do not add the venv site directory to the author process.

The source inventory is `schema, files` with schema `ontokin.current-host-readback-source/0.1.0`. The exact selected source trees/explicit files/optional initializers are in the JSON reference. The P06 schema is separately pinned at `docs/engineering/localized-repair-c271/current-host-p06/SCHEMA.json`, 57,550 bytes, SHA-256 `41d90fed8fa5ff072f1ae620071e3bb54aebc81e02768260fb3c63cfd78591fa`, mode `0o644`.

## Installation evidence has a current-source equality requirement

The installation-index sidecar has `schema, plan, report`, with schema `ontokin.current-host-readback-inspection-installation/0.1.0`. The actual installation plan's `source` object must equal the operational plan's source object **including the inventory descriptor**, not just matching product code. It must carry the correct purpose (`selected-node` or `retained-dependencies`), destination and report path. A successful report is either `INSTALLED_EXACT` or `ALREADY_PRESENT_EXACT`, with `node/ldd/checkers` counts all zero and complete tree equality.

Consequently, old preparation receipts cannot be rewritten or presented as current-source receipts. If exact installed inputs still exist, a newly reviewed unchanged-preparer verification may produce its own current evidence; that is a concrete separately selected operation, not authority supplied by this supplement. [`_check_installation`, `_check_runtime_dependencies`]

## Exact project import graph

The inspection entry imports only the standard library at module import. Its direct imports are listed in the JSON reference. Project helpers are imported by `_load_helpers` only after source authentication and the complete early origin/host/resolution/path proof.

| Importing module | Immediate project imports |
| --- | --- |
| inspection entry via _load_helpers | current_host_readback_v01, supervisor, tools.check_local, tools.prepare_current_host_readback |
| current_host_readback_v01 | supervisor, format_check |
| format_check | canonical, lock, supervisor |
| canonical | errors |
| lock | canonical, errors, supervisor |
| tools.check_local | tools.storage_identity |
| tools.prepare_current_host_readback | current_host_readback_v01 |

All static-tray names are under `repo/prototypes/static_tray_v01/`; tools paths are under `repo/tools/`. The two `prototypes` package initializers contain docstrings only. The observed repository has no `tools/__init__.py`, so do not invent that file as an executed input. `format_check` has function-local imports of store/transaction and lock has function-local imports of sources, but they are not part of this top-level helper-import route. Calling those unrelated functions is outside the H0 authoring path.

This graph does not import any of the seven installed third-party verification distributions. P06's schema compatibility uses the inspection module's own finite `_schema_check` and `json.loads`, not jsonschema. In contrast, **ctypes is an actual top-level helper dependency** in supervisor and preparer. Its native/bootstrap closure cannot be omitted merely because no Node or package trial runs. The later `ctypes.CDLL(None)` calls in `run_process` and `rename_without_replacement` are function bodies, not permission to invoke them now.

## What cannot be inferred from source names

Exact loaded standard-library and extension paths remain unobserved in this review. The recorded Python prefix does not prove which modules are built in, frozen, file backed or loaded from cached bytecode. The validator checks every loaded module's resolved `__file__` and every existing `__cached__` path after helper import against the bound source/runtime inventories. A list of import names therefore cannot serve as the finished runtime manifest.

The next bounded observation should preserve this distinction. It can collect raw current interpreter/module/native-file identities under a frozen plan, but cannot call a partial policy or bypass early proof and label that operational admission. Any helper or native import proposed by the collector must be declared explicitly and reviewed. The actual finite ELF roots are Node, Python, Git, the inspector interpreter and possible commands, required author extensions, present RTLD candidates and their transitive dependencies. Unused wheel images do not enter that closure by filename alone.

## Fixed future commands and evidence

The plan contains exactly two future H1 commands: Node `--version`, then `/usr/bin/ldd NODE`, each with one expected direct start, its prescribed label and fresh stage directory. Its timeout is 5,000 ms total: 3,000 active plus 2,000 cleanup. These commands remain unexecuted in P21.

The exact author/child environment has only PATH=/usr/bin:/bin, LANG=C.UTF-8, LC_ALL=C.UTF-8, TZ=UTC and UV_THREADPOOL_SIZE=2. The five source Git reads have the additional exact Git suppression variables created by `source_commands`; their argv and 5,000-ms bounds are source-defined. An ordinary .git directory is required by `_git_state`; a linked-worktree gitfile is not accepted by this implementation.

The attempt root is a direct absent child of an existing external evidence parent. `output_paths` defines all filenames; the JSON reference preserves their closed shape. Outer capture authority and its already-open bounded log-prefix descriptors exist before validation and cannot live in the future attempt root. Static validation must leave the H1 attempt root absent. Any public static invocation needs its own independent exact-plan review and supplied digest.

No interpreter, product, package, Node, ldd, direct loader or installation was invoked to produce this supplement.
