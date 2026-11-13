# C226: aggregate reached a concrete setup blocker

One immutable default regression attempt finished all seven driver commands. Of 4,662 discovered methods, **4,649 passed and thirteen did not run** because `TorqueArtifactReadTests.setUpClass` failed its frozen A08 export. That separate setup error leaves the aggregate **failed** and **R02 blocked**. The six other driver commands passed at their recorded scopes; sixteen external conformance cases remain pending.

The tested source is `3f17a523b5d5c435f71525a499d2f071ca6e4e96`, tree `324d7a23d67d0c23f5dfba968a63a5c12cb7bcff`, on Linux x86-64 / CPython 3.12.14. Source bytes and Git identity remained unchanged. This directory publishes documentation and evidence; it changes no product implementation, test, fixture, workflow or budget.

Read the [preparation](PREPARATION.md), [results](RESULTS.md), [independent outcome review](REVIEW.md), and [exact next bounded diagnosis](NEXT-TASK.md). The [raw evidence map](evidence/RAW-EVIDENCE.json) binds the full logs, inventories, process receipts and readback artifacts in the restorable C226 handoff. [Scope #184](https://github.com/Omegapy/OntoKin/issues/184) records integration and final delivery separately.

C224's original timeout, C225's focused preparation result, all [nine recommendations and 41 criteria](../review-integration-c221/RECOMMENDATIONS.json), the strict Blender-normal failure and pending Godot work retain their meanings. C226 stops after verified saved delivery; it performs no repair or retry.

[PR #185](https://github.com/Omegapy/OntoKin/pull/185) publishes this documentation/evidence increment. The [checked merge receipt](evidence/INTEGRATION.json) records its exact tree and actual-main documentation result. The final handoff and scope #184 record subsequent closure and confirmed delivery.
