# C199 lifecycle repair and one replacement qualification cohort

**Decision identity:** `OK-VAL-STATIC-TRAY-001/0.1.1-L-R1`  
**Scope:** controlled-process validation only  
**Date:** November 10, 2026, America/Denver  
**Effective gate:** exact amendment and input-lock approval by the independent reviewer

This bounded amendment authorizes one new lifecycle qualification cohort after
the preparation defects below are repaired and its actual executable inputs
receive independent approval. It does not amend the C198 mapping, geometry,
source semantics, native qualification schedule or numerical tolerances.
The owner's existing development authorization includes reviewed technical
repairs; no further owner confirmation is required for this bounded work.

## Why a new cohort is necessary

The original L01–L08 preparation run passed its eight expected outcomes, using
eight directly launched controlled children and one L05 grandchild. Review then
found defects outside the original successful paths: insufficient remaining
promotion allowance; uncertain errors after pointer replacement; unbounded
ledger locking; cleanup insufficiently charged to the outer clock; delayed
child-start accounting; inaccurate pipe-closure reporting on setup failure;
and unbounded filesystem polling work. These defects were repaired. The
independent no-child review retained both the failed probes and their passing
repair probes.

Those edits changed executed code after the original controls. The original
receipts did not contemporaneously bind all executable hashes, and the exact
earlier complete source snapshot was not retained. They remain useful historical
observations and count toward process use; they are not qualification evidence
for the repaired input lock. No hash of a later file is assigned to that earlier
execution. A still earlier directory-sealing preparation error occurred before
any child start and remains separately recorded.

## Exact additional allowance

One replacement cohort, **L-R1**, contains slots **L-R1-01 through L-R1-08**,
mapped in order to the unchanged L01–L08 behavior controls. Each permits at most
one directly launched controlled child. Only L-R1-05 additionally permits one
controlled grandchild. A started failed process consumes its slot. There are no
automatic retries or replacement slots. Stop the remaining cohort at the first
unexpected result, source-binding change or inability to verify cleanup.

The additional allowance is **8 direct children plus 1 grandchild**. Including
the original run, the maximum cumulative lifecycle history is therefore
**16 direct children plus 2 grandchildren**. This explicitly increases the
original controlled-process total; it does not describe that total as unchanged.
Any further repair requiring another actual process cohort needs another
identified, reviewed decision before execution.

The twelve native slots N01–N12 remain unchanged and unconsumed before L-R1.
This amendment authorizes zero Blender starts, exports, native receiving jobs,
renders, simulations or timed authors. A process-stub pass cannot establish
observed Blender cancellation or timeout behavior.

## Preserved limits and observable evidence

The control allowance remains 30,000 ms per case, at most 50 ms between polling
checks, 500 ms graceful termination and 2,000 ms cleanup/cancellation completion.
The production transaction ceiling remains 65,000 ms, with 30,000 ms construction
and receiving stages, 3,000 ms promotion and 2,000 ms cleanup. Ordinary source
defaults remain 100,000 operations / 30,000 ms. Output, log, result and GLB byte
caps and every geometric tolerance remain unchanged. The repaired scanner adds
an explicit 2,048-entry ceiling within each private attempt directory.

L-R1-01 and L-R1-08 test receiving-to-promotion with a sealed prevalidated
construction seam. L-R1-02 through L-R1-07 test construction/cleanup. Each uses
the production process supervisor and immutable-store promotion functions.
Other stages use fixed in-process seams; they are never counted as executed
native construction or receiving. L-R1-08 preserves separate stale and unknown
store copies, rejects the stale pointer, and reconciles the unknown pointer
without a second child or a repeated promotion.

The new runner checks the lock before every case, records reservation, actual
start and terminal outcome, and stops on an unexpected result. All commands,
source files, bootstrap files, stub/grandchild command text, host dependencies,
environment and new output locations are fixed in `LIFECYCLE-INPUTS.json`.
Independent approval binds both that lock and this amendment. Changed executable
bytes invalidate the approval. Exact per-case results, logs, process groups,
cleanup, elapsed time, before/after accepted bytes and source identities are
retained. The original evidence remains under `evidence/lifecycle-original/`.

The coordinator, controlled child and L05 grandchild use `-IBS`: isolated Python,
disabled bytecode writes and disabled site initialization. Review of the earlier
unexecuted `-IB` lock found that system site initialization actually imported
two unbound `site-packages` startup files. That blocked lock is retained. The
coordinator and children now use the same exact finite environment, and the
coordinator checks it before work. The runner rejects unbound local bytecode
caches instead of assuming `-B` prevents reads of an existing cache.

A passing L-R1 cohort closes only the repaired supervisor/store mechanics gate.
The complete producer, independent reader, receiver, fixture and dependency
closure still needs independent approval before N01. C199 cannot claim tray
qualification, later admission, full regression, release, comparative advantage
or full GOAL completion from this amendment or its controls.
