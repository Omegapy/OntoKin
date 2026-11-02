# C090 supplemental language construction preflight

All four final `.21` construction controls pass. The first four-case attempt remains **failed**, with its exact earlier input revision and inherited diagnostics preserved. The second attempt runs only the two repaired articulated controls. This evidence is construction-only: no evaluation, GLB, `.22` torque source or full inherited suite ran.

| Final control | Successful attempt | Objects | Host operation/time ceilings |
| --- | --- | ---: | --- |
| l01 pure import and contextual names | 01 | 8 | 100,000 / 30,000 ms |
| l02 nonidentity fixed local rotation | 01 | 9 | 100,000 / 30,000 ms |
| n31 static articulated marker | 02 | 9 | 1,000,000 / 30,000 ms |
| n32 moving articulated marker | 02 | 9 | 1,000,000 / 30,000 ms |

The initial n31/n32 controls failed at inherited `OKL-E-MOTION-MODE`, elaboration, entry bytes 1014–1208: “Core joints require a static/prescribed parent and a prescribed child.” The author changed only those source/control hinge parents to the existing prescribed massless fixed follower `ball.arm.origin`. Their dependency path still descends from the torque carrier. The corrected sources construct successfully. Their declared one-million-operation source request and matching host policy were already present in attempt 01 and did not change to hide the refusal.

Each attempt freezes exact source/file manifests, module/PNG bytes, modes, complete bundle identities, budgets, source inventory, interpreter/platform, command, stdout/stderr and actual result. Every successful final closure matches the current independent corpus. Full 10,792-file C088 before/after byte and mode inventories are identical, including after the repaired attempt. The original frozen `c090-preflight` directory was not written; its closure identity remains unchanged.

`CLOSURE.json` binds the final four controls and both original result files. Include every regular file here except top-level `tmp/` when packaging. Keep both attempts and their original statuses. This supplemental directory is frozen after closure.
