# C191 receiving-application checks

These tools operate on the actual exported GLBs. They do not rebuild the design
or regenerate a stopping trajectory. [PROVENANCE.json](PROVENANCE.json) identifies
the inherited C190 scripts and the limited C191 changes.

The delivered evidence bundle supplies the pinned Khronos validator archive
and Three.js files with their licenses. Extract the bundle before running these
commands. `three_loader.mjs` resolves the adjacent
`../indexer-view/three` files. These are verification dependencies, not OntoKin
runtime dependencies.

`validate_glbs.cjs` loads every relative path in a JSON list and records the file
hash and complete validator report. Errors or warnings make the command fail.
Any informational messages remain in the receipt.

`three_readback.mjs` loads each manifest entry through the real Three.js
`GLTFLoader`, evaluates its `AnimationMixer` at zero, the declared reference
time and two seconds, and records bounds of all seven mesh identities. Its
manifest supplies the expected final left gap; the right gap remains 15 mm.
This is Node-based loading and playback, with no browser or GPU-rendering claim.

`render_frames.py` runs inside the pinned Blender executable. It independently
decodes each GLB, imports that same file, checks the imported bounds at each pose
and renders three frames through CPU Cycles using the preserved camera. The
disabled-collider control's middle frame uses the enabled case's reference
contact time; it is not reported as contact in the disabled case.

Example command, with paths resolved after extracting the handoff:

```bash
"$C191_BLENDER" --background --factory-startup --threads 4 \
  --python docs/engineering/guided-contact-c191/tools/render_frames.py -- \
  --output /tmp/c191-fresh-renders \
  --job A /absolute/path/to/A/final.glb 1.6
```

Use a new output directory. The tool records actual hashes, versions, camera,
renderer settings, poses, import-bound comparisons and image paths. Inspect the
rendered images as well as the numerical receipt.
