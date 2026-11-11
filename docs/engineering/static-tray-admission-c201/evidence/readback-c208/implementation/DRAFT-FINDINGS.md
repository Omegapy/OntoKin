# C208 original draft results

The first focused run executed 51 methods: 49 passed and two produced errors.
Both changed-accepted-file controls reached the unchanged sealed-candidate verifier,
which correctly rejected changed GLB/audit bytes with its historical Stop type.
The new public readback boundary did not yet normalize that inherited exception
into ReadbackError. The component now preserves its state while normalizing it.
Neither failure changed an accepted pointer or granted readback authority.

The exact first-run implementation and tests are under draft/ with their SHA-256
bindings, and draft-tests.log retains the original complete result. The draft
result was not relabeled as a pass.

Independent draft review additionally identified a timing gap: a successful
29-second process record could fit the 30-second outer cap while exceeding the
28-second child-work allowance. The result checker now conservatively requires
its full successful supervisor duration to fit within 28 seconds and retains the
qualified success cleanup convention (zero termination-cleanup time). The new
focused control constructs a coherently rebound 29-second receipt and requires
rejection. Actual process deadlines/provenance remain unimplemented wrapper gates.

The component job/0.1 binds observations but is explicitly not yet an executable
probe contract: future versioned package entry-point resolution remains pending.
