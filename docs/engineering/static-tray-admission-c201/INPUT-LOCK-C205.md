# C205: C201 executable input-binding validator

> **C207 update:** The [reviewed working-directory contract](WORKING-DIRECTORIES-C207.md) requires every planned stage cwd to equal its own output directory. It preserves the exact argument, environment, output, approval and source bindings below. Old repository-cwd plans reject before preparation. This binding correction grants no process-start or native-readiness authority.

This increment adds a separate validator for the approved four-slot
[C201 admission protocol](ADMISSION.md). An input lock is a record of the exact
source, dependencies, commands and paths that a future invocation intends to
use. The validator rejects missing or changed bindings before any caller could
start a child. It does not implement that caller or authorize execution.

The new component is
[`input_lock.py`](../../../prototypes/static_tray_admission_c201/input_lock.py).
It leaves the existing ledger, qualified geometry, C199/C200 code, historical
input locks and four approved protocol documents unchanged. There is no
production C201 lock, current-host verification or native-readiness receipt in
this increment.

## Separate trusted facts and candidate data

The public operation is `validate_input_lock(lock_path, approval_path,
context=trusted_context)`. The keyword-only context is a frozen `TrustedContext`
whose fields are immutable scalar values and a tuple of gate issuers. It must
come from separately retained host-sealing and independent-review facts, outside
the candidate lock, approval and output directories. The component deliberately
provides no constructor that derives trusted expectations from an untrusted lock.

The context binds repository and host roots, independently observed source commit
and tree, exact lock and approval byte digests, the independently inventoried
dependency closure, the reviewed launch plan, producer and reviewer identities,
evidence purpose and the fixed authority directory's path, device and inode.
The future trusted bootstrap must retain this same authority across controller
restarts and output-directory changes. The producer cannot select a fresh root
or mint a replacement trusted context to erase a stopped invocation.

**This is a trust boundary, not an authentication service.** Python callers can
construct a context object. The validator cannot establish that an arbitrary
caller is an independent reviewer, that a supplied Git identity was genuinely
observed, or that context storage survived a restart. It neither runs Git nor
inspects the currently running interpreter's provenance. The later bootstrap
must establish those facts from the actual committed checkout, current host,
complete inventories and independently received approval. Constructing context
fields by copying a submitted lock would defeat their purpose and is not a
supported production integration.

## Lock schema and checks

The schema is `ontokin.c201.executable-input-lock/0.1`. Each object has an exact
key set. Duplicate JSON keys, nonfinite values, excessive nesting, wrong types,
unknown fields and the old twelve-slot schema fail. JSON inputs are bounded to
16 MiB, each inventory file to 8 GiB and the complete file inventory to 16 GiB.
These are validator resource limits, not changes to the protocol's execution
budgets.

| Binding | Validation performed |
| --- | --- |
| Protocol | Exact approved `ADMISSION.json`, four preparation documents and independent protocol-review bytes; all frozen source, normative and qualified-role bindings are required. |
| Schedule and limits | Exact A01/D01/D03/A02/A03/A04 order, routes, pair/regeneration/predecessor references, ceilings and original stage, source, output and log limits. Integer/boolean substitutions fail. |
| Source | Commit/tree equal independently observed trusted identities; a complete declared repository-file inventory is checked against actual current bytes, sizes and modes. |
| Executable roles | Every qualified shared role, seven separate C201 roles and nine host-role groups must be present. Old transaction, lock or readback paths cannot substitute for new C201 roles. |
| Dependencies | Every input has a graph entry; references resolve without duplicates or self edges; every input is reachable from required roles or preserved protocol bindings. The complete graph and inventory must match the separately sealed closure digest. |
| Commands | Exactly three stages for each A01–A04 slot, exact inherited safe flags and expanded job paths, bound executable/script/loader roles, clean native/Node environments and working directories. The entire launch plan must match independent review. |
| Stores and outputs | Four stores, four per-slot environment roots and twelve stage-output directories exist and are initially empty. They, the repository and the authority root are disjoint and have distinct filesystem identities. Every actual host/gate input file stays outside those roots. |
| Authority | The schedule, absolute path, device and inode equal the independently retained authority. An existing invocation receipt or orphaned journal rejects a new invocation. |
| Host and evidence | Intended dependency versions equal the protocol. Three exact gate receipts bind implementation review, CPU controls and current-host verification to this source and dependency closure. |
| Approval | An independently pinned approval binds exact lock, source, protocol, schedule, closure, launch plan, authority, ceilings and gate-receipt hashes; the reviewer differs from the producer. |

An input ID is `repository:<relative-path>` or `host:<relative-path>`. Its binding
contains `root`, `path`, `size_bytes`, `sha256` and integer permission `mode`.
Repository roles name their exact required path. Host roles cover the Python
executable and standard library; Blender executable and distribution; dynamic
loader and shared libraries; and Node executable, packages and module loader. The separately
reviewed inventory must include every actual transitive executable/library,
module, package initializer and other runtime dependency in those groups or in
their dependency closure.

