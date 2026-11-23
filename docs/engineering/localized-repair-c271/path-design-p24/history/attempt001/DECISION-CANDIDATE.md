# P24: finite RTLD path representation

Decision `P24-PATH-001`, version `ontokin.c271.rtld-path-decision/1`.
**State: proposed for independent review; not adopted or implemented.**
Author: `/root/path_design`. The Director owns adoption, repository writes and delivery.

## Decision and evidence boundary

Propose one inspection-plan version that handles the three literal RTLD candidates in the retained P23 observation. RTLD means the runtime loader considered by the bound `ldd` script. The extension supplies two missing representations: absence below a missing ancestor, and one exact parent-containing symlink target after its containing directory has been resolved. It does not select libraries or emulate a loader.

The frozen inspector at `527368bd5195c439762b43e2cc836ff9822213f8` cannot represent `/libx32/ld-linux-x32.so.2` when `/libx32` is missing; its absent-row predicate requires an existing immediate parent. `_existing_chain` also rejects the observed `..` link target. These are source-backed plan constraints, not observed H0 runtime failures. The same P23 record shows `/lib/ld-linux.so.2` absent through `/lib -> usr/lib`. Its witness must consequently be `/usr/lib/ld-linux.so.2`; the existing absence-guard parent cannot itself be a symlink. This is closure of the already frozen list, not a new host investigation. [S01–S03]

The proposed path outcomes are:

| Literal candidate, in required order | Physical outcome required by the new profile |
| --- | --- |
| `/lib64/ld-linux-x86-64.so.2` | Regular `/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2`, matching the unchanged P16/P17 loader pin |
| `/lib/ld-linux.so.2` | First missing `/usr/lib/ld-linux.so.2`, nearest existing ancestor `/usr/lib`, no remaining suffix |
| `/libx32/ld-linux-x32.so.2` | First missing `/libx32`, nearest existing ancestor `/`, remaining suffix `ld-linux-x32.so.2` |

These are proposed acceptance conditions, not fresh observations. P23 did not supply a complete canonical-component identity inventory. A later operational plan must collect and independently review it on its own host. No P23 inode or temporary path is reusable as a present-host assertion.

## Version and closed input

The new exact pair is `ontokin.current-host-readback-inspection-plan/0.1.4` with `linux-glibc-declared-python-origin-rpath-libc-plt-static-tls-rtld-paths-v1`. It inherits every `/0.1.3` field, origin proof, dependency-role proof, pin and flag predicate. The resolution object adds exactly `rtld_paths`. Unknown pairs or keys fail. Versions `/0.1.0` through `/0.1.3` retain their exact shapes, ordering, callbacks and outcomes; they cannot select this rule. Do not rewrite a `/0.1.4` plan or its digest as `/0.1.3` internally. [S01, S07–S12]

`SCHEMA.json` is the closed machine-readable contract, not an executable plan or a general JSON-Schema implementation. Its exact additions are:

- `rtld_paths`: `{schema, components, absences}`, with schema `ontokin.current-host-readback-rtld-paths/0.1.0`.
- Each component: `{path, kind, identity, target}`. `identity` is exactly the inspector's seven integers `[st_dev, st_ino, st_mode, st_nlink, st_size, st_mtime_ns, st_ctime_ns]`; Booleans are not integers. File type must agree with `kind`. No identity is supplied by this design.
- Each absence: `{path, nearest_existing_ancestor, first_missing, remaining_suffix}`. The exact two rows are the table above; suffix is an array of single literal components, empty for the i386 candidate and `["ld-linux-x32.so.2"]` for x32.

The sorted component set contains exactly nine paths: `/`, `/lib`, `/lib64`, `/usr`, `/usr/lib`, `/usr/lib64`, `/usr/lib64/ld-linux-x86-64.so.2`, `/usr/lib/x86_64-linux-gnu`, and `/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2`. Five are directories, the final canonical loader is a regular file, and precisely these three are symlinks:

| Symlink entry | Exact raw target |
| --- | --- |
| `/lib` | `usr/lib` |
| `/lib64` | `usr/lib64` |
| `/usr/lib64/ld-linux-x86-64.so.2` | `../lib/x86_64-linux-gnu/ld-linux-x86-64.so.2` |

Every component has a matching existing P07 present guard: same kind, device, inode, permission mode and target. The named `/lib64/ld-linux-x86-64.so.2` additionally has a present guard equal to the physical symlink's identity/target. Both first-missing paths have unchanged P07 absence guards with their physical immediate parents and matching parent device/inode. There are no absence guards for fictitious descendants or symlink parents. Additional ordinary guards remain governed by the inherited full-plan closure; they grant no additional traversal exception.

