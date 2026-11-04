# C099 first use by three coding agents

Three fresh agent sessions used the public Agent/0.1 CLI on licensed main `c7bb631f96069dd67cc242f6822de7a16623f996` with CPython 3.12.14. Each started from a separate sparse checkout, an empty store, public language/interface references and a written brief. The two edit agents received the original two-rig scene. The third received no example scene. The coordinator froze dimensions, poses, preservation requirements and tolerances before the sessions.

| Brief | Verified result | Checkout setup | First shell command to final GLB bytes | Requests |
| --- | --- | ---: | ---: | ---: |
| A · moving hand and head | Only the moving hand grew to 0.32 × 0.24 × 0.16 m. Its rig's head turned −60° in 1.5 s. Forward travel, hand extension and the reference rig followed the seed. | 8.28 s | 87.237 s | 9 |
| B · stationary hand and moving base | Only the reference hand grew to 0.28 × 0.21 × 0.14 m. The moving base reached world Z = −1.50 m at 2 s and held through 3 s, preserving the head turn and hand extension. | 7.49 s | 88.638 s | 13 |
| C · blank-file sliding carriage | The source defines a fixed base and a carriage constrained by a slider. It travels 1.00 m in 1.25 s at 0.8 m/s and holds at X = +0.50 m for the rest of the 2.5 s recording. | 8.33 s | 98.385 s | 10 |

All 32 requests succeeded on first submission. The accepted source, artifact chunks, digests and request/response pairs reconcile. Both edit agents encountered a public example of a different radius override in the specification. They received zero maintainer hints. The new assembly's motion is driven by the joint's prescribed action.

Independent readback decoded the indexed faces and all world position and quaternion tracks at 91, 181 and 61 stored times per body respectively. Every interval midpoint and action boundary passed. The maximum position-component error across the three recordings was below 0.00000017 m. Each edited source changed only the two requested spans. Deliberate faults in a vertex, a translation and a rotation triggered the independent check.

The bundled Three.js loader and mixer separately checked playback at 687 sample times across the three files in Node.js. The user handoff includes all three editable sources, recordings, preview GIFs, raw exchanges and replay tools. This is a three-brief pilot with one agent environment. Setup used local Git objects and the agent timer stops at receipt of the downloaded bytes.

The independent newcomer trial is open. Use the [original README under test](https://github.com/Omegapy/OntoKin/blob/f2b0eac9eeef8143c5a4377c45776bf038907ccd/README.md) in a clean checkout and record time to first correct browser playback, any help and the first point of confusion. The target is 15 minutes. A passing human observation advances the milestone to the keyed assembly trial. [Trial protocol](../../../examples/agent/first-use.md)

Scope owner `interactive-c099-first-use-20261104` closes this evidence increment on the existing first-use branch. The product runtime and torque acceptance retain their own pins.
