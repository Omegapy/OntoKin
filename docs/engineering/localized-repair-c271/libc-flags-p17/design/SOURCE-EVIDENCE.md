# P17 source evidence

This record separates exact historical bytes, source interpretation and the selected policy. The executable inspection module was read only as text at SHA-256 `a8274d56076562a91d26b3cdd2f614fce6fd509733e4939b225dff2ddca09db4`; it was never imported or called.

| ID | Bound evidence | Finding and limit |
| --- | --- | --- |
| S01 | `sources/RETAINED-LIBC-FACTS.json` and exact captured libc | ELF64 little-endian, machine 62, type 3. One `DT_FLAGS=24` at file offset 1,981,088; one `DT_FLAGS_1=1` at 1,981,104. The earlier three PLT tag values remain `0x28000`, `0x3d0`, `0x10`. Raw historical data observation only. |
| S02 | `sources/PACKAGE-BINDING.json`, package control, `.dsc`, `INPUTS.json` | Independent standard-library ar/tar decoding matches both package members byte-for-byte to retained libc/loader. Package and source version match. No signature or reproduced-build claim. |
| S03 | `sources/upstream/elf/elf.h` lines 998–1003; full `get-dynamic-info.h`, particularly 133–160 | `DF_BIND_NOW=8`, `DF_STATIC_TLS=16`. Nonbootstrap handling stores flags and translates symbolic/textrel/bind-now bits; loader bootstrap restriction is distinct. These are exact source definitions and control flow, not source-version guesses from a version string. |
| S04 | Full `sources/upstream/elf/dl-static-tls.h`; `dl-reloc.c` lines 40–145 | The helper checks existing static allocation and can attempt surplus allocation. Inadequate capacity/alignment or forced-dynamic state can produce failure. No claim that this phase measured any allocation or runtime state. |
| S05 | `sources/upstream/sysdeps/x86_64/dl-machine.h` lines 362–415; `dl-reloc.c` lines 243–248 | TLS descriptor handling distinguishes optional static placement from dynamic fallback. TPOFF64 requires static TLS; bind-now disables lazy binding in the shown nonprofiling branch. This explains why flags recognition cannot certify runtime feasibility. |
| S06 | P05/P07/P11/P13 adopted contracts; actual inspection source lines 1041–1266 | Existing public/current-origin flags predicate admits only mask 8, with unchanged flags1 mask and multiplicity. Structural guards precede it and string/path/identity guards follow it. P13 keeps source-completeness external. Exact inherited inputs are listed in `READSET.json`. |
| S07 | P16 `ADOPTION.json` plus candidate decision/control/future surface, manifest `61b18ceb15d3ee05d3022c60941ccbbce9c3e08bac148c7750da9f6588091156` | Adopted design adds exact PLT metadata only, with selected-role/pin/loader binding and unchanged flags. Its later adoption requires this separate flags decision before implementation. No P16 control or oracle is amended. |

## Source association and patch coverage

The retained upstream archive is 20,323,540 bytes, SHA-256 `f24aa441021121a79266f0d75242706cab8843a47901fefe74527491807f1998`. The Debian patch archive is 499,524 bytes, SHA-256 `dda4153511bfd543502d18e5bc9323110996fe9c531f14ae3fad6eb17f027c7d`. The `.dsc` is 7,576 bytes, SHA-256 `0915324aa646bb99abfaa9aa6ecb734b30babd28454a3e51f3152912370fbd3e`.

`sources/PATCH-COVERAGE.json` records all 80 active patch entries, their exact hashes and every unified-diff file header. None affects the five selected implementation/header files above or `COPYING.LIB`; no synthetic patched source is presented. `sources/UPSTREAM-SCAN.json` scans every regular member (20,048; 242,115,126 uncompressed bytes) for exact whole tokens `DF_STATIC_TLS`, `DT_FLAGS`, `l_flags`. Historical ChangeLogs remain explicitly distinguished. In current source the static-TLS macro occurs in its definition and the helper comment. A token scan is not a complete semantic or binary-build audit. The inference used here is only that the inspected flags handling and relocation helpers support narrow metadata recognition without adding a name-selection rule.

The official glibc commit notice at <https://sourceware.org/pipermail/glibc-cvs/2021q4/075347.html> corroborates that static-TLS checks were moved into their own helper header. It is supplemental historical context; exact retained 2.41 sources govern this decision. Raw lookup responses are retained externally under `source-attempt001/WEB-LOOKUP.json`. Third-party search results were not used as authority.

The source files retain their original copyright/license notices; the archive's `COPYING.LIB` is included. No source/compiler/target code was executed. The Python standard-library analysis launcher is the only execution involved; this does not claim that the host's own startup loader executed no instructions.
