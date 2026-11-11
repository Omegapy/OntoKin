# Independent C204 component review

**Decision: APPROVE_COMPONENT_ONLY** at source `7861e2d0d7ed940cdf2be4b4fe98dbde3e8c373d`, tree `76108c1059129419356c6504fc478ed49138f4e9`, based on published main `a4747c06611066c09cd8daf5a67e7244de60f178`.

The independent reviewer was `admission_contract_audit`, separate from the implementing worker. The exact five changed files and their hashes are in `c201-ledger-independent-review.json`. The worktree was clean when checked. All five changes are additions; the approved C201 protocol and qualified historical code are unchanged by this candidate.

## Evidence and decision

The first increment implements the exact public four-slot schedule and a durable, one-use accounting component. It rejects changed route/order/reference/allowance inputs, records stage reservations once, gates the specified predecessor/control sequence, conservatively consumes failed or uncertain reservations, and prevents a new live handle from resuming an existing authority. It contains no child-launch entry point. Supplied promotion/cleanup/control results remain explicitly labeled observations.

I inspected all three component source files, the dedicated tests and `LEDGER-C204.md`, and compared their bytes to the exact committed candidate. The implementer's 36 passing methods are supported by the preserved log; I verified source and log hashes rather than claiming another 36-method execution. I ran five independent adversarial controls and a sixth controlled concurrent-interruption probe on those exact module bytes. All six passed, with zero child starts. Details are in `c201-ledger-final-adversarial.json` and `c201-ledger-draft-race.json`; the latter retains its initial working filename but its recorded source digest equals the reviewed candidate.

The earlier failing draft controls remain in `c201-ledger-draft-adversarial.json`. They are historical failures, not the status of this candidate. The original contract audit and exact input hashes remain beside this review.

## Findings resolved before approval

| Finding | Resolution and independent check |
| --- | --- |
| A FIFO used as a receipt or journal blocked before its kind was checked. | Nonblocking opens now precede regular-file validation. Both receipt and journal FIFO controls reject without a blocking writer. |
| D03 accepted `SIBLING` alongside a `STRUCTURE` finding. | Both assigned controls now reject a structural finding. The independent D03 probe stops before A02. |
| `journal_valid` implied more than framing/hash integrity. | The field is now `journal_integrity_valid`; `semantics_verified`, `resumable`, `native_readiness` and `admission_completed` remain false. A deliberately impossible but correctly hash-linked event chain demonstrates this honest boundary. |
| An interrupt after durable append but before memory bookkeeping allowed a duplicate reservation. | Every public mutation poisons its capability on `BaseException` while holding an outer reentrant lock. Counts consume before persistence and uncertainty is explicit. Both duplicate-reservation and concurrently waiting caller probes now stop. |

## Limits that remain intentional

The fixed authority directory must become an immutable input of the future independently reviewed executable lock. A trusted filesystem authority cannot prevent an administrator from deleting all authority evidence, substituting an unrelated root, or changing the interpreter. The documentation states that boundary. Choosing fresh temporary authorities in CPU tests does not exercise or consume the real C201 admission.

An evidence digest and a caller's `passed` observation do not validate actual source bytes, geometry, equality, cleanup or pointer promotion. The component does not claim otherwise. Read-only journal inspection checks bounded canonical framing, identity, sequence and hash links; it does not replay event semantics and cannot grant a resume capability or an admission result.

This approval covers only the tested schedule and accounting component. It is not the C201 technical readiness decision. The complete executable lock, actual host/dependency verification, supervised process orchestration/deadlines, transaction and readback adaptations, accepted-source validation, actual D01/D03 deliveries, four image reviews and final independent admission review remain pending.

Root must complete the applicable source/compiler/core/documentation and frozen-input checks, then apply repository ownership and integration rules. No historical C199/C200 schedule or full regression was rerun by this reviewer. The inherited failed full regression remains visible: 4,239 distinct passing methods and thirteen torque-read methods not run after the unchanged 30,000 ms setup timeout.
