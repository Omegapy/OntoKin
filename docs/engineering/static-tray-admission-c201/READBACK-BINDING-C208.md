# C208: C201 readback job and result bindings

C208 defines and checks the data boundary between an accepted C201 transaction
and its future Node readback. Readback means reopening the delivered GLB, checking
its glTF format with Khronos Validator and measuring its imported objects with
Three.js. This component prepares the exact job and verifies retained observations.
It does not run either external checker.

The implementation is
[`readback_binding.py`](../../../prototypes/static_tray_admission_c201/readback_binding.py).
The C201 `format_check.py` wrapper and `readback.mjs` probe remain unimplemented.
The historical twelve-slot wrapper and probe retain their original bytes, schemas,
limits and closed qualification. They cannot consume this new job by substituting
an old manifest or disabling a guard.

## Public operations and authority

| Operation | Checked behavior |
| --- | --- |
| `bind_readbacks(transactions)` | Retains and revalidates an actual C205/C206/C207 transaction-binding session. It starts and reserves nothing. |
| `prepare_readback(bindings, slot, accepted=handle)` | Verifies that slot's accepted pointer and complete transaction, construction and receiving closures. Writes one job to the exact bound, empty Node output directory. |
| `inspect_readback_job(prepared)` | Rereads the accepted closures and exact job bytes, returning a fresh job object. Inspection remains possible after a result check stops. |
| `verify_readback_result(prepared, process=observation)` | Checks all five expected files, strict probe observations, process/log consistency and unchanged accepted inputs. Returns `BINDINGS_VERIFIED` only for this evidence boundary. |

Prepared jobs and returned evidence always have false process-start,
native-readiness, admission and next-slot authority fields. Returned evidence also
sets `authenticated_execution=false`. A consistent synthetic observation is not
proof that Node ran. The trusted future wrapper must establish process provenance;
the coordinator must own reservations, cross-restart stopping, order and D01/D03
controls. A caller copying trusted values from its own submitted records defeats
the inherited trust boundary and is not supported production integration.

The component does not write an accepted pointer, promote a transaction, advance
the ledger or create family-admission evidence. A Node failure cannot undo the
earlier technical transaction acceptance, and that acceptance cannot hide the
readback failure. Both states remain separately inspectable.

## Exact C201 job

The schema is `ontokin.c201.readback-job/0.1`. The job binds:

- A01–A04 slot, route and Q01 case, the approved protocol and schedule digests,
  the input-lock and approval byte digests, and the locked source commit/tree and
  declared source-file inventory.
- Exact accepted-pointer bytes, accepted revision and transaction-receipt hash;
  the construction and receiving closure hashes; and the accepted source identity.
- Actual accepted `final.glb` and `independent-audit.json` paths, sizes and hashes.
  The audit must itself pass for Q01 and name the actual GLB hash.
- The exact C207 command, including safe Node flags, clean environment and the
  Node stage as cwd/output; every absolute expected output path; fixed check
  options, dependency versions and resource limits.

The accepted transaction is rechecked before job creation, after creation, before
result inspection and again before returning evidence. The retained pointer,
source, dependencies, receipt and complete construction/receiving output closures
must still match. Another handle with an equal revision string is insufficient.

The five Node-stage files are exactly `job.json`, `probe.json`, `node.process.json`,
`node.stdout.log` and `node.stderr.log`. Missing or additional files reject. Files
must be bounded private regular files; symbolic links, hard links and unsafe
ancestor paths reject through the existing input validator. Directory identity
must match the original validated plan. The job and every observed output are
reread for byte equality before success.

The new helper must be included in the future executable lock's complete
transitive input closure, including as a dependency of the eventual wrapper.
This increment does not alter the seven C205 role names. Its fixture lock is an
explicit synthetic control and does not establish that a complete production
executable closure or current-host seal exists.

**This version is not a complete executable probe job.** The C205 `node_packages`
role inventories a closure but does not identify the validator entry, Three.js
entry, GLTFLoader entry and package metadata as separate executable targets.
Historical readback obtained those paths from its twelve-slot manifest, which
is not admitted here. A future versioned, independently reviewed job contract
must bind named package entry points to exact paths and bytes within the sealed
dependency graph, rejecting ambient imports and undeclared resolution. Adding
those fields changes this exact schema and requires an explicit contract revision.

## Probe result and inherited checks

The distinct result schema is `ontokin.c201.readback-probe/0.1`. Success has an
exact field set. It repeats the bound source, slot, accepted revision, pointer,
receipt, GLB/audit hashes, options and limits, and names the SHA-256 of the exact
job bytes. The required state is `PASSED`; a bare `passed=true` is insufficient.
Historical result schemas, wrong slots/revisions, changed checks and extra
authority claims reject.

