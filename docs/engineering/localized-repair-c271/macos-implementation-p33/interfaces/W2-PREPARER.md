# W2: the 0.2.0 preparer route (S6)

**Phase:** C271-P33, gate MI, worker W2, local mode. **Base:** `f3a5acf8`. **Files:**
`tools/prepare_current_host_readback.py` (0.2.0 route added beside the unchanged 0.1.0 route) and
`tests/test_prepare_current_host_readback_v02.py` (development tests).

**Status:** implemented and tested with synthetic inputs only. These are development tests. The
independent author freezes the controls later, so nothing here is a frozen control. Nothing was
prepared: the real Node archive is not on this machine, and no Node, `ldd`, `codesign` or other
process was started.

Contract: [CONTRACT](../../macos-contract-design-p31/CONTRACT.md) sections 3 and 6 (S6), with P05
section 5's rules for the reader archive. Plan: [IMPLEMENTATION-PLAN](../IMPLEMENTATION-PLAN.md)
section 4.2.

## 1. Entry points

| Name | Purpose |
| --- | --- |
| `main(argv)` | The CLI, unchanged in form: `--plan`, `--plan-sha256`, `--apply`. It reads the plan, then dispatches on its schema. A `/0.2.0` plan goes to the 0.2.0 route. Every other document takes the unchanged 0.1.0 path, which refuses anything that is not a 0.1.0 plan. |
| `install_plan(plan, *, apply)` | The 0.1.0 entry, byte-identical. It refuses a 0.2.0 plan through its own shape check. |
| `install_plan_v02(plan, *, apply=False, synthetic_pins=None)` | The 0.2.0 entry. It refuses every plan whose schema is not `/0.2.0`. `synthetic_pins` is the test seam (section 9). |
| `validate_plan_v02(plan)` | Plan check under the adopted pins only, for consumers (W3, W5). |
| `member_inventory_sha256_v02(members)` | The inventory digest (section 3). |
| `node_source_document_v02(plan)`, `node_source_bytes_v02(plan)` | NODE-SOURCE.json built from a selected-node plan (section 4). |
| `rename_exclusive(source, destination)` | `renamex_np` with `RENAME_EXCL` (section 6). |
| `NODE_ARCHIVE_SHA256_V02`, `RENAME_EXCL`, `LIBSYSTEM` | The adopted pin `89c68259…bc0a7`, `0x00000004` and `/usr/lib/libSystem.B.dylib`. |

The 0.2.0 route starts no process at all, whatever the plan or the outcome.

## 2. Plan: `ontokin.current-host-readback-install/0.2.0`

The plan is a closed object. A missing or extra key refuses it.

| Key | Meaning |
| --- | --- |
| `schema` | `ontokin.current-host-readback-install/0.2.0`. This is checked first, so a plan of another version refuses with "The 0.2.0 preparer refuses a plan of another schema version". |
| `contract` | `ontokin.current-host-readback/0.2.0`. |
| `purpose` | `selected-node` or `retained-dependencies`. `isolated-control` has no 0.2.0 form (decision D1). |
| `source_root` | The checkout whose preparer runs the plan. It must equal the preparer's own root (D2). |
| `archive` | `{path, sha256, size_bytes, mode}` of the archive file. `sha256` must equal the purpose's pin. Size and mode are the observed values that the plan freezes. |
| `destination` | The task-specific directory. It must be outside the checkout, and either absent or exactly complete. |
| `root_mode` | The destination root's mode. |
| `files` | Every target file: relative path to `{sha256, size_bytes, mode}`. For `selected-node`, exactly `bin/node` (mode `0o755`) and `NODE-SOURCE.json`. For `retained-dependencies`, exactly the pinned files: under the adopted pins, the 24 of the C199 manifest, compared by digest and size. |
| `directories` | Exactly the parents of the target files, with modes. For `selected-node` this is `{"bin": mode}`. The owner must be able to read and traverse each one. |
| `members` | The complete frozen archive member inventory (section 3). |
| `node_source` | For `selected-node`, `{"signature_check": {"status", "detail"}}`. `status` is `not_performed`, `verified` or `failed`, and `detail` is ASCII text of 1 to 4,096 characters. For `retained-dependencies`, `null`. |
| `report` | The fresh report file. It must be absent, its parent must exist, and it must lie outside the checkout and the destination. |

Every path must be absolute, normalized and free of symbolic-link components. That is the
canonical form of contract section 7, so write `/private/var/…`, not `/var/…`.

