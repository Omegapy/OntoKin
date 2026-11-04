# C097 · Verifying damaged torque recordings

OntoKin's Agent rejected all 26 configured corruptions of the spin-up and overlapping-torque recordings. Each returned its prescribed reader diagnostic. An independent process recompiled the saved source and reproduced each refusal from the supplied binary file. Each reopened project contained the original valid artifact as its only artifact. The failed delivery also has an evaluated run record.

The [original matrix](../../language-design/torque-v0.1/freeze/hostile-delivery-cases.json) contains 40 cases. C092 observed 14 expected refusals on five scenes. On the other two scenes, the unmodified positive exports expired at their 30-second deadlines before any injection. C097 repeats those 24 spin-up and two overlap cases in a new configured cohort. The authored and host compute allowances are both 300 seconds. The one-million-operation ceiling, three-second scenes, geometry, 4 fps request, tolerances and frozen mutation recipes retain their original values. The authored allowance changes each program revision.

| Producer control | Export time | Operations | GLB size | Poses and intervals checked |
| --- | ---: | ---: | ---: | ---: |
| P01 spin-up | 86.405 s | 894,991 | 6,347,880 bytes | 4,176 poses, 4,168 intervals |
| P04 overlapping torques | 79.921 s | 801,557 | 5,548,476 bytes | 3,616 poses, 3,608 intervals |

Both controls passed numerical readback. Compared with the corresponding C093 CLI exports, all binary geometry and animation bytes matched. The JSON differences are confined to the expected source/program identities and the source spans shifted by one byte. Changing `30` to `300` adds that byte. Each case regenerated its own producer bytes and checked them against its control before substituting the damaged recording. The observed refusals cover certificate fields and coverage, invalid clocks, phase coverage, boundary history, numerical basis, structure and quaternion sign continuity.

The clean P01 GLB has SHA-256 `7bcc6c8e35a294f28bfd738129361808765309932e35dda208fb166fea095501`. The P04 GLB has SHA-256 `ed708ebbf969bd630fc6c37fb441cc848edc462bb1f59c4588f347e91ce019c5`. Execution used CPython 3.12.14 on C096 commit `f2874b0394da214a456017d7d7b4e90797a9c809`. The runtime, tests and tools match tested product `fab1137e7b3e24d656ed4ba7cfd55935b6b2f241`.

## Cost of reading an entire animation one byte at a time

A separate host preflight retrieved the first 512 bytes of the earlier 2,447,148-byte A08 rotor animation through the real Agent. The byte sequence and all 512 logged exchanges matched the reopened database. The measured 6.154 seconds projects to 8.17 hours for the payload and two boundary requests, before offline verification and packaging. Projected database growth is 10.08 GB. The inherited harness allows one hour. The full series is deferred until a dedicated booking can document the proposed 12-hour supervised window and at least 45 GB of working space.

## Handoff

The C097 unified ZIP contains the original C096 ZIP, new source bundles, both clean GLBs, the 26 observed damaged GLBs and closed stores, the 40-row original/configured matrix, independent replay tools and the capacity preflight. The next bounded task is source-physics verification against the frozen seven numerical fixtures, 31 source cases and independent reference. The original fixed-budget failures, full interpreter and release roles, predecessor gaps and external attestations retain their recorded status. [Draft PR 90](https://github.com/Omegapy/OntoKin/pull/90)
