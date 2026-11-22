# Independent source semantics review

Reviewer: `/root/design_review`. Scope: the exact three tags rejected in P15. This is source/byte evidence for later candidate review, not candidate adoption or implementation approval.

Root released substantive review only after the verified early-recovery receipt at `../EARLY-RECOVERY-RECEIPT.json` (relative to the P16 session): archive SHA-256 `8cf4fa4e248260411191ec7583eeca4334c0ea6e9cebd38eccc17f3495e342a9`, exact saved-byte equality, 1,580 independent package assertions. The worker read that receipt before this review. All output is confined to `design-review/`.

## Source and captured-byte correspondence

The retained captured libc is exactly the `./usr/lib/x86_64-linux-gnu/libc.so.6` member of the retained official Debian `libc6_2.41-12+deb13u4_amd64.deb`: 1,995,216 bytes, SHA-256 `9792e3cbb541c8f44c7acf5f14f4022ea62998ecc787d326bed4d8b6547dfd92`. An independent standard-library ar/tar reader established byte equality; it did not reuse the earlier reviewer's conclusion. `PACKAGE-BINDING.json` records the package and member hashes and complete control text. The member of the same package for the loader matches P15's `c8438e4f...` identity.

The package control names glibc source version `2.41-12+deb13u4`, amd64. The exact retained `.dsc` names the same source version and binds upstream `f24aa441021121a79266f0d75242706cab8843a47901fefe74527491807f1998` and Debian patch archive `dda4153511bfd543502d18e5bc9323110996fe9c531f14ae3fad6eb17f027c7d`. Both archives were independently hashed before inspection. Official HTTPS retrieval and the P15 source association are retained evidence; this review does not add signature validation, a reproduced build, binary buildinfo or compiler-output proof.

All 20,048 regular upstream archive members (242,115,126 uncompressed bytes) were scanned for `DT_X86_64_PLT`; `TAG-REFERENCE-SCAN.json` records every matching member. This was an automated exact-token scan, not a manual read of the whole archive. A second scan records every `plt_rewrite` occurrence. The 80 active Debian patch headers and source identities were checked. `PATCH-RELEVANCE.json` and the fully read `RELEVANT-PATCH-SECTIONS.diff` show no patch to the tag definitions, tag-index decoder, rewrite consumer, default state, tunable declaration or post-relocation hook. The relevant CPU-feature changes leave the rewrite callback unchanged. The Makefile patch adds an ABI-version test; the nearby Versions hunk adds `GLIBC_ABI_DT_X86_64_PLT`, not another tag consumer.

## Meaning of the three tags

The checksum-bound primary source defines these values in `sources/glibc-2.41/elf/elf.h` (SHA-256 `1490fa24d00c6e1a803edd0402e24f11bcf9de0683953f83a726a9c5462fe46c`):

| Value | x86-64 name | Meaning supported by the consumer |
| --- | --- | --- |
| `0x70000000` | `DT_X86_64_PLT` | Link-time address of the procedure linkage table (PLT). The consumer adds the object's load address. |
| `0x70000001` | `DT_X86_64_PLTSZ` | Total PLT size in bytes. |
| `0x70000003` | `DT_X86_64_PLTENT` | Size of an individual PLT entry in bytes. |

The exact `sysdeps/x86_64/dl-machine.h` (SHA-256 `1545fc722187437ac1c73b5e022fa409ace5998c21915e9d3133c23d0f4413a7`) reads these as numeric address/size fields, not string-table names, dependency names, path names or search suffixes. `elf/get-dynamic-info.h` maps processor-specific values to `l_info`; x86-64's `DT_THISPROCNUM` and `DT_X86_64` macro select the indexed fields. No source-backed claim that these numbers mean the same thing on another architecture is valid. In the same `elf.h`, `0x70000001` and `0x70000003` have different AArch64 meanings (`DT_AARCH64_BTI_PLT` and `DT_AARCH64_PAC_PLT`). Unknown `0x70000002` is not added by the x86-64 definitions.

Independent inert-byte decoding in `CAPTURED-TAG-FACTS.json` confirms machine62, ELF type3, values `0x28000`, `0x3d0`, `0x10`, and exact P15 offsets. The range begins at the start of an executable PT_LOAD. This is a raw observation; no production reader or H0 admission was retried.

## Runtime effects and limits of a metadata claim