## 3. Member inventory and its digest

**`selected-node`.** Each member name maps to `{kind, size_bytes, mode, link_target}`. These are
the contract's name, type, size, mode and link target, with "type" spelled `kind` as in 0.1.0.

- **Name:** relative and normalized. It is `node-v24.22.1-darwin-arm64` or a path below it. No
  member may sit below a declared link or file.
- **`kind`:** `file`, `directory` or `symlink`. A hard link, device, FIFO, sparse or other entry
  cannot be declared, and refuses the archive.
- **`size_bytes`:** the tar header size. It is `0` for directories and links.
- **`mode`:** the `oct()` text of the tar header mode, from `0o0` to `0o7777`. It is frozen
  exactly but otherwise unrestricted, because such members are never written (D3).
- **`link_target`:** for a link, the target exactly as it appears in the archive; otherwise
  `null`. It must be relative. Resolved lexically from the link's directory, it must stay inside
  the archive root `node-v24.22.1-darwin-arm64` and never pass above it.
- **Node member:** `node-v24.22.1-darwin-arm64/bin/node` must be declared as a `file` whose size
  equals the frozen `files["bin/node"].size_bytes`.

**`retained-dependencies`.** Each member maps to the 0.1.0 row `{kind, size_bytes, sha256, mode,
target}`, and P05 section 5's rules apply unchanged. `kind` is a file or a directory only. The
mode must lie between `0o000` and `0o777`, with no group or world write. Every file carries a
`sha256`. `target` maps a member to a planned file, with an exact binding, or to a planned
directory, and every planned file must be mapped. Extraction reuses the 0.1.0 `verify_archive`
unchanged.

**Digest.** `member_inventory_sha256` is the SHA-256 of
`prototypes.static_tray_v01.canonical.json_bytes(plan["members"])`. That is
`json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)`
encoded as ASCII:
- keys are sorted at every level;
- there is no whitespace and no trailing newline;
- a non-ASCII member name refuses.

The order of members in the archive is not part of the inventory.

## 4. `NODE-SOURCE.json`

The preparer builds the file from the plan and never takes it from the archive. Its bytes are
`canonical.json_bytes` of this object, with keys sorted in the bytes:

| Key | Value | Taken from |
| --- | --- | --- |
| `schema` | `ontokin.current-host-readback-node-source/0.2.0` | constant |
| `contract` | `ontokin.current-host-readback/0.2.0` | constant |
| `archive` | `{name: "node-v24.22.1-darwin-arm64.tar.gz", sha256, size_bytes}` | constant name; plan `archive` |
| `checksum_file` | `{url: "https://nodejs.org/dist/v24.22.1/SHASUMS256.txt", sha256: "fdfbffc9…df9dc4", size_bytes: 3171}` | constants of contract section 3 |
| `signature_check` | `{status, detail}` | plan `node_source` |
| `member_inventory_sha256` | section 3 | plan `members` |
| `extracted` | `{member: "node-v24.22.1-darwin-arm64/bin/node", path: "bin/node", sha256, size_bytes, mode}` | constants; plan `files["bin/node"]` |

The plan freezes `files["NODE-SOURCE.json"]` as `{sha256, size_bytes, mode}`:
- **Plan check:** the built bytes must match the frozen digest and size, even in a dry run.
- **Staging:** the bytes are written with an exclusive create and the planned mode.
- **Exact-tree check:** the file is covered before publication, after publication and on reuse.

The destination holds exactly `bin/`, `bin/node` and `NODE-SOURCE.json`.

## 5. Executable check (MC05)

Both archive passes hash the Node member's bytes and compare them with the frozen
`files["bin/node"]` SHA-256 and size. The first 32 bytes must form a `mach_header_64` with:
- `magic` `0xfeedfacf`, little-endian, so a universal (fat) or big-endian file refuses;
- `cputype` `0x0100000c`;
- `filetype` `MH_EXECUTE` (2).

`cpusubtype` is recorded but not checked.

After staging, the exact-tree check binds the bytes and the mode `0o755`, and the header is read
again from the staged file before publication. The extracted file always takes the plan's mode,
never the member's. The load-command rules are the observer's (W3).

## 6. Publication and the `RENAME_EXCL` binding

**Staging.** The stage is a fresh `mkdtemp` under the destination's parent. Its `st_dev` must
equal the parent's.

