# Independent C206 transaction and accepted-source review

**Decision: APPROVE_FIXTURE_COMPONENT_ONLY.** The selected file/closure component
passes its independent review. Production compatibility remains blocked by the
documented working-directory disagreement. This decision grants no native
readiness, execution authority, actual destination acceptance or admission.

## Exact reviewed candidate

- Commit: `afa0a9d40ab0ffbf88e6540bbb685d889a67d391`
- Tree: `2ab3ea43db443f3a33c1aed0cb3a8e36a28cf79d`
- Base main: `f90e012fa9b68a1111b97586c6462851e6166dea`
- Changes: three additions only: `transaction.py`, its dedicated CPU controls,
  and `TRANSACTION-C206.md`.

The reviewer used a separate worktree and branch at the exact candidate. The
worktree was clean, and all 56 reviewed file bindings matched their committed
bytes. The bindings cover the new files, prior components and contracts,
qualified shared roles, independent reader and synthetic fixture scaffolding.
See [candidate bindings](CANDIDATE-BINDINGS.json) and
[machine-readable decision](REVIEW.json).

## Executed checks

All **22 independent CPU controls passed**, with zero product child-start
attempts. Source and test bytes remained unchanged during the run. The controls
exercise the actual component, lowerer, GLB reader, receiving comparator,
filesystem sealing and atomic pointer replacement. They reuse the implementer's
explicitly synthetic fixture scaffold only to construct temporary input/stage
files; their mutations, expected references, assertions and interruption probes
are independently written. The script and
[complete result](final/independent-controls.json) are retained.

The checks cover the whole A01–A04 transaction sequence and exact accepted-source
paths; explicit predecessor, regeneration and equality references; changed
accepted source/dependencies and same-revision unrelated pointers; altered jobs
and provenance; missing native startup and supervisor files; underlying process
identity/log inconsistencies; actual receiving-geometry disagreement; failed
cleanup; FIFO receipts and directory aliases; authority replacement; expiration
of the original transaction clock; failed conditional commit; and two
post-commit interruption points. Every returned acceptance retains false
execution/readiness/admission fields.

A synthetic production-shaped input set was made internally consistent with
the existing C205 schema and separately passed through its real validator.
C206 rejected it with the concrete production working-directory gate. A direct
constructor attempt also rejected. These are fixture controls of a rejection
path, not current-host evidence or a production lock.

The implementer's recorded cohort passed **47 methods**. I inspected its final
log and retained its SHA-256 in the review record; I did not rerun that cohort.
Root owns applicable existing checks and actual-main verification separately.

## Original findings and repairs

The initial draft, SHA-256
`d8a34fc5df726c988309ab0a06328309b58a3bb4159112885c9b8ed2a4470f90`, is retained as
`transaction.draft-observed.py.txt`. Four independently executed probes confirmed
three defects. Their original failed behavior remains in
[draft controls](draft-controls.json); it was not rewritten into passing evidence.

1. **Incomplete qualified output inventory.** The draft rejected
   `native-startup.json` and the supervisor's construction/receiving process
   receipts, although the unchanged qualified roles produce them. The final
   component retains and validates those files and their links to artifacts,
   logs and observations. Final positive controls demonstrate that the complete
   inventory is accepted; missing or inconsistent receipts reject.
2. **Unchecked job and provenance bytes.** Altered construction settings paths
   and receiving candidate paths were accepted by the draft. The final component
   recomputes exact job/provenance data and rejects these mutations before
   promotion. The original two failing probes and final rejection controls are
   distinct records.
3. **Lost reply at the pointer commit point.** An actual `os.replace` followed
   by a controlled `KeyboardInterrupt` left the draft's pointer committed without
   returning `UNKNOWN`. The final exception paths inspect the actual pointer
   instead of relying only on an in-memory flag set after the call. Independent
   probes confirm `UNKNOWN` and matching intended/observed states both after
   replacement and after the promotion function has committed but loses its
   return. Neither path permits repeat completion.

Static review also requested protection against constructing a production-shaped
session through the public class constructor. The final factory token and
fixture-purpose invariants reject that ordinary API bypass. No executed failure
on the earlier constructor is claimed; the final rejection was independently
executed.

## Accepted-source and transaction boundary

The component distinguishes schedule predecessor, source-regeneration reference,
equality references and per-store pointer predecessor. A03 follows A02 while
reading A01's actual accepted source; A04 follows A03 while reading A02. Both
regenerations use retained editable files and their dependency manifest, and
the lowerer processes those actual bytes. A copied GLB or prepared canonical
record cannot substitute for accepted source.

The accepted handle pins exact pointer bytes and the transaction receipt. That
receipt binds the sealed construction and receiving closures, including their
source, outputs, measurements, jobs, logs and underlying receipts. Later
validation detects changed retained bytes and inventories. Exact paired and
regeneration GLB equality also preserves the right sibling's delivered data.
This is transaction evidence; it does not establish that Node checks, D01/D03,
image review or complete schedule ordering occurred.

The historical store's sealing/verifying primitives remain unchanged. The
separate C201 promotion operation compares exact pointer absence under the
promotion lock, then writes, synchronizes, replaces and reads the pointer.
Pre-commit failure preserves the prior pointer. Post-commit uncertainty retains
the actual state without claiming rollback. The original clock remains attached
to preparation through completion, while hard child supervision remains the
future coordinator's responsibility.

Process evidence is validated for consistency, file identity and bounds. The
component cannot authenticate a caller or prove that its supplied files arose
from an actual native process. The fixture-native container and image are
synthetic bytes, and all current accepted bindings are explicitly fixture-only.
Filesystem checks are not protection against unrestricted access to Python
internals or the trusted host. The later bootstrap and coordinator must own
isolation, receipt provenance, one-use ledger integration and durable authority.

## Production blocker and next gate

C205 fixes every command's working directory to the repository root. The
unchanged qualified supervisor launches each child in its stage directory, and
the worker derives its output from that directory. This is a real incompatible
binding, not a missing test. C206 rejects all `production-inputs` sessions and
documents the fixture adapter's separate declared and observed directories.
No existing lock, supervisor, worker or protocol bytes were silently changed.

The next bounded step is to align C201 command working-directory bindings with
the qualified stage contract, independently review that change, and only then
consider removing this specific fixture-only block. Full Node/readback,
orchestration, current-host dependency/alias sealing, trusted bootstrap,
independent native readiness and actual admission remain later gates.

Root reported one separate historical documentation defect: the existing C205
evidence README links to `final-tests.log`, absent from the baseline Git tree.
The exact original log survives in the C205 package under
`workers/input-lock-impl/final-tests.log`. Root plans an evidence-only restoration
of those unchanged manifest-bound bytes, retaining the original failing link
report and rerunning documentation checks. That restoration is outside the
three-file component candidate reviewed here; it does not change this review's
source identities or count as another product feature.

C199/C200 remain closed. The inherited regression remains **FAILED**: 4,239
distinct passing methods and thirteen torque-read methods not run after the
unchanged 30,000 ms setup timeout. No native, receiver, Node, lifecycle or
timed-author run occurred in this review. Original visual limits, broader
compatibility obligations, release gates and unestablished comparative authoring
benefit remain unchanged.
