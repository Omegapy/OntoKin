# C201 first coordinator increment: independent contract audit

## Scope and authority

Reviewed published main `a4747c06611066c09cd8daf5a67e7244de60f178` in `/workspace/scratch/f53463e40cc6/offline-restored-main`. Exact read inputs are bound in `c201-ledger-contract-bindings.json`. This is a design review for an independently useful CPU-only increment, not native readiness approval.

The suitable bounded increment is a separate `prototypes/static_tray_admission_c201/` schedule validator and durable one-use reservation state machine. It should validate exact slot references, enforce reservations and outcome order, persist an immutable invocation identity, and stop after uncertain persistence. It must not call a child process, run the historical coordinator, authorize native execution, alter qualified constructor/reader/store source, or represent supplied success observations as measured delivery evidence.

`ADMISSION.md` sections 3 and 7, `ADMISSION.json` schedule/stop rules, and `IMPLEMENTATION-NEXT.md` govern this step. Keep their approved bytes unchanged. A new implementation note must identify the remaining executor, lock, transaction, readback, host, approval, image and final-review gates.

## Exact schedule

The schedule identity is `C201-Q01-A01-A04-v0.1.0`. Full event order is `A01`, `D01`, `D03`, `A02`, `A03`, `A04`. Native slot order is `A01`, `A02`, `A03`, `A04`.

| Slot | Route | Kind and source | Completed predecessor | Equality references | Extra prerequisites |
| --- | --- | --- | --- | --- | --- |
| A01 | `ontokin` | `baseline`, frozen `ontokin` source closure | none | none | none |
| A02 | `direct-python` | `baseline`, frozen `direct-python` closure | A01 | A01 | D01 then D03 complete |
| A03 | `ontokin` | `clean-regeneration`, A01 retained accepted source/dependencies | A02 | A01 | accepted-source reference A01 |
| A04 | `direct-python` | `clean-regeneration`, A02 retained accepted source/dependencies | A03 | A02, A03 | accepted-source reference A02 |

Every slot is case `Q01`. Every slot has maximum one native start, one receiving start and one actual-delivery Node start. Total ceilings are four of each. One render is allowed per receiving job. Timed authors, simulations, retries, extra renders, extra receiver jobs, lifecycle cohorts, deliberate Blender cancellation experiments and synthetic Node preparation cohorts remain zero.

D01 and D03 consume no native, receiving or Node starts. D01 requires the `CLEARANCE` finding from the actual mutated delivery; D03 requires `SIBLING` with the independent A01 sibling reference. Generic parse/geometry failure does not satisfy either control. The first increment may reserve and record a bounded control observation, but may not claim it performed these mutations or validated their geometry.

Receiving and its cleanup precede conditional promotion. Actual-delivery Node checking follows accepted transaction finalization and gates the next slot. A01's Node check precedes D01; D01 precedes D03; both precede A02. A technical accepted transaction alone does not admit the family.

## Strict schedule validation

Validate complete slot inventory and ordered equality/predecessor/reference values, not just slot count or a set of names. Reject omitted, extra, duplicate, reordered and wrong-route slots, altered case/kind/source references, a fifth slot, a historical twelve-slot schedule and changed stage ceilings. Do not silently derive A-slot references from historical N-slot arithmetic.

Keep protocol identity separate from an eventual executable lock digest. An exact hash of ADMISSION.json is a protocol binding only. It is not proof that all code, dependencies, commands, environments and output roots are frozen.

If JSON is accepted, reject duplicate object keys, NaN/infinity and malformed types before comparison. In Python, booleans compare equal to integers; exact integer checks are necessary for numeric allowances so `true` cannot substitute for `1`. Do not use unbounded reads of receipts or ledgers. Freeze/copy validated data so mutating a caller-owned dictionary cannot change already admitted schedule semantics.

## Invocation identity and directory replay

The invocation authority must be independent of caller-selected output/store directories. A caller must not obtain a new allowance by choosing a different result directory, copying a store, removing its local ledger, changing a lock hash, or instantiating another ledger object.

For this increment, use one explicit, trusted reservation-authority root containing the fixed schedule identity. Exclusive creation at that root is the one-use operation. Keep the invocation receipt after every success, failure and uncertain write. A missing/corrupt/cleared attempt ledger alongside that receipt must block further execution; never treat it as a fresh schedule.

Output directory changes under the same authority must be rejected. Independent authority roots used by CPU tests are isolated fixtures, not real C201 invocations. The production authority root must eventually be fixed by the reviewed executable lock and independently checked before invocation. Caller-provided arbitrary authority roots are not a complete production replay guard. Document this trust boundary rather than claiming protection against an administrator deleting/replacing the entire authority.

Opening existing state for inspection must not grant a resume capability. A prior in-progress reservation has unknown outcome and must be read-only reconciled. Successful continuation belongs only to the already active invocation capability; construction of a new object must not recover a launch-capable handle. No reset/resume/retry entry point belongs here.

## Ledger and reservation invariants

Use a C201-specific schema and schedule identity. Every record must bind the immutable invocation ID, protocol/plan identity, sequence number, slot/control and stage. Include route and expected predecessor/reference metadata where they affect admission. A schema and digest alone cannot establish observed delivery facts.

