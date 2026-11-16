# Export and view recorded animations

[User guides](README.md) · [Project overview](../../README.md) · [Current status](../../STATUS.md)

Run command examples from the repository root with Python 3.11 or later. Each named profile keeps its own contract and evidence; the examples do not select a new default or establish a comparative authoring advantage.

## See the animations

Open [the offline animation viewer](../../examples/visual/viewer.html) from a local checkout. It includes two actual OntoKin exports: an assembly whose head and hand move independently, and a sphere that continues under gravity after its carrier releases it and stops. Play, pause, scrub the timeline, orbit the view, or inspect an object's world position. The viewer loads the exported GLB bytes through Three.js; it does not calculate another physical trajectory.

On macOS, from the repository root:

```bash
open examples/visual/viewer.html
```

The bundled viewer and demonstrations work offline. The [visual example guide](../../examples/visual/README.md) explains the controls, editable sources, generated files, and optional verification tools. To open the exports in another application, use [independent parts](../../examples/visual/01-independent-parts.glb) or [gravity and release](../../examples/visual/02-gravity-and-release.glb). Blender import instructions are included in the guide; the measured target for this milestone is Three.js, with separate Khronos format validation.

## Export an OntoKin program

```bash
python3 -m ontokin export examples/visual/01-independent-parts.ok --output /tmp/independent-parts.glb
python3 -m ontokin export examples/visual/02-gravity-and-release.ok --output /tmp/gravity-and-release.glb
```

Each successful command writes a self-contained GLB and a JSON report beside it, such as `/tmp/gravity-and-release.export.json`. The report identifies the source revision, artifact hash, sampling settings, measured errors, and information retained only as metadata. The `.ok` source remains unchanged.

The default export samples at least 60 times per second and includes exact semantic event/completion boundaries. Its numerical checks read the encoded GLB and compare positions, orientations, and key timing with the reference evaluator. The adapter's default tolerances are `0.001 m`, `0.001 rad`, and `0.000001 s`. These concern exported playback and do not relax the evaluator's stricter language conformance checks. [OK-ENG-002](../../docs/engineering/OK-ENG-002-3d-scene-animation-export-and-visual-validation.md) defines the contract, evidence, and limits.
