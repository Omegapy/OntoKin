# P26 independent blocker review

**Disposition: concrete current-input incompatibility confirmed.** The selected Node requires an actual `libdl.so.2` whose ELF dynamic metadata the adopted inspector cannot accept. This is sufficient to stop the current H0-plan phase. It is a deduction from exact retained source and observations; no H0 or product-parser refusal was executed.

The relevant source is commit `ed2fc453042a9f0bc4808c2aea7f015baf1ff73e`, inspector SHA256 `eea3e6343ae34d9c930a810ca4f363cbcd4264a8d943731f927e41b213755d7a`. The selected contract is plan schema `/0.1.4`, profile `linux-glibc-declared-python-origin-rpath-libc-plt-static-tls-rtld-paths-v1`. Exact evidence/source references and scope qualifications are in `BLOCKER-REVIEW.json`; capture disposition is in `CACHE-SHARED-OUTCOME-REVIEW.json`.

## Observed facts and source rule

The shared-image data capture completed once with return code 0, empty stderr, zero target starts and no unknown operation. Its 409,562-byte output is bound by SHA256 `de8f8090274d1d60acaec0693f7bfff58c15404086ce555dafefb1b3ecc52045`. Successful collection does not imply a successful product inspection.

| Necessary image field | Retained actual value |
| --- | --- |
| Cache alias | `/lib/x86_64-linux-gnu/libdl.so.2` |
| Canonical image | `/usr/lib/x86_64-linux-gnu/libdl.so.2` |
| Size / mode / links | 14,408 bytes / `0o644` / 1 |
| SHA256 | `295fa521a03cd2faa99974f378c9e23dd622021ec7d32bcad4f8ea61aec8a872` |
| ELF identity | ELF64 little endian, ET_DYN, x86-64, System V OSABI 0 |
| SONAME | `libdl.so.2` |
| Dynamic flags | `DT_FLAGS=8`, `DT_FLAGS_1=1` |
| Dynamic entries 14–16 | `0x70000000=4128`, `0x70000001=16`, `0x70000003=16` |

The ordinary tag set in `_read_elf_metadata` excludes all three recorded tags. The source adds them only under the private libc metadata rule. `_read_plan_elf_metadata` applies that rule solely to the selected libc subject; `_check_libc_plt_bindings` requires the subject to be the actual selected Python's libc dependency with exact role, alias, descriptor and fixed hash/size/mode relationships. The selected libc is a distinct 1,995,216-byte image with SHA256 `9792e3cbb541c8f44c7acf5f14f4022ea62998ecc787d326bed4d8b6547dfd92`.

The source-predicted category is `CHI-UNSUPPORTED`, reason `Unreviewed ELF dynamic loader feature`. That string is a source deduction, not captured product stderr. The report does not claim that a complete future plan would reach this predicate before any earlier gate.

## Why this image is necessary

The successful selected-root observation records the pinned Node's first `DT_NEEDED` as `libdl.so.2`, at dynamic entry 0. Node has no RPATH, RUNPATH, SONAME, audit, auxiliary or filter entries. Its `DT_FLAGS_1=1` does not suppress default-library cache entries. The adopted future command is direct `NODE --version` under the fixed five-variable environment in the inspector source.

The retained loader source supplies a narrow selection argument. `dl-deps.c` processes the main object's dynamic entries in order. `rtld.c` first handles preload and audit inputs. The clean environment contains no such overrides, the captured global preload file is absent, and direct kernel-mediated execution supplies no loader command-line override. The observed loader has its own `ld-linux-x86-64.so.2` SONAME and no needed entries. Node's first dependency request therefore precedes its other declared dependencies.

The existing kernel-integrity assumption includes the normal kernel-provided vDSO. Its maps and SONAME were not separately observed. Under that explicit boundary, neither the initial main/loader identities nor the absent preload/audit mechanisms supply an already-loaded libdl. This assumption is not promoted into a new host observation.

