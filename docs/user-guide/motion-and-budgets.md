# Motion profiles and execution budgets

[User guides](README.md) · [Project overview](../../README.md) · [Current status](../../STATUS.md)

Run command examples from the repository root with Python 3.11 or later. Each named profile keeps its own contract and evidence; the examples do not select a new default or establish a comparative authoring advantage.

## Apply source impulses and export their motion

The explicit language `0.4` / `impulse-0.1` profile adds instantaneous world-expressed momentum changes at a free sphere's own local point. An off-center application changes both linear velocity and angular velocity. For a declared free sphere named `ball`, the source event is:

```ontokin
at 1[s] sequence {
    impulse ball using vector(world, 0[N*s], 2[N*s], 0[N*s])
        at point(ball.frame, 0.5[m], 0[m], 0[m]);
}
```

Export the complete pinned source fixture, run the actual agent repair workflow, or start the explicit JSONL service:

```bash
python3 -m ontokin export docs/language-design/impulse-v0.1/p02-off-center-mixed-imports.files.json --bundle --target ontokin.glb/0.4 --output /tmp/ontokin-impulse.glb
python3 tools/build_impulse_agent_demo.py --output-dir /tmp/ontokin-impulse-agent
python3 -m ontokin agent --protocol ontokin.agent/0.4 --store /tmp/ontokin-impulse-state
```

[OK-LANG-004](../../docs/language-design/OK-LANG-004-source-impulses-and-free-sphere-dynamics.md) fixes units, frames, own sphere inertia, ordered release and impulse events, exact source identities, and atomic failure. [OK-AGENT-004](../../docs/engineering/OK-AGENT-004-source-impulse-program-workflows.md) defines complete bounded influence inspection, source-based mass/radius repair, and exact artifact retrieval. GLB/0.4 retains native lofts and regional PBR materials and records the resulting rigid motion, including sufficient samples for authored high-spin cases.

The [I01–I12 release procedure](../../docs/engineering/OK-ENG-005-source-impulse-release-conformance.md) separately requires all 40 frozen source cases, actual agent workflows, independent destination/browser evidence and current inherited execution roles. Implementation and finite release acceptance have separate identities in [STATUS](../../STATUS.md). This impulse profile does not establish contacts, continuous torque, general rigid dynamics or live destination physics; earlier source, agent and export profiles retain their existing meanings and defaults.

## Apply finite force intervals and retrieve recorded motion

Language `0.5` / `force-0.1` adds a constant world force at the center of mass of a supported free homogeneous sphere. Authored intervals have exact activation and completion times; overlapping forces add to the existing gravity and impulse behavior. Source inspections expose the complete revision-bound force history, current acceleration and motion authority.

```bash
python3 -m ontokin export docs/language-design/force-v0.1/p01-single-interval.files.json --bundle --target ontokin.glb/0.5 --end 2.5 --output /tmp/ontokin-force.glb
python3 -m ontokin agent --protocol ontokin.agent/0.5 --store /tmp/ontokin-force-state
python3 tools/build_force_delivery_demo.py --output-dir /tmp/ontokin-force-delivery
```

The explicit export records the requested prefix, including its exact completion boundaries, and checks decoded binary32 motion against the chosen tolerances. A valid short prefix can succeed when a later authored activation would fail. Acceleration and angular bounds add samples within fixed resource limits; a representation that cannot meet its contract fails explicitly. GLB playback uses recorded transforms.

The [force delivery guide](../../examples/force/README.md) explains source-authoritative mass/force/duration repairs, actual chunk retrieval, independent native decoding, and real browser inspection. [OK-LANG-005](../../docs/language-design/OK-LANG-005-finite-center-of-mass-force-intervals.md), [OK-AGENT-005](../../docs/engineering/OK-AGENT-005-finite-force-program-workflows.md) and [OK-ENG-007](../../docs/engineering/OK-ENG-007-native-force-glb-export.md) fix the source, interface and export contracts. [OK-ENG-008](../../docs/engineering/OK-ENG-008-force-release-conformance.md) defines complete F01–F12 acceptance under the current local execution policy, including all required source, regression, compatibility, destination and visual evidence. The complete finite release result is recorded separately in [STATUS](../../STATUS.md).

