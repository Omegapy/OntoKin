# C101 · Two-second torque recordings

The C096 producer delivered the two-second torque-magnitude edit within its original configured 80-second / 1,000,000-operation allowance on a fresh run. It finished in 76.435 s and 827,077 operations. The 4,527,272-byte recording preserved the complete geometry and appearance streams for all eight occurrences. The corresponding C100 attempts reached the elapsed-time limit on their host. [C100 repair matrix](https://github.com/Omegapy/OntoKin/blob/b39036d1ce2185fe7f5378ec47626ce2cb7e2f22/docs/engineering/torque-agent-repairs-c100/README.md)

The unchanged radius edit reached the original deadline after 661,807 operations and published no file. In a separate timed run it spent 62.062 s sampling the node poses and 14.170 s certifying the intervals between poses. The deadline interrupted certification. The public validation function and independent supplied-byte checker each received zero calls. A second timer measured 57.218 s and 18.867 s in the same two stages. Measurement itself affects elapsed time.

## Explicit higher-budget workload

Three fresh stores used source and host ceilings of 2,000,000 operations and 240 s. The producer, duration of two simulated seconds, frame rate of 4 fps, scene source apart from its budget and selected edit, recording tolerances and public destination all matched the C096 workload. These are new program revisions. Processes ran on separate logical CPUs on the same Linux x86-64 host with CPython 3.12.14.

| Program | Elapsed s | Operations | Actual GLB bytes | Selected sphere rotation at 2 s |
|---|---:|---:|---:|---:|
| Base | 43.940 | 452,627 | 2,447,148 | 2 rad |
| Double torque | 77.691 | 827,077 | 4,527,272 | 4 rad |
| Half radius | 131.035 | 1,437,266 | 7,924,988 | 8 rad |

The second sphere reached −1 rad in each recording. All 482 selected vertex positions matched the half-radius sphere, and the unchanged geometry, markers, materials and image passed exact comparison. Decoding every stored rotation key on both spheres gave a maximum absolute angle error below 0.00000042 rad against the constant-torque solution. These key checks supplement the recording proof. [Capacity comparisons](capacity.json) · [Stored rotation keys](angles.json) · [Original-budget geometry comparison](controls.json)

## Independent compatibility work

Direct comparison of the C096 producer's fresh version 0.21 GLBs with the untouched C088 archive reproduced all 27 available files byte for byte. The other four controls reproduced their complete refusal diagnostics. P03, P19 and P20 exhausted 100,000 operations. P28 refused independent spin-norm validation. The broader C1 preflight inventory retains its own acceptance conditions. [Original 31 controls](legacy.json)

For the six frozen neutral-torque cases, the observed physical states, both carriers' kinematic anchors and inherited translation error records agreed at all 48 original clock/side pairs against the .21 controls. P24 and P30 retained the exact nonzero angular shadow error for a torque whose canonical acceleration rounds to zero. The remaining delivered-stream, certificate and event-provenance obligations require their own bindings. [Neutral physics](neutral.json)

The first-use milestone has three passed coding-agent trials and still needs one independent newcomer to play a freshly produced GLB within 15 minutes of opening the pinned README. The C101 handoff contains the facilitator packet, source-bound experiments and full GLBs. Owner `interactive-c101-torque-recording-20261104` closes this documentation scope on draft PR 90. The separate development prototype stays in the handoff. Licensed-main reconciliation and the release gates remain open.
