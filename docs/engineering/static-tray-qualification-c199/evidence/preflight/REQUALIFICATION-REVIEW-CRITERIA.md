# Independent criteria for one C199 lifecycle requalification cohort

## Disposition

The repaired supervisor/store passed the targeted no-child review recorded in
`supervisor-review-v3/REVIEW.json`. That result is limited to the inspected
repair paths. It does not turn the earlier eight lifecycle cases into tests of
the revised files and does not authorize any new process by itself.

A narrowly scoped, versioned validation amendment can authorize one new
controlled lifecycle cohort before native qualification. Review the actual
amendment and immutable executable closure before the first additional child.
The current status is **awaiting that concrete amendment and closure**.

## Required decision content

1. Give the amendment its own immutable identity and version, for example
   `OK-VAL-STATIC-TRAY-001/0.1.1` with scope limited to C199 lifecycle repair and
   requalification. Keep `OK-MAP-STATIC-TRAY-001/0.1.0`, canonical source/record
   semantics and geometry tolerances unchanged. Preserve C198's original files.
2. Explain the concrete defects and repairs: promotion allowance and uncertain
   postcommit outcomes, deadline charging, ledger locking/transition bounds,
   immediate child-start accounting, pipe closure and bounded polling work.
3. Preserve the original L01-L08 receipts, the original 8 direct plus 1 grandchild
   starts, the zero-child preparation failure, both unsuccessful review probes
   and the repaired review. Identify the original executable bytes if retained;
   if exact bytes were not retained, state that limitation instead of deriving
   an execution hash from later edited files.
4. Distinguish original observed success from qualification of current bytes.
   The earlier result remains historical; the new cohort supplies the missing
   evidence for the repaired, sealed implementation.
5. Authorize exactly one replacement cohort with unique slot IDs, for example
   `L-R1-01` through `L-R1-08`. Each slot permits at most one direct controlled
   child. Only the slot corresponding to L05 permits one controlled grandchild.
   Failed starts consume their slot. No slot can be reset or automatically retried.
6. State both counts: additional allowance is **8 direct + 1 grandchild**;
   maximum cumulative historical lifecycle use becomes **16 direct + 2
   grandchildren**. Do not describe the original total limit as unchanged.
7. Keep the twelve native starts and associated receiving ceilings unchanged
   and unconsumed. The amendment authorizes no Blender process, export, receiving
   job, simulation, render or timed author. It establishes no observed Blender
   cancellation behavior.
8. Preserve the original operation, time, polling, cleanup, output and geometry
   limits. Stop the unexecuted remainder at the first unexpected control result.
   Another repair or cohort needs another explicit reviewed decision; this
   amendment is not an open-ended permission to retry.

## Executable closure required before approval

- Exact committed source identity and SHA-256/size inventory for supervisor,
  store, lifecycle runner, fixed stub, bootstrap/package files and every locally
  imported module. Bind the inline L05 grandchild command bytes as well.
- Exact host CPython executable and the used standard-library/shared-library
  closure, effective environment, working-directory policy and fully expanded
  commands. No ambient source path or native dependency should enter this cohort.
- A complete, hashed runner that verifies the declared closure before each
  case, records slot reservation/start/outcome and stops on first failure.
  The present `controls()` list comprehension continues after a false result;
  use a reviewed stop-on-failure driver or repair that behavior before freezing.
- New empty output locations. Preserve all original directories and records.
- Explicit per-case stage/seam mapping: L01/L08 use the receiving stub after
  prevalidated construction; L02-L07 test construction/cleanup with fixed seams.
  No seam is counted as an actual second native or receiving process.
- A recorded check that all native slots remain unconsumed before this cohort.
- Independent approval identifying the exact amendment digest, executable lock
  digest and command schedule. Any changed executable byte voids that approval
  until independently reviewed again.

## Result review

The reviewer checks the exact approved bytes against executed inputs, counts
every started direct child and grandchild, reconciles every slot, and verifies
the recorded process-group cleanup and closed handles. All preexisting accepted
source/output bytes and modes must be preserved except the intended successful
pointer transition. L08 must reject stale state and reconcile a genuinely
uncertain pointer outcome without a second child or repeated promotion.

Retain logs, monotonic timing and source identities. Failed or unused cases stay
explicit. A passing replacement lifecycle cohort closes only its supervisor and
transaction-mechanics obligation. Independent full implementation/fixture/reader
review and the sealed native input lock remain required before the first native
qualification slot.

## Latest targeted repair hashes

| File | SHA-256 |
| --- | --- |
| supervisor.py | c47b84ab464e89d4c8673d7541679a45ddf3fc4816a906aff4546e074b4c5a10 |
| store.py | d0006497ff6fc13ff0b563cdb58445789cd1a26c489ac4ce2a84e77a03607bd0 |
| lifecycle.py | 78fc36483faadb569aaa0370998e58e862745368e7ae73ddb983cd1fb9c86fe5 |
| lifecycle_stub.py | 119dc5798f508e815444b897716c7f6f6009fbb129d94d486cdffa44546f2a44 |

These hashes identify the no-child review snapshot, not an approval of a future
replacement cohort or a complete native executable closure.