`x86_64_dynamic_after_reloc` is called after relocation through `ELF_DYNAMIC_AFTER_RELOC`. It returns early under lazy binding, when rewriting is disabled, when the PLT tag is absent, or when no JUMP_SLOT relocation exists. It also requires the relevant relocation pointer/size, a PLT entry size of at least16, and a total size no smaller than and divisible by the entry size.

When enabled, `x86_64_rewrite_plt_in_place` changes PLT page protections and `x86_64_rewrite_plt` rewrites indirect branches, using JUMP_SLOT relocation offsets/addends and already resolved GOT values. It then restores executable/readable protections. These tags are therefore not universally inert, harmless or runtime-ignored metadata.

The exact default `dl-procruntime.c` sets `plt_rewrite_none`; `feature-control.h` defines its zero-valued enum. `cpu-features.c` can enable rewriting through the `glibc.cpu.plt_rewrite` tunable callback after platform checks. The adopted clean child environment excludes that variable, but this review makes no observation about the already running host's historic loader state. No runtime state or memory safety is certified here.

The existing JUMP_SLOT/GLOB_DAT relocation branch assigns the resolved value without adding `r_addend`. Official GNU ld documentation warns that marked PLT binaries can be incompatible with older loaders lacking this behavior. This is a material reason not to extrapolate the present source argument to arbitrary loaders.

## What bounds are required depends on the stated promise

For a narrowly stated recognizer that only classifies three numeric dynamic entries while retaining the existing ELF table/file/read limits, the values cause no additional read, allocation, iteration or pointer dereference. No separate resource cap follows merely from recognizing them. Existing handling of ordinary relocation/initialization tags also does not validate all runtime memory behavior. Such a recognizer must say that it does not certify PLT structural validity or execution safety.

If a candidate instead claims to admit only structurally coherent PLT metadata, that is an additional explicit policy. Its controls must cover the exact admitted triplet/presence/uniqueness rules, nonzero entry/total sizes, allowed entry-size/alignment, total-size divisibility, 64-bit range overflow, and complete unambiguous file-backed range mapping as claimed. Any new numeric ceiling needs a concrete purpose rather than an arbitrary second policy. These checks would still not prove relocation target validity, instruction layout, page protection safety, execution safety or complete loader compatibility. Rewriting can depend on other dynamic/relocation contents outside this P16 scope.

Neither route permits an unversioned change to the old public parser or old profiles. Nor does metadata admission by itself establish the complete finite plan/closure, actual input inventory, H0, H1 or parent R03.

## Flags remain a distinct preserved gate

Captured `DT_FLAGS=0x18` is raw evidence, and source `elf.h` names its bits `DF_BIND_NOW=0x8` and `DF_STATIC_TLS=0x10`. Current OntoKin permits only `0x8`; its `DT_FLAGS_1` mask is `0x08000001`. P15's reader stopped before this check. The mathematical source comparison indicates that admitting the three tags alone cannot make these unchanged libc bytes pass every current parser predicate. It is an inference about the preserved source, not a new product execution or observed H0 result. No mask change is authorized in P16.

## Supplemental primary references and retrieval limits

The official GNU ld manual (`https://sourceware.org/binutils/docs/ld.html`, web ref `turn406029985view2`) supports `mark-plt` semantics and the older-loader caveat. The official glibc commit notice (`https://sourceware.org/pipermail/glibc-cvs/2024q1/083835.html`, `turn406029985search0`) corroborates the three field meanings; the exact retained 2.41 source remains the implementation authority. The official bug/commit notice (`https://sourceware.org/pipermail/glibc-bugs/2025-August/059912.html`, `turn406029985view1`) explains the ABI-version compatibility marker. These are not proof of this host's executable state.

The direct x86-64 psABI commit retrieval returned `DisabledError`. A third-party PDF search excerpt mentioning power-of-two entry sizes was not used as primary authority. No claim of a firsthand complete ABI read is made. Raw search/open responses, including that failure, are preserved in `WEB-SEARCH-001.json` and `WEB-PRIMARY-002.json`.

Python standard-library tools ran for static source/archive/data inspection. No product import, product/parser execution, Node, ldd, direct loader command, installation, compilation or downloaded-code execution occurred. Python launcher startup can itself invoke its host loader; no claim of zero loader instructions is made. No candidate decision is accepted until its exact frozen manifest and controls have been independently reviewed.
