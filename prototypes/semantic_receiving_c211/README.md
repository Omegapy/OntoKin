# Experimental C211 Blender receiver

This opt-in prototype receives one exact accepted C210 construction artifact in one pinned Blender 4.3.2 build. Read the [finite contract](../../docs/engineering/semantic-receiving-c211/CONTRACT.md) before execution. It is separate from the compiler, Agent, default GLB export and frozen C199/C200 workflows.

`input_bindings.json` fixes the accepted source/dependency, GLB, sidecar, frozen reference and actual prior acceptance evidence. `build_bindings.json` fixes the available executable and all importer Python source bytes; the installed upstream build label is `Unknown`, explicitly retained. `validation.py` independently reads the delivered GLB and compares actual native measurements. `blender_observe.py` imports once, records raw native geometry/properties, explicitly attaches canonical semantic metadata, renders two views, saves the native scene and separately reopens it. Raw native coordinate observations remain available for independent conversion and review.

After the integrator confirms a durable contract/implementation checkpoint, run from the repository root with a new output directory:

```bash
python3 -B prototypes/semantic_receiving_c211/run.py \
  --inputs docs/engineering/semantic-export-c210/evidence/proof \
  --output /absolute/new/c211-receiving
```

The driver performs one import and one reopen, with bounded process deadlines and retained logs. It never retries or overwrites an existing experiment. Failure retains partial evidence. A numeric pass still requires independent visual and code/evidence review. Source changes, altered hashes, new Blender builds, or other assets require a separately reviewed contract; this command does not admit them.

CPU controls run without importing or starting Blender:

```bash
python3 -B -m unittest discover -s tests -p 'test_semantic_receiving_c211.py' -v
```

Tests use synthetic observation fixtures derived from the exact retained GLB to test rejection and accounting. They do not establish actual Blender compatibility. Only the separately identified receiving run can establish that finite result. No executable hinges, following constraints, collision, live physics, source reconstruction, second destination or measured authoring advantage is claimed.
