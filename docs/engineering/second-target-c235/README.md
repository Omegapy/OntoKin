# C235: finite CPU normal-loss checker

This experimental component checks whether the same 23,400 mapped corner
directions retain C214's exact source normals within the unchanged strict
0.000002 component limit. A normal is a direction used for surface shading.
Fresh source admission and geometry-only correspondence precede every check.

The [versioned contract](CONTRACT.md) defines the separate observation schema,
raw-value and corner-map bindings, numerical boundaries, complete loss reporting
and explicit native non-acceptance. It preserves C234 materials and the original
strict Blender failure. It does not start or authorize a native application.

```bash
python3 -IB tools/second_target_c235/check_normals.py \
  --package-root /absolute/extracted-handoff \
  --geometry-observations /absolute/geometry.json \
  --normal-observations /absolute/normals.json
python3 -IB tools/second_target_c235/tests/run_controls.py \
  --package-root /absolute/extracted-handoff
```

The normal document is a complete corner view bound to the exact raw geometry
file and C222 map. Each copied vector must equal the corresponding geometry
array value. A structural refusal is separate from an admitted observation that
measurably exceeds the strict limit; the latter retains every corner result.

Checks establish only the executed CPU source/environment. Exact implementation,
independent review, publication and handoff outcomes belong in their separate
evidence records. Poses and the remaining native preparation are later scopes.
