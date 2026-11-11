# C204: C201 schedule and reservation ledger component

This increment implements preparation components for the approved
[C201 protocol](ADMISSION.md). It is not the executable admission coordinator.
The current source has no child-launch entry point, executable input lock,
readiness approval or native admission result. The four approved protocol
documents and all historical C199/C200 files remain unchanged.

## Implemented boundary

[`schedule.py`](../../../prototypes/static_tray_admission_c201/schedule.py)
binds the exact approved `ADMISSION.json` digest and its complete schedule.
It rejects missing, extra, duplicate, reordered and wrong-route slots, altered
ceilings, wrong predecessor/regeneration/equality references, a historical
twelve-slot plan, and JSON type changes such as a boolean used for an integer.
Caller mutations cannot alter the fixed in-process contract.

[`ledger.py`](../../../prototypes/static_tray_admission_c201/ledger.py)
provides a one-use accounting capability. Its order is A01, D01, D03, A02, A03,
A04. Each slot can reserve construction, receiving and actual-delivery Node
checking once, with maxima of four each. A reservation consumes its allowance
before persistence is attempted. A receipt is returned only after a successful
append and `fsync`; a failed or uncertain persistence operation stops the
capability and cannot authorize a child. Receipt fields explicitly say
`native_start_authorized=false` because this component has no readiness gate.

Receiving requires a successful construction and cleanup observation. A
promotion observation requires successful receiving and cleanup. Node requires
the recorded conditional-promotion and cleanup observations. D01 and D03 follow
A01's Node observation, in that order, and must record their assigned findings,
no `STRUCTURE` finding, and unchanged accepted closure. A failed, timed-out,
cancelled or unknown observation stops the remaining schedule. Wrong-order and
wrong-identity calls also stop it. All public mutations poison the live
capability on an interruption, including an interruption after durable append
but before in-memory bookkeeping or final completion returns.

These are **observation gates**. The ledger binds supplied evidence digests;
it does not open that evidence or establish the truth of a cleanup, equality,
source-preservation, measurement, or pointer-promotion claim. It never mutates an
accepted pointer. Actual closure validation, atomic transaction promotion and
delivery checking remain required before a future coordinator may report
success observations to this component.

## Durable authority and recovery

The trusted caller supplies one existing absolute reservation-authority
directory, disjoint from its initially empty output directory. Both directories
and every ancestor must be real directories. The authority is a host-controlled
input that the future executable lock must bind. It cannot be chosen afresh
when an invocation fails.

The authority holds an exclusive immutable invocation receipt under the fixed
schedule ID and a separate append-only, hash-linked journal. File and directory
creation are synchronized. The live capability checks exact receipt/journal
bytes and filesystem identities before each append. Missing, replaced,
truncated, aliased, nonregular or overlarge files stop progression; nonblocking
file opens prevent a FIFO from trapping the integrity check. An existing receipt
blocks another invocation even when its journal is cleared or absent. An
orphaned journal also blocks it. Changing output directories cannot clear this
authority. The implementation never deletes or resets prior evidence.

The threat boundary is a trusted persistent authority, not a tamper-proof
machine. Someone able to remove all authority evidence, substitute an unrelated
authority root, or modify the interpreter can bypass a filesystem ledger.
Binding and retaining that authority across host/controller restarts is a
pending executable-lock responsibility. This component must not be presented
as solving that external ownership requirement by itself.

`inspect(authority)` is read-only and never produces a resumable capability.
`journal_integrity_valid` checks bounded canonical framing, receipt identity,
sequence and hash links only; `semantics_verified` remains false. It is not
independent semantic replay, proof of completed work or admission. Its event
list preserves observations for later review. The live `snapshot()` reports
in-process reservation attempts and explicitly flags persistence/interruption
uncertainty; those counts are not observed child starts or permission to retry.
`ledger_complete` means only that the observation sequence completed without a
locally observed interruption. `native_readiness` and `admission_completed`
always remain false.

## Verification and remaining work

The dedicated
[CPU controls](../../../tests/test_static_tray_admission_c201_ledger.py)
exercise the actual filesystem and state machine, including competing threads,
partial writes, failed synchronization, lost replies, interruptions after
durable append, interrupted finalization, wrong references, FIFO/alias damage,
failed cleanup/promotion, required control findings and stopped-stage
consumption. They use isolated temporary CPU-only authority directories and
synthetic evidence digests. They start zero native, receiver, Node, lifecycle
stub or timed-author children and do not consume the actual C201 admission.

Run this focused cohort with:

```sh
python3 -m unittest discover -s tests -p test_static_tray_admission_c201_ledger.py -v
```

The next implementation gate remains the separate C201 executable lock,
transaction/readback compatibility and actual coordinator described in
[IMPLEMENTATION-NEXT.md](IMPLEMENTATION-NEXT.md). It must verify immutable
accepted sources and dependencies, enforce actual process deadlines/cleanup,
perform atomic promotion and delivered-geometry comparisons, bind the fixed
authority and all current-host inputs, and obtain independent technical
readiness approval before the sole native invocation. The producer cannot issue
that approval. Four image reviews and independent final result review remain
later admission requirements.

C199/C200 schedules stay closed. The historical full regression remains failed:
4,239 passing methods and thirteen torque-read methods not run after the
unchanged 30,000 ms setup timeout. No general physics, destination behavior,
comparative authoring advantage or full-product completion is established here.