The existing `inspector_commands.rtld_candidates` row keys do not change. The first row is `{path,state:"file",binding}`. The other two are `{path,state:"absent",parent}`, with the same literal immediate-parent strings `/lib` and `/libx32`. Only `/0.1.4` substitutes the authenticated `absences` witness for the old `parent.is_dir()` predicate. `parent` still must equal the literal path's parent. This does not redefine an old version.

Require the unchanged loader binding `c8438e4fde1934e61c88311633f00949ff645d5c04cdb8671fa3d78164d2f307`, 225,672 bytes, `0o755`, at the canonical path above. It must agree with the candidate binding, `libc_plt.loader`, host and author-runtime file maps, the corresponding unique image row and all existing interpreter-role relations. The named candidate must occur in the exact existing role/alias union. Missing candidates are absent from file/image/role inventories; they remain in the complete RTLD list and absence proof.

The new profile binds the retained script descriptor `/usr/bin/ldd`, SHA-256 `7bcd61a279946cb376d36fd91f4938ab4f4aba48e793c652a9797319d23f8dd3`, 5,356 bytes, `0o755`, with exact direct shebang `#!/bin/bash`. This pins the finite list's source; independent review of all relevant script branches is still required. No approval or completeness flag is added. [S02, S03, S05, S08]

## Component order and confinement

Linux resolves a symlink from its containing directory before it continues with later components. The required x86-64 trace is therefore `/` → `lib64` (link) → `/usr/lib64` → loader-name (link) → `..` from `/usr/lib64` to `/usr` → `lib/x86_64-linux-gnu/ld-linux-x86-64.so.2`. Its result is under `/usr/lib`. Lexically reducing `/lib64/../lib` first would incorrectly choose a route through `/lib`. [W01, W02]

Implement a private finite trace verifier within the existing inspector, restricted to these literal candidates and exact edges. Maintain a resolved-directory descriptor stack and a pending component queue. Expand an admitted raw symlink target before resuming the remaining queue. The sole admitted `..` transition is from the authenticated `/usr/lib64` directory to its authenticated `/usr` parent; open that parent relative to the held directory and compare it with the retained `/usr` descriptor. Never use `normpath`, a lexical prefix test, or `Path.resolve()` as the proof.

Expose only private test seams `_check_rtld_alias_trace` and `_check_rtld_absence_trace`, each limited to its exact literal subjects and edges. The x86-64 alias seam does not consult unrelated `/lib`: a synthetic trap there must not alter its correct `/usr/lib` result. The operational `_check_rtld_paths` aggregate always checks all three candidates and all nine components, so it rejects that trap. A seam positive is not plan admission. Fixture-root mappings or injected observations belong only to the labelled test adapter; no alternate root or filesystem backend enters an operational plan or public API.

The `/` anchor identifies the current process root; it is not permission to visit arbitrary paths. Each next physical component must be a listed edge in the fixed trace and have the prescribed type. Root traversal, another parent step, absolute link targets, extra links, `/proc`/magic-link routes, a symlink at an expected physical directory, and even another alias to the same final inode refuse. External absolute paths retain the old normalized-path rules and cannot contain `..`. Do not change root, mount namespace, cwd, permissions or host files.

The i386 trace expands `/lib -> usr/lib` and checks the missing child relative to the authenticated `/usr/lib`. The x32 trace checks `libx32` relative to authenticated `/`. It stops there: no syscall probes its remaining suffix. The exact unresolved suffix stays in the witness, proving which complete literal candidate is unavailable.

## Observation, absence and finite bounds

Use descriptor-relative, no-follow observations: `os.stat(name, dir_fd=parent_fd, follow_symlinks=False)` and `os.open(name, O_PATH|O_NOFOLLOW|O_CLOEXEC, dir_fd=parent_fd)`, adding `O_DIRECTORY` for an expected directory. Open `/` with the same directory restrictions. Compare the full named-entry identity with `fstat` of the opened descriptor before use. For an admitted symlink, read its own bytes through `os.readlink(b"", dir_fd=link_fd)`, compare the complete exact ASCII target, then repeat `fstat` and the parent-relative named-entry observation. This Linux empty-path read is supported for a symlink descriptor opened with `O_PATH|O_NOFOLLOW`; it avoids rereading a replacement link by name. [W03, W04]

Require these Linux/Python capabilities; unsupported flags, unavailable `dir_fd`/no-follow operations or a failed empty-path read are refusals, never a fallback to unchecked resolution. Directory and file descriptors remain data-only; no library, shell, loader or target starts. Retain at most the nine fixed component descriptors plus one transient parent/reanchor descriptor. Close every owned descriptor once on success, refusal, I/O failure or callback interruption.

