# Agent authoring and reusable assemblies

[User guides](README.md) · [Project overview](../../README.md) · [Current status](../../STATUS.md)

Run command examples from the repository root with Python 3.11 or later. Each named profile keeps its own contract and evidence; the examples do not select a new default or establish a comparative authoring advantage.

## Try an agent edit

From a local checkout with Python 3.11 or later, run this example from the repository root.

```sh
python3 tools/build_agent_demo.py --output-dir /tmp/ontokin-first-model
```

Open the checkout's [offline viewer](../../examples/visual/viewer.html), choose **Open GLB**, and select `/tmp/ontokin-first-model/repaired.glb`. Scrub to **1.5 s**. The moving assembly's blue head is wider than the stationary assembly's head. The example uses a scripted client to make the edit, reject a value with the wrong unit, and retrieve the animation through the agent interface.

To try your own edit, start with the [editable scene](../../examples/agent/authoring-demo.ok), the [Agent/0.1 request schema](../../docs/language-design/agent-v0.1/request.schema.json), and the [agent guide](../../examples/agent/README.md). The [first-use task](../../examples/agent/first-use.md) describes how to test a fresh coding agent on this workflow.

To see why a valid part can still make a bad assembly, try the [connected-duct example](../../examples/connected-duct/README.md). It checks the opening between two hollow parts and repairs an offset through the Agent interface.

> **Project status:** OntoKin remains in development. The reference package is **0.4.0**. Its development line supports pinned reusable assemblies, native exterior surfaces and regional PBR materials, instantaneous impulses, and finite center-of-mass force intervals. Explicit Agent/0.5 and recorded GLB/0.5 support force-program inspection, source repair and artifact retrieval. Earlier profiles retain their meanings and defaults. [STATUS.md](../../STATUS.md) identifies integrated implementation, complete release evidence and remaining requirements; component implementation alone does not close a release or the broader product goal.

The [project goal](../../GOAL.md) defines the semantic-authoring mission and current investment gates. [STATUS.md](../../STATUS.md) records verified progress, the active milestone, and the next unmet gate. [AGENTS.md](../../AGENTS.md) defines how development resumes after interruptions and coordinates concurrent work.

## Build an assembly from a pinned component library

From the repository root, with Python 3.11 or later:

```bash
python3 tools/build_construction_demo.py --help
python3 tools/build_construction_demo.py --output-dir /tmp/ontokin-construction-demo
python3 -m ontokin agent --protocol ontokin.agent/0.2 --store /tmp/ontokin-program-state
```

The demonstration uses a real imported component module and a `Keyed` input to construct two assemblies with three and five articulated parts. It discovers the pinned library, inspects a generated occurrence, rejects an invalid units edit, repairs that occurrence's public length parameter, evaluates the motion, and retrieves `keyed-rack.glb` through the agent interface. The final assembly contains 18 objects; the generated collection itself adds no object or mass. Its expected dimensions and 126 world poses are specified independently in the [Rack fixture](../../docs/language-design/construction-v0.1/01-keyed-rack/expected.json).

Open [the offline viewer](../../examples/visual/viewer.html), choose **Open GLB**, and select `/tmp/ontokin-construction-demo/keyed-rack.glb`. The [construction example guide](../../examples/construction/README.md) explains the motion, exact source files, reports, and Python APIs for loading either a local file manifest or an inline bundle. The demo driver reproduces its fixed fixture; the program-bundle APIs support an agent's own authored sources.

[OK-LANG-002](../../docs/language-design/OK-LANG-002-pinned-modules-and-keyed-assembly-construction.md) defines the versioned language extension. [OK-AGENT-002](../../docs/engineering/OK-AGENT-002-program-bundles-and-atomic-source-edits.md) defines program revisions, atomic edits across files, source provenance, and the separate agent service. `.ok` files remain the editable authority; the complete pinned source closure identifies an accepted program. The new animation target is `ontokin.glb/0.2`.

## Author and repair through the agent interface

```bash
python3 tools/build_agent_demo.py --output-dir /tmp/ontokin-agent-demo
python3 -m ontokin agent --store /tmp/ontokin-agent-state
```

The first command runs a complete, inspectable workflow: create a two-assembly scene, reject an invalid units edit, repair only one head, confirm the sibling remains unchanged, evaluate the motion, and retrieve a verified GLB. The second starts the local JSONL interface for an agent's own requests. Python clients can use `from ontokin.agent import AgentService` directly.

The [agent example guide](../../examples/agent/README.md) includes the editable sources, actual [repaired animation](../../examples/agent/repaired.glb), complete [request/response evidence](../../examples/agent/workflow.json), and instructions for opening the result in the offline viewer. [OK-AGENT-001](../../docs/engineering/OK-AGENT-001-ai-agent-authoring-and-inspection-interface.md) defines immutable source revisions, scoped UTF-8 patches, idempotent requests, cancellation, exact-time inspection, engine-bound runs, and recovery. The local interface requires no language-model call or external runtime dependency.