Reserve a stage durably before authorizing its attempted launch. Reservation consumes that slot/stage allowance even when launch fails, times out, is cancelled, or has unknown outcome. Reservations never decrement. Reject duplicate reservations and outcomes without their exact reservation. A process-start receipt may distinguish an observed start from an attempted start, but cannot release a consumed allowance.

Enforce a single in-flight reservation. Native success can permit receiving; receiving success can permit transaction finalization/promotion; accepted transaction plus cleanup can permit Node; successful Node and slot-specific required checks can complete that slot. D01/D03 then gate A02. This exact sequencing should be explicit, or the increment should stop at reservation-only behavior with later stages marked unimplemented. An overly generic `success=True` transition must not be presented as actual transaction/cleanup verification.

Any rejected/failed/timed-out/cancelled/unknown observation stops the whole schedule. A fault in identity, cleanup, equality, a control or persistence also stops later work. Previously successful receipts remain unchanged. Neither an additional successful record nor a fresh path can cure terminal failure. Pending finalization or an incomplete record blocks progression.

The state reader should replay and validate the whole bounded ledger, checking invocation binding, sequence, transition, references and accounting. It must reject malformed/truncated lines, unexpected fields/states, mismatched identity, reordered records and duplicate terminal records. If hash chaining is implemented, verify it; do not imply a hash chain protects against wholesale replacement by an actor controlling the trusted authority.

## Durable persistence and uncertainty

The existing `store.append_event` is useful historical context, not a sufficient implementation: it checks per-path/per-slot transitions and fsyncs a file, but it does not enforce the global C201 order, fixed authority or separate Node/control reservations. Keep it unchanged.

The existing `transaction.write_new` demonstrates exclusive file creation and file plus parent-directory fsync. The existing `store.promote` demonstrates the crucial distinction between pre-replacement failure and post-replacement unknown outcome. Reuse reviewed primitives only when their semantics and transitive imports fit the increment; importing an old lock/coordinator is not a compatibility solution.

Invocation creation and newly created ledger directory entries need durable file and parent-directory updates. Fail closed on any write/flush/fsync/rename error. Do not delete a possibly created invocation receipt after an error. A failed append may have written none, some or all bytes; preserve them, poison the live invocation, and report uncertainty. Reopening must remain inspection-only and must not infer permission from a well-formed final record if the writer did not observe durable completion.

Reject symlinks, hardlink aliases and unsafe file types for authority receipts and ledgers, and avoid trusting a check-then-open race. Serialize writers and bound lock acquisition. A losing concurrent invocation must not truncate or replace the winner's state. Tests should exercise actual files and locking; no Blender or lifecycle subprocess is needed.

This increment does not implement candidate sealing, accepted pointer replacement or the transaction's conditional promotion. Those existing primitives stay unchanged. Its outcomes must clearly identify supplied CPU observations and pending real cleanup/promotion/closure validation.

## Required independent CPU controls

1. Accept exactly the approved schedule and reject each independently altered slot, order, route, case, source reference, predecessor, equality list, control order and ceiling. Cover missing, extra, duplicated and twelve-slot inputs; include boolean-for-integer and mutable-caller-input cases.
2. Reserve and complete the intended stage/control sequence in fresh temporary authority roots. Verify exact monotonic counters and maximum one reservation for each slot/stage. Assert no child-launch API is reachable.
3. Reject every out-of-order slot/stage/control, duplicate reservation, duplicate result, wrong route/reference, fifth slot and premature completion. A02 must remain blocked until A01, D01 and D03 have finished in order.
4. Exercise every failure/timeout/cancellation/unknown outcome at native, receiving, finalization, Node and control boundaries. Each consumes the assigned reservation and blocks all later work without modifying prior records.
5. Attempt a second invocation with a new output path, renamed/copied output store, removed/empty ledger, changed plan hash, and new object at the same authority. The retained exclusive invocation receipt must prevent reuse. Show that read-only inspection does not resume a pending reservation.
6. Exercise two racing in-process threads using the same authority. Exactly one may acquire the invocation; the loser must leave winner bytes unchanged. No separate machine is implied.
7. Inject faults before and after durable creation/append boundaries, including partial write and fsync failure. Preserve partial bytes and invocation marker; no caller receives permission to launch after failed persistence, and no subsequent instance resumes. Verify complete-but-unacknowledged append remains uncertain.
8. Reject malformed, truncated, oversized, symlinked, hardlinked, reordered and mismatched ledger/receipt state. A reader must not silently skip blank or malformed data that changes accounting.
9. Verify completed reservations are inspectable after closing and cannot be reopened for continuation. Expose measured counters, supplied observation status and incomplete native readiness separately.

Run the relevant current Python/source/compiler/core/documentation checks required by AGENTS on the committed increment. Preserve the existing failed full regression: 4,239 distinct passing methods and thirteen torque-read methods not run after unchanged 30,000 ms setup timeout. No consumed C199/C200 cohort rerun is part of this work.

## Explicit remaining gates

After this increment, the complete executable input lock, exact implementation/dependency closure, actual host verification, native approval, supervised process orchestration/deadlines, C201 transaction and accepted-source closure validation, C201 readback/probe compatibility, actual D01/D03 geometry controls, all four deliveries/images and independent final admission review remain pending. A CPU-ledger pass is evidence only for its tested state/persistence behavior.

No native, receiver, Node, lifecycle or author process was started for this audit. No source or historical evidence was changed.
