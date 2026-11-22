# C271 P18 independent exact-source and adapter review

## Verdict and scope

**Candidate 001 passes this independent implementation review. There are no mandatory findings and no design blocker.** The verdict applies only to the three exact source identities below and the adopted P16/P17 metadata-only implementation surface. It does not establish actual-host readiness, successful dynamic loading, TLS behavior, H0/H1 qualification, or authority for another technical phase.

The reviewer authored no product or candidate test changes. The implementation agent authored the production module and shared P16/P17 route engine; the director authored the P17 thin adapter. The reviewer made no repository, Git/index, external-system, or nested-agent changes. The only review artifacts and test-created files are in `/workspace/scratch/cf3e30ae3c50/independent-review`.

| Candidate file | Bytes | SHA-256 |
| --- | ---: | --- |
| `prototypes/static_tray_v01/current_host_inspection_v01.py` | 196305 | `e14542e45deb200bb97f2a591c94bdd19916a1d33dcb3ce9f631816b98e0c206` |
| `tests/test_current_host_libc_plt_metadata_v01.py` | 27946 | `661b7a96aae871e83fcfc4f1fcf975467ac81400961dad81c19283d13f2978d7` |
| `tests/test_current_host_libc_static_tls_flags_v01.py` | 1211 | `d91ad24b3fc62d1b8abd4e8ac5aa68a8459d20a54224a102dbd3ba181a0523d5` |

The independently copied repository bytes, implementer candidate copies, and announced freeze identities agree. These are frozen, uncommitted source changes above documentary checkpoint `cd49c26e39fda0d0cfc875dbae83d618b9877198`, tree `56665edcd07d4704da24560fcd0dd7fd0a933c71`. They are not attributed to that checkpoint's clean tree. The production baseline is retained revision `8dc78c0a0ba6b69f502d35e0bbd1727c3c2ab7e8`, module SHA-256 `a8274d56076562a91d26b3cdd2f614fce6fd509733e4939b225dff2ddca09db4`.

## Independent evidence

One guarded run executed **412 methods**: 73 P16, 41 P17, 135 inherited inspector, 40 inherited ELF-mapping, 96 inherited origin, and 27 selected provider/driver compatibility methods. All passed, with **zero failures, errors, skips, expected failures, or unexpected successes**. The run completed at `2026-11-22T19:35:51.813658+00:00`; measured suite time was 7.584 seconds. No actual process operation was attempted, and all repository Python source identities were unchanged across the run.

Exact command:

```sh
python -B /workspace/scratch/cf3e30ae3c50/independent-review/run_guarded_review.py --repo /workspace/scratch/cf3e30ae3c50/OntoKin --freeze /workspace/scratch/cf3e30ae3c50/independent-review/CANDIDATE-FREEZE.json --out /workspace/scratch/cf3e30ae3c50/independent-review/attempt001 --group all
```

`attempt001/REQUEST.json` records every selected method identity, interpreter/version, environment, source attribution, and exclusion. `attempt001/UNITTEST.log` and `attempt001/RESULT.json` retain the results. `SOURCE-INVENTORY-BEFORE.json`, `SOURCE-INVENTORY-AFTER.json`, `LOADED-REPO-MODULES.json`, and `source-snapshot/` retain the source evidence. Bytecode creation was disabled. A Python audit hook installed before product/test imports rejects real subprocess, shell, fork, spawn, exec, and signal operations. Existing inert test guards remain active.

The reviewer separately audited all 114 retained observations against independently materialized frozen contexts and literal expectations. That audit does not import the product or use the adapter's assertion helpers. It checks exact context/oracle equality, image bytes, full metadata, refusal code/reason/state/details/cause, fault reachability, callback identity evidence, descriptor close counts, bounded read offsets, and expected reader/binding traces. Every row passed. See `OBSERVATION-AUDIT.json`, SHA-256 `892f1614fabf6471483ec8a02b707cc0a4cf48d3ca78501ef6eba08deeee180e`.

## Frozen authority and adapter fidelity

The review obligations were written before the candidate froze. The reviewer read the adopted P16/P17 decisions, control contracts, all 114 original control/expectation rows, and all contexts. The entire original 2,943-line production module and affected inherited test sources were read; the candidate was reviewed as an independently computed complete diff plus surrounding caller context. The full shared adapter and P17 thin adapter were read separately.

Both adopted archives were independently materialized without running their construction or verification scripts. Their complete inventory, CRC, file hashes, byte counts, inert modes, and manifest relationships were verified:

