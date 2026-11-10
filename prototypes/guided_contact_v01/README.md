# C191 finite guided-contact prototype

This separately invoked prototype implements the adopted
[C191 experimental contract](../../docs/language-design/guided-contact-v0.1/SPECIFICATION.md).
It does not change `python -m ontokin`, the `.22` parser, Agent transports or
historical tests. Source `c191-experimental-0.1` describes only the seven-part
two-carriage gauge. The four source examples declare two 1 kg mass owners,
four shoe/stop contact boxes and two massless spatial attachments.

The source literal parser validates identity, exact units, ownership, motion
authority, admitted geometry and execution requests. A pinned Blender subprocess
constructs the declared native scene from an empty scene and records 481 native
poses. A finite GLB encoder retains those times and carriage X values. The
disclosed final projection removes only transverse/rotation guide residuals.

## Run

From the repository root, set `BLENDER` to the adopted Blender 4.5.3 executable.
Its SHA-256 must be
`5e15447670804c855fef6033ac9b8fd82696b762095becf0df79b1c2f8034397`.
The prototype uses Python's standard library; Blender is the explicitly selected
external backend. Independent qualification tools have their own dependencies.

```sh
python -m prototypes.guided_contact_v01 validate \
  docs/language-design/guided-contact-v0.1/examples/A.ok \
  --host-max-operations 1000000 --host-max-elapsed-ms 80000 \
  --canonical-out /tmp/c191-A-canonical.json

python -m prototypes.guided_contact_v01 run \
  docs/language-design/guided-contact-v0.1/examples/A.ok \
  --store /tmp/c191-A --blender "$BLENDER" \
  --host-max-operations 1000000 --host-max-elapsed-ms 80000 \
  --result /tmp/c191-A-result.json
```

Ordinary defaults remain 100000 operations and 30000 ms. The qualification
examples request 1000000 operations and 80 s, so the host must explicitly supply
the matching ceilings. `validate` does not change accepted state. It may write
the requested canonical diagnostic file. Both commands print a JSON result;
failure returns exit status one.

`run --expected-revision SHA` compares the accepted source revision before work
and before commit. `--cancel-file PATH` treats creation of that file as a
cancellation request. `--reopen PATH/scene.blend` reopens and clears the saved
native scene in a new process, without reconstruction or repairs. The supplied
source must match the scene's saved source identity.

## Artifacts and commit point

`STORE/state.json` is the sole accepted-state pointer. It binds the accepted
source hash, canonical input, immutable artifact directory and file manifest.
Each attempt has a separate receipt under `STORE/attempts/ATTEMPT_ID`.
Invalid edits, resource exhaustion, cancellation, malformed results and failed
pointer replacement retain the old pointer and every previously accepted byte.
An orphan candidate directory is explicitly identified as unaccepted evidence.

A successful artifact directory contains:

- Exact source, canonical solver input, source/dependency manifest and backend
  mapping. The original contract manifest and C191-A1 are hash-verified.
- The executed implementation's file hashes and copies. The native subprocess
  executes its retained worker-script copy. Git HEAD and dirty state are recorded
  separately, so a source commit cannot be mistaken for different worktree bytes.
- Editable `scene.blend`, strict `native-result.json`, native configurations,
  481 world-matrix records, derived gap/velocity CSV and native summary.
- Body/collider/visible-part/helper mapping, `raw.glb`, `final.glb` and an exact
  projection receipt with changed fields, X preservation and continuous bounds.
- Native command, timing, bounded stdout/stderr and a SHA-256 file manifest.

The adapter reports represented, constructed, evaluated and exported levels.
It does not set destination validation true. Independent raw/final analysis and
actual receiving-application evidence are separate qualification gates.

## Trusted test seams

The Python entry points are `api.validate_source(...)` and `api.run(...)`.
`run` accepts an optional `hooks` dictionary from the trusted host. This is a
failure-testing seam and is never configurable through `.ok`. Hook names are
recorded in the attempt context; formal native qualification uses no hooks.

| Hook | Arguments and purpose |
| --- | --- |
| `worker_command` | `(argv, stage) -> argv`; substitute a controlled blocking or logging test process |
| `worker_started` | `(process, stage)`; observe the actual native PID and request cancellation |
| `before_native_validation` | `(stage)`; mutate serialized native results before strict validation |
| `before_projection` | `(stage)`; supply an over-bound raw guide residual to the actual projection |
| `before_mapping_validation` | `(stage)`; alter final X/time bytes before the preservation checks |
| `before_publication_validation` | `(stage)`; exercise output-byte limits |
| `replace_state` | `(temporary_state, state_path)`; defaults to `os.replace`, the actual commit point |

`supervisor.supervise(argv, stage, budget, backend, backend_span, hooks=None)`
is the actual process supervisor used by transactions. It starts a new process
session, reads capped streams, checks the deadline and cancellation at intervals
of at most 50 ms, and terminates/reaps the group. Linux child-subreaper behavior
allows it to reap descendants after the worker leader exits. Termination grace
is at most 500 ms before SIGKILL; qualification measures complete cancellation
within two seconds. A result arriving after a failed deadline cannot commit.

## Scope and limits

This is feed-controlled box contact on one finite assembly. The native compound
construction includes the explicitly mapped hidden carriage boxes and passive
base, with the measured collision-group scheme. The motor's impulse bound is
not a calibrated actuator-force model. Native substep positions, direct Bullet
velocity, contact manifolds and impulses are not exposed. Recorded velocities
and gap flags are derived from evaluated poses.

The direct raw encoder is a new experimental output binding. It does not claim
byte identity with C190's Blender animation exporter. Formal reproducibility
requires identical canonical inputs and final GLBs across fresh C191 builds on
the pinned runtime. A successful C191 run does not qualify general dynamics, a
production backend, relative authoring cost, a full release or the project goal.