For the first Node request, the relevant `dl-load.c` sequence has no applicable RPATH, environment-path or RUNPATH input, so it reaches the cache. The retained cache bytes have exactly one numeric-comparator-equivalent libdl row: index 1481, flags `0x303`, hwcap 0, alias `/lib/x86_64-linux-gnu/libdl.so.2`. The exact x86-64 cache header admits those flags. There is no competing named- or legacy-hwcap libdl row. Its captured alias reaches the compatible, stable, canonical regular file identified above.

This reasoning uses the relevant exact loader source and patch context. The complete cache implementation and x86-64/generic headers were read. The 80-patch index has no changes to those cache files or `dl-deps.c`; relevant `dl-load.c` and `rtld.c` patch hunks preserve the described sequence. The accepted P15 source/package association retains its existing limits: it is not a reproduced build or a new whole-source acceptance.

The argument suffices for this first Node dependency. It does not require Python's separate `$ORIGIN` nonselection proof or a complete argument for later cache edges and default directories. All raw `full_loader_selection_proved:false` fields remain unchanged.

## Smallest incompatible requirements

1. The selected Node and its fixed direct command remain required.
2. `_check_resolution` requires the complete actual image/needed-edge closure, including this selected libdl.
3. This distinct non-libc image must pass the ordinary parser, whose tag predicate excludes the recorded trio.
4. The private exception is restricted to the exact selected libc and cannot admit this libdl descriptor.

These requirements cannot all hold for the unchanged inputs and source. Omitting the required image, assigning an inaccurate edge, changing a pin or borrowing the libc role would violate the adopted contract. The earlier commands-list and file-backed-extension representation questions do not form this blocker and remain governed by their separate advisories.

## Further recorded limits

The same raw observation records the trio in `libpthread.so.0`, `libutil.so.1`, `libm.so.6` and `librt.so.1`. It also records `libm` flags 24, which fail the ordinary `value & ~8 == 0` predicate, and `librt` flags-1 value 9, whose bit 8 exceeds the ordinary `1 | 0x08000000` mask. Those later predicates follow the tag check. A future compatibility decision must preserve these findings; widening only the tag set would leave additional source mismatches.

The source author independently recovered the exact libdl bytes from the retained P15 package as inert data. `LIBDL-INERT-RECOVERY.json` binds the package/member/current-image equality and records 23 structural-prefix data checks plus a separate cache decode. This reviewer read that report and compared it with the retained source and actual raw fields. It is supporting data evidence, not a product invocation.

Selected-root attempt001 remains a failed raw-reader attempt with a one-segment string-table restriction and discarded partial ELF fields. Corrected attempt002 remains a separately reviewed successful observation. Preparation preflight records, unexecuted candidate defects, navigation failures and every prior outcome remain preserved. None is relabelled as the present product-source incompatibility.

## Disposition and next scope

The Director's technical stop at **2026-11-23 16:32:32 UTC** is justified. Complete preservation, documentary reconciliation and final verified recovery delivery. C271 and unfinished requirements remain open.

A later separately authorized phase must first follow the governing `EPHEMERAL-HOST.md`: review the portable exact libdl counterexample against durable project verification requirements and approved portable-input routes. Determine the precise source/contract decision needed for the necessary non-libc tag trio and the separately observed libm/librt flags. Any compatibility decision must identify eligible subjects, source semantics, role restrictions and positive/negative controls before implementation and adoption. This does not automatically authorize another temporary-host profiling or exception phase, or a generalization of the libc rule. Existing methods/helpers, the 24-file dependency contract, selected pins, P05/P06 behavior, command/environment/budget constraints, ordinary refusal behavior, N34, historical N57 and independent review requirements remain constraints.

Complete native selection, Python-origin/search-directory/variant proof, final runtime/metadata/alias/path-guard assembly, a complete accepted H0 plan, H0/H1 execution and later qualification remain unfinished. This review grants no further technical execution or adoption authority.
