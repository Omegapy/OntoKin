# P26 final diagnosis: required non-libc ELF metadata exceeds the adopted policy

## Decision and scope

The present inspection policy cannot admit the observed `libdl.so.2` required by the selected Node executable. Its dynamic table contains the three x86-64 PLT tags that the current source permits only for the exact selected libc subject. The independently recovered package bytes reproduce that source mismatch. This is a concrete reason to stop H0 preparation at the current technical boundary.

The conclusion is a source deduction from retained actual observations and inert package bytes. No product inspector, Node, ldd or checker was invoked to reproduce a refusal. No H0 result, approved operational plan or whole N34 source-completeness decision is claimed. The technical boundary was declared at 2026-11-23 16:32:32 UTC; subsequent work here consists only of retained-data/source diagnosis and recovery packaging.

The governing product source is the frozen `ed2fc453042a9f0bc4808c2aea7f015baf1ff73e` file `prototypes/static_tray_v01/current_host_inspection_v01.py`, SHA256 `eea3e6343ae34d9c930a810ca4f363cbcd4264a8d943731f927e41b213755d7a`. Exact source/data identities and locations accompany this report in `FINAL-DIAGNOSIS.json`.

## Actual observation

The shared-image capture completed at 2026-11-23 16:31:23.467796 UTC with return code 0, one data-reader start, zero target starts, empty stderr and no unknown operation recorded. Its 409,562-byte output has SHA256 `de8f8090274d1d60acaec0693f7bfff58c15404086ce555dafefb1b3ecc52045`. The capture remains a completed conditional cache observation; its earlier `full_loader_selection_proved: false` fields are preserved.

The primary image is:

| Field | Observed value |
| --- | --- |
| Named cache path | `/lib/x86_64-linux-gnu/libdl.so.2` |
| Canonical measured path | `/usr/lib/x86_64-linux-gnu/libdl.so.2` |
| Bytes / mode | 14,408 / `0o644` |
| SHA256 | `295fa521a03cd2faa99974f378c9e23dd622021ec7d32bcad4f8ea61aec8a872` |
| ELF identity | ELF64, little endian, System V OSABI 0, x86-64 machine 62, ET_DYN |
| SONAME / needed | `libdl.so.2` / `libc.so.6` |
| RPATH / RUNPATH | Both absent |
| Dynamic flags | `DT_FLAGS = 8`; `DT_FLAGS_1 = 1` |
| First excluded tag | Dynamic entry 14: `0x70000000`, value 4128 |
| Remaining excluded tags | Entry 15: `0x70000001`, value 16; entry 16: `0x70000003`, value 16 |

The recorded alias trace resolves the `/lib` component through the observed `usr/lib` symlink. The final `libdl.so.2` leaf is a regular file, not a leaf symlink. Its identities remained stable through the bounded capture and final recheck.

## Exact policy mismatch and exception applicability

`_read_elf_metadata`, around lines 1892–1905, constructs its ordinary dynamic-tag set. The three observed tags are absent from that set. They are added only when the private `libc_profile` argument is non-null. The failing source predicate is the subsequent `all(tag in ordinary ...)` check, with category `CHI-UNSUPPORTED` and reason `Unreviewed ELF dynamic loader feature`.

`_read_plan_elf_metadata`, around lines 1800–1826, selects that private parser only when the current image path equals `libc_policy["subject"]["path"]`. Every ordinary non-subject image uses the generic parser. `_prepare_libc_plt_policy` and `_check_libc_plt_bindings`, around lines 1328–1394, bind the subject to the actual selected Python `libc.so.6` dependency, its role/alias relations, the exact libc descriptor and the exact loader descriptor. The hardcoded libc binding is 1,995,216 bytes with SHA256 `9792e3cbb541c8f44c7acf5f14f4022ea62998ecc787d326bed4d8b6547dfd92`.

The measured libdl descriptor differs in path, size and digest. It cannot receive the libc exception while preserving these adopted relations and pins. Schema `/0.1.4` retains the private libc dispatch; it does not extend that exception to all glibc shared objects.

`LIBDL-INERT-RECOVERY.json` independently checks the immutable libdl bytes through the structural prefix preceding the tag predicate: ELF identification, type/architecture/version, header and program-table bounds, segment alignment, dynamic-table size and unique file/virtual mapping, and the terminating dynamic entry. All 23 recorded checks pass. Its complete dynamic entries equal the retained actual observation. The first ordinary tag exclusion is entry 14. These are data calculations, not execution of the product parser. They do not establish that an entire future plan would reach this check before any other plan gate.

## Narrow necessity argument: Node's first declared dependency

The selected Node is 126,951,512 bytes, mode `0o755`, SHA256 `acbe4b8d9153b841ed0697cbfc4f93e767386620edb745ab9358306c0a6f31aa`. The successful selected-root capture records `libdl.so.2` as its first `DT_NEEDED` string and dynamic-table entry 0. Node has no SONAME, RPATH, RUNPATH, audit, auxiliary or filter tags in the retained observations. Its flags do not contain `DF_1_NODEFLIB`.

The following source argument is restricted to the unchanged intended direct Node invocation under the fixed five-variable environment and the adopted ordinary kernel/native-execution trust boundary:

1. `elf/dl-deps.c` processes the main object's dynamic entries in order. With no preloads or auxiliary/filter inputs, its first declared dependency request is `libdl.so.2`. That source file is unchanged by the retained active patch series.
2. `elf/rtld.c` initializes the environment search path and preload/audit lists, processes those inputs, and then calls `_dl_map_object_deps`. The fixed environment contains no loader-path, preload or audit override. `/etc/ld.so.preload` is observed absent. Direct kernel-mediated Node invocation supplies no loader CLI option such as `--library-path`, `--preload` or `--inhibit-cache`. The observed loader has SONAME `ld-linux-x86-64.so.2` and no `DT_NEEDED` entries. Node's first libdl request therefore precedes loading of its other declared dependencies.
3. The initially supplied kernel vDSO remains within the inspector's existing kernel-integrity trust boundary. Its maps or SONAME were not separately observed by these captures. This diagnosis does not promote that assumption into a new host proof. Under that boundary, no earlier matching libdl object is supplied by the observed Node/loader identities or the absent preload/audit mechanisms.
4. The relevant `elf/dl-load.c` block checks already-loaded names, applicable RPATH, environment search paths, RUNPATH, cache and then defaults. For this first Node dependency, the observed Node paths and fixed environment provide no earlier file-search directory. This does not depend on proving Python's separate `$ORIGIN/../lib` nonselection: the proposed Node command executes Node directly.
5. The actual cache is 140,751 bytes, SHA256 `52bdd7bee3b50b11a3b47de8f98f464a30c78f8b4328b2f0333dd7c3508d53e3`, new format `glibc-ld.so.cache1.1`, endian flag 2, with 2028 entries. An independent decode of its retained bytes rechecks numeric-name ordering and finds exactly one comparator-equivalent libdl row: index 1481, architecture flags `0x303`, hwcap 0, path `/lib/x86_64-linux-gnu/libdl.so.2`. There is no competing named-hwcaps or legacy-hwcap libdl row. The only cache extension is generator metadata, not a hwcaps section.
6. The exact x86-64 cache header requires flags `0x303`; `elf/dl-cache.c` selects that ordinary row. The captured alias resolves it to the measured canonical libdl. Thus the narrow first-dependency choice is source-supported for the stated direct-invocation context. Later default-directory, Python-origin, general loaded-name reuse and complete transitive selection arguments remain outside this conclusion.

The complete cache implementation and actual x86-64/generic cache headers came from the exact recovered P15 upstream archive. All 80 Debian patches were independently indexed. None changes those cache files or `dl-deps.c`. The relevant `git-updates.diff` changes in `dl-load.c` and `rtld.c` do not change the described dependency/cache-selection block. The ARM float-ABI hunk is conditional on `__arm__`; the machine-mismatch hunk retains a distinct wrong-architecture check. The exact patched-build default-directory argument is unnecessary for this successful cache-choice branch and remains unfinished for wider N34 work.

This is enough to establish a necessary image that the current generic metadata policy cannot admit. It is not proof that Node has run, that its relocations or initialization succeed, or that every later edge is uniquely resolved.

## Other observed mismatches to preserve

The same retained capture also records the excluded tag trio in `libpthread.so.0`, `libutil.so.1`, `libm.so.6` and `librt.so.1`. Their hashes and fields are retained in the JSON diagnosis. They are additional actual observations, not separate product refusal runs.

Two further flags issues must not be lost in a future decision. The measured libm has `DT_FLAGS = 24`, which exceeds the generic `value & ~8 == 0` rule. The measured librt has `DT_FLAGS_1 = 9`, whose `0x8` bit exceeds the allowed `1 | 0x08000000` mask. Those checks occur after the tag allowlist in the current parser. Widening only the tag list would therefore leave further source mismatches. No widening, implementation or qualification was performed here.

## Portable evidence and preserved history

The exact 14,408-byte libdl has been recovered as inert mode-0644 data at `libdl-package-bytes/libdl.so.2.inert`. It came from the already-retained P15 official binary package `libc6_2.41-12+deb13u4_amd64.deb.inert`, 2,846,580 bytes, SHA256 `967aa62605721081c3eb2a17650611a792aa802d76a6511d1840242623d204c9`. The route is its `data.tar.xz` member, then `./usr/lib/x86_64-linux-gnu/libdl.so.2`. Its hash exactly equals the current measured libdl hash. `LIBDL-INERT-RECOVERY.json` binds the package, ar members, tar member, extracted bytes and independent predicate/cache calculations. No fresh host-library read was used for recovery.

Selected-root attempt001 remains a completed reader failure caused by its one-containing-segment diagnostic restriction. It discarded partial ELF evidence and did not prove the actual mapping. Candidate002 retained the P10 interval evidence and its later capture succeeded. Both candidates, all attempts and the original failure classification remain unchanged. That reader correction is separate from the present non-libc tag-policy incompatibility.

## EPHEMERAL next step and remaining gates

Stop technical work in this phase, retain C271 open, and deliver the final verified recovery archive. A fresh disposable-host session must first recover and verify that archive, its exact source revision and the retained evidence; current scratch paths or host identities are not continuation assumptions.

The next bounded technical scope should be a source-backed compatibility **decision** for the observed necessary non-libc tag trio and the separately observed libm/librt flags, starting with the portable libdl fixture. Review whether an explicitly bounded extension is justified under the existing contract, identify exact subjects and source provenance, and specify the required positive/negative controls before authorizing implementation. Preserve all existing pins and ordinary refusal behavior. Do not infer permission to broaden every dynamic tag or transfer libc's private exception to other images.

Whole N34, complete Python-origin/search-directory/variant evidence, final runtime-role and alias agreement, an independently approved operational H0 plan, H0 execution/acceptance, H1 and later qualification gates remain unresolved. The present source deduction is the stopping result; it does not satisfy those later gates.
