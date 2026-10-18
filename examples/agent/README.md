# Agent authoring and repair demonstration

This demonstration uses the working `ontokin.agent/0.1` interface to create a program, inspect its source and values, diagnose a rejected edit, repair one occurrence, evaluate motion, and retrieve a GLB. Every acceptance, diagnosis, state sample, and exported byte comes through `AgentService`.

The scene contains two instances of the same `Rig` class. The first assembly moves while its head turns and its hand extends. The second assembly provides an unchanged reference. A local edit increases only the first head's radius parameter from `0.2 m` to `0.35 m`; the second head remains at `0.2 m`.

## Open the result

Open [the offline viewer](../visual/viewer.html) from a local checkout, choose **Open GLB**, and select [repaired.glb](repaired.glb). Play the animation or scrub to **1.5 seconds**. The moving head is at `(1.5, 1, 0) m`; the reference head is at `(0, 1, 1.5) m`. The first head has the larger geometry. The viewer reads the imported GLB locally.

The viewer deliberately labels arbitrary local imports as having no built-in conformance claim. The source and validation for this particular file are provided separately by [repaired.ok](repaired.ok), [the export report](repaired.export.json), [the agent workflow](workflow.json), and [the milestone evidence](../../docs/engineering/agent-validation/README.md). File loading alone is not a numerical validation.

| File | Role |
| --- | --- |
| [authoring-demo.ok](authoring-demo.ok) | Editable starting program, using existing classes, parts, joints, methods, and independent actions. |
| [rejected-candidate.ok](rejected-candidate.ok) | Intentionally invalid candidate assigning `1[kg]` to a length parameter. Its rejection is part of the demonstration. |
| [repaired.ok](repaired.ok) | Accepted, complete native source after the scoped repair. |
| [repaired.glb](repaired.glb) | Actual retrieved animation bytes. |
| [repaired.export.json](repaired.export.json) | Named destination, source and artifact identities, conversions, tolerances, and decoded numerical checks. |
| [repaired.reference.json](repaired.reference.json) | Twenty-five state samples obtained through agent inspection, for independent Three.js comparison. |
| [workflow.json](workflow.json) | Complete requests, responses, identities, and measured demonstration checks. |

## Reproduce the workflow

From the repository root, with Python 3.11 or later:

```bash
python3 tools/build_agent_demo.py --output-dir /tmp/ontokin-agent-demo
```

The driver uses a fresh temporary durable store. It first discovers the typed `box` constructor, then creates the entire starting program at the evaluated level. It inspects the first assembly's identity and writable span, submits the invalid initializer, and verifies both the `OKL-E-UNIT` diagnostic's exact candidate bytes and preservation of the previous accepted revision.

The corrected patch is calculated against the accepted source. It inserts `head.radius = 0.35[m];` inside the selected assembly's initializer. It does not modify the shared class default. Inspection verifies both occurrences, including the unchanged sibling. An explicit ordinary run advances to `0.5 s` and then `3 s`; later inspection reads that completed interval without advancing it. Finally, the driver exports to `ontokin.glb/0.1`, retrieves bounded artifact chunks, reassembles the GLB, and checks its SHA-256 against the delivered report.

The driver is a deterministic agent-style client with predetermined expectations. It does not call a language model or measure authoring efficiency. It demonstrates that an AI agent can use the same documented operations; it does not certify all AI workflows or the full OntoKin product goal.

## Use the agent interface directly

Run the JSONL service:

```bash
python3 -m ontokin agent --store /tmp/ontokin-agent-state
```

Write one JSON request per line. For example:

```json
{"schema_version":"ontokin.agent/0.1","project_id":"my-scene","request_id":"discover-1","operation":"discover","profile":"core-0.1","filter":{"name":"sphere"},"limit":10}
```

Work requests return a durable queued receipt. The background worker performs them. Use a new identity for each status lookup:

```json
{"schema_version":"ontokin.agent/0.1","project_id":"my-scene","request_id":"status-1","operation":"status","target_request_id":"discover-1"}
```

The outer status describes the lookup; `result.target.status` describes the original work. Repeat the original payload and identity to retrieve its recorded result. Reusing that identity for different work is rejected. An `unknown_outcome` requires reconciliation of source and runs before deliberately submitting a new request.

For a one-request process, save a request as JSON and run:

```bash
python3 -m ontokin agent --store /tmp/ontokin-agent-state --request /tmp/request.json --wait
```

Without `--wait`, a work request remains queued after the process exits. A later service process can perform it. Native source snapshots, accepted revisions, requests, runs, and artifacts persist in the chosen local store. Use a local filesystem and restart the Python process after package upgrades; this release is not a distributed or hot-reload service.

The [engineering contract](../../docs/engineering/OK-AGENT-001-ai-agent-authoring-and-inspection-interface.md) defines all eleven operations, validation levels, exact UTF-8 patching, cancellation, bounded inspection, engine compatibility, retention, and recovery. The [request schema](../../docs/language-design/agent-v0.1/request.schema.json) and [response schema](../../docs/language-design/agent-v0.1/response.schema.json) describe the JSON shapes.
