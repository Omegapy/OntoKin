# C271 P15 independent actual-loader source review

Reviewer: `/root/loader_review`. Decision: **accepted source-complete suffix union only**.

The exact source argument is accepted for the identified actual loader and the adopted ordinary direct-Python invocation context. The Director may continue to the next H0 prerequisite within this same selected phase. No operational plan, whole H0 result, H1 invocation or host qualification is approved by this decision.

## Exact reviewed candidate

The investigator is `/root/state_reconciliation`. The reviewed `source-provenance/REPORT.md` is 12,668 bytes, SHA-256 `ef9f36ff123b82020bf519688c4376e7b4b71afab52f27e551710d14cf4c6656`. Its `FINAL-MANIFEST.json` is 19,967 bytes, SHA-256 `a66fccaf29a5a85fba4479705fd41b0fc40187df9359d913140693cf107ee68a`. Independent verification checked all 61 payload sizes and hashes and the exact file inventory. See `PROVENANCE-MANIFEST-REVIEW.json`.

This review also independently read the current inspection module at retained-branch revision `875c81c506d4e5431b909e190ce294c61312029e`, SHA-256 `a8274d56076562a91d26b3cdd2f614fce6fd509733e4939b225dff2ddca09db4`, for the P11/P13 boundary. That source inspection did not execute the module.

## Binary and source correspondence

The selected Python's exact pin, raw ELF interpreter path, canonical file chain and the loader alias resolution were independently verified. The current loader and the Director's inert copy are identical: 225,672 bytes, SHA-256 `c8438e4fde1934e61c88311633f00949ff645d5c04cdb8671fa3d78164d2f307`, GNU build ID `86f7eb4ff495ed3f2831c6d3d662e4321762a2a3`. See `STATIC-IDENTITY-REVIEW.json`.

An independent ar/tar reader then compared the exact member of the official Debian `libc6_2.41-12+deb13u4_amd64.deb` package with the captured loader. The bytes are identical. The package control independently names `glibc` as source, `2.41-12+deb13u4` as version and `amd64` as architecture. Package SHA-256 is `967aa62605721081c3eb2a17650611a792aa802d76a6511d1840242623d204c9`. This concrete member association is stronger than the embedded version label. See `PACKAGE-BINDING-REVIEW.json`.

The exact official `.dsc` names the same source/version. Its upstream and Debian patch archive checksums were independently verified before source reading; the descriptor and patch checksums also occur in the retained official Debian acceptance notice. The source archives have SHA-256 values `f24aa441021121a79266f0d75242706cab8843a47901fefe74527491807f1998` and `dda4153511bfd543502d18e5bc9323110996fe9c531f14ae3fad6eb17f027c7d`. `SOURCE-MEMBERS.json` binds this reviewer's independently materialized source text and active-patch inventory.

The correspondence uses Debian's official HTTPS artifact/source association and published source recipe. The OpenPGP signature, exact compiler environment and binary buildinfo were not independently validated, and the build was not reproduced. Those limits remain explicit. P11/P13 require a defensible relation to source/build or inspected implementation evidence; they do not require a reproduced build. The exact official package-member match, declared source association, pinned source/patch bytes and inspected architecture/build recipe are sufficient for this finite source-semantic conclusion within the existing native-execution trust boundary.

## Complete finite union

The accepted sorted inventory is:

- `""` — the base directory.
- `glibc-hwcaps/x86-64-v2`.
- `glibc-hwcaps/x86-64-v3`.
- `glibc-hwcaps/x86-64-v4`.

The independent reasoning follows actual construction, rather than inferring completeness from a label or missing search hit:

1. `sysdeps/x86_64/dl-hwcaps-subdirs.c` contains exactly three built-in names. Its CPU-dependent function returns only a mask over that fixed list. The exact three-name constant is also present in the inert binary at offset 181136. The full possible union therefore covers every active CPU subset without claiming which subset is presently active.
2. The fully read `elf/dl-hwcaps.c`, `dl-hwcaps.h` and `dl-hwcaps_split.c` construct `glibc-hwcaps/` plus a selected list name, append a separator, and finally add the empty base entry. Filtering cannot create another name. There is no legacy hardware/TLS permutation generator in this complete constructor.
3. `rtld.c` initializes prepend and mask fields to null. The only assignments of arbitrary list strings are inside explicit loader-command handling. The adopted profile excludes that invocation route. The archive-wide symbol evidence corroborates the inspected call/state relationships. Allowing a future explicit loader command would require new review.
4. `_dl_init_paths` obtains this prefix array, and the inspected `open_path` loop concatenates one search root, one prefix and the needed object name. RPATH and RUNPATH lookup use that loop. This accounts for emitted suffixes; TLS memory machinery does not add directory alternatives to it.
5. All 80 active Debian patch identities independently agree with the investigator's full patch audit. None changes the constructor, splitter, state header or x86-64 list. Relevant `dl-load.c`, `rtld.c`, compiler-configuration and multiarch patch hunks were inspected. They do not introduce another suffix source.
6. Debian's compiled default library roots and cache route are distinct from suffixes added to the selected origin root. Their unchanged full closure and inventory obligations remain for plan review. This decision does not treat a complete suffix list as a complete loader-resolution map.

## P13 boundary and remaining obligations

This is an external reviewer decision. It adds no approval Boolean, completeness selector or manufactured exception to a product plan or variant schema. It does not report a runtime pass or skip for N57; the historical oracle remains unchanged. The accepted implementation still binds the four-key variant document and machine-observable facts, while review sufficiency remains external.

No operational plan or runtime variant document has been supplied or adopted. A later eligible plan in the selected scope must bind this exact loader, accepted rationale and four-entry inventory, plus the complete dependency-name union, actual directory/absence guards, selected Python/kernel identity, source/input records and externally supplied expected digest. An actual plan identity must be reviewed before operational adoption. Any changed loader, source, rationale, suffix set or invocation context requires renewed review.

The next action is the Director's next H0 input-admission check. Stop at its first concrete mismatch; do not repair or substitute inputs. No source-completeness blocker remains in the reviewed candidate. Operational eligibility and all later gates remain undecided.

## Execution disclosure

The Director's `HOST-OBSERVATION-BOUNDARY.json` and this review's `OBSERVATION-BOUNDARY.md` govern the execution wording. Python standard-library scripts ran to inspect bytes, package members and source archives. No Node, ldd, direct loader command, production inspector, installation or H1 target was invoked by this review. No compilation, package installation or downloaded-code execution occurred. No active reviewer job or unknown operation remains.
