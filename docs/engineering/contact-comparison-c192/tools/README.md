# Verify and inspect C192

The experiment's final deliveries are rejected. Successful replay of their
evidence means the same failures and supporting measurements reproduce.

From an exact restored repository, with CPython 3.12.14 and NumPy 2.3.5:

```sh
python -B docs/engineering/contact-comparison-c192/shared/verify_inputs.py --repo .
python -B docs/engineering/contact-comparison-c192/tools/replay_evidence.py \
  --repo /absolute/path/to/repository \
  --archive /absolute/path/to/evidence.tar.xz \
  --out /absolute/path/to/new-replay
```

The archive is stored in this engineering directory and also in the handoff.
Replay verifies its inventory, all six participant build outcomes, the unchanged
playback/mapping gates, 28 analytic controls, captured native replay equality and
rebuild/regeneration hashes. It performs no fresh native or receiving execution.

For a fresh build, select a retained source and a new output directory:

```sh
python -B docs/engineering/contact-comparison-c192/shared/build.py \
  --repo /absolute/path/to/repository --route ok \
  --source /absolute/path/to/01-edit.ok \
  --out /absolute/path/to/new-build \
  --blender /absolute/path/to/blender-4.5.3-linux-x64/blender
```

For the direct route use `--route python` and `design-edit.py` or
`design-reuse.py`. The exact executable SHA-256 is
`5e15447670804c855fef6033ac9b8fd82696b762095becf0df79b1c2f8034397`.
Its origin and archive hash remain in the unchanged C191 backend manifest.
The source bundle does not contain that external executable.

Expected C192 build exit status is one, with a retained mapping failure. The .ok
failed stage is below `store/attempts/<attempt>/failed-stage`; the Python failed
output is below `artifact`. `delivery.json` records no accepted artifact path.
Use `shared/check_delivery.py` on that retained path with `--case edit` or
`--case reuse`. The final-playback portion passes and the mapping portion fails.

`shared/inspect_native_c192.py` wraps the unchanged independent C191 Blender
inspector with the frozen C192 input values. Run it through pinned Blender with
the retained scene as the opened file. `tools/verify_builds.py` records the full
commands and verifies fresh-build and reopened-sample equality. Archived command
receipts retain original absolute paths; adapt paths for a new workspace without
editing those receipts or the original sources.

The evidence archive includes the exact inherited receiving tools, Three.js r186,
Khronos validator and license files under `c192-receiving-deps`. Their command
receipts and real imported-output frames are under `c192-receiving`. These are
verification dependencies, not new product-runtime dependencies.
