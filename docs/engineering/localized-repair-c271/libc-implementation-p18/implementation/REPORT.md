# C271 P18 implementation candidate001

## Verdict and ownership

The bounded implementation is complete and frozen for independent review. Both required executed cohorts passed: 114 frozen P16/P17 controls and 271 inherited methods, with zero failures, errors or skips. This is an implementer report, not independent acceptance, host qualification or parent completion.

The implementer changed only `prototypes/static_tray_v01/current_host_inspection_v01.py` and new `tests/test_current_host_libc_plt_metadata_v01.py`. The Director authored the disjoint new `tests/test_current_host_libc_static_tls_flags_v01.py`; its exact source is included in the same freeze. No existing test, fixture, oracle, contract, pin, limit or canonical record was edited by this worker. No Git/index or external write was performed.

Documentary base: `cd49c26e39fda0d0cfc875dbae83d618b9877198`. Production source before implementation: 183,913 bytes, SHA-256 `a8274d56076562a91d26b3cdd2f614fce6fd509733e4939b225dff2ddca09db4`. The tested work is identified by exact dirty-file hashes and preserved source copies, not described as a committed implementation.

## Exact candidate

`CANDIDATE-FREEZE.json` binds the three original repository paths to copies under `candidate001/`.

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| Inspection module | 196305 | e14542e45deb200bb97f2a591c94bdd19916a1d33dcb3ce9f631816b98e0c206 |
| P16 adapter and shared engine | 27946 | 661b7a96aae871e83fcfc4f1fcf975467ac81400961dad81c19283d13f2978d7 |
| P17 corpus adapter | 1211 | d91ad24b3fc62d1b8abd4e8ac5aa68a8459d20a54224a102dbd3ba181a0523d5 |

No further candidate edit is permitted without a review finding or Director coordination.

## Behavior and source rationale

The exact /0.1.2 pair selects the three-tag metadata rule. The separate /0.1.3 pair selects the same tag rule plus the exact additional flags value24. The prior public parser, /0.1.0, /0.1.1 and P16 flags predicate retain their previous meanings. The new object remains closed to `schema`, `subject` and `loader`; descriptor validation does not admit caller masks or approval fields.

`_check_resolution` reads the actual selected Python metadata before considering any libc row, regardless of image-row order. `_prepare_libc_plt_policy` then checks the selected needed edge and forbidden roles, complete alias/file/image descriptor equality, and exact retained libc and loader pins. It uses unchanged `_bound` actual-file checks before returning an immutable policy. The actual operational caller supplies this policy to `_read_plan_elf_metadata` only for the selected libc path. Pure mocked binding positives cannot produce an operational admission result.

All three origin-derived profiles enter the existing early resolution/guard branch in `_validate`, before helper imports and source Git reads. They also enter the same complete early branch in `_recheck`; each call re-observes Python metadata and reconstructs the libc policy rather than retaining an admitted result. Existing origin proof, loader closure, kernel witness, input snapshot and final launch identity checks remain in force. Equality with host/runtime file maps proves that both new descriptors are already covered by snapshots; named aliases remain subject to the unchanged full path-chain guards.

The private reader preserves the required sequence: inherited structural/terminator checks, x86-64 ET_DYN restriction, exact unknown-tag check, complete once-only trio, flags, then string/path/identity guards. Trio values are decoded but never dereferenced or used as allocation/read/loop bounds. The tag scan counts only three fixed tags within the existing bounded table. /0.1.3 adds only equality with24 beside0/8; it does not expand the old mask. Flags-one and duplicate-entry checks remain unchanged. Named callbacks exist only on the private new routes, and the original descriptor-finally close remains the sole close path.

## Execution and adapter boundaries

| Attempt | Exact selection | Result |
| --- | --- | --- |
| attempt001 | 73 P16 frozen methods +41 P17 frozen methods | 114 passed;0 failures/errors/skips |
| attempt002 | 135 inspection +40 mapping +96 origin methods | 271 passed;0 failures/errors/skips |

The commands, actual interpreter/platform, timestamps, duration, per-method outcomes, full logs and exact source copies are in each attempt’s `RESULTS.json`, `run.log` and `source/`. `run_focused.py` is the retained execution harness. No failed execution attempt occurred. Earlier output truncations were read/display limitations, separately recorded in `SOURCE-READSET.json`; they are not erased or counted as tests.

The two new adapters authenticate the entire original ZIP payloads and independently pinned manifests/oracles before consuming cases. Each raw-reader control uses its own `image` descriptor, never the shared `actual_fixture_bytes` baseline. Complete inputs and literal expectations remain unchanged. Materialized files retain their original inert modes.

Metadata cases call the real raw reader against actual inert bytes. Selector cases call only the actual selector. Binding cases call the actual pure relation primitive with labelled logical observations. D controls first establish their mocked baseline, then invoke actual `_recheck` → `_check_resolution` → `_prepare_libc_plt_policy` → `_check_libc_plt_bindings`; explicitly mocked earlier host checks expose the new binding fault, and no raw libc call follows it. X controls use the declared mocked internal-policy seam and record the actual selected reader. No production pin constant is replaced. The adapter branches on frozen route/fault descriptors, never on case identity to manufacture an exception.

Fault controls inject only after the actual named callback/I/O boundary is reached. They retain actual open/close descriptors, pread ranges, callback traces, exception identity and original details. Every raw success, refusal and post-open fault observes exactly one close of the actual opened descriptor. `attempt001/cases/{p16,p17}/observations/` retains each full record.

N57 remains external: `attempt002/origin-cases/EXTERNAL-REVIEW-OBLIGATION.json` is retained. It is neither a runtime pass nor a skip.

## Preservation and remaining gates

`STATIC-PRESERVATION.json` records the exact11 affected existing functions and10 new functions. Public `read_elf_metadata` has an identical AST. Every preexisting module constant has an identical AST. The complete tail beginning at `_utc`, including evidence/process and public execution entry points, is byte-identical. All25 other files in the P16 protected-source list retain their exact hashes. `PRODUCTION-DIFF.patch` records the source delta. These are structural/preservation checks; independent semantic review must still assess exact caller order and adapter fidelity.

Required pending actions belong to the Director and independent reviewer: exact source/adapter review, applicable compatibility checks, documentary/whole-scope preservation checks, conditional retained-branch publication, verified partial saved handoff and separate receipt. This worker has not claimed these gates.

No actual host inspection, H0/H1, runtime preparation/install, Node/ldd, original-seven/full routine, native/model/hosted execution, main lease/integration or parent closure occurred. No TLS allocation, relocation, PLT execution safety or operational-plan positive is established. Full routine R03 and parent R03–R05 remain unmet. There is no active worker-owned process or unknown write.
