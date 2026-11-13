# C231/0.1: ledger file identity and handle lifetime

This repair restores the replacement-rejection requirement of the
[C204 ledger](../static-tray-admission-c201/LEDGER-C204.md). It changes the
experimental ledger implementation in place. It does not change its schedule,
evidence formats, diagnostics, budgets or readiness meaning. The four frozen
C201 protocol files and their 42 source/role bindings remain exact. Historical
hashes and the consumed C229/C230 diagnostic plans identify their original
implementations and must not be resealed against this repair.

## File identity

The live capability retains the exact descriptors used to create its invocation
marker and journal. Each descriptor keeps the original POSIX file object alive;
a replacement cannot inherit that original object's device/inode pair through
ordinary inode recycling while the descriptor remains open. Both descriptors
must still identify their original regular files with exactly one link before
an append. The implementation checks them again after reading the current
paths. The existing exact bytes, pathname identities, no-follow/nonblocking
opens, directory checks, bounded journal reads and checked append remain.

The retained descriptors are private identity pins. The journal continues to
use its independently checked append path. No native application, child-stage
permission or accepted-source mutation is added. The trusted-host boundary
remains: these checks do not defend against interpreter tampering or an actor
who can replace all authority across host restarts. Directory-identity behavior
is unchanged by this narrowly selected file-object repair.

## Handle lifecycle

Cleanup ownership and weak live-object tracking exist before the first file is
created. Partial creation and a failed or interrupted initial append close all
acquired pins while preserving every durable file. A failing public mutation
poisons the capability before cleanup. Normal completion, explicit stop,
negative observations and every mutation interruption close both pins.

`close()` is idempotent. It does not append, delete, reset or rewrite evidence.
Disposing unfinished work stops the capability and sets the existing
`persistence_or_interruption_uncertain` flag, because no completed durable
observation is established by disposal. `with Ledger.begin(...) as ledger`
calls `close()` on exit and does not suppress an exception. Weak-reference
finalization attempts abandoned-object cleanup without keeping the Ledger alive.
Automatic collection/shutdown cleanup is best effort under asynchronous
interruption; explicit close or context management is the normal lifecycle.

Each owned descriptor receives at most one close attempt. A close exception
stops the capability, marks uncertainty and clears in-memory completion; every
other owned descriptor still receives an attempt. With no prior exception,
cleanup interruptions propagate and ordinary close failures report PERSISTENCE.
Cleanup preserves an already active failure rather than replacing its cause.
An uncertain close is never retried because its numeric descriptor may already
have been reused. No claim of successful resource release follows a lost close
result merely from the attempt. Process termination remains the operating
system's final cleanup boundary.

Explicit disposal acquires lifetime coordination before closing or detaching the
finalizer. If that acquisition is interrupted, no descriptor close has started:
owned pins and the finalizer remain available, the capability is stopped and
uncertain, and in-memory completion is cleared. Later explicit disposal can
make the first close attempt on those retained handles. This is distinct from
retrying a descriptor whose close result is uncertain. An already active body
or mutation exception retains precedence over the cleanup interruption.

Creation descriptors are non-inheritable under the Python file-descriptor
contract. A child-fork hook closes child copies, stops copied capabilities and
replaces inherited mutexes. A coordination lock serializes retained-descriptor
acquisition/registration and removal/close against a concurrent fork, including
partial creation. Every mutation also rejects a different process
identity before acquiring a mutex, so it cannot wait on a lock owned by a
vanished parent thread. Child cleanup does not close the parent's descriptors
or change its capability. A fork inside an arbitrary hostile callback or an
interpreter with altered descriptor semantics is outside this trusted-host
component contract.

## Required evidence and limits

The entire original ledger test file remains byte-identical. Additive
[CPU controls](../../../tests/test_static_tray_admission_c231_ledger_identity.py)
force only a recreated file's numeric identity to equal the original while
preserving real file-object link observations. Rejection and the later STOPPED
result are checked separately, without requiring actual inode recycling.
Controls also observe acquired-descriptor closure across partial creation,
failed persistence, terminal observations, completion, interruption, disposal
and process boundaries. One bounded CPU fork checks copied pins and an inherited
locked mutex; it records exit, timeout and reaping. It starts no native product.

Run the affected C201 CPU cohorts and the additive C231 controls on an identified
source revision, preserve exact outcomes, then run documentation preservation
and links. A focused pass does not complete R02. The fresh full aggregate is a
separate next step; C228's failed aggregate and all prior failed or unrun gates
retain their recorded meanings. The C201 coordinator/native admission and all
consumed native schedules remain deferred or closed.
