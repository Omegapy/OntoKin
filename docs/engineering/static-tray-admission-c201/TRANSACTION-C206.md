# C206: C201 transaction and accepted-source component

This increment implements the file and source portion of the four-slot
[C201 admission protocol](ADMISSION.md). It can retain a baseline transaction,
resolve that transaction's accepted editable source and dependency, and validate
and conditionally accept a clean regeneration. The public implementation is
[`transaction.py`](../../../prototypes/static_tray_admission_c201/transaction.py).

**The current component accepts fixture-only bindings. Production inputs are
rejected because a working-directory disagreement remains unresolved.** This
increment is CPU preparation evidence, not native admission or a production
coordinator. It contains no child-launch operation and does not advance the
existing reservation ledger. No Blender, receiver, Node, lifecycle or timed-author
process is started by its tests.

## Operations and evidence boundary

| Operation | Checks and resulting behavior |
| --- | --- |
| `bind_transactions` | Calls the unchanged C205 validator, rereads the exact lock and approval, retains verified bytes and directory identities, then rejects production purpose with `C201-NATIVE-CWD`. |
| `prepare_transaction` | Revalidates pinned inputs; checks exact slot, route, predecessor, equality and regeneration references; verifies every preceding accepted receipt and full closure; lowers actual frozen or retained editable source; writes the construction job and source into the bound empty stage. |
| `seal_construction` | Checks the unchanged prepared job/source/provenance, native startup and artifact receipts, exact output inventory, underlying supervisor record and cleanup observation; audits the actual GLB with the unchanged independent reader; checks exact paired/regenerated canonical and GLB bytes; seals the candidate and writes the receiver job. |
| `complete_transaction` | Checks the exact receiver job, observed input hashes, measured native-scene/GLB observations and underlying supervisor cleanup record; seals receiving and transaction receipt closures; commits the accepted pointer only if its predecessor is still exactly absent. |
| `inspect_accepted` | Revalidates inputs and the retained pointer/receipt/source/output/receiving closure without starting or retrying anything. |

The separate `AcceptedTransaction` result means transaction acceptance only.
Its `native_start_authorized`, `native_readiness` and `admission_completed` fields
are false. A later coordinator must still validate actual-delivery Node results,
D01/D03 controls, complete schedule ordering and images. The transaction layer
requires preceding transaction receipts but does not treat them as proof that
those additional gates passed.

Process observations bind their purpose, slot, stage, exact input lock, declared
command, process identity, finite timing, successful exit and cleanup flags to
an actual retained supervisor JSON record and log bytes. This verifies consistency
of supplied evidence. It cannot authenticate the caller's process observations,
prove that a native child actually ran, or make a synthetic file a native result.
The CPU fixtures label that limitation explicitly. The future trusted coordinator
must establish actual receipt provenance and supervise real process deadlines.

The same original supervisor `Clock` accompanies preparation through completion;
it cannot be replaced by a new clock at promotion. Cooperative checks preserve
its 65-second total and original construction/receiving/promotion allowances.
This component has no independent watchdog and makes no hard-deadline claim for
external child processes or an unresponsive in-process operation.

## Accepted source and immutable evidence

A01 uses the frozen Q01 OntoKin closure; A02 uses the frozen Q01 direct-Python
closure. A03 resolves A01's actual accepted pointer and sealed `source` directory.
A04 resolves A02 in the same way. Both source files and the manifest must retain
the original bytes. The qualified lowerer compiles those actual editable files;
a canonical record or copied GLB cannot substitute for accepted source.

Schedule predecessor, accepted-source reference, equality references and store
predecessor are separate concepts. A03 follows A02 but regenerates A01. A04
follows A03 but regenerates A02 and compares both A02 and A03. Each slot has its
own initially empty store, so its pointer predecessor is exact absence. A JSON
pointer whose revision happens to be null is not an empty store.

The construction closure retains source, canonical input, provenance, job,
startup/exporter receipt, native result, raw/final GLBs, native scene, logs,
supervisor record, independent measurements, explicit equality results and the
bound process observation. Receiving retains its exact job, observations, image,
logs, supervisor record, measured comparison and bound process observation.
A third sealed closure retains the transaction receipt. The accepted pointer
binds all three by hash. Complete inventories reject missing or extra files.

Prior accepted pointers and closures are checked before preparation, before
sealing, before promotion and after promotion. Changed source, dependencies,
receipts, artifacts, pointer contents or receipt hashes reject progression.
Matching revision strings alone are insufficient. Files must be bounded private
regular files; symbolic links, hard links and FIFOs reject. These checks do not
protect against an adversary with unrestricted write access to the running
Python process or its filesystem; the future bootstrap owns isolation and
trusted authority retention.

## Conditional promotion and uncertainty

The unchanged historical store primitives seal and verify candidates. C206 uses
a separate small promotion operation because historical `store.promote` compares
only revision strings. C201 checks the complete pointer precondition under the
same promotion-lock convention, writes and syncs a private candidate pointer,
then atomically replaces `state.json` and reads it back.

A rejection before replacement preserves the prior pointer. If replacement may
have occurred, exception handling reads the actual pointer and retains
`UNKNOWN`, including an interruption after replacement but before a Python flag
can be set. It preserves intended and observable state and never claims rollback
across the commit point. Repeated completion of a consumed in-memory transaction
is rejected. Durable schedule consumption and cross-restart authority remain the
separate ledger/coordinator's responsibility.

## Concrete production blocker and exact next step

The current C205 validator in
[`input_lock.py`](../../../prototypes/static_tray_admission_c201/input_lock.py)
requires `commands[slot][stage].cwd` to equal the repository root. The unchanged
qualified [`supervisor.run_process`](../../../prototypes/static_tray_v01/supervisor.py)
uses the stage directory as the child's actual working directory. The qualified
[`worker.main`](../../../prototypes/static_tray_v01/worker.py) also requires its
current directory to equal `job.output_directory`.

The component does not silently reinterpret that lock. All `production-inputs`
bindings fail at `bind_transactions`, after the existing validation but before
staging or promotion. Its explicit fixture adapter checks both the declared
repository cwd and the synthetic underlying supervisor's stage cwd, exposing the
disagreement. C205, the historical supervisor, qualified worker and four approved
protocol documents remain unchanged.

The next bounded integration decision is to align the C201 command working
directories with the unchanged qualified worker/supervisor contract, review the
lock change and tests, then remove the fixture-only block only with exact binding
evidence. Actual Node/readback compatibility, trusted bootstrap, complete host and
runtime dependency/alias sealing, receipt provenance, full process orchestration,
independent native readiness and the sole four-slot invocation remain later gates.

## CPU evidence and preserved limits

The dedicated [controls](../../../tests/test_static_tray_admission_c201_transaction.py)
exercise actual new code with real temporary files, real source lowering, actual
independent GLB measurements, actual receiving comparison, immutable sealing and
real conditional pointer replacement. Geometry, native containers, images and
supervisor observations are explicit synthetic fixtures. Child APIs are blocked.
Original draft failures and the independent review are retained separately by
the integrator; passing controls do not rewrite their earlier outcomes.

C199/C200 schedules remain closed. Original hashes, budgets, qualified source and
all historical evidence are preserved. The full legacy regression remains failed:
4,239 passing methods and thirteen torque-read methods not run after the unchanged
30,000 ms setup timeout. This increment does not rerun or close that failure,
establish a broader release, or demonstrate comparative authoring advantage.
