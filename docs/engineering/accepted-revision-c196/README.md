# C196: promote and reuse the accepted repair

**The accepted-store transition passed.** OntoKin advanced the copied accepted
375 mm design to C195's already qualified 365 mm repair, rejected a request
based on the former revision, and regenerated the repaired design from the
saved accepted source. The independent result review passed **958 checks**.
[Measured result](results.json) · [Independent review](evidence/FINAL-RESULT-REVIEW.json)

## What changed in the store

H identifies the preserved 375 mm source, revision `2143515f…`. G identifies
the already accepted 365 mm repair, revision `ba105a8c…`. Their complete hashes
and exact input bytes are fixed by [INPUTS.json](INPUTS.json). No new design
was authored for this continuation.

| Operation | Observed result |
| --- | --- |
| Promote G with expected revision H | One real native construction succeeded and committed G in a new artifact directory. The state pointer names G and matches the retained source, canonical input and manifest hashes. |
| Preserve the former accepted design | All 36 preexisting store files other than the deliberately replaced state file retained their bytes, sizes and modes. The old H source, output closure and C195 ownership-rejection receipt remain intact. |
| Submit valid H with expected revision H against the now-G store | `C193_E_STALE_REVISION` rejected the stale request in the publish phase, with the exact source span. Both revision fields remained G. Only the failed-attempt receipt was added; all native work and output counters were zero. |
| Regenerate through accepted-state readback | The runner resolved `state.json`, read its retained G source and built those readback bytes once in a fresh store. The promoted store remained unchanged. |

[Promotion inventories](evidence/PROMOTION-INVENTORY.json),
[stale-rejection inventories](evidence/STALE-INVENTORY.json) and
[readback provenance](evidence/READBACK.json) retain the exact transition.
The original state bytes are also preserved in the recorded archive. The
unchanged sole publication commit point remains the state-file replacement;
C196 adds no new crash or concurrent-writer experiment.

## Delivered output and execution accounting

Both constructions passed the unchanged independent numerical and provenance
readers. Their canonical input, all native samples, raw GLB and final GLB are
byte-identical to one another and C195's accepted G artifacts. The continuous
mapping bound is **0.074516468 mm**, below the unchanged **0.2 mm** limit.
Unrelated parts retain the accepted geometry and native motion.

Exactly **two constructions and two independent saved-scene replays** ran.
Each new scene reproduced all **481 sample records** after cache clearing,
with unchanged configuration and no reconstruction. The scene files have
different hashes, so each has its own new replay receipt. There were no new
authors or retries. Each construction used the original 1,000,000-operation,
80,000 ms ceilings and a 100-second outer watchdog. Both consumed 450,690
operations and completed successfully. All recorded process-cleanup checks
found no remaining owned descendants. [Complete execution](evidence/RESULTS.json)

**Receiving and visual evidence is inherited.** The exact raw/final GLB hashes
match C195's `ok-repaired` outputs. The reuse maps bind those bytes to the
original Khronos, Three.js, Blender-import and three reviewed-image receipts,
as well as the unchanged checker, dependency and profile identities. No new
receiving execution or visual review is claimed.
[Promotion map](evidence/promotion-receiving-reuse.json) ·
[Regeneration map](evidence/regeneration-receiving-reuse.json)

## Source and reproducibility

The actual construction source was
`53ef0584cb07c9c5d7ce03d1a0b97378f9b4b482`, on Linux x86-64 with CPython
3.12.14 and the pinned Blender 4.5.3 executable. Each delivered artifact retains
all eleven executed prototype modules and records clean status for that
prototype directory. The whole checkout is **not** described as clean during
execution: its new exclusive execution ledger was created before construction.
The 675 frozen input identities and retained module bytes establish the actual
implementation independently of that generated evidence.
[Source provenance](evidence/SOURCE-PROVENANCE.json)

The [sealed archive descriptor](evidence/RECORDED-EVIDENCE.json) identifies
911 files, including the original receipts, prior and new states, editable
scenes, source files, recorded outputs and execution ledger. A separate
extraction restored every declared byte and mode and passed the
[recorded-only audit](evidence/RECORDED-AUDIT.json). This audit performed no
native construction, scene resimulation or receiving job.
[Replay receipt](evidence/RECORDED-REPLAY.json). The separate
[archive review](evidence/ARCHIVE-REVIEW.json) passed 3,654 checks, including
all 911 original archive members and all 911 restored file identities and modes.

The [protocol](PROTOCOL.md), [preparation](PREPARATION.json),
[execution plan](EXECUTION-PLAN.json) and [handoff tools](handoff_tools/README.md)
explain the execution boundary and portable recovery. Completed native work
must not be repeated to recover an interrupted conversation.

## Limits retained

This result qualifies the observed accepted-revision promotion, real stale
revision rejection and accepted-source regeneration. It does not establish
general contact, a production backend, live destination physics, comparative
authoring advantage or full-product acceptance.

The inherited regression driver and supplemental tail remain **FAILED**:
**4,239 distinct passing methods and thirteen torque artifact-read methods
NOT RUN** after the unchanged 30,000 ms setup failure. C196 changed no prior
runtime, tests, solver, contract or acceptance limit. Broader project gates
remain open.
