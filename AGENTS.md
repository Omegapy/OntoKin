# Working on OntoKin

The owner authorizes autonomous technical development and repository stewardship toward [GOAL.md](GOAL.md). Routine work within that mandate should continue through implementation, verification, and reviewable publication. This is not legal ownership and does not enlarge platform permissions or authorization outside the project.

## Recenter and resume

At the start of a session, after compaction, and before choosing or closing a milestone:

1. Read GOAL and [STATUS.md](STATUS.md). Restate the current goal and the next unmet acceptance gate to yourself.
2. Inspect repository status/tree, the actual GitHub head, the integration lease, and relevant CI. Do not treat a synthetic local snapshot commit as the remote head or discard existing work.
3. Read the relevant specifications through [docs/README.md](docs/README.md), especially the adopted language rules and the active engineering contract. Historical proposals are not current implementation guarantees.
4. Continue authorized useful work. Record genuine blockers and the concrete next action; do not silently replace the goal with an easier demonstration.

## Coordinate writers

Follow the lease in STATUS. An independent scheduled review is read-only while another integration owner's lease is live. Delegated workers may edit only their assigned scope under that owner.

After expiry, acquire the lease through an expected-head commit/update and verify acquisition before editing. Keep implementation on an isolated branch and use expected-head publication. If another writer advances the branch, inspect and reconcile; never force an older tree over their work. If the available operation cannot enforce the required head condition, do not pretend acquisition was atomic.

Renew the lease and update STATUS at each meaningful checkpoint, including a completed work unit, a verification result, a changed decision, a blocker, a handoff, and before ending active work. Record only real automation identities and observed scheduled results. These files preserve continuity; they do not themselves run background jobs.

## Preserve meaning and evidence

- Keep `.ok` authoritative. Preserve identity, units/frames, independent ownership/following/connections, one motion authority, mass accounting, and honest release/state transfer.
- A semantic change needs an explicit versioned specification decision, synchronized grammar/examples/diagnostics, and corresponding conformance evidence. Do not silently change expected outcomes to make tests pass.
- Preserve historical product, semantic, foundation, diagram, and maintenance records. Do not rewrite preservation hashes or archival evidence to suppress a failure. Record new decisions and measured results separately.
- Distinguish represented, constructed, evaluated, exported, and destination-validated results. Unsupported behavior, information loss, failed goals, and stale results must remain visible.
- Keep the full GOAL scope and missing domains in STATUS. Completing OK-AGENT-001 or another finite release is not completing OntoKin.
- Runtime dependencies, architecture, and product limits are deliberate decisions. The current reference uses Python's standard library; a future change needs a concrete reason, dependency/provenance review, and relevant evidence. Installed dependency directories must not be committed.

## Verify the actual change

Use checks relevant to the change. Runtime or semantic changes normally require:

```bash
python3 -m unittest discover -s tests -v
python3 -m ontokin conformance --output /tmp/ontokin-conformance.json
```

Documentation and navigation changes require:

```bash
python3 docs/maintenance/reorganization-2026-10-17/verify_reorganization.py
```

Exporter/viewer changes also require fresh source-to-GLB builds, independent Khronos/Three.js checks, and visual inspection as documented in [OK-ENG-002](docs/engineering/OK-ENG-002-3d-scene-animation-export-and-visual-validation.md). Agent-interface work must execute the actual protocol cases, including failure/retry paths; a schema alone is insufficient.

Before declaring a release gate passed, identify the exact source/implementation revision, settings, artifacts, test results, relevant remote CI, and remaining limits. Preserve evidence in the repository or link to a durable identified result. Do not claim an untested destination, universal numeric accuracy, an unrun benchmark, a configured-but-unexecuted job, or all product requirements from a small passing corpus.

Update STATUS with the result and the next unmet gate. Keep it short enough to reread after compaction; detailed reasoning, contracts, and evidence belong in linked engineering records.
