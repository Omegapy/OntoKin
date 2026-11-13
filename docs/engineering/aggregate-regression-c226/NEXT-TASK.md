# Next bounded task: diagnose the frozen A08 setup deadline

First verify the saved C226 handoff and its documented offline restore, then reconcile actual main, branches/PRs, scope issue #184, integration ownership and surviving unpublished work. Read AGENTS, GOAL, STATUS and the complete [nine-task recommendation tracker](../review-integration-c221/RECOMMENDATIONS.json). Preserve all 41 acceptance criteria.

C226 finished one immutable default aggregate attempt on `3f17a523b5d5c435f71525a499d2f071ca6e4e96`. It recorded 4,649 passed methods, thirteen unrun methods and one separate class-setup error. The six other commands passed at their scopes. R02 remains blocked; the default driver was not stopped by its 3,600-second outer ceiling.

## Selected diagnosis boundary

Select one bounded CPU diagnosis of `TorqueArtifactReadTests.setUpClass`, which calls the frozen A08 export through the actual durable service under the original **1,000,000-operation / 30,000-ms** request and host limits. Begin with `tests/test_torque_artifact_reads.py`, the frozen `docs/language-design/torque-v0.1/freeze/agent/request-workflows.json` and workflow manifest, the [C226 exact failure](evidence/SETUP-ERROR.json), and the [historical comparison](evidence/HISTORICAL-COMPARISON.json).

Reconcile the different current and historical implementation digests before attributing the result to an unchanged implementation or a regression. Then identify the concrete work that reaches the `recording_export_readback` deadline. Define and review a finite diagnostic plan before any new execution, retain exact source/input/process evidence, and keep the real-clock, authority, budget, transaction and byte-integrity behavior intact.

Completion is a supported cause or a precise remaining blocker, an independently reviewed diagnosis and one verified saved handoff. Any repair requires its own clearly selected scope and relevant controls; a new complete aggregate remains separately selected afterward. Do not substitute a prebuilt artifact, skip the thirteen methods, increase the frozen product budget or stitch focused results into an aggregate pass.

## Carry forward

R00/R01 remain completed within their recorded scopes. R02 stays blocked until a valid complete aggregate establishes its acceptance. The original C224 timeout, C225 focused result and C191/C193 failure evidence remain unchanged. Other interpreters, sixteen external conformance cases and optional visual/dedicated force-agent roles are still separate obligations.

R07 CPU second-target preparation remains pending after the reliability work; R03-R06 are not new global prerequisites for it. No Godot/Blender process or version probe, new receiving schedule, visual regeneration or later feature is part of this diagnosis. Preserve held PRs #155/#165/#167/#169, consumed schedules, original strict Blender-normal failure and unresolved Godot lineage/rendering limits. Deliver the selected diagnosis handoff and stop.