| Design | Archive SHA-256 | Manifest SHA-256 | Expectation SHA-256 |
| --- | --- | --- | --- |
| P16 | `05d1cbe971678b8f505795e436f2bd096b81848f68b4f9da6adc64392f6fb5af` | `61b18ceb15d3ee05d3022c60941ccbbce9c3e08bac148c7750da9f6588091156` | `33a17cc66604f8b57be88dae7dd05a4bec066c0eaa191fc08400cfc79e18137e` |
| P17 | `d59d4d71a9f73065a000ae3de8233beb82ad5a33a3b526de93debb845f0d86c4` | `5561dcd3cf718362f0716bb0c3ebf7fcf273befa1f6348f9996331d151b7c89b` | `9ec492d20fe2184414d818fca3ff37bcfdf1a20416dcb042d0bc2667456c9bd8` |

`FrozenCorpus` authenticates the entire adopted archive and independent manifest/oracle identities before selecting a case. The shared engine selects behavior by each frozen route, not a case ID. It compares the literal expectation without rewriting it. The per-case `image` descriptor determines the raw input. This matters because 35 P16 contexts retain a shared `actual_fixture_bytes` annotation that differs from the individual image; the adapter correctly uses the individual image. The independent audit authenticated 47 P16 and 30 P17 image-bearing contexts.

Binding positives call the actual pure relation primitive using explicitly mocked logical descriptors. Their records correctly state that no actual file binding or operational plan was proved. Coherent synthetic descriptors still fail the unchanged selected pin. D01/D02 recheck controls disclose prerequisite mocks and retain the actual `_recheck` → `_check_resolution` → `_prepare_libc_plt_policy` → `_check_libc_plt_bindings` chain. The binding fault is reached once, and the outer CHI-DRIFT wrapper retains its exact underlying CHI-INSPECTOR exception. X01/X02 use the permitted already-bound private-policy seam; actual subject dispatch reaches the new raw parser, while another image reaches the conservative public parser.

Callback tests inject only at reached production checkpoints or actual descriptor I/O. The opened descriptor is closed exactly once on success, refusal, and each post-open fault. RuntimeError and HostInspectionError sentinels retain identity; the latter retains details. The dynamic-read OSError retains its original cause. No synthetic pre-reader exception supplies a passing result.

## Production findings

### Version selection and conservative defaults

The new exact schema/profile pairs are separate 0.1.2 PLT and 0.1.3 PLT/static-TLS branches. Pair selection precedes the closed `libc_plt` shape. The object has only schema, subject, and loader; each descriptor has only path, digest, byte count, and mode. Caller-selected masks, approval labels, and extra fields confer no authority. The public parser, old literal plan, old origin plan, and P16 flags behavior remain conservative. The old branches retain their previous ordering and error details.

The independent AST comparison found **no changes to existing constants, no removed symbols, and 96 unchanged existing function/class bodies**. Existing Python/Node pins, resource limits, environment, consumer contracts, output schemas, and stdout predicates are preserved. All inspected inherited test files remain byte-identical to baseline. `SOURCE-STRUCTURAL-AUDIT.json` records the exact 11 modified existing symbols and 10 added private symbols.

### Binding and operational dispatch

The selected author's actual Python bytes are parsed under its existing origin rule. Actual `libc.so.6` needed-name and interpreter observations enter the new proof. The selected Python image row must be unique; its declared metadata must equal those actual observations. The named dependency must have the required declared role and matching host/runtime alias resolution. Full aliases, host/runtime bindings, unique libc/loader descriptors, and selected descriptors must agree. The subject is excluded from the selected Python, Node, Git, inspector script/interpreter, ELF interpreter, and extension paths, including their resolved aliases. The selected libc and loader are distinct.

The pure relation primitive preserves **role → descriptor equality → fixed pins**. The operational constructor then invokes the unchanged real `_bound` reader for both canonical files before freezing the private policy. No production pin is substituted, and no synthetic completeness label enters the product. Only the exact policy subject receives the new parser. Every other image retains its applicable earlier parser.

**Director question: image lookup order.** `_prepare_libc_plt_policy` obtains the Python, subject, and loader rows before calling the pure primitive. On the actual operational route, `_check_resolution` has already validated every image-row shape and rejected duplicate canonical image paths; it also requires and authenticates the Python row before metadata parsing. The constructor's lookup requires exactly one subject and loader row, so missing rows fail closed with PLT-DESCRIPTORS. Its direct defensive duplicate check does the same if the private constructor is called outside that predecessor. These guards can precede the pure role diagnostic on a compound malformed context, but the frozen contract explicitly scopes role/descriptor/pin precedence to the **pure binding primitive**; that primitive preserves the required order. No frozen complete operational-plan diagnostic is replaced, and no missing/duplicate row can obtain a private policy or raw admission. No corrective change is required.

