# Published GLB compatibility checks

Two independently produced files passed the structural preflight on Linux x86-64 with CPython 3.12.14. These checks establish file compatibility. They do not establish a camera alignment, browser rendering quality or physical scale. [Recorded counts and hashes](preflight-results.json)

| Published asset | Size | Splats | Origin |
| --- | ---: | ---: | --- |
| Lux diagnostic | 1,532 bytes | 5 | The Lux project generated five colored splats at known positions. The unmodified GLB and its MIT license are included here. |
| PlayCanvas Biker | 9,166,460 bytes | 152,746 | PlayCanvas publishes this scan as a GLB produced by splat-transform 2.7.1. The upstream link enables replay. A redistribution license specific to the scan was not established in this review. |

For the diagnostic, the original generator defines the position, color and size of each splat. The recorded Git blob matches the published GLB at the pinned revision. [Upstream asset](https://github.com/rudybear/lux/blob/e05fe81a6f82e3f1e336a8abedd4836464a0bd4b/tests/assets/debug_splats.glb) · [Generator](https://github.com/rudybear/lux/blob/e05fe81a6f82e3f1e336a8abedd4836464a0bd4b/tools/debug_splats.py) · [Upstream adoption of the ratified layout](https://github.com/rudybear/lux/commit/65c3aa246e752b6224dc04a83ae1e2b94b74b436) · [MIT license](LICENSE-lux.txt)

PlayCanvas identifies this GLB as a conversion of its existing Biker PLY. Its town hall presentation describes the Biker example as a Luma scan. The published GLB uses a single primitive and supplies fallback point colors. The SuperSplat Biker scene is credited to the account `will`. [Pinned asset](https://github.com/playcanvas/engine/blob/33af7ccdff97b2380e5810fd89059525c8a020b6/examples/assets/splats/biker.glb) · [Original integration](https://github.com/playcanvas/engine/pull/9015) · [PlayCanvas presentation, p. 91](https://metaverse-standards.org/wp-content/uploads/Gaussian-Splat-Town-Hall-Slide-Deck-22Jan25.pdf#page=91) · [SuperSplat scene](https://superspl.at/scene/a5d25fb4)

Run from the repository root. The second check downloads the published file into a temporary directory.

```bash
python -m ontokin.external_gltf examples/splat-composite/fixtures/external/debug_splats.glb \
  --sha256 29d976b8de64b6877d4ed8464f6e038cb597f0ce04202c197c9688a035a7d633

probe_dir=$(mktemp -d)
curl --fail --location --output "$probe_dir/biker.glb" \
  https://raw.githubusercontent.com/playcanvas/engine/33af7ccdff97b2380e5810fd89059525c8a020b6/examples/assets/splats/biker.glb
python -m ontokin.external_gltf "$probe_dir/biker.glb" \
  --sha256 6cf16ff76fa6e223e2a759b4204f89730a84db6202bc7b0093dccae8bdc1a06c
```
