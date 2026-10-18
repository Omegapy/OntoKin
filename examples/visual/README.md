# OntoKin visual demonstrations

These examples provide a complete path from an editable `.ok` program to a visible 3D animation. Python evaluates the authored motion and writes a glTF 2.0 binary file (`.glb`). The offline viewer loads that file with Three.js and plays its stored animation.

## Open the viewer

Open [viewer.html](viewer.html) from your local checkout. No server, installation, account, or network access is required. On macOS, from the repository root:

```bash
open examples/visual/viewer.html
```

Choose a demonstration, use **Play/Pause**, or scrub the timeline. Drag the scene to orbit and scroll to zoom. **Fit view** frames the complete trajectory. Select an object by name or click its shape to inspect its position in world coordinates. **Save GLB** downloads the exact played asset; **Save .ok** downloads its editable source. **Open GLB** reads a self-contained local file, but does not claim that the imported file passed OntoKin's numerical checks.

| Demonstration | Editable source | Animation | Export report |
| --- | --- | --- | --- |
| Independent parts | [01-independent-parts.ok](01-independent-parts.ok) | [01-independent-parts.glb](01-independent-parts.glb) | [01-independent-parts.export.json](01-independent-parts.export.json) |
| Gravity and release | [02-gravity-and-release.ok](02-gravity-and-release.ok) | [02-gravity-and-release.glb](02-gravity-and-release.glb) | [02-gravity-and-release.export.json](02-gravity-and-release.export.json) |

The first example adds visible body/arm geometry to the motion in the original independent-parts fixture and places its shoulder 0.45 metres to the side so the arm remains visible. The assembly translates until 2 seconds, the head finishes a 90-degree yaw at 1 second, and the hand extends until 2 seconds. The actions retain their own endpoints.

The second positions the sphere 0.42 metres to the side of its carrier so both shapes are visible. The sphere is released at 1 second; the carrier stops at 1.25 seconds. At 2 seconds the carrier is at `(1.25, 2, 0)` metres and the sphere is at `(2.42, -2.905, 0)` metres. Both states follow the existing evaluator's rules. The four original conformance `.ok` programs remain unchanged.

Joint markers, motion paths, and the grid are display aids. Markers identify parent attachment sites and remain visible after release; they do not indicate an active constraint. There is no ground collision in this physical subset, so a released sphere can pass below the reference grid. GLB playback does not execute gravity, class methods, or live mechanical constraints.

## Rebuild from source

From the repository root, with Python 3.11 or later:

```bash
python3 tools/build_visual_demos.py
```

This regenerates the two `.glb` files, their `.export.json` reports, reference sample `.reference.json` files, and [demo-data.js](demo-data.js), which embeds the same GLB bytes for offline loading. The reference samples are fresh evaluator observations used by the independent Three.js comparison. The command leaves the `.ok` sources unchanged.

To export another source or choose a smaller interval:

```bash
python3 -m ontokin export examples/visual/02-gravity-and-release.ok --output /tmp/release.glb
python3 -m ontokin export examples/visual/02-gravity-and-release.ok --output /tmp/release-short.glb --end 1.5 --fps 120 --no-helpers
```

The default sample rate is 60 frames per second, with additional event/completion keys and rotation subdivisions where needed. Default pose tolerances are 1 mm and 0.001 radians; the key-time tolerance is 1 microsecond. The report measures decoded animation at source/stored keys, exact boundaries, and three interior points per interval. This finite comparison does not prove an error bound at every possible time or certify every destination.

## Open a GLB in Blender

In Blender, use **File → Import → glTF 2.0 (.glb/.gltf)**, choose a GLB, and inspect the imported action in the timeline; see the [official glTF importer manual](https://docs.blender.org/manual/en/latest/addons/scene_gltf2.html). These are usage instructions; Blender import was not executed for this milestone. The measured external target is the bundled Three.js viewer. A compatible viewer or game engine should be checked independently before claiming its import preserves the contract.

The GLB contains meshes, materials, and animation tracks. OntoKin-specific identity, ownership, body, and joint information is carried in `extras`; another tool may discard that metadata. Continue editing the `.ok` file and export again when the authored behavior changes.

## Rebuild or verify the viewer

The Python exporter needs no external runtime package. Editing the viewer or rerunning its independent checks requires the pinned development packages in [tools/package.json](../../tools/package.json):

```bash
npm ci --prefix tools
npm run build-viewer --prefix tools
python3 tools/build_visual_demos.py --output-dir /tmp/ontokin-visual-check --include-conformance
node tools/verify_gltf.mjs /tmp/ontokin-visual-check --output /tmp/ontokin-external-validation.json
node tools/node_modules/playwright/cli.js install chromium --only-shell
node tools/verify_viewer.mjs --output-dir /tmp/ontokin-viewer-check
```

The external checker validates all six generated GLBs with the official Khronos validator, loads their clips through Three.js, and compares actual world poses with fresh evaluator observations. The viewer check renders screenshots, operates playback/inspection controls, checks narrow layout and downloads, and verifies that file-based playback makes no network requests.

The browser source is [viewer.js](viewer.js), bundled into [viewer.bundle.js](viewer.bundle.js). The bundle includes Three.js 0.180.0 under the [MIT license](THREE-LICENSE.txt). The dependency versions and integrity hashes are pinned in [tools/package-lock.json](../../tools/package-lock.json). Regenerate the bundle after changing the viewer source.

See [OK-ENG-002](../../docs/engineering/OK-ENG-002-3d-scene-animation-export-and-visual-validation.md) for the scene representation, loss disclosures, numerical limits, and measured results.
