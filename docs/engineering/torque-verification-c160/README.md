# C160 | Testing the simulator’s class-attribute guard

Keep the reference membership call in the generated descriptor predicate. The CPython 3.12.14 simulator observed a different exception and work charge when a native membership operator replaced that call. Checking for active monitoring introduced a second observable call. Both differences occurred in a real simulator tick with the original poll and a counted clock. The comparison installed each experimental predicate in a disposable Python process. [Executable tick controls](public_tick.py) · [15 observed outcomes](public_tick.json)

## What a caller can observe

The generated function first checks 151 class attributes that must remain absent, then 84 entries that must retain their original identities. On the real class namespaces, both versions visited all 235 rows on success, stopped at rows 1, 76, 151 or 192 under the selected changes, and retained the subclass lookup route. A substituted accessor raised the original exception in untouched closure state. Replacing the candidate’s added closure cell and supplying that same callable allowed the candidate to skip it. [Mutation and authority controls](guard_controls.py) · [Outcomes](guard_controls.json)

| Condition in the original request poll | Reference tick | Experimental tick |
|---|---|---|
| Local monitoring raises on a call to the native membership accessor | Raised the observer’s exact exception before a clock read or debit | Accessor-identity variant missed the event, read the clock and charged one operation |
| Local monitoring distinguishes the first call in the predicate | First call was the native membership accessor | Entry-guard variant called its eligibility helper first and raised a different exception |
| A Python audit hook raises on the entry guard’s request for the executing frame | Completed, read the clock and charged one | Entry-guard variant raised the audit hook’s exact exception before the clock or debit |

All 15 runs polled once. Clean ticks charged one, and cancellations from the poll charged zero. The accepted state, event index, source object and proof receipts passed their identity checks. An additional CPython-only stress test installed local monitoring during a dictionary lookup and showed why a decision made at entry can go stale. It used raw class-dictionary access in a disposable process. The three public observer controls above require no such mutation. [Late-monitoring probe](observer_boundary.py) · [Outcomes](observer_boundary.json)

## Original A08 recording

The measured checkout was C159 at `1b723b25ce1ab9adf75f2128e9747601dcdc4ac7`. In the isolated timing experiment, the median fell from 9.46 to 5.39 microseconds for the bare expression on intact descriptors. The eligibility failures ended the candidate before a timed Agent comparison. The following measurements used the reference implementation. [Receipts and numeric fingerprints](measurements.json)

| Fresh test | Observed result |
|---|---|
| Original 30-second Agent export | Timed out during recording export/readback at 30.001 s after 418,895 operations. No artifact was published and no read method started. |
| Separately configured 80-second Agent export | Published at 35.588 s after 452,627 operations. All 13 reads passed. |
| Direct original export | Reproduced the 2,447,148-byte historical GLB, SHA-256 `6911a4921133841df9b12e308c59b89b9ef4b5219f604751c6de2861410564aa`. The producer recorded 6.903 s and 448,334 operations. |
| Independent source-aware reader and Chromium | Verified 1,504 poses and 1,496 continuous interval certificates. Chromium sampled eight carriers at 0, 1 and 2 s. Khronos validation returned zero errors and warnings. |

VTK 9.3.1 imported the native clip and updated 14 primitive actors belonging to six mesh-bearing nodes. At 0, 1 and 2 s, the largest absolute difference across their world-matrix components versus the controlled Chromium playback was 0, 2.39 × 10⁻⁷ (rounded up) and 3.90 × 10⁻⁸ (rounded up). The first sample identified the actors. VTK exposed no actors for the two meshless nodes. These results cover three native samples. Controlled interpolation between samples, game-engine playback and independent human review remain open. [VTK probe](vtk_playback.py) · [Per-object matrices](vtk-playback.json)

Thirty stock torque-guard tests and three Agent cancellation/rollback tests passed. All four numerical fingerprint groups matched and the prior scan controls replayed. The last full regression was C157, with 33 of 34 roles passing. Its original A08 setup timed out after the same first 3,971 methods. C160 closes the two candidate designs before a new full driver run. The frozen fresh and in-suite release gate and the full one-byte transfer remain open. [Earlier full run](../torque-verification-c157/README.md)

## Next authoring increment

Use the existing framed-loft language to join a straight duct to a hollow elbow. The pilot already creates, exports and retrieves a 48-triangle elbow through Agent/0.11. Direct and Agent exports produced the same 30,712 bytes. Both open ends have eight wall triangles, 3 m² of wall and an uncovered center. The next step is to verify the entire shared opening between *two* parts and exercise a misaligned joint and its repair. [Editable source](duct/duct.ok) · [Direct mesh measurements](duct/measurements.json) · [Agent replay](duct/agent_smoke.py) · [Agent results](duct/agent-smoke.json)
