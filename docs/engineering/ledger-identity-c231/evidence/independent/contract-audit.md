# C231 independent contract and dependency audit

## Decision

**An in-place correction to `prototypes/static_tray_admission_c201/ledger.py` is permitted within the selected repair. A separate implementation path or ledger schema is not required merely to restore the existing file-replacement rejection contract.** No contract blocker was found. This is a static design/preservation decision, not implementation approval or a test result.

The current component promises that missing, replaced, truncated, aliased, nonregular or overlarge authority files stop progression (`LEDGER-C204.md`, durable authority section). C230 demonstrates a violation: identical bytes and reused numeric device/inode values can pass the live-capability check. Holding the original file objects and retaining the existing byte/path checks repairs that implementation defect; it does not change schedule semantics, event schemas, budgets or release acceptance.

The C210 scope decision freezes four C201 protocol documents and preserves C199/C200 qualified source and closed schedules. It does not freeze every later C201 implementation byte. The ledger was introduced after that protocol. I parsed every current frozen binding: ledger.py is absent from all 42 protocol/normative/qualified-role/source records and all 301 inherited locked-input records. Every checked historical binding currently matches. These inventories overlap and their counts must not be summed as distinct files.

The operational distinction matters: historical evidence remains tied to its original source revision. New checks must name the repaired revision. Never edit an old digest to make changed source look like the historical source.

## Reviewed baseline and boundaries

- Source: `099339f9b320a2c47a0ca2d275468c6e5f1b09e9`
- Tree: `e940be2a1a9bb7def41d20daf06fdf9736942585`
- Reviewed at UTC: 2026-11-13T20:55:27.662333+00:00
- Original ledger SHA-256: `0b4cee3520ba7a0002ec6958b37511e4b541a9823c8a1bc955214ec132924243`
- Original complete ledger test SHA-256: `ea363ae96a8e8ed441da0992fca870047f81f4deabb528786bca9306d85c7b1f`
- Original failing method SHA-256 (its physical definition lines, including indentation): `9dc9ba061bbae777cfe6ab83f1be776bbff5a04af29c6c2f74ae92049fa1ffa5`

Read AGENTS.md, current GOAL.md, C210/DECISION.md, OK-ENG-006, C230/NEXT-TASK.md, the original C204 contract audit/review/component document, current ledger and schedule/input-lock relationships, and relevant original tests. No product code was imported or executed. No aggregate, native application, subprocess lifecycle fixture or consumed diagnosis was run. No repository file was modified.

## What is frozen

The independently approved protocol review pins exactly these four documents:

| Path | SHA-256 |
|---|---|
| `docs/engineering/static-tray-admission-c201/README.md` | `414fcf481d61b36bfe7effc110894dd70744efc8f16417db94438962a8e65889` |
| `docs/engineering/static-tray-admission-c201/ADMISSION.md` | `2dd7b250dae4afbbcc363a84f14590e7746016274db6c62e977761953572119b` |
| `docs/engineering/static-tray-admission-c201/ADMISSION.json` | `f1bd2895cc448f5a1ecb6495814c261dfeba8fecab8ea266e274a35475386064` |
| `docs/engineering/static-tray-admission-c201/IMPLEMENTATION-NEXT.md` | `0d43582742824e0421274e1083a915f4e53d7effa17e52513d39e1a5d3f514bd` |

The 20 qualified roles point to the historical static-tray-v01 constructor, receiver, supervisor, store, canonical/source helpers, independent reader/decoder/audit/expectations/corruption writer and historical coordinator/transaction/lock/format/probe/settings. Those paths remain exact. The normative/source closures and C199/C200 input locks remain exact. The fixed C201 schedule, protocol-review hash, JSON marker/event schemas, 4 MiB journal ceiling, original diagnostics, nonblocking/no-follow checks, and false native-readiness/admission flags are unchanged requirements.

The original test `test_corrupt_replaced_aliased_or_missing_files_poison_live_capability` must remain byte-identical. Preserving the entire original 36-method test module is the clearest implementation boundary. Add controls in a new test file.

## Active dependencies

| Component | Relationship to ledger | Required handling |
|---|---|---|
| `input_lock.py` | Imports `JOURNAL` and `MARKER`; `ADMISSION_ROLES` fixes the ledger role path. | Keep path and constants unchanged. A new executable lock must bind current bytes and receive fresh independent review. |
| `transaction.py` | Imports `input_lock`. | Preserve its source and behavior; include affected component checks. |
| `readback_binding.py` | Imports `input_lock` and `transaction`. | Preserve source/behavior and include affected component checks. |
| `readback_entries.py` | Imports `input_lock`, `readback_binding` and `transaction`. | Preserve source/behavior and include affected component checks. |
| Six existing C201 test modules | Direct or transitive use of the modules above. | Their AST inventory contains 284 existing test methods. Full selected execution counts must be measured, not inferred from this count. |
| Original ledger test module | Directly imports the live ledger and module seams. | Run unchanged; do not replace expected errors or alter its replacement operation. |

The input-lock validator distinguishes fixed historical bindings from newly reviewed executable roles. At its frozen-record check, current ledger.py is not a fixed historical item. Later it checks every actual role input against the submitted binding and trusted source/closure identities. Therefore old real executable locks would correctly reject a modified ledger until a newly reviewed source/closure/approval is prepared. This audit found no production C201 lock or readiness receipt: the component documentation explicitly reports those as pending. Its unit-test fixture supplies synthetic future-role files and hashes their bytes; it is not a native approval.

