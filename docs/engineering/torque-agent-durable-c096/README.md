# C096 · Torque Agent workflows and durable artifact reads

C096 verifies the two-rotor physics export and how an Agent retrieves and reuses it from a saved project. The source models two seconds of motion. It requests 80 seconds of host computation and one million operations. The program finished in **35.046 seconds** using **452,627 operations** on CPython 3.12.14. The resulting 2,447,148-byte GLB matches the C095 artifact byte for byte.

The tested checkout was `7aed65b6b3ffcc12c7237e60a7b8574f1841521a`. Its product, tests and tools match the C093 product commit `fab1137e7b3e24d656ed4ba7cfd55935b6b2f241`. The configured source revision is `sha256:f9706bb36e9be09721c3c14c9e60eb7d66115f9887ac6a24abf8c156c9348336`. In a separate process, the reader compared the delivered bytes against the recompiled source at 1,504 node poses and over 1,496 intervals. Its maximum position and rotation error bounds were 0.448 mm and 0.000259 rad.

The original C093 production case had a different source revision and a fixed 30-second execution ceiling. It failed during export readback after 310,430 operations and committed no artifact. C096's original, unmodified A10 workflow also stopped at its embedded 30-second export. Its separately configured A10 ran all 139 checks across 15 exchanges, including a final response-size refusal after an actual artifact had been staged. The previously accepted data survived that refusal.

## Agent checks

The original A04 case passed its cursor, reopen and stale-revision checks. All 12 malformed wire requests and 18 source refusals returned their expected results. The full and dispatched schema validators agreed on all 3,002 checks drawn from the 12 public operations. Of 52 frozen mutations of actual state responses, 40 failed structural validation. Independent source, time and numerical checks caught all 12 that remained structurally valid.

The 13 artifact-read methods ran on the configured fixture on CPython 3.11.17, 3.12.14 and 3.13.16. They cover byte integrity, access after reopen, cancellation, concurrency and rollback. The configured fixture extends one synthetic clock jump from 31 to 81 seconds to cross the new deadline. The original 30-second test setup retains its own result.

## Retrieval to the end of the artifact

An Agent retrieved the entire 2,447,148-byte GLB in **143,950 consecutive 17-byte chunks** from one durable store. The last chunk contained 15 bytes. A separate exact-end request returned empty data, and one byte past the end was refused. All 143,952 requests and their responses passed protocol-schema validation. Reassembly reproduced SHA-256 `b6e235d31b6482878695a166fe12ebf3ed284ccc95addf55537dacc80ebc424c`.

The capture spans two processes. The first saved 81,408 live responses. The same store held 83 additional completed requests and one queued request. After reopening, the Agent returned the same 83 saved responses, completed the queued request under its original ID and continued in order. The handoff preserves the interruption boundary, the captured exchange sequence and the closed database.

The same configured artifact passed complete retrieval in 38 chunks of up to 65,536 bytes. The 89-byte source PNG passed complete reads at both one and 17 bytes. The one-byte GLB pilot checked 128 contiguous bytes plus the final byte and both EOF boundaries. Its full 2,447,148-read sequence remains open.

## Remaining work

The pilot projects roughly 5.8 hours for the full one-byte GLB series on this host, compared with the inherited one-hour test window. Start the next bounded checkpoint with the hostile-artifact controls that previously timed out before their mutations could run. Keep original and configured outcomes separately identifiable.

The C096 handoff contains the inputs, test fixtures, receipts, actual stores, reconstructable transcript and original C095 ZIP. C093's 67 CLI and 36 native cases retain their earlier measured status. Full torque acceptance and main integration remain open.
