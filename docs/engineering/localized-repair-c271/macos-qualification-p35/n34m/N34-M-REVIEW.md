# N34-M: independent review of the Mach-O parser and the closure claim

**Reviewer:** W1, the N34-M reviewer of phase `C271-P35-macos-host-qualification-mh`, gate MH, stage S2 (Director `c271-p35-e38e3aa82ade`), local mode. W1 is a Claude Code subagent in a fresh context. It wrote none of the parser, the contract, the amendment, the preparation or the plans.\
**Bound commit:** `16d4f9f4a13bb7edef709a1ac050b81469fb3063`. The C271 worktree was clean, with only `.venv/` ignored, at the start and at the end.\
**Contract:** `ontokin.current-host-readback/0.2.0`, design revision 4 (CONTRACT.md as amended by P33-AMENDMENT-001).\
**Obligation:** contract section 7, N34-M; MH-PLAN stage S2; PHASE.json acceptance A2.\
**Host:** macOS 26.6.2 (25G83), arm64; the system and cryptex SystemVersion.plist files are byte-identical.\
**Date:** 2026-11-26.

Places are named by labels:

- `<worktree>` is the C271 worktree.
- `<local>` is the working directory beside the clone.
- `<prefix>` is the installation prefix that holds the interpreter's framework and its non-system libraries.

Framework paths in the tables are relative to the framework version directory, `<prefix>/Cellar/python@3.12/3.12.13/Frameworks/Python.framework/Versions/3.12`; `.venv` paths are relative to `<worktree>/.venv`. The machine-readable form is [N34-M-REVIEW.json](N34-M-REVIEW.json), and the scripts and raw outputs lie beside it.

## Verdict

**ACCEPT_WITH_NONMANDATORY_FINDINGS.** There is no mandatory finding.

- `bin/node` meets every rule of contract section 7. All 111 Mach-O images of the interpreter installation (79 in the framework version directory, 27 in the `.venv`, 5 external dependencies) meet section 4's rules. P33-AMENDMENT-001 (design revision 4) changes neither section.
- The parser under review accepts all 112 files, and its parse agrees field for field with the independent reader's. Its Python inventory equals the reader's listing entry for entry and equals MP's after-snapshot (`c277bdd3…`). M0's Mach-O and Python-installation checks would pass on this host as the files stand.
- The closure claim holds for these files within its stated limits. Every non-system reference resolves to a bound file, and every system reference is absent from disk and present in the image table of the OS cryptex's dyld shared cache.
- D-16: `bin/node` links CoreFoundation by a plain `LC_LOAD_DYLIB` (command 14).
- Nine nonmandatory findings, N-01 to N-09. None blocks the adoption of an execution plan.

## 1. Method

