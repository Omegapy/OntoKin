# C178 · Place the service cart at TU Delft

The gold service cart and the sliding gate have an editable OntoKin source. The surrounding university buildings come from an existing photographic capture of the Aula and Library. C178 places both in the same metre coordinate system. The cart's proposed location is in the courtyard east of the Aula. No physical cart or gate was surveyed there.

## How the scale was established

Yingwen Yu published the original 1,991,216 Gaussian splats in PLY format. The [converter and source record](../../../examples/splat-composite/fixtures/external/DELFT.md) reproduce a 140,000-splat binary glTF (GLB) display copy. It retains the sampled centre coordinates and view-independent color. Cropping, resurveying or retraining the campus was unnecessary. [Original data](https://doi.org/10.17605/OSF.IO/P3CW7) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

The independent world coordinates combine four roof-outline vertices from the Dutch building register with elevation from airborne laser measurements. The visual-registration [plan](plan.json) fixed the roles, reference coordinates, 1.00 m maximum residual and 0.60 m estimated reference uncertainty. The [native-coordinate observations](picks.json) use roof-edge intersections digitized in the source capture. Three pairs determine one proper rotation, translation and positive scale of 22.917947 m per capture unit. The fourth pair has no influence on the fit. A passing report can be used directly in a C177 manifest. © 3DBAG by tudelft3d and 3DGI, used under CC BY 4.0. C178 selected four vertices and combined their horizontal coordinates with AHN elevations. [Required credit](https://docs.3dbag.nl/en/copyright/) · [AHN4 source](https://www.pdok.nl/introductie/-/article/actueel-hoogtebestand-nederland-ahn) · [Plan freeze](https://github.com/Omegapy/OntoKin/commit/df79ff2c22cf53bd4825e99ff01eab54475219b6)

| Point on the Aula | Role | 3D residual |
| --- | --- | ---: |
| Northwest end of west eave | Fit | 0.076 m |
| Southwest end of west eave | Fit | 0.069 m |
| East end of north wing | Fit | 0.024 m |
| East end of south wing | Held out | 0.216 m |

The three fit points have an RMS residual of 0.061 m. All four landmarks are on the same roof. The held-out discrepancy supports visual alignment around this building. The reference uncertainty still applies. Elevation at the world origin comes from the Dutch terrain model. The full capture contains 34 centres within a 0.5 m horizontal radius of that origin. Their heights range from −0.257 to +0.507 m. A wheel or obstacle needs a separately verified contact surface. [Point-by-point results and column-major transform](fit.json)

## Reproduce the registered scene

Use Linux x86-64 with CPython 3.12.14 for the qualified replay. From the repository root, use the [pinned conversion recipe](../../../examples/splat-composite/fixtures/external/DELFT.md) to create the 140,000-splat derivative. Set the three paths below to absolute paths. Use a fresh output directory. The first builder edits the cart, exports both recordings and runs the independent passage checker. The second refits the landmarks, checks the held-out point and creates two hash-bound manifests and a playback receipt.

```sh
site=docs/engineering/captured-environment-c178
ex=examples/splat-composite
output=/absolute/path/to/a/new/preview
glb=/absolute/path/to/delft.glb
three_archive=/absolute/path/to/three-0.186.1.tgz
mkdir "$output"
python3.12 -IB "$ex/build_demo.py" "$output/control"
python3.12 -IB "$ex/prepare_delft.py" "$output/control" "$glb" "$site/plan.json" "$site/picks.json" "$output/demo"
python3.12 -IB "$ex/install_three.py" "$output/three" --archive "$three_archive"
cp "$ex/delft-composite.html" "$output/index.html"
cp "$ex/viewer.js" "$output/viewer.js"
python3.12 -m http.server 8000 --bind 127.0.0.1 --directory "$output"
```

The two 3.25 s recordings reproduce 0.46 m clearance on each side for the original 0.58 m cart and 0.30 m for the widened 0.90 m cart. Those distances come from the moving authored geometry. The frozen plan is specific to the Delft derivative. [Generic fitting CLI and synthetic checks](../../../examples/splat-composite/fixtures/landmarks/README.md) · [Original registration and comparison contract](../external-environment-c177/README.md)

## Scope of verification

C178 is an experimental development checkpoint. On Linux, 12 new tests, 17 earlier composite tests, 66 focused language tests and seven service-entrance regressions passed. Khronos Validator 2.0.0-dev.3.10 reported zero errors and warnings on both cart recordings. For the campus GLB it lacks extension support and reports four invalid namespaced attribute names. The pinned Three.js r186 loader and the extension-specific preflight exercised those attributes. Measured native hardware performance, live collision and comparative agent cost remain open.