### Raw metadata policy and ordering

The exception adds exactly `0x70000000`, `0x70000001`, and `0x70000003`, only on the selected private x86-64 ET_DYN route. Structural and dynamic-table termination checks remain first, followed by architecture/type, the exact unknown-tag predicate, and one occurrence of each trio tag. Values are read as unsigned metadata and are never used as an address, allocation, read length, or loop bound. Zero, maximum, reordered, and inconsistent values exercise that rule without extra output fields.

P16 retains absent/zero/eight DT_FLAGS behavior. P17 additionally accepts exactly 24. Sixteen alone, extra bits, duplicates, and the old forbidden DT_FLAGS_1 bits still refuse. Unknown-tag, architecture, and trio failures preserve their earlier precedence; later string/path/identity checks remain live. Metadata still has exactly nine fields. This does not validate PT_TLS layout or relocations.

### Fresh proof, snapshot, and launch ordering

For both new branches, complete host/author binding, origin/resolution proof, and required path guards execute before `_load_helpers`, source Git reads, or commands. The remainder of the original closure, needed-edge, interpreter, architecture, search-directory, alias, and loader-input checks still executes after raw parsing.

**Director question: local Python metadata reuse.** `origin_images` and `libc_policy` are initialized within each `_check_resolution` call. The Python metadata is read from actual bytes at the start of that proof, checked against the declared row, and used to construct the current libc binding proof. Its local reuse in the immediately following image loop prevents a redundant parser call; that loop still calls `_bound` again. Neither object is stored on the validated plan or reused from a prior invocation. Each `_recheck` calls the full resolution procedure afresh, reconstructing policies, metadata, bindings, pins, closure checks, and guards. This satisfies the prohibition on cached prior admission.

Both selected files must already be equal members of the host/runtime file maps. The unchanged `_input_snapshot` records those maps, and `_launch_check` validates their identities and all guards under the existing command clock. New branches retain the origin kernel witness and CHI-DRIFT cause/wrapper behavior. The real recheck observations corroborate the fault path; no positive actual-host plan is claimed.

## Compatibility selection and exclusions

The 27 selected methods are the 18 `ProviderSelectionAndFiles` methods plus nine driver selection/refusal methods. They cover external selection, digest/shape ordering, ordinary-file identity, copied-source inventory, and no-child refusal at preparation or prelaunch. The provider method that checks preservation of the original seven compares their source bodies and uses mocked setup; it does not replay that routine.

`CurrentHostDriverBindingTests.test_explicit_pair_reaches_real_python_child_without_ambient_override` is **not selected**, rather than counted as skipped or passed. The seven installer tests and broad 31-method local-check suite are also not selected because they do not belong to the affected profile-selection and binding surface. The exact selected identities and rationale are in `REVIEW-OBLIGATIONS.json`, `INHERITED-TEST-INVENTORY.json`, and the run request.

N57 remains external review evidence. It is absent from runtime pass/skip accounting. Original-seven/full readback, real-host inspection, Node, ldd, dynamic-loader execution, H0, H1, and a second technical phase were not run. The review does not infer CI status or authorize main integration.

## Preservation, limitations, and retained failures

There were no candidate test failures or unresolved technical review gaps. Read-only preparation mistakes are retained rather than hidden: initial overlarge text outputs required bounded rereads; two JSON-inspection helpers initially used the wrong expectation shape; an attempted P16 readable-mirror fixture access exposed that full fixtures live only in the archive; and the independent byte auditor initially assumed P16's `size_bytes` key for P17's `bytes` descriptor key. Each failed before any product invocation or fixture mutation and was corrected against the unchanged source schema. The audit records the corrected complete coverage. There was no retest of the candidate after a failed product run, because its single independent run passed.

Startup continuity remains established by `ledger-review/REPORT.md` and `READSET.json`. Earlier P17 pending markers are reconciled by the director's materialized saved-file evidence and `audit/P17-RECONCILIATION.json` with 62 passing groups, together with the live PR/issue markers. Early P18 recovery was already confirmed by `state/EARLY-RECOVERY-RECEIPT.json`. Those records are evidence of continuity, not new permissions. Canonical publication, final delivery packaging, and saved-byte verification remain the director's responsibility.