**The call.** `rename_exclusive` loads `ctypes.CDLL("/usr/lib/libSystem.B.dylib",
use_errno=True).renamex_np` with `argtypes (c_char_p, c_char_p, c_uint)` and `restype c_int`. It
resets errno, calls `renamex_np(staged, destination, RENAME_EXCL)`, and raises `OSError(errno)`
on any nonzero return. Off Darwin it refuses before loading anything. The 0.2.0 route calls no
other rename, move or link function.

**Binding evidence.** The header files were read by path, and `xcrun` was not run. The installed
SDK link `MacOSX.sdk` points to `MacOSX26.5.sdk`.

| SDK file under `/Library/Developer/CommandLineTools/SDKs/` | Bytes | SHA-256 | Line |
| --- | ---: | --- | --- |
| `MacOSX26.5.sdk/usr/include/stdio.h` | 3,069 | `d2220614f42d3cb678ae0de176ba0ab3256e15fb45b3efdb5d17b8ac1f6a4b54` | 61: `#include <_stdio.h>` |
| `MacOSX26.5.sdk/usr/include/_stdio.h` | 20,526 | `8417242466f6df6890587974393e97bb0aeac8caeb80cdf82a4e03a97e6d4660` | 81: `#include <sys/stdio.h>` |
| `MacOSX26.5.sdk/usr/include/sys/stdio.h` | 2,415 | `a8078ae1cba1a46a66d0de6fe7f13bbc969cdb7e78fc2d4b9a5c5cdaaf16126b` | 37: `#define RENAME_EXCL                     0x00000004`; 52: `int renamex_np(const char *, const char *, unsigned int) …` |
| `MacOSX15.4.sdk/usr/include/stdio.h` | 3,069 | `d2220614f42d3cb678ae0de176ba0ab3256e15fb45b3efdb5d17b8ac1f6a4b54` | 61: `#include <_stdio.h>` |
| `MacOSX15.4.sdk/usr/include/_stdio.h` | 20,375 | `4b4cd0b2b9f470546f530b7a23f454ffe9be659762bd4bbbfc24319713022b5c` | 81: `#include <sys/stdio.h>` |
| `MacOSX15.4.sdk/usr/include/sys/stdio.h` | 2,364 | `903ab8dd48a74d66dda5dcd93f2f681c74f2ad54a9a87c5201d9ac059c51603c` | 37: the same `#define`; 51: the same prototype |

The define sits under `#if __DARWIN_C_LEVEL >= __DARWIN_C_FULL` (line 34). The top-level
`stdio.h` holds no define itself; it reaches `sys/stdio.h` through `<_stdio.h>` (finding F2). The
code comment above `RENAME_EXCL` cites this table.

**After a failed call.** The route first reads back the destination (`destination_after_error`)
and the owned stage (`stage_after_error`), and records both. Then:
- **`EEXIST`:** `REJECTED`, "Publication conflict: …; readback recorded, no retry". The owned
  stage is removed.
- **Any other errno, with the destination absent and the owned stage intact:** `REJECTED`,
  "Exclusive publication failed (NAME); nothing was published and there is no fallback rename".
  This covers `ENOTSUP`, `EXDEV` and `EINVAL`. The owned stage is removed.
- **Anything else:** `UNKNOWN`, "Publication outcome requires explicit reconciliation". A stage
  that has gone is not touched, and the destination is never removed.

No call is retried. A later invocation is a separate attempt: it reuses an exact tree or refuses.

## 7. Result: `ontokin.current-host-readback-install-result/0.2.0`

Reports and side files are exclusive creations in `provider._canonical` form: sorted keys, compact
separators and `ensure_ascii`.

