# Inspect and repair source-authored forces

Agent/0.5 processes immutable source `0.5` / `force-0.1` programs. A force statement
applies a constant world force at a free sphere's center of mass for an authored
duration. The source kernel is implemented; the GLB/0.5 adapter is not yet
available. This example deliberately requires an unsupported-delivery error,
not an empty artifact described as a successful export.

From the repository root, record the actual interface workflow:

```sh
python3 tools/build_force_agent_demo.py --output-dir /tmp/ontokin-force-workflow
```

Use a new output directory. The recorder refuses to overwrite existing evidence.
It sends source bundles, creates accepted revisions, requests before/after
samples and repairs three generated-instance programs through source patches.
It retains every request and response, complete source snapshots, failed and
stale candidates, retry receipts, cursor checks and a failed-run prefix/reset.
No manually constructed Python geometry or hidden host-state force is used.

The separate verifier needs verification-only packages. Install them in a virtual
environment, not as application runtime dependencies:

```sh
python3 -m venv /tmp/ontokin-force-verification
. /tmp/ontokin-force-verification/bin/activate
python -m pip install -r tools/force-agent-verification-requirements.txt
python tools/verify_force_agent_workflow.py \
  --workflow-dir /tmp/ontokin-force-workflow \
  --output /tmp/ontokin-force-audit.json
```

For the repeatable integration checks, use the same prepared environment:

```sh
python tools/check_local.py --force-agent
```

This runs the inherited local regression roles, checks the pinned verification
packages, executes the Agent/0.5 tests without skips, then records and audits
a fresh workflow in an isolated evidence directory. The successful scope
remains Agent/0.5; GLB/0.5 and the complete force release need separate work.

To send your own requests, explicitly select the protocol:

```sh
python3 -m ontokin agent --protocol ontokin.agent/0.5 \
  --store /tmp/ontokin-force-store --wait
```

Send one JSON request per line. The unselected CLI still uses Agent/0.1. The
Python program-service default still uses Agent/0.2. Force requests use their
own database and cannot silently open an earlier protocol store.

See the [interface contract](../../docs/engineering/OK-AGENT-005-finite-force-program-workflows.md)
and [verification guide](../../docs/engineering/force-agent-validation/README.md)
for source authority, recorded evidence and the remaining release gates.