An absence is authenticated **only** by `ENOENT` from the exact single missing basename under its already verified physical parent descriptor. The ancestor chain must have succeeded first. Repeat that lookup after rechecking the parent's full identity and its named route from root. A dangling symlink exists as a symlink and therefore cannot be absence. A file in a nonfinal position, `ENOTDIR`, `EACCES`, `EIO`, `ELOOP`, an unavailable root or an error resolving a required link is a refusal, not an empty directory or missing candidate. No inference comes from `exists()`, a caught whole-path `FileNotFoundError`, or a failed attempt to follow a link.

Each verifier invocation performs exactly two full bounded passes, independently reanchored at `/`, and compares every named route, component identity, raw target and absence result with the plan and the other pass. Close the first pass's descriptors before opening the second root. Retained descriptors surviving a rename are insufficient. The second pass is a check, not a retry that can replace failed evidence. On any difference, stop.

Bounds are fixed: nine present components, two absence witnesses, three ordered candidates; at most two symlink expansions and sixteen component transitions per candidate per pass; ten live verifier descriptors; 4,096 ASCII bytes and 128 components for an input or intermediate spelling before reduction; nonempty single components with no whitespace, NUL, backslash or dollar token. The exact target allowlist is stricter than these ceilings. Track visited symlink entry identities and reject repetition; also refuse an OS loop error. No recursive retry or caller-supplied limit is available. Call the existing zero-argument deadline callback before each observation and at final acceptance. All work consumes the existing 60-second static allowance or the existing command clock; no budget increases. Old routes receive no new calls.

## Integration points

Only a later, separately selected implementation may change `current_host_inspection_v01.py` and add one new focused test adapter. Required integration is explicit:

| Existing site | Required `/0.1.4` behavior |
| --- | --- |
| `_plan_shape`, `_select_origin_profile`, `_uses_origin_profile`, `_uses_libc_profile` | Select the exact new pair and closed addition; include all inherited origin/libc gates. Keep old branches intact. |
| `_prepare_libc_plt_policy`, `_read_plan_elf_metadata` | Accept the new pair explicitly; retain actual plan schema in the immutable policy and dispatch the selected libc to the unchanged static-TLS primitive. Do not widen an old selector or raw flag mask. |
| `_check_author_runtime` (both calls), `_check_host_static` | Run the new finite proof before any use of the exceptional alias in `_check_alias_files`/`_alias`. For that one alias, use the verified canonical result and named-link projection; all other aliases retain the old route. Reproduce the full proof on each call, not a cached success flag. |
| `_check_resolution` | Run the finite proof; verify exact candidate row shapes, states, parents and file/absence relations. Then require complete ordered equality with the actual unique literal `RTLDLIST`; retain all image, needed-edge, interpreter, search and script predicates. Use the verified result for the exceptional candidate in the present-loader and `all_roots` checks. |
| `_required_paths`, `_check_plan_guards` | Include all nine components, the named x86-64 alias and both first-missing witnesses. After the finite proof, remove only the four names listed in `SCHEMA.json` from the old chain walk. They remain fully checked by the new proof. Keep `_existing_chain` unchanged for every other path. |
| `_validate` | The first new proof occurs before the first author-runtime alias use. Complete the new proof and inherited origin/libc/resolution/guard proof before `_load_helpers`, Git reads or `STATIC_READY`; repeat at final validation. |
| `_input_snapshot` | Keep the exact fourteen names in `SCHEMA.json`'s `legacy_snapshot_exclusions` in the private RTLD snapshot defined below, not in the generic `FileNotFoundError -> absent` snapshot route. That closed set covers the nine components, named x86-64 alias, two literal absent candidates and two physical first-missing witnesses. Preserve every other input snapshot. |
| `_recheck` | Re-derive the finite proof before author/runtime alias use, repeat full resolution/guards, and compare with the frozen RTLD snapshot. Preserve the existing outer `CHI-DRIFT` wrapper and underlying failure. |
| `_launch_check` | After the ordinary snapshot/guard checks, re-run the finite two-pass identity/absence proof within the existing command clock and compare it with the snapshot, before entering the supervisor launch boundary. Do not use `exists()/is_symlink()` as the exceptional absence proof. |
| `_host`, `_validate_host_projection` | Keep P06 output fields and set relations exact. Project the named loader alias as `{resolved_path: canonical_loader, symlink:true, link_target: exact_raw_target}`. No component, absence, approval or policy key enters HOST. |