| Key | When | Meaning |
| --- | --- | --- |
| `schema`, `contract` | always | the two identifiers |
| `purpose` | always | the plan's purpose, or `null` before the plan validates |
| `passed`, `state` | always | `INSTALLED_EXACT` and `ALREADY_PRESENT_EXACT` are the receipts. `DRY_RUN_READY` is no receipt. The other states are `REJECTED` and `UNKNOWN`. |
| `apply_requested` | always | the `--apply` flag |
| `execution_counts` | always | `{"node": 0, "ldd": 0, "checkers": 0}` |
| `operations` | always | `created_owned_stage` and `removed_owned_stage`, with paths and identities |
| `pins` | always | `{origin, node_archive_sha256, dependency_archive_sha256}`. `origin` is `adopted-contract` or `synthetic-test-seam`. It is `null` if the seam value is refused. |
| `labels` | always | `executor: "macos-arm64-local"`; `node_archive_sha256` and `node_executable` (for `selected-node`); `os_identity` and `python_inventory`: "not observed by the preparer"; `git_binding`: "not used: the preparer starts no process"; `run_kind`: "not applicable: installation preparation" (F5) |
| `preparer_source` | always | `{root, files_at_start}`: the bindings of the preparer, the provider helpers and `canonical.py` as read at start. This is a record, not a source qualification (D2). |
| `archive` | after the archive pass | `{sha256, size_bytes, members, expanded_bytes, symlinks, member_inventory_sha256, extracted_members}`. For `selected-node` it adds `executable` `{member, path, sha256, size_bytes, mode, macho}`. |
| `before` | after the readback | `{"state": "absent"}`, or `{"state": "complete_exact", "files", "directories"}` |
| `after`, `publication` | `INSTALLED_EXACT` | the exact readback, and `{call: "renamex_np", library, flag: "RENAME_EXCL", flag_value: 4}` |
| `error` | refusal | `{code, reason, state, cause}` |
| `publication_error`, `destination_after_error`, `stage_after_error` | failed call | `{errno, name, reason}` and the two readbacks |
| `cleanup_error` | cleanup refused | the failure, with `UNKNOWN` |

**Side files.**
- `<report>.preflight.json` is the report at preflight.
- `<report>.publication.json` is the intent recorded before the call: `{contract, source,
  destination, owned_stage, call: "renamex_np", mode: "RENAME_EXCL", state: "INTENT_RECORDED"}`.

**Refusal record.** The raised `CurrentHostBindingError` carries the same 0.2.0 report as
`refusal_record`, and the CLI prints it on stderr. That includes a CLI digest mismatch, for which
no file is written.

## 8. Decisions

- **D1, `isolated-control`.** In 0.1.0 this purpose exists only to test the generic installer
  without operational pins: its source must be `null`, it skips the purpose checks, and the CLI
  refuses it. Under 0.2.0 the explicit pin seam lets tests run the two operational purposes
  themselves, purpose policy included. A third purpose would test neither policy and would be a
  route around the pins, so it has no 0.2.0 form. The 0.2.0 entry refuses it as an unknown
  purpose.
- **D2, source binding.** The 0.1.0 route verifies its clean checkout through the provider's
  `_verify_source`, which uses a 0.1.0 source document and the ambient `git`. Under 0.2.0, the
  source document belongs to W5's provider, and Git is bound through W4's `git_executable()`.
  Neither existed during this work. The 0.2.0 route therefore starts no process:
  - the plan binds `source_root`, which must be this checkout;
  - the destination and the report stay outside it;
  - the result records the preparer files' bytes at start.

  It does not verify the commit, the tree, the clean state or the complete source inventory
  (question Q1).
- **D3, modes of unextracted Node members.** They are frozen exactly but not restricted, because
  they are never written. Only `bin/node` is written, always with `0o755`.
- **D4, signature status.** The status is recorded, and a `failed` status does not refuse. The
  contract makes the pin the trust anchor and records the signature check "either way" (Q2).
- **D5, report path.** The report path is bound only after its freshness checks, so a refused path
  is never written. This corrects finding F1 for 0.2.0.
- **D6, archive passes.** A dry run, a reuse and an install each read the whole archive. An
  install runs a validation pass before staging, so a bad archive refuses with nothing extracted.

## 9. Development tests

Every test uses a resolved temporary directory and synthetic inputs:
- `tar.gz` archives with the official member names;
- Mach-O header bytes that are never executed;
- plans built by the test.

The NODE-SOURCE.json bytes and the inventory digest are computed independently in the test
module.

A guard patches `subprocess` and the `os` fork, spawn and exec calls, and fails any start. No
test starts a process.

**Labels.** *Real* means a call of libSystem's `renamex_np`. *Simulated* means a patched boundary.
On a non-Darwin host, a test that needs `renamex_np` asserts the documented refusal instead, and
nothing is skipped. On this host, all 50 tests ran their Darwin branch.

**The test seam.** `SyntheticPins` (a frozen dataclass) can reach the preparer only through
`install_plan_v02(..., synthetic_pins=...)`:
- `validate_plan_v02` and the CLI use only the adopted pins;
- a seam result is labelled `pins.origin == "synthetic-test-seam"`;
- one test shows that the CLI cannot reach the seam.

