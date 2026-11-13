# Next bounded scope — diagnose authority-file replacement rejection

First verify the saved C228 handoff and its documented restore path. Reconcile live main, branches/PRs, [scope #188](https://github.com/Omegapy/OntoKin/issues/188), integration ownership and retained unpublished work. Read current AGENTS, GOAL, STATUS and the nine recommendation records / 41 acceptance criteria before selecting execution.

## Question and boundary

Select one independently reviewed **CPU diagnosis** of the two observed same-content authority-file replacement failures in `LedgerControls.test_corrupt_replaced_aliased_or_missing_files_poison_live_capability`. Both the invocation marker and ledger journal were deleted and recreated with their original contents, yet the live capability's next reservation did not raise the expected `LedgerError`. [Exact failed observations](evidence/LEDGER-FAILURE.json).

The rejection contract remains unchanged: replacing an authority file must invalidate the live capability even when its contents are identical. The current aggregate establishes the two failed assertions, not their cause. Begin with the exact executed source, test and ledger implementation identities. Reconcile historical results before treating this as a newly introduced code regression.

## Finite plan and completion

Prepare a small, fixed diagnostic schedule and obtain independent review before any diagnostic execution. Use isolated disposable authority/output directories and fresh evidence locations. Preserve the original operations and expected rejection. Record the actual filesystem and runtime identity and capture relevant file/path/handle identities and ledger state before deletion, after recreation and at reservation. Retain original bytes/hashes, observed errors or missing errors, process outcomes and cleanup. Keep observation overhead and any instrumentation changes explicit.

Do not assume a filesystem mechanism from the two assertion messages. If the proposed schedule cannot distinguish candidate causes, narrow its question before running it. Declare process limits and maximum starts in advance, reserve them once, and retain every failed, inconclusive or unavailable outcome. A concrete prerequisite blocker completes the preparation scope without a workaround that weakens the guard.

Complete this step when the reviewed finite diagnosis finishes or reaches a concrete blocker, then independently review its evidence, publish the factual finding and save the successor handoff. **Stop there.** The diagnosis does not include a repair, another aggregate, a native schedule or R07 second-target work.

## Carry forward

C228 remains a failed aggregate with 4,661 passed methods and one failed method containing two failing subtests. All thirteen torque artifact-read methods and all three readback controls passed within that attempt; the A08 success carries no separately recorded timing or artifact hash. Sixteen external conformance cases remain pending.

Preserve C224's timeout, C226's setup failure, C227's isolated/profile distinction, all original failures and hashes, held drafts, consumed schedules and authoritative `.ok` source. R00/R01 keep their completed scopes; R02 remains blocked; R03-R08 retain their recorded pending work. R07 second-target CPU preparation follows reliability work and is not selected by this diagnosis. Original strict Blender normals and unresolved Godot lineage/rendering limitations remain unchanged.
