# W1 author notes: the freeze of gate MP (C271-P34)

W1, the independent preparation author of phase `C271-P34-macos-preparation-mp`, in local mode.
Director `c271-p34-ec1a7de2360d`. Fresh context; W1 wrote none of the implementation. Frozen on
2026-11-26 from the checkout at `6d08e026` on `work/c271-missing-import-digest-control`. Nothing was
extracted, installed or applied.

These notes name places by label only: `<worktree>` is the C271 checkout, `<local>` the working
directory beside the clone, and `<prefix>` (in `venv-expectation.json`) the Homebrew prefix that
`pyvenv.cfg`'s `home` names. This file holds no machine path.

## 1. Files

| File | Content | Machine paths |
| --- | --- | --- |
| `node-install-plan.json` | install/0.2.0 plan, purpose `selected-node`, report `<local>/c271-p34/receipts/node-install-result.json` | yes (exact) |
| `reader-install-plan.json` | install/0.2.0 plan, purpose `retained-dependencies`, report `<local>/c271-p34/receipts/reader-install-result.json` | yes (exact) |
| `NODE-SOURCE.json.expected` | the exact bytes of `NODE-SOURCE.json` (no trailing newline) | no |
| `venv-expectation.json` | the expected result of PREPARATION-PLAN.md section 3 | no |
| `*.portable.json` | each plan with `<worktree>` and `<local>` in place of the two roots | no |
| `*.dry-run.json` and their portable copies | offered by W1 for finding F1: the same plans with only `report` changed | yes / no |
| `AUTHOR-OBSERVATIONS.json` | what the freeze observed: counts, types, D-06, `bin/node`, links, mapping | no |
| `AUTHOR-CROSSCHECK.json` | the comparison with the implementation's helpers | no |
| `w1_freeze_mp.py`, `w1_crosscheck_mp.py` | the method, as run | no |
| `SHA256SUMS` | SHA-256 of every other file here | no |

Exact plan digests, the values for `--plan-sha256`:

| Plan | SHA-256 | Bytes |
| --- | --- | ---: |
| `node-install-plan.json` | `1fee042d5e3c809a89d4975df40f69d7a27e88abf9ba58d8cf91ca16795c5ff1` | 956,650 |
| `reader-install-plan.json` | `ff5a95da6d349e0bd6ea1d2c79fc02757de48ac9cbb89dc59737b67c6d7a71c8` | 158,115 |
| `node-install-plan.dry-run.json` | `869b6414d42f6ced4ee4ad017ceff7cc63c33b563fcdffcc5999cebebae01d48` | 956,650 |
| `reader-install-plan.dry-run.json` | `a81897783b9df86bb216eb5c371a1191de0a89762e6cd88360c8cc7b7fecf10e` | 158,115 |

## 2. Method

- **Sources.** PHASE.json and PREPARATION-PLAN.md of P34; CONTRACT.md sections 3, 4 and 6, with
  section 1 for the C195 pin and section 7 for the Node allow-list; AMENDMENT-001, confirmed to
  change only the supervisor; W2-PREPARER.md sections 2 to 4, with section 5 for the header
  predicate. The preparer's 0.2.0 source was read for exact key sets and value forms. Also read:
  `dependency_inventory` and its C199 manifest, P22's 0.1.0 plan and inventory as references,
  and the macOS lock and its provenance.
- **Tool.** `w1_freeze_mp.py` uses the standard library only. It ran as
  `.venv/bin/python -I -S -B` (CPython 3.12.13) from the checkout root. Its values are typed from
  the documents, and it imports no module of the checkout.
  - An audit hook refused every process start, every filesystem change, and every write outside
    this directory. Each refusal was tested on targets where a missed refusal could have no effect.
  - Outputs are exclusive creations, read back after writing.
- **Pins first.** Each archive and wheel was read into memory once. Its SHA-256 and size were
  compared with the pin before any member was read, and members were parsed from those same bytes.
- **Two views of each archive.** Python's `tarfile`, the preparer's library on the same
  interpreter, and W1's own ustar, pax and GNU header walk over the decompressed bytes. They were
  compared row by row:
  - name, kind, size, mode, link target and data offset;
  - every file digest for C195, and `bin/node`'s bytes from both views.

  As a third view, CPython 3.9.6's `tarfile` rebuilt both inventories. It gave the same Node
  inventory digest and the same C195 rows.
- **Node archive.** Contract section 3 and note section 3, implemented independently:
  - names relative, normalized, under the root and unique;
  - kinds file, directory or symlink only, with no sparse member;
  - directories and links without data, and modes at most `0o7777`;
  - link targets relative and resolved lexically inside the root, never above it;
  - no member below a link or a file;
  - `bin/node` a declared regular file.

  `NODE-SOURCE.json` was then built from note section 4, in note section 3's canonical form.
