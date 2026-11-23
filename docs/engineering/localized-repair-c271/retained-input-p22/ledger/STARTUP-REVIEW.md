# C271 P22 startup review

**Accepted for startup reconciliation.** The complete required readset is recorded in `READSET.json`, including all 1,751 CURRENT lines, 4,555 task lines and both 370-line requirement/plan ledgers. Governing instructions and C270 records match exact main objects at `70ca7e68ff95df876f801137369d176fe5b2bab3`. C271 remains on the retained branch at `527368bd5195c439762b43e2cc836ff9822213f8`.

## Prior handoff and parent state

P21 delivery is reconciled. The independent predecessor review passed 46/46 checks; the issue273 and PR274 terminal marker objects match. The saved ZIP is 9,327,161 bytes, SHA-256 `ba03995347ed65a5a37b4283211841daf4da74fe4a04dbe0617f9e833e9bb64f`. The later saved terminal receipt is 222,162 bytes, SHA-256 `02d7987249a106b7f205e09f490fe2f35006ffdbf0f37da3dca91e21503082fe`.

Those later records resolve only P21 source-time delivery-pending fields. Frozen artifacts must remain unchanged. P21 is complete as a partial handoff; C271 remains blocked/open, H0 unaccepted, R03–R05 not_done and P02 in_progress. R01/R02 and P01 remain done. Main still names completed C270 because C271 is unmerged; this is expected. No main lease is held.

## Active next action

P22 owner is `c271-p22-aa6113404163`. Confirm the independently reviewed early recovery save/readback, recover exact P09 Node/C195 archive inputs, and freeze one clean source for both preparation and later H0. Obtain independent approval of complete unchanged-preparer plans, isolated destinations and report/index paths. Prepare or verify only Node and the 24-file readback dependencies. Independently review actual successful source-bound receipts, then stop at that prerequisite checkpoint or first concrete blocker.

The successful receipt state must be INSTALLED_EXACT or ALREADY_PRESENT_EXACT with exact source/archive/file/mode bindings. DRY_RUN_READY is insufficient. No H0/H1, original-seven, full routine, main integration, parent closure or second phase follows in this chat.

## Minimal canonical changes for the Director

- Preserve P21 session/delivery evidence and append its terminal delivery resolution with exact receipt/marker/review bindings.
- Replace only the current phase, owner and obsolete P21 delivery next action with P22 scope, gates and stop. Keep C271 and parent requirement/plan statuses unchanged.
- Retain P21 as latest confirmed final handoff until actual P22 final save/readback. Record early recovery only after confirmation.
- Append P22 declaration/outcome sections to REQUIREMENTS and PLAN. Update the active STATUS paragraph while retaining C270 history and released lease.

## Ownership and limits

The Director owns shared Git/index, canonical records, technical execution, publication and saves. Ledger owns only `phase-p22/ledger/` and waits for the next review assignment. No canonical mutation, Git mutation, technical execution or recovered-code execution occurred.

Early-save confirmation and technical preparation gates remain outside this review. Historical C270 broad-driver completion, prior global process termination and P13 difflib completion remain unknown. This review does not establish global absence of work outside declared inputs. Detailed predecessor auditing is reused from `phase-p22/archive_audit/PREDECESSOR-REVIEW.json`, rather than repeated.

## Exact fields

`task.json` uses `status` for the parent and `session_phase.status` for the active phase; there is no root `current_status`. Update `owner`, `next_action` and `authorization.selection`. Preserve the exact P21 `session_phase` and `delivery` objects in `prior_session_phases[]` and `prior_phase_deliveries[]` before replacing their active slots with P22. Append its terminal resolution to `phase_reconciliations[]`. Existing historical arrays have 20 phases, 20 deliveries and six reconciliations.

In CURRENT, update `next_action.summary`, `next_action.suggested_task`, `next_action.sources` and the actual `snapshot_date`; retain `next_action.status=blocked`. CURRENT has no root `owner` or `session_phase`. Keep `latest_handoff` until an actual P22 final save; update `latest_recovery` only after the confirmed early save.