### Khronos Validator

The intended version remains `2.0.0-dev.3.10`. The job retains GLB input,
`uri=final.glb`, disabled timestamps, at most 1,000 issues, no ignored issues,
no external resources and zero allowed errors or warnings. The result must
retain the raw report with its matching validator version and URI. Error and
warning counts must be integer zero, truncation must be false, and informational
and hint counts must agree with the actual issue-message severities. A claimed
pass cannot conceal a warning, truncated result or inconsistent message inventory.

### Three.js CPU import

The intended version remains `0.186.1`, revision `186`. The report must describe
one scene, fourteen named nodes, twelve meshes, zero cameras and zero animations.
It must explicitly retain empty unsupported-object, texture and external-resource
observations. These extra C201 fields make the historical probe's implicit
rejections visible; they do not claim execution before that probe exists.

For every stable semantic identity, the component compares the recorded original
name, semantic properties, owner/follow relationships, children and parent to
the accepted independent audit. Three.js may sanitize its separate importer name;
that does not relax the original-name or identity check. Empty roots and actual
mesh nodes have distinct exact field sets.

The actual recorded world matrices, vertex arrays, normals, triangle indices,
materials and bounds must agree with the accepted audit. Local positions must
also be consistent with the recorded matrix and world vertices. The original
0.000005 m position/dimension allowance and 0.000001 matrix/normal allowance stay
fixed. The component reconstructs every required numeric comparison, rejects
nonfinite values and boolean-as-number substitutions, and checks the complete
ordered measurement list, including each threshold, difference and pass flag.
For the synthetic public Q01 fixture this is 2,060 numeric rows. A missing node,
omitted measurement or contradictory geometry rejects even if the summary says
the import passed. This verifies supplied measurements; the future actual probe
must obtain them by importing the delivered GLB.

## Process observations, limits and uncertainty

The Node job fixes the existing 30,000 ms outer, 28,000 ms child-work and
2,000 ms cleanup allowances; 8 MiB GLB; 4 MiB result; and 4 MiB combined logs.
The retained observation binds the exact job command/environment/cwd, lock,
slot/stage, requested/effective limits, process identity, zero exit status,
closed handles and successful cleanup to the actual supervisor-record bytes.
Actual retained stdout/stderr lengths must equal both supervisor counters.

The qualified supervisor does not expose a separate child-exit timestamp.
For passing records, this component conservatively requires the entire retained
supervisor duration to fit within the 28,000 ms child-work allowance. It also
requires the qualified successful cleanup convention of zero termination-cleanup
milliseconds. The outer allowance remains independently bound; the future wrapper
must enforce its own original outer clock across job preparation, supervision,
verification and persistence. Checking reported numbers cannot enforce a process
deadline or authenticate a timestamp.

Each prepared handle is consumed by one result-verification attempt. Failed or
unknown checks stop that in-memory binding session and block its later prepares
and retries. Explicit `UNKNOWN` or interruption returns an unknown outcome.
Partial files and the original job remain; the accepted pointer is never changed.
Durable one-use invocation state, recovery after process restart and protected
authority storage remain the existing ledger/future coordinator's responsibility.
Creating a fresh component object is not a new execution authorization.

## CPU evidence and stopping point

The [focused controls](../../../tests/test_static_tray_admission_c201_readback_binding.py)
exercise real accepted-source resolution, sealed closures, file reads, job writes
and result checking. Their GLBs, native containers, images, Node reports and
process observations are explicit synthetic fixtures. Child-launch seams are
blocked. No native, receiving, Node, lifecycle or timed-author process starts.

```sh
python3 -B -m unittest tests.test_static_tray_admission_c201_readback_binding -v
```

The exact next increment is the separately reviewed named-package resolution and
versioned executable job contract needed by the C201 probe/wrapper, checked through
CPU-only seams while actual Node execution stays gated. Full process provenance and deadlines,
coordinator/control/ledger sequencing, trusted bootstrap, real host/dependency
and alias sealing, independent readiness, the sole four/four/four invocation,
image review and final admission remain pending.

All four approved C201 protocol documents and qualified C199/C200 source,
locks, evidence, budgets and closed schedules remain unchanged. The inherited
full regression remains **FAILED**: 4,239 distinct passing methods and thirteen
torque-read methods not run after the unchanged 30,000 ms setup timeout. This
increment does not rerun that suite, establish broader compatibility or measured
authoring advantage, or complete the [GOAL](../../../GOAL.md).
