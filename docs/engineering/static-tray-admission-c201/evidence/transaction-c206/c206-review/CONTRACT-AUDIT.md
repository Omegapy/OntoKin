# C206 independent transaction/closure review requirements

Reviewer: `independent_review`, separate from the implementation worker.
Status: pre-implementation contract audit; no candidate approval.
Base identified by root: `f90e012fa9b68a1111b97586c6462851e6166dea`.

## Approved boundary

The increment is a separately implemented C201 transaction and accepted-source
compatibility component. C199/C200's closed native schedules, qualification
coordinator, lock, transaction, immutable evidence and four approved C201
preparation documents must remain exact. No native, receiving, Node, lifecycle
or timed-author child is part of this review. Full native readiness, actual
readback, image review and admission are separate later gates.

## Required semantic distinctions

| Slot | Route | Schedule predecessor | Accepted source | Equality references |
| --- | --- | --- | --- | --- |
| A01 | OntoKin | none | frozen Q01 OntoKin closure | none |
| A02 | Direct Python | A01 after D01/D03 | frozen Q01 Python closure | A01 |
| A03 | OntoKin | A02 | actual retained A01 accepted closure | A01 |
| A04 | Direct Python | A03 | actual retained A02 accepted closure | A02, A03 |

Each slot has a fresh store. The store's expected accepted-pointer predecessor
is distinct from the schedule predecessor and regeneration reference. All
references must be explicit and exact, including types and absence.

## Review controls

1. Accept exact fixture-only validated bindings without granting execution.
2. Reject missing or changed lock/source/dependency inputs after validation.
3. Reject wrong route, schedule predecessor, pair or regeneration reference.
4. Bind baselines to the frozen three-file editable Q01 closure.
5. Resolve regeneration from the accepted pointer and actual retained source.
6. Reject unrelated pointers, same-revision different pointer contents and
   changed accepted-pointer bytes, including during component work.
7. Verify complete source, artifact, native/receiving receipt and closure
   inventories before reporting success; reject missing/extra/unbound files.
8. Confirm retained source/module/artifact/receipt/pointer closure unchanged
   before and after regeneration. A prepared record or copied output is not
   accepted editable source.
9. Reject unsuccessful receiving measurements or failed/uncertain cleanup.
10. Perform required conditional promotion only after validation and cleanup;
    pre-commit failure must preserve the prior pointer.
11. Preserve UNKNOWN on post-replacement failures or lost replies, with actual
    observed pointer state. Do not assert rollback after the commit point.
12. Reject unsafe filesystem aliases, nonregular files and unbounded inputs
    before reads or store operations can block or escape their roots.
13. Reuse qualified source, store, reader and supervisor primitives unchanged;
    no bypass of historical twelve-slot validation.
14. Labels must distinguish synthetic CPU fixtures from actual destination or
    process evidence. A passing component cannot manufacture independent
    approval, current-host sealing, native readiness or family admission.

## Evidence sources read

- `ADMISSION.md`, especially sections 3, 4, 6 and 7.
- `IMPLEMENTATION-NEXT.md` and source handoff `NEXT-TASK.md`.
- `LEDGER-C204.md`, `INPUT-LOCK-C205.md` and both independent reviews.
- C201 schedule and input-lock result definitions.
- Historical source lowerer, transaction, store, supervisor and receiving
  comparison primitives.

The C204 ledger records caller observations and does not validate their truth.
The C205 validator is a read-only snapshot and does not prevent later changes.
Historical `store.promote` conditionally compares only revision, so the new
layer must establish the stronger pointer/path/closure bindings it claims.

Actual independent execution, input hashes, findings and final candidate
decision will be recorded separately. This document is not native approval.
