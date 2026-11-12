# C214: exact source normals and explicit loss reporting

This CPU-only prototype preserves the exact normal directions from the accepted C210 artifact and reports differences in synthetic observations. Surface normals are directions used for shading. Exact retained directions and actual destination shading are separate claims.

Read the [proposed contract](CONTRACT.md), [implementation](prototype.py), [CPU proof driver](run_proof.py) and [results](RESULTS.md). The original C211 strict receiving failure remains unchanged, and its receiver stays held. This profile accepts only explicitly synthetic observations; native fidelity and receiving-evidence fields are always false.

## Reproduce the bounded CPU proof

From the repository root, select a new output directory outside the source tree:

```sh
python3 -IB docs/engineering/source-normals-c214/run_proof.py --output /absolute/new/c214-cpu-proof
```

The command decodes the retained C210 files. It does not run the source program, export a new GLB or start Blender. It writes the exact payload, synthetic fixtures, per-corner reports and a hash-bound result manifest. Existing output files are not overwritten.

The script also provides `build`, `validate` and `report` CLI operations. Each takes `--glb`, `--bundle`, `--semantic` and `--output`; validation/report operations require `--payload`, and reporting additionally requires `--observations`. Output creation is exclusive. Inputs reside in `docs/engineering/semantic-export-c210/evidence/proof/` as `after.glb`, `after.program.bundle.json` and `after.semantic.json`.

The full generated outputs are retained in the C214 handoff under `evidence/c214/generated/`. The committed [run receipt](evidence/CPU-PROOF.json) supplies exact filenames, byte hashes, selected source hashes, interpreter/platform, commands and counts. Full output tables are kept outside Git to avoid duplicating the accepted source and bulky per-corner data.

Read the [next bounded task](NEXT-TASK.md) only after completing C214 publication and verified handoff delivery. [Scope ownership](https://github.com/Omegapy/OntoKin/issues/160).
