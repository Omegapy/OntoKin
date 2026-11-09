# Run the public rotary-indexer repair

The current ChatGPT project is the execution environment. **Immediately spawn two subagents here** and assign one to Blender/Python and the other to OntoKin. The coordinator already has authorization to dispatch both. No separate host, permission request or isolation preflight is needed for this public repair.

1. Give both agents the handoff’s `benchmark/participant/task.md`, its common fixture, the same model settings, time allowance and attempt limit. Give each its own editable starter under `benchmark/starters/` and a separate output directory. Record the allowances at dispatch. Per-agent token counts are optional. Record them only if the environment supplies them and otherwise mark them unavailable.
2. Each agent creates the long-shoe and wide-long-shoe variants from one editable design and supplies its source, rebuild instructions, `long.glb`, `wide-long.glb`, and a measurement report. Both variants must retain the quarter turn and meet the brief’s 15.0 ± 0.5 mm minimum clearance per guard over the full two seconds.
3. The coordinator rebuilds the two variants for each route in a fresh output directory. Use the handoff’s `benchmark/evaluator/neutral_check.py` to measure each submitted export independently of the agent’s report. Record dimensions, the minimum gap and its time for each guard, any failed checks, and available elapsed-time and usage data. Report these as observations from the shared environment.

The [starter qualification](../rotary-indexer-c179/README.md) documents the initial guard penetration. The [public spacer](../hosted-spacer-c183/README.md) is a smaller worked example. The [C184 evidence](README.md#archived-isolation-test) documents the limits of blind scoring on this launcher.

## Qualification for a future blind study

A blind study with an unseen case requires a participant launcher that can restrict each child’s tools and files. Apply the following controls when qualifying such a study.

1. Use two fresh participants with the same requested model settings, empty histories, separate route identities and identical budgets. Stage independently generated, harmless random files in each route and in coordinator and evaluator storage. Record their digests before dispatch.
2. From each actual participant interface, establish own-route read and write. Test cross-route, coordinator and evaluator access, outbound access and nested delegation. Retain each request, response, and identity as observed by the operator. Any protected read or unrestricted alternate tool closes admission immediately.
3. Using disposable public inputs, exhaust the attempt cap and cancel a write while it is in flight. After shutdown, use operator-side snapshots to check for late writes. Seal a submitted artifact, hash it and check that participants cannot change the sealed copy or identify the other route. Run each control with sufficient evidence to distinguish a participant denial from a network outage, bad path, empty file or missing tool.
4. Release one genuinely new case only after both participants pass all required controls. Preregister the editable starters, independent measurements and tolerances, budgets, scoring, failure rule and meaningful improvement threshold. Lock masked scores before unmasking. Use provider token use as an endpoint only if the host can enforce and document it per worker.

[Public spacer evidence](../hosted-spacer-c183/README.md) · [OntoKin goal](../../../GOAL.md)
