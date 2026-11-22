# P16 source evidence and limits

All upstream source copies are exact members of the P15-retained glibc archives. `SOURCE-AUDIT-002.json` records a fresh data-only verification, its exact script/command/interpreter, 46 successful assertions, 20,048 regular upstream members scanned and all 80 active Debian patches. The source files were read as text; no downloaded or product code ran. `READSET.json` distinguishes full reads, selected lines, automatic scans and retained-only files.

## Source index

| ID | Exact evidence and inspected ranges | Supported statement |
| --- | --- | --- |
| S01 | P15 `BLOCKER-REVIEW.md`, `BLOCKER-DECISION.json`, `STATIC-ADMISSION-OUTCOME.json`, full; identities in `INPUTS.json` | Exact first unsupported-tag refusal; later flags predicate not reached; historical capture identity and incomplete gates. |
| S02 | `sources/LIBC-PACKAGE-BINDING.json`; `SOURCE-AUDIT-002.json`; retained package control/provenance report | Exact captured libc and loader equal the two corresponding members of the same pinned official Debian amd64 package. Source/version association and evidence limits. |
| S03 | `sources/upstream/elf/elf.h` lines 924–931, 3045–3054, 3648–3665 | Processor-specific numeric base, exact three x86-64 names, and AArch64 collisions. No claim that all processor-specific tags are supported. |
| S04 | `sources/upstream/elf/get-dynamic-info.h` full; `sources/upstream/sysdeps/x86_64/dl-dtprocnum.h` full | glibc stores the architecture-specific dynamic entries using its x86-64 count. Generic dynamic-pointer adjustment does not adjust the PLT tag; the consumer adds the load bias. |
| S05 | `sources/upstream/sysdeps/x86_64/dl-machine.h` lines 531–765; `sources/upstream/elf/dynamic-link.h` lines 166–208 | Full active PLT rewrite consumer and its call after relocation. It reads GOT/relocation results, changes protection and branch bytes; it introduces no dependency name or search path in this code. |
| S06 | `sources/upstream/sysdeps/x86_64/{feature-control.h,dl-procruntime.c}` full; `sources/upstream/sysdeps/x86/cpu-features.c` lines 1–65, 1292–1325; `sources/upstream/sysdeps/unix/sysv/linux/x86_64/dl-plt-rewrite.h` full | Disabled initializer; nonzero explicit tunable setter; optional relative/direct-absolute branch choices and Linux mprotect probe. CPU-dependent active rewrite is not asserted as executed. |
| S07 | `sources/upstream/sysdeps/x86/dl-tunables.list` full; `sources/upstream/elf/dl-tunables.c` lines 286–357, 434–474; `sources/upstream/scripts/gen-tunables.awk` lines 45–67, 155–193 | No alias for this tunable; initialization from environment; callback requires initialized value; generated alias list excludes unset aliases. |
| S08 | `sources/upstream/sysdeps/x86_64/Makefile` lines 1–25; `sources/upstream/sysdeps/x86_64/configure.ac` lines 1–70 | Build recipe probes linker `-z mark-plt`, adds tags when supported and suppresses them for ld.so. This is a recipe, not a recovered build invocation. |
| S09 | `sources/UPSTREAM-SYMBOL-SCAN.json`, `sources/{DEBIAN-PATCH-SCAN,ALL-SELECTED-PATCH-COVERAGE}.json`; both complete selected `git-updates-*-context.diff` files | Full regular-member symbol scan and all active-patch coverage. Relevant patch sections do not change the selected tag definitions, consumer, disabled initializer or tunable setter. CPU tuning changes elsewhere are retained; the Makefile/version-map change adds an ABI marker check. |
| S10 | Retained `current_host_inspection_v01.py`, SHA-256 `a8274d56076562a91d26b3cdd2f614fce6fd509733e4939b225dff2ddca09db4`; ranges in `READSET.json` | Existing default/tag/flag/bounds/identity contracts, exact environment, profile dispatch and early/recheck ordering. Read as source only. |
| S11 | P05/P07/P11/P13 exact adoptions and contracts, full reads recorded in startup readset | Immutable old behavior, complete role/source/closure gates, synthetic primitive distinction and P13 review-only completeness allocation. |

## Exact primary artifacts

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `glibc_2.41-12+deb13u4.dsc` | 7,576 | `0915324aa646bb99abfaa9aa6ecb734b30babd28454a3e51f3152912370fbd3e` |
| `glibc_2.41.orig.tar.xz` | 20,323,540 | `f24aa441021121a79266f0d75242706cab8843a47901fefe74527491807f1998` |
| `glibc_2.41-12+deb13u4.debian.tar.xz` | 499,524 | `dda4153511bfd543502d18e5bc9323110996fe9c531f14ae3fad6eb17f027c7d` |
| `libc6_2.41-12+deb13u4_amd64.deb` | 2,846,580 | `967aa62605721081c3eb2a17650611a792aa802d76a6511d1840242623d204c9` |

P15's retained provenance names the official HTTPS pool prefix `https://deb.debian.org/debian/pool/main/g/glibc/` for these exact filenames. No new web request was needed to interpret the exact retained source. This report does not substitute a current package listing for those pinned bytes.

The archive member source hashes, selected patch hashes and preserved extraction ranges appear in `sources/*MEMBERS.json`, `SOURCE-AUDIT-002.json` and the candidate manifest. No full source checkout, compilation or installation was created. All copied source members are inert regular files.

## Why opaque metadata recognition is supportable

The three tag values address the existing object's PLT mechanics. The full source consumer first checks lazy binding, rewrite-feature state, tag availability, jump-slot presence and relocation/entry-size prerequisites. When active, it obtains function targets from already relocated GOT entries and writes a direct branch or leaves an entry unchanged. It does not parse a new soname/path, call a library search routine or create a dependency edge in this operation. This supports excluding these **three identified tags on this identified architecture/source pair** from the dependency reader's unknown-feature refusal.

The inference is deliberately narrower than native safety. The consumer can fail to change protection or raise an error restoring protection. PLT/GOT/relocation correctness matters if executed; this reader does not validate it. The implementation's own subset checks are not copied into a new ELF validator. The synthetic all-zero/maximum/inconsistent-value positives explicitly prevent that stronger claim. Operational bytes remain the exact pinned library, and every ordinary inherited gate still applies.

The existing five-variable environment is a further retained condition. The initial rewrite state is disabled; its only noninitial assignment in the scanned source is the nonzero-tunable callback. The exact tunable has no alias; the generated alias list and environment initialization path make the absence of `GLIBC_TUNABLES` meaningful. This is a source-backed explanation under the adopted launch contract, not observation of a live process or proof of a complete kernel/native boundary.

## Build and patch limits

The full active patch scan found relevant selected-file changes only in `git-updates.diff`: CPU tuning changes outside the setter, and a Makefile test. The complete affected CPU/Makefile diff sections were inspected. A neighboring x86-64 `Versions` hunk adds the `GLIBC_ABI_DT_X86_64_PLT` empty version-map marker, which the Makefile test checks. Neither changes the numeric tags or the consumer described above. All original patch bytes remain in the exact archive; no patch was applied or build executed.

P15's official package/source association supplies useful evidence for this finite decision. It does not prove a bit-for-bit build from source, identify the exact linker/compiler invocation, locally validate the `.dsc` signature, or establish any current-host path. The retained source is sufficient to avoid guessing tag semantics; these remaining provenance limits are retained for independent review and future plan adoption.
