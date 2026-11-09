# Register a visual environment with an OntoKin animation

The experimental `ontokin-composite/1` manifest binds a read-only Gaussian-splat GLB to one authored animation. It records which files were used, how to place the environment in the OntoKin world and how closely the recorded landmarks agree. The manifest does not participate in source evaluation.

From a checkout, build a new demo directory and verify either manifest. The builder copies the synthetic environment, exports two editable service entrances with GLB/0.22, and runs the existing independent checker on each. Choose an output directory that does not exist.

```sh
python3.12 -IB examples/splat-composite/build_demo.py ../service-demo
python3.12 -Bm ontokin.composite_manifest ../service-demo/baseline.json
python3.12 -Bm ontokin.composite_manifest ../service-demo/widened.json
```

## File contract

The two generated JSON manifests are complete examples. Paths use forward slashes, remain inside the manifest directory and contain only ASCII letters, digits, periods, hyphens or underscores in each component. SHA-256 values are 64 lowercase hex characters. A failed check exits with a nonzero status.

| Field | Meaning |
| --- | --- |
| `schema` | The literal `ontokin-composite/1`. |
| `environment` | `name`, `path`, `sha256`, human-readable `provenance`, `requiredExtension` set to `KHR_gaussian_splatting`, and `authority` set to `visual-only`. Feed the existing GLB to the structural preflight before rendering. |
| `authored` | `source` and `glb` each have a path and digest. This profile pairs a single-entry, asset-free source bundle with its self-contained OntoKin GLB/0.22. The checker compares the source digest with both source-revision records inside the GLB. The demo passage checker independently checks the actual geometry and motion. |
| `registration` | `kind`, `worldUnit`, `matrix`, `anchors`, and `toleranceM`. |
| `collisionProxy` | Must be JSON `null` in this version. A future qualified proxy would need its own registration, provenance and numerical tests. |

## Registration and residuals

`matrix` is a 16-number glTF column-major affine transform from environment coordinates to the authored glTF world. `worldUnit` is `metre`. Translation occupies entries 12–14 (zero-based). Keep the authored root in its exported frame. Select `rigid` for right-handed rotation and translation in matching metric frames. Select `similarity` when a documented calibration supplies a positive uniform scale. The checker refuses reflection, shear, nonuniform scaling and perspective.

Supply 3–64 uniquely named anchors. Each pairs an observed `environment` coordinate with a `world` coordinate in metres. Pick landmarks that span a plane in both frames. A single line cannot constrain rotation around that line. The checker applies the supplied transform, computes the distance to each world point and reports the per-anchor, maximum and root-mean-square residual in metres. The maximum must be at most the declared `toleranceM` (0–1 m). Supply the transform computed during registration. This checker measures its residuals. File limits and numerical bounds are enforced in [the checker](../../ontokin/composite_manifest.py).

In this synthetic fixture the three landmarks are stored splat centres at the bottom-left, bottom-right and top-left of the striped screen. Their world coordinates come from the fixture design. The identity transform is known by construction. Binary32 storage introduces a small rounding difference. With a real capture, record how the paired landmarks, scale and tolerance were measured in `provenance`. A small residual describes the supplied landmarks only.

## Review the edit

`baseline/main.ok` defines the 0.58 m cart. `widened/main.ok` moves four deck-edge coordinates to make the cart 0.90 m wide. Both manifests refer to the same environment bytes and registration. Each variant has its own source hash, GLB hash, export receipt, passage report and manifest-check report. For example, rerun the wider cart's numerical check directly from the checkout.

```sh
python3.12 -IB examples/service-entrance/checks/check_passage.py \
    ../service-demo/widened/main.ok ../service-demo/widened/accepted-bundle.json \
    ../service-demo/widened/sliding-gate.glb --width 0.90
```

The `crossing.minimum_lateral_clearance_m` fields measure the cart against the post and gate panel throughout the crossing. The expected gaps are 0.46 m and 0.30 m per side, respectively, within 1 µm of those values. These measurements use the authored geometry with collision response disabled. The screen supplies visual depth cues during playback.
