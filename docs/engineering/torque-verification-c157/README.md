# A08 torque export timing and visual verification

The original Agent request did not reliably export the two-second A08 animation within its 30-second deadline on the measured Linux VM. The same source and export options produced the expected animation through the direct Python exporter in 6.030 seconds. The two entry points perform different work. The Agent also admits the request, checks its live execution context, and publishes through a persistent store.

**Tested revision.** [C156 main](https://github.com/Omegapy/OntoKin/commit/21588acad94e1c222b45ed26880ebf0832f8999a), tree `b3fa711f6409355473128c7f846d6be082f42250`. Linux x86-64, AMD EPYC 9V74, CPython 3.12.14. The VM had nine visible CPUs and an eight-CPU quota. The principal comparison pinned processes to logical CPU 4. Exclusive access to the underlying physical host was unverified. The ZIP includes allocation and load records, original producer receipts, unit logs, validator results and rendered frames. [Measured results](measurements.json)

## Original request

The original source and host grant allow 30,000 ms and 1,000,000 operations. Two fresh interpreter runs on CPU 4 timed out in the `recording_export_readback` stage at 348,405 and 410,225 operations. The stock driver then exercised the same 3,971 preceding methods in C156 order on CPU 4. The warmed A08 class hit its deadline at 30.001 s in `recording_export_readback` after 282,401 operations. Setup failed before any read method ran.

Two additional fresh processes ran after the full driver finished. Each used a new local SQLite store. The table reports the elapsed time recorded by the producer itself.

| Attempt | Producer seconds | Charged operations | Read methods entered | Export |
| --- | ---: | ---: | ---: | --- |
| quiet-01 | 30.001 | 381,313 | 0 | failed |
| quiet-02 | 30.001 | 414,471 | 0 | failed |

On logical CPU 6, the stock fresh process, its same-interpreter repeat, two runs with postponed cyclic garbage collection and two memory-backed SQLite runs all exceeded the original deadline in the `recording_export_readback` stage. C156 recorded an original standalone pass and three standalone timeouts. The available observations do not isolate a cause for the prior pass.

## Artifact and destination

The direct exporter charged 448,334 operations and produced 2,447,148 bytes, SHA-256 `6911a4921133841df9b12e308c59b89b9ef4b5219f604751c6de2861410564aa`. The independent source-aware reader checked 188 sample points and 1,496 interval certificates against the frozen inputs. The Khronos validator reported zero errors and zero warnings. Three.js loaded the GLB in Chromium 141.0.7390.37. It sampled all eight carriers at five times and rendered front, oblique and back views. Independent human playback and release-wide external checks remain open.

## Clock experiment

One candidate replaced a generator used to check three class fields in the native Agent clock with ordered membership checks. The candidate kept the fallback for shadowed operations and passed all 20 callback-admission tests. On CPU 5, the corrected alternating 80-second control produced stock times of 37.376 and 31.833 seconds and candidate times of 39.482 and 33.294 seconds. Each run charged 452,627 operations, produced the identical configured GLB and passed all 13 configured reads. Both implementations missed both of their original 30-second attempts. The observed means were 34.604 seconds for stock and 36.388 seconds for the candidate. The runtime stays at C156.

## Full local driver

The stock local driver passed 33 of 34 roles. The unit run executed 4,150 methods. 3,988 of the 3,988 identified pre-torque methods passed. Roles without a passing result were **unit-tests**. The driver checked Python conformance, the force-Agent workflow and the example build, format and browser roles using the pinned tools. The hashes of 52 of 52 rebuilt example GLBs matched the C156 record. The full driver exit was 1. Its source inventory matched before and after. The per-role verdicts, including any skipped or blocked roles, are in [the measurements](measurements.json).

## Next experiment

One separate configured export was sampled during the producer call. Of 1,251 CPU samples, 389 stopped in generated authority predicates and 289 in the source-identity watch. The point-entry and simulator binding catalogues have 30 checks in common by mapping owner, key and expected identity. First prove whether any can be reused without crossing a callback or changing refusal order. The entire second binding predicate accounted for 70 samples (5.6%). A source-side identity change requires the successor-identity procedure and a fresh artifact comparison. [Previous measurements and numerical identity](../torque-verification-c104/README.md)
