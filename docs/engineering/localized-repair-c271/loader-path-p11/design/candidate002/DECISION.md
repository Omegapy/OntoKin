# C271 P11 — one nonselecting Python RPATH

Decision identifier: `ontokin.c271.python-origin-rpath-decision/1` (`P11-LP-001`).
State: proposal for independent review. This is a design/control freeze, not an implementation, executable inspection plan, host qualification or H0 acceptance.

Author: `/root/loader_design`, assigned by Director `c271-p11-2ad494d5da19`. Source baseline supplied by the Director: branch `work/c271-missing-import-digest-control`, commit `e0119f376441fee0fc3956852ac63110ab141011`; observed main `e1a48f7d0635e9aa4f4b6d6a586e7305eb81999d`. Substantive authoring began only after the Director confirmed the early ZIP save and exact downloaded-byte readback. The external early receipt is `session_evidence/EARLY-RECOVERY-RECEIPT.json`.

## 1. Decision and remaining prerequisite

Propose conditional support for **one exact `DT_RPATH` string, `$ORIGIN/../lib`, in the already selected, directly invoked author-Python executable**, under a distinct inspection-plan version and closure profile. The expanded search path must be proved **nonselecting**: none of its possible loader search directories may contain a candidate with any dependency name in the complete declared ELF closure. A candidate of any filesystem kind causes refusal. This deliberately excludes cases where this RPATH supplies a library or changes the chosen dependency.

The profile preserves the current independently reviewed resolution map. It does not implement a general dynamic loader or select another Python. The exact selected image remains SHA-256 `fa67443527ed9647f760d807e2a38f26340757123e643c4639cf273ed15d5ea7`, 30,894,944 bytes, operational mode `0o755`. An inert evidence copy's pathname and nonexecutable mode are not its execution origin.

The retained P09 record identifies the selected named alias as `.../python/bin/python3` and the resolved file as `.../python/bin/python3.12`. P10's independent raw-string observation identifies the RPATH and six direct needed names: `libpthread.so.0`, `libdl.so.2`, `libutil.so.1`, `libm.so.6`, `librt.so.1`, `libc.so.6`. It does not contain a complete Python/extension closure or the sibling `lib` directory inventory. Therefore neither satisfaction nor incompatibility with the proposed nonselecting condition can be established from retained evidence. In particular, no inference that the real `lib` directory is empty or harmless is permitted. [L08–L10]

If a future exact inventory finds `libpython`, another required library, a relevant hwcaps/TLS candidate, an unexplained search alternative, or insufficient source evidence, this profile refuses. A different finite loader decision would then be required. **P11 does not resolve or accept H0-PYTHON-RPATH-TOKEN-001.** It supplies a reviewable, bounded possible implementation prerequisite.

## 2. Source-backed semantic boundary

`$ORIGIN` denotes the directory associated with the object containing the token. The Linux glibc executable-origin implementation inspected in the version-fixed glibc 2.36-8 source reads `/proc/self/exe` for an ordinary directly executed main program. Its fallback origin environment is excluded here. This source is evidence for the rule, not proof that an eventual host uses that exact build. [W01]

glibc's token recognizer supports both braced and unbraced names. Its search code distinguishes inherited RPATH from a requester's RUNPATH. The latter does not grant the former's transitive search behavior. [W02] Linux man-pages documents the corresponding search stages: RPATH when RUNPATH is absent, environment, direct-dependency RUNPATH, cache and defaults; hardware directories can add candidates. [W03]

An upstream March 2025 **patch discussion** explains why explicit loader invocation and `ldd` historically used different origin handling from direct execution. It is not evidence that a fix is deployed. The proposed profile excludes those token-bearing invocation roles and all token-bearing shared objects, avoiding that unresolved generalization. [W04, W05]

These semantics explain why simply deleting the dollar-token guard is invalid. `_check_resolution` currently compares the returned paths directly with absolute search-directory names. It would neither derive an origin nor distinguish the raw token from an absolute directory. `_check_author_runtime` also calls the parser earlier and on rechecks. Both sites must participate in the same reviewed plan branch. [L01]

