# Programs that request an execution budget

Source `0.7` / `planar-reach-budget-0.1` adds a literal header for computation resources. The defaults are still 100,000 operations and 30,000 milliseconds. A host can authorize larger ceilings without changing the budget of a program that omits the declaration.

```ontokin
ontokin "0.7";
module Workshop @ "workshop";
profile "planar-reach-budget-0.1";
execution {
    max_operations = 400000;
    max_elapsed = 80[s];
}
```

The entry source makes the request. The execution environment independently decides whether it is permitted. Imported modules share the entry's allowance and cannot declare a budget. Computation time is separate from `scene.duration` and playback time.

## Run the frozen workshop

[larger-workload.ok](larger-workload.ok) describes six independently moving vessels. Their visible geometry is a two-material loft; each physical body is a homogeneous sphere. A two-second upward force accelerates each body, and a center-applied impulse at one second changes its horizontal velocity without adding spin. The recording lasts three seconds.

The [expected geometry and motion](larger-workload.expected.json) were calculated from the authored dimensions, `a = F / m` and `delta_v = J / m`. The [freeze record](acceptance-freeze.json) identifies these exact bytes before execution. These are new inputs, separate from the original reach acceptance fixtures.

An operator who authorizes 400,000 operations and 80 seconds can use the example host launcher:

```bash
python3 tools/ontokin_budget_host.py export \
  examples/execution-budgets/larger-workload.ok \
  --target ontokin.glb/0.7 --fps 60 --end 3 --no-helpers \
  --output /tmp/ontokin-budget-workshop/workshop.glb
```

The launcher fixes its host policy in Python. Expose it only in an environment where that policy is authorized. The ordinary `python3 -m ontokin export ...` launcher retains the default host ceilings and refuses an unapproved increase. Neither the source nor a caller flag creates host authority.

Optional `--max-operations` and `--max-elapsed-ms` flags explicitly reduce the source request. A cap greater than the corresponding source request is an error, even when the host would permit it. There is no silent clamping or automatic retry.

## Embedding API

A trusted Python host can call `ontokin.budget_runtime.execute_budgeted_export(bundle, policy=HostPolicy(400000, 80000), options=...)`. `bundle` is an immutable `ProgramBundle` containing the exact entry and pinned imports. The result contains independently verified GLB bytes on success, or a bounded diagnostic receipt with no artifact bytes on an expected failure. Caller cancellation retains its original exception identity.

The receipt identifies the source and implementation, policy, source request, caller reductions, effective limits, consumed operations, elapsed time, validated interval and artifact hash. Header admission, construction, numerical work, simulation, recording, export and supplied-byte readback use the same counter and original deadline.

The command-line writer stages both output files and restores existing files after a handled publication error. If restoration itself fails, it retains the original bytes in named recovery backups. A process crash between filesystem replacements still requires checking the report's artifact hash. File persistence follows the completed computation and does not grant further product work.

## Verify the separate cohort

```bash
python3 tools/run_budget_acceptance.py --output-dir /tmp/ontokin-budget-acceptance
node tools/verify_budget_glb.mjs \
  --artifact /tmp/ontokin-budget-acceptance/authorized-large.glb \
  --expected examples/execution-budgets/larger-workload.expected.json \
  --output-dir /tmp/ontokin-budget-independent --browser
```

The Python runner keeps the exact default-limit control and the authorized larger attempt. The independent checker uses the repository's pinned Khronos validator, Three.js and browser tooling. It compares decoded geometry, material regions and animation against the frozen expectations and produces six browser captures for review. These tools require the verification-only dependencies documented in the [C073 evidence record](../../docs/engineering/source-execution-budgets-2026-10-29-c073/README.md).

This is an experimental source/CLI increment. Agent/0.7 is unavailable, the original reach release remains incomplete, and recorded GLB playback does not run live physics in a destination engine. See the [adoption decision](../../docs/language-design/execution-budgets-v0.1/ADOPTION-C073.md) for the exact contract and limits.