The private metadata slot `rtld_path_snapshot` has exactly `{components, results}`. `components` is the verified nine-row list. `results` is the three ordered records: file `{path,state:"file",resolved_path,identity}` or absence `{path,state:"absent",nearest_existing_ancestor,first_missing,remaining_suffix}`. It is derived from successful observations and compared anew; it is not caller authority or a new public artifact. Snapshot construction must itself obtain a fresh finite proof, after preceding validation. No witness survives into another attempt as a cached acceptance.

Literal-list error ordering is fixed: reject duplicate candidate paths with the inherited `CHI-INSPECTOR` check; then compare the full path sequence with the script's single literal list, preserving `CHI-UNSUPPORTED / Inspector RTLDLIST is not the exact reviewed literal list` for omission, addition or order differences. Only afterward accept the new profile's required three states and witness relations. This ordering is new-profile-only; old ordering remains exact.

## Failure and race boundary

New closed-shape/pair errors use `CHI-PLAN`; candidate state/parent/binding-map mismatch uses `CHI-INSPECTOR`; component type/identity, exact absence, capability and I/O faults use `CHI-PATH`; unapproved traversal, cycles and finite-bound excess use `CHI-UNSUPPORTED`. Exact rule IDs and reasons are in `SCHEMA.json`. OS exceptions retain their actual errno and cause. A primitive callback exception propagates as the same object after successful descriptor cleanup; enclosing functions retain their existing timeout/cause handling. A cleanup failure blocks success and retains both primary and cleanup evidence when both occur. No path refusal becomes `supervisor.Stop`.

Before launch these failures prove zero target starts only when the existing launch boundary was never entered. After any actual process outcome, the full recheck still runs; drift overrides success while preserving the actual process receipt/start count. Preserve unknown starts and finalization faults rather than manufacturing zero. Existing sidecars already carry the plan descriptor and failure details; their closed public shapes do not change.

This detects observed identity/namespace changes. It does not make validation and kernel execution atomic. Changes between observations, change-and-restore races, hostile privileged mounts, kernel integrity and later executable loading remain P07 trust limits. The tool neither freezes the filesystem nor asserts immunity to time-of-check/time-of-use races. Final launch and postflight checks reduce the unchecked interval; they do not eliminate it. [S05]

## Preservation, choice and next gate

Preserve all old schemas, parser defaults, historical errors/oracles, exact Python/Node/libc/loader/dependency pins, fixed `ldd NODE` command, environment, P06 consumers, source/operation/deadline limits and original seven test bodies. Preserve the P11 nonselection proof and P13 external source-completeness boundary; no runtime approval field or fake N57 result is introduced. The future source is necessarily new: freeze its actual commit/inventory and use separate operational plans; never rewrite `527368bd...` source receipts. Historical P15/P23 refusals and unrun H0/H1/R03–R05 remain unchanged.

The concrete alternative is to retain all existing refusals and perform the existing `/0.1.3` qualification on a **different, already conforming Linux/glibc host**: same exact selected Python, Node, libc/loader and dependencies; an independently bound `ldd` script/list; every required absent candidate's immediate parent an actual guarded directory; all needed alias targets free of parent traversal; and full fresh H0/H1/routine evidence under the same deadlines. Identify that host and its immutable input/layout evidence before selecting work. Do not manufacture `/libx32`, rewrite `ldd` or system links, or substitute a direct-loader command to create conformance. No such host is established by the retained evidence. This route is therefore concrete but presently unavailable; it risks repeating host search and preparation without resolving C271.

The proposed extension is preferred because it describes the already identified finite topology without changing hosts, pins, commands or loader-selection semantics. A generalized path/loader framework or alternate command protocol would exceed this need. An operational host that fails this exact topology must stop; P24 authorizes no search for further exceptions.

Independent review must accept these exact bytes and all 52 controls frozen by `/root/path_review`; the matrix hash is bound in `SCHEMA.json`. The reviewer supplies the case-by-case crosswalk. Those controls remain unexecuted here. Future implementation must consume them unchanged, preserve every inherited applicable control, distinguish primitive/mock results from full-plan admission, and obtain an independent implementation/adapter review. This design is not an operational plan, H0 acceptance, H1 authorization or parent completion. Stop at separate design adoption or the first concrete design blocker. No implementation, host probe/reconstruction/mutation, product import/test, H0/H1 or full routine is part of this phase.

Sources and exact local input hashes are in [SOURCE-BINDINGS.json](SOURCE-BINDINGS.json). The normative field and path lists are in [SCHEMA.json](SCHEMA.json).