| Test (class) | Covers | Creates or calls |
| --- | --- | --- |
| `test_MC01_changed_archive_bytes_refuse_before_any_member_is_read` (NodeArchivePolicy) | MC01 | archive with one byte flipped in place; `tarfile.open` never called |
| `test_MC01_plan_digest_other_than_the_pin_refuses_before_the_archive_is_opened` | MC01 | pin other than the archive's digest; archive never opened |
| `test_MC02_absolute_member_name_…`, `…_traversing_member_name_…` (3 names), `…_duplicate_member_name_…`, `…_hard_link_member_…`, `…_character_device_member_…`, `…_block_device_member_…`, `…_fifo_member_…`, `…_undeclared_member_…`, `…_escaping_link_target_…` (4 targets) | MC02, each case separately | archives with the bad entry; refused in the validation pass; no stage, no destination |
| `test_MC02_inventory_cannot_declare_a_forbidden_member` | MC02 at plan level | 13 inventory edits, NODE-SOURCE.json re-frozen; refused for the named rule; archive never opened |
| `test_MC03_declared_links_are_accepted_not_extracted_or_followed_dry_run` | MC03 | dry run; only the Node member's data is read; no link created |
| `test_MC04_node_member_missing_refuses`, `test_MC04_node_member_not_a_declared_regular_file_refuses` | MC04 | archive or inventory without the member, or with it as a link, hard link or directory |
| `test_MC05_executable_not_thin_arm64_macho_refuses` | MC05 | seven non-conforming headers (fat, 32-bit, big-endian, x86_64, dylib, truncated, script) |
| `test_MC05_executable_digest_size_or_mode_other_than_frozen_refuses` | MC05 | frozen digest, size or mode other than the bytes |
| `test_MC05_staged_mode_change_refuses_before_publication` | MC05 | **simulated**: `os.fchmod` applies `0o700`; refused before `renamex_np` |
| `test_dry_run_reads_the_archive_and_creates_only_the_preflight_record` | dry run | report and preflight files only |
| `test_node_source_bytes_are_built_from_the_plan_and_must_equal_the_frozen_bytes` | 4.2 | eight plan edits |
| `test_member_inventory_digest_is_sha256_of_canonical_json` | digest rule | order independence; non-ASCII refusal |
| `test_MC03_install_publishes_exactly_bin_node_and_node_source` (Publication) | MC03, receipts | **real**: one install, one `renamex_np`; then `ALREADY_PRESENT_EXACT` |
| `test_MC15_real_renamex_np_refuses_an_existing_destination` | MC15 | **real**: `EEXIST` for an empty directory, a populated directory and a file; nothing replaced |
| `test_MC15_real_conflict_destination_appears_between_staging_and_publication` | MC15 | **real**: another writer creates the destination just before the call; `EEXIST`; content untouched; stage removed |
| `test_MC16_real_failing_calls_refuse_without_fallback` | MC16 | **real**: `EINVAL` (target inside the source), and `EXDEV` to a never-created name in the checkout's directory when the checkout's `st_dev` differs from the temporary directory's, as on this host |
| `test_MC16_real_failing_call_inside_the_flow_refuses_without_fallback` | MC16 | **real** kernel failures (`EINVAL`, `EXDEV`) in the install flow; the test redirects only the call's target argument |
| `test_MC16_simulated_enotsup_refuses_without_fallback` | MC16 | **simulated**: the ctypes call returns -1 with `ENOTSUP` |
| `test_uncertain_publication_is_unknown_and_read_back_before_any_retry` | 0.1.0 rule | **simulated** lost reply after a **real** call: `UNKNOWN`, readback recorded, one call; later reuse |
| `test_apply_off_darwin_refuses_before_staging` | platform | **simulated** platform `linux` |
| `test_rename_excl_value_and_libsystem_binding` | binding | loads libSystem; starts nothing |
| `test_exact_existing_tree_is_reused_already_present_exact` (ExistingDestination) | reuse | hand-built exact tree; apply and dry run |
| `test_MC35_partial_…`, `…_changed_…` (6), `…_extra_destination_entry_…` (`.DS_Store`, file, directory), `…_linked_…` (4), `…_inaccessible_…` (3, mode `0`), `…_destination_that_is_a_file_…` | MC35 | before and after snapshots equal; no stage; no call |
| `test_MC34_unsafe_entries_refuse_before_extraction` (RetainedDependencies) | MC34 | eight unsafe entries in a synthetic reader archive |
| `test_MC34_inventory_cannot_declare_links_special_entries_or_unexpected_modes` | MC34 | five inventory edits |
| `test_dependency_targets_must_equal_the_pinned_files`, `test_adopted_dependency_pin_is_the_c195_archive` | pins | refusals only |
| `test_dependency_install_and_exact_reuse` | receipts | **real**: one install, one `renamex_np`; then reuse |
| `test_v02_entry_refuses_a_v01_plan`, `test_v01_entry_refuses_a_v02_plan`, `test_v02_plan_naming_another_contract_or_purpose_is_refused` (VersionSeparation) | version refusal | each entry with the other's plan |
| `test_v02_plan_paths_bind_this_checkout_and_stay_outside_it` | paths | six cases; checkout names unique per run and never created |
| `test_cli_dispatches_…_adopted_pin_only`, `test_cli_v02_digest_mismatch_…`, `test_cli_keeps_the_v01_route_for_v01_plans` | dispatch | `main` in-process; no process started |
| `test_seam_accepts_only_synthetic_pins` | seam | refusals only |

