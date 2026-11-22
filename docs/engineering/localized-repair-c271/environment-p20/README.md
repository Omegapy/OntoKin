# C271 P20: isolated verification environment

P19 found a dependency mismatch in the shared runtime. P20 prepared a separate environment using the same canonical Python executable and the unchanged seven-package lock. The shared runtime remains unchanged.

The single reviewed attempt completed wheel acquisition, empty-environment creation and offline installation. All seven pins matched, including `rpds-py==2026.5.1`. Static checks verified 293 installed files and 463 original input descriptors. Independent outcome review accepted 15 groups. These are preparation and identity checks; no OntoKin product or full-routine test result follows.

- [Phase and acceptance boundary](PHASE.json)
- [Observed outcome and remaining gates](OUTCOME.json)
- [Exact approved preparation plan](preparation/PREPARATION-PLAN.json)
- [Actual result](preparation/RESULT.json)
- [Independent pre-execution review](reviews/PREPARATION-REVIEW.json)
- [Independent outcome review](reviews/OUTCOME-REVIEW.md)
- [Confirmed early recovery](EARLY-RECOVERY-RECEIPT.json)

Scripts and absolute paths here preserve the actual session evidence. Do not automatically execute a copied script or infer a future host is qualified. Reconcile the source, destination and runtime identities and review a new exact plan where needed. The final handoff preserves the seven original wheels under `inputs/wheels/`, with all unique review/candidate evidence under `recovery/session/`; installed environment directories are excluded.

C271 remains open and in progress; R03–R05 are not done, P02 is in progress, PR274 is draft/open/unmerged and issue273 is open. The next fresh phase binds the prepared environment to the adopted current-host profile and reviews a complete H0 operational plan. H1, the full routine, integration and parent closure remain later gates. The eventual separate final-save receipt is `P20-DELIVERY.json` in this directory.