## 3. Version selection and closed data contracts

Keep the existing `ontokin.current-host-readback-inspection-plan/0.1.0`, `linux-glibc-declared-closure-v1` profile, public `read_elf_metadata` signature/default behavior, result shape and refusal behavior unchanged. An old plan cannot select the new rule, even by adding a new field. Unknown combinations refuse.

The proposed new plan schema is `ontokin.current-host-readback-inspection-plan/0.1.1`. Its top-level keys and P05 contract identifier stay as they are. Its resolution profile is exactly `linux-glibc-declared-python-origin-rpath-v1`. All current resolution keys remain required; exactly one new key, `origin_rpath`, is required in that version. The two versions must be matched as a pair. There is no boolean `allow_tokens`, ambient setting, guessed default or CLI bypass. The fixed `shared_libraries` command's `stdout_predicate` remains literally `linux-glibc-declared-closure-v1`; it describes the unchanged observed-output grammar, not the newly versioned input interpretation.

`origin_rpath` is a closed object with these required fields:

| Field | Exact meaning |
| --- | --- |
| `schema` | `ontokin.current-host-readback-python-origin-rpath/0.1.0`. |
| `subject` | Ordinary descriptor of the selected Python; must equal `author.python_descriptor`, the author runtime executable descriptor and the resolved Python role binding. Exact selected hash/size/mode above. |
| `invocation` | Literal `linux-direct-main`; accepted only with the kernel witness below. |
| `raw_rpath` | Exactly `["$ORIGIN/../lib"]`; the selected image's actual raw metadata must agree. |
| `origin` | Normalized absolute parent of the canonical subject file. |
| `expanded_rpath` | Exactly one normalized absolute path, obtained by the guarded rule in section 4. |
| `kernel_origin` | Closed `{exe_path, at_secure}`; `exe_path` equals the subject path and `at_secure` is integer zero, not a Boolean. This is an expected witness; actual reads must agree. |
| `variant_review` | Descriptor of the independently supplied variant inventory below. |
| `variants` | Exact finite present/absent inventory for every reviewed loader suffix applied to the expanded path. |
| `needed_names` | Sorted, unique exact union of every image's `DT_NEEDED` strings in `resolution.images`; no omissions or additions. |

The separate variant document has exactly `schema, loader, source_review, suffixes`. Schema is `ontokin.current-host-readback-origin-variants/0.1.0`. `loader` is the descriptor of the resolved Python ELF interpreter, already bound in host files/images. `source_review` is the same descriptor as the existing `resolution.rationale`, so the exact independently reviewed rationale remains attached. `suffixes` is the complete finite union of possible search suffixes for that exact loader/platform, including the empty suffix for the base directory. Strings are sorted, unique relative POSIX paths, with no empty components, `.`, `..`, `$`, NUL or whitespace; the sole empty string denotes the base.

Each `variants` row is either `{suffix, path, state:"directory"}` or `{suffix, path, state:"absent", absent_at}`. `path` must be exactly the base expansion plus that suffix. A present row references an exact existing `search_directories` row. An absent row references the first missing path component in the existing absence guards: `absent_at` equals or is an ancestor of `path`, has an existing guarded parent and remains absent. The base row must be a present directory. A directory cannot be silently treated as absent. This reuses P07's guard format without weakening its immediate-parent requirement.

The variant source review must explain the actual loader's compiled/default/hardware/TLS alternatives and why its suffix union is complete. It binds the loader bytes and source/version or inspected implementation evidence. A libc version string or these generic W01–W05 references alone is insufficient. If completeness cannot be justified, the new profile is unsupported. The tool checks the exact reviewed inventory and facts; it does not infer loader implementation from an assertion in JSON.

The external expected plan digest authenticates all fields and referenced descriptors. No field in these objects constitutes approval. A changed variant inventory, rationale, origin, image, closure or output path needs a new separately reviewed plan and fresh attempt. Existing P06 HOST, inspection, manifest, provider, JavaScript consumer and success/failure sidecar schemas remain unchanged. Origin inputs remain in the externally bound inspection plan; they are not projected as new HOST keys. [L01–L06]