`host_root` is an input-path namespace and may be `/`: the real interpreter,
ELF loader, shared libraries and native distributions can span `/usr`, `/lib`
and `/opt`. It is not a staged substitute distribution and is not required to
be disjoint from all output directories. Instead, every actual inventoried
host/gate input file must lie outside the repository, authority and all writable
store/output/environment roots. This permits real absolute host locations
without treating an entire host-root directory as the dependency inventory.

Graph reachability does **not** discover omitted Python imports, dynamic imports,
native loader dependencies, package aliases or undeclared filesystem reads. The
future sealer must inventory them independently and map platform aliases to a
reviewed launch environment. This component conservatively rejects symlink and
hardlink input paths rather than silently resolving them. Native distributions
with aliases therefore need a separately reviewed alias/inventory integration
before a production lock can pass. No alias-resolution policy is invented here.

Commands are reviewed argument vectors, not shell text. Construction and
receiving preserve the qualified background/factory-startup/disable-autoexec,
two-thread, exit-code and system-environment flags, with the exact worker or
receiver and each stage's expanded `--job` path. Their environment retains the
qualified fixed variables, including software rendering and safe Python paths.
HOME, XDG, TMPDIR and Blender configuration/script directories are bound beneath
that slot's separate environment root. Those future subdirectories do not exist
at preflight because the root must be empty; the coordinator must create and
validate them before launch. Node preserves the no-addons and 256 MiB heap
flags, exact module-loader/probe/job paths and its qualified clean environment.

The validator verifies these planned argument strings; it does not prove the
future programs interpret their jobs or write outputs correctly. Actual
transaction, readback and coordinator compatibility must establish that behavior.
The three per-slot child stages do not replace the separate committed coordinator
and transaction role bindings. The trusted bootstrap must also establish its own
clean Python host environment before constructing context.

All file reads open ancestor directories without following symlinks, then use
nonblocking regular-file reads with size, link-count, mode and hash checks.
FIFO, device, symlink and hardlink substitutions reject. Filesystem metadata is
checked before and after each read. Absolute paths have exactly one leading
slash, so an alternate POSIX `//` spelling cannot conceal nested outputs.

## Evidence and approval chronology

`gate_receipts` has exactly `implementation_review`, `cpu_controls` and
`current_host`. Every receipt is separately read, hash checked and required to
name its gate, purpose, trusted issuer, passing outcome, exact source revision,
protocol/schedule and closure digest. An implementation-review issuer cannot be
the producer. The later real sealer must provide actual reports behind these
receipts; a matching JSON claim is not proof that the described work occurred.

The separate `ontokin.c201.input-binding-approval/0.1` record names either
`FIXTURE_BINDINGS_ONLY` or `APPROVE_INPUT_BINDINGS_ONLY`. Its bytes and reviewer
identity must arrive through the independent trusted channel. It is a binding
review, not the full native-readiness decision. Production approval and real gate
receipts are still absent. The producer has no approval-writing entry point in
this component.

The returned frozen `ValidationResult` reports verified binding identities.
`native_start_authorized`, `native_readiness` and `admission_completed` are always
false, including a structurally valid production-inputs record. The validator
writes no receipt and reserves no stage. A passing result is a snapshot; it does
not prevent later changes between verification and use.

The later coordinator must retain or revalidate verified inputs before use,
obtain separate native-readiness approval and call the existing
[one-use ledger](LEDGER-C204.md) with the fixed authority. The ledger's exclusive
creation, not this read-only precheck, resolves racing invocations. Unknown or
stopped receipts remain nonresumable. Deleting an output directory or clearing
only the journal cannot grant a new invocation; external protection must also
prevent removal of all trusted authority evidence.

## CPU controls and exact stopping point

The dedicated
[test module](../../../tests/test_static_tray_admission_c201_input_lock.py)
executes the actual validator against real temporary files. It copies the
approved protocol and historical bindings unchanged. Future C201 roles and host
dependencies are explicitly synthetic fixtures, and every gate/approval says
`fixture-only`. Test code deliberately repins outer lock/approval hashes for
many mutations so that fixed role, schedule, source, dependency, command,
authority and evidence checks are exercised independently of a top-level
digest mismatch. Subprocess, fork and shell launch seams are blocked.

Run the focused controls with:

```sh
python3 -B -m unittest discover -s tests -p test_static_tray_admission_c201_input_lock.py -v
```

The coherent next step is the separately reviewed C201 transaction/readback
compatibility increment. Complete process orchestration, accepted-source and
regeneration resolution, real equality/sibling checks, deadlines, cleanup and
atomic promotion remain pending. A later current-host sealing step must fill
all actual missing roles/dependencies, establish durable trusted context and
independent binding/native-readiness approval before the sole four/four/four
invocation. This increment executes zero native, receiver, Node, lifecycle or
timed-author starts and does not consume the actual C201 schedule.

The historical full regression remains failed: 4,239 distinct passing methods
and thirteen torque-read methods not run after the unchanged 30,000 ms setup
timeout. C199/C200 remain closed; visual limits, broader external compatibility,
comparative authoring advantage and the complete [GOAL](../../../GOAL.md) remain
open. Passing this component gate does not alter those results.