No active nonhistorical Python source or test contains the old ledger SHA as an expected literal. Source inspection found 33 text files containing that SHA, with 51 structured record locations. They are listed in `historical-ledger-pin-records.json`; all are historical evidence or consumed diagnostic plans. The full path-reference inventory, including records that bind a larger source tree rather than this individual hash, is in `contract-dependency-inventory.json`.

## Historical bindings that must intentionally stop matching live modified source

| Record family | Meaning after repair |
|---|---|
| C204 implementation/review/adversarial records | Remain evidence for original ledger bytes and original source commit. The later defect discovery remains visible. |
| C205 input-lock candidate and equality records | Remain original component evidence; no pin update. |
| C206 transaction candidate and equality records | Remain original transaction/dependency evidence; new affected tests bind repaired source separately. |
| C207 cwd check/binding/equality records | Remain original results; no source-equivalence claim is carried forward. |
| C208 readback source/review/publication records | Remain original source-bound evidence and timing/failure dispositions. |
| C209 entry-binding input/equality records | Remain original component evidence. |
| C210 regression exact-input bindings | Remain original aggregate/failure provenance. |
| C229 and C230 run plans, preparation and observed results | Consumed immutable plans. Their source/file guards must reject changed code; they must not be repinned or replayed. |
| C224/C226/C228 aggregate source identities and prior handoff manifests | Continue to identify their original commit/tree and immutable payload. A repair does not rewrite or pass their outcomes. |

A historical digest's disagreement with a new live file is expected source evolution, not a reason to rewrite evidence. The saved/restorable source bundle must retain the original commit and distinct unpublished histories so an auditor can recover those exact bytes. All existing evidence files and historical manifest hashes remain unchanged in the successor package. Opaque ZIP/bundle internals were not reinterpreted as active locks; their exact retained hashes and source histories preserve the prior evidence.

## Resource lifecycle requirements for implementation review

A retained descriptor must refer to the original file from successful exclusive creation until the capability becomes unusable. Numeric inode comparison alone is insufficient after releasing the original file. Continue checking regular-file type/link count, the original retained object's identity, each named path's bytes/identity and bounded nonblocking opens; do not swap a path check for an unverified descriptor write.

Review each release boundary independently:

1. Partial creation: no live object escapes on marker write/chmod/fsync, directory fsync, journal creation or initial append failure. Release every acquired descriptor while preserving all partial files.
2. Successful lifetime: both authority file objects stay retained while the capability can append. Retention prevents the original inode from being recycled under a new file.
3. Terminal observations: explicit stop, rejected ordering/identity, failed stage/cleanup/promotion/control, and successful final completion all release handles after preventing further mutations.
4. Uncertainty: a failed/partial append or interruption poisons the handle before cleanup. Cleanup must not make a stale live capability usable or mask the original causal error.
5. Object disposal: define explicit close/context/disposal behavior, preserve durable authority and consumption, and make cleanup idempotent. Clear owned descriptor slots before close so repeated cleanup cannot close a newly reused descriptor number.
6. Process boundaries: retained descriptors must not leak across exec. A PID-mismatched object must reject before taking a possibly inherited locked mutex. In a fork child, release only the child's copied handles; this cannot close the parent's descriptor table. State the limit if controls simulate this condition rather than executing a fork.

Ordinary path mutation and explicit lifecycle controls are sufficient for this narrow scope. Do not claim tamper-proof behavior against arbitrary interpreter mutation, removal of the entire trusted authority, or a new external authority root. Preserve the existing authority ownership boundary.

## Evidence required before component approval

Run the unchanged original ledger cohort and newly added deterministic replacement/lifecycle controls against an identified, stable candidate. The deterministic control should force numeric identity comparisons to alias while independently demonstrating that the retained original file is unlinked, then require rejection and a separately observed STOPPED result. Do this for both marker and journal; do not require the filesystem to recycle an inode by luck.

Also cover rename-preserved original files, hardlinks, symlinks, FIFO/missing/corrupt files, directory replacement, partial creation/write/fsync/interruption, terminal success/failure and idempotent closure. Original tests already exercise many guards and should be reused. Test descriptor ownership without relying solely on implementation attribute values: retain actual descriptor numbers and observe their liveness or use a tracked OS-call seam. Cleanup controls must not indiscriminately close caller descriptors.

A full affected C201 cohort is justified by active transitive imports; no full product aggregate is selected here. Existing source/compiler/core checks and documentation preservation checks must follow the active contract's applicable scope. Author and independent checks require explicit file hashes, commands, interpreter/platform, outcome accounting and logs. R02 remains blocked until a later fresh complete aggregate passes. No native readiness, destination acceptance, second target or original normal-tolerance gate advances through this repair.

## Audit evidence

- `contract-dependency-inventory.json`: original file identities and every direct text reference to the ledger path/old SHA.
- `historical-ledger-pin-records.json`: all 51 exact JSON pointer locations across 33 historical pin files.
- `frozen-contract-inventory.json`: 42 frozen protocol/source/qualified bindings, all matching; ledger excluded.
- `historical-protected-inputs-check.json`: 301 inherited locked-input bindings, all matching; ledger excluded.
- `active-dependency-inventory.json`: AST import inventory, existing method counts and exact original failing-method hash.

The final implementation decision remains pending exact candidate review and executed controls.
