# C180 · How to test the value of editable physical intent

The owner adopted the [revised mission](../../../GOAL.md) on November 9, 2026. For the next investment decision, the unit of work is a repair someone could ask an agent to make. For example, after widening one moving part, can the agent preserve its attachment, keep a sibling unchanged and regenerate the two requested variants from one design?

## What each experiment can tell us

| | Frozen rotary pilot | Proposed study |
| --- | --- | --- |
| Question | Can each complete workflow deliver a valid, reusable repair under the same limits? | Does the typed source help when both routes use the same execution backend? |
| Comparison | Direct Blender/Python and native OntoKin export. Both deliver to the same GLB checker and viewer. | The same pinned agent uses either direct Blender/Python or an OntoKin adapter to the same Blender version. The adapter must first pass an independent source-to-destination check. |
| Unit | One moving assembly, with two required variants in each submission. | 30–50 unseen tasks, paired by task. Identify their distinct assemblies and task families. Multiple edits to one object share the same underlying design. |
| Decision | Use the pair to locate failures and decide if a larger experiment is justified. | Expand the capabilities that meet a predeclared benefit at acceptable cost. Narrow or pause investment when the benefit is absent. |

The [C179 admission](../rotary-indexer-c179/README.md) established equivalent starting geometry and motion. The two routes reach the common evaluator through different exporters, so any pilot difference can also reflect those exporters. The dated C179 protocol, tool versions, draw, clearance tolerances and scorecard remain the authority for that pair.

## Before reserving tokens for the larger study

1. Choose the target task families. Include dimensioned changes, a joint or motion constraint, reuse of multiple instances and a later edit to one named instance. Keep the test assets, variants and answers out of the agent's examples and the adapter's development fixtures.
2. Set the main outcome and the minimum improvement worth its engineering cost before opening any submissions. A practical main outcome is the fraction of paired tasks that pass both the delivered-geometry checks and a clean rebuild from editable source. Publish the tolerance and physical reference for each task. A timing claim requires a trajectory check. A dynamics claim requires a corresponding physical reference.
3. Use fresh contexts, balance route order across tasks, and give both routes the same information, model settings, time, token limits, backend version and access to inspection tools. Log the first submitted candidate and every subsequent repair. An evaluator outside both workspaces grades opaque submissions and records the scores before route labels are revealed.
4. Report the count where both routes passed, only OntoKin passed, only direct Blender passed, or neither passed. Retain every cutoff or failed submission in the denominator. Report first-pass and final acceptance, dimensional error, physical violations, unintended sibling changes and successful later edits. Distinguish a rejected edit that preserved the accepted source from an invalid state that reached a delivery.
5. For pairs at the same success level, compare elapsed time, model turns, tool calls, input/cache/output tokens, repair turns and interventions. Report setup separately, including adapter development and route-specific preparation. Record the price schedule when stating dollar costs. Report variation by asset family before generalizing from repeated variants.

A new destination earns a support claim only for the properties the destination actually preserves. Pin the source revision and the backend version. Inspect identity, units, frames, joint limits, animation or physical state as applicable after import. Document losses. The existing recorded GLB permits checks on delivered geometry and motion. A USD Physics scene, Unreal behavior or a CAD solid would each require its own destination test.
