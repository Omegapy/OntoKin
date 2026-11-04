# C102 · Neutral torque at the original export limit

Six frozen source programs cover cancellation, zero torque, torque combined with a center-of-mass force, and numerical underflow. Their canonical angular acceleration is zero. The question is whether OntoKin 0.22 preserves the physical behavior and exported scene of the paired 0.21 programs.

| Frozen pair | Original .22 export, 100,000 operations | Separate .22 export, 1,000,000 operations |
| --- | --- | --- |
| p05 · simultaneous cancellation | Refused at 100,001 | Exact geometry and appearance |
| p06 · zero torque | Refused at 100,001 | Exact geometry and appearance |
| p16 · center-of-mass force | Refused at 100,001 | Exact geometry and appearance |
| p23 · extreme terms cancel | Passed at 33,493 | Exact geometry and appearance |
| p24 · rounded acceleration is zero | Passed at 32,702 | Exact geometry and appearance |
| p30 · torque replaced at the boundary | Passed at 40,587 | Exact geometry and appearance |

The three original-budget recordings matched the earlier geometry, index, UV, material and texture streams. Each passed 32 independent interval-certificate checks. The other three original exports produced no GLB. Each higher-budget source added an execution declaration, which changed its program revision. All six higher-budget recordings passed their own comparisons. [Measured case bindings](neutral.json)

The source-event audit reconstructed the two sides of all 48 sample observations. All 38 full torque projections specified by C090 matched, including the persistent axis and reference-error quantities. The independent source-and-byte reader checked 1,656 interval certificates in six .21 controls, 96 in the three original .22 deliveries and 1,672 in the six higher-budget .22 deliveries. It rejected three altered p30 files after the event order, source byte span or a positive interval bound was changed. [Corruption tests](mutations.json)

## Where the two-second radius edit spent its time

The ordinary rerun and a separately instrumented run used the same 2,000,000-operation and 240-second authority as C101. Both reproduced its 7,924,988-byte GLB and 1,437,266 operations. On the instrumented run, pose sampling took 68.824 seconds. The source consistency checks within it took 20.090 seconds across 501,639 calls. Those times overlap. The 561,037 observed operand widths had median 92 bits and maximum 4,777 bits. A faster consistency check could reduce elapsed time. It would leave the 437,266-operation gap to the lower ceiling. [Profile and artifact identities](radius.json)

The three prior coding-agent trials have their own results. An independent human must still run the first-use README and return their fresh animation and observed playback time. The complete handoff includes the facilitator's transfer-folder setup and the frozen next keyed-rack exercise. Product integration, release acceptance and external engine playback retain their separate gates.

Scope `interactive-c102-compatibility-20261104` covers this evidence directory on the existing torque draft branch, starting at `cc7866733a71bb31bf61601c8f6b5d8fe7a0ab67`. This checkpoint closes that documentation scope.
