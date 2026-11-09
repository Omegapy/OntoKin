# A splat environment for the service entrance

Play the cart and gate inside a read-only room made of 1,416 Gaussian splats. Each splat stores a position, orientation, spread, color and opacity. The example's room and striped screen are generated test geometry. The cart and gate come from editable OntoKin source. The independent passage checker measures the authored meshes.

## Open the prepared handoff

Serve the prepared preview folder on localhost. Run the following command **inside that folder**, then open [the viewer](http://127.0.0.1:8000/).

```sh
python3 -m http.server 8000 --bind 127.0.0.1
```

Choose **Screen view**, then scrub between 1 and 2 seconds with **Show environment** enabled. At 1.080 s the salmon screen covers the cart. At 1.294 s it covers part of the gold front face. By 1.800 s the cart is in front. The focused time slider accepts arrow keys in 1 ms steps. As the cart moves forward it becomes visible in front of the screen. Toggle the environment to compare at the same time and camera. Choose **Widened cart** to reload the edited source's GLB. The viewer retains the room, registration, camera and timeline position.

## Build the preview from a checkout

From the repository root, choose an unused path for the preview. The installer downloads the official Three.js 0.186.1 package, verifies its SHA-512 and extracts the small set of modules the experiment imports. The module bytes match upstream [tag r186](https://github.com/mrdoob/three.js/tree/9b4a2ac29c63ccb43fd51c5661f2f873ac2c39b8).

```sh
preview=../ontokin-composite-preview
mkdir "$preview"
cp examples/splat-composite/{index.html,viewer.js} "$preview/"
python3.12 -IB examples/splat-composite/install_three.py "$preview/three"
python3.12 -IB examples/splat-composite/build_demo.py "$preview/demo"
python3.12 -IB examples/splat-composite/prepare_viewer.py "$preview/demo"
python3.12 -m http.server 8000 --bind 127.0.0.1 --directory "$preview"
```

To use a downloaded copy of the same tarball, supply `--archive /path/to/three-0.186.1.tgz` to the installer. The prepared preview works offline after the local server starts.

## Load a different environment

This experimental viewer opens the **two locally prevalidated manifests** in `demo/`. Replace the environment reference and measured registration in both manifests, then rerun `prepare_viewer.py` on the directory before serving it. The Python checker validates the embedded GLB, the two source-to-export identities, the registered anchors and the resource limits. The receipt records the exact manifest hashes and both stored and instantiated splat counts. Trust the local directory and receipt as a unit. See [the manifest format](MANIFEST.md) for the alignment and source requirements.

The browser hashes the served manifest, source and GLB bytes before parsing. It refuses secondary GLB resources and loads only a texture-free, uncompressed environment and a texture-free animated OntoKin GLB. Only objects under the authored root contribute to the overview camera framing. The splats contribute appearance and visual occlusion. Numerical checks run separately against the authored export.

The pinned renderer uses `WebGPURenderer` with an explicitly registered Gaussian-splat loader. The default requests the tested WebGL2 backend. Use `?backend=webgpu` for the experimental WebGPU route. Three.js may fall back to WebGL2 if WebGPU fails to initialize. The metrics panel records which backend actually ran. A Linux SwiftShader Vulkan probe selected WebGPU but returned white frames and device errors. Hardware WebGPU playback needs separate validation. A visible error reports a missing dependency, unsupported backend or failed asset check. The panel also records GLB bytes, parse times, elapsed time to first composite frame submission, and up to 120 intervals between animation callbacks. These measure browser work on the current machine. They do not measure physical display latency. [Three.js GaussianSplat](https://threejs.org/docs/pages/GaussianSplat.html) · [Khronos extension](https://github.com/KhronosGroup/glTF/tree/main/extensions/2.0/Khronos/KHR_gaussian_splatting)

## Play the Delft capture

The [C178 measured-site example](../../docs/engineering/captured-environment-c178/README.md) places the same cart in a photographed campus courtyard. It links the source asset and includes the three-point fit, independent fourth-corner check and commands for building the viewer.