## 4. Origin identity, aliases and guarded normalization

Only the canonical, normalized absolute selected Python file can be the token-bearing subject. It must be a regular x86-64 ELF64 file with one link, mode `0o755`, the exact selected bytes, and no symlink in its own path or any ancestor. Its role is the author Python, never Node, Git, shell, loader, `ldd` target or extension. No other token-bearing image is admitted. These are additional restrictions on the new profile; historical literal-path behavior, including its admitted AArch64 literal inputs, is retained.

The future tool must read `/proc/self/exe` as a bounded kernel pathname and verify that it equals the canonical selected path; `stat` through that pseudo-link must match the selected regular file's device/inode/identity. Missing, inaccessible, relative, bracketed, overlong, renamed/deleted (` (deleted)`) or different paths refuse. No use of cwd, argv[0], `AT_EXECFN`, an evidence-copy directory, another alias's parent, or `LD_ORIGIN_PATH` is allowed. Procfs/kernel identity remains the explicit P07 trust boundary. [W01, W04, W06]

The current process must also have an unambiguous `AT_SECURE=0` witness. A bounded native ELF64-little-endian `/proc/self/auxv` reader may inspect at most 256 type/value pairs, require a complete `AT_NULL` terminator and exactly one `AT_SECURE` entry, and reject nonzero/missing/duplicate/malformed entries. The numeric ABI values are `AT_NULL=0`, `AT_SECURE=23`. No ctypes/native library import or child command is needed. The plan records only the selected stable fields; auxiliary pointers/addresses are not serialized into approvals. [W07, W08]

Do not impose this pseudo-file read on the old profile. For the new branch, the same current-process witnesses and file identity must be rechecked at every existing complete `_recheck`. They cannot establish the history of an earlier process; the plan's independently reviewed direct launcher and unchanged boot/path guards remain required.

Expansion is deliberately a single guarded operation:

1. Retain the exact raw token string from the ELF. Verify the subject/context and all directory guards first.
2. Let `origin` be the subject's immediate parent. The proposed pre-normalization path is exactly `origin + "/../lib"`; it must fit the existing path-length/component bounds before reduction.
3. Require `origin`, its parent and the resulting sibling `lib` directory to be actual guarded nonsymlink directories. The origin cannot be `/`. Their full ancestor chains must agree with the already bound path identities.
4. Remove exactly the known final origin-directory component and append `lib`. No generic `normpath`, `realpath` fallback, repeated parent traversal, escape from a declared parent or user-input cleanup is authorized. Compare the literal derived result with the plan's one `expanded_rpath` element.
5. Use that result only for search-directory membership and nonselecting evidence. The returned ELF metadata still contains the raw `rpath: ["$ORIGIN/../lib"]` and `runpath: []`.

Collapsing `bin/..` across an unbound symlink would change filesystem meaning. Refuse the symlink instead. Ordinary bound dependency-file aliases may remain admitted under P07, but they never supply the Python origin. A matching candidate alias under the added search path still refuses under section 5, including a broken symlink or an alias to an already selected library.

## 5. Exact nonselecting proof and search semantics

After validating actual raw metadata for every declared image, compute `N`, the unique union of all its `needed` names. This deliberately covers more than Python's immediate edges: all author extensions, transitive libraries, other roots and every declared image contribute. Require the plan's `needed_names` to equal sorted `N`. Any `$` in a needed name or SONAME anywhere in this new profile is unsupported; no token expansion in those fields is authorized. Existing slash/whitespace/duplicate and transitive-closure checks still apply.

For every present variant directory, verify its entire exact entry inventory, identity and guards. For every `n` in `N`, require **no entry named exactly `n`**. It does not matter whether an entry is executable, a different ELF class, directory, symlink, broken symlink, the same inode as an admitted library or apparently unreadable. Do not emulate a loader's fallback after encountering it. Refuse the profile. For absent variants, verify the first absent ancestor and its actual guarded parent. A match or changed absence is a `CHI-LOADER` refusal.

