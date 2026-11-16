# C246: held observation hook and external session registry

**Held source only. Godot parsing and native execution have not run.**
This component implements the narrow source boundary selected by
[C244 adoption](../second-target-c244/ADOPTION.md). It does not supply a complete
observer, envelope emitter, launcher, native admission or R07 acceptance.

The stateless [extension](observer.gd) overrides only `_import_node`.
The external [registry](registry.gd) retains one exact `GLTFState`, a terminal
fault latch and detached failure receipts. Its [session](session.gd) captures
original live-map associations and phase-local facts, then observes exactly 18
old-to-new descendant identity edges. A separately recorded root guard refuses
any replacement of the synthetic nonmesh root. All subscriptions use flags zero.

[Native facts](native_facts.gd) retain typed original metadata, script/signal
descriptors, parent/owner relations, and native resource identity/metadata before
the corresponding observer connection. Unsupported types and custom native
callables refuse capture. Resource arrays, complete material parameters and all
evaluated animation poses remain a separately bounded raw-capture component.
The model's metadata representation does not promise equivalence to every
GDScript Variant; its supported synthetic types are explicitly narrower.

Final live membership and phase-local facts can be recorded only after an
explicit caller-return notification, without reading the stale loader map.
The strongest component state is `CHAIN_COMPLETE_RAW_PENDING`; native
acceptance and execution admission remain false. Engine/other-extension
diagnostic coverage remains unestablished and blocks any native admission.

[The executable CPU model](inert_model.py) checks modeled state transitions.
It neither loads nor parses the GDScript sources and supplies no native proof.
[Controls](test_inert_model.py) pass 47 methods. The [binding checker](verify_bindings.py)
passes 122 read-only checks covering 21 exact upstream files, nine authority
documents, the original 18-node GLB and selected lexical source boundaries.
[Results](RESULTS.md) distinguish these checks from native behavior. Final
independent review and publication are recorded separately by the integrator.

The pinned candidate binary is present in the current root environment and its
bytes match C220 by read-only hashing. Its embedded revision still differs from
the inspected upstream revision; no version probe, parser or native start was
performed. Presence alone changes no lineage or execution gate.

## Use and limits

The future reviewed harness must bind one exact state before generation, install
only the admitted stateless extension, notify `generation_returned` only after
the synchronous native call actually returns, then obtain a detached receipt
through `close_state`. This directory intentionally has no runnable Godot
project, auto-registration, loader invocation or launch command. Those later
operations require exact build/project/extension binding, complete diagnostics
and independently reviewed admission; the methods alone grant none of them.

The registry retains the exact state object and refuses reuse or another state
in that process. Unknown callbacks poison the external latch, including before
a session exists. Original nodes are kept only as native integer identities;
replacement handlers use no old pointer or loader map. Every observed old
identity is retired even when its signal is refused. Cleanup skips such
identities, disconnecting only still-valid unretired IDs after caller return.

One root guard subscription is recorded separately from the 18 product
subscriptions. Callback and replacement order may vary. Repeated, missing,
cross-index, cyclic or ambiguous records refuse; the root identity must remain
the same. Final traversal proves membership only, while source identity comes
from the preconversion map and observed edge chain.

Native JSON parsing at the inspected revision represents numeric tokens as
double. The mesh association therefore requires the actual callback JSON value
to be a finite float exactly equal to the locked index, without truncation,
while preserving its native type/value. This does not assert installed behavior.

The snapshot helper bounds recursion depth and visited capture records. It
stops traversal after its first refusal and keeps the partial record. The bound
does **not** limit string bytes, allocation inside native inventory APIs, native
execution time, total process memory or filesystem output. Those remain
unimplemented admission requirements. The snapshot does not read resource
arrays, compare native values or evaluate animation.

## Repeat the CPU checks

From the restored repository, with `PACKAGE` denoting the extracted handoff:

```sh
python3 docs/engineering/second-target-c246/test_inert_model.py
python3 docs/engineering/second-target-c246/verify_bindings.py --package-root "$PACKAGE" --output /tmp/c246-bindings.json
python3 docs/maintenance/reorganization-2026-10-17/verify_reorganization.py
```

The command variable is a local example, not an environment requirement.
Full upstream files retain their notices at the exact handoff paths in
[BINDINGS.json](BINDINGS.json); the inherited nine engine files are reused from
the unchanged C243 inventory. No download or engine run is needed for these checks.

After held-source review and confirmed saved delivery, stop. The
[next separately bounded component](NEXT-TASK.md) remains zero-native work.

The [independent review disposition](REVIEW.md) records the completed review and
its exact limits. Publication remains held source; follow the saved handoff and
[scope #221](https://github.com/Omegapy/OntoKin/issues/221) for actual branch and
delivery identities.