**Run:** `TMPDIR="$(cd "$TMPDIR" && pwd -P)/" .venv/bin/python -B -m unittest
tests.test_prepare_current_host_readback_v02 -v`.

## 10. Checks on this host

- **The new module:** 50 tests, all passed. They also pass under
  `unittest discover -s tests -p test_prepare_current_host_readback_v02.py`.
- **0.1.0 sources:** every 0.1.0 definition is byte-identical, compared by AST source segment.
  `main` differs only by the two dispatch lines.
- **`tests.test_current_host_readback_provider`:** 25 tests; 22 pass, with 2 failures and 1
  error. That is identical to the baseline at `f3a5acf8` on this host, and the normalized output
  is byte-identical. The three failures are pre-existing: the 0.1.0 publication is Linux-only.
- **`tests.test_current_host_inspection_v01`:** 135 tests, with 64 failures and 8 errors.
  That is identical to the baseline, and the normalized output is byte-identical.
- **Mutation check:** 15 source-level mutations of the 0.2.0 route, run in a scratch harness,
  were each detected by at least one test.
- **Whitespace:** `git diff --check` is clean, both files are ASCII and end with a newline.

## 11. Findings

- **F1, 0.1.0, unchanged as instructed.** `install_plan` binds its report path before checking
  it, so its `finally` block writes a report even to a refused path. A report path that already
  exists turns the refusal into `CH-EVIDENCE`/`UNKNOWN`. A report path inside the checkout gets a
  report written into the checkout. An early draft of the 0.2.0 route had the same order: one
  development run wrote a synthetic refusal report to the checkout root. It was preserved in the
  worker evidence and removed, and the checkout is clean. The 0.2.0 route now binds the path only
  after the checks (D5).
- **F2.** The `RENAME_EXCL` define is in `usr/include/sys/stdio.h`. The top-level `stdio.h` named
  by the assignment includes it through `<_stdio.h>` but holds no define itself.
- **F3, pre-existing.** The 0.1.0 preparer and inspector tests listed above fail on Darwin. Their
  expectations are unchanged.
- **F4.** The proposed AMENDMENT-001 (`5dc76ccf`) says every 0.2.0 result names the design
  revision it follows. The install result has no such field yet.
- **F5.** Of the labels in plan section 5, the preparer cannot observe the OS identity, the Python
  inventory digest or the Git binding. The result says so instead of inventing values.

## 12. Open questions

- **Q1.** Should the 0.2.0 preparer also verify its checkout's commit, tree and clean state,
  through W4's `git_executable()` and W5's `/0.2.0` source document, as the 0.1.0 route does with
  its own?
- **Q2.** Should a `failed` signature-check status refuse preparation?
- **Q3.** What design-revision field and value should results carry, once AMENDMENT-001's
  adoption is settled?
- **Q4.** Should the install result carry OS-identity labels through W3's exported reader?
- **Q5.** Who adapts the inspector-side receipt rule (`_check_installation`) to this result and
  layout, and should it compare `source_root`?
- **Q6.** A non-ASCII member name, or a tar mode field above `0o7777`, would refuse. Whether the
  official archive has either is not verified here. MP confirms it when the independent author
  freezes the real inventory.