Existing `glibc-hwcaps` descendant inventory checks remain. The variant review additionally covers legacy hardware and TLS suffixes where relevant. Presence of any relevant directory omitted from the reviewed inventory, or inability to justify the complete suffix set, refuses. The tool compares the supplied variant rows against the separately bound suffix list; **completeness of that source-backed list remains an independent-review obligation**, as it already is for P07's finite loader map. Portable controls do not claim to prove an actual loader's compiled suffix list.

RPATH can affect a descendant lookup; RUNPATH has a different scope and can suppress an ancestor RPATH search for a requester. This profile does not flatten or interchange them. Instead it proves the added RPATH cannot supply any declared needed name in any possible covered search alternative. Hence whether a particular lookup visits the added directory cannot change the declared selected file. A competing candidate makes ordering relevant and is outside this profile. Existing literal RPATH/RUNPATH on other images still follow the unchanged P07 independently reviewed finite resolution. No new search precedence or cache-selection algorithm is introduced. [W02, W03]

Keep the fixed clean environment, empty/absent `/etc/ld.so.preload`, exact opaque-cache review, all configuration/include guards, Node/inspector/Git/interpreter roles, complete needed edges, interpreter closure, architecture matching, loaded Python module inventory and strict observed-ldd map unchanged. Unreviewed name-based dynamic loading outside that finite admitted inventory remains unsupported under P07; nonselecting DT_NEEDED evidence is not proof about arbitrary future `dlopen` behavior.

Recompute the same union and absence checks on every complete pre/postflight recheck. Inventory drift must surface through the current outer `CHI-DRIFT` wrapper with the underlying cause retained. The plan, variant review and rationale descriptors participate in the immutable input snapshot. A future implementation must not cache a successful expansion or absence verdict across rechecks.

## 6. Metadata, flags and finite limits

Keep the public parser's existing raw metadata keys. The current standalone parser and old profile continue refusing `$ORIGIN/../lib` with `CHI-UNSUPPORTED / Unreviewed loader token expansion`. Introduce only a private plan-selected parser path that permits this one raw string for this subject; it yields raw metadata, not expanded paths. A private rule helper is not a host validator. Positive synthetic helper controls must be labelled as such.

The new subject must have exactly one RPATH entry equal to the token, no RUNPATH, and no second colon-separated item. `${ORIGIN}`, `$ORIGIN/lib`, repeated `$ORIGIN`, `$LIB`, `$PLATFORM`, unknown dollars, empty entries, relative literals, whitespace, escaping, arbitrary `..` and mixed RPATH/RUNPATH all refuse in the new subject rule. This intentionally supports less than glibc's token language. Other images remain on the current literal-only reader.

Do not admit `DF_ORIGIN` or `DF_1_ORIGIN` merely because the spelling contains ORIGIN. Preserve the current dynamic-tag allowlist and masks: `DT_FLAGS` permits only bit `0x8`; `DT_FLAGS_1` permits only `0x1 | 0x08000000`. Duplicate flags, audit/filter/auxiliary/unknown loader features, string/parser errors and all existing ELF mapping guards remain refusals. The selected raw P10 record contains `DT_FLAGS_1=1`; no extra flag is required by this proposal. [L01, L10]

Preserve existing ELF file/header/segment/string-table/string/needed bounds, the P10 interval-mapping proof, descriptor closure, short-read/identity checks and callback propagation. New ceilings are: one token-bearing subject; 4 MiB variant document; 4,096 unique needed names; 128 suffixes; at most 32,768 `(present directory, needed name)` checks; 4,096 bytes and 128 path components for the subject, origin, pre-normalization and derived paths; 256 auxiliary-vector pairs. Check callbacks during every new bounded scan/read and before final acceptance. Unsupported size refuses; never extend the unchanged 60,000-ms static allowance, 30,000-ms publication allowance, command/cleanup limits or source execution ceilings of 100,000 operations/30,000 ms.

## 7. Caller order and exact future implementation surface