## Configurable execution budgets: source, CLI and Agent workflows

Explicit source `0.7` / `planar-reach-budget-0.1` can request more computation time and operations within ceilings independently authorized by its execution environment. Ordinary defaults remain **100,000 operations and 30,000 ms**; existing acceptance tests retain their original limits. A larger host ceiling does not silently increase an omitted program budget. Computation time and the animation's modeled duration are separate values.

[The C073 adoption](../../docs/language-design/execution-budgets-v0.1/ADOPTION-C073.md) defines the implemented grammar, trusted host API, bounded admission and explicit GLB/0.7 output. One counter and original deadline cover admission, compilation, simulation, export and independent output validation. [The example guide](../../examples/execution-budgets/README.md) provides an operator-controlled launcher and a frozen six-vessel force/impulse workload. Command-line caps can reduce a request; they cannot authorize a larger host ceiling.

[The C073 engineering record](../../docs/engineering/source-execution-budgets-2026-10-29-c073/README.md) identifies the source/CLI checks and integration. [C074](../../docs/engineering/agent-execution-budgets-2026-10-30-c074/README.md) adds the separately selected **Agent/0.7** service for discovery, exact source edits, saved-program authorization, evaluation, export, retrieval, cancellation and retries. Its [versioned contract and schemas](../../docs/language-design/agent-v0.7/README.md) preserve earlier Agent defaults and stores. [C072](../../docs/engineering/language-execution-budgets-2026-10-29-c072/README.md) retains the original proposal and source evaluation.

```bash
python3 -m ontokin agent --protocol ontokin.agent/0.7 --store /tmp/ontokin-budget-agent
python3 tools/run_budget_agent_acceptance.py --output-dir /tmp/ontokin-budget-agent-evidence
```

The ordinary CLI host permits the default ceilings. An embedding host can use `BudgetAgentService(store, host_policy=HostPolicy(400000, 80000))` from `ontokin.budget_agent` and `ontokin.execution_budget`, or pass that policy to `cli.main`. Request JSON never grants host authority. Agent/0.7 patches use exact UTF-8 spans within an identified source file; earlier finer edit scopes keep their own contracts. Successful artifact production and later retrieval have separate current-policy requests and receipts. C074 remains an experimental development increment; its complete verification and integration are recorded separately.

## Deferred experimental planar reach

Further reach work remains deferred under the [current goal](../../GOAL.md). The following records describe the existing profile and its unresolved release obligations; they do not select the next implementation task.

The C059 reconciliation selects the reviewed C032 development runtime, preserves the later C058 evidence, and excludes the held C035 runtime experiment. Source `0.6` / `planar-reach-0.1`, Agent/0.6 and recorded GLB/0.6 require explicit selection and are marked experimental in capabilities and discovery. Earlier bindings and defaults retain their meanings. [Current integration status](../../STATUS.md) and the [reconciliation record](../../docs/engineering/repository-reconciliation-2026-10-28/README.md) distinguish the actual candidate, checks and resulting main from release acceptance.

Historical original recording evidence is **24/28, a failed gate**. P11/P16/P23/L03 remain unresolved under the original limits; C035 remains held, including adverse timing. The comparison accounting/passive-authority concern remains open. [The M1 decision](../../docs/engineering/OK-DEC-COMPARE-M1-0.1.0.md) rejects the exact proposed model for comparison-only operation saving and adopts no replacement.

Main is the current development baseline under [OK-ENG-009](../../docs/engineering/OK-ENG-009-development-integration-and-branch-lifecycle.md). New checkpoints normally become commits on the same active scope branch. Historical branches are preserved through a separately verified archival history before removal. This consolidation does not complete the reach release: all 28 source recordings, ten Agent artifacts, compatibility, rates, native/browser/visual checks, formal input closure and every R01–R12/Q01–Q22 obligation remain required.

This profile delivers recorded animation. Demonstrating live behavior would require a separate import and behavior test in the named engine version.