- **C195 archive.** P05 section 5's rules, unchanged by 0.2.0 (MC34): names, file or directory
  only, mode at most `0o777` with no group or world write, and every file's SHA-256.
  - **Mapping.** The C199 manifest (SHA-256 `21fd6bad…9ccd5`, `dependency_inventory`'s pin)
    has a `dependencies_root` ending in `evidence/c195-validation/receiving`. The C195 archive is
    that `evidence/` tree. Member `c195-validation/receiving/<rel>` therefore maps to `<rel>`.
  - **Check.** Each of the 24 members was matched by digest and size.
- **Plan bytes.** Canonical JSON: sorted keys, compact separators, ASCII, no trailing newline.
  This is the provider's `_canonical` form, as in P22's plans. The portable copies come from a
  textual replacement of the two roots. Each was checked to map back to the exact bytes and to
  hold no path under the roots' common parent. The plans carry no design-revision field (D-15).
- **Cross-check, afterwards.** `w1_crosscheck_mp.py` imported the preparer by path and called only
  these helpers:
  - `validate_plan_v02`;
  - `member_inventory_sha256_v02`;
  - `node_source_bytes_v02`;
  - the provider's `dependency_inventory`.

  It never called `install_plan_v02` or the CLI, and ran no archive pass. The dry run and the
  application remain the Director's.

## 3. Counts and types

**Node archive** (`node-v24.22.1-darwin-arm64.tar.gz`, SHA-256 equal to the adopted pin, 53,062,778
bytes, mode `0o444`, one link):
- **Members:** 5,888.
  - 4,797 regular files: 4,734 with mode `0o644` and 63 with `0o755`.
  - 1,088 directories, all `0o755`, the root directory member among them.
  - 3 symbolic links, `0o755`.
- **Header types:** `0` ×4,797, `5` ×1,088 and `2` ×3. None other: no pax or GNU long-name header,
  and no hard link, device, FIFO, contiguous or sparse member. All headers are POSIX ustar, and
  1,405 names use the ustar prefix field.
- **End of archive:** from the end marker on, the stream holds only zeros: 1,024 bytes, the two
  zero blocks.
- **Sizes:** 197,423,496 expanded bytes; the tar stream is 201,716,224 bytes.
- **Links.** Each resolves lexically inside the root, to a declared regular file:
  - `bin/corepack` → `../lib/node_modules/corepack/dist/corepack.js`;
  - `bin/npm` → `../lib/node_modules/npm/bin/npm-cli.js`;
  - `bin/npx` → `../lib/node_modules/npm/bin/npx-cli.js`.
- **Inventory digest** (`member_inventory_sha256`):
  `0b2b6072fd2e6b22fd4d2715d9db9429adf17d960825b0048411d1a1d4c0f27d`.

**C195 archive** (SHA-256 `b1e54a6c…e904a0c9`, 2,611,764 bytes, mode `0o644`):
- **Members:** 730, all regular files. Modes: `0o644` ×726, `0o444` ×3 and `0o600` ×1.
- **Headers:** each member is preceded by a pax `x` header, and the only records used are `path`
  and `mtime`. From the end marker on, the stream holds only zeros (9,216 bytes).
- **Directories:** no member is a directory. The 13 planned parent directories therefore map from
  no member and take `0o755`; P05 section 5 allows implicit parents.
- **Mapped members:** 69 members lie under `c195-validation/receiving/`, and only the 24 are mapped.
  No other member has the bytes of any of the 24.
- **Inventory digest:** `72dc3175953b29edce2e2343613c08fb2f0bfb2b40e72faaaa5c9d457d67cb8a`.
- **References:** the inventory, the 24 files, the 13 directories and the root mode equal those of
  P22's 0.1.0 plan and inventory. They were verified, not copied.

**Wheels.**
- **Pins:** the lock's SHA-256 (`b1e3e866…a81c`) equals its provenance record. Each wheel's
  SHA-256 equals the lock, and its size equals the provenance. The wheel directory holds exactly
  the seven.
- **Contents:** no wheel contains bytecode, a `.pth` file or a `.data` directory. Each METADATA
  matches the lock's name and version, and every RECORD row matches the zip's bytes.

## 4. D-06

**Confirmed.**
- **Names:** all 5,888 Node member names and the 3 link targets are ASCII. Every name is relative,
  normalized and below `node-v24.22.1-darwin-arm64`, and none is a duplicate.
- **Modes:** the highest is `0o755`, below the `0o7777` limit, and no member has a setuid, setgid
  or sticky bit.

The refusals that D-06 keeps do not trigger on the official archive, and no rule was weakened.

## 5. bin/node's binding

| Field | Value |
| --- | --- |
| Member | `node-v24.22.1-darwin-arm64/bin/node`, regular file, header mode `0o755` |
| SHA-256 | `6f32069480ec14d52b6d7b1f3c7124cfbbc46203abf5ddf5c65b127435f3f329` |
| Size | 122,545,856 bytes |
| Planned mode | `0o755` (`files["bin/node"]`) |
| Mach-O header | magic `0xfeedfacf` (thin, 64-bit, little-endian), cputype `0x0100000c` (arm64), cpusubtype `0x00000000`, filetype 2 (`MH_EXECUTE`): a thin 64-bit arm64 `MH_EXECUTE` |

**Load commands, for information only.** This is not M0, and not N34-M, which stay with MH.
- **Allow-list:** 21 load commands, all in contract section 7's allow-list:
  - `LC_SEGMENT_64` ×5 and `LC_LOAD_DYLIB` ×4;
  - one each of `LC_SYMTAB`, `LC_DYSYMTAB`, `LC_LOAD_DYLINKER`, `LC_UUID`, `LC_BUILD_VERSION`,
    `LC_SOURCE_VERSION`, `LC_MAIN`, `LC_FUNCTION_STARTS`, `LC_DATA_IN_CODE`,
    `LC_CODE_SIGNATURE`, `LC_DYLD_CHAINED_FIXUPS` and `LC_DYLD_EXPORTS_TRIE`.
- **Paths:**
  - the dynamic linker is `/usr/lib/dyld`;
  - the dylibs are CoreFoundation.framework, Security.framework, `/usr/lib/libc++.1.dylib` and
    `/usr/lib/libSystem.B.dylib`;
  - no path is `@`-relative.
- **UUID:** `6caf9c5b1e60382db33c06521a6aeb0f`.

**NODE-SOURCE.json.** 976 bytes, SHA-256 `e928a8ec87a6fcd8f21d7bef3e080392e0bdaad3acbf2e767997dae5ead9ea2c`,
bound by the plan as `files["NODE-SOURCE.json"]` with mode `0o644`.
- **Status:** `signature_check` is `not_performed`.
- **Detail:** "Not performed. The check needs the release's SHASUMS256.txt and its detached
  signature, and neither was an approved download for gate MP. The adopted archive pin (contract
  section 3) is the trust anchor."

## 6. Differences from the implementation's helpers

**None.** All 29 checks of `AUTHOR-CROSSCHECK.json` agree:
- `validate_plan_v02` accepts all four plans.
- The two inventory digests equal `member_inventory_sha256_v02`.
- `node_source_bytes_v02` builds exactly `NODE-SOURCE.json.expected`.
- `dependency_inventory(ROOT)` equals the reader plan's 24 files by digest and size.
- The preparer's pins, names, schemas and key sets equal the values W1 typed from the documents.

## 7. The .venv expectation

`venv-expectation.json` gives:
- the seven distributions, with name, version, and the wheel's SHA-256 and size;
- 15 expected top-level entries of `site-packages` and the 7 `.dist-info` names;
- every expected file with its bytes from the wheel: 270 from the wheels, and with pip's 21
  metadata files, 291 files in `site-packages`;
- one console script, `jsonschema`, in the `.venv`'s `bin`;
- the `.venv` as observed before the step, and the rules: no other distribution, pip included,
  and no `__pycache__` or `.pyc` anywhere.

## 8. Findings

- **F1, procedure: a dry run consumes its plan's report path.** `install_plan_v02` requires the
  report path to be absent, and a dry run writes `<report>` and `<report>.preflight.json`.
  - **Effect:** the dry run and the `--apply` of PREPARATION-PLAN.md step 6 cannot use the same
    plan. The apply would be refused at the report check, before the archive is read.
  - **Offer:** W1 froze dry-run variants identical except for `report`:
    `<local>/c271-p34/receipts/node-dry-run-result.json` and `reader-dry-run-result.json`. Both
    paths are absent, and `validate_plan_v02` accepts both plans.
  - **Repeats:** a repeat that expects `ALREADY_PRESENT_EXACT` also needs a plan of its own.
  - **Scope:** this concerns the procedure, not the contract. The Director decides.
- **F2, information for S10.** `bin/node`'s load commands name CoreFoundation.framework. This is
  static only. It does not establish whether a start adds `__CF_USER_TEXT_ENCODING`, which MC30
  and MC31 test.
- **F3, limits of the `.venv` expectation.** The files that pip itself writes are predicted from
  pip's installer behaviour, not read from the wheels:
  - `INSTALLER`, containing `pip\n`;
  - an empty `REQUESTED`;
  - a rewritten `RECORD`, whose bytes are not predicted;
  - no `direct_url.json`, because the requirements are named, not direct URLs.

  Any other file that pip writes is a finding for the Director's check. The `jsonschema` script's
  first line will name the `.venv` interpreter.
- **F4, binding assumptions.**
  - **Checkout:** the plans bind `source_root` to `<worktree>`, and the C195 archive inside it.
    The preparer must run from this checkout, at the bound commit B.
  - **Archive:** the Node archive must keep mode `0o444` and a single link.
  - **State at the freeze:** both destinations and all four report paths were absent. The
    destination parent existed, empty, on the reports' volume.

## 9. Conduct

**Limits.**
- No Node, `ldd` or `codesign` process was started. W1 downloaded nothing and made no Git write.
- Nothing was written in the checkout. Its status stayed empty, and the worktree index's
  modification time (14:03:37, the Director's commit) predates this work.
- The only processes started were the two Python interpreters, Git read commands and read-only
  shell utilities.

**One write outside this directory.** The console summary of the first print-only run, 5,271
bytes with no plan bytes, was redirected to the session's own temporary scratch directory, outside
the project. No other write left this directory.