1. **Read:**
   - CONTRACT.md sections 3 (Node's "thin 64-bit arm64"), 4, 7 and 12, and the matching lists in CONTRACT.json;
   - AMENDMENT-001, which changes neither section 4 nor section 7;
   - the parser's Mach-O and Python-installation parts (current_host_observation_v02.py: constants 184–232; parser 715–958; trees and links 960–1069; Python inventory, closure, comparison and packages 1072–1455; launcher 1457–1518; check_runtime 1850–1890; check_git_binding 1893–1926; GIT_VERSION_LINE 116);
   - W3-OBSERVER sections 5, 6 and 9 to 12; MH-PLAN sections 3 and 6; D-16.
2. **Reader.** `n34m_reader.py` is an independent Mach-O reader that uses only the standard library and `struct`. It shares no code with the parser and does not import it.
   - **Each file:** SHA-256, size, mode and link count; thin or fat, with every fat slice; the header, with the cpusubtype's capability bits separated; the file type and flags; and every load command with its decoded fields. It also checks the structure: section, symbol, indirect-symbol and linkedit ranges, and segment overlap.
   - **Trees:** it lists both trees exhaustively without following links, and classifies every regular file by its leading magic.
   - **Resolution:** it resolves the `bin/python` chain hop by hop, cross-checked with `os.path.realpath`. It computes the closure to a fixed point, with two resolutions of `@rpath`: the image's own entries, and a dyld-like rpath stack.
   - **System references:** it checks each one against the disk and against the image table of the cryptex's main shared-cache file. It also checks install names for collisions.
   - **Rules:** it evaluates the contract's rules independently.
3. **Comparison.** `n34m_compare.py` loads the parser by file path. Importing it added only standard-library modules. The script calls only pure functions:
   - `read_macho` with the NODE-SOURCE pin and `private=True`, as `check_runtime` does, then `check_node_macho`;
   - `check_python_macho` for each image;
   - `python_inventory` twice, with `compare_inventory`;
   - `verify_packages`, and `launcher_state` with `check_launcher` for its own process;
   - `read_os_identity`, and `macho_magic_kind` and `_macho_extent` on Git's first bytes.

   It compares the two parses command by command, and cross-checks every tree entry, with every file's SHA-256. It also runs 64 Node and 17 Python mutation cases in memory.
4. **Git.** `n34m_git_scan.py` reads the developer tools' Git statically and extracts its embedded version text.
5. **Runs.** Every run used `<worktree>/.venv/bin/python -I -S -B`. Run 02 is the evidence. Run 03 repeated the comparison after all other work, with the same result. The commands are in the JSON form's `reproduction`.

## 2. The files

### 2.1 `bin/node`

| Property | Value |
| --- | --- |
| Path | `<local>/c271-macos/node-v24.22.1-darwin-arm64/bin/node` |
| SHA-256 | `6f32069480ec14d52b6d7b1f3c7124cfbbc46203abf5ddf5c65b127435f3f329` |
| Size, mode, links | 122,545,856 bytes, `0o755`, 1 |
| Container | thin |
| Magic | `MH_MAGIC_64` (little-endian) |
| cputype | `0x0100000c` CPU_TYPE_ARM64 |
| cpusubtype | `0x00000000`: value 0 (CPU_SUBTYPE_ARM64_ALL), capability bits `0x00000000` |
| File type | 2 `MH_EXECUTE` |
| Flags | `0x00a18085`: MH_NOUNDEFS, MH_DYLDLINK, MH_TWOLEVEL, MH_WEAK_DEFINES, MH_BINDS_TO_WEAK, MH_PIE, MH_HAS_TLV_DESCRIPTORS |
| ncmds, sizeofcmds | 21, 2416 |
| Pin (NODE-SOURCE.json) | equal: SHA-256, size and mode |
| Contract section 7 (reader) | ACCEPT |
| Parser (`read_macho` with the pin, `check_node_macho`) | accepted; no field differs from the reader |

| # | cmd | Name | cmdsize | Decoded fields |
| --- | --- | --- | --- | --- |
| 0 | `0x00000019` | `LC_SEGMENT_64` | 72 | `__PAGEZERO`; file 0 + 0 |
| 1 | `0x00000019` | `LC_SEGMENT_64` | 792 | `__TEXT`; file 0 + 91717632 |
| 2 | `0x00000019` | `LC_SEGMENT_64` | 312 | `__DATA_CONST`; file 91717632 + 1409024 |
| 3 | `0x00000019` | `LC_SEGMENT_64` | 552 | `__DATA`; file 93126656 + 196608 |
| 4 | `0x00000019` | `LC_SEGMENT_64` | 72 | `__LINKEDIT`; file 93323264 + 29222592 |
| 5 | `0x80000034` | `LC_DYLD_CHAINED_FIXUPS` | 16 | data 93323264 + 299400 |
| 6 | `0x80000033` | `LC_DYLD_EXPORTS_TRIE` | 16 | data 93622664 + 1272944 |
| 7 | `0x00000002` | `LC_SYMTAB` | 24 | 664035 symbols, 15856832 string bytes |
| 8 | `0x0000000b` | `LC_DYSYMTAB` | 80 |  |
| 9 | `0x0000000e` | `LC_LOAD_DYLINKER` | 32 | `/usr/lib/dyld` |
| 10 | `0x0000001b` | `LC_UUID` | 24 | `6CAF9C5B-1E60-382D-B33C-06521A6AEB0F` |
| 11 | `0x00000032` | `LC_BUILD_VERSION` | 32 | MACOS, minos 13.5.0, sdk 15.0.0, LD 1115.7.3 |
| 12 | `0x0000002a` | `LC_SOURCE_VERSION` | 16 | 0.0.0.0.0 |
| 13 | `0x80000028` | `LC_MAIN` | 24 | entryoff 22138340, stacksize 0 |
| 14 | `0x0000000c` | `LC_LOAD_DYLIB` | 104 | `/System/Library/Frameworks/CoreFoundation.framework/Versions/A/CoreFoundation`; current 3038.1.255, compatibility 150.0.0 |
| 15 | `0x0000000c` | `LC_LOAD_DYLIB` | 96 | `/System/Library/Frameworks/Security.framework/Versions/A/Security`; current 61439.1.1, compatibility 1.0.0 |
| 16 | `0x0000000c` | `LC_LOAD_DYLIB` | 48 | `/usr/lib/libc++.1.dylib`; current 1800.101.0, compatibility 1.0.0 |
| 17 | `0x0000000c` | `LC_LOAD_DYLIB` | 56 | `/usr/lib/libSystem.B.dylib`; current 1351.0.0, compatibility 1.0.0 |
| 18 | `0x00000026` | `LC_FUNCTION_STARTS` | 16 | data 94895608 + 186096 |
| 19 | `0x00000029` | `LC_DATA_IN_CODE` | 16 | data 95081704 + 0 |
| 20 | `0x0000001d` | `LC_CODE_SIGNATURE` | 16 | data 121576496 + 969360 |

### 2.2 The interpreter installation: selection and trees

- **pyvenv.cfg:** `home = <prefix>/opt/python@3.12/bin`, `include-system-site-packages = false`, `version = 3.12.13`, `executable = <prefix>/Cellar/python@3.12/3.12.13/Frameworks/Python.framework/Versions/3.12/bin/python3.12`.
- **Chain from `<worktree>/.venv/bin/python`** (4 hops; `os.path.realpath` agrees):
  - `<worktree>/.venv/bin/python` → `python3.12`
  - `<worktree>/.venv/bin/python3.12` → `<prefix>/opt/python@3.12/bin/python3.12`
  - `<prefix>/opt/python@3.12` → `../Cellar/python@3.12/3.12.13`
  - `<prefix>/Cellar/python@3.12/3.12.13/bin/python3.12` → `../Frameworks/Python.framework/Versions/3.12/bin/python3.12`
  - It ends at `<prefix>/Cellar/python@3.12/3.12.13/Frameworks/Python.framework/Versions/3.12/bin/python3.12`. `home`'s `python3.12` reaches the same launcher through 2 hops, and `executable` through none.
- **Trees:**
  - The framework version directory holds 3,478 files, 305 directories and 5 links, and the `.venv` holds 297 files, 45 directories and 3 links.
  - By leading magic, 79 framework files and 27 `.venv` files are Mach-O. None is fat, 32-bit, big-endian, a Java class file or an `ar` archive, and there is no special file.
- **Framework links:** `Headers` → `include/python3.12`; `lib/libpython3.12.dylib` → `../Python`; `lib/python3.12/config-3.12-darwin/libpython3.12.a` → `../../../Python`; `lib/python3.12/config-3.12-darwin/libpython3.12.dylib` → `../../../Python`; `lib/python3.12/site-packages` → `../../../../../../lib/python3.12/site-packages`.
- **The parser's inventory:**
  - It holds 3,788 and 345 entries, the same as the reader's listing, with the same kinds, link targets and file SHA-256 values.
  - It has 111 closure images, which equal the reader's images and externals, and 6 closure link hops.
  - Its digest is `c277bdd3ac6aa73105df3924707a271a402a0dc7c722be27a6834f2c78605633` (776,209 canonical bytes). The value is identical on a second computation and in run 03, and equals MP's `python_inventory_after_sha256`.

### 2.3 Load-command sequences of the Python images

Abbreviations: SEG `LC_SEGMENT_64`, INFO `LC_DYLD_INFO_ONLY`, FIXUPS `LC_DYLD_CHAINED_FIXUPS`, EXPORTS `LC_DYLD_EXPORTS_TRIE`, ID `LC_ID_DYLIB`, DYLIB `LC_LOAD_DYLIB`, BUILD `LC_BUILD_VERSION`, SRC `LC_SOURCE_VERSION`, FSTARTS `LC_FUNCTION_STARTS`, DIC `LC_DATA_IN_CODE`, CS `LC_CODE_SIGNATURE`. The complete list of every file, with decoded fields, is in the JSON form.

| ID | Images | Commands in order |
| --- | --- | --- |
| S01 | 62 | SEG×4 INFO SYMTAB DYSYMTAB UUID BUILD SRC DYLIB RPATH FSTARTS DIC CS |
| S02 | 11 | SEG×4 INFO SYMTAB DYSYMTAB UUID BUILD SRC DYLIB×2 RPATH FSTARTS DIC CS |
| S03 | 8 | SEG×4 ID INFO SYMTAB DYSYMTAB UUID BUILD SRC DYLIB FSTARTS DIC CS |
| S04 | 8 | SEG×4 ID INFO SYMTAB DYSYMTAB UUID BUILD SRC DYLIB×2 FSTARTS DIC CS |
| S05 | 3 | SEG×4 INFO SYMTAB DYSYMTAB UUID BUILD SRC DYLIB FSTARTS DIC CS |
| S06 | 3 | SEG×4 INFO SYMTAB DYSYMTAB UUID BUILD SRC DYLIB×3 RPATH FSTARTS DIC CS |
| S07 | 2 | SEG×4 INFO SYMTAB DYSYMTAB UUID BUILD SRC DYLIB×2 FSTARTS DIC CS |
| S08 | 2 | SEG×4 ID FIXUPS EXPORTS SYMTAB DYSYMTAB UUID BUILD SRC DYLIB×2 RPATH FSTARTS DIC CS |
| S09 | 1 | SEG×3 ID FIXUPS EXPORTS SYMTAB DYSYMTAB UUID BUILD SRC DYLIB FSTARTS DIC CS |
| S10 | 1 | SEG×4 FIXUPS EXPORTS SYMTAB DYSYMTAB DYLINKER UUID BUILD SRC MAIN DYLIB×3 RPATH FSTARTS DIC CS |
| S11 | 1 | SEG×4 INFO SYMTAB DYSYMTAB UUID BUILD SRC DYLIB×3 FSTARTS DIC CS |
| S12 | 1 | SEG×4 INFO SYMTAB DYSYMTAB UUID BUILD SRC DYLIB×4 FSTARTS DIC CS |
| S13 | 1 | SEG×4 INFO SYMTAB DYSYMTAB UUID BUILD SRC DYLIB×6 FSTARTS DIC CS |
| S14 | 1 | SEG×4 ID FIXUPS EXPORTS SYMTAB DYSYMTAB UUID BUILD SRC DYLIB FSTARTS DIC CS |
| S15 | 1 | SEG×4 ID FIXUPS EXPORTS SYMTAB DYSYMTAB UUID BUILD SRC DYLIB×2 FSTARTS DIC CS |
| S16 | 1 | SEG×4 ID FIXUPS EXPORTS SYMTAB DYSYMTAB UUID BUILD SRC DYLIB RPATH FSTARTS DIC CS |
| S17 | 1 | SEG×4 ID INFO SYMTAB DYSYMTAB UUID BUILD SRC DYLIB FSTARTS DIC CS RPATH |
| S18 | 1 | SEG×4 ID INFO SYMTAB DYSYMTAB UUID BUILD SRC DYLIB×4 FSTARTS DIC CS |
| S19 | 1 | SEG×4 ID INFO SYMTAB DYSYMTAB UUID BUILD SRC DYLIB×6 FSTARTS DIC CS |
| S20 | 1 | SEG×5 FIXUPS EXPORTS SYMTAB DYSYMTAB DYLINKER UUID BUILD SRC MAIN DYLIB×2 FSTARTS DIC CS |

Every image below is thin, cpusubtype `0x00000000` and free of anomalies. The parser reads it with a binding equal to the reader's, and no parsed field differs. Every non-system reference resolves to a bound image, in both readings. System references are in section 2.7.

### 2.4 Framework images (79)

| File | Type | Bytes | SHA-256 | Seq. | LC_ID_DYLIB | LC_RPATH | Non-system references | Reader / parser |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `Python` | DYLIB | 5,984,672 | `81e88e84a74017ba097c0775aef09f9583617923757f7ed3e16c3203a0106337` | S08 | `<prefix>/opt/python@3.12/Frameworks/Python.framework/Versions/3.12/Python` | `<prefix>/lib` |  | accept / accept |
| `Resources/Python.app/Contents/MacOS/Python` | EXECUTE | 51,392 | `2cb7bcb114a9a92ac12d1072406261ac039bed938b25bfc70dd30ec5855a3353` | S10 |  | `<prefix>/lib` | `<prefix>/Cellar/python@3.12/3.12.13/Frameworks/Python.framework/Versions/3.12/Python` | accept / accept |
| `bin/python3.12` | EXECUTE | 52,448 | `31b9c9a8d50289f3a13f014b3efd8ea3534fc3eea7ca7d9809e166139910b805` | S20 |  |  | `<prefix>/Cellar/python@3.12/3.12.13/Frameworks/Python.framework/Versions/3.12/Python` | accept / accept |
| `lib/python3.12/lib-dynload/_asyncio.cpython-312-darwin.so` | BUNDLE | 117,744 | `64c0199a2a01a2468ba0f401bcfc2e8d00cfc409a98191f386ec74034b0bb3fc` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_bisect.cpython-312-darwin.so` | BUNDLE | 70,752 | `72a09f6545d960c7bf9545b9975072b1f733c053de71b3b1af6c44a8c75ee0d6` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_blake2.cpython-312-darwin.so` | BUNDLE | 89,424 | `588cbd119aa469906b4847f806e8de1ae40f28e10417445046dea88493024273` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_bz2.cpython-312-darwin.so` | BUNDLE | 72,880 | `6f68aacca1dd4ce8a9a532d5fa721a88a8ca0db8580fe56d64e7d060d0ff2326` | S02 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_codecs_cn.cpython-312-darwin.so` | BUNDLE | 185,264 | `69ef4180e7fd8fb5d242faf83d3907e2715d077ad04627d03341b7c2ff686329` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_codecs_hk.cpython-312-darwin.so` | BUNDLE | 201,776 | `03e4f370cfae2427dbed0df0dee89a3358826ff2c2296ebc840d66d2d59ab7f7` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_codecs_iso2022.cpython-312-darwin.so` | BUNDLE | 72,016 | `f0121cab5504abeba42e0d4f3d0b77b4b5247ff3e2348303a7fd38f2bac9156c` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_codecs_jp.cpython-312-darwin.so` | BUNDLE | 301,104 | `be25471da45a6f8b2474ea31cdf5fd4c34a44bed704c90eb14e17ebd26613be9` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_codecs_kr.cpython-312-darwin.so` | BUNDLE | 168,928 | `81b39aea963292e01dbe0a6b71a4bfd5d8bec86c20bbac02b0461505350bdf6b` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_codecs_tw.cpython-312-darwin.so` | BUNDLE | 168,432 | `3323b8c75a9cd023df048b4c6def5f5da688bcda152855f38cbb45241c0c9e55` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_contextvars.cpython-312-darwin.so` | BUNDLE | 68,400 | `4d2f40f15d7d0e4ad5df482e9dace1717b4388d73f80e74b0ee311f42c8767ca` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_crypt.cpython-312-darwin.so` | BUNDLE | 68,576 | `d59e73f49fb78dfeeacdfa0789331392e05b4409f94340d55c5393239a59fa2e` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_csv.cpython-312-darwin.so` | BUNDLE | 91,232 | `54e0f1a6ffd99c18fff7e47b9460e3b6b22b4e48424b11ecb78ed3d8af304833` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_ctypes.cpython-312-darwin.so` | BUNDLE | 158,016 | `5f0d8b2b86165514dc643b55d46f8f109dafe2d6d895637d8d5706b704ba40a6` | S02 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_ctypes_test.cpython-312-darwin.so` | BUNDLE | 74,096 | `4dc72d146dd278856f919f236af366b70758ef5ccfa96d0cf8b334029b7a8db6` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_curses.cpython-312-darwin.so` | BUNDLE | 160,336 | `b83bf804f291368fc2f0354ade89fa8379a3222917e8b26492ad7a46df59d00e` | S02 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_curses_panel.cpython-312-darwin.so` | BUNDLE | 73,008 | `fe7cad3a3f2be4af83a61fbc894623139b7873e5543f7c8971e54f79a9ab4849` | S06 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_datetime.cpython-312-darwin.so` | BUNDLE | 133,376 | `f55f2e280ca4254f73df477d59706cca0bafef5529037684a4a89acb1b3ae1f2` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_dbm.cpython-312-darwin.so` | BUNDLE | 71,760 | `1e5bb29232c5a6b5e4f810b9a99458cff7bd9dfaee0e43021ad0ee382bbc5375` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_decimal.cpython-312-darwin.so` | BUNDLE | 193,136 | `49bdf74bc4f9711af5ae8aac51244f5d596bb92b60d54dda7b0ca225713553d2` | S02 |  | `<prefix>/lib` | `<prefix>/opt/mpdecimal/lib/libmpdec.4.dylib` | accept / accept |
| `lib/python3.12/lib-dynload/_elementtree.cpython-312-darwin.so` | BUNDLE | 117,776 | `25810727ef8db1b16b3d8526f519bfbdbce7c625a07ef8ba111db5fc3eebc470` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_hashlib.cpython-312-darwin.so` | BUNDLE | 98,160 | `1d003b2a0f627e3bf7a8360bcaee37fdecbf652acbbdffb13c2f7f1124f2a159` | S02 |  | `<prefix>/lib` | `<prefix>/opt/openssl@3/lib/libcrypto.3.dylib` | accept / accept |
| `lib/python3.12/lib-dynload/_heapq.cpython-312-darwin.so` | BUNDLE | 69,648 | `29641bc5a775e7e2526b4fc6ec72012357b486e4c317afd31ba97646a4d027e1` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_json.cpython-312-darwin.so` | BUNDLE | 90,160 | `e649da3ad002692b75fd6ae713e5fea94230cae745e9259e6e645adf80bf1ee4` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_lsprof.cpython-312-darwin.so` | BUNDLE | 72,608 | `659f0cc69b45d0b9c08498edd504cf2e065ba70a6257d2cba3049a9c13ac4282` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_lzma.cpython-312-darwin.so` | BUNDLE | 92,368 | `fd9892c7f1fa42e33c867e608784a34be38a70f68ce6b29c169d57ce6b8bb8ab` | S02 |  | `<prefix>/lib` | `<prefix>/opt/xz/lib/liblzma.5.dylib` | accept / accept |
| `lib/python3.12/lib-dynload/_md5.cpython-312-darwin.so` | BUNDLE | 71,552 | `2ae2cc1460627ccf0574a42e3a3ec19c8190b81399ae79f42cd9873e13ed4bcf` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_multibytecodec.cpython-312-darwin.so` | BUNDLE | 96,240 | `077f9b29512762a2bac84bf0abf885b794808ea0e4ae7e112765b3da0c64722b` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_multiprocessing.cpython-312-darwin.so` | BUNDLE | 73,632 | `c4c9cfdedacad4c0daaa4f8c339382e37b66a25fa3144ab7e7af3ed0eaf6f1ef` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_opcode.cpython-312-darwin.so` | BUNDLE | 69,056 | `5d593b93ba62d4ff53f39772a4a37e0d6c997c5faee02639a5d1fa20d1336aa3` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_pickle.cpython-312-darwin.so` | BUNDLE | 151,984 | `b4cffc72de77180041a53ffe70475da4cbedc32952504c99bbfd5be31be01fb4` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_posixshmem.cpython-312-darwin.so` | BUNDLE | 69,648 | `ae5ed9d69a58e679e7c36cc7a153994ac3c9f4fd71ae025406c001e5bbfa325a` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_posixsubprocess.cpython-312-darwin.so` | BUNDLE | 72,176 | `f11ebfe8cff5a7b1bf4622e89a92bdf98bc13c8fa712656ac3083e0f26497336` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_queue.cpython-312-darwin.so` | BUNDLE | 72,256 | `0bd7eeb1670e6605072c75de7ee98a59d0af82c152d34a53458a40f245c54a7d` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_random.cpython-312-darwin.so` | BUNDLE | 71,616 | `73ed9bf10a28e9c131cbe8d82b93b8d3f7ed686116f9b84d78fb06eee08f0d60` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_scproxy.cpython-312-darwin.so` | BUNDLE | 71,024 | `d2a868c484d9c75ea42f448814d4ba333bfe095374cd0d08f842253f732dbde5` | S06 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_sha1.cpython-312-darwin.so` | BUNDLE | 71,600 | `9cd63987e8b95a2b11ddf0e18c8250a0513a01d51659bd70890d6b0dc1e2c487` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_sha2.cpython-312-darwin.so` | BUNDLE | 89,552 | `66d3c6a66e4d958095c06625f0e3f6ca90f094db8720c044c9a5bc9a8a2739e8` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_sha3.cpython-312-darwin.so` | BUNDLE | 73,312 | `d88d86653e5712db17de17325f8e42b0e5d86d9e4ca6dcc36776475b4e62973b` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_socket.cpython-312-darwin.so` | BUNDLE | 132,064 | `a6dafd4ac5025b20a50cd0c822858870353b363de35212509f2f372b3fa950ba` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_sqlite3.cpython-312-darwin.so` | BUNDLE | 164,816 | `1aab5bf0db99d0f524612dcc972c8b988c4b481b735719957911e6113565774b` | S02 |  | `<prefix>/lib` | `<prefix>/opt/sqlite/lib/libsqlite3.dylib` | accept / accept |
| `lib/python3.12/lib-dynload/_ssl.cpython-312-darwin.so` | BUNDLE | 219,024 | `46b887674ce976a47aca6f9a88ada084979f55d80470092a1a6d5ad8aa9ff16c` | S06 |  | `<prefix>/lib` | `<prefix>/opt/openssl@3/lib/libssl.3.dylib`<br>`<prefix>/opt/openssl@3/lib/libcrypto.3.dylib` | accept / accept |
| `lib/python3.12/lib-dynload/_statistics.cpython-312-darwin.so` | BUNDLE | 68,592 | `1c30c77d90606c1b289bf21418a05e488a49dadd8429cc236b5d4da00ed2dd6e` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_struct.cpython-312-darwin.so` | BUNDLE | 94,560 | `965d0171939a95b129bfd63b2b912eb983b3abb5c0a2e874fbe338cf76f4acf6` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_testbuffer.cpython-312-darwin.so` | BUNDLE | 91,696 | `60fd6bc787883df6d47dc40a00d2fad2b0ca13480f042353e84e7715bf9c0569` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_testcapi.cpython-312-darwin.so` | BUNDLE | 366,224 | `b2fb9586c48728ae6101b12021869a5c33edd96ffcb29c2b919a980d624cc219` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_testclinic.cpython-312-darwin.so` | BUNDLE | 112,496 | `5131f6cd3b238e1a6343002f528f965bf12f27cba5650f89d9e3d6153efe51d2` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_testimportmultiple.cpython-312-darwin.so` | BUNDLE | 68,032 | `f5729d6a82e2d3e43d131ba986049807d1ecd6b009ffa798c5942fb3c0791bb9` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_testinternalcapi.cpython-312-darwin.so` | BUNDLE | 94,144 | `9cb21ab0a5c05771141b73af05d8b3e4ba903c1ddbc3859682def1296ec2e576` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_testmultiphase.cpython-312-darwin.so` | BUNDLE | 76,816 | `92fa2b8219533ad84eb5cf2116250803b9c959eed6956c30eddd2a0a2fcb2f3f` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_testsinglephase.cpython-312-darwin.so` | BUNDLE | 69,984 | `6e4054842ef630d5fbef42f7de65aae238cf3d8fef23992629bca9dba62d0202` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_uuid.cpython-312-darwin.so` | BUNDLE | 68,352 | `8422973beb9566e9c4f438c1dba1e6b7584473f142a19133d1c9cfd279c4c140` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_xxinterpchannels.cpython-312-darwin.so` | BUNDLE | 74,624 | `128b6f6d384d90b7a5abfc762e844286507f7403db18a03c98399a2e275c9a17` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_xxsubinterpreters.cpython-312-darwin.so` | BUNDLE | 73,632 | `d9250e816e3555e746e7a171f33a5836d9d5828d77a1bd3bdeefaa8da96e6d65` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_xxtestfuzz.cpython-312-darwin.so` | BUNDLE | 70,816 | `a6c3e45d0d03d514fa9baff0f792e91ecc9ec8b54f3a14584c55be35cf104a20` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/_zoneinfo.cpython-312-darwin.so` | BUNDLE | 91,552 | `1d45980dc9c4679a4b3338797c7b795b61e546c381d525ca6db5ff544c0fcf73` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/array.cpython-312-darwin.so` | BUNDLE | 97,008 | `d2049db88f0972c11168c6dc1ac3ffe937ae9d005d9364a6d0df1ef0e220ee05` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/audioop.cpython-312-darwin.so` | BUNDLE | 89,280 | `29114985f4889c2c4244b1d551ef68a97a10d219ddcc6c82fdb02d02335511ba` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/binascii.cpython-312-darwin.so` | BUNDLE | 88,656 | `dfa141063ec1732c914d367cd13034612d6ba06e08160e1f707c4e198a8fbc95` | S02 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/cmath.cpython-312-darwin.so` | BUNDLE | 88,400 | `3bc80c09cfc82c93a0f79832ef512a00175b3a298b71324d76dca0e9e253b0ec` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/fcntl.cpython-312-darwin.so` | BUNDLE | 70,288 | `c4361e802b6d83d7327330353b1797e44195fe8a0b8276c4bba244f00ef559ae` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/grp.cpython-312-darwin.so` | BUNDLE | 70,544 | `7aa78545af026eae97a8f9f7021584142fde8c77eb2edd227c8a0d09a2da3879` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/math.cpython-312-darwin.so` | BUNDLE | 111,424 | `9e66f43574ae40fb361b243c4288c841398999db8198895ec0d06be7f9273a8a` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/mmap.cpython-312-darwin.so` | BUNDLE | 73,248 | `6337d70c1116e0e73163ee819b2de2e2c0fc7c86e9ea89f0c3315fee1449947e` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/nis.cpython-312-darwin.so` | BUNDLE | 70,736 | `003b62af5d52e130bac28c525939f1110252f94f57eef5ccd7ce9e90c955be85` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/pyexpat.cpython-312-darwin.so` | BUNDLE | 99,488 | `b2d3e5e2e8d6d90744dfd530d9e7425e3a2f7357dae3540f91c3281bd1d0eb10` | S02 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/readline.cpython-312-darwin.so` | BUNDLE | 94,848 | `ea44bafdfe563d097c1ea5eb6ae65b9a62c4465d5534970125857dac8aa41c63` | S02 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/resource.cpython-312-darwin.so` | BUNDLE | 70,288 | `44e836b298d1073e65c93b63165d58866813156d97f308d39805922c0eaa026f` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/select.cpython-312-darwin.so` | BUNDLE | 92,512 | `a58a247cdb85710fd0a1da1501e6a02059a99488c68833e308873c169bf18e96` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/syslog.cpython-312-darwin.so` | BUNDLE | 70,352 | `a47841db27f7d7baa79d3ac8b4830deb0e3ead0710f90c637c574002f113188f` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/termios.cpython-312-darwin.so` | BUNDLE | 71,520 | `85d84ccb2b9352c9ca4e6229a37fa37fe0056bf2eb3b94931650a08d5803386a` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/unicodedata.cpython-312-darwin.so` | BUNDLE | 1,174,448 | `a7e24363036e06315aa955aeccf6c4407215908dd439d6a859937cea2b0002f7` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/xxlimited.cpython-312-darwin.so` | BUNDLE | 70,496 | `843b80b9ef06d9edb882b05c7407c2ea33e34f8e2b81a5ac04a320b20e5cfdea` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/xxlimited_35.cpython-312-darwin.so` | BUNDLE | 69,904 | `b101b4ade2df4fe8016d650a9eea3b4312f94edfc99481e5379ca9aac4c21a5c` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/xxsubtype.cpython-312-darwin.so` | BUNDLE | 69,184 | `906e7ec4d633a4373b7f3eb73b28374cb845fb4a0a452ab09dbe7ac532c7529e` | S01 |  | `<prefix>/lib` |  | accept / accept |
| `lib/python3.12/lib-dynload/zlib.cpython-312-darwin.so` | BUNDLE | 93,680 | `2e15ed450b259c8073048cb3fe3bae7b0a650fc82d29caed1a73e1586fd0b6cd` | S02 |  | `<prefix>/lib` |  | accept / accept |

### 2.5 `.venv` images (27)

| File | Type | Bytes | SHA-256 | Seq. | LC_ID_DYLIB | LC_RPATH | Non-system references | Reader / parser |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `lib/python3.12/site-packages/PIL/.dylibs/libXau.6.dylib` | DYLIB | 69,584 | `c30323abc362ae0e5ff8b043e13a179a1bf6a9f76011ffc57195fd43020de535` | S03 | `/DLC/PIL/.dylibs/libXau.6.dylib` |  |  | accept / accept |
| `lib/python3.12/site-packages/PIL/.dylibs/libavif.16.4.2.dylib` | DYLIB | 2,999,136 | `5e27779af8078c5586c045176db72779a09e5f87c6d516373913a6c092b76340` | S03 | `/DLC/PIL/.dylibs/libavif.16.4.2.dylib` |  |  | accept / accept |
| `lib/python3.12/site-packages/PIL/.dylibs/libbrotlicommon.1.2.0.dylib` | DYLIB | 183,712 | `3f4843c17f3cccc986279a4c9ac8a11dc3077c412fd856d1bad8231bf027a25f` | S03 | `/DLC/PIL/.dylibs/libbrotlicommon.1.2.0.dylib` |  |  | accept / accept |
| `lib/python3.12/site-packages/PIL/.dylibs/libbrotlidec.1.2.0.dylib` | DYLIB | 104,080 | `351fa4a2f4faed4147dfead81a8b0f5500ada31db64f74c8368bc1ab894f0dd1` | S04 | `/DLC/PIL/.dylibs/libbrotlidec.1.2.0.dylib` |  | `@loader_path/libbrotlicommon.1.2.0.dylib` | accept / accept |
| `lib/python3.12/site-packages/PIL/.dylibs/libfreetype.6.dylib` | DYLIB | 769,872 | `b1e5b0bd6f696d9458bbd370c1417f8b1a6bb6953c26c4c0543750f96ec32c33` | S19 | `/DLC/PIL/.dylibs/libfreetype.6.dylib` |  | `@loader_path/libpng16.16.dylib`<br>`@loader_path/libz.1.3.1.zlib-ng.dylib`<br>`@loader_path/libharfbuzz.0.dylib`<br>`@loader_path/libbrotlidec.1.2.0.dylib` | accept / accept |
| `lib/python3.12/site-packages/PIL/.dylibs/libharfbuzz.0.dylib` | DYLIB | 1,625,248 | `2c88b14217bd5c823d615282dc79b860c79b7d066ddae72ad4d10e0ecca8bcb5` | S04 | `/DLC/PIL/.dylibs/libharfbuzz.0.dylib` |  | `@loader_path/libfreetype.6.dylib` | accept / accept |
| `lib/python3.12/site-packages/PIL/.dylibs/libjpeg.62.4.0.dylib` | DYLIB | 701,120 | `172444d18ef193c128e3f9f4323e9d22b0d824b8172a1389ecd048b279280629` | S17 | `/DLC/PIL/.dylibs/libjpeg.62.4.0.dylib` | `/Users/runner/work/Pillow/Pillow/build/deps/darwin/lib` |  | accept / accept |
| `lib/python3.12/site-packages/PIL/.dylibs/liblcms2.2.dylib` | DYLIB | 421,168 | `188685d4468afb124af58f471fb2382f94b98ef560995bc910eefab50134e8fb` | S03 | `/DLC/PIL/.dylibs/liblcms2.2.dylib` |  |  | accept / accept |
| `lib/python3.12/site-packages/PIL/.dylibs/liblzma.5.dylib` | DYLIB | 216,944 | `f08e18e2363a8e4fc8099de9c8b0b96b30a6a2e4a60e890f2cebb1a9e25a92fa` | S03 | `/DLC/PIL/.dylibs/liblzma.5.dylib` |  |  | accept / accept |
| `lib/python3.12/site-packages/PIL/.dylibs/libopenjp2.2.5.4.dylib` | DYLIB | 430,576 | `2af52733d40803561752e12d6e917a5e16932a1fb7426760a2e6d8c10989c47a` | S03 | `/DLC/PIL/.dylibs/libopenjp2.2.5.4.dylib` |  |  | accept / accept |
| `lib/python3.12/site-packages/PIL/.dylibs/libpng16.16.dylib` | DYLIB | 257,296 | `4777ff2529c03d4181470fb9afa10081d36153055c2989aa16bb15d6b513e772` | S04 | `/DLC/PIL/.dylibs/libpng16.16.dylib` |  | `@loader_path/libz.1.3.1.zlib-ng.dylib` | accept / accept |
| `lib/python3.12/site-packages/PIL/.dylibs/libsharpyuv.0.dylib` | DYLIB | 85,856 | `6b2d464413fc35783c79936f1e6be631585448a37765cf79c238be2ea5e5505b` | S03 | `/DLC/PIL/.dylibs/libsharpyuv.0.dylib` |  |  | accept / accept |
| `lib/python3.12/site-packages/PIL/.dylibs/libtiff.6.dylib` | DYLIB | 572,544 | `d17ccc4d89a37c1db72aca63fdf26b2f07eaaeb737a5232a337585e3c920b3ed` | S18 | `/DLC/PIL/.dylibs/libtiff.6.dylib` |  | `@loader_path/liblzma.5.dylib`<br>`@loader_path/libjpeg.62.4.0.dylib`<br>`@loader_path/libz.1.3.1.zlib-ng.dylib` | accept / accept |
| `lib/python3.12/site-packages/PIL/.dylibs/libwebp.7.dylib` | DYLIB | 512,672 | `0a2ba0179e6bcc1bccc1a88c38b7d8efd0302d45a1bfc1eb4cf1f1f03ede73f0` | S04 | `/DLC/PIL/.dylibs/libwebp.7.dylib` |  | `@loader_path/libsharpyuv.0.dylib` | accept / accept |
| `lib/python3.12/site-packages/PIL/.dylibs/libwebpdemux.2.dylib` | DYLIB | 69,616 | `f5ec6b6750ee91ff032ba62b18afc5f37c7bc842bfc9b2d325df41bc656ea066` | S04 | `/DLC/PIL/.dylibs/libwebpdemux.2.dylib` |  | `@loader_path/libwebp.7.dylib` | accept / accept |
| `lib/python3.12/site-packages/PIL/.dylibs/libwebpmux.3.dylib` | DYLIB | 105,792 | `f9c291035190c3af29494ce9fb62987c25ee78c4365c92c323ccc5ec8740143d` | S04 | `/DLC/PIL/.dylibs/libwebpmux.3.dylib` |  | `@loader_path/libwebp.7.dylib` | accept / accept |
| `lib/python3.12/site-packages/PIL/.dylibs/libxcb.1.1.0.dylib` | DYLIB | 193,760 | `125bcffc8971652784b6a8b4061501f891aeafdf361aa4b777ba3bacc548bc84` | S04 | `/DLC/PIL/.dylibs/libxcb.1.1.0.dylib` |  | `@loader_path/libXau.6.dylib` | accept / accept |
| `lib/python3.12/site-packages/PIL/.dylibs/libz.1.3.1.zlib-ng.dylib` | DYLIB | 176,320 | `39ffbe6a87460a579cf414c3ee668e449b32c2cdc2cc0b64921d53fd59cb56ed` | S03 | `/DLC/PIL/.dylibs/libz.1.3.1.zlib-ng.dylib` |  |  | accept / accept |
| `lib/python3.12/site-packages/PIL/_avif.cpython-312-darwin.so` | BUNDLE | 73,680 | `e8a87d29c9ea3e81527efb1818ab7b6ead5bed54e4c2664c73e47f67746fd5f8` | S07 |  |  | `@loader_path/.dylibs/libavif.16.4.2.dylib` | accept / accept |
| `lib/python3.12/site-packages/PIL/_imaging.cpython-312-darwin.so` | BUNDLE | 634,480 | `058a696be42c06bf77d5efd929c13f734a5e1a0c0a9e4b3e684ee5af13b4aa8f` | S13 |  |  | `@loader_path/.dylibs/libtiff.6.dylib`<br>`@loader_path/.dylibs/libjpeg.62.4.0.dylib`<br>`@loader_path/.dylibs/libopenjp2.2.5.4.dylib`<br>`@loader_path/.dylibs/libz.1.3.1.zlib-ng.dylib`<br>`@loader_path/.dylibs/libxcb.1.1.0.dylib` | accept / accept |
| `lib/python3.12/site-packages/PIL/_imagingcms.cpython-312-darwin.so` | BUNDLE | 97,856 | `c940dbd46ca213366037fd958d11678497a5cd41971fc54126ac37baad396a81` | S07 |  |  | `@loader_path/.dylibs/liblcms2.2.dylib` | accept / accept |
| `lib/python3.12/site-packages/PIL/_imagingft.cpython-312-darwin.so` | BUNDLE | 117,344 | `bbd5e4c25140c7c3b476e14ee613457c55da2694029e9a4b0805ed6711fdfd2c` | S11 |  |  | `@loader_path/.dylibs/libfreetype.6.dylib`<br>`@loader_path/.dylibs/libharfbuzz.0.dylib` | accept / accept |
| `lib/python3.12/site-packages/PIL/_imagingmath.cpython-312-darwin.so` | BUNDLE | 72,160 | `3209a70da6bb99bc9f2dc4d98d168baae82440a5062e91a19acccf6c2b653ff6` | S05 |  |  |  | accept / accept |
| `lib/python3.12/site-packages/PIL/_imagingmorph.cpython-312-darwin.so` | BUNDLE | 51,472 | `0237c1c8ca6ab8ad087d8c6cc929d8cfbd49396491b990503e47963f616a021d` | S05 |  |  |  | accept / accept |
| `lib/python3.12/site-packages/PIL/_imagingtk.cpython-312-darwin.so` | BUNDLE | 52,784 | `1e11150b6f16eae297ea7da2193fa66ff4597d85db9e5d60c7238f190c5dd745` | S05 |  |  |  | accept / accept |
| `lib/python3.12/site-packages/PIL/_webp.cpython-312-darwin.so` | BUNDLE | 75,760 | `3c4c8cb49c955900e361ca1bcaf44f8863ffa9edb9f7b3372e15e8938a053320` | S12 |  |  | `@loader_path/.dylibs/libwebp.7.dylib`<br>`@loader_path/.dylibs/libwebpmux.3.dylib`<br>`@loader_path/.dylibs/libwebpdemux.2.dylib` | accept / accept |
| `lib/python3.12/site-packages/rpds/rpds.cpython-312-darwin.so` | DYLIB | 914,320 | `ead037f2e1a72fa09eb8d7f9d399fadde2a8ead83589f10d94a770739c40e341` | S04 | `@rpath/rpds.cpython-312-darwin.so` |  |  | accept / accept |

### 2.6 External dependencies (5)

| File | Type | Bytes | SHA-256 | Seq. | LC_ID_DYLIB | LC_RPATH | Non-system references | Reader / parser |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `<prefix>/Cellar/mpdecimal/4.0.1/lib/libmpdec.4.0.1.dylib` | DYLIB | 188,176 | `14286ba02244c25537b3b5c74902c5fa81959d5d2c1fcf06f89808badb67dea8` | S16 | `<prefix>/opt/mpdecimal/lib/libmpdec.4.dylib` | `@loader_path/../lib` |  | accept / accept |
| `<prefix>/Cellar/openssl@3/3.6.4/lib/libcrypto.3.dylib` | DYLIB | 4,872,736 | `bae675614cd791d37ec35416ea9f87edcc85407d020810504cf458119b63522c` | S14 | `<prefix>/opt/openssl@3/lib/libcrypto.3.dylib` |  |  | accept / accept |
| `<prefix>/Cellar/openssl@3/3.6.4/lib/libssl.3.dylib` | DYLIB | 888,928 | `c6ee373222087cf31bc2f3817537d268b3c23e56b7fadd44bbf5c2317caed349` | S15 | `<prefix>/opt/openssl@3/lib/libssl.3.dylib` |  | `<prefix>/Cellar/openssl@3/3.6.4/lib/libcrypto.3.dylib` | accept / accept |
| `<prefix>/Cellar/sqlite/3.53.4/lib/libsqlite3.3.53.4.dylib` | DYLIB | 1,276,320 | `6b8bb64feced74cd0766990ad5e089566be6fec655a6c96d4cc1358325afb35a` | S08 | `<prefix>/opt/sqlite/lib/libsqlite3.dylib` | `<prefix>/Cellar/sqlite/3.53.4/lib` |  | accept / accept |
| `<prefix>/Cellar/xz/5.8.4/lib/liblzma.5.dylib` | DYLIB | 167,520 | `41cdf225f3e10fb54f952c8eca11c8a847d095470540dc42736ae7bd761beaa4` | S09 | `<prefix>/opt/xz/lib/liblzma.5.dylib` |  |  | accept / accept |

The closure records six link hops:

- `<prefix>/Cellar/mpdecimal/4.0.1/lib/libmpdec.4.dylib` → `libmpdec.4.0.1.dylib`
- `<prefix>/Cellar/sqlite/3.53.4/lib/libsqlite3.dylib` → `libsqlite3.3.53.4.dylib`
- `<prefix>/opt/mpdecimal` → `../Cellar/mpdecimal/4.0.1`
- `<prefix>/opt/openssl@3` → `../Cellar/openssl@3/3.6.4`
- `<prefix>/opt/sqlite` → `../Cellar/sqlite/3.53.4`
- `<prefix>/opt/xz` → `../Cellar/xz/5.8.4`

The external libraries' own references:

- `libmpdec.4.0.1.dylib`: `/usr/lib/libSystem.B.dylib`
- `libcrypto.3.dylib`: `/usr/lib/libSystem.B.dylib`
- `libssl.3.dylib`: `<prefix>/Cellar/openssl@3/3.6.4/lib/libcrypto.3.dylib`, `/usr/lib/libSystem.B.dylib`
- `libsqlite3.3.53.4.dylib`: `/usr/lib/libz.1.dylib`, `/usr/lib/libSystem.B.dylib`
- `liblzma.5.dylib`: `/usr/lib/libSystem.B.dylib`

### 2.7 System references

| Path | Referencing images | Node | On disk | In the cache's image table |
| --- | --- | --- | --- | --- |
| `/System/Library/Frameworks/CoreFoundation.framework/Versions/A/CoreFoundation` | 4 | yes | no | yes |
| `/System/Library/Frameworks/Security.framework/Versions/A/Security` | 1 | yes | no | yes |
| `/System/Library/Frameworks/SystemConfiguration.framework/Versions/A/SystemConfiguration` | 1 |  | no | yes |
| `/usr/lib/libSystem.B.dylib` | 112 | yes | no | yes |
| `/usr/lib/libbz2.1.0.dylib` | 2 |  | no | yes |
| `/usr/lib/libc++.1.dylib` | 1 | yes | no | yes |
| `/usr/lib/libedit.3.dylib` | 1 |  | no | yes |
| `/usr/lib/libexpat.1.dylib` | 1 |  | no | yes |
| `/usr/lib/libffi.dylib` | 1 |  | no | yes |
| `/usr/lib/libiconv.2.dylib` | 1 |  | no | yes |
| `/usr/lib/libncurses.5.4.dylib` | 2 |  | no | yes |
| `/usr/lib/libpanel.5.4.dylib` | 1 |  | no | yes |
| `/usr/lib/libz.1.dylib` | 3 |  | no | yes |

### 2.8 The dyld shared cache and the dynamic linker

| Property | Value |
| --- | --- |
| Main cache file | `/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/dyld_shared_cache_arm64e` |
| SHA-256, size | `7a024959c8c14d46e2964f975f2256b3f9efc2da950a31067d26ac7ac16498d4`, 573,440 bytes |
| Header | magic `dyld_v1  arm64e`, UUID `F2E86C53-6052-388B-BA71-5A0C9B569413`, platform 1, osVersion 26.6.0 |
| Images, subcaches | 3,649 images (from `imagesOffset/imagesCount`), 12 subcaches |
| dyld in the cache | header `dyldInCacheMH` `0x180114000`; `/usr/lib/dyld` in the image table: yes |
| `/usr/lib/dyld` on disk | `373fce2b3689c2113d5341a6bba735e9f970401ba64896c0a6379680192f1cdf`, 2,562,000 bytes, fat: CPU_TYPE_X86_64 `0x00000003` MH_DYLINKER, CPU_TYPE_ARM64 `0x80000002` MH_DYLINKER |

### 2.9 The developer tools' Git (supplementary, for question (d))

`/Library/Developer/CommandLineTools/usr/bin/git`: SHA-256 `be4afb2b003904725826250de9fb76567bbacf82323457b5a1ec26706b66bcae`, 7,604,272 bytes, fat.

| Slice | cpusubtype | Type | Commands | Dylibs (all cache images, none on disk) | LC_RPATH |
| --- | --- | --- | --- | --- | --- |
| CPU_TYPE_X86_64 | `0x00000003` | MH_EXECUTE | 22 | `/System/Library/Frameworks/CoreServices.framework/Versions/A/CoreServices`<br>`/usr/lib/libz.1.dylib`<br>`/usr/lib/libiconv.2.dylib`<br>`/usr/lib/libSystem.B.dylib`<br>`/System/Library/Frameworks/CoreFoundation.framework/Versions/A/CoreFoundation` | none |
| CPU_TYPE_ARM64 | `0x00000000` | MH_EXECUTE | 22 | `/System/Library/Frameworks/CoreServices.framework/Versions/A/CoreServices`<br>`/usr/lib/libz.1.dylib`<br>`/usr/lib/libiconv.2.dylib`<br>`/usr/lib/libSystem.B.dylib`<br>`/System/Library/Frameworks/CoreFoundation.framework/Versions/A/CoreFoundation` | none |

The parser classifies the file as `fat`, and `_macho_extent` refuses it (`MACHO-FAT`). Its arm64 slice embeds `2.50.1 (Apple Git-155)` and `git version %s`, so the predicted line is `git version 2.50.1 (Apple Git-155)\n`; it matches `GIT_VERSION_LINE` (a static prediction; no start).

## 3. Answers

### (a) Does every file meet the contract's rules (thin 64-bit arm64, file type, the closed allow-list, LC_LOAD_DYLINKER /usr/lib/dyld, dylibs only under /usr/lib/ or /System/Library/; any LC_RPATH, LC_DYLD_ENVIRONMENT, upward or re-export dylib, @-relative path or unknown command refuses), and do the Python images meet section 4 as amended?

**Yes, both.**

- **bin/node, section 7.** It is thin, `MH_MAGIC_64`, `CPU_TYPE_ARM64`, cpusubtype `0x00000000` and `MH_EXECUTE`. Its 21 commands are of 14 kinds, all inside the 16-command allow-list: `LC_SEGMENT_64` ×5, `LC_DYLD_CHAINED_FIXUPS`, `LC_DYLD_EXPORTS_TRIE`, `LC_SYMTAB`, `LC_DYSYMTAB`, `LC_LOAD_DYLINKER`, `LC_UUID`, `LC_BUILD_VERSION`, `LC_SOURCE_VERSION`, `LC_MAIN`, `LC_LOAD_DYLIB` ×4, `LC_FUNCTION_STARTS`, `LC_DATA_IN_CODE` and `LC_CODE_SIGNATURE`. The two kinds it does not use are `LC_LOAD_WEAK_DYLIB` and `LC_DYLD_INFO_ONLY`. `LC_LOAD_DYLINKER` is `/usr/lib/dyld`. The four dylibs are CoreFoundation, Security, `/usr/lib/libc++.1.dylib` and `/usr/lib/libSystem.B.dylib`, all normalized absolute paths under `/System/Library/` or `/usr/lib/`. No `LC_RPATH`, `LC_DYLD_ENVIRONMENT`, upward, re-export, weak or lazy dylib, no `@` path and no unknown command occurs. There are no structural anomalies.
- **Python images, section 4** (unchanged by the amendment, whose 17 replaced clauses concern only the supervisor, MC14, MC37 to MC39, the labels and trust assumption 2). All 111 images are thin `MH_MAGIC_64` arm64 with cpusubtype 0. Their file types are `MH_EXECUTE` (2: `bin/python3.12` and `Resources/Python.app/Contents/MacOS/Python`), `MH_DYLIB` (25) and `MH_BUNDLE` (84). Every command is of a kind in Node's allow-list, or `LC_ID_DYLIB` (25 times) or `LC_RPATH` (81 times). None carries `LC_DYLD_ENVIRONMENT`, `LC_LOAD_UPWARD_DYLIB`, `LC_REEXPORT_DYLIB`, `LC_LAZY_LOAD_DYLIB` or an unknown command. Both executables name `/usr/lib/dyld`.
- **Python references.** There are 162, all `LC_LOAD_DYLIB` (no weak reference):
  - 127 system references to 11 distinct paths (13 with Node's two others);
  - 9 absolute non-system references: the launcher and the process image name the framework's `Python` library by its `<prefix>/Cellar/…` path, the lib-dynload modules name five external libraries through `<prefix>/opt/…` links, and libssl names libcrypto by its versioned path. Each resolves to a bound regular file;
  - 26 `@loader_path` references, all from Pillow's 8 extension modules and its bundled `.dylibs`. Each resolves to a bound image in the `.venv`;
  - 0 `@rpath`, 0 `@executable_path` and 0 other `@` forms.
- **`LC_RPATH`.** The 81 entries are `<prefix>/lib` (78), the sqlite library's own lib directory, libmpdec's `@loader_path/../lib` (resolved as a directory from both of its spellings), and an absent build-machine path in Pillow's libjpeg (N-06). Every entry is recorded.
- **Contrast.** Node's own rules would refuse every Python image: 109 by file type, and both executables because of a non-system reference, with an `LC_RPATH` in the process image. That is why section 4 has rules of its own.

### (b) D-16: does bin/node link CoreFoundation, and how?

**Yes, by a plain LC_LOAD_DYLIB.**

- Command 14, at file offset 2,096, is `cmd 0x0000000c`: `LC_LOAD_DYLIB`, not `LC_LOAD_WEAK_DYLIB` `0x80000018` and not a lazy, upward or re-export command. Its cmdsize is 104, its name offset 24 and its timestamp 2. It names `/System/Library/Frameworks/CoreFoundation.framework/Versions/A/CoreFoundation`, current version 3038.1.255 and compatibility version 150.0.0. It is the first of the four dylib commands.
- The path does not exist on disk. It is an image of the cryptex's dyld shared cache (UUID `F2E86C53-6052-388B-BA71-5A0C9B569413`).
- The parser's own parse gives the same command, and `check_node_macho` returns it as the first reference. HOST's `runtime.macho` will therefore carry it.
- dyld must load CoreFoundation and run its initializers before `main`, and a failed load stops the start.
- Under D-16 and MH-PLAN section 6, MC36 stands as written. The load command does not show that `__CF_USER_TEXT_ENCODING` then appears in the probe's `process.env` (N-04).

### (c) W3's Q3: is every cpusubtype CPU_SUBTYPE_ARM64_ALL? Is any file arm64e or fat?

**Every bound file is CPU_SUBTYPE_ARM64_ALL, and none is arm64e or fat.**

- All 112 files have cputype `0x0100000c` and raw cpusubtype `0x00000000`: subtype value 0 and capability bits (mask `0xff000000`) 0. These are `bin/node`, the 79 framework images, the 27 `.venv` images and the 5 external dylibs. None is `CPU_SUBTYPE_ARM64E` (2) or `CPU_SUBTYPE_ARM64_V8` (1), and none has `CPU_SUBTYPE_PTRAUTH_ABI`.
- None is fat. This Python framework build is thin arm64, not universal2. No file in either tree begins with a fat magic, a Java class magic or an `ar` archive magic.
- The only fat files met lie outside the parsed set:
  - the developer tools' Git: x86_64 subtype 3 and arm64 subtype 0;
  - `/usr/lib/dyld`: x86_64 subtype 3 and arm64 subtype `0x80000002`, that is arm64e with `CPU_SUBTYPE_PTRAUTH_ABI`.
- The parser's rule, exactly 0, accepts every bound file. In-memory cases N06 to N09 confirm that it refuses subtypes 1, 2, `0x80000000` and `0x80000002`.

### (d) W3's open questions checked against the real files: fat files refused; @rpath stricter than dyld; MH_OBJECT refused; the Git version checked by grammar only.

**None of them refuses a real file, and each outcome is correct under the contract.**

- **Fat files (Q1).** No bound file is fat, so the rule refuses nothing here. For Node the rule is the contract's ("thin"). For Python images it is an implementation rule, since section 4 does not say thin (N-05). It fails closed. The developer tools' Git is fat, but M0 binds Git by bytes and never parses it. `_macho_extent` on Git's first bytes returns `MACHO-FAT`, which confirms W3's F3. This is correct: the contract sets no Mach-O rule for Git.
- **`@rpath` stricter than dyld (Q4).** No bound image carries an `@rpath` reference, so the rule is never exercised. Neither are the related rules on weak references and leaf names. The real files are accepted.
  - The 81 `LC_RPATH` entries take no part in load-time resolution. The parser records their state, fail closed (N-06).
  - rpds's `LC_ID_DYLIB` is `@rpath/rpds.cpython-312-darwin.so`. That is an install name, not a reference, and section 4 sets no rule for it (N-01 (d)).
  - The rule is correct under section 4's "by dyld's rules with the recorded rpaths" as a stricter subset. N-01 (b) notes the one case in which a subset rule could bind another file than dyld loads. It does not occur here.
- **`MH_OBJECT` (Q5).** No file in either tree is `MH_OBJECT`. `config-3.12-darwin/` holds no `python.o`, and its `libpython3.12.a` and `libpython3.12.dylib` are links to the framework's `Python`. There is no `ar` archive. Nothing is refused. The rule follows section 4's accepted types, so it is correct.
- **Git version by grammar (Q6).** This is not a Mach-O rule. The contract binds Git by path and SHA-256 and states no expected version, and the pinned bytes determine the version.
  - The developer tools' Git embeds `2.50.1 (Apple Git-155)` and the format `git version %s` in its arm64 slice. One `--version` start should therefore print `git version 2.50.1 (Apple Git-155)\n`, which `GIT_VERSION_LINE` admits. This is a static prediction: no Git was started.
  - The grammar-only check is correct under the contract. Both of that Git's slices reference only five system libraries, all images of the cache, so E18's premise holds for that file (N-07).

### (e) Does the parser's source decide each rule as the contract says (bounds checks, truncated or overlapping commands, cmdsize alignment, LC_REQ_DYLD bits, string offsets, any command skipped without checking)?

**Yes. It decides every contract rule as the contract states. It adds stricter rules (N-05), and its reference resolution has edge cases (N-01) that do not arise here. Some recorded properties are not decided (N-02).**

- **Header** (`_macho_extent`, lines 733–741; `parse_macho`, 825–849):
  - Only `cf fa ed fe` passes. The four fat magics give `MACHO-FAT`; the 32-bit and big-endian magics give `MACHO-MAGIC`.
  - At least 32 bytes are present before any unpack.
  - cputype and cpusubtype must match exactly.
  - 0 < ncmds ≤ 4096, 0 < sizeofcmds ≤ 4 MiB, and 32 + sizeofcmds ≤ the file size.
- **Command table:**
  - Each command header lies inside the table; cmdsize is at least 8, a multiple of 8 (the 64-bit rule) and inside the table.
  - The sizes must add up to sizeofcmds exactly. Commands are read in sequence, so they cannot overlap, and a truncated, short or padded table refuses (N11 to N21).
  - The parsed bytes are the hash-bound bytes. `read_macho` takes them from the same read that computes the digest, and reads again with a binding comparison when the table exceeds 64 KiB.
- **`LC_REQ_DYLD`:** names map from full 32-bit values (lines 195–212). A known code with a missing or an extra `LC_REQ_DYLD` bit is unknown and refuses (N36, N37, N44, N47). The table equals the reader's independent table for 0x1 to 0x36.
- **Strings** (`_lc_string`, 748–756): the offset must lie at or after the fixed structure and inside the command; the NUL must lie inside the command; the string must be non-empty and printable ASCII (N22 to N26).
- **Per-command structure:** every command that either rule set can accept is size-checked and range-checked:
  - `LC_SEGMENT_64`: exactly 72 + 80·nsects, and the file range inside the file;
  - `LC_SYMTAB`: symbol and string ranges;
  - `LC_DYSYMTAB`: size only;
  - `LC_UUID`, `LC_SOURCE_VERSION` and `LC_MAIN`: exact sizes; the entry offset inside the file;
  - `LC_BUILD_VERSION`: exactly 24 + 8·ntools;
  - the linkedit-data commands and `LC_DYLD_INFO_ONLY`: exact sizes and ranges;
  - the dylib, dylinker and rpath commands: the string checks above.
- **Skipped commands:** unknown commands, and known commands outside both allow-lists, are recorded undecoded (`name` null, or the name alone). Both rule sets refuse every such command, so no command is accepted unchecked (N39 to N49, P12 to P16).
- **Rules against the contract:**
  - The parser's Node allow-list, its refused list and its Python additions and file types equal CONTRACT.json's lists exactly.
  - `check_node_macho` (884–901) refuses the four named commands and anything outside the 16, requires `/usr/lib/dyld`, refuses any `@` in a dylib reference, and requires a normalized absolute path under the two prefixes. All other path-carrying commands are outside the list.
  - `check_python_macho` (911–951) and `_closure_pass` (1209–1299) apply section 4: the three file types; the allow-list plus `LC_ID_DYLIB` and `LC_RPATH`; refusal of `LC_DYLD_ENVIRONMENT`, `LC_LOAD_UPWARD_DYLIB`, other `@` forms and unknown commands; `@`-relative `LC_RPATH` entries resolved as directories; and every non-system reference resolved to a bound image, with the link hops recorded.
- **Mutation cases:** 64 Node cases and 17 Python cases on the real header bytes, in memory, all with the predicted outcome (section 5). N58 to N63 show the undecided properties of N-02.

### (f) Does the closure claim hold for these files within its stated limits, and what does it not cover?

**It holds for these files. Its limits are as stated, plus the items listed here.**

- **Node:** the bytes are bound (SHA-256 `6f320694…`, 122,545,856 bytes, `0o755`, one link) and equal the NODE-SOURCE.json pin. All 21 load commands were read. Its four dependencies are system paths that do not exist on disk and are images of the cache.
- **Interpreter installation:** the inventory (digest `c277bdd3…`, 776,209 canonical bytes) binds:
  - 3,478 + 297 files, 305 + 45 directories and 5 + 3 links;
  - the 4-hop selection chain and pyvenv.cfg's `home`;
  - 111 images, among them the 5 external dylibs, and 6 closure link hops.
- All 35 non-system references resolve to bound images. The 11 distinct system paths of the Python images are absent from disk and present in the cache's image table.
- **System side:** the cache is the cryptex's `dyld_shared_cache_arm64e`: header magic `dyld_v1  arm64e`, osVersion 26.6.0, 3,649 images and 12 subcaches. The OS identity is macOS 26.6.2 (25G83), and the system and cryptex SystemVersion.plist files are byte-identical. The limits stated in sections 7 and 12 hold: the cache images are identified by OS identity, not by per-file hashes, and the SSV, SIP and the cryptex delivery are assumed, not verified.
- **Not covered by the claim, beyond its stated limits:**
  - the per-file identity of the cache images and of the dynamic linker `/usr/lib/dyld`. dyld is an on-disk system-volume file that is also a cache image; the claim does not name it, and HOST does not record the cache UUID (N-03);
  - whether a reference under `/usr/lib/` or `/System/Library/` is a cache image at all: the prefix rule does not ensure it, and seven `/System/Library` subtrees are firmlinked to the data volume (N-03);
  - code signatures. `LC_CODE_SIGNATURE` is range-checked only. Validity and AMFI enforcement are runtime behaviour;
  - run-time loads by the libraries' own logic: OpenSSL's providers, engines and configuration; CoreFoundation's and Security's plug-ins; libuv's `dlopen` for file-system events in Node; ctypes in Python; `dlopen("@rpath/…")` searches through the recorded rpaths, including `<prefix>/lib` from the process image (N-06);
  - dyld's default fallback directories (`/usr/local/lib`, `/usr/lib`) for a dependency that disappears between the last recheck and a load. That is the time-of-use limit of any static binding; MC29 detects the change afterwards;
  - files that are not Mach-O and are read at run time outside the trees: zoneinfo, locale data, `~/.CFUserTextEncoding`, OpenSSL's configuration;
  - the base installation's global site-packages, the target of the framework's `lib/python3.12/site-packages` link. It is recorded as a link target only. It is not on `sys.path` under `-I -S`, and it is excluded in the venv by `include-system-site-packages = false`;
  - symbol binding at run time. Extension modules resolve Python's API by dynamic lookup in already-loaded images, and interposition is runtime behaviour;
  - Git's dependencies. They lie outside the parser, and this review checked them statically for the developer tools' Git only (N-07).

### (g) Would the parser accept or refuse the real files? If it would refuse, why, and is the cause the parser, the contract or the files?

**It accepts them. No cause of refusal exists in the parser, the contract or the files.**

- **Node.** `read_macho` with the NODE-SOURCE pin and `private=True`, then `check_node_macho`, as `check_runtime` calls them: accepted.
- **Images.** `check_python_macho` on each of the 111 images: accepted.
- **Inventory.** `python_inventory(<worktree>/.venv, <framework version directory>)`: accepted, digest `c277bdd3ac6aa73105df3924707a271a402a0dc7c722be27a6834f2c78605633`. A second computation, and run 03 after all other work, give the same digest and no `compare_inventory` difference. The digest equals MP's `python_inventory_after_sha256`.
- **Packages.** `verify_packages` finds exactly the seven pins, with every RECORD row verified.
- **Launcher.** `check_launcher` accepts this review's own `-I -S -B` process, started as `<worktree>/.venv/bin/python`: process image `Resources/Python.app/Contents/MacOS/Python`, `sys.path` inside the framework.
- So M0 would not fail on this host for any Mach-O or Python-installation reason, as the files stand on 2026-11-26.
- **What would make it refuse later.** Each of these is a change of state, not a defect in the parser, the contract or the files:
  - a start of the framework interpreter that writes bytecode (N-09, MC32);
  - a retargeted `<prefix>/opt` link or a changed external library;
  - the creation of `/Users/runner` (N-06);
  - an OS update.

## 4. Findings

All nine are nonmandatory: none blocks adopting an execution plan.

### N-01 (nonmandatory): Reference resolution: edge cases in which the bound file and dyld's could differ

- **Location:** current_host_observation_v02.py `_closure_pass` (lines 1209–1299: 1227, 1247, 1260), `_search_directory` (1177–1189), `check_python_macho` (911–951)
- **Issue:**
  - (a) For an `@loader_path` reference, the parser checks every spelling of the loader, but records only the lexicographically first resulting spelling of the target (`sorted(outcomes.items())[0]`, line 1260). A target reached through several loader spellings has its own `@loader_path` references checked from its canonical directory and that one spelling only.
  - (b) For `@rpath`, the parser selects the first candidate that exists (line 1247). dyld skips a candidate that exists but does not load, and goes on to the next one, which the parser never bound. Examples are a file built for another platform or a newer OS, a file that is not a dylib, and a file whose signature is invalid.
  - (c) `@executable_path` in a non-executable image is resolved against the process image's directory (line 1227). Before the launcher re-executes, dyld resolves it against the launcher's directory.
  - (d) No rule applies to `LC_ID_DYLIB` values; rpds's is `@rpath/rpds.cpython-312-darwin.so`. dyld can treat an already-loaded image whose install name matches a requested path as that dependency.
- **Effect on the real files:** None of these arises in the real files:
  - no bound image has an `@rpath` or `@executable_path` reference;
  - each of the 26 `@loader_path` references comes from an image with a single spelling;
  - the launcher's only non-system reference is absolute;
  - no install name equals a reference that resolves to another file, and no install name is a cache path. The reader's collision check finds only the five externals' own names, each resolving to the same file.
- **Recommendation:** Not needed for this host's plan. If a later plan binds a tree with `@rpath` references, symlinked Mach-O files or several rpaths, the implementation should first:
  - record every spelling;
  - refuse when an earlier existing candidate is not a loadable image of the accepted type;
  - check every install name against every reference.

### N-02 (nonmandatory): Structural properties recorded but not decided

- **Location:** `_command` (763–822); the `parse_macho` docstring (826–832); W3-OBSERVER section 6.1
- **Issue:** The parser does not decide these properties: section file ranges, `LC_DYSYMTAB` offsets, segment overlap and order, duplicate segment names, `LC_BUILD_VERSION` platform and minimum OS, header flags and code-signature validity. Yet its docstring says it refuses "every structural inconsistency". Cases N58 to N63 are accepted, as the source predicts.
- **Effect on the real files:** No contract rule depends on these properties, and the bytes are pinned. The reader checks section and indirect-symbol ranges and segment overlap, and finds no anomaly in the 112 files. Every platform is macOS. Every minimum OS is at most 26.0: Node 13.5, Pillow 11.0, the framework and the externals 26.0. No file sets `MH_FORCE_FLAT` or `MH_ALLOW_STACK_EXECUTION`.
- **Recommendation:** In a later implementation phase, narrow the docstring and W3-OBSERVER section 6.1 to the checks made, or add the checks.

### N-03 (nonmandatory): The system side of the closure claim holds here, but rests on facts that M0 does not record

- **Location:** CONTRACT.md section 7 (load commands, closure claim) and section 4 (claim); `_closure_pass` line 1235
- **Issue:**
  - A normalized path under `/usr/lib/` or `/System/Library/` is treated as an OS library identified by the OS build, and is not resolved.
  - On this host every such reference is absent from disk and present in the image table of the cryptex's main cache file. That covers the 13 distinct paths of the bound files, Node's four among them, and the five of the developer tools' Git. The main cache file is `dyld_shared_cache_arm64e`: SHA-256 `7a024959…`, 573,440 bytes, UUID `F2E86C53-6052-388B-BA71-5A0C9B569413`, osVersion 26.6.0, 3,649 images.
  - The prefix rule does not ensure this by itself. `/usr/share/firmlinks` maps seven `/System/Library` subtrees onto the writable data volume: Caches, Assets, PreinstalledAssets, AssetsV2, PreinstalledAssetsV2, `CoreServices/CoreTypes.bundle/Contents/Library` and Speech. An on-disk file under either prefix is not a cache image either.
  - The dynamic linker `/usr/lib/dyld` is on disk: fat, x86_64 and arm64e, SHA-256 `373fce2b…`. It is also a cache image, and the header's dyld-in-cache fields are set. It is not hashed, and the claim names only "system libraries".
- **Effect on the real files:** None for these files. Every reference is a cache image, and no reference lies under a firmlinked subtree.
- **Recommendation:** Three changes would strengthen the claim; none is needed for this plan:
  - HOST records the main cache file's digest and UUID, and each system reference's membership in its image table. These are static reads, as `n34m_reader.py` makes.
  - M0 refuses a system reference that is not a cache image.
  - The claim's text names dyld as identified by the OS and unbound.

### N-04 (nonmandatory): D-16 settles MC36's premise from the link, not from the variable

- **Location:** DIRECTOR-DECISIONS.md D-16; MH-PLAN section 6; CONTRACT.md sections 7 and 9 (MC30, MC36)
- **Issue:** `bin/node`'s command 14 is a plain `LC_LOAD_DYLIB` of CoreFoundation, so under D-16 MC36 stands as written. The link means that dyld loads CoreFoundation and runs its initializers before `main`. It does not show that `__CF_USER_TEXT_ENCODING` is then present in the probe's `process.env` with HOST's value, and MC36's expected refusal needs exactly that.
- **Effect on the real files:** None yet. The positive starts observe it.
- **Recommendation:** In the operational freeze, tie MC36 to a positive probe start of the same freeze that observed the variable with HOST's value (MC30). If it was not observed, MC36 stays `NOT_RUN` pending D-16's amendment, and its expected outcome is not weakened.

### N-05 (nonmandatory): Implemented rules stricter than the contract's text

- **Location:** `parse_macho` 836–837; `python_inventory` 1164–1165; `check_python_macho` 933–949; `_counted` 870–877; `_closure_pass` 1240–1266; W3-OBSERVER section 11 (Q1, Q3 to Q5)
- **Issue:** Beyond the contract's words, the parser refuses:
  - a fat Python image (section 4 does not say thin);
  - any cpusubtype other than 0 (the contract says arm64);
  - a weak reference that does not resolve;
  - an `@rpath` reference that only another image's rpaths would resolve;
  - a relative leaf-name reference;
  - an executable without exactly one `LC_MAIN` and one `LC_LOAD_DYLINKER`;
  - either of those commands in another file type;
  - a dylib without exactly one `LC_ID_DYLIB`;
  - a second copy of a single-instance command.
- **Effect on the real files:** Each rule fails closed. Under MH-PLAN section 8, an M0 refusal on any of them would be an implementation cause and would stop MH. Every real file satisfies each rule:
  - no fat or arm64e image;
  - no weak, `@rpath` or leaf-name reference;
  - both executables have one `LC_MAIN` and one `LC_LOAD_DYLINKER`;
  - all 25 dylibs have one `LC_ID_DYLIB`;
  - no single-instance command is repeated.
- **Recommendation:** The observation plan's review cites W3-OBSERVER section 6 as the implemented rule set. A later amendment may write the fat and subtype rules into section 4.

### N-06 (nonmandatory): Unused LC_RPATH entries, one of them a build-machine path

- **Location:** the closure's `rpaths` (raw-compare-02.json, `python_inventory.closure.images`)
- **Issue:**
  - The 81 `LC_RPATH` entries are these:
    - `<prefix>/lib` in 78 framework images: the lib-dynload modules, the `Python` library and the process image;
    - the sqlite library's own lib directory;
    - libmpdec's `@loader_path/../lib`;
    - in Pillow's `libjpeg.62.4.0.dylib`, the absolute `/Users/runner/work/Pillow/Pillow/build/deps/darwin/lib`, which is absent here.
  - No bound image has an `@rpath` reference, so none of these entries takes part in load-time resolution.
- **Effect on the real files:**
  - The parser records each entry's resolution, and records the libjpeg entry as absent at `/Users/runner`.
  - Creating `/Users/runner`, for example an account of that name, would change the inventory. M0 and every recheck would then refuse. That fails closed: it never causes an unbound load.
  - The entries remain search paths for run-time `dlopen("@rpath/…")` calls from those images. dyld's search also includes the main executable's `<prefix>/lib`. Both lie outside the claim.
- **Recommendation:** Note it in the HOST review. No change is needed.

### N-07 (nonmandatory): Git: M0 does not check E18's premise

- **Location:** `check_git_binding` (1893–1926); `GIT_VERSION_LINE` (116); CONTRACT.md section 2 (E18) and section 7
- **Issue:**
  - Git is bound by path, SHA-256, size and mode, and is never parsed. `_macho_extent` refuses it as fat (`MACHO-FAT`, confirmed).
  - The developer tools' Git, `/Library/Developer/CommandLineTools/usr/bin/git` (SHA-256 `be4afb2b…`, 7,604,272 bytes), has an x86_64 slice and an arm64 slice, cpusubtype 3 and 0.
  - Both slices reference only CoreServices, CoreFoundation, libz, libiconv and libSystem. All five are cache images, none is on disk, and neither slice has an `LC_RPATH`.
- **Effect on the real files:**
  - For that file, E18's "its system libraries identified by OS build" holds.
  - Its arm64 slice embeds `2.50.1 (Apple Git-155)` and `git version %s`. Its predicted line, `git version 2.50.1 (Apple Git-155)\n`, matches `GIT_VERSION_LINE`. This is a static prediction; no Git was started.
  - The grammar-only check is consistent with the contract, which states no expected version.
- **Recommendation:** The observation plan's review confirms that the bound Git is this file, or re-reads the load commands of any other candidate. The HOST review compares the recorded line with the embedded text.

### N-08 (nonmandatory): W3-OBSERVER section 5's measured figures predate MP

- **Location:** W3-OBSERVER section 5, "Measured on this host"
- **Issue:** Section 5 was measured "with the venv as MI leaves it (no packages)". It reports 84 images, 5 venv files, and "No `@`-relative reference occurs".
- **Effect on the real files:**
  - At this review there are 111 images. The venv holds 27 of them: Pillow's 18 bundled dylibs and 8 extension modules, and rpds's extension.
  - There are 26 `@loader_path` references, all Pillow's, and 81 `LC_RPATH` entries.
  - The venv holds 297 files, 45 directories and 3 links.
  - Pillow's images are the first real files that exercise the `@loader_path` resolution path. The parser and the independent reader resolve all 26 references to the same bound files.
- **Recommendation:** The observation plan and its review use the frozen inventory's figures, not those of section 5.

### N-09 (nonmandatory): The -B rule names the .venv's interpreter, but this host's python3 is the same framework interpreter

- **Location:** MH-PLAN sections 3 and 5 ("-B"); W3-OBSERVER F4; the `python3 …` check commands in AGENTS.md
- **Issue:**
  - `python3` on this session's PATH is `<prefix>/opt/python@3.12/libexec/bin/python3`. That is a link to the framework's `bin/python3.12`, which is the bound launcher.
  - 1,390 of the framework's 1,804 standard-library sources have no cached bytecode. Of these, 106 lie outside `test`, `idlelib`, `lib2to3`, `turtledemo` and `tkinter`. Examples are `unittest/_log.py`, `unittest/async_case.py`, `doctest.py`, `multiprocessing/managers.py` and `email/mime/*.py`.
  - Suppose the framework interpreter starts under any name, without `-B` and without `PYTHONDONTWRITEBYTECODE`, and imports one of them. It adds a `__pycache__` file to the bound tree, and M0 or a recheck refuses (MC32).
- **Effect on the real files:** This session's environment sets `PYTHONDONTWRITEBYTECODE=1`, so W1's four starts of bare `python3` wrote nothing. The inventory digest equals MP's after-snapshot in runs 02 and 03, and no entry of either tree changed afterwards (section 6).
- **Recommendation:** Extend section 5's rule to every start of the framework's interpreter, whatever its name, the Director's workflow and documentation checks included. Alternatively, keep `PYTHONDONTWRITEBYTECODE=1` set for the phase and record it.

## 5. Mutation cases

Each case changes the real header bytes in memory and calls `parse_macho` and then the rule check: `check_node_macho` for the N cases, on `bin/node`, and `check_python_macho` for the P cases, on `lib/python3.12/lib-dynload/_ssl.cpython-312-darwin.so`. Every observed outcome equals the predicted one. Cases N58 to N63 show the properties that the parser does not decide (N-02).

| ID | Case | Expected | Observed |
| --- | --- | --- | --- |
| N00 | the real header and load commands, unchanged | `ACCEPT` | `ACCEPT` |
| N01 | fat magic 0xcafebabe | `MACHO-FAT` | `MACHO-FAT` |
| N02 | fat 64 magic 0xcafebabf | `MACHO-FAT` | `MACHO-FAT` |
| N03 | 32-bit magic | `MACHO-MAGIC` | `MACHO-MAGIC` |
| N04 | 64-bit big-endian magic | `MACHO-MAGIC` | `MACHO-MAGIC` |
| N05 | cputype x86_64 | `MACHO-CPU` | `MACHO-CPU` |
| N06 | cpusubtype CPU_SUBTYPE_ARM64E (2) | `MACHO-CPU` | `MACHO-CPU` |
| N07 | cpusubtype ARM64_ALL with the capability bit 0x80000000 | `MACHO-CPU` | `MACHO-CPU` |
| N08 | cpusubtype arm64e with CPU_SUBTYPE_PTRAUTH_ABI | `MACHO-CPU` | `MACHO-CPU` |
| N09 | cpusubtype CPU_SUBTYPE_ARM64_V8 (1) | `MACHO-CPU` | `MACHO-CPU` |
| N10 | filetype MH_DYLIB for Node | `MACHO-FILETYPE` | `MACHO-FILETYPE` |
| N11 | ncmds one more than present | `MACHO-MALFORMED` | `MACHO-MALFORMED` |
| N12 | ncmds one fewer than present | `MACHO-MALFORMED` | `MACHO-MALFORMED` |
| N13 | ncmds zero | `MACHO-MALFORMED` | `MACHO-MALFORMED` |
| N14 | sizeofcmds 8 larger than the commands | `MACHO-MALFORMED` | `MACHO-MALFORMED` |
| N15 | sizeofcmds beyond the file | `MACHO-MALFORMED` | `MACHO-MALFORMED` |
| N16 | header shorter than 32 bytes | `MACHO-MALFORMED` | `MACHO-MALFORMED` |
| N17 | command bytes not all supplied | `MACHO-MALFORMED` | `MACHO-MALFORMED` |
| N18 | cmdsize not a multiple of 8 (LC_LOAD_DYLINKER 32 -> 36) | `MACHO-MALFORMED` | `MACHO-MALFORMED` |
| N19 | cmdsize 4 (below 8) | `MACHO-MALFORMED` | `MACHO-MALFORMED` |
| N20 | cmdsize 0 | `MACHO-MALFORMED` | `MACHO-MALFORMED` |
| N21 | last command's cmdsize escapes sizeofcmds | `MACHO-MALFORMED` | `MACHO-MALFORMED` |
| N22 | LC_LOAD_DYLINKER string offset equal to cmdsize | `MACHO-MALFORMED` | `MACHO-MALFORMED` |
| N23 | LC_LOAD_DYLINKER string offset inside the fixed structure (8) | `MACHO-MALFORMED` | `MACHO-MALFORMED` |
| N24 | LC_LOAD_DYLINKER string not NUL-terminated inside the command | `MACHO-MALFORMED` | `MACHO-MALFORMED` |
| N25 | LC_LOAD_DYLINKER string empty | `MACHO-MALFORMED` | `MACHO-MALFORMED` |
| N26 | LC_LOAD_DYLINKER string with a non-ASCII byte | `MACHO-MALFORMED` | `MACHO-MALFORMED` |
| N27 | LC_LOAD_DYLINKER /usr/lib/dyle | `MACHO-DYLINKER` | `MACHO-DYLINKER` |
| N28 | LC_LOAD_DYLIB @rpath/libc++.1.dylib | `MACHO-AT-PATH` | `MACHO-AT-PATH` |
| N29 | LC_LOAD_DYLIB @loader_path/libc++.dylib | `MACHO-AT-PATH` | `MACHO-AT-PATH` |
| N30 | LC_LOAD_DYLIB /usr/lib/../lib/c.dylib | `MACHO-DYLIB-PATH` | `MACHO-DYLIB-PATH` |
| N31 | LC_LOAD_DYLIB /usr/local/lib/c.dylib | `MACHO-DYLIB-PATH` | `MACHO-DYLIB-PATH` |
| N32 | LC_LOAD_DYLIB //usr/lib/libc++.dylib | `MACHO-DYLIB-PATH` | `MACHO-DYLIB-PATH` |
| N33 | LC_LOAD_DYLIB /usr/lib//libc++.dylib | `MACHO-DYLIB-PATH` | `MACHO-DYLIB-PATH` |
| N34 | LC_LOAD_DYLIB relative leaf name libc++.1.dylib | `MACHO-DYLIB-PATH` | `MACHO-DYLIB-PATH` |
| N35 | LC_LOAD_DYLIB /USR/LIB/libc++.1.dylib (case differs) | `MACHO-DYLIB-PATH` | `MACHO-DYLIB-PATH` |
| N36 | LC_LOAD_DYLIB cmd with the LC_REQ_DYLD bit (0x8000000c) | `MACHO-COMMAND` | `MACHO-COMMAND` |
| N37 | LC_LOAD_WEAK_DYLIB without the LC_REQ_DYLD bit (0x18) | `MACHO-COMMAND` | `MACHO-COMMAND` |
| N38 | LC_LOAD_WEAK_DYLIB (0x80000018) of a system dylib | `ACCEPT` | `ACCEPT` |
| N39 | LC_REEXPORT_DYLIB | `MACHO-REFUSED-COMMAND` | `MACHO-REFUSED-COMMAND` |
| N40 | LC_LOAD_UPWARD_DYLIB | `MACHO-REFUSED-COMMAND` | `MACHO-REFUSED-COMMAND` |
| N41 | LC_LAZY_LOAD_DYLIB | `MACHO-COMMAND` | `MACHO-COMMAND` |
| N42 | LC_ID_DYLIB in the executable | `MACHO-COMMAND` | `MACHO-COMMAND` |
| N43 | LC_RPATH /a in place of LC_SOURCE_VERSION | `MACHO-REFUSED-COMMAND` | `MACHO-REFUSED-COMMAND` |
| N44 | LC_RPATH without the LC_REQ_DYLD bit (0x1c) | `MACHO-COMMAND` | `MACHO-COMMAND` |
| N45 | LC_DYLD_ENVIRONMENT /a | `MACHO-REFUSED-COMMAND` | `MACHO-REFUSED-COMMAND` |
| N46 | unknown command 0x37 | `MACHO-COMMAND` | `MACHO-COMMAND` |
| N47 | unknown command 0x80000099 (LC_REQ_DYLD set) | `MACHO-COMMAND` | `MACHO-COMMAND` |
| N48 | LC_VERSION_MIN_MACOSX (known, outside the allow-list) | `MACHO-COMMAND` | `MACHO-COMMAND` |
| N49 | LC_ENCRYPTION_INFO_64 (known, outside the allow-list) | `MACHO-COMMAND` | `MACHO-COMMAND` |
| N50 | a second LC_MAIN in place of LC_UUID | `MACHO-DUPLICATE` | `MACHO-DUPLICATE` |
| N51 | LC_SEGMENT_64 file range beyond the file | `MACHO-MALFORMED` | `MACHO-MALFORMED` |
| N52 | LC_SEGMENT_64 nsects disagrees with cmdsize | `MACHO-MALFORMED` | `MACHO-MALFORMED` |
| N53 | LC_SYMTAB string table beyond the file | `MACHO-MALFORMED` | `MACHO-MALFORMED` |
| N54 | LC_CODE_SIGNATURE beyond the file | `MACHO-MALFORMED` | `MACHO-MALFORMED` |
| N55 | LC_MAIN entry offset beyond the file | `MACHO-MALFORMED` | `MACHO-MALFORMED` |
| N56 | LC_BUILD_VERSION ntools disagrees with cmdsize | `MACHO-MALFORMED` | `MACHO-MALFORMED` |
| N57 | LC_UUID cmdsize 32 (padding) | `MACHO-MALFORMED` | `MACHO-MALFORMED` |
| N58 | LC_BUILD_VERSION platform IOS (2) [not decided by the parser] | `ACCEPT` | `ACCEPT` |
| N59 | header flag MH_FORCE_FLAT [not decided by the parser] | `ACCEPT` | `ACCEPT` |
| N60 | header flag MH_ALLOW_STACK_EXECUTION [not decided by the parser] | `ACCEPT` | `ACCEPT` |
| N61 | __DATA_CONST file range moved to overlap __TEXT [not decided by the parser] | `ACCEPT` | `ACCEPT` |
| N62 | LC_DYSYMTAB indirect-symbol offset beyond the file [not decided by the parser] | `ACCEPT` | `ACCEPT` |
| N63 | LC_SEGMENT_64 section offset beyond the file [not decided by the parser] | `ACCEPT` | `ACCEPT` |
| P00 | the real lib-dynload bundle, unchanged | `ACCEPT` | `ACCEPT` |
| P01 | filetype MH_OBJECT (W3 Q5) | `MACHO-FILETYPE` | `MACHO-FILETYPE` |
| P02 | filetype MH_DYLIB without LC_ID_DYLIB | `MACHO-STRUCTURE` | `MACHO-STRUCTURE` |
| P03 | filetype MH_EXECUTE without LC_MAIN and LC_LOAD_DYLINKER | `MACHO-STRUCTURE` | `MACHO-STRUCTURE` |
| P04 | LC_RPATH @rpath/... | `MACHO-RPATH` | `MACHO-RPATH` |
| P05 | LC_RPATH @loader_path/../lib | `ACCEPT` | `ACCEPT` |
| P06 | LC_RPATH relative directory | `MACHO-RPATH` | `MACHO-RPATH` |
| P07 | LC_RPATH @executable_pathX (no slash) | `MACHO-RPATH` | `MACHO-RPATH` |
| P08 | LC_LOAD_DYLIB @foo/libz.dylib (other @ form) | `MACHO-AT-PATH` | `MACHO-AT-PATH` |
| P09 | LC_LOAD_DYLIB @rpath/ (empty name) | `MACHO-AT-PATH` | `MACHO-AT-PATH` |
| P10 | LC_LOAD_DYLIB @rpath/libz.dylib (per-file rule; resolution is the closure's) | `ACCEPT` | `ACCEPT` |
| P11 | LC_LOAD_DYLIB relative leaf name | `MACHO-DYLIB-PATH` | `MACHO-DYLIB-PATH` |
| P12 | LC_REEXPORT_DYLIB | `MACHO-COMMAND` | `MACHO-COMMAND` |
| P13 | LC_LOAD_UPWARD_DYLIB | `MACHO-REFUSED-COMMAND` | `MACHO-REFUSED-COMMAND` |
| P14 | LC_LAZY_LOAD_DYLIB | `MACHO-COMMAND` | `MACHO-COMMAND` |
| P15 | LC_DYLD_ENVIRONMENT in place of LC_RPATH | `MACHO-REFUSED-COMMAND` | `MACHO-REFUSED-COMMAND` |
| P16 | LC_RPATH without the LC_REQ_DYLD bit (0x1c) | `MACHO-COMMAND` | `MACHO-COMMAND` |

## 6. Conduct

- No Git write: the worktree's index file was last written at 16:08:36 MST, before this review began. No worktree file is newer than it, and no file was created in the worktree, bytecode included (no `__pycache__` exists under `prototypes/static_tray_v01/`).
- No Node, `ldd`, `codesign`, `otool` or Git `--version` start, no download, no install, and no Finder.
- Starts made:
  - `<worktree>/.venv/bin/python -I -S -B` for every script and every inline analysis;
  - shell utilities (`ls`, `find`, `stat`, `readlink`, `grep`, `sed`, `cat`, `env`, `date`, `mkdir`, `mv`);
  - five read-only Git commands in the worktree, to confirm that it was clean: `git status --short` and `git status --short --ignored`, twice each, and `git rev-parse HEAD`. The index file kept its earlier modification time;
  - four starts of bare `python3`, which is the framework interpreter (N-09). One printed an empty line, two read repository JSON, and one printed `sys` facts. Each ran without `-B` but under `PYTHONDONTWRITEBYTECODE=1`, so `dont_write_bytecode` was 1. Nothing was written: the inventory digest equals MP's after-snapshot in runs 02 and 03, and no entry of either tree, or of the external libraries' directories, is newer than 16:12:06 MST.
- Deviations from MH-PLAN section 3, which allows W1 static reads and its own scripts under `-I -S -B`: the Git reads and the bare `python3` starts. Neither wrote anything or changed a bound input.
- Writes: only under `<local>/c271-p35/workers/W1/`.
- First run superseded: `n34m_compare.py` compared the reader's labelled paths with the parser's real paths and so reported false differences. Its outputs are kept in `superseded-run-01/`, produced by earlier versions of the two scripts. Runs 02 and 03 use the corrected script, and their outputs record the scripts' digests.

## 7. Files

Reviewed, at the bound commit:

| File | SHA-256 | Bytes |
| --- | --- | --- |
| `<worktree>/docs/engineering/localized-repair-c271/macos-contract-design-p31/CONTRACT.md` | `42db98dc6099ee605b0963f3734f7bff2d68c019ff6c00a0ee97bd753c03fdc9` | 42,769 |
| `<worktree>/docs/engineering/localized-repair-c271/macos-contract-design-p31/CONTRACT.json` | `c843fc96f19b36b3ea141c5be0fb08c8260565188e8f5f199ff5b0bc08ca3920` | 43,340 |
| `<worktree>/docs/engineering/localized-repair-c271/macos-implementation-p33/AMENDMENT-001.md` | `9ac21432c11818a488e462bfb139138058493c7ff8ecf947617210df10870bc2` | 18,291 |
| `<worktree>/docs/engineering/localized-repair-c271/macos-implementation-p33/AMENDMENT-001.json` | `6dcfbfbf245d2d950942eddac015546995a01e4994a24981ca60f6bbee29824c` | 25,161 |
| `<worktree>/docs/engineering/localized-repair-c271/macos-implementation-p33/interfaces/W3-OBSERVER.md` | `5e936aa4b46590df710dd13da2c2a2d1ac758aa903470bb5e72ef2143a02018d` | 38,426 |
| `<worktree>/docs/engineering/localized-repair-c271/macos-implementation-p33/DIRECTOR-DECISIONS.md` | `f596bc9fb85e33984eaf84c2067f15922749f523723274e49510cd798bed035f` | 21,484 |
| `<worktree>/docs/engineering/localized-repair-c271/macos-qualification-p35/MH-PLAN.md` | `9db4c00fbb078c86ab3488560f95ac8b0976abf255da92d32723ecae60810386` | 14,582 |
| `<worktree>/docs/engineering/localized-repair-c271/macos-qualification-p35/PHASE.json` | `ca9afa5415de8f586dc2e05447434f1feef5ccaae11edb1ea64c96f973ad80c1` | 7,038 |
| `<worktree>/docs/engineering/localized-repair-c271/macos-preparation-p34/reviews/RESULT-REVIEW-001.json` | `daa5f6b21380b6c3999c8c9fe827c15935165a8a3eb8d6291b03233860b9ae8d` | 29,586 |
| `<worktree>/prototypes/static_tray_v01/current_host_observation_v02.py` | `471a954703a1a7974638e500051a6ac538bf81dfb2a01a3944bf441e96622788` | 162,557 |

Produced by W1, in `<local>/c271-p35/workers/W1/`. The two review files are rendered by `n34m_report.py` from the raw outputs, so their own digests are not listed.

| File | SHA-256 | Bytes |
| --- | --- | --- |
| `n34m_reader.py` | `5c6d818571a824e0ca026c16877a6ee6ab2c06d4685bcf7623c458ea28763f42` | 53,529 |
| `n34m_compare.py` | `b3f233fbceafc6b8d69756b9ca839af6458b6b58e962404c8d5f794fd6575843` | 29,398 |
| `n34m_git_scan.py` | `1d6ea57ed1253d01fa2c6da4f1ab5311d47d401e81c1c2b10f3fececcda1f54c` | 2,813 |
| `n34m_report.py` | `ba572869fd4fe16204a620c348bb4374e3bd88b91d0835d9d33071602744ea86` | 76,885 |
| `raw-reader-02.json` | `ae6cacba59751a5e3cdf807df7038dd6d30aec2497a2760201b59ad14dcf3cf8` | 1,792,319 |
| `raw-compare-02.json` | `6ec7077572e156ed2d9ac9867f3890f3bce42b1ed0878224cc50f21241ed3729` | 203,362 |
| `raw-compare-03.json` | `fc0ed5302134de604ad207c3a2de723bd73b573ab1266c99808e6f13237e7537` | 203,362 |
| `raw-git-scan-02.json` | `857ce0fc32a8f9c0e505de1077e24ee5700f988f7dd460c3e51d46844c0268f8` | 694 |
| `superseded-run-01/raw-reader-01.json` | `fa4e33bf874c42ce7fc66a18858b9c0df42e06258ef014e242fc2dcd925107ec` | 1,789,629 |
| `superseded-run-01/raw-compare-01.json` | `5dbc02b81426bc32e38114677eb4f1c7bf2622e866fec1647c0d8ce4a09178c3` | 214,836 |
