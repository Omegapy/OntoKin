# Fit a captured environment to the cart’s metre frame

Freeze a measurement plan before picking landmarks or fitting a transform. Record the environment file’s SHA-256, the world measurement source and uncertainty, the scale basis, and the error limit with its physical rationale. Choose at least three distinct, well-spaced fit points. Reserve a different physical landmark for validation whenever one is available. An off-plane point helps check alignment away from the fitted plane. Record the absence of an independent check in the survey notes when none exists.

Use [the plan](synthetic-plan.json) and [the picks](synthetic-picks.json) as format examples. Keep the original plan in version control or a separately dated record. The picks pin its exact bytes by SHA-256, which detects later changes. The hash alone cannot establish when measurements were made. Record how each observed point was identified in the external GLB, including any applied scene-node transforms. The input coordinates refer to the environment scene before applying the registration. Supply separate evidence for the independence and accuracy of the world reference.

Choose `rigid` for a metric capture. Choose `similarity` when calibration supports one positive scale for the entire capture. The fit minimizes squared distances in the authored world, with equal weight per fit landmark. The predeclared minimum altitude measures spread in two dimensions. In each frame the checker takes the longest baseline between fit points, then finds the point farthest from that line. Both altitudes must meet the minimum in metres.

The supplied control uses the C177 synthetic screen and two other room landmarks. Its prescribed transform rotates about the Y axis, doubles all lengths and adds a translation. The fourth point is reserved for validation. Run from the repository root.

```bash
fixtures=examples/splat-composite/fixtures
python3 -m ontokin.landmark_registration \
  "$fixtures/landmarks/synthetic-plan.json" \
  "$fixtures/landmarks/synthetic-picks.json" \
  "$fixtures/registration-screen.glb" > fit.json
```

The report gives the environment-to-world matrix in glTF column-major order, per-point metre errors, RMS error and maximum error for each role. A successful result includes the `registration` field ready to copy into both C177 manifests alongside the matching environment digest. Run the existing manifest and viewer receipt checks after copying. Exit status 1 reports a fit outside tolerance. Status 2 indicates invalid input or geometry. An empty holdout group has a null verdict. A synthetic control exercises the software. Site accuracy requires independent observations of the actual space.

Rotation follows [Horn’s absolute orientation method](https://doi.org/10.1364/JOSAA.4.000629).
