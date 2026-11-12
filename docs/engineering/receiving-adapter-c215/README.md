# C215: CPU receiving-corner adapter

This proposed adapter connects unordered Blender triangle corners to the exact OntoKin source normals preserved by C214. It uses source object identity and orientation-preserving position triples, converts the explicit local coordinate frame, and reports shading differences with missing, ambiguous and invalid observations kept separate.

Read the [contract](CONTRACT.md), [adapter](adapter.py) and [results](RESULTS.md). The C214 synthetic-only profile and held C211 receiver stay unchanged. All C215 reports keep native fidelity, receiving evidence and provenance authentication false. A caller's native label does not establish actual execution or acceptance.

## Reproduce the CPU smoke proof

From the repository root, choose a new output directory:

```sh
python3 -IB docs/engineering/receiving-adapter-c215/run_proof.py --output /absolute/new/c215-proof
```

The driver reads the retained C210 inputs, generates explicitly synthetic observations and writes reports plus a hash-bound receipt. It does not execute an OntoKin program, exporter or native application. Independent controls and their separate original-GLB reader are retained in the C215 handoff.

For a separately prepared input, `adapter.py` requires `--payload`, `--observations`, `--glb`, `--bundle`, `--semantic`, `--input-lock`, `--receiver-source`, `--importer-source`, `--build-record`, `--import-settings` and `--output`. `--scene` supplies optional synthetic or mandatory native-unverified scene bytes. Output creation is exclusive. A future native plan must independently lock and review every artifact and capture source before execution.

This is a finite exact-position adapter. Coordinate drift, unknown frames, source identity mismatches and unsupported triangulation remain visible refusals or missing/invalid outcomes. No new tolerance or native launch is authorized.

Read the [next bounded receiving task](NEXT-TASK.md) only after completing reviewed C215 publication and verified handoff delivery. [Scope ownership](https://github.com/Omegapy/OntoKin/issues/162).