Only a later independently selected phase may edit the inspection module and add a distinct focused test file. `FUTURE-SURFACE.json` records precise symbols and preserved paths. No production or test file is changed in P11.

`_plan_shape` selects only a supported exact schema/profile pair and the new closed object shape. `_validate` already authenticates the external plan digest before that selection. A private preparation helper derives a subject-only immutable policy after checking the source/plan binding and context. Both `_check_author_runtime` calls and `_check_resolution` must use that same plan-dependent admission. A caller-provided context flag is never proof of admission.

For the **new profile only**, the first author-runtime read is parsing/binding only. Before `_load_helpers`, run the helper-independent `_check_host_static`, `_check_author_host_bindings` and complete `_check_resolution`, including the origin/variant/name-union/nonselecting proof. Those functions use only the already admitted standard-library reader operations. Thus merely permitting a raw token cannot authorize new project/helper imports, source Git reads, preparation commands or `STATIC_READY`. Then retain the normal helper import, loaded-module check, metadata/dependency/installation checks and final host/resolution/guard validation before returning a validated plan. All repeated checks consume the same unchanged static allowance. The old profile's ordering is unchanged. Existing standard-library bootstrap imports and the already running Python remain P07's declared bootstrap trust boundary.

`_recheck` must repeat the full proof before any later effect that depends on it. A parsed raw Python metadata object is never cached as evidence that the complete plan passed. Future source review and focused control adapters must verify that a competing candidate or invalid origin refuses before `_load_helpers` on initial new-profile validation and before source Git/command launch on all routes.

The implementation must keep the public default parser and old profile route intact. It may share the existing internal byte parser, but may not expose an unchecked generic token mode through the CLI, global state or environment. New internal helpers, pseudo-file readers and path-rule code stay in `current_host_inspection_v01.py`; no new production wrapper/installer or general loader helper is proposed.

`_required_paths`, `_input_snapshot` and corresponding rechecks must include origin/expanded directories, every present or absent variant, every `absent_at` witness, the variant document and its source-review descriptor. The existing final `_launch_check` must retain its file/directory/absence checks and repeat the small kernel-origin witness check within the existing command clock. Keep kernel pseudo-files out of the ordinary regular-file snapshot; any retained origin witness belongs only in private validated-plan metadata. The full directory/name proof occurs at the existing preceding `_recheck`, and final directory identity checks detect intervening observed changes without extending the command allowance. Existing successful HOST projection and strict P06 schema checks must remain byte-for-byte in meaning. Additional fixed output fields are not needed: sidecars already bind the plan descriptor. Existing old fixtures and expected failures must not be updated to make the opt-in pass.

## 8. Controls, source gaps and acceptance

`CONTROL-CONTRACT.md`, `EXPECTATIONS.json`, `CONSTRUCTION.json` and `FIXTURE-MANIFEST.json` freeze exact portable synthetic ELF bytes and logical filesystem/kernel/plan contexts. Expected outcomes were authored from this decision and the inspected legacy source, without importing or calling production code. Static verification proves fixture integrity/declared layout and preservation only. It is not a passing implementation result.

The synthetic positive rule inputs are not the selected Python binary and cannot pass its operational hash gate. They exercise a future internal rule seam only. Full-plan binding controls explicitly preserve that distinction. The real selected-image regression remains the retained independent raw observation plus P10 result; P11 does not rerun either parser or target. The complete real operational input set is unavailable, and no positive H0 expectation is frozen.

Independent review must accept this exact proposal and controls, resolve mandatory findings and record the frozen manifest hash. Future implementation must then preserve all legacy checks, consume the frozen cases without modifying their oracle, and obtain a separate implementation review. H0 must subsequently reconstruct and review the complete actual source/runtime/loader/variant/absence inventory and pass every precondition. H1, the original seven outcomes, full routine/R03, integration and R04/R05 closure retain their separate gates.

If source-backed variant completeness or the nonselecting condition cannot be established, the concrete decision is refusal of this profile for that host; no input substitution, alternate runtime search or expectation repair follows. Stop at the declared P11 design/control checkpoint and verified partial delivery.
