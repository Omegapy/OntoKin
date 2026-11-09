# TU Delft Aula and Library capture

Yingwen Yu released the campus capture in 2025 under Creative Commons Attribution 4.0 International. The study by Yu, Verbree, van Oosterom and Pottgiesser describes the UAV image acquisition and reconstruction at Delft University of Technology. The asset is a trained Gaussian-splat field. Its PLY coordinates have a local origin and scale. [Dataset](https://doi.org/10.17605/OSF.IO/P3CW7) · [Dataset README and license notice](https://osf.io/download/kjtfb/) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) · [Paper](https://doi.org/10.5194/agile-giss-6-51-2025)

| File | Bytes | Splats | SHA-256 |
| --- | ---: | ---: | --- |
| Original `Aula & Library.ply` | 493,823,100 | 1,991,216 | `c56b1a07559312fcf1c9ef150802995005b6e3b4f8cf0c501fb96cec5d5ca45a` |
| Whole-campus SH0 display derivative | 7,841,540 | 140,000 | `3f749b56cb5399292dcd8b6c014042529e6772cb7ac37bf5797146cc72347fad` |

The converter keeps the middle record in each of 140,000 evenly spaced intervals in source order. It copies the original XYZ coordinates and the three base color coefficients (SH0). It converts logarithmic spread and opacity-logit values to physical spread in source units and unit-interval opacity, then normalizes and reorders the orientation quaternion. It omits the normals and 45 directional color coefficients. The output is a smaller, view-independent display copy under the same CC BY 4.0 license. Sampling reduces visible detail, especially from ground-level viewpoints. The source field remains available for identifying landmarks.

Run from the repository root with a new output directory. The converter refuses a source with a different SHA-256. The Open Science Framework file record publishes the same digest. [File record](https://api.osf.io/v2/nodes/p3cw7/files/osfstorage/680785e88d3efe388035fd23/) · [Original PLY](https://osf.io/download/73wq8/)

```bash
work=$(mktemp -d)
curl --fail --location --output "$work/delft.ply" https://osf.io/download/73wq8/
python3.12 -IB examples/splat-composite/delft_preview.py "$work/delft.ply" "$work/delft.glb" \
  --max-splats 140000 --report "$work/delft.json"
python3.12 -Bm ontokin.external_gltf "$work/delft.glb" \
  --sha256 3f749b56cb5399292dcd8b6c014042529e6772cb7ac37bf5797146cc72347fad
```

For a local detail view, add six bounding coordinates after `--bbox` in the order `xmin ymin zmin xmax ymax zmax`. The converter first selects the inclusive crop in the original PLY axes, then samples its vertices. A crop creates a different display asset and requires a new digest and receipt.
