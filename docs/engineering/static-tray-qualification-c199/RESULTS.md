# C199 result: implemented, native qualification stopped

The finite static-tray prototype is implemented. **It is not qualified, and no
tray is admitted.** The one approved qualification execution stopped at N01,
the first OntoKin baseline, when the pinned Blender glTF exporter failed. No
retry or later native slot was started.

## Actual execution

| Observation | Result |
| --- | --- |
| Construction starts | 1: N01 / Q01 / OntoKin baseline |
| N01 outcome | Rejected; exporter raised `KeyError: 'loglevel'` |
| Native process | Exit 1 after approximately 1.033 seconds |
| N01 transaction | Approximately 12.365 seconds, including input verification |
| Complete coordinator | Exit 1 after approximately 24.477 seconds |
| Partial native scene | `scene.blend`, 547,575 bytes; retained as diagnostic evidence |
| Delivered raw/final GLBs | 0 |
| Accepted transactions | 0; accepted pointer remains absent |
| Receiving Blender processes / review images | 0 / 0 |
| Checks of actual deliveries in Khronos / Three.js | 0 |
| Actual delivered corruption controls | 0 |
| Unstarted construction slots | N02–N12; eleven slots |
| Native simulations / timed authors / retries | 0 / 0 / 0 |

The process supervisor retained both logs, reaped the child, verified that its
process group was absent and closed the output handles. A saved native scene
alone does not establish correct geometry. There is no native-result receipt,
GLB, independent geometry acceptance, receiving measurement or image from this
attempt. Paired-route equality, clean regeneration, native boundaries, rotated
composition and native scoped-edit/reuse checks remain unexecuted.

The executed implementation is
`498b161f2cf166c67c2d381029f109e03f06ce7c`, tree
`b9ecb3582b0d3fa6f529ec23f0ab2dd5082ded71`. The
[executable input lock](EXECUTABLE-INPUTS.json) has SHA-256
`bbebf20c05e98a4fa34832fe9cf33b225e9a1251a49d5f22aa05365a69fb0cc3`.
Its [independent approval](EXECUTABLE-INPUTS.approval.json), SHA-256
`eab9aa6edf5fe4b50a4340d8ad6b67b5283d4ae7f220f89038e0e98944a760cf`,
predates the native start. The actual coordinator receipt records its real
`qualify` command and environment; each slot's `command` field describes the
equivalent standalone CLI, not an additional host process that was launched.

## Concrete exporter incompatibilities

Read-only inspection of the unchanged pinned exporter explains the fatal path.
The frozen operator map sets `export_loglevel` to 20. The exporter copies this
to `gltf_loglevel`, but initializes the separate `loglevel` entry only when the
value is negative. It later reads `loglevel` unconditionally. The positive value
therefore reaches the observed missing-key failure.

The stderr log also records an earlier action-filter callback error. Explicitly
assigning `export_action_filter = False` invokes a callback which clears
`Scene.gltf_action_filter`; that property has not been created in this factory
background context. The callback error is distinct from the fatal logging error.

Both issues concern how the complete property inventory is applied to the pinned
operator. Static property name, type, range and enum checks had passed. Those
checks did not establish that every admitted property value and callback was
safe in the actual background execution path. The native failure remains the
authoritative result. No setting or callback policy was changed afterward.

## Preparation that passed

The final integrated CPU cohort passed **92 methods** in 53.833 seconds:

| Finite preparation area | Passing methods |
| --- | ---: |
| Source, canonical record and bounded Python source controls | 31 |
| Independent GLB reader, layout, metadata and CLI controls | 22 |
| Receiving measurement comparison using synthetic observations | 11 |
| Transaction, finalization and readback coordinator controls | 28 |

The preceding combined attempt remains a failed run: 78 methods passed and the
receiving test module failed to import. The new test's import was corrected;
its separate eleven-method run passed, followed by the complete 92-method run.
[Integrated evidence](evidence/integrated-cpu/README.md) retains both outcomes
and the captured inputs rather than replacing the failure.

The separately reviewed L-R1 lifecycle cohort passed all eight cases and 131
independent result checks. It consumed eight direct controlled starts and one
grandchild. Including the earlier preparation cohort, historical totals are
sixteen direct starts and two grandchildren. These controls exercise supervision
and atomicity; they do not establish observed Blender cancellation behavior.

Three synthetic Node controls passed the pinned Khronos and Three.js probes.
They are preparation evidence, not checks of a native C199 delivery. The exact
supplemental versions and limits remain in
[EXTERNAL-READBACK.md](EXTERNAL-READBACK.md) and [EXTERNAL-INPUTS.json](EXTERNAL-INPUTS.json).

The unchanged compiler checks passed 57 methods, and the original core conformance
passed 43 cases with 694 assertions. These focused checks do not replace the
inherited failed full regression. That result remains **4,239 distinct passing
methods and thirteen torque-read methods NOT RUN** after the unchanged 30,000 ms
setup failure.

## Disposition

This is eligible for review as an explicitly selected experimental implementation
and an honest failed qualification record under OK-ENG-009. Integration does not
make the profile qualified. Existing runtime defaults, shared compiler bytes,
historical tests, contracts, numerical gates and hosted workflows remain unchanged.

[C200](NEXT-TASK.md) is the next bounded task: repair the two observed pinned-exporter
compatibilities, freeze the exact revised invocation policy and inputs, and obtain
independent approval for a separately identified qualification protocol. The
stopped C199 cohort must not be retried or silently resumed.

## Verified development integration

[PR #135](https://github.com/Omegapy/OntoKin/pull/135) merged the explicit incomplete
increment at `83ff4a5533bbeea3c607a90734d3d8586671de6c`. Its tree
`f25b1eaa0a3d4d87302582d06f9b1da6c563e4d5` equals the reviewed local and published
candidate trees exactly. Resulting-main checks passed 62 focused methods, full
approved input/dependency verification and the documentation checker (29 preserved
sources, no failures). Independent actual-main review passed 16 checks.

The [integration receipt](evidence/repository/INTEGRATION.json) preserves the
separate identities and actual commands. These reruns do not add unique coverage
to the earlier methods or change native qualification. The guarded closing record
adds evidence and documentation only; its resulting identity and lease-release
readback are retained in the handoff controls.
