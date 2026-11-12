# One next task: characterize the upstream normal codec on the CPU

First reconcile live main, the integration lease, [issue #154](https://github.com/Omegapy/OntoKin/issues/154), held [PR #155](https://github.com/Omegapy/OntoKin/pull/155), and the saved C212 handoff. Read [the C212 decision](DECISION.md). The original strict contract still fails; no replacement tolerance is approved.

## Selected implementation scope

Build one isolated, offline characterization harness for the Blender `v4.3.2` normal encoder/decoder at pinned upstream commit `32f5fdce0a0a571a39198edf8d7b5d719bf59f2c`. Give it explicit valid normal-fan basis vectors and angular ranges. Implement and compare the complete selected codec path, including normalization, approximate inverse cosine, short rounding, near-auto and azimuth-zero shortcuts, and invalid-frame behavior. Keep approximate-versus-exact mathematical reference calculations distinct. Record floating-point precision and any difference from native float32 evaluation.

Predeclare independent positive, boundary and negative inputs before running the harness: cardinal and oblique directions; short-rounding midpoints on both signs; cases around the `1e-4` near-auto comparison and `0.9999` azimuth threshold; invalid/degenerate frames; nonfinite and zero vectors; and distinct corner normals across a sharp boundary. A finite analytical counterexample to `2e-6`, conditional on explicit valid frame inputs, is useful evidence; it is not proof of the exact C211 native fan state.

Keep the existing C211 mesh observations as a separate diagnostic corpus. They do not contain the native fan frames or encoded short pairs. Do not fabricate those values or claim a native replay from an assumed frame. The executable/source provenance limitation stays open unless independently resolved by actual evidence.

## Completion condition and stopping point

Deliver reproducible code, source/input bindings, independently reviewed boundary results, and either a defensible conditional error characterization or a precise reason it cannot be established within this scope. State whether the result can support a separately reviewed finite approximation policy or whether a source-preserving alternative needs selection. Do not adopt an arbitrary new budget or repeat C212's already completed measurement as the whole task.

No Blender process, import, render, native save/reopen, second destination, model training, new language syntax, general importer, or C201 admission belongs to this CPU task. It does not alter the held receiver branch. Save a new recovery checkpoint before substantial work and finish with one verified saved handoff, then stop.
